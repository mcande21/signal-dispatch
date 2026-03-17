#!/bin/bash
# Signal Dispatch Recon Pipeline -- Manual Runner
# Runs the sd-recon blueprint steps sequentially
# Usage: ./run-recon.sh "US recession probability 2026" 5

set -e

TOPIC="${1:?Usage: ./run-recon.sh 'topic' issue_number}"
ISSUE_NUMBER="${2:?Usage: ./run-recon.sh 'topic' issue_number}"
WORKER_COUNT="${3:-8}"
WORKER_BUDGET="${4:-2.00}"
DEEP_PULL_BUDGET="${5:-3.00}"
WORKING_DIR="/Users/cooperanderson/projects/signal-dispatch"

echo "=========================================="
echo "Signal Dispatch Recon Pipeline"
echo "=========================================="
echo "Topic:         $TOPIC"
echo "Issue:         #$ISSUE_NUMBER"
echo "Workers:       $WORKER_COUNT"
echo "Worker Budget: \$$WORKER_BUDGET"
echo "Deep Budget:   \$$DEEP_PULL_BUDGET"
echo "=========================================="
echo ""

# Setup
mkdir -p /tmp/sd-recon/workers
mkdir -p /tmp/sd-recon/deep-pulls
mkdir -p "$WORKING_DIR/content/research/$ISSUE_NUMBER"

# -----------------------------------------------------------------------
# PHASE 1: Topic Decomposition (via Claude spawn)
# -----------------------------------------------------------------------
echo "[Phase 1] Decomposing topic into $WORKER_COUNT research angles..."

omni-tool spawn \
  --prompt "Break the research topic '$TOPIC' into exactly $WORKER_COUNT independent research angles. Each angle should be specific, non-overlapping, and include 3-5 web search queries. Write output as a JSON array to /tmp/sd-recon/angles.json with format: [{\"id\": 1, \"name\": \"short-name\", \"mission\": \"description\", \"queries\": [\"q1\", \"q2\", \"q3\"]}]. Design angles that together provide a COMPLETE picture." \
  --model sonnet \
  --tools "Read,Write,Bash" \
  --budget 0.75 \
  --timeout 120 \
  --working-dir "$WORKING_DIR" > /tmp/sd-recon/decompose-result.json 2>&1

if [ ! -f /tmp/sd-recon/angles.json ]; then
  echo "ERROR: Decomposition failed -- no angles.json produced"
  cat /tmp/sd-recon/decompose-result.json
  exit 1
fi

ANGLE_COUNT=$(python3 -c "import json; print(len(json.load(open('/tmp/sd-recon/angles.json'))))")
echo "  → $ANGLE_COUNT angles generated"
echo ""

# -----------------------------------------------------------------------
# PHASE 2: Swarm Launch
# -----------------------------------------------------------------------
echo "[Phase 2] Launching $ANGLE_COUNT research workers in parallel..."

LIARA_PROMPT="You are Liara, the Shadow Broker. Research the assigned topic thoroughly using web searches. For every claim, cite the source URL. Distinguish hard data from analyst commentary. Note confidence levels. Date: $(date '+%Y-%m-%d').

Format: ## Findings [sourced] ## Key Data Points [numbers] ## Confidence Assessment ## Gaps ## Cross-References"

for i in $(seq 0 $((ANGLE_COUNT - 1))); do
  MISSION=$(python3 -c "
import json
angles = json.load(open('/tmp/sd-recon/angles.json'))
a = angles[$i]
queries = ' '.join([f'Search for: \"{q}\"' for q in a['queries']])
print(f\"MISSION: {a['mission']}\n\n{queries}\")
")

  omni-tool spawn \
    --prompt "$LIARA_PROMPT --- $MISSION" \
    --model sonnet \
    --tools "WebSearch,WebFetch,Read,Bash" \
    --budget "$WORKER_BUDGET" \
    --timeout 240 \
    --working-dir "$WORKING_DIR" \
    > "/tmp/sd-recon/workers/worker-$i.json" 2>&1 &

  echo "  Worker $i launched"
done

echo "  Waiting for all workers..."
wait
echo "  → All $ANGLE_COUNT workers complete"
echo ""

# -----------------------------------------------------------------------
# PHASE 3: Collect Results
# -----------------------------------------------------------------------
echo "[Phase 3] Collecting results..."

echo "=== SWARM RESULTS ===" > /tmp/sd-recon/all-results.txt
echo "Topic: $TOPIC" >> /tmp/sd-recon/all-results.txt
echo "" >> /tmp/sd-recon/all-results.txt

for f in /tmp/sd-recon/workers/worker-*.json; do
  NUM=$(basename "$f" .json | sed 's/worker-//')
  echo "=== WORKER $NUM ===" >> /tmp/sd-recon/all-results.txt
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
" >> /tmp/sd-recon/all-results.txt 2>&1
  echo "" >> /tmp/sd-recon/all-results.txt
done

BYTES=$(wc -c < /tmp/sd-recon/all-results.txt)
echo "  → Collected $BYTES bytes"
echo ""

# -----------------------------------------------------------------------
# PHASE 3b: Synthesis (via Claude spawn)
# -----------------------------------------------------------------------
echo "[Phase 3b] Legion synthesis..."

omni-tool spawn \
  --prompt "You are Legion. Read /tmp/sd-recon/all-results.txt and /tmp/sd-recon/angles.json. Produce a unified synthesis with: ## Signal Convergence, ## Signal Divergence, ## Key Data Points Table (20-25 numbers), ## Preliminary Assessment (bull/bear/base with probability), ## Research Gaps, ## Recommended Deep Pull Targets (3-5 specific topics with search queries). Write to $WORKING_DIR/content/research/$ISSUE_NUMBER/synthesis.md" \
  --model sonnet \
  --tools "Read,Write,Bash" \
  --budget 3.00 \
  --timeout 300 \
  --working-dir "$WORKING_DIR" > /tmp/sd-recon/synthesis-result.json 2>&1

echo "  → Synthesis complete"
echo ""

# -----------------------------------------------------------------------
# CHECKPOINT 1
# -----------------------------------------------------------------------
echo "=========================================="
echo "CHECKPOINT: Review synthesis"
echo "=========================================="
echo "Synthesis at: $WORKING_DIR/content/research/$ISSUE_NUMBER/synthesis.md"
echo ""
DECISION="y"  # Auto-continue (review output after pipeline completes)
echo ""

# -----------------------------------------------------------------------
# PHASE 4: Deep Pulls
# -----------------------------------------------------------------------
echo "[Phase 4] Launching deep pull workers..."

DEEP_COUNT=$(python3 -c "
with open('$WORKING_DIR/content/research/$ISSUE_NUMBER/synthesis.md') as f:
    content = f.read()
if '## Recommended Deep Pull Targets' in content:
    section = content.split('## Recommended Deep Pull Targets')[1]
    import re
    targets = re.findall(r'^\d+\.', section, re.MULTILINE)
    print(min(len(targets), 5))
else:
    print(3)
" 2>/dev/null || echo "3")

TARGETS=$(python3 -c "
with open('$WORKING_DIR/content/research/$ISSUE_NUMBER/synthesis.md') as f:
    content = f.read()
if '## Recommended Deep Pull Targets' in content:
    section = content.split('## Recommended Deep Pull Targets')[1]
    next_h = section.find('\n## ')
    if next_h > 0: section = section[:next_h]
    print(section.strip())
else:
    print('Research gaps from synthesis')
" 2>/dev/null)

LIARA_DEEP="You are Liara, the Shadow Broker. DEEP PULL mission -- go beyond surface searches. Find primary sources, quantified transmission mechanisms, historical precedent, and contrarian evidence. Format: ## Deep Findings ## The Number That Matters ## Historical Precedent ## Contrarian Evidence ## Sources"

for i in $(seq 1 $DEEP_COUNT); do
  omni-tool spawn \
    --prompt "$LIARA_DEEP --- Topic: $TOPIC. ALL TARGETS: $TARGETS. YOUR ASSIGNMENT: Focus on target #$i. Date: $(date '+%Y-%m-%d')." \
    --model sonnet \
    --tools "WebSearch,WebFetch,Read,Bash" \
    --budget "$DEEP_PULL_BUDGET" \
    --timeout 300 \
    --working-dir "$WORKING_DIR" \
    > "/tmp/sd-recon/deep-pulls/deep-$i.json" 2>&1 &

  echo "  Deep pull $i launched"
done

echo "  Waiting..."
wait
echo "  → Deep pulls complete"
echo ""

# Collect deep pulls
echo "=== DEEP PULL RESULTS ===" > /tmp/sd-recon/deep-pull-results.txt
for f in /tmp/sd-recon/deep-pulls/deep-*.json; do
  NUM=$(basename "$f" .json | sed 's/deep-//')
  echo "=== DEEP PULL $NUM ===" >> /tmp/sd-recon/deep-pull-results.txt
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
        print(fh.read()[-3000:])
" >> /tmp/sd-recon/deep-pull-results.txt 2>&1
  echo "" >> /tmp/sd-recon/deep-pull-results.txt
done

# -----------------------------------------------------------------------
# PHASE 5: Integration + Adversarial
# -----------------------------------------------------------------------
echo "[Phase 5] Integration + Adversarial challenge..."

omni-tool spawn \
  --prompt "You are Legion. Read /tmp/sd-recon/deep-pull-results.txt and $WORKING_DIR/content/research/$ISSUE_NUMBER/synthesis.md. Integrate deep pull findings: update data points table, resolve contradictions, update probability. Write to $WORKING_DIR/content/research/$ISSUE_NUMBER/synthesis-integrated.md" \
  --model sonnet \
  --tools "Read,Write" \
  --budget 2.50 \
  --timeout 240 \
  --working-dir "$WORKING_DIR" > /tmp/sd-recon/integrate-result.json 2>&1

echo "  → Integration complete"

omni-tool spawn \
  --prompt "You are Grunt (question assumptions) AND Jack (blow it up). Read $WORKING_DIR/content/research/$ISSUE_NUMBER/synthesis-integrated.md. Challenge everything: What assumptions are untested? What data is weakest? Why is the thesis wrong? What's the strongest counter-argument? Then assess which challenges have merit. Write to $WORKING_DIR/content/research/$ISSUE_NUMBER/adversarial.md" \
  --model sonnet \
  --tools "Read,Write" \
  --budget 2.00 \
  --timeout 240 \
  --working-dir "$WORKING_DIR" > /tmp/sd-recon/adversarial-result.json 2>&1

echo "  → Adversarial challenge complete"
echo ""

# -----------------------------------------------------------------------
# CHECKPOINT 2
# -----------------------------------------------------------------------
echo "=========================================="
echo "CHECKPOINT: Review adversarial findings"
echo "=========================================="
echo "Integrated synthesis: $WORKING_DIR/content/research/$ISSUE_NUMBER/synthesis-integrated.md"
echo "Adversarial review:   $WORKING_DIR/content/research/$ISSUE_NUMBER/adversarial.md"
echo ""
DECISION2="y"  # Auto-continue (review output after pipeline completes)
echo ""

# -----------------------------------------------------------------------
# PHASE 6: Final Brief
# -----------------------------------------------------------------------
echo "[Phase 6] Assembling final brief..."

omni-tool spawn \
  --prompt "Produce the final research brief for Signal Dispatch Issue #$ISSUE_NUMBER on '$TOPIC'. Read: $WORKING_DIR/content/research/$ISSUE_NUMBER/synthesis-integrated.md and $WORKING_DIR/content/research/$ISSUE_NUMBER/adversarial.md. Write a complete brief with: Executive Assessment, Evidence Base, Key Data Points table, Probability Assessment (bull/bear/base with resolution criteria), Adversarial Notes, What the Market Is Missing, Sources. Write to $WORKING_DIR/content/research/$ISSUE_NUMBER/brief.md" \
  --model sonnet \
  --tools "Read,Write" \
  --budget 3.00 \
  --timeout 300 \
  --working-dir "$WORKING_DIR" > /tmp/sd-recon/brief-result.json 2>&1

echo ""
echo "=========================================="
echo "PIPELINE COMPLETE"
echo "=========================================="
echo "Research brief: $WORKING_DIR/content/research/$ISSUE_NUMBER/brief.md"
echo "Synthesis:      $WORKING_DIR/content/research/$ISSUE_NUMBER/synthesis-integrated.md"
echo "Adversarial:    $WORKING_DIR/content/research/$ISSUE_NUMBER/adversarial.md"
echo ""
echo "Next: /draft deep_dive --issue $ISSUE_NUMBER"
