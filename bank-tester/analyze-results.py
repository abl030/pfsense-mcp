#!/usr/bin/env python3
"""
Analyze bank tester results from Claude's text output.

Reads *.txt files from a results directory, extracts TASK-REPORT blocks,
parses them, and produces an aggregate summary.

Usage:
    python bank-tester/analyze-results.py <results-dir>
"""

import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER_PY = REPO_ROOT / "generated" / "server.py"


def extract_reports_from_text(filepath: Path) -> list[dict]:
    """Extract task reports from a plain text output file.

    Also looks for tools_invoked immediately after the report block,
    since earlier tester prompts placed it outside the markers.
    """
    reports = []
    text = filepath.read_text()

    # Match report blocks, optionally capturing tools_invoked after the END marker
    pattern = r"---TASK-REPORT-START---(.*?)---TASK-REPORT-END---"
    for m in re.finditer(pattern, text, re.DOTALL):
        report = parse_report(m.group(1).strip())
        if report:
            # If tools_invoked wasn't inside the block, look right after it
            if "tools_invoked" not in report or not report["tools_invoked"]:
                after = text[m.end():m.end() + 2000]
                after_match = re.match(r"\s*tools_invoked:\s*\n((?:\s+-\s+\S+\n?)+)", after)
                if after_match:
                    tools = []
                    for line in after_match.group(1).strip().split("\n"):
                        name = line.strip().lstrip("- ").strip()
                        if name:
                            tools.append(name)
                    report["tools_invoked"] = tools
            reports.append(report)

    return reports


def parse_report(text: str) -> dict | None:
    """Parse a structured task report from text.

    Handles YAML-like format with simple key: value pairs.
    """
    report = {}
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#") or line.startswith("```"):
            i += 1
            continue

        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()

            if key == "details":
                # Parse the details list
                TOP_LEVEL_KEYS = {"cleanup_complete", "notes", "tools_invoked", "task_id", "status", "total_tool_calls", "first_attempt_failures"}
                details = []
                i += 1
                current_detail = {}
                while i < len(lines):
                    dline = lines[i]
                    stripped = dline.strip()
                    if stripped.startswith("```"):
                        i += 1
                        continue
                    # Check if we've hit a top-level key (not indented)
                    if stripped and ":" in stripped and not dline.startswith(" ") and not dline.startswith("\t"):
                        tl_key = stripped.partition(":")[0].strip()
                        if tl_key in TOP_LEVEL_KEYS:
                            if current_detail:
                                details.append(current_detail)
                            break
                    if stripped.startswith("- tool:"):
                        if current_detail:
                            details.append(current_detail)
                        current_detail = {"tool": stripped.split(":", 1)[1].strip()}
                    elif stripped and ":" in stripped and current_detail:
                        dk, _, dv = stripped.partition(":")
                        dk = dk.strip().lstrip("- ")
                        dv = dv.strip()
                        current_detail[dk] = dv
                    elif not stripped.startswith(" ") and not stripped.startswith("-") and ":" in stripped:
                        # We've left the details block
                        if current_detail:
                            details.append(current_detail)
                        break
                    i += 1
                if current_detail and current_detail not in details:
                    details.append(current_detail)
                report["details"] = details
                continue

            elif key == "tools_invoked":
                # Parse tool list
                tools = []
                i += 1
                while i < len(lines):
                    tline = lines[i].strip()
                    if tline.startswith("```") or tline.startswith("---"):
                        break
                    if tline.startswith("- "):
                        tool_name = tline.lstrip("- ").strip()
                        if tool_name:
                            tools.append(tool_name)
                    elif tline and ":" in tline and not tline.startswith("-"):
                        # Left the tools block
                        break
                    i += 1
                report["tools_invoked"] = tools
                continue

            elif key == "notes":
                # Multiline notes block — stop at report markers or top-level keys
                notes_lines = []
                i += 1
                while i < len(lines):
                    nline = lines[i]
                    stripped = nline.strip()
                    if stripped.startswith("---") or stripped.startswith("```"):
                        break
                    # Stop if we hit a top-level key (unindented, with colon)
                    if stripped and ":" in stripped and not nline.startswith(" ") and not nline.startswith("\t"):
                        tl_key = stripped.partition(":")[0].strip()
                        if tl_key in ("tools_invoked", "cleanup_complete", "task_id", "status"):
                            break
                    notes_lines.append(nline)
                    i += 1
                report["notes"] = "\n".join(notes_lines).strip()
                continue
            else:
                report[key] = value

        i += 1

    return report if report else None


def extract_all_tool_names() -> set[str]:
    """Extract all pfsense_* tool names from generated/server.py."""
    if not SERVER_PY.exists():
        return set()
    text = SERVER_PY.read_text()
    return set(re.findall(r"async def (pfsense_\w+)\(", text))


def collect_invoked_tools(reports: list[dict]) -> set[str]:
    """Collect all tools invoked across all reports.

    Strips the 'mcp__pfsense__' prefix that Claude CLI adds, so names
    match the function names extracted from generated/server.py.
    """
    tools: set[str] = set()
    for r in reports:
        for t in r.get("tools_invoked", []):
            # Strip MCP server prefix: mcp__pfsense__pfsense_foo → pfsense_foo
            name = re.sub(r"^mcp__pfsense__", "", t)
            tools.add(name)
    return tools


def generate_summary(results_dir: Path, reports: list[dict]) -> str:
    """Generate a markdown summary from parsed reports."""
    lines = []
    lines.append("# Bank Tester Results Summary\n")
    lines.append(f"**Results directory**: `{results_dir}`\n")
    lines.append(f"**Tasks analyzed**: {len(reports)}\n")

    # Overall status
    statuses = Counter(r.get("status", "unknown") for r in reports)
    lines.append("## Overall Status\n")
    for status, count in statuses.most_common():
        lines.append(f"- **{status}**: {count}")
    lines.append("")

    # Aggregate metrics
    total_calls = 0
    total_first_failures = 0
    for r in reports:
        try:
            total_calls += int(r.get("total_tool_calls", 0))
        except (ValueError, TypeError):
            pass
        try:
            total_first_failures += int(r.get("first_attempt_failures", 0))
        except (ValueError, TypeError):
            pass

    if total_calls > 0:
        success_rate = ((total_calls - total_first_failures) / total_calls) * 100
        lines.append(f"**Total tool calls**: {total_calls}")
        lines.append(f"**First-attempt failures**: {total_first_failures}")
        lines.append(f"**First-attempt success rate**: {success_rate:.1f}%\n")

    # Failure categories
    categories = Counter()
    tool_failures = Counter()
    for r in reports:
        for d in r.get("details", []):
            if isinstance(d, dict):
                cat = d.get("category", "unknown")
                categories[cat] += 1
                tool = d.get("tool", "unknown")
                tool_failures[tool] += 1

    if categories:
        lines.append("## Failure Categories\n")
        lines.append("| Category | Count |")
        lines.append("|----------|-------|")
        for cat, count in categories.most_common():
            lines.append(f"| `{cat}` | {count} |")
        lines.append("")

    if tool_failures:
        lines.append("## Tools With Most Failures\n")
        lines.append("| Tool | Failures |")
        lines.append("|------|----------|")
        for tool, count in tool_failures.most_common(10):
            lines.append(f"| `{tool}` | {count} |")
        lines.append("")

    # Per-task breakdown
    lines.append("## Per-Task Results\n")
    for r in reports:
        task_id = r.get("task_id", "unknown")
        status = r.get("status", "unknown")
        calls = r.get("total_tool_calls", "?")
        failures = r.get("first_attempt_failures", "?")
        cleanup = r.get("cleanup_complete", "?")
        lines.append(f"### {task_id}\n")
        lines.append(f"- **Status**: {status}")
        lines.append(f"- **Tool calls**: {calls}")
        lines.append(f"- **First-attempt failures**: {failures}")
        lines.append(f"- **Cleanup complete**: {cleanup}")

        details = r.get("details", [])
        if details and isinstance(details, list) and len(details) > 0:
            lines.append("- **Failure details**:")
            for d in details:
                if isinstance(d, dict):
                    lines.append(f"  - `{d.get('tool', '?')}` [{d.get('category', '?')}]: {d.get('diagnosis', 'no diagnosis')}")

        notes = r.get("notes", "")
        if notes:
            lines.append(f"- **Notes**: {notes}")
        lines.append("")

    # Tool coverage
    all_tools = extract_all_tool_names()
    invoked_tools = collect_invoked_tools(reports)
    if all_tools:
        covered = invoked_tools & all_tools
        not_covered = sorted(all_tools - invoked_tools)
        pct = len(covered) / len(all_tools) * 100 if all_tools else 0

        lines.append("## Tool Coverage\n")
        lines.append(f"- **Total tools**: {len(all_tools)}")
        lines.append(f"- **Tools invoked**: {len(covered)}")
        lines.append(f"- **Coverage**: {pct:.1f}%")

        if not_covered:
            lines.append(f"- **Not covered** ({len(not_covered)}):")
            # Show first 50 uncovered tools
            for t in not_covered[:50]:
                lines.append(f"  - `{t}`")
            if len(not_covered) > 50:
                lines.append(f"  - ... and {len(not_covered) - 50} more")
        lines.append("")

    # Actionable findings
    if categories:
        lines.append("## Actionable Findings\n")
        if categories.get("missing_enum_values", 0) > 0:
            lines.append("- **Enum values**: Generator should render valid values in parameter descriptions")
        if categories.get("type_confusion", 0) > 0:
            lines.append("- **Type hints**: Generator should add example values for list-typed params")
        if categories.get("missing_required_field", 0) > 0:
            lines.append("- **Required fields**: Generator should mark required fields more clearly")
        if categories.get("dependency_unknown", 0) > 0:
            lines.append("- **Dependencies**: Generator should add 'Requires: ...' notes to dependent resources")
        if categories.get("forgot_apply", 0) > 0:
            lines.append("- **Apply reminders**: Tool docstrings need stronger apply-after-mutation reminders")
        if categories.get("parameter_format", 0) > 0:
            lines.append("- **Parameter format**: Add format examples (CIDR vs plain IP, etc.) to descriptions")
        lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze-results.py <results-dir> [results-dir2 ...]", file=sys.stderr)
        sys.exit(1)

    results_dirs = [Path(d) for d in sys.argv[1:]]
    for d in results_dirs:
        if not d.is_dir():
            print(f"Error: {d} is not a directory", file=sys.stderr)
            sys.exit(1)

    # Collect all reports from text files across all directories
    all_reports = []
    total_files = 0

    for results_dir in results_dirs:
        txt_files = sorted(results_dir.glob("*.txt"))
        if not txt_files:
            continue
        total_files += len(txt_files)
        print(f"Analyzing {len(txt_files)} result files from {results_dir.name}...")

        for tf in txt_files:
            reports = extract_reports_from_text(tf)
            if reports:
                all_reports.extend(reports)
                print(f"  {tf.name}: {len(reports)} report(s)")
            else:
                print(f"  {tf.name}: no reports found")

    if total_files == 0:
        print("No .txt files found in any directory", file=sys.stderr)
        sys.exit(1)

    if not all_reports:
        print("Warning: No task reports found in any file.", file=sys.stderr)

    # Use last directory for summary output, or first if single
    output_dir = results_dirs[-1]
    summary = generate_summary(output_dir, all_reports)

    # Write summary
    summary_path = output_dir / "summary.md"
    with open(summary_path, "w") as f:
        f.write(summary)

    print(f"\nSummary written to {summary_path}")
    print(summary)


if __name__ == "__main__":
    main()
