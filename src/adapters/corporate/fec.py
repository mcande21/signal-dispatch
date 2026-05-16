"""FEC (Federal Election Commission) corporate investigative adapter.

Source: https://api.open.fec.gov/v1/
Auth: FEC_API_KEY env var (free, apply at api.open.fec.gov)
Rate limit: 1,000 requests/hour
TTL: 12h

Covers the money-tracing endpoints that OpenSecrets used to aggregate:
- Schedule A: itemized receipts (who gave money to whom)
- Schedule B: itemized disbursements (how committees spent money)
- Schedule E: independent expenditures (Super PAC spend for/against candidates)
- Committee details (PAC type, connected org, treasurer)
- Candidate totals (fundraising summary)
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


FEC_API_BASE = "https://api.open.fec.gov/v1"

VALID_METHODS = {
    "committee_search",
    "committee_detail",
    "candidate_totals",
    "schedule_a",
    "schedule_b",
    "schedule_e",
}

HEADERS = {
    "User-Agent": "SignalDispatch/1.0 (contact@example.com)",
    "Accept": "application/json",
}


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


class FecCorporateAdapter(GhostMarketAdapter):
    """FEC API adapter for corporate money-flow investigations.

    Traces money from organizations to candidates via PACs, independent
    expenditures, and itemized contribution records.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.api_key = os.environ.get("FEC_API_KEY", "")

    @property
    def ttl_seconds(self) -> int:
        return 43200

    @property
    def source_name(self) -> str:
        return "fec_corporate"

    async def fetch(self, query: dict) -> dict:
        if not self.api_key:
            return {
                "source": "fec_corporate",
                "error": "FEC_API_KEY not set",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        method = query.get("method")
        if method not in VALID_METHODS:
            raise GhostMarketApiError(
                f"fec_corporate: invalid method '{method}', expected one of {sorted(VALID_METHODS)}"
            )

        cache_key = self._build_cache_key(query)
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        try:
            data = await self._dispatch(method, query)
        except GhostMarketApiError as e:
            if e.retryable:
                await asyncio.sleep(2)
                data = await self._dispatch(method, query)
            else:
                raise

        await self._cache_store(cache_key, data)
        return data

    async def _dispatch(self, method: str, query: dict) -> dict:
        if method == "committee_search":
            return await self._committee_search(query)
        elif method == "committee_detail":
            return await self._committee_detail(query)
        elif method == "candidate_totals":
            return await self._candidate_totals(query)
        elif method == "schedule_a":
            return await self._schedule_a(query)
        elif method == "schedule_b":
            return await self._schedule_b(query)
        elif method == "schedule_e":
            return await self._schedule_e(query)
        raise GhostMarketApiError(f"fec_corporate: unhandled method '{method}'")

    def _build_cache_key(self, query: dict) -> str:
        method = query.get("method", "")
        name = query.get("name", query.get("committee_id", query.get("candidate_id", "")))
        cycle = query.get("cycle", "")
        return f"fec_{method}_{name}_{cycle}".lower().replace(" ", "_")

    async def _get(self, endpoint: str, params: dict | None = None) -> dict:
        params = params or {}
        params["api_key"] = self.api_key

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{FEC_API_BASE}{endpoint}",
                    params=params,
                    headers=HEADERS,
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "FEC API rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif status_code in (401, 403):
                raise GhostMarketApiError(
                    "Invalid FEC API key", status_code=status_code
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"FEC API server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"FEC API HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to FEC API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "FEC API request timed out", retryable=True
            ) from e

    # -- committee_search: find PACs/committees by name or connected org --------

    async def _committee_search(self, query: dict) -> dict:
        name = query.get("name", "")
        if not name:
            raise GhostMarketApiError("fec_corporate: 'name' required for committee_search")

        params = {"q": name, "per_page": 20}
        cycle = query.get("cycle")
        if cycle:
            params["cycle"] = cycle

        data = await self._get("/committees/", params)
        await asyncio.sleep(0.5)

        committees = []
        for c in data.get("results", []):
            committees.append({
                "committee_id": c.get("committee_id", ""),
                "name": c.get("name", ""),
                "committee_type": c.get("committee_type", ""),
                "committee_type_full": c.get("committee_type_full", ""),
                "designation": c.get("designation", ""),
                "designation_full": c.get("designation_full", ""),
                "organization_type": c.get("organization_type", ""),
                "organization_type_full": c.get("organization_type_full", ""),
                "connected_org_name": c.get("sponsor_candidate_list", [{}])[0].get("candidate_name", "") if c.get("sponsor_candidate_list") else "",
                "party": c.get("party", ""),
                "state": c.get("state", ""),
                "treasurer_name": c.get("treasurer_name", ""),
                "cycles": c.get("cycles", []),
            })

        return {
            "source": "fec_corporate",
            "method": "committee_search",
            "name": name,
            "committees": committees,
            "result_count": len(committees),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -- committee_detail: full committee record with financial totals ----------

    async def _committee_detail(self, query: dict) -> dict:
        committee_id = query.get("committee_id", "")
        if not committee_id:
            raise GhostMarketApiError("fec_corporate: 'committee_id' required")

        data = await self._get(f"/committee/{committee_id}/")
        await asyncio.sleep(0.5)

        totals_data = await self._get(f"/committee/{committee_id}/totals/", {"per_page": 4})

        results = data.get("results", [data] if "committee_id" in data else [])
        info = results[0] if results else {}

        totals = []
        for t in totals_data.get("results", []):
            totals.append({
                "cycle": t.get("cycle"),
                "receipts": _safe_float(t.get("receipts")),
                "disbursements": _safe_float(t.get("disbursements")),
                "independent_expenditures": _safe_float(t.get("independent_expenditures")),
                "contributions": _safe_float(t.get("contributions")),
                "individual_contributions": _safe_float(t.get("individual_contributions")),
                "other_political_committee_contributions": _safe_float(t.get("other_political_committee_contributions")),
                "cash_on_hand_end_period": _safe_float(t.get("cash_on_hand_end_period")),
                "last_cash_on_hand_end_period": _safe_float(t.get("last_cash_on_hand_end_period")),
            })

        return {
            "source": "fec_corporate",
            "method": "committee_detail",
            "committee_id": committee_id,
            "name": info.get("name", ""),
            "committee_type_full": info.get("committee_type_full", ""),
            "designation_full": info.get("designation_full", ""),
            "treasurer_name": info.get("treasurer_name", ""),
            "party": info.get("party", ""),
            "state": info.get("state", ""),
            "totals_by_cycle": totals,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -- candidate_totals: fundraising summary for a candidate -----------------

    async def _candidate_totals(self, query: dict) -> dict:
        candidate_id = query.get("candidate_id", "")
        name = query.get("name", "")

        if not candidate_id and not name:
            raise GhostMarketApiError("fec_corporate: 'candidate_id' or 'name' required")

        if not candidate_id:
            search_data = await self._get("/candidates/search/", {
                "name": name, "per_page": 5, "sort": "-election_year"
            })
            await asyncio.sleep(0.5)
            candidates = search_data.get("results", [])
            if not candidates:
                return {
                    "source": "fec_corporate",
                    "method": "candidate_totals",
                    "name": name,
                    "error": f"No candidate found for '{name}'",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            candidate_id = candidates[0].get("candidate_id", "")

        totals_data = await self._get(f"/candidate/{candidate_id}/totals/", {"per_page": 4})

        totals = []
        for t in totals_data.get("results", []):
            totals.append({
                "cycle": t.get("cycle"),
                "receipts": _safe_float(t.get("receipts")),
                "disbursements": _safe_float(t.get("disbursements")),
                "individual_contributions": _safe_float(t.get("individual_contributions")),
                "pac_contributions": _safe_float(t.get("other_political_committee_contributions")),
                "cash_on_hand": _safe_float(t.get("cash_on_hand_end_period")),
                "candidate_name": t.get("candidate_name", ""),
                "party": t.get("party", ""),
                "office": t.get("office", ""),
                "state": t.get("state", ""),
            })

        return {
            "source": "fec_corporate",
            "method": "candidate_totals",
            "candidate_id": candidate_id,
            "totals_by_cycle": totals,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -- schedule_a: itemized receipts (who gave to whom) ----------------------

    async def _schedule_a(self, query: dict) -> dict:
        """Schedule A: itemized individual and organization contributions."""
        params = {"per_page": 30, "sort": "-contribution_receipt_amount"}

        committee_id = query.get("committee_id")
        contributor_name = query.get("contributor_name")
        contributor_employer = query.get("contributor_employer")
        min_amount = query.get("min_amount")
        cycle = query.get("cycle", 2026)

        if committee_id:
            params["committee_id"] = committee_id
        if contributor_name:
            params["contributor_name"] = contributor_name
        if contributor_employer:
            params["contributor_employer"] = contributor_employer
        if min_amount:
            params["min_amount"] = min_amount
        if cycle:
            params["two_year_transaction_period"] = cycle

        if not committee_id and not contributor_name and not contributor_employer:
            raise GhostMarketApiError(
                "fec_corporate: schedule_a requires at least one of: committee_id, contributor_name, contributor_employer"
            )

        data = await self._get("/schedules/schedule_a/", params)

        contributions = []
        for r in data.get("results", []):
            contributions.append({
                "contributor_name": r.get("contributor_name", ""),
                "contributor_employer": r.get("contributor_employer", ""),
                "contributor_occupation": r.get("contributor_occupation", ""),
                "contributor_city": r.get("contributor_city", ""),
                "contributor_state": r.get("contributor_state", ""),
                "amount": _safe_float(r.get("contribution_receipt_amount")),
                "date": r.get("contribution_receipt_date", ""),
                "committee_id": r.get("committee_id", ""),
                "committee_name": r.get("committee", {}).get("name", "") if isinstance(r.get("committee"), dict) else "",
                "memo_text": r.get("memo_text", ""),
            })

        return {
            "source": "fec_corporate",
            "method": "schedule_a",
            "contributions": contributions,
            "result_count": len(contributions),
            "total_available": data.get("pagination", {}).get("count", len(contributions)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -- schedule_b: itemized disbursements (how money was spent) --------------

    async def _schedule_b(self, query: dict) -> dict:
        """Schedule B: itemized disbursements from committees."""
        params = {"per_page": 30, "sort": "-disbursement_amount"}

        committee_id = query.get("committee_id")
        recipient_name = query.get("recipient_name")
        cycle = query.get("cycle", 2026)

        if committee_id:
            params["committee_id"] = committee_id
        if recipient_name:
            params["recipient_name"] = recipient_name
        if cycle:
            params["two_year_transaction_period"] = cycle

        if not committee_id and not recipient_name:
            raise GhostMarketApiError(
                "fec_corporate: schedule_b requires at least one of: committee_id, recipient_name"
            )

        data = await self._get("/schedules/schedule_b/", params)

        disbursements = []
        for r in data.get("results", []):
            disbursements.append({
                "recipient_name": r.get("recipient_name", ""),
                "recipient_city": r.get("recipient_city", ""),
                "recipient_state": r.get("recipient_state", ""),
                "amount": _safe_float(r.get("disbursement_amount")),
                "date": r.get("disbursement_date", ""),
                "purpose": r.get("disbursement_description", ""),
                "committee_id": r.get("committee_id", ""),
                "committee_name": r.get("committee", {}).get("name", "") if isinstance(r.get("committee"), dict) else "",
            })

        return {
            "source": "fec_corporate",
            "method": "schedule_b",
            "disbursements": disbursements,
            "result_count": len(disbursements),
            "total_available": data.get("pagination", {}).get("count", len(disbursements)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -- schedule_e: independent expenditures (Super PAC spend) ----------------

    async def _schedule_e(self, query: dict) -> dict:
        """Schedule E: independent expenditures for/against candidates."""
        params = {"per_page": 30, "sort": "-expenditure_amount"}

        committee_id = query.get("committee_id")
        candidate_id = query.get("candidate_id")
        cycle = query.get("cycle", 2026)
        support_oppose = query.get("support_oppose")
        min_amount = query.get("min_amount")

        if committee_id:
            params["committee_id"] = committee_id
        if candidate_id:
            params["candidate_id"] = candidate_id
        if cycle:
            params["cycle"] = cycle
        if support_oppose:
            params["support_oppose_indicator"] = support_oppose
        if min_amount:
            params["min_amount"] = min_amount

        if not committee_id and not candidate_id:
            raise GhostMarketApiError(
                "fec_corporate: schedule_e requires at least one of: committee_id, candidate_id"
            )

        data = await self._get("/schedules/schedule_e/", params)

        expenditures = []
        for r in data.get("results", []):
            expenditures.append({
                "committee_id": r.get("committee_id", ""),
                "committee_name": r.get("committee", {}).get("name", "") if isinstance(r.get("committee"), dict) else "",
                "candidate_id": r.get("candidate_id", ""),
                "candidate_name": r.get("candidate_name", ""),
                "amount": _safe_float(r.get("expenditure_amount")),
                "date": r.get("expenditure_date", ""),
                "description": r.get("expenditure_description", ""),
                "support_oppose": r.get("support_oppose_indicator", ""),
                "office": r.get("candidate_office", ""),
                "state": r.get("candidate_state", ""),
                "payee_name": r.get("payee_name", ""),
            })

        return {
            "source": "fec_corporate",
            "method": "schedule_e",
            "expenditures": expenditures,
            "result_count": len(expenditures),
            "total_available": data.get("pagination", {}).get("count", len(expenditures)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
