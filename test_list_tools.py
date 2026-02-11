"""
Tests for list tool field selection, row filtering, and known-fields docstrings.

Verifies that:
1. _filter_response() correctly filters fields and rows
2. All pfsense_list_* tools have fields/query params in their signature
3. List tools with array responses have "Known fields" in their docstring
4. extract_response_fields() works correctly against the spec

Usage:
    nix develop -c python -m pytest test_list_tools.py -v
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from generator.context_builder import build_tool_contexts
from generator.loader import load_spec

_REPO_ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Load spec and contexts once
# ---------------------------------------------------------------------------

_spec = load_spec(_REPO_ROOT / "openapi-spec.json")
_contexts = build_tool_contexts(_spec)
_list_contexts = [c for c in _contexts if c.is_list_tool]


# ---------------------------------------------------------------------------
# Test _filter_response helper (imported from generated server)
# ---------------------------------------------------------------------------


class TestFilterResponse:
    """Test the _filter_response helper function."""

    @staticmethod
    def _get_filter_fn():
        """Import _filter_response from the generated server."""
        import importlib
        import os

        os.environ.setdefault("PFSENSE_HOST", "https://127.0.0.1")
        os.environ.setdefault("PFSENSE_API_KEY", "test")
        sys.path.insert(0, str(_REPO_ROOT / "generated"))
        mod = importlib.import_module("server")
        return mod._filter_response

    def test_passthrough_non_list(self):
        fn = self._get_filter_fn()
        result = {"key": "value"}
        assert fn(result, None, None) == {"key": "value"}

    def test_passthrough_no_filters(self):
        fn = self._get_filter_fn()
        data = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        assert fn(data, None, None) == data

    def test_field_selection(self):
        fn = self._get_filter_fn()
        data = [
            {"id": 1, "name": "a", "address": "10.0.0.1", "type": "host"},
            {"id": 2, "name": "b", "address": "10.0.0.2", "type": "network"},
        ]
        result = fn(data, "name,address", None)
        assert result == [
            {"id": 1, "name": "a", "address": "10.0.0.1"},
            {"id": 2, "name": "b", "address": "10.0.0.2"},
        ]

    def test_field_selection_always_includes_id(self):
        fn = self._get_filter_fn()
        data = [{"id": 1, "name": "a", "extra": "x"}]
        result = fn(data, "name", None)
        assert result == [{"id": 1, "name": "a"}]

    def test_field_selection_whitespace(self):
        fn = self._get_filter_fn()
        data = [{"id": 1, "name": "a", "type": "host"}]
        result = fn(data, " name , type ", None)
        assert result == [{"id": 1, "name": "a", "type": "host"}]

    def test_query_filter(self):
        fn = self._get_filter_fn()
        data = [
            {"id": 1, "name": "a", "type": "host"},
            {"id": 2, "name": "b", "type": "network"},
            {"id": 3, "name": "c", "type": "host"},
        ]
        result = fn(data, None, {"type": "host"})
        assert result == [
            {"id": 1, "name": "a", "type": "host"},
            {"id": 3, "name": "c", "type": "host"},
        ]

    def test_query_filter_multiple_keys(self):
        fn = self._get_filter_fn()
        data = [
            {"id": 1, "name": "a", "type": "host"},
            {"id": 2, "name": "b", "type": "host"},
        ]
        result = fn(data, None, {"type": "host", "name": "a"})
        assert result == [{"id": 1, "name": "a", "type": "host"}]

    def test_query_filter_string_coercion(self):
        """Query values are compared as strings, matching API behavior."""
        fn = self._get_filter_fn()
        data = [{"id": 1, "port": 443}, {"id": 2, "port": 80}]
        result = fn(data, None, {"port": "443"})
        assert result == [{"id": 1, "port": 443}]

    def test_combined_query_and_fields(self):
        fn = self._get_filter_fn()
        data = [
            {"id": 1, "name": "a", "type": "host", "address": "10.0.0.1"},
            {"id": 2, "name": "b", "type": "network", "address": "10.0.0.0/24"},
        ]
        result = fn(data, "name,address", {"type": "host"})
        assert result == [{"id": 1, "name": "a", "address": "10.0.0.1"}]

    def test_query_no_match(self):
        fn = self._get_filter_fn()
        data = [{"id": 1, "name": "a"}]
        result = fn(data, None, {"name": "nonexistent"})
        assert result == []

    def test_error_response_passthrough(self):
        """Non-list results (error dicts) pass through unchanged."""
        fn = self._get_filter_fn()
        error = {"code": 401, "message": "Unauthorized"}
        assert fn(error, "name", {"type": "host"}) == error


# ---------------------------------------------------------------------------
# Test extract_response_fields
# ---------------------------------------------------------------------------


class TestExtractResponseFields:
    """Test extract_response_fields against the live spec."""

    def test_returns_sorted_fields_for_list_endpoint(self):
        """A known list endpoint (firewall aliases) returns sorted fields."""
        list_ops = [
            c for c in _list_contexts
            if c.tool_name == "pfsense_list_firewall_aliases"
        ]
        assert len(list_ops) == 1
        ctx = list_ops[0]
        assert ctx.response_fields is not None
        assert ctx.response_fields == sorted(ctx.response_fields)
        assert "id" in ctx.response_fields
        assert "name" in ctx.response_fields

    def test_108_list_tools_have_fields(self):
        """108 of 109 list tools should have extractable response fields."""
        with_fields = [c for c in _list_contexts if c.response_fields]
        assert len(with_fields) == 108

    def test_109_list_tools_detected(self):
        """Should detect exactly 109 list tools."""
        assert len(_list_contexts) == 109


# ---------------------------------------------------------------------------
# Test generated code structure (via subprocess to control env)
# ---------------------------------------------------------------------------

_HELPER = """\
import os, sys, json, inspect
os.environ["PFSENSE_MODULES"] = sys.argv[1]
os.environ.setdefault("PFSENSE_HOST", "https://127.0.0.1")
os.environ.setdefault("PFSENSE_API_KEY", "test")
sys.path.insert(0, "generated")
import server as srv
tools = srv.mcp._tool_manager._tools

list_tools = {n: t for n, t in tools.items() if n.startswith("pfsense_list_")}
results = {}
for name, tool in list_tools.items():
    fn = tool.fn
    sig = inspect.signature(fn)
    params = list(sig.parameters.keys())
    source = inspect.getsource(fn)
    results[name] = {
        "has_fields": "fields" in params,
        "has_query": "query" in params,
        "has_filter_call": "_filter_response" in source,
        "has_known_fields": "Known fields:" in (fn.__doc__ or ""),
    }
print(json.dumps(results))
"""


def _get_list_tool_info() -> dict:
    """Get structural info about list tools from the generated server."""
    from generator.context_builder import _ALL_MODULES

    all_mods = ",".join(sorted(_ALL_MODULES))
    result = subprocess.run(
        [sys.executable, "-c", _HELPER, all_mods],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Helper failed:\n{result.stderr}")
    return json.loads(result.stdout)


class TestGeneratedListTools:
    """Verify generated list tools have the correct structure."""

    @pytest.fixture(scope="class")
    def tool_info(self):
        return _get_list_tool_info()

    def test_all_list_tools_have_fields_param(self, tool_info):
        missing = [n for n, info in tool_info.items() if not info["has_fields"]]
        assert not missing, f"List tools missing 'fields' param: {missing}"

    def test_all_list_tools_have_query_param(self, tool_info):
        missing = [n for n, info in tool_info.items() if not info["has_query"]]
        assert not missing, f"List tools missing 'query' param: {missing}"

    def test_all_list_tools_call_filter_response(self, tool_info):
        missing = [n for n, info in tool_info.items() if not info["has_filter_call"]]
        assert not missing, f"List tools missing _filter_response call: {missing}"

    def test_most_list_tools_have_known_fields(self, tool_info):
        """108 of 109 list tools should have Known fields in docstring."""
        with_fields = sum(1 for info in tool_info.values() if info["has_known_fields"])
        assert with_fields == 108

    def test_list_tool_count(self, tool_info):
        assert len(tool_info) == 109
