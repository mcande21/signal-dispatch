# Signal Dispatch -- Geopolitical Intelligence Newsletter

## Status: Foundation + Delta Engine Phase 1

Geopolitical intelligence newsletter combining structured OSINT data feeds with analytical synthesis and prediction market context.

## Workflow

Four skills, executed in sequence for each issue via `/new-issue` mission:

1. **`/intel`** (`.claude/skills/intel/SKILL.md`) -- Full intelligence collection. 5-phase war-room capable research with Ghost Market signals, OSINT, web research, and Legion orthogonal synthesis.
2. **`/draft`** (`.claude/skills/draft/SKILL.md`) -- Collaborative writing. Cooper and Shepard draft together using templates and persona voice.
3. **`/review`** (`.claude/skills/review/SKILL.md`) -- 6-pass editorial review. Style guide (Tali), fact verification (Shepard), probability format, calibration cross-check, persona consistency (Kelly), delta verification (Shepard).
4. **`/publish`** (`.claude/skills/publish/SKILL.md`) -- Format for Substack, archive, update state, social thread outline.

**This is a collaborative workflow, not an automated pipeline.** Skills provide structure. Cooper gates every phase transition.

## Data Pipeline

Self-contained. All adapters live in `src/adapters/` with own venv and dependencies.

**Adapters (`src/adapters/`):**
- Ghost Market (16): OONI, OFAC, Bonbast, EIA, Cloudflare Radar, TEDPIX, USAspending, GDELT, ENTSOG, AGSI, ECB, Comtrade, EIA Grid, VIIRS/FIRMS, dolarVzla, Oryx
- OSINT (3): Federal Register, Congress, FEC
- Standalone: FRED, NOAA, Kalshi (prediction markets)

**Delta Engine (`src/delta/`):**
- `daemon.py` -- Cron-driven poller (hot every 6h, warm daily, cold on-demand)
- `engine.py` -- Delta computation (numeric, event_set, binary, categorical)
- `sources.py` -- 22 poll functions wrapping local adapters
- `clusters.py` -- Correlated delta detection (Iran, Hormuz, Europe energy, conflict, US macro)
- State at `content/state/deltas/` (runtime data, gitignored)

**Active mission:** `.claude/missions/delta-engine.md` -- Phases 2-5 remaining

**Origin:** Adapters consolidated from prediction-markets project (`/Users/cooperanderson/projects/prediction-markets/`). SD is now independent.

## Content Types

| Type | Frequency | Template | Description |
|------|-----------|----------|-------------|
| Weekly Brief | Bi-weekly | `weekly_brief.md` | Core product. Data synthesis + probability updates + market context |
| Breaking Alert | As needed | `breaking_alert.md` | When structured data shows anomaly (OONI reconstitution, rial crash, etc.) |
| Deep Dive | Monthly | `deep_dive.md` | Single-topic comprehensive analysis (like the Iran threat assessment) |

## File Map

| Path | Purpose |
|------|---------|
| `.claude/missions/new-issue.md` | Parent mission -- chains all four skills for producing an issue |
| `.claude/missions/delta-engine.md` | Delta engine build mission -- Phases 2-5 remaining |
| `.claude/skills/intel/SKILL.md` | Research phase -- adapted from prediction-markets /recon + Legion |
| `.claude/skills/draft/SKILL.md` | Collaborative drafting with persona voice |
| `.claude/skills/review/SKILL.md` | 6-pass editorial review |
| `.claude/skills/publish/SKILL.md` | Publication, archival, state updates |
| `config/persona.yaml` | Persona configuration (voice, traits, anti-patterns, platform strategy) |
| `config/newsletter.yaml` | Newsletter configuration (schedule, tiers, platform) |
| `config/sources.yaml` | Data source configuration (Ghost Market adapters, OSINT feeds) |
| `docs/PERSONA.md` | Detailed persona reference with examples |
| `docs/STYLE-GUIDE.md` | Writing style guide (word choice, probability format, citations) |
| `docs/BUILD.md` | Build roadmap (historical -- original automated pipeline plan) |
| `src/paper/templates/` | Article templates (weekly_brief, breaking_alert, deep_dive) |
| `content/state/probabilities.json` | Probability tracking across issues (Brier scores, history) |
| `content/state/issues.json` | Issue lifecycle tracker |
| `content/drafts/` | Work in progress articles |
| `content/published/` | Archive of published issues |
| `content/research/` | Research data snapshots per issue |
| `src/adapters/` | All data source adapters (Ghost Market, OSINT, FRED, NOAA, Kalshi) |
| `src/delta/` | Delta engine -- daemon, computation, clustering, source polling |
| `content/state/deltas/thresholds.json` | Per-source threshold config (Cooper-calibrated) |
| `config/com.signaldispatch.delta.plist` | Launchd template for cron scheduling |

## Delta Engine Alerts

On session start, check for pending delta alerts:

```bash
ls content/state/deltas/alerts/pending/
```

If alerts exist, report them before proceeding:
- Read each alert JSON file
- Present: source, severity, plain_english description, timestamp
- Ask Cooper: acknowledge (move to `acknowledged/`) or escalate to Breaking Alert

Alert schema:
```json
{
  "source": "bonbast",
  "severity": "high",
  "timestamp": "...",
  "plain_english": "...",
  "delta": {},
  "cluster": "iran"
}
```

## Quick Start

To produce a new issue:
1. Run `/mission new-issue` with content type and topic
2. Follow the four-phase workflow: intel → draft → review → publish
3. Cooper gates every phase transition

Or invoke skills individually:
- `/intel deep_dive Iran` -- Research only
- `/draft deep_dive --issue 0` -- Draft from existing research
- `/review --issue 0` -- Review existing draft
