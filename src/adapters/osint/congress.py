"""Congress.gov API adapter for legislative intelligence.

Tracks bills, votes, and legislative actions relevant to prediction markets.
API docs: https://api.congress.gov/
"""

import asyncio
import hashlib
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import httpx

from ..models import OsintResult


class CongressApiError(Exception):
    """Error from Congress.gov API interaction."""
    def __init__(self, message: str, status_code: int | None = None, retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class CongressAdapter:
    """Congress.gov API adapter. Tracks bill status, floor votes, committee actions."""

    BASE_URL = "https://api.congress.gov/v3"
    DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "osint_cache.db"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("CONGRESS_API_KEY", "")

    async def fetch(self, market_data: dict, _db=None) -> OsintResult | None:
        """Fetch congressional activity relevant to market.

        Args:
            market_data: Market dict with 'title' and optionally 'rules_primary'
            db: Database instance (unused, kept for interface compatibility)

        Returns:
            OsintResult with bill status + recent actions, or None if no API key
        """
        if not self.api_key:
            print("WARNING: CONGRESS_API_KEY not set. Skipping Congress.gov fetch.")
            return None

        # 1. Extract search terms from market title + rules
        terms = self._extract_search_terms(market_data)
        if not terms:
            return None

        # 2. Build cache key from terms
        cache_key = hashlib.sha256(",".join(sorted(terms)).encode()).hexdigest()

        # 3. Check cache (TTL = 4h)
        cached = self._get_cached(cache_key, ttl_hours=4)
        if cached:
            return self._cached_to_result(cached)

        # 4. Search for relevant bills
        try:
            bills = await self._search_bills(terms)
        except CongressApiError as e:
            if e.retryable:
                await asyncio.sleep(2)
                bills = await self._search_bills(terms)
            else:
                raise

        if not bills:
            return None

        # 5. For top bills, fetch detailed actions
        data_points = []
        for bill in bills[:3]:  # Limit to top 3 most relevant
            try:
                actions = await self._get_bill_actions(
                    bill["congress"],
                    bill["type"],
                    bill["number"]
                )
                bill["actions"] = actions
                data_points.append(bill)
            except CongressApiError:
                # Skip this bill if actions fetch fails
                continue

        if not data_points:
            return None

        # 6. Build result
        fetch_time = datetime.now(timezone.utc).isoformat()
        summary = self._build_summary(data_points)
        relevance = self._compute_relevance(market_data, data_points)

        # Latest action time determines staleness
        latest_action_date = max(
            (dt for bill in data_points
             for action in bill.get("actions", [])
             if action.get("actionDate")
             if (dt := self._parse_date(action["actionDate"])) is not None),
            default=None
        )
        if latest_action_date:
            staleness_hours = (datetime.now(timezone.utc) - latest_action_date).total_seconds() / 3600
        else:
            staleness_hours = 999.0

        result = OsintResult(
            source="congress_gov",
            source_url=f"{self.BASE_URL}/bill",
            fetch_time=fetch_time,
            data_points=data_points,
            staleness_hours=staleness_hours,
            confidence=0.7,  # API is authoritative but interpretation is heuristic
            summary=summary,
            market_relevance=relevance,
        )

        # 7. Cache the result
        self._cache_result(cache_key, result)

        return result

    def _extract_search_terms(self, market_data: dict) -> list[str]:
        """Extract bill numbers, policy topics, member names from market data."""
        title = market_data.get("title", "")
        rules = market_data.get("rules_primary", "")
        text = f"{title} {rules}"

        terms = []

        # Extract bill patterns: H.R. XXXX, S. XXXX, H.Res. XXX, etc.
        bill_patterns = re.findall(r"\b([HS]\.(?:R\.|J\.Res\.|Con\.Res\.|Res\.)\s*\d+)\b", text, re.IGNORECASE)
        terms.extend(bill_patterns)

        # Extract policy keywords (simple heuristic for now)
        keywords = re.findall(r"\b(bill|legislation|congress|senate|house)\b", text, re.IGNORECASE)
        terms.extend(keywords)

        return list(set(terms))  # Deduplicate

    async def _search_bills(self, terms: list[str], congress: int = 119) -> list[dict]:
        """Search for bills matching terms in the current Congress.

        Returns list of bill dicts with: congress, type, number, title, url
        """
        # Congress.gov API doesn't have a search endpoint that takes arbitrary terms.
        # We'll query the /bill endpoint sorted by updateDate and filter client-side.
        params = {
            "format": "json",
            "limit": 50,
            "offset": 0,
            "api_key": self.api_key,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/bill/{congress}",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise CongressApiError("Congress.gov API rate limit exceeded", status_code=429, retryable=True) from e
            elif status_code == 401 or status_code == 403:
                raise CongressApiError("Invalid Congress.gov API key", status_code=status_code) from e
            elif 500 <= status_code < 600:
                raise CongressApiError(f"Congress.gov API server error: {status_code}", status_code=status_code, retryable=True) from e
            else:
                raise CongressApiError(f"Congress.gov API HTTP error: {status_code}", status_code=status_code) from e
        except httpx.ConnectError as e:
            raise CongressApiError("Cannot connect to Congress.gov API", retryable=True) from e
        except httpx.TimeoutException as e:
            raise CongressApiError("Congress.gov API request timed out", retryable=True) from e

        # Extract bill list and filter by terms
        bills_raw = data.get("bills", [])
        bills_matched = []

        for bill in bills_raw:
            # Bill fields are at top level, not nested under "bill" key
            title = bill.get("title", "")
            number = bill.get("number", "")

            # Simple relevance: check if any term appears in title or bill number
            match_score = sum(
                1 for term in terms
                if term.lower() in title.lower() or term.lower() in str(number).lower()
            )

            if match_score > 0:
                bills_matched.append({
                    "congress": bill.get("congress"),
                    "type": bill.get("type"),
                    "number": number,
                    "title": title,
                    "url": bill.get("url", ""),
                    "match_score": match_score,
                })

        # Sort by match score descending
        bills_matched.sort(key=lambda b: b["match_score"], reverse=True)

        return bills_matched

    async def _get_bill_actions(self, congress: int, bill_type: str, bill_number: int) -> list[dict]:
        """Get recent actions on a specific bill.

        Returns list of action dicts with: actionDate, text, type
        """
        params = {
            "format": "json",
            "limit": 20,
            "api_key": self.api_key,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/bill/{congress}/{bill_type.lower()}/{bill_number}/actions",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise CongressApiError("Congress.gov API rate limit exceeded", status_code=429, retryable=True) from e
            elif 500 <= status_code < 600:
                raise CongressApiError(f"Congress.gov API server error: {status_code}", status_code=status_code, retryable=True) from e
            else:
                raise CongressApiError(f"Congress.gov API HTTP error: {status_code}", status_code=status_code) from e
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise CongressApiError("Congress.gov API network error", retryable=True) from e

        actions_raw = data.get("actions", [])
        actions = []
        for action_data in actions_raw:
            action = action_data.get("action", {})
            actions.append({
                "actionDate": action.get("actionDate", ""),
                "text": action.get("text", ""),
                "type": action.get("type", ""),
            })

        return actions

    async def check_updates(self, since: str, _db=None) -> list[dict]:
        """Poll for new legislative actions since last check.

        Args:
            since: ISO timestamp of last check
            db: Database instance (unused)

        Returns:
            List of bills with updates since the timestamp
        """
        if not self.api_key:
            return []

        # Query bills sorted by updateDate desc, filter since timestamp
        params = {
            "format": "json",
            "limit": 100,
            "offset": 0,
            "api_key": self.api_key,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/bill/119",  # Current congress
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError:
            return []

        bills_raw = data.get("bills", [])
        since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))

        updates = []
        for bill in bills_raw:
            # Bill fields are at top level, not nested under "bill" key
            update_date_str = bill.get("updateDate", "")
            if update_date_str:
                update_date = self._parse_date(update_date_str)
                if update_date and update_date > since_dt:
                    updates.append({
                        "congress": bill.get("congress"),
                        "type": bill.get("type"),
                        "number": bill.get("number"),
                        "title": bill.get("title", ""),
                        "updateDate": update_date_str,
                    })

        return updates

    def _build_summary(self, data_points: list[dict]) -> str:
        """Build human-readable summary from bill data."""
        if not data_points:
            return "No relevant bills found"

        bill = data_points[0]  # Top match
        actions = bill.get("actions", [])
        latest_action = actions[0] if actions else None

        if latest_action:
            return f"{bill['type']} {bill['number']}: {latest_action['text']} ({latest_action['actionDate']})"
        else:
            return f"{bill['type']} {bill['number']}: {bill['title']}"

    def _compute_relevance(self, market_data: dict, data_points: list[dict]) -> float:
        """Compute market relevance score (0.0-1.0) based on match quality."""
        if not data_points:
            return 0.0

        # Simple heuristic: top match score / max possible match score
        top_match = data_points[0]
        match_score = top_match.get("match_score", 0)

        # Normalize by number of search terms
        terms = self._extract_search_terms(market_data)
        if not terms:
            return 0.5

        relevance = min(match_score / len(terms), 1.0)
        return relevance

    def _parse_date(self, date_str: str) -> datetime | None:
        """Parse ISO date string to datetime."""
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    # ========================================================================
    # Cache helpers (inline SQLite, will be unified when edi-1's work lands)
    # ========================================================================

    def _get_cached(self, cache_key: str, ttl_hours: int = 4) -> dict | None:
        """Check cache. Returns None on miss or stale."""
        conn = sqlite3.connect(str(self.DB_PATH))
        cursor = conn.cursor()

        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS osint_congress_cache (
                cache_key TEXT PRIMARY KEY,
                data_json TEXT,
                last_fetched TEXT DEFAULT (datetime('now'))
            )
        """)

        # Query cache
        cursor.execute(
            "SELECT data_json, last_fetched FROM osint_congress_cache WHERE cache_key = ?",
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
            CREATE TABLE IF NOT EXISTS osint_congress_cache (
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
            "INSERT OR REPLACE INTO osint_congress_cache (cache_key, data_json, last_fetched) VALUES (?, ?, datetime('now'))",
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
                - type: str -- query type (e.g., "bill_search", "bill_actions")
                - params: dict -- API parameters

        Returns:
            List of result dicts with standardized fields.
        """
        if not self.api_key:
            print("WARNING: CONGRESS_API_KEY not set. Cannot execute query.")
            return []

        query_type = query.get("type")
        params = query.get("params", {})

        if query_type == "bill_search":
            # Map params to bill search
            search_query = params.get("query", "")
            congress = params.get("congress", 119)
            bill_types = params.get("type", [])
            limit = params.get("limit", 20)

            api_params = {
                "format": "json",
                "limit": limit,
                "offset": 0,
                "api_key": self.api_key,
            }

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.BASE_URL}/bill/{congress}",
                        params=api_params,
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    data = response.json()

                    bills_raw = data.get("bills", [])
                    bills = []

                    # Tokenize search query for matching
                    search_terms = []
                    if search_query:
                        search_terms = [term.strip().lower() for term in search_query.split() if term.strip()]

                    for bill in bills_raw:
                        # Bill fields are at top level, not nested under "bill" key
                        title = bill.get("title", "")
                        bill_type = bill.get("type", "")
                        number = bill.get("number", "")

                        # Filter by type if specified
                        if bill_types and bill_type.lower() not in [t.lower() for t in bill_types]:
                            continue

                        # Filter by search query - token-based matching
                        if search_terms:
                            title_lower = title.lower()
                            if not any(term in title_lower for term in search_terms):
                                continue

                        # Extract action info if available
                        latest_action_raw = bill.get("latestAction", {})
                        latest_action = None
                        if latest_action_raw:
                            latest_action = {
                                "date": latest_action_raw.get("actionDate", ""),
                                "text": latest_action_raw.get("text", ""),
                            }

                        # Extract sponsors
                        sponsors_raw = bill.get("sponsors", [])
                        sponsors = []
                        for sponsor_data in sponsors_raw:
                            sponsor = sponsor_data.get("sponsor", {})
                            sponsors.append({
                                "name": sponsor.get("fullName", ""),
                                "party": sponsor.get("party", ""),
                                "state": sponsor.get("state", ""),
                            })

                        bills.append({
                            "bill_id": f"{bill_type}{number}",
                            "title": title,
                            "type": bill_type,
                            "congress": bill.get("congress"),
                            "introduced_date": bill.get("introducedDate", ""),
                            "latest_action": latest_action,
                            "sponsors": sponsors,
                            "url": bill.get("url", ""),
                        })

                    return bills

            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as e:
                print(f"WARNING: Congress.gov execute_query (bill_search) failed: {e}")
                return []

        elif query_type == "bill_actions":
            # Get bill actions - accepts either bill_id or (congress, type, number)
            congress = params.get("congress", 119)
            limit = params.get("limit", 20)

            # Try decomposed params first
            bill_type = params.get("type")
            bill_number = params.get("number")

            # Fall back to parsing bill_id if decomposed params not present
            if not bill_type or not bill_number:
                bill_id = params.get("bill_id", "")
                if not bill_id:
                    print("WARNING: Either (type, number) or bill_id is required for bill_actions query")
                    return []

                # Extract bill type and number from bill_id
                match = re.match(r"([a-z]+)(\d+)", bill_id.lower())
                if not match:
                    print(f"WARNING: Invalid bill_id format: {bill_id}")
                    return []

                bill_type = match.group(1)
                bill_number = match.group(2)

            api_params = {
                "format": "json",
                "limit": limit,
                "api_key": self.api_key,
            }

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.BASE_URL}/bill/{congress}/{bill_type}/{bill_number}/actions",
                        params=api_params,
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    data = response.json()

                    actions_raw = data.get("actions", [])
                    actions = []
                    for action_data in actions_raw:
                        # Handle both nested and top-level action fields
                        action = action_data.get("action", action_data)
                        actions.append({
                            "date": action.get("actionDate", ""),
                            "text": action.get("text", ""),
                            "type": action.get("type", ""),
                            "action_code": action.get("actionCode", ""),
                        })

                    return actions

            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as e:
                print(f"WARNING: Congress.gov execute_query (bill_actions) failed: {e}")
                return []

        elif query_type == "bill_details":
            # Get full bill details by congress/type/number
            congress = params.get("congress", 119)
            bill_type = params.get("type", "")
            bill_number = params.get("number")

            if not bill_type or not bill_number:
                print("WARNING: type and number are required for bill_details query")
                return []

            api_params = {
                "format": "json",
                "api_key": self.api_key,
            }

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.BASE_URL}/bill/{congress}/{bill_type}/{bill_number}",
                        params=api_params,
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    data = response.json()

                    bill = data.get("bill", {})
                    if not bill:
                        return []

                    # Extract latest action
                    latest_action_raw = bill.get("latestAction", {})
                    latest_action = None
                    if latest_action_raw:
                        latest_action = {
                            "date": latest_action_raw.get("actionDate", ""),
                            "text": latest_action_raw.get("text", ""),
                        }

                    # Extract sponsors
                    sponsors_raw = bill.get("sponsors", [])
                    sponsors = []
                    for sponsor in sponsors_raw:
                        sponsors.append({
                            "name": sponsor.get("fullName", ""),
                            "party": sponsor.get("party", ""),
                            "state": sponsor.get("state", ""),
                        })

                    # Committees URL (committees data requires separate API call)
                    committees_url = bill.get("committees", {}).get("url", "")

                    return [{
                        "bill_id": f"{bill.get('type', '')}{bill.get('number', '')}",
                        "title": bill.get("title", ""),
                        "type": bill.get("type", ""),
                        "congress": bill.get("congress"),
                        "introduced_date": bill.get("introducedDate", ""),
                        "latest_action": latest_action,
                        "sponsors": sponsors,
                        "committees_url": committees_url,
                        "url": bill.get("url", ""),
                        "status": latest_action.get("text", "") if latest_action else "",
                    }]

            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as e:
                print(f"WARNING: Congress.gov execute_query (bill_details) failed: {e}")
                return []

        elif query_type == "list_bills":
            # List bills filtered by date range
            congress = params.get("congress", 119)
            from_date = params.get("from_date")
            to_date = params.get("to_date")
            sort = params.get("sort", "updateDate+desc")
            limit = params.get("limit", 50)

            api_params = {
                "format": "json",
                "api_key": self.api_key,
                "limit": limit,
                "sort": sort,
            }

            if from_date:
                api_params["fromDateTime"] = from_date
            if to_date:
                api_params["toDateTime"] = to_date

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.BASE_URL}/bill/{congress}",
                        params=api_params,
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    data = response.json()

                    bills_raw = data.get("bills", [])
                    bills = []

                    for bill in bills_raw:
                        # Extract latest action
                        latest_action_raw = bill.get("latestAction", {})
                        latest_action = None
                        if latest_action_raw:
                            latest_action = {
                                "date": latest_action_raw.get("actionDate", ""),
                                "text": latest_action_raw.get("text", ""),
                            }

                        bills.append({
                            "bill_id": f"{bill.get('type', '')}{bill.get('number', '')}",
                            "title": bill.get("title", ""),
                            "type": bill.get("type", ""),
                            "congress": bill.get("congress"),
                            "introduced_date": bill.get("introducedDate", ""),
                            "latest_action": latest_action,
                            "url": bill.get("url", ""),
                        })

                    return bills

            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as e:
                print(f"WARNING: Congress.gov execute_query (list_bills) failed: {e}")
                return []

        else:
            print(f"WARNING: Unknown Congress.gov query type: {query_type}")
            return []
