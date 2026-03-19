# INTELLIGENCE REPORT: SD #5 Research Tasks

## TASK 1: Sahm Rule Calculation -- RESOLVED

### The Discrepancy

Your two syntheses gave contradictory readings because one was citing the headline unemployment rate (4.4%) and the other was citing the Sahm indicator value (0.43). They were describing different numbers. The resolution is below.

### Raw Data (Last 15 Months of UNRATE)

Note: October 2025 is missing from the FRED data file.

| Month | Unemployment Rate |
|-------|------------------|
| 2024-12 | 4.1 |
| 2025-01 | 4.0 |
| 2025-02 | 4.2 |
| 2025-03 | 4.2 |
| 2025-04 | 4.2 |
| 2025-05 | 4.3 |
| 2025-06 | 4.1 |
| 2025-07 | 4.3 |
| 2025-08 | 4.3 |
| 2025-09 | 4.4 |
| 2025-11 | 4.5 |
| 2025-12 | 4.4 |
| 2026-01 | 4.3 |
| 2026-02 | 4.4 |

### Sahm Rule Calculation

**Step 1: 3-month moving average for the most recent 3 months (Dec 2025, Jan 2026, Feb 2026)**

(4.4 + 4.3 + 4.4) / 3 = **4.367%**

**Step 2: All 3-month moving averages from the prior 12 months**

Working backward from Nov 2025 (the 12 months before the current 3-month window):

| Window | Months | Average |
|--------|--------|---------|
| Feb-Apr 2025 | 4.2, 4.2, 4.2 | 4.200 |
| Mar-May 2025 | 4.2, 4.2, 4.3 | 4.233 |
| Apr-Jun 2025 | 4.2, 4.3, 4.1 | 4.200 |
| May-Jul 2025 | 4.3, 4.1, 4.3 | 4.233 |
| Jun-Aug 2025 | 4.1, 4.3, 4.3 | 4.233 |
| Jul-Sep 2025 | 4.3, 4.3, 4.4 | 4.333 |
| Sep-Nov 2025 | 4.4, 4.5 (skipping Oct gap) | -- |
| Jan-Mar 2025 | 4.0, 4.2, 4.2 | 4.133 |
| Dec 2024-Feb 2025 | 4.1, 4.0, 4.2 | 4.100 |

**Minimum 3-month average from prior 12 months: 4.100** (Dec 2024 - Feb 2025 window)

**Step 3: Sahm Indicator**

4.367 - 4.100 = **0.267 percentage points**

**Step 4: Has it crossed 0.50?**

**No.** At 0.27, the Sahm Rule has NOT triggered. It is well below the 0.50 threshold.

### Web Confirmation

FRED's own SAHMREALTIME series shows 0.30 for January 2026 and 0.27 for February 2026. My calculation of 0.267 rounds to the same neighborhood -- the small difference is likely due to the missing October 2025 observation in our data file (FRED would use October in its sliding windows).

**However -- critically -- one Motley Fool article from Feb 21, 2026 claims the Sahm Rule "flashed again."** And a FinancialContent piece from March 16 references the Sahm Rule being "triggered" at 4.4% unemployment. These articles appear to be conflating the unemployment rate with the indicator, or referencing a future data point we don't yet have. The February FRED data shows 0.27, clearly below 0.50.

### Verdict

**The Sahm Rule has NOT triggered as of February 2026 data.** The indicator stands at approximately 0.27pp, roughly halfway to the 0.50 trigger. The synthesis that said "approaching 0.50 at 0.43" was closer to correct in spirit but wrong on the exact number. The synthesis that said it "triggered at 4.4% unemployment" was conflating the unemployment rate with the recession indicator -- a common error in financial journalism. 4.4% is the unemployment rate, not the Sahm value.

That said, the trajectory matters: if unemployment ticks up to 4.5-4.6% in the coming months while the trailing minimum stays at 4.1, the Sahm indicator would cross 0.50. It is approaching but has not arrived.

---

## TASK 2: Yield Curve Compression During Supply Shock

### T10Y2Y Trajectory (Last ~3 Months from FRED Data)

| Date | Spread (pp) | Note |
|------|-------------|------|
| Dec 22 | 0.73 | Local high -- the "0.73" Legion cited |
| Dec 31 | 0.71 | |
| Jan 9 | 0.64 | First dip |
| Jan 20 | 0.70 | Brief recovery |
| Jan 30 | 0.74 | Local peak |
| Feb 5 | 0.74 | Second peak |
| Feb 9 | 0.74 | Plateau |
| Feb 11 | 0.66 | Sharp drop begins |
| Feb 12 | 0.62 | |
| Feb 20 | 0.60 | |
| Feb 27 | 0.59 | |
| Mar 2 | 0.58 | |
| Mar 3 | 0.55 | Acceleration |
| Mar 9 | 0.56 | |
| Mar 12 | 0.51 | Trough |
| Mar 17 | 0.52 | Current |

**The compression is real: 0.74 to 0.52 in roughly 5 weeks (Feb 9 to Mar 17).** That is a 22 basis point compression, or about 30% of the spread evaporating.

### What the Bond Market Is Saying (Web Intel)

The web research reveals something far more complex than a simple "flattening." The bond market in March 2026 is being whipsawed between two forces:

**Force 1: Growth Collapse (Pulls 10Y Down)**
- GDP growth slumped to 0.7% (per March 16 reporting)
- February jobs report showed 92,000 job losses
- Government shutdown disrupted federal spending
- The 10Y briefly hit 3.95-3.96% in late Feb / early March on pure recession fear

**Force 2: Supply-Side Inflation Shock (Pushes 10Y Up)**
- Oil spiked toward $115-150/bbl range on Strait of Hormuz closure
- Section 122 tariff surcharge (15% global) added cost-push inflation
- Core PCE hit 3.1%
- The 10Y then surged to 4.28% by March 13 on "war premium"

**The compression of the 10Y-2Y spread is happening because the 2Y is being held UP by Fed expectations** (markets pricing the Fed as trapped -- can't cut with 3.1% Core PCE), **while the 10Y is being pulled in both directions** (growth fears pull it down, inflation pushes it up). The net effect: the 10Y isn't rising as fast as "pure inflation" would suggest, because growth expectations are collapsing simultaneously.

This is the classic **stagflation signature** in the bond market.

### The Anomaly Legion Identified -- Why It Matters

Legion was right to flag this. In a normal supply shock, you'd expect bear steepening: long rates rise more than short rates because the market prices in higher long-run inflation. That IS happening in the absolute yield levels (10Y went from ~3.96% to 4.28%). But the spread is still compressing because the 2Y is rising too -- the Fed is boxed in.

The critical insight: **the spread compression is not "flight to safety" in the traditional sense.** It is the market pricing a policy trap. The Fed cannot cut (inflation at 3.1%), but the economy is stalling (0.7% GDP). The 2Y stays elevated because the market sees no rate cuts coming. The 10Y oscillates because growth fears and inflation fears are pulling it in opposite directions.

### Historical Analogs

**1973-74 Oil Embargo:** The yield curve initially steepened as inflation surged, then flattened as the recession deepened and the market realized the Fed would have to keep rates high despite economic contraction. The recession lasted from November 1973 to March 1975. The yield curve compressed during the transition from "inflation shock" to "recognized stagflation."

**1979-80 Volcker Shock:** Technically not a supply shock analog, but the curve inverted dramatically as the Fed held rates high through a recession. The policy trap dynamic is similar -- the Fed chose inflation-fighting over growth support.

**1990 Oil Shock (Iraq/Kuwait):** Oil doubled from ~$17 to ~$36. The yield curve flattened as the recession began (July 1990). But crucially, this was a much smaller shock than the current one, and the Fed was able to cut quickly. The recession was mild (8 months).

**The closest analog to the current situation is 1973-74**, not 1990. The scale of the oil disruption (Strait of Hormuz = 20% of global supply), combined with a tariff surcharge creating additional cost-push pressure, combined with a Fed that cannot respond (3.1% Core PCE vs 2% target), mirrors the policy trap that defined the Great Stagflation.

### What Happens Next (Based on Historical Pattern)

In 1973-74, the sequence was:
1. Supply shock hits (oil embargo, Oct 1973)
2. Curve initially steepens on inflation panic
3. Curve then compresses as recession becomes undeniable
4. Curve eventually inverts as the Fed is forced to keep rates high through recession
5. Deep recession follows (GDP fell ~3%)

**We appear to be at stage 3.** The spread compression from 0.74 to 0.52 is the market transitioning from "this is an inflation shock" to "this is stagflation." If the pattern holds, continued compression or inversion would follow, signaling the market has fully priced in recession despite elevated inflation.

### Verdict for the SD #5 Draft

This is a powerful featured finding. The framing:

**"The yield curve is telling us something the headline numbers haven't caught up to yet."** While unemployment is still below Sahm-trigger levels and GDP is technically positive at 0.7%, the bond market is pricing in the policy trap: the Fed cannot cut into a supply shock, but the economy is decelerating toward stall speed. The 22bp compression in 5 weeks is the market's real-time probability assessment that this ends in recession -- not because demand collapsed, but because the policy response is paralyzed by simultaneous inflation and growth deterioration.

The T10Y2Y spread at 0.52 and compressing should be read as: **"The bond market gives roughly even odds that the Fed is trapped."**

---

## Sources

- [FRED: Real-time Sahm Rule Recession Indicator](https://fred.stlouisfed.org/series/SAHMREALTIME)
- [Trading Economics: Sahm Rule 2026 Data](https://tradingeconomics.com/united-states/sahm-rule-recession-indicator-fed-data.html)
- [Motley Fool: Sahm Rule Signal Feb 2026](https://www.fool.com/investing/2026/02/21/this-signal-coincided-with-recession-past-65-years/)
- [FinancialContent: Treasury Yields 4.28% War Premium](https://markets.financialcontent.com/stocks/article/marketminute-2026-3-13-bond-market-shock-10-year-treasury-yield-surges-to-428-as-war-premium-rattles-global-finance)
- [FinancialContent: Stagflation Riddle -- GDP 0.7%, Core PCE 3.1%](https://markets.financialcontent.com/stocks/article/marketminute-2026-3-16-the-stagflation-riddle-us-gdp-growth-slumps-to-07-as-core-pce-hits-31)
- [FinancialContent: 5% Threshold -- Oil Shock and Policy Trap](https://markets.financialcontent.com/stocks/article/marketminute-2026-3-12-the-5-threshold-treasury-yields-surge-as-oil-shock-and-policy-trap-rattles-wall-street)
- [CNBC: 10-Year Yields Rise After Tariff Ruling](https://www.cnbc.com/amp/2026/02/20/us-treasury-yields-key-inflation-data-release.html)
- [Mariemont Capital: Treasury Yields Feb 2026](https://mariemontcapital.com/treasury-yields-february-2026-10-year-below-4/)
- [Real Investment Advice: Treasury Yields Don't Lie](https://realinvestmentadvice.com/resources/blog/treasury-yields-dont-lie-but-wars-dont-drive-them/)
- [FinancialContent: Flight to Safety Feb 23](https://markets.financialcontent.com/stocks/article/marketminute-2026-2-23-flight-to-safety-10-year-treasury-yields-drift-to-409-as-inflation-cools-and-geopolitical-tensions-rise)
- [FinancialContent: Safe-Haven Flight Yield Collapse](https://www.financialcontent.com/article/marketminute-2026-3-2-safe-haven-flight-triggers-yield-collapse-10-year-treasury-hits-395-amid-geopolitical-storm)
- [CEPR: How Tariff War Affected Safe Asset Privilege](https://cepr.org/voxeu/columns/how-tariff-war-shock-affected-safe-asset-privilege-us-treasuries)
- [Federal Reserve History: Oil Shock 1973-74](https://www.federalreservehistory.org/essays/oil-shock-of-1973-74)
- [FRED: T10Y2Y Series](https://fred.stlouisfed.org/series/T10Y2Y)
- [Fortune: Unemployment Rate Inching Closer to Sahm Rule](https://fortune.com/2025/12/19/sneaking-unemployment-rate-sahm-rule-recession-indicator-trigger/)
