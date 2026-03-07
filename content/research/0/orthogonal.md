# Legion Orthogonal Analysis: Signal Dispatch #0 -- Iran
## Analyzed: 2026-03-06

---

### 1. PATTERN DETECTION

**1a. OONI Hourly Data -- Missed Micro-Patterns**

- **The transition is NOT clean at 08:00 UTC Feb 28.** Data shows gradual degradation: at 07:00 UTC, measurement_count already down to 214 (from 468 at 06:00, 898 at 05:00). Confirmed_count was 71 at 07:00, collapsed to 10 at 08:00, then zero by 10:00. The 09:00 hour is missing entirely. Shutdown took approximately 2-3 hours to complete (05:00-08:00 degradation, 08:00-10:00 collapse). This suggests staged infrastructure shutdown (backbone by backbone) rather than a single kill switch -- multiple ISPs taken down sequentially, not a NIC-level cut.

- **Anomaly spike at 22:00 UTC March 3.** Most post-shutdown hours show anomaly_counts of 0-6 against measurement_counts of ~100. At 22:00 UTC March 3, anomaly_count jumps to 32 with measurement_count of 200 -- a 6x anomaly spike against post-shutdown baseline. Not flagged in synthesis. Possible interpretations: brief partial restoration attempt, OONI probes reaching targets during a connectivity test, or military/government traffic temporarily allowing broader routing. At 22:00 UTC = 01:30 local Tehran time -- unusual for deliberate policy action but consistent with infrastructure testing.

- **Measurement count shows DEGRADATION TREND.** Liara describes "exactly 100 per hour" post-shutdown. Actual data: 28, 25, 20 (Feb 28), 97-100 (Mar 1), 119, 181, 200 (Mar 2), 200 (Mar 3), 51, 49, 16, 84 (Mar 4), 67, 33, 97, 3, 1, 6, 10 (Mar 5). **March 5 shows the worst measurement capability in the entire dataset.** Counts of 3 and 1 suggest near-zero connectivity, worse than the immediate aftermath. Connectivity is getting WORSE over time, not stabilizing. Could indicate cumulative infrastructure damage from ongoing strikes, not just maintained shutdown.

- **Pre-shutdown anomaly spike Feb 27 07:00-08:00 UTC.** Anomaly_counts of 178 and 183 against measurements of 924 and 1085 (19.3% and 16.9% rates). Highest anomaly rates in pre-shutdown data. One day BEFORE strikes began. Was the regime pre-positioning censorship infrastructure? Increased surveillance?

**1b. Bonbast -- Not Real Market Data**

- Bonbast is likely NOT reporting real in-country transactions. The rate of 1,319,072 IRR/USD is derived from a full forex cross-rate table with 170+ currencies, all with precise decimals. This is NOT a black market transaction report -- it is a derived rate from international forex markets applied to the last known IRR exchange level. The actual Sarrafi (exchange shop) market is almost certainly not functioning during internet shutdown and active war. **Correct interpretation: no data exists on actual in-country exchange rate.** Treating Bonbast as evidence of "relative stability" vs. "freefall" is an analytical error.

**1c. OFAC -- Alternative Interpretations**

- Zero additions during active war has an alternative Liara missed: OFAC designations require intelligence on specific entities. During kinetic operations, intelligence community is consumed by targeting, not designations (bandwidth constraint, not policy choice). Also: adding designations would signal long-term economic pressure plans, contradicting any diplomatic off-ramp the US might want to preserve. Absence of designations could be strategically deliberate. The Feb 27 Oman "breakthrough" proves diplomatic tracks CAN be active while OFAC shows nothing.

**1d. USAspending -- Overinterpretation**

- **$40.7M Booz Allen Hamilton contract is 79% of total and started September 2022.** Headline "$51M total" is dominated by a four-year-old IT consulting contract. Actual Iran-relevant spending: ~$10.6M.
- **Tel Aviv Hilton contracts ($59,928 total) are routine embassy support.** US Embassy in Tel Aviv has permanent staff. Three hotel bookings over three months is unremarkable diplomatic operations, not "coordination activity."
- **Azerbaijan language services ($24,938) is thin evidence.** US maintains diplomatic operations in Baku unrelated to Iran. Inference of "intelligence support" is speculative.

**1e. Prediction Markets -- Signal Poverty**

- Kalshi coverage is 85% tennis and K-pop. Only 3 Iran-related results of 20. Pipeline market signal is near-zero.
- Polymarket data (51% regime change, $500M volume) comes from web research, not structured pipeline. Different evidence class, should be flagged as such.

**1f. Absence of Expected Signals**

- No EIA petroleum data collected -- biggest gap given Hormuz closure
- No Congressional action data (AUMFs, supplemental appropriations, War Powers notifications)
- No CENTCOM procurement spike visible (may be in classified channels)

---

### 2. CONTRARIAN SYNTHESIS

**Thesis: The Islamic Republic is more likely to survive than Liara's 45-55% estimate suggests. Air campaigns alone have never achieved regime change in modern history.**

**Argument 1: Rally-round-the-flag effect.** Every modern case of external military attack on authoritarian regime shows initial domestic consolidation. Iraq survived Desert Storm (1991). Serbia survived 78 days of NATO bombing (1999). Iran itself survived 8 years of war with Iraq (1980-88). December 2025 protests were economic grievances; US strikes reframed the narrative from "regime failing us" to "foreign attack." This is the most robust finding in political science research on rally effects.

**Argument 2: Khamenei martyrdom strengthens regime.** Martyrdom is the foundational legitimacy narrative of the Islamic Republic. Khamenei dying in a foreign strike creates a martyrdom narrative more powerful than any living leader could generate. The IRGC does not depend on a single leader. Historical references: Sadat assassination (1981) did not collapse Egypt. Gandhi assassination (1984) did not collapse India. External assassination with clear attacker typically consolidates surviving institutions.

**Argument 3: Internet shutdown demonstrates regime STRENGTH.** A regime that can sustain a 6+ day internet shutdown across 85 million people is demonstrating formidable coercive capacity. Requires functioning IRGC command chains, telecom cooperation, operational control of backbone routers. A regime in collapse does not execute coordinated national infrastructure shutdowns.

**Argument 4: No valid reference class for regime change via air campaign alone.** Iraq 2003 = ground invasion. Libya 2011 = internal revolution + NATO air. Syria = civil war. Afghanistan 2001 = ground forces + Northern Alliance. Air campaigns alone: 0 cases of regime change in modern history. Kosovo 1999 is closest -- Milosevic survived bombing, fell 15 months later through domestic politics.

**Argument 5: No organized opposition to replace the regime.** MEK (despised domestically), monarchists (limited base), reformists (within system), ethnic separatists (localized), student movements (no organizational structure). Unlike Libya (NTC), Syria (SNC), Afghanistan (Northern Alliance), no organized force exists to step into a vacuum. The IRGC is the only organized national institution.

**Argument 6: China and Russia interests entirely absent from Liara's analysis.** China purchases most Iranian oil exports, $400B+ Belt and Road investments. Russia relies on Iran as key Middle East partner. Both have UNSC vetoes, economic tools, military equipment to support the regime.

**Argument 7: 46-year survival track record.** Iran-Iraq War (1980-88), 2009 Green Movement, 2017-18 protests, 2019 protests (1,500+ killed), 2022 Mahsa Amini protests, continuous sanctions since 1979.

**Weakest assumptions in Liara's analysis:**
1. Assumes convergence of crises is additive. But external attack dampens internal protest through rally effect -- partially canceling.
2. 45-55% may reflect anchoring on dramatic events rather than base rates.
3. Underweights institutional resilience.

**What would invalidate crisis-escalation thesis:**
- Ceasefire within 30 days
- IRGC demonstrating continued chain of command (naming new Supreme Leader)
- China/Russia security guarantees
- Protest decline under rally effect
- Partial internet restoration (regime confidence)

---

### 3. PROBABILITY CALIBRATION CHECK

**Reference Class Analysis:**

| Case | Attack Type | Leader Killed | Regime Change? | Timeline |
|------|-----------|---------------|----------------|----------|
| Iraq 2003 | Ground invasion + air | No (initially) | Yes | 3 weeks (ground forces) |
| Libya 2011 | Internal revolt + NATO air | Yes (Oct 2011) | Yes | 8 months |
| Syria 2011 | Civil war | No | No (survived) | 15+ years |
| Afghanistan 2001 | Air + ground | No (Taliban survived) | Yes | 2 months |
| Serbia 1999 | Air only | No | No (survived bombing) | Fell 15mo later, politically |
| Iran 1980-88 | Ground invasion | No | No | Survived 8 years |

**Base rate for air-campaign-only:** 0% regime change historically.

**Calibration Results:**

| Question | Liara Estimate | Legion Calibration | Direction |
|----------|---------------|-------------------|-----------|
| Regime change 12mo | 45-55% | 30-45% | Lower. Air-only base rates don't support 50%+ |
| Hormuz closed Q2 | High (implied) | 65-75% | Moderate. Linked to ceasefire timing |
| Ceasefire timing | Not before late Q2 | 40-60% before end Q2 | Earlier window. Historical median 5-10 weeks |
| Nuclear deal April | 9.5% (Kalshi) | 2-5% | Lower. Active war = effectively zero |

**Core Calibration Concern:** The narrative is doing more work than the numbers. An outside-view assessment from raw signals alone would produce lower probability estimates. The conjunction of dramatic events (assassination + bombing + shutdown + collapse) feels like it should produce regime change, but feeling is not base rate. The structured data shows: sustained repressive capability, ambiguous economic signals, static external pressure tools, thin market coverage. Data supports "regime under extreme stress" but not necessarily "regime at 50/50 for collapse."

**Conjunction fallacy risk:** Base rate for regime change in any given year for an authoritarian state: ~2-3%. Even multiplying by extreme stress factors, reaching 50% requires strong evidence that THIS convergence is categorically different from all prior survival cases. Evidence is real (assassination is unprecedented) but insufficient for coin-flip estimate.

---

**Summary of Problems Found:**

1. OONI degradation trend (March 5 worse than March 1-2) -- possible ongoing infrastructure destruction
2. March 3 22:00 UTC anomaly spike uninvestigated
3. Bonbast is likely interpolated/derived, not real in-country transactions
4. USAspending $51M inflated by 2022 contract; actual ~$10.6M
5. Tel Aviv Hilton and Azerbaijan contracts overinterpreted
6. OFAC zero-change has diplomatic-optionality interpretation
7. Prediction market pipeline data nearly useless for Iran
8. Regime change probability should be 30-45%, not 45-55%
9. Narrative driving numbers more than data
10. Missing data (EIA, Cloudflare, TEDPIX, Congressional, CENTCOM) creates observation bias
