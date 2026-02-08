## Task 27: FreeRADIUS — Client, Interface, User

**task_id**: 27-freeradius--client-interface-user

**Objective**: Exercise all tools in the services/freeradius subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (12):
- `pfsense_create_services_free_radius_client`
- `pfsense_get_services_free_radius_client`
- `pfsense_update_services_free_radius_client`
- `pfsense_delete_services_free_radius_client`
- `pfsense_create_services_free_radius_interface`
- `pfsense_get_services_free_radius_interface`
- `pfsense_update_services_free_radius_interface`
- `pfsense_delete_services_free_radius_interface`
- `pfsense_create_services_free_radius_user`
- `pfsense_get_services_free_radius_user`
- `pfsense_update_services_free_radius_user`
- `pfsense_delete_services_free_radius_user`

**Steps**:
1. **Create** using `pfsense_create_services_free_radius_client` with `confirm=True`:
    - `addr`: `10.99.99.90`
    - `shortname`: `bt_sys27_frcl`
    - `secret`: `TestSecret123`
    - `descr`: `Bank tester FR client`
2. **Get** using `pfsense_get_services_free_radius_client` with the ID from the create response
3. **Update** using `pfsense_update_services_free_radius_client` with `confirm=True` — set `descr` to `Updated FR client`
4. **Get** again using `pfsense_get_services_free_radius_client` — verify `descr` was updated
5. **Create** using `pfsense_create_services_free_radius_interface` with `confirm=True`:
    - `addr`: `127.0.0.1`
    - `ip_version`: `ipaddr`
    - `descr`: `bt_sys27_fri`
6. **Get** using `pfsense_get_services_free_radius_interface` with the ID from the create response
7. **Update** using `pfsense_update_services_free_radius_interface` with `confirm=True` — set `descr` to `Updated FR interface`
8. **Get** again using `pfsense_get_services_free_radius_interface` — verify `descr` was updated
9. **Create** using `pfsense_create_services_free_radius_user` with `confirm=True`:
    - `username`: `bt_sys27_fruser`
    - `password`: `TestPass123`
    - `motp_secret`: ``
    - `motp_pin`: ``
    - `descr`: `bt_sys27_fruser`
10. **Get** using `pfsense_get_services_free_radius_user` with the ID from the create response
11. **Update** using `pfsense_update_services_free_radius_user` with `confirm=True` — set `descr` to `Updated FR user`
12. **Get** again using `pfsense_get_services_free_radius_user` — verify `descr` was updated

**Important notes**:
FreeRADIUS client addr needs plain IP (no CIDR).
All three endpoints are straightforward CRUD.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_services_free_radius_user` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_free_radius_interface` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_free_radius_client` with `confirm=True` (ID from create step)

**Expected outcome**: All 12 tools exercised successfully.
