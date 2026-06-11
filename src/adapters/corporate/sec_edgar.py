"""SEC EDGAR API adapter.

Source: https://www.sec.gov/edgar
Auth: None required (User-Agent with contact email)
TTL: 6h (filings update throughout the day)
"""

import os
import asyncio
from datetime import datetime, timedelta, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


EDGAR_SEARCH_BASE = "https://efts.sec.gov/LATEST/search-index"
EDGAR_SUBMISSIONS_BASE = "https://data.sec.gov/submissions"
EDGAR_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

HEADERS = {
    "User-Agent": f"SignalDispatch/1.0 ({os.environ.get('SD_CONTACT_EMAIL', 'contact@example.com')})",
    "Accept": "application/json",
}

VALID_METHODS = {
    "company_search",
    "company_filings",
    "filing_search",
    "insider_trades",
    "beneficial_ownership",
}

INSIDER_FORMS = ["4", "4/A"]
BENEFICIAL_FORMS = ["SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"]


class SecEdgarAdapter(GhostMarketAdapter):
    """SEC EDGAR adapter with cache-first pattern.

    Fetches corporate filings, insider trades, and beneficial ownership data.
    Returns raw filing data -- signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 6 hours (filings update throughout the day)."""
        return 21600

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "sec_edgar"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch dispatched by method.

        Args:
            query: {
                "method": str,  -- one of VALID_METHODS
                "company": str, -- company name or ticker (company_search)
                "cik": str,     -- CIK number (company_filings, insider_trades, beneficial_ownership)
                "query": str,   -- search terms (filing_search)
                "forms": list[str], -- form types to filter (optional)
                "days": int,    -- lookback period (optional, default 365)
            }
        """
        method = query.get("method")
        if method not in VALID_METHODS:
            raise GhostMarketApiError(
                f"sec_edgar: invalid method '{method}', expected one of {sorted(VALID_METHODS)}"
            )

        days = query.get("days", 365)
        cache_key = self._build_cache_key(query)

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        try:
            if method == "company_search":
                data = await self._company_search(query.get("company", ""), days)
            elif method == "company_filings":
                data = await self._company_filings(
                    query.get("cik", ""), query.get("forms"), days
                )
            elif method == "filing_search":
                data = await self._filing_search(
                    query.get("query", ""), query.get("forms"), days
                )
            elif method == "insider_trades":
                data = await self._insider_trades(query.get("cik", ""), days)
            elif method == "beneficial_ownership":
                data = await self._beneficial_ownership(query.get("cik", ""), days)
        except GhostMarketApiError as e:
            if e.retryable:
                await asyncio.sleep(2)
                if method == "company_search":
                    data = await self._company_search(query.get("company", ""), days)
                elif method == "company_filings":
                    data = await self._company_filings(
                        query.get("cik", ""), query.get("forms"), days
                    )
                elif method == "filing_search":
                    data = await self._filing_search(
                        query.get("query", ""), query.get("forms"), days
                    )
                elif method == "insider_trades":
                    data = await self._insider_trades(query.get("cik", ""), days)
                elif method == "beneficial_ownership":
                    data = await self._beneficial_ownership(query.get("cik", ""), days)
            else:
                raise

        await self._cache_store(cache_key, data)
        return data

    def _build_cache_key(self, query: dict) -> str:
        method = query.get("method", "")
        if method == "company_search":
            return f"sec_{method}_{query.get('company', '')}"
        elif method in ("company_filings", "insider_trades", "beneficial_ownership"):
            return f"sec_{method}_{query.get('cik', '')}"
        elif method == "filing_search":
            forms = ",".join(sorted(query.get("forms") or []))
            return f"sec_{method}_{query.get('query', '')}_{forms}"
        return f"sec_{method}"

    @staticmethod
    def _pad_cik(cik: str) -> str:
        return cik.lstrip("0").zfill(10)

    async def _get(self, url: str, params: dict | None = None) -> dict:
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
                    "SEC EDGAR rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"SEC EDGAR server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"SEC EDGAR HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to SEC EDGAR", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "SEC EDGAR request timed out", retryable=True
            ) from e

    # -- company_search --------------------------------------------------------

    async def _company_search(self, company: str, days: int) -> dict:
        if not company:
            raise GhostMarketApiError("sec_edgar: 'company' parameter is required")

        ticker_matches = await self._ticker_lookup(company)

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        params = {
            "q": company,
            "forms": "10-K",
            "dateRange": "custom",
            "startdt": start_date.strftime("%Y-%m-%d"),
            "enddt": end_date.strftime("%Y-%m-%d"),
        }
        search_data = await self._get(EDGAR_SEARCH_BASE, params)
        await asyncio.sleep(0.15)

        entities = {}
        for hit in search_data.get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            display_names = src.get("display_names", [])
            ciks = src.get("ciks", [])
            name = display_names[0] if display_names else ""
            cik_val = ciks[0].lstrip("0") if ciks else ""
            file_nums = src.get("file_num", [])
            file_num = file_nums[0] if isinstance(file_nums, list) and file_nums else str(file_nums)
            if name and name not in entities:
                entities[name] = {
                    "entity_name": name,
                    "cik": cik_val,
                    "file_num": file_num,
                    "form_type": src.get("form", src.get("root_forms", [""])[0] if src.get("root_forms") else ""),
                    "file_date": src.get("file_date", ""),
                }

        results = list(entities.values())

        for tm in ticker_matches:
            already = any(
                r["entity_name"].upper() == tm["entity_name"].upper() for r in results
            )
            if not already:
                results.insert(0, tm)

        return {
            "source": "sec_edgar",
            "method": "company_search",
            "company": company,
            "results": results,
            "result_count": len(results),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _ticker_lookup(self, company: str) -> list[dict]:
        try:
            tickers_data = await self._get(EDGAR_TICKERS_URL)
        except GhostMarketApiError:
            return []

        query_upper = company.upper().strip()
        matches = []
        for entry in tickers_data.values():
            ticker = str(entry.get("ticker", "")).upper()
            name = str(entry.get("title", "")).upper()
            cik = str(entry.get("cik_str", ""))
            if query_upper == ticker or query_upper in name:
                matches.append({
                    "entity_name": entry.get("title", ""),
                    "ticker": entry.get("ticker", ""),
                    "cik": cik,
                })
        return matches[:10]

    # -- company_filings -------------------------------------------------------

    async def _company_filings(
        self, cik: str, forms: list[str] | None, days: int
    ) -> dict:
        if not cik:
            raise GhostMarketApiError("sec_edgar: 'cik' parameter is required")

        padded = self._pad_cik(cik)
        url = f"{EDGAR_SUBMISSIONS_BASE}/CIK{padded}.json"
        raw = await self._get(url)

        company_name = raw.get("name", "")
        tickers = raw.get("tickers", [])
        sic = raw.get("sic", "")
        sic_desc = raw.get("sicDescription", "")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        recent = raw.get("filings", {}).get("recent", {})
        filing_dates = recent.get("filingDate", [])
        form_types = recent.get("form", [])
        primary_docs = recent.get("primaryDocument", [])
        accession_numbers = recent.get("accessionNumber", [])
        descriptions = recent.get("primaryDocDescription", [])

        filings = []
        for i in range(len(filing_dates)):
            try:
                filed = datetime.strptime(filing_dates[i], "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            except (ValueError, IndexError):
                continue
            if filed < cutoff:
                continue

            form = form_types[i] if i < len(form_types) else ""
            if forms and form not in forms:
                continue

            accession = accession_numbers[i] if i < len(accession_numbers) else ""
            accession_path = accession.replace("-", "")
            doc = primary_docs[i] if i < len(primary_docs) else ""

            filing_url = ""
            if accession and doc:
                filing_url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{cik.lstrip('0')}/{accession_path}/{doc}"
                )

            filings.append({
                "form_type": form,
                "filing_date": filing_dates[i],
                "description": descriptions[i] if i < len(descriptions) else "",
                "accession_number": accession,
                "url": filing_url,
            })

        return {
            "source": "sec_edgar",
            "method": "company_filings",
            "cik": cik,
            "company_name": company_name,
            "tickers": tickers,
            "sic": sic,
            "sic_description": sic_desc,
            "filings": filings,
            "filing_count": len(filings),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -- filing_search ---------------------------------------------------------

    async def _filing_search(
        self, query: str, forms: list[str] | None, days: int
    ) -> dict:
        if not query:
            raise GhostMarketApiError("sec_edgar: 'query' parameter is required")

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        params = {
            "q": query,
            "dateRange": "custom",
            "startdt": start_date.strftime("%Y-%m-%d"),
            "enddt": end_date.strftime("%Y-%m-%d"),
        }
        if forms:
            params["forms"] = ",".join(forms)

        raw = await self._get(EDGAR_SEARCH_BASE, params)

        filings = []
        for hit in raw.get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            display_names = src.get("display_names", [])
            ciks = src.get("ciks", [])
            file_nums = src.get("file_num", [])
            filings.append({
                "entity_name": display_names[0] if display_names else "",
                "cik": ciks[0].lstrip("0") if ciks else "",
                "form_type": src.get("form", ""),
                "file_date": src.get("file_date", ""),
                "file_num": file_nums[0] if isinstance(file_nums, list) and file_nums else str(file_nums),
                "accession_number": src.get("adsh", ""),
                "period_ending": src.get("period_ending", ""),
            })

        return {
            "source": "sec_edgar",
            "method": "filing_search",
            "query": query,
            "forms_filter": forms,
            "filings": filings,
            "filing_count": len(filings),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -- insider_trades --------------------------------------------------------

    async def _insider_trades(self, cik: str, days: int) -> dict:
        if not cik:
            raise GhostMarketApiError("sec_edgar: 'cik' parameter is required")

        filings_result = await self._company_filings(cik, INSIDER_FORMS, days)
        await asyncio.sleep(0.15)

        return {
            "source": "sec_edgar",
            "method": "insider_trades",
            "cik": cik,
            "company_name": filings_result.get("company_name", ""),
            "trades": filings_result.get("filings", []),
            "trade_count": filings_result.get("filing_count", 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -- beneficial_ownership --------------------------------------------------

    async def _beneficial_ownership(self, cik: str, days: int) -> dict:
        if not cik:
            raise GhostMarketApiError("sec_edgar: 'cik' parameter is required")

        filings_result = await self._company_filings(cik, BENEFICIAL_FORMS, days)
        await asyncio.sleep(0.15)

        return {
            "source": "sec_edgar",
            "method": "beneficial_ownership",
            "cik": cik,
            "company_name": filings_result.get("company_name", ""),
            "filings": filings_result.get("filings", []),
            "filing_count": filings_result.get("filing_count", 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
