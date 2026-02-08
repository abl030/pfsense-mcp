## Task 24: BIND DNS — Access List, View, Zone, Record, Sync, Settings

**task_id**: 24-bind-dns--access-list-view-zone-record-sync-settin

**Objective**: Exercise all tools in the services/bind subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (26):
- `pfsense_get_services_bind_settings`
- `pfsense_update_services_bind_settings`
- `pfsense_create_services_bind_access_list`
- `pfsense_list_services_bind_access_lists`
- `pfsense_get_services_bind_access_list`
- `pfsense_update_services_bind_access_list`
- `pfsense_delete_services_bind_access_list`
- `pfsense_create_services_bind_access_list_entry`
- `pfsense_get_services_bind_access_list_entry`
- `pfsense_update_services_bind_access_list_entry`
- `pfsense_delete_services_bind_access_list_entry`
- `pfsense_create_services_bind_view`
- `pfsense_list_services_bind_views`
- `pfsense_get_services_bind_view`
- `pfsense_update_services_bind_view`
- `pfsense_delete_services_bind_view`
- `pfsense_create_services_bind_zone`
- `pfsense_list_services_bind_zones`
- `pfsense_get_services_bind_zone`
- `pfsense_update_services_bind_zone`
- `pfsense_delete_services_bind_zone`
- `pfsense_create_services_bind_zone_record`
- `pfsense_get_services_bind_zone_record`
- `pfsense_update_services_bind_zone_record`
- `pfsense_delete_services_bind_zone_record`
- `pfsense_post_/api/v2/services/bind/sync`

**Steps**:
1. **Get settings** using `pfsense_get_services_bind_settings` — note current value of `enable_bind`
2. **Update settings** using `pfsense_update_services_bind_settings` with `confirm=True` — set `enable_bind` to `True`
3. **Get settings** again using `pfsense_get_services_bind_settings` — verify `enable_bind` was updated
4. **Create** using `pfsense_create_services_bind_access_list` with `confirm=True`:
    - `entries`: `[{'value': '10.0.0.0/8', 'description': 'test entry'}]`
    - `name`: `bt_sys24_bacl`
5. **List** using `pfsense_list_services_bind_access_lists` — verify the created resource appears
6. **Get** using `pfsense_get_services_bind_access_list` with the ID from the create response
7. **Update** using `pfsense_update_services_bind_access_list` with `confirm=True` — set `name` to `bt_sys24_bacl_upd`
8. **Get** again using `pfsense_get_services_bind_access_list` — verify `name` was updated
9. **Create** using `pfsense_create_services_bind_access_list_entry` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `value`: `10.1.0.0/16`
10. **Get** using `pfsense_get_services_bind_access_list_entry` with the ID from the create response
11. **Update** using `pfsense_update_services_bind_access_list_entry` with `confirm=True` — set `value` to `10.2.0.0/16`
12. **Get** again using `pfsense_get_services_bind_access_list_entry` — verify `value` was updated
13. **Create** using `pfsense_create_services_bind_view` with `confirm=True`:
    - `name`: `bt_sys24_view`
    - `descr`: `Bank tester view`
14. **List** using `pfsense_list_services_bind_views` — verify the created resource appears
15. **Get** using `pfsense_get_services_bind_view` with the ID from the create response
16. **Update** using `pfsense_update_services_bind_view` with `confirm=True` — set `descr` to `Updated view`
17. **Get** again using `pfsense_get_services_bind_view` — verify `descr` was updated
18. **Create** using `pfsense_create_services_bind_zone` with `confirm=True`:
    - `name`: `bt-sys24.example.com`
    - `nameserver`: `ns1.example.com`
    - `mail`: `admin.example.com`
    - `serial`: `2024010101`
    - `forwarders`: `[]`
    - `baseip`: `10.99.99.0`
19. **List** using `pfsense_list_services_bind_zones` — verify the created resource appears
20. **Get** using `pfsense_get_services_bind_zone` with the ID from the create response
21. **Update** using `pfsense_update_services_bind_zone` with `confirm=True` — set `mail` to `admin2.example.com`
22. **Get** again using `pfsense_get_services_bind_zone` — verify `mail` was updated
23. **Create** using `pfsense_create_services_bind_zone_record` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `name`: `testrec`
    - `type_`: `A`
    - `rdata`: `10.99.99.1`
    - `priority`: `0`
24. **Get** using `pfsense_get_services_bind_zone_record` with the ID from the create response
25. **Update** using `pfsense_update_services_bind_zone_record` with `confirm=True` — set `rdata` to `10.99.99.2`
26. **Get** again using `pfsense_get_services_bind_zone_record` — verify `rdata` was updated
27. **Execute** `pfsense_post_/api/v2/services/bind/sync` with `confirm=True`:
(no parameters needed)

**Important notes**:
Enable BIND in settings first. Access list entry and zone record are sub-resources.
Cleanup: record → zone, entry → access_list, view.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_services_bind_zone_record` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_bind_zone` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_bind_view` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_bind_access_list_entry` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_bind_access_list` with `confirm=True` (ID from create step)

**Expected outcome**: All 26 tools exercised successfully.
