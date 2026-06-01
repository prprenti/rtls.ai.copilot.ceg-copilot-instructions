"""Tests for server.py — MCP server entry point."""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _fake_mcp_modules() -> dict[str, types.ModuleType]:
    mcp_module = types.ModuleType("mcp")
    server_module = types.ModuleType("mcp.server")
    fastmcp_module = types.ModuleType("mcp.server.fastmcp")
    fastmcp_module.FastMCP = MagicMock() # pyright: ignore[reportAttributeAccessIssue]
    server_module.fastmcp = fastmcp_module # pyright: ignore[reportAttributeAccessIssue]
    mcp_module.server = server_module # pyright: ignore[reportAttributeAccessIssue]
    return {
        "mcp": mcp_module,
        "mcp.server": server_module,
        "mcp.server.fastmcp": fastmcp_module,
    }


def _import_tool_modules() -> None:
    import importlib

    for module_name in [
        "commands",
    ]:
        importlib.import_module(module_name)


def _reload_server_module():
    import importlib

    sys.modules.pop("server_build_run", None)
    return importlib.import_module("server_build_run")


# ===================================================================
# REPO_ROOT computation
# ===================================================================

class TestRepoRoot:
    def test_repo_root_ignores_workarea(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """PLUGIN_ROOT is always derived from __file__, not $WORKAREA."""
        monkeypatch.setenv("WORKAREA", "/custom/workarea")
        with patch.dict(sys.modules, _fake_mcp_modules()):
            _import_tool_modules()
            with patch("mcp.server.fastmcp.FastMCP"):
                with patch("commands.register_command_tools"):
                    srv_mod = _reload_server_module()
                    # Must NOT follow WORKAREA — always derived from __file__
                    assert srv_mod.PLUGIN_ROOT != "/custom/workarea"
                    assert os.path.isabs(srv_mod.PLUGIN_ROOT)

    def test_repo_root_is_parent_of_plugins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("WORKAREA", raising=False)
        with patch.dict(sys.modules, _fake_mcp_modules()):
            _import_tool_modules()
            with patch("mcp.server.fastmcp.FastMCP"):
                with patch("commands.register_command_tools"):
                    srv_mod = _reload_server_module()
                    assert os.path.isabs(srv_mod.PLUGIN_ROOT)
                    # mcp-server/ should be a child of PLUGIN_ROOT
                    assert os.path.isdir(
                        os.path.join(srv_mod.PLUGIN_ROOT, "mcp-server")
                    )


# ===================================================================
# register functions called
# ===================================================================

class TestRegistration:
    def test_all_register_functions_called(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WORKAREA", "/tmp/test")
        mock_register = MagicMock()

        with patch.dict(sys.modules, _fake_mcp_modules()):
            _import_tool_modules()
            with patch("mcp.server.fastmcp.FastMCP"):
                with patch("commands.register_command_tools", mock_register):
                    _reload_server_module()

        mock_register.assert_called_once()


# ===================================================================
# main() entry point
# ===================================================================

class TestMain:
    def test_main_calls_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WORKAREA", "/tmp/test")
        mock_fastmcp = MagicMock()
        with patch.dict(sys.modules, _fake_mcp_modules()):
            _import_tool_modules()
            with patch("mcp.server.fastmcp.FastMCP", return_value=mock_fastmcp):
                with patch("commands.register_command_tools"):
                    srv_mod = _reload_server_module()
                    srv_mod.main()
                    mock_fastmcp.run.assert_called_once_with(transport="stdio")
