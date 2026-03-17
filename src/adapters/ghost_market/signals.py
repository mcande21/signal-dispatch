"""Ghost Market signal orchestration -- thin utility layer.

Provides data access utilities for agents. Agents read market_config.json
for market-source mappings and use these functions to fetch raw data.
Signal interpretation, normalization, and synthesis are agent responsibilities.
"""

import json
from pathlib import Path
from typing import Any

from .agsi import AgsiAdapter
from .bonbast import BonbastAdapter
from .cloudflare_radar import CloudflareRadarAdapter
from .comtrade import ComtradeAdapter
from .dolarvzla import DolarVzlaAdapter
from .ecb import EcbAdapter
from .eia import EiaAdapter
from .eia_grid import EiaGridAdapter
from .entsog import EntsogAdapter
from .gdelt import GdeltAdapter
from .ofac import OfacAdapter
from .ooni import OoniAdapter
from .oryx import OryxAdapter
from .tedpix import TedpixAdapter
from .usaspending import UsaSpendingAdapter
from .viirs import ViirsAdapter

# Adapter registry - mechanical class lookup by name
ADAPTER_CLASSES = {
    "agsi": AgsiAdapter,
    "bonbast": BonbastAdapter,
    "cloudflare_radar": CloudflareRadarAdapter,
    "comtrade": ComtradeAdapter,
    "dolarvzla": DolarVzlaAdapter,
    "ecb": EcbAdapter,
    "eia": EiaAdapter,
    "eia_grid": EiaGridAdapter,
    "entsog": EntsogAdapter,
    "gdelt": GdeltAdapter,
    "ofac": OfacAdapter,
    "ooni": OoniAdapter,
    "oryx": OryxAdapter,
    "tedpix": TedpixAdapter,
    "usaspending": UsaSpendingAdapter,
    "viirs": ViirsAdapter,
}


def load_market_config() -> dict:
    """Load market-to-source mappings from JSON config."""
    config_path = Path(__file__).parent / "market_config.json"
    with open(config_path) as f:
        return json.load(f)


def list_sources() -> list[str]:
    """List available data source names."""
    return list(ADAPTER_CLASSES.keys())


def list_markets() -> list[str]:
    """List mapped market tickers from config."""
    config = load_market_config()
    return list(config.get("markets", {}).keys())


def get_market_sources(market: str) -> dict:
    """Get source mappings for a specific market from config.

    Returns the sources dict with weights and rationales.
    """
    config = load_market_config()
    market_data = config.get("markets", {}).get(market)
    if not market_data:
        return {}
    return market_data.get("sources", {})


async def fetch_source(
    source_name: str,
    db_path: str,
    query: dict | None = None
) -> dict:
    """Fetch raw data from a single source adapter.

    Args:
        source_name: Name of the source (e.g., 'eia', 'bonbast')
        db_path: Path to SQLite cache database
        query: Optional query parameters for the adapter's fetch() method

    Returns:
        Raw data dict from the adapter's fetch() method
    """
    adapter_cls = ADAPTER_CLASSES.get(source_name)
    if not adapter_cls:
        raise ValueError(f"Unknown source: {source_name}. Available: {list_sources()}")

    adapter = adapter_cls(db_path=db_path)
    try:
        result = await adapter.fetch(query=query or {})
        return result
    finally:
        await adapter.close()


async def fetch_market_sources(
    market: str,
    db_path: str
) -> dict[str, Any]:
    """Fetch raw data from all sources relevant to a market.

    Reads market_config.json to determine which sources to query,
    fetches raw data from each. Returns raw results -- no normalization,
    no weighting, no composite scoring. Agents interpret the data.

    Args:
        market: Market ticker (e.g., 'KXCLOSEHORMUZ')
        db_path: Path to SQLite cache database

    Returns:
        Dict mapping source_name -> {config: {weight, rationale}, data: raw_fetch_result}
        Sources that fail are included with data=None and an error field.
    """
    sources = get_market_sources(market)
    if not sources:
        raise ValueError(f"Unknown market: {market}. Available: {list_markets()}")

    results = {}
    for source_name, source_config in sources.items():
        try:
            query = source_config.get("default_query", {})
            data = await fetch_source(source_name, db_path, query=query)
            results[source_name] = {
                "config": source_config,
                "data": data,
                "error": None
            }
        except Exception as e:
            results[source_name] = {
                "config": source_config,
                "data": None,
                "error": str(e)
            }

    return results
