## Task 54: Network Interface CRUD

**task_id**: 54-network-interface-crud

**Objective**: Exercise all tools in the network subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (8):
- `pfsense_create_interface_vlan`
- `pfsense_delete_interface_vlan`
- `pfsense_post_/api/v2/network/interface`
- `pfsense_get_/api/v2/network/interface`
- `pfsense_patch_/api/v2/network/interface`
- `pfsense_delete_/api/v2/network/interface`
- `pfsense_get_interface_apply_status`
- `pfsense_interface_apply`

**Steps**:
1. **Create** using `pfsense_create_interface_vlan` with `confirm=True`:
    - `if`: `em2`
    - `tag`: `200`
    - `pcp`: `0`
    - `descr`: `bt_sys54_vlan`
2. **Create** using `pfsense_post_/api/v2/network/interface` with `confirm=True`:
    - `if`: `em2.200`
    - `descr`: `bt_sys54_iface`
    - `enable`: `False`
    - `typev4`: `none`
3. **Get** using `pfsense_get_/api/v2/network/interface` with the ID from the create response
4. **Update** using `pfsense_patch_/api/v2/network/interface` with `confirm=True` — set `descr` to `Updated interface`
5. **Get** again using `pfsense_get_/api/v2/network/interface` — verify `descr` was updated
6. **Check apply status** using `pfsense_get_interface_apply_status`
7. **Apply changes** using `pfsense_interface_apply` with `confirm=True`

**Important notes**:
Create a VLAN on em2 (spare NIC), then assign it as a network interface.
Network interface CRUD: create → list → get → update → delete.
Keep interface disabled (enable=false) to avoid disruption.
Cleanup: delete interface → delete VLAN.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_/api/v2/network/interface` with `confirm=True` (ID from create step)
- Delete setup resource at `/api/v2/interface/vlan` using `pfsense_delete_interface_vlan` with `confirm=True`

**Expected outcome**: All 8 tools exercised successfully.
