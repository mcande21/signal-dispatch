"""Bonbast.com (Iranian rial black market rate) JSON API adapter.

Source: https://bonbast.com/converter
Auth: None
Method: POST JSON API
TTL: 1h (rates change frequently)
"""

import asyncio
from datetime import datetime, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


# User-Agent header to avoid bot blocking
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class BonbastAdapter(GhostMarketAdapter):
    """Bonbast.com adapter for Iranian rial black market rates.

    Fetches unofficial USD/IRR and EUR/IRR exchange rates via Bonbast converter API.
    Returns raw exchange rate data with sanity checks.
    Signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 1 hour (rates change frequently)."""
        return 3600

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "bonbast"

    async def fetch(self, query: dict) -> dict:  # noqa: ARG002
        """Cache-first fetch of Bonbast exchange rates.

        Note: query param unused -- Bonbast API returns all rates (interface conformance).

        Args:
            query: Unused (API returns all currencies)

        Returns:
            {
                "rates": {
                    "USD": {"rate": float},  # IRR per USD
                    "EUR": {"rate": float},  # IRR per EUR
                },
                "raw": dict,  # Full JSON response for agent inspection
                "timestamp": str,
            }
        """
        # Cache key
        cache_key = "bonbast_rates"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- fetch from API with retry for retryable errors
        try:
            data = await self._fetch_converter()
        except GhostMarketApiError as e:
            if e.retryable:
                await asyncio.sleep(2)
                data = await self._fetch_converter()
            else:
                raise

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _fetch_converter(self) -> dict:
        """Fetch exchange rates from Bonbast converter API.

        POST /converter returns JSON with rates relative to EUR base.
        Calculate IRR rates per currency from the conversion factors.
        """
        url = "https://bonbast.com/converter"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "Bonbast rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"Bonbast server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"Bonbast HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to Bonbast", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "Bonbast request timed out", retryable=True
            ) from e

        # Parse rates - data has EUR as base (EUR=1)
        irr_value = data.get("IRR")
        if not irr_value:
            raise GhostMarketApiError("No IRR rate in Bonbast response")

        rates = {}
        usd_value = data.get("USD")
        if usd_value and float(usd_value) > 0:
            rates["USD"] = {"rate": float(irr_value) / float(usd_value)}

        rates["EUR"] = {"rate": float(irr_value)}

        return {
            "rates": rates,
            "raw": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
