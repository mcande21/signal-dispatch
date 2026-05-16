"""FERC (Federal Energy Regulatory Commission) adapter.

Sources:
  - Federal Register API for FERC documents (orders, notices, rules)
  - SEC EDGAR for energy company regulatory filings
Auth: None required
TTL: 12h
"""

import asyncio
from datetime import datetime, timedelta, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


FR_API_BASE = "https://www.federalregister.gov/api/v1/documents.json"
FERC_AGENCY_SLUG = "federal-energy-regulatory-commission"

METHODS = {"search_filings", "search_docket", "search_company"}

HEADERS = {
    "User-Agent": "SignalDispatch/1.0 (contact@example.com)",
    "Accept": "application/json",
}

FR_DOC_TYPES = {
    "notice": "Notice",
    "rule": "Rule",
    "proposed_rule": "Proposed Rule",
    "presidential_document": "Presidential Document",
}


class FercAdapter(GhostMarketAdapter):
    """FERC regulatory filings via Federal Register API.

    The FERC eLibrary is an Angular SPA without a usable JSON API.
    We use the Federal Register API which indexes all FERC issuances
    (orders, notices, rules, proposed rules) with full-text search.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def ttl_seconds(self) -> int:
        return 43200

    @property
    def source_name(self) -> str:
        return "ferc"

    async def fetch(self, query: dict) -> dict:
        method = query.get("method")
        if method not in METHODS:
            raise GhostMarketApiError(
                f"FERC: unknown method '{method}', expected one of {METHODS}"
            )

        days = query.get("days", 90)

        if method == "search_filings":
            keyword = query.get("keyword", "")
            doc_type = query.get("doc_type", "")
            cache_key = f"ferc_filings_{keyword}_{doc_type}_{days}"
            return await self._cached_call(
                cache_key, self._search_filings, keyword, doc_type, days
            )
        elif method == "search_docket":
            docket = query.get("docket", "")
            if not docket:
                raise GhostMarketApiError("FERC: search_docket requires 'docket' param")
            cache_key = f"ferc_docket_{docket}_{days}"
            return await self._cached_call(
                cache_key, self._search_docket, docket, days
            )
        else:
            company = query.get("company", "")
            if not company:
                raise GhostMarketApiError("FERC: search_company requires 'company' param")
            cache_key = f"ferc_company_{company}_{days}"
            return await self._cached_call(
                cache_key, self._search_company, company, days
            )

    async def _cached_call(self, cache_key: str, fn, *args) -> dict:
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        try:
            data = await fn(*args)
        except GhostMarketApiError as e:
            if e.retryable:
                await asyncio.sleep(2)
                data = await fn(*args)
            else:
                raise

        await self._cache_store(cache_key, data)
        return data

    async def _search_filings(self, keyword: str, doc_type: str, days: int) -> dict:
        params = self._fr_params(days)
        if keyword:
            params["conditions[term]"] = keyword
        if doc_type and doc_type in FR_DOC_TYPES:
            params["conditions[type][]"] = FR_DOC_TYPES[doc_type]

        data = await self._call_fr(params)
        filings = self._parse_fr_results(data)

        return {
            "source": "ferc",
            "method": "search_filings",
            "keyword": keyword,
            "doc_type": doc_type or "all",
            "filings": filings,
            "result_count": len(filings),
            "total_available": data.get("count", len(filings)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _search_docket(self, docket: str, days: int) -> dict:
        params = self._fr_params(days)
        params["conditions[term]"] = docket

        data = await self._call_fr(params)
        filings = self._parse_fr_results(data)

        return {
            "source": "ferc",
            "method": "search_docket",
            "docket": docket,
            "filings": filings,
            "result_count": len(filings),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _search_company(self, company: str, days: int) -> dict:
        params = self._fr_params(days)
        params["conditions[term]"] = company

        data = await self._call_fr(params)
        filings = self._parse_fr_results(data)

        return {
            "source": "ferc",
            "method": "search_company",
            "company": company,
            "filings": filings,
            "result_count": len(filings),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _fr_params(self, days: int) -> dict:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        return {
            "conditions[agencies][]": FERC_AGENCY_SLUG,
            "conditions[publication_date][gte]": since,
            "per_page": 50,
            "page": 1,
            "order": "newest",
        }

    async def _call_fr(self, params: dict) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    FR_API_BASE, params=params, headers=HEADERS, timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "Federal Register rate limit exceeded",
                    status_code=429,
                    retryable=True,
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"Federal Register server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"Federal Register HTTP error: {status_code}",
                    status_code=status_code,
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to Federal Register API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "Federal Register request timed out", retryable=True
            ) from e

    def _parse_fr_results(self, data: dict) -> list[dict]:
        filings = []
        for doc in data.get("results", []):
            agencies = [a.get("name", "") for a in doc.get("agencies", [])]
            filings.append({
                "document_number": doc.get("document_number", ""),
                "title": doc.get("title", ""),
                "type": doc.get("type", ""),
                "publication_date": doc.get("publication_date", ""),
                "agencies": agencies,
                "abstract": doc.get("abstract", ""),
                "docket_ids": doc.get("docket_ids", []),
                "regulation_id_numbers": doc.get("regulation_id_numbers", []),
                "html_url": doc.get("html_url", ""),
                "pdf_url": doc.get("pdf_url", ""),
            })
        return filings
