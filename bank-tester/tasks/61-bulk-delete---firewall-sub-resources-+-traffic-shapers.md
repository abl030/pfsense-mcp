## Task 61: Bulk Delete — Firewall Sub-Resources + Traffic Shapers

**task_id**: 61-bulk-delete--firewall-sub-resources-+-traffic-shap

**Objective**: Exercise all tools in the firewall subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (15):
- `pfsense_create_firewall_schedule_time_range`
- `pfsense_list_firewall_schedule_time_ranges`
- `pfsense_delete_firewall_schedule_time_ranges`
- `pfsense_create_firewall_traffic_shaper`
- `pfsense_list_firewall_traffic_shapers`
- `pfsense_delete_firewall_traffic_shapers`
- `pfsense_create_firewall_traffic_shaper_queue`
- `pfsense_list_firewall_traffic_shaper_queues`
- `pfsense_delete_firewall_traffic_shaper_queues`
- `pfsense_create_firewall_traffic_shaper_limiter_queue`
- `pfsense_list_firewall_traffic_shaper_limiter_queues`
- `pfsense_delete_firewall_traffic_shaper_limiter_queues`
- `pfsense_create_firewall_traffic_shaper_limiter_bandwidth`
- `pfsense_list_firewall_traffic_shaper_limiter_bandwidths`
- `pfsense_delete_firewall_traffic_shaper_limiter_bandwidths`

**Steps**:
1. **Create** a test resource using `pfsense_create_firewall_schedule_time_range` with `confirm=True` (use parent_id from the parent resource):
    - `month`: `[7, 8]`
    - `day`: `[15, 16]`
    - `hour`: `10:00-18:00`
2. **List** using `pfsense_list_firewall_schedule_time_ranges` — verify resource exists (Needs schedule parent_id)
3. **Bulk delete** using `pfsense_delete_firewall_schedule_time_ranges` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
4. **List** using `pfsense_list_firewall_schedule_time_ranges` — verify collection is empty
5. **Create** a test resource using `pfsense_create_firewall_traffic_shaper` with `confirm=True`:
    - `bandwidth`: `100`
    - `bandwidthtype`: `Mb`
    - `interface`: `wan`
    - `scheduler`: `HFSC`
    - `enabled`: `False`
    - `qlimit`: `50`
    - `queue`: `[]`
    - `tbrconfig`: `1`
6. **List** using `pfsense_list_firewall_traffic_shapers` — verify resource exists
7. **Bulk delete** using `pfsense_delete_firewall_traffic_shapers` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
8. **List** using `pfsense_list_firewall_traffic_shapers` — verify collection is empty
9. **Create** a test resource using `pfsense_create_firewall_traffic_shaper_queue` with `confirm=True` (use parent_id from the parent resource):
    - `name`: `bt_bd61_tsq`
    - `qlimit`: `50`
    - `bandwidth`: `100`
    - `linkshare_m2`: `10%`
10. **List** using `pfsense_list_firewall_traffic_shaper_queues` — verify resource exists (Needs traffic shaper parent_id)
11. **Bulk delete** using `pfsense_delete_firewall_traffic_shaper_queues` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
12. **List** using `pfsense_list_firewall_traffic_shaper_queues` — verify collection is empty
13. **Create** a test resource using `pfsense_create_firewall_traffic_shaper_limiter_queue` with `confirm=True` (use parent_id from the parent resource):
    - `name`: `bt_bd61_limq`
    - `aqm`: `droptail`
14. **List** using `pfsense_list_firewall_traffic_shaper_limiter_queues` — verify resource exists (Needs limiter parent_id)
15. **Bulk delete** using `pfsense_delete_firewall_traffic_shaper_limiter_queues` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
16. **List** using `pfsense_list_firewall_traffic_shaper_limiter_queues` — verify collection is empty
17. **Create** a test resource using `pfsense_create_firewall_traffic_shaper_limiter_bandwidth` with `confirm=True` (use parent_id from the parent resource):
    - `bw`: `50`
    - `bwscale`: `Mb`
18. **List** using `pfsense_list_firewall_traffic_shaper_limiter_bandwidths` — verify resource exists (Needs limiter parent_id)
19. **Bulk delete** using `pfsense_delete_firewall_traffic_shaper_limiter_bandwidths` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
20. **List** using `pfsense_list_firewall_traffic_shaper_limiter_bandwidths` — verify collection is empty

**Important notes**:
Sub-resource bulk deletes. Create parents first, then sub-resources, then bulk delete.
Order: schedule → time_ranges (bulk delete) → schedule cleanup.
Shaper → queues (bulk delete) → shaper cleanup.
Limiter → limiter queues + bandwidths (bulk delete) → limiter cleanup.

**Cleanup** (reverse order):
- No cleanup needed (read-only / settings restored)

**Expected outcome**: All 15 tools exercised successfully.
