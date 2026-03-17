"""FRED (Federal Reserve Economic Data) API adapter.

Standalone version for Signal Dispatch -- no Database dependency.
Uses SQLite cache directly via aiosqlite (same pattern as ghost_market adapters).

Source: https://api.stlouisfed.org/fred
Auth: FRED_API_KEY env var
TTL: 24h (data updates daily at most)
"""

import os
from datetime import datetime, timezone

import httpx

from .base import GhostMarketAdapter, GhostMarketApiError


# FRED API base URL
FRED_API_BASE = "https://api.stlouisfed.org/fred"

# Series IDs tracked for delta purposes
FRED_SERIES = {
    "T10Y2Y": "10Y-2Y Treasury spread (yield curve)",
    "VIXCLS": "CBOE VIX (market volatility)",
    "DFF": "Fed Funds Rate (effective)",
    "DCOILWTICO": "WTI Crude Oil price",
    "CPIAUCSL": "Consumer Price Index (all urban consumers)",
    "PAYEMS": "Nonfarm payrolls",
    "UNRATE": "Unemployment rate",
}


class FredAdapter(GhostMarketAdapter):
    """FRED API adapter with cache-first pattern.

    Fetches time series observations from FRED.
    Returns raw observation data -- signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.api_key = os.environ.get("FRED_API_KEY")

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 24 hours (FRED data updates at most daily)."""
        return 24 * 3600

    @property
    def source_name(self) -> str:
        return "fred"

    async def fetch(self, query: dict) -> dict:
        """Fetch FRED series observations.

        Args:
            query: {
                "series_id": str,       -- FRED series ID (e.g., "VIXCLS")
                "observation_start": str,  -- optional YYYY-MM-DD
                "observation_end": str,    -- optional YYYY-MM-DD
            }

        Returns:
            {
                "series_id": str,
                "title": str,
                "observations": list[{"date": str, "value": float}],
                "units": str,
                "frequency": str,
            }
        """
        series_id = query.get("series_id", "VIXCLS")
        cache_key = f"fred_{series_id}"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- call FRED API
        if not self.api_key:
            raise GhostMarketApiError(
                "FRED_API_KEY not set",
                retryable=False,
            )

        # Fetch series info and observations
        series_info = await self._fetch_series_info(series_id)
        observations = await self._fetch_observations(series_id, query)

        result = {
            "series_id": series_id,
            "title": series_info.get("title", FRED_SERIES.get(series_id, series_id)),
            "units": series_info.get("units", ""),
            "frequency": series_info.get("frequency", ""),
            "observations": observations,
        }

        # 3. Cache and return
        await self._cache_store(cache_key, result)
        return result

    async def _fetch_series_info(self, series_id: str) -> dict:
        """Fetch series metadata (title, units, frequency)."""
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{FRED_API_BASE}/series",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                series_list = data.get("seriess", [])
                return series_list[0] if series_list else {}
        except httpx.HTTPStatusError as e:
            raise GhostMarketApiError(
                f"FRED series info error for {series_id}: HTTP {e.response.status_code}",
                status_code=e.response.status_code,
                retryable=e.response.status_code >= 500,
            ) from e
        except httpx.HTTPError as e:
            raise GhostMarketApiError(
                f"FRED series info network error: {e}",
                retryable=True,
            ) from e

    async def _fetch_observations(self, series_id: str, query: dict) -> list[dict]:
        """Fetch time series observations from FRED."""
        now = datetime.now(timezone.utc)
        default_start = f"{now.year - 10}-01-01"

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": query.get("observation_start", default_start),
            "observation_end": query.get("observation_end", now.strftime("%Y-%m-%d")),
            "sort_order": "asc",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{FRED_API_BASE}/series/observations",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            raise GhostMarketApiError(
                f"FRED observations error for {series_id}: HTTP {e.response.status_code}",
                status_code=e.response.status_code,
                retryable=e.response.status_code >= 500,
            ) from e
        except httpx.HTTPError as e:
            raise GhostMarketApiError(
                f"FRED observations network error: {e}",
                retryable=True,
            ) from e

        observations = []
        for obs in data.get("observations", []):
            value_str = obs.get("value", ".")
            if value_str == ".":
                continue  # FRED uses "." for missing values
            try:
                observations.append({
                    "date": obs["date"],
                    "value": float(value_str),
                })
            except (ValueError, KeyError):
                continue

        return observations
