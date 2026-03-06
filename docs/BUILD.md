# Signal Dispatch -- Build Roadmap

## Status: Foundation Complete

Scaffold in place. Four pipeline stubs with clear interfaces. Config files define the data dependency on prediction-markets.

## Phase 1: Research Pipeline (Priority: HIGH)

**Goal:** Automated data collection from prediction-markets adapters.

### 1.1 Collector Implementation
- [ ] Subprocess wrapper for `pm signals --source X --json`
- [ ] Batch collection across multiple sources
- [ ] Snapshot storage to `content/research/{date}/`
- [ ] Delta detection (what changed since last collection)
- [ ] Error handling for adapter failures (Cloudflare auth, EIA series_id)

### 1.2 OONI Monitoring (Leading Indicator)
- [ ] Scheduled OONI polling (hourly)
- [ ] Anomaly detection: measurement_count threshold (>200/hr = reconstitution signal)
- [ ] Alert trigger when anomaly detected
- [ ] Historical baseline for comparison

### 1.3 Synthesizer Framework
- [ ] Research query generation from data signals
- [ ] Integration point for agent-driven web research
- [ ] Structured output format for paper pipeline consumption
- [ ] Research brief template (data layer + qualitative layer + probability estimates)

**Depends on:** prediction-markets Ghost Market adapters (already built)

## Phase 2: Paper Pipeline (Priority: HIGH)

**Goal:** Turn research briefs into draft articles.

### 2.1 Template Engine
- [ ] Jinja2 template rendering from markdown templates
- [ ] Variable injection (dates, data tables, probabilities)
- [ ] Conditional sections (free vs paid content)
- [ ] Probability table auto-formatting

### 2.2 Drafter Implementation
- [ ] Research brief → template mapping
- [ ] Section generation from structured data
- [ ] Placeholder insertion for editorial additions
- [ ] Draft output to `content/drafts/`

### 2.3 Content Types
- [ ] Weekly brief generation workflow
- [ ] Breaking alert generation workflow (triggered by anomaly detection)
- [ ] Deep dive generation workflow (manual trigger, agent-assisted)

**Depends on:** Phase 1 (research pipeline output format)

## Phase 3: Editing Pipeline (Priority: MEDIUM)

**Goal:** Quality assurance before publishing.

### 3.1 Automated Checks
- [ ] Probability format validation (must be explicit numbers)
- [ ] Vague language detection ("elevated threat" → flag, require number)
- [ ] Source citation check (every claim has a source)
- [ ] Data claim verification against research snapshot
- [ ] Word count / section length checks

### 3.2 Style Guide
- [ ] Define Signal Dispatch voice/tone
- [ ] Consistent terminology list
- [ ] Formatting standards (tables, headers, emphasis)

### 3.3 Calibration Integration
- [ ] Track published probability estimates
- [ ] Compare against outcomes when events resolve
- [ ] Publish calibration metrics (Brier score, calibration curve)
- [ ] Accuracy is the product's credibility -- this is non-negotiable

**Depends on:** Phase 2 (draft output format)

## Phase 4: Publishing Pipeline (Priority: MEDIUM)

**Goal:** Automated publishing to newsletter platform.

### 4.1 Platform Selection
- [ ] Evaluate Substack vs Beehiiv API capabilities
- [ ] Substack: Limited API, may need email-based publishing
- [ ] Beehiiv: Full REST API, better for automation
- [ ] Decision: Pick one, build for it

### 4.2 Formatter Implementation
- [ ] Markdown → newsletter HTML conversion
- [ ] Style injection (fonts, colors, branding)
- [ ] Paywall marker insertion (free/paid split)
- [ ] Image/chart embedding support

### 4.3 Publisher Implementation
- [ ] API authentication
- [ ] Post creation (draft → publish)
- [ ] Scheduling support
- [ ] Subscriber segment targeting (breaking alerts → paid only)

### 4.4 Distribution
- [ ] Twitter/X thread generation from article highlights
- [ ] RSS feed generation
- [ ] Archive page on website (optional, future)

**Depends on:** Phase 3 (edited content), platform selection

## Phase 5: Operational (Priority: LOW -- after launch)

### 5.1 Monitoring Dashboard
- [ ] All structured feeds status at a glance
- [ ] Last collection timestamps
- [ ] Anomaly alerts pending
- [ ] Subscriber metrics

### 5.2 Automation
- [ ] Cron job for daily data collection
- [ ] Anomaly detection → breaking alert trigger
- [ ] Weekly brief generation reminder/kickoff
- [ ] Publishing schedule automation

### 5.3 Growth
- [ ] SEO for published content
- [ ] Cross-posting strategy
- [ ] Guest analysis / collaboration framework
- [ ] Podcast companion (future)

## Quick Wins (Can Do Now)

1. **Publish the Iran analysis** -- The deep dive already exists from our recon session. Format it using the deep_dive template and publish as issue #0.
2. **Set up Substack/Beehiiv account** -- 10 minutes, zero code.
3. **Manual weekly brief** -- Use the template manually while pipelines are being built. The template + prediction-markets CLI is enough for v0.
4. **Twitter/X account** -- Start building audience during the crisis window.

## Architecture Decisions

### Why Not a Monorepo with Prediction Markets?
Signal Dispatch is a PRODUCT. Prediction markets is a RESEARCH project. Different lifecycles, different concerns. Signal Dispatch consumes prediction-markets as a data dependency, not as shared code.

### Why Subprocess over Direct Import?
Prediction-markets uses relative imports, virtual environments, and project-specific dependencies. Subprocess calls to `pm` CLI are cleaner than trying to share a Python environment. File-based data flow (JSON snapshots) is already the pattern in prediction-markets.

### Why Templates over LLM Generation?
Templates provide structural consistency. The LLM (agent) fills the research content, but the STRUCTURE of the newsletter should be predictable. Readers expect consistent formatting. Templates enforce it.
