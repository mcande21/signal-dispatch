---
name: intel
description: Full intelligence collection for a Signal Dispatch issue. Parallel source collection, web research, Legion synthesis.
version: 1.0.0
---

# /intel -- Intelligence Collection

*"I need to know everything about this beat."* -- Shepard

Full intelligence gathering for a Signal Dispatch issue. Validates topic, determines which intelligence tracks to activate, dispatches agents in parallel, synthesizes cross-track findings with Legion orthogonal perspective, and packages a research brief for drafting.

This is the core Signal Dispatch workflow. It turns open-source data feeds into calibrated geopolitical intelligence with nested skepticism. The differentiator: Legion's orthogonal analysis against Liara's synthesis.

## Invocation

- `/intel weekly_brief` -- Full cycle research (all active signal sources)
- `/intel breaking_alert {topic}` -- Urgent research triggered by anomaly
- `/intel deep_dive {topic}` -- Comprehensive single-topic research
- `/intel {type} {topic} --issue {number}` -- Within parent mission context

## Arguments

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| type | Yes | - | `weekly_brief`, `breaking_alert`, or `deep_dive` |
| topic | Conditional | - | Focus area. Required for breaking_alert and deep_dive. |
| --issue | No | auto | Issue number. Auto-generates if not provided. |
| --skip-web | No | false | Skip web research (CLI data only) |

## Project Paths

- **Signal Dispatch root:** `/path/to/home/work/personal/code/research/signal-dispatch`
- **Prediction markets root:** `/path/to/home/work/personal/code/research/prediction-markets`
- **Research output:** `{sd_root}/content/research/{issue-number}/`
- **PM CLI pattern:** `cd {pm_root} && source .venv/bin/activate && python -m src.cli {command}`

## Execution

Five phases. War-room threshold: 3+ tracks → parallel dispatch. 1-2 tracks → sequential dispatch.

### Phase 0: Topic Validation and Source Routing (Shepard)

**Step 0A: Topic Scoping**

Different behavior per content type:

**weekly_brief:**
- Review ALL structured feeds from `/path/to/home/work/personal/code/research/signal-dispatch/config/sources.yaml`
- Read `/path/to/home/work/personal/code/research/signal-dispatch/content/state/probabilities.json` for active tracking events
- Question: "What moved this cycle across all feeds?"

**breaking_alert:**
- Validate the triggering anomaly
- Which feed? What data point? What baseline?
- Confirm with Cooper: Is this signal-level movement or noise?
- Question: "What is the triggering event and historical precedent?"

**deep_dive:**
- Scope the topic boundaries
- What question? What thesis?
- Which sources contribute to resolution?
- Question: "What is the full causal chain from data to conclusion?"

**Step 0B: Source Routing**

Topic-to-source routing table:

| Topic Domain | Ghost Market Sources | OSINT Sources | Web Research |
|-------------|---------------------|---------------|-------------|
| Iran/geopolitics | OONI, Bonbast, TEDPIX, Cloudflare Radar, OFAC, USAspending | Federal Register | Yes |
| Energy/petroleum | EIA | Federal Register | Yes |
| Sanctions/policy | OFAC, USAspending | Federal Register, Congress | Yes |
| Legislation | None | Federal Register, Congress, FEC | Yes |
| Multi-topic (weekly) | ALL active | ALL applicable | Yes |

**Step 0C: Build Track Manifest**

Determine which intelligence tracks to activate:

| Track | Fires When | Agent | CLI Command |
|-------|-----------|-------|-------------|
| Ghost Market Signals | Topic matches sources | Geth | `pm signals --source {X} --json` |
| OSINT Planning | Topic has govt data | Liara | (designs query plan) |
| OSINT Execution | Liara produces plan | Geth | `pm osint --plan-file {path} --json` |
| Web Research | Always (unless --skip-web) | Liara | (web search + synthesis) |
| Prediction Market Context | Always | Geth | `pm search "{topic}" --json` |

**War-room threshold:** 3+ tracks = parallel dispatch. 1-2 = sequential.

**Present manifest to Cooper for approval before dispatching.**

Format:
```
Intelligence manifest for {content_type} on {topic}:
- Track A: Ghost Market Signals (OONI, Bonbast, EIA) -- Geth
- Track B: Web Research + OSINT Planning -- Liara
- Track C: OSINT Execution -- Geth (depends on Track B)
- Track D: Prediction Market Context -- Geth

War-room mode: YES (4 tracks)
Proceed with parallel dispatch?
```

### Phase 1: Source Mapping (Shepard)

**Step 1A: Ghost Market CLI Commands**

Construct exact commands for each active source. Map source names to CLI arguments:

| Source | CLI Argument | Typical Frequency |
|--------|-------------|-------------------|
| OONI | `--source ooni` | 1h refresh |
| Bonbast | `--source bonbast` | 1h refresh |
| EIA | `--source eia` | 24h refresh |
| OFAC | `--source ofac` | 24h refresh |
| Cloudflare Radar | `--source cloudflare_radar` | 1h refresh |
| TEDPIX | `--source tedpix` | 4h refresh |
| USAspending | `--source usaspending` | 24h refresh |

Full command template:
```bash
cd /path/to/home/work/personal/code/research/prediction-markets && \
source .venv/bin/activate && \
python -m src.cli signals --source {source} --json --output data/pipeline/sd-{issue}-{source}.json
```

**Step 1B: OSINT API Doc Selection**

Based on topic, select which capability briefs Liara reads:

**Iran/geopolitics topics:**
- `/path/to/home/work/personal/code/research/prediction-markets/docs/osint/federal_register.md`
- `/path/to/home/work/personal/code/research/prediction-markets/docs/osint/alternative_signals.md`

**Legislation/policy topics:**
- `/path/to/home/work/personal/code/research/prediction-markets/docs/osint/federal_register.md`
- `/path/to/home/work/personal/code/research/prediction-markets/docs/osint/congress_gov.md`

**Election/campaign topics:**
- `/path/to/home/work/personal/code/research/prediction-markets/docs/osint/fec.md`
- `/path/to/home/work/personal/code/research/prediction-markets/docs/osint/congress_gov.md`

**Multi-topic (weekly brief):**
- All three: `federal_register.md`, `congress_gov.md`, `fec.md`
- Plus: `alternative_signals.md` if any Iran/geopolitics coverage

**Step 1C: Web Research Angles**

Define 3-5 research questions per content type:

**weekly_brief questions:**
1. What geopolitical events moved this cycle across all monitored domains?
2. What data trends shifted direction (upticks, drops, reversals)?
3. What consensus views are being challenged by structured data?
4. What upcoming events could shift active probabilities?
5. Where do expert forecasts diverge from base rates?

**breaking_alert questions:**
1. What is the triggering event/anomaly? (exact numbers, timestamps, baselines)
2. Historical precedent: last N times this signal appeared, what followed?
3. Cross-confirmation from other sources? (convergence = higher confidence)
4. Next 48-72 hour scenarios with conditional probabilities?
5. What would invalidate this signal as meaningful?

**deep_dive questions:**
1. What is the conventional wisdom on this topic?
2. Where does structured data contradict consensus?
3. Full causal chain from data signals to resolution criteria?
4. Strongest counterarguments to the thesis?
5. What resolution criteria make this assessable with ground truth?

**Step 1D: Prediction Market Context**

Construct search queries for relevant markets. This provides market-implied probabilities for comparison.

Format:
```bash
cd /path/to/home/work/personal/code/research/prediction-markets && \
source .venv/bin/activate && \
python -m src.cli search "{topic keywords}" --json --output data/pipeline/sd-{issue}-markets.json
```

Example topics:
- `weekly_brief` → "Iran", "sanctions", "oil", "conflict"
- `breaking_alert` on OONI drop → "Iran internet", "Hormuz", "regime"
- `deep_dive` on policy → "{specific policy topic}"

### Phase 2: Parallel Intelligence Collection

**Mode selection based on track manifest:**

**SIMPLE (1-2 tracks):** Sequential dispatch. Liara researches, then Geth fetches. Shepard synthesizes directly.

**WAR-ROOM (3+ tracks):** Parallel dispatch. All tracks fire simultaneously. Liara synthesizes cross-track findings, Legion provides orthogonal analysis.

#### Track A: Ghost Market Signal Fetch (Geth)

**Only fires if topic domain matches Ghost Market sources from Phase 0B.**

Dispatch one Geth instance per source. Parallel execution for speed.

**Dispatch template:**

```
Task(
  subagent_type: "geth",
  prompt: "Run: cd /path/to/home/work/personal/code/research/prediction-markets && source .venv/bin/activate && python -m src.cli signals --source {source} --json --output data/pipeline/sd-{issue}-{source}.json

Report ONLY: exit code and file path. Do NOT read or summarize the JSON.",
  description: "Fetch {source} signals for SD #{issue}",
  model: "haiku"
)
```

**Replace {source} with:** ooni, bonbast, eia, ofac, cloudflare_radar, tedpix, or usaspending

**Multiple parallel Geth dispatches:**

For a weekly brief covering Iran/geopolitics:
- Geth #1: OONI
- Geth #2: Bonbast
- Geth #3: TEDPIX
- Geth #4: Cloudflare Radar
- Geth #5: OFAC
- Geth #6: USAspending

All dispatch simultaneously. Shepard waits for all to return before synthesis.

**Output:** `data/pipeline/sd-{issue}-{source}.json` per source

**Error handling:**
- Exit code != 0 → Note source failure, proceed without that data
- Ghost Market adapters require `ghost_market.db` and must close connections properly (CLI handles cleanup)
- Rate limits (Bonbast, TEDPIX) → retry once after 5s, then note failure

#### Track B: Web Research + OSINT Planning (Liara)

**Skip if `--skip-web` flag is set.**

Liara receives:
- File paths to source config, persona reference, selected OSINT API docs
- Research questions from Phase 1C
- Ghost Market source list (if Track A is active)

**Mission:** (1) Web research on topic with findings structured by theme, (2) OSINT query plan as JSON

**Dispatch template:**

```
Task(
  subagent_type: "liara",
  prompt: "Intelligence research for Signal Dispatch {content_type} on {topic}.

Read these files yourself:
- Source config: /path/to/home/work/personal/code/research/signal-dispatch/config/sources.yaml
- Persona reference: /path/to/home/work/personal/code/research/signal-dispatch/docs/PERSONA.md
{For each selected OSINT API doc:}
- OSINT API docs: /path/to/home/work/personal/code/research/prediction-markets/docs/osint/{doc_name}.md

== CONTEXT ==
Content type: {weekly_brief | breaking_alert | deep_dive}
{If weekly_brief: "Multi-domain intelligence sweep across all active signals."}
{If breaking_alert: "Triggering anomaly: {anomaly description with baseline and current value}"}
{If deep_dive: "Single-topic comprehensive analysis on: {thesis statement}"}

{If Ghost Market track is active:}
📊 GHOST MARKET ACTIVE: These structured data sources are being collected in parallel:
{List of sources from Phase 0B routing: OONI, Bonbast, EIA, etc.}

You will NOT receive fetched signal data (Geth handles that in parallel). Your job is to design the analytical framework -- how should we interpret these signals in this topic's context?

For each signal source:
- What does this source measure in the real world?
- How does it connect to the topic/thesis?
- What magnitude of change would constitute a signal vs. noise?
- How should we combine multiple signals (convergence/divergence logic)?

== MISSION ==
TWO deliverables:

1. WEB RESEARCH: Conduct web research on these key questions:
{Paste research questions from Phase 1C}

Priority: resolution analysis > base rate > current conditions > contrarian case.

Return findings structured as:
### Theme 1: {name}
{Findings with specific data, dates, sources}

### Theme 2: {name}
{Findings with specific data, dates, sources}

{Continue for each research theme}

2. OSINT QUERY PLAN: Read the OSINT API capability briefs. For each relevant source, construct targeted queries that would find official government data relevant to this topic.

Think carefully about:
- What search terms capture the TOPIC/THESIS, not just keywords?
- What agency/type/date filters narrow results to useful documents?
- Which query types from each API are most relevant?

Return the query plan as a JSON code block in this exact format:
```json
{
  \"issue\": \"{issue-number}\",
  \"topic\": \"{topic}\",
  \"queries\": [
    {
      \"source\": \"federal_register\",
      \"queries\": [
        {
          \"type\": \"document_search\",
          \"params\": {
            \"term\": \"sanctions Iran\",
            \"publication_date\": {\"gte\": \"2026-02-01\"},
            \"agencies\": [\"treasury-department\"]
          }
        }
      ]
    }
  ]
}
```

If no OSINT sources are relevant to this topic, return an empty queries array. Better to return no plan than a bad plan that generates noise.

{If Ghost Market track is active:}
3. SIGNAL INTERPRETATION FRAMEWORK: For each Ghost Market source being collected:
{List sources from Phase 0B}

Explain (one paragraph per source):
- What does this source measure in the real world?
- How does it connect to this topic's resolution criteria?
- What magnitude of change would constitute a signal vs. noise?
- How should we combine multiple signals (convergence/divergence logic)?

This is NOT about fetching data (Geth does that). This is about designing the analytical lens we'll use to interpret the raw numbers when they arrive.

Example output:
\"OONI anomaly rate >15% for 3+ consecutive days + Cloudflare outages = systematic internet suppression, not random noise. This signals regime action under pressure, which increases conflict escalation risk. Baseline for Iran: 7-12% anomaly rate is normal. 18%+ sustained = signal. Single-day spikes (<24h) = likely event-driven, not structural.\"",
  description: "Research {topic} + OSINT plan{' + signal framework' if Ghost Market active}",
  model: "sonnet"
)
```

**CRITICAL:** Liara reads files herself. Never paste JSON content into dispatch prompt. Provide file paths only.

**Returns:**
1. Web research findings (structured by theme)
2. OSINT query plan JSON
3. Signal interpretation framework (if Ghost Market track is active)

#### Track C: Prediction Market Context (Geth)

**Always fires unless topic has no relevant markets.**

Search for relevant prediction markets to extract market-implied probabilities.

**Dispatch template:**

```
Task(
  subagent_type: "geth",
  prompt: "Run: cd /path/to/home/work/personal/code/research/prediction-markets && source .venv/bin/activate && python -m src.cli search \"{search_query}\" --json --output data/pipeline/sd-{issue}-markets.json

Report ONLY: exit code and file path. Do NOT read or summarize the JSON.",
  description: "Search markets for {topic}",
  model: "haiku"
)
```

**Replace {search_query} with topic keywords from Phase 1D.**

**Output:** `data/pipeline/sd-{issue}-markets.json`

### Phase 2B: OSINT Execution (Geth)

**Depends on:** Liara returning an OSINT query plan from Track B.

**Only runs if Liara returned an OSINT query plan.**

After Liara returns, extract the JSON query plan from her response and write it to a file:

```
Write(
  file_path="/path/to/home/work/personal/code/research/prediction-markets/data/pipeline/osint-plan-sd-{issue}.json",
  content="{Liara's query plan JSON}"
)
```

Then dispatch Geth to execute:

```
Task(
  subagent_type: "geth",
  prompt: "Run: cd /path/to/home/work/personal/code/research/prediction-markets && source .venv/bin/activate && set -a && source .env && set +a && python -m src.cli osint --plan-file data/pipeline/osint-plan-sd-{issue}.json --json --output data/pipeline/sd-{issue}-osint.json

Report ONLY: exit code and file path. Do NOT read or summarize the JSON.",
  description: "Execute OSINT plan SD #{issue}",
  model: "haiku"
)
```

**Output:** `data/pipeline/sd-{issue}-osint.json`

**Error handling:**
- OSINT execution fails → Note in brief but proceed to Phase 3. OSINT enriches, doesn't gate.
- API rate limits → CLI handles retry logic
- Empty results → Valid outcome. Not all queries have relevant documents.

### Phase 3: Synthesis (Liara + Legion)

**THE SIGNAL DISPATCH DIFFERENTIATOR.**

Two-layer synthesis: Liara's cross-track integration + Legion's orthogonal analysis.

**Mode selection:**

**SIMPLE (1-2 tracks):** Shepard synthesizes directly. Skip Liara synthesis dispatch. Legion still reviews.

**WAR-ROOM (3+ tracks):** Liara synthesizes first, then Legion provides orthogonal analysis.

#### Step 3A: Liara Cross-Track Synthesis

**Only runs when 3+ tracks fired in Phase 2.**

Liara receives:
- Her own web research findings (from Track B)
- Raw Ghost Market signal data (from Track A) -- if Track A fired
- OSINT execution results (from Phase 2B) -- if executed
- Prediction market context (from Track C)
- Signal interpretation framework she designed in Track B (if Ghost Market active)

**Mission:** Interpret raw signals in topic context and produce structured evidence synthesis.

**Dispatch template:**

```
Task(
  subagent_type: "liara",
  prompt: "Synthesize cross-track intelligence for Signal Dispatch #{issue} on {topic}.

Read these files:
{If Ghost Market track fired, for each source:}
- Ghost Market signals ({source}): /path/to/home/work/personal/code/research/prediction-markets/data/pipeline/sd-{issue}-{source}.json
- Source config: /path/to/home/work/personal/code/research/signal-dispatch/config/sources.yaml
{If OSINT executed:}
- OSINT results: /path/to/home/work/personal/code/research/prediction-markets/data/pipeline/sd-{issue}-osint.json
{If prediction market search ran:}
- Prediction markets: /path/to/home/work/personal/code/research/prediction-markets/data/pipeline/sd-{issue}-markets.json

== CONTEXT ==
Your prior research findings are available in your conversation history (Track B web research + signal interpretation framework).

Content type: {weekly_brief | breaking_alert | deep_dive}
Topic: {topic}

== MISSION ==
Interpret raw signals in this topic's context. Each signal becomes a structured finding with directional assessment and confidence.

{If Ghost Market track fired:}
For each Ghost Market signal source (read from sd-{issue}-{source}.json files):
1. What does the raw data show? (actual numbers, not interpretations yet)
2. Read sources.yaml rationale -- why does this source matter for this topic?
3. Apply the signal interpretation framework you designed in Track B
4. Magnitude check: Is this change significant or within normal variance?
5. Baseline comparison: What's the historical baseline for this metric?
6. Duration: Single event spike vs. sustained trend?
7. Cross-confirmation: Do other signals support or contradict?
8. Direction: What does this tell us about the underlying question?

Example output:
\"OONI Iran censorship: 18.2% anomaly rate (7-day avg), 3 active blocking incidents, sustained 72 hours.
Baseline: 7-12% is normal for Iran. 18% is elevated but not crisis-level (>30%).
Duration: 3 consecutive days = systematic suppression, not event spike.
Cross-confirm: Cloudflare Radar shows 2 network outages same timeframe (confirms deliberate action).
Bonbast rial spread widened from 11% to 19% over same period (economic stress correlate).
ASSESSMENT: Converging signals of regime action under pressure. Direction: Increased escalation risk.\"

{If OSINT executed:}
For each OSINT source that returned results:
1. What did the query find? (document types, dates, key content)
2. How does this connect to the topic/thesis?
3. What does it tell us about policy direction or official actions?
4. Does this confirm or contradict other signals?
5. Novelty: Is this information already widely known or homework edge?

{If prediction market data available:}
For prediction market context:
1. What markets are relevant? (titles, close dates)
2. What are current market-implied probabilities?
3. How do structured data signals compare to market prices?
4. Are there mispricings or information lags?

== OUTPUT FORMAT ==
Return a structured synthesis with these sections:

### Signal-by-Signal Interpretation
{For each signal source: one paragraph with raw data, baseline, magnitude check, cross-confirmation, directional assessment}

### Cross-Signal Convergence/Divergence
{Do multiple signals point the same direction? Conflicts? Which signals are stronger? Temporal alignment?}

### Net Directional Assessment
{After considering all signals, what's the overall direction and confidence? What changed from prior baseline?}

### Evidence Quality Rating
{How reliable is this evidence? High/Medium/Low confidence. Data quality issues? Information lag? Novelty?}

### Prediction Market Context
{If markets available: How do market-implied probabilities compare to structured data assessment? Mispricings?}

### Open Questions
{What data would improve confidence? What are we NOT seeing that we should track?}",
  description: "Synthesize SD #{issue} cross-track intelligence",
  model: "sonnet"
)
```

**Liara's synthesis becomes input to Legion's orthogonal analysis.**

**Output structure:** Shepard reads Liara's response and writes it to file:

```
Write(
  file_path="/path/to/home/work/personal/code/research/signal-dispatch/content/research/{issue-number}/synthesis.md",
  content="{Liara's synthesis output}"
)
```

#### Step 3B: Legion Orthogonal Synthesis

**ALWAYS RUNS. This is the Signal Dispatch differentiator.**

Legion receives:
- Liara's synthesis (from Step 3A or Shepard's notes if simple mode)
- ALL raw data files (Ghost Market signals, OSINT results, market context)
- Topic/thesis framing from Phase 0A

**Mission:** Find what Liara missed. NOT a review -- an orthogonal analysis.

**Three deliverables:**
1. **Pattern Detection** -- Statistical anomalies, temporal correlations, absence of expected signals, base rate violations
2. **Contrarian Synthesis** -- Strongest case AGAINST Liara's assessment. What data supports the opposite? What assumptions are weakest?
3. **Probability Calibration Check** -- Is each estimate anchored to base rates or narrative? Would an outside-view estimator agree?

**Dispatch template:**

```
Task(
  subagent_type: "legion",
  prompt: "Orthogonal analysis for Signal Dispatch #{issue} on {topic}.

You are NOT reviewing Liara's synthesis for approval. You are providing an independent, orthogonal perspective to catch what she missed or overweighted.

Read these files:
- Liara's synthesis: /path/to/home/work/personal/code/research/signal-dispatch/content/research/{issue-number}/synthesis.md
{For each data file produced in Phase 2:}
- {source} signals: /path/to/home/work/personal/code/research/prediction-markets/data/pipeline/sd-{issue}-{source}.json
{If OSINT executed:}
- OSINT results: /path/to/home/work/personal/code/research/prediction-markets/data/pipeline/sd-{issue}-osint.json
{If market search ran:}
- Markets: /path/to/home/work/personal/code/research/prediction-markets/data/pipeline/sd-{issue}-markets.json

== CONTEXT ==
Content type: {weekly_brief | breaking_alert | deep_dive}
Topic: {topic}
Liara's net assessment: {brief summary from synthesis.md}

== MISSION ==
Three deliverables. Be SPECIFIC. Generic \"looks good\" is worthless.

### 1. PATTERN DETECTION
Look for patterns Liara may have missed:
- **Statistical anomalies:** Are there outliers in the data that weren't flagged?
- **Temporal correlations:** Do signals cluster in time suspiciously? Lagged correlations?
- **Absence of expected signals:** What SHOULD be moving that isn't? Conspicuous silence?
- **Base rate violations:** Does the assessment drift from historical frequencies without justification?
- **Magnitude inconsistencies:** Are small movements being overinterpreted? Large movements underweighted?

Format: Bulleted findings. Each must reference specific data points.

Example:
\"- OONI anomaly rate peaked 3 days BEFORE Bonbast rial spike. Liara noted both but missed the temporal ordering. Historical pattern (checked last 6 events): currency stress follows censorship spikes by 48-96h. This supports her escalation thesis but strengthens confidence.
- TEDPIX volume spike (340% above 30-day avg) is an outlier. Checked historical TEDPIX data: only 2 prior events >300% in 18 months, both preceded regime announcements within 7 days. Liara didn't flag this.\"

### 2. CONTRARIAN SYNTHESIS
Build the strongest case AGAINST Liara's assessment. Steel-man the opposite view.

Questions to answer:
- What data points support the OPPOSITE conclusion?
- What assumptions in Liara's analysis are weakest?
- Where does she rely on narrative over base rates?
- What would invalidate her thesis?
- Are there alternative explanations for the observed signals?

Format: Structured argument. Be adversarial but intellectually honest.

Example:
\"Liara assesses increased escalation risk from converging signals. Contrarian case:

1. OONI anomaly rate at 18% is elevated but NOT crisis-level. Historical threshold for regime action: 30%+ sustained for 5+ days. Current 72h duration is SHORT.

2. Bonbast rial spread widening could be seasonal. Checked: similar pattern in Jan 2025 (spread 11% → 20% over 10 days) with NO subsequent escalation. Resolved peacefully.

3. Cloudflare outages (2 events) are SMALL. Baseline for Iran: 1-2 outages/week is normal infrastructure instability. Not necessarily coordinated.

4. Base rate for 'regime action within 72h' given these signal levels: Liara implies >60%. Historical: checked last 10 times OONI was 15-20% for 3 days → regime action occurred in 4/10 cases = 40% base rate. Her assessment may be overconfident.

Contrarian net: Signals show regime AWARENESS of pressure, not imminent ACTION. 40-45% escalation risk is more defensible than 60%+.\"

### 3. PROBABILITY CALIBRATION CHECK
Are Liara's probability assessments anchored properly?

- Is each estimate derived from base rates or from narrative?
- Does she cite specific reference classes?
- Would an outside-view estimator (using only the data, no domain knowledge) agree?
- Are there anchoring biases (starting from market price, starting from prior belief)?
- Is confidence level justified by data quality?

Format: Calibration notes with specific probability checks.

Example:
\"Liara doesn't state an explicit probability, but her language ('increased escalation risk', 'converging signals') implies 60-70% confidence.

Calibration check:
- Base rate from historical data: 40% (regime action following these signal levels)
- Evidence strength: 3 signals converging (OONI, Bonbast, Cloudflare). Modest LR ~ 1.5-2.0.
- Bayesian update: 40% prior * 1.75 LR = ~50% posterior (rough).
- Liara's implied 60-70% is 10-20pp above the data-driven estimate.

Diagnosis: Liara is anchoring on narrative (3 signals = strong) rather than base rate. Recommend dampening to 50-55% unless she can justify stronger LR from signal convergence.

Outside-view check: If I saw only the raw numbers (18% OONI, 19% Bonbast spread, 2 Cloudflare outages) without geopolitical framing, I'd estimate 45-50%. Her assessment is narrative-heavy.\"

== OUTPUT FORMAT ==
Three sections as described above. Be AGGRESSIVE. Your job is to find problems, not validate. If you can't find anything, you're not looking hard enough.",
  description: "Orthogonal analysis SD #{issue}",
  model: "sonnet"
)
```

**Legion returns orthogonal findings. Shepard writes to file:**

```
Write(
  file_path="/path/to/home/work/personal/code/research/signal-dispatch/content/research/{issue-number}/orthogonal.md",
  content="{Legion's orthogonal analysis}"
)
```

#### Step 3C: Present Combined Synthesis to Cooper

**Shepard reads both files:**
- `content/research/{issue-number}/synthesis.md` (Liara's cross-track synthesis)
- `content/research/{issue-number}/orthogonal.md` (Legion's orthogonal analysis)

**Present summary:**

```markdown
## Intelligence Synthesis: SD #{issue} on {topic}

### Liara's Assessment
{Key findings from synthesis.md}
- Signal-by-signal interpretation (bullet summary)
- Cross-signal convergence (what aligns)
- Net directional assessment (her conclusion)
- Evidence quality: {High/Medium/Low}

### Legion's Orthogonal Analysis
{Key findings from orthogonal.md}
- Patterns Liara missed: {bullet summary}
- Contrarian case: {strongest opposite argument}
- Probability calibration: {where Liara over/under-estimated}

### Convergence vs. Divergence
{Where they agree (high confidence) vs. where they diverge (needs judgment)}

**Proposed probability estimates:**
{For each event being assessed:}
- Event: {description}
- Liara's implied: {X}%
- Legion's calibration: {Y}%
- Recommended: {Z}% (rationale: {why})

**Cooper: Approve the final framing?**
{Wait for Cooper's decision on probability estimates and any synthesis adjustments}
```

**Cooper gates the next phase.** Do not proceed to Phase 4 without approval.

### Phase 4: Assessment Packaging (Shepard)

After Cooper approves synthesis, package the research brief.

#### Step 4A: Research Brief

Write comprehensive research brief to `content/research/{issue-number}/brief.md`:

**Structure:**

```markdown
# Signal Dispatch #{issue} -- Research Brief

## Executive Summary
{2-3 paragraphs: What moved, what changed, net assessment}

## Content Type
**Type:** {weekly_brief | breaking_alert | deep_dive}
**Topic:** {topic}
**Issue Date:** {date}

## Data Signals

{For each Ghost Market source that produced data:}
### {Source Name} (e.g., OONI, Bonbast, EIA)
**Signal:** {What this source measures, from sources.yaml}
**Refresh:** {Frequency}

**Raw Data:**
{Actual numbers with timestamps. Example:}
- Anomaly rate: 18.2% (7-day rolling average)
- Active blocking incidents: 3
- Measurement count: 247/hr (down from baseline 1,400/hr)
- Data timestamp: 2026-03-05T14:22 UTC

**Baseline Context:**
{What's normal for this metric. Example:}
- Historical baseline: 7-12% anomaly rate for Iran
- Crisis threshold: 30%+ sustained for 5+ days
- Current reading: Elevated but sub-crisis

**Signal Assessment:**
{Interpretation with magnitude, duration, cross-confirmation. From Liara's synthesis + Legion's patterns.}
- Magnitude: 50% above normal, below crisis
- Duration: 72 hours sustained (short-to-medium)
- Cross-confirmation: Bonbast rial spread widened same period (correlate)
- Net: Regime awareness of pressure, not imminent action

{Repeat for each Ghost Market source}

## Web Research

{Structured findings from Liara's Track B web research}

### Theme 1: {name}
{Findings with specific data, dates, sources}

### Theme 2: {name}
{Findings with specific data, dates, sources}

{Continue for each theme}

## OSINT Findings

{If OSINT executed, summarize results from sd-{issue}-osint.json}

**Sources Queried:**
- Federal Register: {query types and date ranges}
- Congress.gov: {query types}
- FEC: {query types}

**Key Documents:**
{List relevant documents with dates, agencies, summaries}

**Gaps:**
{What queries returned empty, what wasn't found}

## Prediction Market Context

{If market search ran, summarize from sd-{issue}-markets.json}

**Relevant Markets:**
{For each market:}
- Title: {full title}
- Close date: {date}
- Current price: YES ${price} / NO ${1-price}
- Implied probability: {XX}%

**Market-Data Divergence:**
{Where structured data assessment differs from market prices. Potential mispricings or information lag.}

## Synthesis

{Paste Liara's synthesis from synthesis.md}

### Signal-by-Signal Interpretation
{From synthesis.md}

### Cross-Signal Convergence/Divergence
{From synthesis.md}

### Net Directional Assessment
{From synthesis.md}

### Evidence Quality Rating
{From synthesis.md}

## Orthogonal Analysis

{Paste Legion's orthogonal analysis from orthogonal.md}

### Pattern Detection
{From orthogonal.md}

### Contrarian Synthesis
{From orthogonal.md}

### Probability Calibration Check
{From orthogonal.md}

## Probability Assessments

{For each event being tracked or assessed:}

### Event: {description with clear resolution criteria}
**Prior probability:** {X}% (from last issue or base rate)
**Evidence:**
{List key evidence items with directional impact}
- {Evidence 1}: {impact description}
- {Evidence 2}: {impact description}
- {Evidence 3}: {impact description}

**Updated probability:** {Y}%
**Direction:** {↑ up / ↓ down / → stable} ({magnitude} change)
**Resolution criteria:** {How this resolves to YES/NO, source of truth}
**Confidence:** {Low / Medium / High}
**Basis:** {Base rate / Model / Expert forecast / Hybrid}

{Repeat for each tracked event}

## Open Questions

{From Liara's synthesis + Legion's analysis}
- What data would improve confidence?
- What are we NOT seeing that we should track?
- Where do we need deeper research?
- What upcoming events are trigger points?

## Next Steps

{For weekly_brief:}
- Draft article covering {X} themes
- Update probabilities.json with new assessments
- Set triggers for next cycle

{For breaking_alert:}
- Draft alert with 24-48h timeline
- Identify trigger conditions for updates
- Flag markets for trade evaluation

{For deep_dive:}
- Draft comprehensive analysis on {thesis}
- Build full causal model from data to conclusion
- Publish with methodology transparency
```

#### Step 4B: Raw Data Archival (Geth)

Copy all pipeline data to issue directory for archival.

**Dispatch Geth:**

```
Task(
  subagent_type: "geth",
  prompt: "Copy Signal Dispatch #{issue} pipeline data to archive.

Source directory: /path/to/home/work/personal/code/research/prediction-markets/data/pipeline/
Destination: /path/to/home/work/personal/code/research/signal-dispatch/content/research/{issue-number}/data/

Files to copy (if they exist):
{For each Ghost Market source:}
- sd-{issue}-{source}.json → data/{source}-signals.json
{If OSINT executed:}
- sd-{issue}-osint.json → data/osint.json
- osint-plan-sd-{issue}.json → data/osint-plan.json
{If market search ran:}
- sd-{issue}-markets.json → data/markets.json

Create destination directory if it doesn't exist.
Skip files that don't exist (sources that didn't fire).
Report: Which files copied, which were missing.",
  description: "Archive SD #{issue} pipeline data",
  model: "haiku"
)
```

**Final directory structure:**

```
content/research/{issue-number}/
├── brief.md               # Comprehensive research brief
├── synthesis.md           # Liara's cross-track synthesis
├── orthogonal.md          # Legion's orthogonal analysis
└── data/                  # Raw data archive
    ├── ooni-signals.json
    ├── bonbast-signals.json
    ├── eia-signals.json
    ├── ofac-signals.json
    ├── cloudflare_radar-signals.json
    ├── tedpix-signals.json
    ├── usaspending-signals.json
    ├── osint.json
    ├── osint-plan.json
    └── markets.json
```

**After archival completes:**

Tell Cooper:
```
Intelligence collection complete for SD #{issue}.

Research brief: /path/to/home/work/personal/code/research/signal-dispatch/content/research/{issue-number}/brief.md

Data collected:
- Ghost Market: {N} sources
- OSINT: {Y/N}
- Prediction Markets: {Y/N}

Synthesis:
- Liara cross-track: {synthesis.md}
- Legion orthogonal: {orthogonal.md}

Ready to proceed to drafting? (Run `/draft {issue-number}` when ready)
```

## Error Handling

| Error | Action |
|-------|--------|
| Ghost Market adapter fails | Note in brief ("OONI data unavailable this cycle"), proceed without. Lower confidence if critical to topic. |
| Liara returns thin results | Note in brief, ask Cooper if more research time needed before proceeding. |
| OSINT execution fails | Note in brief. OSINT enriches, doesn't gate. Proceed to synthesis. |
| All Ghost Market sources fail | Flag as critical error. Cannot produce data-driven brief without structured feeds. Diagnose with Mordin. |
| Legion returns empty/generic | BAD SIGN. Legion must find something. If output is "looks good," Shepard rejects and re-dispatches with more aggressive prompt. |
| pm search returns no markets | Valid outcome. Not all topics have active prediction markets. Note absence in brief. |
| Prediction markets CLI fails | Note in brief, proceed without market context. |
| Issue number collision | Check if issue already exists. Ask Cooper: overwrite or increment? |

## Anti-Patterns

**Don't:**
- Paste JSON data into dispatch prompts → Give agents file paths
- Let Geth summarize data → Exit codes and file paths only
- Skip Legion → The orthogonal perspective is the differentiator
- Auto-proceed to drafting → Cooper gates every phase
- Treat breaking_alert as lightweight → Same depth, different framing
- Default to market price as assessment → Start from base rate and structured data
- Accept "looks good" from Legion → He must find problems or he's not trying
- Hardcode signal interpretation → Context-dependent, agents interpret
- Skip contrarian case → Prevents overconfidence, required for calibration

## Key Principles

- **File-based data flow:** CLI → JSON files → agents read files → markdown output
- **Agents design analytical frameworks BEFORE seeing data** (Track B signal interpretation framework)
- **War-room mode for 3+ tracks** (parallel dispatch), sequential for 1-2
- **Cooper approves track manifest before dispatch** (no autonomous parallel execution without approval)
- **Cooper reviews synthesis before proceeding to draft** (gate at Phase 3C)
- **Legion is adversarial, not validating** (finds problems, not approval)
- **Nested skepticism:** Liara synthesizes, Legion stress-tests, Shepard adjudicates
- **Methodology transparency:** Show all work, all data, all reasoning
- **Base rate anchoring:** Start from historical frequencies, update with evidence
- **Calibration over conviction:** Probability estimates must be falsifiable and trackable

## Related Commands

- **`/draft {issue-number}`** -- Next step after `/intel`. Turns research brief into newsletter article.
- **`/edit {issue-number}`** -- Style consistency, fact verification, probability format checks.
- **`/publish {issue-number}`** -- Format and publish to newsletter platform.

## Notes

- Signal Dispatch project root: `/path/to/home/work/personal/code/research/signal-dispatch`
- Prediction markets project root: `/path/to/home/work/personal/code/research/prediction-markets`
- Ghost Market adapters require `ghost_market.db` and proper connection cleanup (CLI handles)
- OSINT execution requires `.env` file with API keys
- Persona reference defines voice, not methodology (methodology is in this skill)
- Legion's orthogonal analysis is the newsletter's competitive advantage
- Issue numbers auto-increment if not specified
- All probability estimates must be falsifiable with clear resolution criteria
- Track record includes wins AND losses (no hiding failures)
