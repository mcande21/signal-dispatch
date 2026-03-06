# Signal Dispatch -- Style Guide

## Tone and Register

**Default:** Calm, confident, methodical. The practitioner at work.

**Escalation:** Measured urgency when data warrants it. Never panic. The shift from default to urgent is signaled by data, not emotion.

**Range:** From analytical curiosity ("interesting signal in today's OONI data") to measured concern ("three signals converging warrants attention") to firm conviction ("I assess 80% probability -- here's why"). Never reaches panic, never reaches indifference.

## Word Choice

### Prefer
- "I assess" over "I think" or "I believe"
- "probability" over "chance" or "likelihood"
- "signal" over "indicator" or "sign"
- "data shows" over "data suggests"
- "I trade this" over "I have a position"
- "methodology" over "approach" or "method"
- "calibration" over "accuracy"
- "resolution criteria" over "how we'll know"
- Specific numbers over vague quantifiers

### Avoid
- "Breaking" (unless genuinely time-sensitive)
- "Shocking" / "stunning" / "explosive"
- "Sources say" (we use open sources -- cite them)
- "Experts believe" (which experts? cite them)
- "Could" / "might" / "may" without probability
- "Significant" without quantification
- Passive voice in analysis sections
- Hedge words that avoid commitment: "somewhat," "arguably," "perhaps"

### Never
- "BREAKING" in all caps
- Exclamation points in analysis
- Rhetorical questions as clickbait
- "You won't believe..."
- Political labels as shorthand ("liberal," "conservative" -- use specific policy positions)
- "My sources" or "insider knowledge"

## Sentence Structure

- **Lead with data.** Not "I believe X because Y" but "Y data shows X. I assess Z% probability."
- **Active voice for analysis.** "I find" not "it was found."
- **Short sentences for impact.** Long sentences for methodology explanation.
- **Footnotes for depth.** Keep main text clean, put methodology details and wit in footnotes.
- **One idea per paragraph.** Geopolitical analysis is dense -- don't compound it.

## Presenting Probability Estimates

### Format
- Always a specific number: "65%" not "likely"
- Always with basis: "65% based on X, Y, Z"
- Always with prior (when updating): "Updated from 45% to 65%"
- Always with resolution criteria: "Resolves YES if X happens by [date]"
- Uncertainty ranges when appropriate: "60-70%, central estimate 65%"

### Confidence Tiers
| Probability | Language | Usage |
|-------------|----------|-------|
| 90%+ | "I assess with high confidence" | Rare. Reserve for overwhelming evidence. |
| 70-89% | "I assess [X]% probability" | Standard strong assessment. |
| 50-69% | "I assess [X]% probability -- this is close to a coin flip at the low end" | Be honest about uncertainty. |
| 30-49% | "I assess [X]% probability -- more likely NOT to happen" | Explicitly note the base. |
| <30% | "I assess low probability ([X]%)" | Still worth tracking if consequential. |

### Update Format
```
**Updated assessment:** [Event]
- Prior: X% (date of prior assessment)
- New data: [specific data that changed the assessment]
- Updated: Y%
- Change: +/-Z percentage points
- Resolution: [criteria] by [date]
```

## Presenting Data

- **Always cite the source with timestamp.** "OONI (2026-03-05T14:22 UTC)"
- **Always provide baseline context.** "Measurement count: 47/hr (baseline: 1,400/hr)"
- **Always explain significance for new readers.** "If you're new: OONI measurement count below 200/hr has preceded regime action in 4 of the last 5 instances."
- **Charts over tables when showing trends.** Tables for snapshots.
- **Label axes and units.** No ambiguity.

## Citing Sources

- **OSINT feeds:** Source name + timestamp. "OONI (2026-03-05T14:22 UTC)"
- **Prediction markets:** Platform + contract + price + timestamp. "Kalshi: Iran Nuclear Deal by 2027 @ $0.095 (2026-03-05)"
- **News sources:** Publication + date. Link in footnote.
- **Academic/think tank:** Author + institution + date. Link in footnote.
- **No anonymous sources.** Everything is OSINT. If we can't cite it, we don't use it.

## Handling Uncertainty

- **Name it explicitly.** "I'm less confident here because..."
- **Distinguish data uncertainty from model uncertainty.** "The data is clear but my interpretation could be wrong" vs. "The data itself is unreliable"
- **Don't hide behind hedging.** Pick a number. If uncertain, widen the range. "50-65%" is honest. "Could go either way" is cowardly.
- **Flag known unknowns.** "What would change my assessment: X, Y, Z"

## Corrections and Updates

### Format
```
**Correction (date):**
Original: [what was published]
Corrected: [what it should say]
Reason: [why the correction]
Impact: [how this affects any dependent assessments]
```

### Rules
- Corrections are never buried. They go at the top of the next issue.
- Distinguish between factual corrections (data was wrong) and analytical updates (assessment changed with new data).
- Analytical updates are normal and expected. Factual corrections require the full correction format.
- Track correction frequency as a quality metric.

## Formatting Conventions

- **Headers:** Clean hierarchy. H1 for issue title, H2 for sections, H3 for subsections.
- **Bold** for key data points and probability numbers.
- **Italics** for publication names and direct quotes.
- **Footnotes** for methodology detail, wit, and extended citations.
- **Horizontal rules** between major sections.
- **No emojis in analysis.** Ever.
- **No all-caps** except official acronyms (OONI, EIA, IRGC).
