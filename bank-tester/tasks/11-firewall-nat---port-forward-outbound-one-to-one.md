## Task 11: Firewall NAT — Port Forward, Outbound, One-to-One

**task_id**: 11-firewall-nat--port-forward-outbound-one-to-one

**Objective**: Exercise all tools in the firewall/nat subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (19):
- `pfsense_create_firewall_nat_port_forward`
- `pfsense_list_firewall_nat_port_forwards`
- `pfsense_get_firewall_nat_port_forward`
- `pfsense_update_firewall_nat_port_forward`
- `pfsense_delete_firewall_nat_port_forward`
- `pfsense_create_firewall_nat_outbound_mapping`
- `pfsense_list_firewall_nat_outbound_mappings`
- `pfsense_get_firewall_nat_outbound_mapping`
- `pfsense_update_firewall_nat_outbound_mapping`
- `pfsense_delete_firewall_nat_outbound_mapping`
- `pfsense_get_firewall_nat_outbound_mode`
- `pfsense_update_firewall_nat_outbound_mode`
- `pfsense_create_firewall_nat_one_to_one_mapping`
- `pfsense_list_firewall_nat_one_to_one_mappings`
- `pfsense_get_firewall_nat_one_to_one_mapping`
- `pfsense_update_firewall_nat_one_to_one_mapping`
- `pfsense_delete_firewall_nat_one_to_one_mapping`
- `pfsense_get_firewall_apply_status`
- `pfsense_firewall_apply`

**Steps**:
1. **Create** using `pfsense_create_firewall_nat_port_forward` with `confirm=True`:
    - `interface`: `wan`
    - `protocol`: `tcp`
    - `source`: `any`
    - `destination`: `wan:ip`
    - `destination_port`: `8080`
    - `target`: `10.99.99.1`
    - `local_port`: `80`
    - `associated_rule_id`: ``
    - `descr`: `bt_sys11_pf`
2. **List** using `pfsense_list_firewall_nat_port_forwards` — verify the created resource appears
3. **Get** using `pfsense_get_firewall_nat_port_forward` with the ID from the create response
4. **Update** using `pfsense_update_firewall_nat_port_forward` with `confirm=True` — set `descr` to `Updated port forward`
5. **Get** again using `pfsense_get_firewall_nat_port_forward` — verify `descr` was updated
6. **Create** using `pfsense_create_firewall_nat_outbound_mapping` with `confirm=True`:
    - `interface`: `wan`
    - `protocol`: `tcp`
    - `source`: `any`
    - `destination`: `any`
    - `target`: `wan:ip`
    - `descr`: `bt_sys11_outbound`
7. **List** using `pfsense_list_firewall_nat_outbound_mappings` — verify the created resource appears
8. **Get** using `pfsense_get_firewall_nat_outbound_mapping` with the ID from the create response
9. **Update** using `pfsense_update_firewall_nat_outbound_mapping` with `confirm=True` — set `descr` to `Updated outbound`
10. **Get** again using `pfsense_get_firewall_nat_outbound_mapping` — verify `descr` was updated
11. **Get settings** using `pfsense_get_firewall_nat_outbound_mode` — note current value of `mode`
12. **Update settings** using `pfsense_update_firewall_nat_outbound_mode` with `confirm=True` — set `mode` to `'hybrid'`
13. **Get settings** again using `pfsense_get_firewall_nat_outbound_mode` — verify `mode` was updated
14. **Create** using `pfsense_create_firewall_nat_one_to_one_mapping` with `confirm=True`:
    - `interface`: `wan`
    - `external`: `10.99.99.1`
    - `source`: `10.0.0.0/8`
    - `destination`: `any`
    - `descr`: `bt_sys11_1to1`
15. **List** using `pfsense_list_firewall_nat_one_to_one_mappings` — verify the created resource appears
16. **Get** using `pfsense_get_firewall_nat_one_to_one_mapping` with the ID from the create response
17. **Update** using `pfsense_update_firewall_nat_one_to_one_mapping` with `confirm=True` — set `descr` to `Updated 1:1`
18. **Get** again using `pfsense_get_firewall_nat_one_to_one_mapping` — verify `descr` was updated
19. **Check apply status** using `pfsense_get_firewall_apply_status`
20. **Apply changes** using `pfsense_firewall_apply` with `confirm=True`

**Important notes**:
NAT outbound mode must be set to hybrid before creating outbound mappings.
Apply firewall after each mutation.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_firewall_nat_one_to_one_mapping` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_firewall_nat_outbound_mapping` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_firewall_nat_port_forward` with `confirm=True` (ID from create step)

**Expected outcome**: All 19 tools exercised successfully.
