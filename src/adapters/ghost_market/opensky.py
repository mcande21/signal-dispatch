"""OpenSky Network — Real-time Flight Tracking adapter.

Source: https://opensky-network.org/api/states/all
Auth: None required (4000 credits/day anonymous)
TTL: 30 minutes

Signal: Civilian flight density by strategic region. Sudden drops in traffic
over a region = airspace closure = escalation indicator. Different from military
adsb.py — this monitors civilian airspace disruption.
"""

import asyncio
from datetime import datetime, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


OPENSKY_API_URL = "https://opensky-network.org/api/states/all"

# Strategic regions to monitor (lat/lon bounding boxes)
# Format: {"region_name": {"lamin": float, "lamax": float, "lomin": float, "lomax": float}}
MONITORED_REGIONS = {
    "taiwan_strait": {"lamin": 22.0, "lamax": 26.0, "lomin": 119.0, "lomax": 122.5},
    "persian_gulf": {"lamin": 23.0, "lamax": 30.0, "lomin": 48.0, "lomax": 57.0},
    "black_sea": {"lamin": 40.5, "lamax": 46.5, "lomin": 27.5, "lomax": 41.5},
    "red_sea": {"lamin": 12.0, "lamax": 30.0, "lomin": 32.0, "lomax": 44.0},
    "south_china_sea": {"lamin": 5.0, "lamax": 22.0, "lomin": 109.0, "lomax": 121.0},
    "eastern_med": {"lamin": 30.0, "lamax": 38.0, "lomin": 25.0, "lomax": 37.0},
}

# State vector indices (from OpenSky API documentation)
# Index 0: icao24, 1: callsign, 2: origin_country, 5: longitude, 6: latitude,
# 7: altitude, 8: on_ground, ...
ICAO24_IDX = 0
CALLSIGN_IDX = 1
ORIGIN_COUNTRY_IDX = 2
LONGITUDE_IDX = 5
LATITUDE_IDX = 6
ALTITUDE_IDX = 7
ON_GROUND_IDX = 8


class OpenSkyAdapter(GhostMarketAdapter):
    """OpenSky Network regional airspace monitoring adapter.

    Queries OpenSky for civilian flight activity across 6 strategic regions.
    Returns per-region aircraft counts and origin country breakdown.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 30 minutes (live flight data)."""
        return 1800

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "opensky"

    async def fetch(self, query: dict) -> dict:  # noqa: ARG002
        """Cache-first fetch of OpenSky regional airspace data.

        Args:
            query: Unused (fetches all monitored regions)

        Returns:
            {
                "source": "opensky",
                "snapshot_at": str (ISO timestamp),
                "regions": {
                    "taiwan_strait": {
                        "aircraft_count": int,
                        "by_country": {"United States": 5, "China": 3, ...},
                        "no_callsign": int,
                    },
                    ...  # one entry per region in MONITORED_REGIONS
                }
            }
        """
        cache_key = "opensky_regions_snapshot"

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        data = await self._fetch_all_regions()

        if not data.get("partial_failure"):
            await self._cache_store(cache_key, data)
        return data

    async def _fetch_all_regions(self) -> dict:
        """Query all monitored regions sequentially with rate limiting."""
        regions = {}
        had_error = False

        async with httpx.AsyncClient() as client:
            for region_name, bbox in MONITORED_REGIONS.items():
                try:
                    region_data = await self._fetch_region(region_name, bbox, client)
                    regions[region_name] = region_data
                except GhostMarketApiError:
                    had_error = True
                    # Use None for aircraft_count to distinguish error from real empty airspace
                    regions[region_name] = {
                        "aircraft_count": None,
                        "by_country": {},
                        "no_callsign": 0,
                        "error": "failed to fetch",
                    }

                # Rate limit: 1 second between requests to avoid hammering the API
                await asyncio.sleep(1)

        result = {
            "source": "opensky",
            "snapshot_at": datetime.now(timezone.utc).isoformat(),
            "regions": regions,
        }
        if had_error:
            result["partial_failure"] = True
        return result

    async def _fetch_region(self, region_name: str, bbox: dict, client: httpx.AsyncClient) -> dict:
        """Fetch aircraft states for a single bounding box region."""
        params = {
            "lamin": bbox["lamin"],
            "lamax": bbox["lamax"],
            "lomin": bbox["lomin"],
            "lomax": bbox["lomax"],
        }

        headers = {
            "User-Agent": "SignalDispatch/1.0",
        }

        try:
            response = await client.get(
                OPENSKY_API_URL, params=params, headers=headers, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    f"OpenSky API rate limit exceeded (region: {region_name})",
                    status_code=429,
                    retryable=True,
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"OpenSky API server error: {status_code} (region: {region_name})",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"OpenSky API HTTP error: {status_code} (region: {region_name})",
                    status_code=status_code,
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                f"Cannot connect to OpenSky API (region: {region_name})",
                retryable=True,
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                f"OpenSky API request timed out (region: {region_name})",
                retryable=True,
            ) from e

        # Response shape: {"time": int, "states": [[...], [...]]}
        states = data.get("states", [])

        # Filter out on_ground aircraft and count by origin country
        by_country: dict[str, int] = {}
        no_callsign_count = 0

        for state in states:
            # State vector must be long enough and not be on ground
            if len(state) <= ON_GROUND_IDX:
                continue
            if state[ON_GROUND_IDX]:  # Skip on-ground aircraft
                continue

            origin = state[ORIGIN_COUNTRY_IDX] if ORIGIN_COUNTRY_IDX < len(state) else None
            callsign = state[CALLSIGN_IDX] if CALLSIGN_IDX < len(state) else None

            if not origin:
                continue

            # Track no-callsign aircraft (possible military or unidentified)
            if not callsign or (isinstance(callsign, str) and not callsign.strip()):
                no_callsign_count += 1

            # Count by country
            by_country[origin] = by_country.get(origin, 0) + 1

        aircraft_count = sum(by_country.values())

        return {
            "aircraft_count": aircraft_count,
            "by_country": by_country,
            "no_callsign": no_callsign_count,
        }
