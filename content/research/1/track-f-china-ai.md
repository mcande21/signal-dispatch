# Track F: China's AI Infrastructure and Semiconductor Ambitions

**Research Date:** 2026-03-06
**Analyst:** Liara T'Soni
**Classification:** OSINT Synthesis
**Confidence:** High (multi-source corroboration across government reports, industry analysis, and investigative journalism)

---

## Executive Summary

China is executing a state-directed, multi-vector campaign to build sovereign AI infrastructure while remaining critically dependent on Taiwan-manufactured advanced semiconductors. The gap between Chinese and American AI chip capability is widening, not narrowing -- Huawei produces roughly 5% of Nvidia's aggregate AI computing power and is projected to fall to 2% by 2027. China's response is threefold: massive state investment ($47.5B Big Fund III alone), an efficiency-first AI development strategy (DeepSeek), and systematic sanctions evasion including chip smuggling networks worth hundreds of millions. Taiwan's "silicon shield" is eroding from both sides -- TSMC's US expansion dilutes the deterrent while China's gray zone military escalation normalizes encirclement. The semiconductor chokepoint is not just a Taiwan question; it is the central variable in the global AI race.

---

## 1. China's AI Infrastructure Spending

### Scale of Investment

China's AI capital expenditure is massive but still dwarfed by the US. Key figures:

- **Total 2025 AI capex:** Estimated at up to $98 billion, with government contributing ~$56 billion through various funds and internet companies projected at ~$24 billion (Goldman Sachs).
- **2026 projection:** Top Chinese internet firms expected to invest over $70 billion in AI infrastructure.
- **Big Fund III:** $47.5 billion (344 billion yuan) state-backed semiconductor investment vehicle, launched December 2024. Unlike previous phases focused on fab construction, Big Fund III targets supply chain bottlenecks -- lithography tools, EDA software, photoresists, specialty gases, wafer materials.
- **National target:** 105 EFLOPS of AI computing power by 2025, with a network of 250+ AI data centers.

### Private Sector Commitments

| Company | Investment | Timeline | Focus |
|---------|-----------|----------|-------|
| Alibaba | $50B+ | 3-year plan | Cloud computing, AI hardware infrastructure |
| ByteDance | ~$20B | Ongoing | GPUs, data centers |
| Baidu | Multi-billion | Ongoing | AI infrastructure, Kunlun chips |
| Tencent | Multi-billion | Ongoing | AI compute, Enflame chip deployment |

### US Comparison

China's planned AI infrastructure investment represents only 15-20% of what US hyperscalers are expected to spend. The 2026 global AI capex sprint is estimated at $690 billion, heavily concentrated in US firms. This spending gap is the most underappreciated asymmetry in the AI race.

### Military-Civil Fusion Dimension

The Strider/SCSP report (May 2025) identified 856 organizations involved in China's AI data center buildout. Of these, 88 have documented ties to the PLA, China's defense industrial complex, or US-sanctioned entities. More than half of identified AI data centers are already operational, with the number doubling from 2023 to 2024. PLA-linked data centers rely heavily on US and allied software tools, highlighting a gap in current export control regimes that focus on hardware.

---

## 2. Semiconductor Self-Sufficiency Progress

### SMIC: The Frontline

SMIC is China's most advanced foundry and the critical node in the self-sufficiency campaign.

**Current capability:**
- 7nm process: In mass production. Yields described as "good" and "stable." Capacity reportedly around 30,000 wafers per month, with plans to double in 2026.
- 5nm process: Pilot test line with yields below 20%. Huawei and SMIC reportedly achieved a 5nm breakthrough in May 2025 using multi-patterning DUV techniques, but production-scale yields are estimated at roughly one-third of TSMC's for the same node.
- Process technique: Self-Aligned Quadruple Patterning (SAQP) and potentially Self-Aligned Octuple Patterning (SAOP) using DUV lithography to approximate features that normally require EUV. Costs are significantly higher and yields lower, but results are "good enough" for many AI and 5G workloads.

**The EUV wall:** Without access to ASML's EUV lithography systems (blocked by US/Dutch export controls), SMIC cannot efficiently produce chips below 7nm at scale. DUV multi-patterning is a workaround, not a solution -- it increases cost per wafer by an estimated 50% versus EUV-based production.

**Domestic lithography:** In September 2025, SMIC began testing a DUV lithography system from Shanghai Yuliangsheng, signaling progress toward reducing dependence on ASML. China has reportedly reached 35% semiconductor equipment self-sufficiency as of early 2026, up from approximately 20% in 2025.

### Huawei Ascend: The Performance Gap

Huawei's Ascend AI chip family is China's flagship domestic alternative to Nvidia.

| Chip | Process | Performance | vs. Nvidia |
|------|---------|-------------|------------|
| Ascend 910C | SMIC 7nm | ~320 TFLOPS FP16 | ~60% of H100 inference |
| Ascend 920 | SMIC 6nm | ~900 TFLOPS (projected) | 30-40% improvement over 910C |
| Ascend 950 | Expected Q1 2026 | 1 PFLOP FP8 target | Targeting H100-class |

**System-level performance:** Huawei's CloudMatrix 384 system reportedly delivers 300 PFLOPs of dense BF16 compute -- nearly double Nvidia's GB200 NVL72 -- with 3.6x aggregate memory capacity. This suggests China is compensating for per-chip disadvantages with system architecture innovation.

**The widening gap (CFR analysis, December 2025):**
- Huawei produces ~5% of Nvidia's aggregate AI computing power (2025)
- Projected to fall to 4% in 2026 and 2% in 2027
- By 2H 2027, Nvidia's best chips expected to be ~17x more powerful than Huawei's best
- Even a hundredfold increase in Huawei production would not reach half of Nvidia's output by 2027
- Huawei's own public roadmap shows its next-gen 2026 chip will actually be less powerful than its current best

**Huawei founder Ren Zhengfei acknowledged in June 2025 that the company's chips remained a generation behind US processors.**

### Broader Domestic Ecosystem

Beyond Huawei, China's domestic AI chip ecosystem is expanding rapidly:

- **Alibaba T-head (Zhenwu PPU):** Several hundred thousand units shipped, powering 10,000+ chip clusters within Alibaba Cloud. Reportedly on par with Nvidia H20 (the export-compliant chip).
- **Cambricon Technologies:** Revenue surged 43x to $404 million in H1 2025 after a major ByteDance order.
- **Moore Threads, Iluvatar CoreX, Enflame:** Accumulated shipments surpassing 10,000 chips each by late 2025. Enflame backed by Tencent.
- **Baidu Kunlun:** Used by ByteDance for testing and deployment.

### Self-Sufficiency Rate

China's overall semiconductor self-sufficiency rate has risen from 15% in 2019 to approximately 25% in 2025. Domestic chips are projected to power 30-40% of China's AI compute by 2026, up from less than 10% in 2024. For advanced AI-grade chips specifically, the self-sufficiency rate remains much lower.

---

## 3. TSMC Dependency

### The Numbers

TSMC's dominance in advanced semiconductor manufacturing is absolute:

- **Global foundry market share:** 71-72% (Q3 2025, TrendForce)
- **Advanced AI chips:** Upper-90% range of all advanced AI chip fabrication
- **Taiwan overall:** 60% of world's semiconductors, 90% of the most advanced semiconductors
- **Advanced capacity:** 92% of manufacturing capacity for the most advanced chips globally

### China's Specific Dependency

China's AI buildout remains heavily dependent on TSMC-fabricated chips, both directly and indirectly:

- **Direct:** Chinese firms design AI chips (often through intermediaries) that are fabricated at TSMC. The Enflame case (NBC News, 2025) revealed TSMC-manufactured components in a Chinese AI chip, highlighting enforcement challenges.
- **Indirect:** Nvidia, AMD, and other firms that sell to China (or whose chips are diverted to China) all manufacture at TSMC.
- **Huawei shell company scheme:** Huawei reportedly used shell companies to trick TSMC into manufacturing approximately 2 million chiplets for Ascend 910 processors.

### Disruption Scenarios

**If TSMC were disrupted (conflict, sanctions, natural disaster):**

For China:
- Immediate loss of access to the most advanced chips for AI training and inference
- Domestic alternatives (SMIC) cannot substitute -- 7nm DUV multi-patterning cannot match TSMC's 3nm/2nm EUV processes in performance, power efficiency, or cost
- AI ambitions would be set back years, possibly a decade for frontier models
- Existing stockpiles would deplete within months

For everyone else:
- Global AI chip shortage would persist until at least 2028-2029
- TSMC Arizona (4nm operational, 3nm targeted 2027, 2nm late decade) provides partial backup but at fraction of Taiwan capacity
- Samsung and Intel foundries lack the advanced packaging (CoWoS) expertise
- AI development timelines for frontier models would extend significantly
- Hundreds of billions in digital transformation projects delayed

**TSMC has warned key customers (Nvidia, Broadcom) that capacity at its most advanced nodes is already increasingly constrained.** AI chip shortages are projected to persist through 2026 even without disruption.

---

## 4. Stockpiling and Workarounds

### Chip Stockpile Estimates

- **Pre-controls inventory:** China accumulated significant GPU inventory before the October 2023 export control tightening. Exact figures are classified, but industry estimates suggest tens of thousands of A100/H100-class chips.
- **Current banned chips in China:** US officials estimate approximately 25,000 banned chips currently in country, far short of the 115,000+ needed for major data center projects.
- **Huawei component stockpile:** CSIS estimated Huawei may have had enough stockpiled components to manufacture 750,000 to 1 million Ascend 910C chips.
- **Depletion timeline:** Chinese tech giants' Nvidia GPU supplies expected to run dry by early 2026, forcing accelerated transition to domestic alternatives.

### Smuggling and Evasion

**Operation Gatekeeper (December 2025):** DOJ dismantled a sophisticated, multi-jurisdictional smuggling network that moved at least $160 million worth of restricted Nvidia AI chips to China using straw purchasers, domestic warehouses, and deliberate rebranding (workers systematically opened shipments and relabelled Nvidia chips with fake company names).

**Additional evasion strategies documented:**
- **Third-country data centers:** Chinese companies accessing banned chips through large data centers in Malaysia, Singapore, and other nearby countries that have seen import surges.
- **Shell company procurement:** Multiple layers of intermediary companies to obscure end-user identity.
- **Mexico routing:** Reports of chip routing through Mexican intermediaries.
- **Used chip market:** Speculation about targeting used chips circulating globally through unofficial channels.
- **TSMC circumvention:** Huawei used shell companies to have TSMC unknowingly manufacture Ascend chiplets.

### Export Control Effectiveness: Mixed Assessment

**Where controls are working:**
- SMIC stuck at 7nm; rumored 5nm breakthroughs have not materialized at production scale
- Chipmaking technology has demonstrably stalled relative to the frontier
- DeepSeek had to restrict API access after R1 launch, presumably due to insufficient inference compute

**Where controls are failing:**
- Smuggling networks continue to operate despite enforcement
- Third-country routing creates enforcement gaps
- Software and algorithm restrictions lag hardware controls
- PLA-linked data centers still rely on US/allied software tools
- Trump administration partially reversed course, considering H200 sales to China

**Policy whiplash:** The Trump administration suspended the BIS "Affiliates Rule" for one year (until November 2026) following a bilateral meeting with Xi Jinping in October 2025. This creates a window of reduced enforcement pressure.

---

## 5. DeepSeek and the Efficiency Strategy

### The DeepSeek Shock

DeepSeek demonstrated that compute constraints do not necessarily prevent competitive AI development:

- **DeepSeek R1 (January 2025):** Achieved reasoning performance competitive with OpenAI's o1 at a reported training cost of ~$5.6 million, versus estimated $100M+ for GPT-4 class models.
- **DeepSeek V3:** 671 billion parameter model using Mixture-of-Experts (MoE) architecture, activating only 37 billion parameters per token -- drastically reducing inference costs.
- **DeepSeek V4 (expected March 2026):** Trillion-parameter multimodal system (text, images, video) with only 32 billion active parameters per token. Projected inference costs of $0.10-$0.30 per million input tokens -- up to 50x cheaper than GPT-5.

### Architectural Innovation

DeepSeek's January 2026 paper introduced Manifold-Constrained Hyper-Connections (mHC), a fundamental rethink of training architecture designed to make models more cost-effective. This is not incremental optimization -- it represents a philosophical divergence from the US "scale compute" approach.

### Strategic Implications

**The efficiency thesis:** If you cannot match your adversary's hardware, optimize your software. China is pursuing an asymmetric strategy where algorithmic efficiency partially compensates for chip disadvantage.

**Viability assessment:**
- **Short-term (2025-2027):** Highly viable. DeepSeek has proven that competitive models can be trained with significantly less compute. This buys China time while domestic chip capabilities mature.
- **Medium-term (2027-2030):** Uncertain. If AGI or transformative AI requires massive scale (as many US labs believe), efficiency gains may hit diminishing returns. The question is whether the frontier requires brute-force scale or whether architectural innovation can keep pace.
- **Long-term risk for the US:** If DeepSeek's approach generalizes, the entire premise of export controls (deny compute, deny capability) weakens. Efficiency breakthroughs are the greatest threat to the "choke" strategy.

**Counter-argument:** DeepSeek's efficiency gains came partly from training on outputs of US models (distillation). If frontier US models pull further ahead, there may be less to distill from open sources. Access to the frontier still matters even for efficiency-focused approaches.

---

## 6. The Silicon Shield Thesis

### The Original Argument

Taiwan's semiconductor monopoly functions as a "silicon shield" -- both China and the US need TSMC, so neither will allow Taiwan to be destroyed. China cannot take Taiwan without destroying the fabs, and the world cannot afford to lose TSMC.

### Current Assessment: Eroding from Both Sides

**Erosion factor 1 -- TSMC US expansion:**
- TSMC Arizona: $165 billion total investment. Fab 1 producing 4nm chips. Fab 2 (3nm) targeting 2027. Fab 3 (2nm) targeting late decade. Planned expansion to 6 fabs, 2 packaging facilities, and an R&D center.
- Taiwan's N-2 rule restricts overseas fabs to technologies at least two generations behind domestic capability. But even "two generations behind" in Arizona represents frontier capability for most applications.
- NPR (March 2025) reported Taiwanese security concerns about TSMC's US investments diluting the shield.

**Erosion factor 2 -- China domestic progress:**
- As China's domestic chip capability grows (even if slower than the frontier), Taiwan's irreplaceability decreases.
- US export controls paradoxically accelerate this: by denying Chinese access to TSMC, they incentivize domestic alternatives.
- Expert consensus is that the first plank of the silicon shield theory -- that China needs Taiwan's chips -- is becoming "outdated and misguided."

**Erosion factor 3 -- Military normalization:**
- Chinese military incursions around Taiwan are escalating dramatically.
- Taiwan's defense ministry estimated Chinese warplanes entering its air defense zone 200+ times per month in 2025, up from fewer than 10 per month five years ago.
- December 29, 2025: Over 100 Chinese aircraft detected in a single day, 90 crossing the median line. 13 warships, 14 Coast Guard/Maritime Safety vessels. The following day, 27 rockets fired from Fujian, 10 landing inside Taiwan's 24-nautical-mile contiguous zone.
- PLA "Justice Mission-2025" exercise further normalized encirclement operations.

**The strategic paradox:** The silicon shield was always more deterrent-by-mutual-dependency than deterrent-by-capability. As dependency erodes (TSMC diversifies, China builds alternatives), the deterrent weakens. But TSMC's remaining concentration in Taiwan makes it simultaneously less of a shield and more of a target -- a chokepoint worth seizing rather than a resource too valuable to risk.

### The Nightmare Scenario

If China assessed that:
1. TSMC's value to China is declining (domestic alternatives maturing)
2. TSMC's value to the US/West remains critical (AI development depends on it)
3. Seizing or neutralizing TSMC would cripple the adversary's AI advantage

Then the silicon shield inverts: Taiwan's semiconductor monopoly becomes a reason to act, not a reason to refrain. The window where this calculus shifts is the period when China's domestic capability is "good enough" for its own needs but TSMC remains irreplaceable for the West -- plausibly 2028-2032.

---

## Key Uncertainties

1. **SMIC yield rates at 5nm:** If DUV multi-patterning achieves production-viable yields at 5nm, the self-sufficiency timeline accelerates significantly. Current evidence suggests this is 2-3 years away.

2. **DeepSeek V4 performance:** If the trillion-parameter model matches or exceeds GPT-5 class performance at 50x lower cost, it fundamentally changes the compute-capability relationship. Expected March 2026.

3. **Export control policy stability:** Trump administration whiplash (tightening, then suspending enforcement) creates uncertainty. The Affiliates Rule suspension expires November 2026 -- what happens next is a major variable.

4. **Stockpile depletion rate:** How quickly China burns through its Nvidia GPU reserves determines the urgency of the domestic transition. Early 2026 depletion estimates may accelerate strategic decisions.

5. **TSMC Arizona ramp:** If the Arizona fabs achieve high yields and volume production on schedule, the silicon shield erodes faster. Delays would preserve Taiwan's centrality.

6. **Military escalation trajectory:** The December 2025 incidents represent a significant escalation in the gray zone campaign. Whether this is the new normal or a precursor to further escalation is the highest-stakes uncertainty.

---

## Analytical Bottom Line

China is executing a coherent three-part strategy: invest massively in domestic infrastructure, innovate around constraints (DeepSeek efficiency approach), and acquire restricted technology through any available channel. The strategy is partially working -- China's AI capabilities are advancing despite export controls -- but the semiconductor gap is widening, not closing. The critical question is not whether China can build competitive AI models (it can, and has), but whether it can deploy them at scale without access to TSMC's advanced nodes.

Taiwan's strategic value is shifting. It matters less as a source of chips for China (domestic alternatives are emerging) and more as a chokepoint that, if disrupted, would cripple Western AI development. This inversion of the silicon shield thesis is the most dangerous dynamic in the current geopolitical landscape. The window of maximum risk opens when China's domestic capability is "good enough" for its needs while the West remains critically dependent on TSMC -- a window that may be approaching faster than conventional analysis suggests.

---

## Sources

- Goldman Sachs, "China's AI providers expected to invest $70 billion in data centers" (2025)
- Strider Intel / SCSP, "China's AI Infrastructure Surge" (May 2025)
- Council on Foreign Relations, "China's AI Chip Deficit" (December 2025)
- CSIS, "The Limits of Chip Export Controls in Meeting the China Challenge" (2025)
- Congressional Research Service, "U.S. Export Controls and China: Advanced Semiconductors" (R48642, August 2025)
- TrendForce, SMIC earnings and capacity reporting (2025-2026)
- DOJ, Operation Gatekeeper announcement (December 2025)
- Bloomberg, China stockpiling / 115,000 GPU data center investigation (2025)
- MIT Technology Review, "Taiwan's silicon shield could be weakening" (August 2025)
- RAND, "Full Stack: China's Evolving Industrial Policy for AI" (2025)
- Tom's Hardware, CFR report on Huawei vs Nvidia gap (December 2025)
- South China Morning Post, DeepSeek technical paper coverage (January 2026)
- The Diplomat, "China's Taiwan Drills Are Crossing a New Line" (January 2026)
- IEEE Spectrum, "China's AI Chip Race" (2025)
- Federal Reserve, "The Global Trade Effects of the AI Infrastructure Boom" (February 2026)
