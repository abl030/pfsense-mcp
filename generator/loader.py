"""
Load and parse the pfSense REST API OpenAPI 3.0.0 spec.

Reads openapi-spec.json and returns structured operation data
for each path+method combination.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Parameter:
    """An API operation parameter (query, path, header)."""

    name: str
    location: str  # "query", "path", "header"
    required: bool
    schema: dict[str, Any]
    description: str = ""
    default: Any = None
    has_default: bool = False


@dataclass
class Operation:
    """A single API operation (one HTTP method on one path)."""

    operation_id: str
    method: str  # "get", "post", "patch", "put", "delete"
    path: str  # e.g. "/api/v2/firewall/alias"
    tags: list[str]
    parameters: list[Parameter] = field(default_factory=list)
    request_body_schema: dict[str, Any] | None = None
    request_body_required_fields: list[str] = field(default_factory=list)
    response_schema: dict[str, Any] | None = None
    description: str = ""
    summary: str = ""
    requires_basic_auth: bool = False  # True if endpoint only accepts BasicAuth


def load_spec(spec_path: str | Path) -> dict[str, Any]:
    """Load the raw OpenAPI spec from JSON."""
    with open(spec_path) as f:
        return json.load(f)


def resolve_ref(spec: dict[str, Any], ref: str) -> dict[str, Any]:
    """Resolve a $ref pointer like '#/components/schemas/FirewallAlias'."""
    parts = ref.lstrip("#/").split("/")
    node = spec
    for part in parts:
        node = node[part]
    return node


def resolve_schema(spec: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively resolve a schema, handling $ref and allOf.

    Returns a flattened schema with all properties merged.
    """
    if "$ref" in schema:
        return resolve_schema(spec, resolve_ref(spec, schema["$ref"]))

    if "allOf" in schema:
        merged: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
        for sub in schema["allOf"]:
            resolved = resolve_schema(spec, sub)
            merged["properties"].update(resolved.get("properties", {}))
            merged["required"].extend(resolved.get("required", []))
        return merged

    return schema


def _extract_parameter(param: dict[str, Any]) -> Parameter:
    """Extract a Parameter from an OpenAPI parameter object."""
    schema = param.get("schema", {})
    default = schema.get("default")
    return Parameter(
        name=param["name"],
        location=param["in"],
        required=param.get("required", False),
        schema=schema,
        description=param.get("description", ""),
        default=default,
        has_default=("default" in schema),
    )


def _extract_request_body(
    spec: dict[str, Any], request_body: dict[str, Any]
) -> tuple[dict[str, Any] | None, list[str]]:
    """Extract and resolve the request body schema, returning (schema, required_fields)."""
    content = request_body.get("content", {})
    # Prefer application/json
    json_content = content.get("application/json", {})
    if not json_content:
        return None, []

    raw_schema = json_content.get("schema", {})
    resolved = resolve_schema(spec, raw_schema)
    required_fields = resolved.get("required", [])
    return resolved, required_fields


def _extract_response_schema(
    spec: dict[str, Any], responses: dict[str, Any]
) -> dict[str, Any] | None:
    """Extract the 200 response data schema."""
    resp_200 = responses.get("200", {})
    content = resp_200.get("content", {})
    json_content = content.get("application/json", {})
    if not json_content:
        return None

    raw_schema = json_content.get("schema", {})
    resolved = resolve_schema(spec, raw_schema)

    # The response is wrapped in the Success envelope.
    # Extract the 'data' field schema if present.
    data_schema = resolved.get("properties", {}).get("data")
    if data_schema:
        return resolve_schema(spec, data_schema)
    return resolved


def parse_operations(spec: dict[str, Any]) -> list[Operation]:
    """Parse all operations from the spec."""
    operations: list[Operation] = []

    for path, path_item in spec.get("paths", {}).items():
        for method in ("get", "post", "put", "patch", "delete"):
            if method not in path_item:
                continue

            op = path_item[method]
            operation_id = op.get("operationId", "")
            if not operation_id:
                continue

            # Parameters
            params = [_extract_parameter(p) for p in op.get("parameters", [])]

            # Request body
            request_body = op.get("requestBody", {})
            body_schema, body_required = _extract_request_body(spec, request_body)

            # Response schema
            response_schema = _extract_response_schema(spec, op.get("responses", {}))

            # Detect BasicAuth-only endpoints: security field overrides global
            # default. If security is exactly [{"BasicAuth": []}], this endpoint
            # only accepts BasicAuth (not API key or JWT).
            requires_basic_auth = False
            op_security = op.get("security")
            if op_security is not None:
                scheme_names = {
                    k for item in op_security for k in item.keys()
                }
                if scheme_names == {"BasicAuth"}:
                    requires_basic_auth = True

            operations.append(
                Operation(
                    operation_id=operation_id,
                    method=method,
                    path=path,
                    tags=op.get("tags", []),
                    parameters=params,
                    request_body_schema=body_schema,
                    request_body_required_fields=body_required,
                    response_schema=response_schema,
                    description=op.get("description", ""),
                    summary=op.get("summary", ""),
                    requires_basic_auth=requires_basic_auth,
                )
            )

    return operations
