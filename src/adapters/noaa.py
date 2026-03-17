"""NOAA / NWS weather API adapter.

Provides weather observations and forecasts for geopolitical context.

Sources:
  NOAA NCEI: https://www.ncei.noaa.gov/access/services/data/v1  (historical obs)
  NWS: https://api.weather.gov  (forecasts and active alerts)

Auth: None required
TTL: 3 hours (forecasts), 24 hours (historical obs)
"""

from datetime import datetime, timezone

import httpx

from .base import GhostMarketAdapter, GhostMarketApiError


NOAA_API_BASE = "https://www.ncei.noaa.gov/access/services/data/v1"
NWS_API_BASE = "https://api.weather.gov"

NWS_USER_AGENT = "(signal-dispatch, cooper@normandy.dev)"

# GHCN-Daily station IDs for tracked cities
NOAA_STATIONS = {
    "nyc": "USW00094728",
    "chicago": "USW00094846",
    "miami": "USW00012839",
    "austin": "USW00013958",
}

# NWS gridpoint stations for forecast API
NWS_STATIONS = {
    "nyc": {"office": "OKX", "gridX": 33, "gridY": 37},
    "chicago": {"office": "LOT", "gridX": 65, "gridY": 76},
    "miami": {"office": "MFL", "gridX": 75, "gridY": 54},
    "austin": {"office": "EWX", "gridX": 154, "gridY": 93},
}

CITY_STATE_MAP = {
    "nyc": "NY",
    "chicago": "IL",
    "miami": "FL",
    "austin": "TX",
}


class NoaaAdapter(GhostMarketAdapter):
    """NOAA / NWS weather data adapter with cache-first pattern.

    Fetches weather forecasts and active weather alerts.
    Returns raw weather data -- signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 3 hours (forecast refresh rate)."""
        return 10800

    @property
    def source_name(self) -> str:
        return "noaa"

    async def fetch(self, query: dict) -> dict:
        """Fetch NOAA / NWS data.

        Args:
            query: {
                "type": "forecast" | "alerts",
                "city": str (e.g., "nyc") -- for forecast,
                "state": str (e.g., "NY") -- for alerts,
            }

        Returns for type="forecast":
            {
                "type": "forecast",
                "city": str,
                "forecast_time": str,
                "periods": list[dict],
                "fetched_at": str
            }

        Returns for type="alerts":
            {
                "type": "alerts",
                "state": str,
                "alerts": list[dict],
                "alert_count": int,
                "fetched_at": str
            }
        """
        query_type = query.get("type", "forecast")

        if query_type == "forecast":
            return await self._fetch_forecast(query)
        elif query_type == "alerts":
            return await self._fetch_alerts(query)
        else:
            raise GhostMarketApiError(
                f"noaa: unknown query type '{query_type}'. Use 'forecast' or 'alerts'"
            )

    async def _fetch_forecast(self, query: dict) -> dict:
        """Fetch NWS 7-day forecast for a city."""
        city = query.get("city", "nyc").lower()
        if city not in NWS_STATIONS:
            raise GhostMarketApiError(
                f"noaa: unknown city '{city}'. Valid: {list(NWS_STATIONS.keys())}"
            )

        cache_key = f"forecast_{city}"
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        station = NWS_STATIONS[city]
        url = (
            f"{NWS_API_BASE}/gridpoints/{station['office']}"
            f"/{station['gridX']},{station['gridY']}/forecast"
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": NWS_USER_AGENT},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            raise GhostMarketApiError(
                f"NWS forecast HTTP {status_code} for {city}",
                status_code=status_code,
                retryable=status_code == 429 or status_code >= 500,
            ) from e
        except httpx.HTTPError as e:
            raise GhostMarketApiError(
                f"NWS forecast network error: {e}", retryable=True
            ) from e

        properties = data.get("properties", {})
        updated_time = properties.get("updated", datetime.now(timezone.utc).isoformat())
        periods = []
        for period in properties.get("periods", []):
            periods.append({
                "name": period.get("name", ""),
                "start_time": period.get("startTime", ""),
                "end_time": period.get("endTime", ""),
                "temperature": period.get("temperature"),
                "unit": period.get("temperatureUnit", "F"),
                "wind_speed": period.get("windSpeed", ""),
                "wind_direction": period.get("windDirection", ""),
                "short_forecast": period.get("shortForecast", ""),
                "detailed_forecast": period.get("detailedForecast", ""),
                "precipitation_pct": (
                    period.get("probabilityOfPrecipitation", {}).get("value")
                ),
            })

        result = {
            "type": "forecast",
            "city": city,
            "forecast_time": updated_time,
            "periods": periods,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

        await self._cache_store(cache_key, result)
        return result

    async def _fetch_alerts(self, query: dict) -> dict:
        """Fetch active NWS weather alerts for a state."""
        state = query.get("state", "NY").upper()

        cache_key = f"alerts_{state}"
        # Alerts have short TTL -- use 15 min regardless of class TTL
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        url = f"{NWS_API_BASE}/alerts/active"
        params = {"area": state}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    headers={"User-Agent": NWS_USER_AGENT},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            raise GhostMarketApiError(
                f"NWS alerts HTTP {status_code} for {state}",
                status_code=status_code,
                retryable=status_code == 429 or status_code >= 500,
            ) from e
        except httpx.HTTPError as e:
            raise GhostMarketApiError(
                f"NWS alerts network error: {e}", retryable=True
            ) from e

        alerts = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            alerts.append({
                "event": props.get("event", "Unknown"),
                "severity": props.get("severity", "Unknown"),
                "certainty": props.get("certainty", "Unknown"),
                "urgency": props.get("urgency", "Unknown"),
                "headline": props.get("headline", ""),
                "description": props.get("description", ""),
                "instruction": props.get("instruction", ""),
                "sent": props.get("sent", ""),
                "effective": props.get("effective", ""),
                "expires": props.get("expires", ""),
                "areas": props.get("areaDesc", ""),
            })

        result = {
            "type": "alerts",
            "state": state,
            "alerts": alerts,
            "alert_count": len(alerts),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

        await self._cache_store(cache_key, result)
        return result
