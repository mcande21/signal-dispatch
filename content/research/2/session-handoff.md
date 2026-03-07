# Session Handoff: SD #2 Draft Phase

## Resume Command

```
/draft deep_dive --issue 2
```

## Context

Signal Dispatch Issue #2: Deep Dive on Kristi Noem fired as DHS Secretary. Research phase is complete. Drafting phase is next.

## What Was Completed

Full intelligence collection with war-room mode (4 parallel tracks):

1. **Web research** (Liara): 6 themes covering trigger events, Pretti shooting, $220M scandal, operational failures, enforcement record, counterarguments. Then deep follow-up on 3 investigative threads: Trump's role, lingering corruption, and LLC trail.

2. **USAspending** (targeted DHS queries): 8 API calls covering top DHS contracts, advertising/communications, detention/enforcement, FEMA, and vendor-specific searches for Safe America Media, People Who Think, Strategy Group.

3. **OSINT** (Federal Register): Empty results due to publication lag (firing was March 5, queries ran March 6).

4. **Prediction Markets**: No active markets found on this topic.

5. **Cross-track synthesis** (Liara): Political survival failure frame with procurement opacity finding.

6. **Orthogonal analysis** (Legion): Found three critical flaws -- temporal anomaly (pre-decided firing), verification gap (enforcement numbers unverified), and alternative hypothesis (corruption + operational failure explains more).

## Collaborative Thesis (Developed with Cooper)

The story isn't "good enforcer, bad politician." It's about a **shadow procurement network** operating inside DHS under emergency authority, with Corey Lewandowski as the operational hub connecting political operatives to federal contracts.

**The enforcement was real** -- $1.83B CSI Aviation deportation flights, $3.7B detention capacity. 675K removals are plausible based on spending.

**But corruption ran parallel** -- newly-formed LLCs, bypassed competitive bidding, Noem's PAC recipients getting federal dollars, Strategy Group CEO marrying DHS spokesperson during contract period.

**Trump knew** -- White House officials were involved in getting funds approved. "I never knew" is calculated distancing. Firing was pre-decided (simultaneous Mullin announcement proves it).

**The question for readers:** Does the corruption network survive Noem's departure?

## Approved Article Outline

**Title:** "Eight Days: Inside the Shadow Procurement Network That Brought Down DHS Secretary Kristi Noem"

**Analyst confidence:** Medium

### Section 1: Executive Summary (3-4 paragraphs)
- Thesis: shadow procurement network, not political survival failure
- Eight days from LLC formation to $62M contract
- Enforcement real ($3.78B). Corruption parallel ($248M).
- Forward-looking: does the network survive?

### Section 2: Structured Data -- Follow the Money
- The LLCs: Safe America Media, People Who Think, Strategy Group (full details)
- Procurement chain: emergency authority → bypassed bidding → connected operatives
- Enforcement apparatus: CSI Aviation, GEO Group, CoreCivic spending
- $99,999 contract pattern
- Actual USAspending contract numbers

### Section 3: Qualitative Intelligence -- The Collapse
- Operation Metro Surge / Minnesota escalation
- Pretti shooting timeline (six seconds -- narrative anchor)
- Advertising exposure (ProPublica)
- Congressional hearings (bipartisan hostility)
- Trump contradiction and distancing
- The firing (pre-decided)

### Section 4: Assessment -- Three Competing Frames
- Frame A: Political survival failure
- Frame B: Corruption exposure (our thesis)
- Frame C: Too effective, scapegoated
- Score each against observables
- Verification gap + silence of internal defenders

### Section 5: Probability Assessment (5 estimates)
1. Enforcement continuity under Mullin: **60%**
2. Mullin confirmed by April 15: **75%**
3. Federal charges from ad contracts by Dec 2026: **30%**
4. DHS ad spending drops >50% Q2 vs Q1: **70%**
5. ICE removals >700K in 2026: **20%**

### Section 6: Escalation/Resolution Indicators
- March 31 departure, Q2 USAspending data, Mullin hearing, DOJ/IG, litigation

### Section 7: Sources

## Key File Paths

| File | Purpose |
|------|---------|
| `content/research/2/brief.md` | Comprehensive research brief (905 lines, 40KB) |
| `content/research/2/web-research.md` | Web research findings |
| `content/research/2/synthesis.md` | Liara cross-track synthesis |
| `content/research/2/orthogonal.md` | Legion orthogonal analysis |
| `content/research/2/data/` | 11 archived raw data files |
| `src/paper/templates/deep_dive.md` | Article template |
| `config/persona.yaml` | Persona configuration |
| `docs/PERSONA.md` | Persona reference with examples |
| `docs/STYLE-GUIDE.md` | Writing style guide |
| `content/state/issues.json` | Issue tracker (issue #2, status: drafting) |
| `content/state/probabilities.json` | Probability state |

## Key Data Points for Quick Reference

**The LLCs:**
- Safe America Media LLC: formed Feb 6, 2025. First contract Feb 13 ($62.8M). Total $143-158M. Owner: Mike McElwain (GOP strategist).
- People Who Think LLC: $77-90M. Owner: Jay Connaughton (Trump 2016 media adviser).
- Strategy Group: CEO Ben Yoho married DHS spokesperson Tricia McLaughlin. Noem's PAC paid through Feb 2026.

**Lewandowski as hub:**
- "Special government employee" with contract approval authority
- Brought Yoho into Noem's orbit, worked with Connaughton
- Noem testified he didn't approve contracts. Records show he did. Perjury investigation called.

**Enforcement spending:**
- CSI Aviation deportation flights: $1.83B (4 contracts)
- GEO Group detention: $632M
- CoreCivic detention: $478M
- Akima detention: $240M
- Camp East Montana: $598M
- Combined enforcement: $3.78B

**Timeline:**
- Jan 2025: Noem takes office
- Feb 6: Safe America Media formed
- Feb 13: First contract ($62.8M) -- 8 days
- Dec 2025: Operation Metro Surge
- Jan 7, 2026: Renée Nicole Macklin Good killed
- Jan 24: Alex Pretti killed (10 shots in <5 seconds)
- Feb-Mar: ProPublica exposes Strategy Group
- Mar 3-4: Congressional hearings
- Mar 5: Trump fires Noem, announces Mullin simultaneously
- Mar 31: Noem departs

## Drafting Protocol Reminder

- Section-by-section with Cooper gating each section
- First-person singular ("I assess...")
- Lead with data, not opinion
- Specific numbers, not vague quantifiers
- Show methodology transparency
- Footnotes for depth and wit (rare, strategic)
- No emojis, no exclamation points, no hedge words
- Calm confidence throughout

## Output

Draft goes to: `content/drafts/2-deep_dive.md`
