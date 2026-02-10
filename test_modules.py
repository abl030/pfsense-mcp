"""
Spec-derived test suite for PFSENSE_MODULES and PFSENSE_READ_ONLY gating.

All expected values are derived from openapi-spec.json + the module mapping
in context_builder.py — zero hardcoded counts. When the spec changes,
regenerate the server and re-run: tests auto-adapt.

Usage:
    nix develop -c python -m pytest test_modules.py -v
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from generator.context_builder import MODULE_ORDER, _ALL_MODULES, build_tool_contexts
from generator.loader import load_spec

_REPO_ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Derive expected values from spec
# ---------------------------------------------------------------------------

_spec = load_spec(_REPO_ROOT / "openapi-spec.json")
_contexts = build_tool_contexts(_spec)

ALWAYS_ON = 3  # pfsense_report_issue + pfsense_get_overview + pfsense_search_tools — never gated

MODULE_COUNTS: dict[str, dict[str, int]] = {}
for _mod in MODULE_ORDER:
    _reads = sum(1 for c in _contexts if c.module == _mod and not c.is_mutation)
    _writes = sum(1 for c in _contexts if c.module == _mod and c.is_mutation)
    MODULE_COUNTS[_mod] = {"read": _reads, "write": _writes, "total": _reads + _writes}

TOTAL = sum(mc["total"] for mc in MODULE_COUNTS.values()) + ALWAYS_ON

# Sanity: we expect 677 — if the spec changes, this adapts automatically
assert TOTAL == len(_contexts) + ALWAYS_ON

# ---------------------------------------------------------------------------
# Subprocess helper — import generated server with specific env vars
# ---------------------------------------------------------------------------

_HELPER = """\
import os, sys, json
os.environ["PFSENSE_MODULES"] = sys.argv[1]
if len(sys.argv) > 2:
    os.environ["PFSENSE_READ_ONLY"] = sys.argv[2]
os.environ.setdefault("PFSENSE_HOST", "https://127.0.0.1")
os.environ.setdefault("PFSENSE_API_KEY", "test")
sys.path.insert(0, "generated")
import server as srv
tools = srv.mcp._tool_manager._tools
names = sorted(tools.keys())
print(json.dumps({"count": len(names), "names": names}))
"""


def _get_tools(modules: str, read_only: str | None = None) -> dict:
    """Launch a subprocess with the given env vars and return tool info."""
    cmd = [sys.executable, "-c", _HELPER, modules]
    if read_only is not None:
        cmd.append(read_only)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent),
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Helper failed:\n{result.stderr}")
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# TestModuleCounts — verify tool registration counts
# ---------------------------------------------------------------------------


class TestModuleCounts:
    """Verify that PFSENSE_MODULES controls tool counts correctly."""

    def test_default_all_modules(self):
        """No env var (all modules) → all tools registered."""
        all_mods = ",".join(sorted(_ALL_MODULES))
        info = _get_tools(all_mods)
        assert info["count"] == TOTAL

    def test_empty_string(self):
        """Empty PFSENSE_MODULES → only always-on tools."""
        info = _get_tools("")
        assert info["count"] == ALWAYS_ON
        assert "pfsense_report_issue" in info["names"]
        assert "pfsense_get_overview" in info["names"]
        assert "pfsense_search_tools" in info["names"]

    @pytest.mark.parametrize("mod", MODULE_ORDER)
    def test_single_module(self, mod: str):
        """Each module alone → expected count + always-on."""
        info = _get_tools(mod)
        expected = MODULE_COUNTS[mod]["total"] + ALWAYS_ON
        assert info["count"] == expected, (
            f"Module {mod}: expected {expected}, got {info['count']}"
        )

    def test_all_individual_equals_total(self):
        """All modules comma-joined equals total tool count."""
        all_mods = ",".join(MODULE_ORDER)
        info = _get_tools(all_mods)
        assert info["count"] == TOTAL

    def test_multi_module_combo(self):
        """Arbitrary subset: sum of module counts + always-on."""
        subset = ["firewall", "status", "diagnostics"]
        expected = sum(MODULE_COUNTS[m]["total"] for m in subset) + ALWAYS_ON
        info = _get_tools(",".join(subset))
        assert info["count"] == expected

    def test_whitespace_tolerance(self):
        """Whitespace around module names is stripped."""
        info = _get_tools(" firewall , status ")
        expected = MODULE_COUNTS["firewall"]["total"] + MODULE_COUNTS["status"]["total"] + ALWAYS_ON
        assert info["count"] == expected


# ---------------------------------------------------------------------------
# TestReadOnly — verify mutation stripping
# ---------------------------------------------------------------------------


class TestReadOnly:
    """Verify that PFSENSE_READ_ONLY strips mutation tools."""

    def test_read_only_all_modules(self):
        """All modules + READ_ONLY → only GET tools + always-on."""
        all_mods = ",".join(sorted(_ALL_MODULES))
        info = _get_tools(all_mods, "true")
        expected_reads = sum(mc["read"] for mc in MODULE_COUNTS.values()) + ALWAYS_ON
        assert info["count"] == expected_reads

    @pytest.mark.parametrize("mod", MODULE_ORDER)
    def test_read_only_single_module(self, mod: str):
        """Each module in read-only → only reads + always-on."""
        info = _get_tools(mod, "true")
        expected = MODULE_COUNTS[mod]["read"] + ALWAYS_ON
        assert info["count"] == expected, (
            f"Module {mod} read-only: expected {expected}, got {info['count']}"
        )

    def test_read_only_false(self):
        """Explicit 'false' → all tools (same as default)."""
        all_mods = ",".join(sorted(_ALL_MODULES))
        info = _get_tools(all_mods, "false")
        assert info["count"] == TOTAL


# ---------------------------------------------------------------------------
# TestToolPresence — verify correct tools per module
# ---------------------------------------------------------------------------


class TestToolPresence:
    """Verify the right tools are registered for each configuration."""

    def test_always_on_everywhere(self):
        """Always-on tools are present in every configuration."""
        _always_on = {"pfsense_report_issue", "pfsense_get_overview", "pfsense_search_tools"}

        # Empty modules
        info = _get_tools("")
        assert _always_on <= set(info["names"])

        # Single module
        info = _get_tools("firewall")
        assert _always_on <= set(info["names"])

        # Read-only
        info = _get_tools("status", "true")
        assert _always_on <= set(info["names"])

    @pytest.mark.parametrize("mod", MODULE_ORDER)
    def test_module_tools_present(self, mod: str):
        """Each module's tools are present when that module is loaded."""
        info = _get_tools(mod)
        tool_set = set(info["names"])
        expected_tools = {c.tool_name for c in _contexts if c.module == mod}
        missing = expected_tools - tool_set
        assert not missing, f"Module {mod} missing tools: {missing}"

    @pytest.mark.parametrize("mod", MODULE_ORDER)
    def test_module_excludes_others(self, mod: str):
        """Loading one module doesn't leak tools from other modules."""
        info = _get_tools(mod)
        tool_set = set(info["names"]) - {"pfsense_report_issue", "pfsense_get_overview", "pfsense_search_tools"}
        expected_tools = {c.tool_name for c in _contexts if c.module == mod}
        extra = tool_set - expected_tools
        assert not extra, f"Module {mod} has extra tools: {extra}"

    def test_no_duplicates(self):
        """No tool is registered twice."""
        all_mods = ",".join(sorted(_ALL_MODULES))
        info = _get_tools(all_mods)
        assert len(info["names"]) == len(set(info["names"]))
