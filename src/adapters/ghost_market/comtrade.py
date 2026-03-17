"""UN Comtrade (international trade data) API adapter.

Source: https://comtradeapi.un.org
Auth: API key via subscription-key query parameter
TTL: 24 hours
"""

import os
from datetime import datetime, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


# UN Comtrade API base URLs
# Auth endpoint requires subscription-key; preview endpoint is public (no auth)
COMTRADE_API_BASE = "https://comtradeapi.un.org/data/v1/get/C"
COMTRADE_PREVIEW_BASE = "https://comtradeapi.un.org/public/v1/preview/C"

# Country code mapping (M49 codes)
# CRITICAL: UN Comtrade uses M49 codes, NOT ISO country codes
M49_CODES = {
    "IR": 364,   # Iran
    "RU": 643,   # Russia
    "CN": 156,   # China
    "VE": 862,   # Venezuela
    "US": 842,   # United States
    "DE": 276,   # Germany
    "TR": 792,   # Turkey
    "UA": 804,   # Ukraine
    "GT": 320,   # Guatemala
    "HN": 340,   # Honduras
    "SV": 222,   # El Salvador
    "MX": 484,   # Mexico
    "CO": 170,   # Colombia
    "HT": 332,   # Haiti
    "NI": 558,   # Nicaragua
    "EC": 218,   # Ecuador
    "BR": 76,    # Brazil
}


class ComtradeAdapter(GhostMarketAdapter):
    """UN Comtrade international trade data adapter with cache-first pattern.

    Fetches commodity trade data (imports/exports) from UN Comtrade API.
    Returns raw trade records.
    Signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)
        api_key = os.environ.get("COMTRADE_API_KEY")
        if not api_key:
            raise ValueError("COMTRADE_API_KEY environment variable required")
        self.api_key: str = api_key

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 24 hours (86400 seconds)."""
        return 86400

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "comtrade"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of UN Comtrade trade data.

        Args:
            query: {
                "reporter": str (ISO-2 country code, required -- mapped to M49 internally),
                "commodity": str (HS code, default "2709" -- crude petroleum),
                "flow": str ("M" for imports, "X" for exports, default "M"),
                "period": str (year or year+month, default current year),
                "frequency": str ("A" for annual, "M" for monthly, default "A")
            }

        Returns:
            {
                "source": "comtrade",
                "reporter": str (ISO-2 code),
                "reporter_m49": int,
                "commodity": str (HS code),
                "flow": str ("M" or "X"),
                "frequency": str ("A" or "M"),
                "record_count": int,
                "trades": [
                    {
                        "period": str (year or year+month),
                        "partner_code": int (M49 code of trade partner),
                        "partner_desc": str (partner country name),
                        "trade_value": float|None (USD value),
                        "net_weight": float|None (kg),
                        "qty": float|None (quantity in supplementary units),
                    },
                    ...
                ],
                "fetched_at": str (ISO timestamp)
            }
        """
        reporter = query.get("reporter")
        if not reporter:
            raise GhostMarketApiError("comtrade: 'reporter' parameter is required")

        # Map ISO-2 to M49 code
        reporter_m49 = M49_CODES.get(reporter.upper())
        if reporter_m49 is None:
            raise ValueError(
                f"comtrade: unknown ISO country code '{reporter}'. "
                f"Available: {list(M49_CODES.keys())}"
            )

        commodity = query.get("commodity", "2709")  # Default: crude petroleum
        flow = query.get("flow", "M")  # Default: imports
        frequency = query.get("frequency", "A")  # Default: annual
        period = query.get("period", str(datetime.now().year))

        # Cache key incorporates all parameters
        cache_key = f"{reporter}_{commodity}_{flow}_{frequency}_{period}"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- call UN Comtrade API
        data = await self._call_comtrade_api(
            reporter_iso=reporter,
            reporter_m49=reporter_m49,
            commodity=commodity,
            flow=flow,
            frequency=frequency,
            period=period,
        )

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _call_comtrade_api(
        self,
        reporter_iso: str,
        reporter_m49: int,
        commodity: str,
        flow: str,
        frequency: str,
        period: str,
    ) -> dict:
        """Call UN Comtrade API for trade data.

        UN Comtrade API docs: https://comtradeapi.un.org/
        """
        # Build endpoint URL: /C/{frequency}/HS (e.g., /C/A/HS for annual)
        auth_url = f"{COMTRADE_API_BASE}/{frequency}/HS"
        preview_url = f"{COMTRADE_PREVIEW_BASE}/{frequency}/HS"

        # Query parameters
        params: dict[str, str | int] = {
            "reporterCode": reporter_m49,
            "cmdCode": commodity,
            "flowCode": flow,
            "period": period,
        }

        try:
            async with httpx.AsyncClient() as client:
                # Try authenticated endpoint first
                auth_params = {**params, "subscription-key": self.api_key}
                response = await client.get(auth_url, params=auth_params, timeout=30.0)

                # Fallback to preview endpoint on 401/403
                if response.status_code in (401, 403):
                    response = await client.get(preview_url, params=params, timeout=30.0)

                response.raise_for_status()
                raw_data = response.json()

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "UN Comtrade API rate limit exceeded (500 calls/day on free tier)",
                    status_code=429,
                    retryable=True,
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"UN Comtrade API server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"UN Comtrade API HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to UN Comtrade API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "UN Comtrade API request timed out", retryable=True
            ) from e

        # Validate response structure
        # Comtrade returns {"data": [...]} wrapper (similar to AGSI)
        self._validate_response(raw_data, ["data"])

        # Parse trade records
        trades = []
        for record in raw_data.get("data", []):
            # Helper to parse numeric fields (may be strings or None)
            def parse_float(val):
                if val is None or val == "":
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            trades.append({
                "period": record.get("period", ""),
                "partner_code": record.get("partnerCode"),  # M49 code
                "partner_desc": record.get("partnerDesc", ""),
                "trade_value": parse_float(record.get("primaryValue")),  # USD
                "net_weight": parse_float(record.get("netWgt")),  # kg
                "qty": parse_float(record.get("qty")),  # supplementary units
            })

        return {
            "source": "comtrade",
            "reporter": reporter_iso,
            "reporter_m49": reporter_m49,
            "commodity": commodity,
            "flow": flow,
            "frequency": frequency,
            "record_count": len(trades),
            "trades": trades,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
