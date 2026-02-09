## Task 65: Bulk Delete — FreeRADIUS + HAProxy

**task_id**: 65-bulk-delete--freeradius-+-haproxy

**Objective**: Exercise all tools in the services subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (44):
- `pfsense_create_services_free_radius_client`
- `pfsense_list_services_free_radius_clients`
- `pfsense_delete_services_free_radius_clients`
- `pfsense_create_services_free_radius_interface`
- `pfsense_list_services_free_radius_interfaces`
- `pfsense_delete_services_free_radius_interfaces`
- `pfsense_create_services_free_radius_user`
- `pfsense_list_services_free_radius_users`
- `pfsense_delete_services_free_radius_users`
- `pfsense_create_services_ha_proxy_file`
- `pfsense_list_services_ha_proxy_files`
- `pfsense_delete_services_ha_proxy_files`
- `pfsense_create_services_ha_proxy_backend`
- `pfsense_list_services_ha_proxy_backends`
- `pfsense_delete_services_ha_proxy_backends`
- `pfsense_create_services_ha_proxy_backend_acl`
- `pfsense_list_services_ha_proxy_backend_ac_ls`
- `pfsense_delete_services_ha_proxy_backend_ac_ls`
- `pfsense_create_services_ha_proxy_backend_action`
- `pfsense_list_services_ha_proxy_backend_actions`
- `pfsense_delete_services_ha_proxy_backend_actions`
- `pfsense_create_services_ha_proxy_backend_server`
- `pfsense_list_services_ha_proxy_backend_servers`
- `pfsense_delete_services_ha_proxy_backend_servers`
- `pfsense_create_services_ha_proxy_backend_error_file`
- `pfsense_list_services_ha_proxy_backend_error_files`
- `pfsense_delete_services_ha_proxy_backend_error_files`
- `pfsense_create_services_ha_proxy_frontend`
- `pfsense_list_services_ha_proxy_frontends`
- `pfsense_delete_services_ha_proxy_frontends`
- `pfsense_create_services_ha_proxy_frontend_acl`
- `pfsense_list_services_ha_proxy_frontend_ac_ls`
- `pfsense_delete_services_ha_proxy_frontend_ac_ls`
- `pfsense_create_services_ha_proxy_frontend_action`
- `pfsense_list_services_ha_proxy_frontend_actions`
- `pfsense_delete_services_ha_proxy_frontend_actions`
- `pfsense_create_services_ha_proxy_frontend_address`
- `pfsense_list_services_ha_proxy_frontend_addresses`
- `pfsense_delete_services_ha_proxy_frontend_addresses`
- `pfsense_list_services_ha_proxy_frontend_certificates`
- `pfsense_delete_services_ha_proxy_frontend_certificates`
- `pfsense_create_services_ha_proxy_frontend_error_file`
- `pfsense_list_services_ha_proxy_frontend_error_files`
- `pfsense_delete_services_ha_proxy_frontend_error_files`

**Steps**:
1. **Create** a test resource using `pfsense_create_services_free_radius_client` with `confirm=True`:
    - `addr`: `10.99.65.90`
    - `shortname`: `bt_bd65_frcl`
    - `secret`: `TestSecret65`
2. **List** using `pfsense_list_services_free_radius_clients` — verify resource exists
3. **Bulk delete** using `pfsense_delete_services_free_radius_clients` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
4. **List** using `pfsense_list_services_free_radius_clients` — verify collection is empty
5. **Create** a test resource using `pfsense_create_services_free_radius_interface` with `confirm=True`:
    - `addr`: `127.0.0.1`
    - `ip_version`: `ipaddr`
6. **List** using `pfsense_list_services_free_radius_interfaces` — verify resource exists
7. **Bulk delete** using `pfsense_delete_services_free_radius_interfaces` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
8. **List** using `pfsense_list_services_free_radius_interfaces` — verify collection is empty
9. **Create** a test resource using `pfsense_create_services_free_radius_user` with `confirm=True`:
    - `username`: `bt_bd65_fruser`
    - `password`: `TestPass65`
    - `motp_secret`: ``
    - `motp_pin`: ``
10. **List** using `pfsense_list_services_free_radius_users` — verify resource exists
11. **Bulk delete** using `pfsense_delete_services_free_radius_users` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
12. **List** using `pfsense_list_services_free_radius_users` — verify collection is empty
13. **Create** a test resource using `pfsense_create_services_ha_proxy_file` with `confirm=True`:
    - `name`: `bt_bd65_file`
    - `content`: `PCFET0NUWVBFIGh0bWw+`
14. **List** using `pfsense_list_services_ha_proxy_files` — verify resource exists
15. **Bulk delete** using `pfsense_delete_services_ha_proxy_files` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
16. **List** using `pfsense_list_services_ha_proxy_files` — verify collection is empty
17. **Create** a test resource using `pfsense_create_services_ha_proxy_backend` with `confirm=True`:
    - `name`: `bt_bd65_be`
    - `agent_port`: `0`
    - `persist_cookie_name`: `SRVID`
18. **List** using `pfsense_list_services_ha_proxy_backends` — verify resource exists
19. **Bulk delete** using `pfsense_delete_services_ha_proxy_backends` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
20. **List** using `pfsense_list_services_ha_proxy_backends` — verify collection is empty
21. **Create** a test resource using `pfsense_create_services_ha_proxy_backend_acl` with `confirm=True` (use parent_id from the parent resource):
    - `name`: `bt_bd65_bacl`
    - `expression`: `host_starts_with`
    - `value`: `bd65.example.com`
22. **List** using `pfsense_list_services_ha_proxy_backend_ac_ls` — verify resource exists (Needs backend parent_id)
23. **Bulk delete** using `pfsense_delete_services_ha_proxy_backend_ac_ls` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
24. **List** using `pfsense_list_services_ha_proxy_backend_ac_ls` — verify collection is empty
25. **Create** a test resource using `pfsense_create_services_ha_proxy_backend_action` with `confirm=True` (use parent_id from the parent resource):
    - `action`: `http-request_lua`
    - `lua_function`: `bd65_func`
    - `acl`: `bt_bd65_bacl`
26. **List** using `pfsense_list_services_ha_proxy_backend_actions` — verify resource exists (Needs backend parent_id + ACL)
27. **Bulk delete** using `pfsense_delete_services_ha_proxy_backend_actions` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
28. **List** using `pfsense_list_services_ha_proxy_backend_actions` — verify collection is empty
29. **Create** a test resource using `pfsense_create_services_ha_proxy_backend_server` with `confirm=True` (use parent_id from the parent resource):
    - `name`: `bt_bd65_bsrv`
    - `address`: `10.99.65.50`
    - `port`: `8065`
30. **List** using `pfsense_list_services_ha_proxy_backend_servers` — verify resource exists (Needs backend parent_id)
31. **Bulk delete** using `pfsense_delete_services_ha_proxy_backend_servers` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
32. **List** using `pfsense_list_services_ha_proxy_backend_servers` — verify collection is empty
33. **Create** a test resource using `pfsense_create_services_ha_proxy_backend_error_file` with `confirm=True` (use parent_id from the parent resource):
    - `errorcode`: `503`
    - `errorfile`: `bt_bd65_file`
34. **List** using `pfsense_list_services_ha_proxy_backend_error_files` — verify resource exists (Needs backend parent_id + HAProxy file)
35. **Bulk delete** using `pfsense_delete_services_ha_proxy_backend_error_files` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
36. **List** using `pfsense_list_services_ha_proxy_backend_error_files` — verify collection is empty
37. **Create** a test resource using `pfsense_create_services_ha_proxy_frontend` with `confirm=True`:
    - `name`: `bt_bd65_fe`
    - `type_`: `http`
38. **List** using `pfsense_list_services_ha_proxy_frontends` — verify resource exists
39. **Bulk delete** using `pfsense_delete_services_ha_proxy_frontends` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
40. **List** using `pfsense_list_services_ha_proxy_frontends` — verify collection is empty
41. **Create** a test resource using `pfsense_create_services_ha_proxy_frontend_acl` with `confirm=True` (use parent_id from the parent resource):
    - `name`: `bt_bd65_facl`
    - `expression`: `host_starts_with`
    - `value`: `bd65fe.example.com`
42. **List** using `pfsense_list_services_ha_proxy_frontend_ac_ls` — verify resource exists (Needs frontend parent_id)
43. **Bulk delete** using `pfsense_delete_services_ha_proxy_frontend_ac_ls` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
44. **List** using `pfsense_list_services_ha_proxy_frontend_ac_ls` — verify collection is empty
45. **Create** a test resource using `pfsense_create_services_ha_proxy_frontend_action` with `confirm=True` (use parent_id from the parent resource):
    - `action`: `http-request_lua`
    - `lua_function`: `bd65fe_func`
    - `acl`: `bt_bd65_facl`
46. **List** using `pfsense_list_services_ha_proxy_frontend_actions` — verify resource exists (Needs frontend parent_id + ACL)
47. **Bulk delete** using `pfsense_delete_services_ha_proxy_frontend_actions` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
48. **List** using `pfsense_list_services_ha_proxy_frontend_actions` — verify collection is empty
49. **Create** a test resource using `pfsense_create_services_ha_proxy_frontend_address` with `confirm=True` (use parent_id from the parent resource):
    - `extaddr`: `custom`
    - `extaddr_custom`: `10.99.65.80:80`
50. **List** using `pfsense_list_services_ha_proxy_frontend_addresses` — verify resource exists (Needs frontend parent_id)
51. **Bulk delete** using `pfsense_delete_services_ha_proxy_frontend_addresses` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
52. **List** using `pfsense_list_services_ha_proxy_frontend_addresses` — verify collection is empty
53. **List** using `pfsense_list_services_ha_proxy_frontend_certificates` — verify resource exists (Needs frontend parent_id)
54. **Bulk delete** using `pfsense_delete_services_ha_proxy_frontend_certificates` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
55. **List** using `pfsense_list_services_ha_proxy_frontend_certificates` — verify collection is empty
56. **Create** a test resource using `pfsense_create_services_ha_proxy_frontend_error_file` with `confirm=True` (use parent_id from the parent resource):
    - `errorcode`: `503`
    - `errorfile`: `bt_bd65_file`
57. **List** using `pfsense_list_services_ha_proxy_frontend_error_files` — verify resource exists (Needs frontend parent_id + HAProxy file)
58. **Bulk delete** using `pfsense_delete_services_ha_proxy_frontend_error_files` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
59. **List** using `pfsense_list_services_ha_proxy_frontend_error_files` — verify collection is empty

**Important notes**:
Bulk delete FreeRADIUS and HAProxy collections.
HAProxy: create backend/frontend → sub-resources → bulk delete sub-resources → delete parents.
HAProxy sub-resources need parent_id from their parent backend/frontend.
Backend actions need an ACL created first.
Error files need HAProxy file resource.

**Cleanup** (reverse order):
- No cleanup needed (read-only / settings restored)

**Expected outcome**: All 44 tools exercised successfully.
