## Task 13: Firewall Traffic Shaper, Limiter, Queues

**task_id**: 13-firewall-traffic-shaper-limiter-queues

**Objective**: Exercise all tools in the firewall/traffic_shaper subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (27):
- `pfsense_create_firewall_traffic_shaper`
- `pfsense_list_firewall_traffic_shapers`
- `pfsense_get_firewall_traffic_shaper`
- `pfsense_update_firewall_traffic_shaper`
- `pfsense_delete_firewall_traffic_shaper`
- `pfsense_create_firewall_traffic_shaper_queue`
- `pfsense_list_firewall_traffic_shaper_queues`
- `pfsense_get_firewall_traffic_shaper_queue`
- `pfsense_update_firewall_traffic_shaper_queue`
- `pfsense_delete_firewall_traffic_shaper_queue`
- `pfsense_create_firewall_traffic_shaper_limiter`
- `pfsense_list_firewall_traffic_shaper_limiters`
- `pfsense_get_firewall_traffic_shaper_limiter`
- `pfsense_update_firewall_traffic_shaper_limiter`
- `pfsense_delete_firewall_traffic_shaper_limiter`
- `pfsense_create_firewall_traffic_shaper_limiter_bandwidth`
- `pfsense_list_firewall_traffic_shaper_limiter_bandwidths`
- `pfsense_get_firewall_traffic_shaper_limiter_bandwidth`
- `pfsense_update_firewall_traffic_shaper_limiter_bandwidth`
- `pfsense_delete_firewall_traffic_shaper_limiter_bandwidth`
- `pfsense_create_firewall_traffic_shaper_limiter_queue`
- `pfsense_list_firewall_traffic_shaper_limiter_queues`
- `pfsense_get_firewall_traffic_shaper_limiter_queue`
- `pfsense_update_firewall_traffic_shaper_limiter_queue`
- `pfsense_delete_firewall_traffic_shaper_limiter_queue`
- `pfsense_get_firewall_apply_status`
- `pfsense_firewall_apply`

**Steps**:
1. **Create** using `pfsense_create_firewall_traffic_shaper` with `confirm=True`:
    - `bandwidth`: `100`
    - `bandwidthtype`: `Mb`
    - `interface`: `wan`
    - `scheduler`: `HFSC`
    - `enabled`: `False`
    - `qlimit`: `50`
    - `queue`: `[]`
    - `tbrconfig`: `1`
2. **List** using `pfsense_list_firewall_traffic_shapers` — verify the created resource appears
3. **Get** using `pfsense_get_firewall_traffic_shaper` with the ID from the create response
4. **Update** using `pfsense_update_firewall_traffic_shaper` with `confirm=True` — set `bandwidth` to `200`
5. **Get** again using `pfsense_get_firewall_traffic_shaper` — verify `bandwidth` was updated
6. **Create** using `pfsense_create_firewall_traffic_shaper_queue` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `name`: `bt_sys13_tsq`
    - `qlimit`: `50`
    - `bandwidth`: `100`
    - `upperlimit_m2`: ``
    - `realtime_m2`: ``
    - `linkshare_m2`: `10%`
7. **List** using `pfsense_list_firewall_traffic_shaper_queues` — verify the created resource appears
8. **Get** using `pfsense_get_firewall_traffic_shaper_queue` with the ID from the create response
9. **Update** using `pfsense_update_firewall_traffic_shaper_queue` with `confirm=True` — set `qlimit` to `100`
10. **Get** again using `pfsense_get_firewall_traffic_shaper_queue` — verify `qlimit` was updated
11. **Create** using `pfsense_create_firewall_traffic_shaper_limiter` with `confirm=True`:
    - `aqm`: `droptail`
    - `name`: `bt_sys13_lim`
    - `sched`: `wf2q+`
    - `bandwidth`: `[{'bw': 100, 'bwscale': 'Mb', 'schedule': 'none'}]`
    - `buckets`: `16`
    - `ecn`: `False`
    - `enabled`: `False`
    - `mask`: `none`
    - `maskbits`: `1`
    - `maskbitsv6`: `1`
    - `queue`: `[]`
12. **List** using `pfsense_list_firewall_traffic_shaper_limiters` — verify the created resource appears
13. **Get** using `pfsense_get_firewall_traffic_shaper_limiter` with the ID from the create response
14. **Update** using `pfsense_update_firewall_traffic_shaper_limiter` with `confirm=True` — set `buckets` to `32`
15. **Get** again using `pfsense_get_firewall_traffic_shaper_limiter` — verify `buckets` was updated
16. **Create** using `pfsense_create_firewall_traffic_shaper_limiter_bandwidth` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `bw`: `50`
    - `bwscale`: `Mb`
17. **List** using `pfsense_list_firewall_traffic_shaper_limiter_bandwidths` — verify the created resource appears
18. **Get** using `pfsense_get_firewall_traffic_shaper_limiter_bandwidth` with the ID from the create response
19. **Update** using `pfsense_update_firewall_traffic_shaper_limiter_bandwidth` with `confirm=True` — set `bw` to `100`
20. **Get** again using `pfsense_get_firewall_traffic_shaper_limiter_bandwidth` — verify `bw` was updated
21. **Create** using `pfsense_create_firewall_traffic_shaper_limiter_queue` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `name`: `bt_sys13_limq`
    - `aqm`: `droptail`
22. **List** using `pfsense_list_firewall_traffic_shaper_limiter_queues` — verify the created resource appears
23. **Get** using `pfsense_get_firewall_traffic_shaper_limiter_queue` with the ID from the create response
24. **Update** using `pfsense_update_firewall_traffic_shaper_limiter_queue` with `confirm=True` — set `aqm` to `codel`
25. **Get** again using `pfsense_get_firewall_traffic_shaper_limiter_queue` — verify `aqm` was updated
26. **Check apply status** using `pfsense_get_firewall_apply_status`
27. **Apply changes** using `pfsense_firewall_apply` with `confirm=True`

**Important notes**:
Create shaper → queue (sub-resource). Create limiter → bandwidth + limiter/queue (sub-resources).
All sub-resources need parent_id from their parent. Cleanup in reverse order.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_firewall_traffic_shaper_limiter_queue` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_firewall_traffic_shaper_limiter_bandwidth` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_firewall_traffic_shaper_limiter` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_firewall_traffic_shaper_queue` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_firewall_traffic_shaper` with `confirm=True` (ID from create step)

**Expected outcome**: All 27 tools exercised successfully.
