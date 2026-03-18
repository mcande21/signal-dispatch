---
name: publish
description: Publish a reviewed Signal Dispatch issue to Substack and archive
version: 1.0.0
---

# /publish -- Publication

*"I should go."* -- Shepard

Final phase. Format for platform, publish, archive, update state, generate social amplification.

## Invocation

```bash
/publish --issue {number}
/publish --issue {number} --dry-run
```

## Arguments

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| --issue | Yes | - | Issue number (must be review-approved) |
| --dry-run | No | false | Format and preview without publishing |

## Prerequisites

- Draft approved after /review
- `content/drafts/{issue-number}-{type}.md` exists and is final
- `content/state/probabilities.json` updated with staged estimates

## Execution Steps

### Step 1: Format for Platform

Read approved draft. Convert to Substack-compatible format:

**Markdown Cleanup:**
- Substack supports basic Markdown (headers, lists, links, bold/italic)
- Tables: Convert complex tables to simple lists or images
- Code blocks: Supported but rarely used in Signal Dispatch
- Footnotes: Convert `[^1]` to inline references with anchor links

**Paywall Marker:**
Identify free/paid split per newsletter.yaml tiers:

| Content Type | Free Section | Paid Section |
|--------------|--------------|--------------|
| weekly_brief | "This Week's Signals" + "Key Developments" | "Data Appendix" |
| breaking_alert | None | Full content (paid only) |
| deep_dive | Executive Summary | Full analysis |

Insert paywall marker in Substack format: `<!--more-->`

**Image/Chart Embedding:**
- Charts from research pipeline in `content/research/{issue}/charts/`
- Upload to Substack image hosting
- Alt text: descriptive for accessibility

**Footer:**
Add standard footer:
```markdown
---

**Methodology:** [Calibration & Resolution Criteria](https://signaldispatch.substack.com/about)

**Track Record:** View all resolved predictions and Brier scores at [signaldispatch.substack.com/track-record](https://signaldispatch.substack.com/track-record)

**Disclosure:** I trade prediction markets on this analysis. Positions disclosed when relevant.
```

**Output:** `content/drafts/{issue-number}-{type}-formatted.md`

### Step 2: Cooper Review (GATE)

Present formatted version. Last gate before publication.

**Cooper Reviews:**
- Formatted output visually correct?
- Paywall position appropriate?
- Footer links correct?
- Ready to publish?

**Confirm:** "Publish this?"

If no, return to drafting or review. If yes, proceed to Step 3.

### Step 3: Publish to Substack

**Currently manual** (no API automation):

Present formatted content for Cooper to paste into Substack interface.

**Include:**
- **Title:** From front matter
- **Subtitle:** One-line hook with key probability
- **Section:** Newsletter section (e.g., "Weekly Brief", "Breaking Alert", "Deep Dive")
- **Tags:** From front matter (e.g., "Iran", "Sanctions", "OSINT")
- **Paywall position:** Line number where `<!--more-->` appears
- **Scheduling recommendation:** Based on newsletter.yaml schedule
  - weekly_brief: Sunday 8:00 AM ET
  - breaking_alert: Immediate (within 2 hours)
  - deep_dive: First Sunday of month, 8:00 AM ET

**Note:** `publish_to_substack.py` (project root) handles Substack API integration. Currently used for manual-assisted publishing; full automation pending Substack API stability.

**Dry-run mode:** Skip this step. Show formatted output only.

### Step 4: Archive

Copy final version to: `content/published/{issue-number}-{type}-{date}.md`

**Include front matter:**
```yaml
---
issue: {number}
type: {type}
date_published: {ISO date}
topic: {topic}
platform: substack
platform_url: {Substack URL}
paywall_position: {line number}
---
```

**Example:**
```yaml
---
issue: 1
type: weekly_brief
date_published: 2026-03-09
topic: Iran nuclear escalation
platform: substack
platform_url: https://signaldispatch.substack.com/p/weekly-brief-001
paywall_position: 42
---
```

### Step 5: Update Probability State

Finalize `content/state/probabilities.json`:

For each estimate in the published issue:
- Locate entry in probabilities.json
- Add history entry:
  ```json
  {
    "date": "2026-03-09",
    "estimate": 0.65,
    "issue_number": 1,
    "published": true
  }
  ```
- If event resolved, update status:
  ```json
  {
    "status": "resolved",
    "resolution_date": "2026-03-09",
    "outcome": true,
    "resolution_criteria": "..."
  }
  ```

**This is when staged estimates become committed.** Probabilities in draft are staged. Probabilities in published content are locked in the track record.

### Step 6: Update Issue State

Update `content/state/issues.json`:

```json
{
  "issue": 1,
  "type": "weekly_brief",
  "status": "published",
  "date_created": "2026-03-01",
  "date_published": "2026-03-09",
  "topic": "Iran nuclear escalation",
  "draft_path": "content/drafts/1-weekly_brief.md",
  "published_path": "content/published/1-weekly_brief-2026-03-09.md",
  "platform_url": "https://signaldispatch.substack.com/p/weekly-brief-001"
}
```

### Step 7: Social Thread Outline

Generate Twitter/X thread outline (5-7 tweets):

**Structure:**

1. **Hook:** Key finding + probability number
   - Example: "Iranian internet censorship reconstituted in 48 hours. I estimate 65% chance Iran conducts limited strike on Israeli territory within 72 hours. Here's why."

2. **Data:** The signal with source citation
   - Example: "OONI data shows DNS-over-HTTPS blocking reactivated across all Iranian ASNs on March 5, 2026. Last time this pattern occurred: October 2023, 36 hours before Hezbollah rocket barrages."

3. **Context:** Prediction market price comparison
   - Example: "Polymarket: 'Iran strikes Israel in March 2026' trading at 42%. My estimate: 65%. The gap: markets haven't priced in the OONI signal + black market rial movement."

4. **Methodology:** "Here's how I got to this number"
   - Example: "Base rate: 3 of 5 reconstitution events (2019-2024) preceded kinetic action within 96 hours. Rial crashed 12% vs. USD in 24 hours -- capital flight consistent with escalation prep."

5. **Track Record:** Calibration context
   - Example: "Previous Iran escalation calls: 4 resolved, Brier score 0.18. Post-mortem on October 2023 miss: underweighted domestic political constraints."

6. **CTA:** Link to full analysis
   - Example: "Full data breakdown, resolution criteria, and prediction tracker: [link]"

**Voice Constraints:**
- First-person: "I estimate", "My analysis", "Here's what I see"
- No clickbait: No "🚨", no "BREAKING", no panic framing
- Calm confidence: Probability numbers carry weight, not emotional language
- Show work: Cite sources inline (OONI, Bonbast, Polymarket)

**Present to Cooper for review.** Cooper posts manually. Do not auto-post.

**Dry-run mode:** Skip this step. Social threads generated only for actual publications.

### Step 8: Commit

After all state files updated and archive written, commit via Miranda:

**Stage:**
- `content/state/probabilities.json`
- `content/state/issues.json`
- `content/published/{issue-number}-{type}-{date}.md`
- Any updated drafts (if corrections made during formatting)

**Commit message format:**
```
docs: publish SD #{issue} -- {type} on {topic}
```

**Example:**
```
docs: publish SD #1 -- weekly_brief on Iran nuclear escalation
```

**Do NOT auto-commit.** Confirm with Cooper first:
- "Ready to commit publication record?"
- Show commit message
- Wait for confirmation

**Dry-run mode:** Skip commit. No state changes.

## Anti-Patterns

**Don't publish without Cooper's explicit approval at gate**
- Step 2 is a hard gate. No publication without "yes".

**Don't skip archive**
- Published content IS the track record. Every published issue must be archived with metadata.

**Don't update probabilities.json without publishing**
- Staged estimates are not committed until publication. State must match published content.

**Don't write social threads in clickbait voice**
- Same persona applies: data-driven practitioner, calm confidence, show work.
- No 🚨, no "WW3", no panic triggers.

**Don't auto-commit**
- Confirm with Cooper. Publication commits are permanent track record entries.

## Outputs

| File | Purpose |
|------|---------|
| `content/drafts/{issue}-{type}-formatted.md` | Platform-formatted version |
| `content/published/{issue}-{type}-{date}.md` | Archived published version |
| `content/state/probabilities.json` | Updated with committed estimates |
| `content/state/issues.json` | Updated issue status |
| Social thread outline (presented to Cooper) | Twitter/X amplification |

## Notes

- Substack API calls go through `publish_to_substack.py` in the project root.
- Cooper manually pastes formatted content into Substack interface for now.
- Full automation pending Substack API stability.
- Dry-run mode is useful for previewing formatting before gate review.
