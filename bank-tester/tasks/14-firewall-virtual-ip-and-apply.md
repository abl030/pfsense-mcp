## Task 14: Firewall Virtual IP & Apply

**task_id**: 14-firewall-virtual-ip--apply

**Objective**: Exercise all tools in the firewall/virtual_ip subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (7):
- `pfsense_create_firewall_virtual_ip`
- `pfsense_list_firewall_virtual_ips`
- `pfsense_get_firewall_virtual_ip`
- `pfsense_update_firewall_virtual_ip`
- `pfsense_delete_firewall_virtual_ip`
- `pfsense_get_firewall_virtual_ip_apply_status`
- `pfsense_firewall_virtual_ip_apply`

**Steps**:
1. **Create** using `pfsense_create_firewall_virtual_ip` with `confirm=True`:
    - `mode`: `ipalias`
    - `interface`: `wan`
    - `subnet`: `10.99.99.100`
    - `subnet_bits`: `32`
    - `descr`: `bt_sys14_vip`
2. **List** using `pfsense_list_firewall_virtual_ips` — verify the created resource appears
3. **Get** using `pfsense_get_firewall_virtual_ip` with the ID from the create response
4. **Update** using `pfsense_update_firewall_virtual_ip` with `confirm=True` — set `descr` to `Updated VIP`
5. **Get** again using `pfsense_get_firewall_virtual_ip` — verify `descr` was updated
6. **Check apply status** using `pfsense_get_firewall_virtual_ip_apply_status`
7. **Apply changes** using `pfsense_firewall_virtual_ip_apply` with `confirm=True`

**Important notes**:
Virtual IP 'subnet' field is an IP address, not prefix length.
Apply virtual_ip changes separately from regular firewall apply.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_firewall_virtual_ip` with `confirm=True` (ID from create step)

**Expected outcome**: All 7 tools exercised successfully.
