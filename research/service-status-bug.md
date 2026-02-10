# Service Status Bug — REST API v2.7.1 on pfSense CE 2.8.1

## Summary

`GET /api/v2/status/services` reports `enabled: false` and `status: false` for all package-installed services, even when those services are actively running. This is **not WireGuard-specific** (as originally reported in Issue #4) — it affects all 4 package-installed services.

## Affected Services

| Service | Process | Package | `enabled` reported | `status` reported | Actually enabled? | Actually running? |
|---------|---------|---------|-------------------|-------------------|-------------------|-------------------|
| `named` | named | BIND | false | false | true | true |
| `radiusd` | radiusd | FreeRADIUS | false | false | true | true |
| `haproxy` | haproxy | HAProxy | false | false | true | true |
| `wireguard` | php_wg | WireGuard | false | false | true | true |

Core pfSense services (unbound, dpinger, syslogd, etc.) report correctly.

## Root Cause Chain

1. **`get_services()`** (pfSense core PHP) returns an array of service entries from `config.xml`
2. Package-installed services are added to the array via their package XML definitions
3. These entries do **not** include `enabled` or `status` keys — they only have `name`, `description`, `rcfile`, etc.
4. The REST API's **`Service` model** (`/usr/local/pkg/RESTAPI/Models/Service.inc`) maps the array entries to model fields
5. `Service` has `enabled` and `status` as `BooleanField` — missing keys default to `false`
6. Meanwhile, `is_service_enabled($service_name)` and `is_service_running($service_name)` (separate PHP functions) correctly check the actual service state by inspecting process tables and config flags

The bug is in the REST API's `Service` model: it reads `enabled`/`status` from the raw `get_services()` array (where they're absent for package services) instead of calling `is_service_enabled()`/`is_service_running()`.

## All Services — Full Status Table

| # | Service Name | Description | Type | `enabled` correct? | `status` correct? |
|---|-------------|-------------|------|--------------------|--------------------|
| 1 | `unbound` | DNS Resolver | Core | Yes | Yes |
| 2 | `dpinger` | Gateway Monitoring | Core | Yes | Yes |
| 3 | `syslogd` | Syslog | Core | Yes | Yes |
| 4 | `ntpd` | NTP | Core | Yes | Yes |
| 5 | `sshd` | SSH | Core | Yes | Yes |
| 6 | `dhcpd` | DHCP Server | Core | Yes | Yes |
| 7 | `named` | BIND | Package | **No** (false) | **No** (false) |
| 8 | `radiusd` | FreeRADIUS | Package | **No** (false) | **No** (false) |
| 9 | `haproxy` | HAProxy | Package | **No** (false) | **No** (false) |
| 10 | `wireguard` | WireGuard | Package | **No** (false) | **No** (false) |

## WireGuard Kernel-Level Proof

WireGuard on pfSense 2.8 uses a kernel module (not a userspace daemon), which adds an extra layer of confusion:

- `wg show` reports active tunnels with handshake data
- `ifconfig wg0` shows interface UP with assigned IP
- `php_wg` process handles configuration but isn't a traditional service daemon
- `sockstat` shows UDP listeners on WireGuard ports

Despite all this, the service status API reports both `enabled: false` and `status: false`.

## Workaround

The `pfsense_get_overview` composite tool cross-references the service list with known-buggy service names and adds a `_note` field explaining the discrepancy. For accurate individual service status, use `pfsense_post_diagnostics_command_prompt` to call `is_service_running()` / `is_service_enabled()` directly via PHP.

## Classification

- **Type**: REST API model bug (not pfSense core, not generator)
- **Severity**: Low — cosmetic/informational only; services function correctly
- **Upstream fix**: `Service.inc` should call `is_service_enabled()` / `is_service_running()` instead of reading raw array keys
- **Affected versions**: REST API v2.7.1 on pfSense CE 2.8.1 (likely affects all REST API versions)
