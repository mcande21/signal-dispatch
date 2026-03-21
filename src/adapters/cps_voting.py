"""Census Current Population Survey (CPS) Voting and Registration Supplement adapter.

Provides voter turnout data broken down by demographics -- essential for analyzing
how proof-of-citizenship requirements affect different voter populations.

Source: https://api.census.gov/data/{year}/cps/voting/nov
Auth: CENSUS_API_KEY env var (500 req/day without key)
TTL: 90 days (CPS data is biennial, static once published)

Key notes:
- CPS Voting Supplement is collected in November of even-numbered years only.
- API serves microdata (person-level records), not pre-tabulated tables.
- PWSSWGT is the person-level weight -- analysis should use weights for
  population estimates. Raw record counts are unweighted.
- PRCITSHP citizenship codes: 1=native born, 2=native born abroad,
  3=native born PR/territory, 4=naturalized, 5=not a citizen.
"""

import os
from datetime import datetime, timezone

import httpx

from .base import GhostMarketAdapter, GhostMarketApiError


CPS_VOTING_BASE = "https://api.census.gov/data/{year}/cps/voting/nov"

# Latest available survey year (biennial, November even years)
CPS_LATEST_YEAR = 2024

# Citizenship status labels for PRCITSHP
CITIZENSHIP_LABELS = {
    "1": "native_born",
    "2": "native_born_abroad",
    "3": "native_born_territory",
    "4": "naturalized",
    "5": "not_citizen",
}

# Voting response labels for PES1
VOTED_LABELS = {
    "1": "yes",
    "2": "no",
    "-1": "not_in_universe",
    "-2": "dont_know",
    "-3": "refused",
    "-9": "no_response",
}

# Registration response labels for PES2
REGISTERED_LABELS = {
    "1": "yes",
    "2": "no",
    "-1": "not_in_universe",
    "-2": "dont_know",
    "-3": "refused",
    "-9": "no_response",
}


class CpsVotingAdapter(GhostMarketAdapter):
    """CPS Voting and Registration Supplement adapter with cache-first pattern.

    Fetches microdata records from the Census CPS voting supplement.
    Returns raw records -- demographic aggregation handled by the agent layer.

    Supports four query methods:
      - turnout_by_demographics: Full microdata with demographic breakdown
      - registration_barriers: Non-registrants and stated barriers (PES3)
      - citizenship_turnout: Aggregated turnout by citizenship status per state
      - historical_comparison: Multi-year turnout comparison
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.api_key = os.environ.get("CENSUS_API_KEY")

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 90 days (CPS data is biennial, static once published)."""
        return 90 * 24 * 3600

    @property
    def source_name(self) -> str:
        return "cps_voting"

    async def fetch(self, query: dict) -> dict:
        """Dispatch to method-specific fetch based on query["method"].

        Args:
            query: {
                "method": str,  -- one of the four supported methods
                ... method-specific params ...
            }

        Returns:
            Method-specific dict. See individual _fetch_* methods for shapes.

        Raises:
            GhostMarketApiError: On API errors or invalid method.
        """
        method = query.get("method", "citizenship_turnout")

        if method == "turnout_by_demographics":
            return await self._fetch_turnout_by_demographics(query)
        elif method == "registration_barriers":
            return await self._fetch_registration_barriers(query)
        elif method == "citizenship_turnout":
            return await self._fetch_citizenship_turnout(query)
        elif method == "historical_comparison":
            return await self._fetch_historical_comparison(query)
        else:
            raise GhostMarketApiError(
                f"cps_voting: unknown method '{method}'. "
                "Valid: turnout_by_demographics, registration_barriers, "
                "citizenship_turnout, historical_comparison",
                retryable=False,
            )

    # -------------------------------------------------------------------------
    # Method: turnout_by_demographics
    # -------------------------------------------------------------------------

    async def _fetch_turnout_by_demographics(self, query: dict) -> dict:
        """Fetch full demographic microdata for a survey year.

        Args:
            query: {
                "year": int,          -- even year (2020, 2022, 2024)
                "state_fips": str,    -- optional 2-digit state FIPS code
            }

        Returns:
            {
                "method": "turnout_by_demographics",
                "year": int,
                "state_fips": str | None,
                "record_count": int,
                "note": str,
                "records": list[dict],  # microdata records
            }
        """
        year = self._validate_year(query.get("year", CPS_LATEST_YEAR))
        state_fips = query.get("state_fips")

        cache_key = f"cps_voting_turnout_{year}"
        if state_fips:
            cache_key += f"_state{state_fips}"

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # Note: state FIPS is auto-appended by the Census API as the "state" column.
        # GESTFIPS is an ACS variable; in CPS the geography is returned as "state".
        variables = "PWSSWGT,PRCITSHP,PES1,PES2,PRTAGE,PTDTRACE,PEHSPNON,PESEX,PEEDUCA,HEFAMINC"
        geography = f"state:{state_fips}" if state_fips else "state:*"

        raw_rows = await self._call_api(year, variables, geography)
        records = self._rows_to_records(raw_rows)

        result = {
            "method": "turnout_by_demographics",
            "year": year,
            "state_fips": state_fips,
            "record_count": len(records),
            "note": (
                "Microdata -- use PWSSWGT (person weight) for population estimates. "
                "Raw record counts are unweighted."
            ),
            "records": records,
        }

        await self._cache_store(cache_key, result)
        return result

    # -------------------------------------------------------------------------
    # Method: registration_barriers
    # -------------------------------------------------------------------------

    async def _fetch_registration_barriers(self, query: dict) -> dict:
        """Fetch non-registrant records and stated reasons for not registering.

        PES3 codes for non-registration reasons include documentation/ID requirements.
        This directly measures who is blocked by proof-of-citizenship requirements.

        Args:
            query: {"year": int}

        Returns:
            {
                "method": "registration_barriers",
                "year": int,
                "record_count": int,
                "note": str,
                "records": list[dict],
            }
        """
        year = self._validate_year(query.get("year", CPS_LATEST_YEAR))
        cache_key = f"cps_voting_barriers_{year}"

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # PES3 = why didn't you register (only asked of non-registrants)
        # State is auto-appended by Census API as "state" column.
        variables = "PWSSWGT,PES3,PRCITSHP,PTDTRACE,PEHSPNON,PRTAGE"
        geography = "state:*"

        raw_rows = await self._call_api(year, variables, geography)
        records = self._rows_to_records(raw_rows)

        # Filter to records where PES3 has a substantive response
        # (positive codes indicate a stated reason; negative = not in universe)
        barrier_records = [
            r for r in records
            if r.get("PES3") is not None and int(r["PES3"]) > 0
        ]

        result = {
            "method": "registration_barriers",
            "year": year,
            "record_count": len(barrier_records),
            "note": (
                "PES3 records for non-registrants only. "
                "Use PWSSWGT for weighted population estimates. "
                "PES3=3 indicates did not meet registration requirements "
                "(citizenship/ID documentation barrier)."
            ),
            "records": barrier_records,
        }

        await self._cache_store(cache_key, result)
        return result

    # -------------------------------------------------------------------------
    # Method: citizenship_turnout
    # -------------------------------------------------------------------------

    async def _fetch_citizenship_turnout(self, query: dict) -> dict:
        """Fetch and aggregate turnout rates by citizenship status per state.

        Key comparison: do naturalized citizens vote at different rates than
        native-born citizens? Are non-citizen residents captured separately?

        Args:
            query: {
                "year": int,
                "state_fips": str,  -- optional
            }

        Returns:
            {
                "method": "citizenship_turnout",
                "year": int,
                "state_fips": str | None,
                "national_summary": {
                    "<citizenship_label>": {
                        "record_count": int,
                        "voted_count": int,
                        "registered_count": int,
                        "turnout_rate_unweighted": float,
                        "registration_rate_unweighted": float,
                    }
                },
                "by_state": dict,
                "note": str,
            }
        """
        year = self._validate_year(query.get("year", CPS_LATEST_YEAR))
        state_fips = query.get("state_fips")

        cache_key = f"cps_voting_citizenship_{year}"
        if state_fips:
            cache_key += f"_state{state_fips}"

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # State FIPS auto-appended by Census API as "state" column.
        variables = "PWSSWGT,PRCITSHP,PES1,PES2"
        geography = f"state:{state_fips}" if state_fips else "state:*"

        raw_rows = await self._call_api(year, variables, geography)
        records = self._rows_to_records(raw_rows)

        national_summary = self._aggregate_citizenship_turnout(records)
        by_state = self._aggregate_citizenship_turnout_by_state(records)

        result = {
            "method": "citizenship_turnout",
            "year": year,
            "state_fips": state_fips,
            "national_summary": national_summary,
            "by_state": by_state,
            "note": (
                "Turnout and registration rates are unweighted record counts. "
                "For population-representative estimates, apply PWSSWGT. "
                "PES1=1 voted, PES1=2 did not vote. "
                "Negative PES1/PES2 values indicate not-in-universe respondents "
                "(excluded from rate calculations)."
            ),
        }

        await self._cache_store(cache_key, result)
        return result

    # -------------------------------------------------------------------------
    # Method: historical_comparison
    # -------------------------------------------------------------------------

    async def _fetch_historical_comparison(self, query: dict) -> dict:
        """Fetch turnout_by_demographics for multiple years for trend analysis.

        Args:
            query: {
                "years": list[int],   -- even years, e.g. [2016, 2018, 2020, 2022, 2024]
                "state_fips": str,    -- optional
            }

        Returns:
            {
                "method": "historical_comparison",
                "years": list[int],
                "state_fips": str | None,
                "by_year": {
                    "<year>": {turnout_by_demographics result}
                },
                "note": str,
            }
        """
        years = query.get("years", [2020, 2022, 2024])
        state_fips = query.get("state_fips")

        # Validate all years up front
        validated_years = [self._validate_year(y) for y in years]

        by_year = {}
        for year in validated_years:
            year_query = {"year": year}
            if state_fips:
                year_query["state_fips"] = state_fips
            try:
                by_year[year] = await self._fetch_turnout_by_demographics(year_query)
            except GhostMarketApiError as e:
                by_year[year] = {"error": str(e), "year": year}

        return {
            "method": "historical_comparison",
            "years": validated_years,
            "state_fips": state_fips,
            "by_year": by_year,
            "note": (
                "Each year's data fetched independently with 90-day cache. "
                "CPS Voting Supplement is biennial -- even years only."
            ),
        }

    # -------------------------------------------------------------------------
    # Census API call
    # -------------------------------------------------------------------------

    async def _call_api(
        self,
        year: int,
        variables: str,
        geography: str,
    ) -> list[list[str]]:
        """Call Census CPS Voting API and return raw array-of-arrays response.

        Args:
            year: Survey year (even number).
            variables: Comma-separated Census variable names.
            geography: Geography spec, e.g. "state:*" or "state:06".

        Returns:
            list[list[str]] -- first row is headers, remaining rows are data.

        Raises:
            GhostMarketApiError: On HTTP or parse errors.
        """
        url = CPS_VOTING_BASE.format(year=year)
        params: dict = {
            "get": variables,
            "for": geography,
        }
        if self.api_key:
            params["key"] = self.api_key

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            # 404 often means year not yet available
            if status == 404:
                raise GhostMarketApiError(
                    f"cps_voting: year {year} not available from Census API (HTTP 404). "
                    "CPS Voting data typically releases ~6 months after election.",
                    status_code=status,
                    retryable=False,
                ) from e
            raise GhostMarketApiError(
                f"cps_voting: Census API error HTTP {status}",
                status_code=status,
                retryable=status >= 500,
            ) from e
        except httpx.HTTPError as e:
            raise GhostMarketApiError(
                f"cps_voting: network error: {e}",
                retryable=True,
            ) from e

        if not isinstance(data, list) or len(data) < 1:
            raise GhostMarketApiError(
                f"cps_voting: unexpected response format for year {year}",
                retryable=False,
            )

        return data

    # -------------------------------------------------------------------------
    # Data helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _rows_to_records(raw_rows: list[list[str]]) -> list[dict]:
        """Convert Census array-of-arrays response to list of dicts.

        First row is headers; subsequent rows are data values.
        """
        if not raw_rows or len(raw_rows) < 2:
            return []

        headers = raw_rows[0]
        records = []
        for row in raw_rows[1:]:
            if len(row) != len(headers):
                continue
            records.append(dict(zip(headers, row)))

        return records

    @staticmethod
    def _validate_year(year: int) -> int:
        """Validate that year is an even number within supported range.

        Raises:
            GhostMarketApiError: If year is odd or out of range.
        """
        year = int(year)
        if year % 2 != 0:
            raise GhostMarketApiError(
                f"cps_voting: year {year} is odd. "
                "CPS Voting Supplement is only collected in even years (election cycles).",
                retryable=False,
            )
        if year < 1994 or year > CPS_LATEST_YEAR:
            raise GhostMarketApiError(
                f"cps_voting: year {year} out of range. "
                f"Supported: 1994 to {CPS_LATEST_YEAR} (even years only).",
                retryable=False,
            )
        return year

    def _aggregate_citizenship_turnout(
        self, records: list[dict]
    ) -> dict[str, dict]:
        """Aggregate turnout and registration counts by citizenship status.

        Excludes not-in-universe respondents (negative PES1/PES2 codes).
        """
        summary: dict[str, dict] = {}

        for record in records:
            citizenship_code = record.get("PRCITSHP", "")
            label = CITIZENSHIP_LABELS.get(citizenship_code, f"code_{citizenship_code}")

            pes1 = record.get("PES1", "")
            pes2 = record.get("PES2", "")

            # Skip not-in-universe (negative values)
            try:
                pes1_int = int(pes1)
                pes2_int = int(pes2)
            except (ValueError, TypeError):
                continue

            if label not in summary:
                summary[label] = {
                    "record_count": 0,
                    "voted_count": 0,
                    "registered_count": 0,
                    "turnout_rate_unweighted": 0.0,
                    "registration_rate_unweighted": 0.0,
                }

            bucket = summary[label]

            # Only count eligible respondents (positive response codes)
            if pes1_int > 0:
                bucket["record_count"] += 1
                if pes1_int == 1:
                    bucket["voted_count"] += 1

            if pes2_int > 0 and pes1_int > 0:
                if pes2_int == 1:
                    bucket["registered_count"] += 1

        # Compute rates
        for label, bucket in summary.items():
            total = bucket["record_count"]
            if total > 0:
                bucket["turnout_rate_unweighted"] = round(
                    bucket["voted_count"] / total, 4
                )
                bucket["registration_rate_unweighted"] = round(
                    bucket["registered_count"] / total, 4
                )

        return summary

    def _aggregate_citizenship_turnout_by_state(
        self, records: list[dict]
    ) -> dict[str, dict]:
        """Aggregate turnout by citizenship status, broken out per state FIPS."""
        by_state: dict[str, dict] = {}

        for record in records:
            state_fips = record.get("GESTFIPS", record.get("state", ""))
            if not state_fips:
                continue

            if state_fips not in by_state:
                by_state[state_fips] = {}

            citizenship_code = record.get("PRCITSHP", "")
            label = CITIZENSHIP_LABELS.get(citizenship_code, f"code_{citizenship_code}")

            pes1 = record.get("PES1", "")
            pes2 = record.get("PES2", "")

            try:
                pes1_int = int(pes1)
                pes2_int = int(pes2)
            except (ValueError, TypeError):
                continue

            if label not in by_state[state_fips]:
                by_state[state_fips][label] = {
                    "record_count": 0,
                    "voted_count": 0,
                    "registered_count": 0,
                }

            bucket = by_state[state_fips][label]

            if pes1_int > 0:
                bucket["record_count"] += 1
                if pes1_int == 1:
                    bucket["voted_count"] += 1

            if pes2_int > 0 and pes1_int > 0:
                if pes2_int == 1:
                    bucket["registered_count"] += 1

        # Compute rates per state
        for state_fips, citizenship_buckets in by_state.items():
            for label, bucket in citizenship_buckets.items():
                total = bucket["record_count"]
                if total > 0:
                    bucket["turnout_rate_unweighted"] = round(
                        bucket["voted_count"] / total, 4
                    )
                    bucket["registration_rate_unweighted"] = round(
                        bucket["registered_count"] / total, 4
                    )
                else:
                    bucket["turnout_rate_unweighted"] = 0.0
                    bucket["registration_rate_unweighted"] = 0.0

        return by_state
