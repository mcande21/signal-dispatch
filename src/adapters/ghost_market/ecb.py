"""ECB Statistical Data Warehouse (SDW) API adapter.

Source: https://data-api.ecb.europa.eu/service/data
Auth: None required
Format: SDMX JSON
TTL: 6 hours

Provides ECB economic data in SDMX JSON format.
Common datasets:
- EXR: Exchange rates (e.g., EUR/USD, EUR/RUB)
"""

from datetime import datetime, timedelta, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


# ECB SDW API base URL
ECB_API_BASE = "https://data-api.ecb.europa.eu/service/data"


class EcbAdapter(GhostMarketAdapter):
    """ECB SDW API adapter with cache-first pattern.

    Fetches economic data from ECB Statistical Data Warehouse in SDMX JSON format.
    Returns decoded observations as date-value pairs.
    Signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 6 hours (21600 seconds)."""
        return 21600

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "ecb"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of ECB SDW data.

        Args:
            query: {
                "flow_ref": str (dataset, required -- e.g. "EXR"),
                "key": str (dimension key, required -- e.g. "D.USD.EUR.SP00.A"),
                "start_period": str (YYYY-MM-DD, default 30 days ago),
                "end_period": str (YYYY-MM-DD, default today)
            }

        Returns:
            {
                "source": "ecb",
                "flow_ref": str,
                "key": str,
                "record_count": int,
                "observations": [
                    {
                        "date": str (YYYY-MM-DD),
                        "value": float
                    },
                    ...
                ],
                "fetched_at": str (ISO timestamp)
            }
        """
        flow_ref = query.get("flow_ref")
        key = query.get("key")

        if not flow_ref:
            raise GhostMarketApiError("ecb: 'flow_ref' parameter is required")
        if not key:
            raise GhostMarketApiError("ecb: 'key' parameter is required")

        # Default date range: last 30 days
        now = datetime.now(timezone.utc)
        default_start = now - timedelta(days=30)

        start_period = query.get("start_period", default_start.strftime("%Y-%m-%d"))
        end_period = query.get("end_period", now.strftime("%Y-%m-%d"))

        # Cache key incorporates flow_ref, key, and date range
        cache_key = f"{flow_ref}_{key}_{start_period}_{end_period}"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- call ECB API
        data = await self._call_ecb_api(flow_ref, key, start_period, end_period)

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _call_ecb_api(
        self,
        flow_ref: str,
        key: str,
        start_period: str,
        end_period: str
    ) -> dict:
        """Call ECB SDW API for SDMX data.

        ECB SDW API docs: https://data.ecb.europa.eu/help/api/data
        """
        # Build endpoint URL with flow_ref and key in path
        url = f"{ECB_API_BASE}/{flow_ref}/{key}"

        # Query parameters
        params = {
            "startPeriod": start_period,
            "endPeriod": end_period,
            "format": "jsondata"  # SDMX JSON format
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                raw_data = response.json()

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "ECB API rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"ECB API server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"ECB API HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to ECB API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "ECB API request timed out", retryable=True
            ) from e

        # Decode SDMX JSON format to date-value pairs
        observations = self._decode_sdmx(raw_data)

        return {
            "source": "ecb",
            "flow_ref": flow_ref,
            "key": key,
            "record_count": len(observations),
            "observations": observations,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    def _decode_sdmx(self, raw_data: dict) -> list[dict]:
        """Decode SDMX JSON format to date-value pairs.

        SDMX JSON uses numeric indices for dimensions and observations.
        The response structure:
        {
          "structure": {
            "dimensions": {
              "observation": [
                {"id": "TIME_PERIOD", "values": [{"id": "2026-03-01"}, ...]}
              ]
            }
          },
          "dataSets": [
            {
              "series": {
                "0:0:0:0:0": {
                  "observations": {
                    "0": [1.0821],
                    "1": [1.0835],
                    ...
                  }
                }
              }
            }
          ]
        }

        Observation keys ("0", "1", ...) are indices into TIME_PERIOD values.
        Observation values are arrays where first element is the actual value.

        Returns:
            List of {date: str, value: float} dicts sorted by date
        """
        try:
            # Extract TIME_PERIOD values from structure
            structure = raw_data.get("structure", {})
            dimensions = structure.get("dimensions", {})
            observation_dims = dimensions.get("observation", [])

            time_period_dim = None
            for dim in observation_dims:
                if dim.get("id") == "TIME_PERIOD":
                    time_period_dim = dim
                    break

            if not time_period_dim:
                raise GhostMarketApiError("ecb: TIME_PERIOD dimension not found in SDMX response")

            # TIME_PERIOD values array
            time_values = time_period_dim.get("values", [])
            dates = [val.get("id") for val in time_values]

            # Extract series data
            data_sets = raw_data.get("dataSets", [])
            if not data_sets:
                # Empty result set - no data for this series/period
                return []

            # Get first series (we're querying a single series by key)
            series_dict = data_sets[0].get("series", {})
            if not series_dict:
                return []

            # Get first (and only) series key
            series_key = next(iter(series_dict.keys()))
            series_data = series_dict[series_key]

            observations = series_data.get("observations", {})

            # Map observation indices to dates and values
            results = []
            for obs_idx, obs_value in observations.items():
                # obs_idx is string index into dates array
                idx = int(obs_idx)
                if idx >= len(dates):
                    continue  # Invalid index - skip

                date = dates[idx]
                # obs_value is array, first element is the value
                value = obs_value[0] if obs_value else None

                if value is not None:
                    results.append({
                        "date": date,
                        "value": float(value)
                    })

            # Sort by date ascending
            results.sort(key=lambda x: x["date"])

            return results

        except Exception as e:
            raise GhostMarketApiError(
                f"ecb: Failed to decode SDMX response: {e}"
            ) from e
