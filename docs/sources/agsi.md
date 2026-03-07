# AGSI

> European gas storage inventory levels and injection/withdrawal rates

## Quick Reference

| Field | Value |
|-------|-------|
| Adapter | `agsi` |
| CLI | `pm signals --source agsi` |
| Auth | AGSI_API_KEY |
| Refresh | 12 hours |
| API Docs | https://agsi.gie.eu/api |

## Parameters

| Parameter | CLI Flag | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| country | `--param country=DE` | yes | None | ISO-2 country code |
| size | `--param size=60` | no | 30 | Number of daily records |
| days | `--param days=60` | no | 30 | Days back (computes from date) |

## Intelligence Use Cases

- **Energy Security Baseline:** Track storage levels before winter heating season to assess vulnerability
- **Seasonal Vulnerability:** Detect abnormal drawdown rates during cold snaps or supply disruptions
- **Policy Impact:** Measure storage rebuild rates after Russian supply cuts or sanctions implementation
- **Crisis Preparedness:** Compare current storage percent-full to historical averages for early warning

## Example Queries

```bash
# German storage last 60 days
pm signals --source agsi --param country=DE --param size=60 --json

# Dutch storage trends
pm signals --source agsi --param country=NL --param days=30 --json

# Austria winter drawdown
pm signals --source agsi --param country=AT --param size=90 --json
```

## Valid Country Codes

AT, BE, BG, CZ, DE, DK, ES, FR, HR, HU, IT, LV, NL, PL, PT, RO, SE, SK, UA

(EU member states plus Ukraine with storage capacity)

## Output Schema

```json
{
  "source": "agsi",
  "country": "DE",
  "record_count": 30,
  "storage_data": [
    {
      "gas_day": "2026-03-06",
      "gas_in_storage": 156.78,
      "full_pct": 67.4,
      "injection": 0.12,
      "withdrawal": 1.45,
      "consumption": 2.34,
      "trend": -1.33
    }
  ],
  "fetched_at": "2026-03-07T12:00:00+00:00"
}
```

## Notes

- `gas_in_storage`, `injection`, `withdrawal`, `consumption` all in TWh
- `full_pct` is percentage (0-100)
- `trend` is day-over-day change
- Some fields may be null (consumption data not always available)
- Records ordered by gas_day descending (newest first)
- API key required (register at agsi.gie.eu)
