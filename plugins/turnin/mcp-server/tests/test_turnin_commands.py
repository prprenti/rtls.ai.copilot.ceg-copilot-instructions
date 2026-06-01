"""Tests for turnin plugin — tools/turnin_commands.py."""

from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from turnin_commands import (
    _check_env,
    _run_shell,
    _sanitize_extra_args,
    register_turnin_command_tools,
)
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


def make_async_process(stdout: str = "", stderr: str = "", returncode: int = 0):
    proc = AsyncMock()
    proc.communicate = AsyncMock(return_value=(stdout.encode(), stderr.encode()))
    proc.returncode = returncode
    proc.kill = MagicMock()
    proc.wait = AsyncMock()
    return proc


# ===================================================================
# _sanitize_extra_args
# ===================================================================

class TestSanitizeExtraArgs:
    def test_empty_string(self) -> None:
        assert _sanitize_extra_args("") == ""

    def test_normal_args(self) -> None:
        result = _sanitize_extra_args("-flag value1 value2")
        assert "-flag" in result
        assert "value1" in result

    def test_shell_metacharacters_neutralized(self) -> None:
        result = _sanitize_extra_args("-f; rm -rf /")
        import shlex
        tokens = shlex.split(result)
        for tok in tokens:
            assert shlex.quote(tok) == shlex.quote(tok)

    def test_invalid_quotes_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid extra_args"):
            _sanitize_extra_args("unclosed 'quote")


# ===================================================================
# _check_env
# ===================================================================

class TestCheckEnv:
    def test_all_set(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "/p/hdk/bin/cth_psetup")
        monkeypatch.setenv("WORKAREA", str(tmp_path))
        assert _check_env(str(tmp_path)) is None

    def test_missing_cth_setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CTH_SETUP_CMD", raising=False)
        monkeypatch.setenv("WORKAREA", str(tmp_path))
        result = _check_env(str(tmp_path))
        assert result is not None
        assert "CTH_SETUP_CMD" in result

    def test_missing_workarea(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "cmd")
        monkeypatch.delenv("WORKAREA", raising=False)
        result = _check_env("/tmp/repo")
        assert result is not None
        assert "WORKAREA" in result


# ===================================================================
# _run_shell
# ===================================================================

class TestRunShell:
    @pytest.mark.asyncio
    async def test_successful_command(self) -> None:
        proc = make_async_process(stdout="hello world", returncode=0)
        with patch("asyncio.create_subprocess_shell", return_value=proc):
            result = await _run_shell("echo hello", "/tmp")
            assert "hello world" in result

    @pytest.mark.asyncio
    async def test_timeout(self) -> None:
        proc = make_async_process()
        proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        with patch("asyncio.create_subprocess_shell", return_value=proc):
            result = await _run_shell("slow", "/tmp", timeout=1)
            assert "timed out" in result
            proc.kill.assert_called_once()


# ===================================================================
# run_turnin tool
# ===================================================================

class TestRunTurninTool:
    @pytest.mark.asyncio
    async def test_env_not_ready(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CTH_SETUP_CMD", raising=False)
        monkeypatch.delenv("WORKAREA", raising=False)

        mcp = MockFastMCP()
        register_turnin_command_tools(mcp, "/tmp/repo")
        result = await mcp.tools["run_turnin"]("fix bug")
        assert "Environment not ready" in result

    @pytest.mark.asyncio
    async def test_basic_turnin(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "cmd")
        monkeypatch.setenv("WORKAREA", str(tmp_path))

        mcp = MockFastMCP()
        register_turnin_command_tools(mcp, str(tmp_path))

        with patch("turnin_commands._run_shell", return_value="turnin submitted") as mock_run:
            result = await mcp.tools["run_turnin"]("fix bug #123")
            assert "turnin submitted" in result
            cmd = mock_run.call_args[0][0]
            assert "turnin" in cmd

    @pytest.mark.asyncio
    async def test_turnin_with_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "cmd")
        monkeypatch.setenv("WORKAREA", str(tmp_path))

        mcp = MockFastMCP()
        register_turnin_command_tools(mcp, str(tmp_path))

        with patch("turnin_commands._run_shell", return_value="OK") as mock_run:
            result = await mcp.tools["run_turnin"]("msg", files=["a.sv", "b.sv"])
            cmd = mock_run.call_args[0][0]
            assert "a.sv" in cmd


# ===================================================================
# turnin_query tool
# ===================================================================

class TestTurninQueryTool:
    @pytest.mark.asyncio
    async def test_query(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "cmd")
        monkeypatch.setenv("WORKAREA", str(tmp_path))

        mcp = MockFastMCP()
        register_turnin_command_tools(mcp, str(tmp_path))

        with patch("turnin_commands._run_shell", return_value="turnin status: PASS"):
            result = await mcp.tools["turnin_query"]("12345")
            assert "PASS" in result


# ===================================================================
# turnin_my_status tool
# ===================================================================

class TestTurninMyStatusTool:
    @pytest.mark.asyncio
    async def test_default(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "cmd")
        monkeypatch.setenv("WORKAREA", str(tmp_path))

        mcp = MockFastMCP()
        register_turnin_command_tools(mcp, str(tmp_path))

        with patch("turnin_commands._run_shell", return_value="my turnins list") as mock_run:
            result = await mcp.tools["turnin_my_status"]()
            assert "my turnins list" in result
            cmd = mock_run.call_args[0][0]
            assert "-days 7" in cmd

    @pytest.mark.asyncio
    async def test_show_all(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "cmd")
        monkeypatch.setenv("WORKAREA", str(tmp_path))

        mcp = MockFastMCP()
        register_turnin_command_tools(mcp, str(tmp_path))

        with patch("turnin_commands._run_shell", return_value="all") as mock_run:
            await mcp.tools["turnin_my_status"](show_all=True)
            cmd = mock_run.call_args[0][0]
            assert "-all" in cmd


# ===================================================================
# turnin_pipeline_query tool
# ===================================================================

class TestTurninPipelineQueryTool:
    @pytest.mark.asyncio
    async def test_missing_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "cmd")
        monkeypatch.setenv("WORKAREA", str(tmp_path))

        mcp = MockFastMCP()
        register_turnin_command_tools(mcp, str(tmp_path))

        with patch("turnin_commands._git_config", return_value=""):
            with patch("subprocess.run") as mock_sp:
                mock_sp.return_value = subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="main\n"
                )
                result = await mcp.tools["turnin_pipeline_query"]()
                assert "Cannot determine pipeline" in result

    @pytest.mark.asyncio
    async def test_valid_pipeline_query(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "cmd")
        monkeypatch.setenv("WORKAREA", str(tmp_path))

        mcp = MockFastMCP()
        register_turnin_command_tools(mcp, str(tmp_path))

        def fake_git_config(repo, key):
            return {"intel.cluster": "my_cluster", "intel.stepping": "A0"}.get(key, "")

        with patch("turnin_commands._git_config", side_effect=fake_git_config):
            with patch("subprocess.run") as mock_sp:
                mock_sp.return_value = subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="main\n"
                )
                with patch("turnin_commands._run_shell", return_value="pipeline results"):
                    result = await mcp.tools["turnin_pipeline_query"]()
                    assert "pipeline results" in result
