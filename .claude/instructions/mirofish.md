# MiroFish: Swarm Intelligence Reference

Pre-publication stress test for Signal Dispatch probability estimates. Builds a knowledge
graph from raw intelligence, spawns 100-238 simulated market participants (traders,
analysts, government officials, OSINT practitioners), runs social simulation across
simulated Twitter/Reddit, and produces a swarm-implied probability estimate with
surfaced counter-arguments.

**Purpose:** Adversarial validation from a different methodology. Discovers blind spots.
Generates "simulated market response" content for articles.

---

## When to Use

**Use MiroFish when:**
- `/intel` synthesis is complete, before `/draft` begins (Track E fires automatically after Phase 4)
- During `/review` Pass 4b calibration cross-check (if report exists)
- The issue has a strong directional thesis with tradeable implications
- You want a "Swarm Simulation" section in the article

**Skip MiroFish when:**
- No strong directional probability claim in the article
- Research synthesis is thin (<2,000 words) — thin seed = thin simulation
- Time constraint overrides adversarial validation

---

## Seed Document

**Feed the research synthesis, not the article draft.**

| Input | Quality |
|-------|---------|
| `content/research/{issue}/synthesis-updated.md` | Best |
| `content/research/{issue}/recession-synthesis.md` (or equivalent) | Best |
| `content/research/{issue}/brief.md` | Acceptable |
| Multiple synthesis files combined | Good for complex issues |

**Target:** 2,000-6,000 words. The recession E2E used 5,632 words and produced 238 agents.
A thin 700-word brief produced 85 agents and 8 actions — barely worth running.

**Structure that produces rich simulations:**
- Intelligence header (classification, date range, confidence level)
- Key indicators table (source, reading, delta, significance)
- Primary thesis with probability estimate
- Signal convergence / divergence analysis
- Counter-thesis with supporting evidence
- Geopolitical risks and open questions
- Named entities, specific numbers, concrete data

---

## How to Run

```bash
# Blueprint (recommended)
omni-tool blueprint run mirofish-predict \
  --var name="sd-issue-{N}" \
  --var file="content/research/{N}/synthesis-updated.md" \
  --var topic="<the core prediction question for this issue>"

# Individual steps
omni-tool mirofish graph build \
  --project sd-issue-{N} \
  --file content/research/{N}/synthesis-updated.md \
  --topic "<question>" \
  --wait
omni-tool mirofish sim run --project <project-id> --rounds 10
omni-tool mirofish report get --project <project-id> --format text
```

**Health check:**
```bash
omni-tool mirofish health
```

---

## Interpreting Results

**Key metrics to read:**
- Entity count — graph richness; more entities = richer simulation
- Agent count — simulation population size
- Action count — simulation depth (104 actions >> 8 actions)
- Swarm-implied probability — the number to compare against editorial estimate

**Divergence thresholds (from `/review` Pass 4b):**
- <15pp divergence: note, no action required
- ≥15pp divergence: examine the swarm's framing — what assumption is it revealing?
- Convergence: strengthens editorial estimate; note as supporting evidence

**What to extract from the report:**
- Counter-arguments not present in your analysis
- Entity relationships you missed
- Sentiment distribution across agent types (traders vs analysts vs officials)
- The swarm's primary debate topics — these reveal what "the market" would focus on

Reports currently default to Chinese (Gemini config). Extract English-quoted sections
or translate key passages for the divergence check.

---

## Article Integration

Include as a "Swarm Simulation" or "Simulated Market Response" section.

**Template:**
> We ran this intelligence through a swarm simulation of {N} market participants over
> {M} rounds. Key debate points: [from report]. Swarm implied probability: {X}% vs
> our estimate of {Y}%.

**Methodology note:**
> MiroFish swarm intelligence engine, {N} agents derived from knowledge graph entities.

Extract specific agent quotes for color (translate if necessary). Differentiator: no
other newsletter stress-tests predictions with swarm intelligence before publication.

---

## Workflow Integration

| Phase | Role |
|-------|------|
| `/intel` Track E | Fires after Phase 4 synthesis. Produces `mirofish-report.md` in research dir. |
| `/review` Pass 4b | Reads `mirofish-report.md`. Compares swarm probability vs article estimates. |

**Handoff artifact:** `content/research/{issue}/mirofish-report.md`

Pass 4b auto-skips if `mirofish-report.md` is absent — no manual intervention needed.

---

## Prerequisites

MiroFish-local must be running before any command:

```bash
cd ~/work/personal/code/MiroFish-local
docker start mirofish-neo4j
cd backend && .venv/bin/python run.py
```

Simulation dashboard: `http://localhost:3000/simulation/<sim_id>/start`
(Vue frontend must be running separately to access the dashboard)

MCP server available for direct Claude Code integration when running in-session.

---

## Gotchas

- **Rate limits:** Large seed docs hit Gemini rate limits. The 5,632-word recession brief
  needed retries. Build step may require multiple attempts.
- **Preparation time:** 238 agents = 20+ minutes before simulation starts.
- **Report language:** Chinese by default. Translate key sections for the divergence check.
- **Quality floor:** Thin seed = thin simulation. Include concrete numbers, named entities,
  specific dates. Below 30 action count, results are too shallow to include in the article.
- **`--worktree` not applicable here:** Factory mode flags are for multi-instance runs.
