## Task 20: DHCP Server — Address Pool, Static Mapping, Custom Options

**task_id**: 20-dhcp-server--address-pool-static-mapping-custom-op

**Objective**: Exercise all tools in the services/dhcp_server subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (18):
- `pfsense_create_services_dhcp_server_address_pool`
- `pfsense_list_services_dhcp_server_address_pools`
- `pfsense_get_services_dhcp_server_address_pool`
- `pfsense_update_services_dhcp_server_address_pool`
- `pfsense_delete_services_dhcp_server_address_pool`
- `pfsense_create_services_dhcp_server_static_mapping`
- `pfsense_list_services_dhcp_server_static_mappings`
- `pfsense_get_services_dhcp_server_static_mapping`
- `pfsense_update_services_dhcp_server_static_mapping`
- `pfsense_delete_services_dhcp_server_static_mapping`
- `pfsense_create_services_dhcp_server_custom_option`
- `pfsense_list_services_dhcp_server_custom_options`
- `pfsense_get_services_dhcp_server_custom_option`
- `pfsense_update_services_dhcp_server_custom_option`
- `pfsense_delete_services_dhcp_server_custom_option`
- `pfsense_update_services_dhcp_server_backend`
- `pfsense_get_services_dhcp_server_apply_status`
- `pfsense_services_dhcp_server_apply`

**Steps**:
1. **Create** using `pfsense_create_services_dhcp_server_address_pool` with `confirm=True` (use `parent_id="lan"`):
    - `range_from`: `192.168.1.201`
    - `range_to`: `192.168.1.210`
2. **List** using `pfsense_list_services_dhcp_server_address_pools` — verify the created resource appears
3. **Get** using `pfsense_get_services_dhcp_server_address_pool` with the ID from the create response
4. **Update** using `pfsense_update_services_dhcp_server_address_pool` with `confirm=True` — set `range_to` to `192.168.1.215`
5. **Get** again using `pfsense_get_services_dhcp_server_address_pool` — verify `range_to` was updated
6. **Create** using `pfsense_create_services_dhcp_server_static_mapping` with `confirm=True` (use `parent_id="lan"`):
    - `mac`: `00:11:22:33:44:55`
    - `ipaddr`: `192.168.1.250`
    - `descr`: `bt_sys20_static`
7. **List** using `pfsense_list_services_dhcp_server_static_mappings` — verify the created resource appears
8. **Get** using `pfsense_get_services_dhcp_server_static_mapping` with the ID from the create response
9. **Update** using `pfsense_update_services_dhcp_server_static_mapping` with `confirm=True` — set `descr` to `Updated static mapping`
10. **Get** again using `pfsense_get_services_dhcp_server_static_mapping` — verify `descr` was updated
11. **Create** using `pfsense_create_services_dhcp_server_custom_option` with `confirm=True` (use `parent_id="lan"`):
    - `number`: `252`
    - `type_`: `text`
    - `value`: `http://wpad.example.com/wpad.dat`
    - `descr`: `bt_sys20_opt`
12. **List** using `pfsense_list_services_dhcp_server_custom_options` — verify the created resource appears
13. **Get** using `pfsense_get_services_dhcp_server_custom_option` with the ID from the create response
14. **Update** using `pfsense_update_services_dhcp_server_custom_option` with `confirm=True` — set `descr` to `Updated custom option`
15. **Get** again using `pfsense_get_services_dhcp_server_custom_option` — verify `descr` was updated
16. **Update settings** using `pfsense_update_services_dhcp_server_backend` with `confirm=True` — set `dhcpbackend` to `'kea'`
17. **Restore** using `pfsense_update_services_dhcp_server_backend` with `confirm=True` — set `dhcpbackend` back to `'isc'`
18. **Check apply status** using `pfsense_get_services_dhcp_server_apply_status`
19. **Apply changes** using `pfsense_services_dhcp_server_apply` with `confirm=True`

**Important notes**:
All DHCP sub-resources use static parent_id="lan" (the LAN interface name in pfSense).
Apply dhcp_server after mutations. Restore backend to "isc" after testing.

**Skipped endpoints**:
- `/api/v2/services/dhcp_server` — Per-interface singleton — POST not supported by design

**Cleanup** (reverse order):
- Delete using `pfsense_delete_services_dhcp_server_custom_option` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_dhcp_server_static_mapping` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_dhcp_server_address_pool` with `confirm=True` (ID from create step)

**Expected outcome**: All 18 tools exercised successfully.
