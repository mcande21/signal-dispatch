"""NASA FIRMS (Fire Information for Resource Management System) / VIIRS adapter.

Source: https://firms.modaps.eosdis.nasa.gov/api/
Auth: MAP_KEY in URL path
TTL: 24 hours
"""

import csv
import io
import os
from datetime import datetime, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


# NASA FIRMS API base URL
FIRMS_API_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# Predefined country bounding boxes (west, south, east, north)
COUNTRY_BBOXES = {
    "IR": "44,25,63,40",      # Iran
    "RU": "27,41,60,70",      # Russia (western)
    "CN": "100,20,125,45",    # China (eastern)
    "VE": "-73,1,-60,13",     # Venezuela
    "US": "-125,24,-66,50",   # Continental US
    "DE": "5,47,16,55",       # Germany
    "TR": "26,36,45,42",      # Turkey
    "UA": "22,44,40,53",      # Ukraine
}


class ViirsAdapter(GhostMarketAdapter):
    """NASA FIRMS VIIRS fire hotspot data adapter with cache-first pattern.

    Fetches near real-time fire detection data from VIIRS satellite.
    Returns raw hotspot records with basic arithmetic aggregation.
    Signal interpretation handled by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)
        map_key = os.environ.get("NASA_FIRMS_MAP_KEY")
        if not map_key:
            raise ValueError("NASA_FIRMS_MAP_KEY environment variable required")
        self.map_key: str = map_key

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 24 hours (86400 seconds)."""
        return 86400

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "viirs"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of VIIRS fire hotspot data.

        Args:
            query: {
                "country": str (ISO-2 country code, required unless 'area' provided),
                "area": str (optional bounding box override "west,south,east,north"),
                "days": int (1-10, default 1),
                "source": str (default "VIIRS_SNPP_NRT")
            }

        Returns:
            {
                "source": "viirs",
                "country": str (ISO-2 code or None),
                "area": str (bounding box used),
                "days": int,
                "hotspot_count": int,
                "hotspots": [
                    {
                        "latitude": float,
                        "longitude": float,
                        "brightness": float (Kelvin),
                        "frp": float (MW),
                        "confidence": str ("nominal", "low", "high"),
                        "acq_date": str (YYYY-MM-DD),
                        "acq_time": str (HHMM),
                        "daynight": str ("D" or "N"),
                    },
                    ...
                ],
                "summary": {
                    "total_frp": float,
                    "avg_brightness": float,
                    "high_confidence_count": int,
                },
                "fetched_at": str (ISO timestamp)
            }
        """
        # Extract parameters
        country = query.get("country")
        area = query.get("area")
        days = int(query.get("days", 1))
        source = query.get("source", "VIIRS_SNPP_NRT")

        # Validate days parameter
        if not 1 <= days <= 10:
            raise GhostMarketApiError("viirs: 'days' must be between 1 and 10")

        # Determine bounding box
        if area:
            # Use provided bounding box
            bbox = area
            cache_key = f"{bbox}_{days}"
        elif country:
            # Map country to bounding box
            bbox = COUNTRY_BBOXES.get(country)
            if not bbox:
                raise ValueError(
                    f"Unknown country code: {country}. "
                    f"Available: {list(COUNTRY_BBOXES.keys())}"
                )
            cache_key = f"{country}_{days}"
        else:
            raise GhostMarketApiError(
                "viirs: either 'country' or 'area' parameter is required"
            )

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- call FIRMS API
        data = await self._call_firms_api(bbox, days, source, country)

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _call_firms_api(
        self,
        area: str,
        days: int,
        source: str,
        country: str | None
    ) -> dict:
        """Call NASA FIRMS API for VIIRS hotspot data.

        NASA FIRMS API docs: https://firms.modaps.eosdis.nasa.gov/api/
        """
        # Build endpoint URL
        url = f"{FIRMS_API_BASE}/{self.map_key}/{source}/{area}/{days}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                csv_data = response.text

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "NASA FIRMS API rate limit exceeded",
                    status_code=429,
                    retryable=True
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"NASA FIRMS API server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"NASA FIRMS API HTTP error: {status_code}",
                    status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to NASA FIRMS API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "NASA FIRMS API request timed out", retryable=True
            ) from e

        # Parse CSV response
        hotspots = self._parse_csv_hotspots(csv_data)

        # Compute basic arithmetic summary
        summary = self._compute_summary(hotspots)

        return {
            "source": "viirs",
            "country": country,
            "area": area,
            "days": days,
            "hotspot_count": len(hotspots),
            "hotspots": hotspots,
            "summary": summary,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    def _parse_csv_hotspots(self, csv_data: str) -> list[dict]:
        """Parse CSV response into hotspot records.

        CSV columns: latitude, longitude, bright_ti4, scan, track,
                     acq_date, acq_time, satellite, confidence, version,
                     bright_ti5, frp, daynight
        """
        hotspots = []
        reader = csv.DictReader(io.StringIO(csv_data))

        for row in reader:
            # Safe float conversion
            def parse_float(val, default=None):
                if val is None or val == "":
                    return default
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return default

            # Normalize confidence values (API returns 'n', 'l', 'h' or full words)
            confidence = row.get("confidence", "").lower()
            if confidence in ("h", "high"):
                confidence = "high"
            elif confidence in ("l", "low"):
                confidence = "low"
            elif confidence in ("n", "nominal"):
                confidence = "nominal"

            hotspot = {
                "latitude": parse_float(row.get("latitude")),
                "longitude": parse_float(row.get("longitude")),
                "brightness": parse_float(row.get("bright_ti4")),  # Kelvin
                "frp": parse_float(row.get("frp")),  # MW
                "confidence": confidence,
                "acq_date": row.get("acq_date", ""),
                "acq_time": row.get("acq_time", ""),
                "daynight": row.get("daynight", ""),
            }
            hotspots.append(hotspot)

        return hotspots

    def _compute_summary(self, hotspots: list[dict]) -> dict:
        """Compute basic arithmetic summary statistics.

        This is thin aggregation (sum, avg, count), not interpretation.
        Agent decides what the numbers mean.
        """
        if not hotspots:
            return {
                "total_frp": 0.0,
                "avg_brightness": 0.0,
                "high_confidence_count": 0,
            }

        # Filter out None values for aggregation
        frp_values = [h["frp"] for h in hotspots if h["frp"] is not None]
        brightness_values = [
            h["brightness"] for h in hotspots if h["brightness"] is not None
        ]

        total_frp = sum(frp_values)
        avg_brightness = sum(brightness_values) / len(brightness_values) if brightness_values else 0.0
        high_confidence_count = sum(
            1 for h in hotspots if h["confidence"] == "high"
        )

        return {
            "total_frp": total_frp,
            "avg_brightness": avg_brightness,
            "high_confidence_count": high_confidence_count,
        }
