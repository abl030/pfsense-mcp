"""
Convert OpenAPI operationIds to MCP tool names.

Rules from CLAUDE.md:
1. Strip 'Endpoint' suffix
2. get (singular) → get, get (plural) → list
3. post → create (CRUD) or keep for actions/apply
4. patch → update, delete → delete
5. CamelCase → snake_case
6. Prefix with pfsense_
7. Flatten nested resources
"""

from __future__ import annotations

import re

# Paths that end in "apply" — post means "apply", not "create"
_APPLY_PATHS = {
    "/api/v2/firewall/apply",
    "/api/v2/firewall/virtual_ip/apply",
    "/api/v2/interface/apply",
    "/api/v2/routing/apply",
    "/api/v2/services/dhcp_server/apply",
    "/api/v2/services/dns_forwarder/apply",
    "/api/v2/services/dns_resolver/apply",
    "/api/v2/services/haproxy/apply",
    "/api/v2/vpn/ipsec/apply",
    "/api/v2/vpn/wireguard/apply",
}

# Known action endpoints where POST isn't "create"
_ACTION_PATHS = {
    "/api/v2/diagnostics/halt_system",
    "/api/v2/diagnostics/reboot",
    "/api/v2/diagnostics/command_prompt",
    "/api/v2/diagnostics/ping",
    "/api/v2/auth/jwt",
}


_COMPOUND_WORDS = {
    "WireGuard": "wireguard",
    "OpenVPN": "openvpn",
    "IPsec": "ipsec",
    "HAProxy": "haproxy",
    "GraphQL": "graphql",
}


def _camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case, preserving compound words and acronyms."""
    # Step 1: Replace compound words with placeholder tokens
    for compound, replacement in _COMPOUND_WORDS.items():
        name = name.replace(compound, "_" + replacement + "_")

    # Step 2: Uppercase trailing 's' on plural acronyms (VLANs→VLANS)
    name = re.sub(r"([A-Z]{2,})s(?=[A-Z]|$|_)", lambda m: m.group(1) + "S", name)

    # Step 3: Standard CamelCase splitting
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = s.lower()

    # Step 4: Clean up double underscores and leading/trailing underscores
    s = re.sub(r"_+", "_", s)
    s = s.strip("_")
    return s


def _is_plural_endpoint(path: str, param_names: list[str]) -> bool:
    """
    Check if the endpoint is a plural (list) endpoint.

    Uses parameter-based detection: plural GETs have limit/offset params,
    singular GETs have an 'id' param. Falls back to path heuristics.
    """
    has_limit = "limit" in param_names
    has_id = "id" in param_names

    # Parameter-based detection is most reliable
    if has_limit and not has_id:
        return True
    if has_id and not has_limit:
        return False

    # Fallback: path heuristic for edge cases (e.g. no params)
    last_segment = path.rstrip("/").split("/")[-1]
    _SINGULAR_ENDINGS = {"status", "address", "access", "dns", "radius", "alias"}
    if last_segment in _SINGULAR_ENDINGS:
        return False
    if last_segment.endswith("ies") or last_segment.endswith("es"):
        return True
    if last_segment.endswith("s") and not last_segment.endswith("ss"):
        return True
    return False


def _path_to_resource_name(path: str) -> str:
    """
    Convert an API path to a flattened resource name.

    /api/v2/firewall/alias → firewall_alias
    /api/v2/services/haproxy/backend → haproxy_backend
    /api/v2/firewall/nat/one_to_one/mapping → nat_one_to_one_mapping
    """
    # Strip the /api/v2/ prefix
    stripped = re.sub(r"^/api/v2/", "", path)
    # Replace / with _
    parts = stripped.split("/")
    return "_".join(parts)


def operation_id_to_tool_name(
    operation_id: str, method: str, path: str, param_names: list[str] | None = None
) -> str:
    """
    Convert an operationId to a tool name.

    Examples:
        getFirewallAliasEndpoint       GET  /singular → pfsense_get_firewall_alias
        getFirewallAliasesEndpoint     GET  /plural   → pfsense_list_firewall_aliases
        postFirewallAliasEndpoint      POST /singular → pfsense_create_firewall_alias
        patchFirewallAliasEndpoint     PATCH          → pfsense_update_firewall_alias
        deleteFirewallAliasEndpoint    DELETE          → pfsense_delete_firewall_alias
        postFirewallApplyEndpoint      POST /apply    → pfsense_apply_firewall
        getFirewallApplyEndpoint       GET  /apply    → pfsense_get_firewall_apply_status
        putFirewallAliasesEndpoint     PUT  /plural   → pfsense_replace_firewall_aliases
    """
    # Step 1: Strip 'Endpoint' suffix
    name = operation_id
    if name.endswith("Endpoint"):
        name = name[: -len("Endpoint")]

    # Step 2: Separate the HTTP verb prefix from the resource
    # The operationId format is: {verb}{ResourceName}
    # verb is lowercase: get, post, patch, put, delete
    verb_match = re.match(r"^(get|post|patch|put|delete)(.+)$", name)
    if not verb_match:
        # Fallback: just convert the whole thing
        return "pfsense_" + _camel_to_snake(name)

    raw_verb = verb_match.group(1)
    resource_camel = verb_match.group(2)
    resource_snake = _camel_to_snake(resource_camel)

    # Step 3: Map verb based on context
    is_plural = _is_plural_endpoint(path, param_names or [])
    is_apply = path in _APPLY_PATHS
    is_action = path in _ACTION_PATHS
    is_settings = path.endswith("/settings") or path.endswith("/advanced_settings")

    if is_apply:
        if raw_verb == "get":
            return f"pfsense_get_{resource_snake}_status"
        elif raw_verb == "post":
            # Convert resource like "firewall_apply" → just use resource
            return f"pfsense_{resource_snake}"
        return f"pfsense_{raw_verb}_{resource_snake}"

    if raw_verb == "get":
        if is_settings:
            verb = "get"  # Settings are singletons, never "list"
        elif is_plural:
            verb = "list"
        else:
            verb = "get"
    elif raw_verb == "post":
        if is_action:
            verb = raw_verb  # keep as "post" for actions
        else:
            verb = "create"
    elif raw_verb == "patch":
        verb = "update"
    elif raw_verb == "put":
        verb = "replace"
    elif raw_verb == "delete":
        verb = "delete"
    else:
        verb = raw_verb

    return f"pfsense_{verb}_{resource_snake}"
