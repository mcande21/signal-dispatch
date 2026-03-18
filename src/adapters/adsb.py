"""ADS-B Exchange military flight tracking adapter.

Unfiltered flight data including military aircraft -- no MLAT filtering,
no government-request removals. Key value: detecting ISR surges, bomber
deployments, tanker operations, VIP/continuity-of-government aircraft.

Source: https://adsbexchange-com1.p.rapidapi.com/v2/mil/
Auth: ADSB_API_KEY env var (RapidAPI key, X-RapidAPI-Key header)
TTL: 5 minutes (live flight data)
"""

import os

import httpx

from .base import GhostMarketAdapter, GhostMarketApiError


ADSB_API_URL = "https://adsbexchange-com1.p.rapidapi.com/v2/mil/"
ADSB_RAPIDAPI_HOST = "adsbexchange-com1.p.rapidapi.com"

# US military ICAO hex ranges (inclusive)
# AE0000-AE0FFF is the well-known US mil allocation block
US_MIL_HEX_RANGES = [
    (0xAE0000, 0xAEFFFF),
]

# Callsign prefix patterns and their operational context
# Keys are prefix strings; values are (category, reason) tuples
CALLSIGN_PATTERNS = {
    "RCH": ("airlift", "C-17 REACH airlift mission"),
    "REACH": ("airlift", "Military Airlift Command"),
    "JAKE": ("tanker", "KC-135 tanker"),
    "DUKE": ("tanker", "KC-135 tanker"),
    "COBRA": ("unknown", "Military COBRA mission"),
    "DARK": ("unknown", "Special operations"),
    "FORTE": ("isr", "RQ-4 Global Hawk ISR drone"),
    "IRON": ("fighter", "Fighter mission"),
    "VIPER": ("fighter", "Fighter mission"),
    "HAVOC": ("fighter", "Fighter mission"),
}

# Aircraft type strings to category + reason mapping.
# Matched as case-insensitive substrings against the `t` field from ADS-B Exchange.
AIRCRAFT_TYPE_MAP = [
    # ISR / SIGINT
    ("RC135", "isr", "RC-135 Rivet Joint SIGINT"),
    ("RC-135", "isr", "RC-135 Rivet Joint SIGINT"),
    ("E3", "isr", "E-3 Sentry AWACS"),
    ("E-3", "isr", "E-3 Sentry AWACS"),
    ("RQ4", "isr", "RQ-4 Global Hawk ISR drone"),
    ("RQ-4", "isr", "RQ-4 Global Hawk ISR drone"),
    ("P8", "patrol", "P-8 Poseidon maritime patrol"),
    ("P-8", "patrol", "P-8 Poseidon maritime patrol"),
    # Nuclear command / continuity of government
    ("E6", "command", "E-6B Mercury nuclear command relay"),
    ("E-6", "command", "E-6B Mercury nuclear command relay"),
    ("E4", "command", "E-4B Nightwatch airborne command post"),
    ("E-4", "command", "E-4B Nightwatch airborne command post"),
    # Bombers
    ("B52", "bomber", "B-52 Stratofortress"),
    ("B-52", "bomber", "B-52 Stratofortress"),
    ("B1", "bomber", "B-1 Lancer"),
    ("B-1", "bomber", "B-1 Lancer"),
    ("B2", "bomber", "B-2 Spirit stealth bomber"),
    ("B-2", "bomber", "B-2 Spirit stealth bomber"),
    # Tankers
    ("KC135", "tanker", "KC-135 Stratotanker"),
    ("KC-135", "tanker", "KC-135 Stratotanker"),
    ("KC46", "tanker", "KC-46 Pegasus"),
    ("KC-46", "tanker", "KC-46 Pegasus"),
    # Airlift
    ("C17", "airlift", "C-17 Globemaster"),
    ("C-17", "airlift", "C-17 Globemaster"),
    ("C5", "airlift", "C-5 Galaxy"),
    ("C-5", "airlift", "C-5 Galaxy"),
]

# Aircraft types that warrant inclusion in the notable list
NOTABLE_TYPES = {"command", "bomber", "isr"}

# Callsign prefixes that always warrant notable status
NOTABLE_CALLSIGN_PREFIXES = {"FORTE"}

# Empty result template -- returned on API unavailability
_EMPTY_RESULT = {
    "source": "adsb",
    "total_military": 0,
    "aircraft": [],
    "by_category": {
        "isr": 0,
        "bomber": 0,
        "tanker": 0,
        "airlift": 0,
        "command": 0,
        "patrol": 0,
        "fighter": 0,
        "unknown": 0,
    },
    "notable": [],
}


def _hex_in_us_mil_range(hex_str: str) -> bool:
    """Return True if ICAO hex code falls within known US military allocations."""
    if not hex_str:
        return False
    try:
        value = int(hex_str.upper(), 16)
    except ValueError:
        return False
    return any(lo <= value <= hi for lo, hi in US_MIL_HEX_RANGES)


def _classify_aircraft(hex_str: str, callsign: str, ac_type: str) -> tuple[str, str | None]:
    """Derive (category, notable_reason) from available aircraft fields.

    Returns:
        category: one of isr/bomber/tanker/airlift/command/patrol/fighter/unknown
        notable_reason: str if this aircraft warrants notable flag, else None
    """
    callsign_upper = (callsign or "").strip().upper()
    type_upper = (ac_type or "").strip().upper()

    # 1. Type-based classification (most reliable)
    for type_substr, category, description in AIRCRAFT_TYPE_MAP:
        if type_substr.upper() in type_upper:
            notable_reason = description if category in NOTABLE_TYPES else None
            return category, notable_reason

    # 2. Callsign-prefix classification
    for prefix, (category, reason) in CALLSIGN_PATTERNS.items():
        if callsign_upper.startswith(prefix):
            notable_reason = reason if prefix in NOTABLE_CALLSIGN_PREFIXES else None
            return category, notable_reason

    # 3. Hex range implies US military, but type unknown
    if _hex_in_us_mil_range(hex_str):
        return "unknown", None

    return "unknown", None


def _parse_aircraft(raw: dict) -> dict:
    """Map a raw ADS-B Exchange aircraft record to the adapter output shape."""
    hex_str = (raw.get("hex") or "").strip().upper()
    callsign = (raw.get("flight") or raw.get("callsign") or "").strip()
    ac_type = (raw.get("t") or raw.get("type") or "").strip()

    category, _ = _classify_aircraft(hex_str, callsign, ac_type)

    def _safe_float(val) -> float:
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0

    def _safe_int(val) -> int:
        try:
            return int(val)
        except (TypeError, ValueError):
            return 0

    return {
        "hex": hex_str,
        "callsign": callsign,
        "type": ac_type,
        "category": category,
        "alt_baro": _safe_int(raw.get("alt_baro")),
        "lat": _safe_float(raw.get("lat")),
        "lon": _safe_float(raw.get("lon")),
        "ground_speed": _safe_float(raw.get("gs")),
        "track": _safe_float(raw.get("track")),
    }


def _build_notable(aircraft: list[dict]) -> list[dict]:
    """Return list of notable aircraft entries with reason strings."""
    notable = []
    for ac in aircraft:
        hex_str = ac["hex"]
        callsign = ac["callsign"]
        ac_type = ac["type"]
        _, notable_reason = _classify_aircraft(hex_str, callsign, ac_type)
        if notable_reason:
            notable.append({
                "hex": hex_str,
                "callsign": callsign,
                "type": ac_type,
                "reason": notable_reason,
            })
    return notable


def _tally_by_category(aircraft: list[dict]) -> dict:
    """Count aircraft per category."""
    tally = {
        "isr": 0,
        "bomber": 0,
        "tanker": 0,
        "airlift": 0,
        "command": 0,
        "patrol": 0,
        "fighter": 0,
        "unknown": 0,
    }
    for ac in aircraft:
        cat = ac.get("category", "unknown")
        if cat in tally:
            tally[cat] += 1
        else:
            tally["unknown"] += 1
    return tally


class AdsbAdapter(GhostMarketAdapter):
    """ADS-B Exchange military flight tracking adapter.

    Fetches all military aircraft from the unfiltered /v2/mil/ endpoint.
    Classifies by type, callsign pattern, and hex range.
    Returns structured snapshot with categorized counts and notable aircraft.

    Rate limit: 500 requests/month on free RapidAPI tier.
    TTL is set to 5 minutes to balance freshness against quota.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.api_key = os.environ.get("ADSB_API_KEY")

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 5 minutes.

        ADS-B data is live, but the free tier is 500 req/month (~16/day).
        5-minute TTL allows ~288 fetches/day if called continuously, well
        within monthly budget when used for periodic intelligence pulls.
        """
        return 5 * 60

    @property
    def source_name(self) -> str:
        return "adsb"

    async def fetch(self, query: dict) -> dict:  # noqa: ARG002
        """Fetch current military aircraft snapshot from ADS-B Exchange.

        Args:
            query: unused -- the /v2/mil/ endpoint returns all military
                   aircraft with no geographic or type filter required.

        Returns:
            {
                "source": "adsb",
                "total_military": int,
                "aircraft": list[dict],
                "by_category": dict[str, int],
                "notable": list[dict],
            }

        Raises:
            GhostMarketApiError: on HTTP errors (retryable for 5xx).
        """
        cache_key = "adsb_mil_snapshot"

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        if not self.api_key:
            raise GhostMarketApiError(
                "ADSB_API_KEY not set -- set RapidAPI key in environment",
                retryable=False,
            )

        raw_aircraft = await self._fetch_military_aircraft()

        parsed = [_parse_aircraft(ac) for ac in raw_aircraft]

        result = {
            "source": "adsb",
            "total_military": len(parsed),
            "aircraft": parsed,
            "by_category": _tally_by_category(parsed),
            "notable": _build_notable(parsed),
        }

        await self._cache_store(cache_key, result)
        return result

    async def _fetch_military_aircraft(self) -> list[dict]:
        """Call the ADS-B Exchange /v2/mil/ endpoint and return raw aircraft list."""
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": ADSB_RAPIDAPI_HOST,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    ADSB_API_URL,
                    headers=headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            raise GhostMarketApiError(
                f"ADS-B Exchange API error: HTTP {e.response.status_code}",
                status_code=e.response.status_code,
                retryable=e.response.status_code >= 500,
            ) from e
        except httpx.HTTPError as e:
            raise GhostMarketApiError(
                f"ADS-B Exchange network error: {e}",
                retryable=True,
            ) from e

        # API returns {"ac": [...], "total": int, ...} or {"aircraft": [...]}
        aircraft_list = data.get("ac") or data.get("aircraft") or []
        if not isinstance(aircraft_list, list):
            return []

        return aircraft_list
