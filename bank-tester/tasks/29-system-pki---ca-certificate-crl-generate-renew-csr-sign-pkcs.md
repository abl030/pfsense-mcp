## Task 29: System PKI — CA, Certificate, CRL, Generate, Renew, CSR, Sign, PKCS12

**task_id**: 29-system-pki--ca-certificate-crl-generate-renew-csr-

**Objective**: Exercise all tools in the system/certificate subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (17):
- `pfsense_create_system_certificate_authority`
- `pfsense_get_system_certificate_authority`
- `pfsense_update_system_certificate_authority`
- `pfsense_delete_system_certificate_authority`
- `pfsense_create_system_certificate`
- `pfsense_list_system_certificates`
- `pfsense_get_system_certificate`
- `pfsense_update_system_certificate`
- `pfsense_delete_system_certificate`
- `pfsense_create_system_crl`
- `pfsense_list_system_crls`
- `pfsense_get_system_crl`
- `pfsense_delete_system_crl`
- `pfsense_create_system_certificate_authority_generate`
- `pfsense_create_system_certificate_generate`
- `pfsense_create_system_certificate_signing_request`
- `pfsense_create_system_certificate_pkcs12_export`

**Steps**:
1. **Create** using `pfsense_create_system_certificate_authority` with `confirm=True`:
    - `descr`: `bt_sys29_ca`
    - `crt`: `__CA_CERT_PEM__`
    - `prv`: `__CA_KEY_PEM__`
2. **Get** using `pfsense_get_system_certificate_authority` with the ID from the create response
3. **Update** using `pfsense_update_system_certificate_authority` with `confirm=True` — set `descr` to `Updated CA`
4. **Get** again using `pfsense_get_system_certificate_authority` — verify `descr` was updated
5. **Create** using `pfsense_create_system_certificate` with `confirm=True`:
    - `descr`: `bt_sys29_cert`
    - `crt`: `__CERT_PEM__`
    - `prv`: `__CERT_KEY_PEM__`
6. **List** using `pfsense_list_system_certificates` — verify the created resource appears
7. **Get** using `pfsense_get_system_certificate` with the ID from the create response
8. **Update** using `pfsense_update_system_certificate` with `confirm=True` — set `descr` to `Updated cert`
9. **Get** again using `pfsense_get_system_certificate` — verify `descr` was updated
10. **Create** using `pfsense_create_system_crl` with `confirm=True` (inject `caref` from parent's `refid` field):
    - `descr`: `bt_sys29_crl`
    - `method`: `internal`
    - `text`: ``
11. **List** using `pfsense_list_system_crls` — verify the created resource appears
12. **Get** using `pfsense_get_system_crl` with the ID from the create response
13. **Execute** `pfsense_create_system_certificate_authority_generate` with `confirm=True`:
    - `descr`: `bt_sys29_gen_ca`
    - `keytype`: `RSA`
    - `keylen`: `2048`
    - `digest_alg`: `sha256`
    - `dn_commonname`: `BT Gen CA`
    - `dn_country`: `US`
    - `dn_state`: `California`
    - `dn_city`: `San Francisco`
    - `dn_organization`: `pfSense Test`
    - `dn_organizationalunit`: `Testing`
    - `lifetime`: `3650`
14. **Execute** `pfsense_create_system_certificate_generate` with `confirm=True` (Needs a CA to sign — use generated CA's refid as caref.):
    - `descr`: `bt_sys29_gen_cert`
    - `keytype`: `RSA`
    - `keylen`: `2048`
    - `digest_alg`: `sha256`
    - `dn_commonname`: `gen-cert.test`
    - `lifetime`: `365`
    - `type_`: `server`
15. **Execute** `pfsense_create_system_certificate_signing_request` with `confirm=True`:
    - `descr`: `bt_sys29_csr`
    - `keytype`: `RSA`
    - `keylen`: `2048`
    - `digest_alg`: `sha256`
    - `dn_commonname`: `test-csr.example.com`
16. **Execute** `pfsense_create_system_certificate_pkcs12_export` with `confirm=True` (Needs a certificate. Returns binary (application/octet-stream).):
(no parameters needed)

**Important notes**:
CA generate needs full DN fields (country, state, city, org, OU).
CRL needs caref from a CA. Certificate generate needs caref from a CA.
PKCS12 export returns binary data.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_system_crl` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_system_certificate` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_system_certificate_authority` with `confirm=True` (ID from create step)

**Expected outcome**: All 17 tools exercised successfully.
