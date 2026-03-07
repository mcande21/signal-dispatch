# dolarVzla

> Venezuelan parallel market USD/VES exchange rates from multiple independent monitors

## Quick Reference

| Field | Value |
|-------|-------|
| Adapter | `dolarvzla` |
| CLI | `pm signals --source dolarvzla` |
| Auth | None |
| Refresh | 1h |
| API Docs | https://ve.dolarapi.com |

## Parameters

| Parameter | CLI Flag | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| monitor | `--param monitor={name}` | No | All | Filter to specific rate source (e.g., "bcv", "enparalelovzla") |

## Intelligence Use Cases

- **Capital flight pressure:** Official (BCV) vs parallel market spread indicates capital controls stress
- **Regime stability indicator:** Parallel rate spikes signal confidence collapse in official currency
- **Cross-border analysis:** Compare to Colombian peso, Brazil real for regional contagion

## Example Queries

```bash
# All monitors
pm signals --source dolarvzla --json

# Official rate only
pm signals --source dolarvzla --param monitor=bcv --json

# Parallel market baseline
pm signals --source dolarvzla --param monitor=enparalelovzla --json
```

## Valid Values

**monitor** (partial list - API returns all available):
- `bcv` - Banco Central de Venezuela (official rate)
- `enparalelovzla` - EnParaleloVzla monitor
- `promedio` - Average across monitors

## Output Schema

```json
{
  "source": "dolarvzla",
  "record_count": 5,
  "rates": [
    {
      "name": "bcv",
      "buy": 36.50,
      "sell": 36.50,
      "average": 36.50,
      "last_update": "2024-03-07T12:00:00Z"
    }
  ],
  "fetched_at": "2024-03-07T14:30:00Z"
}
```

## Notes

- Some monitors report buy/sell/average, some only average
- BCV (official) typically shows significantly lower rate than parallel markets
- Rapid parallel rate changes indicate acute dollar demand pressure
