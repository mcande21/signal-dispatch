"""AGSI (Aggregated Gas Storage Inventory) API adapter.

Source: https://agsi.gie.eu/api
Auth: API key via x-key header
TTL: 12 hours
"""

import os
from datetime import datetime, timedelta, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


# AGSI API base URL
AGSI_API_BASE = "https://agsi.gie.eu/api"


class AgsiAdapter(GhostMarketAdapter):
    """AGSI gas storage data adapter with cache-first pattern.

    Fetches natural gas storage inventory data from AGSI API.
    Returns raw AGSI storage records.
    Signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)
        api_key = os.environ.get("AGSI_API_KEY")
        if not api_key:
            raise ValueError("AGSI_API_KEY environment variable required")
        self.api_key: str = api_key

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 12 hours (43200 seconds)."""
        return 43200

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "agsi"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of AGSI gas storage data.

        Args:
            query: {
                "country": str (ISO-2 country code, required -- e.g. "DE", "NL", "AT"),
                "size": int (default 30 -- number of daily records),
                "days": int (default 30 -- how many days back, used to compute 'from' date)
            }

        Returns:
            {
                "source": "agsi",
                "country": str (ISO-2 code),
                "record_count": int,
                "storage_data": [
                    {
                        "gas_day": str (YYYY-MM-DD),
                        "gas_in_storage": float (TWh -- total gas in storage),
                        "full_pct": float (percentage full 0-100),
                        "injection": float (TWh injected),
                        "withdrawal": float (TWh withdrawn),
                        "consumption": float (TWh consumed, if available),
                        "trend": float (day-over-day change),
                    },
                    ...
                ],
                "fetched_at": str (ISO timestamp)
            }
        """
        country = query.get("country")
        if not country:
            raise GhostMarketApiError("agsi: 'country' parameter is required")

        size = query.get("size", 30)
        days = query.get("days", 30)

        # Cache key includes country and size
        cache_key = f"{country}_{size}"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- call AGSI API
        data = await self._call_agsi_api(country, size, days)

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _call_agsi_api(self, country: str, size: int, days: int) -> dict:
        """Call AGSI API for gas storage data.

        AGSI API docs: https://agsi.gie.eu/api
        """
        # Compute date range from days parameter
        to_date = datetime.now(timezone.utc)
        from_date = to_date - timedelta(days=days)

        # Build endpoint URL with country code in path
        url = f"{AGSI_API_BASE}/data/{country}"

        # Query parameters
        params = {
            "size": size,
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
        }

        # Auth header
        headers = {"x-key": self.api_key}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers, timeout=30.0)
                response.raise_for_status()
                raw_data = response.json()

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "AGSI API rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"AGSI API server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"AGSI API HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to AGSI API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "AGSI API request timed out", retryable=True
            ) from e

        # Validate response structure
        # AGSI returns {"data": [...]} wrapper
        self._validate_response(raw_data, ["data"])

        # Parse storage records
        storage_data = []
        for record in raw_data.get("data", []):
            # Map AGSI field names to our schema
            # Common AGSI fields: gasInStorage, full, injection, withdrawal, consumption, trend
            # gasDayStart or gasDayStartedOn for date
            gas_day = record.get("gasDayStart") or record.get("gasDayStartedOn", "")

            # Parse numeric fields (may be strings or None)
            def parse_float(val):
                if val is None or val == "":
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            storage_data.append({
                "gas_day": gas_day,
                "gas_in_storage": parse_float(record.get("gasInStorage")),
                "full_pct": parse_float(record.get("full")),
                "injection": parse_float(record.get("injection")),
                "withdrawal": parse_float(record.get("withdrawal")),
                "consumption": parse_float(record.get("consumption")),
                "trend": parse_float(record.get("trend")),
            })

        return {
            "source": "agsi",
            "country": country,
            "record_count": len(storage_data),
            "storage_data": storage_data,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
