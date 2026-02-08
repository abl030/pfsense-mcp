## Task 32: VPN IPsec — Phase 1, Phase 2, Encryption, Apply

**task_id**: 32-vpn-ipsec--phase-1-phase-2-encryption-apply

**Objective**: Exercise all tools in the vpn/ipsec subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (18):
- `pfsense_create_vpni_psec_phase1`
- `pfsense_list_vpni_psec_phase1_encryptions`
- `pfsense_get_vpni_psec_phase1`
- `pfsense_update_vpni_psec_phase1`
- `pfsense_delete_vpni_psec_phase1`
- `pfsense_create_vpni_psec_phase1_encryption`
- `pfsense_get_vpni_psec_phase1_encryption`
- `pfsense_delete_vpni_psec_phase1_encryption`
- `pfsense_create_vpni_psec_phase2`
- `pfsense_list_vpni_psec_phase2_encryptions`
- `pfsense_get_vpni_psec_phase2`
- `pfsense_update_vpni_psec_phase2`
- `pfsense_delete_vpni_psec_phase2`
- `pfsense_create_vpni_psec_phase2_encryption`
- `pfsense_get_vpni_psec_phase2_encryption`
- `pfsense_delete_vpni_psec_phase2_encryption`
- `pfsense_get_vpni_psec_apply_status`
- `pfsense_vpni_psec_apply`

**Steps**:
1. **Create** using `pfsense_create_vpni_psec_phase1` with `confirm=True`:
    - `iketype`: `ikev2`
    - `protocol`: `inet`
    - `interface`: `wan`
    - `remote_gateway`: `10.99.99.20`
    - `authentication_method`: `pre_shared_key`
    - `pre_shared_key`: `TestPSK123456`
    - `myid_type`: `myaddress`
    - `peerid_type`: `peeraddress`
    - `descr`: `bt_sys32_p1`
2. **List** using `pfsense_list_vpni_psec_phase1_encryptions` — verify the created resource appears
3. **Get** using `pfsense_get_vpni_psec_phase1` with the ID from the create response
4. **Update** using `pfsense_update_vpni_psec_phase1` with `confirm=True` — set `descr` to `Updated P1`
5. **Get** again using `pfsense_get_vpni_psec_phase1` — verify `descr` was updated
6. **Create** using `pfsense_create_vpni_psec_phase1_encryption` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `encryption_algorithm_name`: `aes`
    - `encryption_algorithm_keylen`: `256`
    - `hash_algorithm`: `sha256`
    - `dhgroup`: `14`
7. **List** using `pfsense_list_vpni_psec_phase1_encryptions` — verify the created resource appears
8. **Get** using `pfsense_get_vpni_psec_phase1_encryption` with the ID from the create response
9. **Create** using `pfsense_create_vpni_psec_phase2` with `confirm=True` (inject `ikeid` from parent's `ikeid` field):
    - `mode`: `tunnel`
    - `localid_type`: `network`
    - `localid_address`: `10.0.0.0`
    - `localid_netbits`: `24`
    - `remoteid_type`: `network`
    - `remoteid_address`: `10.200.0.0`
    - `remoteid_netbits`: `24`
    - `protocol`: `esp`
    - `descr`: `bt_sys32_p2`
10. **List** using `pfsense_list_vpni_psec_phase2_encryptions` — verify the created resource appears
11. **Get** using `pfsense_get_vpni_psec_phase2` with the ID from the create response
12. **Update** using `pfsense_update_vpni_psec_phase2` with `confirm=True` — set `descr` to `Updated P2`
13. **Get** again using `pfsense_get_vpni_psec_phase2` — verify `descr` was updated
14. **Create** using `pfsense_create_vpni_psec_phase2_encryption` with `confirm=True` (use the `parent_id` from the parent resource created earlier):
    - `encryption_algorithm_name`: `aes`
    - `encryption_algorithm_keylen`: `256`
    - `hash_algorithm`: `sha256`
15. **List** using `pfsense_list_vpni_psec_phase2_encryptions` — verify the created resource appears
16. **Get** using `pfsense_get_vpni_psec_phase2_encryption` with the ID from the create response
17. **Check apply status** using `pfsense_get_vpni_psec_apply_status`
18. **Apply changes** using `pfsense_vpni_psec_apply` with `confirm=True`

**Important notes**:
Phase 2 references Phase 1 via ikeid. Encryption sub-resources reference their parent.
Use aes (AES-CBC) with keylen=256, NOT aes256gcm.
Cleanup: P2 enc → P2 → P1 enc → P1. Apply after each mutation.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_vpni_psec_phase2_encryption` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_vpni_psec_phase2` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_vpni_psec_phase1_encryption` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_vpni_psec_phase1` with `confirm=True` (ID from create step)

**Expected outcome**: All 18 tools exercised successfully.
