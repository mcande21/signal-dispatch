"""Federal Register API adapter for OSINT data collection.

Monitors rules, appointments, and regulatory actions from federalregister.gov.
Free REST API, no authentication required.
"""

import hashlib
import json
from datetime import datetime, timezone, timedelta

import httpx

from ..models import OsintResult


class FederalRegisterApiError(Exception):
    """Error from Federal Register API interaction."""
    def __init__(self, message: str, status_code: int | None = None, retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class FederalRegisterAdapter:
    """Federal Register API adapter. Monitors rules, appointments, and regulatory actions."""

    BASE_URL = "https://www.federalregister.gov/api/v1"

    async def fetch(self, market_data: dict, db) -> OsintResult | None:
        """Fetch Federal Register documents relevant to market.

        Args:
            market_data: Dict with market title, category, rules
            db: Database instance for caching

        Returns:
            OsintResult or None if no relevant documents
        """
        # Extract search terms from market title and rules
        search_terms = self._extract_search_terms(market_data)
        if not search_terms:
            return None

        # Generate query hash for caching
        query_hash = hashlib.sha256(
            json.dumps({"terms": search_terms, "source": "federal_register"}, sort_keys=True).encode()
        ).hexdigest()[:16]

        # Check query cache first
        if db:
            cached = await db.get_cached_osint_query(query_hash)
            if cached:
                return OsintResult(**cached)

        # Cache miss - search documents
        documents = await self._search_documents(search_terms, since_days=30, db=db)

        if not documents:
            return None

        # Build OsintResult
        fetch_time = datetime.now(timezone.utc).isoformat()
        staleness = self._compute_staleness(documents)

        result = OsintResult(
            source="federal_register",
            source_url=f"{self.BASE_URL}/documents.json?conditions[term]={'+'.join(search_terms)}",
            fetch_time=fetch_time,
            data_points=documents,
            staleness_hours=staleness,
            confidence=self._assess_confidence(documents, market_data),
            summary=self._generate_summary(documents, market_data),
            market_relevance=self._assess_relevance(documents, market_data),
        )

        # Cache the result
        if db:
            await db.cache_osint_query_result(query_hash, "federal_register", result.__dict__)

        return result

    def _extract_search_terms(self, market_data: dict) -> list[str]:
        """Extract meaningful search terms from market title and rules.

        Args:
            market_data: Dict with title and rules_primary/rules_secondary

        Returns:
            List of search queries
        """
        title = market_data.get("title", "")
        rules_primary = market_data.get("rules_primary", "")
        rules_secondary = market_data.get("rules_secondary", "")

        combined = f"{title} {rules_primary} {rules_secondary}".lower()

        # Extract entities: capitalized words, agencies, proper nouns
        # Simple regex: words starting with capital or known agency abbreviations
        terms = []

        # Known federal agencies (partial list - expand as needed)
        agencies = [
            "EPA", "FDA", "FCC", "SEC", "DOJ", "HHS", "DOD", "DHS", "DOE",
            "Treasury", "Commerce", "Labor", "Education", "Interior"
        ]

        for agency in agencies:
            if agency.lower() in combined:
                terms.append(agency)

        # Extract proper nouns (words that remain capitalized in title)
        title_words = title.split()
        for word in title_words:
            if word and word[0].isupper() and len(word) > 3:
                # Skip common words
                if word not in ("Will", "Does", "What", "When", "Where", "Who", "How", "The", "This"):
                    terms.append(word)

        # De-duplicate
        return list(set(terms))[:5]  # Limit to 5 most relevant terms

    async def _search_documents(
        self,
        terms: list[str],
        since_days: int = 30,
        db=None,
    ) -> list[dict]:
        """Search Federal Register API for documents matching terms.

        Args:
            terms: Search query terms
            since_days: How many days back to search
            db: Database instance for document caching

        Returns:
            List of document dicts
        """
        # Build search query
        query_string = " ".join(terms)
        since_date = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%Y-%m-%d")

        # Check document cache first
        if db:
            cached_docs = await db.get_cached_federal_register_documents(
                query_terms=query_string,
                since_date=since_date,
            )
            if cached_docs:
                return cached_docs

        # Cache miss - call API
        params = {
            "conditions[term]": query_string,
            "conditions[publication_date][gte]": since_date,
            "per_page": 20,
            "page": 1,
        }

        try:
            documents = []
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/documents.json",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                # Process documents
                for doc in data.get("results", []):
                    doc_cleaned = {
                        "document_number": doc.get("document_number"),
                        "title": doc.get("title"),
                        "type": doc.get("type"),
                        "abstract": doc.get("abstract"),
                        "agencies": [a.get("name") for a in doc.get("agencies", [])],
                        "publication_date": doc.get("publication_date"),
                        "html_url": doc.get("html_url"),
                        "pdf_url": doc.get("pdf_url"),
                    }
                    documents.append(doc_cleaned)

                    # Cache individual document
                    if db:
                        await db.cache_federal_register_document(doc_cleaned, query_string)

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise FederalRegisterApiError("Federal Register API rate limit exceeded", status_code=429, retryable=True) from e
            elif 500 <= status_code < 600:
                raise FederalRegisterApiError(f"Federal Register API server error: {status_code}", status_code=status_code, retryable=True) from e
            else:
                raise FederalRegisterApiError(f"Federal Register API HTTP error: {status_code}", status_code=status_code) from e
        except httpx.ConnectError as e:
            raise FederalRegisterApiError("Cannot connect to Federal Register API", retryable=True) from e
        except httpx.TimeoutException as e:
            raise FederalRegisterApiError("Federal Register API request timed out", retryable=True) from e

        return documents

    async def check_updates(self, since: str, db) -> list[dict]:
        """Poll for new documents since last check. For monitoring mode.

        Args:
            since: ISO date string (YYYY-MM-DD)
            db: Database instance

        Returns:
            List of NEW document dicts (not in cache)
        """
        # Query API for documents since date
        params = {
            "conditions[publication_date][gte]": since,
            "per_page": 100,
            "page": 1,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/documents.json",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                new_documents = []
                for doc in data.get("results", []):
                    doc_number = doc.get("document_number")

                    # Check if already cached
                    if db:
                        cursor = await db.conn.execute(
                            "SELECT 1 FROM osint_federal_register WHERE document_number = ?",
                            (doc_number,)
                        )
                        row = await cursor.fetchone()
                        if row:
                            continue  # Already cached, skip

                    # New document
                    doc_cleaned = {
                        "document_number": doc_number,
                        "title": doc.get("title"),
                        "type": doc.get("type"),
                        "abstract": doc.get("abstract"),
                        "agencies": [a.get("name") for a in doc.get("agencies", [])],
                        "publication_date": doc.get("publication_date"),
                        "html_url": doc.get("html_url"),
                        "pdf_url": doc.get("pdf_url"),
                    }
                    new_documents.append(doc_cleaned)

                    # Cache it
                    if db:
                        await db.cache_federal_register_document(doc_cleaned, query_terms="")

                return new_documents

        except httpx.HTTPStatusError as e:
            raise FederalRegisterApiError(f"HTTP error: {e.response.status_code}", status_code=e.response.status_code) from e

    def _compute_staleness(self, documents: list[dict]) -> float:
        """Compute average staleness of documents in hours.

        Args:
            documents: List of document dicts

        Returns:
            Average hours since publication
        """
        if not documents:
            return 0.0

        now = datetime.now(timezone.utc)
        total_hours = 0.0

        for doc in documents:
            pub_date_str = doc.get("publication_date")
            if not pub_date_str:
                continue

            try:
                pub_date = datetime.fromisoformat(pub_date_str).replace(tzinfo=timezone.utc)
                hours_since = (now - pub_date).total_seconds() / 3600
                total_hours += hours_since
            except (ValueError, TypeError):
                continue

        return total_hours / len(documents) if documents else 0.0

    def _assess_confidence(self, documents: list[dict], _market_data: dict) -> float:
        """Adapter's self-assessed reliability of this data.

        Args:
            documents: List of document dicts
            market_data: Market metadata

        Returns:
            Confidence score 0.0-1.0
        """
        if not documents:
            return 0.0

        # Base confidence on number of results and relevance
        doc_count = len(documents)
        confidence = min(0.5 + (doc_count * 0.05), 1.0)  # More results = higher confidence

        # Boost if official agencies involved
        official_agencies = ["Treasury", "SEC", "EPA", "FDA", "FCC"]
        for doc in documents:
            agencies = doc.get("agencies", [])
            if any(agency in official_agencies for agency in agencies):
                confidence = min(confidence + 0.1, 1.0)
                break

        return round(confidence, 2)

    def _assess_relevance(self, documents: list[dict], market_data: dict) -> float:
        """How relevant are these documents to the market question?

        Args:
            documents: List of document dicts
            market_data: Market metadata

        Returns:
            Relevance score 0.0-1.0
        """
        if not documents:
            return 0.0

        title = market_data.get("title", "").lower()
        title_words = set(title.split())

        # Count keyword matches in document titles
        match_count = 0
        total_docs = len(documents)

        for doc in documents:
            doc_title = doc.get("title", "").lower()
            doc_words = set(doc_title.split())

            # Check overlap
            overlap = title_words & doc_words
            if len(overlap) > 2:  # At least 3 words in common
                match_count += 1

        relevance = match_count / total_docs if total_docs > 0 else 0.0
        return round(relevance, 2)

    def _generate_summary(self, documents: list[dict], _market_data: dict) -> str:
        """Generate human-readable one-liner summary.

        Args:
            documents: List of document dicts
            market_data: Market metadata

        Returns:
            One-line summary string
        """
        if not documents:
            return "No relevant Federal Register documents found"

        doc_count = len(documents)
        doc_types = set(doc.get("type") for doc in documents)
        agencies = set()
        for doc in documents:
            agencies.update(doc.get("agencies", []))

        summary_parts = [
            f"Found {doc_count} Federal Register documents",
        ]

        if doc_types:
            types_str = ", ".join(sorted(t for t in doc_types if t is not None)[:3])
            summary_parts.append(f"Types: {types_str}")

        if agencies:
            agencies_str = ", ".join(sorted(a for a in agencies if a is not None)[:3])
            summary_parts.append(f"Agencies: {agencies_str}")

        return " | ".join(summary_parts)

    async def execute_query(self, query: dict) -> list[dict]:
        """Execute a structured query plan.

        Args:
            query: dict with keys:
                - type: str -- query type (e.g., "document_search")
                - params: dict -- API parameters

        Returns:
            List of result dicts with standardized fields.
        """
        query_type = query.get("type")
        params = query.get("params", {})

        if query_type == "document_search":
            # Map params to API request
            term = params.get("term", "")
            agencies = params.get("agencies", [])
            doc_types = params.get("type", [])
            date_gte = params.get("date_gte")
            date_lte = params.get("date_lte")
            per_page = params.get("per_page", 20)

            # Build API params
            api_params = {
                "conditions[term]": term,
                "per_page": per_page,
                "page": 1,
            }

            if date_gte:
                api_params["conditions[publication_date][gte]"] = date_gte
            if date_lte:
                api_params["conditions[publication_date][lte]"] = date_lte

            # Federal Register API doesn't support agency/type filtering via params cleanly
            # We'll rely on term search and client-side filtering if needed

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.BASE_URL}/documents.json",
                        params=api_params,
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    data = response.json()

                    # Process documents
                    documents = []
                    for doc in data.get("results", []):
                        # Client-side filtering for agencies and document types if specified
                        doc_agencies = doc.get("agencies", [])
                        doc_type = doc.get("type", "")

                        # Filter by agencies if specified
                        if agencies:
                            agency_names = [a.get("name", "") for a in doc_agencies]
                            if not any(agency.lower() in name.lower() for agency in agencies for name in agency_names):
                                continue

                        # Filter by document type if specified
                        if doc_types and doc_type.lower() not in [t.lower() for t in doc_types]:
                            continue
                        doc_cleaned = {
                            "document_number": doc.get("document_number"),
                            "title": doc.get("title"),
                            "type": doc.get("type"),
                            "abstract": doc.get("abstract"),
                            "agencies": [a.get("name") for a in doc.get("agencies", [])],
                            "publication_date": doc.get("publication_date"),
                            "html_url": doc.get("html_url"),
                            "pdf_url": doc.get("pdf_url"),
                        }
                        documents.append(doc_cleaned)

                    return documents

            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as e:
                print(f"WARNING: Federal Register execute_query failed: {e}")
                return []

        else:
            print(f"WARNING: Unknown Federal Register query type: {query_type}")
            return []
