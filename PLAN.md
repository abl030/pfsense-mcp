# Test Failure Catalog

Full test run results: **28 failed, 89 passed** out of 117 generated tests.
Additionally, **106 tests** were skipped by the generator before they could run (58 for missing packages, 27 for parent resources, 8 for unconfigured services, 13 for complex setup requirements).

The golden VM image has the following packages installed:
- pfSense-pkg-Cron (0.3.8_3)
- pfSense-pkg-haproxy (0.63_2)
- pfSense-pkg-Service_Watchdog (1.8.7_1)
- pfSense-pkg-WireGuard (0.2.1)

---

## Category 1: Missing Packages (4 failures + 58 generator-skipped)

### Failures at Runtime (4 tests)

These tests ran but hit `MODEL_MISSING_REQUIRED_PACKAGE` or nginx 404 because the package is not installed:

| Package | Test | Error |
|---------|------|-------|
| `pfSense-pkg-openvpn-client-export` | `test_crud_vpn_openvpn_client_export_config` | nginx 404 (routes not registered without package) |

The OpenVPN client export endpoints (`/api/v2/vpn/openvpn/client_export/*`) all return nginx 404 because `pfSense-pkg-openvpn-client-export` is not installed. This is 1 CRUD test failure. The spec documents this requirement in the endpoint description: `**Required packages**: [ pfSense-pkg-openvpn-client-export ]`.

### Generator-Skipped Tests (58 tests across 4 packages)

The generator's `_MISSING_PACKAGES` list skips these. However, haproxy IS installed on the golden VM now, so 29 of these should be un-skipped.

| Package | Skipped Tests | Actually Installed? |
|---------|--------------|---------------------|
| `pfSense-pkg-haproxy` | 29 | YES -- remove from `_MISSING_PACKAGES` |
| `pfSense-pkg-bind` | 13 | No -- keep skipped |
| `pfSense-pkg-acme` | 10 | No -- keep skipped |
| `pfSense-pkg-freeradius3` | 6 | No -- keep skipped |

### Action Items

1. **Install `pfSense-pkg-openvpn-client-export`** on the golden VM, OR add `/api/v2/vpn/openvpn/client_export` to `_MISSING_PACKAGES` in the test generator to skip it.
2. **Remove `/api/v2/services/haproxy`** from `_MISSING_PACKAGES` -- haproxy IS installed. This will un-skip 29 tests (15 CRUD, 2 settings, 12 read-only).
3. **Optionally install** `pfSense-pkg-bind`, `pfSense-pkg-acme`, `pfSense-pkg-freeradius3` on the golden VM to un-skip 29 more tests. This is lower priority since they aren't typically deployed.

---

## Category 2: Phantom Plural Routes (9 failures)

These are plural (list-all) endpoints that exist in the OpenAPI spec but return **nginx 404** on the actual server. The nginx 404 (not API 404) means the routes were never registered. These are all sub-resource plural endpoints whose singular forms require `parent_id`.

| Test | URL | Parent Resource |
|------|-----|-----------------|
| `test_read_firewall_schedule_time_ranges` | `/api/v2/firewall/schedule/time_ranges` | `firewall/schedule` |
| `test_read_firewall_traffic_shaper_limiter_bandwidths` | `/api/v2/firewall/traffic_shaper/limiter/bandwidths` | `firewall/traffic_shaper/limiter` |
| `test_read_firewall_traffic_shaper_limiter_queues` | `/api/v2/firewall/traffic_shaper/limiter/queues` | `firewall/traffic_shaper/limiter` |
| `test_read_firewall_traffic_shaper_queues` | `/api/v2/firewall/traffic_shaper/queues` | `firewall/traffic_shaper` |
| `test_read_routing_gateway_group_priorities` | `/api/v2/routing/gateway/group/priorities` | `routing/gateway/group` |
| `test_read_services_dns_forwarder_host_override_aliases` | `/api/v2/services/dns_forwarder/host_override/aliases` | `services/dns_forwarder/host_override` |
| `test_read_services_dns_resolver_host_override_aliases` | `/api/v2/services/dns_resolver/host_override/aliases` | `services/dns_resolver/host_override` |
| `test_read_vpn_wireguard_tunnel_addresses` | `/api/v2/vpn/wireguard/tunnel/addresses` | `vpn/wireguard/tunnel` |
| `test_read_diagnostics_tables` | `/api/v2/diagnostics/tables` | `diagnostics/table` (special case) |

### Root Cause

The pfSense REST API v2 does not actually register these plural sub-resource routes. The spec includes them, but the server only serves the singular form (which requires `parent_id` as a query parameter). This is a **spec-vs-reality mismatch**.

The `diagnostics/tables` case is slightly different -- `diagnostics/table` is a pf firewall table (not a sub-resource), but its plural form is also not registered.

### Action Items

1. **Add all 9 paths to `_PARENT_REQUIRED_PATHS`** (or a new `_PHANTOM_PLURAL_PATHS` list) in the test generator so they get skipped.
2. Alternatively, add these paths to a `_NONEXISTENT_ROUTES` list and skip them with a clear reason: "plural route not registered on server".
3. In the generated MCP server, either omit these tools entirely or document that they are spec-only and not functional.

---

## Category 3: Bad Test Data (13 failures)

These tests fail at CREATE time (400 Bad Request) because the test data generator produces invalid values.

### 3a: FIELD_EMPTY_NOT_ALLOWED (4 tests)

The test generator sends `""` (empty string) for port fields, but the API rejects empty strings.

| Test | Field | Sent Value | Fix |
|------|-------|------------|-----|
| `test_crud_firewall_nat_outbound_mapping` | `source_port` | `""` | Send `"any"` instead |
| `test_crud_firewall_nat_port_forward` | `source_port` | `""` | Send `"any"` instead |
| `test_crud_firewall_rule` | `source_port` | `""` | Send `"any"` instead |
| `test_crud_user_auth_server` | `ldap_port` | `""` | Send `"389"` (standard LDAP port) |

**Generator fix**: In `_TEST_VALUES`, change `"source_port"` from `'""'` to `'"any"'`. Add `"ldap_port": '"389"'`.

### 3b: FIELD_INVALID_MANY_VALUE (1 test)

| Test | Field | Sent Value | Fix |
|------|-------|------------|-----|
| `test_crud_firewall_schedule` | `timerange[].position` | `""` (string) | Must be `[]` (array) |

**Generator fix**: Change the `"timerange"` test value to use `"position": []` instead of `"position": ""`.

### 3c: NUMERIC_RANGE_VALIDATOR_MINIMUM_CONSTRAINT (2 tests)

The generator defaults numeric fields to `1`, but some have higher minimums.

| Test | Field | Sent | Minimum | Fix |
|------|-------|------|---------|-----|
| `test_crud_firewall_traffic_shaper_limiter` | `buckets` | `1` | `16` | Send `16` |
| `test_crud_routing_gateway` | `latencyhigh` | `1` | `2` | Send `500` (sensible default) |

**Generator fix**: Add `"buckets": "16"` and `"latencyhigh": "500"` to `_TEST_VALUES`. Also consider adding other gateway-specific values: `"latencylow": "200"`, `"losshigh": "100"`, `"losslow": "50"`.

### 3d: IP_ADDRESS_VALIDATOR_FAILED (1 test)

| Test | Field | Sent | Fix |
|------|-------|------|-----|
| `test_crud_firewall_virtual_ip` | `subnet` | `"24"` (mask bits) | Must be an IP: `"10.99.99.100"` |

**Generator fix**: The `"subnet"` key in `_TEST_VALUES` is `'"24"'`, which works for interface subnet masks but NOT for virtual IPs where `subnet` means the actual IP address. This is a naming collision -- the same field name means different things in different contexts. Options:
- Add special-case handling in the test generator for `/firewall/virtual_ip` endpoints.
- Or rename the mapping to be context-aware (e.g., check if the endpoint is virtual_ip and use an IP address).

### 3e: X509_VALIDATOR_INVALID_VALUE (2 tests)

| Test | Field | Sent | Fix |
|------|-------|------|-----|
| `test_crud_system_certificate` | `crt` | `"test_system_certificate"` | Must be a valid PEM certificate |
| `test_crud_system_certificate_authority` | `crt` | `"test_system_certificate_authority"` | Must be a valid PEM certificate |

**Generator fix**: These endpoints need actual X509 PEM data. Options:
1. Add a pre-generated self-signed CA + cert PEM to `_TEST_VALUES` for `"crt"` and `"prv"`.
2. Skip these CRUD tests (add to `_SKIP_CRUD_PATHS`) since they require real crypto material.
3. Generate a self-signed cert at test time using the `system/certificate/generate` or similar endpoints.

### 3f: FIELD_INVALID_CHOICE (2 tests)

| Test | Field | Sent | Allowed Values | Fix |
|------|-------|------|----------------|-----|
| `test_crud_system_restapi_access_list_entry` | `sched` | `"wf2q+"` | `[]` (empty -- no schedules exist) | Omit the `sched` field entirely |
| `test_crud_services_ntp_time_server` | `type` (on UPDATE) | `"updated_test_value"` | `[server, pool, peer]` | Update a non-enum field instead |

**Generator fix**:
- For `sched` in access_list_entry: The generator sends `"wf2q+"` because `_TEST_VALUES["sched"]` matches. But `sched` in this context is a firewall schedule reference, not a scheduler algorithm. The fix is to make `sched` context-aware, or add `"sched"` to a skip list for non-required fields when the choices are dynamic.
- For the NTP update: The update step picks `type` as the first non-required string field to modify, but `type` is an enum. The update logic should skip enum fields or use a valid enum value.

### 3g: DATETIME_FIELD_MUST_MATCH_FORMAT (1 test)

| Test | Field | Sent | Required Format | Fix |
|------|-------|------|-----------------|-----|
| `test_crud_user` | `expires` | `"test_user"` | `m/d/Y` (e.g. `"12/31/2030"`) | Send `"12/31/2030"` |

**Generator fix**: Add `"expires": '"12/31/2030"'` to `_TEST_VALUES`.

### 3h: USER_GROUP_NAME_EXCEEDS_MAXIMUM_LENGTH_FOR_LOCAL_SCOPE (1 test)

| Test | Field | Sent | Constraint | Fix |
|------|-------|------|------------|-----|
| `test_crud_user_group` | `name` | `"pfsense_test_user_group"` (24 chars) | Max 16 chars for `scope=local` | Use `"pf_testgrp"` (10 chars) |

**Generator fix**: The `name` template `"pfsense_test_{unique}"` generates names that are too long for user groups. Either:
- Add a special shorter name for user groups to the test data.
- Change the `name` template to be shorter: `"pf_t_{unique}"` truncated to 16 chars.
- Or set `scope` to `"remote"` which allows longer names.

---

## Category 4: Endpoints Needing Special Handling (4 failures)

### 4a: ENDPOINT_METHOD_NOT_ALLOWED -- dhcp_server POST (1 test)

| Test | Error |
|------|-------|
| `test_crud_services_dhcp_server` | `405: Resource at /api/v2/services/dhcp_server does not support POST` |

**Root Cause**: DHCP servers cannot be created or deleted -- they are fixed to interfaces. The API only supports GET (read) and PATCH (update) on existing DHCP server configs. The OpenAPI spec technically lists POST/DELETE, but the server rejects them.

**Fix**: Add `/api/v2/services/dhcp_server` to `_SKIP_CRUD_PATHS` with reason: `"DHCP servers are per-interface singletons, cannot create/delete"`. Generate a settings-style test (GET + PATCH) instead.

### 4b: FOREIGN_MODEL_FIELD_VALUE_NOT_FOUND -- service_watchdog (1 test)

| Test | Error |
|------|-------|
| `test_crud_services_service_watchdog` | `404: Field 'name' could not locate 'Service' object with 'name' set to 'pfsense_test_services_service_watchdog'` |

**Root Cause**: Service watchdog entries reference an existing system service by `name`. The `name` field is a foreign key to the services list (e.g., `"sshd"`, `"ntpd"`, `"unbound"`). Sending a non-existent service name causes a 404.

**Fix**: Add `"name"` override for service_watchdog context, e.g. `"sshd"`. Or add a mapping: when the endpoint is `/services/service_watchdog`, use a known service name like `"sshd"`.

### 4c: FOREIGN_MODEL_FIELD_VALUE_NOT_FOUND -- wireguard peer (1 test)

| Test | Error |
|------|-------|
| `test_crud_vpn_wireguard_peer` | `404: Field 'tun' could not locate 'WireGuard Tunnel' object with 'name' set to 'test_vpn_wireguard_peer'` |

**Root Cause**: A WireGuard peer requires a `tun` field referencing an existing WireGuard tunnel by name. No tunnels exist by default, so the peer creation fails.

**Fix**: Either:
1. Create a WireGuard tunnel first (but `test_crud_vpn_wireguard_tunnel` also fails -- see 4d).
2. Add `/api/v2/vpn/wireguard/peer` to `_SKIP_CRUD_PATHS` with reason: `"requires existing WireGuard tunnel"`.
3. Chain tests so `wireguard_tunnel` creates first, then `wireguard_peer` uses it.

### 4d: FIELD_EMPTY_NOT_ALLOWED -- wireguard tunnel (1 test)

| Test | Error |
|------|-------|
| `test_crud_vpn_wireguard_tunnel` | `400: Field 'listenport' cannot be empty` |

**Root Cause**: The test sends `"listenport": ""` (empty string). WireGuard tunnels need a valid port number.

**Fix**: Add `"listenport": '"51820"'` to `_TEST_VALUES` (51820 is the standard WireGuard port).

---

## Summary of All 28 Failures by Category

| Category | Count | Tests |
|----------|-------|-------|
| **Missing package** (`openvpn-client-export`) | 1 | `test_crud_vpn_openvpn_client_export_config` |
| **Phantom plural routes** (spec-only, not on server) | 9 | `test_read_diagnostics_tables`, `test_read_firewall_schedule_time_ranges`, `test_read_firewall_traffic_shaper_limiter_bandwidths`, `test_read_firewall_traffic_shaper_limiter_queues`, `test_read_firewall_traffic_shaper_queues`, `test_read_routing_gateway_group_priorities`, `test_read_services_dns_forwarder_host_override_aliases`, `test_read_services_dns_resolver_host_override_aliases`, `test_read_vpn_wireguard_tunnel_addresses` |
| **Bad test data: empty field** (`source_port`, `ldap_port`, `listenport`) | 5 | `test_crud_firewall_nat_outbound_mapping`, `test_crud_firewall_nat_port_forward`, `test_crud_firewall_rule`, `test_crud_user_auth_server`, `test_crud_vpn_wireguard_tunnel` |
| **Bad test data: wrong type** (`position`, `subnet`, `crt`) | 3 | `test_crud_firewall_schedule`, `test_crud_firewall_virtual_ip`, (combined in 3b/3d) |
| **Bad test data: range violation** (`buckets`, `latencyhigh`) | 2 | `test_crud_firewall_traffic_shaper_limiter`, `test_crud_routing_gateway` |
| **Bad test data: invalid choice** (`sched`, `type` enum on update) | 2 | `test_crud_system_restapi_access_list_entry`, `test_crud_services_ntp_time_server` |
| **Bad test data: X509 validation** | 2 | `test_crud_system_certificate`, `test_crud_system_certificate_authority` |
| **Bad test data: format/length** (`expires`, `name`) | 2 | `test_crud_user`, `test_crud_user_group` |
| **Special handling: method not allowed** | 1 | `test_crud_services_dhcp_server` |
| **Special handling: foreign key** (`service_watchdog`, `wireguard peer`) | 2 | `test_crud_services_service_watchdog`, `test_crud_vpn_wireguard_peer` |

**Total: 28 failures** (1 package + 9 phantom routes + 14 bad data + 4 special handling = 28)

---

## Prioritized Fix Order

### Quick wins (fix in `_TEST_VALUES`, un-skip 0 failures but improve data quality)
1. `"source_port": '"any"'` -- fixes 3 CRUD tests
2. `"listenport": '"51820"'` -- fixes 1 CRUD test
3. `"ldap_port": '"389"'` -- fixes 1 CRUD test
4. `"expires": '"12/31/2030"'` -- fixes 1 CRUD test
5. `"buckets": "16"` -- fixes 1 CRUD test
6. `"latencyhigh": "500"`, `"latencylow": "200"`, `"losshigh": "100"`, `"losslow": "50"` -- fixes 1 CRUD test
7. Update `"timerange"` value to use `"position": []` -- fixes 1 CRUD test

### Generator logic fixes
8. Fix update step to not pick enum fields for the "updated_test_value" test -- fixes `test_crud_services_ntp_time_server`
9. Make `sched` field context-aware or skip it when choices are empty -- fixes `test_crud_system_restapi_access_list_entry`
10. Handle `subnet` differently for `virtual_ip` context (IP not mask) -- fixes `test_crud_firewall_virtual_ip`
11. Shorten user group name to 16 chars max -- fixes `test_crud_user_group`

### Skip list updates
12. Add `/api/v2/services/dhcp_server` to `_SKIP_CRUD_PATHS` -- 1 test
13. Add `/api/v2/vpn/wireguard/peer` to `_SKIP_CRUD_PATHS` (needs existing tunnel) -- 1 test
14. Add `/api/v2/services/service_watchdog` to `_SKIP_CRUD_PATHS` or override `name` to `"sshd"` -- 1 test
15. Add `/api/v2/vpn/openvpn/client_export` to `_MISSING_PACKAGES` -- 1 test
16. Add all 9 phantom plural routes to a new `_NONEXISTENT_ROUTES` skip list -- 9 tests
17. Remove `/api/v2/services/haproxy` from `_MISSING_PACKAGES` -- un-skips 29 tests
18. Skip or provide real X509 PEM data for certificate/CA tests -- 2 tests

### Golden VM improvements (optional)
19. Install `pfSense-pkg-openvpn-client-export` in `vm/setup.sh` to enable client_export tests
20. Optionally install `pfSense-pkg-bind`, `pfSense-pkg-acme`, `pfSense-pkg-freeradius3` to maximize test coverage

### Expected result after all fixes
- Items 1-7 fix 9 tests (quick `_TEST_VALUES` changes)
- Items 8-11 fix 4 tests (generator logic improvements)
- Items 12-16 skip 12 tests that cannot pass without complex setup
- Item 17 un-skips 29 haproxy tests (new tests that should pass)
- Item 18 skips 2 certificate tests (or fixes with real PEM data)
- Net: **0 failures**, ~134 passing tests (up from 89), ~90 skipped (down from 106)
