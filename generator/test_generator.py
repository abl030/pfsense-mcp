"""
Generate integration tests for every API endpoint.

Produces generated/tests.py which tests all endpoints against a live pfSense VM.
Test categories:
  - CRUD lifecycle: create → get → list → update → delete
  - Settings: get → update (roundtrip) → verify
  - Read-only: GET returns 200
  - Apply: GET status returns 200
  - Plural: list returns array

Skips dangerous endpoints (halt, reboot, command_prompt, etc).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .context_builder import ToolContext, _DANGEROUS_ENDPOINTS
from .schema_parser import ToolParameter

# Plural routes that exist in the OpenAPI spec but return nginx 404 on the real server.
# These are sub-resource plural endpoints whose singular forms require parent_id.
# The pfSense REST API simply doesn't register these routes.
_PHANTOM_PLURAL_ROUTES = {
    "/api/v2/diagnostics/tables",
    "/api/v2/firewall/schedule/time_ranges",
    "/api/v2/firewall/traffic_shaper/limiter/bandwidths",
    "/api/v2/firewall/traffic_shaper/limiter/queues",
    "/api/v2/firewall/traffic_shaper/queues",
    "/api/v2/routing/gateway/group/priorities",
    "/api/v2/services/dns_forwarder/host_override/aliases",
    "/api/v2/services/dns_resolver/host_override/aliases",
    "/api/v2/services/dns_resolver/access_list/networks",
    "/api/v2/vpn/wireguard/tunnel/addresses",
    "/api/v2/vpn/wireguard/peer/allowed_ips",
    "/api/v2/vpn/ipsec/phase1/encryptions",
    "/api/v2/vpn/ipsec/phase2/encryptions",
    "/api/v2/vpn/openvpn/client_export/configs",
    "/api/v2/services/dhcp_server/address_pools",
    "/api/v2/services/dhcp_server/custom_options",
    "/api/v2/services/dhcp_server/static_mappings",
    "/api/v2/status/openvpn/server/connections",
    "/api/v2/status/openvpn/server/routes",
    "/api/v2/status/ipsec/child_sas",
    "/api/v2/status/logs/auth",
    "/api/v2/status/logs/openvpn",
    "/api/v2/status/logs/packages/restapi",
    # HAProxy sub-resource plurals (require parent_id on singular form)
    "/api/v2/services/haproxy/settings/dns_resolvers",
    "/api/v2/services/haproxy/settings/email_mailers",
    "/api/v2/services/haproxy/frontend/certificates",
    "/api/v2/services/haproxy/backend/acls",
    "/api/v2/services/haproxy/backend/actions",
    "/api/v2/services/haproxy/backend/errorfiles",
    "/api/v2/services/haproxy/backend/servers",
    "/api/v2/services/haproxy/frontend/acls",
    "/api/v2/services/haproxy/frontend/actions",
    "/api/v2/services/haproxy/frontend/addresses",
    "/api/v2/services/haproxy/frontend/error_files",
    # BIND sub-resource plurals
    "/api/v2/services/bind/access_list/entries",
    "/api/v2/services/bind/sync/domains",
    # FreeRADIUS - all endpoints return nginx 404 despite package installed
    # (possibly needs service restart or different package version)
    "/api/v2/services/freeradius/clients",
    "/api/v2/services/freeradius/interfaces",
    "/api/v2/services/freeradius/users",
    # Status endpoints for unconfigured services
    "/api/v2/status/openvpn/server/connection",
    "/api/v2/status/openvpn/server/route",
    "/api/v2/status/ipsec/child_sa",
}

# Test value generators by field name pattern
_TEST_VALUES: dict[str, str] = {
    # Network - IP addresses
    "interface": '"wan"',
    "if_": '"vtnet0"',
    "ipaddr": '"static"',
    "ipaddrv6": '"none"',
    "subnet": '"24"',
    "subnetv6": "128",
    "subnet_bits": "32",
    "source": '"any"',
    "destination": '"any"',
    "target": '"127.0.0.1"',
    "external": '"10.99.99.1"',
    "ip": '"10.99.99.2"',
    "addr": '"10.99.99.3"',
    "address": '["10.99.99.1"]',
    "network": '"10.99.99.0/24"',
    "remote_addr": '"10.99.99.4"',
    "tunnel_local_addr": '"10.99.99.10"',
    "tunnel_remote_addr": '"10.99.99.5"',
    "tunnel_local_addr6": '"fd00::10"',
    "tunnel_remote_addr6": '"fd00::1"',
    "remote_gateway": '"10.99.99.20"',
    "server_addr": '"10.99.99.30"',
    "endpoint": '"10.99.99.40"',
    "monitor": '"10.99.99.50"',
    "trap_server": '"10.99.99.60"',
    "trap_string": '"public"',
    "carp_peer": '"10.99.99.6"',
    "failover_peerip": '"10.99.99.70"',
    # Network - ports
    "local_port": '"8080"',
    "source_port": '"443"',
    "destination_port": '"80"',
    "port": '"443"',
    "listenport": '"51820"',
    "ldap_port": '"389"',
    "radius_srvcs": '"auth"',
    "radius_auth_port": '"1812"',
    "radius_acct_port": '"1813"',
    # Gateways
    "gateway": '""',  # empty string = default gateway
    "gateway_6rd": '""',
    "prefix_6rd": '""',
    "prefix_6rd_v4plen": "0",
    "track6_interface": '""',
    "vhid": "1",
    # Gateway monitoring
    "latencylow": "200",
    "latencyhigh": "500",
    "losslow": "10",
    "losshigh": "20",
    # Identity
    "name": None,  # handled specially in _test_value_for_param
    "descr": '"Test created by generator"',
    "ifname": '"pf_test_{unique}"',
    "host": '"10.99.99.70"',
    "domain": '"example.com"',
    "username": '"pfsense_test_user"',
    "password": '"Testpass123!Abc"',
    "server": '"10.99.99.7"',
    "expires": '"12/31/2030"',
    # Enums (first value used unless overridden)
    "ipprotocol": '"inet"',
    "protocol": '"tcp"',
    "mode": None,  # use first enum
    "type_": None,  # use first enum
    "action": None,  # use first enum
    "method": None,  # use first enum
    # Traffic shaper
    "mask": None,  # use first enum (context-dependent)
    "bandwidthtype": '"Mb"',
    "bwscale": '"Mb"',
    "scheduler": '"HFSC"',
    "aqm": '"droptail"',
    "sched": None,  # use first enum or skip
    "linkshare_m2": '"10%"',
    "realtime_m2": '""',
    "upperlimit_m2": '""',
    "buckets": "16",
    # Crypto
    "caref": None,  # skip - needs CA
    "certref": None,  # skip - needs cert
    "keytype": '"RSA"',
    "keylen": "2048",
    "ecname": '"prime256v1"',
    "digest_alg": '"sha256"',
    "certificate": '""',
    "public_key": '""',
    "crt": None,  # skip - needs real PEM data
    "prv": None,  # skip - needs real PEM private key
    # Numeric
    "bandwidth": "100",
    "bw": "100",
    "qlimit": "50",
    "parent_id": None,  # handled by CRUD chaining
    "value": '"1"',
    "command": '"echo test"',
    # Scheduling - cron fields
    "hour": '"0"',
    "mday": '"*"',
    "wday": '"*"',
    "month": '"*"',
    "minute": '"0"',
    "who": '"root"',
    # Scheduling - firewall schedule
    "timerange": '[{"month": "1,2,3", "day": "1,2,3", "hour": "0:00-23:59", "position": []}]',
    # Arrays that need minimum entries
    "priorities": '[{"gateway": "WAN_DHCP", "tier": 1, "virtual_ip": ""}]',
    "members": '["wan"]',
    # HAProxy
    "backend": '"none"',
    # VPN
    "peer_public_key": '"dGVzdA=="',  # base64 "test"
    "tunnel_network": '"10.100.0.0/24"',
    "local_network": '"10.0.0.0/24"',
    "remote_network": '"10.200.0.0/24"',
    # LDAP
    "ldap_urltype": '"Standard TCP"',
    "ldap_protver": "3",
    "ldap_scope": '"one"',
    "ldap_basedn": '"dc=example,dc=com"',
    "ldap_authcn": '"ou=people,dc=example,dc=com"',
    "ldap_extended_enabled": "False",
    "ldap_attr_user": '"uid"',
    "ldap_attr_group": '"cn"',
    "ldap_attr_member": '"member"',
    "ldap_attr_groupobj": '"posixGroup"',
    "ldap_timeout": "25",
    # RADIUS
    "radius_timeout": "5",
    "radius_nasip_attribute": '"lan"',
    # HAProxy specifics
    "forwardfor": '"yes"',
    "httpclose": '"http-keep-alive"',
    "http_process_requests": '"enabled"',
    # BIND specifics
    "bind_forwarder": '"10.99.99.80"',
    "baseip": '"10.99.99.0"',
    "entries": '[{"value": "10.0.0.0/8", "description": "test"}]',
    # Email fields
    "email": '"test@example.com"',
    "email_to": '"test@example.com"',
    "email_from": '"noreply@example.com"',
    # Routing gateway timing
    "loss_interval": "2000",
    "time_period": "60000",
    "interval": "500",
    "alert_interval": "1000",
    # HAProxy backend
    "backend_serverpool": '""',
    # WireGuard
    "privatekey": '"YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY="',
    "publickey": '"YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY="',
    "addresses": '[]',
    # SNMP
    "rocommunity": '"public"',
    "trapenable": "False",
    # Auth server (LDAP)
    "type": None,  # use first enum
}

# Per-endpoint overrides for fields that mean different things in different contexts
_ENDPOINT_OVERRIDES: dict[str, dict[str, str]] = {
    "/api/v2/firewall/virtual_ip": {
        "subnet": '"10.99.99.100"',  # virtual_ip subnet is an IP, not a prefix length
    },
    "/api/v2/services/service_watchdog": {
        "name": '"sshd"',  # must reference an existing system service
    },
    "/api/v2/vpn/wireguard/peer": {
        "tun": '"tun_wg0"',  # must reference existing tunnel
        "publickey": '"YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY="',  # valid base64
    },
    "/api/v2/services/dhcp_relay": {
        "server": '["10.99.99.7"]',  # must be array
    },
    "/api/v2/services/acme/account_key": {
        "email": '"test@example.com"',
    },
    "/api/v2/services/haproxy/backend": {
        "email_to": '"test@example.com"',
    },
    "/api/v2/services/haproxy/file": {
        "name": '"pft_haproxy"',
    },
    "/api/v2/services/bind/zone": {
        "baseip": '"10.99.99.0"',
    },
    "/api/v2/services/bind/access_list": {
        "entries": '[{"value": "10.0.0.0/8", "description": "test entry"}]',
    },
    "/api/v2/user/auth_server": {
        "type": '"ldap"',
        "ldap_port": '"389"',
    },
    "/api/v2/vpn/wireguard/tunnel": {
        "listenport": '"51820"',
        "privatekey": '"YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY="',
    },
    "/api/v2/routing/gateway": {
        "gateway": '"10.0.2.1"',  # use the default QEMU gateway IP
        "loss_interval": "2000",
        "latencyhigh": "500",
        "latencylow": "200",
        "losshigh": "20",
        "losslow": "10",
    },
    "/api/v2/firewall/traffic_shaper/limiter": {
        "bandwidth": '[{"bw": 100, "bwscale": "Mb", "schedule": "none"}]',
        "sched": '"wf2q+"',
    },
    "/api/v2/firewall/nat/port_forward": {
        "associated_rule_id": '""',  # empty = no associated rule
    },
    "/api/v2/services/acme/account_key": {
        "email": '"test@example.com"',
        "acmeserver": '"letsencrypt-staging-2"',
    },
    "/api/v2/firewall/rule": {
        "gateway": None,  # omit — uses system default routing
        "defaultqueue": None,  # omit — references non-existent traffic shaper queue
        "ackqueue": None,  # omit — references non-existent traffic shaper queue
        "dnpipe": None,  # omit — references non-existent limiter
        "pdnpipe": None,  # omit — references non-existent limiter
        "sched": None,  # omit — references non-existent schedule
    },
}

# Endpoints that should be completely skipped for CRUD tests
_SKIP_CRUD_PATHS: dict[str, str] = {
    "/api/v2/interface": "requires available physical interface",
    "/api/v2/interface/lagg": "requires multiple physical interfaces",
    "/api/v2/interface/gre": "requires specific tunnel config",
    "/api/v2/interface/gif": "requires specific tunnel config",
    "/api/v2/vpn/ipsec/phase2": "requires existing phase1 with certs",
    "/api/v2/vpn/openvpn/cso": "requires existing OpenVPN server",
    "/api/v2/vpn/openvpn/client_export/config": "requires OpenVPN server configured",
    "/api/v2/services/dhcp_server": "per-interface singleton, POST not supported",
    # FreeRADIUS routes return nginx 404 despite package installed
    "/api/v2/services/freeradius/client": "freeradius routes not registered",
    "/api/v2/services/freeradius/interface": "freeradius routes not registered",
    "/api/v2/services/freeradius/user": "freeradius routes not registered",
    # ACME certificate requires existing ACME account key + DNS validation
    "/api/v2/services/acme/certificate": "requires existing ACME account key and DNS setup",
    # HAProxy sub-resources needing deep chains (action→acl FK, error_file→file FK)
    "/api/v2/services/haproxy/backend/action": "requires valid action enum + context",
    "/api/v2/services/haproxy/backend/error_file": "requires existing HAProxy file FK",
    "/api/v2/services/haproxy/frontend/action": "requires existing ACL FK",
    "/api/v2/services/haproxy/frontend/error_file": "requires existing HAProxy file FK",
    # HAProxy settings sub-resources return 500 (requires parent model)
    "/api/v2/services/haproxy/settings/dns_resolver": "server error: requires parent model",
    "/api/v2/services/haproxy/settings/email_mailer": "server error: requires parent model",
}

# ── Pre-generated test PEM certificates ───────────────────────────────────────
# Self-signed CA and server cert for testing certificate endpoints.
# Generated with: openssl req -x509 -newkey rsa:2048 ...
_TEST_CA_CERT_PEM = (
    "-----BEGIN CERTIFICATE-----\\n"
    "MIIDMzCCAhugAwIBAgIUbtFPoQ0zYg1ScUJ7+FnklDgHgh8wDQYJKoZIhvcNAQEL\\n"
    "BQAwKTEQMA4GA1UEAwwHVGVzdCBDQTEVMBMGA1UECgwMcGZTZW5zZSBUZXN0MB4X\\n"
    "DTI2MDIwNzAxMjYyMloXDTM2MDIwNTAxMjYyMlowKTEQMA4GA1UEAwwHVGVzdCBD\\n"
    "QTEVMBMGA1UECgwMcGZTZW5zZSBUZXN0MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A\\n"
    "MIIBCgKCAQEAs3inegnOteSWo/iRAV5YUZ7tx1pDni+cdDcNkDgPubrM9baB/EVP\\n"
    "A1CqpV1F20YcHu9o2H/BS308cCwOxNFuarjsTzHgrH7WG9gwUvXfDPkJ08ivvWxS\\n"
    "4WXsVqP6OQ7iOgJpDTx0ALyBLq2isW2/nn5Eubs9SL65pk8FBMe6cZ/JVRQ2KUwo\\n"
    "HwKq+HR6qBhrLFeAFVBHB/NXjQHWT7Kkym9nPA8RMwvkXyQZj8vXL8gWwqFEY7dk\\n"
    "x8hpJ10vnRjWz3afNeP9qRLBlIxdz0NlrbaZ/Xh/h+2pQX3i8S4cyTYDF56Cw98X\\n"
    "PjWoOi45TlZ33cbh7YsgyODZcmr1WOeRSQIDAQABo1MwUTAdBgNVHQ4EFgQUNKKH\\n"
    "IC1T0pAoUUXO2+TT488p45AwHwYDVR0jBBgwFoAUNKKHIC1T0pAoUUXO2+TT488p\\n"
    "45AwDwYDVR0TAQH/BAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEAonF1YEnW+vSp\\n"
    "jRxq+vB3foaHUkiEDP4ipDdknZgu19JKW+NSEvz9mAKU1zVnN621I1JURuDELBTN\\n"
    "Ba5oa1BnAQ3kzEtGr/yJZh477i15L/FBUvTjUQlnftKSJF22BD0YamALSsdHyJaS\\n"
    "l6a8YdaFV2muzjk0aDFutMk1kESiUh02FY5dU8MTPcarGSqUFBxT9TqGYlf7TcEI\\n"
    "A35EDCIbEzkqUofzzp70rXN1Z9TdR/rf74waSn4/tPhF5/Eosf0+hC/IRz1V+3+6\\n"
    "bCIx8M+jzQZU8u92iAnZkp9rGgBZZnonZ6phI0WAR67UBSvD5939DGlqDiQjMsuX\\n"
    "z+e3gqRxKQ==\\n"
    "-----END CERTIFICATE-----"
)

_TEST_CA_KEY_PEM = (
    "-----BEGIN PRIVATE KEY-----\\n"
    "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCzeKd6Cc615Jaj\\n"
    "+JEBXlhRnu3HWkOeL5x0Nw2QOA+5usz1toH8RU8DUKqlXUXbRhwe72jYf8FLfTxw\\n"
    "LA7E0W5quOxPMeCsftYb2DBS9d8M+QnTyK+9bFLhZexWo/o5DuI6AmkNPHQAvIEu\\n"
    "raKxbb+efkS5uz1IvrmmTwUEx7pxn8lVFDYpTCgfAqr4dHqoGGssV4AVUEcH81eN\\n"
    "AdZPsqTKb2c8DxEzC+RfJBmPy9cvyBbCoURjt2THyGknXS+dGNbPdp814/2pEsGU\\n"
    "jF3PQ2Wttpn9eH+H7alBfeLxLhzJNgMXnoLD3xc+Nag6LjlOVnfdxuHtiyDI4Nly\\n"
    "avVY55FJAgMBAAECggEAAWVrDsjRv1oqY9cqBZ6JcFpx/hmGf3izrmHD7L8gPDEm\\n"
    "/rMEmtpNLY5B7ZcRVTiGknpepe8vKUUC+dprOP5qGKbHS9cW/jCJvjNgg4dfIgIz\\n"
    "9d5Qo61v4vSrMddaZHmS//bcgK+w3//sv1i2ycuRReHfQKn4uulPl2rI9AsRDmji\\n"
    "RWry7Dz5of17vvKe63N/sdmsDNo0RphucTBVnLw/MsDI5WXjMYqCILC/CBNhM3Ey\\n"
    "emPUaZucUGc6AY+BMzF7XrYNaHL3IkN06dC8Iyn7h2v/gSSuknTa2zfUw5nBSlja\\n"
    "m+wmFswXWf7OSsT1SV2o+ebs95nKdHQSIJJVMHAFaQKBgQD5P2hac7ivzr669lGk\\n"
    "Cdf+6d7ERpwInEOJBqahuUFfsZSVgxjPBVXSSb2CAF+4cVGn4Tbj5h3ZuIfUct7D\\n"
    "f0wUfBG4dTdciAQ5+F4EWnVVeS1aHTyMy1VP+cvwHek4T0sxwFJLze99iiPv7IJl\\n"
    "Py3N2pL0bzWI9kgIJal8YFCcRQKBgQC4VVSm+dUlUB+VExufxEljTBQw9SgAwoi0\\n"
    "sE/sf2pbcRHk9mneYBLLmkat6Rig4j+S/WFFPWZdnD7JCG1NjgRhJr54iRXzR2yB\\n"
    "cq5qPplTtJB7zxF+gk01LJHnuqfIOOc9vrCM2eTQTs/hhgjcWVUudWbgFxoQNcDy\\n"
    "c8YyCSNLNQKBgQDGU8IBV1t56RSzSBSmZn7Mg+OSYmz+HPlQK06kGPj/4BnO7kXr\\n"
    "VN95ONvmec2wwdqrrvUyWoUeHUtXrR+8h6pOEns3P24R3tkeF5cX97KtlIKV1fW8\\n"
    "Qn9b5/Ry2BofiFjY+aOCVhde2XDHFHadgaw8xNNyVJtQpEek0/MM2MbL0QKBgAyY\\n"
    "WAZov7Wi+eV3vsV15gXQ5vhJaAhVQn4GJg/kzOGeojhg1e8J5X7f9cBgUvx7ORjU\\n"
    "E1dl0J7I1ElsN/u6nnX87brSsxtCYBmgOmasDFH53n13MpzQTnI5r2aEDH7T1IkV\\n"
    "hH67TLUnDXE9dVGJERbxkqvxKCi/Y4Wtf3dfxHeZAoGBAKivNGFeCgaoqwdvIP7I\\n"
    "xr/D03OgdfPn2qlR1HqsZbBFncBcs8ZaqqJ8z4XtciwCJAXMqGbd2EGRB6qmLPYe\\n"
    "fmXBZyQ+OJXbjaw1hYWo6UsNa4SnPSwYbZsoht3bgqM7YNoMur3xAgKTMpHK1LRv\\n"
    "KExPKJsV0Kb6sQ6X2vFrnVBh\\n"
    "-----END PRIVATE KEY-----"
)

_TEST_CERT_PEM = (
    "-----BEGIN CERTIFICATE-----\\n"
    "MIIDKzCCAhOgAwIBAgIUGjPhTAHBo+rI0jwF4drOD1h07/EwDQYJKoZIhvcNAQEL\\n"
    "BQAwKTEQMA4GA1UEAwwHVGVzdCBDQTEVMBMGA1UECgwMcGZTZW5zZSBUZXN0MB4X\\n"
    "DTI2MDIwNzAxMjYyOFoXDTM2MDIwNTAxMjYyOFowMjEZMBcGA1UEAwwQdGVzdC5l\\n"
    "eGFtcGxlLmNvbTEVMBMGA1UECgwMcGZTZW5zZSBUZXN0MIIBIjANBgkqhkiG9w0B\\n"
    "AQEFAAOCAQ8AMIIBCgKCAQEAsFHLy6MMYwtaV0SSr9nLOFbWlF9YZedINQV8E/z4\\n"
    "26dJcBCHPLaEj8dI7jgNZnhdzoX52FG3zNs+Tw7NC8uYjFRC32gyx2nULn1T+lzC\\n"
    "cPcU/wmSstgWXSUPUQkZSbua2ETH7IqKFeVMN3fCz/1eNmXR0Cjs16H7M7+qOeMH\\n"
    "A/gMHCZhuyCEBsiF3uga6tg2P048CrQprmlccy3EXcDEFLYppCvycncpqVyneixL\\n"
    "alV3ZLtULWetot3NMy/09bNpwDrzrzbq6BrEMnp0ANT8PpM19wVoxwWmdgkbeUk+\\n"
    "Il9WirEFdTg9IUuEFworVbAkiaYNqISs85KdfmgkpOM+BwIDAQABo0IwQDAdBgNV\\n"
    "HQ4EFgQUPkeP0fa/AoRDCCIjEDRCUxLu6AowHwYDVR0jBBgwFoAUNKKHIC1T0pAo\\n"
    "UUXO2+TT488p45AwDQYJKoZIhvcNAQELBQADggEBAH3zwwnB/RfzmNBKm9dYf3EE\\n"
    "gS3fIdRu7vOTJpRAhAxhjg92po2OyxLCINuRHQImXP3A4+Dxpvm57Gupzc8Ct098\\n"
    "XyscFNebR/XrVPI11ggRhy3giVH61dS8OpkrcwRyVuTF/S11312e+ptsqpiAWh0M\\n"
    "JsXqUCVjwW39FdcxBim++9LAt2XeiyaxqlJln0jN5jyLmSF90CV4NnFMOOdIMkwn\\n"
    "uFouKAgxbb1q1mL1VE9c4fD9BXxqfldnkZqOG56331TVfhJ99dsIxh7aO9rk1txW\\n"
    "RKgTO+dSPffND5e5lENE+BDKx9cUm2Vtc05J3vD7V4cyK8bmBzA6tt6uI/8qvsA=\\n"
    "-----END CERTIFICATE-----"
)

_TEST_CERT_KEY_PEM = (
    "-----BEGIN PRIVATE KEY-----\\n"
    "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCwUcvLowxjC1pX\\n"
    "RJKv2cs4VtaUX1hl50g1BXwT/Pjbp0lwEIc8toSPx0juOA1meF3OhfnYUbfM2z5P\\n"
    "Ds0Ly5iMVELfaDLHadQufVP6XMJw9xT/CZKy2BZdJQ9RCRlJu5rYRMfsiooV5Uw3\\n"
    "d8LP/V42ZdHQKOzXofszv6o54wcD+AwcJmG7IIQGyIXe6Brq2DY/TjwKtCmuaVxz\\n"
    "LcRdwMQUtimkK/JydympXKd6LEtqVXdku1QtZ62i3c0zL/T1s2nAOvOvNuroGsQy\\n"
    "enQA1Pw+kzX3BWjHBaZ2CRt5ST4iX1aKsQV1OD0hS4QXCitVsCSJpg2ohKzzkp1+\\n"
    "aCSk4z4HAgMBAAECggEABAZ3W23x/Z2H5vUgT4EZNBnmFTC7YRGEzae95kDrYixc\\n"
    "BKxul0gSwlY03TIMuu763pj4FA8C3gY6p8MOkvsyFNtkRBsUtFu/UH5jo+lpNlCr\\n"
    "EIrPPWOp2F+HuCcNMOiRB5NDvdaIgikgHSYP8v/1nif4lcLRbAzSd3h5MjrIxreM\\n"
    "bc2wpu/tNgwnpcvGbhUqFBssMucvlXLeKxiP5pF7Un0+WjqC+tCJztOkryvmyE2g\\n"
    "jMEysclD1H7AYVqrusBmuxPW5AAb4Tv2vA4G2xm9n8BhpwpCGZdsa7ZYkb+s89Ec\\n"
    "n0G/fCoRWk21p2U1N18C5QOMuxqxAFxb7YRYJszzCQKBgQDdSh6cpUgE9FeUbUkV\\n"
    "tqbMjmSQKPpBEu2LF7u7x+OBPIEdFrCDMQuZHAc+MT0XFlO8jA4Pm1OoRFaI7RVZ\\n"
    "8G9b/aORUg+xMKOl3o+bInY2FT/ddmp7J1J0dQDfMbU/f+jTCIzAhI094wJc3ScX\\n"
    "336/nQkLRsoOdQB0gwBsodamKQKBgQDL+efd2FlP7/VJg4PGsJHGGRJ0vqtsj//c\\n"
    "is1C0vCkoqtAfMtVP7wMT9SC1u+cjW13Bh6auWHL3MK31iLceymfB+73ZPBDuXz/\\n"
    "lTv+hKqtYZbc1g7w9SJEqN41tFRsdMRnq18WcYAMCoQiY4R3B9lYJOqBiuvZt0mI\\n"
    "vGRwYU9orwKBgQCpZSu5zewrnr/MJzxjGsbkn7vrfvLTDaI5b5mOTZ2iOKa9lbjZ\\n"
    "NJokQoho21hga/79vlilKcoIbQexGYvWpW8ZhDfJ7n+ErC8Zsh1MLD1BeVLCPPuV\\n"
    "+qvr6gUY1fxg95FKuqjEVrOoRDZyz/g1Fij4lUVvFGloV7hZeE7C2cBuwQKBgQCA\\n"
    "ZSWL4pSNmelXxf4cAqcwADY64I59fsM66vA7wRYTPAX6SNOhLMZNJa8KUQtxCyE9\\n"
    "i8+V611g+uxi1dsJ2EkhvtewSIxoxQimxSSHmLDrBIP3LJMpH9TbTUTan1GJF5NO\\n"
    "AnSPZxCIA9Ka5vPKDVnFfy9SLcU6PYJ/HL9IciiPJwKBgC93lXfdoyA5waYdBGYL\\n"
    "VEaSfh3hxGd5sC+krUK7VXV/bCkGOX71AsiAY8Wo35yu3+24tnLaMVocgcFzjmXi\\n"
    "hZu2Fa7IccV7iRh0wxoXD3BtjV37vzLq4C5yD5hgFgeNwF3LfrWVOWFAy2bjrA5+\\n"
    "U1dtBhHADj/YuAIFAStvX2JE\\n"
    "-----END PRIVATE KEY-----"
)

# ── Chained CRUD definitions ─────────────────────────────────────────────────
# Maps child endpoint path → chain definition for dependency-chained tests.
# Each chain defines parent resources to create first, their bodies, and how
# to inject parent data into the child's request body.
#
# Structure:
#   "parents": list of parent resources to create (in order)
#     - "path": parent API endpoint
#     - "body": JSON body for POST
#     - "inject": {child_field: parent_response_field} — optional field injection
#   "child_body": explicit child body (if None, generated from schema)
#   "child_overrides": override specific fields in generated child body
#   "update_field": field to test PATCH with (default: "descr")

_HAPROXY_BACKEND_BODY: dict[str, Any] = {
    "name": "pft_be_{tag}",
    "agent_port": "0",
    "persist_cookie_name": "SRVID",
    "descr": "Test backend for {tag}",
}

_GATEWAY_BODY: dict[str, Any] = {
    "name": "pft_gw_{tag}",
    "gateway": "10.0.2.1",
    "interface": "wan",
    "ipprotocol": "inet",
    "descr": "Test gateway for {tag}",
    "latencylow": 200,
    "latencyhigh": 500,
    "losslow": 10,
    "losshigh": 20,
    "loss_interval": 2000,
    "time_period": 60000,
    "interval": 500,
    "alert_interval": 1000,
}

_CHAINED_CRUD: dict[str, dict[str, Any]] = {
    # ── Interface VLAN ────────────────────────────────────────────────────
    "/api/v2/interface/vlan": {
        "parents": [],
        "child_body": {
            "if": "vtnet0",
            "tag": 100,
            "pcp": 0,
            "descr": "Test VLAN",
        },
        "update_field": "descr",
    },
    # ── Routing: static_route needs gateway ───────────────────────────────
    "/api/v2/routing/static_route": {
        "parents": [
            {
                "path": "/api/v2/routing/gateway",
                "body_template": _GATEWAY_BODY,
                "tag": "sr",
                "inject": {"gateway": "name"},
            }
        ],
        "child_body": {
            "network": "10.200.0.0/24",
            "descr": "Test static route",
        },
        "update_field": "descr",
    },
    # ── Routing: gateway/group needs gateways ─────────────────────────────
    "/api/v2/routing/gateway/group": {
        "parents": [
            {
                "path": "/api/v2/routing/gateway",
                "body_template": _GATEWAY_BODY,
                "tag": "gg",
            }
        ],
        "child_body": {
            "name": "pft_gw_group",
            "descr": "Test gateway group",
            "priorities": [{"gateway": "pft_gw_gg", "tier": 1}],
        },
        "update_field": "descr",
    },
    # ── VPN: wireguard/peer needs tunnel ──────────────────────────────────
    "/api/v2/vpn/wireguard/peer": {
        "parents": [
            {
                "path": "/api/v2/vpn/wireguard/tunnel",
                "body": {
                    "name": "pft_tun_peer",
                    "listenport": "51821",
                    "privatekey": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY=",
                    "addresses": [],
                },
                "inject": {"tun": "name"},
            }
        ],
        "child_body": {
            "publickey": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY=",
            "descr": "Test WG peer",
        },
        "update_field": "descr",
    },
    # ── HAProxy: frontend needs backend ───────────────────────────────────
    "/api/v2/services/haproxy/frontend": {
        "parents": [
            {
                "path": "/api/v2/services/haproxy/backend",
                "body_template": _HAPROXY_BACKEND_BODY,
                "tag": "fe",
            }
        ],
        "child_body": {
            "name": "pft_fe_chain",
            "type": "http",
            "descr": "Test frontend",
        },
        "update_field": "descr",
    },
    # ── HAProxy backend sub-resources (parent_id injection) ───────────────
    "/api/v2/services/haproxy/backend/acl": {
        "parents": [
            {
                "path": "/api/v2/services/haproxy/backend",
                "body_template": _HAPROXY_BACKEND_BODY,
                "tag": "bacl",
                "inject": {"parent_id": "id"},
            }
        ],
        "child_body": {
            "name": "pft_bacl",
            "expression": "host_starts_with",
            "value": "test.example.com",
        },
        "update_field": "value",
        "update_value": '"updated.example.com"',
    },
    "/api/v2/services/haproxy/backend/server": {
        "parents": [
            {
                "path": "/api/v2/services/haproxy/backend",
                "body_template": _HAPROXY_BACKEND_BODY,
                "tag": "bsrv",
                "inject": {"parent_id": "id"},
            }
        ],
        "child_body": {
            "name": "pft_bsrv",
            "address": "10.99.99.50",
            "port": "8080",
        },
        "update_field": "address",
        "update_value": '"10.99.99.51"',
    },
    # ── HAProxy frontend sub-resources (2-level: backend → frontend → child)
    "/api/v2/services/haproxy/frontend/acl": {
        "parents": [
            {
                "path": "/api/v2/services/haproxy/backend",
                "body_template": _HAPROXY_BACKEND_BODY,
                "tag": "facl",
            },
            {
                "path": "/api/v2/services/haproxy/frontend",
                "body": {
                    "name": "pft_fe_acl",
                    "type": "http",
                },
                "inject": {"parent_id": "id"},
            },
        ],
        "child_body": {
            "name": "pft_facl",
            "expression": "host_starts_with",
            "value": "test.example.com",
        },
        "update_field": "value",
        "update_value": '"updated.example.com"',
    },
    "/api/v2/services/haproxy/frontend/address": {
        "parents": [
            {
                "path": "/api/v2/services/haproxy/backend",
                "body_template": _HAPROXY_BACKEND_BODY,
                "tag": "faddr",
            },
            {
                "path": "/api/v2/services/haproxy/frontend",
                "body": {
                    "name": "pft_fe_addr",
                    "type": "http",
                },
                "inject": {"parent_id": "id"},
            },
        ],
        "child_body": {
            "extaddr": "custom",
            "extaddr_custom": "10.99.99.80:80",
        },
        "update_field": None,
    },
    # ── BIND: sync/domain needs zone ──────────────────────────────────────
    "/api/v2/services/bind/sync/domain": {
        "parents": [
            {
                "path": "/api/v2/services/bind/zone",
                "body": {
                    "name": "chain.example.com",
                    "nameserver": "ns1.example.com",
                    "mail": "admin.example.com",
                    "serial": 2024010101,
                    "forwarders": [],
                    "baseip": "10.99.99.0",
                },
                "inject": {"parent_id": "id"},
            }
        ],
        "child_body": {
            "dstdomainport": "53",
            "synctype": "master",
            "targetip": "10.99.99.100",
        },
        "update_field": None,
    },
    # ── Certificate Authority (PEM data) ──────────────────────────────────
    "/api/v2/system/certificate_authority": {
        "parents": [],
        "child_body": {
            "descr": "Test CA",
            "crt": "__CA_CERT_PEM__",
            "prv": "__CA_KEY_PEM__",
        },
        "update_field": "descr",
    },
    # ── Certificate (PEM data) ────────────────────────────────────────────
    "/api/v2/system/certificate": {
        "parents": [],
        "child_body": {
            "descr": "Test Cert",
            "crt": "__CERT_PEM__",
            "prv": "__CERT_KEY_PEM__",
        },
        "update_field": "descr",
    },
    # ── ACME account key ──────────────────────────────────────────────────
    "/api/v2/services/acme/account_key": {
        "parents": [],
        "child_body": {
            "name": "pft_acme_key",
            "descr": "Test ACME key",
            "email": "test@example.com",
            "acmeserver": "letsencrypt-staging-2",
        },
        "update_field": "descr",
    },
}


def _test_value_for_param(
    param: ToolParameter, unique_id: str, endpoint_path: str = ""
) -> str | None:
    """Generate a test value for a parameter."""
    # Check endpoint-specific overrides first
    if endpoint_path and endpoint_path in _ENDPOINT_OVERRIDES:
        overrides = _ENDPOINT_OVERRIDES[endpoint_path]
        api_name = param.api_name or param.name
        if api_name in overrides:
            val = overrides[api_name]
            if val is None:
                return None  # explicitly skip this field
            return val.replace("{unique}", unique_id)
        if param.name in overrides:
            val = overrides[param.name]
            if val is None:
                return None
            return val.replace("{unique}", unique_id)

    # Special handling for "name" fields — must be short and alphanumeric
    if param.name == "name" and param.python_type == "str":
        # Truncate unique_id to keep name under 16 chars (user group limit)
        short = unique_id[:10].replace("-", "_")
        return f'"pft_{short}"'

    # Check explicit mapping
    if param.name in _TEST_VALUES:
        val = _TEST_VALUES[param.name]
        if val is None:
            # Use first enum value if available
            if param.enum:
                return repr(param.enum[0])
            return None
        return val.replace("{unique}", unique_id)

    # Enum: use first value
    if param.enum:
        return repr(param.enum[0])

    # IP address pattern detection
    name_lower = param.name.lower()
    if param.python_type == "str" and any(
        kw in name_lower
        for kw in ("addr", "ip_", "gateway", "_ip", "server", "peer", "remote", "local")
    ):
        return '"10.99.99.99"'

    # Port pattern detection
    if param.python_type == "str" and "port" in name_lower:
        return '"443"'

    # Type-based fallback
    if param.python_type == "str":
        return f'"test_{unique_id}"'
    elif param.python_type == "int":
        return "1"
    elif param.python_type == "float":
        return "1.0"
    elif param.python_type == "bool":
        return "False"
    elif param.python_type.startswith("list["):
        return "[]"
    elif param.python_type.startswith("dict["):
        return "{}"
    elif param.python_type == "str | int":
        return '"1"'

    return None


@dataclass
class EndpointGroup:
    """A group of related endpoints for one resource."""

    base_path: str
    singular_get: ToolContext | None = None
    plural_get: ToolContext | None = None
    create: ToolContext | None = None
    update: ToolContext | None = None
    delete: ToolContext | None = None
    replace: ToolContext | None = None
    category: str = "unknown"  # crud, settings, readonly, apply, action


def _group_endpoints(contexts: list[ToolContext]) -> list[EndpointGroup]:
    """Group tool contexts by resource for lifecycle tests."""
    by_path: dict[str, dict[str, ToolContext]] = defaultdict(dict)
    for ctx in contexts:
        by_path[ctx.path][ctx.method] = ctx

    groups: list[EndpointGroup] = []

    for path in sorted(by_path.keys()):
        ops = by_path[path]
        methods = set(ops.keys())

        group = EndpointGroup(base_path=path)

        if path.endswith("/apply"):
            group.category = "apply"
            group.singular_get = ops.get("get")
            group.create = ops.get("post")
        elif path.endswith("/settings") or path.endswith("/advanced_settings"):
            group.category = "settings"
            group.singular_get = ops.get("get")
            group.update = ops.get("patch")
        elif methods >= {"get", "post", "patch", "delete"}:
            group.category = "crud"
            group.singular_get = ops.get("get")
            group.create = ops.get("post")
            group.update = ops.get("patch")
            group.delete = ops.get("delete")
            group.replace = ops.get("put")
        elif methods == {"get"}:
            ctx = ops["get"]
            pnames = [p.name for p in ctx.parameters]
            if "limit" in pnames:
                group.category = "plural_readonly"
            else:
                group.category = "readonly"
            group.singular_get = ctx
        elif "get" in methods and "delete" in methods and "post" not in methods:
            group.category = "readonly"
            group.singular_get = ops.get("get")
        elif "get" in methods and "put" in methods:
            group.category = "plural_readonly"
            group.singular_get = ops.get("get")
            group.replace = ops.get("put")
        elif "post" in methods and len(methods) <= 2:
            group.category = "action"
            group.create = ops.get("post")
        else:
            group.category = "other"
            group.singular_get = ops.get("get")

        groups.append(group)

    return groups


def _is_dangerous(ctx: ToolContext | None) -> bool:
    """Check if a context represents a dangerous endpoint."""
    if ctx is None:
        return False
    return ctx.operation_id in _DANGEROUS_ENDPOINTS


def _should_skip_crud(group: EndpointGroup) -> tuple[bool, str]:
    """Check if a CRUD group should be skipped, and why."""
    if not group.create:
        return True, "no create endpoint"

    # Chained tests handle their own dependencies — don't skip them
    if group.base_path in _CHAINED_CRUD:
        return False, ""

    # Check path-based skip list
    if group.base_path in _SKIP_CRUD_PATHS:
        return True, _SKIP_CRUD_PATHS[group.base_path]

    # Check for required fields we can't generate
    for p in group.create.parameters:
        if p.required and p.name == "parent_id":
            return True, "requires parent_id (needs parent resource first)"
        if p.required and p.name in ("caref", "certref"):
            return True, f"requires {p.name} (needs existing CA/cert)"

    return False, ""


def generate_tests(contexts: list[ToolContext]) -> str:
    """Generate the complete test file content."""
    groups = _group_endpoints(contexts)

    lines: list[str] = []
    lines.append(_gen_header())
    lines.append("")

    test_count = 0

    # CRUD lifecycle tests (regular + chained)
    for group in groups:
        if group.category == "crud":
            skip, reason = _should_skip_crud(group)
            if skip:
                lines.append(f"# SKIP {group.base_path}: {reason}")
                lines.append("")
                continue
            if _is_dangerous(group.create) or _is_dangerous(group.delete):
                lines.append(f"# SKIP {group.base_path}: dangerous endpoint")
                lines.append("")
                continue

            # Use chained generator if this endpoint has dependencies
            if group.base_path in _CHAINED_CRUD:
                code = _gen_chained_crud_test(group)
            else:
                code = _gen_crud_test(group)
            if code:
                lines.append(code)
                lines.append("")
                test_count += 1

    # Settings roundtrip tests
    for group in groups:
        if group.category == "settings" and group.singular_get:
            lines.append(_gen_settings_test(group))
            lines.append("")
            test_count += 1

    # Read-only tests
    for group in groups:
        if group.category in ("readonly", "plural_readonly"):
            if _is_dangerous(group.singular_get):
                continue
            if group.base_path in _PHANTOM_PLURAL_ROUTES:
                lines.append(
                    f"# SKIP {group.base_path}: phantom plural route (spec-only, not registered on server)"
                )
                lines.append("")
                continue
            lines.append(_gen_readonly_test(group))
            lines.append("")
            test_count += 1

    # Apply status tests
    for group in groups:
        if group.category == "apply" and group.singular_get:
            lines.append(_gen_apply_test(group))
            lines.append("")
            test_count += 1

    # Add a summary comment at the top
    header_line = f"# Total generated tests: {test_count}"
    lines.insert(1, header_line)

    return "\n".join(lines)


def _gen_header() -> str:
    """Generate the test file header with imports and fixtures."""
    return '''"""
Auto-generated integration tests for pfSense REST API v2.

Generated by: python -m generator
Tests every endpoint against a live pfSense VM.

DO NOT EDIT THIS FILE DIRECTLY.
Fix the generator instead, then re-run.
"""

from __future__ import annotations

import os
import time

import httpx
import pytest

BASE_URL = os.environ.get("PFSENSE_TEST_URL", "https://127.0.0.1:18443")
API_KEY = os.environ.get("PFSENSE_TEST_API_KEY", "")
AUTH_USER = os.environ.get("PFSENSE_TEST_USER", "admin")
AUTH_PASS = os.environ.get("PFSENSE_TEST_PASS", "pfsense")

# Pre-generated test certificates (self-signed, 10-year validity)
CA_CERT_PEM = "''' + _TEST_CA_CERT_PEM + '''"
CA_KEY_PEM = "''' + _TEST_CA_KEY_PEM + '''"
CERT_PEM = "''' + _TEST_CERT_PEM + '''"
CERT_KEY_PEM = "''' + _TEST_CERT_KEY_PEM + '''"


@pytest.fixture(scope="session")
def client() -> httpx.Client:
    """Authenticated httpx client for the test VM."""
    if API_KEY:
        c = httpx.Client(
            base_url=BASE_URL,
            headers={"X-API-Key": API_KEY},
            verify=False,
            timeout=30,
        )
    else:
        c = httpx.Client(
            base_url=BASE_URL,
            auth=(AUTH_USER, AUTH_PASS),
            verify=False,
            timeout=30,
        )
    yield c
    c.close()


def _ok(resp: httpx.Response) -> dict:
    """Assert response is 200 and return data."""
    assert resp.status_code == 200, f"{resp.request.method} {resp.request.url} -> {resp.status_code}: {resp.text[:500]}"
    body = resp.json()
    assert body.get("code") == 200, f"API error: {body}"
    return body.get("data", body)


def _delete_with_retry(client: httpx.Client, path: str, obj_id, params: dict | None = None) -> None:
    """Delete a resource with retry for 503 (busy) and accept 404 (already gone)."""
    p = {"id": obj_id}
    if params:
        p.update(params)
    for _attempt in range(3):
        resp = client.delete(path, params=p)
        if resp.status_code != 503:
            break
        time.sleep(5)
    assert resp.status_code in (200, 404), f"Delete {path} id={obj_id} failed: {resp.text[:500]}"'''


def _gen_crud_test(group: EndpointGroup) -> str:
    """Generate a CRUD lifecycle test: create → get → list → update → delete."""
    assert group.create is not None
    path = group.base_path
    test_name = path.replace("/api/v2/", "").replace("/", "_")
    unique = test_name.replace("/", "_").replace("-", "_")

    # Build create payload
    create_params = group.create.parameters
    create_body: dict[str, str] = {}
    for p in create_params:
        if p.source != "body":
            continue
        val = _test_value_for_param(p, unique, endpoint_path=path)
        if val is None:
            if p.required:
                return f"# SKIP {path}: can't generate test value for required field '{p.name}'"
            continue
        api_name = p.api_name or p.name
        # For fields that expect arrays, wrap if needed
        if p.python_type.startswith("list[") and not val.startswith("["):
            val = f"[{val}]"
        create_body[api_name] = val

    # Build update payload - pick a safe non-enum string field
    update_field = None
    update_value = None
    for p in create_params:
        if (
            p.source == "body"
            and not p.required
            and p.python_type == "str"
            and p.name in ("descr", "description")
            and not p.enum  # skip enums
        ):
            update_field = p.api_name or p.name
            update_value = '"Updated by test"'
            break
    if not update_field:
        for p in create_params:
            if (
                p.source == "body"
                and not p.required
                and p.python_type == "str"
                and p.name not in ("name", "username", "type_", "sched")
                and not p.enum  # skip enums — sending arbitrary string to enum field breaks
            ):
                update_field = p.api_name or p.name
                update_value = '"updated_test_value"'
                break

    # Find the plural list path
    plural_path = None
    if path.endswith("y"):
        plural_path = path[:-1] + "ies"
    elif path.endswith("s"):
        plural_path = path + "es"
    else:
        plural_path = path + "s"

    create_body_str = "{\n"
    for k, v in create_body.items():
        create_body_str += f'        "{k}": {v},\n'
    create_body_str += "    }"

    lines = []
    lines.append(f"def test_crud_{test_name}(client: httpx.Client):")
    lines.append(f'    """CRUD lifecycle: {path}"""')
    lines.append(f"    # CREATE")
    lines.append(f"    create_resp = client.post(")
    lines.append(f'        "{path}",')
    lines.append(f"        json={create_body_str},")
    lines.append(f"    )")
    lines.append(f"    data = _ok(create_resp)")
    lines.append(f'    obj_id = data.get("id")')
    lines.append(f"    assert obj_id is not None, f\"No id in create response: {{data}}\"")
    lines.append(f"")
    lines.append(f"    try:")
    lines.append(f"        # GET (singular)")
    lines.append(f"        get_resp = client.get(")
    lines.append(f'            "{path}",')
    lines.append(f'            params={{"id": obj_id}},')
    lines.append(f"        )")
    lines.append(f"        get_data = _ok(get_resp)")
    lines.append(f'        assert get_data.get("id") == obj_id')
    lines.append(f"")

    # List test (if plural path likely exists and is not a phantom)
    if plural_path not in _PHANTOM_PLURAL_ROUTES:
        lines.append(f"        # LIST (plural)")
        lines.append(f"        list_resp = client.get(")
        lines.append(f'            "{plural_path}",')
        lines.append(f'            params={{"limit": 0}},')
        lines.append(f"        )")
        lines.append(f"        if list_resp.status_code == 200:")
        lines.append(f"            list_data = list_resp.json()")
        lines.append(f'            if list_data.get("code") == 200:')
        lines.append(f'                assert isinstance(list_data.get("data"), list)')
        lines.append(f"")

    # Update test
    if update_field and update_value:
        lines.append(f"        # UPDATE")
        lines.append(f"        update_resp = client.patch(")
        lines.append(f'            "{path}",')
        lines.append(f'            json={{"id": obj_id, "{update_field}": {update_value}}},')
        lines.append(f"        )")
        lines.append(f"        update_data = _ok(update_resp)")
        lines.append(f'        assert update_data.get("{update_field}") == {update_value}')
        lines.append(f"")

    lines.append(f"    finally:")
    lines.append(f"        # DELETE (cleanup, with retry for 503)")
    lines.append(f"        for _attempt in range(3):")
    lines.append(f"            del_resp = client.delete(")
    lines.append(f'                "{path}",')
    lines.append(f'                params={{"id": obj_id}},')
    lines.append(f"            )")
    lines.append(f"            if del_resp.status_code != 503:")
    lines.append(f"                break")
    lines.append(f"            time.sleep(5)")
    lines.append(f"        # 200 = deleted, 404 = already gone (acceptable)")
    lines.append(f"        assert del_resp.status_code in (200, 404), f\"Delete failed: {{del_resp.text[:500]}}\"")
    lines.append(f"")

    return "\n".join(lines)


def _gen_settings_test(group: EndpointGroup) -> str:
    """Generate a settings roundtrip test: get → verify 200."""
    path = group.base_path
    test_name = path.replace("/api/v2/", "").replace("/", "_")

    lines = []
    lines.append(f"def test_settings_{test_name}(client: httpx.Client):")
    lines.append(f'    """Settings read: {path}"""')
    lines.append(f"    # GET current settings")
    lines.append(f'    resp = client.get("{path}")')
    lines.append(f"    data = _ok(resp)")
    lines.append(f"    assert isinstance(data, dict)")
    lines.append(f"")

    return "\n".join(lines)


def _gen_readonly_test(group: EndpointGroup) -> str:
    """Generate a read-only test: GET returns 200."""
    ctx = group.singular_get
    assert ctx is not None
    path = ctx.path
    test_name = path.replace("/api/v2/", "").replace("/", "_")
    is_plural = group.category == "plural_readonly"

    lines = []
    lines.append(f"def test_read_{test_name}(client: httpx.Client):")
    lines.append(f'    """Read-only: {path}"""')

    if is_plural:
        lines.append(f'    resp = client.get("{path}", params={{"limit": 5}})')
    else:
        has_id = any(p.name == "id" for p in ctx.parameters)
        if has_id:
            lines.append(f"    # Singular GET requires id -- skip if no objects exist")
            lines.append(f'    resp = client.get("{path}", params={{"id": 0}})')
            lines.append(f"    # May return 404 if no objects -- that's ok")
            lines.append(f"    assert resp.status_code in (200, 400, 404), f\"Unexpected: {{resp.status_code}}\"")
            lines.append(f"")
            return "\n".join(lines)
        else:
            lines.append(f'    resp = client.get("{path}")')

    lines.append(f"    data = _ok(resp)")
    if is_plural:
        lines.append(f"    assert isinstance(data, list)")
    else:
        lines.append(f"    assert data is not None")
    lines.append(f"")

    return "\n".join(lines)


def _gen_apply_test(group: EndpointGroup) -> str:
    """Generate an apply status test."""
    path = group.base_path
    test_name = path.replace("/api/v2/", "").replace("/", "_")

    lines = []
    lines.append(f"def test_apply_{test_name}(client: httpx.Client):")
    lines.append(f'    """Apply status: {path}"""')
    lines.append(f'    resp = client.get("{path}")')
    lines.append(f"    data = _ok(resp)")
    lines.append(f"    assert isinstance(data, dict)")
    lines.append(f"")

    return "\n".join(lines)


def _resolve_parent_body(parent_def: dict[str, Any]) -> dict[str, Any]:
    """Resolve a parent's body from either 'body' or 'body_template' + 'tag'."""
    if "body" in parent_def:
        return dict(parent_def["body"])
    template = parent_def["body_template"]
    tag = parent_def.get("tag", "x")
    body = {}
    for k, v in template.items():
        if isinstance(v, str) and "{tag}" in v:
            body[k] = v.replace("{tag}", tag)
        else:
            body[k] = v
    return body


def _body_to_code(body: dict[str, Any], indent: int = 8) -> str:
    """Convert a dict to Python code string for a JSON body."""
    pad = " " * indent
    result = "{\n"
    for k, v in body.items():
        if isinstance(v, str):
            # Check for PEM placeholders
            if v == "__CA_CERT_PEM__":
                result += f'{pad}"{k}": CA_CERT_PEM,\n'
            elif v == "__CA_KEY_PEM__":
                result += f'{pad}"{k}": CA_KEY_PEM,\n'
            elif v == "__CERT_PEM__":
                result += f'{pad}"{k}": CERT_PEM,\n'
            elif v == "__CERT_KEY_PEM__":
                result += f'{pad}"{k}": CERT_KEY_PEM,\n'
            else:
                result += f'{pad}"{k}": {v!r},\n'
        elif isinstance(v, bool):
            result += f'{pad}"{k}": {v},\n'
        elif isinstance(v, (int, float)):
            result += f'{pad}"{k}": {v},\n'
        elif isinstance(v, list):
            result += f'{pad}"{k}": {v!r},\n'
        elif isinstance(v, dict):
            result += f'{pad}"{k}": {v!r},\n'
        else:
            result += f'{pad}"{k}": {v!r},\n'
    result += " " * (indent - 4) + "}"
    return result


def _gen_chained_crud_test(group: EndpointGroup) -> str:
    """Generate a CRUD test with parent resource setup/teardown."""
    path = group.base_path
    chain = _CHAINED_CRUD[path]
    test_name = path.replace("/api/v2/", "").replace("/", "_")
    parents = chain.get("parents", [])
    child_body = chain.get("child_body")
    update_field = chain.get("update_field", "descr")
    update_value = chain.get("update_value", '"Updated by test"')

    lines: list[str] = []
    lines.append(f"def test_crud_{test_name}(client: httpx.Client):")
    parent_paths = ", ".join(p["path"].split("/api/v2/")[-1] for p in parents)
    if parents:
        lines.append(f'    """CRUD lifecycle: {path} (needs: {parent_paths})"""')
    else:
        lines.append(f'    """CRUD lifecycle: {path} (chained)"""')

    # ── Create parent resources ───────────────────────────────────────────
    parent_vars: list[str] = []
    for i, parent in enumerate(parents):
        var = f"p{i}"
        parent_vars.append(var)
        parent_body = _resolve_parent_body(parent)
        body_code = _body_to_code(parent_body)
        lines.append(f"    # Setup: create parent {parent['path'].split('/api/v2/')[-1]}")
        lines.append(f"    {var}_resp = client.post(")
        lines.append(f'        "{parent["path"]}",')
        lines.append(f"        json={body_code},")
        lines.append(f"    )")
        lines.append(f"    {var} = _ok({var}_resp)")
        lines.append(f'    {var}_id = {var}.get("id")')
        lines.append(f'    assert {var}_id is not None, f"No id in parent response: {{{var}}}"')
        lines.append(f"")

    # ── Build child body ──────────────────────────────────────────────────
    if child_body:
        # Use explicit child body
        final_body = dict(child_body)
    else:
        # This shouldn't happen for chained tests — they all have child_body
        return f"# SKIP {path}: chained test missing child_body"

    # Apply parent injections
    injections: list[tuple[str, str, str]] = []  # (child_field, parent_var, parent_field)
    for i, parent in enumerate(parents):
        inject = parent.get("inject", {})
        for child_field, parent_field in inject.items():
            injections.append((child_field, f"p{i}", parent_field))

    # ── Indentation for nesting ───────────────────────────────────────────
    if parents:
        # Wrap in try/finally for each parent (nested)
        base_indent = "    "
        for i in range(len(parents)):
            lines.append(f"{base_indent}try:")
            base_indent += "    "
    else:
        base_indent = "    "

    # CREATE
    lines.append(f"{base_indent}# CREATE")
    body_code = _body_to_code(final_body, indent=len(base_indent) + 8)
    lines.append(f"{base_indent}body = {body_code}")

    # Apply dynamic injections from parents
    for child_field, pvar, pfield in injections:
        lines.append(f'{base_indent}body["{child_field}"] = {pvar}["{pfield}"]')

    lines.append(f"{base_indent}create_resp = client.post(")
    lines.append(f'{base_indent}    "{path}",')
    lines.append(f"{base_indent}    json=body,")
    lines.append(f"{base_indent})")
    lines.append(f"{base_indent}data = _ok(create_resp)")
    lines.append(f'{base_indent}obj_id = data.get("id")')
    lines.append(f'{base_indent}assert obj_id is not None, f"No id in create response: {{data}}"')
    lines.append(f"")

    lines.append(f"{base_indent}try:")
    inner = base_indent + "    "

    # Determine if sub-resource GET/DELETE also need parent_id
    parent_id_injection = None
    for child_field, pvar, pfield in injections:
        if child_field == "parent_id":
            parent_id_injection = (pvar, pfield)
            break

    # GET
    lines.append(f"{inner}# GET (singular)")
    if parent_id_injection:
        pvar, pfield = parent_id_injection
        lines.append(f"{inner}get_resp = client.get(")
        lines.append(f'{inner}    "{path}",')
        lines.append(f'{inner}    params={{"id": obj_id, "parent_id": {pvar}["{pfield}"]}},')
        lines.append(f"{inner})")
    else:
        lines.append(f"{inner}get_resp = client.get(")
        lines.append(f'{inner}    "{path}",')
        lines.append(f'{inner}    params={{"id": obj_id}},')
        lines.append(f"{inner})")
    lines.append(f"{inner}_ok(get_resp)")
    lines.append(f"")

    # UPDATE
    if update_field:
        lines.append(f"{inner}# UPDATE")
        if parent_id_injection:
            pvar, pfield = parent_id_injection
            lines.append(f"{inner}update_resp = client.patch(")
            lines.append(f'{inner}    "{path}",')
            lines.append(f'{inner}    json={{"id": obj_id, "parent_id": {pvar}["{pfield}"], "{update_field}": {update_value}}},')
            lines.append(f"{inner})")
        else:
            lines.append(f"{inner}update_resp = client.patch(")
            lines.append(f'{inner}    "{path}",')
            lines.append(f'{inner}    json={{"id": obj_id, "{update_field}": {update_value}}},')
            lines.append(f"{inner})")
        lines.append(f"{inner}_ok(update_resp)")
        lines.append(f"")

    # DELETE child (finally)
    lines.append(f"{base_indent}finally:")
    if parent_id_injection:
        pvar, pfield = parent_id_injection
        lines.append(
            f'{base_indent}    _delete_with_retry(client, "{path}", obj_id, '
            f'{{"parent_id": {pvar}["{pfield}"]}})'
        )
    else:
        lines.append(f'{base_indent}    _delete_with_retry(client, "{path}", obj_id)')

    # ── Cleanup parents in reverse order ──────────────────────────────────
    if parents:
        for i in range(len(parents) - 1, -1, -1):
            # Close the try block
            close_indent = "    " * (i + 1)
            lines.append(f"{close_indent}finally:")
            lines.append(
                f'{close_indent}    _delete_with_retry(client, "{parents[i]["path"]}", p{i}_id)'
            )

    lines.append(f"")
    return "\n".join(lines)
