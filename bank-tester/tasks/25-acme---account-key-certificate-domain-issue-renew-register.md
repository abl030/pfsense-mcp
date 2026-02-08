## Task 25: ACME — Account Key, Certificate, Domain, Issue/Renew/Register

**task_id**: 25-acme--account-key-certificate-domain-issue-renew-r

**Objective**: Exercise all tools in the services/acme subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (23):
- `pfsense_get_services_acme_settings`
- `pfsense_update_services_acme_settings`
- `pfsense_create_services_acme_account_key`
- `pfsense_list_services_acme_account_keys`
- `pfsense_get_services_acme_account_key`
- `pfsense_update_services_acme_account_key`
- `pfsense_delete_services_acme_account_key`
- `pfsense_create_services_acme_certificate`
- `pfsense_list_services_acme_certificates`
- `pfsense_get_services_acme_certificate`
- `pfsense_update_services_acme_certificate`
- `pfsense_delete_services_acme_certificate`
- `pfsense_create_services_acme_certificate_domain`
- `pfsense_get_services_acme_certificate_domain`
- `pfsense_update_services_acme_certificate_domain`
- `pfsense_delete_services_acme_certificate_domain`
- `pfsense_create_services_acme_certificate_action`
- `pfsense_get_services_acme_certificate_action`
- `pfsense_update_services_acme_certificate_action`
- `pfsense_delete_services_acme_certificate_action`
- `pfsense_create_services_acme_account_key_register`
- `pfsense_create_services_acme_certificate_issue`
- `pfsense_create_services_acme_certificate_renew`

**Steps**:
1. **Get settings** using `pfsense_get_services_acme_settings` — note current value of `enable`
2. **Update settings** using `pfsense_update_services_acme_settings` with `confirm=True` — set `enable` to `True`
3. **Get settings** again using `pfsense_get_services_acme_settings` — verify `enable` was updated
4. **Create** using `pfsense_create_services_acme_account_key` with `confirm=True`:
    - `name`: `bt_sys25_acme_key`
    - `descr`: `Bank tester ACME key`
    - `email`: `test@example.com`
    - `acmeserver`: `letsencrypt-staging-2`
5. **List** using `pfsense_list_services_acme_account_keys` — verify the created resource appears
6. **Get** using `pfsense_get_services_acme_account_key` with the ID from the create response
7. **Update** using `pfsense_update_services_acme_account_key` with `confirm=True` — set `descr` to `Updated ACME key`
8. **Get** again using `pfsense_get_services_acme_account_key` — verify `descr` was updated
9. **Create** using `pfsense_create_services_acme_certificate` with `confirm=True`:
    - `name`: `bt_sys25_acme_cert`
    - `descr`: `Bank tester ACME cert`
    - `acmeserver`: `letsencrypt-staging-2`
10. **List** using `pfsense_list_services_acme_certificates` — verify the created resource appears
11. **Get** using `pfsense_get_services_acme_certificate` with the ID from the create response
12. **Update** using `pfsense_update_services_acme_certificate` with `confirm=True` — set `descr` to `Updated ACME cert`
13. **Get** again using `pfsense_get_services_acme_certificate` — verify `descr` was updated
14. **Create** using `pfsense_create_services_acme_certificate_domain` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `name`: `test.example.com`
    - `method`: `standalone`
15. **Get** using `pfsense_get_services_acme_certificate_domain` with the ID from the create response
16. **Update** using `pfsense_update_services_acme_certificate_domain` with `confirm=True` — set `name` to `updated.example.com`
17. **Get** again using `pfsense_get_services_acme_certificate_domain` — verify `name` was updated
18. **Create** using `pfsense_create_services_acme_certificate_action` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `status`: `active`
    - `command`: `/bin/true`
19. **Get** using `pfsense_get_services_acme_certificate_action` with the ID from the create response
20. **Update** using `pfsense_update_services_acme_certificate_action` with `confirm=True` — set `command` to `/bin/echo updated`
21. **Get** again using `pfsense_get_services_acme_certificate_action` — verify `command` was updated
22. **Execute** `pfsense_create_services_acme_account_key_register` with `confirm=True` (Async — returns 200 with status=pending. Uses the created account key.):
(no parameters needed)
23. **Execute** `pfsense_create_services_acme_certificate_issue` with `confirm=True` (Async — returns 200 with status=pending.):
(no parameters needed)
24. **Execute** `pfsense_create_services_acme_certificate_renew` with `confirm=True` (Async — returns 200 with status=pending.):
(no parameters needed)

**Important notes**:
ACME register/issue/renew are async (return status=pending immediately).
acmeserver must be one of the fixed enum values (e.g., letsencrypt-staging-2).
Cleanup: domain → certificate, account key.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_services_acme_certificate_action` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_acme_certificate_domain` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_acme_certificate` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_services_acme_account_key` with `confirm=True` (ID from create step)

**Expected outcome**: All 23 tools exercised successfully.
