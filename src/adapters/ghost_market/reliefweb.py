"""ReliefWeb — UN Humanitarian Crises adapter.

Source: https://api.reliefweb.int/v1/disasters
Auth: Requires appname parameter (free, no key)
TTL: 12 hours

Signal: Active UN-declared disasters and crises → geopolitical disruption indicators,
ongoing emergencies that presage commodity/market impact.
"""

import os
from datetime import datetime, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


RELIEFWEB_API_URL = "https://api.reliefweb.int/v1/disasters"
RELIEFWEB_APPNAME = os.environ.get("RELIEFWEB_APPNAME", "signaldispatch")


class ReliefWebAdapter(GhostMarketAdapter):
    """ReliefWeb UN disaster API adapter with cache-first pattern.

    Fetches active humanitarian crises from ReliefWeb API.
    Returns structured disaster data for signal interpretation.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 12 hours."""
        return 43200

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "reliefweb"

    async def fetch(self, query: dict) -> dict:  # noqa: ARG002
        """Cache-first fetch of ReliefWeb active disasters.

        Args:
            query: Unused (no per-query params; fetches ongoing disasters)

        Returns:
            {
                "source": "reliefweb",
                "fetched_at": str (ISO timestamp),
                "active_disasters": [
                    {
                        "name": str,
                        "countries": [str],
                        "date": str,
                        "type": [str],
                        "status": str,
                        "url": str,
                    },
                    ...
                ],
                "disaster_count": int
            }
        """
        cache_key = "reliefweb_active_disasters"

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        data = await self._call_reliefweb_api()

        await self._cache_store(cache_key, data)
        return data

    async def _call_reliefweb_api(self) -> dict:
        """Call ReliefWeb API for ongoing disasters."""
        # ReliefWeb requires appname query parameter
        params = {
            "appname": RELIEFWEB_APPNAME,
            "filter[field]": "status",
            "filter[value]": "ongoing",
            "sort": "date.created:desc",
            "limit": 50,
            "fields[include]": ["name", "country", "date", "type", "status", "url"],
        }

        headers = {
            "User-Agent": "SignalDispatch/1.0",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    RELIEFWEB_API_URL, params=params, headers=headers, timeout=30.0
                )
                response.raise_for_status()
                raw = response.json()

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "ReliefWeb API rate limit exceeded",
                    status_code=429,
                    retryable=True,
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"ReliefWeb API server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"ReliefWeb API HTTP error: {status_code}",
                    status_code=status_code,
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to ReliefWeb API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "ReliefWeb API request timed out", retryable=True
            ) from e

        # ReliefWeb returns {"data": [...]} structure
        items = raw.get("data", [])

        disasters = []
        for item in items:
            fields = item.get("fields", {})
            name = fields.get("name", "")
            date_str = fields.get("date", {})
            # date is often {"created": "ISO", "changed": "ISO"}
            if isinstance(date_str, dict):
                date = date_str.get("created", date_str.get("changed", ""))
            else:
                date = str(date_str) if date_str else ""

            # Countries is array of {"name": str, "id": int}
            countries = []
            for country_obj in fields.get("country", []):
                if isinstance(country_obj, dict):
                    country_name = country_obj.get("name", "")
                else:
                    country_name = str(country_obj)
                if country_name:
                    countries.append(country_name)

            # Type is array of {"name": str, "id": int}
            types = []
            for type_obj in fields.get("type", []):
                if isinstance(type_obj, dict):
                    type_name = type_obj.get("name", "")
                else:
                    type_name = str(type_obj)
                if type_name:
                    types.append(type_name)

            status = fields.get("status", "")
            url = fields.get("url", "")

            if name:
                disasters.append({
                    "name": name,
                    "countries": countries,
                    "date": date,
                    "type": types,
                    "status": status,
                    "url": url,
                })

        return {
            "source": "reliefweb",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "active_disasters": disasters,
            "disaster_count": len(disasters),
        }
