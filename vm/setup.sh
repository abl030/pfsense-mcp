#!/usr/bin/env bash
#
# Build a golden pfSense QCOW2 with the REST API installed and configured.
#
# Usage (from repo root):
#   nix shell nixpkgs#expect nixpkgs#qemu nixpkgs#curl nixpkgs#gzip -c bash vm/setup.sh
#
# Produces: vm/golden.qcow2
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

# --- Configuration ---
MEMSTICK_URL="https://atxfiles.netgate.com/mirror/downloads/pfSense-CE-memstick-serial-2.7.2-RELEASE-amd64.img.gz"
MEMSTICK_GZ="vm/pfSense-CE-memstick-serial-2.7.2-RELEASE-amd64.img.gz"
MEMSTICK="vm/pfSense-CE-memstick-serial-2.7.2-RELEASE-amd64.img"
WORK_DISK="vm/pfsense-test.qcow2"
GOLDEN_DISK="vm/golden.qcow2"
API_KEY_FILE="vm/api-key.json"

HTTPS_PORT=18443
SSH_PORT=12222

# --- Helpers ---
log() { echo "==> $*"; }
die() { echo "FATAL: $*" >&2; exit 1; }

cleanup_qemu() {
    if [[ -n "${QEMU_PID:-}" ]] && kill -0 "$QEMU_PID" 2>/dev/null; then
        log "Cleaning up QEMU (PID $QEMU_PID)..."
        kill "$QEMU_PID" 2>/dev/null || true
        wait "$QEMU_PID" 2>/dev/null || true
    fi
}
trap cleanup_qemu EXIT

wait_for_api() {
    local max_attempts=${1:-60}
    local attempt=0
    log "Waiting for REST API to become ready (max ${max_attempts}s)..."
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -sk -m 5 -o /dev/null -w '%{http_code}' \
            -u admin:pfsense \
            "https://127.0.0.1:${HTTPS_PORT}/api/v2/system/version" 2>/dev/null | grep -q '200'; then
            log "API is ready! (took ${attempt}s)"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    die "API did not become ready after ${max_attempts}s"
}

# --- Step 1: Download memstick image ---
if [[ -f "$MEMSTICK" ]]; then
    log "Memstick image already exists: $MEMSTICK"
else
    if [[ -f "$MEMSTICK_GZ" ]]; then
        log "Decompressing existing $MEMSTICK_GZ..."
    else
        log "Downloading pfSense memstick image..."
        curl -L -o "$MEMSTICK_GZ" "$MEMSTICK_URL"
    fi
    log "Decompressing memstick image..."
    gunzip -k "$MEMSTICK_GZ"
    log "Memstick ready: $MEMSTICK"
fi

# --- Step 2: Run installer (install.exp) ---
if [[ -f "$WORK_DISK" ]]; then
    log "Work disk already exists, skipping install. Delete $WORK_DISK to re-run."
else
    log "Running automated installer..."
    expect vm/install.exp
    [[ -f "$WORK_DISK" ]] || die "install.exp did not produce $WORK_DISK"
    log "Installation complete."
fi

# --- Step 3: Run first boot (firstboot.exp) ---
# firstboot.exp creates the API key and configures the VM.
# We check for the API key file as a signal that firstboot has run.
if [[ -f "$API_KEY_FILE" ]]; then
    log "API key file exists, skipping firstboot. Delete $API_KEY_FILE to re-run."
else
    log "Running first boot configuration..."
    expect vm/firstboot.exp
    [[ -f "$API_KEY_FILE" ]] || die "firstboot.exp did not produce $API_KEY_FILE"
    log "First boot complete."
fi

# --- Step 3.5: Upgrade to pfSense 2.8.1 ---
UPGRADE_SENTINEL="vm/upgrade-done"
if [[ -f "$UPGRADE_SENTINEL" ]]; then
    log "Upgrade already done, skipping. Delete $UPGRADE_SENTINEL to re-run."
else
    log "Upgrading pfSense 2.7.2 → 2.8.1..."
    expect vm/upgrade-2.8.exp
    [[ $? -eq 0 ]] || die "upgrade-2.8.exp failed"
    touch "$UPGRADE_SENTINEL"
    log "Upgrade complete."
fi

# --- Step 4: Configure golden image ---
# Boot the VM, fix auth_methods, install packages, then shut down cleanly.
log "Configuring golden image (auth_methods + packages)..."

# Boot the VM in background (no -nographic with -daemonize; use -display none)
qemu-system-x86_64 \
    -m 2048 \
    -enable-kvm \
    -drive "file=$WORK_DISK,if=virtio,format=qcow2" \
    -device virtio-rng-pci \
    -display none \
    -netdev "user,id=wan0,net=10.0.2.0/24,hostfwd=tcp::${HTTPS_PORT}-:443,hostfwd=tcp::${SSH_PORT}-:22" \
    -device e1000,netdev=wan0,mac=52:54:00:00:00:01 \
    -netdev user,id=lan0,net=10.0.3.0/24 \
    -device e1000,netdev=lan0,mac=52:54:00:00:00:02 \
    -netdev user,id=opt0,net=10.0.4.0/24 \
    -device e1000,netdev=opt0,mac=52:54:00:00:00:03 \
    -daemonize \
    -pidfile vm/qemu.pid \
    -serial null \
    -monitor none

QEMU_PID=$(cat vm/qemu.pid)
log "QEMU booted (PID $QEMU_PID)"

# Wait for API
wait_for_api 120

# --- Fix auth_methods ---
log "Checking current REST API settings..."
current_settings=$(curl -sk -u admin:pfsense \
    "https://127.0.0.1:${HTTPS_PORT}/api/v2/system/restapi/settings" 2>/dev/null)
current_auth=$(echo "$current_settings" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('auth_methods','unknown'))" 2>/dev/null || echo "unknown")
log "Current auth_methods: $current_auth"

if echo "$current_auth" | grep -q "KeyAuth"; then
    log "KeyAuth already present, no fix needed."
else
    log "Patching auth_methods to include KeyAuth..."
    patch_result=$(curl -sk -u admin:pfsense \
        -X PATCH \
        -H "Content-Type: application/json" \
        -d '{"auth_methods":["BasicAuth","KeyAuth"]}' \
        "https://127.0.0.1:${HTTPS_PORT}/api/v2/system/restapi/settings" 2>/dev/null)
    log "Patch result: $patch_result"

    # Verify the fix
    verify_settings=$(curl -sk -u admin:pfsense \
        "https://127.0.0.1:${HTTPS_PORT}/api/v2/system/restapi/settings" 2>/dev/null)
    verify_auth=$(echo "$verify_settings" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('auth_methods','unknown'))" 2>/dev/null || echo "unknown")
    log "Verified auth_methods: $verify_auth"

    echo "$verify_auth" | grep -q "KeyAuth" || die "Failed to patch auth_methods"
fi

# --- Install packages ---
# These packages are needed for full API coverage during testing.
PACKAGES=(
    "pfSense-pkg-acme"
    "pfSense-pkg-bind"
    "pfSense-pkg-Cron"
    "pfSense-pkg-freeradius3"
    "pfSense-pkg-haproxy"
    "pfSense-pkg-Service_Watchdog"
    "pfSense-pkg-WireGuard"
    "pfSense-pkg-openvpn-client-export"
)

log "Installing packages..."
for pkg in "${PACKAGES[@]}"; do
    log "  Installing $pkg..."
    result=$(curl -sk -u admin:pfsense \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$pkg\"}" \
        "https://127.0.0.1:${HTTPS_PORT}/api/v2/system/package" 2>/dev/null)
    code=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('code','?'))" 2>/dev/null || echo "err")
    if [[ "$code" == "200" ]]; then
        log "    OK"
    else
        log "    WARNING: $pkg returned code $code (may need retry)"
        # Retry once — first attempt can timeout for large packages
        sleep 5
        result=$(curl -sk -u admin:pfsense \
            -X POST \
            -H "Content-Type: application/json" \
            -d "{\"name\": \"$pkg\"}" \
            "https://127.0.0.1:${HTTPS_PORT}/api/v2/system/package" 2>/dev/null)
        code=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('code','?'))" 2>/dev/null || echo "err")
        log "    Retry: $code"
    fi
done

# Verify packages installed
installed=$(curl -sk -u admin:pfsense \
    "https://127.0.0.1:${HTTPS_PORT}/api/v2/system/packages?limit=0" 2>/dev/null | \
    python3 -c "import sys,json; pkgs=json.load(sys.stdin).get('data',[]); [print(f'  {p[\"name\"]}') for p in pkgs]" 2>/dev/null)
log "Installed packages:"
echo "$installed"

# --- Configure LAN + DHCP ---
# LAN (em1) was assigned during firstboot with 192.168.1.1/24.
# WAN firewall rules for HTTPS/SSH were added via REST API in firstboot.
# Enable DHCP server on LAN for sub-resource tests.
log "Enabling DHCP server on LAN..."
dhcp_result=$(curl -sk -u admin:pfsense \
    -X PATCH \
    -H "Content-Type: application/json" \
    -d '{"id":"lan","enable":true,"range_from":"192.168.1.100","range_to":"192.168.1.200"}' \
    "https://127.0.0.1:${HTTPS_PORT}/api/v2/services/dhcp_server" 2>/dev/null)
dhcp_code=$(echo "$dhcp_result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('code','?'))" 2>/dev/null || echo "err")
log "DHCP server enable: $dhcp_code"

log "Applying DHCP changes..."
curl -sk -u admin:pfsense -X POST \
    "https://127.0.0.1:${HTTPS_PORT}/api/v2/services/dhcp_server/apply" 2>/dev/null || true
sleep 2

# Shut down the VM gracefully so config.xml is saved to disk
log "Shutting down VM gracefully via REST API..."
curl -sk -u admin:pfsense -X POST \
    "https://127.0.0.1:${HTTPS_PORT}/api/v2/diagnostics/halt_system" \
    2>/dev/null || true

# Wait for QEMU to exit (up to 60s)
log "Waiting for QEMU to exit..."
for i in $(seq 1 60); do
    if ! kill -0 "$QEMU_PID" 2>/dev/null; then
        log "QEMU exited after ${i}s"
        break
    fi
    sleep 1
done
# Force kill if still running
if kill -0 "$QEMU_PID" 2>/dev/null; then
    log "Force killing QEMU..."
    kill "$QEMU_PID" 2>/dev/null || true
    wait "$QEMU_PID" 2>/dev/null || true
fi
unset QEMU_PID
rm -f vm/qemu.pid
sleep 2

# --- Step 5: Create golden image ---
log "Creating golden image..."
cp "$WORK_DISK" "$GOLDEN_DISK"
log "Golden image ready: $GOLDEN_DISK"

# --- Step 6: Extract API key for test use ---
if [[ -f "$API_KEY_FILE" ]]; then
    API_KEY=$(python3 -c "import json; print(json.load(open('$API_KEY_FILE')).get('data',{}).get('key',''))" 2>/dev/null || echo "")
    if [[ -n "$API_KEY" ]]; then
        echo "$API_KEY" > vm/api-key.txt
        log "API key extracted to vm/api-key.txt"
    else
        log "WARNING: Could not extract API key from $API_KEY_FILE"
    fi
fi

log ""
log "=== Golden image build complete ==="
log "  Image:   $GOLDEN_DISK"
log "  API key: vm/api-key.txt"
log ""
log "To test: bash vm/test-harness.sh"
