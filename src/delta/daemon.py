"""Signal Dispatch delta engine daemon.

Entry point for scheduled polling runs.

Usage:
    python -m src.delta.daemon --cadence hot    # Hot sources (6h cycle)
    python -m src.delta.daemon --cadence warm   # Warm sources (daily)
    python -m src.delta.daemon --cadence cold   # Cold sources (on-demand)
    python -m src.delta.daemon --all            # All sources

Cadences:
    hot  -- bonbast, ooni, gdelt, prediction_markets (every 6h via launchd)
    warm -- eia, agsi (daily)
    cold -- fred (on-demand or weekly)

State layout (all under content/state/deltas/):
    current/          -- latest delta per source (JSON)
    history/          -- append-only daily JSONL logs
    prior_state/      -- raw source snapshots for next comparison
    clusters/         -- correlated delta groups
    alerts/pending/   -- unacknowledged threshold breaches
    alerts/acknowledged/ -- Cooper has seen these
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_SD_ROOT = Path(__file__).parent.parent.parent  # signal-dispatch/
_DELTAS_ROOT = _SD_ROOT / "content" / "state" / "deltas"
_THRESHOLDS_PATH = _DELTAS_ROOT / "thresholds.json"

_CURRENT_DIR = _DELTAS_ROOT / "current"
_HISTORY_DIR = _DELTAS_ROOT / "history"
_PRIOR_DIR = _DELTAS_ROOT / "prior_state"
_CLUSTERS_DIR = _DELTAS_ROOT / "clusters"
_ALERTS_PENDING_DIR = _DELTAS_ROOT / "alerts" / "pending"
_ALERTS_ACKED_DIR = _DELTAS_ROOT / "alerts" / "acknowledged"

# Ensure all dirs exist at import time
for _d in (
    _CURRENT_DIR, _HISTORY_DIR, _PRIOR_DIR, _CLUSTERS_DIR,
    _ALERTS_PENDING_DIR, _ALERTS_ACKED_DIR,
):
    _d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Source cadence registry
# ---------------------------------------------------------------------------

# Each entry: (source_name, cadence, poll_fn, engine_fn_key)
# engine_fn_key maps to how we build the delta in _run_source()
HOT_SOURCES = [
    "bonbast", "ooni", "cloudflare_radar", "tedpix",
    "dolarvzla", "gdelt", "viirs", "prediction_markets",
    "acled", "adsb", "telegram_osint",
]
WARM_SOURCES = [
    "eia", "agsi", "entsog", "ofac", "oryx",
    "usaspending", "federal_register", "congress",
    "opensanctions",
]
COLD_SOURCES = [
    "fred", "ecb", "comtrade", "eia_grid", "fec", "noaa",
]


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("delta.daemon")


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load_thresholds() -> dict:
    with open(_THRESHOLDS_PATH) as f:
        return json.load(f)


def _load_prior(source: str) -> dict | None:
    """Load prior state snapshot for a source. Returns None if not found."""
    path = _PRIOR_DIR / f"{source}.json"
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log.warning("Could not load prior state for %s: %s", source, e)
        return None


def _save_prior(source: str, data: dict) -> None:
    """Atomically save current data as the new prior state."""
    path = _PRIOR_DIR / f"{source}.json"
    _atomic_write(path, data)


def _atomic_write(path: Path, data: Any) -> None:
    """Write JSON atomically: write .tmp, rename over target."""
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent), prefix=path.name, suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, str(path))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _write_current(source: str, delta: dict) -> None:
    """Write latest delta for a source to current/."""
    path = _CURRENT_DIR / f"{source}.json"
    _atomic_write(path, delta)


def _append_history(source: str, delta: dict) -> None:
    """Append delta to today's JSONL history file."""
    date_str = _today_str()
    path = _HISTORY_DIR / f"{source}-{date_str}.jsonl"
    line = json.dumps(delta, separators=(",", ":"))
    with open(path, "a") as f:
        f.write(line + "\n")


def _write_alert(source: str, delta: dict) -> None:
    """Write a threshold breach alert to alerts/pending/."""
    ts = _now_iso().replace(":", "-").replace("+", "Z")
    filename = f"{source}-{ts}.json"
    path = _ALERTS_PENDING_DIR / filename
    payload = {
        "alert_id": filename,
        "created_at": _now_iso(),
        "source": source,
        "threshold_status": delta.get("threshold_status"),
        "plain_english": delta.get("plain_english", ""),
        "delta": delta,
    }
    _atomic_write(path, payload)
    log.info("ALERT [%s]: %s", source, delta.get("plain_english", ""))


def _load_history_values(source: str, field_key: str = "value", days: int = 30) -> list[float]:
    """Load historical values from JSONL files for percentile context.

    Reads the last `days` of history files and extracts current[field_key].
    Returns a flat list of floats.
    """
    values: list[float] = []
    today = datetime.now(timezone.utc)
    for i in range(days):
        from datetime import timedelta  # noqa: PLC0415
        day = today - timedelta(days=i)
        date_str = day.strftime("%Y-%m-%d")
        path = _HISTORY_DIR / f"{source}-{date_str}.jsonl"
        if not path.exists():
            continue
        try:
            with open(path) as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        val = entry.get("current", {}).get(field_key)
                        if val is not None:
                            values.append(float(val))
                    except (json.JSONDecodeError, ValueError, TypeError):
                        continue
        except OSError:
            continue
    return values


# ---------------------------------------------------------------------------
# Per-source run logic
# ---------------------------------------------------------------------------

async def run_bonbast(thresholds: dict) -> dict | None:
    """Poll Bonbast, compute numeric delta, return delta dict."""
    from .sources import poll_bonbast  # noqa: PLC0415
    from .engine import compute_numeric  # noqa: PLC0415

    current_raw = await poll_bonbast()
    if not current_raw.get("ok"):
        log.error("bonbast poll failed: %s", current_raw.get("error"))
        return None

    current_usd = current_raw.get("usd_irr")
    if current_usd is None:
        log.warning("bonbast: no USD/IRR in response")
        return None

    prior = _load_prior("bonbast")
    prior_usd = prior.get("usd_irr") if prior else None
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior("bonbast", current_raw)

    if prior_usd is None:
        log.info("bonbast: no prior state, recording baseline")
        return None

    history = _load_history_values("bonbast", field_key="value")

    delta = compute_numeric(
        source="bonbast",
        prior_value=prior_usd,
        current_value=current_usd,
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        field_name="USD/IRR",
        thresholds=thresholds.get("bonbast", {}),
        history_values=history if history else None,
    )
    return delta


async def run_fred(thresholds: dict, series_id: str = "VIXCLS") -> dict | None:
    """Poll FRED, compute numeric delta."""
    from .sources import poll_fred  # noqa: PLC0415
    from .engine import compute_numeric  # noqa: PLC0415

    current_raw = await poll_fred(series_id=series_id)
    if not current_raw.get("ok"):
        log.error("fred poll failed: %s", current_raw.get("error"))
        return None

    current_val = current_raw.get("latest_value")
    if current_val is None:
        log.warning("fred: no latest_value in response for %s", series_id)
        return None

    cache_key = f"fred_{series_id.lower()}"
    prior = _load_prior(cache_key)
    prior_val = prior.get("latest_value") if prior else None
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior(cache_key, current_raw)

    if prior_val is None:
        log.info("fred[%s]: no prior state, recording baseline", series_id)
        return None

    obs_values = [o["value"] for o in current_raw.get("observations", [])]

    delta = compute_numeric(
        source=f"fred_{series_id.lower()}",
        prior_value=prior_val,
        current_value=current_val,
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        field_name=current_raw.get("series_label", series_id),
        thresholds=thresholds.get("fred", {}),
        history_values=obs_values if obs_values else None,
    )
    return delta


async def run_eia(thresholds: dict, series_id: str = "WCESTUS1") -> dict | None:
    """Poll EIA, compute numeric delta."""
    from .sources import poll_eia  # noqa: PLC0415
    from .engine import compute_numeric  # noqa: PLC0415

    current_raw = await poll_eia(series_id=series_id)
    if not current_raw.get("ok"):
        log.error("eia poll failed: %s", current_raw.get("error"))
        return None

    current_val = current_raw.get("latest_value")
    if current_val is None:
        log.warning("eia: no latest_value")
        return None

    cache_key = f"eia_{series_id.lower()}"
    prior = _load_prior(cache_key)
    prior_val = prior.get("latest_value") if prior else None
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior(cache_key, current_raw)

    if prior_val is None:
        log.info("eia[%s]: no prior state, recording baseline", series_id)
        return None

    obs_values = [o["value"] for o in current_raw.get("observations", [])]

    delta = compute_numeric(
        source=f"eia_{series_id.lower()}",
        prior_value=prior_val,
        current_value=current_val,
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        field_name=current_raw.get("series_title", series_id),
        thresholds=thresholds.get("eia", {}),
        history_values=obs_values if obs_values else None,
    )
    return delta


async def run_agsi(thresholds: dict, country: str = "DE") -> dict | None:
    """Poll AGSI gas storage, compute numeric delta on fill %."""
    from .sources import poll_agsi  # noqa: PLC0415
    from .engine import compute_numeric  # noqa: PLC0415

    current_raw = await poll_agsi(country=country)
    if not current_raw.get("ok"):
        log.error("agsi poll failed: %s", current_raw.get("error"))
        return None

    current_pct = current_raw.get("latest_full_pct")
    if current_pct is None:
        log.warning("agsi: no latest_full_pct")
        return None

    cache_key = f"agsi_{country.lower()}"
    prior = _load_prior(cache_key)
    prior_pct = prior.get("latest_full_pct") if prior else None
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior(cache_key, current_raw)

    if prior_pct is None:
        log.info("agsi[%s]: no prior state, recording baseline", country)
        return None

    storage = current_raw.get("storage_data", [])
    hist_pcts = [s["full_pct"] for s in storage if s.get("full_pct") is not None]

    delta = compute_numeric(
        source=f"agsi_{country.lower()}",
        prior_value=prior_pct,
        current_value=current_pct,
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        field_name=f"{country} gas storage fill %",
        thresholds=thresholds.get("agsi", {}),
        history_values=hist_pcts if hist_pcts else None,
    )
    return delta


async def run_prediction_markets(thresholds: dict) -> list[dict]:
    """Poll Kalshi markets, compute numeric deltas for each ticker."""
    from .sources import poll_prediction_markets  # noqa: PLC0415
    from .engine import compute_numeric  # noqa: PLC0415

    current_raw = await poll_prediction_markets()
    if not current_raw.get("ok"):
        log.error("prediction_markets poll failed: %s", current_raw.get("error"))
        return []

    prior = _load_prior("prediction_markets")
    prior_markets = prior.get("markets", {}) if prior else {}
    _save_prior("prediction_markets", current_raw)

    deltas = []
    for ticker, market in current_raw.get("markets", {}).items():
        current_price = market.get("yes_price")
        if current_price is None:
            continue
        prior_market = prior_markets.get(ticker, {})
        prior_price = prior_market.get("yes_price")
        prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

        if prior_price is None:
            log.info("prediction_markets[%s]: no prior, recording baseline", ticker)
            continue

        delta = compute_numeric(
            source=f"pm_{ticker.lower()}",
            prior_value=prior_price,
            current_value=current_price,
            prior_as_of=prior_as_of,
            current_as_of=current_raw["as_of"],
            field_name=f"{market.get('title', ticker)} YES",
            thresholds=thresholds.get("prediction_markets", {}),
        )
        deltas.append(delta)

    return deltas


async def run_ooni(thresholds: dict) -> dict | None:
    """Poll OONI, compute binary state delta."""
    from .sources import poll_ooni  # noqa: PLC0415
    from .engine import compute_binary  # noqa: PLC0415

    current_raw = await poll_ooni()
    if not current_raw.get("ok"):
        log.error("ooni poll failed: %s", current_raw.get("error"))
        return None

    anomaly_rate = current_raw.get("anomaly_rate", 0.0)
    new_blocked = current_raw.get("new_blocked_endpoints", 0)
    current_state = anomaly_rate > 0.15 or new_blocked > 0  # elevated anomaly = blocking active

    prior = _load_prior("ooni")
    prior_state = prior.get("blocking_active", False) if prior else False
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    # Persist state flag alongside raw data
    current_raw["blocking_active"] = current_state
    _save_prior("ooni", current_raw)

    delta = compute_binary(
        source="ooni",
        prior_state=prior_state,
        current_state=current_state,
        state_label_true="blocking_active",
        state_label_false="normal",
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        state_duration_hours=None,
        thresholds=thresholds.get("ooni", {}),
        new_blocked_endpoints=new_blocked,
    )
    return delta


async def run_gdelt(thresholds: dict, query: str = "Iran military conflict") -> dict | None:
    """Poll GDELT, compute event-set delta."""
    from .sources import poll_gdelt  # noqa: PLC0415
    from .engine import compute_event_set  # noqa: PLC0415

    current_raw = await poll_gdelt(query=query)
    if not current_raw.get("ok"):
        log.error("gdelt poll failed: %s", current_raw.get("error"))
        return None

    current_count = current_raw.get("article_count", 0)
    cache_key = f"gdelt_{query.lower().replace(' ', '_')[:30]}"
    prior = _load_prior(cache_key)
    prior_count = prior.get("article_count", 0) if prior else 0
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior(cache_key, current_raw)

    history_counts = _load_history_for_gdelt(cache_key, days=30)

    delta = compute_event_set(
        source=f"gdelt_{query.split()[0].lower()}",
        prior_count=prior_count,
        current_count=current_count,
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        prior_categories=None,
        current_categories=None,
        thresholds=thresholds.get("gdelt", {}),
        history_counts=history_counts if history_counts else None,
    )
    return delta


async def run_cloudflare_radar(thresholds: dict) -> dict | None:
    """Poll Cloudflare Radar Iran traffic, compute binary + numeric delta."""
    from .sources import poll_cloudflare_radar  # noqa: PLC0415
    from .engine import compute_numeric  # noqa: PLC0415

    current_raw = await poll_cloudflare_radar(location="IR", endpoint="anomalies")
    if not current_raw.get("ok"):
        log.error("cloudflare_radar poll failed: %s", current_raw.get("error"))
        return None

    current_count = current_raw.get("anomaly_count", 0)
    prior = _load_prior("cloudflare_radar")
    prior_count = prior.get("anomaly_count", 0) if prior else 0
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior("cloudflare_radar", current_raw)

    if prior is None:
        log.info("cloudflare_radar: no prior state, recording baseline")
        return None

    delta = compute_numeric(
        source="cloudflare_radar",
        prior_value=float(prior_count),
        current_value=float(current_count),
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        field_name="IR anomaly count",
        thresholds=thresholds.get("cloudflare_radar", {}),
    )
    return delta


async def run_tedpix(thresholds: dict) -> dict | None:
    """Poll Tehran Stock Exchange TEDPIX, compute numeric delta."""
    from .sources import poll_tedpix  # noqa: PLC0415
    from .engine import compute_numeric  # noqa: PLC0415

    current_raw = await poll_tedpix()
    if not current_raw.get("ok"):
        log.error("tedpix poll failed: %s", current_raw.get("error"))
        return None

    current_val = current_raw.get("tedpix")
    if current_val is None:
        log.warning("tedpix: no value in response")
        return None

    prior = _load_prior("tedpix")
    prior_val = prior.get("tedpix") if prior else None
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior("tedpix", current_raw)

    if prior_val is None:
        log.info("tedpix: no prior state, recording baseline")
        return None

    delta = compute_numeric(
        source="tedpix",
        prior_value=float(prior_val),
        current_value=float(current_val),
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        field_name="TEDPIX index",
        thresholds=thresholds.get("tedpix", {}),
    )
    return delta


async def run_dolarvzla(thresholds: dict) -> dict | None:
    """Poll Venezuelan bolivar black-market rate, compute numeric delta."""
    from .sources import poll_dolarvzla  # noqa: PLC0415
    from .engine import compute_numeric  # noqa: PLC0415

    current_raw = await poll_dolarvzla()
    if not current_raw.get("ok"):
        log.error("dolarvzla poll failed: %s", current_raw.get("error"))
        return None

    current_val = current_raw.get("usd_ves")
    if current_val is None:
        log.warning("dolarvzla: no usd_ves in response")
        return None

    prior = _load_prior("dolarvzla")
    prior_val = prior.get("usd_ves") if prior else None
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior("dolarvzla", current_raw)

    if prior_val is None:
        log.info("dolarvzla: no prior state, recording baseline")
        return None

    delta = compute_numeric(
        source="dolarvzla",
        prior_value=float(prior_val),
        current_value=float(current_val),
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        field_name="USD/VES",
        thresholds=thresholds.get("dolarvzla", {}),
    )
    return delta


async def run_viirs(thresholds: dict, country: str = "IR") -> dict | None:
    """Poll VIIRS fire hotspots, compute event-set delta."""
    from .sources import poll_viirs  # noqa: PLC0415
    from .engine import compute_event_set  # noqa: PLC0415

    current_raw = await poll_viirs(country=country)
    if not current_raw.get("ok"):
        log.error("viirs poll failed: %s", current_raw.get("error"))
        return None

    current_count = current_raw.get("hotspot_count", 0)
    cache_key = f"viirs_{country.lower()}"
    prior = _load_prior(cache_key)
    prior_count = prior.get("hotspot_count", 0) if prior else 0
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior(cache_key, current_raw)

    if prior is None:
        log.info("viirs[%s]: no prior state, recording baseline", country)
        return None

    delta = compute_event_set(
        source=f"viirs_{country.lower()}",
        prior_count=prior_count,
        current_count=current_count,
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        prior_categories=None,
        current_categories=None,
        thresholds=thresholds.get("viirs", {}),
    )
    return delta


async def run_entsog(thresholds: dict) -> dict | None:
    """Poll ENTSOG European gas flows, compute numeric delta."""
    from .sources import poll_entsog  # noqa: PLC0415
    from .engine import compute_numeric  # noqa: PLC0415

    current_raw = await poll_entsog()
    if not current_raw.get("ok"):
        log.error("entsog poll failed: %s", current_raw.get("error"))
        return None

    current_count = current_raw.get("flow_count", 0)
    prior = _load_prior("entsog")
    prior_count = prior.get("flow_count", 0) if prior else 0
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior("entsog", current_raw)

    if prior is None:
        log.info("entsog: no prior state, recording baseline")
        return None

    delta = compute_numeric(
        source="entsog",
        prior_value=float(prior_count),
        current_value=float(current_count),
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        field_name="EU gas flow count",
        thresholds=thresholds.get("entsog", {}),
    )
    return delta


async def run_ofac(thresholds: dict) -> dict | None:
    """Poll OFAC SDN list, compute numeric delta on IRAN entity count."""
    from .sources import poll_ofac  # noqa: PLC0415
    from .engine import compute_numeric  # noqa: PLC0415

    current_raw = await poll_ofac(filter_term="IRAN")
    if not current_raw.get("ok"):
        log.error("ofac poll failed: %s", current_raw.get("error"))
        return None

    current_count = current_raw.get("entity_count", 0)

    prior = _load_prior("ofac")
    prior_count = prior.get("entity_count", 0) if prior else None
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior("ofac", current_raw)

    if prior is None or prior_count is None:
        log.info("ofac: no prior state, recording baseline")
        return None

    delta = compute_numeric(
        source="ofac",
        prior_value=float(prior_count),
        current_value=float(current_count),
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        field_name="IRAN SDN entity count",
        thresholds=thresholds.get("ofac", {}),
    )
    return delta


async def run_oryx(thresholds: dict, country: str = "Russia") -> dict | None:
    """Poll Oryx equipment losses, compute event-set delta."""
    from .sources import poll_oryx  # noqa: PLC0415
    from .engine import compute_event_set  # noqa: PLC0415

    current_raw = await poll_oryx(country=country)
    if not current_raw.get("ok"):
        log.error("oryx poll failed: %s", current_raw.get("error"))
        return None

    current_total = current_raw.get("total_losses", 0)
    cache_key = f"oryx_{country.lower().replace(' ', '_')}"
    prior = _load_prior(cache_key)
    prior_total = prior.get("total_losses", 0) if prior else 0
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior(cache_key, current_raw)

    if prior is None:
        log.info("oryx[%s]: no prior state, recording baseline", country)
        return None

    delta = compute_event_set(
        source=f"oryx_{country.lower().replace(' ', '_')}",
        prior_count=prior_total,
        current_count=current_total,
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        prior_categories=None,
        current_categories=None,
        thresholds=thresholds.get("oryx", {}),
    )
    return delta


async def run_usaspending(thresholds: dict) -> dict | None:
    """Poll USASpending DoD contracts. Composite delta -- records baseline only."""
    from .sources import poll_usaspending  # noqa: PLC0415

    current_raw = await poll_usaspending(agency="DoD")
    if not current_raw.get("ok"):
        log.error("usaspending poll failed: %s", current_raw.get("error"))
        return None

    _save_prior("usaspending", current_raw)
    log.info("usaspending: composite delta not yet implemented -- baseline recorded")
    return None


async def run_federal_register(thresholds: dict) -> dict | None:
    """Poll Federal Register Iran sanctions entries, compute event-set delta on count."""
    from .sources import poll_federal_register  # noqa: PLC0415
    from .engine import compute_event_set  # noqa: PLC0415

    current_raw = await poll_federal_register(query="Iran sanctions")
    if not current_raw.get("ok"):
        log.error("federal_register poll failed: %s", current_raw.get("error"))
        return None

    current_count = current_raw.get("entry_count", 0)
    prior = _load_prior("federal_register")
    prior_count = prior.get("entry_count", 0) if prior else None
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior("federal_register", current_raw)

    if prior is None or prior_count is None:
        log.info("federal_register: no prior state, recording baseline")
        return None

    delta = compute_event_set(
        source="federal_register",
        prior_count=prior_count,
        current_count=current_count,
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        prior_categories=None,
        current_categories=None,
        thresholds=thresholds.get("federal_register", {}),
    )
    return delta


async def run_congress(thresholds: dict) -> dict | None:
    """Poll Congress.gov Iran-related bills, compute event-set delta on count."""
    from .sources import poll_congress  # noqa: PLC0415
    from .engine import compute_event_set  # noqa: PLC0415

    current_raw = await poll_congress(query="Iran")
    if not current_raw.get("ok"):
        log.error("congress poll failed: %s", current_raw.get("error"))
        return None

    current_count = current_raw.get("bill_count", 0)
    prior = _load_prior("congress")
    prior_count = prior.get("bill_count", 0) if prior else None
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior("congress", current_raw)

    if prior is None or prior_count is None:
        log.info("congress: no prior state, recording baseline")
        return None

    delta = compute_event_set(
        source="congress",
        prior_count=prior_count,
        current_count=current_count,
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        prior_categories=None,
        current_categories=None,
        thresholds=thresholds.get("congress", {}),
    )
    return delta


async def run_ecb(thresholds: dict) -> dict | None:
    """Poll ECB EU 10-year bond yield, compute numeric delta."""
    from .sources import poll_ecb  # noqa: PLC0415
    from .engine import compute_numeric  # noqa: PLC0415

    current_raw = await poll_ecb()
    if not current_raw.get("ok"):
        log.error("ecb poll failed: %s", current_raw.get("error"))
        return None

    current_val = current_raw.get("latest_value")
    if current_val is None:
        log.warning("ecb: no latest_value")
        return None

    prior = _load_prior("ecb")
    prior_val = prior.get("latest_value") if prior else None
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior("ecb", current_raw)

    if prior_val is None:
        log.info("ecb: no prior state, recording baseline")
        return None

    obs_values = [o["value"] for o in current_raw.get("observations", []) if "value" in o]

    delta = compute_numeric(
        source="ecb",
        prior_value=float(prior_val),
        current_value=float(current_val),
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        field_name="EU 10Y bond yield",
        thresholds=thresholds.get("ecb", {}),
        history_values=obs_values if obs_values else None,
    )
    return delta


async def run_comtrade(thresholds: dict) -> dict | None:
    """Poll Comtrade Iran trade data. Composite delta -- records baseline only."""
    from .sources import poll_comtrade  # noqa: PLC0415

    current_raw = await poll_comtrade(reporter="IR", partner="CN")
    if not current_raw.get("ok"):
        log.error("comtrade poll failed: %s", current_raw.get("error"))
        return None

    _save_prior("comtrade", current_raw)
    log.info("comtrade: composite delta not yet implemented -- baseline recorded")
    return None


async def run_eia_grid(thresholds: dict) -> dict | None:
    """Poll EIA US grid electricity data, compute numeric delta."""
    from .sources import poll_eia_grid  # noqa: PLC0415
    from .engine import compute_numeric  # noqa: PLC0415

    current_raw = await poll_eia_grid(respondent="US48", data_type="D")
    if not current_raw.get("ok"):
        log.error("eia_grid poll failed: %s", current_raw.get("error"))
        return None

    current_val = current_raw.get("latest_value")
    if current_val is None:
        log.warning("eia_grid: no latest_value")
        return None

    prior = _load_prior("eia_grid")
    prior_val = prior.get("latest_value") if prior else None
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior("eia_grid", current_raw)

    if prior_val is None:
        log.info("eia_grid: no prior state, recording baseline")
        return None

    obs_values = [o.get("value") for o in current_raw.get("grid_data", []) if o.get("value") is not None]

    delta = compute_numeric(
        source="eia_grid",
        prior_value=float(prior_val),
        current_value=float(current_val),
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        field_name="US48 net generation",
        thresholds=thresholds.get("eia_grid", {}),
        history_values=obs_values if obs_values else None,
    )
    return delta


async def run_fec(thresholds: dict) -> dict | None:
    """Poll FEC campaign finance data. Composite delta -- records baseline only."""
    from .sources import poll_fec  # noqa: PLC0415

    current_raw = await poll_fec(query="defense")
    if not current_raw.get("ok"):
        log.error("fec poll failed: %s", current_raw.get("error"))
        return None

    _save_prior("fec", current_raw)
    log.info("fec: composite delta not yet implemented -- baseline recorded")
    return None


async def run_noaa(thresholds: dict) -> dict | None:
    """Poll NOAA weather alerts for tracked states, compute event-set delta."""
    from .sources import poll_noaa  # noqa: PLC0415
    from .engine import compute_event_set  # noqa: PLC0415

    current_raw = await poll_noaa(query_type="alerts", state="NY")
    if not current_raw.get("ok"):
        log.error("noaa poll failed: %s", current_raw.get("error"))
        return None

    current_count = current_raw.get("alert_count", 0)
    prior = _load_prior("noaa")
    prior_count = prior.get("alert_count", 0) if prior else 0
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior("noaa", current_raw)

    if prior is None:
        log.info("noaa: no prior state, recording baseline")
        return None

    delta = compute_event_set(
        source="noaa",
        prior_count=prior_count,
        current_count=current_count,
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        prior_categories=None,
        current_categories=None,
        thresholds=thresholds.get("noaa", {}),
    )
    return delta


async def run_acled(thresholds: dict) -> dict | None:
    """Poll ACLED conflict events, compute event-set delta on total events."""
    from .sources import poll_acled  # noqa: PLC0415
    from .engine import compute_event_set  # noqa: PLC0415

    current_raw = await poll_acled()
    if not current_raw.get("ok"):
        log.error("acled poll failed: %s", current_raw.get("error"))
        return None

    current_events = current_raw.get("total_events", 0)
    current_fatalities = current_raw.get("total_fatalities", 0)

    prior = _load_prior("acled")
    prior_events = prior.get("total_events", 0) if prior else 0
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior("acled", current_raw)

    if prior is None:
        log.info("acled: no prior state, recording baseline")
        return None

    delta = compute_event_set(
        source="acled",
        prior_count=prior_events,
        current_count=current_events,
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        prior_categories=None,
        current_categories={"total_fatalities": current_fatalities},
        thresholds=thresholds.get("acled", {}),
    )
    return delta


async def run_adsb(thresholds: dict) -> dict | None:
    """Poll ADS-B Exchange military flights, compute event-set delta on total military count."""
    from .sources import poll_adsb  # noqa: PLC0415
    from .engine import compute_event_set  # noqa: PLC0415

    current_raw = await poll_adsb()
    if not current_raw.get("ok"):
        log.error("adsb poll failed: %s", current_raw.get("error"))
        return None

    current_total = current_raw.get("total_military", 0)
    current_by_category = current_raw.get("by_category", {})

    prior = _load_prior("adsb")
    prior_total = prior.get("total_military", 0) if prior else 0
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior("adsb", current_raw)

    if prior is None:
        log.info("adsb: no prior state, recording baseline")
        return None

    delta = compute_event_set(
        source="adsb",
        prior_count=prior_total,
        current_count=current_total,
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        prior_categories=prior.get("by_category") if prior else None,
        current_categories=current_by_category,
        thresholds=thresholds.get("adsb", {}),
    )
    return delta


async def run_opensanctions(thresholds: dict) -> dict | None:
    """Poll OpenSanctions, compute categorical delta on search result counts."""
    from .sources import poll_opensanctions  # noqa: PLC0415
    from .engine import compute_categorical  # noqa: PLC0415

    current_raw = await poll_opensanctions()
    if not current_raw.get("ok"):
        log.error("opensanctions poll failed: %s", current_raw.get("error"))
        return None

    # Build a flat snapshot: total results per search term + cross_jurisdiction count
    searches = current_raw.get("searches", {})
    current_snapshot = {term: data.get("total_results", 0) for term, data in searches.items()}
    current_snapshot["cross_jurisdiction"] = len(current_raw.get("cross_jurisdiction", []))

    prior = _load_prior("opensanctions")
    prior_snapshot = prior.get("snapshot", {}) if prior else {}
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    # Persist the snapshot alongside the raw data for next comparison
    current_raw["snapshot"] = current_snapshot
    _save_prior("opensanctions", current_raw)

    if prior is None or not prior_snapshot:
        log.info("opensanctions: no prior state, recording baseline")
        return None

    delta = compute_categorical(
        source="opensanctions",
        prior_snapshot=prior_snapshot,
        current_snapshot=current_snapshot,
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        thresholds=thresholds.get("opensanctions", {}),
    )
    return delta


async def run_telegram_osint(thresholds: dict) -> dict | None:
    """Poll Telegram OSINT channels, compute event-set delta on urgent message count."""
    from .sources import poll_telegram_osint  # noqa: PLC0415
    from .engine import compute_event_set  # noqa: PLC0415

    current_raw = await poll_telegram_osint()
    if not current_raw.get("ok"):
        log.error("telegram_osint poll failed: %s", current_raw.get("error"))
        return None

    current_urgent = current_raw.get("urgent_messages", 0)

    prior = _load_prior("telegram_osint")
    prior_urgent = prior.get("urgent_messages", 0) if prior else 0
    prior_as_of = prior.get("as_of", current_raw["as_of"]) if prior else current_raw["as_of"]

    _save_prior("telegram_osint", current_raw)

    if prior is None:
        log.info("telegram_osint: no prior state, recording baseline")
        return None

    delta = compute_event_set(
        source="telegram_osint",
        prior_count=prior_urgent,
        current_count=current_urgent,
        prior_as_of=prior_as_of,
        current_as_of=current_raw["as_of"],
        prior_categories=None,
        current_categories=None,
        thresholds=thresholds.get("telegram_osint", {}),
    )
    return delta


def _load_history_for_gdelt(cache_key: str, days: int = 30) -> list[float]:
    """Load historical GDELT article counts from prior_state snapshots.

    Since GDELT prior_state files store article_count, we read them directly.
    """
    counts: list[float] = []
    # We only have one prior snapshot, so history is thin initially.
    # Over time the JSONL history files will accumulate -- read from there.
    from datetime import timedelta  # noqa: PLC0415
    today = datetime.now(timezone.utc)
    source_key = cache_key.replace("gdelt_", "gdelt", 1).split("_")[0]
    for i in range(days):
        day = today - timedelta(days=i)
        date_str = day.strftime("%Y-%m-%d")
        history_path = _HISTORY_DIR / f"{source_key}-{date_str}.jsonl"
        if not history_path.exists():
            continue
        try:
            with open(history_path) as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        val = entry.get("current", {}).get("count")
                        if val is not None:
                            counts.append(float(val))
                    except (json.JSONDecodeError, ValueError, TypeError):
                        continue
        except OSError:
            continue
    return counts


# ---------------------------------------------------------------------------
# Main run orchestration
# ---------------------------------------------------------------------------

async def run_cadence(cadence: str, thresholds: dict) -> list[dict]:
    """Run all sources for a given cadence. Returns list of deltas computed."""
    all_deltas: list[dict] = []

    async def _run_source(coro_fn, *args):
        try:
            result = await coro_fn(*args)
            if result is None:
                return
            if isinstance(result, list):
                all_deltas.extend(result)
            else:
                all_deltas.append(result)
        except Exception as e:
            log.exception("Unhandled error in source run: %s", e)

    tasks = []

    if cadence in ("hot", "all"):
        tasks += [
            _run_source(run_bonbast, thresholds),
            _run_source(run_ooni, thresholds),
            _run_source(run_cloudflare_radar, thresholds),
            _run_source(run_tedpix, thresholds),
            _run_source(run_dolarvzla, thresholds),
            _run_source(run_gdelt, thresholds, "Iran military conflict"),
            _run_source(run_gdelt, thresholds, "Strait Hormuz Iran"),
            _run_source(run_gdelt, thresholds, "Europe energy crisis"),
            _run_source(run_gdelt, thresholds, "Ukraine Russia conflict"),
            _run_source(run_viirs, thresholds, "IR"),
            _run_source(run_prediction_markets, thresholds),
            _run_source(run_acled, thresholds),
            _run_source(run_adsb, thresholds),
            _run_source(run_telegram_osint, thresholds),
        ]

    if cadence in ("warm", "all"):
        tasks += [
            _run_source(run_eia, thresholds, "WCESTUS1"),
            _run_source(run_agsi, thresholds, "DE"),
            _run_source(run_entsog, thresholds),
            _run_source(run_ofac, thresholds),
            _run_source(run_oryx, thresholds, "Russia"),
            _run_source(run_usaspending, thresholds),
            _run_source(run_federal_register, thresholds),
            _run_source(run_congress, thresholds),
            _run_source(run_opensanctions, thresholds),
        ]

    if cadence in ("cold", "all"):
        tasks += [
            _run_source(run_fred, thresholds, "VIXCLS"),
            _run_source(run_fred, thresholds, "T10Y2Y"),
            _run_source(run_fred, thresholds, "DCOILWTICO"),
            _run_source(run_fred, thresholds, "DFF"),
            _run_source(run_ecb, thresholds),
            _run_source(run_comtrade, thresholds),
            _run_source(run_eia_grid, thresholds),
            _run_source(run_fec, thresholds),
            _run_source(run_noaa, thresholds),
        ]

    # Run all with return_exceptions equivalent: gather won't abort on failure
    # (_run_source already catches exceptions)
    await asyncio.gather(*tasks)
    return all_deltas


async def main_async(cadence: str) -> None:
    """Main daemon logic: poll, compute, threshold-check, cluster, write."""
    log.info("=== Signal Dispatch Delta Engine -- cadence=%s ===", cadence)

    thresholds = _load_thresholds()

    # 1. Poll sources and compute deltas
    deltas = await run_cadence(cadence, thresholds)
    log.info("Computed %d deltas", len(deltas))

    # 2. Write current + history for each delta
    for delta in deltas:
        source = delta.get("source", "unknown")
        try:
            _write_current(source, delta)
            _append_history(source, delta)
        except Exception as e:
            log.error("Failed to write delta for %s: %s", source, e)

    # 3. Threshold alerts
    for delta in deltas:
        status = delta.get("threshold_status", "clear")
        if status in ("breached", "watch"):
            source = delta.get("source", "unknown")
            try:
                _write_alert(source, delta)
            except Exception as e:
                log.error("Failed to write alert for %s: %s", source, e)

    # 4. Cluster detection
    try:
        from .clusters import detect_clusters, write_clusters  # noqa: PLC0415
        clusters = detect_clusters(deltas, thresholds)
        if clusters:
            written = write_clusters(clusters, _CLUSTERS_DIR)
            log.info("Detected %d cluster(s), written to %s", len(clusters), written)
            # Write cluster alerts
            for cluster in clusters:
                if cluster.get("status") in ("breached", "watch"):
                    cluster_delta = {
                        "source": f"cluster_{cluster['cluster_id']}",
                        "threshold_status": cluster["status"],
                        "plain_english": cluster["plain_english"],
                        "delta": cluster,
                    }
                    _write_alert(f"cluster_{cluster['cluster_id']}", cluster_delta)
        else:
            log.info("No clusters detected")
    except Exception as e:
        log.error("Cluster detection failed: %s", e)

    log.info("=== Run complete ===")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Signal Dispatch delta engine -- poll sources and compute deltas"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--cadence",
        choices=["hot", "warm", "cold"],
        help="Run sources for this cadence tier",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Run all sources regardless of cadence",
    )
    args = parser.parse_args()

    cadence = "all" if args.all else args.cadence
    asyncio.run(main_async(cadence))


if __name__ == "__main__":
    main()
