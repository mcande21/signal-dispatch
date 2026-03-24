"""Signal Dispatch — raw readings persistence layer.

Writes every adapter fetch() output to a time-series SQLite table
(data/signals.db) for trend analysis and backtesting.

This layer is INDEPENDENT of the delta engine. Both consume adapter
output directly. Neither feeds into the other.

Usage:
    from src.delta.persist import persist_reading, init_db

    await init_db()
    await persist_reading(source="bonbast", cadence="hot", payload=data)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import aiosqlite

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_SD_ROOT = Path(__file__).parent.parent.parent  # signal-dispatch/
_DB_PATH = _SD_ROOT / "data" / "signals.db"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS source_readings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT    NOT NULL,       -- adapter name: "bonbast", "gdelt", etc.
    collected_at    TEXT    NOT NULL,       -- ISO timestamp of fetch
    cadence         TEXT    NOT NULL,       -- "hot" | "warm" | "cold"
    payload         TEXT    NOT NULL,       -- full adapter.fetch() output as JSON
    key_metric      REAL,                   -- primary scalar for this source (nullable)
    key_metric_name TEXT                    -- what key_metric represents
);
"""

_CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_source_collected
ON source_readings (source, collected_at);
"""

_CREATE_METRIC_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_source_metric
ON source_readings (source, key_metric_name, collected_at);
"""


# ---------------------------------------------------------------------------
# Key metric extractors
# One entry per adapter: source_name → (metric_name, extractor_fn)
# extractor_fn: payload dict → float | None
# ---------------------------------------------------------------------------

def _safe(fn: Callable[[dict], Any]) -> Callable[[dict], float | None]:
    """Wrap extractor to return None on any exception."""
    def wrapped(payload: dict) -> float | None:
        try:
            result = fn(payload)
            return float(result) if result is not None else None
        except Exception:
            return None
    return wrapped


KEY_METRIC_MAP: dict[str, tuple[str, Callable[[dict], float | None]]] = {
    # -------------------------------------------------------------------------
    # Ghost Market — financial / geopolitical
    # -------------------------------------------------------------------------
    "bonbast": (
        "usd_irr_rate",
        _safe(lambda p: p.get("usd_irr") or p.get("rates", {}).get("USD", {}).get("rate")),
    ),
    "dolarvzla": (
        "usd_ves_parallel_rate",
        _safe(lambda p: p.get("usd_ves") or p.get("rate") or p.get("rates", {}).get("USD")),
    ),
    "tedpix": (
        "tedpix_index",
        _safe(lambda p: p["index"]),
    ),
    "eia": (
        "crude_inventory_mbbl",
        _safe(lambda p: p.get("value") or p.get("inventory_mbbl")),
    ),
    "eia_grid": (
        "us_grid_generation_mwh",
        _safe(lambda p: p.get("total_generation_mwh") or p.get("value")),
    ),
    "agsi": (
        "eu_gas_storage_pct",
        _safe(lambda p: p.get("storage_percent") or p.get("percent_full")),
    ),
    "entsog": (
        "eu_gas_flow_gwh",
        _safe(lambda p: p.get("total_flow_gwh") or p.get("value")),
    ),
    "ecb": (
        "eurusd_rate",
        _safe(lambda p: p.get("value") or p.get("rate")),
    ),
    "fred": (
        "vix",
        _safe(lambda p: p.get("value")),
    ),
    "noaa": (
        "temperature_anomaly_c",
        _safe(lambda p: p.get("value") or p.get("anomaly_c")),
    ),

    # -------------------------------------------------------------------------
    # Ghost Market — OSINT / event feeds
    # -------------------------------------------------------------------------
    "gdelt": (
        "article_count",
        _safe(lambda p: p.get("article_count") or len(p.get("articles", []))),
    ),
    "acled": (
        "event_count",
        _safe(lambda p: p.get("total_events") or p.get("event_count") or len(p.get("events", []))),
    ),
    "viirs": (
        "hotspot_count",
        _safe(lambda p: p.get("hotspot_count") or len(p.get("hotspots", []))),
    ),
    "oryx": (
        "total_losses",
        _safe(lambda p: p.get("total_losses") or p.get("loss_count")),
    ),
    "ooni": (
        "anomaly_rate",
        _safe(lambda p: p.get("anomaly_rate") or p.get("blocked_count") or len(p.get("blocked_endpoints", []))),
    ),
    "cloudflare_radar": (
        "traffic_anomaly_score",
        _safe(lambda p: p.get("anomaly_score") or p.get("score")),
    ),
    "adsb": (
        "aircraft_count",
        _safe(lambda p: p.get("aircraft_count") or len(p.get("aircraft", []))),
    ),
    "telegram_osint": (
        "urgent_message_count",
        _safe(lambda p: p.get("urgent_messages") or p.get("urgent_count") or len(p.get("messages", []))),
    ),
    "ofac": (
        "designation_count",
        _safe(lambda p: p.get("total_results") or p.get("designation_count")),
    ),
    "opensanctions": (
        "new_entry_count",
        _safe(lambda p: p.get("new_entries") or p.get("count")),
    ),
    "usaspending": (
        "contract_total_usd",
        _safe(lambda p: p.get("total_obligated_amount") or p.get("total_usd")),
    ),
    "comtrade": (
        "trade_value_usd",
        _safe(lambda p: p.get("trade_value") or p.get("value_usd")),
    ),
    "federal_register": (
        "document_count",
        _safe(lambda p: p.get("count") or len(p.get("results", []))),
    ),
    "congress": (
        "bill_count",
        _safe(lambda p: p.get("count") or len(p.get("bills", []))),
    ),
    "fec": (
        "total_contributions_usd",
        _safe(lambda p: p.get("total_receipts") or p.get("total_usd")),
    ),

    # -------------------------------------------------------------------------
    # New adapters (built 2026-03-20)
    # -------------------------------------------------------------------------
    "who_outbreaks": (
        "active_notice_count",
        _safe(lambda p: p.get("notice_count")),
    ),
    "reliefweb": (
        "active_disaster_count",
        _safe(lambda p: p.get("disaster_count")),
    ),
    "opensky": (
        "total_airborne_aircraft",
        _safe(lambda p: sum(
            r.get("aircraft_count", 0)
            for r in p.get("regions", {}).values()
        )),
    ),
}


# ---------------------------------------------------------------------------
# DB initialization
# ---------------------------------------------------------------------------

async def init_db(db_path: Path = _DB_PATH) -> None:
    """Initialize the signals database and ensure schema exists."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(str(db_path)) as conn:
        await conn.execute(_CREATE_TABLE_SQL)
        await conn.execute(_CREATE_INDEX_SQL)
        await conn.execute(_CREATE_METRIC_INDEX_SQL)
        await conn.commit()
    log.info("signals.db initialized at %s", db_path)


# ---------------------------------------------------------------------------
# Core persistence function
# ---------------------------------------------------------------------------

async def persist_reading(
    source: str,
    cadence: str,
    payload: dict,
    db_path: Path = _DB_PATH,
) -> None:
    """Persist one adapter fetch() result to source_readings.

    Args:
        source:   Adapter name ("bonbast", "gdelt", etc.)
        cadence:  Run cadence tier ("hot", "warm", "cold")
        payload:  Raw dict returned by adapter.fetch()
        db_path:  Path to SQLite db (default: data/signals.db)
    """
    collected_at = datetime.now(timezone.utc).isoformat()

    # Extract key metric
    metric_name, extractor = KEY_METRIC_MAP.get(source, (None, None))
    key_metric: float | None = extractor(payload) if extractor else None

    payload_json = json.dumps(payload, separators=(",", ":"))

    try:
        async with aiosqlite.connect(str(db_path)) as conn:
            await conn.execute(
                """
                INSERT INTO source_readings
                    (source, collected_at, cadence, payload, key_metric, key_metric_name)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (source, collected_at, cadence, payload_json, key_metric, metric_name),
            )
            await conn.commit()
        log.debug(
            "persisted reading: source=%s metric=%s=%s",
            source, metric_name, key_metric,
        )
    except Exception as e:
        # Persistence failure must never crash the daemon
        log.error("persist_reading failed for %s: %s", source, e)


# ---------------------------------------------------------------------------
# Query helpers (for analysis / backtesting)
# ---------------------------------------------------------------------------

async def query_metric_series(
    source: str,
    metric_name: str,
    since: str | None = None,
    limit: int = 1000,
    db_path: Path = _DB_PATH,
) -> list[dict]:
    """Return time-series of key_metric values for a source.

    Args:
        source:      Adapter name
        metric_name: e.g. "usd_irr_rate"
        since:       ISO timestamp lower bound (optional)
        limit:       Max rows (default 1000)

    Returns:
        List of {"collected_at": str, "value": float} dicts, oldest first.
    """
    sql = """
        SELECT collected_at, key_metric
        FROM source_readings
        WHERE source = ?
          AND key_metric_name = ?
          AND key_metric IS NOT NULL
    """
    params: list[Any] = [source, metric_name]

    if since:
        sql += " AND collected_at >= ?"
        params.append(since)

    sql += " ORDER BY collected_at ASC LIMIT ?"
    params.append(limit)

    async with aiosqlite.connect(str(db_path)) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(sql, params)
        rows = await cursor.fetchall()

    return [{"collected_at": r["collected_at"], "value": r["key_metric"]} for r in rows]


async def query_latest(
    source: str,
    db_path: Path = _DB_PATH,
) -> dict | None:
    """Return the most recent raw payload for a source."""
    async with aiosqlite.connect(str(db_path)) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            """
            SELECT source, collected_at, cadence, payload, key_metric, key_metric_name
            FROM source_readings
            WHERE source = ?
            ORDER BY collected_at DESC
            LIMIT 1
            """,
            (source,),
        )
        row = await cursor.fetchone()

    if not row:
        return None

    return {
        "source": row["source"],
        "collected_at": row["collected_at"],
        "cadence": row["cadence"],
        "payload": json.loads(row["payload"]),
        "key_metric": row["key_metric"],
        "key_metric_name": row["key_metric_name"],
    }


async def get_source_stats(db_path: Path = _DB_PATH) -> list[dict]:
    """Return summary stats per source — count, first/last reading, latest metric."""
    async with aiosqlite.connect(str(db_path)) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            """
            SELECT
                source,
                COUNT(*) as reading_count,
                MIN(collected_at) as first_reading,
                MAX(collected_at) as last_reading,
                key_metric_name,
                (
                    SELECT key_metric FROM source_readings s2
                    WHERE s2.source = s1.source
                    ORDER BY collected_at DESC LIMIT 1
                ) as latest_metric
            FROM source_readings s1
            GROUP BY source
            ORDER BY source
            """,
        )
        rows = await cursor.fetchall()

    return [dict(r) for r in rows]
