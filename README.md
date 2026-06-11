# Signal Dispatch

Geopolitical intelligence newsletter pipeline. Structured OSINT data feeds, a delta-detection engine, and a human-gated editorial workflow producing calibrated probability analysis published on Substack.

**Methodology:** every assessment carries a timestamped probability estimate with explicit resolution criteria, in the Tetlock calibrated-forecasting tradition. Brier scores tracked, post-mortems published.

## How It Works

```
 Data adapters  ──►  Delta engine  ──►  Editorial workflow  ──►  Substack
 (src/adapters)      (src/delta)        (intel → draft →
                                         review → publish)
```

1. **Adapters** poll ~25 public data sources (markets, sanctions, energy, conflict, regulatory).
2. The **delta engine** daemon polls on hot (6h) / warm (daily) / cold (on-demand) cadences, computes deltas against prior state, clusters correlated movement (e.g. Iran, Hormuz, Europe-energy), and raises alerts.
3. The **editorial workflow** turns signals into issues through four phases — research, drafting, review, publication — with a human gate at every transition. This is a collaborative pipeline, not an automated one.

## Data Adapters

All adapters are self-contained in `src/adapters/` (async, httpx-based, shared `base.py` plumbing).

| Group | Sources |
|-------|---------|
| Ghost Market (16) | OONI, OFAC, Bonbast, EIA, Cloudflare Radar, TEDPIX, USAspending, GDELT, ENTSOG, AGSI, ECB, Comtrade, EIA Grid, VIIRS/FIRMS, dolarVzla, Oryx |
| OSINT (3) | Federal Register, Congress.gov, FEC |
| Corporate investigative (6) | SEC EDGAR, FEC corporate, FERC, ProPublica Nonprofits, CourtListener, Senate Lobbying (LDA) |
| Standalone | FRED, NOAA/NWS, Kalshi (prediction markets), ACLED, ADS-B, OpenSanctions, Telegram |

Most sources need no key. The ones that do are listed in `.env.example` (all free-tier).

## Delta Engine

`src/delta/`:

- `daemon.py` — cron-driven poller (launchd template at `config/com.signaldispatch.delta.plist`)
- `sources.py` — poll functions wrapping the local adapters
- `engine.py` — delta computation (numeric, event_set, binary, categorical)
- `clusters.py` — correlated-delta detection across named clusters
- Runtime state lives at `content/state/deltas/` (gitignored)

## Editorial Workflow

Four Claude Code skills under `.claude/skills/`, chained by the `new-issue` mission:

| Phase | Skill | What it does |
|-------|-------|--------------|
| 1 | `intel` | Multi-phase research: delta summary, Ghost Market signals, OSINT, web research, synthesis |
| 2 | `draft` | Collaborative drafting from research artifacts using the persona voice |
| 3 | `review` | 6-pass editorial review: style, fact verification, probability format, calibration, persona, delta verification |
| 4 | `publish` | Substack formatting, archival, probability-state updates |

Content types: **Weekly Brief** (bi-weekly), **Breaking Alert** (as needed), **Deep Dive** (monthly). Templates in `src/paper/templates/`.

## Repository Layout

| Path | Purpose |
|------|---------|
| `src/adapters/` | Data source adapters |
| `src/delta/` | Delta engine (daemon, computation, clustering) |
| `src/paper/` | PDF generation + article templates |
| `config/` | Newsletter, persona, and source configuration; launchd template |
| `content/drafts/` | Work-in-progress issues (markdown gitignored; PDFs/OG images tracked) |
| `content/published/` | Archive of published issues |
| `content/research/` | Per-issue research snapshots (briefs, signal data, synthesis) |
| `content/brand/` | Logo/profile asset generators and outputs |
| `docs/` | Persona reference, style guide, build roadmap, per-source notes |
| `.claude/` | Skills, missions, and project instructions for the editorial workflow |
| `run-scan.sh` / `run-recon.sh` | Environmental scan / reconnaissance pipelines |

## Setup

Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

cp .env.example .env   # fill in the API keys you need
```

Adapters degrade gracefully: sources whose keys are missing are skipped or fall back to keyless endpoints where available.

Set `SD_CONTACT_EMAIL` to your own contact address — some sources (SEC EDGAR, NWS) require a contact email in the `User-Agent` header and may reject requests without one.

### Kalshi

Kalshi uses RSA-PSS request signing. Set `KALSHI_KEY_ID` and point `KALSHI_PRIVATE_KEY_PATH` at your private key file (keep it outside version control — `*.pem` is gitignored).

### Substack

The publish phase formats drafts for Substack. The posting scripts themselves are kept out of the repository (gitignored); publishing authenticates with a browser cookie via the `SUBSTACK_COOKIES` environment variable — credentials are never stored in the repo.

### Delta daemon

Edit the paths in `config/com.signaldispatch.delta.plist` for your machine, then:

```bash
cp config/com.signaldispatch.delta.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.signaldispatch.delta.plist
```

## State & Calibration

- `content/state/probabilities.json` — probability tracking across issues (Brier scores, revision history)
- `content/state/issues.json` — issue lifecycle tracker
- `content/state/deltas/thresholds.json` — per-source alert thresholds

## License

No license granted. All rights reserved. The analysis and published content in `content/` are the newsletter's editorial property.
