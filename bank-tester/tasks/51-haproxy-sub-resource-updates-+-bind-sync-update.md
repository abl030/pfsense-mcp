## Task 51: HAProxy Sub-Resource Updates + BIND Sync Update

**task_id**: 51-haproxy-sub-resource-updates-+-bind-sync-update

**Objective**: Exercise all tools in the services/haproxy subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (42):
- `pfsense_create_services_haproxy_backend`
- `pfsense_delete_services_haproxy_backend`
- `pfsense_create_services_haproxy_backend_acl`
- `pfsense_delete_services_haproxy_backend_acl`
- `pfsense_create_services_haproxy_backend_action`
- `pfsense_list_services_haproxy_backend_actions`
- `pfsense_get_services_haproxy_backend_action`
- `pfsense_update_services_haproxy_backend_action`
- `pfsense_delete_services_haproxy_backend_action`
- `pfsense_create_services_haproxy_backend_error_file`
- `pfsense_get_services_haproxy_backend_error_file`
- `pfsense_update_services_haproxy_backend_error_file`
- `pfsense_delete_services_haproxy_backend_error_file`
- `pfsense_list_services_haproxy_backend_error_files`
- `pfsense_create_services_haproxy_frontend`
- `pfsense_delete_services_haproxy_frontend`
- `pfsense_create_services_haproxy_frontend_acl`
- `pfsense_delete_services_haproxy_frontend_acl`
- `pfsense_create_services_haproxy_frontend_action`
- `pfsense_list_services_haproxy_frontend_actions`
- `pfsense_get_services_haproxy_frontend_action`
- `pfsense_update_services_haproxy_frontend_action`
- `pfsense_delete_services_haproxy_frontend_action`
- `pfsense_create_services_haproxy_frontend_address`
- `pfsense_list_services_haproxy_frontend_addresses`
- `pfsense_get_services_haproxy_frontend_address`
- `pfsense_update_services_haproxy_frontend_address`
- `pfsense_delete_services_haproxy_frontend_address`
- `pfsense_create_services_haproxy_frontend_certificate`
- `pfsense_list_services_haproxy_frontend_certificates`
- `pfsense_get_services_haproxy_frontend_certificate`
- `pfsense_update_services_haproxy_frontend_certificate`
- `pfsense_delete_services_haproxy_frontend_certificate`
- `pfsense_get_services_haproxy_apply_status`
- `pfsense_services_haproxy_apply`
- `pfsense_get_services_bind_settings`
- `pfsense_update_services_bind_settings`
- `pfsense_create_services_bind_sync_remote_host`
- `pfsense_list_services_bind_sync_remote_hosts`
- `pfsense_get_services_bind_sync_remote_host`
- `pfsense_update_services_bind_sync_remote_host`
- `pfsense_delete_services_bind_sync_remote_host`

**Steps**:
1. **Create** using `pfsense_create_services_haproxy_backend` with `confirm=True`:
    - `name`: `bt_sys51_be`
    - `agent_port`: `0`
    - `persist_cookie_name`: `SRVID`
2. **Create** using `pfsense_create_services_haproxy_backend_acl` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `name`: `bt_sys51_bacl`
    - `expression`: `host_starts_with`
    - `value`: `test.example.com`
3. **Create** using `pfsense_create_services_haproxy_backend_action` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `action`: `http-request_lua`
    - `lua_function`: `test_func`
    - `acl`: `bt_sys51_bacl`
4. **List** using `pfsense_list_services_haproxy_backend_actions` — verify the created resource appears
5. **Get** using `pfsense_get_services_haproxy_backend_action` with the ID from the create response
6. **Update** using `pfsense_update_services_haproxy_backend_action` with `confirm=True` — set `lua_function` to `updated_func`
7. **Get** again using `pfsense_get_services_haproxy_backend_action` — verify `lua_function` was updated
8. **Create** using `pfsense_create_services_haproxy_backend_error_file` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `errorcode`: `503`
    - `errorfile`: `bt_sys51_file`
9. **Get** using `pfsense_get_services_haproxy_backend_error_file` with the ID from the create response
10. **Update** using `pfsense_update_services_haproxy_backend_error_file` with `confirm=True` — set `errorcode` to `502`
11. **Get** again using `pfsense_get_services_haproxy_backend_error_file` — verify `errorcode` was updated
12. **Read** using `pfsense_list_services_haproxy_backend_error_files` (List backend error files (plural))
13. **Create** using `pfsense_create_services_haproxy_frontend` with `confirm=True`:
    - `name`: `bt_sys51_fe`
    - `type_`: `http`
    - `descr`: `Sprint 2 frontend`
14. **Create** using `pfsense_create_services_haproxy_frontend_acl` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `name`: `bt_sys51_facl`
    - `expression`: `host_starts_with`
    - `value`: `test.example.com`
15. **Create** using `pfsense_create_services_haproxy_frontend_action` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `action`: `http-request_lua`
    - `name`: `bt_sys51_fact`
    - `acl`: `bt_sys51_facl`
16. **List** using `pfsense_list_services_haproxy_frontend_actions` — verify the created resource appears
17. **Get** using `pfsense_get_services_haproxy_frontend_action` with the ID from the create response
18. **Update** using `pfsense_update_services_haproxy_frontend_action` with `confirm=True` — set `name` to `bt_sys51_fact_upd`
19. **Get** again using `pfsense_get_services_haproxy_frontend_action` — verify `name` was updated
20. **Create** using `pfsense_create_services_haproxy_frontend_address` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `extaddr`: `custom`
    - `extaddr_custom`: `10.99.99.81:80`
21. **List** using `pfsense_list_services_haproxy_frontend_addresses` — verify the created resource appears
22. **Get** using `pfsense_get_services_haproxy_frontend_address` with the ID from the create response
23. **Update** using `pfsense_update_services_haproxy_frontend_address` with `confirm=True` — set `extaddr_custom` to `10.99.99.81:8080`
24. **Get** again using `pfsense_get_services_haproxy_frontend_address` — verify `extaddr_custom` was updated
25. **Create** using `pfsense_create_services_haproxy_frontend_certificate` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
(no parameters needed)
26. **List** using `pfsense_list_services_haproxy_frontend_certificates` — verify the created resource appears
27. **Get** using `pfsense_get_services_haproxy_frontend_certificate` with the ID from the create response
28. **Update** using `pfsense_update_services_haproxy_frontend_certificate` with `confirm=True` — set `ssl_certificate` to ``
29. **Get** again using `pfsense_get_services_haproxy_frontend_certificate` — verify `ssl_certificate` was updated
30. **Check apply status** using `pfsense_get_services_haproxy_apply_status`
31. **Apply changes** using `pfsense_services_haproxy_apply` with `confirm=True`
32. **Get settings** using `pfsense_get_services_bind_settings` — note current value of `enable_bind`
33. **Update settings** using `pfsense_update_services_bind_settings` with `confirm=True` — set `enable_bind` to `True`
34. **Get settings** again using `pfsense_get_services_bind_settings` — verify `enable_bind` was updated
35. **Create** using `pfsense_create_services_bind_sync_remote_host` with `confirm=True`:
    - `syncdestinenable`: `False`
    - `syncdesttimeout`: `120`
    - `syncprotocol`: `http`
    - `ipaddress`: `10.99.99.60`
    - `syncport`: `80`
    - `username`: `admin`
    - `password`: `pfsense`
36. **List** using `pfsense_list_services_bind_sync_remote_hosts` — verify the created resource appears
37. **Get** using `pfsense_get_services_bind_sync_remote_host` with the ID from the create response
38. **Update** using `pfsense_update_services_bind_sync_remote_host` with `confirm=True` — set `syncdesttimeout` to `180`
39. **Get** again using `pfsense_get_services_bind_sync_remote_host` — verify `syncdesttimeout` was updated

**Important notes**:
Tests HAProxy sub-resource PATCH operations (backend action/error_file, frontend action/address/certificate).
Also tests BIND sync remote host update.
Setup: create backend/frontend with ACLs, then CRUD sub-resources.
Cleanup: sub-resources → frontend → backend.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_services_bind_sync_remote_host` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_haproxy_frontend_certificate` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_haproxy_frontend_address` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_haproxy_frontend_action` with `confirm=True` (ID from create step)
- Delete setup resource at `/api/v2/services/haproxy/frontend/acl` using `pfsense_delete_services_haproxy_frontend_acl` with `confirm=True`
- Delete setup resource at `/api/v2/services/haproxy/frontend` using `pfsense_delete_services_haproxy_frontend` with `confirm=True`
- Delete using `pfsense_delete_services_haproxy_backend_error_file` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_haproxy_backend_action` with `confirm=True` (ID from create step)
- Delete setup resource at `/api/v2/services/haproxy/backend/acl` using `pfsense_delete_services_haproxy_backend_acl` with `confirm=True`
- Delete setup resource at `/api/v2/services/haproxy/backend` using `pfsense_delete_services_haproxy_backend` with `confirm=True`

**Expected outcome**: All 42 tools exercised successfully.
