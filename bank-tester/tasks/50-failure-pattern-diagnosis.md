## Task 50: Failure Pattern Diagnosis

**task_id**: 50-failure-pattern-diagnosis

**Objective**: Attempt a series of operations across different subsystems. Some may succeed on the first try, some may not. For EVERY operation that fails or behaves unexpectedly, provide a detailed independent diagnosis. Classify each issue into exactly one of these root cause layers:

- **generator_bug**: The MCP tool generator produced incorrect schemas, parameter types, defaults, or docstrings
- **pfsense_api_bug**: The pfSense REST API itself has a bug or inconsistency
- **claude_code_bug**: The MCP client (Claude Code runtime) is doing something wrong in serialization, transport, or tool invocation
- **openapi_spec_issue**: The OpenAPI spec describes the API incorrectly or incompletely (e.g., marks fields as required when they're conditional)
- **expected_behavior**: This is how it's supposed to work — the consumer just needs to learn the right values or patterns

For each diagnosis, explain your reasoning in detail. What evidence did you use to reach your conclusion? What alternative explanations did you consider and rule out?

**Tools to exercise**:
- `pfsense_create_firewall_traffic_shaper_limiter`
- `pfsense_create_firewall_traffic_shaper_limiter_queue`
- `pfsense_update_firewall_traffic_shaper_limiter_queue`
- `pfsense_update_services_dns_resolver_settings`
- `pfsense_create_services_ha_proxy_backend`
- `pfsense_create_services_ha_proxy_frontend`
- `pfsense_create_services_ha_proxy_frontend_action`
- `pfsense_create_services_free_radius_user`
- `pfsense_update_services_free_radius_user`
- `pfsense_create_system_certificate_authority_generate`
- `pfsense_create_user_auth_server`
- `pfsense_create_vpni_psec_phase1`
- `pfsense_create_vpni_psec_phase2`
- `pfsense_create_auth_key`
- `pfsense_post_auth_jwt`
- `pfsense_get_diagnostics_table`
- `pfsense_get_system_package`
- `pfsense_list_firewall_aliases`
- `pfsense_replace_firewall_aliases`
- `pfsense_list_firewall_rules`
- `pfsense_replace_firewall_rules`
- `pfsense_list_user_groups`
- `pfsense_replace_user_groups`
- `pfsense_list_system_tunables`
- `pfsense_replace_system_tunables`
- `pfsense_delete_firewall_traffic_shaper_limiter_queue`
- `pfsense_delete_firewall_traffic_shaper_limiter`
- `pfsense_delete_services_ha_proxy_frontend`
- `pfsense_delete_services_ha_proxy_backend`
- `pfsense_delete_services_free_radius_user`
- `pfsense_delete_vpni_psec_phase2`
- `pfsense_delete_vpni_psec_phase1`
- `pfsense_firewall_apply`
- `pfsense_apply_haproxy`
- `pfsense_vpni_psec_apply`

**Steps**:

### Part 1: Traffic Shaper Limiter Queue Update

1. **Create** a traffic shaper limiter using `pfsense_create_firewall_traffic_shaper_limiter` with `confirm=True`:
    - `name`: `bt_diag_lim`
    - `sched`: `wf2q+`
    - `aqm`: `droptail`
    - `bandwidth`: `[{"bw": 100, "bwscale": "Mb", "schedule": "none"}]`
    - `enabled`: `False`
    - `mask`: `none`
    - `ecn`: `False`
    - `queue`: `[]`
2. **Create** a limiter queue using `pfsense_create_firewall_traffic_shaper_limiter_queue` with `confirm=True` (parent_id from step 1):
    - `name`: `bt_diag_limq`
    - `aqm`: `droptail`
3. **Update** the limiter queue using `pfsense_update_firewall_traffic_shaper_limiter_queue` with `confirm=True` — change `aqm` to `codel`
4. **Diagnose**: What happened? If it failed, what layer is the bug in? Examine the error message carefully.

### Part 2: DNS Resolver Settings Update

5. **Update** DNS resolver settings using `pfsense_update_services_dns_resolver_settings` with `confirm=True` — change `port` to `5353`
6. **Diagnose**: Did it require any fields you didn't expect? If so, why might those fields be marked as required?
7. **Restore** `port` back to `53`

### Part 3: HAProxy Frontend Action

8. **Create** an HAProxy backend using `pfsense_create_services_ha_proxy_backend` with `confirm=True`:
    - `name`: `bt_diag_be`
9. **Create** an HAProxy frontend using `pfsense_create_services_ha_proxy_frontend` with `confirm=True`:
    - `name`: `bt_diag_fe`
    - `backend`: the backend ID from step 8
    - `type_`: `http`
    - `status`: `active`
10. **Create** a frontend action using `pfsense_create_services_ha_proxy_frontend_action` with `confirm=True` (parent_id from step 9):
    - `action`: `http-request_lua`
    - `lua_function`: `test_func`
11. **Diagnose**: What happened? Were you asked for fields that don't seem relevant to the action type you chose? What does this tell you about how the API schema was designed?

### Part 4: FreeRADIUS User Update

12. **Create** a FreeRADIUS user using `pfsense_create_services_free_radius_user` with `confirm=True`:
    - `username`: `bt_diag_user`
    - `password`: `TestPass123`
13. **Update** the user using `pfsense_update_services_free_radius_user` with `confirm=True` — change only `descr` to `updated description`
14. **Diagnose**: Did the update require fields beyond what you were changing? If so, what does this suggest about how the API validates PATCH requests?

### Part 5: Certificate Authority Generation

15. **Generate** a self-signed RSA CA using `pfsense_create_system_certificate_authority_generate` with `confirm=True`:
    - `descr`: `bt_diag_ca`
    - `keylen`: `2048`
    - `digest`: `sha256`
    - `lifetime`: `365`
    - `dn_commonname`: `BT Diag CA`
    - `dn_country`: `US`
    - `dn_state`: `Texas`
    - `dn_city`: `Austin`
    - `dn_organization`: `BankTest`
    - `dn_organizationalunit`: `QA`
    - `trust`: `True`
16. **Diagnose**: Were there any fields the tool required that shouldn't be needed for a self-signed RSA certificate authority? What might explain this?

### Part 6: Authentication Server

17. **Create** an LDAP auth server using `pfsense_create_user_auth_server` with `confirm=True`:
    - `name`: `bt_diag_ldap`
    - `type_`: `ldap`
    - `host`: `10.0.0.100`
    - `ldap_port`: `389`
    - `ldap_urltype`: `TCP - Standard`
    - `ldap_scope`: `subtree`
    - `ldap_basedn`: `dc=example,dc=com`
    - `ldap_authcn`: `ou=Users,dc=example,dc=com`
18. **Diagnose**: Were you required to provide fields that only make sense for a different server type (e.g., RADIUS)? What does this tell you about the schema design?

### Part 7: IPsec Phase 1 and Phase 2

19. **Create** an IPsec Phase 1 using `pfsense_create_vpni_psec_phase1` with `confirm=True`:
    - `iketype`: `ikev2`
    - `protocol`: `inet`
    - `interface`: `wan`
    - `remote_gateway`: `10.99.99.50`
    - `authentication_method`: `pre_shared_key`
    - `pre_shared_key`: `DiagTestPSK123`
    - `myid_type`: `myaddress`
    - `peerid_type`: `peeraddress`
    - `descr`: `bt_diag_p1`
20. **Diagnose**: Were you asked for fields related to certificate authentication even though you're using pre-shared key? What about the encryption array?

21. **Create** an IPsec Phase 2 using `pfsense_create_vpni_psec_phase2` with `confirm=True` (use ikeid from step 19):
    - `mode`: `tunnel`
    - `localid_type`: `network`
    - `localid_address`: `10.50.0.0`
    - `localid_netbits`: `24`
    - `remoteid_type`: `network`
    - `remoteid_address`: `10.60.0.0`
    - `remoteid_netbits`: `24`
    - `protocol`: `esp`
    - `hash_algorithm_option`: `["sha256"]`
    - `descr`: `bt_diag_p2`
22. **Diagnose**: Did you encounter issues with field requirements or value formats? Look carefully at any enum validation errors and the hash algorithm values.

### Part 8: Authentication Endpoints

23. **Try** to create an API key using `pfsense_create_auth_key` with `confirm=True`
24. **Try** to get a JWT using `pfsense_post_auth_jwt` with `confirm=True` and `username`=`admin`, `password`=`pfsense`
25. **Diagnose**: What happened? Why might these endpoints behave differently from all other endpoints?

### Part 9: ID Format Discovery

26. **Try** to get a PF table using `pfsense_get_diagnostics_table` — pick whatever table name seems reasonable to you
27. **Try** to get a system package using `pfsense_get_system_package` — use a package name that you think exists on the system
28. **Diagnose**: Did the ID format match what you expected? What does this tell you about ID conventions across different endpoints?

### Part 10: PUT/Replace Operations

29. **List** current firewall aliases using `pfsense_list_firewall_aliases`
30. **Replace** using `pfsense_replace_firewall_aliases` with `confirm=True` — pass the exact data from step 29 as `items`
31. **List** current firewall rules using `pfsense_list_firewall_rules`
32. **Replace** using `pfsense_replace_firewall_rules` with `confirm=True` — pass the exact data from step 31 as `items`
33. **List** current user groups using `pfsense_list_user_groups`
34. **Replace** using `pfsense_replace_user_groups` with `confirm=True` — pass the exact data from step 33 as `items`
35. **List** current system tunables using `pfsense_list_system_tunables`
36. **Replace** using `pfsense_replace_system_tunables` with `confirm=True` — pass the exact data from step 35 as `items`
37. **Diagnose**: Did all four replace operations behave the same way? If not, compare the tool schemas, your invocations, and the error messages very carefully. What could explain any differences in behavior between tools that should be identical?

### Final Analysis

After completing all parts, provide a comprehensive `## Root Cause Analysis` section that:

1. Lists EVERY failure encountered with its root cause classification
2. Groups failures by root cause layer
3. Identifies any systemic patterns (are multiple failures caused by the same underlying issue?)
4. For each root cause layer, explains what would need to change to fix it
5. Ranks the issues by impact (how many operations does each issue affect?)

**Cleanup** (reverse order):
- Delete IPsec Phase 2 with `confirm=True`
- Delete IPsec Phase 1 with `confirm=True`
- Apply IPsec with `confirm=True`
- Delete FreeRADIUS user with `confirm=True`
- Delete HAProxy frontend with `confirm=True`
- Delete HAProxy backend with `confirm=True`
- Apply HAProxy with `confirm=True`
- Delete limiter queue with `confirm=True`
- Delete limiter with `confirm=True`
- Apply firewall with `confirm=True`

**Expected outcome**: Complete diagnosis of every failure encountered, with independent root cause analysis.
