"""OFAC SDN List adapter.

Source: https://www.treasury.gov/ofac/downloads/sdn.csv
Auth: None required
TTL: 24h (updated frequently, check daily)
"""

import asyncio
import csv
from datetime import datetime, timezone
from io import StringIO

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


# OFAC SDN CSV URL
OFAC_SDN_CSV_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"


class OfacAdapter(GhostMarketAdapter):
    """OFAC SDN List adapter with cache-first pattern.

    Tracks daily diffs of Iran-related sanctions entities.
    Returns raw SDN data and diff computations - signal interpretation handled by agent layer.
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
        return "ofac"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of OFAC SDN list.

        Args:
            query: {"filter": str (optional, default "IRAN")}

        Returns:
            {
                "snapshot": [{"name": str, "type": str, "program": str}, ...],
                "diff": {
                    "additions": [entity_dict, ...],
                    "removals": [entity_dict, ...],
                    "net_change": int
                },
                "last_updated": str,
            }
        """
        filter_keyword = query.get("filter", "IRAN")
        cache_key = "iran_sdn_snapshot"

        # 1. Check cache for previous snapshot
        cached = await self._cache_lookup(cache_key)

        # If cache hit, build result from cache without re-fetching
        if cached:
            # Return cached result with empty diff (since we're not comparing)
            return {
                "snapshot": cached["snapshot"],
                "diff": {"additions": [], "removals": [], "net_change": 0},
                "last_updated": cached["last_updated"],
            }

        # 2. Cache miss -- fetch current snapshot with retry for retryable errors
        try:
            current_snapshot = await self._call_ofac_api(filter_keyword)
        except GhostMarketApiError as e:
            if e.retryable:
                await asyncio.sleep(2)
                current_snapshot = await self._call_ofac_api(filter_keyword)
            else:
                raise

        # 3. Build result (first run has no diff)
        result = {
            "snapshot": current_snapshot,
            "diff": {"additions": [], "removals": [], "net_change": 0},
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        # 4. Cache the new snapshot (store just snapshot and timestamp)
        await self._cache_store(cache_key, {
            "snapshot": current_snapshot,
            "last_updated": result["last_updated"],
        })

        return result

    async def _call_ofac_api(self, filter_keyword: str) -> list[dict]:
        """Fetch and parse OFAC SDN CSV, filter by keyword.

        Args:
            filter_keyword: Filter entities by program (e.g., "IRAN")

        Returns:
            List of filtered entity dicts
        """
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(OFAC_SDN_CSV_URL, timeout=30.0)
                response.raise_for_status()  # httpx raises synchronously
                csv_text = response.text
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "OFAC rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"OFAC server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"OFAC HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to OFAC", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "OFAC request timed out", retryable=True
            ) from e

        # Parse CSV - no header row, positional columns
        # Column 0: ent_num, Column 1: SDN_Name, Column 2: SDN_Type, Column 3: Program
        reader = csv.reader(StringIO(csv_text))
        filtered_entities = []

        for row in reader:
            if len(row) < 4:
                continue
            # Column 3 contains program/country designations
            program = row[3].strip()
            # Skip placeholder values
            if program == "-0-":
                program = ""
            if filter_keyword.upper() in program.upper():
                filtered_entities.append({
                    "ent_num": row[0].strip(),
                    "name": row[1].strip().strip('"'),
                    "type": row[2].strip() if row[2].strip() != "-0-" else "entity",
                    "program": program,
                })

        return filtered_entities

    def _compute_diff(
        self, previous: list[dict], current: list[dict]
    ) -> dict:
        """Compute additions and removals between snapshots.

        Args:
            previous: Previous snapshot entity list
            current: Current snapshot entity list

        Returns:
            {
                "additions": [entity, ...],
                "removals": [entity, ...],
                "net_change": int (positive = additions, negative = removals)
            }
        """
        # Use ent_num as unique identifier
        previous_nums = {e["ent_num"] for e in previous if e["ent_num"]}
        current_nums = {e["ent_num"] for e in current if e["ent_num"]}

        added_nums = current_nums - previous_nums
        removed_nums = previous_nums - current_nums

        additions = [e for e in current if e["ent_num"] in added_nums]
        removals = [e for e in previous if e["ent_num"] in removed_nums]

        net_change = len(additions) - len(removals)

        return {
            "additions": additions,
            "removals": removals,
            "net_change": net_change,
        }
