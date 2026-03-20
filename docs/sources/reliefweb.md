# ReliefWeb

> UN humanitarian crises and ongoing disaster tracker

## Quick Reference

| Field | Value |
|-------|-------|
| Adapter | `reliefweb` |
| CLI | `pm signals --source reliefweb` |
| Auth | Registered appname required (see Notes) |
| Refresh | 12 hours |
| API | https://api.reliefweb.int/v1/disasters |

## Signal Value

Active UN-declared disasters → geopolitical disruption indicators:
- Commodity supply disruption (conflict, flood, drought affecting production regions)
- Market access risk (port/infrastructure damage)
- Humanitarian crises that presage political instability
- Leading indicator for refugee flows and regional destabilization

## Status

⚠️ **Registration required.** ReliefWeb requires an approved `appname` parameter (as of late 2025). The adapter is built and ready but returns 403 until a registered appname is configured.

To register: <https://apidoc.reliefweb.int/parameters#appname>

Once approved, set `RELIEFWEB_APPNAME` env var or update the constant in `reliefweb.py`.

## Example Queries

```bash
# Fetch all ongoing disasters (requires registered appname)
pm signals --source reliefweb --json

# Count active disasters
pm signals --source reliefweb --json | jq '.disaster_count'

# Filter by country
pm signals --source reliefweb --json | jq '.active_disasters[] | select(.countries[] | contains("Sudan"))'
```

## Output Schema

```json
{
  "source": "reliefweb",
  "fetched_at": "2026-03-20T04:00:00Z",
  "disaster_count": 42,
  "active_disasters": [
    {
      "name": "Sudan: Civil War (2023 - )",
      "countries": ["Sudan"],
      "date": "2023-04-16T00:00:00+00:00",
      "type": ["Civil Unrest"],
      "status": "ongoing",
      "url": "https://reliefweb.int/disaster/..."
    }
  ]
}
```

## Notes

- Filters for `status=ongoing` only (excludes resolved disasters)
- Returns up to 50 most recent ongoing disasters, sorted by date desc
- Adapter handles 500/429/timeout with retryable error classification
