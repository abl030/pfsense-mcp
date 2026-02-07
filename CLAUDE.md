# pfSense MCP Server

## Goal

Build a **self-contained, auto-generated MCP server** for the pfSense REST API v2. The server is generated from `openapi-spec.json` (the official OpenAPI 3.0.0 spec, 258 paths, 178 schemas, 677 operations). When pfSense updates their API, pull a new spec and re-run the generator.

## Work Order

Complete these phases in order. Phase 1 gives you a working test target. Phase 2 builds the generator and tests against it.

### Phase 1: VM Test Infrastructure

Build `vm/setup.sh` — a single script that produces a golden pfSense QCOW2 with the REST API installed and configured. Then build a test harness so each test copies the golden image, boots it, runs tests, and destroys it.

**Deliverables:**
- `vm/setup.sh` — downloads pfSense serial memstick, runs `install.exp`, runs `firstboot.exp`, fixes `auth_methods`, produces `vm/golden.qcow2`
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

# Install (boots from memstick, installs to QCOW2)
qemu-system-x86_64 -m 1024 -enable-kvm \
    -drive file=vm/pfsense-test.qcow2,if=virtio,format=qcow2 \
    -drive file=vm/pfSense-CE-memstick-serial-2.7.2-RELEASE-amd64.img,format=raw,if=none,id=usbstick \
    -device usb-ehci -device usb-storage,drive=usbstick,bootindex=0 \
    -nographic -net nic,model=virtio \
    -net user,hostfwd=tcp::8443-:443,hostfwd=tcp::2222-:22

# Boot from disk (after install)
qemu-system-x86_64 -m 1024 -enable-kvm \
    -drive file=vm/pfsense-test.qcow2,if=virtio,format=qcow2 \
    -nographic -net nic,model=virtio \
    -net user,hostfwd=tcp::8443-:443,hostfwd=tcp::2222-:22
```

Requirements: KVM, 1024 MB RAM, 4 GB disk. QEMU user-mode networking assigns 10.0.2.15 via DHCP.

### Expect Script Gotchas (CRITICAL)

These were discovered through painful trial and error. Do NOT change the working patterns:

1. **ncurses escape sequences**: Arrow keys (`\033[A`) get misinterpreted as standalone ESC + garbage. Use letter shortcuts (`T`, `N`, `>`) instead.

2. **"Last Chance" dialog defaults to NO**: The ZFS confirmation dialog focuses NO as a safety feature. Must send `\t` (Tab) before `\r` (Enter) to switch to YES.

3. **Phase 9 pattern matching**: Matching on `"ZFS Configuration"` matches too early (dialog title renders before menu items). Match on `"stripe: 1 disk"` instead.

4. **pfSense tcsh prompt**: `[2.7.2-RELEASE][root@pfSense.home.arpa]/root:` — contains ANSI escape codes between `/root` and `:`. Match on `home\\.arpa` (consecutive bytes), NOT `$`, `#`, `%`, or `/root:`.

5. **SSH toggle**: Option 14 shows "enable" if disabled, "disable" if already enabled. Handle both cases.

6. **`service php-fpm restart` fails**: Returns error about php_fpm_enable. Ignore it — REST API works anyway because package installation triggers a webConfigurator restart.

7. **Disk appears as `vtbd0`** (VirtIO block device), NIC as `vtnet0`.

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
- First boot + REST API install: ~2-3 minutes
- Boot to API-ready: ~45-75 seconds
- Total golden image build: ~8 minutes (one-time)

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

**Current: 165 tests, 163 passing (2 transient 503s from dispatcher rate limiting)**

The test generator (`generator/test_generator.py`) produces `generated/tests.py` against the live VM. Tests cover CRUD lifecycles, settings roundtrips, read-only GETs, apply endpoints, and plural list endpoints.

### Test infrastructure

- `RetryClient` wraps httpx.Client with automatic retry on 503 (dispatcher busy), up to 4 attempts with backoff
- `_CHAINED_CRUD` supports multi-parent dependency chains with `receives_from` for inter-parent field injection (e.g., cert needs CA's refid)
- PEM certificates embedded in test constants for CA/cert-dependent endpoints (IPsec, OpenVPN, CRL, HAProxy frontend/certificate)

### Permanently skipped endpoints (17) — with reasons

**Hardware/VM limitations (5):**
- `interface` — requires available physical interface (VM has only 1 NIC assigned to WAN)
- `interface/lagg` — requires multiple physical interfaces
- `interface/gre` — requires specific tunnel config between interfaces
- `interface/gif` — requires specific tunnel config between interfaces
- `vpn/openvpn/client_export/config` — requires functioning OpenVPN server with connected client cert

**pfSense singleton design (1):**
- `services/dhcp_server` — per-interface singleton, POST not supported

**No LAN interface in VM (3):**
- `services/dhcp_server/address_pool` — requires LAN interface
- `services/dhcp_server/custom_option` — requires LAN interface
- `services/dhcp_server/static_mapping` — requires LAN interface

**pfSense server bugs (4):**
- `services/freeradius/client` — routes return nginx 404 despite package installed
- `services/freeradius/interface` — routes return nginx 404
- `services/freeradius/user` — routes return nginx 404
- `system/crl/revoked_certificate` — pfSense bug: cert serial number is hex but CRL X509_CRL.php code expects INT (500 error)

**Impractical test payloads (4):**
- `services/haproxy/backend/action` — 16 required context-dependent fields
- `services/haproxy/frontend/action` — 16 required context-dependent fields
- `services/haproxy/settings/dns_resolver` — server 500 error, requires parent model
- `services/haproxy/settings/email_mailer` — server 500 error, requires parent model

### Phantom plural routes (42)

Routes present in the OpenAPI spec but return nginx 404 on the real server. These are sub-resource plural endpoints whose singular forms require `parent_id`. The pfSense REST API simply doesn't register these routes. All are tested via their singular CRUD endpoints instead.

### Key test patterns

- **IPsec encryption**: Use `aes` (AES-CBC) with `keylen=256`, NOT `aes256gcm` (GCM keylen field is not the key size)
- **Gateway group priority**: Need a second gateway as parent — the priority's `gateway` field must reference an existing gateway by name
- **CRL `descr` field**: Not editable via PATCH — set `update_field=None` for CRL chains

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

The dev shell includes jinja2 and pytest for generator development.

## Rules

1. **Never manually edit `generated/server.py`**. Fix the generator or templates instead.
2. **`openapi-spec.json` is the single source of truth**. All type information, parameter names, and endpoint structure come from the spec.
3. **Test against the VM, not production**. The golden image exists for this purpose.
4. **Expect scripts are fragile but working**. Do not change timing, patterns, or shortcuts unless something breaks. See gotchas above.

## Integration

See `examples/nixosconfig-integration.md` for deploying into the homelab NixOS fleet.
