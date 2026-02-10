## Task 38: Additional Status & Read-Only Endpoints

**task_id**: 38-additional-status--read-only-endpoints

**Objective**: Exercise all tools in the status subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (18):
- `pfsense_get_status_ipsec_child_sa`
- `pfsense_list_status_ipsec_child_sas`
- `pfsense_list_status_logs_openvpn`
- `pfsense_list_status_logs_packages_restapi`
- `pfsense_list_status_dhcp_server_leases`
- `pfsense_list_interface_bridges`
- `pfsense_list_auth_keys`
- `pfsense_list_system_packages`
- `pfsense_list_system_certificates`
- `pfsense_list_system_certificate_authorities`
- `pfsense_list_system_crls`
- `pfsense_list_diagnostics_tables`
- `pfsense_list_diagnostics_config_history_revisions`
- `pfsense_list_network_interfaces`
- `pfsense_list_users`
- `pfsense_list_services_acme_account_key_registrations`
- `pfsense_list_services_acme_certificate_issuances`
- `pfsense_list_services_acme_certificate_renewals`

**Steps**:
1. **Read** using `pfsense_get_status_ipsec_child_sa` (Get singular IPsec child SA)
2. **Read** using `pfsense_list_status_ipsec_child_sas` (List IPsec child SAs)
3. **Read** using `pfsense_list_status_logs_openvpn` (OpenVPN logs — use limit parameter)
4. **Read** using `pfsense_list_status_logs_packages_restapi` (REST API package logs)
5. **Read** using `pfsense_list_status_dhcp_server_leases` (DHCP server leases (also tested in task 35))
6. **Read** using `pfsense_list_interface_bridges` (List bridges (plural, read-only))
7. **Read** using `pfsense_list_auth_keys` (List API keys (read-only plural))
8. **Read** using `pfsense_list_system_packages` (List installed packages (plural))
9. **Read** using `pfsense_list_system_certificates` (List all certificates (plural))
10. **Read** using `pfsense_list_system_certificate_authorities` (List all CAs (plural))
11. **Read** using `pfsense_list_system_crls` (List all CRLs (plural))
12. **Read** using `pfsense_list_diagnostics_tables` (List pf tables (plural))
13. **Read** using `pfsense_list_diagnostics_config_history_revisions` (List config history revisions (plural))
14. **Read** using `pfsense_list_network_interfaces` (List all network interfaces (top-level plural))
15. **Read** using `pfsense_list_users` (List all users (top-level plural))
16. **Read** using `pfsense_list_services_acme_account_key_registrations` (List ACME registrations)
17. **Read** using `pfsense_list_services_acme_certificate_issuances` (List ACME certificate issuances)
18. **Read** using `pfsense_list_services_acme_certificate_renewals` (List ACME certificate renewals)

**Important notes**:
All read-only endpoints. Use limit parameter on log endpoints.

**Cleanup** (reverse order):
- No cleanup needed (read-only / settings restored)

**Expected outcome**: All 18 tools exercised successfully.
