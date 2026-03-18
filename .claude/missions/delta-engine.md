---
name: delta-engine
description: Build SD's temporal reasoning layer -- delta computation, alerting, editorial integration
mode: interactive
---

# Mission: Delta Engine

*"Intelligence requires processing change, not snapshots."* -- Legion

## Context

Crucix war room research (2026-03-17) revealed SD's core architectural gap: no temporal reasoning layer. Each /intel run is blind to the last. The delta engine fixes this -- automated change detection across all sources, threshold-based alerting, and editorial pipeline integration.

Phase 1 is built and running. This mission tracks the remaining work.

## What Exists (Phase 1 -- DONE)

- `src/delta/daemon.py` -- Main entry point, runs by cadence (hot/warm/cold/all)
- `src/delta/engine.py` -- Delta computation (numeric, event_set, binary, categorical, composite stub)
- `src/delta/sources.py` -- 22 poll functions, all using local adapters
- `src/delta/clusters.py` -- Cluster detection (Iran, Hormuz, Europe energy, conflict, US macro)
- `src/adapters/` -- All adapters consolidated from prediction-markets, self-contained
- `content/state/deltas/` -- State directory (current, history, prior_state, clusters, alerts, thresholds.json)
- `.venv/` -- SD's own venv with dependencies
- `pyproject.toml`, `.env`, `.env.example`

22 sources producing deltas. 26 baselines recorded. Zero subprocess dependency on PM project.

## Uncommitted Work

33 files across multiple sessions need to be committed in logical chunks:

1. **Adapters + project setup** -- `src/adapters/`, `pyproject.toml`, `.env.example`, `.gitignore`
2. **Delta engine** -- `src/delta/`, `content/state/deltas/thresholds.json`, `config/com.signaldispatch.delta.plist`
3. **Pre-existing uncommitted** -- Skills (`/scan`, `/recon`), brand assets, publishing scripts, research data

Commit these as separate logical commits before starting new work. State files (`content/state/deltas/current/`, `prior_state/`, `history/`) should be gitignored -- they're runtime data, not source.

## Phases

### Phase 2: Cleanup + Harden (next)

**Goal:** Fix known issues, commit everything clean, set up the cron schedule.

| Task | Priority | Effort |
|------|----------|--------|
| Fix FRED precision (values showing as integers, should be floats) | P1 | 30min |
| Fix Oryx returning 0 events (adapter or data format issue) | P1 | 30min |
| Fix plain_english formatting ("flat0%" → "flat") | P2 | 15min |
| Fix prior_state/current file naming inconsistency (case) | P2 | 15min |
| Gitignore runtime state (`content/state/deltas/current/`, `prior_state/`, `history/`, `clusters/`, `alerts/`) | P1 | 5min |
| Commit adapter consolidation | P1 | 5min |
| Commit delta engine | P1 | 5min |
| Commit pre-existing uncommitted work (skills, brand, publishing) | P1 | 10min |
| Install launchd plist for hot-cadence (every 6h) | P2 | 15min |
| Add Cloudflare Radar token to .env (free signup) | P3 | 10min |

## Known Stragglers

Issues that are incomplete, broken, or need attention. Organized by priority.

### API Keys in Logs (OPSEC)
- httpx logs show full URLs including API keys (Congress API key, FEC API key visible in daemon output)
- Fix: Suppress httpx logging or redact URLs before logging
- Priority: P2 -- local machine only, not urgent, but fix before any log shipping

### GDELT Rate Limiting
- Daemon fires 4 GDELT queries simultaneously, hits rate limit
- Fix: Add sequential execution with delay between GDELT queries, or consolidate into fewer queries
- Priority: P2

### Kalshi Auth Verification
- Verify Kalshi auth works in SD's `.env` (keys were copied from PM project)
- RSA-PSS auth requires `.kalshi-key.pem` at the right path
- Priority: P2

### Launchd Not Installed
- Template at `config/com.signaldispatch.delta.plist`
- Cooper needs to customize paths and install manually
- Priority: P2 -- daemon won't auto-restart until this is done

### Composite Delta Types (Stubbed)
- USAspending, Comtrade, FEC all return stub "not yet implemented" from engine
- These need cross-field relational delta logic (Phase 4)
- Priority: P3

### Cloudflare Radar Token Missing
- Needs `CLOUDFLARE_RADAR_TOKEN` in `.env` (free at developers.cloudflare.com/radar)
- Without it, Cloudflare source always fails silently
- Priority: P3 -- Cooper manual action

### TEDPIX Unreachable
- tsetmc.com (Tehran Stock Exchange) is unreachable from outside Iran -- Iran internet controls
- May need proxy approach long-term, or accept as known gap
- Priority: P3 -- by design, not a bug

### Threshold Calibration (Ongoing)
- All thresholds are initial conservative guesses
- Real calibration requires 4-6 issues of real delta data
- Priority: ongoing after Phase 3

### Historical Context Shallow (Self-Resolving)
- Percentile calculations need 30+ data points per source
- Most sources currently have 1-3 data points
- Will improve naturally as daemon accumulates history
- Priority: self-resolving

### Phase 3: Editorial Integration

**Goal:** Wire the delta engine into SD's skill pipeline (/intel, /draft, /review).

| Task | Priority | Effort |
|------|----------|--------|
| `/intel` Stage 1: Delta merge -- read accumulated deltas, produce `delta_summary.md` | P1 | 2h |
| `/draft` probability commitment protocol -- deltas shown before probability suggestions | P1 | 1h |
| `/review` Pass 6: Delta verification -- confirm draft claims match computed deltas | P2 | 1h |
| Template sections: Pattern Recognition, Historical Parallels, Decision Board | P2 | 2h |
| Alert check at session start -- Shepard checks `alerts/pending/` on /reload or /sitrep | P1 | 30min |

### Phase 4: Advanced Types + Calibration

**Goal:** Complete delta type coverage and calibrate thresholds through real usage.

| Task | Priority | Effort |
|------|----------|--------|
| Composite delta type for USAspending (cross-field relational) | P2 | 2h |
| Composite delta type for Comtrade | P2 | 2h |
| Composite delta type for FEC | P3 | 1h |
| Threshold calibration after 4-6 issues with real delta data | P1 | ongoing |
| Two-stream Brier score tracking (system-suggested vs Cooper-actual) | P2 | 2h |
| Historical context depth -- percentile requires 30+ data points per source | P2 | ongoing |

### Phase 5: New Source Onboarding (blocked)

**Goal:** Add high-value Crucix-identified sources. Blocked on licensing/access research.

| Source | Blocker | Action Needed |
|--------|---------|---------------|
| ACLED (conflict events) | Commercial license for newsletter use | Contact ACLED for pricing, confirm redistribution terms for transformative analysis |
| ADS-B Exchange (military flights) | Commercial use requires written authorization | Contact ADS-B Exchange via RapidAPI |
| OpenSanctions (global sanctions) | Journalist exemption may apply | Confirm exemption covers newsletter use case |
| Telegram OSINT (17 channels) | Web scraping technically violates Telegram ToS | Decision: accept risk for public channel scraping, or use Bot API |

**Do not start onboarding until licensing is resolved.** Build adapters only after terms are clear.

## Workflow

```
Phase 2 (cleanup)
  ├── Fix bugs (EDI, focused dispatches)
  ├── Commit in logical chunks (Miranda)
  └── Install cron (Cooper manual)
       │
Phase 3 (editorial integration)
  ├── Garrus scopes /intel Stage 1 integration
  ├── EDI implements per-skill modifications
  └── Test with real issue (SD #5 recession deep dive)
       │
Phase 4 (calibration)
  ├── Runs alongside normal editorial workflow
  ├── Threshold tuning after each issue
  └── Brier score tracking after 15+ issues
       │
Phase 5 (new sources)
  └── Only after licensing resolved
```

## Key Decisions (Cooper)

These require editorial judgment, not engineering:

1. **Threshold calibration** -- What magnitude of rial movement is signal vs noise? Current default: 5% for notification, 2% for watch. Only real usage reveals the right numbers.
2. **Daemon location** -- Currently local machine. If laptop sleeps, hot-cadence polling stops. VPS is always-on but adds infrastructure. Decision point: after Phase 3, based on how much the hot cadence actually matters.
3. **Crucix as sandbox** -- Legion recommended running unmodified Crucix for 4 weeks to develop delta intuition. Optional. Cooper decides if that's useful or a distraction.
4. **Anchoring mitigation** -- The probability commitment protocol (show deltas first, calibration ranges after Cooper commits) is a workflow choice. Cooper can override anytime.

## Reference

- **War room session:** af55e030 (sitreps at `/tmp/normandy-collab-af55e030/sitreps/`)
- **Legion conversation:** 3 rounds of synthesis, full spec in conversation history
- **Liara follow-up research:** ACLED licensing, Telegram channels, ADS-B ToS, OpenSanctions quality, LLM dependency analysis
- **Architecture spec source:** Legion Round 3 -- delta type taxonomy, cadence model, editorial buffer as architecture
