# Signal Dispatch -- Geopolitical Intelligence Newsletter

## Status: Foundation -- Scaffolding Complete

Geopolitical intelligence newsletter combining structured OSINT data feeds with analytical synthesis and prediction market context.

## Architecture

Four pipelines, executed in sequence for each issue:

1. **Research Pipeline** (`src/research/`) -- Collects structured data from prediction-markets adapters + web research synthesis
2. **Paper Pipeline** (`src/paper/`) -- Drafts articles from research output using templates
3. **Editing Pipeline** (`src/editing/`) -- Style consistency, fact verification, probability calibration checks
4. **Publishing Pipeline** (`src/publishing/`) -- Formats and publishes to Substack/Beehiiv

## Data Dependency

This project does NOT contain its own data adapters. It wraps the prediction-markets pipeline:
- Ghost Market adapters (OONI, OFAC, Bonbast, EIA, Cloudflare Radar, TEDPIX, USAspending)
- OSINT adapters (Federal Register, Congress, FEC)
- FRED + NOAA data sources
- Prediction market CLI (`pm signals`, `pm search`, `pm scan`)

**Prediction markets project:** `/path/to/home/work/personal/code/research/prediction-markets/`

## Content Types

| Type | Frequency | Template | Description |
|------|-----------|----------|-------------|
| Weekly Brief | Weekly | `weekly_brief.md` | Core product. Data synthesis + probability updates + market context |
| Breaking Alert | As needed | `breaking_alert.md` | When structured data shows anomaly (OONI reconstitution, rial crash, etc.) |
| Deep Dive | Monthly | `deep_dive.md` | Single-topic comprehensive analysis (like the Iran threat assessment) |

## File Map

| Path | Purpose |
|------|---------|
| `src/research/collector.py` | Runs prediction-markets adapters, collects structured data snapshots |
| `src/research/synthesizer.py` | Orchestrates web research, combines with structured data |
| `src/paper/drafter.py` | Takes research output, applies template, produces draft |
| `src/paper/templates/` | Markdown templates for each content type |
| `src/editing/editor.py` | Style checks, fact verification hooks, probability format validation |
| `src/publishing/publisher.py` | Platform API integration (Substack/Beehiiv) |
| `src/publishing/formatter.py` | Markdown to newsletter HTML conversion |
| `content/drafts/` | Work in progress articles |
| `content/published/` | Archive of published issues |
| `content/research/` | Research data snapshots per issue |
| `config/newsletter.yaml` | Newsletter configuration |
| `config/sources.yaml` | Data source configuration |
| `docs/BUILD.md` | Build roadmap -- what needs implementation |
