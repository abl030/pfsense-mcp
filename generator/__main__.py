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
from .context_builder import build_tool_contexts
from .loader import load_spec
from .test_generator import generate_tests

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SPEC = REPO_ROOT / "openapi-spec.json"
DEFAULT_OUTPUT = REPO_ROOT / "generated" / "server.py"
DEFAULT_TEST_OUTPUT = REPO_ROOT / "generated" / "tests.py"


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
    parser.add_argument(
        "--test-output",
        type=Path,
        default=DEFAULT_TEST_OUTPUT,
        help="Output path for generated tests",
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

    # --- Generate tests ---
    print("Generating tests...")
    test_content = generate_tests(contexts)

    print(f"Writing tests to {args.test_output}...")
    args.test_output.parent.mkdir(parents=True, exist_ok=True)
    args.test_output.write_text(test_content)

    print("Verifying test syntax...")
    try:
        compile(test_content, str(args.test_output), "exec")
        print("  Valid Python syntax")
    except SyntaxError as e:
        print(f"  SYNTAX ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Count tests
    test_count = test_content.count("\ndef test_")
    print(f"  {test_count} test functions")

    print(f"\nDone!")
    print(f"  Server: {args.output} ({len(contexts)} tools)")
    print(f"  Tests:  {args.test_output} ({test_count} tests)")


if __name__ == "__main__":
    main()
