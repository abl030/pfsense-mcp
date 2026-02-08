## Task 33: VPN OpenVPN — Server, Client, CSO

**task_id**: 33-vpn-openvpn--server-client-cso

**Objective**: Exercise all tools in the vpn/openvpn subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (15):
- `pfsense_create_vpn_open_vpn_server`
- `pfsense_list_vpn_open_vpn_servers`
- `pfsense_get_vpn_open_vpn_server`
- `pfsense_update_vpn_open_vpn_server`
- `pfsense_delete_vpn_open_vpn_server`
- `pfsense_create_vpn_open_vpn_client`
- `pfsense_list_vpn_open_vpn_clients`
- `pfsense_get_vpn_open_vpn_client`
- `pfsense_update_vpn_open_vpn_client`
- `pfsense_delete_vpn_open_vpn_client`
- `pfsense_create_vpn_open_vpncso`
- `pfsense_list_vpn_open_vpncs_os`
- `pfsense_get_vpn_open_vpncso`
- `pfsense_update_vpn_open_vpncso`
- `pfsense_delete_vpn_open_vpncso`

**Steps**:
1. **Create** using `pfsense_create_vpn_open_vpn_server` with `confirm=True`:
    - `mode`: `p2p_tls`
    - `protocol`: `UDP4`
    - `dev_mode`: `tun`
    - `interface`: `wan`
    - `local_port`: `1194`
    - `tunnel_network`: `10.100.0.0/24`
    - `descr`: `bt_sys33_ovpn`
2. **List** using `pfsense_list_vpn_open_vpn_servers` — verify the created resource appears
3. **Get** using `pfsense_get_vpn_open_vpn_server` with the ID from the create response
4. **Update** using `pfsense_update_vpn_open_vpn_server` with `confirm=True` — set `descr` to `Updated OVPN server`
5. **Get** again using `pfsense_get_vpn_open_vpn_server` — verify `descr` was updated
6. **Create** using `pfsense_create_vpn_open_vpn_client` with `confirm=True`:
    - `mode`: `p2p_tls`
    - `protocol`: `UDP4`
    - `dev_mode`: `tun`
    - `interface`: `wan`
    - `server_addr`: `10.99.99.30`
    - `server_port`: `1194`
    - `descr`: `bt_sys33_ovpn_cl`
7. **List** using `pfsense_list_vpn_open_vpn_clients` — verify the created resource appears
8. **Get** using `pfsense_get_vpn_open_vpn_client` with the ID from the create response
9. **Update** using `pfsense_update_vpn_open_vpn_client` with `confirm=True` — set `descr` to `Updated OVPN client`
10. **Get** again using `pfsense_get_vpn_open_vpn_client` — verify `descr` was updated
11. **Create** using `pfsense_create_vpn_open_vpncso` with `confirm=True`:
    - `common_name`: `bt_sys33_cso`
    - `tunnel_network`: `10.101.0.0/24`
    - `descr`: `bt_sys33_cso`
12. **List** using `pfsense_list_vpn_open_vpncs_os` — verify the created resource appears
13. **Get** using `pfsense_get_vpn_open_vpncso` with the ID from the create response
14. **Update** using `pfsense_update_vpn_open_vpncso` with `confirm=True` — set `descr` to `Updated CSO`
15. **Get** again using `pfsense_get_vpn_open_vpncso` — verify `descr` was updated

**Important notes**:
OpenVPN server in TLS mode may produce log prefix before JSON response.
local_port must be string, not int.

**Skipped endpoints**:
- `/api/v2/vpn/openvpn/client_export/config` — Tested via existing task 09 workflow (7-step chain)

**Cleanup** (reverse order):
- Delete using `pfsense_delete_vpn_open_vpncso` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_vpn_open_vpn_client` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_vpn_open_vpn_server` with `confirm=True` (ID from create step)

**Expected outcome**: All 15 tools exercised successfully.
