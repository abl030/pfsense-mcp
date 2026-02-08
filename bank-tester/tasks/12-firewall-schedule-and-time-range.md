## Task 12: Firewall Schedule & Time Range

**task_id**: 12-firewall-schedule--time-range

**Objective**: Exercise all tools in the firewall/schedule subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (12):
- `pfsense_create_firewall_schedule`
- `pfsense_list_firewall_schedules`
- `pfsense_get_firewall_schedule`
- `pfsense_update_firewall_schedule`
- `pfsense_delete_firewall_schedule`
- `pfsense_create_firewall_schedule_time_range`
- `pfsense_list_firewall_schedule_time_ranges`
- `pfsense_get_firewall_schedule_time_range`
- `pfsense_update_firewall_schedule_time_range`
- `pfsense_delete_firewall_schedule_time_range`
- `pfsense_get_firewall_apply_status`
- `pfsense_firewall_apply`

**Steps**:
1. **Create** using `pfsense_create_firewall_schedule` with `confirm=True`:
    - `name`: `bt_sys12_sched`
    - `timerange`: `[{'month': '1,2,3', 'day': '1,2,3', 'hour': '0:00-23:59', 'position': []}]`
    - `descr`: `Bank tester schedule`
2. **List** using `pfsense_list_firewall_schedules` — verify the created resource appears
3. **Get** using `pfsense_get_firewall_schedule` with the ID from the create response
4. **Update** using `pfsense_update_firewall_schedule` with `confirm=True` — set `descr` to `Updated schedule`
5. **Get** again using `pfsense_get_firewall_schedule` — verify `descr` was updated
6. **Create** using `pfsense_create_firewall_schedule_time_range` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `month`: `[4, 5, 6]`
    - `day`: `[10, 11, 12]`
    - `hour`: `8:00-17:00`
7. **List** using `pfsense_list_firewall_schedule_time_ranges` — verify the created resource appears
8. **Get** using `pfsense_get_firewall_schedule_time_range` with the ID from the create response
9. **Update** using `pfsense_update_firewall_schedule_time_range` with `confirm=True` — set `hour` to `9:00-18:00`
10. **Get** again using `pfsense_get_firewall_schedule_time_range` — verify `hour` was updated
11. **Check apply status** using `pfsense_get_firewall_apply_status`
12. **Apply changes** using `pfsense_firewall_apply` with `confirm=True`

**Important notes**:
Time range is a sub-resource of schedule — needs parent_id from the schedule.
Cleanup time_range before schedule.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_firewall_schedule_time_range` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_firewall_schedule` with `confirm=True` (ID from create step)

**Expected outcome**: All 12 tools exercised successfully.
