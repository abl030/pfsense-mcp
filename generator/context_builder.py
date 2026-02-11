"""
Build template context for each tool from parsed operations.

Combines loader, naming, and schema_parser to produce the
complete data structure needed by the Jinja2 template.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .loader import Operation, load_spec, parse_operations
from .naming import operation_id_to_tool_name
from .schema_parser import ToolParameter, extract_tool_parameters, extract_response_fields

# Canonical module ordering — used for code generation and env var docs.
MODULE_ORDER = [
    "firewall", "interface", "routing",
    "vpn_wireguard", "vpn_openvpn", "vpn_ipsec",
    "services_dhcp", "services_dns_resolver", "services_dns_forwarder",
    "services_haproxy", "services_bind", "services_freeradius", "services_acme",
    "services_misc",
    "system", "status", "diagnostics", "user", "auth",
]

_ALL_MODULES = set(MODULE_ORDER)

# Longest-prefix-first path → module mapping.
# Order matters: more specific prefixes must come before shorter ones.
_PATH_TO_MODULE = [
    ("/api/v2/vpn/wireguard", "vpn_wireguard"),
    ("/api/v2/vpn/openvpn", "vpn_openvpn"),
    ("/api/v2/vpn/ipsec", "vpn_ipsec"),
    ("/api/v2/services/dhcp_server", "services_dhcp"),
    ("/api/v2/services/dhcp_relay", "services_dhcp"),
    ("/api/v2/services/dns_resolver", "services_dns_resolver"),
    ("/api/v2/services/dns_forwarder", "services_dns_forwarder"),
    ("/api/v2/services/haproxy", "services_haproxy"),
    ("/api/v2/services/bind", "services_bind"),
    ("/api/v2/services/freeradius", "services_freeradius"),
    ("/api/v2/services/acme", "services_acme"),
    ("/api/v2/services/", "services_misc"),
    ("/api/v2/firewall", "firewall"),
    ("/api/v2/interface", "interface"),
    ("/api/v2/routing", "routing"),
    ("/api/v2/system", "system"),
    ("/api/v2/status", "status"),
    ("/api/v2/diagnostics", "diagnostics"),
    ("/api/v2/user", "user"),
    ("/api/v2/auth", "auth"),
    ("/api/v2/graphql", "diagnostics"),
]

# Per-endpoint parameter description enhancements.
# key = (operationId, param_name), value = text to append to description.
_PARAM_DESCRIPTION_HINTS: dict[tuple[str, str], str] = {
    ("getDiagnosticsTableEndpoint", "id"): (
        " Common pfSense PF table names: virusprot, bogons, snort2c, "
        "LAN_NETWORK, WAN_NETWORK."
    ),
    ("getSystemPackageEndpoint", "id"): (
        " NOTE: The id is an integer array index (0, 1, 2, ...), not a package name string."
    ),
    ("postServicesHAProxyFrontendActionEndpoint", "acl"): (
        " For unconditional actions, use the name of any existing ACL"
        " (the action will apply regardless). Cannot be empty."
    ),
    ("postVPNIPsecPhase2Endpoint", "hash_algorithm_option"): (
        " Valid values: ['hmac_sha1', 'hmac_sha256', 'hmac_sha384', 'hmac_sha512', 'aesxcbc']."
        " Note: use hmac_ prefix (not plain sha256)."
    ),
    ("patchVPNIPsecPhase2Endpoint", "hash_algorithm_option"): (
        " Valid values: ['hmac_sha1', 'hmac_sha256', 'hmac_sha384', 'hmac_sha512', 'aesxcbc']."
        " Note: use hmac_ prefix (not plain sha256)."
    ),
    # WireGuard private key must be valid Curve25519
    ("postVPNWireGuardTunnelEndpoint", "privatekey"): (
        " Must be a valid WireGuard Curve25519 private key (base64-encoded, 32 bytes"
        " with proper bit clamping). Generate with `wg genkey`."
    ),
    ("patchVPNWireGuardTunnelEndpoint", "privatekey"): (
        " Must be a valid WireGuard Curve25519 private key (base64-encoded, 32 bytes"
        " with proper bit clamping). Generate with `wg genkey`."
    ),
    # ARP table interface uses display names (WAN, LAN), not device names (em0, em1)
    ("deleteDiagnosticsARPTableEndpoint", "query"): (
        " Note: the `interface` filter uses display names like 'WAN', 'LAN'"
        " — not device names like 'em0', 'em1'."
    ),
    ("deleteDiagnosticsARPTableEntryEndpoint", "query"): (
        " Note: the `interface` filter uses display names like 'WAN', 'LAN'"
        " — not device names like 'em0', 'em1'."
    ),
    # CRL fields are non-editable after creation (pfSense marks them immutable)
    ("patchSystemCRLEndpoint", "descr"): (
        " WARNING: This field is read-only after creation — PATCH will return"
        " FIELD_VALUE_CHANGED_WHEN_NOT_EDITABLE if a different value is sent."
    ),
    ("patchSystemCRLEndpoint", "lifetime"): (
        " WARNING: This field is read-only after creation — PATCH will return"
        " FIELD_VALUE_CHANGED_WHEN_NOT_EDITABLE if a different value is sent."
    ),
    ("patchSystemCRLEndpoint", "serial"): (
        " WARNING: This field is read-only after creation — PATCH will return"
        " FIELD_VALUE_CHANGED_WHEN_NOT_EDITABLE if a different value is sent."
    ),
}

# Per-tool docstring notes — appended after the danger warning block.
# key = operationId, value = note text for the generated docstring.
_TOOL_DOCSTRING_NOTES: dict[str, str] = {
    "getStatusServicesEndpoint": (
        "NOTE: Package-installed services (WireGuard, HAProxy, BIND, FreeRADIUS) "
        "always report enabled=false and status=false due to a REST API bug. "
        "Use pfsense_get_overview for accurate service status."
    ),
    "getFirewallRulesEndpoint": (
        "NOTE: Rules reference firewall aliases by name (e.g. source='MY_ALIAS'). "
        "To resolve alias names to their actual IPs/networks, call "
        "pfsense_list_firewall_aliases and match by name."
    ),
    "getServicesDHCPServerStaticMappingsEndpoint": (
        "NOTE: Results include static mappings from ALL interfaces. Use the parent_id "
        "parameter to filter by interface (e.g. parent_id='lan' or parent_id='opt3')."
    ),
}

# Subsystem prefixes that require an explicit "apply" call after mutations.
_APPLY_SUBSYSTEMS = [
    "/api/v2/firewall/virtual_ip",
    "/api/v2/firewall",
    "/api/v2/interface",
    "/api/v2/routing",
    "/api/v2/services/dhcp_server",
    "/api/v2/services/dns_forwarder",
    "/api/v2/services/dns_resolver",
    "/api/v2/services/haproxy",
    "/api/v2/vpn/ipsec",
    "/api/v2/vpn/wireguard",
]

# Dangerous endpoints: exclude or add extra warnings.
_DANGEROUS_ENDPOINTS = {
    "postDiagnosticsHaltSystemEndpoint": "DANGEROUS: Halts the pfSense system.",
    "postDiagnosticsRebootEndpoint": "DANGEROUS: Reboots the pfSense system.",
    "postDiagnosticsCommandPromptEndpoint": "DANGEROUS: Executes arbitrary shell commands.",
    "deleteDiagnosticsARPTableEndpoint": "DANGEROUS: Clears the entire ARP table.",
    "deleteDiagnosticsConfigHistoryRevisionsEndpoint": "DANGEROUS: Deletes all config history.",
    "deleteFirewallStatesEndpoint": "DANGEROUS: Clears all firewall states.",
    "postGraphQLEndpoint": "DANGEROUS: Executes raw GraphQL queries.",
}


@dataclass
class ToolContext:
    """Complete context for generating one tool function."""

    tool_name: str
    operation_id: str
    method: str  # "get", "post", "patch", "put", "delete"
    path: str  # e.g. "/api/v2/firewall/alias"
    module: str  # e.g. "firewall", "vpn_wireguard", "services_dhcp"
    description: str
    parameters: list[ToolParameter]
    is_mutation: bool  # POST/PATCH/PUT/DELETE
    needs_confirmation: bool  # mutations need confirm gate
    needs_apply: bool  # mutation in a subsystem that requires apply
    apply_endpoint: str | None  # e.g. "/api/v2/firewall/apply"
    apply_tool_name: str | None  # e.g. "pfsense_firewall_apply"
    is_dangerous: bool
    danger_warning: str | None
    requires_basic_auth: bool  # True if endpoint only accepts BasicAuth
    has_request_body: bool
    body_params: list[ToolParameter]  # params that go in JSON body
    query_params: list[ToolParameter]  # params that go in URL query
    docstring_note: str | None = None  # Extra note appended to docstring
    is_list_tool: bool = False  # True for pfsense_list_* tools
    response_fields: list[str] | None = None  # Known response fields for list tools


def _path_to_module(path: str) -> str:
    """Map an API path to its module name via longest-prefix match."""
    for prefix, module in _PATH_TO_MODULE:
        if path.startswith(prefix):
            return module
    raise ValueError(f"No module mapping for path: {path}")


def _find_apply_info(
    path: str, method: str
) -> tuple[bool, str | None, str | None]:
    """Determine if this operation needs an apply reminder."""
    if method == "get":
        return False, None, None

    # Check if this path belongs to an apply subsystem
    # Use longest-match to handle /firewall/virtual_ip vs /firewall
    matched_prefix = None
    for prefix in sorted(_APPLY_SUBSYSTEMS, key=len, reverse=True):
        if path.startswith(prefix + "/") or path == prefix:
            matched_prefix = prefix
            break

    if not matched_prefix:
        return False, None, None

    # Don't add apply reminder to the apply endpoint itself
    if path.endswith("/apply"):
        return False, None, None

    apply_path = matched_prefix + "/apply"
    # Build the apply tool name from the subsystem
    subsystem = matched_prefix.replace("/api/v2/", "").replace("/", "_")
    apply_tool = f"pfsense_{subsystem}_apply"

    return True, apply_path, apply_tool


def _build_docstring(
    op: Operation,
    _tool_name: str,
    _params: list[ToolParameter],
    needs_apply: bool,
    apply_tool_name: str | None,
    is_dangerous: bool,
    danger_warning: str | None,
) -> str:
    """Build a tool docstring from operation metadata."""
    parts = []

    # Summary line
    summary = op.summary or op.description or f"{op.method.upper()} {op.path}"
    # Clean HTML
    import re

    summary = re.sub(r"<[^>]+>", "", summary).strip()
    if summary:
        parts.append(summary)

    # BasicAuth warning — these endpoints cannot work with API key auth
    if op.requires_basic_auth:
        parts.append(
            "\nWARNING: This endpoint requires HTTP BasicAuth (username:password). "
            "It does NOT accept API key or JWT authentication. "
            "If the MCP server is configured with API key auth, this tool will return 401."
        )

    # Danger warning
    if is_dangerous and danger_warning:
        parts.append(f"\nWARNING: {danger_warning}")

    # Apply reminder
    if needs_apply and apply_tool_name:
        parts.append(
            f"\nNote: After this operation, call `{apply_tool_name}` to apply pending changes."
        )

    # Method and path for reference
    parts.append(f"\nAPI: {op.method.upper()} {op.path}")

    return "\n".join(parts)


def build_tool_contexts(spec: dict[str, Any]) -> list[ToolContext]:
    """Build template contexts for all operations in the spec."""
    operations = parse_operations(spec)
    contexts: list[ToolContext] = []

    for op in operations:
        # Get parameter names for naming
        param_names = [p.name for p in op.parameters]

        # Tool name
        tool_name = operation_id_to_tool_name(
            op.operation_id, op.method, op.path, param_names
        )

        # Extract parameters
        params = extract_tool_parameters(spec, op)

        # Apply per-endpoint parameter description hints
        for p in params:
            hint_key = (op.operation_id, p.api_name or p.name)
            if hint_key in _PARAM_DESCRIPTION_HINTS:
                p.description += _PARAM_DESCRIPTION_HINTS[hint_key]

        # Mutation detection
        is_mutation = op.method in ("post", "patch", "put", "delete")

        # Apply info
        needs_apply, apply_endpoint, apply_tool_name = _find_apply_info(
            op.path, op.method
        )

        # Dangerous check
        is_dangerous = op.operation_id in _DANGEROUS_ENDPOINTS
        danger_warning = _DANGEROUS_ENDPOINTS.get(op.operation_id)

        # Confirmation gate: all mutations need it
        needs_confirmation = is_mutation

        # Split params into body vs query
        body_params = [p for p in params if p.source == "body"]
        query_params = [p for p in params if p.source in ("query", "path")]

        has_request_body = bool(body_params)

        # Build docstring
        description = _build_docstring(
            op,
            tool_name,
            params,
            needs_apply,
            apply_tool_name,
            is_dangerous,
            danger_warning,
        )

        # Derive module from path
        module = _path_to_module(op.path)

        # Per-tool docstring note
        docstring_note = _TOOL_DOCSTRING_NOTES.get(op.operation_id)

        # List tool detection and response field extraction
        is_list_tool = tool_name.startswith("pfsense_list_")
        response_fields = None
        if is_list_tool:
            response_fields = extract_response_fields(spec, op)

        contexts.append(
            ToolContext(
                tool_name=tool_name,
                operation_id=op.operation_id,
                method=op.method,
                path=op.path,
                module=module,
                description=description,
                parameters=params,
                is_mutation=is_mutation,
                needs_confirmation=needs_confirmation,
                needs_apply=needs_apply,
                apply_endpoint=apply_endpoint,
                apply_tool_name=apply_tool_name,
                is_dangerous=is_dangerous,
                danger_warning=danger_warning,
                requires_basic_auth=op.requires_basic_auth,
                docstring_note=docstring_note,
                has_request_body=has_request_body,
                body_params=body_params,
                query_params=query_params,
                is_list_tool=is_list_tool,
                response_fields=response_fields,
            )
        )

    return contexts


# ---------------------------------------------------------------------------
# Tool index for discovery
# ---------------------------------------------------------------------------

_GENERIC_PARAMS = frozenset({
    "id", "limit", "offset", "sort_by", "sort_order", "query",
    "confirm", "parent_id", "items",
})


def build_tool_index(
    contexts: list[ToolContext],
) -> list[dict[str, str | list[str]]]:
    """Build a searchable tool index for the pfsense_search_tools discovery tool.

    Each entry: name, module, method, desc (one-line summary), kw (keywords).
    Keywords derived from tool name, module, path segments, and field names.
    Rebuilds automatically when the generator runs — zero manual maintenance.
    """
    index: list[dict[str, str | list[str]]] = []
    for ctx in contexts:
        kw: set[str] = set()

        # Tool name parts (skip "pfsense" prefix)
        kw.update(ctx.tool_name.split("_")[1:])

        # Module parts
        kw.update(ctx.module.split("_"))

        # Path segments after /api/v2/
        path_tail = ctx.path.replace("/api/v2/", "")
        kw.update(seg for seg in path_tail.split("/") if seg)

        # Body param names (first 10, skip generic)
        for p in ctx.body_params[:10]:
            if p.name not in _GENERIC_PARAMS:
                kw.add(p.name)

        # One-line summary
        desc = ctx.description.split("\n")[0].strip()

        index.append({
            "name": ctx.tool_name,
            "module": ctx.module,
            "method": ctx.method,
            "desc": desc,
            "kw": sorted(kw),
        })

    # Always-on tools (not in the spec, hand-maintained)
    index.append({
        "name": "pfsense_report_issue",
        "module": "_always_on",
        "method": "none",
        "desc": "Report an unexpected pfSense MCP tool error by composing a GitHub issue command",
        "kw": ["bug", "error", "github", "issue", "report"],
    })
    index.append({
        "name": "pfsense_get_overview",
        "module": "_always_on",
        "method": "get",
        "desc": "Get a concise pfSense system overview: version, interfaces, gateways, and services",
        "kw": ["gateways", "interfaces", "overview", "services", "status", "summary", "version"],
    })
    index.append({
        "name": "pfsense_search_tools",
        "module": "_always_on",
        "method": "none",
        "desc": "Search for pfSense tools by keyword to discover available operations",
        "kw": ["discover", "find", "help", "list", "search", "tools"],
    })

    return index
