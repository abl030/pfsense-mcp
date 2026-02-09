## Task 57: Singular Deletes + Misc Gaps

**task_id**: 57-singular-deletes-+-misc-gaps

**Objective**: Exercise all tools in the diagnostics subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (9):
- `pfsense_post_/api/v2/diagnostics/arp_table/entry`
- `pfsense_post_/api/v2/diagnostics/config_history/revision`
- `pfsense_post_/api/v2/diagnostics/table`
- `pfsense_post_/api/v2/firewall/state`
- `pfsense_create_system_restapi_access_list_entry`
- `pfsense_get_system_restapi_access_list_entry`
- `pfsense_update_system_restapi_access_list_entry`
- `pfsense_delete_system_restapi_access_list_entry`
- `pfsense_create_auth_key`

**Steps**:
1. **Execute** `pfsense_post_/api/v2/diagnostics/arp_table/entry` with `confirm=True` (List ARP table first, pick an entry, DELETE it by ID.):
(no parameters needed)
2. **Execute** `pfsense_post_/api/v2/diagnostics/config_history/revision` with `confirm=True` (List config history revisions, DELETE one by ID.):
(no parameters needed)
3. **Execute** `pfsense_post_/api/v2/diagnostics/table` with `confirm=True` (List PF tables, pick 'virusprot', DELETE entries from it.):
(no parameters needed)
4. **Execute** `pfsense_post_/api/v2/firewall/state` with `confirm=True` (List firewall states, DELETE one by ID (if any exist).):
(no parameters needed)
5. **Create** using `pfsense_create_system_restapi_access_list_entry` with `confirm=True`:
    - `type_`: `allow`
    - `network`: `172.16.0.0/12`
    - `descr`: `bt_sys57_acl_del`
6. **Get** using `pfsense_get_system_restapi_access_list_entry` with the ID from the create response
7. **Update** using `pfsense_update_system_restapi_access_list_entry` with `confirm=True` — set `descr` to `Updated for delete test`
8. **Get** again using `pfsense_get_system_restapi_access_list_entry` — verify `descr` was updated
9. **Execute** `pfsense_create_auth_key` with `confirm=True` (Create an API key via command_prompt (BasicAuth workaround), then delete it via DELETE endpoint.):
(no parameters needed)

**Important notes**:
Singular delete operations for diagnostic/status resources.
These don't follow standard CRUD — they need existing data to delete.
ARP entries: list table, pick entry, delete by ID.
Config history: list revisions, delete one revision by ID.
PF tables: list tables, pick 'virusprot', delete entries.
Firewall states: list states, delete one (if any exist).
REST API ACL: create entry, then delete it.
Auth key: use diagnostics/command_prompt to create a key via PHP, then delete via API.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_system_restapi_access_list_entry` with `confirm=True` (ID from create step)

**Expected outcome**: All 9 tools exercised successfully.
