"""OONI (Open Observatory of Network Interference) API adapter.

Source: https://api.ooni.io/api/v1/
Auth: None required
TTL: 1h (active monitoring)
"""

from datetime import datetime, timedelta, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


# OONI API base URL
OONI_API_BASE = "https://api.ooni.io/api/v1"


class OoniAdapter(GhostMarketAdapter):
    """OONI internet censorship data adapter with cache-first pattern.

    Fetches internet censorship measurements for Iran (IR).
    Returns raw OONI data with mechanical anomaly_rate calculation.
    Signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 1 hour (active monitoring)."""
        return 3600

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "ooni"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of OONI aggregation data.

        Args:
            query: {"probe_cc": str (default "IR"), "days": int (default 7)}

        Returns:
            {
                "country": str,
                "measurements": [{"date": str, "anomaly_count": int, ...}, ...],
                "anomaly_rate": float,
                "incidents": [{"id": str, "title": str, ...}, ...],
                "last_updated": str,
            }
        """
        probe_cc = query.get("probe_cc", "IR")
        days = query.get("days", 7)

        # Cache key includes country and days
        cache_key = f"{probe_cc}_aggregation_{days}"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- call OONI API
        data = await self._call_ooni_api(probe_cc, days)

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _call_ooni_api(self, probe_cc: str, days: int) -> dict:
        """Call OONI API for aggregation and incidents.

        OONI API docs: https://api.ooni.io/apidocs/
        """
        # Calculate date range
        until_date = datetime.now(timezone.utc)
        since_date = until_date - timedelta(days=days)

        # Format dates as YYYY-MM-DD
        since_str = since_date.strftime("%Y-%m-%d")
        until_str = until_date.strftime("%Y-%m-%d")

        # Fetch aggregation data
        agg_url = f"{OONI_API_BASE}/aggregation"
        agg_params = {
            "probe_cc": probe_cc,
            "since": since_str,
            "until": until_str,
            "test_name": "web_connectivity",
            "axis_x": "measurement_start_day",
        }

        try:
            async with httpx.AsyncClient() as client:
                # Fetch aggregation
                agg_response = await client.get(agg_url, params=agg_params, timeout=30.0)
                agg_response.raise_for_status()
                agg_data = agg_response.json()

                # Fetch incidents
                # Note: incidents endpoint doesn't support probe_cc filtering
                # We'll filter client-side instead
                incidents_url = f"{OONI_API_BASE}/incidents/search"
                inc_response = await client.get(incidents_url, timeout=30.0)
                inc_response.raise_for_status()
                inc_data = inc_response.json()

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "OONI API rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"OONI API server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"OONI API HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to OONI API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "OONI API request timed out", retryable=True
            ) from e

        # Parse aggregation response
        measurements = []
        total_anomaly = 0
        total_measurements = 0

        for item in agg_data.get("result", []):
            anomaly_count = item.get("anomaly_count", 0)
            measurement_count = item.get("measurement_count", 0)
            confirmed_count = item.get("confirmed_count", 0)

            measurements.append({
                "date": item.get("measurement_start_day"),
                "anomaly_count": anomaly_count,
                "confirmed_count": confirmed_count,
                "measurement_count": measurement_count,
            })

            total_anomaly += anomaly_count
            total_measurements += measurement_count

        # Calculate overall anomaly rate
        anomaly_rate = total_anomaly / total_measurements if total_measurements > 0 else 0.0

        # Parse incidents (filter for active incidents in target country)
        now = datetime.now(timezone.utc)
        active_incidents = []
        for incident in inc_data.get("incidents", []):
            # Filter by country code first
            # Incidents have a "CCs" field with list of affected countries
            incident_ccs = incident.get("CCs", [])
            if probe_cc not in incident_ccs:
                continue

            # Check if incident is currently active
            start_date_str = incident.get("start_date")
            end_date_str = incident.get("end_date")

            if start_date_str:
                start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
                # If no end date, incident is ongoing
                if end_date_str:
                    end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                    is_active = start_date <= now <= end_date
                else:
                    is_active = start_date <= now

                if is_active:
                    active_incidents.append({
                        "id": incident.get("id"),
                        "title": incident.get("title"),
                        "start_date": start_date_str,
                        "end_date": end_date_str,
                    })

        return {
            "country": probe_cc,
            "measurements": measurements,
            "anomaly_rate": anomaly_rate,
            "incidents": active_incidents,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
