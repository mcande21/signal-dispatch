# ENTSOG

> European gas pipeline physical flow data from transmission system operators

## Quick Reference

| Field | Value |
|-------|-------|
| Adapter | `entsog` |
| CLI | `pm signals --source entsog` |
| Auth | None |
| Refresh | 1 hour |
| API Docs | https://transparency.entsog.eu/#/api |

## Parameters

| Parameter | CLI Flag | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| country | `--param country=DE` | yes | None | ISO-2 country code |
| indicator | `--param indicator=Physical Flow` | no | Physical Flow | Flow metric type |
| period_type | `--param period_type=day` | no | day | Time granularity |
| limit | `--param limit=20` | no | 10 | Max records returned |
| days | `--param days=14` | no | 7 | Days back from today |

## Intelligence Use Cases

- **Russia-Europe Energy Leverage:** Monitor flows at key points like Mallnow (Germany) to detect supply manipulation or disruption
- **Sanctions Impact:** Track changes in Russian gas flows through transit countries (Poland, Hungary) before/after policy changes
- **Energy Security Signals:** Sudden drops in flow values indicate supply chain vulnerability or political tension

## Example Queries

```bash
# German gas flows last 14 days
pm signals --source entsog --param country=DE --param days=14 --json

# Polish entry points (Russia transit)
pm signals --source entsog --param country=PL --param limit=20 --json

# Hourly flows for Hungary
pm signals --source entsog --param country=HU --param period_type=hour --json
```

## Valid Country Codes

AT, BE, BG, CZ, DE, DK, EE, ES, FI, FR, GR, HR, HU, IE, IT, LT, LU, LV, NL, PL, PT, RO, SE, SI, SK, UA

(All EU member states plus Ukraine)

## Output Schema

```json
{
  "source": "entsog",
  "country": "DE",
  "indicator": "Physical Flow",
  "period_type": "day",
  "record_count": 10,
  "flows": [
    {
      "point_key": "DE-GASPOOL-0001ITP-00096",
      "point_label": "Mallnow",
      "direction": "entry",
      "value": 123456789.0,
      "unit": "kWh/d",
      "period_from": "2026-03-06",
      "period_to": "2026-03-07",
      "operator_key": "DE-TSO-0001"
    }
  ],
  "fetched_at": "2026-03-07T12:00:00+00:00"
}
```

## Notes

- Null `value` fields are normal (no flow that period)
- Units vary by point: kWh/d or Nm3/d (normal cubic meters per day)
- Entry = gas entering country, Exit = gas leaving country
- Point labels are human-readable (Mallnow, Yamal, etc.)
