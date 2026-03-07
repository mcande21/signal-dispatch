# ECB Statistical Data Warehouse

> European Central Bank economic data in SDMX JSON format

## Quick Reference

| Field | Value |
|-------|-------|
| Adapter | `ecb` |
| CLI | `pm signals --source ecb` |
| Auth | None |
| Refresh | 6 hours |
| API Docs | https://data.ecb.europa.eu/help/api/data |

## Parameters

| Parameter | CLI Flag | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| flow_ref | `--param flow_ref={value}` | yes | none | Dataset identifier (e.g., EXR, BSI, ICP) |
| key | `--param key={value}` | yes | none | Data series within dataset (e.g., D.USD.EUR.SP00.A) |
| start_period | `--param start_period={date}` | no | 30 days ago | Start date (YYYY-MM-DD) |
| end_period | `--param end_period={date}` | no | today | End date (YYYY-MM-DD) |

## Intelligence Use Cases

- **Currency stress signals:** EUR/USD for dollar weaponization stories, EUR/TRY for Turkey economic pressure, EUR/RUB for Russia sanctions impact
- **Inflation trends:** ICP indices for eurozone price stability, potential ECB policy shifts
- **Banking sector stability:** BSI data for eurozone banking stress indicators

## Example Queries

```bash
# EUR/USD exchange rate (30 days)
pm signals --source ecb --param flow_ref=EXR --param key=D.USD.EUR.SP00.A --json

# EUR/TRY for Turkey economic pressure (90 days)
pm signals --source ecb --param flow_ref=EXR --param key=D.TRY.EUR.SP00.A \
  --param start_period=2025-12-01 --param end_period=2026-03-01 --json

# EUR/RUB for Russia sanctions impact (6 months)
pm signals --source ecb --param flow_ref=EXR --param key=D.RUB.EUR.SP00.A \
  --param start_period=2025-09-01 --json
```

## Valid Values

**Critical:** `flow_ref` and `key` are REQUIRED with no defaults.

Common `flow_ref` datasets:
- **EXR** - Exchange rates
- **ICP** - Inflation (HICP indices)
- **BSI** - Balance sheet items (banking data)

Common `key` values for EXR:
- `D.USD.EUR.SP00.A` - EUR/USD daily spot
- `D.TRY.EUR.SP00.A` - EUR/TRY daily spot
- `D.RUB.EUR.SP00.A` - EUR/RUB daily spot
- `D.CNY.EUR.SP00.A` - EUR/CNY daily spot

Key format: `{freq}.{currency}.{currency}.{type}.{series}`

## Output Schema

```json
{
  "source": "ecb",
  "flow_ref": "EXR",
  "key": "D.USD.EUR.SP00.A",
  "record_count": 30,
  "observations": [
    {"date": "2026-02-05", "value": 1.0821},
    {"date": "2026-02-06", "value": 1.0835}
  ],
  "fetched_at": "2026-03-07T12:00:00Z"
}
```

## Notes

- SDMX JSON format with numeric indices for dimensions and observations
- Empty result sets return `[]` for observations (valid query, no data)
- Rate limits: None specified, but 6-hour cache TTL prevents excessive requests
- Invalid flow_ref/key combinations return HTTP 4xx errors
