## Task 26: Small Services — NTP, SSH, Cron, Service Watchdog, WoL, DHCP Relay, Syslog

**task_id**: 26-small-services--ntp-ssh-cron-service-watchdog-wol-

**Objective**: Exercise all tools in the services subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (24):
- `pfsense_get_services_ntp_settings`
- `pfsense_update_services_ntp_settings`
- `pfsense_create_services_ntp_time_server`
- `pfsense_list_services_ntp_time_servers`
- `pfsense_get_services_ntp_time_server`
- `pfsense_update_services_ntp_time_server`
- `pfsense_delete_services_ntp_time_server`
- `pfsense_get_services_ssh`
- `pfsense_update_services_ssh`
- `pfsense_create_services_cron_job`
- `pfsense_list_services_cron_jobs`
- `pfsense_get_services_cron_job`
- `pfsense_update_services_cron_job`
- `pfsense_delete_services_cron_job`
- `pfsense_create_services_service_watchdog`
- `pfsense_list_services_service_watchdogs`
- `pfsense_get_services_service_watchdog`
- `pfsense_update_services_service_watchdog`
- `pfsense_delete_services_service_watchdog`
- `pfsense_create_services_wake_on_lan_send`
- `pfsense_get_services_dhcp_relay`
- `pfsense_update_services_dhcp_relay`
- `pfsense_get_/api/v2/services/syslog/settings`
- `pfsense_patch_/api/v2/services/syslog/settings`

**Steps**:
1. **Get settings** using `pfsense_get_services_ntp_settings` — note current value of `orphan`
2. **Update settings** using `pfsense_update_services_ntp_settings` with `confirm=True` — set `orphan` to `'12'`
3. **Get settings** again using `pfsense_get_services_ntp_settings` — verify `orphan` was updated
4. **Create** using `pfsense_create_services_ntp_time_server` with `confirm=True`:
    - `timeserver`: `time.example.com`
    - `type_`: `server`
    - `prefer`: `False`
    - `noselect`: `False`
    - `ispool`: `False`
5. **List** using `pfsense_list_services_ntp_time_servers` — verify the created resource appears
6. **Get** using `pfsense_get_services_ntp_time_server` with the ID from the create response
7. **Update** using `pfsense_update_services_ntp_time_server` with `confirm=True` — set `timeserver` to `time2.example.com`
8. **Get** again using `pfsense_get_services_ntp_time_server` — verify `timeserver` was updated
9. **Get settings** using `pfsense_get_services_ssh` — note current value of `port`
10. **Update settings** using `pfsense_update_services_ssh` with `confirm=True` — set `port` to `'2222'`
11. **Get settings** again using `pfsense_get_services_ssh` — verify `port` was updated
12. **Restore** using `pfsense_update_services_ssh` with `confirm=True` — set `port` back to `'22'`
13. **Create** using `pfsense_create_services_cron_job` with `confirm=True`:
    - `command`: `/bin/echo bt_sys26_cron`
    - `who`: `root`
    - `minute`: `0`
    - `hour`: `0`
    - `mday`: `*`
    - `month`: `*`
    - `wday`: `*`
14. **List** using `pfsense_list_services_cron_jobs` — verify the created resource appears
15. **Get** using `pfsense_get_services_cron_job` with the ID from the create response
16. **Update** using `pfsense_update_services_cron_job` with `confirm=True` — set `command` to `/bin/echo bt_sys26_cron_updated`
17. **Get** again using `pfsense_get_services_cron_job` — verify `command` was updated
18. **Create** using `pfsense_create_services_service_watchdog` with `confirm=True`:
    - `name`: `sshd`
    - `descr`: `bt_sys26_watchdog`
19. **List** using `pfsense_list_services_service_watchdogs` — verify the created resource appears
20. **Get** using `pfsense_get_services_service_watchdog` with the ID from the create response
21. **Update** using `pfsense_update_services_service_watchdog` with `confirm=True` — set `descr` to `Updated watchdog`
22. **Get** again using `pfsense_get_services_service_watchdog` — verify `descr` was updated
23. **Execute** `pfsense_create_services_wake_on_lan_send` with `confirm=True`:
    - `interface`: `lan`
    - `mac_addr`: `00:11:22:33:44:55`
24. **Get settings** using `pfsense_get_services_dhcp_relay` — note current value of `enable`
25. **Update settings** using `pfsense_update_services_dhcp_relay` with `confirm=True` — set `enable` to `False` (also include: `server=['10.0.2.1']`)
26. **Get settings** again using `pfsense_get_services_dhcp_relay` — verify `enable` was updated
27. **Get settings** using `pfsense_get_/api/v2/services/syslog/settings` — note current value of `logall`
28. **Update settings** using `pfsense_patch_/api/v2/services/syslog/settings` with `confirm=True` — set `logall` to `True`
29. **Get settings** again using `pfsense_get_/api/v2/services/syslog/settings` — verify `logall` was updated

**Important notes**:
WoL uses interface name "lan" (not physical NIC).
Service watchdog name must reference an existing service (e.g., sshd).
Restore SSH port to 22 after testing.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_services_service_watchdog` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_cron_job` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_ntp_time_server` with `confirm=True` (ID from create step)

**Expected outcome**: All 24 tools exercised successfully.
