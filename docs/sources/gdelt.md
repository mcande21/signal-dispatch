# GDELT

> Global news event database with real-time article tracking and tone analysis

## Quick Reference

| Field | Value |
|-------|-------|
| Adapter | `gdelt` |
| CLI | `pm signals --source gdelt` |
| Auth | None |
| Refresh | 15 minutes |
| API Docs | https://api.gdeltproject.org/api/v2/doc/doc |

## Parameters

| Parameter | CLI Flag | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| query | `--param query="terms"` | yes | - | Search terms (keywords, phrases) |
| maxrecords | `--param maxrecords=N` | no | 25 | Max articles returned (1-250) |
| timespan | `--param timespan=Nd` | no | "1d" | Time window (e.g., "1d", "7d", "30d") |
| mode | `--param mode=MODE` | no | "ArtList" | Query mode (ArtList, TimelineVol, etc.) |

## Intelligence Use Cases

- **Protest tracking:** Monitor "protest iran" for coverage volume and geographic spread
- **Sanctions monitoring:** Track "OFAC sanctions" for enforcement announcements
- **Regional conflict:** Search "houthi attack" for escalation patterns
- **Policy signals:** Query "state department iran" for diplomatic posture shifts
- **Market events:** Track "oil supply disruption" for energy security signals

## Example Queries

```bash
# Monitor Iran protest coverage over last week
pm signals --source gdelt --param query="protest iran" --param timespan=7d --json

# Track Houthi activity (last 24h, top 50 articles)
pm signals --source gdelt --param query="houthi attack" --param maxrecords=50 --json

# Oil disruption headlines (last 3 days)
pm signals --source gdelt --param query="oil supply disruption" --param timespan=3d --json
```

## Output Schema

```json
{
  "source": "gdelt",
  "query": "search terms",
  "timespan": "7d",
  "article_count": 42,
  "articles": [
    {
      "url": "https://...",
      "title": "Article headline",
      "source": "domain.com",
      "language": "English",
      "seendate": "20260307T120000Z"
    }
  ],
  "fetched_at": "2026-03-07T12:00:00Z"
}
```

## Notes

- Rate limit: undefined (adapter handles 429 retries)
- Timespan format: `Nd` where N is days (e.g., "1d", "7d", "30d")
- Mode "ArtList" returns article URLs + metadata (default)
- **Stretch capabilities not yet exposed:** tone filtering, source country filtering,
  GKG (Global Knowledge Graph) queries, timeline volume analysis, geo-specific search
