## Task 39: PUT Replace — All Plural Collection Replacements

**task_id**: 39-put-replace--all-plural-collection-replacements

**Objective**: Exercise all tools in the all subsystem through CRUD lifecycle, settings, and actions.

**Tools to exercise** (76):
- `pfsense_list_firewall_aliases`
- `pfsense_replace_firewall_aliases`
- `pfsense_list_firewall_rules`
- `pfsense_replace_firewall_rules`
- `pfsense_list_firewall_nat_port_forwards`
- `pfsense_replace_firewall_nat_port_forwards`
- `pfsense_list_firewall_nat_outbound_mappings`
- `pfsense_replace_firewall_nat_outbound_mappings`
- `pfsense_list_firewall_nat_one_to_one_mappings`
- `pfsense_replace_firewall_nat_one_to_one_mappings`
- `pfsense_list_firewall_schedules`
- `pfsense_replace_firewall_schedules`
- `pfsense_list_firewall_traffic_shapers`
- `pfsense_replace_firewall_traffic_shapers`
- `pfsense_list_firewall_traffic_shaper_limiters`
- `pfsense_replace_firewall_traffic_shaper_limiters`
- `pfsense_list_interface_groups`
- `pfsense_replace_interface_groups`
- `pfsense_list_services_acme_account_keys`
- `pfsense_replace_services_acme_account_keys`
- `pfsense_list_services_acme_certificates`
- `pfsense_replace_services_acme_certificates`
- `pfsense_list_services_bind_access_lists`
- `pfsense_replace_services_bind_access_lists`
- `pfsense_list_services_bind_views`
- `pfsense_replace_services_bind_views`
- `pfsense_list_services_bind_zones`
- `pfsense_replace_services_bind_zones`
- `pfsense_list_services_bind_sync_remote_hosts`
- `pfsense_replace_services_bind_sync_remote_hosts`
- `pfsense_list_services_cron_jobs`
- `pfsense_replace_services_cron_jobs`
- `pfsense_list_services_dhcp_servers`
- `pfsense_replace_services_dhcp_servers`
- `pfsense_list_services_dns_forwarder_host_overrides`
- `pfsense_replace_services_dns_forwarder_host_overrides`
- `pfsense_list_services_dns_resolver_access_lists`
- `pfsense_replace_services_dns_resolver_access_lists`
- `pfsense_list_services_dns_resolver_domain_overrides`
- `pfsense_replace_services_dns_resolver_domain_overrides`
- `pfsense_list_services_dns_resolver_host_overrides`
- `pfsense_replace_services_dns_resolver_host_overrides`
- `pfsense_list_services_free_radius_clients`
- `pfsense_replace_services_free_radius_clients`
- `pfsense_list_services_free_radius_interfaces`
- `pfsense_replace_services_free_radius_interfaces`
- `pfsense_list_services_free_radius_users`
- `pfsense_replace_services_free_radius_users`
- `pfsense_list_services_haproxy_backends`
- `pfsense_replace_services_haproxy_backends`
- `pfsense_list_services_haproxy_files`
- `pfsense_replace_services_haproxy_files`
- `pfsense_list_services_haproxy_frontends`
- `pfsense_replace_services_haproxy_frontends`
- `pfsense_list_services_ntp_time_servers`
- `pfsense_replace_services_ntp_time_servers`
- `pfsense_list_services_service_watchdogs`
- `pfsense_replace_services_service_watchdogs`
- `pfsense_list_system_tunables`
- `pfsense_replace_system_tunables`
- `pfsense_list_system_restapi_access_list`
- `pfsense_replace_system_restapi_access_list`
- `pfsense_list_user_auth_servers`
- `pfsense_replace_user_auth_servers`
- `pfsense_list_user_groups`
- `pfsense_replace_user_groups`
- `pfsense_list_vpn_ipsec_phase1s`
- `pfsense_replace_vpn_ipsec_phase1s`
- `pfsense_list_vpn_ipsec_phase2s`
- `pfsense_replace_vpn_ipsec_phase2s`
- `pfsense_list_vpn_openvpn_client_export_configs`
- `pfsense_replace_vpn_openvpn_client_export_configs`
- `pfsense_list_vpn_wireguard_peers`
- `pfsense_replace_vpn_wireguard_peers`
- `pfsense_list_vpn_wireguard_tunnels`
- `pfsense_replace_vpn_wireguard_tunnels`

**Steps**:
1. **List** current resources using `pfsense_list_firewall_aliases`
2. **Replace** using `pfsense_replace_firewall_aliases` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
3. **List** again using `pfsense_list_firewall_aliases` — verify nothing changed
4. **List** current resources using `pfsense_list_firewall_rules`
5. **Replace** using `pfsense_replace_firewall_rules` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
6. **List** again using `pfsense_list_firewall_rules` — verify nothing changed
7. **List** current resources using `pfsense_list_firewall_nat_port_forwards`
8. **Replace** using `pfsense_replace_firewall_nat_port_forwards` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
9. **List** again using `pfsense_list_firewall_nat_port_forwards` — verify nothing changed
10. **List** current resources using `pfsense_list_firewall_nat_outbound_mappings`
11. **Replace** using `pfsense_replace_firewall_nat_outbound_mappings` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
12. **List** again using `pfsense_list_firewall_nat_outbound_mappings` — verify nothing changed
13. **List** current resources using `pfsense_list_firewall_nat_one_to_one_mappings`
14. **Replace** using `pfsense_replace_firewall_nat_one_to_one_mappings` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
15. **List** again using `pfsense_list_firewall_nat_one_to_one_mappings` — verify nothing changed
16. **List** current resources using `pfsense_list_firewall_schedules`
17. **Replace** using `pfsense_replace_firewall_schedules` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
18. **List** again using `pfsense_list_firewall_schedules` — verify nothing changed
19. **List** current resources using `pfsense_list_firewall_traffic_shapers`
20. **Replace** using `pfsense_replace_firewall_traffic_shapers` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
21. **List** again using `pfsense_list_firewall_traffic_shapers` — verify nothing changed
22. **List** current resources using `pfsense_list_firewall_traffic_shaper_limiters`
23. **Replace** using `pfsense_replace_firewall_traffic_shaper_limiters` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
24. **List** again using `pfsense_list_firewall_traffic_shaper_limiters` — verify nothing changed
25. **List** current resources using `pfsense_list_interface_groups`
26. **Replace** using `pfsense_replace_interface_groups` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
27. **List** again using `pfsense_list_interface_groups` — verify nothing changed
28. **List** current resources using `pfsense_list_services_acme_account_keys`
29. **Replace** using `pfsense_replace_services_acme_account_keys` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
30. **List** again using `pfsense_list_services_acme_account_keys` — verify nothing changed
31. **List** current resources using `pfsense_list_services_acme_certificates`
32. **Replace** using `pfsense_replace_services_acme_certificates` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
33. **List** again using `pfsense_list_services_acme_certificates` — verify nothing changed
34. **List** current resources using `pfsense_list_services_bind_access_lists`
35. **Replace** using `pfsense_replace_services_bind_access_lists` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
36. **List** again using `pfsense_list_services_bind_access_lists` — verify nothing changed
37. **List** current resources using `pfsense_list_services_bind_views`
38. **Replace** using `pfsense_replace_services_bind_views` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
39. **List** again using `pfsense_list_services_bind_views` — verify nothing changed
40. **List** current resources using `pfsense_list_services_bind_zones`
41. **Replace** using `pfsense_replace_services_bind_zones` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
42. **List** again using `pfsense_list_services_bind_zones` — verify nothing changed
43. **List** current resources using `pfsense_list_services_bind_sync_remote_hosts`
44. **Replace** using `pfsense_replace_services_bind_sync_remote_hosts` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
45. **List** again using `pfsense_list_services_bind_sync_remote_hosts` — verify nothing changed
46. **List** current resources using `pfsense_list_services_cron_jobs`
47. **Replace** using `pfsense_replace_services_cron_jobs` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
48. **List** again using `pfsense_list_services_cron_jobs` — verify nothing changed
49. **List** current resources using `pfsense_list_services_dhcp_servers`
50. **Replace** using `pfsense_replace_services_dhcp_servers` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
51. **List** again using `pfsense_list_services_dhcp_servers` — verify nothing changed
52. **List** current resources using `pfsense_list_services_dns_forwarder_host_overrides`
53. **Replace** using `pfsense_replace_services_dns_forwarder_host_overrides` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
54. **List** again using `pfsense_list_services_dns_forwarder_host_overrides` — verify nothing changed
55. **List** current resources using `pfsense_list_services_dns_resolver_access_lists`
56. **Replace** using `pfsense_replace_services_dns_resolver_access_lists` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
57. **List** again using `pfsense_list_services_dns_resolver_access_lists` — verify nothing changed
58. **List** current resources using `pfsense_list_services_dns_resolver_domain_overrides`
59. **Replace** using `pfsense_replace_services_dns_resolver_domain_overrides` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
60. **List** again using `pfsense_list_services_dns_resolver_domain_overrides` — verify nothing changed
61. **List** current resources using `pfsense_list_services_dns_resolver_host_overrides`
62. **Replace** using `pfsense_replace_services_dns_resolver_host_overrides` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
63. **List** again using `pfsense_list_services_dns_resolver_host_overrides` — verify nothing changed
64. **List** current resources using `pfsense_list_services_free_radius_clients`
65. **Replace** using `pfsense_replace_services_free_radius_clients` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
66. **List** again using `pfsense_list_services_free_radius_clients` — verify nothing changed
67. **List** current resources using `pfsense_list_services_free_radius_interfaces`
68. **Replace** using `pfsense_replace_services_free_radius_interfaces` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
69. **List** again using `pfsense_list_services_free_radius_interfaces` — verify nothing changed
70. **List** current resources using `pfsense_list_services_free_radius_users`
71. **Replace** using `pfsense_replace_services_free_radius_users` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
72. **List** again using `pfsense_list_services_free_radius_users` — verify nothing changed
73. **List** current resources using `pfsense_list_services_haproxy_backends`
74. **Replace** using `pfsense_replace_services_haproxy_backends` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
75. **List** again using `pfsense_list_services_haproxy_backends` — verify nothing changed
76. **List** current resources using `pfsense_list_services_haproxy_files`
77. **Replace** using `pfsense_replace_services_haproxy_files` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
78. **List** again using `pfsense_list_services_haproxy_files` — verify nothing changed
79. **List** current resources using `pfsense_list_services_haproxy_frontends`
80. **Replace** using `pfsense_replace_services_haproxy_frontends` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
81. **List** again using `pfsense_list_services_haproxy_frontends` — verify nothing changed
82. **List** current resources using `pfsense_list_services_ntp_time_servers`
83. **Replace** using `pfsense_replace_services_ntp_time_servers` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
84. **List** again using `pfsense_list_services_ntp_time_servers` — verify nothing changed
85. **List** current resources using `pfsense_list_services_service_watchdogs`
86. **Replace** using `pfsense_replace_services_service_watchdogs` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
87. **List** again using `pfsense_list_services_service_watchdogs` — verify nothing changed
88. **List** current resources using `pfsense_list_system_tunables`
89. **Replace** using `pfsense_replace_system_tunables` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
90. **List** again using `pfsense_list_system_tunables` — verify nothing changed
91. **List** current resources using `pfsense_list_system_restapi_access_list`
92. **Replace** using `pfsense_replace_system_restapi_access_list` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
93. **List** again using `pfsense_list_system_restapi_access_list` — verify nothing changed
94. **List** current resources using `pfsense_list_user_auth_servers`
95. **Replace** using `pfsense_replace_user_auth_servers` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
96. **List** again using `pfsense_list_user_auth_servers` — verify nothing changed
97. **List** current resources using `pfsense_list_user_groups`
98. **Replace** using `pfsense_replace_user_groups` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
99. **List** again using `pfsense_list_user_groups` — verify nothing changed
100. **List** current resources using `pfsense_list_vpn_ipsec_phase1s`
101. **Replace** using `pfsense_replace_vpn_ipsec_phase1s` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
102. **List** again using `pfsense_list_vpn_ipsec_phase1s` — verify nothing changed
103. **List** current resources using `pfsense_list_vpn_ipsec_phase2s`
104. **Replace** using `pfsense_replace_vpn_ipsec_phase2s` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
105. **List** again using `pfsense_list_vpn_ipsec_phase2s` — verify nothing changed
106. **List** current resources using `pfsense_list_vpn_openvpn_client_export_configs`
107. **Replace** using `pfsense_replace_vpn_openvpn_client_export_configs` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
108. **List** again using `pfsense_list_vpn_openvpn_client_export_configs` — verify nothing changed
109. **List** current resources using `pfsense_list_vpn_wireguard_peers`
110. **Replace** using `pfsense_replace_vpn_wireguard_peers` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
111. **List** again using `pfsense_list_vpn_wireguard_peers` — verify nothing changed
112. **List** current resources using `pfsense_list_vpn_wireguard_tunnels`
113. **Replace** using `pfsense_replace_vpn_wireguard_tunnels` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body.
114. **List** again using `pfsense_list_vpn_wireguard_tunnels` — verify nothing changed

**Important notes**:
PUT replace operations: GET current → PUT same data back → verify (safe no-op).
Each replace call replaces the ENTIRE collection, so always fetch first.
Do NOT pass empty arrays — that would delete all resources.

**Cleanup** (reverse order):
- No cleanup needed (read-only / settings restored)

**Expected outcome**: All 76 tools exercised successfully.
