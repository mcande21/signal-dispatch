# UN Comtrade

> Bilateral trade flows by commodity -- imports/exports between countries

## Quick Reference

| Field | Value |
|-------|-------|
| Adapter | `comtrade` |
| CLI | `pm signals --source comtrade` |
| Auth | `COMTRADE_API_KEY` env var (fallback to preview endpoint) |
| Refresh | 24 hours |
| API Docs | https://comtradeapi.un.org |

## Parameters

| Parameter | CLI Flag | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| reporter | `--param reporter={code}` | yes | - | ISO-2 country code (mapped to M49 internally) |
| commodity | `--param commodity={code}` | no | 2709 | HS code (crude petroleum default) |
| flow | `--param flow={code}` | no | M | M=imports, X=exports |
| frequency | `--param frequency={code}` | no | A | A=annual, M=monthly |
| period | `--param period={year}` | no | current year | Year or YYYYMM for monthly |

## Intelligence Use Cases

- **Sanctions evasion:** Track commodity rerouting through intermediaries (Iran crude → Turkey, Russia oil → India)
- **Supply chain dependency:** Who imports what from sanctioned states
- **Trade diversion patterns:** Volume shifts after policy changes
- **Commodity strategic exposure:** Nuclear materials, arms, energy imports

## Example Queries

```bash
# Turkey importing Iranian crude petroleum (annual)
pm signals --source comtrade --param reporter=TR --param commodity=2709 --param flow=M --json

# Russia crude exports (monthly data for current year)
pm signals --source comtrade --param reporter=RU --param commodity=2709 --param flow=X --param frequency=M --json

# China gold imports
pm signals --source comtrade --param reporter=CN --param commodity=7108 --param flow=M --json
```

## Valid Values

**Mapped M49 Countries:** IR (Iran), RU (Russia), CN (China), VE (Venezuela), US (United States), DE (Germany), TR (Turkey), UA (Ukraine)

**Key HS Commodity Codes:**
- 2709: Crude petroleum
- 2711: Natural gas (LNG)
- 7108: Gold
- 8401-8405: Nuclear reactors/materials
- 93: Arms and ammunition (chapter-level)

**Flow Codes:** M (imports), X (exports)

**Frequency:** A (annual), M (monthly)

## Output Schema

```json
{
  "source": "comtrade",
  "reporter": "TR",
  "reporter_m49": 792,
  "commodity": "2709",
  "flow": "M",
  "frequency": "A",
  "record_count": 12,
  "trades": [
    {
      "period": "2024",
      "partner_code": 364,
      "partner_desc": "Iran",
      "trade_value": 125000000.0,
      "net_weight": 500000.0,
      "qty": null
    }
  ],
  "fetched_at": "2026-03-07T12:00:00Z"
}
```

## Notes

- Rate limit: 500 calls/day on free tier (returns 429 on exceeded)
- Country mapping is LIMITED to M49_CODES in adapter (8 countries)
- Unknown ISO codes will fail with available list
- Preview endpoint (public) used as fallback if auth fails
- Trade values in USD, weights in kg
