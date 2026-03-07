# Oryx

> Visually confirmed military equipment losses in Russia-Ukraine war from photographic evidence

## Quick Reference

| Field | Value |
|-------|-------|
| Adapter | `oryx` |
| CLI | `pm signals --source oryx` |
| Auth | None |
| Refresh | 12h |
| API Docs | https://github.com/scarnecchia/oryx_data |

## Parameters

| Parameter | CLI Flag | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| dataset | `--param dataset={type}` | No | totals | "totals" (cumulative) or "daily" (time series) |
| country | `--param country={name}` | No | Both | Filter to "Russia" or "Ukraine" |

## Intelligence Use Cases

- **Attrition tracking:** Cumulative equipment losses indicate long-term degradation
- **Operational tempo:** Daily loss rates spike during offensives or major engagements
- **Force composition:** Equipment type distribution reveals doctrine and supply chains

## Example Queries

```bash
# Total Russian losses
pm signals --source oryx --param dataset=totals --param country=Russia --json

# Ukrainian daily losses
pm signals --source oryx --param dataset=daily --param country=Ukraine --json

# All cumulative losses
pm signals --source oryx --json
```

## Valid Values

**dataset:**
- `totals` - Cumulative losses by equipment type (default)
- `daily` - Time series of daily losses

**country:**
- `Russia`
- `Ukraine`
- (omit for both)

## Output Schema

**Totals:**
```json
{
  "source": "oryx",
  "dataset": "totals",
  "country_filter": "Russia",
  "record_count": 45,
  "equipment": [
    {
      "country": "Russia",
      "equipment_type": "Main Battle Tank",
      "destroyed": 1234,
      "captured": 456,
      "abandoned": 78,
      "damaged": 123
    }
  ]
}
```

**Daily:**
```json
{
  "source": "oryx",
  "dataset": "daily",
  "country_filter": "Ukraine",
  "daily_losses": [
    {
      "date": "2024-03-07",
      "country": "Ukraine",
      "total": 15,
      "destroyed": 8,
      "captured": 2,
      "abandoned": 3,
      "damaged": 2
    }
  ]
}
```

## Notes

- All losses photographically verified (Oryx's standard)
- Actual losses likely higher - not all losses documented
- Daily dataset useful for tracking operational intensity
