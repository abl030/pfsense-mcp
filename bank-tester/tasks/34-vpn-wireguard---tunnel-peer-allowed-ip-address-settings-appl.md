## Task 34: VPN WireGuard — Tunnel, Peer, Allowed IP, Address, Settings, Apply

**task_id**: 34-vpn-wireguard--tunnel-peer-allowed-ip-address-sett

**Objective**: Exercise all tools in the vpn/wireguard subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (20):
- `pfsense_get_vpn_wire_guard_settings`
- `pfsense_update_vpn_wire_guard_settings`
- `pfsense_create_vpn_wire_guard_tunnel`
- `pfsense_list_vpn_wire_guard_tunnel_addresses`
- `pfsense_get_vpn_wire_guard_tunnel`
- `pfsense_update_vpn_wire_guard_tunnel`
- `pfsense_delete_vpn_wire_guard_tunnel`
- `pfsense_create_vpn_wire_guard_tunnel_address`
- `pfsense_get_vpn_wire_guard_tunnel_address`
- `pfsense_delete_vpn_wire_guard_tunnel_address`
- `pfsense_create_vpn_wire_guard_peer`
- `pfsense_list_vpn_wire_guard_peer_allowed_i_ps`
- `pfsense_get_vpn_wire_guard_peer`
- `pfsense_update_vpn_wire_guard_peer`
- `pfsense_delete_vpn_wire_guard_peer`
- `pfsense_create_vpn_wire_guard_peer_allowed_ip`
- `pfsense_get_vpn_wire_guard_peer_allowed_ip`
- `pfsense_delete_vpn_wire_guard_peer_allowed_ip`
- `pfsense_get_vpn_wire_guard_apply_status`
- `pfsense_vpn_wire_guard_apply`

**Steps**:
1. **Get settings** using `pfsense_get_vpn_wire_guard_settings` — note current value of `enable`
2. **Update settings** using `pfsense_update_vpn_wire_guard_settings` with `confirm=True` — set `enable` to `True`
3. **Get settings** again using `pfsense_get_vpn_wire_guard_settings` — verify `enable` was updated
4. **Create** using `pfsense_create_vpn_wire_guard_tunnel` with `confirm=True`:
    - `name`: `bt_sys34_tun`
    - `listenport`: `51820`
    - `privatekey`: `YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY=`
    - `addresses`: `[]`
5. **List** using `pfsense_list_vpn_wire_guard_tunnel_addresses` — verify the created resource appears
6. **Get** using `pfsense_get_vpn_wire_guard_tunnel` with the ID from the create response
7. **Update** using `pfsense_update_vpn_wire_guard_tunnel` with `confirm=True` — set `listenport` to `51821`
8. **Get** again using `pfsense_get_vpn_wire_guard_tunnel` — verify `listenport` was updated
9. **Create** using `pfsense_create_vpn_wire_guard_tunnel_address` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `address`: `10.100.0.1`
    - `mask`: `24`
10. **List** using `pfsense_list_vpn_wire_guard_tunnel_addresses` — verify the created resource appears
11. **Get** using `pfsense_get_vpn_wire_guard_tunnel_address` with the ID from the create response
12. **Create** using `pfsense_create_vpn_wire_guard_peer` with `confirm=True` (inject `tun` from parent's `name` field):
    - `publickey`: `YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY=`
    - `descr`: `bt_sys34_peer`
13. **List** using `pfsense_list_vpn_wire_guard_peer_allowed_i_ps` — verify the created resource appears
14. **Get** using `pfsense_get_vpn_wire_guard_peer` with the ID from the create response
15. **Update** using `pfsense_update_vpn_wire_guard_peer` with `confirm=True` — set `descr` to `Updated peer`
16. **Get** again using `pfsense_get_vpn_wire_guard_peer` — verify `descr` was updated
17. **Create** using `pfsense_create_vpn_wire_guard_peer_allowed_ip` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `address`: `10.200.0.0`
    - `mask`: `24`
18. **List** using `pfsense_list_vpn_wire_guard_peer_allowed_i_ps` — verify the created resource appears
19. **Get** using `pfsense_get_vpn_wire_guard_peer_allowed_ip` with the ID from the create response
20. **Check apply status** using `pfsense_get_vpn_wire_guard_apply_status`
21. **Apply changes** using `pfsense_vpn_wire_guard_apply` with `confirm=True`

**Important notes**:
Tunnel addresses and peer allowed_ips are sub-resources (NOT inline arrays).
Peer needs tunnel name (tun field). Allowed IP needs peer parent_id.
Cleanup: allowed_ip → peer → address → tunnel. Apply after each mutation.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_vpn_wire_guard_peer_allowed_ip` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_vpn_wire_guard_peer` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_vpn_wire_guard_tunnel_address` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_vpn_wire_guard_tunnel` with `confirm=True` (ID from create step)

**Expected outcome**: All 20 tools exercised successfully.
