"""
Tests for the naming module — camelCase to snake_case conversion.

Run: nix develop -c python -m pytest test_naming.py -v
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from generator.naming import _camel_to_snake, operation_id_to_tool_name
from generator.loader import load_spec


# ── Unit tests: _camel_to_snake ──────────────────────────────────────────


class TestCamelToSnake:
    """Parametrized tests for all known problematic and working patterns."""

    # Previously broken compound words
    @pytest.mark.parametrize(
        "input_,expected",
        [
            ("HAProxy", "haproxy"),
            ("HAProxyBackend", "haproxy_backend"),
            ("HAProxyFrontendACL", "haproxy_frontend_acl"),
            ("HAProxySettingsDNSResolver", "haproxy_settings_dns_resolver"),
            ("WireGuard", "wireguard"),
            ("WireGuardPeer", "wireguard_peer"),
            ("WireGuardSettings", "wireguard_settings"),
            ("OpenVPN", "openvpn"),
            ("OpenVPNServer", "openvpn_server"),
            ("OpenVPNClientCSO", "openvpn_client_cso"),
            ("IPsec", "ipsec"),
            ("IPsecPhase1", "ipsec_phase1"),
            ("IPsecChildSAs", "ipsec_child_sas"),
            ("GraphQL", "graphql"),
        ],
        ids=lambda x: x if isinstance(x, str) and x[0].isupper() else "",
    )
    def test_compound_words(self, input_: str, expected: str):
        assert _camel_to_snake(input_) == expected

    # Previously broken plural acronyms
    @pytest.mark.parametrize(
        "input_,expected",
        [
            ("VLANs", "vlans"),
            ("CRLs", "crls"),
            ("GREs", "gres"),
            ("LAGGs", "laggs"),
            ("VirtualIPs", "virtual_ips"),
            ("ACLs", "acls"),
            ("CSOs", "csos"),
        ],
        ids=lambda x: x if isinstance(x, str) and x[0].isupper() else "",
    )
    def test_plural_acronyms(self, input_: str, expected: str):
        assert _camel_to_snake(input_) == expected

    # Already-working patterns (must not regress)
    @pytest.mark.parametrize(
        "input_,expected",
        [
            ("ARP", "arp"),
            ("ARPTable", "arp_table"),
            ("CARP", "carp"),
            ("CARPStatus", "carp_status"),
            ("DHCP", "dhcp"),
            ("DHCPServer", "dhcp_server"),
            ("DNS", "dns"),
            ("DNSResolver", "dns_resolver"),
            ("SSH", "ssh"),
            ("NTP", "ntp"),
            ("NTPSettings", "ntp_settings"),
            ("JWT", "jwt"),
            ("RADIUS", "radius"),
            ("PKCS12", "pkcs12"),
            ("Firewall", "firewall"),
            ("FirewallAlias", "firewall_alias"),
            ("FirewallNATOneToOneMapping", "firewall_nat_one_to_one_mapping"),
            ("SystemVersion", "system_version"),
        ],
        ids=lambda x: x if isinstance(x, str) and x[0].isupper() else "",
    )
    def test_already_working(self, input_: str, expected: str):
        assert _camel_to_snake(input_) == expected

    # Full resource paths from operationIds (verb stripped)
    @pytest.mark.parametrize(
        "input_,expected",
        [
            ("ServicesHAProxyApply", "services_haproxy_apply"),
            ("VPNIPsecApply", "vpn_ipsec_apply"),
            ("VPNWireGuardApply", "vpn_wireguard_apply"),
            ("StatusOpenVPNServerConnection", "status_openvpn_server_connection"),
            ("InterfaceVLANs", "interface_vlans"),
            ("InterfaceGREs", "interface_gres"),
            ("InterfaceLAGGs", "interface_laggs"),
            ("SystemCRLs", "system_crls"),
            ("FirewallVirtualIPs", "firewall_virtual_ips"),
            ("VPNIPsecChildSAs", "vpn_ipsec_child_sas"),
            ("VPNOpenVPNClientCSOs", "vpn_openvpn_client_csos"),
        ],
        ids=lambda x: x if isinstance(x, str) and x[0].isupper() else "",
    )
    def test_full_resource_paths(self, input_: str, expected: str):
        assert _camel_to_snake(input_) == expected


# ── Integration tests: operation_id_to_tool_name ─────────────────────────


class TestOperationIdToToolName:
    """Test full name generation including verb mapping."""

    @pytest.mark.parametrize(
        "op_id,method,path,params,expected",
        [
            (
                "postServicesHAProxyApplyEndpoint",
                "post",
                "/api/v2/services/haproxy/apply",
                [],
                "pfsense_services_haproxy_apply",
            ),
            (
                "getServicesHAProxyApplyEndpoint",
                "get",
                "/api/v2/services/haproxy/apply",
                [],
                "pfsense_get_services_haproxy_apply_status",
            ),
            (
                "getInterfaceVLANsEndpoint",
                "get",
                "/api/v2/interface/vlans",
                ["limit", "offset"],
                "pfsense_list_interface_vlans",
            ),
            (
                "getInterfaceVLANEndpoint",
                "get",
                "/api/v2/interface/vlan",
                ["id"],
                "pfsense_get_interface_vlan",
            ),
            (
                "deleteStatusOpenVPNServerConnectionEndpoint",
                "delete",
                "/api/v2/status/openvpn/server/connection",
                ["id"],
                "pfsense_delete_status_openvpn_server_connection",
            ),
            (
                "postVPNIPsecApplyEndpoint",
                "post",
                "/api/v2/vpn/ipsec/apply",
                [],
                "pfsense_vpn_ipsec_apply",
            ),
            (
                "putFirewallVirtualIPsEndpoint",
                "put",
                "/api/v2/firewall/virtual_ips",
                [],
                "pfsense_replace_firewall_virtual_ips",
            ),
        ],
    )
    def test_tool_names(self, op_id, method, path, params, expected):
        assert operation_id_to_tool_name(op_id, method, path, params) == expected


# ── Golden file regression test ──────────────────────────────────────────


GOLDEN_FILE = Path(__file__).parent / "tests" / "expected_tool_names.json"
SPEC_FILE = Path(__file__).parent / "openapi-spec.json"


class TestGoldenFile:
    """Compare all 677 generated names against the golden file."""

    def test_all_names_match(self):
        assert GOLDEN_FILE.exists(), f"Golden file not found: {GOLDEN_FILE}"
        with open(GOLDEN_FILE) as f:
            expected = json.load(f)

        spec = load_spec(str(SPEC_FILE))
        actual = {}
        for path, path_item in sorted(spec["paths"].items()):
            for method in ["get", "post", "put", "patch", "delete"]:
                if method not in path_item:
                    continue
                op = path_item[method]
                op_id = op.get("operationId", "")
                params = op.get("parameters", [])
                param_names = [p["name"] for p in params if "name" in p]
                tool_name = operation_id_to_tool_name(op_id, method, path, param_names)
                actual[op_id] = tool_name

        assert len(actual) == len(expected), (
            f"Count mismatch: got {len(actual)}, expected {len(expected)}"
        )

        mismatches = []
        for op_id in sorted(expected):
            if op_id not in actual:
                mismatches.append(f"  MISSING: {op_id}")
            elif actual[op_id] != expected[op_id]:
                mismatches.append(
                    f"  {op_id}: got {actual[op_id]!r}, expected {expected[op_id]!r}"
                )

        assert not mismatches, (
            f"{len(mismatches)} name mismatches:\n" + "\n".join(mismatches)
        )


# ── Safety net: no single-letter segments ────────────────────────────────


class TestNoSingleLetterSegments:
    """Ensure no tool name has isolated single-letter segments."""

    def test_no_single_letter_between_underscores(self):
        """No tool name should contain _x_ (single letter between underscores)."""
        spec = load_spec(str(SPEC_FILE))
        bad_names = []
        for path, path_item in sorted(spec["paths"].items()):
            for method in ["get", "post", "put", "patch", "delete"]:
                if method not in path_item:
                    continue
                op = path_item[method]
                op_id = op.get("operationId", "")
                params = op.get("parameters", [])
                param_names = [p["name"] for p in params if "name" in p]
                name = operation_id_to_tool_name(op_id, method, path, param_names)
                # Check for _x_ pattern (single letter between underscores)
                if re.search(r"_[a-z0-9]_", name):
                    bad_names.append(f"  {name} (from {op_id})")

        assert not bad_names, (
            f"{len(bad_names)} names have single-letter segments:\n"
            + "\n".join(bad_names)
        )

    def test_no_double_underscores(self):
        """No tool name should contain double underscores."""
        spec = load_spec(str(SPEC_FILE))
        bad_names = []
        for path, path_item in sorted(spec["paths"].items()):
            for method in ["get", "post", "put", "patch", "delete"]:
                if method not in path_item:
                    continue
                op = path_item[method]
                op_id = op.get("operationId", "")
                params = op.get("parameters", [])
                param_names = [p["name"] for p in params if "name" in p]
                name = operation_id_to_tool_name(op_id, method, path, param_names)
                if "__" in name:
                    bad_names.append(f"  {name} (from {op_id})")

        assert not bad_names, (
            f"{len(bad_names)} names have double underscores:\n"
            + "\n".join(bad_names)
        )


def generate_golden_file():
    """Utility: regenerate the golden file from current code."""
    spec = load_spec(str(SPEC_FILE))
    mapping = {}
    for path, path_item in sorted(spec["paths"].items()):
        for method in ["get", "post", "put", "patch", "delete"]:
            if method not in path_item:
                continue
            op = path_item[method]
            op_id = op.get("operationId", "")
            params = op.get("parameters", [])
            param_names = [p["name"] for p in params if "name" in p]
            tool_name = operation_id_to_tool_name(op_id, method, path, param_names)
            mapping[op_id] = tool_name
    with open(GOLDEN_FILE, "w") as f:
        json.dump(mapping, f, indent=2)
        f.write("\n")
    print(f"Wrote {len(mapping)} entries to {GOLDEN_FILE}")
