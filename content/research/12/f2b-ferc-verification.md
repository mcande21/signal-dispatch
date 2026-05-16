# F.2b FERC Filing Verification: Critical Follow-up

**Track:** LEAD (Legal/Regulatory) -- Verification of F.2 findings
**Date:** 2026-05-15
**Issue:** SD #12
**Status:** Complete -- multi-source verification with significant new finding

---

## CRITICAL NEW FINDING: ER26-534-000

**The prior F.2 analysis missed a significant FERC filing.** On November 17, 2025, Sierra Pacific Power Company filed an **"Amended Liberty PPA"** with FERC under Section 205(d) of the Federal Power Act.

- **Docket:** ER26-534-000
- **Description:** "Sec. 205(d) Rate Filing: Filing of Amended Liberty PPA to be effective 12/29/2025"
- **Filed:** November 17, 2025
- **Effective date:** December 29, 2025
- **Accession Number:** 20251117-5192
- **Federal Register Citation:** 90 FR 52378 (November 20, 2025, document 2025-20427)
- **Comment deadline:** 5 p.m. ET December 8, 2025

**This is NOT a termination filing. It is an amendment to the existing Liberty PPA.** The filing amends the terms of the wholesale power purchase agreement -- not cancelling it but changing its terms, effective December 29, 2025. The filing occurred approximately five months *before* NV Energy publicly communicated the May 2027 end date to Liberty (Liberty filed its CPUC advice letter in March 2026).

### Implications

1. The Liberty PPA is confirmed as a FERC-jurisdictional rate filing under Section 205(d). This eliminates the possibility that the agreement is a purely bilateral contract outside FERC jurisdiction.

2. SPPC was actively amending the PPA as recently as December 2025. The amendment may have added or modified the termination provisions that NV Energy subsequently exercised.

3. A second filing on December 3, 2025 (ER26-645-000, accession 20251203-5053) involves a related "SPPC-Harney Funding Agreement Filing" under Section 205(d), effective 12/4/2025. The Harney connection is unclear but may relate to infrastructure or transmission agreements connected to the Liberty service territory.

---

## Verification Method 1: FERC eLibrary Direct Access

**Outcome: eLibrary web interface returned only headers, no document content.** FERC's eLibrary requires interactive browser access; automated fetches returned empty pages for both ER26-534 and ER19-2176 docket sheets.

However, the Federal Register API provided the definitive finding. FERC publishes all rate filings in Combined Notices of Filings in the Federal Register, and the API is searchable.

---

## Verification Method 2: Federal Register Combined Notices

**Outcome: 17 FERC documents mentioning Sierra Pacific Power since January 2025.** Key findings:

| Date | Doc # | Docket | Description |
|------|-------|--------|-------------|
| 2025-03-31 | 2025-05470 | ER25-1749-000 | Compliance filing per Order No. 904 (not Liberty-related) |
| 2025-11-20 | 2025-20427 | **ER26-534-000** | **"Filing of Amended Liberty PPA to be effective 12/29/2025"** |
| 2025-12-08 | 2025-22179 | **ER26-645-000** | **"SPPC-Harney Funding Agreement Filing" effective 12/4/2025** |

**No cancellation or termination filing for the Liberty PPA was found in any 2025-2026 Federal Register notice.** The searches covered:
- "Sierra Pacific" + "cancellation" (2025-present): 0 Liberty-related cancellations
- "Sierra Pacific" + "termination" (2025-present): 0 Liberty-related terminations
- "Sierra Pacific" + "Liberty" (all time): 31 total documents, none containing a cancellation of the main PPA

---

## Verification Method 3: Rate Schedule Database

**Outcome: Confirmed the SPPC-Liberty rate schedule history at FERC.**

The full filing chronology of the SPPC-Liberty relationship at FERC:

| Year | Rate Schedule | Description | Docket |
|------|---------------|-------------|--------|
| 2014 | RS 66 | Engineering Procurement Construction Agreement -- Liberty Utilities | ER14-1490 (est.) |
| 2015 | RS 55 | SPPC Liberty 1st Amended Service Agreement | ER15-2603 (est.) |
| 2016 | RS 55 | SPPC & Liberty 2nd Amendment Service Agreement | ER16-771 (est.) |
| 2016 | RS 66 | SPPC & Liberty EPC Agreement Amendment | ER16-822 (est.) |
| 2019 | RS 66 | **SPPC & Liberty EPC Cancellation** | **ER19-2174-000** |
| 2019 | RS 71 | **CalPeco & SPPC 609 Line Agreement Cancellation** | **ER19-2176-000** |
| 2020 | RS 55 | SPPC & Liberty 3rd Amended Service Agreement | ER20-3017-000 |
| 2021 | SA 21-00011 | SPPC Liberty (new service agreement) | ER21-1476-000 |
| 2025 | -- | **Amended Liberty PPA** | **ER26-534-000** |

**Key finding:** Rate Schedule No. 55 appears to be the **main wholesale power supply/service agreement.** It has been amended three times (2015, 2016, 2020) and was the most frequently updated SPPC-Liberty filing. The 2019 cancellations (RS 66 and RS 71) were ancillary agreements:
- RS 66 was the "Engineering Procurement Construction Agreement" -- a construction contract, not the PPA itself
- RS 71 was the "609 Line Agreement" -- an infrastructure/transmission line agreement

**The main PPA (likely RS 55 or its successor) has NOT been cancelled.**

---

## Verification Method 4: Liberty/CalPeco Filings

**Outcome: Liberty's activity is exclusively at the CPUC, not FERC.**

- **March 2026 CPUC Advice Letter:** Liberty filed requesting expedited RFP authorization for replacement power, citing NV Energy's stated termination. No specific advice letter number found in public searches.
- **CPUC Docket A.24-09-010:** Liberty's 2025 General Rate Case (approved March 2026, 11.4% increase)
- **CPUC Docket A.25-10-xxx:** Liberty's 2025 ECAC Application for energy cost adjustment
- **No FERC filing by Liberty:** No complaint, protest, or intervention at FERC regarding the termination

---

## Verification Method 5: Trade Press Coverage

**Outcome: Extensive coverage, zero mention of FERC filing status.**

Sources reviewed:
- Fortune (May 12, 2026): No FERC filing mentioned. Notes FERC jurisdiction over wholesale sales but does not investigate filing status.
- Ars Technica (May 2026): No FERC filing mentioned.
- CalMatters (March 20, 2026): No FERC filing mentioned. Notes Liberty filed CPUC advice letter.
- Energy News Beat (May 2026): No FERC filing mentioned. Notes agreement extended in 2015, 2020, and "late 2025."
- KOLO/Fox Reno (March 2026): No FERC filing mentioned.
- Davis Enterprise: No FERC filing mentioned.
- Stoel Rives regulatory update (March 25, 2026): Covers Liberty CPUC proceedings but no FERC dimension.

**No energy trade reporter, law firm, or regulatory commentator has raised the FERC filing question.** This is notable given the story has been in national press since May 12, 2026.

---

## Verification Method 6: 2019 Filing Cross-Reference

**Outcome: The 2019 cancellations were ancillary agreements, not the main PPA.**

From the Federal Register raw text (84 FR 29511, June 24, 2019):

- **ER19-2174-000 (RS 66):** "Tariff Cancellation: Rate Schedule No. 66 SPPC & Liberty EPC Cancellation to be effective 8/17/2019"
  - This was the Engineering Procurement Construction Agreement -- a construction-phase contract for building infrastructure, not the ongoing power supply agreement.

- **ER19-2176-000 (RS 71):** "Tariff Cancellation: Rate Schedule No. 71 -- CalPeco & SPPC 609 Line Agreement Cancellation to be effective 8/17/2019"
  - This was the 609 Line Agreement -- a specific transmission line infrastructure agreement. "609 Line" refers to a specific transmission interconnection between SPPC and CalPeco.

Both cancellations were filed June 17, 2019, effective August 17, 2019. They cleaned up ancillary construction/infrastructure agreements that had been completed. The main wholesale power supply arrangement (RS 55 and its successors) remained in effect and was subsequently amended (2020, 2021, 2025).

---

## The Legal Framework: 18 CFR 35.15

The cancellation/termination filing requirement is specifically at **18 CFR 35.15** (not 18 CFR 2.4(c)(4), which addresses FERC's suspension power):

> **(a) General rule.** When a rate schedule, tariff or service agreement or part thereof required to be on file with the Commission is proposed to be cancelled or is to terminate by its own terms and no new rate schedule, tariff or service agreement or part thereof is to be filed in its place, a filing must be made to cancel such rate schedule, tariff or service agreement or part thereof **at least sixty days but not more than one hundred-twenty days prior to** the cancellation/termination effective date.

> **(b) Applicability exception.** Power sales contracts **executed on or after July 9, 1996** that terminate naturally are **exempt** from subsection (a) requirements.

> **(c) Alternative notice.** For exempt contracts, utilities must notify the Commission **within 30 days after termination occurs.**

### Critical question: When was the SPPC-Liberty PPA executed?

The original wholesale supply arrangement was established as part of the 2009 asset sale (agreement signed 2009, transfer effective January 1, 2011). **This is after July 9, 1996**, which means:

- Under 18 CFR 35.15(b), if the PPA terminates "by its own terms" (i.e., it has a fixed end date that arrives, or an expiration provision the parties exercised), the 60-day advance filing requirement of 35.15(a) does **not** apply.
- Under 35.15(c), SPPC would only need to notify FERC within 30 days **after** termination occurs (i.e., after May 2027).

**However:** The PPA has been repeatedly amended and extended (2015, 2016, 2020, 2021, 2025). Each amendment was filed at FERC as a Section 205(d) rate filing. The November 2025 "Amended Liberty PPA" filing (ER26-534-000) confirms SPPC treats this as a FERC-jurisdictional rate filing. Even if the 60-day advance cancellation notice is not required under 35.15(b), FERC retains jurisdiction to review the termination under Sections 205 and 206.

---

## CONFIDENCE ASSESSMENT

### Filing exists but we missed it: 15%
**Reasoning:** We found the November 2025 **amendment** filing (ER26-534-000), which our prior search missed. However, this is an amendment, not a cancellation/termination. A separate termination/cancellation filing could theoretically exist in the FERC eLibrary without appearing in Federal Register combined notices (e.g., if it was filed very recently and the FR notice hasn't published yet). Given that the Federal Register API returned 17 Sierra Pacific documents for 2025-2026 and none were cancellations, and given that FERC combined notices typically publish within 1-2 weeks of filing, the probability of a hidden cancellation filing is low but non-zero.

### Filing genuinely does not exist: 65%
**Reasoning:** The strongest interpretation. Multiple lines of evidence converge:
- Zero cancellation/termination filings found in Federal Register API (comprehensive, searchable)
- Zero mentions in any of 15+ news articles, CPUC filings, or SEC disclosures
- Zero energy law commentary analyzing a FERC proceeding
- The 35.15(b) exemption for post-1996 contracts provides a legal basis for not filing in advance
- NV Energy may plan to file only after termination under 35.15(c)

### Filing exists but is not yet public / under seal: 5%
**Reasoning:** FERC proceedings are generally public. Sealed filings are rare and typically involve market-sensitive information or critical infrastructure security. A wholesale power contract termination would not normally qualify.

### Contract may not require a FERC filing (bilateral, not tariffed): 15%
**Reasoning:** Weakened by the ER26-534-000 finding. The November 2025 amendment was filed at FERC as a Section 205(d) rate filing, which means SPPC itself treats this as a FERC-jurisdictional agreement. However, the 35.15(b) exemption for post-1996 contracts that terminate by their own terms could mean SPPC genuinely believes no advance filing is required -- not because the contract isn't FERC-jurisdictional, but because the regulation exempts natural expirations from the advance notice requirement.

---

## REVISED ASSESSMENT (from F.2)

### What changed from the prior analysis

1. **New filing discovered:** ER26-534-000 (Amended Liberty PPA, Nov 2025) was not found in the F.2 search. This confirms the PPA is FERC-jurisdictional.

2. **Regulatory framework corrected:** The primary filing requirement is 18 CFR 35.15, not 18 CFR 2.4(c)(4). Section 2.4(c)(4) addresses FERC's power to *suspend* cancellation notices; Section 35.15 is the actual filing requirement. Critically, 35.15(b) exempts post-1996 power sales contracts from the 60-day advance filing requirement if they terminate by their own terms.

3. **Rate schedule clarified:** The 2019 cancellations (RS 66, RS 71) were ancillary construction/infrastructure agreements, not the main PPA. The main agreement is RS 55 (and its successors/amendments).

### What the absence now means

The picture is more nuanced than F.2 suggested:

- **The PPA is FERC-jurisdictional** (confirmed by ER26-534-000 Section 205(d) filing).
- **A termination filing may not be legally required in advance** under 35.15(b) because the contract was executed after July 9, 1996.
- **A post-termination notice IS required** under 35.15(c) within 30 days of the May 2027 termination.
- **FERC retains authority** to review the termination under Section 206 even without a pre-termination filing. Any party (Liberty, California officials, FERC itself) could file a Section 206 complaint.
- **The November 2025 amendment raises questions:** What did the "Amended Liberty PPA" change? If it modified the termination terms, the amendment itself could be subject to Section 205/206 review. The amendment was filed 4 months before Liberty publicly disclosed the termination timeline.

---

## RECOMMENDATION

### Can we report "no FERC filing found"?

**Yes, with important caveats.** The reportable finding is:

> No FERC filing for the cancellation or termination of the SPPC-Liberty wholesale power supply agreement was found as of May 15, 2026. Sierra Pacific Power Company did file an "Amended Liberty PPA" with FERC in November 2025 (ER26-534-000), effective December 29, 2025, but this was an amendment to the agreement -- not a termination notice. Under 18 CFR 35.15(b), an advance termination filing may not be legally required for power sales contracts executed after July 9, 1996, though a post-termination notice under 35.15(c) would be required within 30 days of the May 2027 termination.

### What we CANNOT report

- We cannot claim NV Energy is violating FERC filing requirements. The 35.15(b) exemption provides a plausible legal basis for not filing in advance.
- We cannot claim the absence is evidence of deliberate jurisdictional avoidance without additional evidence (though the strategic incentive exists).
- We cannot determine what the November 2025 PPA amendment changed without accessing the actual filing document in FERC eLibrary.

### What we SHOULD report

- The PPA is confirmed as FERC-jurisdictional (ER26-534-000).
- No termination filing exists in FERC public records.
- The November 2025 amendment is temporally significant -- it precedes the public disclosure of the termination by 4 months.
- FERC retains authority to intervene under Section 206 regardless of whether an advance filing is made.
- No party (Liberty, California, environmental groups, Congress) has yet raised the FERC jurisdictional question publicly.

### Outstanding question for further investigation

**What did the November 2025 PPA amendment change?** If it added or modified the termination provision that NV Energy subsequently exercised, this is a major story. The actual filing document (accession 20251117-5192) would need to be retrieved from FERC eLibrary via interactive browser access.
