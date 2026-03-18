"""ACLED (Armed Conflict Location & Event Data) API adapter.

Source: https://api.acleddata.com/acled/read
Auth: ACLED_API_KEY + ACLED_EMAIL env vars (passed as query params)
TTL: 1 hour
"""

import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import httpx

from .base import GhostMarketAdapter, GhostMarketApiError


ACLED_API_BASE = "https://api.acleddata.com/acled/read"


class AcledAdapter(GhostMarketAdapter):
    """ACLED conflict event adapter with cache-first pattern.

    Fetches geolocated conflict events for the past 7 days.
    Returns structured summary: totals, breakdowns by region/country/type,
    and top events by fatality count.
    Signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 1 hour (ACLED updates daily)."""
        return 3600

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "acled"

    async def fetch(self, query: dict) -> dict:  # noqa: ARG002
        """Cache-first fetch of ACLED conflict event data.

        Args:
            query: Unused. Adapter always fetches the past 7 days.

        Returns:
            {
                "source": "acled",
                "total_events": int,
                "total_fatalities": int,
                "period": "7d",
                "by_region": {
                    "Middle East": {"events": int, "fatalities": int},
                    ...
                },
                "by_event_type": {
                    "Battles": {"events": int, "fatalities": int},
                    ...
                },
                "top_events": [
                    {
                        "date": str,
                        "country": str,
                        "event_type": str,
                        "fatalities": int,
                        "notes": str,
                    },
                    ...  # top 10 by fatalities
                ],
                "by_country": {
                    "Sudan": {"events": int, "fatalities": int},
                    ...  # top 10 countries by event count
                },
                "fetched_at": str (ISO timestamp)
            }

        Returns error dict (does not raise) when API key is not configured.
        """
        token = os.environ.get("ACLED_ACCESS_TOKEN")

        if not token:
            return {
                "source": "acled",
                "error": "Missing required environment variable: ACLED_ACCESS_TOKEN",
            }

        today = datetime.now(timezone.utc).date()
        seven_days_ago = today - timedelta(days=7)
        cache_key = f"weekly_{seven_days_ago.isoformat()}_{today.isoformat()}"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- call ACLED API
        data = await self._call_acled_api(token, seven_days_ago, today)

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _call_acled_api(
        self,
        token: str,
        start_date: "datetime.date",
        end_date: "datetime.date",
    ) -> dict:
        """Call ACLED API and return structured summary.

        ACLED API docs: https://apidocs.acleddata.com/
        Uses Bearer token auth (JWT access token).
        """
        params = {
            "event_date": f"{start_date.isoformat()}|{end_date.isoformat()}",
            "event_date_where": "BETWEEN",
            "limit": 500,
        }
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    ACLED_API_BASE, params=params, headers=headers, timeout=30.0
                )
                response.raise_for_status()
                raw_data = response.json()

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 401 or status_code == 403:
                raise GhostMarketApiError(
                    f"ACLED API authentication failed: {status_code}",
                    status_code=status_code,
                ) from e
            elif status_code == 429:
                raise GhostMarketApiError(
                    "ACLED API rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"ACLED API server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"ACLED API HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to ACLED API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "ACLED API request timed out", retryable=True
            ) from e

        return self._parse_response(raw_data)

    def _parse_response(self, raw_data: dict) -> dict:
        """Parse ACLED API response into structured summary."""
        events = raw_data.get("data", [])

        total_events = len(events)
        total_fatalities = 0

        by_region: dict[str, dict] = defaultdict(lambda: {"events": 0, "fatalities": 0})
        by_event_type: dict[str, dict] = defaultdict(lambda: {"events": 0, "fatalities": 0})
        by_country_raw: dict[str, dict] = defaultdict(lambda: {"events": 0, "fatalities": 0})

        all_events_sorted = []

        for event in events:
            fatalities = int(event.get("fatalities", 0) or 0)
            total_fatalities += fatalities

            region = event.get("region", "Unknown")
            by_region[region]["events"] += 1
            by_region[region]["fatalities"] += fatalities

            event_type = event.get("event_type", "Unknown")
            by_event_type[event_type]["events"] += 1
            by_event_type[event_type]["fatalities"] += fatalities

            country = event.get("country", "Unknown")
            by_country_raw[country]["events"] += 1
            by_country_raw[country]["fatalities"] += fatalities

            notes_raw = event.get("notes", "") or ""
            all_events_sorted.append({
                "date": event.get("event_date", ""),
                "country": country,
                "event_type": event_type,
                "fatalities": fatalities,
                "notes": notes_raw[:300] if notes_raw else "",
            })

        # Top 10 events by fatality count
        top_events = sorted(all_events_sorted, key=lambda e: e["fatalities"], reverse=True)[:10]

        # Top 10 countries by event count
        top_countries = sorted(
            by_country_raw.items(), key=lambda kv: kv[1]["events"], reverse=True
        )[:10]
        by_country = {k: v for k, v in top_countries}

        return {
            "source": "acled",
            "total_events": total_events,
            "total_fatalities": total_fatalities,
            "period": "7d",
            "by_region": dict(by_region),
            "by_event_type": dict(by_event_type),
            "top_events": top_events,
            "by_country": by_country,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
