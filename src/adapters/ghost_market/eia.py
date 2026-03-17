"""EIA (US Energy Information Administration) API adapter.

Source: https://api.eia.gov/v2/
Auth: API key required (EIA_API_KEY env var)
TTL: 24h (data updates weekly)
"""

import asyncio
import os
from datetime import datetime, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


# EIA API base URL
EIA_API_BASE = "https://api.eia.gov/v2"

# Available EIA series IDs for oil markets
# Agents choose which series to fetch based on market conditions
EIA_SERIES = {
    "WCESTUS1": "Weekly US ending stocks of crude oil (inventory)",
    "WCRIMUS2": "Weekly US imports of crude oil",
    "WCREXUS2": "Weekly US exports of crude oil",
    "WCRSTUS1": "Weekly US refinery utilization rate",
    "WCSSTUS1": "Weekly US Strategic Petroleum Reserve stocks",
}


class EiaAdapter(GhostMarketAdapter):
    """EIA oil data adapter with cache-first pattern.

    Fetches weekly petroleum status data (inventory, imports, exports).
    Returns raw API data - signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str, api_key: str | None = None):
        super().__init__(db_path)
        self.api_key = api_key or os.environ.get("EIA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "EIA API key required. Set EIA_API_KEY environment variable "
                "or pass api_key parameter."
            )

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 24 hours (weekly data updates)."""
        return 86400

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "eia"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of EIA series data.

        Args:
            query: {"series_id": str, "weeks": int (default 52)}

        Returns:
            {
                "series_id": str,
                "title": str,
                "observations": [{"period": str, "value": float}, ...],
                "last_updated": str,
            }
        """
        series_id = query.get("series_id", "WCESTUS1")  # Default to crude oil inventory
        weeks = query.get("weeks", 52)

        # Cache key includes series_id and weeks
        cache_key = f"{series_id}_{weeks}"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- call EIA API with retry for retryable errors
        try:
            data = await self._call_eia_api(series_id, weeks)
        except GhostMarketApiError as e:
            if e.retryable:
                await asyncio.sleep(2)
                data = await self._call_eia_api(series_id, weeks)
            else:
                raise

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _call_eia_api(self, series_id: str, weeks: int) -> dict:
        """Call EIA API for petroleum status data.

        EIA API v2 docs: https://www.eia.gov/opendata/documentation.php
        """
        url = f"{EIA_API_BASE}/petroleum/sum/sndw/data/"
        params = {
            "api_key": self.api_key,
            "frequency": "weekly",
            "data[0]": "value",
            "facets[series][]": series_id,
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": str(weeks),
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                api_data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "EIA API rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif status_code == 401:
                raise GhostMarketApiError(
                    "Invalid EIA API key", status_code=401
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"EIA API server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"EIA API HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to EIA API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "EIA API request timed out", retryable=True
            ) from e

        # Parse response
        observations = []
        for item in api_data.get("response", {}).get("data", []):
            period = item.get("period")
            value = item.get("value")
            if period and value is not None:
                observations.append({"period": period, "value": float(value)})

        return {
            "series_id": series_id,
            "title": EIA_SERIES.get(series_id, series_id),
            "observations": observations,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
