"""GDELT (Global Database of Events, Language, and Tone) API adapter.

Source: https://api.gdeltproject.org/api/v2/doc/doc
Auth: None required
TTL: 15 minutes
"""

from datetime import datetime, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


# GDELT API base URL
GDELT_API_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"


class GdeltAdapter(GhostMarketAdapter):
    """GDELT article search adapter with cache-first pattern.

    Fetches news article data from GDELT Doc API.
    Returns raw GDELT article list data.
    Signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 15 minutes (news refresh rate)."""
        return 900

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "gdelt"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of GDELT article data.

        Args:
            query: {
                "query": str (search terms, required),
                "maxrecords": int (default 25),
                "timespan": str (default "1d" -- last 24h),
                "mode": str (default "ArtList")
            }

        Returns:
            {
                "source": "gdelt",
                "query": str,
                "timespan": str,
                "article_count": int,
                "articles": [
                    {"url": str, "title": str, "source": str, "language": str, "seendate": str},
                    ...
                ],
                "fetched_at": str (ISO timestamp)
            }
        """
        search_query = query.get("query")
        if not search_query:
            raise GhostMarketApiError("gdelt: 'query' parameter is required")

        maxrecords = query.get("maxrecords", 25)
        timespan = query.get("timespan", "1d")
        mode = query.get("mode", "ArtList")

        # Cache key includes search query, timespan, and maxrecords
        cache_key = f"{search_query}_{timespan}_{maxrecords}"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- call GDELT API
        data = await self._call_gdelt_api(search_query, maxrecords, timespan, mode)

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _call_gdelt_api(
        self, search_query: str, maxrecords: int, timespan: str, mode: str
    ) -> dict:
        """Call GDELT API for article list.

        GDELT API docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
        """
        params = {
            "query": search_query,
            "mode": mode,
            "maxrecords": maxrecords,
            "timespan": timespan,
            "format": "json",
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; GhostMarket/1.0)"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    GDELT_API_BASE, params=params, headers=headers, timeout=30.0
                )
                response.raise_for_status()
                raw_data = response.json()

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "GDELT API rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"GDELT API server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"GDELT API HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to GDELT API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "GDELT API request timed out", retryable=True
            ) from e

        # Validate response structure
        self._validate_response(raw_data, ["articles"])

        # Parse article list
        articles = []
        for item in raw_data.get("articles", []):
            articles.append({
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "source": item.get("domain", ""),
                "language": item.get("language", ""),
                "seendate": item.get("seendate", ""),
            })

        return {
            "source": "gdelt",
            "query": search_query,
            "timespan": timespan,
            "article_count": len(articles),
            "articles": articles,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
