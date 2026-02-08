## Task 43: Adversarial — Confirm Gate Behavior

**task_id**: 43-adversarial-adversarial--confirm-gate-behavior

**Objective**: Test error handling by intentionally sending bad inputs across multiple endpoints.

**Instructions**: For each test case below, make the API call exactly as specified. Record the error response quality: does it clearly explain what went wrong? Does it suggest the correct values?

**Steps**:
1. **Call without confirm=True — should return preview, not execute**: Call `pfsense_create_firewall_alias` with `name='bt_adv43_alias'`, `type_='host'`, `address=['10.0.0.1']`
   - Expected: preview message mentioning POST and confirm=True
   - Rate error message quality: clear/unclear/missing
2. **Call delete without confirm=True — should return preview**: Call `pfsense_delete_firewall_alias` with `id=99999`
   - Expected: preview message mentioning DELETE and confirm=True
   - Rate error message quality: clear/unclear/missing
3. **Call update without confirm=True — should return preview**: Call `pfsense_update_system_dns` with `dnsallowoverride=False`
   - Expected: preview message mentioning PATCH and confirm=True
   - Rate error message quality: clear/unclear/missing
4. **Call apply without confirm=True — should return preview**: Call `pfsense_apply_firewall` with 
   - Expected: preview message mentioning POST and confirm=True
   - Rate error message quality: clear/unclear/missing

**Expected outcome**: All calls should fail with clear error messages. No resources should be created.

**Cleanup**: None needed (all calls should fail).
