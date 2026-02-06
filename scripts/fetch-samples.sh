#!/usr/bin/env bash
# Fetch API samples from all GET endpoints on a live pfSense instance.
# Only performs read-only (GET) operations — safe to run anytime.
#
# Usage: ./scripts/fetch-samples.sh [/path/to/secrets.env]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SAMPLES_DIR="$REPO_ROOT/api-samples"
SPEC_FILE="$REPO_ROOT/openapi-spec.json"
SECRETS_FILE="${1:-${PFSENSE_MCP_ENV_FILE:-/run/secrets/mcp/pfsense.env}}"

# Load credentials
if [[ ! -f "$SECRETS_FILE" ]]; then
    echo "Error: Secrets file not found: $SECRETS_FILE" >&2
    exit 1
fi

while IFS='=' read -r key value; do
    [[ -z "$key" || "$key" == \#* ]] && continue
    export "$key=$value"
done < "$SECRETS_FILE"

HOST="${PFSENSE_HOST:?PFSENSE_HOST not set}"
API_KEY="${PFSENSE_API_KEY:?PFSENSE_API_KEY not set}"
VERIFY_SSL="${PFSENSE_VERIFY_SSL:-false}"

CURL_OPTS=(-s -S --max-time 30)
if [[ "$VERIFY_SSL" == "false" ]]; then
    CURL_OPTS+=(-k)
fi

mkdir -p "$SAMPLES_DIR"

# Extract all GET paths from the OpenAPI spec
GET_PATHS=$(python3 -c "
import json, sys
spec = json.load(open('$SPEC_FILE'))
for path, methods in sorted(spec['paths'].items()):
    if 'get' in methods:
        print(path)
")

total=0
success=0
failed=0
skipped=0

echo "Fetching API samples from $HOST..."
echo "Output directory: $SAMPLES_DIR"
echo ""

while IFS= read -r path; do
    total=$((total + 1))

    # Skip endpoints that require path parameters (contain {})
    if [[ "$path" == *"{"* ]]; then
        skipped=$((skipped + 1))
        echo "SKIP $path (requires path parameters)"
        continue
    fi

    # Build filename from path: /api/v2/firewall/alias -> firewall_alias.json
    filename=$(echo "$path" | sed 's|^/api/v2/||' | tr '/' '_')
    output_file="$SAMPLES_DIR/${filename}.json"

    # Fetch with timeout
    http_code=$(curl "${CURL_OPTS[@]}" \
        -H "X-API-Key: $API_KEY" \
        -o "$output_file" \
        -w "%{http_code}" \
        "${HOST}${path}" 2>/dev/null || echo "000")

    if [[ "$http_code" == "200" ]]; then
        # Verify valid JSON
        if python3 -c "import json; json.load(open('$output_file'))" 2>/dev/null; then
            size=$(wc -c < "$output_file")
            success=$((success + 1))
            echo " OK  $path ($size bytes)"
        else
            failed=$((failed + 1))
            echo "FAIL $path (invalid JSON)"
            rm -f "$output_file"
        fi
    else
        failed=$((failed + 1))
        echo "FAIL $path (HTTP $http_code)"
        # Keep the response for debugging if it exists
        if [[ -f "$output_file" ]] && [[ ! -s "$output_file" ]]; then
            rm -f "$output_file"
        fi
    fi
done <<< "$GET_PATHS"

echo ""
echo "Done: $success OK, $failed failed, $skipped skipped (of $total GET endpoints)"
echo "Samples saved to: $SAMPLES_DIR/"
