## Task 08: Diagnostics

**task_id**: 08-diagnostics

**Objective**: Use diagnostic/status tools to gather system information.

**Steps**:
1. View the ARP table
2. Get network interface status (all interfaces)
3. Get system logs with a limit of 20 entries
4. Run a ping to 127.0.0.1 (localhost) with count of 3

**Expected outcome**: All diagnostic queries return valid data. Ping is an action endpoint (POST) that requires confirm=True.

**Cleanup**: None required — diagnostics are read-only (ping is ephemeral).
