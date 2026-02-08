## Task 41: Adversarial — Missing Required Fields

**task_id**: 41-adversarial-adversarial--missing-required-fields

**Objective**: Test error handling by intentionally sending bad inputs across multiple endpoints.

**Instructions**: For each test case below, make the API call exactly as specified. Record the error response quality: does it clearly explain what went wrong? Does it suggest the correct values?

**Steps**:
1. **Omit required 'name' field**: Call `pfsense_create_firewall_alias` with `type_='host'`, `address=['10.0.0.1']`, `confirm=True`
   - Expected: error about missing required field
   - Rate error message quality: clear/unclear/missing
2. **Omit required 'type_' field**: Call `pfsense_create_firewall_rule` with `interface='wan'`, `protocol='tcp'`, `source='any'`, `destination='any'`, `confirm=True`
   - Expected: error about missing required field
   - Rate error message quality: clear/unclear/missing
3. **Omit required 'password' field**: Call `pfsense_create_user` with `username='bt_adv41_user'`, `confirm=True`
   - Expected: error about missing required field
   - Rate error message quality: clear/unclear/missing
4. **Omit required 'interface' field**: Call `pfsense_create_routing_gateway` with `name='bt_adv41_gw'`, `gateway='10.0.2.1'`, `ipprotocol='inet'`, `confirm=True`
   - Expected: error about missing required field
   - Rate error message quality: clear/unclear/missing
5. **Omit required 'iketype' field**: Call `pfsense_create_vpn_ipsec_phase1` with `protocol='inet'`, `interface='wan'`, `remote_gateway='10.0.2.1'`, `confirm=True`
   - Expected: error about missing required field
   - Rate error message quality: clear/unclear/missing

**Expected outcome**: All calls should fail with clear error messages. No resources should be created.

**Cleanup**: None needed (all calls should fail).
