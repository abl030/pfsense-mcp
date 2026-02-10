## Task 16: Interface — Interface, VLAN, Bridge, GRE, Group, LAGG, Apply

**task_id**: 16-interface--interface-vlan-bridge-gre-group-lagg-ap

**Objective**: Exercise all tools in the interface subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (28):
- `pfsense_create_interface_vlan`
- `pfsense_list_interface_vlans`
- `pfsense_get_interface_vlan`
- `pfsense_update_interface_vlan`
- `pfsense_delete_interface_vlan`
- `pfsense_create_interface_bridge`
- `pfsense_list_interface_bridges`
- `pfsense_get_interface_bridge`
- `pfsense_update_interface_bridge`
- `pfsense_delete_interface_bridge`
- `pfsense_create_interface_gre`
- `pfsense_list_interface_gres`
- `pfsense_get_interface_gre`
- `pfsense_update_interface_gre`
- `pfsense_delete_interface_gre`
- `pfsense_create_interface_group`
- `pfsense_list_interface_groups`
- `pfsense_get_interface_group`
- `pfsense_update_interface_group`
- `pfsense_delete_interface_group`
- `pfsense_create_interface_lagg`
- `pfsense_list_interface_laggs`
- `pfsense_get_interface_lagg`
- `pfsense_update_interface_lagg`
- `pfsense_delete_interface_lagg`
- `pfsense_list_interface_available_interfaces`
- `pfsense_get_interface_apply_status`
- `pfsense_interface_apply`

**Steps**:
1. **Create** using `pfsense_create_interface_vlan` with `confirm=True`:
    - `if`: `em0`
    - `tag`: `100`
    - `pcp`: `0`
    - `descr`: `bt_sys16_vlan`
2. **List** using `pfsense_list_interface_vlans` — verify the created resource appears
3. **Get** using `pfsense_get_interface_vlan` with the ID from the create response
4. **Update** using `pfsense_update_interface_vlan` with `confirm=True` — set `descr` to `Updated VLAN`
5. **Get** again using `pfsense_get_interface_vlan` — verify `descr` was updated
6. **Create** using `pfsense_create_interface_bridge` with `confirm=True`:
    - `members`: `['lan']`
    - `descr`: `bt_sys16_bridge`
7. **List** using `pfsense_list_interface_bridges` — verify the created resource appears
8. **Get** using `pfsense_get_interface_bridge` with the ID from the create response
9. **Update** using `pfsense_update_interface_bridge` with `confirm=True` — set `descr` to `Updated bridge`
10. **Get** again using `pfsense_get_interface_bridge` — verify `descr` was updated
11. **Create** using `pfsense_create_interface_gre` with `confirm=True`:
    - `if`: `wan`
    - `remote_addr`: `198.51.100.1`
    - `tunnel_local_addr`: `10.255.0.1`
    - `tunnel_remote_addr`: `10.255.0.2`
    - `tunnel_remote_addr6`: ``
    - `descr`: `bt_sys16_gre`
12. **List** using `pfsense_list_interface_gres` — verify the created resource appears
13. **Get** using `pfsense_get_interface_gre` with the ID from the create response
14. **Update** using `pfsense_update_interface_gre` with `confirm=True` — set `descr` to `Updated GRE`
15. **Get** again using `pfsense_get_interface_gre` — verify `descr` was updated
16. **Create** using `pfsense_create_interface_group` with `confirm=True`:
    - `ifname`: `bt16grp`
    - `members`: `['wan']`
    - `descr`: `bt_sys16_group`
17. **List** using `pfsense_list_interface_groups` — verify the created resource appears
18. **Get** using `pfsense_get_interface_group` with the ID from the create response
19. **Update** using `pfsense_update_interface_group` with `confirm=True` — set `descr` to `Updated group`
20. **Get** again using `pfsense_get_interface_group` — verify `descr` was updated
21. **Create** using `pfsense_create_interface_lagg` with `confirm=True`:
    - `members`: `['em2']`
    - `proto`: `none`
    - `descr`: `bt_sys16_lagg`
22. **List** using `pfsense_list_interface_laggs` — verify the created resource appears
23. **Get** using `pfsense_get_interface_lagg` with the ID from the create response
24. **Update** using `pfsense_update_interface_lagg` with `confirm=True` — set `descr` to `Updated LAGG`
25. **Get** again using `pfsense_get_interface_lagg` — verify `descr` was updated
26. **Read** using `pfsense_list_interface_available_interfaces`
27. **Check apply status** using `pfsense_get_interface_apply_status`
28. **Apply changes** using `pfsense_interface_apply` with `confirm=True`

**Important notes**:
LAGG uses em2 (spare NIC). GRE needs remote_addr as routable IP.
Bridge members must reference existing interfaces by pfSense name.
Apply interface after mutations.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_interface_lagg` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_interface_group` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_interface_gre` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_interface_bridge` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_interface_vlan` with `confirm=True` (ID from create step)

**Expected outcome**: All 28 tools exercised successfully.
