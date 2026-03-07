# VIIRS/FIRMS

> NASA satellite fire detection for conflict damage and infrastructure destruction verification

## Quick Reference

| Field | Value |
|-------|-------|
| Adapter | `viirs` |
| CLI | `pm signals --source viirs` |
| Auth | NASA_FIRMS_MAP_KEY |
| Refresh | 24 hours |
| API Docs | https://firms.modaps.eosdis.nasa.gov/api/ |

## Parameters

| Parameter | CLI Flag | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| country | `--param country=UA` | yes* | None | ISO-2 country code (predefined bboxes) |
| area | `--param area=30,40,35,45` | yes* | None | Custom bounding box "west,south,east,north" |
| days | `--param days=3` | no | 1 | Days back (1-10 max) |
| source | `--param source=VIIRS_SNPP_NRT` | no | VIIRS_SNPP_NRT | Satellite instrument |

\* Either `country` or `area` required

## Intelligence Use Cases

- **Conflict Damage Verification:** Confirm reported strikes on infrastructure (Ukraine refineries, power plants)
- **Infrastructure Destruction:** Detect and geolocate attacks on industrial facilities from satellite thermal signatures
- **Crisis Monitoring:** Track fire activity during civil unrest or military operations (Venezuela protests, Middle East conflicts)
- **Energy Infrastructure:** Verify refinery fires, pipeline explosions, or industrial sabotage claims

## Example Queries

```bash
# Ukraine fires last 3 days (conflict zones)
pm signals --source viirs --param country=UA --param days=3 --json

# Iran custom region (refineries)
pm signals --source viirs --param area=44,30,55,38 --param days=2 --json

# Russia western region
pm signals --source viirs --param country=RU --param days=5 --json
```

## Valid Country Codes (Predefined Bounding Boxes)

| Code | Country | Bounding Box (W,S,E,N) |
|------|---------|------------------------|
| IR | Iran | 44,25,63,40 |
| RU | Russia (western) | 27,41,60,70 |
| CN | China (eastern) | 100,20,125,45 |
| VE | Venezuela | -73,1,-60,13 |
| US | Continental US | -125,24,-66,50 |
| DE | Germany | 5,47,16,55 |
| TR | Turkey | 26,36,45,42 |
| UA | Ukraine | 22,44,40,53 |

## Output Schema

```json
{
  "source": "viirs",
  "country": "UA",
  "area": "22,44,40,53",
  "days": 3,
  "hotspot_count": 47,
  "hotspots": [
    {
      "latitude": 48.45,
      "longitude": 35.12,
      "brightness": 345.6,
      "frp": 12.3,
      "confidence": "high",
      "acq_date": "2026-03-06",
      "acq_time": "1430",
      "daynight": "D"
    }
  ],
  "summary": {
    "total_frp": 578.9,
    "avg_brightness": 342.1,
    "high_confidence_count": 23
  },
  "fetched_at": "2026-03-07T12:00:00+00:00"
}
```

## Notes

- `brightness` is in Kelvin (thermal signature)
- `frp` is Fire Radiative Power in megawatts
- Confidence: "high", "nominal", or "low"
- `daynight`: "D" for day, "N" for night acquisitions
- Days parameter limited to 10 by NASA API
- MAP_KEY required (register at firms.modaps.eosdis.nasa.gov)
