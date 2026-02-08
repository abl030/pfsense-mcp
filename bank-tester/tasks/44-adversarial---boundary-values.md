## Task 44: Adversarial — Boundary Values

**task_id**: 44-adversarial-adversarial--boundary-values

**Objective**: Test error handling by intentionally sending bad inputs across multiple endpoints.

**Instructions**: For each test case below, make the API call exactly as specified. Record the error response quality: does it clearly explain what went wrong? Does it suggest the correct values?

**Steps**:
1. **Create alias with empty name**: Call `pfsense_create_firewall_alias` with `name=''`, `type_='host'`, `address=['10.0.0.1']`, `confirm=True`
   - Expected: validation error
   - Rate error message quality: clear/unclear/missing
2. **Create alias with very long name (200 chars)**: Call `pfsense_create_firewall_alias` with `name='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'`, `type_='host'`, `address=['10.0.0.1']`, `confirm=True`
   - Expected: validation error or truncation
   - Rate error message quality: clear/unclear/missing
3. **Create rule with special chars in descr**: Call `pfsense_create_firewall_rule` with `type_='pass'`, `interface='wan'`, `ipprotocol='inet'`, `protocol='tcp'`, `source='any'`, `destination='any'`, `descr="<script>alert('xss')</script>"`, `confirm=True`
   - Expected: either sanitized or error
   - Rate error message quality: clear/unclear/missing

**Expected outcome**: All calls should fail with clear error messages. No resources should be created.

**Cleanup**: None needed (all calls should fail).
