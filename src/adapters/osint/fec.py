"""FEC (Federal Election Commission) API adapter for campaign finance intelligence.

Tracks campaign filings, contributions, and candidate activity.
API docs: https://api.open.fec.gov/developers/
"""

import asyncio
import hashlib
import os
import re
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx

from ..models import OsintResult


class FecApiError(Exception):
    """Error from FEC API interaction."""
    def __init__(self, message: str, status_code: int | None = None, retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class FecAdapter:
    """FEC API adapter. Tracks campaign filings, contributions, and candidate activity."""

    BASE_URL = "https://api.open.fec.gov/v1"
    DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "osint_cache.db"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("FEC_API_KEY", "")

    async def fetch(self, market_data: dict, db=None) -> OsintResult | None:
        """Fetch FEC data relevant to market.

        Args:
            market_data: Market dict with 'title' and optionally 'rules_primary'
            db: Database instance (unused, kept for interface compatibility)

        Returns:
            OsintResult with filing data + contribution totals, or None if no API key
        """
        if not self.api_key:
            print("WARNING: FEC_API_KEY not set. Skipping FEC fetch.")
            return None

        # 1. Extract candidate info from market title/rules
        candidates = self._extract_candidates(market_data)
        if not candidates:
            return None

        # 2. Build cache key from candidate search terms
        cache_key = hashlib.sha256(str(candidates).encode()).hexdigest()

        # 3. Check cache (TTL = 24h for filings)
        cached = self._get_cached(cache_key, ttl_hours=24)
        if cached:
            return self._cached_to_result(cached)

        # 4. Search for candidates
        data_points = []
        for candidate_info in candidates:
            try:
                candidates_found = await self._search_candidates(
                    name=candidate_info.get("name"),
                    office=candidate_info.get("office"),
                    state=candidate_info.get("state"),
                )
            except FecApiError as e:
                if e.retryable:
                    await asyncio.sleep(2)
                    candidates_found = await self._search_candidates(
                        name=candidate_info.get("name"),
                        office=candidate_info.get("office"),
                        state=candidate_info.get("state"),
                    )
                else:
                    raise

            # 5. For matching candidates, fetch recent filings
            for cand in candidates_found[:2]:  # Limit to top 2 per search
                try:
                    filings = await self._get_filings(cand["candidate_id"], since_days=30)
                    if filings:
                        data_points.append({
                            "candidate": cand,
                            "filings": filings,
                        })
                except FecApiError:
                    continue

        if not data_points:
            return None

        # 6. Build result
        fetch_time = datetime.now(timezone.utc).isoformat()
        summary = self._build_summary(data_points)
        relevance = self._compute_relevance(market_data, data_points)

        # Latest filing date determines staleness
        latest_filing_date = max(
            (dt for dp in data_points
             for filing in dp.get("filings", [])
             if filing.get("receipt_date")
             if (dt := self._parse_date(filing["receipt_date"])) is not None),
            default=None
        )
        if latest_filing_date:
            staleness_hours = (datetime.now(timezone.utc) - latest_filing_date).total_seconds() / 3600
        else:
            staleness_hours = 999.0

        result = OsintResult(
            source="fec",
            source_url=f"{self.BASE_URL}/candidates/search/",
            fetch_time=fetch_time,
            data_points=data_points,
            staleness_hours=staleness_hours,
            confidence=0.8,  # FEC data is highly authoritative
            summary=summary,
            market_relevance=relevance,
        )

        # 7. Cache the result
        self._cache_result(cache_key, result)

        return result

    def _extract_candidates(self, market_data: dict) -> list[dict]:
        """Extract candidate names, offices, states from market title/rules.

        Returns list of dicts with: name, office, state
        """
        title = market_data.get("title", "")
        rules = market_data.get("rules_primary", "")
        text = f"{title} {rules}"

        candidates = []

        # Simple heuristic: look for office keywords and state abbreviations
        # Office patterns
        office_patterns = {
            "president": "P",
            "presidential": "P",
            "senate": "S",
            "senator": "S",
            "house": "H",
            "congress": "H",
            "representative": "H",
        }

        office_type = None
        for keyword, code in office_patterns.items():
            if keyword in text.lower():
                office_type = code
                break

        # State patterns (2-letter abbreviations)
        states = re.findall(r"\b([A-Z]{2})\b", text)
        state = states[0] if states else None

        # Name extraction (very basic - just uppercase word sequences)
        # In practice, this would need NER or more sophisticated extraction
        name_candidates = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", text)

        if name_candidates:
            for name in name_candidates[:3]:  # Limit to first 3 potential names
                candidates.append({
                    "name": name,
                    "office": office_type,
                    "state": state,
                })
        elif office_type or state:
            # At least search by office/state even without a name
            candidates.append({
                "name": None,
                "office": office_type,
                "state": state,
            })

        return candidates

    async def _search_candidates(
        self,
        name: str | None = None,
        office: str | None = None,
        state: str | None = None,
        election_year: int = 2026
    ) -> list[dict]:
        """Search for candidates matching criteria.

        Returns list of candidate dicts with: candidate_id, name, office, state, party
        """
        params = {
            "api_key": self.api_key,
            "election_year": election_year,
            "per_page": 20,
        }

        if name:
            params["name"] = name
        if office:
            params["office"] = office
        if state:
            params["state"] = state

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/candidates/search/",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise FecApiError("FEC API rate limit exceeded", status_code=429, retryable=True) from e
            elif status_code == 401 or status_code == 403:
                raise FecApiError("Invalid FEC API key", status_code=status_code) from e
            elif 500 <= status_code < 600:
                raise FecApiError(f"FEC API server error: {status_code}", status_code=status_code, retryable=True) from e
            else:
                raise FecApiError(f"FEC API HTTP error: {status_code}", status_code=status_code) from e
        except httpx.ConnectError as e:
            raise FecApiError("Cannot connect to FEC API", retryable=True) from e
        except httpx.TimeoutException as e:
            raise FecApiError("FEC API request timed out", retryable=True) from e

        results = data.get("results", [])
        candidates = []
        for cand in results:
            candidates.append({
                "candidate_id": cand.get("candidate_id", ""),
                "name": cand.get("name", ""),
                "office": cand.get("office", ""),
                "state": cand.get("state", ""),
                "party": cand.get("party", ""),
            })

        return candidates

    async def _get_filings(self, candidate_id: str, since_days: int = 30) -> list[dict]:
        """Get recent filings for a candidate.

        Returns list of filing dicts with: filing_id, receipt_date, total_receipts,
        total_disbursements, cash_on_hand, etc.
        """
        # Calculate min_receipt_date
        min_date = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%Y-%m-%d")

        params = {
            "api_key": self.api_key,
            "candidate_id": candidate_id,
            "min_receipt_date": min_date,
            "per_page": 20,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/filings/",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise FecApiError("FEC API rate limit exceeded", status_code=429, retryable=True) from e
            elif 500 <= status_code < 600:
                raise FecApiError(f"FEC API server error: {status_code}", status_code=status_code, retryable=True) from e
            else:
                raise FecApiError(f"FEC API HTTP error: {status_code}", status_code=status_code) from e
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise FecApiError("FEC API network error", retryable=True) from e

        results = data.get("results", [])
        filings = []
        for filing in results:
            filings.append({
                "filing_id": filing.get("file_number", ""),
                "receipt_date": filing.get("receipt_date", ""),
                "total_receipts": filing.get("total_receipts", 0),
                "total_disbursements": filing.get("total_disbursements", 0),
                "cash_on_hand": filing.get("cash_on_hand_end_period", 0),
                "coverage_end_date": filing.get("coverage_end_date", ""),
                "filing_type": filing.get("form_type", ""),
                "committee_name": filing.get("committee_name", ""),
            })

        return filings

    async def check_updates(self, since: str, _db=None) -> list[dict]:
        """Poll for new filings since last check.

        Args:
            since: ISO timestamp of last check
            db: Database instance (unused)

        Returns:
            List of filings submitted since the timestamp
        """
        if not self.api_key:
            return []

        # Query filings sorted by receipt_date desc
        since_date = datetime.fromisoformat(since.replace("Z", "+00:00")).strftime("%Y-%m-%d")

        params = {
            "api_key": self.api_key,
            "min_receipt_date": since_date,
            "per_page": 100,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/filings/",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError:
            return []

        results = data.get("results", [])
        updates = []
        for filing in results:
            updates.append({
                "filing_id": filing.get("file_number", ""),
                "candidate_id": filing.get("candidate_id", ""),
                "receipt_date": filing.get("receipt_date", ""),
                "form_type": filing.get("form_type", ""),
            })

        return updates

    def _build_summary(self, data_points: list[dict]) -> str:
        """Build human-readable summary from FEC data."""
        if not data_points:
            return "No relevant filings found"

        dp = data_points[0]
        candidate = dp["candidate"]
        filings = dp.get("filings", [])

        if filings:
            latest = filings[0]
            return f"{candidate['name']} ({candidate['party']}-{candidate['state']}): ${latest['total_receipts']:,.0f} receipts, ${latest['cash_on_hand']:,.0f} cash on hand ({latest['receipt_date']})"
        else:
            return f"{candidate['name']} ({candidate['party']}-{candidate['state']}): No recent filings"

    def _compute_relevance(self, _market_data: dict, data_points: list[dict]) -> float:
        """Compute market relevance score (0.0-1.0) based on candidate matches."""
        if not data_points:
            return 0.0

        # Simple heuristic: if we found candidates and filings, relevance is high
        has_filings = any(dp.get("filings") for dp in data_points)
        if has_filings:
            return 0.8
        else:
            return 0.5

    def _parse_date(self, date_str: str) -> datetime | None:
        """Parse ISO date string to datetime."""
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    # ========================================================================
    # Cache helpers (inline SQLite, will be unified when edi-1's work lands)
    # ========================================================================

    def _get_cached(self, cache_key: str, ttl_hours: int = 24) -> dict | None:
        """Check cache. Returns None on miss or stale."""
        conn = sqlite3.connect(str(self.DB_PATH))
        cursor = conn.cursor()

        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS osint_fec_cache (
                cache_key TEXT PRIMARY KEY,
                data_json TEXT,
                last_fetched TEXT DEFAULT (datetime('now'))
            )
        """)

        # Query cache
        cursor.execute(
            "SELECT data_json, last_fetched FROM osint_fec_cache WHERE cache_key = ?",
            (cache_key,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        data_json, last_fetched = row
        last_fetched_dt = datetime.fromisoformat(last_fetched)
        age_hours = (datetime.now(timezone.utc) - last_fetched_dt.replace(tzinfo=timezone.utc)).total_seconds() / 3600

        if age_hours > ttl_hours:
            return None

        import json
        return json.loads(data_json)

    def _cache_result(self, cache_key: str, result: OsintResult):
        """Cache an OsintResult."""
        import json

        conn = sqlite3.connect(str(self.DB_PATH))
        cursor = conn.cursor()

        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS osint_fec_cache (
                cache_key TEXT PRIMARY KEY,
                data_json TEXT,
                last_fetched TEXT DEFAULT (datetime('now'))
            )
        """)

        # Serialize result to JSON
        data_json = json.dumps({
            "source": result.source,
            "source_url": result.source_url,
            "fetch_time": result.fetch_time,
            "data_points": result.data_points,
            "staleness_hours": result.staleness_hours,
            "confidence": result.confidence,
            "summary": result.summary,
            "market_relevance": result.market_relevance,
        })

        cursor.execute(
            "INSERT OR REPLACE INTO osint_fec_cache (cache_key, data_json, last_fetched) VALUES (?, ?, datetime('now'))",
            (cache_key, data_json)
        )
        conn.commit()
        conn.close()

    def _cached_to_result(self, cached: dict) -> OsintResult:
        """Convert cached dict back to OsintResult."""
        return OsintResult(
            source=cached["source"],
            source_url=cached["source_url"],
            fetch_time=cached["fetch_time"],
            data_points=cached["data_points"],
            staleness_hours=cached["staleness_hours"],
            confidence=cached["confidence"],
            summary=cached["summary"],
            market_relevance=cached["market_relevance"],
        )

    async def execute_query(self, query: dict) -> list[dict]:
        """Execute a structured query plan.

        Args:
            query: dict with keys:
                - type: str -- query type (e.g., "candidate_search", "candidate_filings")
                - params: dict -- API parameters

        Returns:
            List of result dicts with standardized fields.
        """
        if not self.api_key:
            print("WARNING: FEC_API_KEY not set. Cannot execute query.")
            return []

        query_type = query.get("type")
        params = query.get("params", {})

        if query_type == "candidate_search":
            # Map params to candidate search
            name = params.get("name")
            office = params.get("office")
            state = params.get("state")
            party = params.get("party")
            cycle = params.get("cycle", 2026)
            per_page = params.get("per_page", 20)

            api_params = {
                "api_key": self.api_key,
                "election_year": cycle,
                "per_page": per_page,
            }

            if name:
                api_params["name"] = name
            if office:
                api_params["office"] = office
            if state:
                api_params["state"] = state
            if party:
                api_params["party"] = party

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.BASE_URL}/candidates/search/",
                        params=api_params,
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    data = response.json()

                    results = data.get("results", [])
                    candidates = []
                    for cand in results:
                        candidates.append({
                            "candidate_id": cand.get("candidate_id", ""),
                            "name": cand.get("name", ""),
                            "office": cand.get("office", ""),
                            "state": cand.get("state", ""),
                            "party": cand.get("party", ""),
                            "total_receipts": cand.get("total_receipts", 0),
                            "total_disbursements": cand.get("total_disbursements", 0),
                            "url": f"https://www.fec.gov/data/candidate/{cand.get('candidate_id', '')}/" if cand.get("candidate_id") else "",
                        })

                    return candidates

            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as e:
                print(f"WARNING: FEC execute_query (candidate_search) failed: {e}")
                return []

        elif query_type == "candidate_filings":
            # Get candidate filings
            candidate_id = params.get("candidate_id")
            filing_type = params.get("filing_type")
            per_page = params.get("per_page", 20)

            if not candidate_id:
                print("WARNING: candidate_id is required for candidate_filings query")
                return []

            api_params = {
                "api_key": self.api_key,
                "candidate_id": candidate_id,
                "per_page": per_page,
            }

            if filing_type:
                api_params["form_type"] = filing_type

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.BASE_URL}/filings/",
                        params=api_params,
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    data = response.json()

                    results = data.get("results", [])
                    filings = []
                    for filing in results:
                        filings.append({
                            "filing_id": filing.get("file_number", ""),
                            "form_type": filing.get("form_type", ""),
                            "report_type": filing.get("report_type", ""),
                            "coverage_start": filing.get("coverage_start_date", ""),
                            "coverage_end": filing.get("coverage_end_date", ""),
                            "total_receipts": filing.get("total_receipts", 0),
                            "total_disbursements": filing.get("total_disbursements", 0),
                            "url": f"https://www.fec.gov/data/filings/?data_type=processed&committee_id={filing.get('committee_id', '')}" if filing.get("committee_id") else "",
                        })

                    return filings

            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as e:
                print(f"WARNING: FEC execute_query (candidate_filings) failed: {e}")
                return []

        else:
            print(f"WARNING: Unknown FEC query type: {query_type}")
            return []
