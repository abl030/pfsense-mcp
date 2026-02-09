## Task 52: Gateway Group Priority CRUD

**task_id**: 52-gateway-group-priority-crud

**Objective**: Exercise all tools in the routing subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (10):
- `pfsense_create_routing_gateway`
- `pfsense_delete_routing_gateway`
- `pfsense_create_routing_gateway_group`
- `pfsense_delete_routing_gateway_group`
- `pfsense_create_routing_gateway_group_priority`
- `pfsense_get_routing_gateway_group_priority`
- `pfsense_update_routing_gateway_group_priority`
- `pfsense_delete_routing_gateway_group_priority`
- `pfsense_get_routing_apply_status`
- `pfsense_routing_apply`

**Steps**:
1. **Create** using `pfsense_create_routing_gateway` with `confirm=True`:
    - `name`: `bt_sys52_gw`
    - `gateway`: `10.0.2.1`
    - `interface`: `wan`
    - `ipprotocol`: `inet`
    - `descr`: `Sprint 2 gateway`
    - `latencylow`: `200`
    - `latencyhigh`: `500`
    - `losslow`: `10`
    - `losshigh`: `20`
    - `loss_interval`: `2000`
    - `time_period`: `60000`
    - `interval`: `500`
    - `alert_interval`: `1000`
2. **Create** using `pfsense_create_routing_gateway_group` with `confirm=True`:
    - `name`: `bt_sys52_gg`
    - `descr`: `Sprint 2 gateway group`
    - `priorities`: `[{'gateway': 'bt_sys52_gw', 'tier': 1}]`
3. **Create** using `pfsense_create_routing_gateway_group_priority` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `gateway`: `bt_sys52_gw`
    - `tier`: `2`
4. **Get** using `pfsense_get_routing_gateway_group_priority` with the ID from the create response
5. **Update** using `pfsense_update_routing_gateway_group_priority` with `confirm=True` — set `tier` to `3`
6. **Get** again using `pfsense_get_routing_gateway_group_priority` — verify `tier` was updated
7. **Check apply status** using `pfsense_get_routing_apply_status`
8. **Apply changes** using `pfsense_routing_apply` with `confirm=True`

**Important notes**:
Gateway group priority is a sub-resource of gateway group.
Setup: create gateway → create gateway group (with initial priority) → CRUD additional priorities.
Cleanup: priority → group → gateway.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_routing_gateway_group_priority` with `confirm=True` (ID from create step)
- Delete setup resource at `/api/v2/routing/gateway/group` using `pfsense_delete_routing_gateway_group` with `confirm=True`
- Delete setup resource at `/api/v2/routing/gateway` using `pfsense_delete_routing_gateway` with `confirm=True`

**Expected outcome**: All 10 tools exercised successfully.
