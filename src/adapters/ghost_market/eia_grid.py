"""EIA Grid Monitor API adapter.

Source: https://api.eia.gov/v2/electricity/rto/daily-region-data/
Auth: API key required (EIA_API_KEY env var, shared with EIA petroleum adapter)
TTL: 1h (hourly updates)
"""

import asyncio
import os
from datetime import datetime, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


# EIA Grid Monitor API endpoint
EIA_GRID_API_BASE = "https://api.eia.gov/v2/electricity/rto/daily-region-data/data/"


class EiaGridAdapter(GhostMarketAdapter):
    """EIA Grid Monitor adapter with cache-first pattern.

    Fetches US electricity grid data (demand, generation, interchange).
    Returns raw API data - signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)
        api_key = os.environ.get("EIA_API_KEY")
        if not api_key:
            raise ValueError(
                "EIA API key required. Set EIA_API_KEY environment variable."
            )
        self.api_key: str = api_key

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 1 hour (hourly data updates)."""
        return 3600

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "eia_grid"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of EIA grid data.

        Args:
            query: {
                "respondent": str (region code, default "US48" - lower 48 states),
                "type": str ("D" for demand, "NG" for net generation, default "D"),
                "frequency": str ("daily" or "hourly", default "daily"),
                "length": int (number of records, default 14)
            }

        Returns:
            {
                "source": "eia_grid",
                "respondent": str,
                "type": str,
                "frequency": str,
                "record_count": int,
                "grid_data": [
                    {
                        "period": str,
                        "value": float|None,
                        "respondent": str,
                        "respondent_name": str,
                        "type": str,
                        "type_name": str,
                    },
                    ...
                ],
                "fetched_at": str (ISO timestamp),
            }
        """
        respondent = query.get("respondent", "US48")
        data_type = query.get("type", "D")
        frequency = query.get("frequency", "daily")
        length = query.get("length", 14)

        # Cache key includes all query params
        cache_key = f"{respondent}_{data_type}_{frequency}_{length}"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- call EIA Grid API with retry for retryable errors
        try:
            data = await self._call_eia_grid_api(respondent, data_type, frequency, length)
        except GhostMarketApiError as e:
            if e.retryable:
                await asyncio.sleep(2)
                data = await self._call_eia_grid_api(respondent, data_type, frequency, length)
            else:
                raise

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _call_eia_grid_api(
        self,
        respondent: str,
        data_type: str,
        frequency: str,
        length: int
    ) -> dict:
        """Call EIA Grid Monitor API for electricity data.

        EIA API v2 docs: https://www.eia.gov/opendata/documentation.php
        """
        params = {
            "api_key": self.api_key,
            "frequency": frequency,
            "data[0]": "value",
            "facets[respondent][]": respondent,
            "facets[type][]": data_type,
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": str(length),
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    EIA_GRID_API_BASE,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                api_data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "EIA Grid API rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif status_code == 401:
                raise GhostMarketApiError(
                    "Invalid EIA API key", status_code=401
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"EIA Grid API server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"EIA Grid API HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to EIA Grid API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "EIA Grid API request timed out", retryable=True
            ) from e

        # Parse response
        grid_data = []
        for item in api_data.get("response", {}).get("data", []):
            period = item.get("period")
            value = item.get("value")
            grid_data.append({
                "period": period,
                "value": float(value) if value is not None else None,
                "respondent": item.get("respondent", respondent),
                "respondent_name": item.get("respondent-name", ""),
                "type": item.get("type", data_type),
                "type_name": item.get("type-name", ""),
            })

        return {
            "source": "eia_grid",
            "respondent": respondent,
            "type": data_type,
            "frequency": frequency,
            "record_count": len(grid_data),
            "grid_data": grid_data,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
