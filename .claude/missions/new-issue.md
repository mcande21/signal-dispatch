---
name: new-issue
description: Produce a Signal Dispatch newsletter issue from research through publication
mode: interactive
args:
  - name: type
    required: true
    description: Content type -- weekly_brief | breaking_alert | deep_dive
  - name: topic
    required: false
    description: Focus area or topic (required for breaking_alert and deep_dive, optional for weekly_brief)
---

# Mission: New Issue

*"Structured intelligence. Explicit probabilities. Tradeable insight."*

## Objective

Produce a complete Signal Dispatch newsletter issue from raw intelligence through publication, following a gated four-phase workflow.

## Background

Signal Dispatch wraps the prediction-markets project for structured data (Ghost Market adapters, OSINT feeds, prediction market CLI). Three content types with different framing but identical research depth:

- **weekly_brief** -- Cycle review. What moved, what it means, what to watch.
- **breaking_alert** -- Urgency without panic. Signal detected, data evidence, probability impact.
- **deep_dive** -- Comprehensive single-topic. Executive summary, data layers, assessment.

Persona voice: Data-Driven Practitioner. Methodologically rigorous, skin-in-the-game transparent, calm confidence. See `config/persona.yaml` and `docs/PERSONA.md`.

This is collaborative work -- the editor and Shepard work through each phase together. Skills provide structure, not automation. Each phase produces artifacts that feed the next. Nothing proceeds without the editor's gate.

## Parameters

| Param | Required | Description |
|-------|----------|-------------|
| type | Yes | `weekly_brief`, `breaking_alert`, or `deep_dive` |
| topic | Conditional | Required for breaking_alert and deep_dive. Optional for weekly_brief (defaults to "this cycle's signals"). |

## Issue Initialization

Before beginning Phase 1:

1. Read `content/state/issues.json`, get next issue number
2. Create issue directory: `content/research/{issue-number}/`
3. Record in issues.json:
   ```json
   {
     "issue_number": N,
     "type": "{type}",
     "topic": "{topic}",
     "date_started": "{ISO-8601}",
     "status": "research"
   }
   ```
4. Confirm with the editor: "Issue #{number}: {type} on {topic}. Ready to begin research?"

## Execution

### Phase 1: Research -- `/intel`

**Invoke:** `/intel {type} {topic} --issue {number}`

**Output:** `content/research/{issue-number}/` populated with research artifacts

**Gate:** The editor reviews research brief, decides whether to proceed to drafting

**On approval:** Update issues.json status to `"drafting"`

---

### Phase 2: Draft -- `/draft`

**Invoke:** `/draft {type} --issue {number}`

**Input:** Research artifacts from Phase 1

**Output:** `content/drafts/{issue-number}-{type}.md`

**Gate:** The editor reviews draft, decides whether to proceed to review

**On approval:** Update issues.json status to `"review"`

---

### Phase 3: Review -- `/review`

**Invoke:** `/review --issue {number}`

**Input:** Draft from Phase 2 + research artifacts for fact-checking

**Output:** Review findings, updated `probabilities.json`

**Gate:** The editor approves final version

**On approval:** Update issues.json status to `"approved"`

---

### Phase 4: Publish -- `/publish`

**Invoke:** `/publish --issue {number}`

**Input:** Approved draft

**Output:**
- Published to Substack
- Archived to `content/published/`
- Social thread outline

**On completion:** Update issues.json status to `"published"`, add `date_published`

## Constraints

- Each phase must complete before the next begins.
- the editor gates every phase transition. No auto-progression.
- Breaking alerts follow the same depth but with urgency framing -- they do NOT skip phases.
- All probability estimates must have: specific number, basis, resolution criteria.
- File-based data flow: CLI → JSON → agents read files → markdown output.

## Success Criteria

- [ ] Research brief produced with structured data + web research + Legion orthogonal synthesis
- [ ] Draft written in persona voice with probability updates formatted correctly
- [ ] Review passes style guide, fact verification, probability format, calibration, and persona checks
- [ ] Published to platform with archived copy
- [ ] Probability state updated with all published estimates
- [ ] Issue tracker updated with complete lifecycle

## Key Files

| File | Role |
|------|------|
| `config/persona.yaml` | Persona configuration |
| `docs/PERSONA.md` | Persona reference |
| `docs/STYLE-GUIDE.md` | Writing style guide |
| `src/paper/templates/{type}.md` | Article templates |
| `config/sources.yaml` | Data source routing |
| `config/newsletter.yaml` | Newsletter config |
| `content/state/probabilities.json` | Probability tracking |
| `content/state/issues.json` | Issue lifecycle |

---

Mission loaded. What type of issue are we producing?
