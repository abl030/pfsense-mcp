#!/usr/bin/env bash
#
# Bank Tester: run the tester Claude against a fresh pfSense VM using the MCP server.
#
# Usage (from repo root):
#   nix develop -c bash bank-tester/run-bank-test.sh [task-filter]
#
# Examples:
#   bash bank-tester/run-bank-test.sh              # run all tasks (except destructive)
#   bash bank-tester/run-bank-test.sh 01           # run only task 01
#   bash bank-tester/run-bank-test.sh "01 03 05"   # run tasks 01, 03, 05
#   INCLUDE_DESTRUCTIVE=1 bash bank-tester/run-bank-test.sh  # include task 99
#
# Requires: vm/golden.qcow2 (built by vm/setup.sh), claude CLI on PATH
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

# --- Logging helpers ---
ts() { date '+%H:%M:%S'; }
log() { echo "[$(ts)] $*"; }
logf() { echo "[$(ts)] $*" | tee -a "$LIVE_LOG"; }

GOLDEN="vm/golden.qcow2"
HTTPS_PORT=18443
SSH_PORT=12222
API_KEY_FILE="vm/api-key.txt"
MCP_CONFIG_TEMPLATE="bank-tester/mcp-config.json"
TESTER_PROMPT="bank-tester/TESTER-CLAUDE.md"
TASKS_DIR="bank-tester/tasks"
TASK_FILTER="${1:-}"
INCLUDE_DESTRUCTIVE="${INCLUDE_DESTRUCTIVE:-0}"
MODEL="${MODEL:-sonnet}"

# --- Preflight checks ---
[[ -f "$GOLDEN" ]] || { log "FATAL: $GOLDEN not found. Run vm/setup.sh first."; exit 1; }
[[ -f "$API_KEY_FILE" ]] || { log "FATAL: $API_KEY_FILE not found. Run vm/setup.sh first."; exit 1; }
[[ -f "$MCP_CONFIG_TEMPLATE" ]] || { log "FATAL: $MCP_CONFIG_TEMPLATE not found."; exit 1; }
[[ -f "$TESTER_PROMPT" ]] || { log "FATAL: $TESTER_PROMPT not found."; exit 1; }
command -v claude >/dev/null 2>&1 || { log "FATAL: claude CLI not found on PATH."; exit 1; }

# Resolve fastmcp to absolute path (nix develop puts it on PATH)
FASTMCP_PATH="$(command -v fastmcp 2>/dev/null || true)"
if [[ -z "$FASTMCP_PATH" ]]; then
    log "FATAL: fastmcp not found on PATH. Run inside 'nix develop -c'."
    exit 1
fi
log "Using fastmcp: $FASTMCP_PATH"
log "Using model: $MODEL"

# --- Create results directory ---
RUN_ID="$(date +%Y%m%d-%H%M%S)"
RESULTS_DIR="bank-tester/results/run-${RUN_ID}"
mkdir -p "$RESULTS_DIR"
log "Results dir: $RESULTS_DIR"

# --- Create live log early (logf needs it) ---
LIVE_LOG="${RESULTS_DIR}/live.log"
touch "$LIVE_LOG"

# --- Create temp clone ---
TMPIMG=$(mktemp /tmp/pfsense-banktest-XXXXXX.qcow2)
log "Cloning golden image to $TMPIMG..."
cp "$GOLDEN" "$TMPIMG"

# --- Cleanup on exit ---
QEMU_PID=""
cleanup() {
    log "Cleaning up..."
    if [[ -n "$QEMU_PID" ]] && kill -0 "$QEMU_PID" 2>/dev/null; then
        kill "$QEMU_PID" 2>/dev/null || true
        wait "$QEMU_PID" 2>/dev/null || true
    fi
    rm -f "$TMPIMG"
    rm -f "${RESULTS_DIR}/mcp-config-live.json"
    log "Done."
}
trap cleanup EXIT

# --- Check port availability ---
if ss -tln 2>/dev/null | grep -q ":${HTTPS_PORT} " || \
   lsof -iTCP:${HTTPS_PORT} -sTCP:LISTEN 2>/dev/null | grep -q .; then
    log "FATAL: Port $HTTPS_PORT already in use"
    exit 1
fi

# --- Boot VM ---
log "Booting pfSense VM (HTTPS=$HTTPS_PORT, SSH=$SSH_PORT)..."
qemu-system-x86_64 \
    -m 2048 \
    -enable-kvm \
    -drive "file=$TMPIMG,if=virtio,format=qcow2" \
    -device virtio-rng-pci \
    -nographic \
    -netdev "user,id=wan0,net=10.0.2.0/24,hostfwd=tcp::${HTTPS_PORT}-:443,hostfwd=tcp::${SSH_PORT}-:22" \
    -device e1000,netdev=wan0,mac=52:54:00:00:00:01 \
    -netdev user,id=lan0,net=10.0.3.0/24 \
    -device e1000,netdev=lan0,mac=52:54:00:00:00:02 \
    -netdev user,id=opt0,net=10.0.4.0/24 \
    -device e1000,netdev=opt0,mac=52:54:00:00:00:03 \
    &>/dev/null &
QEMU_PID=$!
log "QEMU PID: $QEMU_PID"

# --- Wait for API (with progress) ---
log "Waiting for REST API..."
MAX_WAIT=120
WAITED=0
while [[ $WAITED -lt $MAX_WAIT ]]; do
    HTTP_CODE=$(curl -sk -m 5 -o /dev/null -w '%{http_code}' \
        -u admin:pfsense \
        "https://127.0.0.1:${HTTPS_PORT}/api/v2/system/version" 2>/dev/null || echo "000")
    if [[ "$HTTP_CODE" == "200" ]]; then
        echo ""
        log "API ready! (${WAITED}s)"
        break
    fi
    # Print progress: HTTP code every 10s, dot otherwise
    if (( WAITED % 10 == 0 && WAITED > 0 )); then
        echo -n " [${HTTP_CODE}]"
    else
        echo -n "."
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done

if [[ $WAITED -ge $MAX_WAIT ]]; then
    echo ""
    log "FATAL: API not ready after ${MAX_WAIT}s (last HTTP code: $HTTP_CODE)"
    exit 1
fi

# --- Verify QEMU still running ---
if ! kill -0 "$QEMU_PID" 2>/dev/null; then
    log "FATAL: QEMU died during API wait"
    exit 1
fi

# --- Build live MCP config ---
API_KEY=$(cat "$API_KEY_FILE")
LIVE_MCP_CONFIG="${RESULTS_DIR}/mcp-config-live.json"
sed -e "s|FASTMCP_PATH_PLACEHOLDER|${FASTMCP_PATH}|g" \
    -e "s|REPO_DIR_PLACEHOLDER|${REPO_DIR}|g" \
    -e "s|API_KEY_PLACEHOLDER|${API_KEY}|g" \
    "$MCP_CONFIG_TEMPLATE" > "$LIVE_MCP_CONFIG"
log "MCP config: $LIVE_MCP_CONFIG"

# --- Quick MCP server smoke test ---
log "Smoke-testing MCP server..."
MCP_SMOKE=$(timeout 10 "$FASTMCP_PATH" run "$REPO_DIR/generated/server.py" --transport stdio <<< '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"0.1"}}}' 2>/dev/null | head -1 || true)
if [[ -n "$MCP_SMOKE" ]] && echo "$MCP_SMOKE" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'result' in d" 2>/dev/null; then
    log "MCP server responds OK"
else
    log "WARNING: MCP server smoke test inconclusive (may still work via claude CLI)"
fi

# --- Collect task files ---
# Default ordering: 01-09 (workflow) → 35,37 (read-only) → 10-34 (systematic) → 36 → 40-44 (adversarial) → 99 (destructive)
# Destructive task 99 only included with INCLUDE_DESTRUCTIVE=1
TASK_FILES=()
for task_file in "$TASKS_DIR"/*.md; do
    task_basename="$(basename "$task_file" .md)"

    # Skip destructive tasks unless opted in
    if [[ "$task_basename" == 99-* ]] && [[ "$INCLUDE_DESTRUCTIVE" != "1" ]]; then
        log "Skipping destructive task: $task_basename (set INCLUDE_DESTRUCTIVE=1 to include)"
        continue
    fi

    if [[ -n "$TASK_FILTER" ]]; then
        match=false
        for pattern in $TASK_FILTER; do
            if [[ "$task_basename" == *"$pattern"* ]]; then
                match=true
                break
            fi
        done
        if [[ "$match" == "false" ]]; then
            continue
        fi
    fi
    TASK_FILES+=("$task_file")
done

if [[ ${#TASK_FILES[@]} -eq 0 ]]; then
    log "FATAL: No task files found matching filter '${TASK_FILTER}'"
    exit 1
fi

log "Running ${#TASK_FILES[@]} task(s)..."
log "Tail the live log: tail -f ${LIVE_LOG}"
echo ""

# --- Run each task ---
PASSED=0
FAILED=0
TASK_NUM=0
TESTER_SYSTEM_PROMPT="$(cat "$TESTER_PROMPT")"

for task_file in "${TASK_FILES[@]}"; do
    task_name="$(basename "$task_file" .md)"
    TASK_NUM=$((TASK_NUM + 1))
    logf "=== Task ${TASK_NUM}/${#TASK_FILES[@]}: $task_name ==="
    task_content="$(cat "$task_file")"

    # Log the claude CLI invocation (without the full prompt, just the flags)
    CLAUDE_CMD="claude -p --mcp-config $LIVE_MCP_CONFIG --strict-mcp-config --permission-mode bypassPermissions --output-format text --model $MODEL --max-budget-usd 200.00"
    logf "  cmd: $CLAUDE_CMD"
    logf "  task file: $task_file ($(wc -c < "$task_file") bytes)"

    # Check QEMU health before each task
    if ! kill -0 "$QEMU_PID" 2>/dev/null; then
        logf "  FATAL: QEMU died before task could start"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Quick API health check
    API_CHECK=$(curl -sk -m 5 -o /dev/null -w '%{http_code}' \
        -u admin:pfsense \
        "https://127.0.0.1:${HTTPS_PORT}/api/v2/system/version" 2>/dev/null || echo "000")
    if [[ "$API_CHECK" != "200" ]]; then
        logf "  WARNING: API returned $API_CHECK before task start"
    fi

    TASK_START=$(date +%s)

    # Run tester Claude with text output (human-readable, tailable)
    set +e
    claude -p \
        --mcp-config "$LIVE_MCP_CONFIG" \
        --strict-mcp-config \
        --permission-mode bypassPermissions \
        --output-format text \
        --model "$MODEL" \
        --max-budget-usd 200.00 \
        --append-system-prompt "$TESTER_SYSTEM_PROMPT" \
        "$task_content" \
        2> "${RESULTS_DIR}/${task_name}.stderr" \
        | tee "${RESULTS_DIR}/${task_name}.txt" >> "$LIVE_LOG"
    task_exit=${PIPESTATUS[0]}
    set -e

    TASK_END=$(date +%s)
    TASK_DURATION=$((TASK_END - TASK_START))
    OUTPUT_SIZE=$(wc -c < "${RESULTS_DIR}/${task_name}.txt")
    STDERR_SIZE=$(wc -c < "${RESULTS_DIR}/${task_name}.stderr" 2>/dev/null || echo 0)

    if [[ $task_exit -eq 0 ]]; then
        logf "  PASS (exit $task_exit, ${TASK_DURATION}s, output=${OUTPUT_SIZE}B, stderr=${STDERR_SIZE}B)"
        PASSED=$((PASSED + 1))
    else
        logf "  FAIL (exit $task_exit, ${TASK_DURATION}s, output=${OUTPUT_SIZE}B, stderr=${STDERR_SIZE}B)"
        FAILED=$((FAILED + 1))
    fi

    # Always show stderr if non-empty (not just on failure)
    if [[ -s "${RESULTS_DIR}/${task_name}.stderr" ]]; then
        logf "  --- stderr (first 10 lines) ---"
        head -10 "${RESULTS_DIR}/${task_name}.stderr" | sed 's/^/  | /' | tee -a "$LIVE_LOG"
        logf "  --- end stderr ---"
    fi

    # Warn if output is suspiciously small (likely empty/no tool calls)
    if [[ $OUTPUT_SIZE -lt 50 ]]; then
        logf "  WARNING: Output is only ${OUTPUT_SIZE} bytes — Claude may not have called any tools"
    fi

    echo "" | tee -a "$LIVE_LOG"
done

# --- Analyze results ---
log "Analyzing results..."
python3 bank-tester/analyze-results.py "$RESULTS_DIR"

echo ""
log "=== Bank Test Complete ==="
log "  Passed: $PASSED / ${#TASK_FILES[@]}"
log "  Failed: $FAILED / ${#TASK_FILES[@]}"
log "  Results: $RESULTS_DIR"
log "  Summary: ${RESULTS_DIR}/summary.md"

exit $FAILED
