## Task 72: Sprint 1-4 Failure Pattern Diagnosis

**task_id**: 72-sprint-failure-diagnosis

**Objective**: Attempt each operation below. Some will succeed, some will fail. For EVERY failure, provide an independent root cause diagnosis. Classify each into exactly one layer:

- **generator_bug**: The MCP tool generator produced incorrect schemas, parameter types, defaults, or docstrings. A fix to the generator would prevent this.
- **pfsense_api_bug**: The pfSense REST API itself has a bug or inconsistency. Cannot be fixed on our side.
- **openapi_spec_issue**: The OpenAPI spec describes the API incorrectly. Fixable via generator workarounds.
- **test_design_bug**: The test values or setup are wrong. Not a real bug.
- **model_behavior**: The AI consumer made an incorrect guess. Better docstrings could help.
- **expected_behavior**: Working as designed — consumer just needs to learn the pattern.

For each diagnosis, explain your reasoning. What evidence did you use? What alternative explanations did you consider?

**Tools to exercise**: See each part below.

---

### Part 1: PUT/Replace Roundtrip Failures

These operations GET the current collection, then PUT the exact same data back. A working API should accept its own output as input (roundtrip invariant).

1. **List** FreeRADIUS clients: `pfsense_list_services_free_radius_clients`
2. **Replace** with same data: `pfsense_replace_services_free_radius_clients` with `items` = the data from step 1, `confirm=True`
3. **Diagnose** the result.

4. **List** FreeRADIUS interfaces: `pfsense_list_services_free_radius_interfaces`
5. **Replace** with same data: `pfsense_replace_services_free_radius_interfaces`, `confirm=True`
6. **Diagnose**.

7. **List** FreeRADIUS users: `pfsense_list_services_free_radius_users`
8. **Replace** with same data: `pfsense_replace_services_free_radius_users`, `confirm=True`
9. **Diagnose**.

10. **List** NTP time servers: `pfsense_list_services_ntp_time_servers`
11. **Replace** with same data: `pfsense_replace_services_ntp_time_servers`, `confirm=True`
12. **Diagnose**.

13. **List** service watchdogs: `pfsense_list_services_service_watchdogs`
14. **Replace** with same data: `pfsense_replace_services_service_watchdogs`, `confirm=True`
15. **Diagnose**.

16. **List** BIND access lists: `pfsense_list_services_bind_access_lists`
17. **Replace** with same data: `pfsense_replace_services_bind_access_lists`, `confirm=True`
18. **Diagnose**.

19. **List** user groups: `pfsense_list_user_groups`
20. **Replace** with same data: `pfsense_replace_user_groups`, `confirm=True`
21. **Diagnose**.

### Part 2: CRL PATCH — Non-Editable Fields

22. **List** CAs: `pfsense_list_system_certificate_authorities` — find any CA with `descr` containing `bt_` or use the first one.
23. **Create** a CRL: `pfsense_create_system_crl` with `caref` from step 22, `descr`: `bt_diag_crl`, `method`: `internal`, `lifetime`: `3650`, `serial`: `0`, `confirm=True`
24. **Update** the CRL: `pfsense_update_system_crl` — try changing `descr` to `bt_diag_crl_updated`, `confirm=True`
25. **Diagnose** the result. Try other fields too (`lifetime`, `serial`). Are ANY fields editable?
26. **Cleanup**: Delete the CRL with `confirm=True`.

### Part 3: Network Interface PATCH ID Typing

27. **Create** a network interface: `pfsense_create_network_interface` with `if_device`: `em2`, `descr`: `bt_diag_if`, `typev4`: `staticv4`, `ipaddr`: `192.168.72.1`, `subnet`: `24`, `enable`: `true`, `confirm=True`
28. **Apply**: `pfsense_interface_apply` with `confirm=True`
29. Note the returned interface ID (should be something like `opt1`).
30. **Update** the interface: `pfsense_update_network_interface` with the ID from step 29, change `descr` to `bt_diag_if_updated`, `confirm=True`
31. **Diagnose** the result. Look carefully at the `id` parameter type. Does the tool accept string IDs like `opt1`?
32. **Cleanup**: Delete the interface, apply.

### Part 4: ARP Table Interface Naming

33. **List** ARP table: `pfsense_list_diagnostics_arp_table`
34. Note how the `interface` field is formatted in the response (device name like `em0` vs display name like `WAN`).
35. **Bulk delete** with `pfsense_delete_diagnostics_arp_table` using `query={"interface": "em0"}`, `confirm=True`
36. **Diagnose**: Did the filter work? If not, what format does the `interface` field actually use? Try the correct format.

### Part 5: Bulk DELETE Query Requirements

37. **Create** a firewall alias: `pfsense_create_firewall_alias` with `name`: `bt_diag72_alias`, `type`: `host`, `address`: `["10.0.0.1"]`, `confirm=True`
38. **Bulk delete** with NO query: `pfsense_delete_firewall_aliases` with just `confirm=True` (no `query` parameter)
39. **Diagnose** the error. What does the API require? Is this documented in the tool's docstring?
40. **Retry** with a query filter to clean up the test alias.

### Part 6: Sub-Resource Minimum Constraints

41. **Create** a firewall schedule: `pfsense_create_firewall_schedule` with `name`: `bt_diag72_sched`, `timerange`: `[{"month": "1", "day": "1", "hour": "0:00-23:59", "position": "0,1,2,3,4,5,6", "rangedescr": "bt_test_range"}]`, `confirm=True`
42. **Bulk delete** all time ranges: `pfsense_delete_firewall_schedule_time_ranges` with `parent_id` from step 41, `query={"rangedescr": "bt_test_range"}`, `confirm=True`
43. **Diagnose** the result. Can you delete the last time range from a schedule?
44. **Cleanup**: Delete the schedule with `confirm=True`.

### Part 7: IPsec Encryption Minimum + WireGuard Key Validation

45. **Create** IPsec Phase 1: `pfsense_create_vpni_psec_phase1` with `iketype`: `ikev2`, `protocol`: `inet`, `interface`: `wan`, `remote_gateway`: `10.99.99.72`, `authentication_method`: `pre_shared_key`, `pre_shared_key`: `DiagTest72PSK`, `myid_type`: `myaddress`, `peerid_type`: `peeraddress`, `descr`: `bt_diag72_p1`, `confirm=True`
46. **List** the encryptions: `pfsense_list_vpni_psec_phase1_encryptions` with `parent_id` from step 45.
47. **Bulk delete** all encryptions: `pfsense_delete_vpni_psec_phase1_encryptions` with `parent_id` from step 45, `query={"encryption_algorithm_name": "aes"}`, `confirm=True`
48. **Diagnose** the result. What happens when you try to remove the last encryption from a Phase 1?

49. **Create** WireGuard tunnel: `pfsense_create_vpn_wire_guard_tunnel` with `name`: `bt_diag72_wg`, `privatekey`: `dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleTE=`, `confirm=True`
50. **Diagnose** the result. Does WireGuard accept any base64 string as a private key, or does it validate the key format?

51. **Cleanup**: Delete Phase 1, apply IPsec. Delete WireGuard tunnel if created, apply WireGuard.

### Part 8: System Package Install (Timeout Test)

52. **List** available packages: `pfsense_list_system_packages` with `query={"name": "pfSense-pkg-Status_Traffic_Totals"}`
53. **Install** a small package: `pfsense_create_system_package` with `name`: `pfSense-pkg-Status_Traffic_Totals`, `confirm=True`
54. **Diagnose** the result. Did it succeed, timeout, or fail? How long did it take?
55. If it installed, **delete** it: `pfsense_delete_system_package` with the package id, `confirm=True`

### Final Analysis

After completing all parts, provide a comprehensive **Root Cause Analysis**:

1. List EVERY failure with its root cause classification
2. Group by root cause layer
3. Identify systemic patterns
4. For each `generator_bug` or `openapi_spec_issue`, explain exactly what change to the generator would fix it
5. For each `pfsense_api_bug`, state whether any generator-side workaround is possible
6. Rank by impact — which fixes would eliminate the most failures across the entire tool suite?

**Cleanup** all created resources in reverse order when done.
