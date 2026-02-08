## Task 03: Firewall Rule

**task_id**: 03-firewall-rule

**Objective**: Create a firewall pass rule, verify it, update it, then clean up.

**Steps**:
1. Create a firewall rule that passes TCP traffic on port 8080 on the WAN interface
   - type: pass
   - interface: wan (this may need to be a list)
   - protocol: tcp
   - destination port: 8080
   - description: `bt_test_rule`
2. Apply firewall changes
3. List firewall rules and verify the new rule appears
4. Get the specific rule by ID
5. Update the rule's description to `bt_test_rule_updated`
6. Apply firewall changes
7. Delete the rule
8. Apply firewall changes

**Expected outcome**: Rule is created, verified, updated, and deleted. Note the `interface` field — it may require a list like `["wan"]` rather than a plain string.

**Cleanup**: Delete the rule (step 7). Apply after delete (step 8).
