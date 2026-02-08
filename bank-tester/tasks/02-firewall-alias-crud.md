## Task 02: Firewall Alias CRUD

**task_id**: 02-firewall-alias-crud

**Objective**: Perform a full create-read-update-delete cycle on a firewall alias.

**Steps**:
1. Create a host alias named `bt_testservers` with type `host` containing IPs `10.0.0.1` and `10.0.0.2`
2. Apply firewall changes
3. List all aliases and verify `bt_testservers` appears
4. Get the specific alias by its ID
5. Update the alias to add a third IP `10.0.0.3`
6. Apply firewall changes
7. Get the alias again to verify all 3 IPs present
8. Delete the alias
9. Apply firewall changes
10. List aliases to confirm it is gone

**Expected outcome**: Full CRUD cycle completes. The alias type field may be named `type` or `type_` — try both if needed.

**Cleanup**: Delete the alias created in step 1 (step 8). Apply after delete (step 9).
