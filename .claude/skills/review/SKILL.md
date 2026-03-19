---
name: review
description: Editorial review of a Signal Dispatch draft -- style, accuracy, calibration, persona consistency
version: 1.0.0
---

# `/review` -- Editorial Review

*"Edge requires honesty."*

Quality assurance before publication. Six-pass editorial review ensuring style guide compliance, fact verification, probability calibration, and persona consistency.

## Purpose

Reviews a Signal Dispatch draft through five specialized passes:
- **Style Guide Compliance** (Tali) -- Word choice, structure, format against docs/STYLE-GUIDE.md
- **Fact Verification** (Shepard) -- Data accuracy against research brief
- **Probability Format Validation** (Shepard) -- Completeness of probability estimates
- **Calibration Cross-Check** (Shepard) -- Probability update consistency and staging
- **Persona Consistency** (Kelly) -- Voice adherence to Data-Driven Practitioner archetype

This is the final gate before publication. Editorial integrity protects calibration credibility. One wrong number undermines the brand.

## Invocation

```bash
/review --issue <number>
```

## Arguments

| Argument | Required | Description | Example |
|----------|----------|-------------|---------|
| `--issue` | Yes | Issue number | `--issue 003` |

## Prerequisites

Before running `/review`, verify these files exist:

1. **Draft:** `content/drafts/{issue-number}-{type}.md`
   - {type} is one of: weekly_brief, breaking_alert, deep_dive
   - File must be complete (not stub or outline)

2. **Research brief:** `content/research/{issue-number}/brief.md`
   - Contains source data for all claims in draft
   - Has timestamped citations for verification

3. **Probability state:** `content/state/probabilities.json`
   - Tracks all active probability estimates
   - Contains priors for comparison

If any prerequisite is missing, `/review` will error. Use `/intel` to create the research brief first.

## Review Protocol -- Five Passes

### Pass 1: Style Guide Compliance (Tali)

**Purpose:** Mechanical adherence to Signal Dispatch style rules. Tali is thorough and detail-oriented -- ideal for systematic rule-checking.

**What Tali reviews:**

**Word Choice:**
- "I assess" (not "I think" or "I believe")
- "probability" (not "chance" or "likelihood")
- "signal" (not "indicator" or "sign")
- "data shows" (not "data suggests")
- "I trade this" (not "I have a position")
- "methodology" (not "approach" or "method")
- "calibration" (not "accuracy")
- "resolution criteria" (not "how we'll know")
- Specific numbers over vague quantifiers

**Avoided Words:**
- "Breaking" (unless genuinely time-sensitive)
- "Shocking" / "stunning" / "explosive"
- "Sources say" (we use open sources -- cite them)
- "Experts believe" (which experts? cite them)
- "Could" / "might" / "may" without probability
- "Significant" without quantification
- Passive voice in analysis sections
- Hedge words: "somewhat," "arguably," "perhaps"

**Never Allowed:**
- "BREAKING" in all caps
- Exclamation points in analysis
- Rhetorical questions as clickbait
- "You won't believe..."
- Political labels as shorthand (use specific policy positions)
- "My sources" or "insider knowledge"
- Emojis in analysis

**Sentence Structure:**
- Leads with data ("Y data shows X" not "I believe X because Y")
- Active voice for analysis ("I find" not "it was found")
- One idea per paragraph
- Short sentences for impact, long sentences for methodology

**Probability Format:**
- Has specific number (not "likely")
- Has stated basis ("based on X, Y, Z")
- Has prior when updating ("Updated from 45% to 65%")
- Has resolution criteria ("Resolves YES if X by [date]")
- Confidence tier matches language (see style guide table)

**Citations:**
- OSINT: Source name + timestamp ("OONI (2026-03-05T14:22 UTC)")
- Markets: Platform + contract + price + timestamp ("Kalshi: Iran Nuclear Deal by 2027 @ $0.095 (2026-03-05)")
- News: Publication + date, link in footnote
- No anonymous sources

**Formatting:**
- Clean header hierarchy (H1 title, H2 sections, H3 subsections)
- **Bold** for key data points and probability numbers
- *Italics* for publication names and direct quotes
- Footnotes for methodology detail and wit
- No emojis, no all-caps except acronyms (OONI, EIA, IRGC)

**Dispatch template:**

```
Task(
  subagent_type: "tali",
  prompt: "Editorial style review for Signal Dispatch issue #{issue-number}.

Read these files:
- Draft: /path/to/home/projects/signal-dispatch/content/drafts/{issue-number}-{type}.md
- Style guide: /path/to/home/projects/signal-dispatch/docs/STYLE-GUIDE.md

Review the draft against EVERY rule in the style guide. Check:
- Word choice (assess not think, probability not chance, etc.)
- Avoided words (breaking, shocking, sources say, hedge words)
- Never-allowed patterns (all-caps, exclamation points, rhetorical questions, emojis)
- Sentence structure (leads with data, active voice, one idea per paragraph)
- Probability format (number + basis + prior + resolution criteria)
- Citation format (source + timestamp for OSINT, platform + contract + price for markets)
- Formatting (headers, bold/italics usage, footnotes, no emojis)

For EACH violation found, report:
1. Line/location in draft
2. Rule violated (reference style guide section)
3. Current text
4. Suggested fix

Categorize violations:
- **Critical:** Must fix (wrong probability format, missing citations, passive analysis voice)
- **Important:** Should fix (word choice, hedge words, structure issues)
- **Minor:** Nice to fix (formatting consistency, footnote opportunities)

Report format:
- PASS (no violations) or NEEDS WORK (list violations by category)
- Violation count by severity

Be thorough. This is the final editorial gate before publication.",
  description: "Style review SD #{issue-number}",
  model: "sonnet"
)
```

### Pass 2: Fact Verification (Shepard)

**Purpose:** Ensure every data claim in the draft matches the research brief. Even small discrepancies destroy calibration credibility.

**What Shepard verifies:**

Read draft and research brief side by side. For every data claim:

**Numbers:**
- Does the number match research brief exactly?
- Is the baseline context correct?
- Are percentage changes calculated correctly?
- Are dates and timestamps accurate?

**Source Citations:**
- Is the source name correct?
- Is the timestamp format correct (YYYY-MM-DDTHH:MM UTC)?
- Does the citation match the research brief?
- Are prediction market prices and dates accurate?

**Context:**
- Is the baseline stated correctly?
- Are historical comparisons accurate?
- Are "X of the last Y times" patterns correct?

**Workflow:**

1. Open draft: `content/drafts/{issue-number}-{type}.md`
2. Open research brief: `content/research/{issue-number}/brief.md`
3. Extract every data claim from draft
4. Verify each claim against research brief
5. Flag discrepancies with:
   - Location in draft
   - What draft says
   - What research brief says
   - Severity (critical if wrong number/date, important if wrong context)

**Report format:**

```markdown
## Fact Verification: SD Issue #{issue-number}

### Critical Issues (wrong numbers/dates)
- [list with location, discrepancy, correct value]

### Important Issues (wrong context/baselines)
- [list with location, discrepancy, correct value]

### Verified Claims: {count}
### Discrepancies: {count}

Result: PASS / NEEDS WORK
```

If discrepancies exist, NEEDS WORK. No exceptions.

### Pass 3: Probability Format Validation (Shepard)

**Purpose:** Verify every probability estimate meets completeness requirements. Incomplete estimates undermine calibration tracking.

**What Shepard validates:**

For every probability estimate in the draft, check:

**Required Elements:**
- [ ] Specific number ("65%" not "likely")
- [ ] Stated basis ("based on X, Y, Z signals")
- [ ] Resolution criteria ("Resolves YES if...")
- [ ] Resolution date ("...by 2026-06-30")

**For Updates (when revising existing estimate):**
- [ ] Prior stated ("Prior: 45%")
- [ ] Prior date stated ("prior from 2026-02-19")
- [ ] Change magnitude ("Updated to 65%, +20 percentage points")
- [ ] New data that triggered update

**Confidence Tier Match:**
Verify language matches probability range per style guide:
- 90%+ → "I assess with high confidence"
- 70-89% → "I assess [X]% probability"
- 50-69% → "I assess [X]% probability -- close to coin flip at low end"
- 30-49% → "I assess [X]% probability -- more likely NOT to happen"
- <30% → "I assess low probability ([X]%)"

**Workflow:**

1. Extract all probability estimates from draft
2. For each estimate, verify checklist above
3. Flag incomplete estimates with:
   - Location in draft
   - Missing element(s)
   - Suggested format

**Report format:**

```markdown
## Probability Format Validation: SD Issue #{issue-number}

### Estimates Found: {count}

### Complete: {count}
- [list with probability and event]

### Incomplete: {count}
- [list with location, missing elements, suggested fix]

Result: PASS / NEEDS WORK
```

If any estimate is incomplete, NEEDS WORK. Calibration tracking depends on complete format.

### Pass 4: Calibration Cross-Check (Shepard)

**Purpose:** Verify probability updates are consistent with evidence and stage updates to probabilities.json (without committing until publish).

**What Shepard validates:**

**Load probability state:**
- Read `content/state/probabilities.json`
- Extract all active predictions

**For each probability in draft:**

**Prior Correctness:**
- Does stated prior match probabilities.json?
- Is prior date correct?
- If new prediction, confirm it's not duplicating existing one

**Update Direction:**
- Is update direction consistent with new evidence?
- Example: If OONI measurements recovered AND rial spread compressed → stability UP
- Flag if update contradicts evidence direction

**Update Magnitude:**
- Is update size reasonable given evidence strength?
- Large updates (>20 percentage points) require strong justification
- Multiple large updates in one issue = red flag

**Calibration Red Flags:**
- More than 2 large updates (>20pp) in single issue
- Update without new data
- Update contradicts evidence direction
- Frequent updates to same prediction (signal instability)

**Workflow:**

1. Read `content/state/probabilities.json`
2. Extract probability estimates from draft
3. For each estimate:
   - Verify prior matches state file
   - Check update direction vs evidence
   - Assess update magnitude reasonableness
   - Flag calibration concerns
4. Stage updates (create temp file, don't commit)

**Report format:**

```markdown
## Calibration Cross-Check: SD Issue #{issue-number}

### Estimates Reviewed: {count}

### Prior Verification:
- Correct: {count}
- Incorrect: {count} [list with details]

### Update Direction:
- Consistent with evidence: {count}
- Questionable: {count} [list with concerns]

### Magnitude Concerns:
- Large updates (>20pp): {count} [list with justification check]
- Multiple large updates: {yes/no}

### Calibration Red Flags:
- [list any patterns that suggest calibration issues]

### Staged Updates:
- Written to: content/state/probabilities.json.staged
- DO NOT commit until publish

Result: PASS / NEEDS WORK / WARN
```

PASS = all checks clear
NEEDS WORK = incorrect priors or contradictory updates
WARN = calibration red flags but not blocking (Cooper decides)

### Pass 4b: Swarm Calibration (if MiroFish was run)

**Purpose:** Compare article probability estimates against MiroFish swarm-implied probabilities. Adversarial validation from a different methodology -- graph-based swarm vs editorial review.

**Prerequisite:** `content/research/{issue-number}/mirofish-report.md` exists. If it doesn't, skip this pass entirely and note "MiroFish not run" in the review summary.

**What Shepard validates:**

**Probability Comparison:**
- Extract swarm-implied probability from `mirofish-report.md`
- Compare against each corresponding probability estimate in the draft
- Calculate divergence (absolute percentage point difference)

**Divergence Thresholds:**
- **<15pp divergence:** Note discrepancy, no action required
- **≥15pp divergence:** Flag for deeper examination -- does the swarm's framing reveal assumptions the article makes implicitly?
- **Convergence (both aligned):** Strengthens the editorial estimate; note as supporting evidence

**Counter-Argument Check:**
- Read the swarm's surfaced counter-arguments from the report
- Identify any counter-argument the article does NOT address
- Flag gaps as "Swarm surface, article silent" -- these are not necessarily errors, but warrant consideration

**Article Integration (if Cooper decides to include):**
- Swarm results can appear as a "simulated market response" section
- Format: "Our swarm simulation of {N} market participants converged on X% probability..."
- Only include if it adds interpretive value beyond the editorial assessment

**Workflow:**

1. Read `content/research/{issue-number}/mirofish-report.md`
2. Read draft probability estimates
3. Compare and calculate divergence for each estimate
4. Review swarm counter-arguments against article coverage
5. Flag gaps and large divergences

**Report format:**

```markdown
## Swarm Calibration: SD Issue #{issue-number}

### Probability Comparison
| Event | Article | Swarm | Divergence | Flag? |
|-------|---------|-------|------------|-------|
| [event] | [X%] | [Y%] | [Zpp] | YES/no |

### Large Divergences (≥15pp)
- [event]: Article X%, Swarm Y% (+/-Z pp)
  - Swarm framing: {brief summary of swarm's reasoning}
  - Article assumption to examine: {what the swarm's divergence implies}

### Counter-Arguments Surfaced by Swarm
- Addressed in article: {count}
- NOT addressed (gaps): {list}

### Article Integration
- Recommended: YES/NO
- If YES, suggested placement: {section}

Result: PASS (divergence <15pp on all) / WARN (divergence ≥15pp, review needed) / SKIPPED (no MiroFish report)
```

PASS = all divergences below threshold, no unaddressed counter-arguments that change the thesis
WARN = divergence ≥15pp or significant gap in counter-argument coverage (Cooper decides)
SKIPPED = `mirofish-report.md` not present

### Pass 5: Persona Consistency (Kelly)

**Purpose:** Verify voice matches Data-Driven Practitioner archetype and institutional brand. Persona drift compounds over issues -- catch it early.

**What Kelly reviews:**

**Voice Archetype Check:**
- First-person singular throughout? ("I assess" not "we assess")
- Calm confidence maintained? (no panic, no hedging)
- Methodologically rigorous? (shows work, cites sources)
- Skin-in-the-game transparent? ("I trade this" present when appropriate)
- Respectfully direct? (active voice, writes for intelligent outsider)

**Institutional Brand:**
- "Signal Dispatch" used for institutional references (methodology, infrastructure)?
- Not personal blog tone?
- No claimed credentials that don't exist?
- Trademark phrases used naturally (not forced)?

**Emotional Register:**
- Confidence without arrogance?
- Analytical curiosity present?
- Measured concern when data warrants (not fear-mongering)?
- Honest about uncertainty?
- Dry wit in footnotes only (rare, strategic)?

**Red Flags from Persona Guide:**
- Claiming credentials that don't exist
- Making unfalsifiable predictions
- Fear-based language for engagement
- Political partisanship disguised as analysis
- Condescension toward readers
- AI-polished generic writing
- Clickbait headlines

**Signature Phrases (check for natural usage):**

Openings:
- "Here's what moved this cycle:"
- "Three signals shifted simultaneously:"
- "The data changed my assessment:"

Anchors:
- "Edge requires honesty."
- "Show your work."
- "Calibration over conviction."
- "Losses prove the wins are real."

Recurring:
- "I trade this."
- "Numbers without receipts."
- "Here's the recipe, not just the meal."
- "Not panic. Pattern recognition."

**Dispatch template:**

```
Task(
  subagent_type: "kelly",
  prompt: "Persona consistency review for Signal Dispatch issue #{issue-number}.

Read these files:
- Draft: /path/to/home/projects/signal-dispatch/content/drafts/{issue-number}-{type}.md
- Persona guide: /path/to/home/projects/signal-dispatch/docs/PERSONA.md
- Persona config: /path/to/home/projects/signal-dispatch/config/persona.yaml

Review the draft for voice consistency with the Data-Driven Practitioner archetype.

Check:
- First-person singular throughout (\"I assess\" not \"we assess\")
- Calm confidence maintained (no panic, no hedging)
- Methodologically rigorous (shows work, cites sources)
- Skin-in-the-game transparency (\"I trade this\" when appropriate)
- Active voice for analysis
- Institutional brand clarity (\"Signal Dispatch\" for methodology references)
- Emotional register appropriate (confidence not arrogance, measured concern not fear)

Red flags to catch:
- Claiming credentials that don't exist
- Fear-based engagement language
- Political partisanship
- Condescension toward readers
- AI-generic polished writing
- Clickbait patterns

For signature phrases, verify:
- Used naturally (not forced)
- Fit context appropriately
- Don't feel like templates

For each persona drift point found, report:
1. Location in draft
2. Issue (voice inconsistency, red flag, forced phrasing)
3. Current text
4. Suggested revision to match archetype

Categorize:
- **Critical:** Breaks core archetype (wrong person, fear-mongering, credentials claimed)
- **Important:** Voice drift (hedging, passive voice, condescension)
- **Minor:** Refinement opportunity (signature phrase could be more natural)

Report format:
- PASS (consistent with archetype) or NEEDS WORK (list drift points)
- Drift count by severity

Voice consistency is the brand. Drift compounds over issues. Be thorough.",
  description: "Persona review SD #{issue-number}",
  model: "sonnet"
)
```

### Pass 6: Delta Verification

**Purpose:** Cross-check every data claim in the draft against computed deltas. Mechanical fact-checking -- not editorial judgment.

**What Shepard verifies:**

1. Read `content/research/{issue}/delta_summary.md`
2. For each numeric claim in the draft (percentages, counts, values):
   - Find the corresponding delta in the summary
   - Verify the number matches (within rounding tolerance)
   - Flag any claim that doesn't have a supporting delta
3. For each source attribution ("OONI data shows...", "according to FRED..."):
   - Verify the source was actually polled in this cycle
   - Verify the claim matches what the source returned

**Rules:**
- This is mechanical verification, not editorial judgment
- Unverified claims are not necessarily wrong -- they may come from web research or manual analysis
- Only flag discrepancies (claim contradicts computed delta) as errors
- Claims sourced from prediction markets, web research, or expert analysis are exempt from delta verification

**Report format:**

```markdown
## Delta Verification: SD Issue #{issue-number}

### Verified Claims: {count}
- [claim → delta source, with value match confirmed]

### Unverified Claims: {count} (no matching delta -- informational only)
- [claim, location in draft, likely source type]

### Discrepancies: {count} (claim contradicts computed delta -- must fix)
- [claim, location, what draft says, what delta says]

Result: PASS / NEEDS WORK
```

PASS = no discrepancies (unverified claims are informational, not blocking)
NEEDS WORK = one or more discrepancies found

**Note:** If `delta_summary.md` doesn't exist for this issue (delta engine hasn't run, or issue predates delta engine), skip Pass 6 and note in review summary.

## Parallel Dispatch Strategy

**Passes 1 and 5 can run in parallel** (Tali style review + Kelly persona review). They're independent checks.

**Passes 2-4 and 6 run sequentially** (all Shepard). They build on each other:
- Pass 2 verifies data accuracy (foundation)
- Pass 3 validates probability format (structure)
- Pass 4 cross-checks calibration (consistency)
- Pass 4b swarm calibration (adversarial validation -- skip if no MiroFish report)
- Pass 6 verifies numeric claims against computed deltas (mechanical)

**Workflow:**

1. Dispatch Tali (Pass 1) and Kelly (Pass 5) in parallel
2. Wait for both to return
3. Run Shepard Passes 2-4 sequentially
4. Run Shepard Pass 4b (swarm calibration) -- skip if mirofish-report.md absent
5. Run Shepard Pass 6 (delta verification) -- skip if delta_summary.md absent
6. Synthesize all pass results
7. Present review summary to Cooper

## Review Summary Format

After all passes complete, present this summary to Cooper:

```markdown
## Editorial Review: SD Issue #{issue-number}

### Pass Results
| Pass | Agent | Result | Findings |
|------|-------|--------|----------|
| Style Guide | Tali | PASS/NEEDS WORK | {count} violations |
| Fact Verification | Shepard | PASS/NEEDS WORK | {count} discrepancies |
| Probability Format | Shepard | PASS/NEEDS WORK | {count} incomplete |
| Calibration | Shepard | PASS/NEEDS WORK/WARN | {count} concerns |
| Swarm Calibration | Shepard | PASS/WARN/SKIPPED | {divergence summary} |
| Persona | Kelly | PASS/NEEDS WORK | {count} drift points |
| Delta Verification | Shepard | PASS/NEEDS WORK/SKIPPED | {count} discrepancies |

### Overall: PASS / NEEDS WORK

---

### Critical Issues (must fix before publish)
[List all critical findings across passes]

### Important Issues (should fix before publish)
[List all important findings across passes]

### Minor Issues (optional refinements)
[List all minor findings across passes]

### Calibration Notes
[Any red flags or patterns from Pass 4]

### Staged Updates
- Probability updates staged to: content/state/probabilities.json.staged
- DO NOT commit until publish

---

Cooper: Approve for publish, or request fixes?
```

## Cooper Decision Points

After review summary:

**If PASS across all passes:**
- "Approve for publish" → proceed to `/publish`
- "Request minor fixes" → make edits, no re-review needed

**If NEEDS WORK on any pass:**
- Fix critical and important issues
- Re-run `/review --issue {number}` after fixes
- Iterate until PASS

**If WARN on calibration:**
- Cooper decides: accept the calibration concerns or revise probabilities
- WARN is not blocking, but requires explicit approval

**If WARN on swarm calibration (Pass 4b):**
- Review the swarm's divergence and counter-arguments
- Cooper decides: investigate the divergence, revise the probability, or accept with justification
- WARN is not blocking -- the swarm is adversarial input, not editorial authority
- If divergence is large AND the swarm surfaces a counter-argument not in the article, consider whether the thesis needs strengthening

## Anti-Patterns

**Don't skip fact verification.**
- "It's probably right" is not acceptable
- One wrong number undermines calibration credibility
- VERIFY every data point against research brief

**Don't rubber-stamp persona.**
- Voice drift is subtle and compounds over issues
- Kelly catches patterns Shepard might miss
- Persona consistency IS the brand

**Don't approve large probability swings without justification.**
- Updates >20 percentage points require clear evidence
- Multiple large updates in one issue suggest overcorrection
- This is the calibration moat -- protect it

**Don't commit probabilities.json until publish.**
- Pass 4 stages updates to .staged file
- Only `/publish` commits to main state file
- Prevents orphaned probability state if review fails

## Error Handling

**If draft doesn't exist:**
```
Error: Draft not found
Expected: content/drafts/{issue-number}-{type}.md

Run /draft first to create the draft, or check issue number.
```

**If research brief doesn't exist:**
```
Error: Research brief not found
Expected: content/research/{issue-number}/brief.md

Run /intel to create research brief first.
```

**If probabilities.json doesn't exist:**
```
Error: Probability state not found
Expected: content/state/probabilities.json

Initialize state file:
echo '{"predictions": []}' > content/state/probabilities.json
```

**If agent returns with errors:**
Report to Cooper with context. Don't silently fail or skip passes.

## Notes

- Tali and Kelly use Sonnet (sufficient for systematic review)
- Shepard uses current model (Opus) for judgment calls
- Review is the final editorial gate -- be thorough
- Calibration credibility depends on catching errors here
- Persona drift compounds -- Kelly's role is critical
- One wrong data point undermines the entire brand

---

*"Show your work."*
