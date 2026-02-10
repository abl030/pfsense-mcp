## Task 60: Bulk Delete — Firewall Core

**task_id**: 60-bulk-delete--firewall-core

**Objective**: Exercise all tools in the firewall subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (23):
- `pfsense_create_firewall_alias`
- `pfsense_list_firewall_aliases`
- `pfsense_delete_firewall_aliases`
- `pfsense_create_firewall_rule`
- `pfsense_list_firewall_rules`
- `pfsense_delete_firewall_rules`
- `pfsense_create_firewall_nat_port_forward`
- `pfsense_list_firewall_nat_port_forwards`
- `pfsense_delete_firewall_nat_port_forwards`
- `pfsense_create_firewall_nat_outbound_mapping`
- `pfsense_list_firewall_nat_outbound_mappings`
- `pfsense_delete_firewall_nat_outbound_mappings`
- `pfsense_create_firewall_nat_one_to_one_mapping`
- `pfsense_list_firewall_nat_one_to_one_mappings`
- `pfsense_delete_firewall_nat_one_to_one_mappings`
- `pfsense_create_firewall_schedule`
- `pfsense_list_firewall_schedules`
- `pfsense_delete_firewall_schedules`
- `pfsense_create_firewall_virtual_ip`
- `pfsense_list_firewall_virtual_ips`
- `pfsense_delete_firewall_virtual_ips`
- `pfsense_list_firewall_states`
- `pfsense_delete_firewall_states`

**Steps**:
1. **Create** a test resource using `pfsense_create_firewall_alias` with `confirm=True`:
    - `name`: `bt_bd60_alias`
    - `type_`: `host`
    - `address`: `['10.99.60.1']`
2. **List** using `pfsense_list_firewall_aliases` — verify resource exists
3. **Bulk delete** using `pfsense_delete_firewall_aliases` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
4. **List** using `pfsense_list_firewall_aliases` — verify collection is empty
5. **Create** a test resource using `pfsense_create_firewall_rule` with `confirm=True`:
    - `type_`: `pass`
    - `interface`: `wan`
    - `ipprotocol`: `inet`
    - `protocol`: `tcp`
    - `source`: `any`
    - `destination`: `any`
    - `descr`: `bt_bd60_rule`
6. **List** using `pfsense_list_firewall_rules` — verify resource exists
7. **Bulk delete** using `pfsense_delete_firewall_rules` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
8. **List** using `pfsense_list_firewall_rules` — verify collection is empty
9. **Create** a test resource using `pfsense_create_firewall_nat_port_forward` with `confirm=True`:
    - `interface`: `wan`
    - `protocol`: `tcp`
    - `source`: `any`
    - `destination`: `wan:ip`
    - `destination_port`: `8060`
    - `target`: `10.99.60.1`
    - `local_port`: `80`
    - `associated_rule_id`: ``
10. **List** using `pfsense_list_firewall_nat_port_forwards` — verify resource exists
11. **Bulk delete** using `pfsense_delete_firewall_nat_port_forwards` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
12. **List** using `pfsense_list_firewall_nat_port_forwards` — verify collection is empty
13. **Create** a test resource using `pfsense_create_firewall_nat_outbound_mapping` with `confirm=True`:
    - `interface`: `wan`
    - `protocol`: `tcp`
    - `source`: `any`
    - `destination`: `any`
    - `target`: `wan:ip`
14. **List** using `pfsense_list_firewall_nat_outbound_mappings` — verify resource exists
15. **Bulk delete** using `pfsense_delete_firewall_nat_outbound_mappings` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
16. **List** using `pfsense_list_firewall_nat_outbound_mappings` — verify collection is empty
17. **Create** a test resource using `pfsense_create_firewall_nat_one_to_one_mapping` with `confirm=True`:
    - `interface`: `wan`
    - `external`: `10.99.60.2`
    - `source`: `10.0.0.0/8`
    - `destination`: `any`
18. **List** using `pfsense_list_firewall_nat_one_to_one_mappings` — verify resource exists
19. **Bulk delete** using `pfsense_delete_firewall_nat_one_to_one_mappings` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
20. **List** using `pfsense_list_firewall_nat_one_to_one_mappings` — verify collection is empty
21. **Create** a test resource using `pfsense_create_firewall_schedule` with `confirm=True`:
    - `name`: `bt_bd60_sched`
    - `timerange`: `[{'month': '1,2,3', 'day': '1,2,3', 'hour': '0:00-23:59', 'position': []}]`
22. **List** using `pfsense_list_firewall_schedules` — verify resource exists
23. **Bulk delete** using `pfsense_delete_firewall_schedules` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
24. **List** using `pfsense_list_firewall_schedules` — verify collection is empty
25. **Create** a test resource using `pfsense_create_firewall_virtual_ip` with `confirm=True`:
    - `mode`: `ipalias`
    - `interface`: `wan`
    - `subnet`: `10.99.60.100`
    - `subnet_bits`: `32`
26. **List** using `pfsense_list_firewall_virtual_ips` — verify resource exists
27. **Bulk delete** using `pfsense_delete_firewall_virtual_ips` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
28. **List** using `pfsense_list_firewall_virtual_ips` — verify collection is empty
29. **List** using `pfsense_list_firewall_states` — verify resource exists (Bulk clear all firewall states — no create needed, states auto-generate)
30. **Bulk delete** using `pfsense_delete_firewall_states` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
31. **List** using `pfsense_list_firewall_states` — verify collection is empty

**Important notes**:
Bulk delete all resources in each firewall collection.
Pattern: create resource → list → bulk DELETE → verify empty.
Firewall states auto-exist — just bulk delete without create.
WARNING: This deletes ALL aliases, rules, NAT entries, schedules, VIPs.
Run on an ephemeral/test VM only.

**Cleanup** (reverse order):
- No cleanup needed (read-only / settings restored)

**Expected outcome**: All 23 tools exercised successfully.
