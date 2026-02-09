## Task 64: Bulk Delete — BIND + ACME + Small Services

**task_id**: 64-bulk-delete--bind-+-acme-+-small-services

**Objective**: Exercise all tools in the services subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (30):
- `pfsense_create_services_bind_access_list`
- `pfsense_list_services_bind_access_lists`
- `pfsense_delete_services_bind_access_lists`
- `pfsense_create_services_bind_access_list_entry`
- `pfsense_list_services_bind_access_list_entries`
- `pfsense_delete_services_bind_access_list_entries`
- `pfsense_create_services_bind_view`
- `pfsense_list_services_bind_views`
- `pfsense_delete_services_bind_views`
- `pfsense_create_services_bind_zone`
- `pfsense_list_services_bind_zones`
- `pfsense_delete_services_bind_zones`
- `pfsense_create_services_bind_sync_remote_host`
- `pfsense_list_services_bind_sync_remote_hosts`
- `pfsense_delete_services_bind_sync_remote_hosts`
- `pfsense_create_services_acme_account_key`
- `pfsense_list_services_acme_account_keys`
- `pfsense_delete_services_acme_account_keys`
- `pfsense_create_services_acme_certificate`
- `pfsense_list_services_acme_certificates`
- `pfsense_delete_services_acme_certificates`
- `pfsense_create_services_cron_job`
- `pfsense_list_services_cron_jobs`
- `pfsense_delete_services_cron_jobs`
- `pfsense_create_services_ntp_time_server`
- `pfsense_list_services_ntp_time_servers`
- `pfsense_delete_services_ntp_time_servers`
- `pfsense_create_services_service_watchdog`
- `pfsense_list_services_service_watchdogs`
- `pfsense_delete_services_service_watchdogs`

**Steps**:
1. **Create** a test resource using `pfsense_create_services_bind_access_list` with `confirm=True`:
    - `entries`: `[{'value': '10.64.0.0/8', 'description': 'bd64 entry'}]`
    - `name`: `bt_bd64_bacl`
2. **List** using `pfsense_list_services_bind_access_lists` — verify resource exists
3. **Bulk delete** using `pfsense_delete_services_bind_access_lists` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
4. **List** using `pfsense_list_services_bind_access_lists` — verify collection is empty
5. **Create** a test resource using `pfsense_create_services_bind_access_list_entry` with `confirm=True` (use parent_id from the parent resource):
    - `value`: `10.64.1.0/16`
6. **List** using `pfsense_list_services_bind_access_list_entries` — verify resource exists (Needs BIND access list parent_id)
7. **Bulk delete** using `pfsense_delete_services_bind_access_list_entries` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
8. **List** using `pfsense_list_services_bind_access_list_entries` — verify collection is empty
9. **Create** a test resource using `pfsense_create_services_bind_view` with `confirm=True`:
    - `name`: `bt_bd64_view`
10. **List** using `pfsense_list_services_bind_views` — verify resource exists
11. **Bulk delete** using `pfsense_delete_services_bind_views` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
12. **List** using `pfsense_list_services_bind_views` — verify collection is empty
13. **Create** a test resource using `pfsense_create_services_bind_zone` with `confirm=True`:
    - `name`: `bt-bd64.example.com`
    - `nameserver`: `ns1.example.com`
    - `mail`: `admin.example.com`
    - `serial`: `2024010101`
    - `forwarders`: `[]`
    - `baseip`: `10.99.64.0`
14. **List** using `pfsense_list_services_bind_zones` — verify resource exists
15. **Bulk delete** using `pfsense_delete_services_bind_zones` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
16. **List** using `pfsense_list_services_bind_zones` — verify collection is empty
17. **Create** a test resource using `pfsense_create_services_bind_sync_remote_host` with `confirm=True`:
    - `syncdestinenable`: `False`
    - `syncdesttimeout`: `120`
    - `syncprotocol`: `http`
    - `ipaddress`: `10.99.64.60`
    - `syncport`: `80`
    - `username`: `admin`
    - `password`: `pfsense`
18. **List** using `pfsense_list_services_bind_sync_remote_hosts` — verify resource exists
19. **Bulk delete** using `pfsense_delete_services_bind_sync_remote_hosts` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
20. **List** using `pfsense_list_services_bind_sync_remote_hosts` — verify collection is empty
21. **Create** a test resource using `pfsense_create_services_acme_account_key` with `confirm=True`:
    - `name`: `bt_bd64_key`
    - `email`: `bd64@example.com`
    - `acmeserver`: `letsencrypt-staging-2`
22. **List** using `pfsense_list_services_acme_account_keys` — verify resource exists
23. **Bulk delete** using `pfsense_delete_services_acme_account_keys` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
24. **List** using `pfsense_list_services_acme_account_keys` — verify collection is empty
25. **Create** a test resource using `pfsense_create_services_acme_certificate` with `confirm=True`:
    - `name`: `bt_bd64_cert`
    - `acmeserver`: `letsencrypt-staging-2`
    - `a_domainlist`: `[{'name': 'bd64.example.com', 'method': 'standalone'}]`
26. **List** using `pfsense_list_services_acme_certificates` — verify resource exists
27. **Bulk delete** using `pfsense_delete_services_acme_certificates` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
28. **List** using `pfsense_list_services_acme_certificates` — verify collection is empty
29. **Create** a test resource using `pfsense_create_services_cron_job` with `confirm=True`:
    - `command`: `/bin/echo bt_bd64_cron`
    - `who`: `root`
    - `minute`: `30`
    - `hour`: `3`
    - `mday`: `*`
    - `month`: `*`
    - `wday`: `*`
30. **List** using `pfsense_list_services_cron_jobs` — verify resource exists
31. **Bulk delete** using `pfsense_delete_services_cron_jobs` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
32. **List** using `pfsense_list_services_cron_jobs` — verify collection is empty
33. **Create** a test resource using `pfsense_create_services_ntp_time_server` with `confirm=True`:
    - `timeserver`: `time.bd64.example.com`
    - `type_`: `server`
    - `prefer`: `False`
    - `noselect`: `False`
    - `ispool`: `False`
34. **List** using `pfsense_list_services_ntp_time_servers` — verify resource exists
35. **Bulk delete** using `pfsense_delete_services_ntp_time_servers` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
36. **List** using `pfsense_list_services_ntp_time_servers` — verify collection is empty
37. **Create** a test resource using `pfsense_create_services_service_watchdog` with `confirm=True`:
    - `name`: `sshd`
38. **List** using `pfsense_list_services_service_watchdogs` — verify resource exists
39. **Bulk delete** using `pfsense_delete_services_service_watchdogs` with `confirm=True` — use `query` parameter to filter (e.g., `query={"id": "<id>"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={"name": "<name>"}` from the list results)
40. **List** using `pfsense_list_services_service_watchdogs` — verify collection is empty

**Important notes**:
Bulk delete BIND, ACME, cron, NTP, and service watchdog collections.
Enable BIND settings first if needed.
BIND sub-resources: create parent → entry → bulk delete entries → delete parent.

**Cleanup** (reverse order):
- No cleanup needed (read-only / settings restored)

**Expected outcome**: All 30 tools exercised successfully.
