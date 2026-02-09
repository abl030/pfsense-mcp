## Task 55: OpenVPN Client Export Chain

**task_id**: 55-openvpn-client-export-chain

**Objective**: Exercise all tools in the vpn/openvpn subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (10):
- `pfsense_create_system_certificate_authority_generate`
- `pfsense_create_system_certificate_generate`
- `pfsense_create_vpn_open_vpn_server`
- `pfsense_delete_vpn_open_vpn_server`
- `pfsense_create_vpn_open_vpn_client_export_config`
- `pfsense_list_vpn_open_vpn_client_export_configs`
- `pfsense_get_vpn_open_vpn_client_export_config`
- `pfsense_update_vpn_open_vpn_client_export_config`
- `pfsense_delete_vpn_open_vpn_client_export_config`
- `pfsense_create_vpn_open_vpn_client_export`

**Steps**:
1. **Execute** `pfsense_create_system_certificate_authority_generate` with `confirm=True`:
    - `descr`: `bt_sys55_ca`
    - `keytype`: `RSA`
    - `keylen`: `2048`
    - `digest_alg`: `sha256`
    - `dn_commonname`: `BT OVPN Export CA`
    - `dn_country`: `US`
    - `dn_state`: `California`
    - `dn_city`: `San Francisco`
    - `dn_organization`: `pfSense Test`
    - `dn_organizationalunit`: `Testing`
    - `lifetime`: `3650`
2. **Execute** `pfsense_create_system_certificate_generate` with `confirm=True`:
    - `descr`: `bt_sys55_server_cert`
    - `keytype`: `RSA`
    - `keylen`: `2048`
    - `digest_alg`: `sha256`
    - `dn_commonname`: `ovpn-server.test`
    - `lifetime`: `365`
    - `type_`: `server`
3. **Create** using `pfsense_create_vpn_open_vpn_server` with `confirm=True`:
    - `mode`: `server_tls`
    - `protocol`: `UDP4`
    - `dev_mode`: `tun`
    - `interface`: `wan`
    - `local_port`: `11940`
    - `tunnel_network`: `10.110.0.0/24`
    - `descr`: `bt_sys55_ovpn_srv`
4. **Execute** `pfsense_create_system_certificate_generate` with `confirm=True` (User cert for client export.):
    - `descr`: `bt_sys55_user_cert`
    - `keytype`: `RSA`
    - `keylen`: `2048`
    - `digest_alg`: `sha256`
    - `dn_commonname`: `ovpn-user.test`
    - `lifetime`: `365`
    - `type_`: `user`
5. **Create** using `pfsense_create_vpn_open_vpn_client_export_config` with `confirm=True`:
    - `server`: ``
    - `pkcs11providers`: `[]`
    - `pkcs11id`: ``
    - `pass`: ``
    - `proxyaddr`: ``
    - `proxyport`: ``
    - `useproxypass`: `False`
    - `proxyuser`: ``
    - `proxypass`: ``
6. **List** using `pfsense_list_vpn_open_vpn_client_export_configs` — verify the created resource appears
7. **Get** using `pfsense_get_vpn_open_vpn_client_export_config` with the ID from the create response
8. **Update** using `pfsense_update_vpn_open_vpn_client_export_config` with `confirm=True` — set `pass` to `testpass`
9. **Get** again using `pfsense_get_vpn_open_vpn_client_export_config` — verify `pass` was updated
10. **Execute** `pfsense_create_vpn_open_vpn_client_export` with `confirm=True` (Export type must be 'confinline' (not 'inline'). Needs client_export config ID + certref.):
    - `type`: `confinline`

**Important notes**:
7-step dependency chain: CA → server cert → OVPN server → user cert → export config → export.
OVPN server in server_tls mode may produce log prefix before JSON.
local_port must be string. Export type is 'confinline'.
Cleanup: export config → OVPN server → certs → CA.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_vpn_open_vpn_client_export_config` with `confirm=True` (ID from create step)
- Delete setup resource at `/api/v2/vpn/openvpn/server` using `pfsense_delete_vpn_open_vpn_server` with `confirm=True`

**Expected outcome**: All 10 tools exercised successfully.
