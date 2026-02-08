## Task 15: Firewall States

**task_id**: 15-firewall-states

**Objective**: Exercise all tools in the firewall/state subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (2):
- `pfsense_get_firewall_states_size`
- `pfsense_update_firewall_states_size`

**Steps**:
1. **Get settings** using `pfsense_get_firewall_states_size` — note current value of `maximumstates`
2. **Update settings** using `pfsense_update_firewall_states_size` with `confirm=True` — set `maximumstates` to `500000`
3. **Get settings** again using `pfsense_get_firewall_states_size` — verify `maximumstates` was updated

**Important notes**:
States are read-only (listing current state table). States/size is a singleton.
List states, read states/size, patch states/size.
Do NOT delete all states (destructive).

**Cleanup** (reverse order):
- No cleanup needed (read-only / settings restored)

**Expected outcome**: All 2 tools exercised successfully.
