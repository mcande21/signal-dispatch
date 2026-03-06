# Mission: Persona Synthesis + Build Phase 1

## Status: READY TO EXECUTE

## Context

War room session 14039717 dispatched 3 agents to research and design the Signal Dispatch newsletter persona. This mission picks up their results and continues into the build phase.

## Phase 1: Synthesize War Room Results

### Artifacts to Read

War room sitreps (check both locations -- agents may have finished or session may have expired):

**Primary (war room session):**
- `/tmp/normandy-collab-14039717/sitreps/liara-1-sitrep.md` -- Credibility recon: what makes geopolitical intelligence authors trusted
- `/tmp/normandy-collab-14039717/sitreps/kasumi-1-sitrep.md` -- Social engineering: trust architecture, authority signals, persona construction framework
- `/tmp/normandy-collab-14039717/sitreps/kelly-1-sitrep.md` -- Personality design: voice archetype, traits, sample writing

**Additional war room data:**
- `/tmp/normandy-collab-14039717/board/` -- Inter-agent messages and findings
- `/tmp/normandy-collab-14039717/traces/` -- Structured discoveries

**If war room session expired** (OS cleaned /tmp), check background task outputs:
- Liara (persona recon): agent af63713
- Kasumi (social engineering): agent a846d1f
- Kelly (personality design): agent aa29b8a

**Competitive recon** (from earlier in session):
- `/tmp/newsletter-competitive-recon.md` -- Liara's full competitive landscape analysis

### Synthesis Tasks

1. Read all three sitreps
2. Run war room convergence: `normandy-cache --session-path /tmp/normandy-collab-14039717 convergence -t 0.75`
3. Identify where all three agents agree (convergences = high confidence)
4. Resolve contradictions (e.g., real name vs pen name debate)
5. Produce unified persona profile

## Phase 2: Scaffold Persona into Project

### Create: `config/persona.yaml`

The persona configuration file. Should include:
- Name (real name, pen name, or hybrid)
- Bio (short and long versions)
- Background/origin story
- Voice characteristics (3-5 core traits)
- Emotional register (what range of emotions expressed)
- Signature phrases or verbal habits
- Anti-patterns (what this persona NEVER does)
- Trust timeline (what to establish by month 1, 3, 6, 12)
- Platform presence plan (which platforms, posting patterns)
- Visual identity notes (aesthetic direction)

### Create: `docs/PERSONA.md`

Detailed persona reference document:
- Full background narrative
- Voice guide with examples
- Sample opening paragraphs for each content type (weekly brief, breaking alert, deep dive)
- How the persona handles being wrong (critical for calibration credibility)
- Consistency checklist (what must stay constant across all touchpoints)
- Red flags to avoid

### Create: `docs/STYLE-GUIDE.md`

Writing style guide derived from persona:
- Tone and register
- Word choice preferences and prohibitions
- Sentence structure patterns
- How to present probability estimates
- How to present data
- How to cite sources
- How to handle uncertainty
- Template for corrections/updates

## Phase 3: Continue Build Roadmap (Phase 1 from BUILD.md)

After persona is scaffolded, continue with the research pipeline:

### 3.1 Collector Implementation
- Subprocess wrapper for `pm signals --source X --json`
- Batch collection across multiple sources
- Snapshot storage to `content/research/{date}/`
- Error handling for known adapter issues (Cloudflare auth, EIA series_id)

### 3.2 OONI Monitoring
- Scheduled polling configuration
- Anomaly detection: measurement_count threshold (>200/hr = reconstitution signal)
- Alert trigger mechanism

### 3.3 Issue #0: Iran Deep Dive
- Format the Iran threat assessment from this session as Issue #0
- Source material: `/tmp/iran-recon-web-research.md` (if still exists)
- Backup: The analysis was also discussed in the prediction-markets session on 2026-03-05
- Apply the deep_dive template from `src/paper/templates/deep_dive.md`
- Apply the persona voice from the style guide

## Key Files in Signal Dispatch

| File | Purpose |
|------|---------|
| `.claude/CLAUDE.md` | Project orientation |
| `docs/BUILD.md` | Full 5-phase build roadmap |
| `config/newsletter.yaml` | Newsletter config (schedule, tiers, platform) |
| `config/sources.yaml` | Data source mapping to prediction-markets adapters |
| `src/paper/templates/` | Article templates (weekly_brief, breaking_alert, deep_dive) |

## Data Dependencies

Signal Dispatch wraps the prediction-markets project for data:
- **Project root:** `/Users/cooperanderson/work/personal/code/research/prediction-markets/`
- **CLI:** `cd prediction-markets && source .venv/bin/activate && python -m src.cli signals --source X --json`
- **Adapters:** OONI, OFAC, Bonbast, EIA, Cloudflare Radar, TEDPIX, USAspending
- **OSINT:** Federal Register, Congress, FEC

## Session Notes (2026-03-05)

### What was accomplished this session:
- Full Iran threat recon (all 7 Ghost Market adapters + OSINT + 30+ web sources)
- Signal Dispatch project scaffolded (23 files, 4 pipelines, git initialized)
- Competitive landscape validated (gap confirmed -- nobody does structured data + probabilities + prediction market bridge)
- War room launched for persona construction (3 agents: Liara, Kasumi, Kelly)

### Key competitive findings:
- $15-25/month price point is wide open
- Polymarket-Substack partnership is a tailwind (native market data embeds)
- Calibration tracking is the moat (nobody else publishes accuracy)
- Iran is the beachhead (7 live adapters, nobody covers Iran-internal in English)
- Start Substack for discovery, build for Beehiiv migration at scale

### Iran recon key findings:
- Active shooting war since Feb 28, 2026 (Operation Epic Fury)
- Khamenei killed, IRGC retaliating across 9 countries
- OONI data confirms Iran internet at 1-4% (flatlined post-strikes)
- Lone-wolf attacks highest near-term probability (Austin incident Mar 1)
- Cyber threats elevated (60+ hacktivist groups, CISA at 38% staffing)
- Think tank consensus on elevated homeland risk
- East Coast primary geographic risk (NYC, DC, NJ -- documented sleeper cell activity)
- No direct "Iran attacks US" market on Kalshi; nuclear deal market at $0.095

### Quick wins identified:
1. Set up Substack account (10 min, zero code)
2. Format Iran analysis as Issue #0
3. Create Twitter/X presence
4. Publish during crisis window for maximum audience capture
