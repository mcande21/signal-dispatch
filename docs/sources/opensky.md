# OpenSky — Regional Airspace Monitor

> Civilian flight density across 6 strategic regions as an escalation indicator

## Quick Reference

| Field | Value |
|-------|-------|
| Adapter | `opensky` |
| CLI | `pm signals --source opensky` |
| Auth | None (4000 credits/day anonymous) |
| Refresh | 30 minutes |
| API | https://opensky-network.org/api/states/all |

## Signal Value

Civilian airspace as geopolitical signal:
- **Traffic drops** = airspace closure = escalation indicator
- **No-callsign count** = potential unidentified or military traffic bleeding into civilian bands
- **Origin country mix** = regional power presence shifts over contested areas
- Complements `adsb.py` (military-only ADS-B Exchange) with civilian baseline

Different from military tracking — this is the civilian layer. A region going quiet on both channels simultaneously is a strong escalation signal.

## Monitored Regions

| Region | Bounding Box | Signal Context |
|--------|-------------|----------------|
| Taiwan Strait | 22-26°N, 119-122.5°E | Cross-strait tension indicator |
| Persian Gulf | 23-30°N, 48-57°E | Iran/Gulf state activity |
| Black Sea | 40.5-46.5°N, 27.5-41.5°E | Ukraine conflict spillover |
| Red Sea | 12-30°N, 32-44°E | Houthi disruption baseline |
| South China Sea | 5-22°N, 109-121°E | SCS territorial dispute activity |
| Eastern Mediterranean | 30-38°N, 25-37°E | Israel/Lebanon/Syria corridor |

## Example Queries

```bash
# Full regional snapshot
pm signals --source opensky --json

# Taiwan Strait aircraft count
pm signals --source opensky --json | jq '.regions.taiwan_strait.aircraft_count'

# Red Sea — check for airspace suppression
pm signals --source opensky --json | jq '.regions.red_sea'

# All regions sorted by aircraft count
pm signals --source opensky --json | jq '.regions | to_entries | sort_by(-.value.aircraft_count) | .[] | "\(.key): \(.value.aircraft_count)"'
```

## Output Schema

```json
{
  "source": "opensky",
  "snapshot_at": "2026-03-20T04:14:42Z",
  "regions": {
    "taiwan_strait": {
      "aircraft_count": 48,
      "by_country": {
        "Taiwan": 16,
        "China": 8,
        "Republic of Korea": 6
      },
      "no_callsign": 3
    },
    "red_sea": {
      "aircraft_count": 1,
      "by_country": {"Egypt": 1},
      "no_callsign": 0
    }
  }
}
```

## Baseline (2026-03-20 04:14 UTC)

Initial calibration snapshot:
- Taiwan Strait: 48 aircraft (Taiwan 16, China 8, Korea 6)
- Persian Gulf: 12 aircraft (UAE 8, Qatar 4)
- Black Sea: 36 aircraft (Turkey 17, China 2, Germany 2)
- **Red Sea: 1 aircraft** (Egypt 1) — Houthi disruption depressing traffic
- South China Sea: 57 aircraft (Philippines 16, China 10, Vietnam 8)
- Eastern Med: 50 aircraft (Turkey 16, UAE 10, Israel 4)

Red Sea at 1 vs South China Sea at 57 is the standout. Houthi threat has effectively closed civilian routing through the corridor.

## Notes

- Filters out on-ground aircraft (only airborne tracked)
- 1-second delay between region queries to respect anonymous rate limits
- 30-minute cache — short enough to catch airspace closures within one refresh cycle
- Anonymous limit: 4000 API credits/day. Each region query = ~1 credit. 6 regions × 48 refreshes/day = 288 credits/day. Well within limits.
