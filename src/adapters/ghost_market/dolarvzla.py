"""dolarVzla (Venezuelan parallel exchange rate) JSON API adapter.

Source: https://ve.dolarapi.com/v1/dolares
Auth: None
Method: GET JSON API
TTL: 1h (rates change frequently)
"""

import asyncio
from datetime import datetime, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


class DolarVzlaAdapter(GhostMarketAdapter):
    """dolarVzla adapter for Venezuelan parallel dollar rates.

    Fetches unofficial USD/VES exchange rates from multiple monitors via dolarapi.com API.
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
        return "dolarvzla"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of dolarVzla exchange rates.

        Args:
            query: dict with optional keys:
                - monitor: str (optional -- specific source like "bcv", "enparalelovzla")

        Returns:
            {
                "source": "dolarvzla",
                "record_count": int,
                "rates": [
                    {
                        "name": str,
                        "buy": float|None,
                        "sell": float|None,
                        "average": float|None,
                        "last_update": str,
                    },
                    ...
                ],
                "fetched_at": str (ISO timestamp),
            }
        """
        # Cache key based on monitor filter (default = all monitors)
        monitor = query.get("monitor", "")
        cache_key = monitor if monitor else "default"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- fetch from API with retry for retryable errors
        try:
            data = await self._fetch_rates(monitor or None)
        except GhostMarketApiError as e:
            if e.retryable:
                await asyncio.sleep(2)
                data = await self._fetch_rates(monitor or None)
            else:
                raise

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _fetch_rates(self, monitor: str | None = None) -> dict:
        """Fetch exchange rates from pydolarve API.

        GET /api/v1/dollar returns JSON with rate data from multiple monitors.
        Optional query param: monitor=<name> to filter to specific source.
        """
        base_url = "https://ve.dolarapi.com/v1/dolares"
        params = {}
        if monitor:
            params["monitor"] = monitor

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    base_url,
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                raw_data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "dolarVzla rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"dolarVzla server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"dolarVzla HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to dolarVzla", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "dolarVzla request timed out", retryable=True
            ) from e

        # Parse and normalize response (map Spanish field names to English)
        rates = self._parse_rates(raw_data)

        return {
            "source": "dolarvzla",
            "record_count": len(rates),
            "rates": rates,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    def _parse_rates(self, raw_data: dict | list) -> list[dict]:
        """Parse API response and map Spanish field names to English.

        API returns either a list of monitors or a single monitor dict.
        Field mappings:
            compra -> buy
            venta -> sell
            promedio -> average
            fuente/title -> name
            fechaActualizacion/last_update -> last_update
        """
        # Handle both list and single-dict responses
        if isinstance(raw_data, dict):
            monitors = [raw_data]
        else:
            monitors = raw_data

        rates = []
        for monitor in monitors:
            # Extract name (try 'fuente' then 'title' then 'monitor')
            name = monitor.get("fuente") or monitor.get("title") or monitor.get("monitor", "unknown")

            # Parse numeric fields safely
            buy = self._safe_float(monitor.get("compra"))
            sell = self._safe_float(monitor.get("venta"))
            average = self._safe_float(monitor.get("promedio"))

            # Extract timestamp
            last_update = monitor.get("fechaActualizacion") or monitor.get("last_update", "")

            rates.append({
                "name": name,
                "buy": buy,
                "sell": sell,
                "average": average,
                "last_update": last_update,
            })

        return rates

    def _safe_float(self, value) -> float | None:
        """Convert value to float if possible, return None otherwise."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
