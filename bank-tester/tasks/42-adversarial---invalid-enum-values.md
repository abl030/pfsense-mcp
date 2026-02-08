## Task 42: Adversarial — Invalid Enum Values

**task_id**: 42-adversarial-adversarial--invalid-enum-values

**Objective**: Test error handling by intentionally sending bad inputs across multiple endpoints.

**Instructions**: For each test case below, make the API call exactly as specified. Record the error response quality: does it clearly explain what went wrong? Does it suggest the correct values?

**Steps**:
1. **Use invalid alias type**: Call `pfsense_create_firewall_alias` with `name='bt_adv42_alias'`, `type_='bogus_type'`, `confirm=True`
   - Expected: error listing valid enum values
   - Rate error message quality: clear/unclear/missing
2. **Use invalid protocol**: Call `pfsense_create_firewall_rule` with `type_='pass'`, `interface='wan'`, `ipprotocol='inet'`, `protocol='bogus_protocol'`, `source='any'`, `destination='any'`, `confirm=True`
   - Expected: error listing valid enum values
   - Rate error message quality: clear/unclear/missing
3. **Use invalid iketype**: Call `pfsense_create_vpn_ipsec_phase1` with `iketype='ikev99'`, `protocol='inet'`, `interface='wan'`, `remote_gateway='10.0.2.1'`, `confirm=True`
   - Expected: error listing valid enum values
   - Rate error message quality: clear/unclear/missing
4. **Use invalid auth server type**: Call `pfsense_create_user_auth_server` with `name='bt_adv42_auth'`, `type_='kerberos'`, `host='10.0.0.1'`, `confirm=True`
   - Expected: error listing valid enum values
   - Rate error message quality: clear/unclear/missing
5. **Use invalid NAT outbound mode**: Call `pfsense_update_firewall_nat_outbound_mode` with `mode='turbo'`, `confirm=True`
   - Expected: error listing valid enum values
   - Rate error message quality: clear/unclear/missing

**Expected outcome**: All calls should fail with clear error messages. No resources should be created.

**Cleanup**: None needed (all calls should fail).
