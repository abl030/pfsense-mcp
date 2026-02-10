# pfSense MCP Server

Auto-generated MCP server for the pfSense REST API v2. 677 tools generated from `openapi-spec.json` (OpenAPI 3.0.0, 258 paths, 178 schemas). When pfSense updates their API, pull a new spec and re-run the generator.

## Rules

1. **Never manually edit `generated/server.py`**. Fix the generator or templates instead.
2. **`openapi-spec.json` is the single source of truth**. All type information, parameter names, and endpoint structure come from the spec.
3. **Test against the VM, not production**. The golden image exists for this purpose.
4. **Expect scripts are fragile but working**. Do not change timing, patterns, or shortcuts unless something breaks.
5. **Always use `nix develop -c`** for ALL commands that need qemu, curl, python, pytest, expect, or any dev tool.
6. **Testing must be automated**. Every feature/fix needs a pytest suite or equivalent that runs without human intervention. No manual-only verification — if it can't be `pytest`'d, write a script.
7. **Sprint progress lives in CLAUDE.md**. When work spans multiple sessions, document sprint plans, progress, and outcomes here so future sessions have full context.

## Repository Structure

```
openapi-spec.json            # OpenAPI 3.0.0 spec (input)
generator/                   # Python generator
  __main__.py                # Entry point: python -m generator
  loader.py                  # Load and parse the OpenAPI spec
  naming.py                  # Convert operationIds to tool names
  schema_parser.py           # Extract parameter types from schemas
  context_builder.py         # Build template context for each tool
  codegen.py                 # Render templates and write output
templates/
  server.py.j2               # FastMCP server template
generated/
  server.py                  # The MCP server (677 tools — never hand-edit)
test_modules.py              # Spec-derived pytest suite for module/read-only gating (85 tests)
bank-tester/                 # AI-driven integration test suite
  run-bank-test.sh           # Orchestrator: boot VM → run tasks → collect results
  generate-tasks.py          # Auto-generate task files from spec + task-config.yaml
  task-config.yaml           # Per-subsystem test values, deps, endpoint types
  analyze-results.py         # Parse results, compute tool coverage
  TESTER-CLAUDE.md           # System prompt for the tester Claude
  tasks/                     # 53 task files
  results/run-*/             # Per-run results
vm/                          # Test infrastructure
  setup.sh                   # Golden image builder (install + firstboot + upgrade)
  install.exp                # Automated pfSense installer
  firstboot.exp              # First-boot configuration
  upgrade-2.8.exp            # pfSense 2.7.2 → 2.8.1 upgrade
research/                    # Analysis documents and MCP best practices
```

## Generator

Reads `openapi-spec.json`, builds tool definitions for each path+method, renders via Jinja2.

```bash
nix develop -c python -m generator    # regenerate generated/server.py
```

### Key patterns in generated code:
- **FastMCP** server with `PfSenseClient` (httpx + X-API-Key auth)
- **Module gating**: tools wrapped in `if "module" in _PFSENSE_MODULES:` blocks (19 modules)
- **Read-only mode**: mutation tools additionally gated on `not _PFSENSE_READ_ONLY`
- **Confirmation gates**: all mutations require `confirm=True`
- **Apply reminders**: docstrings note when `{subsystem}_apply` is needed
- **Dangerous endpoint warnings**: halt, reboot, command_prompt, etc.
- **BasicAuth detection**: endpoints requiring username/password auth are flagged

### Generator fixes applied (context for future work):
- Conditional required fields downgraded to optional when description says "only available when"
- PATCH defaults set to `None` (not spec defaults) to avoid overwriting existing config
- `parent_id` and body `id` normalized to `str | int`
- `allOf`/`$ref` array items resolve to `list[dict[str, Any]]`
- Large integers (>= 2^53) replaced with `None`
- HTML stripped from descriptions
- Bulk DELETE tools include query parameter hint in docstring

### Module system (`PFSENSE_MODULES` + `PFSENSE_READ_ONLY`):
- `context_builder.py` maps each API path to one of 19 modules via `_PATH_TO_MODULE` (longest-prefix match)
- `codegen.py` groups tools by `(module, is_mutation)` and wraps in `if` blocks
- `server.py.j2` parses `PFSENSE_MODULES` (comma-separated, default: all) and `PFSENSE_READ_ONLY` (default: false)
- `pfsense_report_issue` and `pfsense_get_overview` are always registered (never gated)
- `test_modules.py` derives all expected values from the spec — zero hardcoded counts

```bash
nix develop -c python -m pytest test_modules.py -v    # 85 tests, ~2 min
```

## VM Test Infrastructure

Golden pfSense CE 2.8.1 image with REST API v2.7.1, built in ~25 minutes:

```bash
bash vm/setup.sh    # install.exp → firstboot.exp → upgrade-2.8.exp → golden.qcow2
```

Config: 3 e1000 NICs (WAN/LAN/spare), 2GB RAM, VirtIO RNG, QEMU user-mode networking.

### Rebuild shortcuts:
```bash
# Full rebuild:
rm -f vm/pfsense-test.qcow2 vm/api-key.json vm/api-key.txt vm/upgrade-done vm/golden.qcow2
bash vm/setup.sh

# Upgrade-only (skip install + firstboot):
rm -f vm/upgrade-done vm/golden.qcow2
bash vm/setup.sh
```

## Bank Tester

AI-driven integration testing: Claude consumes the MCP server as a real client against a live pfSense VM.

```bash
nix develop -c bash bank-tester/run-bank-test.sh              # all tasks
nix develop -c bash bank-tester/run-bank-test.sh 35            # single task
MODEL=opus nix develop -c bash bank-tester/run-bank-test.sh    # use Opus
nix develop -c python bank-tester/analyze-results.py bank-tester/results/run-*/  # coverage
```

### Task generation:
```bash
nix develop -c python bank-tester/generate-tasks.py    # regenerate from spec + task-config.yaml
```

Supports 8 endpoint types: `crud`, `bulk_delete`, `read_only`, `replace`, `action`, `settings`, `apply`, `setup_only`. 342 endpoint entries in `task-config.yaml` produce 51 auto-generated task files. 2 hand-written diagnostic tasks (71, 72) cover edge cases that can't be auto-generated.

## Test Coverage

**670/677 tools invoked (99.0%)** across 53 tasks and 13 runs. Verified programmatically via `analyze-results.py`.

### Untested (7 tools) — infrastructure/safety blocked

| Tool | Reason |
|------|--------|
| `pfsense_post_diagnostics_halt_system` | Shuts down VM |
| `pfsense_post_diagnostics_reboot` | Reboots VM |
| `pfsense_update_system_web_gui_settings` | Breaks API connectivity |
| `pfsense_update_system_restapi_version` | Breaks API connectivity |
| `pfsense_delete_system_packages` | Risk of removing REST API itself |
| `pfsense_create_system_restapi_settings_sync` | Requires BasicAuth + HA peer |
| `pfsense_delete_status_openvpn_server_connection` | Requires active OVPN client |

### Known pfSense API bugs (17 bugs)

All independently verified via Opus diagnostic runs. 0 generator bugs remain.

**PUT/Replace failures (7)**: Package apply hooks reference PHP functions not loaded in REST API context (FreeRADIUS x3, Service Watchdog), NTP config_path null, BIND roundtrip invariant violation, user groups uniqueness before clear.

**HAProxy singular operations (6)**: `get_config_path()` → `get_parent_model()` fails for dns_resolver and email_mailer sub-resources. LIST, CREATE, and bulk DELETE work fine.

**Service status (1)**: `Service` model reads `enabled`/`status` from raw `get_services()` array — missing keys for package services default to `false`. Affects named, radiusd, haproxy, wireguard. Docstring warning added; `pfsense_get_overview` annotates affected services.

**Other (3)**: Limiter queue ecn condition references parent model field. FreeRADIUS PATCH requires password even for unrelated changes. CRL fields immutable after creation (not marked readOnly in spec).

### Summary

| Category | Count |
|----------|-------|
| Working | **653** |
| pfSense API bug | **17** |
| Untested | **7** |
| **Total** | **677** |

## Nix Packaging

```nix
packages.x86_64-linux.default = writeShellApplication {
  name = "pfsense-mcp";
  runtimeInputs = [ pythonEnv ];
  text = ''exec fastmcp run ${./generated/server.py}'';
};
```

## Notifications

Long autonomous tasks ping via Gotify:
```bash
gotify-ping "pfSense MCP" "Task complete / Need input — check session"
```

## Open Issues

### Issue #2: Tool naming — RESOLVED in v1.1.0
Fixed `_camel_to_snake` in `naming.py`: compound word map (`HAProxy`→`haproxy`, `WireGuard`→`wireguard`, `IPsec`→`ipsec`, `OpenVPN`→`openvpn`, `GraphQL`→`graphql`) + plural acronym handling (`VLANs`→`vlans`, `CRLs`→`crls`, etc.). 198 of 677 tool names changed. Golden file regression test in `test_naming.py` (60 tests) + `tests/expected_tool_names.json`.

### Issue #3: Add `pfsense_get_overview` composite tool — RESOLVED in v1.2.0
Hand-written tool in `server.py.j2` (like `pfsense_report_issue`). Calls 4 status endpoints in parallel (version, interfaces, gateways, services), annotates package services affected by the Service model bug. Always registered, not module-gated.

### Issue #4: Service status bug for package-installed services — RESOLVED in v1.2.0
Not WireGuard-specific — affects all 4 package-installed services (WireGuard, HAProxy, BIND, FreeRADIUS). Root cause: REST API `Service` model reads `enabled`/`status` from raw `get_services()` array where package services lack these keys, defaulting to `false`. Docstring warning added to `list_status_services`, `pfsense_get_overview` annotates affected services. Full writeup in `research/service-status-bug.md`.
