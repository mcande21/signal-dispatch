"""ProPublica Nonprofit Explorer API adapter.

Source: https://projects.propublica.org/nonprofits/api/v2/
Auth: None required
TTL: 24h (990 data is annual)
"""

import asyncio
from datetime import datetime, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


API_BASE = "https://projects.propublica.org/nonprofits/api/v2"

VALID_METHODS = {"search", "organization", "filings"}

FILING_FIELDS = [
    "tax_prd_yr",
    "totrevenue",
    "totfuncexpns",
    "totassetsend",
    "totliabend",
    "compnsatncurrofcr",
    "grntstogovts",
    "grntstoindiv",
    "totcntrbgfts",
    "invstmntinc",
]


class ProPublicaNonprofitAdapter(GhostMarketAdapter):
    """ProPublica Nonprofit Explorer adapter with cache-first pattern.

    Fetches nonprofit organization data and IRS 990 filings.
    Returns raw data -- signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 24 hours."""
        return 86400

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "propublica_nonprofits"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch dispatched by method.

        Args:
            query: {
                "method": str,      -- one of VALID_METHODS
                "name": str,        -- organization name (search)
                "ein": str,         -- EIN number, no dashes (organization, filings)
                "state": str,       -- state abbreviation filter (optional, search)
                "ntee_code": str,   -- NTEE category filter (optional, search)
            }
        """
        method = query.get("method")
        if method not in VALID_METHODS:
            raise GhostMarketApiError(
                f"propublica_nonprofits: invalid method '{method}', "
                f"expected one of {sorted(VALID_METHODS)}"
            )

        cache_key = self._build_cache_key(query)

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        try:
            if method == "search":
                data = await self._search(query)
            elif method == "organization":
                data = await self._organization(query.get("ein", ""))
            elif method == "filings":
                data = await self._filings(query.get("ein", ""))
        except GhostMarketApiError as e:
            if e.retryable:
                await asyncio.sleep(2)
                if method == "search":
                    data = await self._search(query)
                elif method == "organization":
                    data = await self._organization(query.get("ein", ""))
                elif method == "filings":
                    data = await self._filings(query.get("ein", ""))
            else:
                raise

        await self._cache_store(cache_key, data)
        return data

    def _build_cache_key(self, query: dict) -> str:
        method = query.get("method", "")
        if method == "search":
            parts = [
                f"pp_search_{query.get('name', '')}",
                query.get("state", ""),
                query.get("ntee_code", ""),
            ]
            return "_".join(p for p in parts if p)
        return f"pp_{method}_{query.get('ein', '')}"

    @staticmethod
    def _normalize_ein(ein: str) -> str:
        return ein.replace("-", "").strip()

    async def _get(self, url: str, params: dict | None = None) -> dict | None:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30.0)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "ProPublica rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"ProPublica server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"ProPublica HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to ProPublica", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "ProPublica request timed out", retryable=True
            ) from e

    # -- search ----------------------------------------------------------------

    async def _search(self, query: dict) -> dict:
        name = query.get("name", "")
        if not name:
            raise GhostMarketApiError(
                "propublica_nonprofits: 'name' parameter is required for search"
            )

        params = {"q": name}
        state = query.get("state")
        if state:
            params["state[id]"] = state.upper()
        ntee_code = query.get("ntee_code")
        if ntee_code:
            params["ntee[id]"] = ntee_code.upper()

        raw = await self._get(f"{API_BASE}/search.json", params)
        if raw is None:
            return {
                "source": "propublica_nonprofits",
                "method": "search",
                "name": name,
                "organizations": [],
                "total_results": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        orgs = []
        for org in raw.get("organizations", []):
            orgs.append({
                "ein": str(org.get("ein", "")),
                "name": org.get("name", ""),
                "city": org.get("city", ""),
                "state": org.get("state", ""),
                "ntee_code": org.get("ntee_code", ""),
                "subsection_code": org.get("subsection_code"),
                "total_revenue": org.get("total_revenue"),
                "total_expenses": org.get("total_expenses"),
            })

        return {
            "source": "propublica_nonprofits",
            "method": "search",
            "name": name,
            "organizations": orgs,
            "total_results": raw.get("total_results", len(orgs)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -- organization ----------------------------------------------------------

    async def _organization(self, ein: str) -> dict:
        if not ein:
            raise GhostMarketApiError(
                "propublica_nonprofits: 'ein' parameter is required"
            )

        ein = self._normalize_ein(ein)
        raw = await self._get(f"{API_BASE}/organizations/{ein}.json")

        if raw is None:
            raise GhostMarketApiError(
                f"propublica_nonprofits: EIN {ein} not found", status_code=404
            )

        org = raw.get("organization", {})
        filings = self._extract_filings(raw.get("filings_with_data", []))

        return {
            "source": "propublica_nonprofits",
            "method": "organization",
            "ein": ein,
            "organization": {
                "name": org.get("name", ""),
                "address": org.get("address", ""),
                "city": org.get("city", ""),
                "state": org.get("state", ""),
                "ntee_code": org.get("ntee_code", ""),
                "subsection_code": org.get("subsection_code"),
                "ruling_date": org.get("ruling_date", ""),
                "tax_period": org.get("tax_period"),
                "asset_amount": org.get("asset_amount"),
                "income_amount": org.get("income_amount"),
            },
            "filings": filings,
            "filing_count": len(filings),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -- filings ---------------------------------------------------------------

    async def _filings(self, ein: str) -> dict:
        if not ein:
            raise GhostMarketApiError(
                "propublica_nonprofits: 'ein' parameter is required"
            )

        ein = self._normalize_ein(ein)
        raw = await self._get(f"{API_BASE}/organizations/{ein}.json")

        if raw is None:
            raise GhostMarketApiError(
                f"propublica_nonprofits: EIN {ein} not found", status_code=404
            )

        org_name = raw.get("organization", {}).get("name", "")
        filings = self._extract_filings(raw.get("filings_with_data", []))

        return {
            "source": "propublica_nonprofits",
            "method": "filings",
            "ein": ein,
            "organization_name": org_name,
            "filings": filings,
            "filing_count": len(filings),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -- helpers ---------------------------------------------------------------

    @staticmethod
    def _extract_filings(filings_with_data: list) -> list[dict]:
        filings = []
        for f in filings_with_data:
            filing = {}
            for field in FILING_FIELDS:
                filing[field] = f.get(field)
            filings.append(filing)
        return filings
