## Task 18: DNS Resolver — Settings, Access Lists, Host Overrides

**task_id**: 18-dns-resolver--settings-access-lists-host-overrides

**Objective**: Exercise all tools in the services/dns_resolver subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (24):
- `pfsense_get_services_dns_resolver_settings`
- `pfsense_update_services_dns_resolver_settings`
- `pfsense_create_services_dns_resolver_access_list`
- `pfsense_get_services_dns_resolver_access_list_network`
- `pfsense_get_services_dns_resolver_access_list`
- `pfsense_update_services_dns_resolver_access_list`
- `pfsense_delete_services_dns_resolver_access_list`
- `pfsense_create_services_dns_resolver_access_list_network`
- `pfsense_delete_services_dns_resolver_access_list_network`
- `pfsense_create_services_dns_resolver_host_override`
- `pfsense_list_services_dns_resolver_host_overrides`
- `pfsense_get_services_dns_resolver_host_override`
- `pfsense_update_services_dns_resolver_host_override`
- `pfsense_delete_services_dns_resolver_host_override`
- `pfsense_create_services_dns_resolver_host_override_alias`
- `pfsense_get_services_dns_resolver_host_override_alias`
- `pfsense_delete_services_dns_resolver_host_override_alias`
- `pfsense_create_services_dns_resolver_domain_override`
- `pfsense_list_services_dns_resolver_domain_overrides`
- `pfsense_get_services_dns_resolver_domain_override`
- `pfsense_update_services_dns_resolver_domain_override`
- `pfsense_delete_services_dns_resolver_domain_override`
- `pfsense_get_services_dns_resolver_apply_status`
- `pfsense_services_dns_resolver_apply`

**Steps**:
1. **Get settings** using `pfsense_get_services_dns_resolver_settings` — note current value of `port`
2. **Update settings** using `pfsense_update_services_dns_resolver_settings` with `confirm=True` — set `port` to `'5353'`
3. **Get settings** again using `pfsense_get_services_dns_resolver_settings` — verify `port` was updated
4. **Create** using `pfsense_create_services_dns_resolver_access_list` with `confirm=True`:
    - `action`: `allow`
    - `name`: `bt_sys18_dnsacl`
    - `networks`: `[]`
5. **List** using `pfsense_get_services_dns_resolver_access_list_network` — verify the created resource appears
6. **Get** using `pfsense_get_services_dns_resolver_access_list` with the ID from the create response
7. **Update** using `pfsense_update_services_dns_resolver_access_list` with `confirm=True` — set `name` to `bt_sys18_dnsacl_upd`
8. **Get** again using `pfsense_get_services_dns_resolver_access_list` — verify `name` was updated
9. **Create** using `pfsense_create_services_dns_resolver_access_list_network` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `network`: `10.1.0.0`
    - `mask`: `16`
10. **Get** using `pfsense_get_services_dns_resolver_access_list_network` with the ID from the create response
11. **Create** using `pfsense_create_services_dns_resolver_host_override` with `confirm=True`:
    - `host`: `bt-sys18-ho`
    - `domain`: `example.com`
    - `ip`: `['10.99.99.2']`
    - `aliases`: `[]`
    - `descr`: `Bank tester host override`
12. **List** using `pfsense_list_services_dns_resolver_host_overrides` — verify the created resource appears
13. **Get** using `pfsense_get_services_dns_resolver_host_override` with the ID from the create response
14. **Update** using `pfsense_update_services_dns_resolver_host_override` with `confirm=True` — set `descr` to `Updated override`
15. **Get** again using `pfsense_get_services_dns_resolver_host_override` — verify `descr` was updated
16. **Create** using `pfsense_create_services_dns_resolver_host_override_alias` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `host`: `testalias`
    - `domain`: `alias.example.com`
17. **Get** using `pfsense_get_services_dns_resolver_host_override_alias` with the ID from the create response
18. **Create** using `pfsense_create_services_dns_resolver_domain_override` with `confirm=True`:
    - `domain`: `bt-sys18.example.com`
    - `ip`: `10.99.99.3`
    - `descr`: `Bank tester domain override`
19. **List** using `pfsense_list_services_dns_resolver_domain_overrides` — verify the created resource appears
20. **Get** using `pfsense_get_services_dns_resolver_domain_override` with the ID from the create response
21. **Update** using `pfsense_update_services_dns_resolver_domain_override` with `confirm=True` — set `descr` to `Updated domain override`
22. **Get** again using `pfsense_get_services_dns_resolver_domain_override` — verify `descr` was updated
23. **Check apply status** using `pfsense_get_services_dns_resolver_apply_status`
24. **Apply changes** using `pfsense_services_dns_resolver_apply` with `confirm=True`

**Important notes**:
Access list network is sub-resource of access_list.
Host override alias is sub-resource of host_override.
Apply dns_resolver after mutations.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_services_dns_resolver_domain_override` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_dns_resolver_host_override_alias` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_dns_resolver_host_override` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_dns_resolver_access_list_network` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_dns_resolver_access_list` with `confirm=True` (ID from create step)

**Expected outcome**: All 24 tools exercised successfully.
