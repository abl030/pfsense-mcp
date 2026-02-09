#!/usr/bin/env python3
"""
Generate bank tester task files from task-config.yaml and openapi-spec.json.

Reads the task configuration and produces markdown task files in bank-tester/tasks/.
Reuses generator/naming.py for tool name derivation.

Usage:
    python bank-tester/generate-tasks.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

# Add repo root to path so we can import generator modules
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from generator.naming import operation_id_to_tool_name
from generator.loader import load_spec, parse_operations

SPEC_PATH = REPO_ROOT / "openapi-spec.json"
CONFIG_PATH = REPO_ROOT / "bank-tester" / "task-config.yaml"
TASKS_DIR = REPO_ROOT / "bank-tester" / "tasks"


def load_config() -> list[dict[str, Any]]:
    """Load and return the task config."""
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    return config.get("tasks", [])


def build_tool_name_map(spec: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Build a mapping of (path, method) -> tool_name from the spec."""
    tool_map: dict[str, dict[str, str]] = {}
    operations = parse_operations(spec)
    for op in operations:
        param_names = [p.name for p in op.parameters]
        tool_name = operation_id_to_tool_name(
            op.operation_id, op.method, op.path, param_names
        )
        if op.path not in tool_map:
            tool_map[op.path] = {}
        tool_map[op.path][op.method] = tool_name
    return tool_map


def get_tool_name(tool_map: dict, path: str, method: str) -> str:
    """Look up a tool name, with fallback."""
    return tool_map.get(path, {}).get(method, f"pfsense_{method}_{path}")


def format_values(values: Any, indent: int = 2) -> str:
    """Format test values as human-readable key=value pairs."""
    if not values:
        return "(no parameters needed)"
    if isinstance(values, dict):
        lines = []
        for k, v in values.items():
            if isinstance(v, str) and len(v) > 60:
                v_display = v[:57] + "..."
            else:
                v_display = repr(v) if not isinstance(v, str) else v
            lines.append(f"{'  ' * indent}- `{k}`: `{v_display}`")
        return "\n".join(lines)
    return str(values)


def generate_crud_steps(
    task_config: dict,
    ep: dict,
    tool_map: dict,
    step_num: int,
    all_steps: list[str],
    cleanup_steps: list[str],
    tools_exercised: list[str],
) -> int:
    """Generate CRUD steps for an endpoint. Returns next step number."""
    path = ep["path"]
    create_values = ep.get("create_values", {})
    update_field = ep.get("update_field")
    update_value = ep.get("update_value")
    parent = ep.get("parent")
    parent_id_field = ep.get("parent_id_field")
    static_parent_id = ep.get("static_parent_id")
    inject_field = ep.get("inject_field")
    inject_from = ep.get("inject_from")
    setup_only = ep.get("setup_only", False)

    # Derive tool names
    create_tool = get_tool_name(tool_map, path, "post")
    get_tool = get_tool_name(tool_map, path, "get")
    update_tool = get_tool_name(tool_map, path, "patch")
    delete_tool = get_tool_name(tool_map, path, "delete")

    # Check for list tool (plural path)
    # Find the shortest matching path to avoid picking sub-resource plurals
    # e.g., /firewall/aliases (shorter) wins over /firewall/alias/sub_resource (longer)
    list_tool = None
    best_path = None
    for p in tool_map:
        if p.startswith(path) and p != path and "get" in tool_map[p]:
            candidate = get_tool_name(tool_map, p, "get")
            if "list_" in candidate:
                if best_path is None or len(p) < len(best_path):
                    best_path = p
                    list_tool = candidate

    # Parent reference
    parent_note = ""
    if parent and parent_id_field:
        parent_note = f" (use the `{parent_id_field}` from the parent resource created earlier)"
    elif static_parent_id:
        parent_note = f" (use `parent_id=\"{static_parent_id}\"`)"
    elif inject_field and inject_from:
        parent_note = f" (inject `{inject_field}` from parent's `{inject_from}` field)"

    # Create
    all_steps.append(
        f"{step_num}. **Create** using `{create_tool}` with `confirm=True`{parent_note}:\n{format_values(create_values)}"
    )
    tools_exercised.append(create_tool)
    step_num += 1

    if setup_only:
        cleanup_steps.insert(0, f"- Delete setup resource at `{path}` using `{delete_tool}` with `confirm=True`")
        tools_exercised.append(delete_tool)
        return step_num

    # List (if available)
    if list_tool:
        all_steps.append(
            f"{step_num}. **List** using `{list_tool}` — verify the created resource appears"
        )
        tools_exercised.append(list_tool)
        step_num += 1

    # Get
    all_steps.append(
        f"{step_num}. **Get** using `{get_tool}` with the ID from the create response"
    )
    tools_exercised.append(get_tool)
    step_num += 1

    # Update
    if update_field:
        all_steps.append(
            f'{step_num}. **Update** using `{update_tool}` with `confirm=True` — set `{update_field}` to `{update_value}`'
        )
        tools_exercised.append(update_tool)
        step_num += 1

        # Verify update
        all_steps.append(
            f"{step_num}. **Get** again using `{get_tool}` — verify `{update_field}` was updated"
        )
        step_num += 1

    # Delete goes in cleanup
    cleanup_steps.insert(
        0,
        f"- Delete using `{delete_tool}` with `confirm=True` (ID from create step)",
    )
    tools_exercised.append(delete_tool)

    return step_num


def generate_settings_steps(
    ep: dict,
    tool_map: dict,
    step_num: int,
    all_steps: list[str],
    tools_exercised: list[str],
) -> int:
    """Generate settings GET/PATCH steps. Returns next step number."""
    path = ep["path"]
    patch_field = ep.get("patch_field")
    patch_value = ep.get("patch_value")
    restore_value = ep.get("restore_value")
    extra_fields = ep.get("extra_fields", {})

    patch_only = ep.get("patch_only", False)
    patch_tool = get_tool_name(tool_map, path, "patch")

    # Get current settings (skip if patch_only — no GET endpoint exists)
    if not patch_only:
        get_tool = get_tool_name(tool_map, path, "get")
        all_steps.append(
            f"{step_num}. **Get settings** using `{get_tool}` — note current value of `{patch_field}`"
        )
        tools_exercised.append(get_tool)
        step_num += 1

    # Patch
    if patch_field:
        extra_note = ""
        if extra_fields:
            extra_note = f" (also include: {', '.join(f'`{k}={v}`' for k, v in extra_fields.items())})"
        all_steps.append(
            f"{step_num}. **Update settings** using `{patch_tool}` with `confirm=True` — set `{patch_field}` to `{repr(patch_value)}`{extra_note}"
        )
        tools_exercised.append(patch_tool)
        step_num += 1

        # Verify (only if GET exists)
        if not patch_only:
            all_steps.append(
                f"{step_num}. **Get settings** again using `{get_tool}` — verify `{patch_field}` was updated"
            )
            step_num += 1

        # Restore
        if restore_value is not None:
            all_steps.append(
                f"{step_num}. **Restore** using `{patch_tool}` with `confirm=True` — set `{patch_field}` back to `{repr(restore_value)}`"
            )
            step_num += 1

    return step_num


def generate_apply_steps(
    ep: dict,
    tool_map: dict,
    step_num: int,
    all_steps: list[str],
    tools_exercised: list[str],
) -> int:
    """Generate apply steps. Returns next step number."""
    path = ep["path"]
    status_tool = get_tool_name(tool_map, path, "get")
    apply_tool = get_tool_name(tool_map, path, "post")

    all_steps.append(
        f"{step_num}. **Check apply status** using `{status_tool}`"
    )
    tools_exercised.append(status_tool)
    step_num += 1

    all_steps.append(
        f"{step_num}. **Apply changes** using `{apply_tool}` with `confirm=True`"
    )
    tools_exercised.append(apply_tool)
    step_num += 1

    return step_num


def generate_action_steps(
    ep: dict,
    tool_map: dict,
    step_num: int,
    all_steps: list[str],
    tools_exercised: list[str],
) -> int:
    """Generate action POST steps. Returns next step number."""
    path = ep["path"]
    action_body = ep.get("action_body", {})
    notes = ep.get("notes", "")
    needs_basic_auth = ep.get("needs_basic_auth", False)

    method = ep.get("action_method", "post")
    action_tool = get_tool_name(tool_map, path, method)

    auth_note = " **Note: requires BasicAuth (admin:pfsense), not API key.**" if needs_basic_auth else ""
    extra_note = f" ({notes})" if notes else ""

    all_steps.append(
        f"{step_num}. **Execute** `{action_tool}` with `confirm=True`{auth_note}{extra_note}:\n{format_values(action_body)}"
    )
    tools_exercised.append(action_tool)
    step_num += 1

    return step_num


def generate_read_only_steps(
    ep: dict,
    tool_map: dict,
    step_num: int,
    all_steps: list[str],
    tools_exercised: list[str],
) -> int:
    """Generate read-only GET steps. Returns next step number."""
    path = ep["path"]
    notes = ep.get("notes", "")

    get_tool = get_tool_name(tool_map, path, "get")
    extra_note = f" ({notes})" if notes else ""

    all_steps.append(
        f"{step_num}. **Read** using `{get_tool}`{extra_note}"
    )
    tools_exercised.append(get_tool)
    step_num += 1

    return step_num


def generate_replace_steps(
    ep: dict,
    tool_map: dict,
    step_num: int,
    all_steps: list[str],
    tools_exercised: list[str],
) -> int:
    """Generate PUT (replace) steps: GET current → PUT back → verify. Returns next step number."""
    path = ep["path"]
    notes = ep.get("notes", "")

    replace_tool = get_tool_name(tool_map, path, "put")
    list_tool = get_tool_name(tool_map, path, "get")

    extra_note = f" ({notes})" if notes else ""

    # GET current collection
    all_steps.append(
        f"{step_num}. **List** current resources using `{list_tool}`{extra_note}"
    )
    tools_exercised.append(list_tool)
    step_num += 1

    # PUT the same data back (safe no-op)
    all_steps.append(
        f"{step_num}. **Replace** using `{replace_tool}` with `confirm=True` — PUT the same data back (safe no-op). Pass the full list from the previous step as the request body."
    )
    tools_exercised.append(replace_tool)
    step_num += 1

    # GET again to verify
    all_steps.append(
        f"{step_num}. **List** again using `{list_tool}` — verify nothing changed"
    )
    step_num += 1

    return step_num


def generate_bulk_delete_steps(
    ep: dict,
    tool_map: dict,
    step_num: int,
    all_steps: list[str],
    tools_exercised: list[str],
) -> int:
    """Generate bulk delete steps: create resource → list → bulk DELETE → verify. Returns next step number."""
    plural_path = ep["path"]
    singular_path = ep.get("singular_path", plural_path.rstrip("s"))  # Heuristic: remove trailing 's'
    notes = ep.get("notes", "")
    create_values = ep.get("create_values", {})
    parent_note = ""
    if ep.get("parent"):
        parent_note = f" (use parent_id from the parent resource)"

    extra_note = f" ({notes})" if notes else ""

    # Find tools
    delete_plural_tool = get_tool_name(tool_map, plural_path, "delete")
    list_tool = get_tool_name(tool_map, plural_path, "get")
    create_tool = get_tool_name(tool_map, singular_path, "post")

    # Step 1: Create a resource via singular POST (if create_values provided)
    if create_values:
        vals_str = format_values(create_values, indent=2)
        all_steps.append(
            f"{step_num}. **Create** a test resource using `{create_tool}` with `confirm=True`{parent_note}:\n{vals_str}"
        )
        tools_exercised.append(create_tool)
        step_num += 1

    # Step 2: List to verify it exists
    all_steps.append(
        f"{step_num}. **List** using `{list_tool}` — verify resource exists{extra_note}"
    )
    tools_exercised.append(list_tool)
    step_num += 1

    # Step 3: Bulk delete — must use query parameter for filtering
    # (API requires at least one content-filtering query param for mass deletion)
    filter_field = ep.get("filter_field", "")
    filter_value = ep.get("filter_value", "")
    if filter_field and filter_value:
        query_hint = f', `query={{"{filter_field}": "{filter_value}"}}`'
    else:
        query_hint = " — use `query` parameter to filter (e.g., `query={\"id\": \"<id>\"}` where `<id>` is the ID of the created resource from step 1, or use any field filter like `query={\"name\": \"<name>\"}` from the list results)"
    all_steps.append(
        f"{step_num}. **Bulk delete** using `{delete_plural_tool}` with `confirm=True`{query_hint}"
    )
    tools_exercised.append(delete_plural_tool)
    step_num += 1

    # Step 4: List again to verify empty
    all_steps.append(
        f"{step_num}. **List** using `{list_tool}` — verify collection is empty"
    )
    step_num += 1

    return step_num


def generate_adversarial_task(task: dict, task_num: str) -> str:
    """Generate an adversarial task file."""
    title = task["title"]
    test_cases = task.get("test_cases", [])

    lines = [
        f"## Task {task_num}: {title}",
        "",
        f"**task_id**: {task_num}-adversarial-{title.lower().replace(' ', '-').replace('—', '').replace(',', '')[:40]}",
        "",
        f"**Objective**: Test error handling by intentionally sending bad inputs across multiple endpoints.",
        "",
        "**Instructions**: For each test case below, make the API call exactly as specified. Record the error response quality: does it clearly explain what went wrong? Does it suggest the correct values?",
        "",
        "**Steps**:",
    ]

    for i, tc in enumerate(test_cases, 1):
        tool = tc["tool"]
        desc = tc["description"]
        params = tc.get("params", {})
        expected = tc.get("expected", "error")
        params_str = ", ".join(f"`{k}={repr(v)}`" for k, v in params.items())
        lines.append(f"{i}. **{desc}**: Call `{tool}` with {params_str}")
        lines.append(f"   - Expected: {expected}")
        lines.append(f"   - Rate error message quality: clear/unclear/missing")

    lines.extend([
        "",
        "**Expected outcome**: All calls should fail with clear error messages. No resources should be created.",
        "",
        "**Cleanup**: None needed (all calls should fail).",
        "",
    ])

    return "\n".join(lines)


def generate_systematic_task(task: dict, tool_map: dict, task_num: str) -> str:
    """Generate a systematic subsystem-coverage task file."""
    title = task["title"]
    endpoints = task.get("endpoints", [])
    notes = task.get("notes", "")
    skips = task.get("skip", [])

    task_id_suffix = title.lower()
    for char in "— ,&()/'":
        task_id_suffix = task_id_suffix.replace(char, "-")
    task_id_suffix = task_id_suffix.replace("--", "-").strip("-")[:50]

    all_steps: list[str] = []
    cleanup_steps: list[str] = []
    tools_exercised: list[str] = []
    step_num = 1

    # Process endpoints in order
    for ep in endpoints:
        ep_type = None
        if ep.get("crud", False):
            ep_type = "crud"
        elif ep.get("settings", False):
            ep_type = "settings"
        elif ep.get("apply", False):
            ep_type = "apply"
        elif ep.get("action", False):
            ep_type = "action"
        elif ep.get("read_only", False):
            ep_type = "read_only"
        elif ep.get("replace", False):
            ep_type = "replace"
        elif ep.get("bulk_delete", False):
            ep_type = "bulk_delete"
        elif ep.get("setup_only", False):
            ep_type = "crud"  # Use CRUD generator but with setup_only flag

        if ep_type == "crud":
            step_num = generate_crud_steps(
                task, ep, tool_map, step_num, all_steps, cleanup_steps, tools_exercised
            )
        elif ep_type == "settings":
            step_num = generate_settings_steps(
                ep, tool_map, step_num, all_steps, tools_exercised
            )
        elif ep_type == "apply":
            step_num = generate_apply_steps(
                ep, tool_map, step_num, all_steps, tools_exercised
            )
        elif ep_type == "action":
            step_num = generate_action_steps(
                ep, tool_map, step_num, all_steps, tools_exercised
            )
        elif ep_type == "read_only":
            step_num = generate_read_only_steps(
                ep, tool_map, step_num, all_steps, tools_exercised
            )
        elif ep_type == "replace":
            step_num = generate_replace_steps(
                ep, tool_map, step_num, all_steps, tools_exercised
            )
        elif ep_type == "bulk_delete":
            step_num = generate_bulk_delete_steps(
                ep, tool_map, step_num, all_steps, tools_exercised
            )

    # Add adversarial subtasks if present
    adversarial = task.get("adversarial", [])
    if adversarial:
        all_steps.append("")
        all_steps.append("**Adversarial subtasks** (attempt once, record error quality):")
        for adv in adversarial:
            step_num += 1
            all_steps.append(f"{step_num}. {adv['description']}")

    # Deduplicate tools
    unique_tools = list(dict.fromkeys(tools_exercised))

    # Build the markdown
    lines = [
        f"## Task {task_num}: {title}",
        "",
        f"**task_id**: {task_num}-{task_id_suffix}",
        "",
        f"**Objective**: Exercise all tools in the {task.get('subsystem', 'unknown')} subsystem through CRUD lifecycle, settings, and actions.",
        "",
        f"**Tools to exercise** ({len(unique_tools)}):",
    ]
    for t in unique_tools:
        lines.append(f"- `{t}`")

    lines.extend([
        "",
        "**Steps**:",
    ])
    lines.extend(all_steps)

    if notes:
        lines.extend([
            "",
            "**Important notes**:",
            notes.strip(),
        ])

    if skips:
        lines.extend([
            "",
            "**Skipped endpoints**:",
        ])
        for s in skips:
            lines.append(f"- `{s['path']}` — {s.get('reason', 'no reason given')}")

    lines.extend([
        "",
        "**Cleanup** (reverse order):",
    ])
    if cleanup_steps:
        lines.extend(cleanup_steps)
    else:
        lines.append("- No cleanup needed (read-only / settings restored)")

    lines.extend([
        "",
        f"**Expected outcome**: All {len(unique_tools)} tools exercised successfully.",
        "",
    ])

    return "\n".join(lines)


def generate_destructive_task(task: dict, task_num: str) -> str:
    """Generate the destructive opt-in task."""
    title = task["title"]
    notes = task.get("notes", "")

    lines = [
        f"## Task {task_num}: {title}",
        "",
        f"**task_id**: {task_num}-destructive",
        "",
        "**Objective**: Test destructive operations (reboot, halt). Only run with INCLUDE_DESTRUCTIVE=1.",
        "",
        "**Steps**:",
        "1. Call `pfsense_post_diagnostics_reboot` with `confirm=True`",
        "2. Wait 90 seconds for API to come back",
        "3. Verify API is responding by calling `pfsense_get_system_version`",
        "4. Call `pfsense_post_diagnostics_halt_system` with `confirm=True`",
        "",
        "**Important notes**:",
        notes.strip() if notes else "This will terminate the VM.",
        "",
        "**Cleanup**: None (VM will be destroyed after halt).",
        "",
        "**Expected outcome**: Reboot completes and API returns. Halt stops the VM.",
        "",
    ]
    return "\n".join(lines)


def main():
    """Generate all task files."""
    print("Loading OpenAPI spec...")
    spec = load_spec(SPEC_PATH)

    print("Building tool name map...")
    tool_map = build_tool_name_map(spec)
    total_tools = sum(len(methods) for methods in tool_map.values())
    print(f"  {total_tools} tools across {len(tool_map)} paths")

    print("Loading task config...")
    tasks = load_config()
    print(f"  {len(tasks)} tasks defined")

    # Don't delete existing tasks 01-09
    generated_count = 0
    all_tools_exercised: set[str] = set()

    for task in tasks:
        num = task["number"]
        task_num = f"{num:02d}"

        if task.get("adversarial_only"):
            content = generate_adversarial_task(task, task_num)
        elif task.get("destructive"):
            content = generate_destructive_task(task, task_num)
        else:
            content = generate_systematic_task(task, tool_map, task_num)

        # Extract tools from content for coverage tracking
        for match in re.finditer(r"`(pfsense_\w+)`", content):
            all_tools_exercised.add(match.group(1))

        output_path = TASKS_DIR / f"{task_num}-{task['title'].lower().replace(' ', '-').replace('—', '-').replace(',', '').replace('/', '-').replace('&', 'and')[:60]}.md"
        output_path.write_text(content)
        generated_count += 1
        print(f"  Generated: {output_path.name}")

    print(f"\nGenerated {generated_count} task files")
    print(f"Tools referenced: {len(all_tools_exercised)} / {total_tools}")
    print(f"Coverage estimate: {len(all_tools_exercised) / total_tools * 100:.1f}%")


if __name__ == "__main__":
    main()
