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
from .schema_parser import ToolParameter, extract_tool_parameters

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
    description: str
    parameters: list[ToolParameter]
    is_mutation: bool  # POST/PATCH/PUT/DELETE
    needs_confirmation: bool  # mutations need confirm gate
    needs_apply: bool  # mutation in a subsystem that requires apply
    apply_endpoint: str | None  # e.g. "/api/v2/firewall/apply"
    apply_tool_name: str | None  # e.g. "pfsense_firewall_apply"
    is_dangerous: bool
    danger_warning: str | None
    has_request_body: bool
    body_params: list[ToolParameter]  # params that go in JSON body
    query_params: list[ToolParameter]  # params that go in URL query


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
    tool_name: str,
    params: list[ToolParameter],
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

        contexts.append(
            ToolContext(
                tool_name=tool_name,
                operation_id=op.operation_id,
                method=op.method,
                path=op.path,
                description=description,
                parameters=params,
                is_mutation=is_mutation,
                needs_confirmation=needs_confirmation,
                needs_apply=needs_apply,
                apply_endpoint=apply_endpoint,
                apply_tool_name=apply_tool_name,
                is_dangerous=is_dangerous,
                danger_warning=danger_warning,
                has_request_body=has_request_body,
                body_params=body_params,
                query_params=query_params,
            )
        )

    return contexts
