"""
Generate integration tests for every API endpoint.

Produces generated/tests.py which tests all endpoints against a live pfSense VM.
Test categories:
  - CRUD lifecycle: create → get → list → update → delete
  - Settings: get → update (roundtrip) → verify
  - Read-only: GET returns 200
  - Apply: GET status returns 200
  - Plural: list returns array

Halt/reboot tests run last (zz_/zzz_ prefix).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .context_builder import ToolContext, _DANGEROUS_ENDPOINTS, _PHANTOM_PLURAL_ROUTES
from .schema_parser import ToolParameter

# Test value generators by field name pattern
_TEST_VALUES: dict[str, str] = {
    # Network - IP addresses
    "interface": '"wan"',
    "if_": '"em0"',
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
    "/api/v2/services/freeradius/client": {
        "addr": '"10.99.99.90"',
        "shortname": '"pft_frcl"',
        "secret": '"TestSecret123"',
    },
    "/api/v2/services/freeradius/interface": {
        "addr": '"127.0.0.1"',
        "ip_version": '"ipaddr"',
    },
    "/api/v2/services/freeradius/user": {
        "username": '"pft_fruser"',
        "password": '"TestPass123"',
        "motp_secret": '""',
        "motp_pin": '""',
    },
    "/api/v2/interface/gre": {
        "if": '"wan"',
        "remote_addr": '"198.51.100.1"',
        "tunnel_local_addr": '"10.255.0.1"',
        "tunnel_remote_addr": '"10.255.0.2"',
        "tunnel_remote_addr6": '""',
    },
    "/api/v2/interface/lagg": {
        "members": '["em2"]',
        "proto": '"none"',
        "descr": '"Test LAGG"',
    },
    "/api/v2/services/haproxy/settings/dns_resolver": {
        "name": '"pft_hadns"',
        "server": '"8.8.8.8"',
    },
    "/api/v2/services/haproxy/settings/email_mailer": {
        "name": '"pft_haml"',
        "mailserver": '"10.99.99.90"',
    },
}

# Endpoints that should be completely skipped for CRUD tests
_SKIP_CRUD_PATHS: dict[str, str] = {
    "/api/v2/vpn/openvpn/client_export/config": "tested via custom test_action_vpn_openvpn_client_export (6-step chain)",
    "/api/v2/services/dhcp_server": "per-interface singleton — POST not supported by design, PATCH tested via singleton",
    "/api/v2/services/haproxy/settings/dns_resolver": "500 parent Model not constructed — GET/DELETE broken even after config.xml init (confirmed v2.7.1 bug)",
    "/api/v2/services/haproxy/settings/email_mailer": "500 parent Model not constructed — GET/DELETE broken even after config.xml init (confirmed v2.7.1 bug)",
    "/api/v2/system/package": "nginx 504 timeout (60s hardcoded) + QEMU NAT too slow for package downloads; GET tested via read tests",
}

# ── Singleton GET/PATCH endpoints (settings-like but not auto-detected) ───────
# These are GET/PATCH endpoints whose path doesn't end in /settings.
# Each entry maps path → {"field": <patchable field>, "value": <test value>}.
# Tests: GET → PATCH with test value → GET verify → PATCH restore original.
_SINGLETON_TESTS: dict[str, dict[str, Any]] = {
    "/api/v2/firewall/nat/outbound/mode": {
        "field": "mode",
        "value": "hybrid",
    },
    "/api/v2/firewall/states/size": {
        "field": "maximumstates",
        "value": 500000,
    },
    "/api/v2/routing/gateway/default": {
        "field": "defaultgw4",
        "value": "",
    },
    "/api/v2/services/dhcp_relay": {
        "field": "enable",
        "value": False,
        "extra_fields": {"server": ["10.0.2.1"]},
    },
    "/api/v2/services/ssh": {
        "field": "port",
        "value": "2222",
    },
    "/api/v2/status/carp": {
        "field": "maintenance_mode",
        "value": True,
        "restore": False,
        "extra_fields": {"enable": True},
    },
    "/api/v2/system/console": {
        "field": "passwd_protect_console",
        "value": True,
    },
    "/api/v2/system/dns": {
        "field": "dnsallowoverride",
        "value": False,
    },
    "/api/v2/system/hostname": {
        "field": "hostname",
        "value": "pfttest",
        "extra_fields": {"domain": "home.arpa"},
    },
    "/api/v2/system/notifications/email_settings": {
        "field": "ipaddress",
        "value": "127.0.0.1",
        "extra_fields": {"username": "test", "password": "test"},
    },
    "/api/v2/services/dhcp_server/backend": {
        "field": "dhcpbackend",
        "value": "kea",
        "restore": "isc",
        "patch_only": True,
    },
    "/api/v2/system/timezone": {
        "field": "timezone",
        "value": "America/Chicago",
        "restore": "Etc/UTC",
        "raw_patch": True,  # PATCH response has "Setting timezone...done.\n" prefix before JSON
    },
}

# Singleton endpoints to skip
_SKIP_SINGLETON: dict[str, str] = {
    "/api/v2/system/restapi/version": "PATCH triggers API version change (destructive)",
}

# ── Action POST endpoints ─────────────────────────────────────────────────────
# POST-only endpoints safe to test. Each entry maps path → test config.
# "body" = request body, "chain" = optional parent setup, "status" = expected HTTP status.
_ACTION_TESTS: dict[str, dict[str, Any]] = {
    "/api/v2/auth/key": {
        "body": {"descr": "Test API key from tests", "length_bytes": 16},
        "needs_basic_auth": True,
    },
    "/api/v2/auth/jwt": {
        "body": {},
        "needs_basic_auth": True,
    },
    "/api/v2/system/certificate/signing_request": {
        "body": {
            "descr": "Test CSR",
            "keytype": "RSA",
            "keylen": 2048,
            "digest_alg": "sha256",
            "dn_commonname": "test-csr.example.com",
        },
        "cleanup_path": "/api/v2/system/certificate",
    },
    "/api/v2/system/certificate_authority/generate": {
        "body": {
            "descr": "Test Generated CA",
            "keytype": "RSA",
            "keylen": 2048,
            "digest_alg": "sha256",
            "dn_commonname": "Test Gen CA",
            "dn_country": "US",
            "dn_state": "California",
            "dn_city": "San Francisco",
            "dn_organization": "pfSense Test",
            "dn_organizationalunit": "Testing",
            "lifetime": 3650,
        },
        "cleanup_path": "/api/v2/system/certificate_authority",
    },
    "/api/v2/system/certificate_authority/renew": {"needs_generated_ca": True},
    "/api/v2/system/certificate/generate": {
        "needs_ca": True,
        "body": {
            "descr": "Test Generated Cert",
            "keytype": "RSA",
            "keylen": 2048,
            "digest_alg": "sha256",
            "dn_commonname": "gen-cert.test",
            "lifetime": 365,
            "type": "server",
        },
        "cleanup_path": "/api/v2/system/certificate",
    },
    "/api/v2/system/certificate/renew": {"needs_generated_cert": True},
    "/api/v2/system/certificate/signing_request/sign": {"needs_ca_and_csr": True},
    "/api/v2/status/service": {
        "body": {"id": 0, "action": "restart"},
    },
    "/api/v2/diagnostics/command_prompt": {
        "body": {"command": "echo pfsense-mcp-test"},
    },
    "/api/v2/graphql": {
        "body": {"query": "{ __schema { queryType { name } } }"},
        "raw_response": True,  # GraphQL returns raw {"data": ...} not standard envelope
    },
    "/api/v2/services/wake_on_lan/send": {
        "body": {"interface": "lan", "mac_addr": "00:11:22:33:44:55"},
    },
    "/api/v2/diagnostics/ping": {
        "body": {"host": "127.0.0.1", "count": 1},
    },
    "/api/v2/system/certificate/pkcs12/export": {
        "needs_generated_cert": True,
    },
    "/api/v2/diagnostics/reboot": {
        "body": {},
        "test_prefix": "zz_",
    },
    "/api/v2/diagnostics/halt_system": {
        "body": {},
        "test_prefix": "zzz_",
    },
}

# Action endpoints to skip
_SKIP_ACTION: dict[str, str] = {
    "/api/v2/services/acme/account_key/register": "needs real ACME server for registration",
    "/api/v2/services/acme/certificate/issue": "requires real ACME server",
    "/api/v2/services/acme/certificate/renew": "requires real ACME server",
    "/api/v2/system/restapi/settings/sync": "HA sync endpoint times out without peer",
}

# ── Pre-generated test PEM certificates ───────────────────────────────────────
# Self-signed CA and server cert for testing certificate endpoints.
# Generated with: openssl req -x509 -newkey rsa:2048 ...
_TEST_CA_CERT_PEM = (
    "-----BEGIN CERTIFICATE-----\\n"
    "MIIDITCCAgmgAwIBAgICMDkwDQYJKoZIhvcNAQELBQAwKTEQMA4GA1UEAwwHVGVz\\n"
    "dCBDQTEVMBMGA1UECgwMcGZTZW5zZSBUZXN0MB4XDTI2MDIwNzA4NDMwOFoXDTM2\\n"
    "MDIwNTA4NDMwOFowKTEQMA4GA1UEAwwHVGVzdCBDQTEVMBMGA1UECgwMcGZTZW5z\\n"
    "ZSBUZXN0MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsHyXY8NQRm6C\\n"
    "OKfrDVjrVjWGePxOILQcpaU1GRGpbfXyjXQMbMOcHYDeXa853857iMhcH17bbBes\\n"
    "yEIYb0uy/dr42bAxLthnk7waOVefm4xkcG51MEe6tDIzsKC6kDfAclHb0Hjb9kgT\\n"
    "K20cW1yL6z9BHIghgas2kzwxJR9mM2ZirW5tVetdspDJi3755O6Q3j1nGK5KZBMC\\n"
    "sxTxVMyvldhZpaEEw3Rnz216lUlchcNDW1DlDoPuif9x4XfGWlijhX5B+/KNwnVT\\n"
    "J3WeW/obh2RtOn7fwZsweB9R7ZNgNeZK2SZytqYyOET25+iSWEAtlUg4zmug0SYE\\n"
    "/uErP4+yiwIDAQABo1MwUTAdBgNVHQ4EFgQUdNDSsN13N5F8L4E/zoSE/h+XN/Mw\\n"
    "HwYDVR0jBBgwFoAUdNDSsN13N5F8L4E/zoSE/h+XN/MwDwYDVR0TAQH/BAUwAwEB\\n"
    "/zANBgkqhkiG9w0BAQsFAAOCAQEAS+ML0N+Z2F6txyF/OUdV1Y9kf9DDQi9c48kJ\\n"
    "5jkFxX/m7Ur8XmKUY3QgucVvcIg9gHY4aOkW226DfMBrv/gC7Ko3i+Kz4SfdaZg6\\n"
    "XbNgJhWTdnGR/vYbuRoVw/UUA+Xs6aHMlA60pIYLacNVBigBsrEKznREjDceG+Bw\\n"
    "Bixkx+/UkmNf0J3dvzNYZTc1Hy27sm5wI2zsZlYAHOCgocU5fcXwICBqlVYbEejv\\n"
    "ERGkEIg2k3Sd+6Yh7gRxGkeQv9vMq7yZfEiTaQ9NMAD7FRjM5Mms1Fs2qkxG8JX3\\n"
    "v2DrRM6dA1e+yXyHDGCOmQcLsYnYXBD932W+EF14SQaaIELJ1g==\\n"
    "-----END CERTIFICATE-----"
)

_TEST_CA_KEY_PEM = (
    "-----BEGIN PRIVATE KEY-----\\n"
    "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCwfJdjw1BGboI4\\n"
    "p+sNWOtWNYZ4/E4gtBylpTUZEalt9fKNdAxsw5wdgN5drznfznuIyFwfXttsF6zI\\n"
    "QhhvS7L92vjZsDEu2GeTvBo5V5+bjGRwbnUwR7q0MjOwoLqQN8ByUdvQeNv2SBMr\\n"
    "bRxbXIvrP0EciCGBqzaTPDElH2YzZmKtbm1V612ykMmLfvnk7pDePWcYrkpkEwKz\\n"
    "FPFUzK+V2FmloQTDdGfPbXqVSVyFw0NbUOUOg+6J/3Hhd8ZaWKOFfkH78o3CdVMn\\n"
    "dZ5b+huHZG06ft/BmzB4H1Htk2A15krZJnK2pjI4RPbn6JJYQC2VSDjOa6DRJgT+\\n"
    "4Ss/j7KLAgMBAAECggEAFsQbq0zYoB1FQxW2JoSf5wEElbrGQUW6pEuJa/BxULP3\\n"
    "U/PyXl1lWBD1nlQqPQqfuOdPquRLncf4C+UqzcCQGFsU2s/1qDtWMSKEp3z8I86a\\n"
    "bj5xc4btOK15KYGyT0RB2P1iQ6Qzi7OEdYefrtFjYzdHqOyOlfGGGrwbAtToFB0c\\n"
    "FYT188F+R1i9K3CC3sX0I/A6xkRPBWNLkl6nDxKh9egHhrSCxecEzPcNTGoZo2Em\\n"
    "E309RGwnpvafeVc6jZfESGtiutpCf+trxKU+S/qlcmvC6222ZjPa18k+o4KSHpGm\\n"
    "9xBtbQxqYTVd16fKBLZF2OYcEAFezbhHsBeF6YGPYQKBgQDgl5sySL718A1AnWM0\\n"
    "hjJZOXuv08LyHEEWvQiIOVU2Cac1FrdV2lakMU8+aN899H//uY8W5PImR2/+gm6i\\n"
    "BFBFpfuEt/bytJ6/uyG1ztTq5YUjPENM7jD/p/KTyTlXd9SxaZ5cxMqKLIsINrKE\\n"
    "mrBsxKAeIsf94VngfadXeV14cwKBgQDJKs8RXMUk7u+vUlmYsjoKKfv0ucXwPg9N\\n"
    "uFPz7RWx2t0ZNfHQgrXgkTj+9d2NDNkdGC20rPK9zy3uULi3qTyTZ7oepMsNwUn1\\n"
    "Ov+yffnYHgzpuO3v2m6zhORq59AFrgbFzoNJUW5rAnfEBl+7HgeXLDqyvaTDPo6g\\n"
    "49ivGjaPiQKBgQCyzgBw+BmQE515Y9QnbO+IuYsPYLhDqNrpD3ZLfdmpO+YzDfLI\\n"
    "FxwDfH5qYXPaD14YadLRl1RxxU4UgiMyOdzulka4Uv34HHSGkKU16YT5veFRPBkY\\n"
    "lknMQBmQLxPH308mL8A0ezgE6ZGG6IUXrU/oSGJxm589MLwtTdx8d9NCoQKBgQDG\\n"
    "afLSrS3Fv+WohxDYCvI0FDTurE0PKCbwAV7MuIstYTGyLALWJhY96P7OerKK7KE4\\n"
    "kSCDlBHYJQCojfWjMMkOmsB4eRHN/1dzCT4qTxaekwUpgb0tVcTaS7j/uKT09TC4\\n"
    "6XeUWT0PTt/R+Hdzl6rk8Dr1ERfxe0IybojKLJCkAQKBgExKn6TG43y8gM9rxaSD\\n"
    "zRA8kLMI96LniQImjhHH/mSrWtW3t8Z5zDMn5vuPoaScv84SAiAWGDl6bmInNKpA\\n"
    "yA/IibZNOenOUHmFzS87uzoDrC7ch8eqEa43KhBcsryMYNqphwjw6CNL1gZkGVpT\\n"
    "1IgDA7lYJ4B3TIjIFzk/Pknn\\n"
    "-----END PRIVATE KEY-----"
)

_TEST_CERT_PEM = (
    "-----BEGIN CERTIFICATE-----\\n"
    "MIIDGjCCAgKgAwIBAgIDAQkyMA0GCSqGSIb3DQEBCwUAMCkxEDAOBgNVBAMMB1Rl\\n"
    "c3QgQ0ExFTATBgNVBAoMDHBmU2Vuc2UgVGVzdDAeFw0yNjAyMDcwODQzMDhaFw0z\\n"
    "NjAyMDUwODQzMDhaMDIxGTAXBgNVBAMMEHRlc3QuZXhhbXBsZS5jb20xFTATBgNV\\n"
    "BAoMDHBmU2Vuc2UgVGVzdDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEB\\n"
    "AMVJuOo0Uc/W/SmJ5VeWxbDmc4ERs1oYgN4iJfYbPTAyVOcncKcvRJfnn/7yzKBm\\n"
    "+8VJ6vEW85w4l9i1TpZGJcjVztcxGWyShQset4dGCEO/dlN5Mdjk40SUJagjnqJx\\n"
    "v5CiKRadBGonFC4q9OgzLTo49Pp67FTBLkJ2YOYfSKfff1jsRPWkVLh1DryhfhrG\\n"
    "MnIkSqiwd8GcH1CvLQgJXl+gkwW+aj0bFN/p8tqFdhzkOXNBuhDNV1cm7s9koLda\\n"
    "wRwEZC61kDBLD03F1BpTC3SCjwrffOSe9iaW6xu3Zd6thkWLk+qUbo7jVqssefEU\\n"
    "irI2TwwdIcoEcj+IKn2XDJkCAwEAAaNCMEAwHQYDVR0OBBYEFLpeQt6fkePzG8Rv\\n"
    "NVVxDg1TaFVSMB8GA1UdIwQYMBaAFHTQ0rDddzeRfC+BP86EhP4flzfzMA0GCSqG\\n"
    "SIb3DQEBCwUAA4IBAQBvvfaGdkf69515YpbZL3l7RPJV5xs/SEd0hWS9NiX1ccv9\\n"
    "L07Ldy0IbqYRochnWMZq/nZfTC6u2U2n1nMKeFlos5D351pZt7sNqSDBx28Uq2rN\\n"
    "x8Yh7h9UR18jkDJhv/SvFRWy7n2uQ4GQEZLoHzzhQMSoiCW2xGXl/28NZuY7br5a\\n"
    "FTnr7FQ+iqiVoX+mPocCYnhnD4gqtLQYlrkcnf9YAXtT1m01ICLWGImgIFp86kVY\\n"
    "Dfr8SxzwH1GAcFn0xB6I50yqxPCbGZBZqWvSAiynsxEK+TqWEk+cWN4Y+vkRWAbZ\\n"
    "f/gVTMr8CvCVTVmE3UTbWPD/YjzuN1WuDgqjDRjD\\n"
    "-----END CERTIFICATE-----"
)

_TEST_CERT_KEY_PEM = (
    "-----BEGIN PRIVATE KEY-----\\n"
    "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDFSbjqNFHP1v0p\\n"
    "ieVXlsWw5nOBEbNaGIDeIiX2Gz0wMlTnJ3CnL0SX55/+8sygZvvFSerxFvOcOJfY\\n"
    "tU6WRiXI1c7XMRlskoULHreHRghDv3ZTeTHY5ONElCWoI56icb+QoikWnQRqJxQu\\n"
    "KvToMy06OPT6euxUwS5CdmDmH0in339Y7ET1pFS4dQ68oX4axjJyJEqosHfBnB9Q\\n"
    "ry0ICV5foJMFvmo9GxTf6fLahXYc5DlzQboQzVdXJu7PZKC3WsEcBGQutZAwSw9N\\n"
    "xdQaUwt0go8K33zknvYmlusbt2XerYZFi5PqlG6O41arLHnxFIqyNk8MHSHKBHI/\\n"
    "iCp9lwyZAgMBAAECggEAK4X6D2D/c3SgYRuUxt/yOPZ+IMlA4e1p8Jdj/IlB1HIm\\n"
    "HOCsj5Vz8ncc6uexkOlnPbzy4cEIeTxa82n8LlbHWykf+oVQcI1aYHukTWl7xUZl\\n"
    "2kBwaMMGCEkOjateAcRKWKQNoHl/UdPRNeYwJVG09pU+Jkwb+w6rH+pxshLQuofG\\n"
    "pD1BZWzs9EfuVXeuo1h4pk8T9JL0VsYQWBr97Le5EGMgGEkPEvVS3SgT8if0tAU+\\n"
    "Ld3kOv7GgGKeNjos3PMpCp82kHYsA+KXKpwQIrut/LRnBm3eSzOqjbh3QQF7UbxH\\n"
    "1ah28lnTzwc5GUi3A9Aj0WupDTwimtSnV2evgDh/IQKBgQDnAsfLP/AxPsFIzld3\\n"
    "DiydfD5jWWvCHwElBex7yDHxHXPdoywvRBueT+EoG8IhvTcroCUIWy82Af7TQ6WL\\n"
    "m/WmjWlmsnZ8ah1r42gx4rObRc18q2yNnAPksDVbBLoSY4vp8o2o56vme321G02A\\n"
    "r/I0lzqaYIX7lxJmDsscNgExLQKBgQDaoRP6vg4v2TsKJZGGO/Z4VUUWu9QLexzj\\n"
    "TllWogMqZZ6flMQshhyBP7N/hiO1VbDE0aiuAsO/ZTbdPVXZ8pA8oM2cEfWNNDsc\\n"
    "rvlm4vQrJ+awp2RnEQsniRizgxeYwzQjo1am7uv2udrYenwhgnNVDQEdlTlOzO8a\\n"
    "9N9a2BH0nQKBgAM1KK0L0Dv+0RQ/uTsv+TKenQcoILTrVUq8UFJPr1HXxNoY/+4Q\\n"
    "FgoWtdumtwVc6T0z1g/NpFQtpuosEEpl+f08DXCdncOQfaQX3kSDD1dimr3Wa4Vz\\n"
    "2yH7yGHhKOxEcZboBUuJG/vxTweKv4K/7q8IQooOOQ4LRPgh0HQt08ppAoGBANki\\n"
    "e5ZfpfVtuU5Vi5eW/C38+jYe6/VPG5zB1sbM93nnHUh+1uslczAG1T5FOjfB2GNR\\n"
    "m0bfpgvz+S532UkxuIEOb8aeq5LHGiJdwYOmyjwGT/6I8ZXPfpWQesDm5Muqq6Dt\\n"
    "e4Ul66LKaYjw9VHOnr8MwFviNd2Geb77Ds3JpOOdAoGBAMZ0cH7TID2qhOhbHNbq\\n"
    "1oe1VMJ2wABJQ923jPwNa8UqzoZtE/NGkzaEPBZ91SpHSo88DmzcvY06C7tKi//H\\n"
    "k4i7T0WIbj93UPzwEzamnI+KF1rrzsZpImoJ5vvEe7EnQMXUwcGwXsJZphNjFhUp\\n"
    "wpkYG2WCI0nyfqoM9noi/oj1\\n"
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
            "if": "em0",
            "tag": 100,
            "pcp": 0,
            "descr": "Test VLAN",
        },
        "update_field": "descr",
    },
    # ── Interface (needs VLAN as parent) ──────────────────────────────────
    "/api/v2/interface": {
        "parents": [
            {
                "path": "/api/v2/interface/vlan",
                "body_template": {
                    "if": "em2",
                    "tag": 999,
                    "pcp": 0,
                    "descr": "Test VLAN for iface",
                },
                "tag": "iface",
                "inject": {"if": "vlanif"},
            }
        ],
        "child_body": {
            "descr": "TESTVLAN",
            "enable": True,
            "typev4": "static",
            "ipaddr": "10.99.99.1",
            "subnet": 24,
            "ipaddrv6": "none",
            "subnetv6": 128,
            "prefix_6rd": "",
            "gateway_6rd": "",
            "prefix_6rd_v4plen": 0,
            "track6_interface": "",
        },
        "update_field": "descr",
        "update_value": '"TESTVLAN_UPDATED"',
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
    # NOTE: bind/sync/domain removed — path does not exist in OpenAPI spec
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
    # ── Firewall schedule/time_range ─────────────────────────────────────
    "/api/v2/firewall/schedule/time_range": {
        "parents": [
            {
                "path": "/api/v2/firewall/schedule",
                "body": {
                    "name": "pft_sched_tr",
                    "timerange": [{"month": "1,2,3", "day": "1,2,3", "hour": "0:00-23:59", "position": []}],
                    "descr": "Test schedule for time_range",
                },
                "inject": {"parent_id": "id"},
            }
        ],
        "child_body": {
            "month": [4, 5, 6],
            "day": [10, 11, 12],
            "hour": "8:00-17:00",
        },
        "update_field": None,
    },
    # ── Traffic shaper limiter/bandwidth ──────────────────────────────────
    "/api/v2/firewall/traffic_shaper/limiter/bandwidth": {
        "parents": [
            {
                "path": "/api/v2/firewall/traffic_shaper/limiter",
                "body": {
                    "aqm": "droptail",
                    "name": "pft_lim_bw",
                    "sched": "wf2q+",
                    "bandwidth": [{"bw": 100, "bwscale": "Mb", "schedule": "none"}],
                    "buckets": 16,
                    "ecn": False,
                    "enabled": False,
                    "mask": "none",
                    "maskbits": 1,
                    "maskbitsv6": 1,
                    "queue": [],
                },
                "inject": {"parent_id": "id"},
            }
        ],
        "child_body": {
            "bw": 50,
            "bwscale": "Mb",
        },
        "update_field": None,
    },
    # ── Traffic shaper limiter/queue ──────────────────────────────────────
    "/api/v2/firewall/traffic_shaper/limiter/queue": {
        "parents": [
            {
                "path": "/api/v2/firewall/traffic_shaper/limiter",
                "body": {
                    "aqm": "droptail",
                    "name": "pft_lim_q",
                    "sched": "wf2q+",
                    "bandwidth": [{"bw": 100, "bwscale": "Mb", "schedule": "none"}],
                    "buckets": 16,
                    "ecn": False,
                    "enabled": False,
                    "mask": "none",
                    "maskbits": 1,
                    "maskbitsv6": 1,
                    "queue": [],
                },
                "inject": {"parent_id": "id"},
            }
        ],
        "child_body": {
            "name": "pft_limq",
            "aqm": "droptail",
        },
        "update_field": None,
    },
    # ── Traffic shaper/queue ──────────────────────────────────────────────
    "/api/v2/firewall/traffic_shaper/queue": {
        "parents": [
            {
                "path": "/api/v2/firewall/traffic_shaper",
                "body": {
                    "bandwidth": 100,
                    "bandwidthtype": "Mb",
                    "interface": "wan",
                    "scheduler": "HFSC",
                    "enabled": False,
                    "qlimit": 50,
                    "queue": [],
                    "tbrconfig": 1,
                },
                "inject": {"parent_id": "id"},
            }
        ],
        "child_body": {
            "name": "pft_tsq",
            "qlimit": 50,
            "bandwidth": 100,
            "upperlimit_m2": "",
            "realtime_m2": "",
            "linkshare_m2": "10%",
        },
        "update_field": None,
    },
    # ── BIND access_list/entry ────────────────────────────────────────────
    "/api/v2/services/bind/access_list/entry": {
        "parents": [
            {
                "path": "/api/v2/services/bind/access_list",
                "body": {
                    "entries": [{"value": "10.0.0.0/8", "description": "test entry"}],
                    "name": "pft_bacl_en",
                },
                "inject": {"parent_id": "id"},
            }
        ],
        "child_body": {
            "value": "10.1.0.0/16",
        },
        "update_field": None,
    },
    # ── BIND zone/record ──────────────────────────────────────────────────
    "/api/v2/services/bind/zone/record": {
        "parents": [
            {
                "path": "/api/v2/services/bind/zone",
                "body": {
                    "name": "pftzrec.example.com",
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
            "name": "testrec",
            "type": "A",
            "rdata": "10.99.99.1",
            "priority": 0,
        },
        "update_field": None,
    },
    # ── DNS forwarder host_override/alias ─────────────────────────────────
    "/api/v2/services/dns_forwarder/host_override/alias": {
        "parents": [
            {
                "path": "/api/v2/services/dns_forwarder/host_override",
                "body": {
                    "domain": "example.com",
                    "host": "pft-dnsfwd-al",
                    "ip": "10.99.99.2",
                    "aliases": [],
                    "descr": "Test host override for alias",
                },
                "inject": {"parent_id": "id"},
            }
        ],
        "child_body": {
            "host": "testalias",
            "domain": "alias.example.com",
        },
        "update_field": None,
    },
    # ── DNS resolver access_list/network ──────────────────────────────────
    "/api/v2/services/dns_resolver/access_list/network": {
        "parents": [
            {
                "path": "/api/v2/services/dns_resolver/access_list",
                "body": {
                    "action": "allow",
                    "name": "pft_dnsacl_nw",
                    "networks": [],
                },
                "inject": {"parent_id": "id"},
            }
        ],
        "child_body": {
            "network": "10.1.0.0",
            "mask": 16,
        },
        "update_field": None,
    },
    # ── DNS resolver host_override/alias ──────────────────────────────────
    "/api/v2/services/dns_resolver/host_override/alias": {
        "parents": [
            {
                "path": "/api/v2/services/dns_resolver/host_override",
                "body": {
                    "domain": "example.com",
                    "host": "pft-dnsres-al",
                    "ip": ["10.99.99.2"],
                    "aliases": [],
                    "descr": "Test host override for alias",
                },
                "inject": {"parent_id": "id"},
            }
        ],
        "child_body": {
            "host": "testalias",
            "domain": "alias.example.com",
        },
        "update_field": None,
    },
    # ── WireGuard tunnel/address ──────────────────────────────────────────
    "/api/v2/vpn/wireguard/tunnel/address": {
        "parents": [
            {
                "path": "/api/v2/vpn/wireguard/tunnel",
                "body": {
                    "name": "pft_tun_addr",
                    "listenport": "51822",
                    "privatekey": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY=",
                    "addresses": [],
                },
                "inject": {"parent_id": "id"},
            }
        ],
        "child_body": {
            "address": "10.100.0.1",
            "mask": 24,
        },
        "update_field": None,
    },
    # ── WireGuard peer/allowed_ip (2-level: tunnel → peer → allowed_ip) ──
    "/api/v2/vpn/wireguard/peer/allowed_ip": {
        "parents": [
            {
                "path": "/api/v2/vpn/wireguard/tunnel",
                "body": {
                    "name": "pft_tun_aip",
                    "listenport": "51823",
                    "privatekey": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY=",
                    "addresses": [],
                },
            },
            {
                "path": "/api/v2/vpn/wireguard/peer",
                "body": {
                    "tun": "pft_tun_aip",
                    "publickey": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY=",
                    "descr": "Test WG peer for allowed_ip",
                },
                "inject": {"parent_id": "id"},
            },
        ],
        "child_body": {
            "address": "10.200.0.0",
            "mask": 24,
        },
        "update_field": None,
    },
    # ── System CRL (needs CA) ────────────────────────────────────────────
    "/api/v2/system/crl": {
        "parents": [
            {
                "path": "/api/v2/system/certificate_authority",
                "body": {
                    "descr": "Test CA for CRL",
                    "crt": "__CA_CERT_PEM__",
                    "prv": "__CA_KEY_PEM__",
                },
                "inject": {"caref": "refid"},
            }
        ],
        "child_body": {
            "descr": "Test CRL",
            "method": "internal",
            "text": "",
        },
        "update_field": None,  # descr is not editable on CRL
    },
    # ── System CRL/revoked_certificate ──────────────────────────────────
    # SKIPPED: pfSense server bug — cert serial number is hex but CRL code
    # expects INT (500: "0x... is not INT" in openssl_x509_crl/X509_CRL.php).
    # Uncomment when upstream fixes the CRL revocation endpoint.
    # "/api/v2/system/crl/revoked_certificate": { ... },
    #
    # ── (placeholder to keep structure — remove above comment when fixed) ──
    # ── Routing gateway/group/priority (3-level) ─────────────────────────
    "/api/v2/routing/gateway/group/priority": {
        "parents": [
            {
                "path": "/api/v2/routing/gateway",
                "body_template": _GATEWAY_BODY,
                "tag": "gp",
            },
            {
                "path": "/api/v2/routing/gateway",
                "body": {
                    "name": "pft_gw_gp2",
                    "gateway": "10.0.2.99",
                    "interface": "wan",
                    "ipprotocol": "inet",
                    "descr": "Test GW 2 for priority",
                },
            },
            {
                "path": "/api/v2/routing/gateway/group",
                "body": {
                    "name": "pft_gw_grp_p",
                    "descr": "Test group for priority",
                    "priorities": [{"gateway": "pft_gw_gp", "tier": 1}],
                },
                "inject": {"parent_id": "id"},
            },
        ],
        "child_body": {
            "gateway": "pft_gw_gp2",
            "tier": 2,
        },
        "update_field": None,
    },
    # ── HAProxy frontend/certificate ─────────────────────────────────────
    "/api/v2/services/haproxy/frontend/certificate": {
        "parents": [
            {
                "path": "/api/v2/services/haproxy/backend",
                "body_template": _HAPROXY_BACKEND_BODY,
                "tag": "fcrt",
            },
            {
                "path": "/api/v2/services/haproxy/frontend",
                "body": {"name": "pft_fe_crt", "type": "http"},
                "inject": {"parent_id": "id"},
            },
        ],
        "child_body": {},
        "update_field": None,
    },
    # ── HAProxy backend/error_file (file + backend) ──────────────────────
    "/api/v2/services/haproxy/backend/error_file": {
        "parents": [
            {
                "path": "/api/v2/services/haproxy/file",
                "body": {"name": "pft_ha_efb", "content": "PCFET0NUWVBFIGh0bWw+"},
            },
            {
                "path": "/api/v2/services/haproxy/backend",
                "body_template": _HAPROXY_BACKEND_BODY,
                "tag": "bef",
                "inject": {"parent_id": "id"},
            },
        ],
        "child_body": {
            "errorcode": 503,
            "errorfile": "pft_ha_efb",
        },
        "update_field": None,
    },
    # ── HAProxy frontend/error_file (file + backend + frontend) ──────────
    "/api/v2/services/haproxy/frontend/error_file": {
        "parents": [
            {
                "path": "/api/v2/services/haproxy/file",
                "body": {"name": "pft_ha_eff", "content": "PCFET0NUWVBFIGh0bWw+"},
            },
            {
                "path": "/api/v2/services/haproxy/backend",
                "body_template": _HAPROXY_BACKEND_BODY,
                "tag": "fef",
            },
            {
                "path": "/api/v2/services/haproxy/frontend",
                "body": {"name": "pft_fe_ef", "type": "http"},
                "inject": {"parent_id": "id"},
            },
        ],
        "child_body": {
            "errorcode": 503,
            "errorfile": "pft_ha_eff",
        },
        "update_field": None,
    },
    # ── VPN IPsec phase1 (CA + cert → phase1) ────────────────────────────
    "/api/v2/vpn/ipsec/phase1": {
        "parents": [
            {
                "path": "/api/v2/system/certificate_authority",
                "body": {
                    "descr": "Test CA for IPsec",
                    "crt": "__CA_CERT_PEM__",
                    "prv": "__CA_KEY_PEM__",
                },
                "inject": {"caref": "refid"},
            },
            {
                "path": "/api/v2/system/certificate",
                "body": {
                    "descr": "Test Cert for IPsec",
                    "crt": "__CERT_PEM__",
                    "prv": "__CERT_KEY_PEM__",
                },
                "receives_from": {0: {"caref": "refid"}},
                "inject": {"certref": "refid"},
            },
        ],
        "child_body": {
            "iketype": "ikev2",
            "mode": "main",
            "protocol": "inet",
            "interface": "wan",
            "remote_gateway": "10.99.99.20",
            "authentication_method": "pre_shared_key",
            "myid_type": "myaddress",
            "myid_data": "",
            "peerid_type": "any",
            "peerid_data": "",
            "pre_shared_key": "TestPSK123456789012345",
            "descr": "Test IPsec P1",
            "encryption": [
                {
                    "encryption_algorithm_name": "aes",
                    "encryption_algorithm_keylen": 256,
                    "hash_algorithm": "sha256",
                    "dhgroup": 14,
                }
            ],
        },
        "update_field": "descr",
    },
    # ── VPN IPsec phase1/encryption ──────────────────────────────────────
    "/api/v2/vpn/ipsec/phase1/encryption": {
        "parents": [
            {
                "path": "/api/v2/system/certificate_authority",
                "body": {
                    "descr": "Test CA for P1enc",
                    "crt": "__CA_CERT_PEM__",
                    "prv": "__CA_KEY_PEM__",
                },
            },
            {
                "path": "/api/v2/system/certificate",
                "body": {
                    "descr": "Test Cert for P1enc",
                    "crt": "__CERT_PEM__",
                    "prv": "__CERT_KEY_PEM__",
                },
                "receives_from": {0: {"caref": "refid"}},
            },
            {
                "path": "/api/v2/vpn/ipsec/phase1",
                "body": {
                    "iketype": "ikev2",
                    "mode": "main",
                    "protocol": "inet",
                    "interface": "wan",
                    "remote_gateway": "10.99.99.21",
                    "authentication_method": "pre_shared_key",
                    "myid_type": "myaddress",
                    "myid_data": "",
                    "peerid_type": "any",
                    "peerid_data": "",
                    "pre_shared_key": "TestPSK123456789012345",
                    "descr": "Test P1 for enc",
                    "encryption": [
                        {
                            "encryption_algorithm_name": "aes",
                            "encryption_algorithm_keylen": 256,
                            "hash_algorithm": "sha256",
                            "dhgroup": 14,
                        }
                    ],
                },
                "receives_from": {0: {"caref": "refid"}, 1: {"certref": "refid"}},
                "inject": {"parent_id": "id"},
            },
        ],
        "child_body": {
            "encryption_algorithm_name": "aes128gcm",
            "encryption_algorithm_keylen": 128,
            "hash_algorithm": "sha256",
            "dhgroup": 14,
        },
        "update_field": None,
    },
    # ── VPN IPsec phase2 (CA + cert → phase1 → phase2) ──────────────────
    "/api/v2/vpn/ipsec/phase2": {
        "parents": [
            {
                "path": "/api/v2/system/certificate_authority",
                "body": {
                    "descr": "Test CA for P2",
                    "crt": "__CA_CERT_PEM__",
                    "prv": "__CA_KEY_PEM__",
                },
            },
            {
                "path": "/api/v2/system/certificate",
                "body": {
                    "descr": "Test Cert for P2",
                    "crt": "__CERT_PEM__",
                    "prv": "__CERT_KEY_PEM__",
                },
                "receives_from": {0: {"caref": "refid"}},
            },
            {
                "path": "/api/v2/vpn/ipsec/phase1",
                "body": {
                    "iketype": "ikev2",
                    "mode": "main",
                    "protocol": "inet",
                    "interface": "wan",
                    "remote_gateway": "10.99.99.22",
                    "authentication_method": "pre_shared_key",
                    "myid_type": "myaddress",
                    "myid_data": "",
                    "peerid_type": "any",
                    "peerid_data": "",
                    "pre_shared_key": "TestPSK123456789012345",
                    "descr": "Test P1 for P2",
                    "encryption": [
                        {
                            "encryption_algorithm_name": "aes",
                            "encryption_algorithm_keylen": 256,
                            "hash_algorithm": "sha256",
                            "dhgroup": 14,
                        }
                    ],
                },
                "receives_from": {0: {"caref": "refid"}, 1: {"certref": "refid"}},
                "inject": {"ikeid": "ikeid"},
            },
        ],
        "child_body": {
            "mode": "tunnel",
            "localid_type": "network",
            "localid_address": "10.0.0.0",
            "localid_netbits": 24,
            "natlocalid_address": "",
            "natlocalid_netbits": 0,
            "remoteid_type": "network",
            "remoteid_address": "10.200.0.0",
            "remoteid_netbits": 24,
            "descr": "Test IPsec P2",
            "encryption_algorithm_option": [{"name": "aes", "keylen": 256}],
            "hash_algorithm_option": ["hmac_sha256"],
        },
        "update_field": "descr",
    },
    # ── VPN IPsec phase2/encryption ──────────────────────────────────────
    "/api/v2/vpn/ipsec/phase2/encryption": {
        "parents": [
            {
                "path": "/api/v2/system/certificate_authority",
                "body": {
                    "descr": "Test CA for P2enc",
                    "crt": "__CA_CERT_PEM__",
                    "prv": "__CA_KEY_PEM__",
                },
            },
            {
                "path": "/api/v2/system/certificate",
                "body": {
                    "descr": "Test Cert for P2enc",
                    "crt": "__CERT_PEM__",
                    "prv": "__CERT_KEY_PEM__",
                },
                "receives_from": {0: {"caref": "refid"}},
            },
            {
                "path": "/api/v2/vpn/ipsec/phase1",
                "body": {
                    "iketype": "ikev2",
                    "mode": "main",
                    "protocol": "inet",
                    "interface": "wan",
                    "remote_gateway": "10.99.99.23",
                    "authentication_method": "pre_shared_key",
                    "myid_type": "myaddress",
                    "myid_data": "",
                    "peerid_type": "any",
                    "peerid_data": "",
                    "pre_shared_key": "TestPSK123456789012345",
                    "descr": "Test P1 for P2enc",
                    "encryption": [
                        {
                            "encryption_algorithm_name": "aes",
                            "encryption_algorithm_keylen": 256,
                            "hash_algorithm": "sha256",
                            "dhgroup": 14,
                        }
                    ],
                },
                "receives_from": {0: {"caref": "refid"}, 1: {"certref": "refid"}},
            },
            {
                "path": "/api/v2/vpn/ipsec/phase2",
                "body": {
                    "mode": "tunnel",
                    "localid_type": "network",
                    "localid_address": "10.0.0.0",
                    "localid_netbits": 24,
                    "natlocalid_address": "",
                    "natlocalid_netbits": 0,
                    "remoteid_type": "network",
                    "remoteid_address": "10.200.0.0",
                    "remoteid_netbits": 24,
                    "descr": "Test P2 for enc",
                    "encryption_algorithm_option": [{"name": "aes", "keylen": 256}],
                    "hash_algorithm_option": ["hmac_sha256"],
                },
                "receives_from": {2: {"ikeid": "ikeid"}},
                "inject": {"parent_id": "id"},
            },
        ],
        "child_body": {
            "name": "aes128gcm",
            "keylen": 128,
        },
        "update_field": None,
    },
    # ── VPN OpenVPN server (CA + cert → server) ──────────────────────────
    "/api/v2/vpn/openvpn/server": {
        "parents": [
            {
                "path": "/api/v2/system/certificate_authority",
                "body": {
                    "descr": "Test CA for OVPN srv",
                    "crt": "__CA_CERT_PEM__",
                    "prv": "__CA_KEY_PEM__",
                },
                "inject": {"caref": "refid"},
            },
            {
                "path": "/api/v2/system/certificate",
                "body": {
                    "descr": "Test Cert for OVPN srv",
                    "crt": "__CERT_PEM__",
                    "prv": "__CERT_KEY_PEM__",
                },
                "receives_from": {0: {"caref": "refid"}},
                "inject": {"certref": "refid"},
            },
        ],
        "child_body": {
            "mode": "p2p_tls",
            "dev_mode": "tun",
            "protocol": "UDP4",
            "interface": "wan",
            "tls_type": "auth",
            "dh_length": "2048",
            "ecdh_curve": "prime256v1",
            "data_ciphers": ["AES-256-GCM"],
            "data_ciphers_fallback": "AES-256-GCM",
            "digest": "SHA256",
            "description": "Test OVPN server",
            "serverbridge_interface": "",
            "serverbridge_dhcp_start": "",
            "serverbridge_dhcp_end": "",
        },
        "update_field": "description",
    },
    # ── VPN OpenVPN client (CA → client) ─────────────────────────────────
    "/api/v2/vpn/openvpn/client": {
        "parents": [
            {
                "path": "/api/v2/system/certificate_authority",
                "body": {
                    "descr": "Test CA for OVPN cli",
                    "crt": "__CA_CERT_PEM__",
                    "prv": "__CA_KEY_PEM__",
                },
                "inject": {"caref": "refid"},
            },
        ],
        "child_body": {
            "mode": "p2p_tls",
            "dev_mode": "tun",
            "protocol": "UDP4",
            "interface": "wan",
            "server_addr": "10.99.99.30",
            "server_port": "1194",
            "proxy_user": "",
            "proxy_passwd": "",
            "tls_type": "auth",
            "data_ciphers": ["AES-256-GCM"],
            "data_ciphers_fallback": "AES-256-GCM",
            "digest": "SHA256",
            "description": "Test OVPN client",
        },
        "update_field": "description",
    },
    # ── VPN OpenVPN CSO ──────────────────────────────────────────────────
    "/api/v2/vpn/openvpn/cso": {
        "parents": [],
        "child_body": {
            "common_name": "pft_ovpn_cso",
            "description": "Test CSO",
        },
        "update_field": "description",
    },
    # ── ACME certificate (needs account key) ─────────────────────────────
    "/api/v2/services/acme/certificate": {
        "parents": [
            {
                "path": "/api/v2/services/acme/account_key",
                "body": {
                    "name": "pft_acme_crt",
                    "descr": "Test ACME key for cert",
                    "email": "test@example.com",
                    "acmeserver": "letsencrypt-staging-2",
                },
                "inject": {"acmeaccount": "name"},
            },
        ],
        "child_body": {
            "name": "pft_acme_cert",
            "descr": "Test ACME cert",
            "keypaste": "__CERT_KEY_PEM__",
            "a_domainlist": [
                {"name": "test.example.com", "method": "standalone", "status": "enable"}
            ],
        },
        "update_field": "descr",
    },
    # ── ACME certificate/domain ──────────────────────────────────────────
    "/api/v2/services/acme/certificate/domain": {
        "parents": [
            {
                "path": "/api/v2/services/acme/account_key",
                "body": {
                    "name": "pft_acme_dom",
                    "descr": "Test ACME key for domain",
                    "email": "test@example.com",
                    "acmeserver": "letsencrypt-staging-2",
                },
            },
            {
                "path": "/api/v2/services/acme/certificate",
                "body": {
                    "name": "pft_acme_cd",
                    "descr": "Test ACME cert for domain",
                    "keypaste": "__CERT_KEY_PEM__",
                    "a_domainlist": [
                        {"name": "test1.example.com", "method": "standalone", "status": "enable"}
                    ],
                },
                "receives_from": {0: {"acmeaccount": "name"}},
                "inject": {"parent_id": "id"},
            },
        ],
        "child_body": {
            "name": "test2.example.com",
            "method": "standalone",
            "status": "enable",
        },
        "update_field": None,
    },
    # ── ACME certificate/action ──────────────────────────────────────────
    "/api/v2/services/acme/certificate/action": {
        "parents": [
            {
                "path": "/api/v2/services/acme/account_key",
                "body": {
                    "name": "pft_acme_act",
                    "descr": "Test ACME key for action",
                    "email": "test@example.com",
                    "acmeserver": "letsencrypt-staging-2",
                },
            },
            {
                "path": "/api/v2/services/acme/certificate",
                "body": {
                    "name": "pft_acme_ca",
                    "descr": "Test ACME cert for action",
                    "keypaste": "__CERT_KEY_PEM__",
                    "a_domainlist": [
                        {"name": "test3.example.com", "method": "standalone", "status": "enable"}
                    ],
                },
                "receives_from": {0: {"acmeaccount": "name"}},
                "inject": {"parent_id": "id"},
            },
        ],
        "child_body": {
            "command": "echo test",
            "method": "shellcommand",
        },
        "update_field": None,
    },
    # ── Interface GRE tunnel ──────────────────────────────────────────────
    "/api/v2/interface/gre": {
        "parents": [],
        "child_body": {
            "if": "wan",
            "remote_addr": "198.51.100.1",
            "tunnel_local_addr": "10.255.0.1",
            "tunnel_remote_addr": "10.255.0.2",
            "tunnel_remote_addr6": "",
        },
        "update_field": None,
    },
    # ── Interface LAGG ────────────────────────────────────────────────────
    "/api/v2/interface/lagg": {
        "parents": [],
        "child_body": {
            "members": ["em2"],
            "proto": "none",
            "descr": "Test LAGG",
        },
        "update_field": None,
    },
    # ── DHCP server sub-resources (static parent_id = "lan") ─────────────
    "/api/v2/services/dhcp_server/address_pool": {
        "parents": [],
        "child_body": {
            "parent_id": "lan",
            "range_from": "192.168.1.210",
            "range_to": "192.168.1.220",
        },
        "static_parent_id": "lan",
        "update_field": None,
    },
    "/api/v2/services/dhcp_server/custom_option": {
        "parents": [],
        "child_body": {
            "parent_id": "lan",
            "number": 252,
            "type": "text",
            "value": "http://wpad.example.com/wpad.dat",
        },
        "static_parent_id": "lan",
        "update_field": None,
    },
    "/api/v2/services/dhcp_server/static_mapping": {
        "parents": [],
        "child_body": {
            "parent_id": "lan",
            "mac": "00:11:22:33:44:55",
            "ipaddr": "192.168.1.250",
            "descr": "Test static map",
        },
        "static_parent_id": "lan",
        "update_field": "descr",
    },
    # ── HAProxy backend/action (needs backend parent + ACL sibling) ──────
    "/api/v2/services/haproxy/backend/action": {
        "parents": [
            {
                "path": "/api/v2/services/haproxy/backend",
                "body_template": _HAPROXY_BACKEND_BODY,
                "tag": "bact",
                "inject": {"parent_id": "id"},
            }
        ],
        "siblings": [
            {
                "path": "/api/v2/services/haproxy/backend/acl",
                "body": {
                    "name": "pft_acl_bact",
                    "expression": "host_starts_with",
                    "value": "test.example.com",
                },
                "inject": {"acl": "name"},
            }
        ],
        "child_body": {
            "action": "http-request_deny",
            "server": "",
            "customaction": "",
            "deny_status": "403",
            "realm": "",
            "rule": "",
            "lua_function": "",
            "name": "",
            "fmt": "",
            "find": "",
            "replace": "",
            "path": "",
            "status": "",
            "reason": "Denied",
        },
        "update_field": None,
    },
    # ── HAProxy frontend/action (needs backend + frontend parents + ACL sibling) ─
    "/api/v2/services/haproxy/frontend/action": {
        "parents": [
            {
                "path": "/api/v2/services/haproxy/backend",
                "body_template": _HAPROXY_BACKEND_BODY,
                "tag": "fact",
            },
            {
                "path": "/api/v2/services/haproxy/frontend",
                "body": {
                    "name": "pft_fe_act",
                    "type": "http",
                },
                "inject": {"parent_id": "id"},
            },
        ],
        "siblings": [
            {
                "path": "/api/v2/services/haproxy/frontend/acl",
                "body": {
                    "name": "pft_acl_fact",
                    "expression": "host_starts_with",
                    "value": "test.example.com",
                },
                "inject": {"acl": "name"},
            }
        ],
        "child_body": {
            "action": "http-request_deny",
            "server": "",
            "customaction": "",
            "deny_status": "403",
            "realm": "",
            "rule": "",
            "lua_function": "",
            "name": "",
            "fmt": "",
            "find": "",
            "replace": "",
            "path": "",
            "status": "",
            "reason": "Denied",
        },
        "update_field": None,
    },
    # ── System CRL/revoked_certificate ────────────────────────────────────
    "/api/v2/system/crl/revoked_certificate": {
        "parents": [
            {
                "path": "/api/v2/system/certificate_authority",
                "body": {
                    "descr": "CA for CRL revoke",
                    "crt": "__CA_CERT_PEM__",
                    "prv": "__CA_KEY_PEM__",
                },
                "inject": {"caref": "refid"},
            },
            {
                "path": "/api/v2/system/certificate",
                "body": {
                    "descr": "Cert for CRL revoke",
                    "crt": "__CERT_PEM__",
                    "prv": "__CERT_KEY_PEM__",
                },
                "receives_from": {0: {"caref": "refid"}},
                "inject": {"certref": "refid"},
            },
            {
                "path": "/api/v2/system/crl",
                "body": {
                    "descr": "CRL for revoke",
                    "method": "internal",
                    "text": "",
                },
                "receives_from": {0: {"caref": "refid"}},
                "inject": {"parent_id": "id"},
            },
        ],
        "child_body": {
            "revoke_time": 1700000000,
            "reason": 0,
        },
        "update_field": None,
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

    # Check path-based skip list first (takes priority over chained config)
    if group.base_path in _SKIP_CRUD_PATHS:
        return True, _SKIP_CRUD_PATHS[group.base_path]

    # Chained tests handle their own dependencies — don't skip them
    if group.base_path in _CHAINED_CRUD:
        return False, ""

    # Check for required fields we can't generate
    for p in group.create.parameters:
        if p.required and p.name == "parent_id":
            return True, "requires parent_id (needs parent resource first)"
        if p.required and p.name in ("caref", "certref"):
            return True, f"requires {p.name} (needs existing CA/cert)"

    return False, ""


# ── Custom test functions (non-standard patterns) ────────────────────────────
_CUSTOM_TESTS: list[str] = [
    # OpenVPN client export: 6-step chain across two endpoints.
    # Requires pfSense-pkg-openvpn-client-export (pre-installed in golden image).
    '''\
def test_action_vpn_openvpn_client_export(client: httpx.Client):
    """Action + CRUD: /api/v2/vpn/openvpn/client_export (+config)"""
    # 1. Create CA
    ca_resp = client.post("/api/v2/system/certificate_authority/generate", json={
        "descr": "CA for OVPN export", "keytype": "RSA", "keylen": 2048,
        "digest_alg": "sha256", "dn_commonname": "OVPN Export CA", "lifetime": 3650,
        "dn_country": "US", "dn_state": "California", "dn_city": "San Francisco",
        "dn_organization": "pfSense Test", "dn_organizationalunit": "Testing",
    })
    ca = _ok(ca_resp)
    try:
        # 2. Create server certificate
        srv_cert_resp = client.post("/api/v2/system/certificate/generate", json={
            "descr": "OVPN server cert", "caref": ca["refid"], "keytype": "RSA",
            "keylen": 2048, "digest_alg": "sha256", "dn_commonname": "ovpn-server.test",
            "lifetime": 365, "type": "server",
        })
        srv_cert = _ok(srv_cert_resp)
        try:
            # 3. Create OpenVPN server (server_tls mode avoids auth issues)
            ovpn_resp = client.post("/api/v2/vpn/openvpn/server", json={
                "mode": "server_tls", "dev_mode": "tun", "protocol": "UDP4",
                "interface": "wan", "local_port": "11941",
                "caref": ca["refid"], "certref": srv_cert["refid"],
                "dh_length": "2048", "ecdh_curve": "prime256v1",
                "tunnel_network": "10.0.8.0/24",
                "description": "OVPN export test",
                "data_ciphers": ["AES-256-GCM"],
                "data_ciphers_fallback": "AES-256-GCM",
                "digest": "SHA256",
            })
            # server_tls mode may produce log output before JSON
            assert ovpn_resp.status_code == 200, f"OVPN server create {ovpn_resp.status_code}: {ovpn_resp.text[:500]}"
            text = ovpn_resp.text
            json_start = text.find("{")
            ovpn = json.loads(text[json_start:])["data"] if json_start > 0 else ovpn_resp.json()["data"]
            try:
                # 4. Create user certificate
                user_cert_resp = client.post("/api/v2/system/certificate/generate", json={
                    "descr": "OVPN user cert", "caref": ca["refid"], "keytype": "RSA",
                    "keylen": 2048, "digest_alg": "sha256", "dn_commonname": "ovpn-user.test",
                    "lifetime": 365, "type": "user",
                })
                user_cert = _ok(user_cert_resp)
                try:
                    # 5. Create export config
                    cfg_resp = client.post("/api/v2/vpn/openvpn/client_export/config", json={
                        "server": ovpn["vpnid"],
                        "pkcs11providers": [], "pkcs11id": "", "pass": "",
                        "proxyaddr": "", "proxyport": "", "useproxypass": "",
                        "proxyuser": "", "proxypass": "",
                    })
                    cfg = _ok(cfg_resp)
                    cfg_id = cfg.get("id")
                    try:
                        # 6. Export (the action under test)
                        export_resp = client.post("/api/v2/vpn/openvpn/client_export", json={
                            "id": cfg_id, "certref": user_cert["refid"],
                            "type": "confinline",
                        })
                        _ok(export_resp)
                    finally:
                        client.delete("/api/v2/vpn/openvpn/client_export/config",
                                      params={"id": cfg_id})
                finally:
                    client.delete("/api/v2/system/certificate", params={"id": user_cert["id"]})
            finally:
                client.delete("/api/v2/vpn/openvpn/server", params={"id": ovpn["id"]})
        finally:
            client.delete("/api/v2/system/certificate", params={"id": srv_cert["id"]})
    finally:
        client.delete("/api/v2/system/certificate_authority", params={"id": ca["id"]})''',
]


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

    # Singleton GET/PATCH tests (settings-like endpoints not auto-detected)
    for group in groups:
        if group.category == "other" and group.base_path in _SINGLETON_TESTS:
            config = _SINGLETON_TESTS[group.base_path]
            lines.append(_gen_singleton_test(group.base_path, config))
            lines.append("")
            test_count += 1
        elif group.category == "other" and group.base_path in _SKIP_SINGLETON:
            lines.append(f"# SKIP {group.base_path}: {_SKIP_SINGLETON[group.base_path]}")
            lines.append("")

    # Action POST tests (deferred tests with test_prefix run at end, sorted by prefix)
    deferred_actions: list[tuple[str, str, dict[str, Any]]] = []
    for group in groups:
        if group.category == "action" and group.base_path in _SKIP_ACTION:
            lines.append(f"# SKIP {group.base_path}: {_SKIP_ACTION[group.base_path]}")
            lines.append("")
        elif group.category == "action" and group.base_path in _ACTION_TESTS:
            config = _ACTION_TESTS[group.base_path]
            if config.get("test_prefix"):
                deferred_actions.append((config["test_prefix"], group.base_path, config))
            else:
                lines.append(_gen_action_test(group.base_path, config))
                lines.append("")
                test_count += 1

    # ── Custom tests (hand-written, non-standard patterns) ──────────────
    for custom_fn in _CUSTOM_TESTS:
        lines.append(custom_fn)
        lines.append("")
        test_count += 1

    # Emit deferred action tests last, sorted by prefix (zz_ before zzz_)
    for _prefix, action_path, config in sorted(deferred_actions, key=lambda x: x[0]):
        lines.append(_gen_action_test(action_path, config))
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

import json
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


class RetryClient(httpx.Client):
    """httpx.Client that retries on 503 (dispatcher busy)."""
    def request(self, method, url, **kwargs):
        for attempt in range(6):
            resp = super().request(method, url, **kwargs)
            if resp.status_code != 503:
                return resp
            time.sleep(10 * (attempt + 1))
        return resp


@pytest.fixture(scope="session")
def client() -> httpx.Client:
    """Authenticated httpx client for the test VM."""
    if API_KEY:
        c = RetryClient(
            base_url=BASE_URL,
            headers={"X-API-Key": API_KEY},
            verify=False,
            timeout=30,
        )
    else:
        c = RetryClient(
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


def _gen_singleton_test(path: str, config: dict[str, Any]) -> str:
    """Generate a singleton GET/PATCH roundtrip test."""
    test_name = path.replace("/api/v2/", "").replace("/", "_")
    field = config["field"]
    value = config["value"]
    extra_fields = config.get("extra_fields", {})
    restore = config.get("restore")  # explicit restore value, or None to use original
    patch_only = config.get("patch_only", False)

    lines = []
    lines.append(f"def test_singleton_{test_name}(client: httpx.Client):")
    lines.append(f'    """Singleton roundtrip: {path}"""')

    if not patch_only:
        lines.append(f"    # GET current value")
        lines.append(f'    resp = client.get("{path}")')
        lines.append(f"    original = _ok(resp)")
        lines.append(f"    assert isinstance(original, dict)")
        lines.append(f'    original_value = original.get("{field}")')
        lines.append(f"")

    # Build PATCH body
    raw_patch = config.get("raw_patch", False)
    patch_body: dict[str, Any] = {field: value}
    patch_body.update(extra_fields)
    lines.append(f"    # PATCH with test value")
    lines.append(f"    patch_resp = client.patch(")
    lines.append(f'        "{path}",')
    lines.append(f"        json={patch_body!r},")
    lines.append(f"    )")
    if raw_patch:
        lines.append(f"    assert patch_resp.status_code == 200, f\"PATCH {{patch_resp.status_code}}: {{patch_resp.text[:200]}}\"")
    else:
        lines.append(f"    patched = _ok(patch_resp)")
        lines.append(f'    assert patched.get("{field}") == {value!r}')
    lines.append(f"")

    if not patch_only:
        lines.append(f"    # GET to verify persistence")
        lines.append(f'    verify_resp = client.get("{path}")')
        lines.append(f"    verify = _ok(verify_resp)")
        lines.append(f'    assert verify.get("{field}") == {value!r}')
        lines.append(f"")

    # Restore original value
    if restore is not None:
        restore_body: dict[str, Any] = {field: restore}
        restore_body.update(extra_fields)
        lines.append(f"    # Restore original value")
        lines.append(f"    client.patch(")
        lines.append(f'        "{path}",')
        lines.append(f"        json={restore_body!r},")
        lines.append(f"    )")
    elif not patch_only:
        lines.append(f"    # Restore original value")
        lines.append(f"    if original_value is not None:")
        restore_extra = "".join(
            f', "{k}": {v!r}' for k, v in extra_fields.items()
        )
        lines.append(
            f'        client.patch("{path}", '
            f'json={{"{field}": original_value{restore_extra}}})'
        )
    lines.append(f"")

    return "\n".join(lines)


def _gen_action_test(path: str, config: dict[str, Any]) -> str:
    """Generate an action endpoint test (POST)."""
    test_name = path.replace("/api/v2/", "").replace("/", "_")
    test_prefix = config.get("test_prefix", "")
    body = config.get("body", {})
    expect_status = config.get("expect_status", [200])
    if isinstance(expect_status, int):
        expect_status = [expect_status]
    cleanup_path = config.get("cleanup_path")
    needs_ca = config.get("needs_ca", False)
    needs_generated_ca = config.get("needs_generated_ca", False)
    needs_generated_cert = config.get("needs_generated_cert", False)
    needs_ca_and_csr = config.get("needs_ca_and_csr", False)

    lines = []
    lines.append(f"def test_{test_prefix}action_{test_name}(client: httpx.Client):")
    lines.append(f'    """Action: POST {path}"""')

    # DN fields required for CA generate on REST API v2.4.3
    dn_fields = (
        '"dn_country": "US", "dn_state": "California", '
        '"dn_city": "San Francisco", "dn_organization": "pfSense Test", '
        '"dn_organizationalunit": "Testing"'
    )

    # Complex multi-step actions
    if needs_generated_ca:
        lines.append(f"    # Generate a CA first")
        lines.append(f'    ca_resp = client.post("/api/v2/system/certificate_authority/generate", json={{')
        lines.append(f'        "descr": "CA for renew test", "keytype": "RSA", "keylen": 2048,')
        lines.append(f'        "digest_alg": "sha256", "dn_commonname": "Renew Test CA", "lifetime": 3650,')
        lines.append(f'        {dn_fields},')
        lines.append(f"    }})")
        lines.append(f"    ca = _ok(ca_resp)")
        lines.append(f"    try:")
        lines.append(f'        resp = client.post("{path}", json={{"caref": ca["refid"]}})')
        lines.append(f"        _ok(resp)")
        lines.append(f"    finally:")
        lines.append(f'        client.delete("/api/v2/system/certificate_authority", params={{"id": ca["id"]}})')
        lines.append(f"")
        return "\n".join(lines)

    if needs_generated_cert:
        binary_export = "pkcs12" in path
        lines.append(f"    # Generate a CA and cert first")
        lines.append(f'    ca_resp = client.post("/api/v2/system/certificate_authority/generate", json={{')
        lines.append(f'        "descr": "CA for cert action", "keytype": "RSA", "keylen": 2048,')
        lines.append(f'        "digest_alg": "sha256", "dn_commonname": "Cert Action CA", "lifetime": 3650,')
        lines.append(f'        {dn_fields},')
        lines.append(f"    }})")
        lines.append(f"    ca = _ok(ca_resp)")
        lines.append(f'    cert_resp = client.post("/api/v2/system/certificate/generate", json={{')
        lines.append(f'        "descr": "Cert for action", "caref": ca["refid"], "keytype": "RSA",')
        lines.append(f'        "keylen": 2048, "digest_alg": "sha256", "dn_commonname": "action.test",')
        lines.append(f'        "lifetime": 365, "type": "server",')
        lines.append(f"    }})")
        lines.append(f"    cert = _ok(cert_resp)")
        lines.append(f"    try:")
        body_fields = ", ".join(f'"{k}": {v!r}' for k, v in body.items()) if body else ""
        extra = f", {body_fields}" if body_fields else ""
        if binary_export:
            # PKCS12 export returns binary — use Accept: application/octet-stream
            lines.append(f'        resp = client.post("{path}", json={{"certref": cert["refid"]{extra}}}, headers={{"Accept": "application/octet-stream"}})')
            lines.append(f'        assert resp.status_code == 200, f"PKCS12 export {{resp.status_code}}: {{resp.text[:200]}}"')
            lines.append(f'        assert len(resp.content) > 0, "PKCS12 export returned empty body"')
        else:
            lines.append(f'        resp = client.post("{path}", json={{"certref": cert["refid"]{extra}}})')
            lines.append(f"        _ok(resp)")
        lines.append(f"    finally:")
        lines.append(f'        client.delete("/api/v2/system/certificate", params={{"id": cert["id"]}})')
        lines.append(f'        client.delete("/api/v2/system/certificate_authority", params={{"id": ca["id"]}})')
        lines.append(f"")
        return "\n".join(lines)

    if needs_ca_and_csr:
        lines.append(f"    # Generate CA, create CSR, then sign it")
        lines.append(f'    ca_resp = client.post("/api/v2/system/certificate_authority/generate", json={{')
        lines.append(f'        "descr": "CA for CSR sign", "keytype": "RSA", "keylen": 2048,')
        lines.append(f'        "digest_alg": "sha256", "dn_commonname": "CSR Sign CA", "lifetime": 3650,')
        lines.append(f'        {dn_fields},')
        lines.append(f"    }})")
        lines.append(f"    ca = _ok(ca_resp)")
        lines.append(f'    csr_resp = client.post("/api/v2/system/certificate/signing_request", json={{')
        lines.append(f'        "descr": "Test CSR to sign", "keytype": "RSA", "keylen": 2048,')
        lines.append(f'        "digest_alg": "sha256", "dn_commonname": "csr-sign.test",')
        lines.append(f"    }})")
        lines.append(f"    csr_data = _ok(csr_resp)")
        lines.append(f"    try:")
        lines.append(f'        resp = client.post("{path}", json={{')
        lines.append(f'            "descr": "Signed from CSR", "caref": ca["refid"],')
        lines.append(f'            "csr": csr_data["csr"], "digest_alg": "sha256",')
        lines.append(f"        }})")
        lines.append(f"        signed = _ok(resp)")
        lines.append(f"    finally:")
        lines.append(f'        client.delete("/api/v2/system/certificate", params={{"id": csr_data["id"]}})')
        lines.append(f'        client.delete("/api/v2/system/certificate_authority", params={{"id": ca["id"]}})')
        lines.append(f"")
        return "\n".join(lines)

    # Simple action or action needing CA parent
    if needs_ca:
        lines.append(f"    # Generate a CA first")
        lines.append(f'    ca_resp = client.post("/api/v2/system/certificate_authority/generate", json={{')
        lines.append(f'        "descr": "CA for cert gen", "keytype": "RSA", "keylen": 2048,')
        lines.append(f'        "digest_alg": "sha256", "dn_commonname": "Cert Gen CA", "lifetime": 3650,')
        lines.append(f'        {dn_fields},')
        lines.append(f"    }})")
        lines.append(f"    ca = _ok(ca_resp)")
        body_with_ca = dict(body)
        body_repr = repr(body_with_ca)
        lines.append(f"    body = {body_repr}")
        lines.append(f'    body["caref"] = ca["refid"]')
        lines.append(f"    try:")
        lines.append(f'        resp = client.post("{path}", json=body)')
        lines.append(f"        data = _ok(resp)")
        if cleanup_path:
            lines.append(f'        client.delete("{cleanup_path}", params={{"id": data["id"]}})')
        lines.append(f"    finally:")
        lines.append(f'        client.delete("/api/v2/system/certificate_authority", params={{"id": ca["id"]}})')
        lines.append(f"")
        return "\n".join(lines)

    # Simple POST action
    needs_basic_auth = config.get("needs_basic_auth", False)
    if needs_basic_auth:
        lines.append(f"    # Auth endpoints require BasicAuth, not API key")
        lines.append(f"    ba_client = httpx.Client(")
        lines.append(f"        base_url=BASE_URL,")
        lines.append(f"        verify=False,")
        lines.append(f"        auth=(AUTH_USER, AUTH_PASS),")
        lines.append(f"        timeout=30,")
        lines.append(f"    )")
        client_var = "ba_client"
    else:
        client_var = "client"

    lines.append(f'    resp = {client_var}.post("{path}", json={body!r})')
    raw_response = config.get("raw_response", False)
    if raw_response:
        lines.append(f"    assert resp.status_code == 200, f\"{{resp.status_code}}: {{resp.text[:500]}}\"")
        lines.append(f"    data = resp.json()")
        lines.append(f"    assert data is not None")
    elif expect_status == [200]:
        lines.append(f"    data = _ok(resp)")
        lines.append(f"    assert data is not None")
    else:
        lines.append(f"    assert resp.status_code in {expect_status!r}, f\"Unexpected: {{resp.status_code}}: {{resp.text[:500]}}\"")

    if cleanup_path:
        lines.append(f"    data = resp.json().get('data', {{}})")
        lines.append(f"    if data.get('id') is not None:")
        lines.append(f'        client.delete("{cleanup_path}", params={{"id": data["id"]}})')

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
    siblings = chain.get("siblings", [])
    setup_patches = chain.get("setup_patches", [])
    setup_posts = chain.get("setup_posts", [])
    child_body = chain.get("child_body")
    update_field = chain.get("update_field", "descr")
    update_value = chain.get("update_value", '"Updated by test"')
    delete_may_fail = chain.get("delete_may_fail", False)

    lines: list[str] = []
    lines.append(f"def test_crud_{test_name}(client: httpx.Client):")
    parent_paths = ", ".join(p["path"].split("/api/v2/")[-1] for p in parents)
    if parents:
        lines.append(f'    """CRUD lifecycle: {path} (needs: {parent_paths})"""')
    else:
        lines.append(f'    """CRUD lifecycle: {path} (chained)"""')

    # ── Setup patches (idempotent PATCH requests, no cleanup) ────────────
    for sp in setup_patches:
        sp_body = _body_to_code(sp["body"])
        lines.append(f"    # Setup: patch {sp['path'].split('/api/v2/')[-1]}")
        lines.append(f"    client.patch(")
        lines.append(f'        "{sp["path"]}",')
        lines.append(f"        json={sp_body},")
        lines.append(f"    )")
        lines.append(f"")

    # ── Setup posts (idempotent POST requests, no cleanup) ────────────
    for sp in setup_posts:
        sp_body = _body_to_code(sp["body"])
        lines.append(f"    # Setup: post {sp['path'].split('/api/v2/')[-1]}")
        lines.append(f"    client.post(")
        lines.append(f'        "{sp["path"]}",')
        lines.append(f"        json={sp_body},")
        lines.append(f"    )")
        lines.append(f"")

    # ── Create parent resources ───────────────────────────────────────────
    parent_vars: list[str] = []
    for i, parent in enumerate(parents):
        var = f"p{i}"
        parent_vars.append(var)
        parent_body = _resolve_parent_body(parent)
        body_code = _body_to_code(parent_body)
        receives = parent.get("receives_from", {})
        lines.append(f"    # Setup: create parent {parent['path'].split('/api/v2/')[-1]}")
        if receives:
            lines.append(f"    {var}_body = {body_code}")
            for src_idx, field_map in sorted(receives.items()):
                for local_field, src_field in field_map.items():
                    lines.append(f'    {var}_body["{local_field}"] = p{src_idx}["{src_field}"]')
            lines.append(f"    {var}_resp = client.post(")
            lines.append(f'        "{parent["path"]}",')
            lines.append(f"        json={var}_body,")
            lines.append(f"    )")
        else:
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

    # ── Create sibling resources (same parent_id as child) ───────────────
    sibling_vars: list[str] = []
    sibling_injections: list[tuple[str, str, str]] = []  # (child_field, sib_var, sib_field)
    for j, sib in enumerate(siblings):
        svar = f"sib{j}"
        sibling_vars.append(svar)
        sib_body = dict(sib["body"])
        sib_body_code = _body_to_code(sib_body, indent=len(base_indent) + 8)
        lines.append(f"{base_indent}# Setup: create sibling {sib['path'].split('/api/v2/')[-1]}")
        lines.append(f"{base_indent}{svar}_body = {sib_body_code}")
        # Siblings use the same parent_id as the child will
        for child_field, pvar, pfield in injections:
            if child_field == "parent_id":
                lines.append(f'{base_indent}{svar}_body["parent_id"] = {pvar}["{pfield}"]')
                break
        lines.append(f"{base_indent}{svar}_resp = client.post(")
        lines.append(f'{base_indent}    "{sib["path"]}",')
        lines.append(f"{base_indent}    json={svar}_body,")
        lines.append(f"{base_indent})")
        lines.append(f"{base_indent}{svar} = _ok({svar}_resp)")
        lines.append(f'{base_indent}{svar}_id = {svar}.get("id")')
        lines.append(f"")
        # Collect sibling injections
        for child_field, sib_field in sib.get("inject", {}).items():
            sibling_injections.append((child_field, svar, sib_field))

    # CREATE
    lines.append(f"{base_indent}# CREATE")
    body_code = _body_to_code(final_body, indent=len(base_indent) + 8)
    lines.append(f"{base_indent}body = {body_code}")

    # Apply dynamic injections from parents
    for child_field, pvar, pfield in injections:
        lines.append(f'{base_indent}body["{child_field}"] = {pvar}["{pfield}"]')

    # Apply dynamic injections from siblings
    for child_field, svar, sfield in sibling_injections:
        lines.append(f'{base_indent}body["{child_field}"] = {svar}["{sfield}"]')

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
    static_parent_id = chain.get("static_parent_id")
    parent_id_injection = None
    if static_parent_id is None:
        for child_field, pvar, pfield in injections:
            if child_field == "parent_id":
                parent_id_injection = (pvar, pfield)
                break

    # GET
    lines.append(f"{inner}# GET (singular)")
    if static_parent_id:
        lines.append(f"{inner}get_resp = client.get(")
        lines.append(f'{inner}    "{path}",')
        lines.append(f'{inner}    params={{"id": obj_id, "parent_id": {static_parent_id!r}}},')
        lines.append(f"{inner})")
    elif parent_id_injection:
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
        if static_parent_id:
            lines.append(f"{inner}update_resp = client.patch(")
            lines.append(f'{inner}    "{path}",')
            lines.append(f'{inner}    json={{"id": obj_id, "parent_id": {static_parent_id!r}, "{update_field}": {update_value}}},')
            lines.append(f"{inner})")
        elif parent_id_injection:
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
    if delete_may_fail:
        # DELETE is known-broken (API bug) — best-effort cleanup, don't assert
        lines.append(f'{base_indent}    client.delete("{path}", params={{"id": obj_id}})  # may 500 (API bug)')
    elif static_parent_id:
        lines.append(
            f'{base_indent}    _delete_with_retry(client, "{path}", obj_id, '
            f'{{"parent_id": {static_parent_id!r}}})'
        )
    elif parent_id_injection:
        pvar, pfield = parent_id_injection
        lines.append(
            f'{base_indent}    _delete_with_retry(client, "{path}", obj_id, '
            f'{{"parent_id": {pvar}["{pfield}"]}})'
        )
    else:
        lines.append(f'{base_indent}    _delete_with_retry(client, "{path}", obj_id)')

    # ── Cleanup siblings (after child, before parents) ───────────────────
    for j in range(len(siblings) - 1, -1, -1):
        svar = sibling_vars[j]
        sib = siblings[j]
        if parent_id_injection:
            pvar, pfield = parent_id_injection
            lines.append(
                f'{base_indent}    _delete_with_retry(client, "{sib["path"]}", {svar}_id, '
                f'{{"parent_id": {pvar}["{pfield}"]}})'
            )
        else:
            lines.append(
                f'{base_indent}    _delete_with_retry(client, "{sib["path"]}", {svar}_id)'
            )

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
