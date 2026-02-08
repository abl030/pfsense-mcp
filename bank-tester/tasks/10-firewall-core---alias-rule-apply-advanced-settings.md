## Task 10: Firewall Core — Alias, Rule, Apply, Advanced Settings

**task_id**: 10-firewall-core--alias-rule-apply-advanced-settings

**Objective**: Exercise all tools in the firewall subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (14):
- `pfsense_create_firewall_alias`
- `pfsense_list_firewall_aliases`
- `pfsense_get_firewall_alias`
- `pfsense_update_firewall_alias`
- `pfsense_delete_firewall_alias`
- `pfsense_create_firewall_rule`
- `pfsense_list_firewall_rules`
- `pfsense_get_firewall_rule`
- `pfsense_update_firewall_rule`
- `pfsense_delete_firewall_rule`
- `pfsense_get_firewall_advanced_settings`
- `pfsense_update_firewall_advanced_settings`
- `pfsense_get_firewall_apply_status`
- `pfsense_firewall_apply`

**Steps**:
1. **Create** using `pfsense_create_firewall_alias` with `confirm=True`:
    - `name`: `bt_sys10_alias`
    - `type_`: `host`
    - `address`: `['10.0.10.1', '10.0.10.2']`
    - `descr`: `Bank tester alias`
2. **List** using `pfsense_list_firewall_aliases` — verify the created resource appears
3. **Get** using `pfsense_get_firewall_alias` with the ID from the create response
4. **Update** using `pfsense_update_firewall_alias` with `confirm=True` — set `descr` to `Updated by bank tester`
5. **Get** again using `pfsense_get_firewall_alias` — verify `descr` was updated
6. **Create** using `pfsense_create_firewall_rule` with `confirm=True`:
    - `type_`: `pass`
    - `interface`: `wan`
    - `ipprotocol`: `inet`
    - `protocol`: `tcp`
    - `source`: `any`
    - `destination`: `any`
    - `descr`: `bt_sys10_rule`
7. **List** using `pfsense_list_firewall_rules` — verify the created resource appears
8. **Get** using `pfsense_get_firewall_rule` with the ID from the create response
9. **Update** using `pfsense_update_firewall_rule` with `confirm=True` — set `descr` to `Updated rule`
10. **Get** again using `pfsense_get_firewall_rule` — verify `descr` was updated
11. **Get settings** using `pfsense_get_firewall_advanced_settings` — note current value of `aliasesresolveinterval`
12. **Update settings** using `pfsense_update_firewall_advanced_settings` with `confirm=True` — set `aliasesresolveinterval` to `600`
13. **Get settings** again using `pfsense_get_firewall_advanced_settings` — verify `aliasesresolveinterval` was updated
14. **Check apply status** using `pfsense_get_firewall_apply_status`
15. **Apply changes** using `pfsense_firewall_apply` with `confirm=True`

**Adversarial subtasks** (attempt once, record error quality):
17. Create alias without type_ field — expect error about required field
18. Create rule with protocol='bogus' — expect enum validation error

**Important notes**:
Create alias first, then rule (rule may reference alias).
Apply after each mutation. Read advanced_settings and patch one field.

**Cleanup** (reverse order):
- Delete using `pfsense_delete_firewall_rule` with `confirm=True` (ID from create step)
- Delete using `pfsense_delete_firewall_alias` with `confirm=True` (ID from create step)

**Expected outcome**: All 14 tools exercised successfully.
