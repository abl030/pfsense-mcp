## Task 17: Routing — Gateway, Gateway Group, Priority, Static Route, Apply

**task_id**: 17-routing--gateway-gateway-group-priority-static-rou

**Objective**: Exercise all tools in the routing subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (18):
- `pfsense_create_routing_gateway`
- `pfsense_list_routing_gateway_groups`
- `pfsense_get_routing_gateway`
- `pfsense_update_routing_gateway`
- `pfsense_delete_routing_gateway`
- `pfsense_create_routing_gateway_group`
- `pfsense_get_routing_gateway_group`
- `pfsense_update_routing_gateway_group`
- `pfsense_delete_routing_gateway_group`
- `pfsense_get_routing_gateway_default`
- `pfsense_update_routing_gateway_default`
- `pfsense_create_routing_static_route`
- `pfsense_list_routing_static_routes`
- `pfsense_get_routing_static_route`
- `pfsense_update_routing_static_route`
- `pfsense_delete_routing_static_route`
- `pfsense_get_routing_apply_status`
- `pfsense_routing_apply`

**Steps**:
1. **Create** using `pfsense_create_routing_gateway` with `confirm=True`:
    - `name`: `bt_sys17_gw`
    - `gateway`: `10.0.2.1`
    - `interface`: `wan`
    - `ipprotocol`: `inet`
    - `descr`: `Bank tester gateway`
    - `latencylow`: `200`
    - `latencyhigh`: `500`
    - `losslow`: `10`
    - `losshigh`: `20`
    - `loss_interval`: `2000`
    - `time_period`: `60000`
    - `interval`: `500`
    - `alert_interval`: `1000`
2. **List** using `pfsense_list_routing_gateway_groups` — verify the created resource appears
3. **Get** using `pfsense_get_routing_gateway` with the ID from the create response
4. **Update** using `pfsense_update_routing_gateway` with `confirm=True` — set `descr` to `Updated gateway`
5. **Get** again using `pfsense_get_routing_gateway` — verify `descr` was updated
6. **Create** using `pfsense_create_routing_gateway_group` with `confirm=True`:
    - `name`: `bt_sys17_gg`
    - `descr`: `Bank tester gateway group`
    - `priorities`: `[{'gateway': 'bt_sys17_gw', 'tier': 1}]`
7. **List** using `pfsense_list_routing_gateway_groups` — verify the created resource appears
8. **Get** using `pfsense_get_routing_gateway_group` with the ID from the create response
9. **Update** using `pfsense_update_routing_gateway_group` with `confirm=True` — set `descr` to `Updated group`
10. **Get** again using `pfsense_get_routing_gateway_group` — verify `descr` was updated
11. **Get settings** using `pfsense_get_routing_gateway_default` — note current value of `defaultgw4`
12. **Update settings** using `pfsense_update_routing_gateway_default` with `confirm=True` — set `defaultgw4` to `''`
13. **Get settings** again using `pfsense_get_routing_gateway_default` — verify `defaultgw4` was updated
14. **Create** using `pfsense_create_routing_static_route` with `confirm=True`:
    - `network`: `10.200.0.0/24`
    - `gateway`: `bt_sys17_gw`
    - `descr`: `bt_sys17_sr`
15. **List** using `pfsense_list_routing_static_routes` — verify the created resource appears
16. **Get** using `pfsense_get_routing_static_route` with the ID from the create response
17. **Update** using `pfsense_update_routing_static_route` with `confirm=True` — set `descr` to `Updated route`
18. **Get** again using `pfsense_get_routing_static_route` — verify `descr` was updated
19. **Check apply status** using `pfsense_get_routing_apply_status`
20. **Apply changes** using `pfsense_routing_apply` with `confirm=True`

**Important notes**:
Create gateway first. Gateway group and static route both reference it by name.
Cleanup: delete route → group → gateway. Apply after each mutation.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_routing_static_route` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_routing_gateway_group` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_routing_gateway` with `confirm=True` (ID from create step)

**Expected outcome**: All 18 tools exercised successfully.
