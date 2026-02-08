# pfSense MCP Server

## Goal

Build a **self-contained, auto-generated MCP server** for the pfSense REST API v2. The server is generated from `openapi-spec.json` (the official OpenAPI 3.0.0 spec, 258 paths, 178 schemas, 677 operations). When pfSense updates their API, pull a new spec and re-run the generator.

## Work Order

Complete these phases in order. Phase 1 gives you a working test target. Phase 2 builds the generator and tests against it.

### Phase 1: VM Test Infrastructure

Build `vm/setup.sh` — a single script that produces a golden pfSense QCOW2 with the REST API installed and configured. Then build a test harness so each test copies the golden image, boots it, runs tests, and destroys it.

**Deliverables:**
- `vm/setup.sh` — downloads pfSense serial memstick, runs `install.exp`, runs `firstboot.exp`, runs `upgrade-2.8.exp`, fixes `auth_methods`, produces `vm/golden.qcow2`
- Test harness script or Python wrapper that: copies golden → boots QEMU → waits for API ready → runs tests → kills QEMU → deletes copy
- Smoke test that creates a firewall alias via the API and reads it back

**What already exists (read these first):**
- `vm/install.exp` — working automated ZFS installer via serial console
- `vm/firstboot.exp` — working first-boot config (interfaces, SSH, REST API install, API key)
- `vm/reference-config.xml` — full config.xml exported from a configured VM
- `vm/RESEARCH.md` — comprehensive findings from manual research

### Phase 2: Generator

**CRITICAL: NEVER edit `generated/server.py` directly. EVER.** If a generated tool has a bug, fix the generator or templates so re-running produces correct output. You are testing the generator, not the generated code. Hand-patching the output defeats the entire purpose of code generation.

Build the Python generator that reads `openapi-spec.json` and outputs `generated/server.py`. Test every generated tool against the VM from Phase 1.

**Deliverables:**
- `generator/` — Python package that reads the spec and generates the server
- `templates/server.py.j2` — Jinja2 template for code generation
- `generated/server.py` — the generated FastMCP server (output of the generator)
- Tests that verify generated tools work against the live VM

---

## Phase 1 Reference: VM Test Infrastructure

### pfSense Image (serial memstick)

Download: `https://atxfiles.netgate.com/mirror/downloads/pfSense-CE-memstick-serial-2.7.2-RELEASE-amd64.img.gz`

This is a serial-console installer image. `-nographic` in QEMU gives serial on stdio, which `expect` automates.

### QEMU Commands

```bash
# Create disk
qemu-img create -f qcow2 vm/pfsense-test.qcow2 4G

# Boot (3 e1000 NICs: em0=WAN, em1=LAN, em2=spare for LAGG tests)
qemu-system-x86_64 -m 2048 -enable-kvm \
    -drive file=vm/pfsense-test.qcow2,if=virtio,format=qcow2 \
    -device virtio-rng-pci \
    -nographic \
    -netdev user,id=wan0,net=10.0.2.0/24,hostfwd=tcp::18443-:443,hostfwd=tcp::12222-:22 \
    -device e1000,netdev=wan0,mac=52:54:00:00:00:01 \
    -netdev user,id=lan0,net=10.0.3.0/24 \
    -device e1000,netdev=lan0,mac=52:54:00:00:00:02 \
    -netdev user,id=opt0,net=10.0.4.0/24 \
    -device e1000,netdev=opt0,mac=52:54:00:00:00:03
```

Requirements: KVM, 2048 MB RAM, 4 GB disk. VirtIO RNG for entropy (critical for cert generation). QEMU user-mode networking assigns 10.0.2.15 via DHCP on WAN. 3 e1000 NICs needed for WAN+LAN+LAGG testing.

### VM Build Optimization

The install step (`install.exp`) takes ~3-5 minutes and produces a pristine installed disk. When iterating on `firstboot.exp` or `upgrade-2.8.exp`, you can skip completed steps by keeping their sentinel files:

```bash
# Full rebuild (install + firstboot + upgrade + golden):
rm -f vm/pfsense-test.qcow2 vm/api-key.json vm/api-key.txt vm/upgrade-done vm/golden.qcow2
bash vm/setup.sh

# Firstboot-only rebuild (skip install):
rm -f vm/api-key.json vm/api-key.txt vm/upgrade-done vm/golden.qcow2
bash vm/setup.sh

# Upgrade-only rebuild (skip install + firstboot, ~20 min):
rm -f vm/upgrade-done vm/golden.qcow2
bash vm/setup.sh
```

However, if firstboot or upgrade fails partway through, the work disk may have corrupt state (REST API partially installed, wrong firewall rules, etc.). In that case, delete `vm/pfsense-test.qcow2` too and do a full rebuild. Signs of corrupt state: "already installed" messages when you expect a fresh install, unexpected firewall behavior, wrong NIC assignments.

### Upgrade Iteration Workflow (disk names)

When iterating on `upgrade-2.8.exp`, use a backup disk so you never have to re-run install+firstboot (~7 min):

| Disk | Purpose |
|------|---------|
| `vm/pfsense-test.qcow2` | Work disk — install.exp and firstboot.exp write here. upgrade-2.8.exp runs on this. |
| `vm/pfsense-pre-upgrade.qcow2` | Backup of pfsense-test.qcow2 taken AFTER firstboot, BEFORE upgrade. Restore from this on upgrade failure. |
| `vm/golden.qcow2` | Final golden image — copy of pfsense-test.qcow2 after ALL steps succeed (install + firstboot + upgrade + step 4). |

```bash
# One-time: build pre-upgrade baseline (~7 min)
rm -f vm/pfsense-test.qcow2 vm/api-key.json vm/api-key.txt vm/upgrade-done vm/golden.qcow2
expect vm/install.exp && expect vm/firstboot.exp
cp vm/pfsense-test.qcow2 vm/pfsense-pre-upgrade.qcow2
```

**Fast iteration loop (< 1 min to detect failure):**

```bash
# 1. Restore clean state + delete stale log
cp vm/pfsense-pre-upgrade.qcow2 vm/pfsense-test.qcow2
rm -f vm/upgrade-2.8.log

# 2. Run upgrade in BACKGROUND
expect vm/upgrade-2.8.exp &

# 3. Tail the log — watch for failures or progress
#    Check every 30-60s. Kill immediately on "up to date", "TIMEOUT", etc.
tail -f vm/upgrade-2.8.log

# 4. On failure: kill %1, fix upgrade-2.8.exp, go to step 1
# 5. On success: touch vm/upgrade-done, continue with setup.sh step 4
```

**Key principle:** NEVER wait blindly on a long task. Always tail the log and kill early on failure. Each iteration costs only the copy time (~2s) + time to first failure, NOT 20 minutes.

### Expect Script Gotchas (CRITICAL)

These were discovered through painful trial and error. Do NOT change the working patterns:

1. **ncurses escape sequences**: Arrow keys (`\033[A`) get misinterpreted as standalone ESC + garbage. Use letter shortcuts (`T`, `N`, `>`) instead.

2. **"Last Chance" dialog defaults to NO**: The ZFS confirmation dialog focuses NO as a safety feature. Must send `\t` (Tab) before `\r` (Enter) to switch to YES.

3. **Phase 9 pattern matching**: Matching on `"ZFS Configuration"` matches too early (dialog title renders before menu items). Match on `"stripe: 1 disk"` instead.

4. **pfSense tcsh prompt**: `[2.7.2-RELEASE][root@pfSense.home.arpa]/root:` — contains ANSI escape codes between `/root` and `:`. Match on `home\\.arpa` (consecutive bytes), NOT `$`, `#`, `%`, or `/root:`.

5. **SSH toggle**: Option 14 shows "enable" if disabled, "disable" if already enabled. Handle both cases.

6. **`service php-fpm restart` fails**: Returns error about php_fpm_enable. Ignore it — REST API works anyway because package installation triggers a webConfigurator restart.

7. **Disk appears as `vtbd0`** (VirtIO block device), NICs as `em0`/`em1`/`em2` (e1000).

8. **WAN `blockpriv` blocks QEMU traffic**: With WAN+LAN configured, pfSense enables `blockpriv` (Block Private Networks) on WAN. This silently drops ALL traffic from QEMU's `10.0.2.x` subnet BEFORE any user-defined firewall rules are evaluated. Adding pass rules via easyrule or REST API has NO effect. Fix: run `pfSsh.php playback enableallowallwan` from the shell — this removes `blockpriv`, `blockbogons`, adds a pass-all WAN rule, and reloads the filter atomically.

9. **`pfctl -d` is instantly re-enabled**: Any filter reload (including REST API calls that trigger `filter_configure_sync()`) re-enables pf, making `pfctl -d` useless for anything beyond a single immediate command.

10. **Tcl bracket escaping**: `[` and `]` in Tcl `send` commands are interpreted as command substitution. Escape them as `\[` and `\]` when they appear in JSON arrays (e.g., `\"interface\":\[\"wan\"\]`).

11. **Always delete stale work disks**: When debugging firstboot.exp, always `rm vm/pfsense-test.qcow2 vm/api-key.json` before rebuilding. A work disk from a failed firstboot has partial state (REST API may be "already installed", firewall rules may be half-applied) that causes confusing expect pattern mismatches and wastes time.

12. **Curl needs `-m` timeout**: All curl commands in expect/bash scripts MUST include `-m 5` (or similar timeout). Without it, curl hangs indefinitely on SSL handshake when the firewall blocks traffic, stalling the entire build.

### Config.xml: What Needs Fixing

After `firstboot.exp` runs, the `auth_methods` in config.xml is set to `BasicAuth` only. API key auth returns 401 on subsequent boots because `KeyAuth` is not included.

**Fix**: The setup script must patch config.xml after firstboot to set:
```xml
<auth_methods>BasicAuth,KeyAuth</auth_methods>
```

This can be done via the REST API itself (BasicAuth still works) or by booting the VM, opening a shell, and using `sed` on `/cf/conf/config.xml`.

REST API config location in config.xml: `<pfsense><installedpackages><package><conf>`

### Config.xml: API Key Format

Keys are stored as SHA256 hashes:
- `<hash_algo>sha256</hash_algo>`
- `<hash>` contains `sha256(raw_key_hex_string)`

The firstboot script creates a key via `POST /api/v2/auth/key` using BasicAuth (`admin:pfsense`). The response contains the raw key. The hash in config.xml is `sha256` of that raw key.

### Test Harness Design

Each test run should be fully isolated:

```
1. cp vm/golden.qcow2 /tmp/pfsense-test-$$.qcow2
2. Boot QEMU in background (port-forwarded to random or fixed ports)
3. Poll https://127.0.0.1:8443/api/v2/system/version until 200 (API ready)
4. Run test suite against the API
5. Kill QEMU
6. rm /tmp/pfsense-test-$$.qcow2
```

Auth for tests: use BasicAuth (`admin:pfsense`) or the API key created by firstboot. Boot to API-ready takes ~45-75 seconds.

### Timing

- Install from memstick: ~3-5 minutes
- First boot + REST API v2.4.3 install: ~2-3 minutes
- Upgrade 2.7.2 → 2.8.1 + REST API v2.7.1: ~15-20 minutes
- Boot to API-ready: ~45-75 seconds
- Total golden image build: ~25 minutes (one-time)

---

## Phase 2 Reference: Generator

### Source of Truth

`openapi-spec.json` — the raw OpenAPI 3.0.0 spec from pfSense REST API v2. This is the ONLY input to the generator. Do not use `endpoint-inventory.json` or `api-samples/` — they were exploratory artifacts. Read everything from the spec directly.

### Generator Architecture

```
generator/
├── __init__.py
├── __main__.py          # Entry point: python -m generator
├── loader.py            # Load and parse the OpenAPI spec
├── naming.py            # Convert operationIds to tool names
├── schema_parser.py     # Extract parameter types from schemas
├── context_builder.py   # Build template context for each tool
└── codegen.py           # Render templates and write output
```

The generator:
1. Loads `openapi-spec.json`
2. For each path+method, builds a tool definition with: name, docstring, parameters with types, HTTP method, URL path, request body schema, whether it's a mutation
3. Renders `templates/server.py.j2` → `generated/server.py`

### Generated Server Design

- Uses **FastMCP** (`from fastmcp import FastMCP`)
- Single `PfSenseClient` class handles auth (X-API-Key header) and HTTP (httpx)
- Environment variables: `PFSENSE_HOST`, `PFSENSE_API_KEY`, `PFSENSE_VERIFY_SSL`
- One async tool function per API operation
- Graceful error handling with clear messages

### Authentication

All requests use `X-API-Key: <key>` header. No session/cookie management needed.

### Response Envelope

Every response follows:
```json
{"code": 200, "status": "ok", "response_id": "SUCCESS", "message": "", "data": { ... }}
```

The generated tools should unwrap this and return `data` directly. On error, return the full envelope for debugging.

### CRUD Pattern

Most resources follow:
```
GET    /api/v2/{category}/{resource}s   → list all (plural, supports limit/offset/sort_by/sort_order/query)
GET    /api/v2/{category}/{resource}    → get one (singular, requires ?id=N)
POST   /api/v2/{category}/{resource}    → create (request body from schema)
PATCH  /api/v2/{category}/{resource}    → update (id + fields in body)
DELETE /api/v2/{category}/{resource}    → delete (requires ?id=N, optional ?apply=true)
```

### Apply Pattern

Some subsystems require explicit apply after mutations: `firewall`, `firewall/virtual_ip`, `interface`, `routing`, `services/dhcp_server`, `services/dns_forwarder`, `services/dns_resolver`, `services/haproxy`, `vpn/ipsec`, `vpn/wireguard`.

```
GET  /api/v2/{category}/apply    → check apply status
POST /api/v2/{category}/apply    → apply pending changes
```

After create/update/delete on these subsystems, the tool docstring should remind the user to call the apply endpoint.

### Settings Pattern

Singletons (not CRUD collections):
```
GET   /api/v2/{category}/settings   → read settings
PATCH /api/v2/{category}/settings   → update settings
```

### Tool Naming

Convert operationId to tool name:
1. Strip `Endpoint` suffix
2. `get` (singular) → `get`, `get` (plural) → `list`
3. `post` → `create` (CRUD) or keep for actions/apply
4. `patch` → `update`, `delete` → `delete`
5. CamelCase → snake_case
6. Prefix with `pfsense_`
7. Flatten nested resources: `/services/haproxy/backend/acl` → `pfsense_create_haproxy_backend_acl`

Apply endpoints: `pfsense_apply_{subsystem}` / `pfsense_get_{subsystem}_apply_status`

### Confirmation Gates

All mutations (POST, PATCH, PUT, DELETE) require `confirm: bool = False`:
- `confirm=False` (default): return preview (parameters, endpoint URL)
- `confirm=True`: execute the mutation

Read-only operations (GET) never need confirmation.

### Dangerous Endpoints (Exclude or Gate)

Exclude from generation or add extra warnings:
- `POST /api/v2/diagnostics/halt_system`
- `POST /api/v2/diagnostics/reboot`
- `POST /api/v2/diagnostics/command_prompt`
- `DELETE /api/v2/diagnostics/arp_table` (bulk clear)
- `DELETE /api/v2/diagnostics/config_history/revisions` (bulk clear)
- `DELETE /api/v2/firewall/states` (bulk clear)
- `POST /api/v2/graphql` (raw execution)

### Known Quirks

1. **Singular GET returns 400 without `id`**: Expected behavior, not a bug.
2. **DELETE `apply` parameter**: Some DELETEs accept `?apply=true`.
3. **PUT vs PATCH**: PUT is bulk replacement on plural endpoints. PATCH is partial update. Prefer PATCH for tools.
4. **Status endpoints**: All read-only (GET only). No confirmation needed.
5. **Log endpoints**: Can return megabytes. Tools must accept `limit`.
6. **CARP status**: `PATCH /status/carp` is a mutation disguised as status.

---

## Phase 2 Status: Test Coverage

**Current: 203 tests, 203 passing** against 258 API paths (677 operations)

### Coverage summary

| Metric | Count | % |
|---|---|---|
| Paths with active tests | 203 | 78.7% |
| Paths with documented skip | 55 | 21.3% |
| **Total accounted** | **258** | **100%** |

pfSense CE 2.8.1 with REST API v2.7.1 (upgraded from 2.7.2 via `upgrade-2.8.exp`).

### Test infrastructure

- `RetryClient` wraps httpx.Client with automatic retry on 503 (dispatcher busy), up to 6 attempts with backoff
- `_CHAINED_CRUD` supports multi-parent dependency chains with `receives_from` for inter-parent field injection (e.g., cert needs CA's refid)
- `_CHAINED_CRUD` supports `static_parent_id` for sub-resources with a fixed parent (e.g., DHCP sub-resources always use `parent_id: "lan"`)
- `_CHAINED_CRUD` supports `siblings` for creating sibling resources under the same parent (e.g., HAProxy ACL for action tests)
- PEM certificates embedded in test constants for CA/cert-dependent endpoints (IPsec, OpenVPN, CRL, HAProxy frontend/certificate)
- VM uses 3 e1000 NICs (em0=WAN, em1=LAN, em2=spare for LAGG), VirtIO RNG, 2GB RAM
- REST API v2.7.1 on pfSense CE 2.8.1 (upgraded via `vm/upgrade-2.8.exp`)

### Permanently skipped endpoints — with reasons

Every skip is documented in `_SKIP_CRUD_PATHS`, `_SKIP_ACTION`, `_SKIP_SINGLETON`, or `_PHANTOM_PLURAL_ROUTES` in `test_generator.py`.

**Hardware/VM limitations (2):**
- `interface` — interface CRUD can destabilize VM (em2 reserved for LAGG)
- `vpn/openvpn/client_export/config` — complex 5-step chain: CA+cert+OVPN server+user cert (deferred)

**pfSense singleton design (1):**
- `services/dhcp_server` — per-interface singleton, POST not supported

**REST API bugs persisting in v2.7.1 (3):**
- `services/haproxy/settings/dns_resolver`, `email_mailer` — 500 parent model construction bug
- `system/certificate/pkcs12/export` — 406 no content handler for binary format

**Infrastructure limitations (1):**
- `system/package` — install/delete trigger nginx 504 gateway timeout (>60s via QEMU NAT); GET endpoints tested via read tests

**External dependencies (4):**
- `services/acme/account_key/register` — needs real ACME server
- `services/acme/certificate/issue` — needs real ACME server
- `services/acme/certificate/renew` — needs real ACME server
- `system/restapi/settings/sync` — HA sync endpoint times out without peer

**Other (2):**
- `vpn/openvpn/client_export` — requires functioning OpenVPN server
- `system/restapi/version` — PATCH triggers API version change (destructive)

### Phantom plural routes (39)

Routes present in the OpenAPI spec but return nginx 404 on the real server. These are sub-resource plural endpoints whose singular forms require `parent_id`. The pfSense REST API simply doesn't register these routes. All are tested via their singular CRUD endpoints instead.

### Backlog: Endpoint Unblocking Sprints

Deep research on all skipped endpoints is in `research/skipped-endpoints-analysis.md`. Work is split into 10 sprints, ordered by confidence (high first). Each sprint follows the same process:

1. **Plan** — read the research report for that sprint, read the current test generator and any relevant generated tests, then enter plan mode and propose an approach
2. **Iterate** — implement, regenerate, run targeted tests (`-k`), fix failures, repeat
3. **Finalize** — run full suite, commit, update this section with the outcome (passed/blocked/skipped)
4. **Decision** — if it doesn't work for a technical reason, document why here and move on

**When you open a new Claude session in this repo, check which sprint is next (the first one without a status) and start its planning phase.**

| Sprint | Endpoints | Approach | Status |
|--------|-----------|----------|--------|
| 0 | Phantom plural routes (39 paths) | Remove from MCP server generator (`codegen.py`/`context_builder.py`) using `_PHANTOM_PLURAL_ROUTES` set. Update tool count in `README.md` and `flake.nix`. | **TODO** |
| 1 | `interface` CRUD (+3 tests) | Create VLAN on em2, assign as opt1, PATCH, delete. Safe — doesn't touch WAN/LAN. | **TODO** |
| 2 | `services/dhcp_server` POST | Confirm by-design limitation. Re-categorize skip reason from "singleton" to "not applicable — POST not supported, PATCH tested". No new tests needed. | **TODO** |
| 3 | `system/certificate/pkcs12/export` (+1 test) | Try `Accept: application/octet-stream` header. If still 406, use client-side PKCS12 generation as fallback proof. | **TODO** |
| 4 | `services/haproxy/settings/dns_resolver` & `email_mailer` (+2 tests) | Initialize HAProxy config in config.xml via `diagnostics/command_prompt` PHP call, then POST sub-resources. | **TODO** |
| 5 | `system/package` POST/DELETE (+1 test) | Try `pfSense-pkg-cron` (smaller than arping). Use 504-as-success polling pattern. | **TODO** |
| 6 | `vpn/openvpn/client_export` (+3 tests) | 6-step chain: CA → server cert → OVPN server → user cert → export → config GET/DELETE. Pre-install `pfSense-pkg-openvpn-client-export` in golden image. | **TODO** |
| 7 | ACME `register`/`issue`/`renew` (+3 tests) | Run Pebble (test ACME server) on host, configure custom ACME server URL in pfSense, register + issue + renew. Requires Docker on host. | **TODO** |
| 8 | `system/restapi/settings/sync` | Try localhost sync or async dispatcher. Low confidence — likely stays skipped. | **TODO** |
| 9 | `system/restapi/version` PATCH | Confirm too destructive. Keep skipped. | **TODO** |

### Key test patterns

- **IPsec encryption**: Use `aes` (AES-CBC) with `keylen=256`, NOT `aes256gcm` (GCM keylen field is not the key size)
- **Gateway group priority**: Need a second gateway as parent — the priority's `gateway` field must reference an existing gateway by name
- **CRL `descr` field**: Not editable via PATCH — set `update_field=None` for CRL chains
- **Auth endpoints**: `auth/key` and `auth/jwt` require BasicAuth, not API key. Tests use a dedicated httpx.Client with `auth=(user, pass)`
- **Skip priority**: `_SKIP_CRUD_PATHS` is checked before `_CHAINED_CRUD`, `_SKIP_ACTION` is checked before `_ACTION_TESTS` — this ensures skips always win

---

## Nix Packaging

`flake.nix` wraps the generated server:

```nix
packages.x86_64-linux.default = writeShellApplication {
  name = "pfsense-mcp";
  runtimeInputs = [ pythonEnv ];  # python3 with fastmcp + httpx
  text = ''exec fastmcp run ${./generated/server.py}'';
};
```

The dev shell includes jinja2, pytest, qemu, and curl for generator development and VM testing.

## Rules

1. **Never manually edit `generated/server.py`**. Fix the generator or templates instead.
2. **`openapi-spec.json` is the single source of truth**. All type information, parameter names, and endpoint structure come from the spec.
3. **Test against the VM, not production**. The golden image exists for this purpose.
4. **Expect scripts are fragile but working**. Do not change timing, patterns, or shortcuts unless something breaks. See gotchas above.
5. **Every skipped endpoint must be documented with a reason** — in `_SKIP_CRUD_PATHS`, `_SKIP_ACTION`, `_SKIP_SINGLETON`, or `_PHANTOM_PLURAL_ROUTES` in `test_generator.py`, AND in the "Permanently skipped endpoints" section of this file. No silent skips.
6. **Always use `nix develop -c` for ALL commands** that need qemu, curl, python, pytest, expect, or any dev tool. These are NOT on the system PATH — they are only available inside the nix dev shell. Running `qemu-system-x86_64` or `pytest` without `nix develop -c` will fail with "command not found".

## Test Development Workflow

Each full test run takes ~5-8 minutes. To avoid wasting time:

1. **Regenerate**: `nix develop -c python -m generator`
2. **Test only new/changed tests first** using `-k` filter:
   ```bash
   nix develop -c bash vm/run-tests.sh -v -k "singleton_ or action_"
   ```
3. **Iterate on failures** — keep using `-k` to re-run only failing tests until all pass
4. **Final full suite run** — only after new tests all pass individually:
   ```bash
   nix develop -c bash vm/run-tests.sh -v
   ```
5. **Commit** only after full suite passes

## Integration

See `examples/nixosconfig-integration.md` for deploying into the homelab NixOS fleet.
