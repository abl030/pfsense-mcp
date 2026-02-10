## Task 21: HAProxy Core — Settings, Files, Backend CRUD, Apply

**task_id**: 21-haproxy-core--settings-files-backend-crud-apply

**Objective**: Exercise all tools in the services/haproxy subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (14):
- `pfsense_get_services_haproxy_settings`
- `pfsense_update_services_haproxy_settings`
- `pfsense_create_services_haproxy_file`
- `pfsense_list_services_haproxy_files`
- `pfsense_get_services_haproxy_file`
- `pfsense_update_services_haproxy_file`
- `pfsense_delete_services_haproxy_file`
- `pfsense_create_services_haproxy_backend`
- `pfsense_list_services_haproxy_backends`
- `pfsense_get_services_haproxy_backend`
- `pfsense_update_services_haproxy_backend`
- `pfsense_delete_services_haproxy_backend`
- `pfsense_get_services_haproxy_apply_status`
- `pfsense_services_haproxy_apply`

**Steps**:
1. **Get settings** using `pfsense_get_services_haproxy_settings` — note current value of `maxconn`
2. **Update settings** using `pfsense_update_services_haproxy_settings` with `confirm=True` — set `maxconn` to `100`
3. **Get settings** again using `pfsense_get_services_haproxy_settings` — verify `maxconn` was updated
4. **Create** using `pfsense_create_services_haproxy_file` with `confirm=True`:
    - `name`: `bt_sys21_file`
    - `content`: `PCFET0NUWVBFIGh0bWw+`
5. **List** using `pfsense_list_services_haproxy_files` — verify the created resource appears
6. **Get** using `pfsense_get_services_haproxy_file` with the ID from the create response
7. **Update** using `pfsense_update_services_haproxy_file` with `confirm=True` — set `content` to `VXBkYXRlZA==`
8. **Get** again using `pfsense_get_services_haproxy_file` — verify `content` was updated
9. **Create** using `pfsense_create_services_haproxy_backend` with `confirm=True`:
    - `name`: `bt_sys21_be`
    - `agent_port`: `0`
    - `persist_cookie_name`: `SRVID`
10. **List** using `pfsense_list_services_haproxy_backends` — verify the created resource appears
11. **Get** using `pfsense_get_services_haproxy_backend` with the ID from the create response
12. **Update** using `pfsense_update_services_haproxy_backend` with `confirm=True` — set `advanced` to `# updated by bank tester`
13. **Get** again using `pfsense_get_services_haproxy_backend` — verify `advanced` was updated
14. **Check apply status** using `pfsense_get_services_haproxy_apply_status`
15. **Apply changes** using `pfsense_services_haproxy_apply` with `confirm=True`

**Important notes**:
Apply haproxy after mutations.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_services_haproxy_backend` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_haproxy_file` with `confirm=True` (ID from create step)

**Expected outcome**: All 14 tools exercised successfully.
