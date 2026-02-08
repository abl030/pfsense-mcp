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

GOLDEN="vm/golden.qcow2"
HTTPS_PORT=18443
SSH_PORT=12222
API_KEY_FILE="vm/api-key.txt"
MCP_CONFIG_TEMPLATE="bank-tester/mcp-config.json"
TESTER_PROMPT="bank-tester/TESTER-CLAUDE.md"
TASKS_DIR="bank-tester/tasks"
TASK_FILTER="${1:-}"
INCLUDE_DESTRUCTIVE="${INCLUDE_DESTRUCTIVE:-0}"

# --- Preflight checks ---
[[ -f "$GOLDEN" ]] || { echo "FATAL: $GOLDEN not found. Run vm/setup.sh first."; exit 1; }
[[ -f "$API_KEY_FILE" ]] || { echo "FATAL: $API_KEY_FILE not found. Run vm/setup.sh first."; exit 1; }
[[ -f "$MCP_CONFIG_TEMPLATE" ]] || { echo "FATAL: $MCP_CONFIG_TEMPLATE not found."; exit 1; }
[[ -f "$TESTER_PROMPT" ]] || { echo "FATAL: $TESTER_PROMPT not found."; exit 1; }
command -v claude >/dev/null 2>&1 || { echo "FATAL: claude CLI not found on PATH."; exit 1; }

# Resolve fastmcp to absolute path (nix develop puts it on PATH)
FASTMCP_PATH="$(command -v fastmcp 2>/dev/null || true)"
if [[ -z "$FASTMCP_PATH" ]]; then
    echo "FATAL: fastmcp not found on PATH. Run inside 'nix develop -c'."
    exit 1
fi
echo "==> Using fastmcp: $FASTMCP_PATH"

# --- Create results directory ---
RUN_ID="$(date +%Y%m%d-%H%M%S)"
RESULTS_DIR="bank-tester/results/run-${RUN_ID}"
mkdir -p "$RESULTS_DIR"
echo "==> Results will be written to $RESULTS_DIR"

# --- Create temp clone ---
TMPIMG=$(mktemp /tmp/pfsense-banktest-XXXXXX.qcow2)
echo "==> Cloning golden image to $TMPIMG..."
cp "$GOLDEN" "$TMPIMG"

# --- Cleanup on exit ---
QEMU_PID=""
cleanup() {
    echo "==> Cleaning up..."
    if [[ -n "$QEMU_PID" ]] && kill -0 "$QEMU_PID" 2>/dev/null; then
        kill "$QEMU_PID" 2>/dev/null || true
        wait "$QEMU_PID" 2>/dev/null || true
    fi
    rm -f "$TMPIMG"
    # Clean up live MCP config
    rm -f "${RESULTS_DIR}/mcp-config-live.json"
    echo "==> Done."
}
trap cleanup EXIT

# --- Check port availability ---
if ss -tln 2>/dev/null | grep -q ":${HTTPS_PORT} " || \
   lsof -iTCP:${HTTPS_PORT} -sTCP:LISTEN 2>/dev/null | grep -q .; then
    echo "FATAL: Port $HTTPS_PORT already in use"
    exit 1
fi

# --- Boot VM ---
echo "==> Booting pfSense VM (HTTPS=$HTTPS_PORT, SSH=$SSH_PORT)..."
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
echo "==> QEMU PID: $QEMU_PID"

# --- Wait for API ---
echo "==> Waiting for REST API..."
MAX_WAIT=120
WAITED=0
while [[ $WAITED -lt $MAX_WAIT ]]; do
    HTTP_CODE=$(curl -sk -m 5 -o /dev/null -w '%{http_code}' \
        -u admin:pfsense \
        "https://127.0.0.1:${HTTPS_PORT}/api/v2/system/version" 2>/dev/null || echo "000")
    if [[ "$HTTP_CODE" == "200" ]]; then
        echo "==> API ready! (${WAITED}s)"
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done

if [[ $WAITED -ge $MAX_WAIT ]]; then
    echo "FATAL: API not ready after ${MAX_WAIT}s"
    exit 1
fi

# --- Build live MCP config ---
API_KEY=$(cat "$API_KEY_FILE")
LIVE_MCP_CONFIG="${RESULTS_DIR}/mcp-config-live.json"
sed -e "s|FASTMCP_PATH_PLACEHOLDER|${FASTMCP_PATH}|g" \
    -e "s|REPO_DIR_PLACEHOLDER|${REPO_DIR}|g" \
    -e "s|API_KEY_PLACEHOLDER|${API_KEY}|g" \
    "$MCP_CONFIG_TEMPLATE" > "$LIVE_MCP_CONFIG"
echo "==> Live MCP config written to $LIVE_MCP_CONFIG"

# --- Collect task files ---
# Default ordering: 01-09 (workflow) → 35,37 (read-only) → 10-34 (systematic) → 36 → 40-44 (adversarial) → 99 (destructive)
# Destructive task 99 only included with INCLUDE_DESTRUCTIVE=1
TASK_FILES=()
for task_file in "$TASKS_DIR"/*.md; do
    task_basename="$(basename "$task_file" .md)"

    # Skip destructive tasks unless opted in
    if [[ "$task_basename" == 99-* ]] && [[ "$INCLUDE_DESTRUCTIVE" != "1" ]]; then
        echo "==> Skipping destructive task: $task_basename (set INCLUDE_DESTRUCTIVE=1 to include)"
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
    echo "FATAL: No task files found matching filter '${TASK_FILTER}'"
    exit 1
fi

LIVE_LOG="${RESULTS_DIR}/live.log"
touch "$LIVE_LOG"

echo "==> Running ${#TASK_FILES[@]} task(s)..."
echo "==> Tail the live log in another terminal:"
echo "    tail -f ${LIVE_LOG}"
echo ""

# --- Run each task ---
PASSED=0
FAILED=0
TESTER_SYSTEM_PROMPT="$(cat "$TESTER_PROMPT")"

for task_file in "${TASK_FILES[@]}"; do
    task_name="$(basename "$task_file" .md)"
    echo "=== Task: $task_name ===" | tee -a "$LIVE_LOG"
    task_content="$(cat "$task_file")"

    # Run tester Claude with text output (human-readable, tailable)
    set +e
    claude -p \
        --mcp-config "$LIVE_MCP_CONFIG" \
        --strict-mcp-config \
        --permission-mode bypassPermissions \
        --output-format text \
        --model sonnet \
        --max-budget-usd 2.00 \
        --append-system-prompt "$TESTER_SYSTEM_PROMPT" \
        "$task_content" \
        2> "${RESULTS_DIR}/${task_name}.stderr" \
        | tee "${RESULTS_DIR}/${task_name}.txt" >> "$LIVE_LOG"
    task_exit=${PIPESTATUS[0]}
    set -e

    if [[ $task_exit -eq 0 ]]; then
        echo "    PASS (exit $task_exit)" | tee -a "$LIVE_LOG"
        PASSED=$((PASSED + 1))
    else
        echo "    FAIL (exit $task_exit)" | tee -a "$LIVE_LOG"
        FAILED=$((FAILED + 1))
        # Print stderr for debugging
        if [[ -s "${RESULTS_DIR}/${task_name}.stderr" ]]; then
            echo "    stderr:" | tee -a "$LIVE_LOG"
            head -5 "${RESULTS_DIR}/${task_name}.stderr" | sed 's/^/      /' | tee -a "$LIVE_LOG"
        fi
    fi
    echo "" | tee -a "$LIVE_LOG"
done

# --- Analyze results ---
echo "==> Analyzing results..."
python3 bank-tester/analyze-results.py "$RESULTS_DIR"

echo ""
echo "=== Bank Test Complete ==="
echo "  Passed: $PASSED / ${#TASK_FILES[@]}"
echo "  Failed: $FAILED / ${#TASK_FILES[@]}"
echo "  Results: $RESULTS_DIR"
echo "  Summary: ${RESULTS_DIR}/summary.md"

exit $FAILED
