## Task 22: HAProxy Backend Sub-Resources — ACL, Action, Server, Error File

**task_id**: 22-haproxy-backend-sub-resources--acl-action-server-e

**Objective**: Exercise all tools in the services/haproxy/backend subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (21):
- `pfsense_create_services_ha_proxy_backend`
- `pfsense_delete_services_ha_proxy_backend`
- `pfsense_create_services_ha_proxy_backend_acl`
- `pfsense_list_services_ha_proxy_backend_ac_ls`
- `pfsense_get_services_ha_proxy_backend_acl`
- `pfsense_update_services_ha_proxy_backend_acl`
- `pfsense_delete_services_ha_proxy_backend_acl`
- `pfsense_create_services_ha_proxy_backend_server`
- `pfsense_list_services_ha_proxy_backend_servers`
- `pfsense_get_services_ha_proxy_backend_server`
- `pfsense_update_services_ha_proxy_backend_server`
- `pfsense_delete_services_ha_proxy_backend_server`
- `pfsense_create_services_ha_proxy_backend_error_file`
- `pfsense_get_services_ha_proxy_backend_error_file`
- `pfsense_delete_services_ha_proxy_backend_error_file`
- `pfsense_create_services_ha_proxy_backend_action`
- `pfsense_list_services_ha_proxy_backend_actions`
- `pfsense_get_services_ha_proxy_backend_action`
- `pfsense_delete_services_ha_proxy_backend_action`
- `pfsense_get_services_ha_proxy_apply_status`
- `pfsense_services_ha_proxy_apply`

**Steps**:
1. **Create** using `pfsense_create_services_ha_proxy_backend` with `confirm=True`:
    - `name`: `bt_sys22_be`
    - `agent_port`: `0`
    - `persist_cookie_name`: `SRVID`
    - `descr`: `Parent backend for sub-resources`
2. **Create** using `pfsense_create_services_ha_proxy_backend_acl` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `name`: `bt_sys22_bacl`
    - `expression`: `host_starts_with`
    - `value`: `test.example.com`
3. **List** using `pfsense_list_services_ha_proxy_backend_ac_ls` — verify the created resource appears
4. **Get** using `pfsense_get_services_ha_proxy_backend_acl` with the ID from the create response
5. **Update** using `pfsense_update_services_ha_proxy_backend_acl` with `confirm=True` — set `value` to `updated.example.com`
6. **Get** again using `pfsense_get_services_ha_proxy_backend_acl` — verify `value` was updated
7. **Create** using `pfsense_create_services_ha_proxy_backend_server` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `name`: `bt_sys22_bsrv`
    - `address`: `10.99.99.50`
    - `port`: `8080`
8. **List** using `pfsense_list_services_ha_proxy_backend_servers` — verify the created resource appears
9. **Get** using `pfsense_get_services_ha_proxy_backend_server` with the ID from the create response
10. **Update** using `pfsense_update_services_ha_proxy_backend_server` with `confirm=True` — set `address` to `10.99.99.51`
11. **Get** again using `pfsense_get_services_ha_proxy_backend_server` — verify `address` was updated
12. **Create** using `pfsense_create_services_ha_proxy_backend_error_file` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `errorcode`: `503`
    - `errorfile`: `bt_sys22_file`
13. **Get** using `pfsense_get_services_ha_proxy_backend_error_file` with the ID from the create response
14. **Create** using `pfsense_create_services_ha_proxy_backend_action` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `action`: `http-request_lua`
    - `name`: `bt_sys22_bact`
    - `acl`: `bt_sys22_bacl`
15. **List** using `pfsense_list_services_ha_proxy_backend_actions` — verify the created resource appears
16. **Get** using `pfsense_get_services_ha_proxy_backend_action` with the ID from the create response
17. **Check apply status** using `pfsense_get_services_ha_proxy_apply_status`
18. **Apply changes** using `pfsense_services_ha_proxy_apply` with `confirm=True`

**Important notes**:
All sub-resources need parent_id from the backend.
Backend action requires an ACL — create a sibling ACL under the same backend first.
Error file needs a HAProxy file resource created first.
Cleanup sub-resources before backend.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_services_ha_proxy_backend_action` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_ha_proxy_backend_error_file` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_ha_proxy_backend_server` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_ha_proxy_backend_acl` with `confirm=True` (ID from create step)
- Delete setup resource at `/api/v2/services/haproxy/backend` using `pfsense_delete_services_ha_proxy_backend` with `confirm=True`

**Expected outcome**: All 21 tools exercised successfully.
