## Task 67: Bulk Delete — VPN + Status

**task_id**: 67-bulk-delete--vpn-+-status

**Objective**: Exercise all tools in the vpn subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (39):
- `pfsense_create_vpni_psec_phase1`
- `pfsense_list_vpni_psec_phase1s`
- `pfsense_delete_vpni_psec_phase1s`
- `pfsense_create_vpni_psec_phase1_encryption`
- `pfsense_list_vpni_psec_phase1_encryptions`
- `pfsense_delete_vpni_psec_phase1_encryptions`
- `pfsense_create_vpni_psec_phase2`
- `pfsense_list_vpni_psec_phase2s`
- `pfsense_delete_vpni_psec_phase2s`
- `pfsense_create_vpni_psec_phase2_encryption`
- `pfsense_list_vpni_psec_phase2_encryptions`
- `pfsense_delete_vpni_psec_phase2_encryptions`
- `pfsense_create_vpn_open_vpn_server`
- `pfsense_list_vpn_open_vpn_servers`
- `pfsense_delete_vpn_open_vpn_servers`
- `pfsense_create_vpn_open_vpn_client`
- `pfsense_list_vpn_open_vpn_clients`
- `pfsense_delete_vpn_open_vpn_clients`
- `pfsense_create_vpn_open_vpncso`
- `pfsense_list_vpn_open_vpncs_os`
- `pfsense_delete_vpn_open_vpncs_os`
- `pfsense_list_vpn_open_vpn_client_export_configs`
- `pfsense_delete_vpn_open_vpn_client_export_configs`
- `pfsense_create_vpn_wire_guard_tunnel`
- `pfsense_list_vpn_wire_guard_tunnels`
- `pfsense_delete_vpn_wire_guard_tunnels`
- `pfsense_create_vpn_wire_guard_tunnel_address`
- `pfsense_list_vpn_wire_guard_tunnel_addresses`
- `pfsense_delete_vpn_wire_guard_tunnel_addresses`
- `pfsense_create_vpn_wire_guard_peer`
- `pfsense_list_vpn_wire_guard_peers`
- `pfsense_delete_vpn_wire_guard_peers`
- `pfsense_create_vpn_wire_guard_peer_allowed_ip`
- `pfsense_list_vpn_wire_guard_peer_allowed_i_ps`
- `pfsense_delete_vpn_wire_guard_peer_allowed_i_ps`
- `pfsense_list_status_dhcp_server_leases`
- `pfsense_delete_status_dhcp_server_leases`
- `pfsense_list_status_open_vpn_server_connections`
- `pfsense_delete_status_open_vpn_server_connections`

**Steps**:
1. **Create** a test resource using `pfsense_create_vpni_psec_phase1` with `confirm=True`:
    - `iketype`: `ikev2`
    - `protocol`: `inet`
    - `interface`: `wan`
    - `remote_gateway`: `10.99.67.20`
    - `authentication_method`: `pre_shared_key`
    - `pre_shared_key`: `TestPSK67`
    - `myid_type`: `myaddress`
    - `peerid_type`: `peeraddress`
2. **List** using `pfsense_list_vpni_psec_phase1s` — verify resource exists
3. **Bulk delete** using `pfsense_delete_vpni_psec_phase1s` with `confirm=True` — delete ALL resources in this collection
4. **List** using `pfsense_list_vpni_psec_phase1s` — verify collection is empty
5. **Create** a test resource using `pfsense_create_vpni_psec_phase1_encryption` with `confirm=True` (use parent_id from the parent resource):
    - `encryption_algorithm_name`: `aes`
    - `encryption_algorithm_keylen`: `256`
    - `hash_algorithm`: `sha256`
    - `dhgroup`: `14`
6. **List** using `pfsense_list_vpni_psec_phase1_encryptions` — verify resource exists (Needs phase1 parent_id)
7. **Bulk delete** using `pfsense_delete_vpni_psec_phase1_encryptions` with `confirm=True` — delete ALL resources in this collection
8. **List** using `pfsense_list_vpni_psec_phase1_encryptions` — verify collection is empty
9. **Create** a test resource using `pfsense_create_vpni_psec_phase2` with `confirm=True`:
    - `mode`: `tunnel`
    - `localid_type`: `network`
    - `localid_address`: `10.67.0.0`
    - `localid_netbits`: `24`
    - `remoteid_type`: `network`
    - `remoteid_address`: `10.200.67.0`
    - `remoteid_netbits`: `24`
    - `protocol`: `esp`
10. **List** using `pfsense_list_vpni_psec_phase2s` — verify resource exists (Needs ikeid from phase1)
11. **Bulk delete** using `pfsense_delete_vpni_psec_phase2s` with `confirm=True` — delete ALL resources in this collection
12. **List** using `pfsense_list_vpni_psec_phase2s` — verify collection is empty
13. **Create** a test resource using `pfsense_create_vpni_psec_phase2_encryption` with `confirm=True` (use parent_id from the parent resource):
    - `encryption_algorithm_name`: `aes`
    - `encryption_algorithm_keylen`: `256`
    - `hash_algorithm`: `sha256`
14. **List** using `pfsense_list_vpni_psec_phase2_encryptions` — verify resource exists (Needs phase2 parent_id)
15. **Bulk delete** using `pfsense_delete_vpni_psec_phase2_encryptions` with `confirm=True` — delete ALL resources in this collection
16. **List** using `pfsense_list_vpni_psec_phase2_encryptions` — verify collection is empty
17. **Create** a test resource using `pfsense_create_vpn_open_vpn_server` with `confirm=True`:
    - `mode`: `p2p_tls`
    - `protocol`: `UDP4`
    - `dev_mode`: `tun`
    - `interface`: `wan`
    - `local_port`: `11967`
    - `tunnel_network`: `10.167.0.0/24`
18. **List** using `pfsense_list_vpn_open_vpn_servers` — verify resource exists (May need CA/cert for TLS mode)
19. **Bulk delete** using `pfsense_delete_vpn_open_vpn_servers` with `confirm=True` — delete ALL resources in this collection
20. **List** using `pfsense_list_vpn_open_vpn_servers` — verify collection is empty
21. **Create** a test resource using `pfsense_create_vpn_open_vpn_client` with `confirm=True`:
    - `mode`: `p2p_tls`
    - `protocol`: `UDP4`
    - `dev_mode`: `tun`
    - `interface`: `wan`
    - `server_addr`: `10.99.67.30`
    - `server_port`: `1194`
22. **List** using `pfsense_list_vpn_open_vpn_clients` — verify resource exists
23. **Bulk delete** using `pfsense_delete_vpn_open_vpn_clients` with `confirm=True` — delete ALL resources in this collection
24. **List** using `pfsense_list_vpn_open_vpn_clients` — verify collection is empty
25. **Create** a test resource using `pfsense_create_vpn_open_vpncso` with `confirm=True`:
    - `common_name`: `bt_bd67_cso`
    - `tunnel_network`: `10.167.1.0/24`
26. **List** using `pfsense_list_vpn_open_vpncs_os` — verify resource exists
27. **Bulk delete** using `pfsense_delete_vpn_open_vpncs_os` with `confirm=True` — delete ALL resources in this collection
28. **List** using `pfsense_list_vpn_open_vpncs_os` — verify collection is empty
29. **List** using `pfsense_list_vpn_open_vpn_client_export_configs` — verify resource exists (May need OVPN server setup first)
30. **Bulk delete** using `pfsense_delete_vpn_open_vpn_client_export_configs` with `confirm=True` — delete ALL resources in this collection
31. **List** using `pfsense_list_vpn_open_vpn_client_export_configs` — verify collection is empty
32. **Create** a test resource using `pfsense_create_vpn_wire_guard_tunnel` with `confirm=True`:
    - `name`: `bt_bd67_tun`
    - `listenport`: `51867`
    - `privatekey`: `YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY=`
    - `addresses`: `[]`
33. **List** using `pfsense_list_vpn_wire_guard_tunnels` — verify resource exists
34. **Bulk delete** using `pfsense_delete_vpn_wire_guard_tunnels` with `confirm=True` — delete ALL resources in this collection
35. **List** using `pfsense_list_vpn_wire_guard_tunnels` — verify collection is empty
36. **Create** a test resource using `pfsense_create_vpn_wire_guard_tunnel_address` with `confirm=True` (use parent_id from the parent resource):
    - `address`: `10.167.0.1`
    - `mask`: `24`
37. **List** using `pfsense_list_vpn_wire_guard_tunnel_addresses` — verify resource exists (Needs tunnel parent_id)
38. **Bulk delete** using `pfsense_delete_vpn_wire_guard_tunnel_addresses` with `confirm=True` — delete ALL resources in this collection
39. **List** using `pfsense_list_vpn_wire_guard_tunnel_addresses` — verify collection is empty
40. **Create** a test resource using `pfsense_create_vpn_wire_guard_peer` with `confirm=True`:
    - `publickey`: `YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY=`
41. **List** using `pfsense_list_vpn_wire_guard_peers` — verify resource exists (Needs tunnel name for tun field)
42. **Bulk delete** using `pfsense_delete_vpn_wire_guard_peers` with `confirm=True` — delete ALL resources in this collection
43. **List** using `pfsense_list_vpn_wire_guard_peers` — verify collection is empty
44. **Create** a test resource using `pfsense_create_vpn_wire_guard_peer_allowed_ip` with `confirm=True` (use parent_id from the parent resource):
    - `address`: `10.200.67.0`
    - `mask`: `24`
45. **List** using `pfsense_list_vpn_wire_guard_peer_allowed_i_ps` — verify resource exists (Needs peer parent_id)
46. **Bulk delete** using `pfsense_delete_vpn_wire_guard_peer_allowed_i_ps` with `confirm=True` — delete ALL resources in this collection
47. **List** using `pfsense_list_vpn_wire_guard_peer_allowed_i_ps` — verify collection is empty
48. **List** using `pfsense_list_status_dhcp_server_leases` — verify resource exists (Bulk delete DHCP leases — no create needed)
49. **Bulk delete** using `pfsense_delete_status_dhcp_server_leases` with `confirm=True` — delete ALL resources in this collection
50. **List** using `pfsense_list_status_dhcp_server_leases` — verify collection is empty
51. **List** using `pfsense_list_status_open_vpn_server_connections` — verify resource exists (Bulk delete OVPN connections — may be empty if no OVPN server)
52. **Bulk delete** using `pfsense_delete_status_open_vpn_server_connections` with `confirm=True` — delete ALL resources in this collection
53. **List** using `pfsense_list_status_open_vpn_server_connections` — verify collection is empty

**Important notes**:
Bulk delete VPN and status collections.
IPsec: create P1 → P1 enc → P2 → P2 enc → bulk delete in reverse.
OpenVPN: may need CA/cert chain for TLS mode servers.
WireGuard: tunnel → addresses + peers → allowed_ips → bulk delete in reverse.
Status endpoints (leases, connections) may be empty — just call DELETE anyway.

**Cleanup** (reverse order):
- No cleanup needed (read-only / settings restored)

**Expected outcome**: All 39 tools exercised successfully.
