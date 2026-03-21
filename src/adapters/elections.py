"""MEDSL (MIT Election Data + Science Lab) historical election results adapter.

Provides county-level and district-level election results for analyzing voter
turnout patterns -- primary use case: SAVE Act voter ID impact analysis.

Sources:
  - Constituency returns: https://github.com/MEDSL/constituency-returns
  - County presidential returns: https://github.com/MEDSL/county-returns
  - 2024 official results: https://github.com/MEDSL/2024-elections-official

Auth: None required (public data)
TTL: 90 days (election data is static after certification)
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone

import httpx

from .base import GhostMarketAdapter, GhostMarketApiError


log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dataset URLs
# ---------------------------------------------------------------------------

# Constituency-level (state/district) returns -- covers 1976-2018
_HOUSE_URL = (
    "https://raw.githubusercontent.com/MEDSL/constituency-returns/master/"
    "1976-2018-house.csv"
)
_SENATE_URL = (
    "https://raw.githubusercontent.com/MEDSL/constituency-returns/master/"
    "1976-2018-senate.csv"
)

# County-level presidential returns -- 2000-2016
_COUNTY_PRES_URL = (
    "https://raw.githubusercontent.com/MEDSL/county-returns/master/"
    "countypres_2000-2016.csv"
)

# 2024 official state-level presidential results
_PRES_2024_STATE_URL = (
    "https://raw.githubusercontent.com/MEDSL/2024-elections-official/main/"
    "2024-president-state.csv"
)

# 2024 official state-level senate results
_SENATE_2024_STATE_URL = (
    "https://raw.githubusercontent.com/MEDSL/2024-elections-official/main/"
    "2024-senate-state.csv"
)

# Cache keys for each dataset
_CACHE_HOUSE = "elections_house_1976_2018"
_CACHE_SENATE = "elections_senate_1976_2018"
_CACHE_COUNTY_PRES = "elections_county_pres_2000_2016"
_CACHE_PRES_2024 = "elections_pres_2024_state"
_CACHE_SENATE_2024 = "elections_senate_2024_state"


class ElectionsAdapter(GhostMarketAdapter):
    """MEDSL election results adapter with cache-first pattern.

    Downloads and caches CSV datasets from MEDSL GitHub repositories.
    Provides query methods for house results, county presidential returns,
    state-level turnout proxies, and before/after state comparisons.

    fetch() dispatches on query["method"]:
        - house_results
        - county_presidential
        - turnout_by_state
        - state_comparison
    """

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 90 days (election data is static post-certification)."""
        return 90 * 24 * 3600

    @property
    def source_name(self) -> str:
        return "elections"

    async def fetch(self, query: dict) -> dict:
        """Dispatch to method handler based on query["method"].

        Methods:
            house_results:
                Params: year (int), state (str, optional -- state_po abbreviation)
                Returns district-level House results.

            county_presidential:
                Params: year (int), state (str, optional)
                Returns county-level presidential results.

            turnout_by_state:
                Params: year (int)
                Returns state-level turnout derived from presidential results.

            state_comparison:
                Params: years (list[int]), states (list[str]),
                        office (str: "house"/"president"/"senate")
                Returns results for specified states across years -- useful
                for before/after voter ID law analysis.
        """
        method = query.get("method", "house_results")

        if method == "house_results":
            return await self._house_results(query)
        elif method == "county_presidential":
            return await self._county_presidential(query)
        elif method == "turnout_by_state":
            return await self._turnout_by_state(query)
        elif method == "state_comparison":
            return await self._state_comparison(query)
        else:
            raise GhostMarketApiError(
                f"elections: unknown method '{method}'. "
                "Valid: house_results, county_presidential, "
                "turnout_by_state, state_comparison",
                retryable=False,
            )

    # -------------------------------------------------------------------------
    # Method handlers
    # -------------------------------------------------------------------------

    async def _house_results(self, query: dict) -> dict:
        """Return district-level House results for a given year and optional state.

        Returns:
            {
                "method": "house_results",
                "year": int,
                "state": str | None,
                "data": list[{
                    "year": int,
                    "state": str,
                    "state_po": str,
                    "district": str,
                    "stage": str,
                    "candidate": str,
                    "party": str,
                    "candidatevotes": int,
                    "totalvotes": int,
                    "vote_share": float,
                }]
            }
        """
        year = query.get("year")
        state_filter = _normalize_state(query.get("state"))

        rows = await self._load_dataset(_CACHE_HOUSE, _HOUSE_URL)

        results = []
        for row in rows:
            row_year = _safe_int(row.get("year"))
            if year is not None and row_year != year:
                continue
            row_state = row.get("state_po", "").upper()
            if state_filter and row_state != state_filter:
                continue
            # Only general election results (exclude primaries, runoffs)
            stage = row.get("stage", "").lower()
            if stage not in ("gen", "general", ""):
                continue

            candidate_votes = _safe_int(row.get("candidatevotes", 0))
            total_votes = _safe_int(row.get("totalvotes", 0))
            vote_share = (candidate_votes / total_votes) if total_votes > 0 else 0.0

            results.append({
                "year": row_year,
                "state": row.get("state", ""),
                "state_po": row_state,
                "district": row.get("district", ""),
                "stage": row.get("stage", ""),
                "candidate": row.get("candidate", ""),
                "party": row.get("party", ""),
                "candidatevotes": candidate_votes,
                "totalvotes": total_votes,
                "vote_share": round(vote_share, 4),
            })

        return {
            "method": "house_results",
            "year": year,
            "state": state_filter,
            "data": results,
        }

    async def _county_presidential(self, query: dict) -> dict:
        """Return county-level presidential results for a given year and optional state.

        Covers 2000-2016 (MEDSL county returns dataset).

        Returns:
            {
                "method": "county_presidential",
                "year": int,
                "state": str | None,
                "data": list[{
                    "year": int,
                    "state": str,
                    "state_po": str,
                    "county": str,
                    "county_fips": str,
                    "candidate": str,
                    "party": str,
                    "candidatevotes": int,
                    "totalvotes": int,
                    "vote_share": float,
                }]
            }
        """
        year = query.get("year")
        state_filter = _normalize_state(query.get("state"))

        rows = await self._load_dataset(_CACHE_COUNTY_PRES, _COUNTY_PRES_URL)

        results = []
        for row in rows:
            row_year = _safe_int(row.get("year"))
            if year is not None and row_year != year:
                continue
            row_state = row.get("state_po", "").upper()
            if state_filter and row_state != state_filter:
                continue

            candidate_votes = _safe_int(row.get("candidatevotes", 0))
            total_votes = _safe_int(row.get("totalvotes", 0))
            vote_share = (candidate_votes / total_votes) if total_votes > 0 else 0.0

            results.append({
                "year": row_year,
                "state": row.get("state", ""),
                "state_po": row_state,
                "county": row.get("county", ""),
                "county_fips": str(row.get("FIPS", "")),
                "candidate": row.get("candidate", ""),
                "party": row.get("party", ""),
                "candidatevotes": candidate_votes,
                "totalvotes": total_votes,
                "vote_share": round(vote_share, 4),
            })

        return {
            "method": "county_presidential",
            "year": year,
            "state": state_filter,
            "data": results,
        }

    async def _turnout_by_state(self, query: dict) -> dict:
        """Return state-level turnout proxy derived from presidential results.

        Aggregates candidatevotes/totalvotes by state. For 2024, uses the
        2024 official state-level file. For 2000-2016, derives from county data.
        For years without dedicated datasets, tries constituency-level.

        Note: These are *votes cast*, not registered voter turnout rate.
        The US Elections Project (electproject.org) publishes VAP turnout but
        requires a separate scrape; this method returns what MEDSL provides.

        Returns:
            {
                "method": "turnout_by_state",
                "year": int,
                "note": str,
                "data": list[{
                    "state": str,
                    "state_po": str,
                    "total_votes": int,
                    "leading_candidate": str,
                    "leading_party": str,
                    "leading_votes": int,
                    "leading_vote_share": float,
                }]
            }
        """
        year = query.get("year")
        if year is None:
            raise GhostMarketApiError(
                "elections.turnout_by_state: 'year' param required",
                retryable=False,
            )

        if year == 2024:
            rows = await self._load_dataset(_CACHE_PRES_2024, _PRES_2024_STATE_URL)
            votes_field = "votes"
            total_field = "totalvotes"
            party_field = "party_simplified"
        elif 2000 <= year <= 2016:
            # Aggregate county rows to state level
            county_result = await self._county_presidential({"year": year})
            return _aggregate_county_to_state(county_result["data"], year)
        else:
            # Fall back to constituency-level presidential file (1976-2016 range)
            rows = await self._load_dataset(
                "elections_pres_constituency",
                "https://raw.githubusercontent.com/MEDSL/constituency-returns/master/"
                "1976-2016-president.csv",
            )
            votes_field = "candidatevotes"
            total_field = "totalvotes"
            party_field = "party"

        # Aggregate rows to state level
        state_map: dict[str, dict] = {}
        for row in rows:
            row_year = _safe_int(row.get("year"))
            if row_year != year:
                continue

            state_po = row.get("state_po", "").upper()
            candidate = row.get("candidate", "")
            party = row.get(party_field, "")
            candidate_votes = _safe_int(row.get(votes_field, 0))
            total_votes = _safe_int(row.get(total_field, 0))

            if state_po not in state_map:
                state_map[state_po] = {
                    "state": row.get("state", state_po),
                    "state_po": state_po,
                    "total_votes": total_votes,
                    "candidates": {},
                }
            # Track per-candidate totals (some states have mode splits)
            cand_key = f"{candidate}|{party}"
            existing = state_map[state_po]["candidates"].get(cand_key, 0)
            state_map[state_po]["candidates"][cand_key] = existing + candidate_votes
            # Keep max total_votes (same across rows for a state)
            if total_votes > state_map[state_po]["total_votes"]:
                state_map[state_po]["total_votes"] = total_votes

        results = []
        for state_po, info in sorted(state_map.items()):
            total_v = info["total_votes"]
            candidates = info["candidates"]
            if not candidates:
                continue
            top_key = max(candidates, key=lambda k: candidates[k])
            top_votes = candidates[top_key]
            top_candidate, top_party = top_key.split("|", 1)
            results.append({
                "state": info["state"],
                "state_po": state_po,
                "total_votes": total_v,
                "leading_candidate": top_candidate,
                "leading_party": top_party,
                "leading_votes": top_votes,
                "leading_vote_share": round(top_votes / total_v, 4) if total_v > 0 else 0.0,
            })

        return {
            "method": "turnout_by_state",
            "year": year,
            "note": (
                "Votes cast derived from MEDSL official results. "
                "For VAP/registered voter turnout rates, see electproject.org."
            ),
            "data": results,
        }

    async def _state_comparison(self, query: dict) -> dict:
        """Compare election results for specified states across multiple years.

        Primary analytical method for voter ID impact analysis -- compare a
        state against itself before and after a voter ID law change.

        Returns:
            {
                "method": "state_comparison",
                "years": list[int],
                "states": list[str],
                "office": str,
                "data": {
                    "<state_po>": {
                        "<year>": {
                            "total_votes": int,
                            "top_candidates": list[{candidate, party, votes, share}]
                        }
                    }
                }
            }
        """
        years = query.get("years", [])
        states_raw = query.get("states", [])
        office = query.get("office", "president").lower()

        if not years:
            raise GhostMarketApiError(
                "elections.state_comparison: 'years' param required (list of ints)",
                retryable=False,
            )
        if not states_raw:
            raise GhostMarketApiError(
                "elections.state_comparison: 'states' param required (list of state codes)",
                retryable=False,
            )

        states = [_normalize_state(s) for s in states_raw if s]

        # Gather per-year data for each requested year
        data: dict[str, dict] = {s: {} for s in states}

        for year in years:
            if office == "house":
                result = await self._house_results({"year": year})
                rows = result["data"]
            elif office == "senate":
                rows = await self._get_senate_rows(year, states)
            else:
                # President: try county (2000-2016), then state-level (2024),
                # then constituency-level (1976-2016)
                if year == 2024:
                    pres_result = await self._turnout_by_state({"year": 2024})
                    rows = _state_turnout_to_rows(pres_result["data"])
                elif 2000 <= year <= 2016:
                    result = await self._county_presidential({"year": year})
                    rows = result["data"]
                else:
                    result = await self._house_results({"year": year})
                    rows = []  # no constituency-level pres outside those methods

            # Detect if rows come from county data (has "county" field) --
            # county rows repeat totalvotes per candidate per county, so
            # we must sum candidatevotes to get the state total.
            is_county_data = bool(rows and rows[0].get("county"))

            for state_po in states:
                state_rows = [r for r in rows if r.get("state_po", "").upper() == state_po]
                if not state_rows:
                    continue

                # Sum per-candidate (works for all row types)
                cand_totals: dict[str, dict] = {}
                for r in state_rows:
                    candidate = r.get("candidate", r.get("leading_candidate", ""))
                    party = r.get("party", r.get("leading_party", ""))
                    votes = r.get("candidatevotes", 0)
                    key = f"{candidate}|{party}"
                    if key not in cand_totals:
                        cand_totals[key] = {"candidate": candidate, "party": party, "votes": 0}
                    cand_totals[key]["votes"] += votes

                # Total votes: for county data, sum all candidate votes;
                # for state/district data, take max totalvotes from rows.
                if is_county_data:
                    total_v = sum(cand_totals[k]["votes"] for k in cand_totals)
                else:
                    total_v = max(
                        r.get("totalvotes", r.get("total_votes", 0)) for r in state_rows
                    )

                top_candidates = sorted(
                    cand_totals.values(), key=lambda x: x["votes"], reverse=True
                )[:5]
                for tc in top_candidates:
                    tc["vote_share"] = round(tc["votes"] / total_v, 4) if total_v > 0 else 0.0

                data[state_po][str(year)] = {
                    "total_votes": total_v,
                    "top_candidates": top_candidates,
                }

        return {
            "method": "state_comparison",
            "years": years,
            "states": states,
            "office": office,
            "data": data,
        }

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    async def _get_senate_rows(self, year: int, states: list[str]) -> list[dict]:
        """Load senate results for a given year, filtered to states."""
        if year == 2024:
            rows_raw = await self._load_dataset(_CACHE_SENATE_2024, _SENATE_2024_STATE_URL)
            state_filter = set(states)
            results = []
            for row in rows_raw:
                row_year = _safe_int(row.get("year"))
                if row_year != year:
                    continue
                state_po = row.get("state_po", "").upper()
                if state_filter and state_po not in state_filter:
                    continue
                candidate_votes = _safe_int(row.get("votes", 0))
                total_votes = _safe_int(row.get("totalvotes", 0))
                results.append({
                    "year": row_year,
                    "state": row.get("state", ""),
                    "state_po": state_po,
                    "candidate": row.get("candidate", ""),
                    "party": row.get("party_simplified", ""),
                    "candidatevotes": candidate_votes,
                    "totalvotes": total_votes,
                })
            return results
        else:
            rows_raw = await self._load_dataset(_CACHE_SENATE, _SENATE_URL)
            state_filter = set(states)
            results = []
            for row in rows_raw:
                row_year = _safe_int(row.get("year"))
                if row_year != year:
                    continue
                state_po = row.get("state_po", "").upper()
                if state_filter and state_po not in state_filter:
                    continue
                stage = row.get("stage", "").lower()
                if stage not in ("gen", "general", ""):
                    continue
                candidate_votes = _safe_int(row.get("candidatevotes", 0))
                total_votes = _safe_int(row.get("totalvotes", 0))
                results.append({
                    "year": row_year,
                    "state": row.get("state", ""),
                    "state_po": state_po,
                    "candidate": row.get("candidate", ""),
                    "party": row.get("party", ""),
                    "candidatevotes": candidate_votes,
                    "totalvotes": total_votes,
                })
            return results

    async def _load_dataset(self, cache_key: str, url: str) -> list[dict]:
        """Load a CSV dataset -- cache-first.

        Checks SQLite cache first. On miss, fetches from URL and stores.
        Returns list of row dicts (CSV headers as keys).
        """
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached.get("rows", [])

        rows = await self._fetch_csv(url)
        await self._cache_store(cache_key, {
            "url": url,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "row_count": len(rows),
            "rows": rows,
        })
        log.info("elections: cached %d rows from %s (key=%s)", len(rows), url, cache_key)
        return rows

    async def _fetch_csv(self, url: str) -> list[dict]:
        """Fetch a CSV file from a URL and parse it.

        Returns list of dicts with CSV headers as keys.
        Handles 404 gracefully (returns empty list).
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=120.0, follow_redirects=True)

                if response.status_code == 404:
                    log.warning("elections: 404 for %s -- dataset may not be published yet", url)
                    return []

                response.raise_for_status()
                text = response.text

        except httpx.HTTPStatusError as e:
            raise GhostMarketApiError(
                f"elections: HTTP {e.response.status_code} fetching {url}",
                status_code=e.response.status_code,
                retryable=e.response.status_code >= 500,
            ) from e
        except httpx.HTTPError as e:
            raise GhostMarketApiError(
                f"elections: network error fetching {url}: {e}",
                retryable=True,
            ) from e

        reader = csv.DictReader(io.StringIO(text))
        rows = []
        for row in reader:
            # Strip surrounding quotes from keys/values (csv.DictReader handles this)
            rows.append(dict(row))
        return rows


# ---------------------------------------------------------------------------
# Module-level utilities
# ---------------------------------------------------------------------------

def _normalize_state(state: str | None) -> str | None:
    """Normalize state input to 2-letter uppercase abbreviation.

    Passes through None if no state filter requested.
    """
    if not state:
        return None
    return state.strip().upper()


def _safe_int(value) -> int:
    """Parse int from string, returning 0 on failure."""
    if value is None:
        return 0
    try:
        # Handle float strings like "17208.0"
        return int(float(str(value).replace(",", "").strip()))
    except (ValueError, TypeError):
        return 0


def _aggregate_county_to_state(county_rows: list[dict], year: int) -> dict:
    """Aggregate county-level rows to state-level turnout summary."""
    state_map: dict[str, dict] = {}

    for row in county_rows:
        state_po = row.get("state_po", "").upper()
        candidate = row.get("candidate", "")
        party = row.get("party", "")
        c_votes = _safe_int(row.get("candidatevotes", 0))

        if state_po not in state_map:
            state_map[state_po] = {
                "state": row.get("state", state_po),
                "state_po": state_po,
                "total_votes": 0,
                "candidates": {},
            }

        # Sum candidate votes across counties
        cand_key = f"{candidate}|{party}"
        existing = state_map[state_po]["candidates"].get(cand_key, 0)
        state_map[state_po]["candidates"][cand_key] = existing + c_votes

    # Set total_votes = sum of all candidate votes per state (avoids double counting)
    # totalvotes in county CSV is the per-county total, repeated per candidate row
    # Best approach: take max candidate total_votes from any row -- but that's county-level.
    # Instead, use max of candidate sums (should be close to actual total).
    results = []
    for state_po, info in sorted(state_map.items()):
        candidates = info["candidates"]
        if not candidates:
            continue
        # totalvotes = sum of all candidate votes (includes minor party)
        total_v = sum(candidates.values())
        top_key = max(candidates, key=lambda k: candidates[k])
        top_votes = candidates[top_key]
        top_candidate, top_party = top_key.split("|", 1)
        results.append({
            "state": info["state"],
            "state_po": state_po,
            "total_votes": total_v,
            "leading_candidate": top_candidate,
            "leading_party": top_party,
            "leading_votes": top_votes,
            "leading_vote_share": round(top_votes / total_v, 4) if total_v > 0 else 0.0,
        })

    return {
        "method": "turnout_by_state",
        "year": year,
        "note": (
            "Votes cast derived from MEDSL county returns (2000-2016). "
            "For VAP/registered voter turnout rates, see electproject.org."
        ),
        "data": results,
    }


def _state_turnout_to_rows(turnout_data: list[dict]) -> list[dict]:
    """Convert turnout_by_state data back to a flat row format for state_comparison."""
    rows = []
    for entry in turnout_data:
        rows.append({
            "state_po": entry["state_po"],
            "state": entry["state"],
            "candidate": entry["leading_candidate"],
            "party": entry["leading_party"],
            "leading_candidate": entry["leading_candidate"],
            "leading_party": entry["leading_party"],
            "candidatevotes": entry["leading_votes"],
            "totalvotes": entry["total_votes"],
            "total_votes": entry["total_votes"],
        })
    return rows
