# Signal Interpretation Framework: Iran Deep Dive -- SD #0

## Individual Source Frameworks

### OONI (Iran Internet Connectivity)

OONI measures application-layer internet censorship through volunteer-run measurement probes. For Iran, this captures DNS injection, HTTP blocking, and protocol-level interference on networks like MCI and IranCell. In the current context, OONI is a **primary indicator of regime coercive capacity and intent.** The January 8, 2026 shutdown -- the most severe in Iran's history -- demonstrated a new technical sophistication: IPv6 routes withdrawn while IPv4 routes remained "up" but traffic was blocked (a "stealth outage"). Baseline for Iran: anomaly rate of 7-12% is normal operating noise. The January shutdown drove this effectively to near-100% for over a week. Signal thresholds: anomaly rate sustained above 15% for 3+ consecutive days indicates systematic suppression. Complete measurement dropout is the strongest signal -- it means the regime has shut down external connectivity entirely. In wartime context, sustained shutdown also serves a military purpose (denying OSINT to adversaries), so distinguish C2-motivated shutdowns from protest-suppression shutdowns by cross-referencing with protest reporting and Cloudflare data.

### Bonbast (Iranian Rial Black Market Rate)

Bonbast tracks the unofficial/parallel market exchange rate for the Iranian rial against major currencies, particularly USD. This rate reflects real economic sentiment among Iranian citizens and businesses because the official exchange rate is artificially maintained by the Central Bank. The rial is a **composite indicator of capital flight, economic confidence, and sanctions bite.** The rial hit a record low of 1,750,000/USD in December 2025. Current rates around 1,315,000-1,666,000/USD suggest some stabilization but remain historically extreme. Signal vs noise: daily movements under 2% are normal volatility. A 5%+ single-day drop signals acute crisis. A bid-ask spread exceeding 5% signals illiquidity and panic. Critical convergence: when Bonbast rial drops simultaneously with TEDPIX, capital is fleeing the country entirely. In wartime, the question shifts from "is the economy deteriorating?" to "is the regime losing the ability to maintain even the parallel market?"

### TEDPIX (Tehran Stock Exchange)

TEDPIX is the composite index of the Tehran Stock Exchange, serving as a proxy for Iranian elite economic sentiment. Unlike the rial, TEDPIX reflects decisions by wealthier, more connected Iranians -- IRGC-linked businesses, bazaar merchants, educated middle class. TEDPIX is a **leading indicator of elite confidence.** Daily moves exceeding 3% warrant attention; moves above 5% indicate major sentiment shift; above 10% signals panic liquidation or euphoria. Critical pattern: 5+ consecutive down days combined with volume spikes indicates sustained institutional selling. Most actionable convergence: TEDPIX crash + rial crash + OONI shutdown = regime simultaneously losing elite confidence, popular confidence, and resorting to coercive information control. In wartime, interpret TEDPIX direction relative to conflict events: if TEDPIX drops after Iranian retaliatory strikes, domestic actors believe the regime's military response is damaging to their interests.

**NOTE:** TEDPIX data collection FAILED for SD #0 -- tsetmc.com (Tehran Stock Exchange website) unreachable. CLI reports "Site may be unreachable due to Iran internet shutdown." This is itself a signal confirming sustained internet disruption.

### Cloudflare Radar (Traffic Anomalies)

Cloudflare Radar provides network-layer traffic data from Cloudflare's global edge network, capturing BGP routing anomalies, traffic volume changes, and internet outages at the infrastructure level. While OONI measures censorship (what the regime blocks), Cloudflare measures connectivity (whether the infrastructure is functioning). These are complementary. **Convergence of both signals is the strongest indicator of deliberate state action versus technical failure.** OONI anomalies without Cloudflare disruption = targeted content blocking. Cloudflare outages without OONI anomalies = infrastructure failure. Both simultaneously = coordinated regime shutdown. In the current conflict, Cloudflare Radar also captures the impact of military strikes on telecommunications infrastructure.

**NOTE:** Cloudflare Radar API returned HTTP 400 for SD #0. API configuration issue, not necessarily a signal.

### OFAC (Sanctions List Changes)

OFAC publishes the Specially Designated Nationals (SDN) list, the primary instrument of US financial sanctions. OFAC is a **policy velocity indicator.** Baseline: 5-10 additions per month is maintenance-level enforcement. More than 10 per month signals escalation. Any removals are diplomatically significant (extremely rare). Watch for three patterns: (1) vessel sanctions targeting Iranian oil exports and the China evasion channel; (2) IRGC-linked designations targeting military apparatus, signaling regime-change intent; (3) secondary sanctions on Chinese/Russian entities indicating willingness to escalate with Iran's remaining trade partners. OFAC designation list serves as a leading indicator for Federal Register publication.

### USAspending (Federal Procurement Patterns)

USAspending tracks all federal contract awards, revealing government spending priorities through procurement patterns. For Iran analysis, this captures **military readiness, diplomatic infrastructure, and intelligence activity.** Key keyword clusters: "CENTCOM" + "Iran" for military operations; "mine countermeasure" or "Strait of Hormuz" for naval readiness; "Iran" + "democracy" for regime-change support funding; "sanctions compliance" for enforcement scaling. Signal thresholds: total Iran-related obligations exceeding $10M in 90 days = elevated; above $50M = major initiative; above $100M = operation-level. Watch for small contracts ($500K and under) -- fast-track procurements for immediate operational needs. Agency patterns: DOD = kinetic capability; State Dept = diplomatic/post-conflict planning; Treasury = sanctions enforcement. A surge in State Department "transition" or "governance" contracts would signal US planning for post-Islamic Republic Iran.

## Convergence Logic

**Cluster 1: Regime Coercive Capacity** (OONI + Cloudflare)
- Both elevated = deliberate shutdown, regime is acting
- OONI only = targeted content blocking, regime is managing
- Cloudflare only = infrastructure failure (possibly kinetic strikes on telecom)
- Neither = internet functioning, regime not in crisis mode OR has lost capacity

**Cluster 2: Economic Viability** (Bonbast + TEDPIX)
- Both dropping = capital flight, elite and popular panic (strongest signal)
- Rial down / TEDPIX up = capital rotating domestically, not fleeing (moderate)
- Rial stable / TEDPIX dropping = equity-specific risk (moderate)
- Both stable = economy functioning within current constraints (baseline)

**Cluster 3: External Pressure Trajectory** (OFAC + USAspending)
- OFAC additions + DOD contract surge = escalation
- OFAC additions + State Dept contract surge = regime change planning
- OFAC removals + any = de-escalation / diplomatic progress
- Neither moving = policy status quo

**Cross-cluster convergence (highest confidence signals):**
- Cluster 1 (shutdown) + Cluster 2 (capital flight) + Cluster 3 (escalation) = regime under maximum pressure, highest probability of fundamental change
- Cluster 1 (quiet) + Cluster 2 (stabilizing) + Cluster 3 (de-escalation) = crisis receding, regime adaptation succeeding
- Cluster 1 (shutdown) + Cluster 2 (stable) + Cluster 3 (escalation) = regime maintaining control despite external pressure (rally-round-flag)
- Cluster 1 (quiet) + Cluster 2 (collapsing) + Cluster 3 (status quo) = internal economic crisis without external catalyst (organic instability)
