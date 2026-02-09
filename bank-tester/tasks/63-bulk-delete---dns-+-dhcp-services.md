## Task 63: Bulk Delete — DNS + DHCP Services

**task_id**: 63-bulk-delete--dns-+-dhcp-services

**Objective**: Exercise all tools in the services subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (30):
- `pfsense_create_services_dns_resolver_host_override`
- `pfsense_list_services_dns_resolver_host_overrides`
- `pfsense_delete_services_dns_resolver_host_overrides`
- `pfsense_create_services_dns_resolver_host_override_alias`
- `pfsense_list_services_dns_resolver_host_override_aliases`
- `pfsense_delete_services_dns_resolver_host_override_aliases`
- `pfsense_create_services_dns_resolver_domain_override`
- `pfsense_list_services_dns_resolver_domain_overrides`
- `pfsense_delete_services_dns_resolver_domain_overrides`
- `pfsense_create_services_dns_resolver_access_list`
- `pfsense_list_services_dns_resolver_access_lists`
- `pfsense_delete_services_dns_resolver_access_lists`
- `pfsense_create_services_dns_resolver_access_list_network`
- `pfsense_list_services_dns_resolver_access_list_networks`
- `pfsense_delete_services_dns_resolver_access_list_networks`
- `pfsense_create_services_dns_forwarder_host_override`
- `pfsense_list_services_dns_forwarder_host_overrides`
- `pfsense_delete_services_dns_forwarder_host_overrides`
- `pfsense_create_services_dns_forwarder_host_override_alias`
- `pfsense_list_services_dns_forwarder_host_override_aliases`
- `pfsense_delete_services_dns_forwarder_host_override_aliases`
- `pfsense_create_services_dhcp_server_address_pool`
- `pfsense_list_services_dhcp_server_address_pools`
- `pfsense_delete_services_dhcp_server_address_pools`
- `pfsense_create_services_dhcp_server_static_mapping`
- `pfsense_list_services_dhcp_server_static_mappings`
- `pfsense_delete_services_dhcp_server_static_mappings`
- `pfsense_create_services_dhcp_server_custom_option`
- `pfsense_list_services_dhcp_server_custom_options`
- `pfsense_delete_services_dhcp_server_custom_options`

**Steps**:
1. **Create** a test resource using `pfsense_create_services_dns_resolver_host_override` with `confirm=True`:
    - `host`: `bt-bd63-ho`
    - `domain`: `example.com`
    - `ip`: `['10.99.63.1']`
    - `aliases`: `[]`
2. **List** using `pfsense_list_services_dns_resolver_host_overrides` — verify resource exists
3. **Bulk delete** using `pfsense_delete_services_dns_resolver_host_overrides` with `confirm=True` — delete ALL resources in this collection
4. **List** using `pfsense_list_services_dns_resolver_host_overrides` — verify collection is empty
5. **Create** a test resource using `pfsense_create_services_dns_resolver_host_override_alias` with `confirm=True` (use parent_id from the parent resource):
    - `host`: `testalias63`
    - `domain`: `alias63.example.com`
6. **List** using `pfsense_list_services_dns_resolver_host_override_aliases` — verify resource exists (Needs host override parent_id)
7. **Bulk delete** using `pfsense_delete_services_dns_resolver_host_override_aliases` with `confirm=True` — delete ALL resources in this collection
8. **List** using `pfsense_list_services_dns_resolver_host_override_aliases` — verify collection is empty
9. **Create** a test resource using `pfsense_create_services_dns_resolver_domain_override` with `confirm=True`:
    - `domain`: `bt-bd63.example.com`
    - `ip`: `10.99.63.2`
10. **List** using `pfsense_list_services_dns_resolver_domain_overrides` — verify resource exists
11. **Bulk delete** using `pfsense_delete_services_dns_resolver_domain_overrides` with `confirm=True` — delete ALL resources in this collection
12. **List** using `pfsense_list_services_dns_resolver_domain_overrides` — verify collection is empty
13. **Create** a test resource using `pfsense_create_services_dns_resolver_access_list` with `confirm=True`:
    - `action`: `allow`
    - `name`: `bt_bd63_dnsacl`
    - `networks`: `[]`
14. **List** using `pfsense_list_services_dns_resolver_access_lists` — verify resource exists
15. **Bulk delete** using `pfsense_delete_services_dns_resolver_access_lists` with `confirm=True` — delete ALL resources in this collection
16. **List** using `pfsense_list_services_dns_resolver_access_lists` — verify collection is empty
17. **Create** a test resource using `pfsense_create_services_dns_resolver_access_list_network` with `confirm=True` (use parent_id from the parent resource):
    - `network`: `10.63.0.0`
    - `mask`: `16`
18. **List** using `pfsense_list_services_dns_resolver_access_list_networks` — verify resource exists (Needs access list parent_id)
19. **Bulk delete** using `pfsense_delete_services_dns_resolver_access_list_networks` with `confirm=True` — delete ALL resources in this collection
20. **List** using `pfsense_list_services_dns_resolver_access_list_networks` — verify collection is empty
21. **Create** a test resource using `pfsense_create_services_dns_forwarder_host_override` with `confirm=True`:
    - `domain`: `example.com`
    - `host`: `bt-bd63-fho`
    - `ip`: `10.99.63.3`
    - `aliases`: `[]`
22. **List** using `pfsense_list_services_dns_forwarder_host_overrides` — verify resource exists
23. **Bulk delete** using `pfsense_delete_services_dns_forwarder_host_overrides` with `confirm=True` — delete ALL resources in this collection
24. **List** using `pfsense_list_services_dns_forwarder_host_overrides` — verify collection is empty
25. **Create** a test resource using `pfsense_create_services_dns_forwarder_host_override_alias` with `confirm=True` (use parent_id from the parent resource):
    - `host`: `testalias63f`
    - `domain`: `alias63f.example.com`
26. **List** using `pfsense_list_services_dns_forwarder_host_override_aliases` — verify resource exists (Needs host override parent_id)
27. **Bulk delete** using `pfsense_delete_services_dns_forwarder_host_override_aliases` with `confirm=True` — delete ALL resources in this collection
28. **List** using `pfsense_list_services_dns_forwarder_host_override_aliases` — verify collection is empty
29. **Create** a test resource using `pfsense_create_services_dhcp_server_address_pool` with `confirm=True`:
    - `range_from`: `192.168.1.220`
    - `range_to`: `192.168.1.230`
30. **List** using `pfsense_list_services_dhcp_server_address_pools` — verify resource exists (Uses static parent_id 'lan')
31. **Bulk delete** using `pfsense_delete_services_dhcp_server_address_pools` with `confirm=True` — delete ALL resources in this collection
32. **List** using `pfsense_list_services_dhcp_server_address_pools` — verify collection is empty
33. **Create** a test resource using `pfsense_create_services_dhcp_server_static_mapping` with `confirm=True`:
    - `mac`: `AA:BB:CC:DD:EE:63`
    - `ipaddr`: `192.168.1.245`
34. **List** using `pfsense_list_services_dhcp_server_static_mappings` — verify resource exists (Uses static parent_id 'lan')
35. **Bulk delete** using `pfsense_delete_services_dhcp_server_static_mappings` with `confirm=True` — delete ALL resources in this collection
36. **List** using `pfsense_list_services_dhcp_server_static_mappings` — verify collection is empty
37. **Create** a test resource using `pfsense_create_services_dhcp_server_custom_option` with `confirm=True`:
    - `number`: `253`
    - `type_`: `text`
    - `value`: `http://bd63.example.com`
38. **List** using `pfsense_list_services_dhcp_server_custom_options` — verify resource exists (Uses static parent_id 'lan')
39. **Bulk delete** using `pfsense_delete_services_dhcp_server_custom_options` with `confirm=True` — delete ALL resources in this collection
40. **List** using `pfsense_list_services_dhcp_server_custom_options` — verify collection is empty

**Important notes**:
Bulk delete DNS resolver, DNS forwarder, and DHCP sub-resources.
DNS sub-resources: create parent → sub-resource → bulk delete sub → delete parent.
DHCP sub-resources use static parent_id='lan'.

**Cleanup** (reverse order):
- No cleanup needed (read-only / settings restored)

**Expected outcome**: All 30 tools exercised successfully.
