"""Cloudflare Radar API adapter.

Source: https://api.cloudflare.com/client/v4/radar/
Auth: Bearer token (CLOUDFLARE_RADAR_TOKEN env var, optional for some endpoints)
TTL: 1h (network traffic data is real-time)
"""

import asyncio
import os
from datetime import datetime, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


# Cloudflare Radar API base URL
CLOUDFLARE_RADAR_BASE = "https://api.cloudflare.com/client/v4/radar"


class CloudflareRadarAdapter(GhostMarketAdapter):
    """Cloudflare Radar adapter for Iran internet traffic monitoring.

    Tracks network anomalies and outages.
    Returns raw Cloudflare data - signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str, api_token: str | None = None):
        super().__init__(db_path)
        self.api_token = api_token or os.environ.get("CLOUDFLARE_RADAR_TOKEN")

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 1 hour (network traffic is real-time)."""
        return 3600

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "cloudflare_radar"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of Cloudflare Radar data.

        Args:
            query: {
                "location": str (e.g., "IR" for Iran),
                "endpoint": "anomalies" | "outages"
            }

        Returns:
            {
                "location": str,
                "anomalies": [...],
                "outages": [...],
                "last_updated": str,
            }
        """
        location = query.get("location", "IR")
        endpoint = query.get("endpoint", "anomalies")

        if endpoint not in ("anomalies", "outages"):
            raise ValueError("endpoint must be 'anomalies' or 'outages'")

        # Cache key includes location and endpoint
        cache_key = f"{location}_{endpoint}"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- call Cloudflare Radar API with retry for retryable errors
        try:
            data = await self._call_radar_api(location, endpoint)
        except GhostMarketApiError as e:
            if e.retryable:
                await asyncio.sleep(2)
                data = await self._call_radar_api(location, endpoint)
            else:
                raise

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _call_radar_api(self, location: str, endpoint: str) -> dict:
        """Call Cloudflare Radar API for traffic anomalies or outages.

        Cloudflare Radar API docs: https://developers.cloudflare.com/api/operations/radar_get_TrafficAnomalies
        """
        # Map endpoint to URL path
        endpoint_paths = {
            "anomalies": "traffic_anomalies/locations",
            "outages": "annotations/outages",
        }

        url = f"{CLOUDFLARE_RADAR_BASE}/{endpoint_paths[endpoint]}"
        params = {
            "location": location,
            "limit": "10",  # Last 10 events
        }

        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers, timeout=30.0)
                response.raise_for_status()
                api_data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "Cloudflare Radar API rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif status_code in (401, 403):
                # Try to provide helpful error message
                if not self.api_token:
                    raise GhostMarketApiError(
                        "Cloudflare Radar API requires authentication. "
                        "Set CLOUDFLARE_RADAR_TOKEN environment variable.",
                        status_code=status_code,
                    ) from e
                else:
                    raise GhostMarketApiError(
                        "Invalid Cloudflare Radar API token", status_code=status_code
                    ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"Cloudflare Radar API server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"Cloudflare Radar API HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to Cloudflare Radar API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "Cloudflare Radar API request timed out", retryable=True
            ) from e

        # Parse response - Cloudflare wraps data in "result" key
        result = api_data.get("result", {})

        # Defensive parsing - structure may vary
        items = []
        if isinstance(result, list):
            items = result
        elif isinstance(result, dict):
            # Try common keys
            items = result.get("data", result.get("items", []))

        return {
            "location": location,
            "endpoint": endpoint,
            "items": items,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
