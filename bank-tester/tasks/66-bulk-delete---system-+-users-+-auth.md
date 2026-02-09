## Task 66: Bulk Delete — System + Users + Auth

**task_id**: 66-bulk-delete--system-+-users-+-auth

**Objective**: Exercise all tools in the system subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (22):
- `pfsense_create_system_tunable`
- `pfsense_list_system_tunables`
- `pfsense_delete_system_tunables`
- `pfsense_list_system_certificate_authorities`
- `pfsense_delete_system_certificate_authorities`
- `pfsense_list_system_certificates`
- `pfsense_delete_system_certificates`
- `pfsense_list_system_cr_ls`
- `pfsense_delete_system_cr_ls`
- `pfsense_create_user`
- `pfsense_list_users`
- `pfsense_delete_users`
- `pfsense_create_user_group`
- `pfsense_list_user_groups`
- `pfsense_delete_user_groups`
- `pfsense_create_user_auth_server`
- `pfsense_list_user_auth_servers`
- `pfsense_delete_user_auth_servers`
- `pfsense_list_auth_keys`
- `pfsense_delete_auth_keys`
- `pfsense_list_diagnostics_config_history_revisions`
- `pfsense_delete_diagnostics_config_history_revisions`

**Steps**:
1. **Create** a test resource using `pfsense_create_system_tunable` with `confirm=True`:
    - `tunable`: `net.inet.tcp.tso`
    - `value`: `0`
2. **List** using `pfsense_list_system_tunables` — verify resource exists
3. **Bulk delete** using `pfsense_delete_system_tunables` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
4. **List** using `pfsense_list_system_tunables` — verify collection is empty
5. **List** using `pfsense_list_system_certificate_authorities` — verify resource exists (Bulk delete all CAs — may include system CAs)
6. **Bulk delete** using `pfsense_delete_system_certificate_authorities` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
7. **List** using `pfsense_list_system_certificate_authorities` — verify collection is empty
8. **List** using `pfsense_list_system_certificates` — verify resource exists (Bulk delete all certificates — may include system certs)
9. **Bulk delete** using `pfsense_delete_system_certificates` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
10. **List** using `pfsense_list_system_certificates` — verify collection is empty
11. **List** using `pfsense_list_system_cr_ls` — verify resource exists (Bulk delete all CRLs)
12. **Bulk delete** using `pfsense_delete_system_cr_ls` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
13. **List** using `pfsense_list_system_cr_ls` — verify collection is empty
14. **Create** a test resource using `pfsense_create_user` with `confirm=True`:
    - `username`: `bt_bd66_user`
    - `password`: `Testpass66!Abc`
15. **List** using `pfsense_list_users` — verify resource exists
16. **Bulk delete** using `pfsense_delete_users` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
17. **List** using `pfsense_list_users` — verify collection is empty
18. **Create** a test resource using `pfsense_create_user_group` with `confirm=True`:
    - `name`: `bt_bd66_group`
    - `scope`: `local`
19. **List** using `pfsense_list_user_groups` — verify resource exists
20. **Bulk delete** using `pfsense_delete_user_groups` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
21. **List** using `pfsense_list_user_groups` — verify collection is empty
22. **Create** a test resource using `pfsense_create_user_auth_server` with `confirm=True`:
    - `type_`: `ldap`
    - `name`: `bt_bd66_ldap`
    - `host`: `10.99.66.7`
    - `ldap_port`: `389`
    - `ldap_urltype`: `Standard TCP`
    - `ldap_protver`: `3`
    - `ldap_scope`: `one`
    - `ldap_basedn`: `dc=example,dc=com`
    - `ldap_authcn`: `ou=people,dc=example,dc=com`
    - `ldap_extended_enabled`: `False`
    - `ldap_attr_user`: `uid`
    - `ldap_attr_group`: `cn`
    - `ldap_attr_member`: `member`
    - `ldap_attr_groupobj`: `posixGroup`
    - `ldap_timeout`: `25`
23. **List** using `pfsense_list_user_auth_servers` — verify resource exists
24. **Bulk delete** using `pfsense_delete_user_auth_servers` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
25. **List** using `pfsense_list_user_auth_servers` — verify collection is empty
26. **List** using `pfsense_list_auth_keys` — verify resource exists (Bulk delete all API keys — WARNING: may lock you out! Only clear test keys.)
27. **Bulk delete** using `pfsense_delete_auth_keys` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
28. **List** using `pfsense_list_auth_keys` — verify collection is empty
29. **List** using `pfsense_list_diagnostics_config_history_revisions` — verify resource exists (Bulk delete config history revisions)
30. **Bulk delete** using `pfsense_delete_diagnostics_config_history_revisions` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
31. **List** using `pfsense_list_diagnostics_config_history_revisions` — verify collection is empty

**Important notes**:
Bulk delete system, user, auth, and diagnostics collections.
WARNING: Deleting all API keys locks you out. Deleting all CAs/certs may break HTTPS.
Tester should be careful — create throwaway resources and only bulk-delete those.
For CAs/certs/CRLs: may bulk delete empty or only delete test resources.
For auth/keys: the tester should skip this if it would lock out API access.

**Cleanup** (reverse order):
- No cleanup needed (read-only / settings restored)

**Expected outcome**: All 22 tools exercised successfully.
