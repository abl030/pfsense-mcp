"""
Render the Jinja2 template and write the generated server.

Uses tool contexts from context_builder and the server.py.j2 template
to produce generated/server.py. Tool functions are generated
programmatically for precise formatting control.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import jinja2

from .context_builder import ToolContext
from .schema_parser import ToolParameter

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "templates"
OUTPUT_FILE = REPO_ROOT / "generated" / "server.py"


def _gen_signature(tool: ToolContext) -> str:
    """Generate the function signature lines."""
    lines = []
    lines.append("@mcp.tool()")
    lines.append(f"async def {tool.tool_name}(")

    # Python requires: required params first, then optional (with defaults).
    # Order: required API params → confirm (has default) → optional API params

    # Required params first (no defaults)
    for p in tool.parameters:
        if p.required:
            lines.append(f"    {p.name}: {p.python_type},")

    # confirm gate (has default) — between required and optional
    if tool.is_mutation:
        lines.append("    confirm: bool = False,")

    # Optional params (all have defaults)
    for p in tool.parameters:
        if not p.required:
            if p.has_default and p.default is not None:
                lines.append(
                    f"    {p.name}: {p.python_type} | None = {repr(p.default)},"
                )
            else:
                lines.append(f"    {p.name}: {p.python_type} | None = None,")

    lines.append(") -> dict[str, Any] | list[Any] | str:")

    return "\n".join(lines)


def _gen_docstring(tool: ToolContext) -> str:
    """Generate the docstring."""
    # Keep docstring concise: just the API ref line
    doc_lines = []
    doc_lines.append(f'    """{tool.method.upper()} {tool.path}')

    if tool.requires_basic_auth:
        doc_lines.append("")
        doc_lines.append(
            "    WARNING: This endpoint requires HTTP BasicAuth (username:password)."
        )
        doc_lines.append(
            "    It does NOT accept API key or JWT auth. Will return 401 via MCP."
        )

    if tool.is_dangerous and tool.danger_warning:
        doc_lines.append("")
        doc_lines.append(f"    WARNING: {tool.danger_warning}")

    if tool.needs_apply and tool.apply_tool_name:
        doc_lines.append("")
        doc_lines.append(
            f"    Note: Call {tool.apply_tool_name} after this to apply changes."
        )

    # Parameter descriptions (brief)
    has_param_docs = False
    for p in tool.parameters:
        if p.description or p.enum:
            if not has_param_docs:
                doc_lines.append("")
                has_param_docs = True
            desc = p.description or ""
            # Strip HTML tags from OpenAPI descriptions
            desc = re.sub(r"<br\s*/?>", " ", desc)
            desc = re.sub(r"<[^>]+>", "", desc)
            # Collapse whitespace
            desc = re.sub(r"\s+", " ", desc).strip()
            # No truncation on descriptions — AI consumers handle long text fine,
            # and truncating loses critical info (modifier syntax, conditionals)
            if p.enum:
                enum_str = ", ".join(repr(v) for v in p.enum)
                if desc:
                    desc += f" Valid values: [{enum_str}]"
                else:
                    desc = f"Valid values: [{enum_str}]"
            doc_lines.append(f"    {p.name}: {desc}")

    doc_lines.append('    """')
    return "\n".join(doc_lines)


def _gen_confirmation_gate(tool: ToolContext) -> str:
    """Generate the confirmation gate for mutations."""
    if not tool.is_mutation:
        return ""

    lines = ["    if not confirm:"]
    msg_parts = [
        f'            "This is a {tool.method.upper()} operation on {tool.path}. "',
        '            "Set confirm=True to execute."',
    ]
    if tool.is_dangerous and tool.danger_warning:
        msg_parts.append(f'            "\\n\\nWARNING: {tool.danger_warning}"')
    if tool.needs_apply and tool.apply_tool_name:
        msg_parts.append(
            f'            "\\n\\nNote: After this operation, call {tool.apply_tool_name} to apply changes."'
        )

    lines.append("        return (")
    for part in msg_parts:
        lines.append(part)
    lines.append("        )")
    return "\n".join(lines)


def _gen_body(tool: ToolContext) -> str:
    """Generate the function body (after docstring and confirmation gate)."""
    lines = []

    # Query params dict
    if tool.query_params:
        lines.append("    params: dict[str, Any] = {}")
        for p in tool.query_params:
            api_key = p.api_name or p.name
            if api_key == "query":
                # The 'query' parameter is a catch-all dict (style: form, explode: true).
                # Merge its keys into params so they become individual query params
                # (e.g., query={"name": "foo"} → ?name=foo) instead of ?query={...}
                lines.append(f"    if {p.name} is not None:")
                lines.append(f"        params.update({p.name})")
            else:
                lines.append(f"    if {p.name} is not None:")
                lines.append(f'        params["{api_key}"] = {p.name}')

    # Request body
    if tool.has_request_body and tool.method != "put":
        lines.append("    body: dict[str, Any] = {}")
        for p in tool.body_params:
            api_key = p.api_name or p.name
            lines.append(f"    if {p.name} is not None:")
            lines.append(f'        body["{api_key}"] = {p.name}')
    elif tool.method == "put" and tool.has_request_body:
        lines.append("    body = items")

    # API call
    call_args = [
        f'        "{tool.method.upper()}",',
        f'        "{tool.path}",',
    ]
    if tool.query_params:
        call_args.append("        params=params,")
    if tool.has_request_body:
        call_args.append("        json_body=body,")

    lines.append("    return await _client.request(")
    lines.extend(call_args)
    lines.append("    )")

    return "\n".join(lines)


def _gen_tool_function(tool: ToolContext) -> str:
    """Generate a complete tool function."""
    parts = []
    parts.append(_gen_signature(tool))
    parts.append(_gen_docstring(tool))

    gate = _gen_confirmation_gate(tool)
    if gate:
        parts.append(gate)

    parts.append(_gen_body(tool))
    return "\n".join(parts)


def render(contexts: list[ToolContext]) -> str:
    """Render the complete server file."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
    )
    template = env.get_template("server.py.j2")

    # Generate all tool functions
    tool_functions = []
    for ctx in contexts:
        tool_functions.append(_gen_tool_function(ctx))

    tool_code = "\n\n\n".join(tool_functions)

    return template.render(
        tool_count=len(contexts),
        tool_code="\n\n\n" + tool_code + "\n",
    )


def write_output(content: str, output_path: Path | None = None) -> Path:
    """Write the rendered content to the output file."""
    path = output_path or OUTPUT_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path
