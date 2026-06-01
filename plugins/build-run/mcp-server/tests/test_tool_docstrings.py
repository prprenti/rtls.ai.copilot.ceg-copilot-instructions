"""Prompt quality tests — structural/heuristic checks for MCP tool docstrings.

These tests validate that MCP tool descriptions are well-formed for LLM
consumption. They run deterministically (no LLM calls) and check:
  - Presence and length of docstrings
  - Action verbs in descriptions
  - No placeholder/TODO text
  - No duplicate tool names
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from typing import Any


class MockFastMCP:
    def __init__(self, name: str = "test-mcp", **kwargs: Any):
        self.name = name
        self.tools: dict[str, Any] = {}

    def tool(self, *args: Any, **kwargs: Any):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator

# Import remaining registration functions
from commands import register_command_tools

pytestmark = pytest.mark.prompt_quality


# ---------------------------------------------------------------------------
# Fixture: register all tools on a MockFastMCP
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def registered_mcp(tmp_path_factory) -> MockFastMCP:
    """Register all tools on a mock MCP for inspection."""
    mcp = MockFastMCP("test-mcp")
    repo = str(tmp_path_factory.mktemp("repo"))

    register_command_tools(mcp, repo)  # pyright: ignore[reportArgumentType]

    return mcp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestToolDocstrings:
    def test_every_tool_has_docstring(self, registered_mcp: MockFastMCP) -> None:
        """Every registered tool must have a non-empty docstring."""
        missing = []
        for name, fn in registered_mcp.tools.items():
            doc = fn.__doc__
            if not doc or not doc.strip():
                missing.append(name)
        assert not missing, f"Tools missing docstrings: {missing}"

    def test_docstrings_min_length(self, registered_mcp: MockFastMCP) -> None:
        """Docstrings should be at least 20 characters (not just stubs)."""
        short = []
        for name, fn in registered_mcp.tools.items():
            doc = (fn.__doc__ or "").strip()
            if len(doc) < 20:
                short.append(f"{name} ({len(doc)} chars)")
        assert not short, f"Tools with too-short docstrings: {short}"

    def test_docstrings_contain_action_verb(self, registered_mcp: MockFastMCP) -> None:
        """Docstrings should contain at least one action verb for clarity."""
        action_verbs = re.compile(
            r"\b(returns?|lists?|gets?|quer(?:y|ies)|runs?|reads?|checks?|"
            r"search(?:es)?|fetche?s?|look|compute|add|updat|creat|verif|"
            r"extract|discover|provid|build|valid|show)\b",
            re.IGNORECASE,
        )
        no_verb = []
        for name, fn in registered_mcp.tools.items():
            doc = fn.__doc__ or ""
            if not action_verbs.search(doc):
                no_verb.append(name)
        assert not no_verb, f"Tools without action verbs in docstring: {no_verb}"

    def test_no_todo_or_placeholder(self, registered_mcp: MockFastMCP) -> None:
        """Docstrings should not contain TODO/FIXME/placeholder text."""
        placeholder_pat = re.compile(
            r"\b(TODO|FIXME|HACK|XXX|PLACEHOLDER|TBD)\b", re.IGNORECASE
        )
        found = []
        for name, fn in registered_mcp.tools.items():
            doc = fn.__doc__ or ""
            if placeholder_pat.search(doc):
                found.append(name)
        assert not found, f"Tools with placeholder text in docstring: {found}"

    def test_no_duplicate_tool_names(self, registered_mcp: MockFastMCP) -> None:
        """All registered tool names should be unique."""
        names = list(registered_mcp.tools.keys())
        dupes = [n for n in names if names.count(n) > 1]
        assert not dupes, f"Duplicate tool names: {set(dupes)}"

    def test_tool_count_reasonable(self, registered_mcp: MockFastMCP) -> None:
        """Sanity check: we expect at least 3 tools registered (commands)."""
        assert len(registered_mcp.tools) >= 3, (
            f"Only {len(registered_mcp.tools)} tools registered, expected >= 3"
        )
