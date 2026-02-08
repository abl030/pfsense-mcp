## Task 04: Port Forward Workflow

**task_id**: 04-port-forward-workflow

**Objective**: Create a NAT port forward rule that forwards external port 9090 to an internal host.

**Steps**:
1. Create a host alias named `bt_webserver` with type `host` containing IP `192.168.1.50`
2. Apply firewall changes
3. Create a NAT port forward rule:
   - interface: wan
   - protocol: tcp
   - destination port: 9090
   - target/redirect IP: 192.168.1.50
   - target/redirect port: 80
   - description: `bt_port_forward`
4. Apply firewall changes
5. List NAT port forward rules and verify the new rule appears
6. Get the specific rule by ID to verify details
7. Delete the NAT port forward rule
8. Apply firewall changes
9. Delete the alias `bt_webserver`
10. Apply firewall changes

**Expected outcome**: Port forward is created and verified. Cleanup removes both the NAT rule and the alias.

**Cleanup**: Delete NAT rule first (step 7), then alias (step 9). Apply after each delete.
