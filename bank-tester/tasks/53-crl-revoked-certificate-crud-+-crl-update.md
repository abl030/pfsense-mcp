## Task 53: CRL Revoked Certificate CRUD + CRL Update

**task_id**: 53-crl-revoked-certificate-crud-+-crl-update

**Objective**: Exercise all tools in the system/crl subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (11):
- `pfsense_create_system_certificate_authority_generate`
- `pfsense_create_system_certificate_generate`
- `pfsense_create_system_crl`
- `pfsense_list_system_cr_ls`
- `pfsense_get_system_crl`
- `pfsense_update_system_crl`
- `pfsense_delete_system_crl`
- `pfsense_create_system_crl_revoked_certificate`
- `pfsense_get_system_crl_revoked_certificate`
- `pfsense_update_system_crl_revoked_certificate`
- `pfsense_delete_system_crl_revoked_certificate`

**Steps**:
1. **Execute** `pfsense_create_system_certificate_authority_generate` with `confirm=True`:
    - `descr`: `bt_sys53_ca`
    - `keytype`: `RSA`
    - `keylen`: `2048`
    - `digest_alg`: `sha256`
    - `dn_commonname`: `BT Sprint2 CA`
    - `dn_country`: `US`
    - `dn_state`: `California`
    - `dn_city`: `San Francisco`
    - `dn_organization`: `pfSense Test`
    - `dn_organizationalunit`: `Testing`
    - `lifetime`: `3650`
2. **Execute** `pfsense_create_system_certificate_generate` with `confirm=True` (Needs CA refid as caref.):
    - `descr`: `bt_sys53_cert`
    - `keytype`: `RSA`
    - `keylen`: `2048`
    - `digest_alg`: `sha256`
    - `dn_commonname`: `revoke-me.test`
    - `lifetime`: `365`
    - `type_`: `server`
3. **Create** using `pfsense_create_system_crl` with `confirm=True` (inject `caref` from parent's `refid` field):
    - `descr`: `bt_sys53_crl`
    - `method`: `internal`
    - `text`: ``
4. **List** using `pfsense_list_system_cr_ls` — verify the created resource appears
5. **Get** using `pfsense_get_system_crl` with the ID from the create response
6. **Update** using `pfsense_update_system_crl` with `confirm=True` — set `descr` to `Updated CRL`
7. **Get** again using `pfsense_get_system_crl` — verify `descr` was updated
8. **Create** using `pfsense_create_system_crl_revoked_certificate` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `reason`: `0`
9. **Get** using `pfsense_get_system_crl_revoked_certificate` with the ID from the create response
10. **Update** using `pfsense_update_system_crl_revoked_certificate` with `confirm=True` — set `reason` to `1`
11. **Get** again using `pfsense_get_system_crl_revoked_certificate` — verify `reason` was updated

**Important notes**:
Full CRL chain: generate CA → generate cert → create CRL (referencing CA) → CRUD revoked certs.
CRL update (PATCH) tests the previously uncovered update_system_crl tool.
Cert serial numbers must be small (not 160-bit) to avoid PHP INT overflow.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_system_crl_revoked_certificate` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_system_crl` with `confirm=True` (ID from create step)

**Expected outcome**: All 11 tools exercised successfully.
