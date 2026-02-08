## Task 30: REST API — Settings, Access List, Version

**task_id**: 30-rest-api--settings-access-list-version

**Objective**: Exercise all tools in the system/restapi subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (7):
- `pfsense_get_system_restapi_settings`
- `pfsense_update_system_restapi_settings`
- `pfsense_create_system_restapi_access_list_entry`
- `pfsense_get_system_restapi_access_list_entry`
- `pfsense_update_system_restapi_access_list_entry`
- `pfsense_delete_system_restapi_access_list_entry`
- `pfsense_get_system_restapi_version`

**Steps**:
1. **Get settings** using `pfsense_get_system_restapi_settings` — note current value of `ha_sync_hosts`
2. **Update settings** using `pfsense_update_system_restapi_settings` with `confirm=True` — set `ha_sync_hosts` to `[]`
3. **Get settings** again using `pfsense_get_system_restapi_settings` — verify `ha_sync_hosts` was updated
4. **Create** using `pfsense_create_system_restapi_access_list_entry` with `confirm=True`:
    - `type_`: `allow`
    - `network`: `10.0.0.0/8`
    - `descr`: `bt_sys30_acl`
5. **Get** using `pfsense_get_system_restapi_access_list_entry` with the ID from the create response
6. **Update** using `pfsense_update_system_restapi_access_list_entry` with `confirm=True` — set `descr` to `Updated ACL entry`
7. **Get** again using `pfsense_get_system_restapi_access_list_entry` — verify `descr` was updated
8. **Read** using `pfsense_get_system_restapi_version`

**Important notes**:
Be careful with access list — don't lock yourself out.
Version PATCH is destructive (skipped).

**Skipped endpoints**:
- `/api/v2/system/restapi/version` — PATCH triggers API version change (destructive)

**Cleanup** (reverse order):
- Delete using `pfsense_delete_system_restapi_access_list_entry` with `confirm=True` (ID from create step)

**Expected outcome**: All 7 tools exercised successfully.
