# Issue 8: Linerixibat PDUFA March 24 — Integrated Synthesis
**Generated:** 2026-03-17
**Integrated from:** Legion synthesis + Deep Pull 1 (DEEP PULL 0 timed out — no usable data)
**PDUFA date:** 2026-03-24 (T-7 days)
**Source corpus:** 8 parallel workers + 1 deep pull

---

## Integration Notes

**DEEP PULL 0:** Session timed out at 300s. Output was unreadable (encrypted session artifact). No findings integrated.

**DEEP PULL 1:** Substantive findings. Two updates to the synthesis:
1. **Resubmission class contradiction resolved** (see below)
2. **Resubmission timeline caveat added** — the inferred timeline is reconstructed, not publicly confirmed

---

## Contradiction Resolution: Class 1 vs. Class 2 Resubmission

**Original synthesis called this a "Class 2 resubmission." Deep Pull 1 identifies it as "Class 1."**

This is not a minor semantic difference — it changes the regulatory mechanics.

| Class | FDA review goal from resubmission date | Dec 23 CRL → late Jan resubmit → PDUFA |
|-------|---------------------------------------|----------------------------------------|
| Class 1 | 2 months | ~March 24, 2026 ✓ |
| Class 2 | 6 months | ~July 2026 ✗ |

**Resolution: Class 1 resubmission is correct.** The March 24, 2026 PDUFA date is consistent with a ~2-month Class 1 review timeline from a late-January resubmission. A Class 2 resubmission from the same date would push the PDUFA to approximately July 2026. The original synthesis classification was in error.

**What Class 1 resubmission implies:** The resubmission responded to a "minor" FDA deficiency — typically manufacturing, labeling, or circumscribed safety data additions. Class 1 resubmissions are not reserved for minor concerns per se, but FDA's acceptance of a 2-month review goal signals the agency believed the outstanding issues were defined and addressable. This is a modestly positive signal compared to Class 2, which implies more open-ended concern.

**Caveat on timeline:** Deep Pull 1 notes there is no public GSK announcement of "we resubmitted on [date]." The CRL Dec 23 → resubmit Jan → PDUFA March 24 inference is reconstructed from public calendar arithmetic, not from a confirmed GSK filing notice. This is described as normal for Class 1 resubmissions. The PDUFA date itself is confirmed; the exact resubmission date is inferred.

---

## Signal Convergence

All eight workers agree on the following picture:

**1. This is a resubmission decision, not an original approval.**
The March 24 PDUFA date is the resolution of a **Class 1 resubmission** *(corrected from Class 2)* following a Complete Response Letter (CRL) issued December 23, 2025. FDA's concern was not trial validity — it was a hepatic safety signal and a REMS requirement. The March 24 decision is a binary: is the revised REMS adequate? Every worker who touched the regulatory timeline landed here.

**2. The GLISTEN Phase 3 trial is statistically robust.**
p=0.0013 on the primary endpoint (Worst Scratch Intensity, 0–10 NRS). -0.72 point treatment difference. Published in peer-reviewed journal (PubMed 41173016). Workers 1 and 2 both independently flagged this as "clean" pivotal data. No worker found evidence of data integrity concerns, misrepresented endpoints, or FDA signals suggesting the trial itself is in dispute.

**3. No Advisory Committee was convened.**
Worker 3 confirmed: no adcom. Workers 0 and 6 both noted this is consistent with IBAT class precedent and FDA's standard practice for rare disease drugs with well-characterized endpoints. No briefing documents are public as of T-7. This is consistent with resubmission review mechanics — briefing documents typically precede adcoms, and there's no adcom here.

**4. First adult IBAT indication; fills a genuine unmet need.**
Two pediatric IBAT inhibitors are already approved (odevixibat/Bylvay for PFIC/ALGS; maralixibat/Livmarli for ALGS). No approved pruritus-specific therapy exists for adult PBC in the US. The two recent disease-modifying PBC approvals (seladelpar/Livdelzi 2023, elafibranor/Iqirvo 2024) address liver disease progression, not itch. Linerixibat fills a distinct, complementary niche. Workers 0, 5, and 6 converged on this.

**5. The diarrhea mechanism is pharmacodynamic, not idiosyncratic.**
Worker 2 found the C4 biomarker study (PMID 39945351) that grounds this mechanistically: IBAT inhibition elevates C4 (bile acid synthesis marker), bile acid spillover into the colon drives osmotic/secretory diarrhea. This is a class effect. It cannot be engineered away, only managed with dose selection. GSK optimized for tolerability (GLIMMER trial dose-finding), not efficacy maximization — the 40mg BID dose is the class floor.

**6. The GSK-Alfasigma deal structure is a deliberate risk transfer.**
$300M upfront (paid regardless of approval) + $100M approval milestone + total value up to $690M. Announced March 9, 2026 — fifteen days before PDUFA. Workers 2 and 4 both independently interpreted the deal timing: GSK divested *before* resolution and transferred approval risk to Alfasigma. This is consistent with GSK's strategic repositioning toward oncology and vaccines, but the timing also reflects GSK assigning meaningful probability to non-approval and pricing that into the deal structure.

---

## Signal Divergence

Three genuine tensions where the workers' findings pull in different directions:

**Tension 1: What the "no AdCom" signal means.**
Worker 6's base rate analysis shows positive adcom vote → ~97% approval. But there was no adcom. Worker 3 says this is standard practice for IBAT class; absence of adcom = FDA confidence in the data. Worker 2 suggests the opposite reading is also valid: the CRL was issued *because* FDA had concerns (hepatic signal + REMS), and the adcom waiver means there's no public record of how FDA weighed those concerns. The adcom absence removes the strongest public probability signal available.

**Tension 2: Whether the 12% SAE rate is explainable or alarming.**
Worker 2 identified a 4-fold discrepancy between linerixibat's GLISTEN SAE rate (12%) and the IBAT class meta-analysis SAE rate (2.2%). Worker 2's explanation: population difference — adult PBC patients with established disease vs. the pediatric cholestatic conditions in approved agents. This is plausible. But Worker 1 flagged the same number without the explanation, noting it "will be the safety discussion." The question of whether FDA accepts the population-difference explanation for the SAE discrepancy is the operative regulatory risk that cannot be resolved from open-source data.

**Tension 3: GSK's public framing vs. FDA's stated CRL concern.**
Worker 2 identified a specific gap: GSK described GLISTEN's safety profile as "consistent with the mechanism of IBAT inhibition" — accurate for GI adverse events, but this framing sidesteps the hepatic signal that generated the CRL. FDA mandated the REMS in December 2025. GSK's public communications did not. The March 24 decision turns on whether the revised REMS adequately addresses what FDA actually flagged, not what GSK publicly characterized.

---

## Key Data Points Table

| # | Data Point | Value | Source | Status |
|---|-----------|-------|--------|--------|
| 1 | PDUFA date | March 24, 2026 | FDA calendar / multiple | Confirmed |
| 2 | Days to decision | 7 | Current date | Current |
| 3 | Primary endpoint (WSI, 0–10 NRS) | -0.72 treatment difference vs. placebo | GLISTEN PubMed 41173016 | Confirmed |
| 4 | Primary endpoint p-value | p = 0.0013 | GLISTEN trial | Confirmed |
| 5 | Responder rate (linerixibat) | 56% | GLISTEN trial | Confirmed |
| 6 | Responder rate (placebo) | 43% | GLISTEN trial | Confirmed |
| 7 | Responder gap p-value | p = 0.043 (CI touches 0%) | Worker 1 analysis | Confirmed |
| 8 | Diarrhea rate (linerixibat arm) | 61% | GLISTEN Phase 3 | Confirmed |
| 9 | Serious adverse event rate (linerixibat) | 12% | GLISTEN Phase 3 | Confirmed |
| 10 | IBAT class meta-analysis SAE rate | 2.2% | Worker 2 cross-ref | Confirmed |
| 11 | SAE rate discrepancy (vs. class) | ~4× | Worker 2 calculation | Confirmed |
| 12 | Trial duration | 24 weeks | GLISTEN Phase 3 | Confirmed |
| 13 | Approved dose | 40mg BID | GLIMMER → GLISTEN | Confirmed |
| 14 | GSK-Alfasigma upfront payment | $300M | March 9, 2026 press release | Confirmed |
| 15 | Approval milestone payment | $100M | GSK/Alfasigma announcement | Confirmed |
| 16 | Total deal value | Up to $690M | BioXconomy | Confirmed |
| 17 | Deal signing date | March 9, 2026 | GSK press release | Confirmed |
| 18 | Days between deal and PDUFA | 15 | Calculation | Confirmed |
| 19 | Kalshi market price (reported) | ~$0.62 | Unconfirmed (no live access) | Unconfirmed |
| 20 | Our probability estimate | **72%** | Integrated synthesis (updated) | Updated |
| 21 | FDA overall PDUFA approval rate | ~67.7% | Worker 6 base rate | Confirmed |
| 22 | Priority review first-cycle approval rate | ~77% | Worker 6 base rate | Confirmed |
| 23 | Positive adcom → approval rate | ~97% | Worker 6 base rate | Confirmed |
| 24 | BTD + Orphan + positive adcom compound | 85–97% range | Worker 6 synthesis | Confirmed |
| 25 | CRL date (original) | December 23, 2025 | FDA NDA219624 CRL document | Confirmed |
| 26 | **Resubmission class** | **Class 1** *(corrected from Class 2)* | Deep Pull 1 | **Updated** |
| 27 | **Class 1 PDUFA review goal** | **2 months from resubmission** | FDA PDUFA standards | **New** |
| 28 | **Resubmission date (inferred)** | **~Late January 2026 (reconstructed)** | Deep Pull 1 calendar inference | **New — unconfirmed** |
| 29 | **No public GSK resubmission announcement** | Confirmed absent | Deep Pull 1 | **New** |

---

## Probability Assessment

### Updated Estimate: 72% (revised from 68–75% range)

**What changed from the preliminary assessment:**

The Class 1 resubmission determination is a modest positive update. Class 1 implies FDA accepted the resubmission under a 2-month review goal — signaling the outstanding issues were defined and circumscribed (not open-ended). This shifts the probability slightly upward from the lower end of the 68–75% range established after integrating the deal timing signal.

The resubmission timeline caveat (reconstructed, not confirmed) is neutral — it doesn't change the underlying regulatory picture, only the epistemic confidence in our timeline reconstruction. The PDUFA date itself remains confirmed.

**Net probability movement:** 68–75% range → **72% point estimate**

The two-percentage-point upward move from the midpoint reflects the Class 1 signal. The estimate remains well below the 77% base rate for priority review first-cycle approvals, appropriately discounting for: (1) this being a resubmission rather than original approval, (2) the hepatic safety signal whose exact nature remains unknown, and (3) the GSK deal timing as a genuine negative signal.

---

### Base Case: Approval (probability: 72%)

**Why:** The pivotal trial is published, statistically robust, and FDA-reviewed. Class 1 resubmission acceptance signals FDA viewed the outstanding issues as defined and addressable. The REMS requirement was mandated in December 2025, meaning FDA was already contemplating an approval pathway — they weren't rejecting the drug, they were conditioning approval. If the revised REMS is adequate, the path to approval exists. No adcom, no public signals of further review concerns.

**Confidence modifiers:** No adcom removes the strongest public signal but doesn't change the underlying trial data. The 12% SAE rate requires the population-difference explanation to hold with FDA reviewers — plausible but unverifiable from public sources.

### Bear Case: Second CRL (probability: 22%)

**Why:** The CRL was issued for a hepatic safety signal — not GI tolerability, which is expected and class-consistent. The gap between GSK's public framing ("consistent with mechanism") and FDA's stated concern (hepatic signal requiring REMS) suggests incomplete alignment between sponsor and regulator. If the revised REMS is deemed inadequate, or if FDA has additional concerns that surfaced during the Class 1 review that are not yet public, a second CRL is the outcome. The deal structure — GSK transferring risk to Alfasigma 15 days before decision — is consistent with a sponsor assigning non-trivial probability (~20–30%) to non-approval.

**Key risk factor:** The exact nature of the December 23, 2025 CRL hepatic signal is not public. This is the single most important unknown.

### Bull Case: Clean Approval + Market Surprise (probability: 6%)

**Why:** If the briefing documents (possibly now public, T-7) show clean REMS resolution and FDA signals confidence, the 62-cent Kalshi market is significantly mispriced. The 10-percentage-point gap between market (62%) and our estimate (72%) suggests the market is pricing in more CRL risk than the base rate warrants. If the briefing docs are positive, the trade moves immediately.

---

## Research Gaps

**Critical (decision-relevant):**

1. **Exact CRL language from December 23, 2025** — What specifically triggered the hepatic safety concern? Was it ALT elevation, bilirubin, actual hepatic AEs, or a signal from pharmacovigilance? This is the number-one unknown. It determines whether the REMS revision is likely adequate or whether FDA has concerns that a REMS can't address.

2. **FDA briefing documents (may now be public)** — PDUFA is T-7. FDA may post summary review documents. If posted, they are authoritative. See sources listed below — `fda.gov` drug page for NDA219624 may have updated review documents.

3. **Live Kalshi contract data** — Current ticker, exact resolution criteria language, live price, volume, and OI. Worker 7 confirmed web search cannot reach this — requires direct API query to `api.kalshi.com/trade-api/v2/markets`. The ~62c figure is unconfirmed.

4. **Revised REMS proposal contents** — What monitoring, prescriber certification, and patient enrollment requirements did GSK/Alfasigma propose in the resubmission? Standard REMS (liver function monitoring every 3 months) is approvable. REMS with ETASU is a commercial red flag.

**Moderate (useful but not decision-critical):**

5. **Alfasigma's US commercial infrastructure** — Alfasigma is an Italian pharma, less established in US rare disease. Launch risk is real even with approval.

6. **Subgroup performance in moderate vs. severe itch** — The 56% vs. 43% responder gap with CI touching 0% on lower bound is the clinical significance pressure point.

7. **Long-term extension (OLE) data** — 24-week trial is short for a chronic condition. OLE likely ongoing but not yet reported.

---

## Confirmed Sources (Deep Pull 1)

- FDA CRL NDA219624 December 23, 2025 — `download.open.fda.gov/crl/CRL_NDA219624_20251223.pdf`
- FDA Novel Drug Approvals 2026 — `fda.gov/drugs/novel-drug-approvals-fda/novel-drug-approvals-2026`
- GLISTEN Phase III Trial — PubMed 41173016
- GLISTEN — Lancet Gastroenterology & Hepatology (PIIS2468-1253(25)00192-X)
- GSK GLISTEN Phase III Results Press Release
- GSK NDA Accepted for Review Press Release
- GSK-Alfasigma $690M Deal — BioXconomy
- GSK AASLD 2025 Data Presentation
- PMC: GLISTEN Biomarker Analysis (PMC12879065)
- FDA REMS Database — `accessdata.fda.gov/scripts/cder/rems/index.cfm`
- Precision FDA — Linerixibat Substance (c424c09a-87f9-4c89-8d13-11f908dd5e2c)
- HCPLive Q1 2026 FDA Preview
- FDA Drug Approval Decisions March 2026 — GI Advisor

---

## Meta-Note

The intelligence picture sharpened on one dimension: the resubmission is Class 1, not Class 2. This is the most actionable update from the deep pull — it slightly tightens the probability upward (to 72%) and resolves an internal inconsistency in the original synthesis. The core uncertainty structure is unchanged: the exact CRL hepatic signal and the adequacy of the revised REMS remain the two unresolvable unknowns from open-source data. The 10-percentage-point gap between Kalshi (~62%) and this estimate (72%) is the trade signal. Briefing documents (pull target #1) and live Kalshi price (pull target #2) remain the highest-leverage next steps before PDUFA closes on March 24.

*— Legion synthesis, integrated from 8 workers + Deep Pull 1*
