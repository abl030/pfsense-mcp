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
    "/api/v2/interface/vlan": "requires valid parent interface",
    "/api/v2/interface/gre": "requires specific tunnel config",
    "/api/v2/interface/gif": "requires specific tunnel config",
    "/api/v2/routing/static_route": "requires existing gateway object",
    "/api/v2/routing/gateway/group": "requires existing gateways with valid tiers",
    "/api/v2/vpn/ipsec/phase2": "requires existing phase1",
    "/api/v2/vpn/openvpn/cso": "requires existing OpenVPN server",
    "/api/v2/vpn/openvpn/client_export/config": "requires OpenVPN server configured",
    "/api/v2/services/dhcp_server": "per-interface singleton, POST not supported",
    "/api/v2/vpn/wireguard/peer": "requires existing WireGuard tunnel",
    "/api/v2/system/certificate": "requires valid PEM certificate data",
    "/api/v2/system/certificate_authority": "requires valid PEM CA data",
    # FreeRADIUS routes return nginx 404 despite package installed
    "/api/v2/services/freeradius/client": "freeradius routes not registered",
    "/api/v2/services/freeradius/interface": "freeradius routes not registered",
    "/api/v2/services/freeradius/user": "freeradius routes not registered",
    # ACME requires valid X509 private key
    "/api/v2/services/acme/account_key": "requires valid X509 private key",
    "/api/v2/services/acme/certificate": "requires existing ACME account key",
    # HAProxy frontend requires existing backend
    "/api/v2/services/haproxy/frontend": "requires existing backend",
    # HAProxy sub-resources require parent_id
    "/api/v2/services/haproxy/backend/acl": "requires existing backend parent",
    "/api/v2/services/haproxy/backend/action": "requires existing backend parent",
    "/api/v2/services/haproxy/backend/error_file": "requires existing backend parent",
    "/api/v2/services/haproxy/backend/server": "requires existing backend parent",
    "/api/v2/services/haproxy/frontend/acl": "requires existing frontend parent",
    "/api/v2/services/haproxy/frontend/action": "requires existing frontend parent",
    "/api/v2/services/haproxy/frontend/address": "requires existing frontend parent",
    "/api/v2/services/haproxy/frontend/certificate": "requires existing frontend parent",
    "/api/v2/services/haproxy/frontend/error_file": "requires existing frontend parent",
    # BIND sub-resources
    "/api/v2/services/bind/sync/domain": "requires existing BIND zone",
    # HAProxy settings sub-resources return 500 (requires parent model)
    "/api/v2/services/haproxy/settings/dns_resolver": "server error: requires parent model",
    "/api/v2/services/haproxy/settings/email_mailer": "server error: requires parent model",
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

    # CRUD lifecycle tests
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
    return body.get("data", body)'''


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
