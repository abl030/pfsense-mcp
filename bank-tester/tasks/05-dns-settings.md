## Task 05: DNS Settings

**task_id**: 05-dns-settings

**Objective**: Read DNS resolver settings and manage a host override.

**Steps**:
1. Get current DNS resolver settings
2. Create a DNS resolver host override:
   - host: `bt-testhost`
   - domain: `example.com`
   - IP address: `192.168.1.99`
   - description: `bt_dns_override`
3. Apply DNS resolver changes
4. List DNS resolver host overrides and verify the new entry appears
5. Get the specific host override by ID
6. Delete the host override
7. Apply DNS resolver changes
8. Verify the host override is gone

**Expected outcome**: Settings read succeeds. Host override CRUD works with apply pattern.

**Cleanup**: Delete the host override (step 6). Apply after delete (step 7).
