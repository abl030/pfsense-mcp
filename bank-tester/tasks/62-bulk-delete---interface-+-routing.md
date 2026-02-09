## Task 62: Bulk Delete — Interface + Routing

**task_id**: 62-bulk-delete--interface-+-routing

**Objective**: Exercise all tools in the interface subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (26):
- `pfsense_create_interface_vlan`
- `pfsense_list_interface_vla_ns`
- `pfsense_delete_interface_vla_ns`
- `pfsense_create_interface_gre`
- `pfsense_list_interface_gr_es`
- `pfsense_delete_interface_gr_es`
- `pfsense_create_interface_group`
- `pfsense_list_interface_groups`
- `pfsense_delete_interface_groups`
- `pfsense_create_interface_lagg`
- `pfsense_list_interface_lag_gs`
- `pfsense_delete_interface_lag_gs`
- `pfsense_list_network_interfaces`
- `pfsense_delete_network_interfaces`
- `pfsense_create_routing_gateway`
- `pfsense_list_routing_gateways`
- `pfsense_delete_routing_gateways`
- `pfsense_create_routing_gateway_group`
- `pfsense_list_routing_gateway_groups`
- `pfsense_delete_routing_gateway_groups`
- `pfsense_create_routing_gateway_group_priority`
- `pfsense_list_routing_gateway_group_priorities`
- `pfsense_delete_routing_gateway_group_priorities`
- `pfsense_create_routing_static_route`
- `pfsense_list_routing_static_routes`
- `pfsense_delete_routing_static_routes`

**Steps**:
1. **Create** a test resource using `pfsense_create_interface_vlan` with `confirm=True`:
    - `if`: `em2`
    - `tag`: `300`
    - `pcp`: `0`
2. **List** using `pfsense_list_interface_vla_ns` — verify resource exists
3. **Bulk delete** using `pfsense_delete_interface_vla_ns` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
4. **List** using `pfsense_list_interface_vla_ns` — verify collection is empty
5. **Create** a test resource using `pfsense_create_interface_gre` with `confirm=True`:
    - `if`: `wan`
    - `remote_addr`: `198.51.100.1`
    - `tunnel_local_addr`: `10.255.0.1`
    - `tunnel_remote_addr`: `10.255.0.2`
    - `tunnel_remote_addr6`: ``
6. **List** using `pfsense_list_interface_gr_es` — verify resource exists
7. **Bulk delete** using `pfsense_delete_interface_gr_es` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
8. **List** using `pfsense_list_interface_gr_es` — verify collection is empty
9. **Create** a test resource using `pfsense_create_interface_group` with `confirm=True`:
    - `ifname`: `bt62grp`
    - `members`: `['wan']`
10. **List** using `pfsense_list_interface_groups` — verify resource exists
11. **Bulk delete** using `pfsense_delete_interface_groups` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
12. **List** using `pfsense_list_interface_groups` — verify collection is empty
13. **Create** a test resource using `pfsense_create_interface_lagg` with `confirm=True`:
    - `members`: `['em2']`
    - `proto`: `none`
14. **List** using `pfsense_list_interface_lag_gs` — verify resource exists
15. **Bulk delete** using `pfsense_delete_interface_lag_gs` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
16. **List** using `pfsense_list_interface_lag_gs` — verify collection is empty
17. **List** using `pfsense_list_network_interfaces` — verify resource exists (Bulk delete network interfaces — careful, may include system interfaces)
18. **Bulk delete** using `pfsense_delete_network_interfaces` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
19. **List** using `pfsense_list_network_interfaces` — verify collection is empty
20. **Create** a test resource using `pfsense_create_routing_gateway` with `confirm=True`:
    - `name`: `bt_bd62_gw`
    - `gateway`: `10.0.2.1`
    - `interface`: `wan`
    - `ipprotocol`: `inet`
    - `latencylow`: `200`
    - `latencyhigh`: `500`
    - `losslow`: `10`
    - `losshigh`: `20`
    - `loss_interval`: `2000`
    - `time_period`: `60000`
    - `interval`: `500`
    - `alert_interval`: `1000`
21. **List** using `pfsense_list_routing_gateways` — verify resource exists
22. **Bulk delete** using `pfsense_delete_routing_gateways` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
23. **List** using `pfsense_list_routing_gateways` — verify collection is empty
24. **Create** a test resource using `pfsense_create_routing_gateway_group` with `confirm=True`:
    - `name`: `bt_bd62_gg`
    - `descr`: `bulk delete group`
    - `priorities`: `[{'gateway': 'bt_bd62_gw', 'tier': 1}]`
25. **List** using `pfsense_list_routing_gateway_groups` — verify resource exists (Needs gateway created first)
26. **Bulk delete** using `pfsense_delete_routing_gateway_groups` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
27. **List** using `pfsense_list_routing_gateway_groups` — verify collection is empty
28. **Create** a test resource using `pfsense_create_routing_gateway_group_priority` with `confirm=True` (use parent_id from the parent resource):
    - `gateway`: `bt_bd62_gw`
    - `tier`: `2`
29. **List** using `pfsense_list_routing_gateway_group_priorities` — verify resource exists (Needs gateway group parent_id)
30. **Bulk delete** using `pfsense_delete_routing_gateway_group_priorities` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
31. **List** using `pfsense_list_routing_gateway_group_priorities` — verify collection is empty
32. **Create** a test resource using `pfsense_create_routing_static_route` with `confirm=True`:
    - `network`: `10.200.0.0/24`
    - `gateway`: `bt_bd62_gw`
33. **List** using `pfsense_list_routing_static_routes` — verify resource exists (Needs gateway name)
34. **Bulk delete** using `pfsense_delete_routing_static_routes` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
35. **List** using `pfsense_list_routing_static_routes` — verify collection is empty

**Important notes**:
Bulk delete interface and routing collections.
Order: create gateway → group → priorities → static routes.
Bulk delete: priorities → group → static routes → gateway.
VLANs use em2. LAGGs use em2. Network interfaces bulk delete should be last.

**Cleanup** (reverse order):
- No cleanup needed (read-only / settings restored)

**Expected outcome**: All 26 tools exercised successfully.
