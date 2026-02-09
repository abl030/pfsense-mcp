# Sprint 4 Failure Analysis — Remaining Recoverable Tools + HAProxy Validation

**Runs**: `run-20260209-160222` (task 70), `run-20260209-160715` (task 71)
**Model**: Claude Opus 4.6
**Tasks**: 70-71 (2 tasks)
**Result**: 2/2 PASS (all exit 0)
**Runtime**: ~4 minutes total
**Total tool calls**: 33 (18 + 15)
**First-attempt failures**: 7 (1 + 6)
**First-attempt success rate**: 78.8%

## Summary

Sprint 4 had two objectives:
1. Recover 6 tools that were never tested but appeared feasible (DHCP server CRUD, ARP table bulk delete, REST API access list bulk delete)
2. Validate the HAProxy settings 500 bug assumption — were ALL 12 tools broken, or just some?

**Major finding**: 6 of 12 HAProxy settings tools actually WORK. Our old assumption (all 12 broken) was wrong. Only singular operations (GET/PATCH/DELETE by id) are broken — plural operations (LIST, CREATE, bulk DELETE) work fine.

## Coverage Impact

| Before Sprint 4 | After Sprint 4 |
|-----------------|----------------|
| 650/677 (96.0%) | 668/677 (98.7%) |

**+18 tools recovered** (6 DHCP/ARP/ACL + 12 HAProxy invoked, of which 6 succeeded and 6 confirmed broken but invoked)

## Per-Task Analysis

### Task 70: Remaining Recoverable Tools

- **Status**: PASS
- **Tool calls**: 18
- **First-attempt failures**: 1
- **Tools invoked**: 14 (including 6 target tools + 8 helper/setup tools)

| # | Tool | Error | Category | Self-corrected? |
|---|------|-------|----------|----------------|
| 1 | `pfsense_delete_diagnostics_arp_table` | Returned empty [] with `query={"interface": "em0"}` | parameter_format | Yes — used `"WAN"` instead of `"em0"` |

**Key findings**:
- DHCP server CRUD works cleanly when you first assign em2 as a network interface (→ opt1)
- ARP table `interface` field uses pfSense display names ("WAN", "LAN") not device names ("em0", "em1")
- REST API access list bulk DELETE correctly filters by `descr` field
- All 6 target tools exercised successfully on first or second attempt

### Task 71: HAProxy Settings 500 Bug Validation

- **Status**: PASS (diagnostic task — all tools invoked, bug status documented)
- **Tool calls**: 15
- **First-attempt failures**: 6 (all pfSense 500 bugs on singular endpoints)
- **Tools invoked**: 13 (12 target + 1 apply)

| # | Tool | Error | Category |
|---|------|-------|----------|
| 1 | `get_services_ha_proxy_settings_dns_resolver` | 500 MODEL_CANNOT_GET_CONFIG_PATH_WITHOUT_PARENT_MODEL | unexpected_error (pfSense bug) |
| 2 | `get_services_ha_proxy_settings_email_mailer` | 500 MODEL_CANNOT_GET_CONFIG_PATH_WITHOUT_PARENT_MODEL | unexpected_error (pfSense bug) |
| 3 | `update_services_ha_proxy_settings_dns_resolver` | 500 MODEL_CANNOT_GET_CONFIG_PATH_WITHOUT_PARENT_MODEL | unexpected_error (pfSense bug) |
| 4 | `update_services_ha_proxy_settings_email_mailer` | 500 MODEL_CANNOT_GET_CONFIG_PATH_WITHOUT_PARENT_MODEL | unexpected_error (pfSense bug) |
| 5 | `delete_services_ha_proxy_settings_dns_resolver` | 500 MODEL_CANNOT_GET_CONFIG_PATH_WITHOUT_PARENT_MODEL | unexpected_error (pfSense bug) |
| 6 | `delete_services_ha_proxy_settings_email_mailer` | 500 MODEL_CANNOT_GET_CONFIG_PATH_WITHOUT_PARENT_MODEL | unexpected_error (pfSense bug) |

**CRITICAL FINDING: HAProxy settings bug is PARTIAL, not total.**

WORKING (6 tools):
- `list_services_ha_proxy_settings_dns_resolvers` — returns empty array
- `list_services_ha_proxy_settings_email_mailers` — returns empty array
- `create_services_ha_proxy_settings_dns_resolver` — creates item successfully
- `create_services_ha_proxy_settings_email_mailer` — creates item successfully
- `delete_services_ha_proxy_settings_dns_resolvers` (bulk) — deletes matching items
- `delete_services_ha_proxy_settings_email_mailers` (bulk) — deletes matching items

BROKEN (6 tools — pfSense API bug, unfixable):
- `get_services_ha_proxy_settings_dns_resolver` — 500
- `get_services_ha_proxy_settings_email_mailer` — 500
- `update_services_ha_proxy_settings_dns_resolver` — 500
- `update_services_ha_proxy_settings_email_mailer` — 500
- `delete_services_ha_proxy_settings_dns_resolver` (singular) — 500
- `delete_services_ha_proxy_settings_email_mailer` (singular) — 500

**Root cause**: Plural endpoints (LIST, bulk DELETE) and CREATE operate on the collection path directly. Singular endpoints (GET/PATCH/DELETE by id) need `get_config_path()` which calls `get_parent_model()`, and the parent model construction fails for these HAProxy settings sub-resources.

## Remaining Uncovered (9 tools — all permanently blocked)

| Tool | Reason |
|------|--------|
| `create_system_package` | QEMU NAT too slow → nginx 504 |
| `delete_system_package` | QEMU NAT too slow → nginx 504 |
| `delete_system_packages` | QEMU NAT too slow → nginx 504 |
| `create_system_restapi_settings_sync` | Requires BasicAuth + HA peer |
| `delete_status_open_vpn_server_connection` | Needs active OVPN client connection |
| `post_diagnostics_halt_system` | Shuts down VM |
| `post_diagnostics_reboot` | Reboots VM |
| `update_system_restapi_version` | Breaks API connectivity |
| `update_system_web_gui_settings` | Breaks API connectivity |

## Updated HAProxy Bug Assessment

Previous: "12 HAProxy settings tools broken — 500 parent Model not constructed"
Updated: "6 HAProxy settings tools broken (singular GET/PATCH/DELETE). 6 work (LIST, CREATE, bulk DELETE)."

This is a significant correction. The old assumption was based on manual testing of only the GET endpoints during the v2.7.1 upgrade phase. By running a full diagnostic with Opus, we discovered that half the endpoints work fine.
