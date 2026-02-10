## Task 23: HAProxy Frontend & Sub-Resources

**task_id**: 23-haproxy-frontend--sub-resources

**Objective**: Exercise all tools in the services/haproxy/frontend subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (31):
- `pfsense_create_services_haproxy_backend`
- `pfsense_delete_services_haproxy_backend`
- `pfsense_create_services_haproxy_frontend`
- `pfsense_list_services_haproxy_frontends`
- `pfsense_get_services_haproxy_frontend`
- `pfsense_update_services_haproxy_frontend`
- `pfsense_delete_services_haproxy_frontend`
- `pfsense_create_services_haproxy_frontend_acl`
- `pfsense_list_services_haproxy_frontend_acls`
- `pfsense_get_services_haproxy_frontend_acl`
- `pfsense_update_services_haproxy_frontend_acl`
- `pfsense_delete_services_haproxy_frontend_acl`
- `pfsense_create_services_haproxy_frontend_action`
- `pfsense_list_services_haproxy_frontend_actions`
- `pfsense_get_services_haproxy_frontend_action`
- `pfsense_delete_services_haproxy_frontend_action`
- `pfsense_create_services_haproxy_frontend_address`
- `pfsense_list_services_haproxy_frontend_addresses`
- `pfsense_get_services_haproxy_frontend_address`
- `pfsense_delete_services_haproxy_frontend_address`
- `pfsense_create_services_haproxy_frontend_certificate`
- `pfsense_list_services_haproxy_frontend_certificates`
- `pfsense_get_services_haproxy_frontend_certificate`
- `pfsense_delete_services_haproxy_frontend_certificate`
- `pfsense_create_services_haproxy_frontend_error_file`
- `pfsense_list_services_haproxy_frontend_error_files`
- `pfsense_get_services_haproxy_frontend_error_file`
- `pfsense_update_services_haproxy_frontend_error_file`
- `pfsense_delete_services_haproxy_frontend_error_file`
- `pfsense_get_services_haproxy_apply_status`
- `pfsense_services_haproxy_apply`

**Steps**:
1. **Create** using `pfsense_create_services_haproxy_backend` with `confirm=True`:
    - `name`: `bt_sys23_be`
    - `agent_port`: `0`
    - `persist_cookie_name`: `SRVID`
2. **Create** using `pfsense_create_services_haproxy_frontend` with `confirm=True`:
    - `name`: `bt_sys23_fe`
    - `type_`: `http`
    - `descr`: `Bank tester frontend`
3. **List** using `pfsense_list_services_haproxy_frontends` — verify the created resource appears
4. **Get** using `pfsense_get_services_haproxy_frontend` with the ID from the create response
5. **Update** using `pfsense_update_services_haproxy_frontend` with `confirm=True` — set `descr` to `Updated frontend`
6. **Get** again using `pfsense_get_services_haproxy_frontend` — verify `descr` was updated
7. **Create** using `pfsense_create_services_haproxy_frontend_acl` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `name`: `bt_sys23_facl`
    - `expression`: `host_starts_with`
    - `value`: `test.example.com`
8. **List** using `pfsense_list_services_haproxy_frontend_acls` — verify the created resource appears
9. **Get** using `pfsense_get_services_haproxy_frontend_acl` with the ID from the create response
10. **Update** using `pfsense_update_services_haproxy_frontend_acl` with `confirm=True` — set `value` to `updated.example.com`
11. **Get** again using `pfsense_get_services_haproxy_frontend_acl` — verify `value` was updated
12. **Create** using `pfsense_create_services_haproxy_frontend_action` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `action`: `http-request_lua`
    - `name`: `bt_sys23_fact`
    - `acl`: `bt_sys23_facl_sib`
13. **List** using `pfsense_list_services_haproxy_frontend_actions` — verify the created resource appears
14. **Get** using `pfsense_get_services_haproxy_frontend_action` with the ID from the create response
15. **Create** using `pfsense_create_services_haproxy_frontend_address` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `extaddr`: `custom`
    - `extaddr_custom`: `10.99.99.80:80`
16. **List** using `pfsense_list_services_haproxy_frontend_addresses` — verify the created resource appears
17. **Get** using `pfsense_get_services_haproxy_frontend_address` with the ID from the create response
18. **Create** using `pfsense_create_services_haproxy_frontend_certificate` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
(no parameters needed)
19. **List** using `pfsense_list_services_haproxy_frontend_certificates` — verify the created resource appears
20. **Get** using `pfsense_get_services_haproxy_frontend_certificate` with the ID from the create response
21. **Create** using `pfsense_create_services_haproxy_frontend_error_file` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `errorcode`: `503`
    - `errorfile`: `bt_sys23_file`
22. **List** using `pfsense_list_services_haproxy_frontend_error_files` — verify the created resource appears
23. **Get** using `pfsense_get_services_haproxy_frontend_error_file` with the ID from the create response
24. **Update** using `pfsense_update_services_haproxy_frontend_error_file` with `confirm=True` — set `errorcode` to `502`
25. **Get** again using `pfsense_get_services_haproxy_frontend_error_file` — verify `errorcode` was updated
26. **Check apply status** using `pfsense_get_services_haproxy_apply_status`
27. **Apply changes** using `pfsense_services_haproxy_apply` with `confirm=True`

**Important notes**:
Frontend requires a backend to exist. All frontend sub-resources need parent_id.
Frontend action requires ACL (create sibling). Error file needs HAProxy file.
Cleanup: sub-resources → frontend → backend.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_services_haproxy_frontend_error_file` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_haproxy_frontend_certificate` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_haproxy_frontend_address` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_haproxy_frontend_action` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_haproxy_frontend_acl` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_haproxy_frontend` with `confirm=True` (ID from create step)
- Delete setup resource at `/api/v2/services/haproxy/backend` using `pfsense_delete_services_haproxy_backend` with `confirm=True`

**Expected outcome**: All 31 tools exercised successfully.
