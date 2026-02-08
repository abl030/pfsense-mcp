"""
Extract parameter types from OpenAPI schemas.

Maps OpenAPI types to Python type annotations and builds
parameter lists for generated tool functions.
"""

from __future__ import annotations

import keyword
from dataclasses import dataclass, field
from typing import Any

from .loader import Operation, Parameter, resolve_schema

# Python names that can't be used as parameter names
_RESERVED = set(keyword.kwlist) | {"type"}


def _safe_name(name: str) -> str:
    """Make a name safe for use as a Python parameter."""
    if name in _RESERVED:
        return name + "_"
    return name


@dataclass
class ToolParameter:
    """A parameter for a generated tool function."""

    name: str  # Python-safe name (may have _ suffix for reserved words)
    python_type: str  # e.g. "str", "int", "bool", "list[str]", "dict[str, Any]"
    required: bool
    default: Any = None
    has_default: bool = False
    description: str = ""
    enum: list[str] | None = None
    source: str = "query"  # "query", "body", "path"
    api_name: str = ""  # Original API name (for body/query keys)


def _openapi_type_to_python(schema: dict[str, Any]) -> str:
    """Map an OpenAPI schema to a Python type string."""
    # Handle oneOf (e.g. id can be int or string)
    if "oneOf" in schema:
        types = [_openapi_type_to_python(s) for s in schema["oneOf"]]
        # Simplify: if it's int|string, just use str (accepts both)
        if set(types) == {"int", "str"}:
            return "str | int"
        return " | ".join(types)

    if "anyOf" in schema:
        types = [_openapi_type_to_python(s) for s in schema["anyOf"]]
        return " | ".join(types)

    oa_type = schema.get("type", "string")

    if oa_type == "string":
        return "str"
    elif oa_type == "integer":
        return "int"
    elif oa_type == "number":
        return "float"
    elif oa_type == "boolean":
        return "bool"
    elif oa_type == "array":
        items = schema.get("items", {})
        item_type = _openapi_type_to_python(items)
        return f"list[{item_type}]"
    elif oa_type == "object":
        return "dict[str, Any]"
    else:
        return "Any"


def _is_read_only(prop_schema: dict[str, Any]) -> bool:
    """Check if a property is read-only."""
    return prop_schema.get("readOnly", False)


def extract_tool_parameters(
    spec: dict[str, Any], operation: Operation
) -> list[ToolParameter]:
    """
    Extract all parameters for a tool function from an operation.

    Combines URL query/path parameters with request body fields.
    """
    params: list[ToolParameter] = []
    seen_names: set[str] = set()

    # 1. Query/path parameters
    for p in operation.parameters:
        # Skip the catch-all 'query' parameter
        if p.name == "query":
            continue
        safe = _safe_name(p.name)
        params.append(
            ToolParameter(
                name=safe,
                python_type=_openapi_type_to_python(p.schema),
                required=p.required,
                default=p.default,
                has_default=p.has_default,
                description=_clean_description(p.description),
                enum=p.schema.get("enum"),
                source="query" if p.location == "query" else p.location,
                api_name=p.name,
            )
        )
        seen_names.add(p.name)

    # 2. Request body fields (for POST, PATCH, PUT)
    if operation.request_body_schema and operation.method in (
        "post",
        "patch",
        "put",
    ):
        body = operation.request_body_schema
        # If the body is an array type (PUT bulk), handle it as a single param
        if body.get("type") == "array":
            params.append(
                ToolParameter(
                    name="items",
                    python_type="list[dict[str, Any]]",
                    required=True,
                    description="List of objects for bulk replacement.",
                    source="body",
                )
            )
        else:
            # Resolve and flatten the schema to get properties
            resolved = resolve_schema(spec, body)
            properties = resolved.get("properties", {})
            required_fields = set(operation.request_body_required_fields)

            for prop_name, prop_schema in properties.items():
                if prop_name in seen_names:
                    continue
                # Skip read-only fields (they're in responses, not requests)
                if _is_read_only(prop_schema):
                    continue

                resolved_prop = resolve_schema(spec, prop_schema)
                is_required = prop_name in required_fields

                default = resolved_prop.get("default")
                has_default = "default" in resolved_prop
                # Sanitize int64 max/min sentinel values — they mean "no limit"
                # and are too large for the Anthropic API to serialize
                if isinstance(default, int) and abs(default) >= 2**53:
                    default = None
                    has_default = False
                # Conditional fields should default to None — sending a spec
                # default when the condition isn't met causes validation errors
                # (e.g., target_subnet=128 fails for IPv4 addresses)
                desc_text = resolved_prop.get("description", "")
                if has_default and default is not None and "only available when" in desc_text:
                    default = None
                    has_default = True  # still has a default (None), just not the spec's

                safe = _safe_name(prop_name)
                params.append(
                    ToolParameter(
                        name=safe,
                        python_type=_openapi_type_to_python(resolved_prop),
                        required=is_required,
                        default=default,
                        has_default=has_default,
                        description=_clean_description(
                            resolved_prop.get("description", "")
                        ),
                        enum=resolved_prop.get("enum"),
                        source="body",
                        api_name=prop_name,
                    )
                )
                seen_names.add(prop_name)

    # Sort: required params first, then optional
    params.sort(key=lambda p: (not p.required, p.name))

    return params


def _clean_description(desc: str) -> str:
    """Clean HTML tags and whitespace from descriptions."""
    import re

    # Remove HTML tags
    desc = re.sub(r"<[^>]+>", "", desc)
    # Normalize whitespace
    desc = re.sub(r"\s+", " ", desc).strip()
    return desc
