"""
Entry point for the pfSense MCP server generator.

Usage:
    python -m generator [--spec SPEC_PATH] [--output OUTPUT_PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .codegen import render, write_output
from .context_builder import MODULE_ORDER, build_tool_contexts
from .loader import load_spec

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SPEC = REPO_ROOT / "openapi-spec.json"
DEFAULT_OUTPUT = REPO_ROOT / "generated" / "server.py"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate pfSense MCP server")
    parser.add_argument(
        "--spec",
        type=Path,
        default=DEFAULT_SPEC,
        help="Path to OpenAPI spec JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output path for generated server",
    )
    args = parser.parse_args()

    print(f"Loading spec from {args.spec}...")
    spec = load_spec(args.spec)

    print("Building tool contexts...")
    contexts = build_tool_contexts(spec)
    print(f"  {len(contexts)} tools")

    # Count categories
    mutations = sum(1 for c in contexts if c.is_mutation)
    reads = len(contexts) - mutations
    dangerous = sum(1 for c in contexts if c.is_dangerous)
    with_apply = sum(1 for c in contexts if c.needs_apply)
    print(f"  {reads} read-only, {mutations} mutations")
    print(f"  {dangerous} dangerous, {with_apply} need apply")

    # Module breakdown
    print("  Module breakdown:")
    for mod in MODULE_ORDER:
        mod_reads = sum(1 for c in contexts if c.module == mod and not c.is_mutation)
        mod_writes = sum(1 for c in contexts if c.module == mod and c.is_mutation)
        mod_total = mod_reads + mod_writes
        if mod_total:
            print(f"    {mod}: {mod_total} tools ({mod_reads} read, {mod_writes} write)")

    # --- Generate server ---
    print("Rendering server...")
    content = render(contexts)

    print(f"Writing server to {args.output}...")
    path = write_output(content, args.output)

    print("Verifying server syntax...")
    try:
        compile(content, str(path), "exec")
        print("  Valid Python syntax")
    except SyntaxError as e:
        print(f"  SYNTAX ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nDone! Server: {args.output} ({len(contexts)} tools)")


if __name__ == "__main__":
    main()
