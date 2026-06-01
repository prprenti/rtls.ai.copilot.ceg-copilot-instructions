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
    yaml_module = types.ModuleType("yaml")
    yaml_module.safe_load = lambda *args, **kwargs: {} # pyright: ignore[reportAttributeAccessIssue]
    return {
        "mcp": mcp_module,
        "mcp.server": server_module,
        "mcp.server.fastmcp": fastmcp_module,
        "yaml": yaml_module,
    }


def _import_tool_modules() -> None:
    import importlib

    for module_name in [
        "tools.skills",
        "tools.commands",
        "tools.apis",
        "tools.context",
        "tools.hsd",
        "tools.gatekeeper",
        "tools.vmanager",
        "tools.submcp",
    ]:
        importlib.import_module(module_name)


def _reload_server_module():
    import importlib

    sys.modules.pop("server", None)
    return importlib.import_module("server")


# ===================================================================
# REPO_ROOT computation
# ===================================================================

class TestRepoRoot:
    def test_repo_root_ignores_workarea(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """REPO_ROOT is always derived from __file__, not $WORKAREA."""
        monkeypatch.setenv("WORKAREA", "/custom/workarea")
        with patch.dict(sys.modules, _fake_mcp_modules()):
            _import_tool_modules()
            with patch("mcp.server.fastmcp.FastMCP"):
                with patch("tools.skills.register_skills_tools"):
                    with patch("tools.commands.register_command_tools"):
                        with patch("tools.apis.register_api_tools"):
                            with patch("tools.context.register_context_tools"):
                                with patch("tools.hsd.register_hsd_tools"):
                                    with patch("tools.gatekeeper.register_gatekeeper_tools"):
                                        with patch("tools.vmanager.register_vmanager_tools"):
                                            with patch("tools.submcp.register_submcp_tools"):
                                                srv_mod = _reload_server_module()
                                                # Must NOT follow WORKAREA — always parent of ddgmcp/
                                                assert srv_mod.REPO_ROOT != "/custom/workarea"
                                                assert os.path.isabs(srv_mod.REPO_ROOT)

    def test_repo_root_is_parent_of_ddgmcp(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("WORKAREA", raising=False)
        with patch.dict(sys.modules, _fake_mcp_modules()):
            _import_tool_modules()
            with patch("mcp.server.fastmcp.FastMCP"):
                with patch("tools.skills.register_skills_tools"):
                    with patch("tools.commands.register_command_tools"):
                        with patch("tools.apis.register_api_tools"):
                            with patch("tools.context.register_context_tools"):
                                with patch("tools.hsd.register_hsd_tools"):
                                    with patch("tools.gatekeeper.register_gatekeeper_tools"):
                                        with patch("tools.vmanager.register_vmanager_tools"):
                                            with patch("tools.submcp.register_submcp_tools"):
                                                srv_mod = _reload_server_module()
                                                assert os.path.isabs(srv_mod.REPO_ROOT)
                                                # ddgmcp/ should be a child of REPO_ROOT
                                                assert os.path.isdir(
                                                    os.path.join(srv_mod.REPO_ROOT, "ddgmcp")
                                                )


# ===================================================================
# register functions called
# ===================================================================

class TestRegistration:
    def test_all_register_functions_called(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WORKAREA", "/tmp/test")
        mocks = {}
        for name in [
            "tools.skills.register_skills_tools",
            "tools.commands.register_command_tools",
            "tools.apis.register_api_tools",
            "tools.context.register_context_tools",
            "tools.hsd.register_hsd_tools",
            "tools.gatekeeper.register_gatekeeper_tools",
            "tools.vmanager.register_vmanager_tools",
            "tools.submcp.register_submcp_tools",
        ]:
            mocks[name] = MagicMock()

        with patch.dict(sys.modules, _fake_mcp_modules()):
            _import_tool_modules()
            with patch("mcp.server.fastmcp.FastMCP"):
                with patch("tools.skills.register_skills_tools", mocks["tools.skills.register_skills_tools"]):
                    with patch("tools.commands.register_command_tools", mocks["tools.commands.register_command_tools"]):
                        with patch("tools.apis.register_api_tools", mocks["tools.apis.register_api_tools"]):
                            with patch("tools.context.register_context_tools", mocks["tools.context.register_context_tools"]):
                                with patch("tools.hsd.register_hsd_tools", mocks["tools.hsd.register_hsd_tools"]):
                                    with patch("tools.gatekeeper.register_gatekeeper_tools", mocks["tools.gatekeeper.register_gatekeeper_tools"]):
                                        with patch("tools.vmanager.register_vmanager_tools", mocks["tools.vmanager.register_vmanager_tools"]):
                                            with patch("tools.submcp.register_submcp_tools", mocks["tools.submcp.register_submcp_tools"]):
                                                _reload_server_module()

        for name, mock in mocks.items():
            mock.assert_called_once()


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
                with patch("tools.skills.register_skills_tools"):
                    with patch("tools.commands.register_command_tools"):
                        with patch("tools.apis.register_api_tools"):
                            with patch("tools.context.register_context_tools"):
                                with patch("tools.hsd.register_hsd_tools"):
                                    with patch("tools.gatekeeper.register_gatekeeper_tools"):
                                        with patch("tools.vmanager.register_vmanager_tools"):
                                            with patch("tools.submcp.register_submcp_tools"):
                                                srv_mod = _reload_server_module()
                                                srv_mod.main()
                                                mock_fastmcp.run.assert_called_once_with(transport="stdio")
