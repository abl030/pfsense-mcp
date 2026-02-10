## Task 56: PKI Actions + Service Restart + Read-Only Gaps

**task_id**: 56-pki-actions-+-service-restart-+-read-only-gaps

**Objective**: Exercise all tools in the system subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (8):
- `pfsense_create_system_certificate_authority_generate`
- `pfsense_create_system_certificate_generate`
- `pfsense_create_system_certificate_signing_request`
- `pfsense_create_system_certificate_authority_renew`
- `pfsense_create_system_certificate_renew`
- `pfsense_create_system_certificate_signing_request_sign`
- `pfsense_create_status_service`
- `pfsense_get_status_openvpn_server_connection`

**Steps**:
1. **Execute** `pfsense_create_system_certificate_authority_generate` with `confirm=True`:
    - `descr`: `bt_sys56_ca`
    - `keytype`: `RSA`
    - `keylen`: `2048`
    - `digest_alg`: `sha256`
    - `dn_commonname`: `BT PKI Actions CA`
    - `dn_country`: `US`
    - `dn_state`: `California`
    - `dn_city`: `San Francisco`
    - `dn_organization`: `pfSense Test`
    - `dn_organizationalunit`: `Testing`
    - `lifetime`: `3650`
2. **Execute** `pfsense_create_system_certificate_generate` with `confirm=True`:
    - `descr`: `bt_sys56_cert`
    - `keytype`: `RSA`
    - `keylen`: `2048`
    - `digest_alg`: `sha256`
    - `dn_commonname`: `renew-me.test`
    - `lifetime`: `365`
    - `type_`: `server`
3. **Execute** `pfsense_create_system_certificate_signing_request` with `confirm=True`:
    - `descr`: `bt_sys56_csr`
    - `keytype`: `RSA`
    - `keylen`: `2048`
    - `digest_alg`: `sha256`
    - `dn_commonname`: `sign-me.test`
4. **Execute** `pfsense_create_system_certificate_authority_renew` with `confirm=True` (Renew the generated CA. Needs CA refid.):
(no parameters needed)
5. **Execute** `pfsense_create_system_certificate_renew` with `confirm=True` (Renew the generated cert. Needs cert refid.):
(no parameters needed)
6. **Execute** `pfsense_create_system_certificate_signing_request_sign` with `confirm=True` (Sign the CSR with the CA. Needs CSR refid and CA refid.):
(no parameters needed)
7. **Execute** `pfsense_create_status_service` with `confirm=True` (Restart sshd service via POST.):
    - `name`: `sshd`
8. **Read** using `pfsense_get_status_openvpn_server_connection` (Get singular OVPN server connection — may 404 if none active)

**Important notes**:
PKI actions: renew CA, renew cert, sign CSR. All need refids from generated resources.
Service restart: POST to status/service to restart sshd.
Cleanup: delete generated certs and CA.

**Cleanup** (reverse order):
- No cleanup needed (read-only / settings restored)

**Expected outcome**: All 8 tools exercised successfully.
