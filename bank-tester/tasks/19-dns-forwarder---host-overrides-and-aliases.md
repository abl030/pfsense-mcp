## Task 19: DNS Forwarder — Host Overrides & Aliases

**task_id**: 19-dns-forwarder--host-overrides--aliases

**Objective**: Exercise all tools in the services/dns_forwarder subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (10):
- `pfsense_create_services_dns_forwarder_host_override`
- `pfsense_list_services_dns_forwarder_host_override_aliases`
- `pfsense_get_services_dns_forwarder_host_override`
- `pfsense_update_services_dns_forwarder_host_override`
- `pfsense_delete_services_dns_forwarder_host_override`
- `pfsense_create_services_dns_forwarder_host_override_alias`
- `pfsense_get_services_dns_forwarder_host_override_alias`
- `pfsense_delete_services_dns_forwarder_host_override_alias`
- `pfsense_get_services_dns_forwarder_apply_status`
- `pfsense_services_dns_forwarder_apply`

**Steps**:
1. **Create** using `pfsense_create_services_dns_forwarder_host_override` with `confirm=True`:
    - `domain`: `example.com`
    - `host`: `bt-sys19-ho`
    - `ip`: `10.99.99.2`
    - `aliases`: `[]`
    - `descr`: `Bank tester forwarder host override`
2. **List** using `pfsense_list_services_dns_forwarder_host_override_aliases` — verify the created resource appears
3. **Get** using `pfsense_get_services_dns_forwarder_host_override` with the ID from the create response
4. **Update** using `pfsense_update_services_dns_forwarder_host_override` with `confirm=True` — set `descr` to `Updated forwarder override`
5. **Get** again using `pfsense_get_services_dns_forwarder_host_override` — verify `descr` was updated
6. **Create** using `pfsense_create_services_dns_forwarder_host_override_alias` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `host`: `testalias`
    - `domain`: `alias.example.com`
7. **List** using `pfsense_list_services_dns_forwarder_host_override_aliases` — verify the created resource appears
8. **Get** using `pfsense_get_services_dns_forwarder_host_override_alias` with the ID from the create response
9. **Check apply status** using `pfsense_get_services_dns_forwarder_apply_status`
10. **Apply changes** using `pfsense_services_dns_forwarder_apply` with `confirm=True`

**Important notes**:
Host override alias is sub-resource of host_override.
Apply dns_forwarder after mutations.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_services_dns_forwarder_host_override_alias` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_dns_forwarder_host_override` with `confirm=True` (ID from create step)

**Expected outcome**: All 10 tools exercised successfully.
