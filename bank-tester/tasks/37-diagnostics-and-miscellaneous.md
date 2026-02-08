## Task 37: Diagnostics & Miscellaneous

**task_id**: 37-diagnostics--miscellaneous

**Objective**: Exercise all tools in the diagnostics subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (8):
- `pfsense_list_diagnostics_arp_table`
- `pfsense_get_diagnostics_arp_table_entry`
- `pfsense_get_diagnostics_config_history_revision`
- `pfsense_get_diagnostics_table`
- `pfsense_post_diagnostics_command_prompt`
- `pfsense_post_diagnostics_ping`
- `pfsense_list_system_package_available`
- `pfsense_get_system_package`

**Steps**:
1. **Read** using `pfsense_list_diagnostics_arp_table`
2. **Read** using `pfsense_get_diagnostics_arp_table_entry`
3. **Read** using `pfsense_get_diagnostics_config_history_revision`
4. **Read** using `pfsense_get_diagnostics_table`
5. **Execute** `pfsense_post_diagnostics_command_prompt` with `confirm=True`:
    - `command`: `echo bt_sys37_test`
6. **Execute** `pfsense_post_diagnostics_ping` with `confirm=True`:
    - `host`: `127.0.0.1`
    - `count`: `1`
7. **Read** using `pfsense_list_system_package_available`
8. **Read** using `pfsense_get_system_package` (GET only — POST/DELETE trigger 504 timeout)

**Important notes**:
Do NOT use diagnostics/halt_system or diagnostics/reboot (destructive).
Do NOT delete all ARP entries or config history (destructive).

**Skipped endpoints**:
- `/api/v2/system/package` — nginx 504 timeout via QEMU NAT
- `/api/v2/system/package` — nginx 504 timeout via QEMU NAT

**Cleanup** (reverse order):
- No cleanup needed (read-only / settings restored)

**Expected outcome**: All 8 tools exercised successfully.
