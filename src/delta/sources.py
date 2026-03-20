"""Source polling -- uses local adapters from src.adapters.

Each poll_* function fetches raw data from a source and normalizes it into
a shape the delta engine can consume.  All functions are async and return
a dict with at minimum:
  {
    "source": str,
    "as_of": str (ISO),
    "ok": bool,
    "error": str | None,
    ... source-specific fields ...
  }

Import strategy: direct local imports from src.adapters.* package.
Signal Dispatch is now fully self-contained -- no subprocess calls to PM.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Bootstrap: load .env from SD root
# ---------------------------------------------------------------------------

_SD_ROOT = Path(__file__).parent.parent.parent  # signal-dispatch/
load_dotenv(_SD_ROOT / ".env")

# SQLite cache DB stored under data/ in the SD root
_DB_PATH = str(_SD_ROOT / "data" / "ghost_market_cache.db")
(_SD_ROOT / "data").mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ok(source: str, data: dict) -> dict:
    return {"source": source, "as_of": _now_iso(), "ok": True, "error": None, **data}


def _err(source: str, error: str) -> dict:
    return {"source": source, "as_of": _now_iso(), "ok": False, "error": error}


# ---------------------------------------------------------------------------
# Bonbast -- Iranian rial black-market rate (numeric, hot)
# ---------------------------------------------------------------------------

async def poll_bonbast() -> dict:
    """Fetch Bonbast USD/IRR and EUR/IRR rates.

    Returns:
        {
            "usd_irr": float,
            "eur_irr": float,
            "raw_rates": dict,
        }
    """
    try:
        from src.adapters.ghost_market import BonbastAdapter  # noqa: PLC0415
        adapter = BonbastAdapter(_DB_PATH)
        result = await adapter.fetch({})
        await adapter.close()

        rates = result.get("rates", {})
        usd_irr = rates.get("USD", {}).get("rate")
        eur_irr = rates.get("EUR", {}).get("rate")
        return _ok("bonbast", {
            "usd_irr": usd_irr,
            "eur_irr": eur_irr,
            "raw_rates": rates,
        })
    except Exception as e:
        return _err("bonbast", str(e))


# ---------------------------------------------------------------------------
# FRED -- macro economic indicators (numeric, cold)
# ---------------------------------------------------------------------------

FRED_SERIES_TRACKED = {
    "T10Y2Y": "10Y-2Y Treasury spread (yield curve)",
    "VIXCLS": "CBOE VIX (market volatility)",
    "DFF": "Fed Funds Rate (effective)",
    "DCOILWTICO": "WTI Crude Oil price",
    "CPIAUCSL": "Consumer Price Index (all urban consumers)",
    "PAYEMS": "Nonfarm payrolls",
    "UNRATE": "Unemployment rate",
}


async def poll_fred(series_id: str = "VIXCLS") -> dict:
    """Fetch the latest observation for a FRED series.

    Args:
        series_id: FRED series ID. Default: VIXCLS (VIX).

    Returns:
        {
            "series_id": str,
            "series_label": str,
            "latest_value": float,
            "latest_date": str,
            "observations": list[dict],  # last 60 obs for context
        }
    """
    try:
        from src.adapters import FredAdapter  # noqa: PLC0415
        adapter = FredAdapter(_DB_PATH)
        result = await adapter.fetch({"series_id": series_id})
        await adapter.close()

        observations = result.get("observations", [])
        recent = observations[-60:] if len(observations) > 60 else observations
        latest = recent[-1] if recent else None
        return _ok("fred", {
            "series_id": series_id,
            "series_label": FRED_SERIES_TRACKED.get(series_id, series_id),
            "latest_value": latest["value"] if latest else None,
            "latest_date": latest["date"] if latest else None,
            "observations": recent,
        })
    except Exception as e:
        return _err("fred", str(e))


# ---------------------------------------------------------------------------
# EIA -- US petroleum inventory (numeric, warm)
# ---------------------------------------------------------------------------

async def poll_eia(series_id: str = "WCESTUS1") -> dict:
    """Fetch EIA weekly petroleum series.

    Default: WCESTUS1 (US crude oil ending stocks).

    Returns:
        {
            "series_id": str,
            "series_title": str,
            "latest_value": float,
            "latest_period": str,
            "observations": list[dict],
        }
    """
    try:
        from src.adapters.ghost_market import EiaAdapter  # noqa: PLC0415
        adapter = EiaAdapter(_DB_PATH)
        result = await adapter.fetch({"series_id": series_id, "weeks": 52})
        await adapter.close()

        obs = result.get("observations", [])
        # EIA returns desc; adapter may have already sorted -- use last entry
        latest = obs[-1] if obs else None
        return _ok("eia", {
            "series_id": series_id,
            "series_title": result.get("title", series_id),
            "latest_value": latest["value"] if latest else None,
            "latest_period": latest.get("period", latest.get("date", "")) if latest else None,
            "observations": obs,
        })
    except Exception as e:
        return _err("eia", str(e))


# ---------------------------------------------------------------------------
# AGSI -- European gas storage (numeric, warm)
# ---------------------------------------------------------------------------

async def poll_agsi(country: str = "DE") -> dict:
    """Fetch AGSI gas storage data for a country.

    Default: DE (Germany, largest European storage player).

    Returns:
        {
            "country": str,
            "latest_full_pct": float,
            "latest_gas_day": str,
            "latest_withdrawal": float,
            "storage_data": list[dict],
        }
    """
    try:
        from src.adapters.ghost_market import AgsiAdapter  # noqa: PLC0415
        adapter = AgsiAdapter(_DB_PATH)
        result = await adapter.fetch({"country": country, "size": 30, "days": 30})
        await adapter.close()

        storage = result.get("storage_data", [])
        latest = storage[-1] if storage else None
        return _ok("agsi", {
            "country": country,
            "latest_full_pct": latest.get("full_pct") if latest else None,
            "latest_gas_day": latest.get("gas_day") if latest else None,
            "latest_withdrawal": latest.get("withdrawal") if latest else None,
            "storage_data": storage,
        })
    except Exception as e:
        return _err("agsi", str(e))


# ---------------------------------------------------------------------------
# Prediction markets -- Kalshi YES prices (numeric, hot)
# ---------------------------------------------------------------------------

KALSHI_MARKETS_TRACKED = [
    "KXCLOSEHORMUZ",      # Strait of Hormuz closure
    "KXUSAIRANAGREEMENT", # US-Iran nuclear deal
    "KXIRANISR",          # Iran-Israel military conflict
]


async def poll_prediction_markets(tickers: list[str] | None = None) -> dict:
    """Fetch current YES prices for tracked Kalshi markets.

    Requires KALSHI_KEY_ID and KALSHI_PRIVATE_KEY_PATH environment variables.
    Falls back gracefully if auth missing.

    Returns:
        {
            "markets": {
                "<ticker>": {
                    "ticker": str,
                    "title": str,
                    "yes_price": float,  # 0.0-1.0 midpoint
                    "volume": float,
                    "status": str,
                }
            }
        }
    """
    tickers = tickers or KALSHI_MARKETS_TRACKED
    key_id = os.environ.get("KALSHI_KEY_ID")
    key_path = os.environ.get("KALSHI_PRIVATE_KEY_PATH")

    if not key_id or not key_path:
        return _err("prediction_markets", "KALSHI_KEY_ID or KALSHI_PRIVATE_KEY_PATH not set")

    try:
        from src.adapters import KalshiAdapter  # noqa: PLC0415
        adapter = KalshiAdapter(_DB_PATH)
        result = await adapter.fetch({"tickers": tickers})
        await adapter.close()

        markets: dict[str, Any] = {}
        for ticker, market_data in result.get("markets", {}).items():
            markets[ticker] = {
                "ticker": ticker,
                "title": market_data.get("title", ticker),
                "yes_price": market_data.get("yes_price"),
                "volume": market_data.get("volume"),
                "status": market_data.get("status", "unknown"),
            }
            if market_data.get("error"):
                markets[ticker]["error"] = market_data["error"]

        return _ok("prediction_markets", {"markets": markets})
    except Exception as e:
        return _err("prediction_markets", str(e))


# ---------------------------------------------------------------------------
# OONI -- Iran internet censorship (binary/state, hot)
# ---------------------------------------------------------------------------

async def poll_ooni(probe_cc: str = "IR", days: int = 7) -> dict:
    """Fetch OONI censorship measurements for a country.

    Returns:
        {
            "country": str,
            "anomaly_rate": float,
            "measurement_count": int,
            "anomaly_count": int,
            "new_blocked_endpoints": int,
            "active_incidents": list[dict],
            "measurements": list[dict],
        }
    """
    try:
        from src.adapters.ghost_market import OoniAdapter  # noqa: PLC0415
        adapter = OoniAdapter(_DB_PATH)
        result = await adapter.fetch({"probe_cc": probe_cc, "days": days})
        await adapter.close()

        measurements = result.get("measurements", [])
        total_meas = sum(m.get("measurement_count", 0) for m in measurements)
        total_anom = sum(m.get("anomaly_count", 0) for m in measurements)

        # Approximate new blocked endpoints: confirmed_count delta in last 24h
        new_blocked = 0
        if len(measurements) >= 2:
            today_conf = measurements[-1].get("confirmed_count", 0)
            yesterday_conf = measurements[-2].get("confirmed_count", 0)
            new_blocked = max(0, today_conf - yesterday_conf)

        return _ok("ooni", {
            "country": probe_cc,
            "anomaly_rate": result.get("anomaly_rate", 0.0),
            "measurement_count": total_meas,
            "anomaly_count": total_anom,
            "new_blocked_endpoints": new_blocked,
            "active_incidents": result.get("incidents", []),
            "measurements": measurements,
        })
    except Exception as e:
        return _err("ooni", str(e))


# ---------------------------------------------------------------------------
# GDELT -- global event monitoring (event_set, hot)
# ---------------------------------------------------------------------------

GDELT_QUERIES = {
    "iran_conflict": "Iran military conflict",
    "hormuz": "Strait Hormuz Iran",
    "europe_energy": "Europe gas energy crisis",
    "ukraine": "Ukraine Russia conflict",
}


async def poll_gdelt(query: str = "Iran military conflict", timespan: str = "1d") -> dict:
    """Fetch GDELT article count for a query.

    Returns:
        {
            "query": str,
            "timespan": str,
            "article_count": int,
            "articles": list[dict],
        }
    """
    try:
        from src.adapters.ghost_market import GdeltAdapter  # noqa: PLC0415
        adapter = GdeltAdapter(_DB_PATH)
        result = await adapter.fetch({"query": query, "maxrecords": 50, "timespan": timespan})
        await adapter.close()

        return _ok("gdelt", {
            "query": query,
            "timespan": timespan,
            "article_count": result.get("article_count", 0),
            "articles": result.get("articles", []),
        })
    except Exception as e:
        return _err("gdelt", str(e))


# ---------------------------------------------------------------------------
# Cloudflare Radar -- Iran internet traffic (numeric + binary, hot)
# ---------------------------------------------------------------------------

async def poll_cloudflare_radar(location: str = "IR", endpoint: str = "anomalies") -> dict:
    """Fetch Cloudflare Radar internet traffic anomalies for a location.

    Returns:
        {
            "location": str,
            "endpoint": str,
            "anomalies": list[dict],
            "anomaly_count": int,
        }
    """
    try:
        from src.adapters.ghost_market import CloudflareRadarAdapter  # noqa: PLC0415
        adapter = CloudflareRadarAdapter(_DB_PATH)
        result = await adapter.fetch({"location": location, "endpoint": endpoint})
        await adapter.close()

        anomalies = result.get("anomalies", result.get("data", []))
        return _ok("cloudflare_radar", {
            "location": location,
            "endpoint": endpoint,
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
        })
    except Exception as e:
        return _err("cloudflare_radar", str(e))


# ---------------------------------------------------------------------------
# TedPIX -- Tehran Stock Exchange (numeric, hot)
# ---------------------------------------------------------------------------

async def poll_tedpix() -> dict:
    """Fetch Tehran Stock Exchange TEDPIX index.

    Returns:
        {
            "tedpix": float,
            "change_pct": float | None,
        }
    """
    try:
        from src.adapters.ghost_market import TedpixAdapter  # noqa: PLC0415
        adapter = TedpixAdapter(_DB_PATH)
        result = await adapter.fetch({})
        await adapter.close()

        return _ok("tedpix", {
            "tedpix": result.get("tedpix") or result.get("value"),
            "change_pct": result.get("change_pct") or result.get("change"),
        })
    except Exception as e:
        return _err("tedpix", str(e))


# ---------------------------------------------------------------------------
# DolarVzla -- Venezuelan bolivar black market rate (numeric, hot)
# ---------------------------------------------------------------------------

async def poll_dolarvzla() -> dict:
    """Fetch Venezuelan bolivar black market exchange rate.

    Returns:
        {
            "usd_ves": float,  # USD per VES from first monitor with a sell rate
        }
    """
    try:
        from src.adapters.ghost_market import DolarVzlaAdapter  # noqa: PLC0415
        adapter = DolarVzlaAdapter(_DB_PATH)
        result = await adapter.fetch({})
        await adapter.close()

        # Adapter returns {"rates": [{"name": str, "buy": float|None, "sell": float|None, "average": float|None, ...}, ...]}
        # Prefer "paralelo" (parallel/black market rate), fall back to "oficial" or first with a value
        rates = result.get("rates", [])
        usd_ves = None
        for preferred_name in ("paralelo", "enparalelovzla", "oficial"):
            for rate_entry in rates:
                if rate_entry.get("name", "").lower() == preferred_name:
                    val = rate_entry.get("sell") or rate_entry.get("average") or rate_entry.get("buy")
                    if val and val > 0:
                        usd_ves = float(val)
                        break
            if usd_ves is not None:
                break
        if usd_ves is None:
            # Last resort: any non-zero rate
            for rate_entry in rates:
                val = rate_entry.get("sell") or rate_entry.get("average") or rate_entry.get("buy")
                if val and val > 0:
                    usd_ves = float(val)
                    break

        return _ok("dolarvzla", {
            "usd_ves": usd_ves,
            "rates": rates,
        })
    except Exception as e:
        return _err("dolarvzla", str(e))


# ---------------------------------------------------------------------------
# VIIRS -- fire hotspot detection (event_set, hot)
# ---------------------------------------------------------------------------

async def poll_viirs(country: str = "IR", days: int = 1) -> dict:
    """Fetch NASA FIRMS VIIRS fire hotspots for a country.

    Returns:
        {
            "country": str,
            "hotspot_count": int,
            "hotspots": list[dict],
        }
    """
    try:
        from src.adapters.ghost_market import ViirsAdapter  # noqa: PLC0415
        adapter = ViirsAdapter(_DB_PATH)
        result = await adapter.fetch({"country": country, "days": days})
        await adapter.close()

        hotspots = result.get("hotspots", [])
        return _ok("viirs", {
            "country": country,
            "hotspot_count": len(hotspots),
            "hotspots": hotspots,
        })
    except Exception as e:
        return _err("viirs", str(e))


# ---------------------------------------------------------------------------
# ENTSOG -- European natural gas pipeline flows (numeric, warm)
# ---------------------------------------------------------------------------

async def poll_entsog(country: str = "DE") -> dict:
    """Fetch ENTSOG European gas pipeline flow data.

    Default: DE (Germany, main European gas hub).

    Returns:
        {
            "country": str,
            "flows": list[dict],
            "flow_count": int,
        }
    """
    try:
        from src.adapters.ghost_market import EntsogAdapter  # noqa: PLC0415
        adapter = EntsogAdapter(_DB_PATH)
        result = await adapter.fetch({"country": country, "days": 7, "limit": 20})
        await adapter.close()

        flows = result.get("flows", result.get("data", []))
        return _ok("entsog", {
            "country": country,
            "flows": flows,
            "flow_count": len(flows),
        })
    except Exception as e:
        return _err("entsog", str(e))


# ---------------------------------------------------------------------------
# OFAC -- US Treasury sanctions list (categorical, warm)
# ---------------------------------------------------------------------------

async def poll_ofac(filter_term: str = "IRAN") -> dict:
    """Fetch OFAC SDN list entries matching filter.

    Returns:
        {
            "filter": str,
            "entity_count": int,
            "snapshot": list[dict],
            "new_entries": list[dict],
        }
    """
    try:
        from src.adapters.ghost_market import OfacAdapter  # noqa: PLC0415
        adapter = OfacAdapter(_DB_PATH)
        result = await adapter.fetch({"filter": filter_term})
        await adapter.close()

        snapshot = result.get("snapshot", [])
        return _ok("ofac", {
            "filter": filter_term,
            "entity_count": len(snapshot),
            "snapshot": snapshot,
            "new_entries": result.get("new_entries", []),
        })
    except Exception as e:
        return _err("ofac", str(e))


# ---------------------------------------------------------------------------
# Oryx -- equipment loss tracking (event_set, warm)
# ---------------------------------------------------------------------------

async def poll_oryx(country: str = "Russia") -> dict:
    """Fetch Oryx equipment loss data for a country.

    The adapter returns a list of per-equipment-type records plus an "All Types"
    aggregate row.  We extract totals from the aggregate row (or sum leaf records
    as a fallback) since the adapter does not expose a top-level total_losses key.

    Returns:
        {
            "country": str,
            "total_losses": int,
            "destroyed": int,
            "captured": int,
            "abandoned": int,
            "damaged": int,
            "equipment": list[dict],
        }
    """
    try:
        from src.adapters.ghost_market import OryxAdapter  # noqa: PLC0415
        adapter = OryxAdapter(_DB_PATH)
        result = await adapter.fetch({"country": country})
        await adapter.close()

        equipment = result.get("equipment", [])

        # Prefer the "All Types" aggregate row that Oryx includes
        all_types_row = next(
            (r for r in equipment if r.get("equipment_type", "").strip() == "All Types"),
            None,
        )

        if all_types_row:
            destroyed = all_types_row.get("destroyed", 0)
            captured = all_types_row.get("captured", 0)
            abandoned = all_types_row.get("abandoned", 0)
            damaged = all_types_row.get("damaged", 0)
        else:
            # Fallback: sum leaf rows (exclude sub-aggregate rows that embed
            # their totals in the equipment_type string)
            leaf_rows = [
                r for r in equipment
                if not any(
                    kw in r.get("equipment_type", "")
                    for kw in ("Losses excluding", "Losses of Armoured")
                )
            ]
            destroyed = sum(r.get("destroyed", 0) for r in leaf_rows)
            captured = sum(r.get("captured", 0) for r in leaf_rows)
            abandoned = sum(r.get("abandoned", 0) for r in leaf_rows)
            damaged = sum(r.get("damaged", 0) for r in leaf_rows)

        total_losses = destroyed + captured + abandoned + damaged

        return _ok("oryx", {
            "country": country,
            "total_losses": total_losses,
            "destroyed": destroyed,
            "captured": captured,
            "abandoned": abandoned,
            "damaged": damaged,
            "equipment": equipment,
        })
    except Exception as e:
        return _err("oryx", str(e))


# ---------------------------------------------------------------------------
# USASpending -- US federal contracting (composite, warm -- stub)
# ---------------------------------------------------------------------------

async def poll_usaspending(agency: str = "DoD") -> dict:
    """Fetch USASpending federal contract data. Composite delta -- stubbed."""
    try:
        from src.adapters.ghost_market import UsaSpendingAdapter  # noqa: PLC0415
        adapter = UsaSpendingAdapter(_DB_PATH)
        result = await adapter.fetch({"agency": agency})
        await adapter.close()

        return _ok("usaspending", {
            "agency": agency,
            "data": result,
        })
    except Exception as e:
        return _err("usaspending", str(e))


# ---------------------------------------------------------------------------
# Federal Register -- US regulatory filings (categorical, warm)
# ---------------------------------------------------------------------------

async def poll_federal_register(query: str = "Iran sanctions") -> dict:
    """Fetch Federal Register entries matching query via direct API call.

    The OSINT adapter class uses PM-specific market_data interface.
    We call the Federal Register REST API directly.

    Returns:
        {
            "query": str,
            "entry_count": int,
            "entries": list[dict],
        }
    """
    from datetime import timedelta  # noqa: PLC0415
    try:
        import httpx  # noqa: PLC0415
        since_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        params = {
            "conditions[term]": query,
            "conditions[publication_date][gte]": since_date,
            "per_page": 20,
            "page": 1,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.federalregister.gov/api/v1/documents.json",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        entries = [
            {
                "document_number": doc.get("document_number"),
                "title": doc.get("title"),
                "type": doc.get("type"),
                "publication_date": doc.get("publication_date"),
                "agencies": [a.get("name") for a in doc.get("agencies", [])],
                "html_url": doc.get("html_url"),
            }
            for doc in data.get("results", [])
        ]

        return _ok("federal_register", {
            "query": query,
            "entry_count": len(entries),
            "entries": entries,
        })
    except Exception as e:
        return _err("federal_register", str(e))


# ---------------------------------------------------------------------------
# Congress -- US legislative activity (categorical, warm)
# ---------------------------------------------------------------------------

async def poll_congress(query: str = "Iran", limit: int = 20) -> dict:
    """Fetch recent Congress.gov bills via direct API call.

    The OSINT adapter uses PM-specific market_data interface.
    We call the Congress.gov API directly.

    Returns:
        {
            "query": str,
            "bill_count": int,
            "bills": list[dict],
        }
    """
    try:
        import httpx  # noqa: PLC0415
        api_key = os.environ.get("CONGRESS_API_KEY")
        if not api_key:
            return _err("congress", "CONGRESS_API_KEY not set")

        params = {
            "format": "json",
            "limit": limit,
            "api_key": api_key,
            "sort": "updateDate+desc",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.congress.gov/v3/bill/119",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        bills_raw = data.get("bills", [])
        # Client-side filter for Iran-relevant bills
        query_lower = query.lower()
        bills = []
        for bill in bills_raw:
            title = (bill.get("title") or "").lower()
            if query_lower in title:
                bills.append({
                    "number": bill.get("number"),
                    "type": bill.get("type"),
                    "congress": bill.get("congress"),
                    "title": bill.get("title"),
                    "update_date": bill.get("updateDate"),
                    "origin_chamber": bill.get("originChamber"),
                })

        return _ok("congress", {
            "query": query,
            "bill_count": len(bills),
            "bills": bills,
        })
    except Exception as e:
        return _err("congress", str(e))


# ---------------------------------------------------------------------------
# FEC -- Federal Election Commission (composite, cold -- stub)
# ---------------------------------------------------------------------------

async def poll_fec(query: str = "defense") -> dict:
    """Fetch FEC campaign finance committee totals. Composite delta -- stubbed.

    Returns basic committee search results for the query term.
    """
    try:
        import httpx  # noqa: PLC0415
        api_key = os.environ.get("FEC_API_KEY")
        if not api_key:
            return _err("fec", "FEC_API_KEY not set")

        params = {
            "q": query,
            "api_key": api_key,
            "per_page": 20,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.open.fec.gov/v1/committees/",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        committees = data.get("results", [])
        return _ok("fec", {
            "query": query,
            "committee_count": len(committees),
            "data": committees[:5],  # Trim for storage
        })
    except Exception as e:
        return _err("fec", str(e))


# ---------------------------------------------------------------------------
# ECB -- European Central Bank rates (numeric + categorical, cold)
# ---------------------------------------------------------------------------

async def poll_ecb(
    flow_ref: str = "EXR",
    key: str = "D.USD.EUR.SP00.A",
) -> dict:
    """Fetch ECB data series.

    Default: EUR/USD daily exchange rate.

    Args:
        flow_ref: ECB SDW dataset ID (e.g., "EXR" for exchange rates)
        key: SDMX dimension key (e.g., "D.USD.EUR.SP00.A")

    Returns:
        {
            "flow_ref": str,
            "key": str,
            "latest_value": float | None,
            "latest_date": str | None,
            "observations": list[dict],
        }
    """
    try:
        from src.adapters.ghost_market import EcbAdapter  # noqa: PLC0415
        adapter = EcbAdapter(_DB_PATH)
        result = await adapter.fetch({"flow_ref": flow_ref, "key": key})
        await adapter.close()

        observations = result.get("observations", [])
        latest = observations[-1] if observations else None
        return _ok("ecb", {
            "flow_ref": flow_ref,
            "key": key,
            "latest_value": latest.get("value") if latest else None,
            "latest_date": latest.get("date") if latest else None,
            "observations": observations,
        })
    except Exception as e:
        return _err("ecb", str(e))


# ---------------------------------------------------------------------------
# Comtrade -- UN international trade statistics (composite, cold -- stub)
# ---------------------------------------------------------------------------

async def poll_comtrade(reporter: str = "IR", partner: str = "CN") -> dict:
    """Fetch UN Comtrade trade data. Composite delta -- stubbed.

    Default: Iran (IR) to China (CN) crude petroleum trade.
    Adapter accepts ISO-2 country codes and maps to M49 internally.
    """
    try:
        from src.adapters.ghost_market import ComtradeAdapter  # noqa: PLC0415
        adapter = ComtradeAdapter(_DB_PATH)
        result = await adapter.fetch({
            "reporter": reporter,
            "partner": partner,
            "commodity": "2709",  # Crude petroleum
            "flow": "X",         # Exports
        })
        await adapter.close()

        return _ok("comtrade", {
            "reporter": reporter,
            "partner": partner,
            "data": result,
        })
    except Exception as e:
        return _err("comtrade", str(e))


# ---------------------------------------------------------------------------
# EIA Grid -- US electricity grid data (numeric, cold)
# ---------------------------------------------------------------------------

async def poll_eia_grid(respondent: str = "US48", data_type: str = "D") -> dict:
    """Fetch EIA grid electricity data.

    Default: US 48-state demand.

    Args:
        respondent: Region code (default "US48")
        data_type: "D" for demand, "NG" for net generation (default "D")

    Returns:
        {
            "respondent": str,
            "data_type": str,
            "latest_value": float | None,
            "grid_data": list[dict],
        }
    """
    try:
        from src.adapters.ghost_market import EiaGridAdapter  # noqa: PLC0415
        adapter = EiaGridAdapter(_DB_PATH)
        result = await adapter.fetch({
            "respondent": respondent,
            "type": data_type,
            "frequency": "daily",
            "length": 14,
        })
        await adapter.close()

        # Adapter returns data under "grid_data" key
        grid_data = result.get("grid_data", [])
        # grid_data is sorted desc; get most recent non-None
        latest_value = None
        for entry in grid_data:
            if entry.get("value") is not None:
                latest_value = float(entry["value"])
                break

        return _ok("eia_grid", {
            "respondent": respondent,
            "data_type": data_type,
            "latest_value": latest_value,
            "grid_data": grid_data,
        })
    except Exception as e:
        return _err("eia_grid", str(e))


# ---------------------------------------------------------------------------
# NOAA -- weather data (numeric + event_set, cold)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# ACLED -- armed conflict event data (event_set, hot)
# ---------------------------------------------------------------------------

async def poll_acled() -> dict:
    """Fetch ACLED conflict events for the past 7 days.

    Returns:
        {
            "total_events": int,
            "total_fatalities": int,
            "by_region": dict,
            "by_country": dict,
            "top_events": list[dict],
        }
    """
    try:
        from src.adapters.acled import AcledAdapter  # noqa: PLC0415
        adapter = AcledAdapter(_DB_PATH)
        result = await adapter.fetch({})
        await adapter.close()

        return _ok("acled", {
            "total_events": result.get("total_events", 0),
            "total_fatalities": result.get("total_fatalities", 0),
            "by_region": result.get("by_region", {}),
            "by_country": result.get("by_country", {}),
            "top_events": result.get("top_events", []),
        })
    except Exception as e:
        return _err("acled", str(e))


# ---------------------------------------------------------------------------
# ADS-B -- military flight tracking (event_set + numeric, hot)
# ---------------------------------------------------------------------------

async def poll_adsb() -> dict:
    """Fetch current military aircraft snapshot from ADS-B Exchange.

    Returns:
        {
            "total_military": int,
            "by_category": dict[str, int],
            "notable": list[dict],
        }
    """
    try:
        from src.adapters.adsb import AdsbAdapter  # noqa: PLC0415
        adapter = AdsbAdapter(_DB_PATH)
        result = await adapter.fetch({})
        await adapter.close()

        return _ok("adsb", {
            "total_military": result.get("total_military", 0),
            "by_category": result.get("by_category", {}),
            "notable": result.get("notable", []),
        })
    except Exception as e:
        return _err("adsb", str(e))


# ---------------------------------------------------------------------------
# OpenSanctions -- multi-jurisdiction sanctions (categorical, warm)
# ---------------------------------------------------------------------------

async def poll_opensanctions(search_terms: list[str] | None = None) -> dict:
    """Fetch OpenSanctions multi-jurisdiction entity data.

    Args:
        search_terms: Override default search terms (Iran, Russia, Wagner, Houthis).

    Returns:
        {
            "dataset": {"entity_count": int, "last_updated": str},
            "searches": dict[str, {"total_results": int, "entities": list}],
            "cross_jurisdiction": list[dict],
        }
    """
    try:
        from src.adapters.opensanctions import OpenSanctionsAdapter  # noqa: PLC0415
        adapter = OpenSanctionsAdapter(_DB_PATH, search_terms=search_terms)
        query = {}
        if search_terms:
            query["search_terms"] = search_terms
        result = await adapter.fetch(query)
        await adapter.close()

        return _ok("opensanctions", {
            "dataset": result.get("dataset", {}),
            "searches": result.get("searches", {}),
            "cross_jurisdiction": result.get("cross_jurisdiction", []),
        })
    except Exception as e:
        return _err("opensanctions", str(e))


# ---------------------------------------------------------------------------
# Telegram OSINT -- conflict channel scraping (event_set, hot)
# ---------------------------------------------------------------------------

async def poll_telegram_osint() -> dict:
    """Scrape public Telegram OSINT channels for conflict signals.

    Note: TelegramOsintAdapter.fetch() takes no query dict -- it scrapes
    all configured channels and returns aggregated signal data.

    Returns:
        {
            "total_messages": int,
            "urgent_messages": int,
            "channels": dict,
            "urgency_summary": dict,
        }
    """
    try:
        from src.adapters.telegram_osint import TelegramOsintAdapter  # noqa: PLC0415
        adapter = TelegramOsintAdapter()
        result = await adapter.fetch()

        return _ok("telegram_osint", {
            "total_messages": result.get("total_messages", 0),
            "urgent_messages": result.get("urgent_messages", 0),
            "channels": result.get("channels", {}),
            "urgency_summary": result.get("urgency_summary", {}),
        })
    except Exception as e:
        return _err("telegram_osint", str(e))


async def poll_noaa(query_type: str = "forecast", city: str = "nyc", state: str = "NY") -> dict:
    """Fetch NOAA weather forecast or active alerts.

    Returns:
        For forecast: {"city": str, "forecast_time": str, "periods": list[dict]}
        For alerts: {"state": str, "alerts": list[dict], "alert_count": int}
    """
    try:
        from src.adapters import NoaaAdapter  # noqa: PLC0415
        adapter = NoaaAdapter(_DB_PATH)
        if query_type == "forecast":
            result = await adapter.fetch({"type": "forecast", "city": city})
        else:
            result = await adapter.fetch({"type": "alerts", "state": state})
        await adapter.close()

        return _ok("noaa", result)
    except Exception as e:
        return _err("noaa", str(e))


# ---------------------------------------------------------------------------
# WHO Disease Outbreak News -- pandemic/epidemic signals (event_set, warm)
# ---------------------------------------------------------------------------

async def poll_who_outbreaks() -> dict:
    """Fetch WHO Disease Outbreak News active notices.

    Signal: Disease outbreaks → supply chain disruption, labor market impact,
    commodity demand shifts, travel/trade route closure risk.

    Returns:
        {
            "active_notices": list[dict],
            "notice_count": int,
            "fetched_at": str,
        }
    """
    try:
        from src.adapters.ghost_market.who_outbreaks import WhoOutbreaksAdapter  # noqa: PLC0415
        adapter = WhoOutbreaksAdapter(_DB_PATH)
        result = await adapter.fetch({})
        await adapter.close()

        return _ok("who_outbreaks", {
            "active_notices": result.get("active_notices", []),
            "notice_count": result.get("notice_count", 0),
            "fetched_at": result.get("fetched_at", ""),
        })
    except Exception as e:
        return _err("who_outbreaks", str(e))


# ---------------------------------------------------------------------------
# ReliefWeb -- UN humanitarian crises (event_set, warm)
# ---------------------------------------------------------------------------

async def poll_reliefweb() -> dict:
    """Fetch ReliefWeb ongoing humanitarian disasters and crises.

    Signal: Active UN-declared disasters → geopolitical disruption indicators,
    commodity/market impact precursors.

    Returns:
        {
            "active_disasters": list[dict],
            "disaster_count": int,
            "fetched_at": str,
        }
    """
    try:
        from src.adapters.ghost_market.reliefweb import ReliefWebAdapter  # noqa: PLC0415
        adapter = ReliefWebAdapter(_DB_PATH)
        result = await adapter.fetch({})
        await adapter.close()

        return _ok("reliefweb", {
            "active_disasters": result.get("active_disasters", []),
            "disaster_count": result.get("disaster_count", 0),
            "fetched_at": result.get("fetched_at", ""),
        })
    except Exception as e:
        return _err("reliefweb", str(e))


# ---------------------------------------------------------------------------
# OpenSky -- civilian airspace monitoring (snapshot, hot)
# ---------------------------------------------------------------------------

async def poll_opensky() -> dict:
    """Fetch OpenSky civilian flight density across 6 strategic regions.

    Signal: Civilian traffic drops = airspace closure = escalation indicator.
    Regions: Taiwan Strait, Persian Gulf, Black Sea, Red Sea,
             South China Sea, Eastern Mediterranean.

    Returns:
        {
            "regions": dict[str, {"aircraft_count": int, "by_country": dict, "no_callsign": int}],
            "snapshot_at": str,
        }
    """
    try:
        from src.adapters.ghost_market.opensky import OpenSkyAdapter  # noqa: PLC0415
        adapter = OpenSkyAdapter(_DB_PATH)
        result = await adapter.fetch({})
        await adapter.close()

        return _ok("opensky", {
            "regions": result.get("regions", {}),
            "snapshot_at": result.get("snapshot_at", ""),
        })
    except Exception as e:
        return _err("opensky", str(e))
