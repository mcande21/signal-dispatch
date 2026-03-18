---
name: draft
description: Collaborative drafting of a Signal Dispatch newsletter issue from research brief
version: 1.0.0
---

# `/draft` -- Collaborative Drafting

*"Here's the recipe, not just the meal."*

Collaborative writing phase. Cooper and Shepard draft together using research artifacts and persona voice. This is NOT agent-generated content -- it's human-AI collaborative writing where Shepard proposes sections based on research data and Cooper reviews, modifies, and approves.

## Invocation

```bash
/draft weekly_brief --issue {number}
/draft breaking_alert --issue {number}
/draft deep_dive --issue {number}
```

## Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| type | positional | Yes | Content type: `weekly_brief`, `breaking_alert`, or `deep_dive` |
| `--issue` | flag | Yes | Issue number (e.g., `--issue 001`) |

## Prerequisites

**Must exist before starting:**
- `content/research/{issue-number}/brief.md` -- Research phase must be complete and Cooper-approved
- Research artifacts (data snapshots, web research notes) in research directory

**Files to read before drafting:**
1. `content/research/{issue-number}/brief.md` -- The research foundation
2. `src/paper/templates/{type}.md` -- Template for selected content type
3. `config/persona.yaml` -- Voice configuration
4. `docs/PERSONA.md` -- Complete persona guide
5. `docs/STYLE-GUIDE.md` -- Writing rules and conventions
6. `content/state/probabilities.json` -- Tracked probability state (for Step 0 commitment protocol)
7. `content/research/{issue-number}/delta_summary.md` -- Delta summary from intel phase (for Step 0, if exists)

## Template Selection

| Content Type | Template | Framing |
|--------------|----------|---------|
| `weekly_brief` | `src/paper/templates/weekly_brief.md` | Core product. Data synthesis + probability table anchor + market context. Opens with what moved. |
| `breaking_alert` | `src/paper/templates/breaking_alert.md` | Time-sensitive signal. Opens with source + timestamp + data point. Urgency from data, not emotion. Same depth, different pace. |
| `deep_dive` | `src/paper/templates/deep_dive.md` | Comprehensive single-topic analysis. Executive summary first. Structured data is the differentiator. Probability assessment with full basis chain. |

## Drafting Protocol

### Step 0: Probability Commitment

**Runs before any drafting begins. Skip if no tracked probabilities exist OR if no `delta_summary.md` exists for this issue.**

1. Read `content/state/probabilities.json` for all currently tracked outcomes and their current values
2. Read `content/research/{issue}/delta_summary.md` for what moved since the last issue
3. For each tracked outcome, present to Cooper:
   - The event description
   - Current probability and when it was last revised
   - Relevant deltas from the summary that touch this outcome (by cluster or source)
4. Wait for Cooper to commit his revised number for each outcome -- he goes first, based on what he saw in the delta summary
5. After Cooper commits, Shepard may share calibration context:
   - How similar delta patterns have correlated with past revisions (if history supports it)
   - Whether Cooper's revision is within or outside the range of historical adjustments for similar signal magnitudes
   - Frame this as a learning observation, not a correction or recommendation
6. Cooper may adjust his committed number after seeing calibration context, or hold it -- his call
7. Record final values in `content/state/probabilities.json` using the extended history schema (see below)

**The tone here is collaborative, not procedural.** Shepard is thinking through the evidence with Cooper, not running him through a checklist.

#### Anti-anchoring rules

- Do NOT suggest probability revision numbers before Cooper commits his
- Do NOT present "the system suggests..." or "based on the data, X% seems appropriate" language
- Present raw deltas and let Cooper form his own judgment
- Calibration context is shown AFTER commitment as a learning tool, not a prior
- Cooper can always override -- this is editorial judgment, not model output

#### Extended history schema

When recording a revision under this protocol, history entries take additional optional fields:

```json
{
  "date": "2026-03-17",
  "probability": 0.45,
  "issue": 4,
  "note": "...",
  "cooper_initial": 0.45,
  "calibration_shown": "Similar OONI drop in Jan 2026 correlated with +8-12pp upward revision. Cooper's +10pp is within that range.",
  "delta_cluster": ["iran-internet", "ooni-measurement-count"]
}
```

Fields:
- `cooper_initial` -- The number Cooper committed before seeing calibration context. Omit if Cooper did not revise (probability unchanged).
- `calibration_shown` -- Free-text summary of what historical context was shared. Omit if no calibration context was available.
- `delta_cluster` -- Array of delta cluster IDs or source names that informed this revision. Omit if unclear.

**Existing history entries without these fields are valid.** They predate the protocol. New entries generated under this protocol should include all three where applicable.

---

### Step 1: Propose Outline

Shepard reads template and research brief. Proposes section-by-section outline to Cooper:
- What each section will cover
- Key data points to include per section
- Probability updates that map to sections
- Estimated depth per section

**Cooper reviews and approves or redirects before drafting begins.**

### Step 2: Section-by-Section Drafting

For each section in the template:

1. Shepard drafts content based on:
   - Research brief data (structured feeds + web synthesis)
   - Persona voice (PERSONA.md guidelines)
   - Style guide rules (STYLE-GUIDE.md)
   - Probability format (see below)
   - Template structure for this content type

2. Cooper reviews the section:
   - Approves as-is
   - Requests modifications
   - Redirects approach

3. Iterate until section approved

**No section proceeds until Cooper approves.** This is collaborative writing, not sequential generation.

### Step 3: Compile Complete Draft

After all sections approved:
1. Assemble sections into complete draft
2. Verify all template sections filled
3. Cross-check probability format consistency
4. Verify source citations follow style guide
5. Save to output location

## Probability Update Format

### Updated Estimate (with Prior)

```
**Updated assessment:** {Event description}
- Prior: {X}% ({date of prior assessment})
- New data: {specific data point that changed assessment}
- Updated: {Y}%
- Change: {+/-Z} percentage points
- Resolution: {resolution criteria} by {date}
```

**Example:**
```
**Updated assessment:** Coordinated internet shutdown in Iran
- Prior: 35% (2026-02-19)
- New data: OONI measurement count dropped to 47/hr (baseline: 1,400/hr)
- Updated: 72%
- Change: +37 percentage points
- Resolution: Nationwide OONI measurement count below 200/hr for 12+ consecutive hours by 2026-03-31
```

### New Prediction (no Prior)

```
**New assessment:** {Event description}
- Initial: {X}%
- Basis: {data and reasoning}
- Resolution: {resolution criteria} by {date}
```

**Example:**
```
**New assessment:** US sanctions expansion targeting Iranian petrochemical exports
- Initial: 68%
- Basis: USAspending.gov shows 3 new contract modifications for maritime interdiction equipment ($47M total), OFAC update cycle historically precedes expansion by 14-21 days
- Resolution: New OFAC designations affecting petrochemical sector announced by 2026-04-15
```

## Voice Checklist (from PERSONA.md)

Every section must satisfy these criteria:

- [ ] First-person singular ("I assess..." not "we assess" or "it is assessed")
- [ ] Lead with data, not opinion (data → analysis, not claim → support)
- [ ] Active voice in analysis sections
- [ ] Specific numbers, not vague quantifiers ("72%" not "likely", "47/hr" not "significantly lower")
- [ ] "I trade this" disclosure where relevant to content type
- [ ] Footnotes for methodology depth and wit (rare, strategic)
- [ ] No emojis anywhere
- [ ] No exclamation points in analysis sections
- [ ] No hedge words ("somewhat," "arguably," "perhaps")
- [ ] No doomsday language or fear-mongering
- [ ] Calm confidence throughout

## Content Type Specific Notes

### weekly_brief

**Opening signature:** "Here's what moved this cycle:" or "Three signals shifted simultaneously:" -- lead with what changed.

**Probability table is the anchor.** Every active tracking event gets updated. Format:
```
| Event | Prior | Current | Δ | Confidence |
|-------|-------|---------|---|------------|
| {Event} | X% | Y% | +/-Z | High/Med/Low |
```

**What to Watch section** = forward-looking triggers. What specific data changes would move assessments. Include exact thresholds where possible:
- "OONI measurement count sustained above 1,000/hr for 48 hours"
- "Bonbast spread compresses below 10%"
- "EIA reports OPEC spare capacity below 2.5M bbl/day"

**Data Appendix (paid tier):** Raw numbers, methodology notes, extended source citations. This is what justifies "here's the recipe."

### breaking_alert

**Open with the signal:** Source, timestamp, data point. No preamble.

Good: "OONI measurement count dropped below 200/hr at 2026-03-05T14:22 UTC."
Bad: "An interesting development occurred today in Iranian internet infrastructure..."

**"What Happened" = factual, 2-3 paragraphs max.** Describe the data change. No analysis yet.

**"What It Means" = analysis with probability impact.** This is where assessment happens. Include probability update using standard format.

**Urgency from data, not emotional language.** The numbers carry weight. Don't add "BREAKING" or "URGENT" labels. The alert format itself signals urgency.

**Same depth. Different pace, not different rigor.** Breaking alerts are shorter but maintain full methodology transparency -- show basis, cite sources, state resolution criteria.

### deep_dive

**Executive summary first.** Busy readers get conclusion upfront. 3-4 paragraphs max:
- What the question is
- What the data shows
- What I assess
- What it means for markets

**Structured data section = the differentiator.** This is what sets Signal Dispatch apart. Walk through each OSINT feed:
- What it measures
- Current reading vs baseline
- Historical context
- Significance

**Qualitative intelligence = web research synthesis.** Connect structured data to broader context. News sources, think tank analysis, academic work. Always cited.

**Probability assessment = formal with full basis chain.** For deep dives, show the reasoning tree:
- Base rate (if applicable)
- Signal 1 → updates to X%
- Signal 2 → updates to Y%
- Signal 3 → updates to Z%
- Final assessment with confidence interval

**Escalation/resolution indicators = what changes the assessment.** Specific triggers that would move probability up or down. Include thresholds where possible.

## Output

**Draft file location:**
```
content/drafts/{issue-number}-{type}.md
```

**Examples:**
- `content/drafts/001-weekly_brief.md`
- `content/drafts/002-breaking_alert.md`
- `content/drafts/003-deep_dive.md`

**Draft must include:**
- All sections from template filled with research-backed content
- Every probability estimate formatted per update format (with prior OR as new assessment)
- Source citations following style guide conventions (source + timestamp)
- Resolution criteria for every prediction
- Footnotes where methodology depth or wit is appropriate
- No placeholder text or TK markers

## Anti-Patterns

**Don't let EDI generate the draft autonomously.**
This is Shepard + Cooper collaborative writing. Shepard proposes sections based on research data, Cooper reviews and modifies. Not: "EDI, write the draft and return when done."

**Don't skip probability format.**
Every estimate needs: number + basis + resolution criteria + prior (if updating). No "I assess this is likely" -- that's not a probability.

**Don't use vague language.**
"Elevated" needs a number. "Significant" needs quantification. "Concerning" is emotional framing, not analysis. The style guide exists for a reason.

**Don't break persona voice.**
If the writing feels generic, AI-polished, or institutional-bland, read PERSONA.md and redraft. The voice is methodological rigor + skin-in-the-game + calm confidence. Not corporate newsletter voice.

**Don't draft without reading research brief thoroughly.**
The research phase created structured artifacts. Use them. If you find yourself making up context or guessing at data points, stop and return to the research brief.

**Don't proceed without Cooper approval between sections.**
This is not a "generate everything and present at end" workflow. Section-by-section review catches drift early.

## Workflow Summary

```
/draft {type} --issue {number}
    ↓
Read prerequisites (research brief, template, persona, style guide)
    ↓
[If probabilities.json + delta_summary.md both exist]
Step 0: Probability Commitment
    - Present each tracked outcome + relevant deltas to Cooper
    - Cooper commits revised numbers
    - Shepard shares calibration context (after commitment)
    - Record final values with extended history schema
    ↓
Step 1: Propose section outline to Cooper
    ↓
Cooper approves or redirects
    ↓
For each section:
    - Shepard drafts based on research + persona + style
    - Cooper reviews
    - Iterate until approved
    ↓
Compile complete draft
    ↓
Save to content/drafts/{issue-number}-{type}.md
    ↓
Report completion + next step (editing phase)
```

---

*Drafting is where research becomes readable intelligence. The data is already collected. The analysis is already done. This phase translates structured artifacts into the Signal Dispatch voice.*
