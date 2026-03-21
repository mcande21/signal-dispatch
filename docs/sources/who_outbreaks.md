# WHO Disease Outbreak News

> Active disease outbreak notices from the World Health Organization

## Quick Reference

| Field | Value |
|-------|-------|
| Adapter | `who_outbreaks` |
| CLI | `pm signals --source who_outbreaks` |
| Auth | None |
| Refresh | 24 hours |
| API | https://www.who.int/api/news/diseaseoutbreaknews |

## Signal Value

Disease outbreaks → macro disruption signals:
- Supply chain stress (port/logistics closures, labor shortages)
- Commodity demand shifts (medical supplies, food security)
- Travel/trade route closure risk
- Labor market impact in affected regions

Not a direct market signal — most useful for identifying second-order effects on commodity prices and regional trade flows.

## Example Queries

```bash
# Fetch all active outbreak notices
pm signals --source who_outbreaks --json

# Check notice count
pm signals --source who_outbreaks --json | jq '.notice_count'

# Filter for specific disease
pm signals --source who_outbreaks --json | jq '.active_notices[] | select(.disease == "Mpox")'
```

## Output Schema

```json
{
  "source": "who_outbreaks",
  "fetched_at": "2026-03-20T04:00:00Z",
  "notice_count": 50,
  "active_notices": [
    {
      "title": "Avian influenza – situation in Egypt",
      "disease": "Avian influenza",
      "countries": ["Egypt"],
      "published_at": "2026-03-15T00:00:00+00:00",
      "summary": "Truncated plain-text summary (500 char max)",
      "url": "https://www.who.int/..."
    }
  ]
}
```

## Notes

- Returns all notices (up to API default, typically 50 most recent)
- `disease` and `countries` are best-effort extractions from the title — may be null/empty for unusual title formats
- 24h cache; outbreak situations can change faster — check `published_at` on individual notices
- Complements CDC Travel Health Notices with international perspective
