## Task 35: Status Endpoints — All Read-Only

**task_id**: 35-status-endpoints--all-read-only

**Objective**: Exercise all tools in the status subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (16):
- `pfsense_get_status_system`
- `pfsense_list_status_services`
- `pfsense_list_status_gateways`
- `pfsense_list_status_interfaces`
- `pfsense_get_status_carp`
- `pfsense_update_status_carp`
- `pfsense_list_status_dhcp_server_leases`
- `pfsense_list_status_ipsec_sas`
- `pfsense_list_status_openvpn_servers`
- `pfsense_list_status_openvpn_clients`
- `pfsense_list_status_logs_system`
- `pfsense_list_status_logs_firewall`
- `pfsense_list_status_logs_dhcp`
- `pfsense_list_status_logs_auth`
- `pfsense_get_status_logs_settings`
- `pfsense_update_status_logs_settings`

**Steps**:
1. **Read** using `pfsense_get_status_system`
2. **Read** using `pfsense_list_status_services`
3. **Read** using `pfsense_list_status_gateways`
4. **Read** using `pfsense_list_status_interfaces`
5. **Get settings** using `pfsense_get_status_carp` — note current value of `maintenance_mode`
6. **Update settings** using `pfsense_update_status_carp` with `confirm=True` — set `maintenance_mode` to `True` (also include: `enable=True`)
7. **Get settings** again using `pfsense_get_status_carp` — verify `maintenance_mode` was updated
8. **Restore** using `pfsense_update_status_carp` with `confirm=True` — set `maintenance_mode` back to `False`
9. **Read** using `pfsense_list_status_dhcp_server_leases`
10. **Read** using `pfsense_list_status_ipsec_sas`
11. **Read** using `pfsense_list_status_openvpn_servers`
12. **Read** using `pfsense_list_status_openvpn_clients`
13. **Read** using `pfsense_list_status_logs_system` (Use limit parameter to avoid huge responses)
14. **Read** using `pfsense_list_status_logs_firewall`
15. **Read** using `pfsense_list_status_logs_dhcp`
16. **Read** using `pfsense_list_status_logs_auth`
17. **Get settings** using `pfsense_get_status_logs_settings` — note current value of `logall`
18. **Update settings** using `pfsense_update_status_logs_settings` with `confirm=True` — set `logall` to `True`
19. **Get settings** again using `pfsense_get_status_logs_settings` — verify `logall` was updated

**Important notes**:
All status endpoints are read-only (GET only), except CARP (PATCH) and log settings (PATCH).
Use limit parameter on log endpoints.

**Cleanup** (reverse order):
- No cleanup needed (read-only / settings restored)

**Expected outcome**: All 16 tools exercised successfully.
