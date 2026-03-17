"""ENTSOG (European Network of Transmission System Operators for Gas) API adapter.

Source: https://transparency.entsog.eu/api/v1
Auth: None required
TTL: 1 hour
"""

from datetime import datetime, timedelta, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


# ENTSOG API base URL
ENTSOG_API_BASE = "https://transparency.entsog.eu/api/v1/operationaldata"


class EntsogAdapter(GhostMarketAdapter):
    """ENTSOG physical flow data adapter with cache-first pattern.

    Fetches gas flow data at interconnection points from ENTSOG API.
    Returns raw physical flow data.
    Signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 1 hour (3600 seconds)."""
        return 3600

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "entsog"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of ENTSOG physical flow data.

        Args:
            query: {
                "country": str (ISO-2 country code, required -- e.g. "DE", "PL", "HU"),
                "indicator": str (default "Physical Flow"),
                "period_type": str (default "day"),
                "limit": int (default 10),
                "days": int (default 7 -- how many days back from today)
            }

        Returns:
            {
                "source": "entsog",
                "country": str,
                "indicator": str,
                "period_type": str,
                "record_count": int,
                "flows": [
                    {
                        "point_key": str,         # interconnection point ID
                        "point_label": str,       # human-readable name (e.g. "Mallnow")
                        "direction": str,         # "entry" or "exit"
                        "value": float|None,      # flow value
                        "unit": str,              # e.g. "kWh/d" or "Nm3/d"
                        "period_from": str,       # date
                        "period_to": str,         # date
                        "operator_key": str,      # TSO identifier
                    },
                    ...
                ],
                "fetched_at": str (ISO timestamp)
            }
        """
        country = query.get("country")
        if not country:
            raise GhostMarketApiError("entsog: 'country' parameter is required")

        indicator = query.get("indicator", "Physical Flow")
        period_type = query.get("period_type", "day")
        limit = query.get("limit", 10)
        days = query.get("days", 7)

        # Cache key includes country, indicator, period_type, limit, and days
        cache_key = f"{country}_{indicator}_{period_type}_{limit}_{days}"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- call ENTSOG API
        data = await self._call_entsog_api(country, indicator, period_type, limit, days)

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _call_entsog_api(
        self, country: str, indicator: str, period_type: str, limit: int, days: int
    ) -> dict:
        """Call ENTSOG API for physical flow data.

        ENTSOG API docs: https://transparency.entsog.eu/#/api
        """
        # Calculate date range (days back from today)
        to_date = datetime.now(timezone.utc)
        from_date = to_date - timedelta(days=days)

        params = {
            "forCountry": country,
            "indicator": indicator,
            "periodType": period_type,
            "limit": limit,
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(ENTSOG_API_BASE, params=params, timeout=30.0)
                response.raise_for_status()
                raw_data = response.json()

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "ENTSOG API rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"ENTSOG API server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"ENTSOG API HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to ENTSOG API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "ENTSOG API request timed out", retryable=True
            ) from e

        # Validate response structure
        self._validate_response(raw_data, ["operationaldata"])

        # Parse flow data
        flows = []
        for item in raw_data.get("operationaldata", []):
            flows.append({
                "point_key": item.get("pointKey", ""),
                "point_label": item.get("pointLabel", ""),
                "direction": item.get("directionKey", ""),
                "value": item.get("value"),  # Can be None
                "unit": item.get("unit", ""),
                "period_from": item.get("periodFrom", ""),
                "period_to": item.get("periodTo", ""),
                "operator_key": item.get("operatorKey", ""),
            })

        return {
            "source": "entsog",
            "country": country,
            "indicator": indicator,
            "period_type": period_type,
            "record_count": len(flows),
            "flows": flows,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
