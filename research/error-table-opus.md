# Known pfSense API Bugs

16 bugs identified so far, independently verified via Opus 4.6 diagnostic runs against pfSense CE 2.8.1 + REST API v2.7.1. All appear to be upstream pfSense issues rather than generator bugs, though we may be wrong — if you hit something new, use `pfsense_report_issue` to let us know.

## Summary

| Category | Count |
|----------|-------|
| PUT/Replace failures | 7 |
| HAProxy singular operations | 6 |
| Other | 3 |
| **Total** | **16** |

## PUT/Replace Failures (7)

Package apply hooks reference PHP functions not loaded in REST API context, plus other PUT-specific issues.

| # | Tool | Error | Root Cause |
|---|------|-------|-----------|
| 1 | `replace_services_free_radius_clients` | 500: undefined `freeradius_clients_resync()` | PHP function only available in FreeRADIUS package context, not REST API |
| 2 | `replace_services_free_radius_interfaces` | 500: undefined `freeradius_settings_resync()` | Same — package apply hook not loaded |
| 3 | `replace_services_free_radius_users` | 500: undefined `freeradius_users_resync()` | Same — package apply hook not loaded |
| 4 | `replace_services_service_watchdog` | 500: undefined `servicewatchdog_cron_job()` | Same — package apply hook not loaded |
| 5 | `replace_services_ntp_settings` | 500: null `config_path` | NTP model's config path resolves to null during PUT |
| 6 | `replace_services_bind_access_lists` | 500: roundtrip invariant violation | GET response format doesn't match PUT request schema |
| 7 | `replace_user_groups` | `FIELD_MUST_BE_UNIQUE` | PUT validates uniqueness before clearing existing items |

## HAProxy Singular Operations (6)

`get_config_path()` calls `get_parent_model()` which fails for dns_resolver and email_mailer sub-resources. LIST, CREATE, and bulk DELETE work fine for both.

| # | Tool | Operation |
|---|------|-----------|
| 8 | `get_services_haproxy_dns_resolver` | GET singular |
| 9 | `update_services_haproxy_dns_resolver` | PATCH singular |
| 10 | `delete_services_haproxy_dns_resolver` | DELETE singular |
| 11 | `get_services_haproxy_email_mailer` | GET singular |
| 12 | `update_services_haproxy_email_mailer` | PATCH singular |
| 13 | `delete_services_haproxy_email_mailer` | DELETE singular |

All 6 return: `500 MODEL_CANNOT_GET_CONFIG_PATH_WITHOUT_PARENT_MODEL`

## Other (3)

| # | Tool | Error | Root Cause |
|---|------|-------|-----------|
| 14 | `update_firewall_traffic_shaper_limiter_queue` | 500: `ecn` references non-existent `sched` field | Limiter queue model inherits `ecn` condition from parent limiter, but `sched` only exists on parent |
| 15 | `update_services_free_radius_user` | PATCH requires `password` even when unchanged | API validates ALL required fields on PATCH, not just submitted ones |
| 16 | `update_system_certificate_revocation_list` | CRL fields immutable after creation | PATCH endpoint exists but rejects changes (fields not marked readOnly in spec) |

## Generator Error History

Prior to generator fixes, Opus 4.6 had 15 first-attempt errors across 670 tested tools. 12 were traced to generator issues and fixed:

- 8 conditional required field downgrades (detect "only available when" in descriptions)
- 2 BasicAuth endpoint warnings (auth/key and auth/jwt flagged in docstrings)
- 2 docstring improvements (PF table names, IPsec hash enum prefix)

After fixes, the Opus diagnostic run showed no remaining generator or spec issues — the only failures observed were the 16 upstream bugs above. Testing was thorough but not exhaustive; edge cases may exist that our test suite didn't cover.
