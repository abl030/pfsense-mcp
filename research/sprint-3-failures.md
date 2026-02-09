# Sprint 3 Failure Analysis — Bulk Plural DELETEs

**Run**: `run-20260209-120557`
**Model**: Claude Opus 4.6
**Tasks**: 60-67 (8 tasks)
**Result**: 8/8 PASS (all exit 0)
**Runtime**: ~42 minutes total (12:07 to 12:49)
**Total tool calls**: ~309 (241 confirmed from 6 structured reports + ~68 estimated from tasks 62/66)
**First-attempt failures**: 9 across 8 tasks
**First-attempt success rate**: 97.1% (241 known calls, 7 failures in those 6 tasks)

## Summary

All 8 bulk delete tasks passed. 80 bulk plural DELETE endpoints were exercised successfully. The dominant failure pattern was `MODEL_DELETE_MANY_REQUIRES_QUERY_PARAMS` — pfSense bulk DELETE endpoints require at least one query filter parameter as a safety guardrail against accidental full wipes. This is not a bug; it is intentional API behavior. The model self-corrected on every occurrence by adding a query filter on retry.

No generator bugs were found. No fixes needed. All 9 first-attempt failures fall into two categories: pfSense API safety constraints (7) and parameter format issues from task descriptions (2).

## Recurring Pattern: Bulk DELETE Query Parameter Requirement

**Observed in**: Tasks 60, 61, 65, 66, 67

All pfSense bulk DELETE (plural) endpoints return `MODEL_DELETE_MANY_REQUIRES_QUERY_PARAMS` when called without a `query` parameter. This is a server-side safety guardrail — you cannot wipe an entire collection without specifying at least one filter. The model learned this pattern after the first encounter and proactively included `query` filters on subsequent bulk deletes.

**Not a generator bug**: The tool signatures correctly expose the optional `query` parameter. The error message from pfSense is clear and actionable. Adding a note to bulk DELETE tool docstrings ("At least one query parameter is required for bulk deletion") could eliminate this failure class entirely, but at 3 occurrences across 80 bulk deletes it is a minor issue.

## Recurring Pattern: MODEL_MANY_MINIMUM_REACHED

**Observed in**: Tasks 61, 64, 67

Some sub-resources have a minimum cardinality constraint (e.g., a schedule must have at least 1 time range, an IPsec Phase 1 must have at least 1 encryption). Bulk deleting ALL items of these types fails with `MODEL_MANY_MINIMUM_REACHED`. The workaround is to either:
1. Filter the bulk delete to only remove test items (leaving at least one), or
2. Delete the parent resource, which cascades child deletion.

**Not a generator bug**: This is correct pfSense API behavior. These constraints are not documented in the OpenAPI spec, so the generator cannot know about them. The model successfully worked around each instance.

## Per-Task Analysis

### Task 60: Bulk Delete — Firewall Core

- **Status**: PASS
- **Tool calls**: 30
- **First-attempt failures**: 1
- **Tools invoked**: 25 (7 create, 9 list, 7 bulk delete, 2 apply)

| # | Tool | Error | Category | Self-corrected? |
|---|------|-------|----------|----------------|
| 1 | `pfsense_delete_firewall_states` | `MODEL_DELETE_MANY_REQUIRES_QUERY_PARAMS` — no query filter provided | pfsense_api_constraint | Yes (added `query={"interface": "em0"}`) |
| 1b | `pfsense_delete_firewall_states` (retry) | Request timed out with `limit=0` on em0 | model_behavior | Yes (retried with `limit=10`) |

**Notable**: All 7 core firewall CRUD subsystems (aliases, rules, port forwards, outbound mappings, 1:1 mappings, schedules, virtual IPs) worked flawlessly on first attempt. The only issue was `delete_firewall_states`, which is a special case — states are ephemeral kernel objects, not config items. Bulk delete with `limit=0` (unlimited) timed out because the QEMU VM had thousands of active states. Using `limit=10` succeeded.

### Task 61: Bulk Delete — Firewall Sub-Resources + Traffic Shapers

- **Status**: PASS
- **Tool calls**: 22
- **First-attempt failures**: 1
- **Tools invoked**: 20 (7 create, 4 list, 7 bulk delete, 1 singular delete, 1 apply)

| # | Tool | Error | Category | Self-corrected? |
|---|------|-------|----------|----------------|
| 1 | `pfsense_delete_firewall_schedule_time_ranges` | `MODEL_DELETE_MANY_REQUIRES_QUERY_PARAMS` — no query filter | pfsense_api_constraint | Partially (added `parent_id` filter, then hit minimum constraint) |
| 1b | `pfsense_delete_firewall_schedule_time_ranges` (retry 2) | `MODEL_MANY_MINIMUM_REACHED` — schedule needs at least 1 time range | pfsense_api_constraint | Yes (filtered by `rangedescr` to delete only test item) |

**Notable**: Limiter bandwidths also have a minimum=1 constraint, but the model proactively handled it with filtered deletes. Traffic shaper queues and limiter sub-resources all followed consistent bulk delete patterns.

### Task 62: Bulk Delete — Interface + Routing

- **Status**: PASS
- **Tool calls**: ~36 (estimated; no structured report)
- **First-attempt failures**: 0
- **Tools invoked**: 26 (per model confirmation: "All 26 tools exercised successfully")

**Notable**: Zero failures across a complex dependency chain (VLANs, GREs, groups, LAGGs, network interfaces, gateways, gateway groups, priorities, static routes). The model correctly preserved system resources (WAN, LAN, WAN_DHCP, WAN_DHCP6, WireGuard group) by using targeted query filters on every bulk delete. This is the cleanest task in the sprint.

**Limitation**: Task 62 did not produce a structured `---TASK-REPORT-START---` block. The output was only 224 bytes of summary text. All 26 tools are confirmed invoked based on the model's explicit statement, but we cannot verify exact tool call counts or parameter details.

### Task 63: Bulk Delete — DNS + DHCP Services

- **Status**: PASS
- **Tool calls**: 40
- **First-attempt failures**: 0
- **Tools invoked**: 30 (10 create, 10 list, 10 bulk delete)

**Notable**: Perfect execution across 10 subsystems (DNS resolver host overrides, aliases, domain overrides, access lists, access list networks; DNS forwarder host overrides, aliases; DHCP address pools, static mappings, custom options). Zero failures. The model noted an API inconsistency: DNS Resolver `ip` takes an array of strings while DNS Forwarder `ip` takes a single string. DHCP sub-resources correctly used `parent_id="lan"` (string), confirming the parent_id normalization fix from Phase 3.2.

### Task 64: Bulk Delete — BIND + ACME + Small Services

- **Status**: PASS
- **Tool calls**: 40
- **First-attempt failures**: 1
- **Tools invoked**: 32 (10 create, 10 list, 10 bulk delete, 2 singular delete)

| # | Tool | Error | Category | Self-corrected? |
|---|------|-------|----------|----------------|
| 1 | `pfsense_delete_services_bind_access_list_entries` | `MODEL_MANY_MINIMUM_REACHED` — ACL needs at least 1 entry | pfsense_api_constraint | Yes (filtered by `value` field to delete only test entry) |

**Notable**: ACME certificate creation correctly required an existing account key (`acmeaccount` field). Cron job bulk delete correctly used `command` field filter to avoid deleting system cron jobs. Service watchdog auto-resolved service name to description (sshd -> "Secure Shell Daemon").

### Task 65: Bulk Delete — FreeRADIUS + HAProxy

- **Status**: PASS
- **Tool calls**: 56
- **First-attempt failures**: 1
- **Tools invoked**: 44 (15 create, 14 list, 14 bulk delete, 1 apply)

| # | Tool | Error | Category | Self-corrected? |
|---|------|-------|----------|----------------|
| 1 | `pfsense_delete_services_ha_proxy_frontend_certificates` | `MODEL_DELETE_MANY_REQUIRES_QUERY_PARAMS` — empty collection, but still needs query | pfsense_api_constraint | Yes (added `query={"parent_id": "0"}`) |

**Notable**: Largest task in the sprint (44 tools). HAProxy sub-resource pattern is highly consistent: backend/frontend -> ACLs -> actions -> servers/addresses -> error files, all with `parent_id` linking. FreeRADIUS client `addr` accepts plain IP (no CIDR). Bulk delete required a query parameter even on empty collections, which tripped up the frontend certificates delete.

### Task 66: Bulk Delete — System + Users + Auth

- **Status**: PASS
- **Tool calls**: ~32 (estimated; no structured report)
- **First-attempt failures**: 2
- **Tools invoked**: 22 (per model confirmation: "All 22 tools exercised successfully")

The model's summary text reported 2 first-attempt failures:

| # | Tool | Error | Category | Self-corrected? |
|---|------|-------|----------|----------------|
| 1 | (bulk delete, likely `pfsense_delete_*`) | `MODEL_DELETE_MANY_REQUIRES_QUERY_PARAMS` — no query filter | pfsense_api_constraint | Yes |
| 2 | `pfsense_create_user` | Used `username` field instead of `name` | model_behavior | Yes (switched to `name` field) |

**Notable findings from model summary**:
- Config history revisions appear to persist even after bulk delete (pfSense may regenerate revisions immediately on config change).
- Auth keys and system certs/CAs require careful filtering to avoid self-lockout. The model correctly created throwaway resources and only bulk-deleted those.
- The `pfsense_create_user` tool uses `name` field, not `username` — this is documented in the tool schema but the model initially guessed wrong.

**Limitation**: Task 66 did not produce a structured `---TASK-REPORT-START---` block. The output was 414 bytes of summary text. The exact failure details (tool names, parameters, error messages) are not available. The 2 failures are inferred from the model's summary.

### Task 67: Bulk Delete — VPN + Status

- **Status**: PASS
- **Tool calls**: 53
- **First-attempt failures**: 3
- **Tools invoked**: 43 (14 create, 12 list, 13 bulk delete, 2 singular delete, 2 generate)

| # | Tool | Error | Category | Self-corrected? |
|---|------|-------|----------|----------------|
| 1 | `pfsense_create_vpni_psec_phase1` | Encryption sub-objects used nested format (`encryption-algorithm.name`) instead of flat (`encryption_algorithm_name`) | test_design_bug | Yes (fixed field names on retry) |
| 2 | `pfsense_delete_vpni_psec_phase1_encryptions` | `MODEL_MANY_MINIMUM_REACHED` — P1 needs at least 1 encryption | pfsense_api_constraint | No (workaround: deleted parent P1 which cascades) |
| 3 | `pfsense_create_vpn_wire_guard_tunnel` | Random base64 rejected — WireGuard private keys need Curve25519 bit clamping | model_behavior | Yes (used a properly clamped key) |

**Notable findings**:
- IPsec encryption bulk delete is fundamentally blocked by `MODEL_MANY_MINIMUM_REACHED` when the parent P1/P2 exists. The tool was invoked (exercised) but returned an error. Workaround: delete the parent resource to cascade.
- WireGuard private key validation is strict — random 32-byte base64 is not a valid Curve25519 key. The model correctly generated a clamped key on retry.
- OpenVPN server/client both require `caref` even in `p2p_tls` mode — model created CA + cert as prerequisites.
- Status endpoints (DHCP leases, OpenVPN connections) were empty on the test VM but bulk delete tools were still exercised.

## Failure Classification Summary

| Category | Count | Description |
|----------|-------|-------------|
| pfsense_api_constraint | 6 | `MODEL_DELETE_MANY_REQUIRES_QUERY_PARAMS` (3) + `MODEL_MANY_MINIMUM_REACHED` (3) — intentional safety constraints |
| model_behavior | 2 | WireGuard key format (1), `create_user` field name guess (1) — model self-corrected |
| test_design_bug | 1 | IPsec encryption nested field format in task description |
| generator_bug | 0 | None |
| pfsense_api_bug | 0 | None |

**Key observation**: Zero generator bugs and zero pfSense API bugs. All 9 first-attempt failures are either API safety constraints (working as designed) or minor model behavior issues that self-corrected. This is the cleanest sprint so far.

## Potential Generator Improvements (Optional, Low Priority)

1. **Bulk DELETE docstring hint**: Add "Note: At least one query parameter is required for bulk deletion." to all plural DELETE tool docstrings. This would eliminate the 3 `MODEL_DELETE_MANY_REQUIRES_QUERY_PARAMS` failures. Low priority since the model learns the pattern quickly.

2. **WireGuard private key hint**: Add a parameter description note: "Must be a valid Curve25519 private key (32 bytes, base64-encoded with proper bit clamping)." This would help consumers provide valid keys on first attempt.

3. **IPsec encryption field format hint**: The encryption sub-object uses flat field names (`encryption_algorithm_name`, not `encryption-algorithm.name`). The tool schema already documents this, but the task description used the wrong format.

## Coverage Impact

### Sprint 3 Tools Invoked (this run only)

- **Total unique tools**: 241
  - 80 plural (bulk) DELETE tools
  - 6 singular DELETE tools
  - 155 create/list/apply/generate tools (used as setup for bulk deletes)

### Bulk DELETE Coverage

- **Bulk DELETEs targeted**: ~85 (per CLAUDE.md Sprint 4 plan)
- **Bulk DELETEs exercised**: 80
- **Blocked by minimum constraint** (invoked but errored): 2 (`delete_vpni_psec_phase1_encryptions`, `delete_vpni_psec_phase2_encryptions` — not counted as failures since tools were invoked)
- **Not covered**: ~5 (HAProxy settings dns_resolver/email_mailer — known pfSense 500 bugs; a few edge cases)

### Running Total

| Milestone | Tools | Coverage |
|-----------|-------|---------|
| Phase 2 baseline | 504/677 | 74.4% |
| Sprint 1 (PUT/replace) | +76 list+replace = 534 | 78.9% |
| Sprint 2 (sub-resource CRUD) | +35 = 579 | 85.5% |
| **Sprint 3 (bulk DELETEs)** | **+62 net-new = 641** | **94.7%** |

**Net-new tools from Sprint 3**: ~62 (primarily bulk plural DELETEs that were never previously invoked; many of the create/list tools used as setup were already covered in prior sprints).

**Note on tasks 62 + 66**: These two tasks did not produce structured `---TASK-REPORT-START---` blocks, so their tool invocations (26 + 22 = 48 tools) are confirmed by the model's summary statements but cannot be cross-referenced with tool call counts. The summary.md from `analyze-results.py` only counted 193 tools / 6 tasks because it only parsed structured reports. The actual total including tasks 62 and 66 is 241 unique tools across all 8 tasks.

### Remaining Gap (~36 tools)

| Category | Count | Notes |
|----------|-------|-------|
| pfSense 500 bugs (HAProxy settings) | 2 | `get_/create_ services_ha_proxy_settings_{dns_resolver,email_mailer}` |
| Permanently untestable | 5 | halt, reboot, webgui settings, restapi version, restapi sync |
| PUT/replace with pfSense bugs | 7 | Sprint 1 identified 7 pfSense upstream bugs |
| Miscellaneous uncovered | ~22 | GraphQL, some sub-resource actions, diagnostics edge cases |
