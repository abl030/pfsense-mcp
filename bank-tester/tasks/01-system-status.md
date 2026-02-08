## Task 01: System Status Check

**task_id**: 01-system-status

**Objective**: Gather basic system information using read-only tools.

**Steps**:
1. Get the pfSense system version
2. Get the system hostname
3. Get gateway status (list all gateways)
4. Get current DHCP leases on the LAN interface
5. Get the system's current DNS server configuration

**Expected outcome**: All 5 queries return valid data. No mutations needed, no confirm required, no cleanup needed.

**Cleanup**: None required — all operations are read-only.
