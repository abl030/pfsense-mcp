## Task 09: Full Network Setup

**task_id**: 09-full-network-setup

**Objective**: Build a complete network setup with alias + firewall rule + NAT, verify everything, then tear it all down in reverse order.

**Steps**:
1. Create a host alias `bt_appservers` with type `host` containing `172.16.0.10` and `172.16.0.11`
2. Apply firewall
3. Create a firewall rule to pass TCP 443 on WAN with description `bt_https_rule`
4. Apply firewall
5. Create a NAT port forward: WAN TCP 8443 → 172.16.0.10:443, description `bt_nat_https`
6. Apply firewall
7. Verify all three resources exist (list aliases, list rules, list NAT rules)
8. Delete the NAT port forward
9. Apply firewall
10. Delete the firewall rule
11. Apply firewall
12. Delete the alias
13. Apply firewall
14. Verify all three resources are gone (list each type again)

**Expected outcome**: All resources created, verified, then cleaned up in reverse dependency order (NAT → rule → alias). Each step requires apply.

**Cleanup**: Steps 8-13 are the cleanup. Verify in step 14.
