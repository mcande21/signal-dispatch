"""OpenSanctions adapter.

Source: https://api.opensanctions.org
Auth: None required for basic queries
TTL: 24h (dataset updated daily)

Aggregates sanctions data across OFAC, EU, UN, and 30+ jurisdictions.
Upgrades SD's OFAC-only coverage to global multi-jurisdiction signals.
"""

import asyncio
import os
from datetime import datetime, timezone

import httpx

from .base import GhostMarketAdapter, GhostMarketApiError


OPENSANCTIONS_BASE_URL = "https://api.opensanctions.org"

DEFAULT_SEARCH_TERMS = ["Iran", "Russia", "Wagner", "Houthis"]

# Minimum jurisdictions for cross-jurisdiction coordinated sanctions flag
CROSS_JURISDICTION_THRESHOLD = 3

# Maximum entities to return per search term
MAX_ENTITIES_PER_TERM = 20


class OpenSanctionsAdapter(GhostMarketAdapter):
    """OpenSanctions global sanctions adapter with cache-first pattern.

    Searches across OFAC, EU FSF, UN consolidated list, and 30+ other
    sanctions registries. Returns unified entity data and cross-jurisdiction
    coordination signals - signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str, search_terms: list[str] | None = None):
        super().__init__(db_path)
        self.search_terms = search_terms if search_terms is not None else DEFAULT_SEARCH_TERMS

    @staticmethod
    def _auth_headers() -> dict:
        """Return Authorization header if OPENSANCTIONS_API_KEY is set."""
        key = os.environ.get("OPENSANCTIONS_API_KEY")
        if key:
            return {"Authorization": f"ApiKey {key}"}
        return {}

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 24 hours."""
        return 86400

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "opensanctions"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of OpenSanctions data.

        Args:
            query: {
                "search_terms": list[str] (optional, defaults to adapter default terms)
            }

        Returns:
            {
                "source": "opensanctions",
                "dataset": {
                    "entity_count": int,
                    "last_updated": str,
                },
                "searches": {
                    "<term>": {
                        "total_results": int,
                        "entities": [
                            {
                                "id": str,
                                "name": str,
                                "schema": str,
                                "datasets": [str],
                                "first_seen": str,
                                "last_seen": str,
                                "countries": [str],
                                "score": float,
                            },
                            ...  # top 20 results
                        ]
                    },
                    ...
                },
                "cross_jurisdiction": [
                    {
                        "name": str,
                        "jurisdictions": [str],
                        "jurisdiction_count": int,
                    },
                    ...
                ]
            }
        """
        search_terms = query.get("search_terms", self.search_terms)
        cache_key = "opensanctions_snapshot"

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # Fetch dataset metadata (optional -- may 404 if endpoint moved)
        try:
            dataset_meta = await self._fetch_dataset_stats()
        except GhostMarketApiError:
            dataset_meta = {"entity_count": None, "last_updated": None}

        searches: dict[str, dict] = {}
        for i, term in enumerate(search_terms):
            # Rate limit: 1s delay between search queries (after first)
            if i > 0:
                await asyncio.sleep(1)
            try:
                searches[term] = await self._search_entities(term)
            except GhostMarketApiError as e:
                if e.retryable:
                    await asyncio.sleep(2)
                    searches[term] = await self._search_entities(term)
                else:
                    raise

        cross_jurisdiction = self._compute_cross_jurisdiction(searches)

        result = {
            "source": "opensanctions",
            "dataset": dataset_meta,
            "searches": searches,
            "cross_jurisdiction": cross_jurisdiction,
        }

        await self._cache_store(cache_key, result)
        return result

    async def _fetch_dataset_stats(self) -> dict:
        """Fetch dataset metadata from /datasets/default.

        Returns:
            {
                "entity_count": int,
                "last_updated": str,
            }
        """
        url = f"{OPENSANCTIONS_BASE_URL}/datasets/default"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self._auth_headers(), timeout=30.0)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            raise self._classify_http_error(e, "dataset stats") from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to OpenSanctions", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "OpenSanctions dataset request timed out", retryable=True
            ) from e

        return {
            "entity_count": data.get("entity_count", 0),
            "last_updated": data.get("last_change") or data.get("updated_at") or datetime.now(timezone.utc).isoformat(),
        }

    async def _search_entities(self, term: str) -> dict:
        """Search entities via /search/default.

        Args:
            term: Search query string

        Returns:
            {
                "total_results": int,
                "entities": [entity_dict, ...]  # top MAX_ENTITIES_PER_TERM
            }
        """
        url = f"{OPENSANCTIONS_BASE_URL}/search/default"
        params = {"q": term, "limit": 50}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=self._auth_headers(), timeout=30.0)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            raise self._classify_http_error(e, f"search '{term}'") from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to OpenSanctions", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                f"OpenSanctions search request timed out for '{term}'", retryable=True
            ) from e

        raw_results = data.get("results", [])
        total = data.get("total", {})
        # total can be int or {"value": int, ...} depending on API version
        if isinstance(total, dict):
            total_count = total.get("value", len(raw_results))
        else:
            total_count = int(total) if total else len(raw_results)

        entities = []
        for item in raw_results[:MAX_ENTITIES_PER_TERM]:
            entities.append(self._normalize_entity(item))

        return {
            "total_results": total_count,
            "entities": entities,
        }

    def _normalize_entity(self, raw: dict) -> dict:
        """Normalize a raw OpenSanctions result to the SD entity shape.

        Args:
            raw: Raw entity dict from OpenSanctions API

        Returns:
            Normalized entity dict
        """
        properties = raw.get("properties", {})

        # Name: prefer caption, fall back to properties.name list
        name = raw.get("caption", "")
        if not name:
            name_list = properties.get("name", [])
            name = name_list[0] if name_list else raw.get("id", "")

        # Countries: from properties.country or properties.jurisdiction
        countries = list({
            c for field in ("country", "jurisdiction", "nationality")
            for c in properties.get(field, [])
            if c
        })

        return {
            "id": raw.get("id", ""),
            "name": name,
            "schema": raw.get("schema", ""),
            "datasets": raw.get("datasets", []),
            "first_seen": raw.get("first_seen", ""),
            "last_seen": raw.get("last_seen", ""),
            "countries": countries,
            "score": float(raw.get("score", 0.0)),
        }

    def _compute_cross_jurisdiction(self, searches: dict[str, dict]) -> list[dict]:
        """Identify entities appearing in 3+ jurisdictions across all searches.

        Entities sanctioned by multiple countries signal coordinated international
        action - the high-value output for geopolitical intelligence.

        Args:
            searches: Dict of term -> search result dicts

        Returns:
            List of cross-jurisdiction entity dicts, sorted by jurisdiction_count desc
        """
        # Collect all entities, tracking datasets per unique entity id
        entity_datasets: dict[str, set[str]] = {}
        entity_names: dict[str, str] = {}

        for term_results in searches.values():
            for entity in term_results.get("entities", []):
                eid = entity["id"]
                if not eid:
                    continue
                if eid not in entity_datasets:
                    entity_datasets[eid] = set()
                    entity_names[eid] = entity["name"]
                entity_datasets[eid].update(entity.get("datasets", []))

        cross = []
        for eid, datasets in entity_datasets.items():
            if len(datasets) >= CROSS_JURISDICTION_THRESHOLD:
                jurisdictions = sorted(datasets)
                cross.append({
                    "name": entity_names[eid],
                    "jurisdictions": jurisdictions,
                    "jurisdiction_count": len(jurisdictions),
                })

        # Sort by jurisdiction_count descending (most coordinated first)
        cross.sort(key=lambda x: x["jurisdiction_count"], reverse=True)
        return cross

    @staticmethod
    def _classify_http_error(e: httpx.HTTPStatusError, context: str) -> GhostMarketApiError:
        """Map HTTP status codes to GhostMarketApiError with retryable flag.

        Args:
            e: The httpx HTTPStatusError
            context: Human-readable context for the error message

        Returns:
            GhostMarketApiError with appropriate retryable flag
        """
        status_code = e.response.status_code
        if status_code == 429:
            return GhostMarketApiError(
                f"OpenSanctions rate limit exceeded ({context})",
                status_code=429,
                retryable=True,
            )
        if 500 <= status_code < 600:
            return GhostMarketApiError(
                f"OpenSanctions server error: {status_code} ({context})",
                status_code=status_code,
                retryable=True,
            )
        return GhostMarketApiError(
            f"OpenSanctions HTTP error: {status_code} ({context})",
            status_code=status_code,
        )
