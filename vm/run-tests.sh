#!/usr/bin/env bash
#
# Clone the golden pfSense VM, boot it, run all generated tests, tear down.
#
# Usage (from repo root):
#   nix develop -c bash vm/run-tests.sh [pytest-args...]
#
# Examples:
#   bash vm/run-tests.sh                    # run all tests
#   bash vm/run-tests.sh -x                 # stop on first failure
#   bash vm/run-tests.sh -k firewall_alias  # run only alias tests
#   bash vm/run-tests.sh -v                 # verbose output
#
# Requires: vm/golden.qcow2 (built by vm/setup.sh)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

GOLDEN="vm/golden.qcow2"
HTTPS_PORT=18443
SSH_PORT=12222
TEST_FILE="generated/tests.py"
API_KEY_FILE="vm/api-key.txt"

# --- Preflight checks ---
[[ -f "$GOLDEN" ]] || { echo "FATAL: $GOLDEN not found. Run vm/setup.sh first."; exit 1; }
[[ -f "$TEST_FILE" ]] || { echo "FATAL: $TEST_FILE not found. Run python -m generator first."; exit 1; }

# --- Create temp clone ---
TMPIMG=$(mktemp /tmp/pfsense-test-XXXXXX.qcow2)
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
    -m 1024 \
    -enable-kvm \
    -drive "file=$TMPIMG,if=virtio,format=qcow2" \
    -nographic \
    -net nic,model=virtio \
    -net "user,hostfwd=tcp::${HTTPS_PORT}-:443,hostfwd=tcp::${SSH_PORT}-:22" \
    &>/dev/null &
QEMU_PID=$!
echo "==> QEMU PID: $QEMU_PID"

# --- Wait for API ---
echo "==> Waiting for REST API..."
MAX_WAIT=120
WAITED=0
while [[ $WAITED -lt $MAX_WAIT ]]; do
    HTTP_CODE=$(curl -sk -o /dev/null -w '%{http_code}' \
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

# --- Read API key if available ---
API_KEY=""
if [[ -f "$API_KEY_FILE" ]]; then
    API_KEY=$(cat "$API_KEY_FILE" 2>/dev/null || true)
fi

# --- Run tests ---
echo "==> Running tests..."
echo ""
export PFSENSE_TEST_URL="https://127.0.0.1:${HTTPS_PORT}"
export PFSENSE_TEST_API_KEY="$API_KEY"
export PFSENSE_TEST_USER="admin"
export PFSENSE_TEST_PASS="pfsense"

# Pass any extra args to pytest (e.g. -x, -k, -v)
python3 -m pytest "$TEST_FILE" "$@"
TEST_EXIT=$?

echo ""
echo "==> Tests finished with exit code $TEST_EXIT"
exit $TEST_EXIT
