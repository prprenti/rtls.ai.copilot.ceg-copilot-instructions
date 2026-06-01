"""Tests for validation plugin — tools/register_topology.py (crifd_query)."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from register_topology import register_register_topology_tools
from typing import Any
from unittest.mock import MagicMock


class MockFastMCP:
    def __init__(self, name: str = "test-mcp", **kwargs: Any):
        self.name = name
        self.tools: dict[str, Any] = {}

    def tool(self, *args: Any, **kwargs: Any):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


def make_async_process(stdout: str = "", stderr: str = "", returncode: int = 0):
    proc = AsyncMock()
    proc.communicate = AsyncMock(return_value=(stdout.encode(), stderr.encode()))
    proc.returncode = returncode
    proc.kill = MagicMock()
    proc.wait = AsyncMock()
    return proc


class TestCrifdQueryTool:
    @pytest.fixture(autouse=True)
    def setup_mcp(self, tmp_path: Path) -> None:
        self.repo_root = tmp_path
        self.mcp = MockFastMCP()
        register_register_topology_tools(self.mcp, str(tmp_path))

    def _create_helper_stub(self) -> None:
        skills_dir = self.repo_root / "skills" / "register-topology"
        skills_dir.mkdir(parents=True, exist_ok=True)
        (skills_dir / "crifd_query.py").write_text("# stub")

    def test_missing_helper_script(self) -> None:
        result = asyncio.run(
            self.mcp.tools["crifd_query"](crif="test.xml", query="REG0")
        )
        assert "not found" in result.lower()

    def test_successful_query(self) -> None:
        self._create_helper_stub()

        with patch(
            "register_topology._run_helper_json",
            return_value='{"registers": [{"name": "REG0"}]}',
        ):
            result = asyncio.run(
                self.mcp.tools["crifd_query"](crif="test.xml", query="REG0")
            )
            assert "REG0" in result

    def test_mutually_exclusive_flags(self) -> None:
        self._create_helper_stub()

        result = asyncio.run(
            self.mcp.tools["crifd_query"](
                crif="test.xml", query="REG0", exact=True, regex=True
            )
        )
        assert "mutually exclusive" in result

    def test_negative_limit(self) -> None:
        self._create_helper_stub()
        result = asyncio.run(
            self.mcp.tools["crifd_query"](crif="test.xml", query="REG0", limit=-1)
        )
        assert "limit must be >= 0" in result

    def test_negative_indent(self) -> None:
        self._create_helper_stub()
        result = asyncio.run(
            self.mcp.tools["crifd_query"](crif="test.xml", query="REG0", indent=-1)
        )
        assert "indent must be >= 0" in result

    def test_zero_timeout(self) -> None:
        self._create_helper_stub()
        result = asyncio.run(
            self.mcp.tools["crifd_query"](crif="test.xml", query="REG0", timeout=0)
        )
        assert "timeout must be > 0" in result

    def test_exact_flag_passed(self) -> None:
        self._create_helper_stub()

        with patch(
            "register_topology._run_helper_json",
            return_value="{}",
        ) as mock_run:
            asyncio.run(
                self.mcp.tools["crifd_query"](
                    crif="test.xml", query="REG0", exact=True
                )
            )
            cmd = mock_run.call_args[0][0]
            assert "--exact" in cmd
