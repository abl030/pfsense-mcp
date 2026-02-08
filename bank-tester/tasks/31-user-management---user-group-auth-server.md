## Task 31: User Management — User, Group, Auth Server

**task_id**: 31-user-management--user-group-auth-server

**Objective**: Exercise all tools in the user subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (14):
- `pfsense_create_user`
- `pfsense_list_user_auth_servers`
- `pfsense_get_user`
- `pfsense_update_user`
- `pfsense_delete_user`
- `pfsense_create_user_group`
- `pfsense_list_user_groups`
- `pfsense_get_user_group`
- `pfsense_update_user_group`
- `pfsense_delete_user_group`
- `pfsense_create_user_auth_server`
- `pfsense_get_user_auth_server`
- `pfsense_update_user_auth_server`
- `pfsense_delete_user_auth_server`

**Steps**:
1. **Create** using `pfsense_create_user` with `confirm=True`:
    - `username`: `bt_sys31_user`
    - `password`: `Testpass123!Abc`
    - `descr`: `Bank tester user`
2. **List** using `pfsense_list_user_auth_servers` — verify the created resource appears
3. **Get** using `pfsense_get_user` with the ID from the create response
4. **Update** using `pfsense_update_user` with `confirm=True` — set `descr` to `Updated user`
5. **Get** again using `pfsense_get_user` — verify `descr` was updated
6. **Create** using `pfsense_create_user_group` with `confirm=True`:
    - `name`: `bt_sys31_group`
    - `scope`: `local`
    - `descr`: `Bank tester group`
7. **List** using `pfsense_list_user_groups` — verify the created resource appears
8. **Get** using `pfsense_get_user_group` with the ID from the create response
9. **Update** using `pfsense_update_user_group` with `confirm=True` — set `descr` to `Updated group`
10. **Get** again using `pfsense_get_user_group` — verify `descr` was updated
11. **Create** using `pfsense_create_user_auth_server` with `confirm=True`:
    - `type_`: `ldap`
    - `name`: `bt_sys31_ldap`
    - `host`: `10.99.99.7`
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
    - `descr`: `Bank tester LDAP`
12. **List** using `pfsense_list_user_auth_servers` — verify the created resource appears
13. **Get** using `pfsense_get_user_auth_server` with the ID from the create response
14. **Update** using `pfsense_update_user_auth_server` with `confirm=True` — set `descr` to `Updated LDAP`
15. **Get** again using `pfsense_get_user_auth_server` — verify `descr` was updated

**Important notes**:
Auth server type_ must be 'ldap' or 'radius'. LDAP needs many required fields.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_user_auth_server` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_user_group` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_user` with `confirm=True` (ID from create step)

**Expected outcome**: All 14 tools exercised successfully.
