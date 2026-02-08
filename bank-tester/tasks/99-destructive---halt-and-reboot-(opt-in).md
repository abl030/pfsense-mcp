## Task 99: Destructive — Halt & Reboot (opt-in)

**task_id**: 99-destructive

**Objective**: Test destructive operations (reboot, halt). Only run with INCLUDE_DESTRUCTIVE=1.

**Steps**:
1. Call `pfsense_post_diagnostics_reboot` with `confirm=True`
2. Wait 90 seconds for API to come back
3. Verify API is responding by calling `pfsense_get_system_version`
4. Call `pfsense_post_diagnostics_halt_system` with `confirm=True`

**Important notes**:
ONLY run with INCLUDE_DESTRUCTIVE=1. Reboot first, wait for API, then halt.
These will terminate the VM.

**Cleanup**: None (VM will be destroyed after halt).

**Expected outcome**: Reboot completes and API returns. Halt stops the VM.
