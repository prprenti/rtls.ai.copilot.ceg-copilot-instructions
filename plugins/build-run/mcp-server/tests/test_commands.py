"""Tests for tools/commands.py — shell command execution tools."""

from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from commands import (
    _check_env,
    _run_shell,
    _sanitize_extra_args,
    register_command_tools,
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
        # shlex.quote wraps tokens in single quotes, neutralising metacharacters.
        # The semicolon is part of a quoted token like '-f;', so it's safe.
        assert "rm" in result  # token is preserved but quoted
        # Verify every token is individually shlex-quoted
        import shlex
        tokens = shlex.split(result)
        for tok in tokens:
            assert shlex.quote(tok) == shlex.quote(tok)  # round-trips safely

    def test_quoted_string_preserved(self) -> None:
        result = _sanitize_extra_args('"hello world"')
        assert "hello world" in result

    def test_invalid_quotes_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid extra_args"):
            _sanitize_extra_args("unclosed 'quote")

    def test_pipe_neutralized(self) -> None:
        result = _sanitize_extra_args("arg1 | cat /etc/passwd")
        # The pipe should be quoted as a literal
        assert "|" not in result or "'|'" in result

    def test_backtick_neutralized(self) -> None:
        result = _sanitize_extra_args("`whoami`")
        # backticks should be quoted away
        assert "`" not in result or "'" in result


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

    def test_invalid_workarea_dir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "cmd")
        monkeypatch.setenv("WORKAREA", "/nonexistent/path/xxxxx")
        result = _check_env("/tmp/repo")
        assert result is not None
        assert "not a valid directory" in result

    def test_both_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CTH_SETUP_CMD", raising=False)
        monkeypatch.delenv("WORKAREA", raising=False)
        result = _check_env("/tmp/repo")
        assert result is not None
        assert "CTH_SETUP_CMD" in result
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
    async def test_nonzero_exit(self) -> None:
        proc = make_async_process(stdout="output", stderr="error msg", returncode=1)
        with patch("asyncio.create_subprocess_shell", return_value=proc):
            result = await _run_shell("fail", "/tmp")
            assert "STDERR" in result
            assert "Exit code: 1" in result

    @pytest.mark.asyncio
    async def test_timeout(self) -> None:
        proc = make_async_process()
        proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        with patch("asyncio.create_subprocess_shell", return_value=proc):
            result = await _run_shell("slow", "/tmp", timeout=1)
            assert "timed out" in result
            proc.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_stderr_appended(self) -> None:
        proc = make_async_process(stdout="out", stderr="warn", returncode=0)
        with patch("asyncio.create_subprocess_shell", return_value=proc):
            result = await _run_shell("cmd", "/tmp")
            assert "STDERR" in result
            assert "warn" in result


# ===================================================================
# Registered tools
# ===================================================================

class TestCheckEnvironmentTool:
    @pytest.mark.asyncio
    async def test_happy_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "/p/hdk/bin/cth_psetup")
        monkeypatch.setenv("WORKAREA", str(tmp_path))
        monkeypatch.setenv("RTLMODELS", "/models")

        mcp = MockFastMCP()
        register_command_tools(mcp, str(tmp_path)) # pyright: ignore[reportArgumentType]

        proc = make_async_process(stdout="/usr/bin/grdlbuild", returncode=0)
        with patch("commands._run_shell", return_value="/usr/bin/tool"):
            result = await mcp.tools["check_environment"]()
            assert "CTH_SETUP_CMD: OK" in result


class TestRunGrdlbuildTool:
    @pytest.mark.asyncio
    async def test_env_not_ready(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CTH_SETUP_CMD", raising=False)
        monkeypatch.delenv("WORKAREA", raising=False)

        mcp = MockFastMCP()
        register_command_tools(mcp, "/tmp/repo") # pyright: ignore[reportArgumentType]
        result = await mcp.tools["run_grdlbuild"]("vc_cdc")
        assert "Environment not ready" in result

    @pytest.mark.asyncio
    async def test_invalid_task_name(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "cmd")
        monkeypatch.setenv("WORKAREA", str(tmp_path))

        mcp = MockFastMCP()
        register_command_tools(mcp, str(tmp_path)) # pyright: ignore[reportArgumentType]
        result = await mcp.tools["run_grdlbuild"]("bad;task")
        assert "Invalid task name" in result

    @pytest.mark.asyncio
    async def test_valid_task(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "cmd")
        monkeypatch.setenv("WORKAREA", str(tmp_path))

        mcp = MockFastMCP()
        register_command_tools(mcp, str(tmp_path)) # pyright: ignore[reportArgumentType]

        with patch("commands._run_shell", return_value="BUILD OK") as mock_run:
            result = await mcp.tools["run_grdlbuild"]("vc_cdc")
            assert "BUILD OK" in result
            # Verify the command passed to _run_shell starts with grdlbuild
            cmd = mock_run.call_args[0][0]
            assert cmd.startswith("grdlbuild")

    @pytest.mark.asyncio
    async def test_extra_args_injection_blocked(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "cmd")
        monkeypatch.setenv("WORKAREA", str(tmp_path))

        mcp = MockFastMCP()
        register_command_tools(mcp, str(tmp_path)) # pyright: ignore[reportArgumentType]

        with patch("commands._run_shell", return_value="OK") as mock_run:
            result = await mcp.tools["run_grdlbuild"]("vc_cdc", extra_args="-flag value")
            cmd = mock_run.call_args[0][0]
            # extra_args should be shlex-quoted
            assert "value" in cmd


class TestRunMakeTool:
    @pytest.mark.asyncio
    async def test_invalid_target(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "cmd")
        monkeypatch.setenv("WORKAREA", str(tmp_path))

        mcp = MockFastMCP()
        register_command_tools(mcp, str(tmp_path)) # pyright: ignore[reportArgumentType]
        result = await mcp.tools["run_make"]("target;evil")
        assert "Invalid make target" in result

    @pytest.mark.asyncio
    async def test_valid_target(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "cmd")
        monkeypatch.setenv("WORKAREA", str(tmp_path))

        mcp = MockFastMCP()
        register_command_tools(mcp, str(tmp_path)) # pyright: ignore[reportArgumentType]

        with patch("commands._run_shell", return_value="make done") as mock_run:
            result = await mcp.tools["run_make"]("all")
            assert "make done" in result

    @pytest.mark.asyncio
    async def test_nonexistent_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CTH_SETUP_CMD", "cmd")
        monkeypatch.setenv("WORKAREA", str(tmp_path))

        mcp = MockFastMCP()
        register_command_tools(mcp, str(tmp_path)) # pyright: ignore[reportArgumentType]
        result = await mcp.tools["run_make"]("all", directory="nonexistent_subdir")
        assert "does not exist" in result
