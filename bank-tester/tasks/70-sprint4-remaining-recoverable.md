## Task 70: Sprint 4 — Remaining Recoverable Tools

**task_id**: 70-sprint4-remaining-recoverable

**Objective**: Exercise the 6 remaining tools that are not covered by any previous task. These require specific setup sequences.

**Tools to exercise** (6):
- `pfsense_get_services_dhcp_server`
- `pfsense_create_services_dhcp_server`
- `pfsense_update_services_dhcp_server`
- `pfsense_delete_services_dhcp_server`
- `pfsense_delete_diagnostics_arp_table`
- `pfsense_delete_system_restapi_access_list`

---

### Part 1: DHCP Server CRUD (4 tools)

DHCP servers are keyed by interface name. The golden image already has DHCP configured on "lan". To test full CRUD, you need to:

1. **GET the existing LAN DHCP server**: Call `pfsense_get_services_dhcp_server` with `id="lan"`. This exercises the GET tool and confirms DHCP is running.

2. **Create a network interface for em2**: Before creating a DHCP server on a new interface, you must assign em2 as a network interface. Call `pfsense_create_network_interface` with:
   - `if_device`: `"em2"`
   - `descr`: `"bt_s4_opt"`
   - `typev4`: `"staticv4"`
   - `ipaddr`: `"192.168.70.1"`
   - `subnet`: `24`
   - `enable`: `true`
   - `confirm`: `true`
   Then call `pfsense_interface_apply` to apply the interface.

3. **Create a DHCP server on the new interface**: Call `pfsense_create_services_dhcp_server` with:
   - `interface`: the interface ID returned from step 2 (it will be something like `"opt1"` or `"opt2"`)
   - `enable`: `true`
   - `range_from`: `"192.168.70.100"`
   - `range_to`: `"192.168.70.200"`
   - `confirm`: `true`
   Then call `pfsense_services_dhcp_server_apply`.

4. **Update the DHCP server**: Call `pfsense_update_services_dhcp_server` with:
   - `id`: the interface ID from step 2
   - `domain`: `"bt-sprint4.test"`
   - `confirm`: `true`
   Then call `pfsense_services_dhcp_server_apply`.

5. **Delete the DHCP server**: Call `pfsense_delete_services_dhcp_server` with:
   - `id`: the interface ID from step 2
   - `apply`: `true`
   - `confirm`: `true`

6. **Cleanup**: Delete the network interface created in step 2:
   - Call `pfsense_delete_network_interface` with the ID from step 2 and `confirm=true`
   - Call `pfsense_interface_apply`

### Part 2: Bulk Delete ARP Table (1 tool)

The ARP table rebuilds automatically from network traffic, so clearing it is safe.

1. **List ARP entries first**: Call `pfsense_list_diagnostics_arp_table_entries` to see current entries.

2. **Bulk delete ARP table**: Call `pfsense_delete_diagnostics_arp_table` with:
   - `query`: `{"type": "dynamic"}` (filter to only dynamic entries — don't delete static ARP if any exist)
   - `confirm`: `true`

   Note: This is a bulk DELETE and requires at least one `query` parameter. If `type` doesn't work as a filter, try `query={"interface": "em0"}` instead.

3. **Verify ARP table rebuilds**: Call `pfsense_list_diagnostics_arp_table_entries` again — entries will reappear as the system communicates on the network.

### Part 3: Bulk Delete REST API Access List (1 tool)

This is the bulk (plural) DELETE for the REST API access list. Be careful not to delete entries that would lock you out.

1. **List current access list**: Call `pfsense_list_system_restapi_access_list_entries` to see existing entries.

2. **Create a test entry**: Call `pfsense_create_system_restapi_access_list_entry` with:
   - `type`: `"allow"`
   - `network`: `"10.99.99.0/24"`
   - `descr`: `"bt_s4_test_acl"`
   - `confirm`: `true`

3. **Bulk delete the test entry only**: Call `pfsense_delete_system_restapi_access_list` with:
   - `query`: `{"descr": "bt_s4_test_acl"}`
   - `confirm`: `true`

   **CRITICAL**: Use the query filter to delete ONLY the test entry. Do NOT delete all entries or you will lose API access.

4. **Verify**: Call `pfsense_list_system_restapi_access_list_entries` again to confirm the test entry is gone and the original entries remain.
