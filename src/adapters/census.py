"""Census Bureau / American Community Survey (ACS) adapter.

Standalone version for Signal Dispatch -- no Database dependency.
Uses SQLite cache directly via aiosqlite (same pattern as fred.py).

Source: https://api.census.gov/data/
Auth: CENSUS_API_KEY env var (optional -- 500 req/day without key, unlimited with)
TTL: 30 days (ACS data is annual -- no point re-fetching frequently)

Primary dataset: 2023/acs/acs5  (5-year, full geographic coverage)
Secondary: 2024/acs/acs1        (1-year, only geographies with 65K+ pop)

Use case: demographic backbone for analyzing the SAVE Act -- citizenship status,
naturalization rates, and cross-tabs by congressional district, state, county.
"""

import os
from urllib.parse import urlencode, quote

import httpx

from .base import GhostMarketAdapter, GhostMarketApiError


CENSUS_API_BASE = "https://api.census.gov/data"

# Default ACS 5-year dataset year (most recent with full geographic coverage)
ACS5_YEAR = "2023"
ACS1_YEAR = "2024"

# B05003 -- Sex by Age by Citizenship Status
# _008E through _012E = male 18+: native, foreign born naturalized, foreign born non-citizen, born abroad of US parents, unknown
# We track the three citizenship categories for 18+ (voting-age)
# Male 18+
B05003_MALE_18PLUS = {
    "native": "B05003_008E",              # Native citizen
    "naturalized": "B05003_010E",         # Naturalized citizen
    "non_citizen": "B05003_011E",         # Non-citizen
}
# Female 18+
B05003_FEMALE_18PLUS = {
    "native": "B05003_019E",              # Native citizen
    "naturalized": "B05003_021E",         # Naturalized citizen
    "non_citizen": "B05003_022E",         # Non-citizen
}

# Race suffix codes for B05003A-I tables
RACE_SUFFIXES = {
    "A": "White alone",
    "B": "Black or African American alone",
    "C": "American Indian and Alaska Native alone",
    "D": "Asian alone",
    "E": "Native Hawaiian and Other Pacific Islander alone",
    "F": "Some other race alone",
    "G": "Two or more races",
    "H": "White alone, not Hispanic or Latino",
    "I": "Hispanic or Latino",
}

# B29001 -- Citizen Voting-Age Population (CVAP) by Age
CVAP_VARS = {
    "total": "B29001_001E",
    "age_18_29": "B29001_002E",
    "age_30_44": "B29001_003E",
    "age_45_64": "B29001_004E",
    "age_65_plus": "B29001_005E",
}

# B06009 -- Place of Birth by Educational Attainment
NATIVITY_EDUCATION_VARS = {
    # Native
    "native_total": "B06009_002E",
    "native_less_than_hs": "B06009_003E",
    "native_hs_diploma": "B06009_004E",
    "native_some_college": "B06009_005E",
    "native_bachelor_plus": "B06009_006E",
    # Foreign born
    "foreign_total": "B06009_025E",
    "foreign_less_than_hs": "B06009_026E",
    "foreign_hs_diploma": "B06009_027E",
    "foreign_some_college": "B06009_028E",
    "foreign_bachelor_plus": "B06009_029E",
}

# B06012 -- Place of Birth by Poverty Status in the Past 12 Months
# Table structure: _001E = total, _002E-_004E = total by poverty level,
# _005E-_008E = born in state, _009E-_012E = born other state,
# _013E-_016E = born outside US (native), _017E-_020E = foreign born
NATIVITY_POVERTY_VARS = {
    # All nativity (total)
    "total": "B06012_001E",
    "total_below_100pct": "B06012_002E",
    "total_100_to_149pct": "B06012_003E",
    "total_at_or_above_150pct": "B06012_004E",
    # Foreign born
    "foreign_total": "B06012_017E",
    "foreign_below_100pct": "B06012_018E",
    "foreign_100_to_149pct": "B06012_019E",
    "foreign_at_or_above_150pct": "B06012_020E",
}

# B06010 -- Place of Birth by Individual Income in the Past 12 Months
NATIVITY_INCOME_VARS = {
    # Native
    "native_total": "B06010_002E",
    "native_no_income": "B06010_003E",
    "native_1_to_9999": "B06010_004E",
    "native_10000_to_14999": "B06010_005E",
    "native_15000_to_24999": "B06010_006E",
    "native_25000_to_34999": "B06010_007E",
    "native_35000_to_49999": "B06010_008E",
    "native_50000_to_64999": "B06010_009E",
    "native_65000_to_74999": "B06010_010E",
    "native_75000_plus": "B06010_011E",
    # Foreign born
    "foreign_total": "B06010_026E",
    "foreign_no_income": "B06010_027E",
    "foreign_1_to_9999": "B06010_028E",
    "foreign_10000_to_14999": "B06010_029E",
    "foreign_15000_to_24999": "B06010_030E",
    "foreign_25000_to_34999": "B06010_031E",
    "foreign_35000_to_49999": "B06010_032E",
    "foreign_50000_to_64999": "B06010_033E",
    "foreign_65000_to_74999": "B06010_034E",
    "foreign_75000_plus": "B06010_035E",
}


def _build_geo_params(geo_type: str, state_fips: str | None, county_fips: str | None) -> dict:
    """Build Census API geography parameters for a given geo_type.

    Args:
        geo_type: "state", "county", "congressional district", or "tract"
        state_fips: 2-digit state FIPS code (required for county and tract)
        county_fips: 3-digit county FIPS code (required for tract)

    Returns:
        Dict with "for" and optional "in" keys to add to request params.
    """
    if geo_type == "state":
        return {"for": "state:*"}

    if geo_type == "county":
        if state_fips:
            return {"for": "county:*", "in": f"state:{state_fips}"}
        return {"for": "county:*"}

    if geo_type == "congressional district":
        if state_fips:
            return {
                "for": "congressional district:*",
                "in": f"state:{state_fips}",
            }
        # All CDs nationwide requires nested in= format
        return {
            "for": "congressional district:*",
            "in": "state:*",
        }

    if geo_type == "tract":
        if not state_fips:
            raise GhostMarketApiError(
                "census: state_fips required for tract-level queries",
                retryable=False,
            )
        if county_fips:
            return {
                "for": "tract:*",
                "in": f"state:{state_fips} county:{county_fips}",
            }
        return {
            "for": "tract:*",
            "in": f"state:{state_fips}",
        }

    raise GhostMarketApiError(
        f"census: unsupported geo_type '{geo_type}'. "
        "Use: state, county, congressional district, tract",
        retryable=False,
    )


def _parse_array_response(raw: list[list]) -> list[dict]:
    """Convert Census JSON arrays-of-arrays to list of dicts.

    Census API always returns first row as headers.
    """
    if not raw or len(raw) < 2:
        return []
    headers = raw[0]
    return [dict(zip(headers, row)) for row in raw[1:]]


def _safe_int(value: str | None) -> int | None:
    """Parse Census estimate value -- Census uses '-666666666' for suppressed data."""
    if value is None:
        return None
    try:
        v = int(value)
        # Census sentinel values for suppressed / missing data
        if v < -1:
            return None
        return v
    except (ValueError, TypeError):
        return None


class CensusAdapter(GhostMarketAdapter):
    """Census Bureau / ACS adapter with cache-first pattern.

    Dispatches on query["method"] to one of five fetch methods:
      - citizenship_by_geography  (B05003)
      - cvap_by_geography         (B29001)
      - nativity_by_education     (B06009)
      - nativity_by_poverty       (B06012)
      - nativity_by_income        (B06010)
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.api_key = os.environ.get("CENSUS_API_KEY")

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 30 days (ACS data is annual)."""
        return 30 * 24 * 3600

    @property
    def source_name(self) -> str:
        return "census"

    async def fetch(self, query: dict) -> dict:
        """Dispatch to method-specific handler.

        Args:
            query: {
                "method": str,       -- Required. One of the five method names.
                "dataset": str,      -- Optional. "acs5" (default) or "acs1".
                "year": str,         -- Optional. Override dataset year.
                "geo_type": str,     -- Geography granularity (method-dependent).
                "state_fips": str,   -- Optional 2-digit state FIPS.
                "county_fips": str,  -- Optional 3-digit county FIPS (for tract).
                "race": str,         -- Optional race suffix A-I (citizenship only).
            }

        Returns:
            Method-specific dict. All include:
                {
                    "method": str,
                    "dataset": str,
                    "geo_type": str,
                    "data": list[dict],
                }
        """
        method = query.get("method", "citizenship_by_geography")

        dispatch = {
            "citizenship_by_geography": self._fetch_citizenship,
            "cvap_by_geography": self._fetch_cvap,
            "nativity_by_education": self._fetch_nativity_education,
            "nativity_by_poverty": self._fetch_nativity_poverty,
            "nativity_by_income": self._fetch_nativity_income,
        }

        if method not in dispatch:
            raise GhostMarketApiError(
                f"census: unknown method '{method}'. "
                f"Valid methods: {list(dispatch.keys())}",
                retryable=False,
            )

        return await dispatch[method](query)

    # -------------------------------------------------------------------------
    # Core API call
    # -------------------------------------------------------------------------

    async def _census_get(
        self,
        dataset_path: str,
        variables: list[str],
        geo_params: dict,
    ) -> list[dict]:
        """Make a Census API request and return parsed rows.

        Census API enforces a 50-variable limit per request.
        This method splits into batches if needed and merges results by row index.

        Args:
            dataset_path: e.g. "2023/acs/acs5"
            variables: List of variable codes (e.g. ["B05003_008E"])
            geo_params: Dict with "for" and optional "in" keys.

        Returns:
            List of dicts with variable values + geography identifiers.
        """
        url = f"{CENSUS_API_BASE}/{dataset_path}"

        # Always include NAME for readable geography labels
        if "NAME" not in variables:
            variables = ["NAME"] + variables

        # Split into batches of 50 (Census limit)
        # Always keep NAME in each batch for merging; don't count it against the 50
        non_name = [v for v in variables if v != "NAME"]
        batch_size = 49  # 49 data vars + NAME = 50 per request
        batches = [
            non_name[i : i + batch_size]
            for i in range(0, len(non_name), batch_size)
        ]
        if not batches:
            batches = [[]]

        merged: list[dict] | None = None

        for batch in batches:
            get_vars = ["NAME"] + batch
            params: dict = {"get": ",".join(get_vars)}
            params.update(geo_params)
            if self.api_key:
                params["key"] = self.api_key

            # Census API requires specific URL encoding:
            # - 'for' and 'in' values contain spaces and colons that must not be
            #   double-encoded. Build the query string manually using quote() so
            #   spaces become %20 and colons/asterisks stay literal in values.
            qs = urlencode(params, quote_via=lambda s, safe, encoding, errors: quote(s, safe=":*,", encoding=encoding, errors=errors))
            full_url = f"{url}?{qs}"

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(full_url, timeout=60.0)

                    # Census returns 204 for valid queries with no data
                    if response.status_code == 204:
                        return []

                    response.raise_for_status()
                    raw = response.json()

            except httpx.HTTPStatusError as e:
                raise GhostMarketApiError(
                    f"census API error ({dataset_path}): HTTP {e.response.status_code}",
                    status_code=e.response.status_code,
                    retryable=e.response.status_code >= 500,
                ) from e
            except httpx.HTTPError as e:
                raise GhostMarketApiError(
                    f"census network error ({dataset_path}): {e}",
                    retryable=True,
                ) from e

            if not isinstance(raw, list) or len(raw) < 2:
                return []

            rows = _parse_array_response(raw)

            if merged is None:
                merged = rows
            else:
                # Merge: use NAME as the join key (Census preserves order but be safe)
                existing_by_name = {r["NAME"]: r for r in merged}
                for row in rows:
                    name = row["NAME"]
                    if name in existing_by_name:
                        # Add new variable columns, skip geo cols already present
                        for k, v in row.items():
                            if k not in existing_by_name[name]:
                                existing_by_name[name][k] = v
                merged = list(existing_by_name.values())

        return merged or []

    def _resolve_dataset(self, query: dict) -> str:
        """Resolve dataset path from query params."""
        dataset = query.get("dataset", "acs5")
        if dataset == "acs1":
            year = query.get("year", ACS1_YEAR)
            return f"{year}/acs/acs1"
        year = query.get("year", ACS5_YEAR)
        return f"{year}/acs/acs5"

    def _resolve_geo(self, query: dict) -> tuple[str, dict]:
        """Resolve geo_type and geo_params from query."""
        geo_type = query.get("geo_type", "state")
        state_fips = query.get("state_fips")
        county_fips = query.get("county_fips")
        geo_params = _build_geo_params(geo_type, state_fips, county_fips)
        return geo_type, geo_params

    # -------------------------------------------------------------------------
    # Method: citizenship_by_geography (B05003)
    # -------------------------------------------------------------------------

    async def _fetch_citizenship(self, query: dict) -> dict:
        """Fetch citizenship status for voting-age (18+) population.

        Uses B05003 (total) or B05003A-I (by race if race suffix provided).

        Returns:
            {
                "method": "citizenship_by_geography",
                "dataset": str,
                "geo_type": str,
                "data": list[{
                    "name": str,
                    "fips": str,          -- concatenated FIPS components
                    "native_citizen_18plus": int | None,
                    "naturalized_citizen_18plus": int | None,
                    "non_citizen_18plus": int | None,
                    "total_18plus": int | None,
                    "race": str | None,   -- None for total (B05003)
                }]
            }
        """
        dataset_path = self._resolve_dataset(query)
        geo_type, geo_params = self._resolve_geo(query)
        race = query.get("race")

        # Build table prefix: B05003 (total) or B05003A-I (by race)
        if race:
            if race.upper() not in RACE_SUFFIXES:
                raise GhostMarketApiError(
                    f"census: invalid race suffix '{race}'. "
                    f"Valid: {list(RACE_SUFFIXES.keys())}",
                    retryable=False,
                )
            prefix = f"B05003{race.upper()}"
            race_label = RACE_SUFFIXES[race.upper()]
        else:
            prefix = "B05003"
            race_label = None

        # Variable offsets are the same across race-specific tables
        # Male 18+: positions 8, 10, 11 (native, naturalized, non-citizen)
        # Female 18+: positions 19, 21, 22
        male_vars = {
            "native": f"{prefix}_008E",
            "naturalized": f"{prefix}_010E",
            "non_citizen": f"{prefix}_011E",
        }
        female_vars = {
            "native": f"{prefix}_019E",
            "naturalized": f"{prefix}_021E",
            "non_citizen": f"{prefix}_022E",
        }

        all_vars = list(male_vars.values()) + list(female_vars.values())

        cache_key = (
            f"census_citizenship_{dataset_path.replace('/', '_')}"
            f"_{geo_type.replace(' ', '_')}"
            f"_{query.get('state_fips', 'all')}"
            f"_{query.get('county_fips', 'all')}"
            f"_{race or 'total'}"
        )

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        rows = await self._census_get(dataset_path, all_vars, geo_params)

        data = []
        for row in rows:
            # Sum male + female for each citizenship category
            native = _safe_int(row.get(male_vars["native"])) or 0
            native_f = _safe_int(row.get(female_vars["native"])) or 0
            naturalized = _safe_int(row.get(male_vars["naturalized"])) or 0
            naturalized_f = _safe_int(row.get(female_vars["naturalized"])) or 0
            non_citizen = _safe_int(row.get(male_vars["non_citizen"])) or 0
            non_citizen_f = _safe_int(row.get(female_vars["non_citizen"])) or 0

            native_total = native + native_f
            naturalized_total = naturalized + naturalized_f
            non_citizen_total = non_citizen + non_citizen_f
            total_18plus = native_total + naturalized_total + non_citizen_total

            # Build FIPS from available geo components
            fips_parts = []
            for col in ("state", "county", "congressional district", "tract"):
                if col in row:
                    fips_parts.append(row[col])
            fips = "".join(fips_parts)

            data.append({
                "name": row.get("NAME", ""),
                "fips": fips,
                "native_citizen_18plus": native_total if native_total else None,
                "naturalized_citizen_18plus": naturalized_total if naturalized_total else None,
                "non_citizen_18plus": non_citizen_total if non_citizen_total else None,
                "total_18plus": total_18plus if total_18plus else None,
                "race": race_label,
            })

        result = {
            "method": "citizenship_by_geography",
            "dataset": dataset_path,
            "geo_type": geo_type,
            "data": data,
        }

        await self._cache_store(cache_key, result)
        return result

    # -------------------------------------------------------------------------
    # Method: cvap_by_geography (B29001)
    # -------------------------------------------------------------------------

    async def _fetch_cvap(self, query: dict) -> dict:
        """Fetch Citizen Voting-Age Population (CVAP) by geography and age bracket.

        Returns:
            {
                "method": "cvap_by_geography",
                "dataset": str,
                "geo_type": str,
                "data": list[{
                    "name": str,
                    "fips": str,
                    "cvap_total": int | None,
                    "cvap_18_29": int | None,
                    "cvap_30_44": int | None,
                    "cvap_45_64": int | None,
                    "cvap_65_plus": int | None,
                }]
            }
        """
        dataset_path = self._resolve_dataset(query)
        geo_type, geo_params = self._resolve_geo(query)

        all_vars = list(CVAP_VARS.values())

        cache_key = (
            f"census_cvap_{dataset_path.replace('/', '_')}"
            f"_{geo_type.replace(' ', '_')}"
            f"_{query.get('state_fips', 'all')}"
            f"_{query.get('county_fips', 'all')}"
        )

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        rows = await self._census_get(dataset_path, all_vars, geo_params)

        data = []
        for row in rows:
            fips_parts = []
            for col in ("state", "county", "congressional district", "tract"):
                if col in row:
                    fips_parts.append(row[col])
            fips = "".join(fips_parts)

            data.append({
                "name": row.get("NAME", ""),
                "fips": fips,
                "cvap_total": _safe_int(row.get(CVAP_VARS["total"])),
                "cvap_18_29": _safe_int(row.get(CVAP_VARS["age_18_29"])),
                "cvap_30_44": _safe_int(row.get(CVAP_VARS["age_30_44"])),
                "cvap_45_64": _safe_int(row.get(CVAP_VARS["age_45_64"])),
                "cvap_65_plus": _safe_int(row.get(CVAP_VARS["age_65_plus"])),
            })

        result = {
            "method": "cvap_by_geography",
            "dataset": dataset_path,
            "geo_type": geo_type,
            "data": data,
        }

        await self._cache_store(cache_key, result)
        return result

    # -------------------------------------------------------------------------
    # Method: nativity_by_education (B06009)
    # -------------------------------------------------------------------------

    async def _fetch_nativity_education(self, query: dict) -> dict:
        """Fetch nativity by educational attainment (B06009).

        Returns:
            {
                "method": "nativity_by_education",
                "dataset": str,
                "geo_type": str,
                "data": list[{
                    "name": str,
                    "fips": str,
                    "native_total": int | None,
                    "native_less_than_hs": int | None,
                    "native_hs_diploma": int | None,
                    "native_some_college": int | None,
                    "native_bachelor_plus": int | None,
                    "foreign_total": int | None,
                    "foreign_less_than_hs": int | None,
                    "foreign_hs_diploma": int | None,
                    "foreign_some_college": int | None,
                    "foreign_bachelor_plus": int | None,
                }]
            }
        """
        dataset_path = self._resolve_dataset(query)
        geo_type, geo_params = self._resolve_geo(query)

        all_vars = list(NATIVITY_EDUCATION_VARS.values())

        cache_key = (
            f"census_nativity_edu_{dataset_path.replace('/', '_')}"
            f"_{geo_type.replace(' ', '_')}"
            f"_{query.get('state_fips', 'all')}"
            f"_{query.get('county_fips', 'all')}"
        )

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        rows = await self._census_get(dataset_path, all_vars, geo_params)

        data = []
        for row in rows:
            fips_parts = []
            for col in ("state", "county", "congressional district", "tract"):
                if col in row:
                    fips_parts.append(row[col])
            fips = "".join(fips_parts)

            entry = {"name": row.get("NAME", ""), "fips": fips}
            for field, var_code in NATIVITY_EDUCATION_VARS.items():
                entry[field] = _safe_int(row.get(var_code))
            data.append(entry)

        result = {
            "method": "nativity_by_education",
            "dataset": dataset_path,
            "geo_type": geo_type,
            "data": data,
        }

        await self._cache_store(cache_key, result)
        return result

    # -------------------------------------------------------------------------
    # Method: nativity_by_poverty (B06012)
    # -------------------------------------------------------------------------

    async def _fetch_nativity_poverty(self, query: dict) -> dict:
        """Fetch nativity by poverty status (B06012).

        Returns:
            {
                "method": "nativity_by_poverty",
                "dataset": str,
                "geo_type": str,
                "data": list[{
                    "name": str,
                    "fips": str,
                    "total": int | None,
                    "total_below_100pct": int | None,
                    "total_100_to_149pct": int | None,
                    "total_at_or_above_150pct": int | None,
                    "foreign_total": int | None,
                    "foreign_below_100pct": int | None,
                    "foreign_100_to_149pct": int | None,
                    "foreign_at_or_above_150pct": int | None,
                }]
            }
        """
        dataset_path = self._resolve_dataset(query)
        geo_type, geo_params = self._resolve_geo(query)

        all_vars = list(NATIVITY_POVERTY_VARS.values())

        cache_key = (
            f"census_nativity_pov_{dataset_path.replace('/', '_')}"
            f"_{geo_type.replace(' ', '_')}"
            f"_{query.get('state_fips', 'all')}"
            f"_{query.get('county_fips', 'all')}"
        )

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        rows = await self._census_get(dataset_path, all_vars, geo_params)

        data = []
        for row in rows:
            fips_parts = []
            for col in ("state", "county", "congressional district", "tract"):
                if col in row:
                    fips_parts.append(row[col])
            fips = "".join(fips_parts)

            entry = {"name": row.get("NAME", ""), "fips": fips}
            for field, var_code in NATIVITY_POVERTY_VARS.items():
                entry[field] = _safe_int(row.get(var_code))
            data.append(entry)

        result = {
            "method": "nativity_by_poverty",
            "dataset": dataset_path,
            "geo_type": geo_type,
            "data": data,
        }

        await self._cache_store(cache_key, result)
        return result

    # -------------------------------------------------------------------------
    # Method: nativity_by_income (B06010)
    # -------------------------------------------------------------------------

    async def _fetch_nativity_income(self, query: dict) -> dict:
        """Fetch nativity by individual income brackets (B06010).

        Returns:
            {
                "method": "nativity_by_income",
                "dataset": str,
                "geo_type": str,
                "data": list[{
                    "name": str,
                    "fips": str,
                    "native_total": int | None,
                    "native_no_income": int | None,
                    "native_1_to_9999": int | None,
                    ... (all NATIVITY_INCOME_VARS keys)
                    "foreign_total": int | None,
                    "foreign_no_income": int | None,
                    ... etc.
                }]
            }
        """
        dataset_path = self._resolve_dataset(query)
        geo_type, geo_params = self._resolve_geo(query)

        all_vars = list(NATIVITY_INCOME_VARS.values())

        cache_key = (
            f"census_nativity_inc_{dataset_path.replace('/', '_')}"
            f"_{geo_type.replace(' ', '_')}"
            f"_{query.get('state_fips', 'all')}"
            f"_{query.get('county_fips', 'all')}"
        )

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        rows = await self._census_get(dataset_path, all_vars, geo_params)

        data = []
        for row in rows:
            fips_parts = []
            for col in ("state", "county", "congressional district", "tract"):
                if col in row:
                    fips_parts.append(row[col])
            fips = "".join(fips_parts)

            entry = {"name": row.get("NAME", ""), "fips": fips}
            for field, var_code in NATIVITY_INCOME_VARS.items():
                entry[field] = _safe_int(row.get(var_code))
            data.append(entry)

        result = {
            "method": "nativity_by_income",
            "dataset": dataset_path,
            "geo_type": geo_type,
            "data": data,
        }

        await self._cache_store(cache_key, result)
        return result
