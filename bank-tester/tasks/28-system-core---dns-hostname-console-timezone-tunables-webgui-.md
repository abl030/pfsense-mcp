## Task 28: System Core — DNS, Hostname, Console, Timezone, Tunables, WebGUI, Notifications

**task_id**: 28-system-core--dns-hostname-console-timezone-tunable

**Objective**: Exercise all tools in the system subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (18):
- `pfsense_get_system_dns`
- `pfsense_update_system_dns`
- `pfsense_get_system_hostname`
- `pfsense_update_system_hostname`
- `pfsense_get_system_console`
- `pfsense_update_system_console`
- `pfsense_get_system_timezone`
- `pfsense_update_system_timezone`
- `pfsense_create_system_tunable`
- `pfsense_list_system_tunables`
- `pfsense_get_system_tunable`
- `pfsense_update_system_tunable`
- `pfsense_delete_system_tunable`
- `pfsense_get_system_web_gui_settings`
- `pfsense_update_system_web_gui_settings`
- `pfsense_list_system_notifications_email_settings`
- `pfsense_update_system_notifications_email_settings`
- `pfsense_get_system_version`

**Steps**:
1. **Get settings** using `pfsense_get_system_dns` — note current value of `dnsallowoverride`
2. **Update settings** using `pfsense_update_system_dns` with `confirm=True` — set `dnsallowoverride` to `False`
3. **Get settings** again using `pfsense_get_system_dns` — verify `dnsallowoverride` was updated
4. **Get settings** using `pfsense_get_system_hostname` — note current value of `hostname`
5. **Update settings** using `pfsense_update_system_hostname` with `confirm=True` — set `hostname` to `'bttesthost'` (also include: `domain=home.arpa`)
6. **Get settings** again using `pfsense_get_system_hostname` — verify `hostname` was updated
7. **Restore** using `pfsense_update_system_hostname` with `confirm=True` — set `hostname` back to `'pfSense'`
8. **Get settings** using `pfsense_get_system_console` — note current value of `passwd_protect_console`
9. **Update settings** using `pfsense_update_system_console` with `confirm=True` — set `passwd_protect_console` to `True`
10. **Get settings** again using `pfsense_get_system_console` — verify `passwd_protect_console` was updated
11. **Get settings** using `pfsense_get_system_timezone` — note current value of `timezone`
12. **Update settings** using `pfsense_update_system_timezone` with `confirm=True` — set `timezone` to `'America/Chicago'`
13. **Get settings** again using `pfsense_get_system_timezone` — verify `timezone` was updated
14. **Restore** using `pfsense_update_system_timezone` with `confirm=True` — set `timezone` back to `'Etc/UTC'`
15. **Create** using `pfsense_create_system_tunable` with `confirm=True`:
    - `tunable`: `net.inet.tcp.tso`
    - `value`: `0`
    - `descr`: `bt_sys28_tunable`
16. **List** using `pfsense_list_system_tunables` — verify the created resource appears
17. **Get** using `pfsense_get_system_tunable` with the ID from the create response
18. **Update** using `pfsense_update_system_tunable` with `confirm=True` — set `descr` to `Updated tunable`
19. **Get** again using `pfsense_get_system_tunable` — verify `descr` was updated
20. **Get settings** using `pfsense_get_system_web_gui_settings` — note current value of `port`
21. **Update settings** using `pfsense_update_system_web_gui_settings` with `confirm=True` — set `port` to `'8443'`
22. **Get settings** again using `pfsense_get_system_web_gui_settings` — verify `port` was updated
23. **Restore** using `pfsense_update_system_web_gui_settings` with `confirm=True` — set `port` back to `'443'`
23. **Get settings** using `pfsense_list_system_notifications_email_settings` — note current value of `ipaddress`
24. **Update settings** using `pfsense_update_system_notifications_email_settings` with `confirm=True` — set `ipaddress` to `'127.0.0.1'` (also include: `username=test`, `password=test`)
25. **Get settings** again using `pfsense_list_system_notifications_email_settings` — verify `ipaddress` was updated
26. **Read** using `pfsense_get_system_version`

**Important notes**:
Timezone PATCH response may have text prefix before JSON — handle carefully.
Restore hostname and timezone after testing.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_system_tunable` with `confirm=True` (ID from create step)

**Expected outcome**: All 18 tools exercised successfully.
