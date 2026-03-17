# `/recon` -- Swarm Research Pipeline

*"Deploy the army. Synthesize the intel. Pull the threads that matter."*

Hybrid research pipeline combining omni-tool spawn workers (broad recon) with targeted deep pulls and adversarial challenge. Produces a structured research brief ready for `/draft`.

## Purpose

When a topic needs comprehensive coverage across many angles simultaneously -- more than Liara or Geth can cover in a single dispatch -- `/recon` launches a swarm of parallel researchers, synthesizes their findings, identifies gaps, runs deep pulls on high-signal threads, and stress-tests the thesis through adversarial challenge.

**Use `/recon` when:**
- Topic has 5+ independent research angles
- Breadth matters more than depth initially (you'll go deep on what matters)
- Time is available for a full pipeline run (~15-20 minutes)
- You want structured probability assessment with adversarial validation

**Use `/intel` instead when:**
- Topic is narrow enough for 2-3 focused dispatches
- You need results in under 5 minutes
- The research angles are already known

## Invocation

```bash
/recon <topic> --issue <number> [--workers N] [--budget LOW|MED|HIGH]
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `topic` | Yes | -- | Research topic in quotes |
| `--issue` | Yes | -- | Signal Dispatch issue number |
| `--workers` | No | 8 | Number of parallel research workers |
| `--budget` | No | MED | Budget tier: LOW ($8), MED ($18), HIGH ($30) |

**Budget tiers:**

| Tier | Workers | Worker $ | Deep Pulls | Deep $ | Synthesis | Adversarial | Total |
|------|---------|----------|------------|--------|-----------|-------------|-------|
| LOW | 6 | $0.50 | 2 | $1.00 | $2.00 | $1.00 | ~$8 |
| MED | 8 | $1.00 | 3-5 | $2.00 | $3.00 | $2.00 | ~$18 |
| HIGH | 12 | $1.50 | 5 | $3.00 | $4.00 | $3.00 | ~$30 |

## Pipeline Phases

### Phase 1: Topic Decomposition

Shepard (or a Claude spawn) breaks the topic into N independent research angles. Each angle gets:
- A specific mission statement
- 3-5 web search queries
- Clear scope boundaries (non-overlapping)

**Output:** `/tmp/sd-recon/angles.json`

### Phase 2: Swarm Launch (Broad Recon)

N parallel `omni-tool spawn` workers launch simultaneously. Each worker:
- Receives Liara's system prompt (Shadow Broker research persona)
- Gets one specific research angle
- Has web search + web fetch tools
- Runs independently with its own context window and budget
- Returns a structured intelligence brief

**Output:** `/tmp/sd-recon/workers/worker-{0..N}.json`

### Phase 3: Collect + Synthesize

All worker outputs are aggregated into a single file. Legion (synthesis agent) reads all results and produces:
- Signal convergence (where workers agree)
- Signal divergence (where they contradict)
- Key data points table (20-25 most important numbers)
- Preliminary probability assessment
- Research gaps
- Recommended deep pull targets (3-5 threads)

**Output:** `content/research/{issue}/synthesis.md`

### CHECKPOINT 1: Review Synthesis

Cooper reviews the synthesis and decides:
- Which deep pull targets to pursue
- Whether any angles are completely missing
- Whether to add more workers or proceed

### Phase 4: Deep Pulls (Targeted Research)

3-5 targeted spawn workers launch on approved threads. Each worker:
- Gets the "Deep Pull" Liara prompt (go beyond surface, find primary sources)
- Has higher budget ($2-3 per worker)
- Focuses on: primary sources, quantified mechanisms, historical precedent, contrarian evidence

**Output:** `/tmp/sd-recon/deep-pulls/deep-{1..5}.json`

### Phase 5: Integration + Adversarial Challenge

Legion integrates deep pull findings into the synthesis. Then Grunt + Jack run adversarial challenge:
- What assumptions are untested?
- Which data is weakest?
- Why is the thesis wrong?
- What's the strongest counter-argument?

**Output:**
- `content/research/{issue}/synthesis-integrated.md`
- `content/research/{issue}/adversarial.md`

### CHECKPOINT 2: Review Adversarial

Cooper reviews adversarial findings and decides:
- Does the thesis survive?
- Any probability adjustments needed?
- Ready for final brief assembly?

### Phase 6: Final Brief Assembly

Produces the structured research brief in Signal Dispatch format:
- Executive assessment
- Evidence base (organized by theme)
- Key data points table
- Probability assessment (bull/bear/base with resolution criteria)
- Adversarial notes
- What the market is missing
- Complete source list

**Output:** `content/research/{issue}/brief.md`

## Execution

The pipeline runs via `run-recon.sh` in the project root:

```bash
./run-recon.sh "<topic>" <issue_number> [worker_count] [worker_budget] [deep_pull_budget]
```

Or via the omni-tool blueprint (when available):
```bash
omni-tool blueprint run sd-recon \
  --var topic="<topic>" \
  --var issue_number=<N>
```

**When invoked as a skill**, Shepard:
1. Parses arguments
2. Confirms the research plan with Cooper
3. Runs `run-recon.sh` in background
4. Monitors progress and presents checkpoints
5. After completion, reads the brief and presents a summary

## Liara System Prompt (Injected into Workers)

```
You are Liara, the Shadow Broker. Information is power. You find what is
hidden -- not just what is documented, but what is buried or deliberately
obscured. You trace connections others miss.

Your mission: Research the assigned topic thoroughly using web searches.
For every claim, cite the source URL. Distinguish between hard data
(government statistics, official reports) and analyst commentary. Note
confidence levels.

Format:
## Findings [detailed, sourced]
## Key Data Points [specific numbers, the receipts]
## Confidence Assessment [how confident and why]
## Gaps [what you couldn't find or verify]
## Cross-References [connections to other domains]
```

## Deep Pull Prompt (Injected into Phase 4 Workers)

```
You are Liara, the Shadow Broker. DEEP PULL mission -- go beyond surface
searches. Find:
- Primary sources (government data, official reports, court filings)
- Quantified transmission mechanisms (how does X cause Y, with numbers)
- Historical precedent (when has this happened before, what resulted)
- Contrarian evidence (what argues AGAINST the thesis)
- The data point nobody else has found

Format:
## Deep Findings [detailed, sourced, quantified]
## The Number That Matters [single most important data point]
## Historical Precedent [when has this happened before]
## Contrarian Evidence [what argues against the thesis]
## Sources [all URLs]
```

## File Map

| File | Purpose |
|------|---------|
| `run-recon.sh` | Shell script pipeline runner |
| `~/...blueprints/sd-recon.yaml` | Blueprint YAML (for omni-tool when available) |
| `/tmp/sd-recon/angles.json` | Topic decomposition |
| `/tmp/sd-recon/workers/` | Broad sweep worker outputs |
| `/tmp/sd-recon/deep-pulls/` | Deep pull worker outputs |
| `content/research/{issue}/synthesis.md` | Initial synthesis |
| `content/research/{issue}/synthesis-integrated.md` | Post-deep-pull synthesis |
| `content/research/{issue}/adversarial.md` | Adversarial challenge |
| `content/research/{issue}/brief.md` | Final research brief |

## Error Handling

**Workers hit budget limits:**
- Common at LOW tier. Partial results are still collected.
- Synthesis step handles incomplete worker outputs.
- If >50% of workers failed, flag in synthesis and recommend re-run at higher budget.

**Synthesis fails to identify deep pull targets:**
- Fall back to gap analysis from worker outputs
- Shepard manually selects deep pull topics

**Adversarial challenge is weak:**
- Re-run with higher budget
- Or dispatch Grunt and Jack as separate Normandy agents for more rigorous challenge

## Notes

- Total pipeline runtime: ~15-20 minutes at MED tier
- Workers are fully independent -- no coordination between them
- The power is in the synthesis, not the individual workers
- Deep pulls are where the real edge comes from -- broad sweep identifies where to look, deep pulls find what matters
- Always review synthesis before deep pulls -- human judgment on thread selection is the highest-leverage decision in the pipeline

---

*"The swarm is recon. The squad is operations. Use both."*
