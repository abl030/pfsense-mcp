# pfSense MCP Server

## Goal

Build a **self-contained, auto-generated MCP server** for the pfSense REST API v2. The server is generated from `openapi-spec.json` (the official OpenAPI 3.0.0 spec, 258 paths, 178 schemas, 677 operations). When pfSense updates their API, pull a new spec and re-run the generator.

## Work Order

Complete these phases in order. Phase 1 gives you a working test target. Phase 2 builds the generator and tests against it. Phase 3 tests the MCP server end-to-end with an AI consumer.

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

## Test Coverage

OpenAPI spec: 258 paths, 677 operations. Generated MCP server: 677 tools.

Bank tester: **71 tasks across 4 sprints**, 668/677 tools invoked (**98.7% tool coverage**). 9 uncovered: 6 HAProxy singular 500 bug, 3 system package 504 (QEMU NAT), plus 4 destructive/endpoint-altering tools tested only in isolation.

Testing is done via the bank tester (`bank-tester/run-bank-test.sh`), which boots a VM, runs Claude against the MCP server, and validates results. See the Phase 3 section for details.

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

The dev shell includes jinja2, qemu, and curl for generator development and VM testing.

## Phase 3: Bank Tester Integration Testing

Test the MCP server end-to-end by having a "tester Claude" use it as a real consumer. 45 task files (9 workflow + 30 systematic + 5 adversarial + 1 destructive) reference 533/677 tools (78.7%) statically. Use findings to improve tool docstrings, parameter hints, and error messages.

### Running the bank tester

```bash
nix develop -c bash bank-tester/run-bank-test.sh              # all tasks (except destructive)
nix develop -c bash bank-tester/run-bank-test.sh 01            # single task
nix develop -c bash bank-tester/run-bank-test.sh "01 03 05"    # subset
nix develop -c bash bank-tester/run-bank-test.sh 35            # recommended: start with read-only
INCLUDE_DESTRUCTIVE=1 nix develop -c bash bank-tester/run-bank-test.sh  # include task 99
MODEL=opus nix develop -c bash bank-tester/run-bank-test.sh 50  # run with Opus (default: sonnet)
```

### Bank tester structure

```
bank-tester/
  run-bank-test.sh          # Orchestrator: boot VM → run tasks → collect results
  mcp-config.json           # MCP config template (placeholders for key/path)
  TESTER-CLAUDE.md          # System prompt for the tester Claude
  generate-tasks.py         # Auto-generate task files from OpenAPI spec + task-config.yaml
  task-config.yaml           # Per-subsystem test values, deps, skip reasons
  tasks/                    # 45 task files (01-09 workflow, 10-39 systematic, 40-44 adversarial, 99 destructive)
  analyze-results.py        # Parse tester output, aggregate failure categories + tool coverage
  results/run-*/            # Per-run results (txt + summary.md + live.log)
```

---

## Rules

1. **Never manually edit `generated/server.py`**. Fix the generator or templates instead.
2. **`openapi-spec.json` is the single source of truth**. All type information, parameter names, and endpoint structure come from the spec.
3. **Test against the VM, not production**. The golden image exists for this purpose.
4. **Expect scripts are fragile but working**. Do not change timing, patterns, or shortcuts unless something breaks. See gotchas above.
5. **Always use `nix develop -c` for ALL commands** that need qemu, curl, python, pytest, expect, or any dev tool. These are NOT on the system PATH — they are only available inside the nix dev shell. Running `qemu-system-x86_64` or `pytest` without `nix develop -c` will fail with "command not found".

## Integration

See `examples/nixosconfig-integration.md` for deploying into the homelab NixOS fleet.

---

## MCP Research — Best Practices for Building MCP Servers

**IMPORTANT: Always add new learnings to this section as they are discovered during bank tester runs, generator fixes, or any MCP-related debugging. Every fix, workaround, or surprise should be captured here as a numbered best practice. This section is the living record of what we've learned — don't let findings get lost in commit messages or memory files.**

Findings from building a 677-tool MCP server and testing it with an AI consumer (bank tester). These are hard-won lessons applicable to any MCP server project.

### Tool Schema Constraints

1. **Return type annotations must cover all response shapes.** FastMCP validates tool return values against the function's return type annotation. If your API returns both objects and arrays, the return type must be `dict[str, Any] | list[Any] | str` — not just `dict[str, Any] | str`. A `list` response against a `dict`-only annotation triggers an `Output validation error` that confuses the consumer even though the data was successfully retrieved.

2. **Sanitize large integers from OpenAPI specs.** The Anthropic API rejects tool schemas containing integers that exceed safe serialization limits (e.g., `9223372036854775807` / int64 max). OpenAPI specs commonly use these as sentinel values meaning "no limit". The generator must detect values where `abs(value) >= 2**53` and replace them with `None` defaults. Without this, the entire MCP server fails to register with `tools.N.custom.input_schema: int too big to convert`.

3. **One bad tool schema poisons the whole server.** When the Anthropic API rejects a single tool's schema, ALL tools become unavailable for that request — not just the broken one. This makes schema validation bugs critical-severity, since a single overlooked field can take down a 677-tool server.

### Tool Discoverability (What Works)

4. **Consistent naming conventions are highly discoverable.** The pattern `pfsense_{verb}_{resource}` (e.g., `create_firewall_rule`, `list_status_gateways`, `apply_firewall`) let the tester find every tool on the first attempt. Verbs: `get` (singular), `list` (plural), `create`, `update`, `delete`, `apply`.

5. **Apply-pattern reminders in docstrings work.** Adding `"Note: Call {apply_tool_name} after this to apply changes."` to mutation tool docstrings meant the tester never forgot to apply. This is more effective than relying on the consumer to know which subsystems need apply.

6. **Confirmation gates (`confirm=True`) work smoothly.** The preview-then-execute pattern for mutations caused zero confusion in testing. The tester naturally used `confirm=True` on first attempt. The preview message showing the HTTP method and path provides useful context.

### Tool Count Challenges

7. **677 tools is at the edge of API limits.** With this many tools, some API calls intermittently fail due to serialization or token budget constraints. Consider: grouping related tools, lazy-loading tool subsets, or offering a "tool catalog" meta-tool that returns available tools for a subsystem.

### Error Handling

8. **Distinguish API errors from schema validation errors.** When FastMCP's output validation rejects a valid API response, the error message is indistinguishable from an actual API failure. The consumer retried with the same parameters (which will never help for a schema bug). Error messages should clearly indicate whether the failure was in the upstream API vs. local schema validation.

9. **Sibling tool call error propagation is overly aggressive.** When one tool in a parallel batch triggers a validation error, FastMCP cancels all sibling calls with a generic error. For read-only operations, this is unnecessarily conservative — one failed GET shouldn't prevent other independent GETs from executing.

### OpenAPI-to-MCP Generation Lessons

10. **Undocumented route differences cause silent failures.** OpenAPI specs may document routes that behave differently on the real server (e.g., some sub-resource plural endpoints may 404 on older versions). Test generated tools against a live instance to identify discrepancies.

11. **`readOnly` schema fields must be excluded from request parameters.** Including response-only fields as tool parameters confuses the consumer into thinking they're settable.

12. **Enum values belong in parameter descriptions.** When an API field accepts a fixed set of values, listing them in the tool's parameter description eliminates the most common failure category (`missing_enum_values`). Don't rely on the consumer guessing valid values.

13. **Default values from specs need validation.** Not all OpenAPI defaults are safe to use as Python defaults. Sentinel values (int64 max/min), empty objects that should be `None`, and values that depend on server state should all be sanitized during generation.

### Sub-resource vs Inline Array Pattern

14. **Array parameters that are actually sub-resources cause `parameter_format` failures.** Some APIs expose array fields (e.g., WireGuard `addresses`, `allowedips`) in the create schema, but passing JSON arrays triggers validation errors. The correct pattern is to create the parent without the array, then add items via sub-resource endpoints (`tunnel/address`, `peer/allowed_ip`). Tool docstrings should explicitly note when an array parameter must be managed via sub-resources instead of inline.

### Conditional Required Fields (Solved)

15. **Conditional required fields must be downgraded to optional in the generator.** OpenAPI 3.0 can't express "required when X=Y", so specs mark conditionally-required fields (e.g., `ecname` for ECDSA, `caref` for intermediate CAs) as always-required. **Fix (implemented)**: the generator detects `"only available when"` in field descriptions and downgrades matching required fields to optional (`default=None`). The pfSense spec has 696 fields with this pattern. This eliminates 8 of 15 Opus first-attempt errors with a single pattern-matching change. See finding #25.

### Description Quality

16. **Strip HTML and increase truncation limits for conditional field docs.** OpenAPI descriptions often contain `<br>` tags and conditional availability notes (e.g., "only available when enableremotelogging is true"). A 120-char truncation limit cuts these off mid-sentence, hiding critical dependency information from the consumer. Fix: strip HTML tags, collapse whitespace, increase limit to 250 chars. This fixed a `dependency_unknown` failure in bank tester task 35 where the tester couldn't see that `logall` requires `enableremotelogging`.

17. **Conditional field defaults cause IPv4/IPv6 mismatches.** When a spec sets `default: 128` for a subnet field (valid for IPv6), sending that default for an IPv4 address causes validation failure. Fix: detect conditional fields (description contains "only available when") and set their defaults to `None` so they're only sent when explicitly specified. Applied in `schema_parser.py`.

18. **`allOf`/`$ref` in array items must resolve to `dict`, not `str`.** When an array's `items` schema uses `allOf` with a `$ref` (e.g., `timerange` containing `FirewallScheduleTimeRange` objects), the type resolver must recognize this as `list[dict[str, Any]]`, not `list[str]`. Without `$ref`/`allOf` handling, the function falls through to the default `"string"` type, generating `list[str]` which causes "must be of type array" errors when the API receives strings instead of objects.

### PATCH Default Value Hazard

19. **PATCH operations must default optional body fields to `None`, not spec defaults.** When an OpenAPI spec defines defaults for optional fields (e.g., `auth_methods: ["BasicAuth"]`), using those as Python function parameter defaults causes PATCH to overwrite existing server values with spec defaults. This is catastrophic for settings like authentication methods — the tester got locked out of API key auth because `auth_methods` silently reverted to `["BasicAuth"]`. Fix: for PATCH operations, all non-required body fields should default to `None`, meaning "don't include in request body".

### Parent ID Type Normalization

20. **Sub-resource `parent_id` fields need consistent typing.** OpenAPI specs may type `parent_id` as `integer` in request bodies but `oneOf: [integer, string]` in query parameters. The API actually accepts strings (e.g., `"lan"` for DHCP server sub-resources). Normalizing `parent_id` to `str | int` everywhere prevents type errors when consumers pass interface names as parent identifiers.

### Destructive Settings in Automated Testing

21. **Settings mutations that change the API listening endpoint break all subsequent tests.** Changing WebGUI port (443→8443), protocol (HTTPS→HTTP), or SSL certificate makes the API unreachable from MCP clients configured with the original endpoint. In a full 42-task suite run, task 28's port change killed tasks 29-37 (all returned ConnectTimeout). Fix: exclude endpoint-altering settings from automated test sequences, or run them last. These tools work correctly — they're just destructive to the test harness itself.

### MCP Client Serialization Bug

22. **Claude Code MCP client inconsistently serializes `list` parameters as strings (Sonnet only).** When a tool has `items: list[dict[str, Any]]`, the Sonnet MCP client sometimes passes the JSON array as a string (`'[]'`) instead of a parsed list. This causes Pydantic validation failures: `Input should be a valid list [type=list_type, input_value='[]', input_type=str]`. The bug is non-deterministic — `pfsense_replace_firewall_aliases` works but all 37 other identically-typed `replace_*` tools fail. **UPDATE**: Opus 4.6 does NOT reproduce this bug — all 4 replace operations tested with Opus succeeded. The bug is model-specific (Sonnet serialization behavior). Since Opus is the target model, this is no longer a blocking issue.

### PUT Replace Uniqueness Validation

23. **pfSense PUT replace validates uniqueness before clearing existing items.** When using PUT to replace a collection with the same data (idempotent no-op), pfSense validates uniqueness constraints against the existing items before clearing them. This causes false `FIELD_MUST_BE_UNIQUE` errors on resources with unique name constraints (e.g., user groups). Discovered by Opus diagnostic run. Not fixable — pfSense API bug.

### Opus 4.6 Diagnostic Run

24. **Independent Opus diagnosis validates our analysis.** An Opus 4.6 diagnostic run (task 50, `run-20260209-080902`) independently classified all 15 Opus-relevant errors. Agreement rate: 75% full agreement, 25% different-but-valid classification. Opus's top finding matches ours: conditional-required fields from polymorphic schemas is the #1 systemic issue. See `research/opus-diagnosis-run.md` and `research/error-table-opus.md` for full analysis.

### Validating "Known Bugs" Through Diagnostic Runs

26. **Always re-validate assumed-broken endpoints.** The HAProxy settings dns_resolver/email_mailer endpoints were marked as "all 12 tools broken" based on manual GET testing during v2.7.1 upgrade. Sprint 4 ran a full Opus diagnostic (task 71) that tested all 12 tools and discovered 6 actually work (LIST, CREATE, bulk DELETE). Only singular GET/PATCH/DELETE are broken. Old assumptions carried forward without validation wasted 6 coverage points. **Rule**: Never mark an endpoint as permanently broken without running it through the Opus diagnostic loop first.

### Generator Phase 4: Conditional Required + BasicAuth + Docstring Fixes

25. **Conditional required field downgrade eliminates 8 of 15 Opus errors.** When a field's description contains `"only available when"` AND the spec marks it `required`, the generator now downgrades it to optional (`default=None`). The pfSense spec has 696 fields with this exact pattern. Combined with BasicAuth endpoint detection (4 operations) and docstring improvements (PF table names, package ID format, IPsec Phase 2 hash enums, HAProxy action ACL guidance), this reduces Opus first-attempt failures from 15 to 3 (all unfixable pfSense API bugs). See `research/error-table-opus.md`.

### Bank Tester Results — Coverage Expansion Run (Complete)

**Expanded suite**: 45 tasks (was 42), 533/677 tools referenced statically (78.7%).

**Changes made**:
- Fixed list-tool discovery bug in `generate-tasks.py` (shortest path match, not first match)
- Added `update_field` to 16 CRUD entries that lacked PATCH coverage
- Added `patch_only` settings support (DHCP backend has no GET)
- Fixed DHCP address_pool `descr` (field doesn't exist), outbound mapping `target`
- New task 38: 18 read-only plural endpoints
- New task 39: 38 PUT/replace endpoints (GET→PUT same data→verify)
- Task 99 expanded: +ARP table clear, +firewall states clear

**Results** (13 runs across 4 sprints):
- **71 tasks total** (44 baseline + 8 Sprint 1 PUT/replace + 7 Sprint 2 sub-resource CRUD + 10 Sprint 3 bulk DELETEs + 2 Sprint 4 recoverable/validation)
- **668/677 unique tools invoked (98.7% tool coverage)**

**Remaining uncovered** (9 tools):

| Category | Count | Notes |
|----------|-------|-------|
| HAProxy singular 500 bug | 6 | GET/PATCH/DELETE for dns_resolver + email_mailer (LIST/CREATE/bulk DELETE work) |
| System package 504 | 3 | QEMU NAT too slow for pkg install/delete |

**Not in standard suite** (tested in isolation or blocked):
- `pfsense_post_diagnostics_halt_system` — shuts down VM (destructive)
- `pfsense_post_diagnostics_reboot` — reboots VM (task 99 only)
- `pfsense_update_system_restapi_version` — breaks API connectivity
- `pfsense_update_system_web_gui_settings` — breaks API connectivity
- `pfsense_create_system_restapi_settings_sync` — requires BasicAuth + HA setup
- `pfsense_delete_status_open_vpn_server_connection` — needs active OVPN client

### Notifications

When running long tasks autonomously, Claude will ping via Gotify on completion or when input is needed:
```bash
gotify-ping "pfSense MCP" "Task complete / Need input — check session"
```

---

## Current Task: Coverage Expansion Sprints

### Methodology — The Iterative Failure Analysis Loop

This is the core testing methodology. Every sprint follows the same cycle:

1. **Generate** new task files targeting uncovered tools (via `generate-tasks.py` + `task-config.yaml`)
2. **Copy** generated tasks to a standalone test set (only the new tasks, not the full 44-task suite — saves time and credits)
3. **Run with Opus** (`MODEL=opus nix develop -c bash bank-tester/run-bank-test.sh "51 52 53..."`)
4. **Collect first-pass failures** — save raw results to `bank-tester/results/`
5. **Categorize every failure** into `research/sprint-N-failures.md`:
   - `generator_bug` — fixable in our generator/templates
   - `openapi_spec_issue` — spec marks fields wrong, fixable via generator workarounds
   - `pfsense_api_bug` — unfixable, document and accept
   - `claude_code_bug` — MCP client issue
   - `test_design_bug` — bad test values or missing dependencies
6. **Run targeted diagnostic task** (like task 50) — have Opus independently classify each failure without hints. Compare its analysis against ours.
7. **Fix** what's fixable in the generator, regenerate `server.py`
8. **Retest** only the failing tasks — iterate until green or only pfSense bugs remain
9. **Update docs** — merge findings into `research/error-table-opus.md`, update CLAUDE.md MCP best practices, update MEMORY.md

This loop is what took us from 15 Opus errors → 3 (all pfSense bugs). Apply it to every sprint.

### Coverage Baseline

**Current**: 514/677 tools invoked (75.9%) across all runs

| Gap Category | Count | Recoverable? |
|--------------|-------|-------------|
| PUT/replace (Sonnet bug #22, Opus unblocked) | 21 | YES — full Opus re-run |
| Sub-resource CRUD + actions | 36 | YES — new task-config entries |
| Singular DELETEs (cleanup gaps) | 14 | YES — expand existing tasks |
| Bulk plural DELETEs | 85 | NEEDS DESIGN — ephemeral VMs or create-then-bulk-delete pattern |
| Permanently untestable | 7 | NO |

**Target**: 670/677 (98.9%) — everything except the 7 permanently untestable tools.

### Sprint 1: PUT/Replace Recovery (Opus re-run)

**Goal**: Recover ~21 PUT/replace tools that failed under Sonnet but work with Opus.

**Tasks**: New task 51 — copy of task 39 (PUT/replace) but run with Opus only. Covers all 38 replace endpoints. 17 already work; expect ~20 more to pass. One (`replace_user_groups`) has known pfSense uniqueness bug.

**Steps**:
1. Copy task 39 content to `bank-tester/tasks/51-put-replace-opus-retest.md`
2. Run: `MODEL=opus nix develop -c bash bank-tester/run-bank-test.sh 51`
3. Collect failures → categorize → save to `research/sprint-1-failures.md`
4. Run targeted diagnostic if any unexpected failures
5. Fix generator if needed, retest

**Expected yield**: +20 tools → 534/677 (78.9%)

### Sprint 2: Sub-Resource CRUD + Actions

**Goal**: Cover 36 uncovered create/get/list/update tools via new task-config entries.

**New tasks** (52-57), each targeting a cluster of related sub-resources:

| Task | Tools | Dependency Chain |
|------|-------|-----------------|
| 52: CRL Revoked Certs | 4 | CA → cert → CRL → revoked cert CRUD |
| 53: Gateway Group Priorities | 3 | Gateway → gateway group → priority CRUD |
| 54: Network Interface CRUD | 3 | Create/get/update a VLAN-based interface (safe, doesn't reassign WAN/LAN) |
| 55: OpenVPN Client Export | 4 | CA → server cert → OVPN server → user cert → export config → export action |
| 56: PKI Actions (renew/sign) | 3 | CA → cert → renew cert, CA renew, CSR sign |
| 57: Service Actions + Missing PATCH | ~8 | `create_status_service` (restart a service), HAProxy sub-resource updates, BIND sync host update |
| 58: Misc Gaps | ~11 | DHCP server CRUD, ACME cert domain, system package install, diagnostics singular deletes |

**Steps**:
1. Add entries to `task-config.yaml` for each task above
2. Run `nix develop -c python bank-tester/generate-tasks.py` — generates only new tasks
3. Copy generated tasks 52-58 to standalone test set
4. Run: `MODEL=opus nix develop -c bash bank-tester/run-bank-test.sh "52 53 54 55 56 57 58"`
5. Failure analysis loop (steps 4-9 from methodology)

**Expected yield**: +36 tools → 570/677 (84.2%)

### Sprint 3: Singular DELETE Coverage

**Goal**: Cover 14 singular DELETE tools that were never invoked because their parent resource was never created or cleanup was skipped.

**Approach**: Expand existing tasks or add to Sprint 2 tasks — ensure every CRUD endpoint has a proper `delete` step in cleanup. Specific fixes:

| Tool | Fix |
|------|-----|
| `delete_auth_key` | Add to task 36 (auth) — create key, then delete it |
| `delete_diagnostics_arp_table_entry` | Add to task 37 — delete single ARP entry |
| `delete_diagnostics_config_history_revision` | Add to task 37 — delete single revision |
| `delete_diagnostics_table` | Add to task 37 — delete PF table entries |
| `delete_firewall_state` | Add to task 10 — delete single state |
| `delete_system_package` | Skip — triggers nginx 504 (QEMU NAT too slow) |
| `delete_network_interface` | Covered by Sprint 2 task 54 |
| `delete_routing_gateway_group_priority` | Covered by Sprint 2 task 53 |
| `delete_services_dhcp_server` | Covered by Sprint 2 task 58 |
| `delete_system_crl_revoked_certificate` | Covered by Sprint 2 task 52 |
| `delete_vpn_open_vpn_client_export_config` | Covered by Sprint 2 task 55 |
| `delete_status_open_vpn_server_connection` | Read-only status — may not be deletable |
| `delete_services_ha_proxy_settings_dns_resolver` | Blocked — pfSense 500 bug |
| `delete_services_ha_proxy_settings_email_mailer` | Blocked — pfSense 500 bug |

**Steps**:
1. Update `task-config.yaml` for existing tasks (add delete steps)
2. Regenerate affected task files
3. Run only the modified tasks with Opus
4. Failure analysis loop

**Expected yield**: +10 tools (4 blocked) → 580/677 (85.7%)

### Sprint 4: Bulk Plural DELETEs

**Goal**: Cover ~85 bulk DELETE plural endpoints. These are the `DELETE /api/v2/.../resources` (no `id`, wipes all or filtered subset) endpoints.

**Design challenge**: Bulk deletes wipe ALL resources of a type. Can't run in the main suite — would destroy resources needed by other tasks.

**Approach**: Create-then-bulk-delete pattern in isolated tasks:
1. Create 2 resources of the type
2. Delete 1 via singular DELETE (already covered)
3. Delete remaining via bulk plural DELETE (the uncovered tool)
4. Verify collection is empty

**New tasks** (60-69), grouped by subsystem:

| Task | Bulk DELETEs | Count |
|------|-------------|-------|
| 60: Firewall bulk deletes | aliases, rules, NAT (3 types), schedules, time ranges, states, shapers, limiters, virtual IPs | ~13 |
| 61: Interface bulk deletes | VLANs, GREs, groups, LAGGs, network interfaces | ~5 |
| 62: Routing bulk deletes | gateways, gateway groups, priorities, static routes | ~4 |
| 63: Services/DNS bulk deletes | resolver (access lists, networks, host overrides, domain overrides), forwarder | ~7 |
| 64: Services/DHCP+misc bulk deletes | address pools, static mappings, custom options, cron jobs, NTP, watchdog, FreeRADIUS | ~10 |
| 65: HAProxy bulk deletes | backends, frontends, files, all sub-resources | ~14 |
| 66: VPN bulk deletes | IPsec P1/P2/encryptions, WireGuard tunnels/peers/addresses, OpenVPN | ~12 |
| 67: System bulk deletes | CAs, certs, CRLs, tunables, REST API access list, packages | ~7 |
| 68: Auth + User bulk deletes | auth keys, users, groups, auth servers, ACME, BIND | ~8 |
| 69: Status + Diagnostics bulk deletes | DHCP leases, OVPN connections, ARP table, config history | ~5 |

**IMPORTANT**: These tasks must run AFTER all other tasks, or in isolation. Each task is self-contained: create → bulk delete → verify empty.

**Steps**:
1. Add bulk delete task entries to `task-config.yaml`
2. Add `bulk_delete: true` endpoint type support to `generate-tasks.py`
3. Generate tasks 60-69
4. Run each task individually with Opus (can't parallelize — they share the VM)
5. Failure analysis loop per task

**Expected yield**: +80 tools (5 blocked by pfSense bugs) → 660/677 (97.5%)

### Sprint 5: Destructive / Ephemeral VM Tests

**Goal**: Cover the remaining ~7 tools that require special handling.

**Approach**: Use ephemeral one-shot VMs. Each test boots a fresh golden image copy, runs one destructive operation, and discards the VM.

| Tool | Test Strategy |
|------|--------------|
| `pfsense_post_diagnostics_reboot` | Boot VM → reboot → wait for API → verify. Discard VM. |
| `pfsense_post_diagnostics_halt_system` | Boot VM → halt → verify VM stopped. Discard VM. |
| `pfsense_update_system_web_gui_settings` | Boot VM → change port → verify API on new port → discard. |
| `pfsense_update_system_restapi_version` | Boot VM → attempt version change → record result → discard. |
| `pfsense_get_services_ha_proxy_settings_dns_resolver` | Known 500 bug — run, record failure, classify as pfSense bug. |
| `pfsense_get_services_ha_proxy_settings_email_mailer` | Known 500 bug — run, record failure, classify as pfSense bug. |
| `pfsense_create_system_restapi_settings_sync` | Needs BasicAuth + HA — may remain untestable without HA peer. |

**Implementation**: Modify `run-bank-test.sh` (or new `run-destructive-test.sh`) to:
1. Copy golden → ephemeral disk per task
2. Boot VM per task
3. Run single task
4. Kill VM, discard disk
5. Repeat for next task

**Expected yield**: +4-5 tools (2 are known pfSense 500 bugs, 1 needs HA) → 665/677 (98.2%)

### Sprint 6: Final Sweep + Documentation

**Goal**: Achieve maximum coverage, document everything.

**Steps**:
1. Re-run `analyze-results.py` across ALL runs — get definitive coverage number
2. For any remaining uncovered tools, categorize as: permanently blocked (pfSense bug), infrastructure limitation (QEMU/HA), or missing test (add it)
3. Run final full-suite Opus pass to confirm all tasks green
4. Update CLAUDE.md coverage numbers, MCP best practices with any new findings
5. Create `research/final-coverage-report.md` with per-tool status
6. Save all failure analyses from sprints 1-5 into `research/` folder

### Sprint Execution Order

```
Sprint 1 → Sprint 2+3 (parallel, independent) → Sprint 4 → Sprint 5 → Sprint 6
```

Sprints 2 and 3 can overlap since they target different task files. Sprint 4 (bulk deletes) must come after 2+3 since some bulk deletes need resources from sub-resource tasks. Sprint 5 needs a modified test harness. Sprint 6 is final documentation.

### Estimated Coverage Progression

| After Sprint | Tools Covered | Coverage | Delta |
|-------------|--------------|---------|-------|
| Baseline | 514 | 75.9% | — |
| Sprint 1 (PUT/replace) | 534 | 78.9% | +20 |
| Sprint 2+3 (CRUD + deletes) | 580 | 85.7% | +46 |
| Sprint 4 (bulk deletes) | 660 | 97.5% | +80 |
| Sprint 5 (destructive) | 665 | 98.2% | +5 |
| Sprint 6 (sweep) | ~668 | 98.7% | +3 |
| **Theoretical max** | **670** | **98.9%** | — |

7 tools permanently untestable. 2 of those are pfSense 500 bugs that we document but can't fix.
