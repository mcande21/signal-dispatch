"""CourtListener (Free Law Project) API adapter.

Source: https://www.courtlistener.com/api/rest/v4/
Auth: COURTLISTENER_API_TOKEN env var (optional, increases rate limit)
Rate limit: 100/day without token, 5000/day with token
TTL: 6h
"""

import os
import re
from datetime import datetime, timedelta, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


COURTLISTENER_API_BASE = "https://www.courtlistener.com/api/rest/v4"

VALID_METHODS = {
    "search_opinions",
    "search_dockets",
    "search_recap",
    "docket_detail",
}

SEARCH_TYPE_MAP = {
    "search_opinions": "o",
    "search_dockets": "d",
    "search_recap": "r",
}


class CourtListenerAdapter(GhostMarketAdapter):
    """CourtListener API adapter with cache-first pattern.

    Fetches federal court opinions, dockets, and PACER filings.
    Returns raw court data -- signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.api_token = os.environ.get("COURTLISTENER_API_TOKEN")

    @property
    def ttl_seconds(self) -> int:
        return 21600

    @property
    def source_name(self) -> str:
        return "courtlistener"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch dispatched by method.

        Args:
            query: {
                "method": str,       -- one of VALID_METHODS
                "query": str,        -- search terms
                "court": str,        -- court filter (optional, e.g. "dcd", "scotus")
                "docket_id": int,    -- for docket_detail
                "days": int,         -- lookback period (optional, default 365)
                "party_name": str,   -- party name filter (optional)
            }
        """
        method = query.get("method")
        if method not in VALID_METHODS:
            raise GhostMarketApiError(
                f"courtlistener: invalid method '{method}', expected one of {sorted(VALID_METHODS)}"
            )

        cache_key = self._build_cache_key(query)

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        dispatch = {
            "search_opinions": self._search_opinions,
            "search_dockets": self._search_dockets,
            "search_recap": self._search_recap,
            "docket_detail": self._docket_detail,
        }

        data = await dispatch[method](query)

        await self._cache_store(cache_key, data)
        return data

    def _build_cache_key(self, query: dict) -> str:
        method = query.get("method", "")
        if method == "docket_detail":
            return f"cl_{method}_{query.get('docket_id', '')}"
        parts = [
            f"cl_{method}",
            query.get("query", ""),
            query.get("court", ""),
            query.get("party_name", ""),
            str(query.get("days", 365)),
        ]
        return "_".join(p for p in parts if p)

    def _build_headers(self) -> dict:
        headers = {
            "Accept": "application/json",
            "User-Agent": "SignalDispatch/1.0",
        }
        if self.api_token:
            headers["Authorization"] = f"Token {self.api_token}"
        return headers

    async def _get(self, url: str, params: dict | None = None) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, params=params, headers=self._build_headers(), timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "CourtListener rate limit exceeded",
                    status_code=429,
                    retryable=True,
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"CourtListener server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"CourtListener HTTP error: {status_code}",
                    status_code=status_code,
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to CourtListener API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "CourtListener API request timed out", retryable=True
            ) from e

    def _search_params(self, query: dict, search_type: str) -> dict:
        days = query.get("days", 365)
        filed_after = (
            datetime.now(timezone.utc) - timedelta(days=days)
        ).strftime("%Y-%m-%d")

        params = {
            "q": query.get("query", ""),
            "type": search_type,
            "order_by": "dateFiled desc",
            "filed_after": filed_after,
        }

        court = query.get("court")
        if court:
            params["court"] = court

        party_name = query.get("party_name")
        if party_name:
            params["case_name"] = party_name

        return params

    # -- search_opinions -------------------------------------------------------

    async def _search_opinions(self, query: dict) -> dict:
        search_query = query.get("query", "")
        if not search_query:
            raise GhostMarketApiError("courtlistener: 'query' parameter is required")

        params = self._search_params(query, SEARCH_TYPE_MAP["search_opinions"])
        raw = await self._get(f"{COURTLISTENER_API_BASE}/search/", params)

        opinions = []
        for result in raw.get("results", []):
            opinions.append({
                "case_name": result.get("caseName", ""),
                "court": result.get("court", ""),
                "court_citation_string": result.get("court_citation_string", ""),
                "date_filed": result.get("dateFiled", ""),
                "citation": _first_citation(result),
                "snippet": _clean_snippet(result.get("snippet", "")),
                "docket_id": result.get("docket_id"),
                "cluster_id": result.get("cluster_id"),
                "absolute_url": result.get("absolute_url", ""),
            })

        return {
            "source": "courtlistener",
            "method": "search_opinions",
            "query": search_query,
            "court_filter": query.get("court"),
            "results": opinions,
            "result_count": len(opinions),
            "total_count": raw.get("count", len(opinions)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -- search_dockets --------------------------------------------------------

    async def _search_dockets(self, query: dict) -> dict:
        search_query = query.get("query", "")
        if not search_query:
            raise GhostMarketApiError("courtlistener: 'query' parameter is required")

        params = self._search_params(query, SEARCH_TYPE_MAP["search_dockets"])
        raw = await self._get(f"{COURTLISTENER_API_BASE}/search/", params)

        dockets = []
        for result in raw.get("results", []):
            dockets.append({
                "case_name": result.get("caseName", ""),
                "court": result.get("court", ""),
                "docket_number": result.get("docketNumber", ""),
                "date_filed": result.get("dateFiled", ""),
                "date_terminated": result.get("dateTerminated", ""),
                "cause": result.get("cause", ""),
                "nature_of_suit": result.get("suitNature", ""),
                "jury_demand": result.get("juryDemand", ""),
                "docket_id": result.get("docket_id"),
                "absolute_url": result.get("absolute_url", ""),
            })

        return {
            "source": "courtlistener",
            "method": "search_dockets",
            "query": search_query,
            "court_filter": query.get("court"),
            "results": dockets,
            "result_count": len(dockets),
            "total_count": raw.get("count", len(dockets)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -- search_recap ----------------------------------------------------------

    async def _search_recap(self, query: dict) -> dict:
        search_query = query.get("query", "")
        if not search_query:
            raise GhostMarketApiError("courtlistener: 'query' parameter is required")

        params = self._search_params(query, SEARCH_TYPE_MAP["search_recap"])
        raw = await self._get(f"{COURTLISTENER_API_BASE}/search/", params)

        entries = []
        for result in raw.get("results", []):
            entries.append({
                "case_name": result.get("caseName", ""),
                "court": result.get("court", ""),
                "docket_number": result.get("docketNumber", ""),
                "date_filed": result.get("dateFiled", ""),
                "description": result.get("description", ""),
                "document_number": result.get("document_number"),
                "attachment_number": result.get("attachment_number"),
                "is_available": result.get("is_available", False),
                "snippet": _clean_snippet(result.get("snippet", "")),
                "docket_id": result.get("docket_id"),
                "absolute_url": result.get("absolute_url", ""),
            })

        return {
            "source": "courtlistener",
            "method": "search_recap",
            "query": search_query,
            "court_filter": query.get("court"),
            "results": entries,
            "result_count": len(entries),
            "total_count": raw.get("count", len(entries)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -- docket_detail ---------------------------------------------------------

    async def _docket_detail(self, query: dict) -> dict:
        docket_id = query.get("docket_id")
        if not docket_id:
            raise GhostMarketApiError(
                "courtlistener: 'docket_id' parameter is required"
            )

        raw = await self._get(f"{COURTLISTENER_API_BASE}/dockets/{docket_id}/")

        docket_entries = []
        for entry in raw.get("docket_entries", []):
            docket_entries.append({
                "date_filed": entry.get("date_filed", ""),
                "entry_number": entry.get("entry_number"),
                "description": entry.get("description", ""),
                "recap_documents": [
                    {
                        "description": doc.get("description", ""),
                        "document_number": doc.get("document_number"),
                        "is_available": doc.get("is_available", False),
                        "page_count": doc.get("page_count"),
                    }
                    for doc in entry.get("recap_documents", [])
                ],
            })

        parties = []
        for party in raw.get("parties", []):
            attorneys = []
            for atty in party.get("attorneys", []):
                attorneys.append({
                    "name": atty.get("attorney_name", ""),
                    "firm": atty.get("firm_name", ""),
                    "roles": [r.get("role", "") for r in atty.get("roles", [])],
                })
            parties.append({
                "name": party.get("name", ""),
                "type": party.get("party_type", ""),
                "attorneys": attorneys,
            })

        return {
            "source": "courtlistener",
            "method": "docket_detail",
            "docket_id": docket_id,
            "case_name": raw.get("case_name", ""),
            "court": raw.get("court", ""),
            "docket_number": raw.get("docket_number", ""),
            "date_filed": raw.get("date_filed", ""),
            "date_terminated": raw.get("date_terminated", ""),
            "cause": raw.get("cause", ""),
            "nature_of_suit": raw.get("nature_of_suit", ""),
            "assigned_to_str": raw.get("assigned_to_str", ""),
            "referred_to_str": raw.get("referred_to_str", ""),
            "parties": parties,
            "docket_entries": docket_entries,
            "entry_count": len(docket_entries),
            "result_count": 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _first_citation(result: dict) -> str:
    """Extract first available citation string."""
    citation = result.get("citation", [])
    if isinstance(citation, list) and citation:
        return str(citation[0])
    if isinstance(citation, str):
        return citation
    return result.get("sibling_ids", [""])[0] if result.get("sibling_ids") else ""


def _clean_snippet(snippet: str) -> str:
    """Strip HTML markup from search result snippets."""
    if not snippet:
        return ""
    return re.sub(r"<[^>]+>", "", snippet).strip()
