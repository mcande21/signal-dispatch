#!/bin/bash
# Signal Dispatch Environmental Scan Pipeline
# Usage: ./run-scan.sh [--focus shadows|financial|institutional]

set -e

FOCUS="${1:-full}"
if [ "$FOCUS" = "--focus" ]; then FOCUS="${2:-full}"; fi

WORKING_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKER_BUDGET="2.00"
DATE=$(date '+%Y-%m-%d')
SCAN_DIR="$WORKING_DIR/content/research/scans"

mkdir -p "$SCAN_DIR"
mkdir -p /tmp/sd-scan/workers

echo "=========================================="
echo "Signal Dispatch Environmental Scan"
echo "=========================================="
echo "Focus: $FOCUS"
echo "Date:  $DATE"
echo "=========================================="
echo ""

LIARA_PROMPT="You are Liara, the Shadow Broker. You are scanning for geopolitical signals -- anomalies, breaking patterns, things that don't fit the narrative. Date: $DATE.

For your assigned domain, search aggressively. Report:
## What's Happening (facts, sourced)
## What's Anomalous (unusual patterns, breaks from baseline)
## Confidence (strong/moderate/weak for each finding)
## Cross-Domain Connections (how this connects to other geopolitical domains)

Be specific. Numbers, dates, source URLs. We want signal, not noise."

# Build domain list based on focus
case "$FOCUS" in
  full)
    DOMAINS=(
      "Sanctions & Economic Warfare: Recent OFAC actions, new designations, evasion networks exposed, secondary sanctions. Search: 'OFAC sanctions $(date +%Y) $(date +%B)' 'sanctions evasion network $(date +%Y)'"
      "Internet Freedom & Digital Authoritarianism: Internet shutdowns, VPN crackdowns, surveillance tech exports. Search: 'internet shutdown $(date +%Y) $(date +%B)' 'digital censorship crackdown $(date +%Y)'"
      "Energy & Commodities: Pipeline disruptions, LNG issues, SPR, OPEC surprises, rare earth. Search: 'energy disruption $(date +%Y) $(date +%B)' 'rare earth supply chain $(date +%Y)'"
      "Military & Conflict: Unusual deployments, naval movements, weapons transfers. Search: 'military deployment $(date +%Y) $(date +%B)' 'weapons transfer $(date +%Y)'"
      "Trade Coercion & Economic Statecraft: Tariff escalations, trade route disruptions, agreement collapses. Search: 'trade war tariff $(date +%Y) $(date +%B)' 'trade route disruption $(date +%Y)'"
      "Democratic Backsliding: Election manipulation, judicial capture, press freedom attacks. Search: 'democratic backsliding $(date +%Y)' 'press freedom crackdown $(date +%Y)'"
      "Prediction Markets & Risk Pricing: Geopolitical contracts, mispricings, volume anomalies. Search: 'polymarket geopolitical $(date +%Y)' 'prediction market probability $(date +%Y)'"
      "US Government Activity: Executive orders, emergency declarations, agency restructuring. Search: 'executive order $(date +%Y) $(date +%B)' 'DOGE federal cuts $(date +%Y)'"
      "Climate & Disaster Cascades: Compounding events, food crisis, tipping points. Search: 'climate tipping point $(date +%Y)' 'food crisis $(date +%Y)'"
      "Emerging Tech & AI Governance: AI regulation, chip controls, spectrum, biotech. Search: 'AI regulation $(date +%Y) $(date +%B)' 'chip export control $(date +%Y)'"
      "Financial Shadow Moves: SWF repositioning, debt crises, gold hoarding, shadow banking. Search: 'sovereign wealth fund $(date +%Y)' 'private credit default $(date +%Y)' 'central bank gold $(date +%Y)'"
      "Institutional Decay: Agency capacity loss, journalism collapse, election security, public health. Search: 'federal agency cuts $(date +%Y)' 'local newspaper closure $(date +%Y)' 'election security $(date +%Y)'"
    )
    ;;
  shadows)
    DOMAINS=(
      "Democratic Backsliding (SHADOW): What governance changes are happening under cover of the dominant news story? Search: 'democratic backsliding $(date +%Y)' 'quiet legislation passed $(date +%Y) $(date +%B)'"
      "US Government Unusual Activity (SHADOW): What's being restructured, defunded, or reorganized while media covers the main story? Search: 'DOGE cuts $(date +%Y) $(date +%B)' 'federal agency eliminated $(date +%Y)'"
      "Financial Shadow Moves: What's moving in money flows that the dominant story covers up? Search: 'de-dollarization $(date +%Y) $(date +%B)' 'BRICS payment $(date +%Y)' 'private credit crisis $(date +%Y)'"
      "Institutional Decay: What systems are quietly breaking? Search: 'CDC surveillance cuts $(date +%Y)' 'CISA election security $(date +%Y)' 'local journalism collapse $(date +%Y)'"
      "What Is The Dominant Story Distracting From? Research what the BIGGEST current news story is, then search for what is NOT being covered because of it. Search: 'underreported news $(date +%Y) $(date +%B)' 'what media is missing $(date +%Y)'"
      "Quiet Power Moves: Search for coups, constitutional changes, judicial captures, military takeovers getting zero coverage. Search: 'Africa coup $(date +%Y)' 'constitutional amendment term extension $(date +%Y)' 'China moves $(date +%Y) $(date +%B)'"
    )
    ;;
  financial)
    DOMAINS=(
      "Sovereign Wealth Fund Repositioning: Where are SWFs moving money? Search: 'sovereign wealth fund $(date +%Y) repositioning' 'Saudi PIF $(date +%Y)' 'Norway fund $(date +%Y)'"
      "Quiet Debt Crises: Which countries are silently approaching default? Search: 'sovereign debt default $(date +%Y)' 'IMF bailout $(date +%Y) $(date +%B)' 'debt crisis developing $(date +%Y)'"
      "Gold & Commodity Hoarding: Central bank and institutional accumulation patterns. Search: 'central bank gold purchases $(date +%Y)' 'commodity hoarding $(date +%Y)' 'strategic reserves $(date +%Y)'"
      "Shadow Banking & Private Credit: Stress in the unregulated lending system. Search: 'private credit default $(date +%Y)' 'shadow banking crisis $(date +%Y)' 'commercial real estate default $(date +%Y)'"
      "Currency & De-dollarization: Currency collapses and dollar alternatives. Search: 'currency crisis $(date +%Y)' 'BRICS payment system $(date +%Y)' 'CBDC launch $(date +%Y)'"
      "US Fiscal Position: Deficit trajectory, Treasury demand, interest burden. Search: 'US deficit $(date +%Y)' 'Treasury auction demand $(date +%Y)' 'debt ceiling $(date +%Y)'"
    )
    ;;
  institutional)
    DOMAINS=(
      "International Institutions: UN, WHO, WFP defunding and capacity loss. Search: 'UN funding crisis $(date +%Y)' 'WHO budget cut $(date +%Y)' 'WFP funding $(date +%Y)'"
      "US Federal Agency Capacity: EPA, FDA, NOAA, CDC staffing and budget. Search: 'EPA cuts $(date +%Y)' 'CDC staffing $(date +%Y)' 'NOAA budget $(date +%Y)'"
      "Election Infrastructure: CISA, voting security, redistricting. Search: 'election security $(date +%Y)' 'CISA cuts $(date +%Y)' 'voting rights $(date +%Y)'"
      "Academic & Research: University funding, NIH grants, scientific capacity. Search: 'NIH funding cut $(date +%Y)' 'university retrenchment $(date +%Y)' 'research funding $(date +%Y)'"
      "Local Journalism: News deserts, closures, accountability gaps. Search: 'local newspaper closure $(date +%Y)' 'news desert $(date +%Y)' 'journalism layoffs $(date +%Y)'"
      "Public Health & Pandemic Prep: Disease surveillance, vaccine capacity, H5N1. Search: 'public health funding $(date +%Y)' 'H5N1 $(date +%Y) $(date +%B)' 'disease surveillance $(date +%Y)'"
    )
    ;;
  *)
    echo "Unknown focus: $FOCUS"
    echo "Options: full, shadows, financial, institutional"
    exit 1
    ;;
esac

WORKER_COUNT=${#DOMAINS[@]}
# -----------------------------------------------------------------------
# PHASE 0: Ghost Market Adapter Dashboard
# -----------------------------------------------------------------------
echo "[Phase 0] Polling Ghost Market adapters..."
PM_DIR="../prediction-markets"
if [ -f "$PM_DIR/src/cli.py" ]; then
  mkdir -p /tmp/sd-scan/adapters

  # Dashboard poll
  (cd "$PM_DIR" && python src/cli.py signals --check --json > /tmp/sd-scan/adapters/dashboard.json 2>/dev/null) &

  # Key adapter fetches in parallel
  (cd "$PM_DIR" && python src/cli.py signals --source ooni --param probe_cc=IR --json > /tmp/sd-scan/adapters/ooni-ir.json 2>/dev/null) &
  (cd "$PM_DIR" && python src/cli.py signals --source bonbast --json > /tmp/sd-scan/adapters/bonbast.json 2>/dev/null) &
  (cd "$PM_DIR" && python src/cli.py signals --source agsi --param country=EU --json > /tmp/sd-scan/adapters/agsi-eu.json 2>/dev/null) &
  (cd "$PM_DIR" && python src/cli.py signals --source eia --json > /tmp/sd-scan/adapters/eia.json 2>/dev/null) &
  (cd "$PM_DIR" && python src/cli.py signals --source viirs --param country=IR --json > /tmp/sd-scan/adapters/viirs-ir.json 2>/dev/null) &
  (cd "$PM_DIR" && python src/cli.py signals --source gdelt --param query="geopolitical crisis" --json > /tmp/sd-scan/adapters/gdelt.json 2>/dev/null) &
  (cd "$PM_DIR" && python src/cli.py signals --source oryx --json > /tmp/sd-scan/adapters/oryx.json 2>/dev/null) &
  (cd "$PM_DIR" && python src/cli.py signals --source ofac --json > /tmp/sd-scan/adapters/ofac.json 2>/dev/null) &
  (cd "$PM_DIR" && python src/cli.py signals --source dolarvzla --json > /tmp/sd-scan/adapters/dolarvzla.json 2>/dev/null) &

  wait
  ADAPTER_COUNT=$(ls /tmp/sd-scan/adapters/*.json 2>/dev/null | wc -l)
  echo "  → $ADAPTER_COUNT adapter feeds collected"

  # Build adapter summary for worker context
  python3 -c "
import json, os, glob
summary = []
for f in sorted(glob.glob('/tmp/sd-scan/adapters/*.json')):
    name = os.path.basename(f).replace('.json', '')
    try:
        data = json.load(open(f))
        if isinstance(data, dict):
            summary.append(f'### {name}\n{json.dumps(data, indent=2)[:500]}')
        elif isinstance(data, list) and len(data) > 0:
            summary.append(f'### {name}\n{json.dumps(data[:3], indent=2)[:500]}')
    except:
        summary.append(f'### {name}\nFailed to parse')
with open('/tmp/sd-scan/adapter-summary.txt', 'w') as out:
    out.write('## Ghost Market Adapter Data (structured feeds)\n\n')
    out.write('\n\n'.join(summary))
" 2>/dev/null
  echo "  → Adapter summary written"
else
  echo "  → prediction-markets project not found, skipping adapters"
  echo "No adapter data available." > /tmp/sd-scan/adapter-summary.txt
fi
echo ""

# -----------------------------------------------------------------------
# PHASE 1: Web Research Workers
# -----------------------------------------------------------------------
echo "[Phase 1] Launching $WORKER_COUNT domain workers..."

for i in "${!DOMAINS[@]}"; do
  DOMAIN="${DOMAINS[$i]}"

  omni-tool spawn \
    --prompt "$LIARA_PROMPT --- DOMAIN: $DOMAIN" \
    --model sonnet \
    --tools "WebSearch,WebFetch,Read,Bash" \
    --budget "$WORKER_BUDGET" \
    --timeout 180 \
    --working-dir "$WORKING_DIR" \
    > "/tmp/sd-scan/workers/worker-$i.json" 2>&1 &

  echo "  Worker $i: $(echo "$DOMAIN" | cut -d: -f1)"
done

echo ""
echo "  Waiting for all workers..."
wait
echo "  All $WORKER_COUNT workers complete."
echo ""

# Collect results
echo "[Phase 2] Collecting results..."

echo "# Signal Dispatch Environmental Scan" > /tmp/sd-scan/all-results.txt
echo "## $DATE | Focus: $FOCUS" >> /tmp/sd-scan/all-results.txt
echo "" >> /tmp/sd-scan/all-results.txt

for f in /tmp/sd-scan/workers/worker-*.json; do
  NUM=$(basename "$f" .json | sed 's/worker-//')
  DOMAIN_NAME=$(echo "${DOMAINS[$NUM]}" | cut -d: -f1)
  echo "=== $DOMAIN_NAME ===" >> /tmp/sd-scan/all-results.txt
  python3 -c "
import json
try:
    data = json.load(open('$f'))
    if isinstance(data, dict):
        print(data.get('result', data.get('message', json.dumps(data, indent=2))))
    else:
        print(str(data))
except:
    with open('$f') as fh:
        content = fh.read()
        print(content[-3000:])
" >> /tmp/sd-scan/all-results.txt 2>&1
  echo "" >> /tmp/sd-scan/all-results.txt
done

echo "  Collected $(wc -c < /tmp/sd-scan/all-results.txt) bytes"
echo ""

# Synthesize
echo "[Phase 3] Synthesizing signal map..."

omni-tool spawn \
  --prompt "You are Legion. Read /tmp/sd-scan/all-results.txt (web research) AND /tmp/sd-scan/adapter-summary.txt (structured Ghost Market data). Produce a signal map:

## Hot Signals (actively moving, consequential)
Numbered list. Each: one-line summary, confidence level, source.

## Shadow Signals (being missed while everyone watches the dominant story)
Numbered list. Each: what's happening, why it's missed, why it matters.

## Cross-Domain Convergences
Where do multiple domains reinforce the same thesis?

## Deep Dive Candidates (ranked)
Topics worth a full /recon run. Ranked by: signal strength + novelty + actionability.

## Channel Convergence Analysis
Where do structured data (Ghost Market adapters), web research, and prediction
markets all point in the same direction? Rate each convergence:
- 3+ channels = HIGHEST confidence (immediate deep dive candidate)
- 2 channels = HIGH confidence (strong candidate)
- 1 channel = MEDIUM (monitor, may be noise)

## Tradeable Signals
Market implications, prediction market edges, asymmetric opportunities.
Flag any prediction market prices that diverge from our structured data assessment.

## Adapter Anomalies
From the Ghost Market data, flag any readings that cross signal thresholds:
- OONI <200 measurements/hr (censorship event)
- Bonbast >15% spread (economic stress)
- AGSI <35% storage entering spring (refill crisis)
- VIIRS >50 hotspots/day in conflict zone (active operations)
- dolarVzla >40% parallel spread (regime stress)
- GDELT >25 articles/day on single topic (media attention spike)

Write to $WORKING_DIR/content/research/scans/scan-$DATE.md" \
  --model sonnet \
  --tools "Read,Write,Bash" \
  --budget 2.50 \
  --timeout 240 \
  --working-dir "$WORKING_DIR" > /tmp/sd-scan/synthesis-result.json 2>&1

echo ""
echo "=========================================="
echo "SCAN COMPLETE"
echo "=========================================="
echo "Signal map: $WORKING_DIR/content/research/scans/scan-$DATE.md"
echo "Raw data:   /tmp/sd-scan/all-results.txt"
echo ""
echo "Next steps:"
echo "  1. Review the signal map"
echo "  2. Pick a deep dive candidate"
echo "  3. Run: /recon '<topic>' --issue <N>"
