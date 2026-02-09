## Task 71: HAProxy Settings 500 Bug Validation

**task_id**: 71-haproxy-settings-500-validation

**Objective**: Validate whether the HAProxy settings dns_resolver and email_mailer endpoints still return 500 errors. These were previously reported as broken with "parent Model not constructed" in pfSense REST API v2.4.3 and assumed broken in v2.7.1. This task tests them against the current v2.8.1 + REST API v2.7.1 environment.

**Tools to exercise** (12):
- `pfsense_get_services_ha_proxy_settings_dns_resolver`
- `pfsense_list_services_ha_proxy_settings_dns_resolvers`
- `pfsense_create_services_ha_proxy_settings_dns_resolver`
- `pfsense_update_services_ha_proxy_settings_dns_resolver`
- `pfsense_delete_services_ha_proxy_settings_dns_resolver`
- `pfsense_delete_services_ha_proxy_settings_dns_resolvers`
- `pfsense_get_services_ha_proxy_settings_email_mailer`
- `pfsense_list_services_ha_proxy_settings_email_mailers`
- `pfsense_create_services_ha_proxy_settings_email_mailer`
- `pfsense_update_services_ha_proxy_settings_email_mailer`
- `pfsense_delete_services_ha_proxy_settings_email_mailer`
- `pfsense_delete_services_ha_proxy_settings_email_mailers`

---

### Instructions

For each endpoint group, attempt every operation and record the result. If an operation returns a 500 error, that's expected — record it and move on. If it works, that's great — it means the bug is fixed.

### Part 1: DNS Resolver Settings

1. **List DNS resolvers**: Call `pfsense_list_services_ha_proxy_settings_dns_resolvers`. Record result (success or 500 error).

2. **Get a DNS resolver**: If the list returned items, call `pfsense_get_services_ha_proxy_settings_dns_resolver` with the first item's `id`. If the list was empty or failed, try with `id=0`.

3. **Create a DNS resolver**: Call `pfsense_create_services_ha_proxy_settings_dns_resolver` with reasonable test values (look at the tool's docstring for parameter names). Use `name` or `descr` prefixed with `bt_s4_`. Set `confirm=true`.

4. **Update the DNS resolver**: If create succeeded, call `pfsense_update_services_ha_proxy_settings_dns_resolver` with the created id and a changed field. Set `confirm=true`.

5. **Delete the DNS resolver (singular)**: If create succeeded, call `pfsense_delete_services_ha_proxy_settings_dns_resolver` with the id. Set `confirm=true`.

6. **Delete DNS resolvers (bulk)**: Call `pfsense_delete_services_ha_proxy_settings_dns_resolvers` with `query={"name": "bt_s4_"}` and `confirm=true`. This exercises the bulk delete even if nothing matches.

### Part 2: Email Mailer Settings

7. **List email mailers**: Call `pfsense_list_services_ha_proxy_settings_email_mailers`. Record result.

8. **Get an email mailer**: If list returned items, get the first. Otherwise try `id=0`.

9. **Create an email mailer**: Call `pfsense_create_services_ha_proxy_settings_email_mailer` with reasonable test values. Use `name` or `descr` prefixed with `bt_s4_`. Set `confirm=true`.

10. **Update the email mailer**: If create succeeded, update a field. Set `confirm=true`.

11. **Delete the email mailer (singular)**: If create succeeded, delete it. Set `confirm=true`.

12. **Delete email mailers (bulk)**: Call `pfsense_delete_services_ha_proxy_settings_email_mailers` with `query={"name": "bt_s4_"}` and `confirm=true`.

### Part 3: Apply

After any successful mutations, call `pfsense_apply_haproxy` to apply changes.

### Reporting

For each of the 12 tools, record whether it returned:
- **Success** (any 2xx response) — the bug is fixed
- **500 error** ("parent Model not constructed" or similar) — the bug persists
- **Other error** — new information

This is a diagnostic task. Even if all 12 tools fail with 500, the task is "success" as long as all tools were invoked and results documented.
