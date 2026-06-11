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

**Critical: Header format must match established pattern.**

The `publish_to_substack.py` script parses H1 as the Substack title and H2 as the subtitle. The formatted file must use this exact structure:

```markdown
# {Article Title}
## Signal Dispatch {Type} | {Date}
```

**Do NOT include:**
- Front matter metadata blocks (Title:, Subtitle:, Tags:) in the article body -- the script ignores them and they render as visible text
- `# Signal Dispatch -- Deep Dive` as a separate H1 before the title -- that becomes the title instead
- `### {Date}` as H3 -- the date belongs in the H2 line

**Correct example (matching SD #4 layout):**
```markdown
# What's Dying While Everyone Watches Iran
## Signal Dispatch Deep Dive | March 16, 2026

**Classification:** Open Source Intelligence
**Topic:** ...
```

**Wrong (what SD #5 initially had):**
```markdown
Title: The Compound Shock...
Subtitle: Three shocks...
Section: Deep Dive
---
# Signal Dispatch -- Deep Dive
## The Compound Shock...
### March 18, 2026
```

**Output:** `content/drafts/{issue-number}-{type}-formatted.md`

### Step 1B: Generate OG Image / Thumbnail

Generate a 1200x630 OG image matching the Signal Dispatch brand theme.

**Brand Theme:**
- Background: Deep navy gradient (#0A0F1A top → #0E1424 bottom)
- Accent: Signal orange/amber (#D4853A) -- used for "SIGNAL DISPATCH" header text and accent lines
- Title font: Bebas Neue (bold, uppercase) -- available at `content/brand/BebasNeue-Regular.ttf`
- Primary text: Off-white (#F0EDE8)
- Secondary text: Muted (#B4AFA5)
- Background texture: Faint grid lines (#1E2A3C), diagonal scan lines lower-right
- Large issue number watermark (semi-transparent) in bottom-right corner
- "SIGNAL DISPATCH" with orange accent line at top-left
- Content type + date at bottom-left (e.g., "DEEP DIVE | MARCH 18, 2026")

**Generator reference:** `content/drafts/generate_og_image.py` (SD #4 generator -- study this for exact implementation)

**Workflow:**
1. Use `/marketing-studio` or dispatch EDI to generate a Python Pillow script matching the brand theme
2. Title text should be the article title in Bebas Neue caps
3. Subtitle in smaller muted text below
4. Output to: `content/drafts/{issue-number}-og-image.png`
5. Upload as cover image in Substack editor after draft creation

### Step 2: the editor Review (GATE)

Present formatted version + OG image. Last gate before publication.

**the editor Reviews:**
- Formatted output visually correct?
- OG image matches brand?
- Paywall position appropriate?
- Footer links correct?
- Ready to publish?

**Confirm:** "Publish this?"

If no, return to drafting or review. If yes, proceed to Step 3.

### Step 3: Publish Draft to Substack

**Use `publish_to_substack.py` to create a Substack draft.**

```bash
SUBSTACK_COOKIES="substack.sid={cookie_value}" \
  .venv/bin/python publish_to_substack.py --draft-only content/drafts/{issue}-{type}-formatted.md
```

**The script:**
- Parses H1 as Substack title, H2 as subtitle
- Converts markdown to ProseMirror JSON (Substack's internal format)
- Handles footnotes (converted to inline superscript + Notes section in Step 1)
- Creates a draft and returns the draft URL

**Auth:** Requires `SUBSTACK_COOKIES` env var with the `substack.sid` session cookie. Get from browser: DevTools → Application → Cookies → signaldsp.substack.com → `substack.sid` value. URL-encode special characters (`+` → `%2B`, `/` → `%2F`).

**After draft creation:**
1. Open the returned draft URL in browser
2. Upload OG image as cover image
3. Set paywall position (the `<!--more-->` marker should already be converted)
4. Verify formatting in Substack preview
5. Set scheduling or publish immediately

**Modes:**
- `--draft-only` -- Creates draft, returns URL (default for this workflow)
- `--publish` -- Creates and immediately publishes (use with caution)
- `--dry-run` -- Prints ProseMirror JSON without hitting API

**Scheduling recommendation:**
- weekly_brief: Sunday 8:00 AM ET
- breaking_alert: Immediate (within 2 hours)
- deep_dive: First Sunday of month, 8:00 AM ET (or immediately if timely -- e.g., pre-FOMC)

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

### Step 4B: Resolution Sweep + State Reconciliation

Mandatory pre-publication check. Runs after archive (Step 4), before probability state is finalized (Step 5). **Do not proceed to Step 5 if either sub-check fails.**

#### Resolution Sweep

Scan all entries in `probabilities.json` `events` array. For each event where `resolution_date` has passed:

1. **Resolve it.** "We haven't checked" is not a valid reason to leave it open. Move the entry from `events` to `resolved` with:
   - `resolved`: `"YES"` / `"NO"` / `"PARTIAL"`
   - `resolution_date`: actual date resolution was determined
   - `resolution_note`: 2-3 sentences -- what the assessment got right, what it missed
   - `final_probability`: the last committed probability before resolution
   - `brier_score`: `(final_probability - outcome)²` where outcome is `1` (happened) or `0` (didn't happen). For PARTIAL, treat as `0.5`.

   Example:
   ```json
   {
     "id": "hormuz-disruption-6-weeks",
     "event": "Hormuz disruption persists more than 6 weeks",
     "resolved": "YES",
     "resolution_date": "2026-04-13",
     "resolution_note": "Disruption persisted past the 6-week threshold. The 80% estimate at resolution captured the trajectory well -- IRGC hardening and absence of any de-escalation pathway were the key signals. Miss: underestimated how quickly hardline succession would consolidate after Larijani's death.",
     "final_probability": 0.80,
     "brier_score": 0.04
   }
   ```

2. **Timeline extension.** If resolution is genuinely ambiguous, document:
   - Add an `extension` field to the event entry: `{ "extended_to": "YYYY-MM-DD", "justification": "..." }`
   - Justification must cite a specific, verifiable condition.

3. **Update calibration summary.** After resolving, recalculate `calibration_summary`:
   - Increment `total_resolved`
   - Recalculate `mean_brier_score` across all resolved entries
   - Update the appropriate `calibration_buckets` outcome count

#### State File Reconciliation

Every probability percentage stated in the article text must exactly match `current_probability` in `probabilities.json`.

- Extract all probability claims from the article (e.g., "12% chance", "we assess 40%").
- Cross-reference each against the corresponding event in `probabilities.json`.
- If the article updates a probability (e.g., moves Iran ceasefire from 8% to 12%), the state file `current_probability` and `history` must already reflect the new value before publication.

**Discrepancy = STOP.** Reconcile before proceeding. Either:
- Correct the article text to match the state file, or
- Update the state file with the new estimate (adding a history entry) and confirm with the editor.

Do not publish an article that disagrees with its own probability ledger.

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

#### Ledger Status

Every published issue should include or link to a current probability ledger. Options:

1. **Standalone Substack page** (preferred): Maintain a living `/track-record` page on Substack updated after each publication. Link from the article footer (the footer template already references `signaldispatch.substack.com/track-record`).

2. **Embedded ledger section**: If the article warrants it (e.g., a weekly brief with multiple probability updates), embed a condensed table:
   - All active tracked events with current probability and last-updated date
   - Any newly resolved events from Step 4B with Brier score and post-mortem summary
   - Format: clean table, probabilities as percentages, dates as Month DD YYYY

The ledger does not need to be exhaustive in every article -- but every reader should be able to find the full current state via one click from any issue.

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

**Present to the editor for review.** The editor posts manually. Do not auto-post.

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

**Do NOT auto-commit.** Confirm with the editor first:
- "Ready to commit publication record?"
- Show commit message
- Wait for confirmation

**Dry-run mode:** Skip commit. No state changes.

## Anti-Patterns

**Don't publish without the editor's explicit approval at gate**
- Step 2 is a hard gate. No publication without "yes".

**Don't skip archive**
- Published content IS the track record. Every published issue must be archived with metadata.

**Don't update probabilities.json without publishing**
- Staged estimates are not committed until publication. State must match published content.

**Don't write social threads in clickbait voice**
- Same persona applies: data-driven practitioner, calm confidence, show work.
- No 🚨, no "WW3", no panic triggers.

**Don't auto-commit**
- Confirm with the editor. Publication commits are permanent track record entries.

## Outputs

| File | Purpose |
|------|---------|
| `content/drafts/{issue}-{type}-formatted.md` | Platform-formatted version |
| `content/published/{issue}-{type}-{date}.md` | Archived published version |
| `content/state/probabilities.json` | Updated with committed estimates |
| `content/state/issues.json` | Updated issue status |
| Social thread outline (presented to the editor) | Twitter/X amplification |

## Notes

- Substack API calls go through `publish_to_substack.py` in the project root.
- the editor manually pastes formatted content into Substack interface for now.
- Full automation pending Substack API stability.
- Dry-run mode is useful for previewing formatting before gate review.
