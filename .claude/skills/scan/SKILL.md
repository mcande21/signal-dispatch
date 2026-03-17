# `/scan` -- Environmental Signal Sweep

*"Poke until it hurts. Find what's moving."*

Broad environmental scan across multiple geopolitical domains. Launches parallel workers to sweep the world for anomalies, breaking patterns, and underreported signals. The output is a signal map -- not an article, but the raw material that identifies what's worth investigating.

## Purpose

`/scan` is the first step in the Signal Dispatch workflow. Before you know what to write about, you need to see what's moving. This skill launches a swarm of researchers across 10-15 domains simultaneously, looking for anomalies, disruptions, and signals that don't fit the narrative.

**Use `/scan` when:**
- Starting a new issue cycle and need to find the story
- World events have shifted and you need a fresh read
- Looking for what's being missed while everyone watches the obvious story
- Regular cadence check (bi-weekly before each brief)

**Use `/recon` instead when:**
- You already know the topic and need depth
- Single-topic deep research, not broad sweep

**Use `/intel` instead when:**
- You have a specific issue topic and need structured collection from Ghost Market adapters + OSINT feeds

## Invocation

```bash
/scan                          # Full 12-domain sweep
/scan --focus shadows          # What's being missed (underreported signals)
/scan --focus financial        # Financial/market shadow moves
/scan --focus institutional    # Institutional decay signals
/scan --focus <custom>         # Custom domain focus
```

## Scan Domains (Default Full Sweep)

| # | Domain | What Workers Look For |
|---|--------|----------------------|
| 1 | Sanctions & economic warfare | OFAC actions, evasion networks, secondary sanctions |
| 2 | Internet freedom & digital authoritarianism | Shutdowns, VPN crackdowns, surveillance tech |
| 3 | Energy & commodities | Pipeline disruptions, LNG, SPR, OPEC, rare earth |
| 4 | Military & conflict | Deployments, weapons transfers, satellite imagery |
| 5 | Trade coercion & economic statecraft | Tariffs, route disruptions, trade agreement collapses |
| 6 | Democratic backsliding | Election manipulation, judicial capture, press freedom |
| 7 | Prediction markets & risk pricing | Geopolitical contracts, mispricings, volume spikes |
| 8 | US government unusual activity | EOs, emergency declarations, DOD budget shifts |
| 9 | Climate & natural disaster cascades | Compounding events, food crisis, tipping points |
| 10 | Emerging tech & AI governance | AI regulation, chip controls, quantum, biotech |
| 11 | Financial shadow moves | SWF repositioning, debt crises, gold hoarding, shadow banking |
| 12 | Institutional decay | Agency gutting, journalism collapse, election infrastructure |

### Focus Presets

**`--focus shadows`** (6 workers):
Domains 6, 8, 11, 12 + "What is the dominant news story distracting from?" + "What moves are being made under cover of the current crisis?"

**`--focus financial`** (6 workers):
SWF repositioning, quiet debt crises, gold/commodity hoarding, private credit/shadow banking, currency collapses, US fiscal position

**`--focus institutional`** (6 workers):
UN/international org defunding, federal agency capacity, election infrastructure, academic/research pressure, local journalism, public health surveillance

## Pipeline

### Phase 1: Domain Assignment

Shepard assigns domains to workers based on scan type (full or focused). Each worker gets:
- Domain name and description
- 3-4 specific search queries
- Instructions to report anomalies, not just news
- Date context (what's current)

### Phase 2: Parallel Sweep

All workers launch simultaneously via `omni-tool spawn`:
- Liara system prompt injected
- $0.75-1.00 per worker (broad sweep, not deep)
- 180s timeout each
- WebSearch + WebFetch tools

### Phase 3: Signal Aggregation

Collect all worker outputs. For each domain, extract:
- What's actually happening (facts)
- What's unusual or anomalous
- Confidence level (strong/moderate/weak)
- Cross-domain connections

### Phase 4: Cross-Domain Synthesis

Legion reads all domain reports and produces:
- **Hot Signals**: Things that are actively moving and consequential
- **Shadow Signals**: Things being missed because of the dominant story
- **Convergences**: Where multiple domains point the same direction
- **Deep Dive Candidates**: Topics worth a full `/recon` or `/intel` run
- **Tradeable Signals**: Anything with market implications

### CHECKPOINT: Signal Review

Cooper reviews the signal map and decides:
- Which signals to pursue for the next issue
- Whether to launch `/recon` on a specific topic
- Whether any signals warrant a breaking alert

### Phase 5: Signal Map Output

Produces a structured signal map:

```markdown
# Signal Dispatch Environmental Scan
## Date: YYYY-MM-DD

## Hot Signals (actively moving)
1. [signal] -- [one-line summary] -- [confidence]
2. ...

## Shadow Signals (being missed)
1. [signal] -- [one-line summary] -- [why it's missed]
2. ...

## Cross-Domain Convergences
[Where multiple domains reinforce the same thesis]

## Deep Dive Candidates
[Ranked by signal strength + novelty + actionability]

## Tradeable Signals
[Market implications, prediction market edges]

## Raw Domain Reports
[Full output from each worker, organized by domain]
```

**Output:** `content/research/scans/scan-{date}.md`

## Execution

```bash
# Via shell script
./run-scan.sh [--focus <preset>]

# Via Shepard (when invoked as skill)
# Shepard parses args, launches workers, presents signal map
```

## Relationship to Other Skills

```
/scan (broad sweep, find the story)
  ↓ identifies topic
/recon (deep research swarm on that topic)
  ↓ produces research brief
/intel (structured OSINT + Ghost Market data collection)
  ↓ supplements with adapter data
/draft (collaborative writing from research)
  ↓ produces article
/review (5-pass editorial)
  ↓ validates
/publish (format + publish to Substack)
```

`/scan` feeds `/recon`. `/recon` feeds `/draft`. They're sequential phases of the Signal Dispatch production pipeline, each appropriate at different stages.

## Ghost Market Integration (from prediction-markets /scan)

The prediction-markets project provides 16 structured data adapters via `pm signals` CLI. During a `/scan`, these run as a parallel track alongside the web research swarm -- structured data + open-source web research converging on the same signal map.

### Adapter Dashboard Poll

Before launching web workers, run the adapter dashboard to establish baselines:

```bash
cd /Users/cooperanderson/projects/prediction-markets
pm signals --check --json > /tmp/sd-scan/adapter-dashboard.json
```

This polls all 16 adapters and returns current values + freshness. Workers receive this context.

### Signal Group Mapping

The prediction-markets project maps geopolitical domains to data sources via `market_config.json`. Signal Dispatch uses the same mapping:

| Signal Group | Adapters | What Converges |
|--------------|----------|---------------|
| Iran | OONI, Bonbast, TEDPIX, VIIRS, GDELT | Internet + rial + market + hotspots + news volume |
| Russia-Ukraine | Oryx, ENTSOG, GDELT | Equipment losses + gas flows + news volume |
| Venezuela | dolarVzla, OONI | Parallel rate + internet freedom |
| Europe Energy | AGSI, ENTSOG, ECB | Gas storage + pipeline flows + exchange rates |
| US Policy | USAspending, OFAC | Procurement patterns + sanctions actions |
| Trade | Comtrade, EIA | Trade flows + energy supply |
| Conflict | VIIRS, Oryx, GDELT | Satellite fire data + losses + media |

### Specific Adapter Fetches (run in parallel with web workers)

```bash
# Iran signal group
pm signals --source ooni --param probe_cc=IR --json
pm signals --source bonbast --json
pm signals --source viirs --param country=IR --json

# Energy
pm signals --source agsi --param country=EU --json
pm signals --source eia --json
pm signals --source entsog --json

# Conflict
pm signals --source oryx --json
pm signals --source gdelt --param query="military conflict" --json

# Policy
pm signals --source ofac --json
pm signals --source usaspending --json
```

### Channel Convergence Model (from prediction-markets)

**Key methodology borrowed from PM /scan:** When multiple independent channels surface the same signal, confidence scales non-linearly.

| Channels Converging | Signal Strength | Action |
|--------------------|----------------|--------|
| 3+ channels (web + adapter + prediction market) | HIGHEST | Immediate deep dive candidate |
| 2 channels (any combination) | HIGH | Strong candidate, investigate |
| 1 channel only | MEDIUM | Monitor, may be noise |

**Example convergence:** OONI shows Iran measurement count dropping (adapter) + web research finds internet blackout reports (web worker) + Kalshi Iran contracts spiking in volume (prediction market) = **3-channel convergence on Iran crisis signal**.

The synthesis step explicitly looks for these multi-channel convergences and ranks deep dive candidates by convergence count.

### Prediction Market Layer

Alongside Ghost Market adapters, `/scan` checks prediction market pricing for anomalies:

```bash
# Search for geopolitical contracts
pm search "Iran" --json
pm search "recession" --json
pm search "NATO" --json
pm search "tariff" --json
```

Prediction market prices that diverge from our structured data assessment represent either a mispricing (opportunity) or information we don't have (gap to investigate).

### Baseline + Threshold Logic

Every adapter has documented "normal" and "signal" ranges (from the Ghost Market research playbook at `/Users/cooperanderson/projects/prediction-markets/.claude/instructions/ghost-market-research-playbook.md`):

| Adapter | Normal Range | Signal Threshold | What It Means |
|---------|-------------|-----------------|---------------|
| OONI (Iran) | >1000 measurements/hr | <200/hr | Censorship event likely |
| Bonbast (rial) | 5-10% spread | >15% spread | Economic stress |
| AGSI (EU gas) | >50% storage | <35% entering spring | Refill crisis risk |
| VIIRS (conflict zone) | <10 hotspots/day | >50 hotspots/day | Active military operations |
| dolarVzla | <20% parallel spread | >40% parallel spread | Capital flight / regime stress |
| GDELT | <10 articles/day on topic | >25 articles/day | Media attention spike |

When an adapter reading crosses a threshold, it's automatically flagged in the signal map.

## Natural Language Routing (from prediction-markets /scan)

The PM /scan skill uses a routing decision tree that maps user intent to the right discovery mechanism. Signal Dispatch adapts this:

| User Says | Route To |
|-----------|----------|
| "scan the world" / "what's moving" | Full 12-domain sweep |
| "what am I missing" / "shadows" | Shadow focus (underreported signals) |
| "check the data" / "adapters" | Ghost Market dashboard poll only |
| "Iran" / "energy" / specific topic | Focused domain scan + relevant adapters |
| "markets" / "what's mispriced" | Prediction market scan + adapter comparison |
| "convergence" / "what's lining up" | Multi-channel convergence analysis |

## Budget

| Scan Type | Workers | Adapters | Cost |
|-----------|---------|----------|------|
| Full sweep (12 domains) | 12 web + synthesis | All 16 | ~$12-15 |
| Focused (6 domains) | 6 web + synthesis | Relevant subset | ~$7-9 |
| Adapter-only dashboard | 0 web workers | All 16 | ~$2 (synthesis only) |
| Convergence check | 6 web + synthesis | All 16 | ~$10-12 |

## Notes

- `/scan` is designed to run bi-weekly, before each Signal Dispatch brief
- The signal map is NOT the article -- it's the intelligence that identifies what the article should be about
- Multiple scans can be compared over time to track signal evolution
- The "shadow signals" focus is the Signal Dispatch differentiator -- looking where nobody else is looking
- Scan results are saved for historical comparison at `content/research/scans/`
- **Channel convergence is the secret weapon** -- when structured data, web research, and prediction markets all point the same direction, that's a real signal
- Agents should design their analytical framework BEFORE seeing data (PM /scan principle) -- prevents confirmation bias

---

*"The data pipelines don't care where the spotlight is."*
