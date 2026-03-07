# Cross-Track Intelligence Synthesis: Signal Dispatch #0 -- Iran
## Synthesized: 2026-03-06

---

### Signal-by-Signal Interpretation

**1. OONI -- Iran Internet Connectivity**

*Raw data:* 102 hourly measurements spanning Feb 27 to Mar 5. On Feb 27 (the day before strikes began), Iran showed its normal elevated censorship baseline: anomaly rates of 10-20% with confirmed blockings consistently in the 100-270 range per hour across 400-1000+ measurements. Peak confirmed blocks hit 293 at 01:00 UTC on Feb 28. Then, starting around 08:00 UTC on Feb 28, the data structure breaks. Confirmed blocks drop to **zero** and never recover across the entire remaining dataset (Mar 1-5). Simultaneously, measurement counts collapse from 500-1000+ per hour down to exactly 100 per hour (the OONI minimum sampling floor), with many hours missing entirely.

*Interpretation:* This is not censorship relaxation -- it is the signature of a near-total connectivity collapse. When confirmed_count drops to zero while measurement_count drops to minimum thresholds, it means OONI probes can barely reach Iran at all. You cannot "confirm" a block if you cannot complete the measurement. The Feb 27-28 transition from high-measurement/high-confirmation to low-measurement/zero-confirmation is the OONI fingerprint of a full internet shutdown. The framework defines sustained anomaly rates above 15% for 3+ days as systematic suppression, but what we are seeing is worse: **measurement dropout**, identified as the strongest possible signal.

*Magnitude:* Extreme. ~85-90% reduction in measurement capability. The January 8, 2026 shutdown used a sophisticated IPv6-withdrawal technique. The Feb 28 shutdown appears even more severe.

*Duration:* Sustained 6+ days (Feb 28 through Mar 5 at minimum). No partial restoration pattern as seen after January 18.

*Direction:* **Regime is maintaining wartime information blackout.** Dual purposes: (1) denying OSINT to US/Israeli targeting operations, (2) suppressing domestic information flow about strike damage and leadership losses. The regime retains operational control of telecommunications infrastructure.

**Confidence: HIGH.** Data is unambiguous.

---

**2. Bonbast -- Iranian Rial Black Market Rate**

*Raw data:* USD rate of 1,319,072 IRR/USD. EUR rate of 1,532,505 IRR/EUR. Timestamp: Mar 6, 2026.

*Baseline:* Record low of 1,750,000/USD in December 2025. Current reading represents ~25% appreciation from the worst point. Still catastrophically weak -- ~96% depreciation from pre-sanctions levels, ~77% from early 2023.

*Interpretation:* Counterintuitive. The rial has NOT crashed further despite active war, leadership assassination, and sustained internet shutdown. Possible explanations: (a) parallel market not functioning normally due to internet shutdown (Bonbast may have stale/limited data), (b) regime burning foreign reserves, (c) December 2025 low already priced in worst-case, (d) market dysfunction during connectivity blackout.

*Direction:* **Ambiguous.** Economy has not experienced a second acute crash since war began, but data quality is suspect during connectivity blackout.

**Confidence: MEDIUM-LOW.** Reliability during internet shutdown is questionable.

---

**3. OFAC -- Sanctions List Snapshot**

*Raw data:* 2,140 Iran-related designated entities. Breakdown: 1,139 entities, 387 individuals, 547 vessels, 67 aircraft. Dominant program tags: IRAN (669), IRAN-EO13902 (604), IRAN-EO13846 (445), IRAN-HR (222). IRGC designations: 64. **Diff shows zero additions and zero removals.**

*Interpretation:* The US is conducting active military strikes yet the sanctions apparatus has not been updated. This is a ceiling effect: (1) military operation supersedes sanctions as pressure tool, (2) OFAC additions require legal review that may be delayed during kinetic operations, (3) existing architecture (2,140 entities including 547 vessels) is already near-maximal, (4) absence of removals confirms no diplomatic track active.

*Direction:* **Status quo on sanctions = ceiling effect, not inaction.** Policy velocity has shifted from sanctions to kinetic action.

**Confidence: HIGH.** Authoritative source.

---

**4. USAspending -- Federal Procurement Patterns**

*Raw data:* 12 awards totaling $51,346,471.57.

*Key contracts:*
- **Reveal Technology** ($9.5M via GSA, Dec 2025): AI/ML for defense/intelligence applications. Awarded 2 months before strikes = preparation signature.
- **Tel Aviv Hilton** (three State Dept awards totaling ~$60K, Nov 2025 - Jan 2026): Repeated diplomatic hotel bookings in Israel in months preceding joint strikes = sustained coordination activity.
- **Azerbaijan language services** ($25K, State Dept, Sep 2025): Language services in Iran's northern neighbor = possible diplomatic or intelligence support.
- **PAE Government Services** (DOJ, ~$624K): Operational support in austere environments.

*Direction:* **Pattern consistent with pre-planned military/intelligence operation.** Procurement trail shows AI/intelligence scaling (Dec 2025), sustained State Dept presence in Tel Aviv (Oct 2025 - Jan 2026), regional positioning (Azerbaijan). These are preparation signatures, not reactive wartime spending.

**Confidence: MEDIUM.** Contracts are real; Iran relevance is inferred from timing and vendor profiles.

---

**5. OSINT -- Federal Register**

*Raw data:* Six of seven queries returned empty. Single hit: DHS notice terminating Yemen TPS designation (Mar 3, 2026), effective May 4, 2026.

*Interpretation:* Yemen TPS termination tangentially relevant -- Houthis are a key Iranian proxy. Terminating during active US operations against Iran signals treating the Iran-proxy axis as a unified problem. Empty Iran results = executive branch has not published new Iran-specific regulatory actions. Consistent with kinetic action replacing regulatory action.

*Direction:* **Regulatory quiet on Iran. Peripheral actions consistent with broader Iran-axis pressure.**

**Confidence: MEDIUM.**

---

**6. TEDPIX -- Tehran Stock Exchange (FAILED)**

*Collection failure:* tsetmc.com unreachable. CLI attributes to "Iran internet shutdown."

*As signal:* The failure IS the data. Confirms OONI assessment of near-total connectivity collapse.

**Confidence: HIGH** (that internet is down). **N/A** (for what TEDPIX would show).

---

**7. Prediction Markets**

*Available:* US-Iran nuclear deal by April 2026: 9.5% (Kalshi, $413K volume). Polymarket (per web research, NOT in pipeline): 51% regime falls by end of 2026, 28% by March 31.

*Critical gap:* Kalshi coverage is thin. Polymarket is the real venue with $500M volume. Pipeline needs Polymarket integration.

**Confidence: LOW** due to incomplete venue coverage.

---

### Cross-Signal Convergence/Divergence

**Cluster 1 -- Regime Coercive Capacity (OONI + Cloudflare):** OONI shows deliberate shutdown. Cloudflare ambiguous (API error). Assessment: **regime is acting** -- retains capability and will to impose wartime information blackout. 6+ day sustained shutdown with no signs of lifting.

**Cluster 2 -- Economic Viability (Bonbast + TEDPIX):** Bonbast shows rial holding at crisis levels without further collapse. TEDPIX unavailable. Assessment: **incomplete, but no evidence of acute economic freefall beyond pre-war baseline.** Data quality suspect during shutdown.

**Cluster 3 -- External Pressure Trajectory (OFAC + USAspending):** OFAC zero change (ceiling effect). USAspending $51M with preparation signatures. Assessment: **maximum external pressure, shifted from sanctions to kinetic operations.**

**Cross-cluster convergence:** Cluster 1 (confirmed shutdown) + Cluster 2 (uncertain) + Cluster 3 (kinetic escalation beyond sanctions) = **maximum pressure** pattern with degraded economic data.

**Key convergence:** OONI collapse and TEDPIX failure point same direction -- internet severely disrupted. USAspending procurement and OFAC ceiling point same direction -- US policy has escalated beyond sanctions to military action.

**Key divergence:** Bonbast rate's relative stability diverges from expectations. Under active bombing + internet shutdown + leader assassination, we would expect currency freefall. Rate stability likely indicates market dysfunction rather than economic resilience.

**Temporal alignment:** OONI transition precisely at Feb 28 confirms internet shutdown is directly correlated with military operation, not protest cycle. USAspending procurement timeline (Dec 2025 forward) precedes strikes by 2-3 months = operational planning lead time.

---

### Net Directional Assessment

All structured signals converge: **Iran is under simultaneous external military assault and internal information blackout, with sanctions exposure at maximum levels and no diplomatic off-ramp visible.**

**On core questions:**

1. **Regime survival:** Extreme stress but not yet collapse. Regime retains infrastructure control (internet shutdown requires functioning IRGC command chains). Assassination and military infrastructure destruction are irreversible losses. Operating on institutional inertia and pre-issued orders. **45-55% probability of fundamental change within 12 months.**

2. **Strait of Hormuz:** Commercially closed via insurance mechanism. No ceasefire imminent. **Commercial closure sustained through at least Q2 2026.**

3. **Ceasefire:** Zero signals toward diplomatic resolution. Iran explicitly rejects negotiations. **No ceasefire before late Q2 2026 at earliest.**

**Baseline shift:** Before Feb 28, Iran was in "slow internal deterioration." Strikes fundamentally changed trajectory to "acute, multi-domain crisis."

---

### Evidence Quality Rating

| Source | Quality | Notes |
|--------|---------|-------|
| OONI | **HIGH** | Hourly measurements, clear transition, internally consistent |
| Bonbast | **MEDIUM-LOW** | Rate exists but reliability during shutdown questionable |
| TEDPIX | **N/A (failure = signal)** | Confirms shutdown independently |
| Cloudflare | **N/A (ambiguous)** | API config issue |
| OFAC | **HIGH** | Authoritative, clear diff |
| USAspending | **MEDIUM** | Contracts real, Iran relevance inferred |
| OSINT | **MEDIUM** | Yemen TPS tangential, empty Iran results informative |
| Markets | **LOW** | Kalshi thin, Polymarket is the venue |

**Overall: MEDIUM-HIGH.** OONI is excellent. OFAC is authoritative. Economic indicators degraded by the conditions they measure. Prediction market coverage has significant venue gap.

**Novelty edge:** The OONI transition pattern (confirmed blocks dropping to zero = measurement dropout, NOT censorship relaxation) requires domain expertise to interpret correctly. Naive reading would be a serious analytical error.

---

### Prediction Market Context

**Structured data vs. market prices:** Signals support Polymarket regime-collapse range (51%). The 9.5% nuclear deal probability on Kalshi is correctly priced given active war and explicit negotiation rejection.

**Potential mispricings:** Largest in Strait of Hormuz/energy markets, not well represented on prediction platforms but directly measurable through Ghost Market signals.

**Pipeline gap:** Needs Polymarket integration. Kalshi's Iran coverage is thin and low-volume. $500M Polymarket volume is where market intelligence lives.

---

### Open Questions

1. **EIA data not collected.** US petroleum inventory/SPR data would illuminate Hormuz closure impact on energy markets.
2. **Cloudflare Radar API needs diagnosis.** Config issue or API change?
3. **Bonbast reliability during shutdown.** Does Bonbast rely on in-country transaction reporting that would be disrupted?
4. **TEDPIX -- is the exchange operating domestically?** Trading suspended or merely externally unreachable?
5. **Polymarket integration.** Single highest-value pipeline improvement.
6. **OFAC: watch for post-strike designation waves.** Zero-change may reflect processing lag.
7. **Internal regime information environment.** State media (IRIB) controls domestic narrative. No structured signal for regime messaging.
8. **Polymarket insider trading.** $1M+ profits from six pre-positioned accounts on US military action contracts. Prediction market order flow as intelligence source.
