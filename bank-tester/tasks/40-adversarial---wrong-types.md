## Task 40: Adversarial — Wrong Types

**task_id**: 40-adversarial-adversarial--wrong-types

**Objective**: Test error handling by intentionally sending bad inputs across multiple endpoints.

**Instructions**: For each test case below, make the API call exactly as specified. Record the error response quality: does it clearly explain what went wrong? Does it suggest the correct values?

**Steps**:
1. **Send integer where string expected for 'name'**: Call `pfsense_create_firewall_alias` with `name=12345`, `type_='host'`, `address=['10.0.0.1']`, `confirm=True`
   - Expected: error about type
   - Rate error message quality: clear/unclear/missing
2. **Send string where boolean expected for 'disabled'**: Call `pfsense_create_firewall_rule` with `type_='pass'`, `interface='wan'`, `ipprotocol='inet'`, `protocol='tcp'`, `source='any'`, `destination='any'`, `disabled='yes'`, `confirm=True`
   - Expected: error about type
   - Rate error message quality: clear/unclear/missing
3. **Send string where list expected for 'dnsserver'**: Call `pfsense_update_system_dns` with `dnsserver='8.8.8.8'`, `confirm=True`
   - Expected: error about type
   - Rate error message quality: clear/unclear/missing
4. **Send boolean where string expected for 'username'**: Call `pfsense_create_user` with `username=True`, `password='test'`, `confirm=True`
   - Expected: error about type
   - Rate error message quality: clear/unclear/missing
5. **Send list where string expected for 'gateway'**: Call `pfsense_create_routing_gateway` with `name='bt_adv40_gw'`, `gateway=['10.0.2.1']`, `interface='wan'`, `ipprotocol='inet'`, `confirm=True`
   - Expected: error about type
   - Rate error message quality: clear/unclear/missing

**Expected outcome**: All calls should fail with clear error messages. No resources should be created.

**Cleanup**: None needed (all calls should fail).
