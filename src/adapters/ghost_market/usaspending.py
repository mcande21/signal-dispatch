"""USAspending.gov API adapter.

Source: https://api.usaspending.gov/api/v2/
Auth: None required
TTL: 24h (government data updates daily)
"""

import asyncio
from datetime import datetime, timedelta, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


# USAspending API base URL
USASPENDING_API_BASE = "https://api.usaspending.gov/api/v2"

# Iran-relevant keywords for contract search (reference - agents choose search terms)
DEFAULT_KEYWORDS = ["Iran", "Farsi", "Persian", "CENTCOM", "Arabian Gulf", "Strait of Hormuz"]

# Award type codes (contracts only)
CONTRACT_TYPE_CODES = ["A", "B", "C", "D"]


class UsaSpendingAdapter(GhostMarketAdapter):
    """USAspending.gov adapter with cache-first pattern.

    Fetches federal contract data by keyword search.
    Returns raw contract data - signal interpretation handled by agent layer.
    """

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 24 hours (government data updates daily)."""
        return 86400

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "usaspending"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of USAspending contract data.

        Args:
            query: {
                "keywords": list[str] (default: DEFAULT_KEYWORDS),
                "days": int (default: 90)
            }

        Returns:
            {
                "awards": list[dict],
                "total_count": int,
                "total_obligation": float,
                "timestamp": str,
            }
        """
        keywords = query.get("keywords", DEFAULT_KEYWORDS)
        days = query.get("days", 90)

        # Cache key includes days lookback
        cache_key = f"usaspending_iran_{days}"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- call USAspending API with retry for retryable errors
        try:
            data = await self._call_usaspending_api(keywords, days)
        except GhostMarketApiError as e:
            if e.retryable:
                await asyncio.sleep(2)
                data = await self._call_usaspending_api(keywords, days)
            else:
                raise

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _call_usaspending_api(self, keywords: list[str], days: int) -> dict:
        """Call USAspending API for award search.

        USAspending API docs: https://api.usaspending.gov/
        """
        url = f"{USASPENDING_API_BASE}/search/spending_by_award/"

        # Date range: last N days
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Build request body
        request_body = {
            "filters": {
                "keywords": keywords,
                "time_period": [
                    {
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                    }
                ],
                "award_type_codes": CONTRACT_TYPE_CODES,
            },
            "fields": [
                "Award ID",
                "Recipient Name",
                "Award Amount",
                "Award Type",
                "Awarding Agency",
                "Start Date",
            ],
            "limit": 100,
            "page": 1,
            "sort": "Award Amount",
            "order": "desc",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=request_body, timeout=30.0)
                response.raise_for_status()
                api_data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "USAspending API rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"USAspending API server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"USAspending API HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to USAspending API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "USAspending API request timed out", retryable=True
            ) from e

        # Parse response
        awards = []
        total_obligation = 0.0
        results = api_data.get("results", [])

        for item in results:
            award = {
                "award_id": item.get("Award ID"),
                "recipient": item.get("Recipient Name"),
                "obligation": float(item.get("Award Amount", 0)),
                "award_type": item.get("Award Type"),
                "agency": item.get("Awarding Agency"),
                "start_date": item.get("Start Date"),
            }
            awards.append(award)
            total_obligation += award["obligation"]

        return {
            "awards": awards,
            "total_count": api_data.get("page_metadata", {}).get("total", len(awards)),
            "total_obligation": total_obligation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
