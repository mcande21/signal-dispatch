# F.1 Legal/Regulatory Reconnaissance: NV Energy / Liberty Utilities / Data Center Power Redirect

**Track:** LEAD (Legal/Regulatory)
**Date:** 2026-05-15
**Issue:** SD #12
**Status:** First pass -- broad sweep to map legal landscape

---

## 1. Obligation to Serve

### What We Found

The "obligation to serve" (or "duty to serve") is a foundational principle of public utility law, rooted in English common law (common carrier doctrine) and codified in every U.S. state. The Energy Bar Association's seminal 1985 paper (21 Energy L.J. 179) identifies three core components:

1. **Duty to serve** all qualified persons within the service territory in a safe and adequate manner
2. **Obligation to maintain reasonable rates** for service
3. **Corollary right to serve** -- protection from unwarranted competition (the monopoly franchise)

The Vanderbilt Law Faculty publication (scholarship.law.vanderbilt.edu) traces this to the "regulatory compact": utilities receive a monopoly franchise in exchange for extraordinary service obligations, including serving unprofitable customers and providing advanced notice of disconnection.

**Key distinction -- retail vs. wholesale:**

- At the **retail** level, the duty to serve is well-established in every state statute. The Building Decarbonization Coalition's 50-state survey confirms every state has an OTS statute, though formulations vary from 10 words ("Every public utility shall furnish adequate, efficient, and reasonable service") to multi-section codes.

- At the **wholesale** level, the obligation is far more ambiguous. The EBA paper argues: "While a strong argument can be made that electric utilities do not have an obligation to serve wholesale customers under the Federal Power Act and can in fact abandon service upon the expiration or termination of a contract or service agreement, the present state of the law as administered by FERC does not allow for such a possibility without Commission approval."

- The 2025 EBA article (Jermyn, 46 Energy L.J. 491) updates this framework specifically for the data center era, noting the duty to serve "is not limitless" but "utilities must generally make all 'reasonable' extensions of service customers request, even when an individual extension may not be profitable."

### NV Energy's Classification

NV Energy consists of two PUCN-regulated investor-owned utilities: **Nevada Power Company** (southern Nevada) and **Sierra Pacific Power Company** (northern Nevada). Both conduct business as NV Energy. Acquired by **Berkshire Hathaway Energy** in December 2013 for $5.6 billion. PUCN regulates their service territories, rates, and resource planning. NV Energy serves approximately 1.4 million customers across a 46,000-square-mile service territory.

**Critical nuance:** NV Energy's duty to serve applies to customers *within its Nevada service territory*. Liberty Utilities' Lake Tahoe customers are *not* NV Energy retail customers -- they are **wholesale** customers purchasing through a contractual arrangement. This distinction is the legal hinge of the entire case.

### The NV Energy / Liberty Relationship

This is a **full-requirements wholesale power supply contract** dating to 2009, when NV Energy sold its California electric distribution assets to Liberty Utilities. The arrangement was always described as "temporary" -- intended to supply Liberty until it could secure independent power sources. The contract was extended in 2015, 2020, and late 2025. Liberty generates approximately 25% of its power from its own solar facilities in Nevada; the remaining 75% comes from NV Energy under this wholesale agreement.

**What needs deeper investigation:**
- The actual contract terms (is it a FERC-filed rate schedule or a bilateral agreement?)
- Whether the contract has a fixed expiration or requires notice of termination
- Whether FERC was involved in any extensions
- The 2009 asset sale agreement terms regarding power supply obligations

---

## 2. Electricity vs. Water Legal Framework

### What We Found

The legal distinction between electricity and water is less about statutory text (most state OTS statutes cover both) and more about three overlapping but distinct doctrines:

**Public Trust Doctrine:** Applies strongly to water but not electricity. Under public trust law (traced to Justinian's Institutes, 535 CE), water, navigable waterways, and wildlife are held in trust by the state for all people. California's *National Audubon Society v. Superior Court* (1983, "Mono Lake" case) is the landmark: the state has a continuing duty to protect trust resources. Some states extend this to all natural resources (Hawaii's constitution covers "all natural resources, including land, water, air, minerals and energy sources"), but most do not. A Michigan Journal of Environmental & Administrative Law article (Noel & Firestone, 2015) explicitly explores public trust implications for electricity production but concludes it's a "very little attention" area.

**Essential Service / Due Process:** The U.S. Supreme Court's *Jackson v. Metropolitan Edison Co.* (1974) is the key case. The Court ruled that a private utility terminating service is NOT state action triggering 14th Amendment due process protections -- even though electricity is "essential" and the utility is a monopoly. Justice Marshall dissented, arguing the utility's monopoly status and state regulation should make its actions attributable to the state. This creates a gap: electricity service termination by a private utility does not carry the same constitutional weight as a government action.

**Regulatory Framework:** Water utilities face additional constraints through the Safe Drinking Water Act (federal), public health codes (state/local), and the fact that water is a physical natural resource that cannot be easily substituted. Electricity can theoretically be sourced from multiple generators and delivered over shared transmission. This substitutability is what makes the NV Energy/Liberty situation legally possible but practically devastating -- Liberty *can* theoretically find another supplier, even though doing so in 12 months for 49,000 customers on an isolated grid is extremely difficult.

### Key Distinction Summary

| Factor | Water | Electricity |
|--------|-------|-------------|
| Public Trust Doctrine | Strong application | Minimal/emerging |
| Federal health mandates | Safe Drinking Water Act | None equivalent |
| Resource substitutability | Very low (physical delivery) | Higher (generator agnostic) |
| Common carrier treatment | Not common carrier | Not common carrier |
| State OTS statutes | Covered | Covered |
| Constitutional protection (Jackson) | Stronger argument | Ruled NOT state action |

**What needs deeper investigation:**
- Whether any state has extended public trust doctrine to electricity supply
- Whether the "essential service" doctrine has evolved post-Jackson in the AI/data center context
- California-specific utility obligations (Cal. Pub. Util. Code sections 761-788 are very strong on obligation to serve)

---

## 3. The NV Energy / Liberty Utilities Mechanism

### What We Found

**The specific sequence:**

1. **2009:** NV Energy sells California electric distribution assets to Liberty Utilities. Strikes a "temporary" full-requirements wholesale power supply agreement.
2. **2015:** Contract extended (Liberty had not secured independent supply).
3. **2020:** Contract extended again.
4. **Late 2025:** Contract extended one more time -- but NV Energy sets a firm end date of May 2027.
5. **March 2026:** Liberty files an advice letter with the CPUC seeking authorization for an expedited RFP process to find replacement power.
6. **April 2026:** South Lake Tahoe Mayor Cody Bass writes to CPUC expressing community concern. Sierra Club Tahoe Area Group and Tahoe Spark file protests calling for a full CPUC proceeding rather than expedited RFP.
7. **Summer 2026 (planned):** Liberty to issue formal RFP for replacement power.
8. **May 2027:** NV Energy supply ends; NV Energy's $4.2 billion Greenlink West transmission line expected online (cutting it close).

**Regulatory process findings:**

- **PUCN involvement:** Not directly visible in reporting. Since NV Energy is terminating a wholesale contract (not retail service), the PUCN's role is unclear. NV Energy's Integrated Resource Plan (filed with PUCN per NRS 704.741) is where data center load growth projections appear -- the PUCN approved this plan. But whether the PUCN specifically approved or reviewed the Liberty termination is an open question.

- **CPUC involvement:** Liberty is CPUC-regulated. The CPUC approves Liberty's rates and procurement. But as Fortune's reporting emphasizes: "The CPUC approves Liberty's rates and procurement requests, but it cannot order NV Energy to keep selling wholesale power or dictate how Nevada plans for data centers."

- **FERC involvement:** This is the jurisdictional gap. The wholesale sale from NV Energy (Nevada) to Liberty (serving California customers) is interstate wholesale commerce -- squarely within FERC jurisdiction under FPA Section 201. However, there is no reporting on any FERC filing or docket related to this termination. This is a critical gap.

**NV Energy's stated rationale:** Spokesperson Katie Jo Collier: "a planned transition for many years, not a reaction to recent developments." The company frames it as fulfilling the original 2009 understanding. But Liberty's own CPUC filing states NV Energy cited "data centers in the Tahoe-Reno Industrial Center area and northern Nevada transmission constraints" as reasons for ending service.

**The jurisdictional mess (per Fortune):** "No single regulator oversees the entire chain from power generation to customer bills. California residents pay rates approved by California state regulators, but the Liberty grid sits under NV Energy's authority and is fully reliant upon Nevada power transmission lines."

### Gaps -- What We Could Not Find

- **FERC docket:** No evidence found of a FERC filing for the termination of this wholesale agreement. Under 18 C.F.R. Section 2.4(c)(4), a notice of cancellation or termination must be filed with FERC before service can be terminated, even if the contract expires by its own terms. If NV Energy has not made this filing, that is significant.
- **The actual contract:** No public access to the terms of the NV Energy/Liberty wholesale agreement.
- **PUCN docket:** No specific PUCN proceeding found related to this termination.
- **CPUC advice letter number:** The specific CPUC filing was referenced but not linked in reporting.

---

## 4. FERC Jurisdiction

### What We Found

**Statutory framework:**

The Federal Power Act (16 U.S.C. Section 791a et seq.) gives FERC jurisdiction over:
- The transmission of electric energy in interstate commerce
- The sale of electric energy at wholesale in interstate commerce
- Facilities for such transmission or sale

FPA Section 201(d) defines "sale of electric energy at wholesale" as "a sale of electric energy to any person for resale." The NV Energy-to-Liberty sale is precisely this: NV Energy sells to Liberty, who resells to 49,000 retail customers.

**Key provisions for termination:**

- **Section 205(c):** Requires utilities providing FERC-jurisdictional service to file rate schedules and all contracts affecting rates.
- **Section 205(d):** No change to rates, charges, classification, or service may be made "except after sixty days' notice to the Commission and to the public."
- **18 C.F.R. Section 2.4(c)(4):** FERC regulations require that "a notice of cancellation or termination" be filed with the Commission, "whether the service is proposed to be cancelled or is to terminate by its own terms."

**FERC position on wholesale service termination (EBA paper):** "FERC has taken the position that service, once commenced, can only be abandoned pursuant to the filing of a change in rate schedule, subject to Commission review. In other words, FERC approval is required before service can be abandoned." However, the paper also argues there is "a very strong argument" that properly filed notices of termination, consistent with contract terms, terminate the service obligation at the end of the notice period unless FERC exercises Section 202(b) or Section 207 authority to order continuation.

**Section 202(b) -- Interconnection orders:** FERC can order interconnection if it determines it is "in the public interest" and will not "impair [the utility's] ability to render adequate service." The *El Paso Electric v. FERC* (5th Cir. 2000) case involved exactly this: Las Cruces, New Mexico sought to replace El Paso Electric as retail provider, and FERC ordered El Paso to sell wholesale power temporarily under Section 202(b). The court affirmed in part but required an evidentiary hearing on the impacts.

**Relevance to NV Energy/Liberty:** FERC could theoretically:
1. Reject or delay the termination if NV Energy files under Section 205
2. Initiate a Section 206 proceeding on its own motion if it finds the termination "unjust and unreasonable"
3. Order continued service under Section 202(b) if public interest warrants it

**But:** No reporting suggests FERC has been engaged at all. This could mean: (a) no FERC filing has been made, (b) the contract allows termination without FERC review, or (c) nobody has complained to FERC yet.

**Recent FERC context:**
- April 2026: PUCN approved NV Energy's plan to join CAISO's Extended Day-Ahead Market (EDAM) by fall 2028. This may affect Liberty's options.
- May 2026: FERC Chairman Laura Swett stated PJM may be "too big to function" and faces a "serious legitimacy crisis" partly driven by data center demand.
- FERC is actively grappling with data center/grid conflicts via the PJM behind-the-meter proceedings (Talen-Amazon Susquehanna case).

---

## 5. Data Center Incentive Structures

### What We Found

**Nevada's data center tax abatement program (NRS 360.754):**

The Governor's Office of Economic Development (GOED) administers generous tax abatements:

**10-year abatements:**
- Personal property tax: 75% abatement
- Sales and use tax: reduced to 2%
- Requirements: 10 full-time Nevada employees, 100% statewide average wage, $25M capital investment within 5 years

**20-year abatements:**
- Same tax reductions
- Requirements: 50 full-time Nevada employees, 100% statewide average wage, $100M capital investment within 5 years

**Additional requirements:** 12 weeks paid family/medical leave for 50+ employee operations, 50% Nevada-resident construction workforce, medical insurance plan (65% premium coverage).

**NV Energy's own marketing:** NV Energy publishes a data center brochure advertising Nevada's incentive package, and has created a "Clean Transition Tariff" specifically designed for large customers (minimum 5 MW) with long-term contract periods and pricing designed to fully cover costs of new renewable resources.

**Nevada's broader attractiveness:** No corporate income tax, inexpensive land, tax breaks. NV Energy currently requires data center developers to fund their own infrastructure and energy requirements.

**The 704B law (NRS 704B):** Passed in 2001, allows large-load businesses to leave NV Energy and purchase power from alternative providers. Used by MGM Resorts, Switch, Wynn Resorts, Caesars, Peppermill Reno. In 2019, SB547 reformed the process to require departing companies to prove exit is "in the public interest" (stricter than the prior "not contrary to public interest" standard).

**Behind-the-meter generation:** A Northern Nevada data center (Peru Ridge/South Valley at TRIC) applied in April 2026 to operate temporary 350 MW natural gas power plants "behind the meter" because NV Energy cannot serve them for 2-3 years. The Sierra Club warned this "locks the public out of the process" because state energy regulators would have reduced oversight. These facilities would not comply with Nevada's renewable portfolio standard.

**Key data points:**
- Data centers consumed 22% of Nevada's total electricity in 2024
- Projected to hit 35% by 2030
- 12 data center projects in Northern Nevada could add 5,900 MW by 2033
- 75% of NV Energy's major-project load growth is attributed to data centers
- NV Energy needs 47% more energy statewide than forecast just two years ago
- NV Energy's northern Nevada demand expected to double from ~2,000 MW to ~4,000 MW in 8-10 years

**SWEEP Report (Southwest Energy Efficiency Project, March 2025):** Recommends states NOT provide economic development incentives to data centers, and instead require them to: (1) purchase 100% renewable energy, (2) pay full costs of new generation and transmission, (3) report annually on energy consumption and renewable percentages.

### What Needs Deeper Investigation

- Whether data center customers receive any preferential treatment in NV Energy's queue or resource allocation beyond the tax abatements
- Whether the NV Energy Integrated Resource Plan specifically trades off Liberty's wholesale supply against data center load growth
- How much of the $4.2B Greenlink West transmission project cost is borne by existing residential customers vs. data center customers (reporting suggests ~70% borne by Southern Nevada ratepayers)

---

## 6. Precedent

### What We Found

**Otter Tail Power Co. v. United States, 410 U.S. 366 (1973):** The closest structural precedent. Otter Tail, a retail utility, refused to sell wholesale power to municipal systems when its retail franchises expired -- trying to maintain its monopoly. The Supreme Court upheld the District Court's finding that this violated Section 2 of the Sherman Act (monopolization). The decree enjoined Otter Tail from refusing to sell wholesale or wheel power. **Key difference from NV Energy:** Otter Tail was refusing to sell to *preserve its retail monopoly*. NV Energy is refusing to continue selling because it claims it *lacks capacity*. The anticompetitive motive is different, but the structural question -- can a utility cut off a wholesale customer -- is the same.

**El Paso Electric Co. v. FERC, 201 F.3d 667 (5th Cir. 2000):** The City of Las Cruces, NM wanted to replace El Paso Electric as retail provider for 30,000 customers. Filed under FPA Section 202(b) for FERC to order temporary wholesale sales. FERC granted the request; the 5th Circuit affirmed in part. **Relevance:** Demonstrates FERC can compel wholesale sales in the public interest. But the case involved a city *choosing* to municipalize, not being cut off by its supplier.

**Dakota Energy Cooperative / Marlboro Electric Cooperative (2022):** Courts dismissed distribution cooperatives' attempts to exit long-term wholesale power supply contracts (running through 2075 and 2058 respectively). The courts held the contracts were "unambiguous" and didn't allow early exit. **Relevance:** Shows that long-term wholesale supply contracts are enforceable. The flip side -- can the *supplier* exit? -- is less settled.

**Wabash Valley Power / Tipmont (FERC 2020):** FERC proceeding involving a distribution cooperative seeking to terminate its all-requirements wholesale contract with its G&T cooperative. FERC found the buyout terms needed to be "just and reasonable" and set the matter for hearing. **Relevance:** FERC treats wholesale contract termination as requiring its review, even between cooperatives.

**Talen-Amazon Susquehanna (2024-2025):** FERC rejected an amended interconnection agreement that would have expanded behind-the-meter power use for Amazon data centers at the Susquehanna nuclear plant. FERC cited reliability and cost concerns for other customers. **Relevance:** Establishes that FERC is willing to reject arrangements that benefit data centers at the expense of grid reliability and other customers.

**PJM / Maryland OPC Complaint (May 2026):** Maryland Office of People's Counsel filed at FERC arguing PJM's cost allocation rules unfairly assign ~$1.6 billion in data-center-driven transmission costs to Maryland ratepayers over the next decade. **Relevance:** The cost-shifting argument -- data centers imposing costs on residential customers -- is gaining formal legal traction.

### What We Did NOT Find

- **No direct precedent** for a utility terminating a wholesale supply agreement specifically to redirect capacity to industrial (data center) customers. This appears to be genuinely novel.
- No case where a wholesale customer was cut off and FERC intervened to order continuation specifically because the supplier wanted to serve other customers instead.

---

## RECOMMENDED DRILL-DOWN TARGETS

Based on this first pass, the following threads are most promising for F.2/F.3 investigation:

### Thread 1: FERC Filing Status (HIGHEST PRIORITY)
**Why:** Under 18 C.F.R. 2.4(c)(4), NV Energy is required to file notice of termination with FERC for any wholesale service cancellation. If no filing exists, this is a significant regulatory gap -- or potential violation. If a filing does exist, it would contain NV Energy's legal rationale and any conditions imposed by FERC.
**What to look for:** Search FERC's eLibrary (elibrary.ferc.gov) for any filings by NV Energy (Sierra Pacific Power Company or Nevada Power Company) related to Liberty Utilities, termination of wholesale service, or the Lake Tahoe supply agreement. Also search for any Section 206 complaints filed by third parties.

### Thread 2: The Actual Wholesale Contract Terms
**Why:** Everything depends on whether the NV Energy/Liberty wholesale agreement has a fixed expiration date, requires notice of termination, includes capacity reservation clauses, or contains force majeure provisions related to load growth. If NV Energy is terminating a contract that has already expired on its own terms, the legal posture is very different from terminating an ongoing obligation.
**What to look for:** Liberty's March 2026 CPUC advice letter should reference the contract. The CPUC proceeding may have filings with contract details. Also check Liberty's parent company (Algonquin Power & Utilities Corp) SEC filings.

### Thread 3: NV Energy's Integrated Resource Plan and Data Center Capacity Allocation
**Why:** NV Energy's 2024 IRP (filed with PUCN) is where the tradeoff between existing wholesale obligations and new data center load would be documented. If the IRP explicitly allocates capacity away from Liberty toward data centers, this is the smoking gun for the "redirect" narrative. Sierra Club expert testimony filed with Nevada regulators (reviewed by Fortune) identified that 75% of major-project load growth is attributed to data centers.
**What to look for:** PUCN docket for NV Energy's 2024 IRP. Sierra Club testimony. Any PUCN conditions or orders related to the Liberty wholesale arrangement.

### Thread 4: Constitutional / Civil Rights Angle
**Why:** *Jackson v. Metropolitan Edison* (1974) held that private utility service termination is not state action. But that was a single retail customer. Cutting off 49,000 customers to redirect power to corporate data centers may present a different factual pattern -- especially if the decision involves state-approved resource planning (the IRP) and state-granted tax incentives (NRS 360.754). There may be an environmental justice or disparate impact argument if the affected community has demographic characteristics that trigger heightened scrutiny.
**What to look for:** Environmental justice analysis of the Lake Tahoe community vs. the TRIC data center corridor. Any legal scholarship updating Jackson for the infrastructure-scarcity era.

### Thread 5: NV Energy's EDAM Entry and Market Structure Shift
**Why:** In April 2026, PUCN approved NV Energy joining CAISO's Extended Day-Ahead Market by fall 2028. If Liberty could access EDAM, it might have options beyond bilateral contracts. But the timing (2028) is after the May 2027 deadline. This thread explores whether market restructuring could provide a structural solution.
**What to look for:** PUCN order approving EDAM entry, conditions related to existing wholesale obligations, whether Liberty Utilities can participate in EDAM as a CAISO-adjacent entity.

---

## SOURCE INDEX

| Source | Type | URL | Relevance |
|--------|------|-----|-----------|
| Ars Technica (2026-05-14) | News | arstechnica.com | Primary reporting on NV Energy/Liberty |
| Fortune (2026-05-12) | News | fortune.com | Original investigative reporting (most cited) |
| Electrek (2026-05-13) | News | electrek.co | Data center demand numbers, grid context |
| Energy News Beat (2026-05-14) | News | energynewsbeat.co | Most detailed timeline reconstruction |
| ERITV News (2026-05-12) | News | eritvnews.com | Full Fortune synthesis with regulatory detail |
| Fox Reno (2026-04-01) | News | foxreno.com | Early Liberty Utilities statement, Greenlink detail |
| EBA Journal (1985) | Legal scholarship | eba-net.org | Obligation to serve at wholesale under FPA |
| EBA Journal (Jermyn, 2025) | Legal scholarship | eba-net.org | Updated duty to serve for data center era |
| Vanderbilt Law | Legal scholarship | scholarship.law.vanderbilt.edu | Duty to serve in retail competition context |
| Building Decarb Coalition | Policy | buildingdecarb.org | 50-state OTS statute survey |
| 16 U.S.C. 824q | Federal statute | law.cornell.edu | Native load service obligation |
| PJM/FERC Fact Sheet | Regulatory | pjm.com | Sections 205/206 framework |
| FERC v. EPSA (2016) | Supreme Court | law.cornell.edu | FERC wholesale jurisdiction boundaries |
| Otter Tail Power (1973) | Supreme Court | law.cornell.edu | Antitrust/refusal to wholesale |
| Jackson v. Met Edison (1974) | Supreme Court | loc.gov | Essential service / state action |
| El Paso Electric v. FERC (2000) | 5th Circuit | justia.com | FERC compelled wholesale sales |
| NV GOED Data Center Program | State government | goed.nv.gov | Tax abatement details, NRS 360.754 |
| NRS 704B | State statute | leg.state.nv.us | 704B exit law for large customers |
| PUCN | State regulator | puc.nv.gov | NV Energy classification, EDAM approval |
| NV Energy SEC Filing (2014) | Corporate | sec.gov | Berkshire Hathaway acquisition, utility structure |
| SWEEP Report (2025) | Policy | swenergy.org | Data center energy policy recommendations |
| Nevada Independent (2026-04-29) | News | thenevadaindependent.com | Behind-the-meter gas plants at TRIC |
| Simcore Partners (2026-01-29) | Analysis | simcorepartners.com | PJM behind-the-meter/co-location analysis |
| Data Center Frontier (2026-03-12) | Industry | datacenterfrontier.com | PJM BTMG reform for data centers |
| APPA / Maryland OPC (2026-05-11) | Regulatory | publicpower.org | FERC complaint on data center cost shifting |
| JD Supra (2026-05-08) | Legal news | jdsupra.com | PUCN approves NV Energy EDAM entry |
| Utility Dive (2026-05-13) | Industry | utilitydive.com | FERC Chairman Swett on PJM crisis |
| Energy Central (2024-12-06) | Industry | energycentral.com | Obligation to serve vs data center loads |
| Utility Dive (2022-04-20) | Industry | utilitydive.com | Dakota Energy/Marlboro co-op contract cases |
