"""Senate Lobbying Disclosure Act (LDA) API adapter.

Source: https://lda.gov/api/v1/ (migrated from lda.senate.gov, which shuts down 2026-06-30)
Auth: None required
TTL: 12h (filings update on quarterly cycles)
"""

from datetime import datetime, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


API_BASE = "https://lda.gov/api/v1"

VALID_METHODS = {
    "search_filings",
    "search_registrants",
    "search_clients",
    "lobbyist_lookup",
    "contributions",
}

HEADERS = {
    "User-Agent": "SignalDispatch/1.0 (contact@example.com)",
    "Accept": "application/json",
}


class SenateLobbyingAdapter(GhostMarketAdapter):
    """Senate LDA lobbying disclosure adapter with cache-first pattern.

    Fetches lobbying registrations, activity reports, and campaign contributions.
    Returns raw disclosure data -- signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 12 hours."""
        return 43200

    @property
    def source_name(self) -> str:
        return "senate_lobbying"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch dispatched by query method.

        Args:
            query: {
                "method": str,              -- one of VALID_METHODS
                "registrant_name": str,     -- lobbying firm name
                "client_name": str,         -- client organization name
                "lobbyist_name": str,       -- individual lobbyist name
                "issue_code": str,          -- issue area code (ENE, FUE, TAX, etc.)
                "filing_year": int,         -- year filter (default: current year)
                "filing_type": str,         -- "LD-1", "LD-2", or "LD-203"
            }
        """
        method = query.get("method")
        if method not in VALID_METHODS:
            return {
                "source": "senate_lobbying",
                "error": f"Unknown method: {method}. Valid: {sorted(VALID_METHODS)}",
            }

        dispatch = {
            "search_filings": self._search_filings,
            "search_registrants": self._search_registrants,
            "search_clients": self._search_clients,
            "lobbyist_lookup": self._lobbyist_lookup,
            "contributions": self._contributions,
        }

        return await dispatch[method](query)

    # ------------------------------------------------------------------
    # Method implementations
    # ------------------------------------------------------------------

    async def _search_filings(self, query: dict) -> dict:
        filing_year = query.get("filing_year", datetime.now(timezone.utc).year)
        registrant = query.get("registrant_name", "")
        client = query.get("client_name", "")
        issue_code = query.get("issue_code", "")
        filing_type = query.get("filing_type", "")

        cache_parts = [
            "filings",
            str(filing_year),
            registrant.lower(),
            client.lower(),
            issue_code.lower(),
            filing_type.lower(),
        ]
        cache_key = "_".join(p for p in cache_parts if p)

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        params = {"filing_year": str(filing_year)}
        if registrant:
            params["registrant_name"] = registrant
        if client:
            params["client_name"] = client
        if issue_code:
            params["issue_code"] = issue_code
        if filing_type:
            params["filing_type"] = filing_type

        raw = await self._call_api("/filings/", params)

        filings = []
        for item in raw.get("results", []):
            activities = []
            for act in item.get("lobbying_activities", []):
                activities.append({
                    "general_issue_code": act.get("general_issue_code", ""),
                    "general_issue_code_display": act.get("general_issue_code_display", ""),
                    "description": act.get("description", ""),
                    "lobbyists": [
                        {
                            "name": lob.get("lobbyist", {}).get("name", "")
                            if isinstance(lob.get("lobbyist"), dict)
                            else str(lob.get("lobbyist", "")),
                            "covered_position": lob.get("covered_official_position", ""),
                        }
                        for lob in act.get("lobbyists", [])
                    ],
                    "government_entities": [
                        ent.get("name", "") if isinstance(ent, dict) else str(ent)
                        for ent in act.get("government_entities", [])
                    ],
                })

            registrant_obj = item.get("registrant", {})
            client_obj = item.get("client", {})

            filings.append({
                "filing_uuid": item.get("filing_uuid", ""),
                "filing_type": item.get("filing_type_display", item.get("filing_type", "")),
                "filing_year": item.get("filing_year"),
                "filing_period": item.get("filing_period_display", item.get("filing_period", "")),
                "dt_posted": item.get("dt_posted", ""),
                "registrant_name": registrant_obj.get("name", "") if isinstance(registrant_obj, dict) else str(registrant_obj),
                "registrant_id": registrant_obj.get("id", "") if isinstance(registrant_obj, dict) else "",
                "client_name": client_obj.get("name", "") if isinstance(client_obj, dict) else str(client_obj),
                "client_id": client_obj.get("id", "") if isinstance(client_obj, dict) else "",
                "income": _safe_float(item.get("income")),
                "expenses": _safe_float(item.get("expenses")),
                "activities": activities,
            })

        result = {
            "source": "senate_lobbying",
            "method": "search_filings",
            "filing_year": filing_year,
            "registrant_name": registrant,
            "client_name": client,
            "issue_code": issue_code,
            "filings": filings,
            "result_count": len(filings),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await self._cache_store(cache_key, result)
        return result

    async def _search_registrants(self, query: dict) -> dict:
        registrant = query.get("registrant_name", "")
        if not registrant:
            raise GhostMarketApiError(
                "senate_lobbying: 'registrant_name' parameter is required for search_registrants"
            )

        cache_key = f"registrants_{registrant.lower()}"

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        raw = await self._call_api("/registrants/", {"registrant_name": registrant})

        registrants = []
        for item in raw.get("results", []):
            registrants.append({
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "description": item.get("description", ""),
                "address": item.get("address", ""),
                "country": item.get("country_display", item.get("country", "")),
                "ppb_country": item.get("ppb_country_display", item.get("ppb_country", "")),
            })

        result = {
            "source": "senate_lobbying",
            "method": "search_registrants",
            "query": registrant,
            "registrants": registrants,
            "result_count": len(registrants),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await self._cache_store(cache_key, result)
        return result

    async def _search_clients(self, query: dict) -> dict:
        client = query.get("client_name", "")
        if not client:
            raise GhostMarketApiError(
                "senate_lobbying: 'client_name' parameter is required for search_clients"
            )

        cache_key = f"clients_{client.lower()}"

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        raw = await self._call_api("/clients/", {"client_name": client})

        clients = []
        for item in raw.get("results", []):
            clients.append({
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "general_description": item.get("general_description", ""),
                "country": item.get("country_display", item.get("country", "")),
                "state": item.get("state_display", item.get("state", "")),
                "ppb_country": item.get("ppb_country_display", item.get("ppb_country", "")),
                "ppb_state": item.get("ppb_state_display", item.get("ppb_state", "")),
            })

        result = {
            "source": "senate_lobbying",
            "method": "search_clients",
            "query": client,
            "clients": clients,
            "result_count": len(clients),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await self._cache_store(cache_key, result)
        return result

    async def _lobbyist_lookup(self, query: dict) -> dict:
        lobbyist = query.get("lobbyist_name", "")
        if not lobbyist:
            raise GhostMarketApiError(
                "senate_lobbying: 'lobbyist_name' parameter is required for lobbyist_lookup"
            )

        cache_key = f"lobbyist_{lobbyist.lower()}"

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        raw = await self._call_api("/lobbyists/", {"lobbyist_name": lobbyist})

        lobbyists = []
        for item in raw.get("results", []):
            lobbyists.append({
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "prefix": item.get("prefix_display", item.get("prefix", "")),
                "suffix": item.get("suffix_display", item.get("suffix", "")),
            })

        result = {
            "source": "senate_lobbying",
            "method": "lobbyist_lookup",
            "query": lobbyist,
            "lobbyists": lobbyists,
            "result_count": len(lobbyists),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await self._cache_store(cache_key, result)
        return result

    async def _contributions(self, query: dict) -> dict:
        filing_year = query.get("filing_year", datetime.now(timezone.utc).year)
        lobbyist = query.get("lobbyist_name", "")

        cache_parts = ["contributions", str(filing_year), lobbyist.lower()]
        cache_key = "_".join(p for p in cache_parts if p)

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        params = {"filing_year": str(filing_year)}
        if lobbyist:
            params["lobbyist_name"] = lobbyist

        raw = await self._call_api("/contributions/", params)

        contributions = []
        for item in raw.get("results", []):
            registrant_obj = item.get("registrant", {})
            contributions.append({
                "filing_uuid": item.get("filing_uuid", ""),
                "filing_year": item.get("filing_year"),
                "filing_period": item.get("filing_period_display", item.get("filing_period", "")),
                "dt_posted": item.get("dt_posted", ""),
                "registrant_name": registrant_obj.get("name", "") if isinstance(registrant_obj, dict) else str(registrant_obj),
                "lobbyist_name": item.get("lobbyist_name", ""),
                "contribution_type": item.get("contribution_type_display", item.get("contribution_type", "")),
                "contributor_name": item.get("contributor_name", ""),
                "payee_name": item.get("payee_name", ""),
                "honoree_name": item.get("honoree_name", ""),
                "amount": _safe_float(item.get("amount")),
                "date": item.get("date", ""),
            })

        result = {
            "source": "senate_lobbying",
            "method": "contributions",
            "filing_year": filing_year,
            "lobbyist_name": lobbyist,
            "contributions": contributions,
            "result_count": len(contributions),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await self._cache_store(cache_key, result)
        return result

    # ------------------------------------------------------------------
    # HTTP layer
    # ------------------------------------------------------------------

    async def _call_api(self, endpoint: str, params: dict) -> dict:
        """Make request to Senate LDA API."""
        url = f"{API_BASE}{endpoint}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, params=params, headers=HEADERS, timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "Senate LDA rate limit exceeded",
                    status_code=429,
                    retryable=True,
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"Senate LDA server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"Senate LDA HTTP error: {status_code}",
                    status_code=status_code,
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to Senate LDA API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "Senate LDA API request timed out", retryable=True
            ) from e


def _safe_float(value) -> float | None:
    """Parse string to float, returning None on failure."""
    if value is None:
        return None
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None
