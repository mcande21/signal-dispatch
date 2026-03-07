# EIA Grid

> US electricity grid demand, generation, and interchange by region

## Quick Reference

| Field | Value |
|-------|-------|
| Adapter | `eia_grid` |
| CLI | `pm signals --source eia_grid` |
| Auth | EIA_API_KEY |
| Refresh | 1 hour |
| API Docs | https://www.eia.gov/opendata/documentation.php |

## Parameters

| Parameter | CLI Flag | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| respondent | `--param respondent=PJM` | no | US48 | Region code (see list below) |
| type | `--param type=NG` | no | D | Data type: D=demand, NG=net generation |
| frequency | `--param frequency=hourly` | no | daily | Time granularity: daily or hourly |
| length | `--param length=30` | no | 14 | Number of records to return |

## Intelligence Use Cases

- **Infrastructure Stress:** Detect demand spikes during extreme weather (heat waves, cold snaps) that stress grid capacity
- **Regional Vulnerability:** Track generation shortfalls in specific regions (Texas winter storms, California heat)
- **Energy Security:** Monitor cross-border interchange with Mexico/Canada during supply disruptions
- **Policy Impact:** Measure generation mix changes after coal plant closures or renewable deployment

## Example Queries

```bash
# Texas grid demand last 30 days
pm signals --source eia_grid --param respondent=ERCO --param length=30 --json

# PJM net generation hourly
pm signals --source eia_grid --param respondent=PJM --param type=NG --param frequency=hourly --json

# Lower 48 aggregate demand
pm signals --source eia_grid --param respondent=US48 --param length=60 --json
```

## Valid Respondent Codes

US48, BPAT, CISO, ERCO, ISNE, MISO, NYIS, PJM, SOCO, SWPP

- **US48:** Continental United States aggregate
- **BPAT:** Bonneville Power (Pacific Northwest)
- **CISO:** California Independent System Operator
- **ERCO:** Electric Reliability Council of Texas (ERCOT)
- **ISNE:** ISO New England
- **MISO:** Midcontinent Independent System Operator
- **NYIS:** New York Independent System Operator
- **PJM:** PJM Interconnection (Mid-Atlantic)
- **SOCO:** Southern Company
- **SWPP:** Southwest Power Pool

## Output Schema

```json
{
  "source": "eia_grid",
  "respondent": "PJM",
  "type": "D",
  "frequency": "daily",
  "record_count": 14,
  "grid_data": [
    {
      "period": "2026-03-06",
      "value": 123456.78,
      "respondent": "PJM",
      "respondent_name": "PJM Interconnection",
      "type": "D",
      "type_name": "Demand"
    }
  ],
  "fetched_at": "2026-03-07T12:00:00+00:00"
}
```

## Notes

- Values are in megawatt-hours (MWh)
- Hourly frequency returns more granular data but uses more quota
- API key required (register at eia.gov/opendata)
- Rate limit: 5 requests per second
