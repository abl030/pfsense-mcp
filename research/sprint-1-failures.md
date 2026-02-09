# Sprint 1: PUT/Replace Recovery — Failure Analysis

**Run**: `run-20260209-103541`
**Model**: Claude Opus 4.6
**Task**: 39 (PUT/replace — all 38 plural collection replacements)
**Result**: PASS (exit 0), 114 tool calls, 272 seconds
**Tools invoked**: 76 (38 list + 38 replace)

## Summary

31/38 replace operations succeeded on first attempt. All 7 failures are pfSense API bugs.

| Category | Count | Fixable? |
|----------|-------|----------|
| pfSense API bug — undefined function | 4 | NO (upstream) |
| pfSense API bug — null config path | 1 | NO (upstream) |
| pfSense API bug — validation ordering | 1 | NO (upstream, known #23) |
| pfSense API bug — roundtrip invariant | 1 | NO (upstream) |
| Generator bug | 0 | — |
| OpenAPI spec issue | 0 | — |
| MCP client bug | 0 | — |

## Every Failure, Classified

### 1. FreeRADIUS Clients — `replace_services_free_radius_clients`

**Error**: `Call to undefined function RESTAPI\Models\freeradius_clients_resync()`
**Classification**: **pfsense_api_bug**
**Analysis**: FreeRADIUS package REST API models define a `replace_all()` method that calls `apply()`, which invokes `freeradius_clients_resync()`. This PHP function doesn't exist in the REST API models. The FreeRADIUS package likely provides it via its own include, but the REST API doesn't load it for PUT operations.
**Workaround**: None — cannot use PUT replace for FreeRADIUS clients.

### 2. FreeRADIUS Interfaces — `replace_services_free_radius_interfaces`

**Error**: `Call to undefined function RESTAPI\Models\freeradius_settings_resync()`
**Classification**: **pfsense_api_bug**
**Analysis**: Same root cause as #1. Different resync function name (`freeradius_settings_resync` vs `freeradius_clients_resync`), same missing-function pattern.
**Workaround**: None.

### 3. FreeRADIUS Users — `replace_services_free_radius_users`

**Error**: `Call to undefined function RESTAPI\Models\freeradius_users_resync()`
**Classification**: **pfsense_api_bug**
**Analysis**: Same root cause as #1 and #2.
**Workaround**: None.

### 4. NTP Time Servers — `replace_services_ntp_time_servers`

**Error**: `RESTAPI\Core\Model::set_config(): Argument #1 ($path) must be of type string, null given`
**Classification**: **pfsense_api_bug**
**Analysis**: The `NTPTimeServer` model has a null `config_path` property. When `replace_all()` calls `set_config()` to write the replaced collection back to config.xml, it passes null as the path, triggering a PHP type error. The model likely has a parent/child config path structure where the parent isn't properly initialized for PUT operations.
**Workaround**: None — cannot use PUT replace for NTP time servers.

### 5. Service Watchdogs — `replace_services_service_watchdogs`

**Error**: `Call to undefined function RESTAPI\Models\servicewatchdog_cron_job()`
**Classification**: **pfsense_api_bug**
**Analysis**: Same pattern as FreeRADIUS — the ServiceWatchdog model's `apply()` method calls `servicewatchdog_cron_job()`, which is a package-provided function not loaded by the REST API for PUT operations.
**Workaround**: None.

### 6. BIND Access Lists — `replace_services_bind_access_lists`

**Error**: `Field 'entries' must contain a minimum of 1 entries.`
**Classification**: **pfsense_api_bug** (roundtrip invariant violation)
**Analysis**: pfSense has 4 built-in BIND access lists. GET returns them with empty `entries` arrays. PUT validates that each ACL has at least 1 entry. This means GET→PUT roundtrip fails — the API returns data that it won't accept back. This is a validation asymmetry bug.
**Workaround**: Could filter out built-in ACLs before PUT, but this requires consumer-side knowledge of which ACLs are built-in.

### 7. User Groups — `replace_user_groups`

**Error**: `Field 'name' must be unique. Value is in use by object with ID '0'.`
**Classification**: **pfsense_api_bug** (known #23)
**Analysis**: Known bug. PUT replace validates uniqueness constraints against the existing collection before clearing it. Replacing groups with the same data fails because `name` appears to be duplicated (old group + new group with same name). This was independently discovered by the Opus diagnostic run.
**Workaround**: None — fundamental validation ordering issue.

## Key Takeaways

1. **Opus completely eliminates the Sonnet MCP client serialization bug (#22).** All 38 replace tools were successfully called (even the 7 that return API errors). With Sonnet, 37/38 failed before even reaching the API.

2. **5 new pfSense API bugs discovered** (in addition to 2 previously known):
   - 3x FreeRADIUS undefined resync functions
   - 1x NTP null config path
   - 1x Service Watchdog undefined function
   - 1x BIND access list roundtrip invariant violation
   (Previously known: user groups uniqueness #23)

3. **Zero generator, spec, or client issues.** The replace tool generation is correct. All failures are in pfSense's PHP backend.

4. **New pfSense bug pattern**: Package-provided functions (FreeRADIUS, Service Watchdog) aren't loaded during PUT replace operations. This suggests the REST API's `replace_all()` code path doesn't include package function files. Likely affects any package with custom apply/resync functions.

## Coverage Impact

- **Previously invoked**: 523/677 (77.3%) across 7 runs
- **Net new from Sprint 1**: +21 replace tools (many list+replace tools already covered from prior runs)
- **Running total**: **544/677 (80.4%)**
- **Remaining gap**: 133 tools (85 bulk DELETEs, ~28 sub-resource CRUD, ~14 singular DELETEs, 7 permanently untestable)

### New tools from Sprint 1
```
pfsense_replace_services_acme_certificates
pfsense_replace_services_bind_access_lists
pfsense_replace_services_bind_sync_remote_hosts
pfsense_replace_services_bind_views
pfsense_replace_services_bind_zones
pfsense_replace_services_dhcp_servers
pfsense_replace_services_dns_forwarder_host_overrides
pfsense_replace_services_dns_resolver_access_lists
pfsense_replace_services_dns_resolver_domain_overrides
pfsense_replace_services_free_radius_interfaces
pfsense_replace_services_free_radius_users
pfsense_replace_services_ha_proxy_backends
pfsense_replace_services_ha_proxy_files
pfsense_replace_services_ha_proxy_frontends
pfsense_replace_services_ntp_time_servers
pfsense_replace_services_service_watchdogs
pfsense_replace_system_restapi_access_list
pfsense_replace_vpni_psec_phase2s
pfsense_replace_vpn_open_vpn_client_export_configs
pfsense_replace_vpn_wire_guard_peers
pfsense_replace_vpn_wire_guard_tunnels
```
