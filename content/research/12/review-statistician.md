# SD #12 Statistician Review: "The Gap"

**Reviewer:** Garrus (Statistician Pass)
**Date:** 2026-05-15
**Input:** Draft (`content/drafts/12-deep_dive.md`), research brief, orthogonal analysis, synthesis, supporting research tracks F.3/F.4
**Function:** Model specification, causal identification, uncertainty quantification, missing analysis

---

## VERDICT

This piece would not survive peer review in its current form, but the fixes are surgical, not structural. The core argument is sound and well-sourced. The problems are calibration problems -- probability precision that exceeds data quality, causal language that outruns identification, and a missing counterfactual that weakens the strongest claim. Five priority fixes, detailed below, bring this to defensible territory. The narrative architecture does not need to change. The numbers need to be honest about what they do and do not know.

---

## 1. MODEL SPECIFICATION

### 1a. The 48% Liberty Replacement Probability

**Claim (draft, "The Capacity"):**
> "I assess a 48% probability that Liberty secures adequate replacement power by the May 2027 deadline"

**Statistical concern:** Point estimate precision implies a calibrated model that does not exist. The difference between 48% and 50% is not meaningful given the inputs. The estimate rests primarily on one variable -- Greenlink West on-time completion -- and treats everything else as narrative decoration. The draft acknowledges this implicitly: "Major transmission projects of this scale complete on schedule 60-70% of the time." If that is the reference class, the estimate is anchored to the Greenlink schedule with ad hoc adjustments. That is not 48%. That is "roughly 50%, driven by Greenlink."

The decomposition into 70-75% (some power via emergency purchases) and 25-30% (cost-neutral transition) is analytically useful but poorly justified. Where does 70-75% come from? What is the reference class for "emergency short-term wholesale purchases succeed in isolated grid situations"? The draft does not say. The 25-30% for cost-neutral transition is more defensible (conditional on Greenlink on-time AND Liberty securing competitive rates in a market where it has no leverage), but the conditioning logic is not shown.

**Hidden assumptions:**
- Greenlink West on-time probability is treated as 60-70% with no source citation. The DOE 2023 transmission study is cited for "12-18 month average delays" but not directly mapped to this project. Is a 525-kV, 472-mile line in the same reference class as the DOE study population? What projects are in that study?
- The estimate assumes NV Energy does not create friction on transmission access for Liberty's replacement suppliers. This is not a safe assumption given NV Energy controls the 38 interconnection points.
- Liberty's 25% self-generation via solar is treated as firm. Solar capacity factors in the Sierra Nevada are seasonal. Winter peak demand and solar output are inversely correlated in this geography.

**Recommended fix:** Round to 45-55% range. State explicitly: "The point estimate is approximately 50%, driven primarily by Greenlink West completion timing (reference class: 60-70% on-schedule for major EHV transmission projects per DOE 2023). I shade below 50% because Liberty's procurement timeline is compressed, the relevant transmission capacity is 80% pre-committed, and Liberty has failed to achieve independence in 16 prior years." The decomposition is valuable -- keep it but frame it as a scenario split, not a probability decomposition: "If replacement means lights stay on, the probability is higher (roughly 70%). If it means a cost-neutral transition, the probability is much lower (roughly 25-30%)."

**Severity: HIGH.** This is the article's headline probability and it reads more precise than it is.

### 1b. The 15% FERC Intervention Probability

**Claim (draft, "The Question"):**
> "I assess a 15% probability that FERC intervenes to extend service -- about one in seven"

**Statistical concern:** This is an unconditional probability that conflates two independent events: (a) someone files at FERC, and (b) FERC acts given filing. Legion's orthogonal analysis correctly identifies this structure. The draft should decompose or at least acknowledge the conditioning.

If P(filing) = 25-30% and P(intervention | filing) = 35-40%, the product is 9-12%. If P(filing) = 40% and P(intervention | filing) = 35%, the product is 14%. The 15% is within the plausible range, but the reasoning is stronger and more transparent when the conditional structure is visible.

**Hidden assumption:** The 15% assumes current political dynamics are stable through May 2027. But the story broke nationally on May 12, 2026. Political salience is not static. If the story generates sustained media coverage, P(filing) increases substantially. The draft's own escalation indicators acknowledge this: "Liberty filing a Section 206 complaint changes FERC intervention probability from 15% to 35-45%." That conditional jump is large enough to suggest the unconditional estimate is volatile.

**Recommended fix:** Add one sentence decomposing the conditional structure: "This estimate includes the probability that nobody files -- currently the most likely outcome. If a complaint is filed, the conditional probability of FERC action rises to 35-45%." The 15% point estimate is defensible. The transparency improvement is about showing the work.

**Severity: MEDIUM.** The number is reasonable. The reasoning is hidden.

### 1c. The 40% Pattern Replication Probability

**Claim (draft, "The Pattern"):**
> "I assess a 40% probability that another community faces a wholesale supply termination specifically driven by data center demand within the next twelve months"

**Statistical concern:** This is the best-specified probability in the piece. The resolution criteria are tight: "a utility files to terminate or non-renew a wholesale supply agreement citing data center load, affecting 1,000+ residential customers, by May 2027." The 40% correctly distinguishes between the general pattern (rate increases, grid conflicts -- already happening) and the specific mechanism (wholesale termination stranding residents -- rare and requires unusual conditions). This is well-calibrated.

**One issue:** The base rate for wholesale supply termination disputes is not stated. Legion's orthogonal flags this: "wholesale service termination disputes are a regular feature of electricity regulation." What is the annual rate of wholesale supply termination filings at FERC? If it is 10-20 per year, the question becomes what fraction are data-center-driven and affect 1,000+ residents. If the base rate is 2-3 per year, 40% may be too high. The article should either state the base rate or acknowledge that it is unavailable.

**Recommended fix:** Add: "The base rate for wholesale service termination disputes at FERC is [X per year / not readily available for the specific conditions here]. The 40% reflects the replicating conditions -- interstate wholesale relationships, isolated grids, capacity constraints from concentrated data center demand -- while acknowledging these conditions are unusual." If the base rate is truly unknown, say so. That is more honest than silence.

**Severity: LOW.** This is the strongest probability in the piece. Minor improvement available.

### 1d. The 18% Federal Legislation Probability

**Claim (draft, "The Question"):**
> "I assess an 18% probability that federal legislation addressing data center grid impact passes within twenty-four months"

**Statistical concern:** Same precision problem as 48%. The difference between 18% and 20% is not meaningful. The article itself walks through the logic in terms of rough categories (bipartisan sponsorship: necessary but not sufficient; national security framing: probable kill shot; administration posture: hostile). These are qualitative inputs that do not produce an 18% rather than a 15% or 20%.

**Hidden assumption:** The 24-month window spans the 2026 midterm elections. If Democrats take the House (which the article's own prior issue #9 probabilities suggest is likely at 85%), legislative dynamics shift substantially. The draft mentions midterms but does not condition on electoral outcomes. P(legislation | D House) is meaningfully different from P(legislation | R House).

**Recommended fix:** Round to "roughly 15-20%" or "approximately one in five to one in six." If you want a point estimate, 18% is fine, but frame it: "I round to approximately 18%, recognizing this is a judgment call in a range of 15-22%." Alternatively, note the midterm conditioning: "This estimate assumes current Congressional composition. A Democratic House majority after November 2026 -- which I assess at ~85% in SD #9 -- would increase this estimate, though the administration's veto posture and national security framing remain obstacles."

**Severity: MEDIUM-LOW.** The number is in the right zone. The false precision is a credibility issue.

---

## 2. CAUSAL CLAIMS

### 2a. "Data Centers Caused the Termination"

**Claim (draft, "The Contract"):**
> "The contract was always going to end. Data centers determined when."

**Causal identification strategy:** This is the article's core causal claim, and it relies on a difference-in-differences-style argument: NV Energy extended three times over 16 years (the counterfactual pattern), then refused to extend when data center demand arrived (the treatment). The logic is: absent the treatment (data center demand), the counterfactual outcome (fourth extension) would have occurred.

**Statistical concern:** This identification strategy is suggestive but not definitive. There are at least three confounders the article does not rule out:

1. **Regulatory patience exhaustion.** NV Energy may have terminated regardless of data centers, simply because 16 years of a "temporary" arrangement is extraordinary patience by any commercial standard. The first three extensions were voluntary and unusual. A fourth refusal could reflect a policy decision unrelated to data centers. NV Energy's spokesperson explicitly frames it this way.

2. **BHE earnings pressure.** Legion's orthogonal analysis identifies this: BHE's energy segment had flat-to-declining earnings in 2024-2025. Terminating a cost-based wholesale arrangement frees capacity for higher-margin industrial customers (data centers) and justifies capital expenditure on Greenlink West (higher rate base = higher returns). The data center demand is the opportunity, but BHE's financial incentive to terminate exists independently of any specific industrial customer type.

3. **General load growth.** Nevada is one of the fastest-growing states. Even without data centers, Northern Nevada faces population-driven load growth that constrains capacity. The 0 MW import capacity figure may reflect general growth, not exclusively data center growth.

The article's strongest evidence for the causal claim is Liberty's own CPUC filing: NV Energy cited "data centers in the Tahoe-Reno Industrial Center area and northern Nevada transmission constraints." This is close to an admission -- but note the "among other reasons" qualifier and the conjunction with "transmission constraints," which could exist independently.

**Recommended fix:** The current language is actually well-calibrated -- "Data centers determined when" is a timing claim, not a sole-cause claim. Strengthen it by explicitly addressing the counterfactual: "Would NV Energy have extended a fourth time absent data center demand? The evidence suggests yes: three prior extensions established a pattern of voluntary accommodation. But certainty is impossible. What is clear is that 5,900 MW of data center capacity requests in the same service territory, 0 MW of available import capacity, and a $4.2 billion transmission line 80% committed to data centers made a fourth extension economically irrational in a way that general load growth alone would not have." This is one additional sentence that converts an implicit causal claim into an explicit counterfactual argument.

**Severity: HIGH.** This is the thesis. The causal reasoning should be airtight.

### 2b. Correlation Masquerading as Causation: Greenlink-Termination Synchronization

**Claim (draft, "The Capacity"):**
> "The completion date for Greenlink West: May 2027. The same month Liberty's power supply ends."

**Statistical concern:** The article presents this synchronization as evidence of NV Energy optimizing for data centers. But the synchronization is also consistent with NV Energy's stated defense: the termination date was calibrated to when Liberty would have access to alternative suppliers via Greenlink. Both interpretations are consistent with the data. The article should acknowledge the dual interpretation rather than letting the juxtaposition imply the worst reading.

The draft does handle this partially ("NV Energy frames this synchronization as accommodation"), but the rhetorical structure -- presenting the synchronization in the "Capacity" section rather than a balanced assessment -- weights the negative interpretation.

**Recommended fix:** No language change needed. The current treatment is adequate. The dual interpretation is acknowledged. This is a flag, not a fix.

**Severity: LOW.**

### 2c. PJM 11x as Implied Causation for Lake Tahoe

**Claim (draft, "The Pattern"):**
> "capacity auction prices rose from $28.92 to $329.17 per MW-day over two delivery years -- an approximately 11-fold increase"

**Statistical concern:** The draft includes the caveat: "PJM operates a competitive wholesale market, not a vertically integrated utility system, and the 11x figure does not directly predict cost impacts for Lake Tahoe residents." This is good. However, the proximity to the Lake Tahoe narrative creates an implied connection that the caveat partially undoes. A reader who skims will take away "11x price increase" and associate it with the Tahoe story.

The draft's own caveat is sufficient. The placement is the issue -- it comes mid-paragraph after the dramatic number, which is where readers stop reading.

**Recommended fix:** Move the caveat to immediately follow the 11x figure: "PJM Interconnection capacity auction prices rose approximately 11-fold over two delivery years -- a different market mechanism than Nevada's bilateral termination, but with the same downstream effect: residential ratepayers absorb cost increases driven by data center demand." The current structure buries the caveat. Lead with it.

**Severity: MEDIUM.** The article handles this better than the synthesis did (Legion flagged this and it was corrected), but the placement can still mislead skimmers.

---

## 3. UNCERTAINTY QUANTIFICATION

### 3a. Probability Precision Does Not Match Data Quality

**General finding:** Four probability estimates are stated to single-percentage-point precision (48%, 15%, 40%, 18%). The underlying data does not support this precision. The inputs are qualitative judgments, reference class analogies, and expert elicitation -- not models with measured parameters.

For comparison: the Intergovernmental Panel on Climate Change (IPCC) uses likelihood language precisely because single-point estimates on complex systems imply false precision. The IPCC scale maps: "about as likely as not" (33-66%), "unlikely" (0-33%), "likely" (66-100%). Signal Dispatch's estimates land in "about as likely as not" (48%, 40%) and "unlikely" (15%, 18%).

**Recommended fix:** Either (a) round all estimates to the nearest 5% (50%, 15%, 40%, 20%) and state that precision beyond 5-point increments is not supported by the evidence base, or (b) keep the point estimates but add explicit uncertainty ranges: "48% (plausible range 40-55%)", "15% (plausible range 10-20%)", "40% (plausible range 30-50%)", "18% (plausible range 12-25%)." Option (b) is more informative.

The 48% is the most problematic because it implies a coin flip with two percentage points of calibration. The evidence base supports "roughly a coin flip" and nothing more precise.

**Severity: HIGH.** This is the single most important fix for credibility. A newsletter that tracks Brier scores must be especially careful about precision claims.

### 3b. The 48% Decomposition Lacks Justification

**Claim (draft, "The Capacity"):**
> "the probability that some power is available through emergency short-term purchases is higher (70-75%). The probability of a clean, cost-neutral transition is much lower (25-30%)"

**Statistical concern:** These sub-estimates are presented as decomposing the 48%, but the arithmetic does not work as a standard probability decomposition. If there is a 70-75% chance of "some power" and a 25-30% chance of "cost-neutral transition," the overall probability depends on how "adequate replacement" maps to these outcomes. Is adequate = some power? Then the estimate should be 70-75%. Is adequate = cost-neutral? Then the estimate should be 25-30%. The 48% sits between these in a way that implies a weighting function (something like: adequate = partially some power, partially cost-neutral), but the weights are not stated.

**Recommended fix:** Reframe the decomposition as scenario analysis rather than probability decomposition:
"What 'adequate' means determines the estimate. If the question is whether lights stay on -- whether Liberty has any power supply, however expensive, by May 2027 -- I assess roughly 70%. If the question is whether Liberty achieves a cost-neutral replacement that does not shock ratepayers -- I assess roughly 25-30%. The 48% reflects a judgment that 'adequate' falls between these extremes: firm contracts covering 75%+ of load, but at costs that will be passed through to ratepayers."

This is clearer, more honest, and eliminates the false decomposition.

**Severity: HIGH.** The decomposition is the most analytically interesting part of the estimate and it is currently confusing.

### 3c. Missing Confidence Intervals on Key Figures

Several empirical claims in the draft are presented as point estimates where the underlying data has meaningful uncertainty:

| Claim | Stated | Underlying Uncertainty |
|-------|--------|----------------------|
| 78% of capacity requests are data centers | 78% | This is the request queue, not the planning forecast. After NV Energy's discounting (49-85%), the actual planning share is 40-60% (acknowledged in the text). Lead with the planning range. |
| $457M in tax incentives for ~300 jobs | $1.5M/job | "~300" is likely statutory minimums, not actual employment. If actual employment is 400-600, the per-job figure drops to $760K-$1.1M. Still extreme, but the range matters. |
| 77% rate increase since late 2022 | 77% | Single source (Bloomberg via F.5). The decomposition into Liberty's own costs vs. NV Energy wholesale rate is not shown. The article correctly notes most is pre-data-center, but the uncertainty on attribution is total. |
| 0 MW available import capacity | 0 MW | This is the 704B exit limit for the 2024-2027 action plan period. It is a planning parameter, not a permanent physical constraint. When Greenlink West comes online, this changes. The article conflates a current planning constraint with a permanent condition. |

**Recommended fix:** For the 78% figure, the draft already handles this well: "Twelve of those projects are data centers. They account for 5,900 MW -- 78% of all capacity requests. NV Energy applies 49-85% planning discounts; after discounting, data centers still represent an estimated 40-60% of incorporated load growth." This is fine.

For the $457M/300 jobs, add: "approximately 300 permanent jobs at statutory minimum requirements -- actual employment may be higher, which would reduce the per-job figure, though not below the $750,000 range."

For the 0 MW figure, consider adding: "during the current action plan period" to prevent misreading as permanent.

**Severity: MEDIUM.** The draft handles most of these adequately. The $457M/job figure is the one most likely to be challenged.

---

## 4. WHAT IS MISSING

### 4a. Counterfactual Analysis: Would NV Energy Have Terminated Without Data Centers?

This is the single most important missing analysis. The article's thesis hinges on data centers as the proximate cause, but no explicit counterfactual is constructed. A rigorous treatment would ask:

- What was NV Energy's capacity situation in 2015 and 2020 when it chose to extend? Was there spare capacity then?
- How much of the 0 MW import capacity constraint is attributable to data centers vs. general Nevada population growth vs. existing industrial load?
- If data center demand were removed from the IRP, would Sierra Pacific have available import capacity? The IRP shows 5,900 MW of data center requests out of 7,600 MW total. Removing data centers leaves 1,700 MW of non-data-center requests. Would NV Energy have extended under those conditions?

The research tracks contain enough data to construct this counterfactual, at least approximately. The IRP data shows the capacity math with and without data centers. The article should do that math explicitly rather than leaving it as an inference.

**Recommended fix:** Add 2-3 sentences in "The Capacity" section: "Remove data center demand from the IRP and Sierra Pacific's capacity picture changes fundamentally. Of the 7,600 MW in capacity requests, 5,900 MW are data centers. The remaining 1,700 MW of general load growth is manageable within NV Energy's existing resource plan. The 0 MW import capacity constraint exists because data center demand filled the pipeline. Under the counterfactual -- same Nevada growth, no data center boom -- NV Energy would likely have had capacity to extend the Liberty arrangement a fourth time."

**Severity: HIGH.** This is the missing analytical step that converts the causal claim from suggestive to rigorous.

### 4b. Selection Bias in the Pattern Analysis

The national pattern section documents conflicts in 10+ states. But is the sample representative, or are we only observing conflicts that generated media coverage? The selection process -- stories that made it to Fortune, Ars Technica, local news -- biases toward dramatic cases. There may be jurisdictions where data center demand was absorbed without conflict (because the utility had spare capacity, or because the state PUC proactively created cost-allocation tariffs, or because the data center developer funded its own infrastructure).

The article would be stronger if it acknowledged this: "These are the conflicts that surfaced publicly. Jurisdictions where data center integration proceeded without conflict -- because capacity existed or regulators acted proactively -- are not visible in this analysis. The pattern is real but the sample is biased toward failure cases."

**Recommended fix:** One sentence in "The Pattern" section acknowledging the survivorship bias.

**Severity: LOW-MEDIUM.** The pattern claim is not wrong, but it is incomplete without this caveat.

### 4c. Demand Elasticity: Is AI Compute Demand Inelastic?

Legion's orthogonal analysis flags this and the draft does not address it. The entire structural argument assumes data center demand is inelastic -- that the compute must happen and the grid must accommodate it. But this assumption is untested and historically questionable. Crypto mining generated similar "the grid cannot handle it" alarm in 2017-2021 before demand collapsed with prices. If AI compute demand is elastic (if higher electricity costs push workloads offshore, drive efficiency improvements, or slow deployment), the "structural conflict" narrative softens over a 3-5 year horizon.

The article does not need to resolve this question. It should acknowledge it exists: "The permanence of this conflict depends on whether AI compute demand is inelastic -- whether the workloads must run here regardless of cost -- or elastic, as cryptocurrency mining proved to be. If elastic, the structural pressure may ease within 2-3 years. Current industry behavior (behind-the-meter generation, $4.2B transmission investment, 362 MW of gas turbines at TRIC) suggests the industry is treating demand as inelastic. Whether the market agrees remains to be seen."

**Recommended fix:** 2-3 sentences in "The Pattern" section. This is the strongest counterargument to the article's structural thesis and ignoring it weakens the piece.

**Severity: MEDIUM.** Not fatal to the argument. Conspicuous in its absence.

### 4d. Liberty's Perverse Incentives Deserve More Weight

The draft includes a paragraph noting that Algonquin/Liberty may profit from higher replacement costs (higher rate base = higher CPUC-approved returns). This is correct and well-placed. But it is buried in "The Community" section as a subordinate observation. It deserves more prominence because it resolves the FERC non-filing mystery -- the party with the clearest standing to invoke FERC jurisdiction (Liberty) has a financial incentive not to. This is not a minor complication. It means 49,000 residents have no motivated champion.

**Recommended fix:** This is already in the draft. Consider elevating it from a paragraph in "The Community" to a named callout or a more prominent position. The current treatment is adequate but could hit harder.

**Severity: LOW.** Already addressed. Flagging for emphasis.

---

## 5. PRIORITY FIXES (RANKED)

1. **Round probabilities or add explicit ranges.** 48% -> "roughly 50% (range: 40-55%)" or round to 50%. 18% -> "roughly 15-20%" or round to 20%. 15% and 40% are already round enough. This is the single highest-impact credibility fix.

2. **Add the counterfactual analysis for data center causation.** 2-3 sentences: remove data center demand from the IRP, show the capacity math changes, make the causal inference explicit rather than implied.

3. **Reframe the 48% decomposition as scenario analysis.** Replace the 70-75% / 25-30% decomposition with named scenarios (lights-on vs. cost-neutral) and explain which definition of "adequate" produces the headline estimate.

4. **Decompose the 15% FERC estimate.** One sentence showing P(filing) x P(intervention | filing) structure. The point estimate can stay the same.

5. **Add demand elasticity caveat.** 2-3 sentences in "The Pattern" acknowledging that the permanence of the structural conflict depends on whether AI compute demand proves elastic or inelastic.

---

## 6. WHAT WORKS

The article's strengths, which should not be disturbed:

- **Resolution criteria are specific and verifiable.** "Firm procurement contracts covering 75%+ of annual load by May 31, 2027" is a well-specified resolution. This is better calibration practice than most professional forecasting.
- **The escalation indicators are excellent.** Each probability estimate includes named events that would move the estimate, with direction and magnitude. This is best-practice uncertainty communication.
- **The 78% vs. 40-60% distinction is properly handled.** Legion flagged the request queue vs. planning forecast conflation and the draft correctly presents both numbers with the appropriate caveat. This was the biggest statistical trap in the research and the draft navigated it.
- **The PJM caveat is present.** The different market mechanism is noted. Placement could improve (per 2c above) but the caveat exists.
- **The "planned transition" defense is given genuine weight.** The article does not straw-man NV Energy. The contract was temporary. Liberty failed to achieve independence. NV Energy extended three times. This is honestly presented and then the article shows where the defense breaks down. This is how causal arguments should be built.

---

## OVERALL VERDICT

Would this survive peer review? Not in current form -- the probability precision, missing counterfactual, and decomposition confusion would draw reviewer comments. But the core analysis is sound, the sourcing is excellent, and the causal logic is directionally correct even where the identification strategy could be tighter.

With the five priority fixes above, this piece is defensible. The narrative architecture, the sourcing, and the legal analysis are strong. The statistics need to be honest about their own uncertainty. That is a calibration adjustment, not a rewrite.

Can it wait? The calibrations cannot.
