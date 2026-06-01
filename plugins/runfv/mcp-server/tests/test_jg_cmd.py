"""Tests for RunFV plugin — jg_cmd.py command builder."""

from __future__ import annotations

import json
import os
from typing import Any

import pytest

from jg_cmd import (
    _sanitize_extra_args,
    _validate_name,
    register_jg_cmd_tools,
)


class MockFastMCP:
    def __init__(self, name: str = "test-mcp", **kwargs: Any):
        self.name = name
        self.tools: dict[str, Any] = {}

    def tool(self, *args: Any, **kwargs: Any):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


# ===================================================================
# _sanitize_extra_args
# ===================================================================

class TestSanitizeExtraArgs:
    def test_empty_string(self) -> None:
        assert _sanitize_extra_args("") == ""

    def test_simple_args(self) -> None:
        result = _sanitize_extra_args("-verbose -timeout 300")
        assert "-verbose" in result
        assert "-timeout" in result
        assert "300" in result

    def test_quoted_args(self) -> None:
        result = _sanitize_extra_args('-define "MY_FLAG=1"')
        assert "MY_FLAG=1" in result

    def test_shell_injection_blocked(self) -> None:
        result = _sanitize_extra_args("-flag; rm -rf /")
        # shlex.split splits on ; so tokens are ["-flag;", "rm", "-rf", "/"]
        # shlex.quote wraps each token safely
        assert "rm" in result  # present but quoted safely
        # The semicolon is inside a quoted token, not a raw shell separator
        assert result != "-flag; rm -rf /"

    def test_invalid_quoting(self) -> None:
        with pytest.raises(ValueError, match="Invalid extra_args"):
            _sanitize_extra_args("unterminated 'quote")


# ===================================================================
# _validate_name
# ===================================================================

class TestValidateName:
    def test_valid_alphanumeric(self) -> None:
        assert _validate_name("memss_pma", "dut") is None

    def test_valid_with_hyphens(self) -> None:
        assert _validate_name("boot-err-checks", "proof") is None

    def test_empty_returns_none(self) -> None:
        assert _validate_name("", "dut") is None

    def test_invalid_characters(self) -> None:
        result = _validate_name("bad;name", "dut")
        assert result is not None
        assert "Invalid" in result

    def test_invalid_spaces(self) -> None:
        result = _validate_name("bad name", "proof")
        assert result is not None


# ===================================================================
# Tool registration
# ===================================================================

class TestToolRegistration:
    def test_jg_cmd_registered(self) -> None:
        mcp = MockFastMCP("test")
        register_jg_cmd_tools(mcp, "/tmp/repo")  # type: ignore[arg-type]
        assert "jg_cmd" in mcp.tools


# ===================================================================
# jg_cmd tool — command builder
# ===================================================================

class TestJgCmd:
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path, monkeypatch):
        self.mcp = MockFastMCP("test")
        self.repo_root = str(tmp_path)
        register_jg_cmd_tools(self.mcp, self.repo_root)  # type: ignore[arg-type]
        self.jg_cmd = self.mcp.tools["jg_cmd"]
        monkeypatch.setenv("WORKAREA", str(tmp_path))

    @pytest.mark.asyncio
    async def test_basic_prove_all(self) -> None:
        result = await self.jg_cmd(tcl_commands="prove -all")
        data = json.loads(result)
        assert "error" not in data
        assert "prove -all" in data["tcl_script"]
        assert "exit -force" in data["tcl_script"]
        assert any("jg" in cmd for cmd in data["commands"])

    @pytest.mark.asyncio
    async def test_default_app_fpv(self) -> None:
        result = await self.jg_cmd(tcl_commands="prove -all")
        data = json.loads(result)
        jg_commands = [c for c in data["commands"] if c.startswith("jg ") or c.startswith("'jg'")]
        assert len(jg_commands) == 1
        assert "-fpv" in jg_commands[0]

    @pytest.mark.asyncio
    async def test_custom_app(self) -> None:
        result = await self.jg_cmd(tcl_commands="prove -all", app="cdc")
        data = json.loads(result)
        jg_commands = [c for c in data["commands"] if c.startswith("jg ") or c.startswith("'jg'")]
        assert len(jg_commands) == 1
        assert "-cdc" in jg_commands[0]

    @pytest.mark.asyncio
    async def test_invalid_app(self) -> None:
        result = await self.jg_cmd(tcl_commands="prove -all", app="bad")
        data = json.loads(result)
        assert "error" in data
        assert "Invalid app" in data["error"]

    @pytest.mark.asyncio
    async def test_empty_tcl_commands(self) -> None:
        result = await self.jg_cmd(tcl_commands="   ")
        data = json.loads(result)
        assert "error" in data
        assert "No Tcl commands" in data["error"]

    @pytest.mark.asyncio
    async def test_proof_without_dut(self) -> None:
        result = await self.jg_cmd(
            tcl_commands="prove -all",
            proof="my_proof",
        )
        data = json.loads(result)
        assert "error" in data
        assert "dut is also required" in data["error"]

    @pytest.mark.asyncio
    async def test_proof_with_dut(self) -> None:
        result = await self.jg_cmd(
            tcl_commands="prove -all",
            dut="memss_pma",
            proof="boot_checks",
        )
        data = json.loads(result)
        assert "error" not in data
        assert len(data["commands"]) >= 3  # load-proof + mkdir + jg
        assert any("run_fv load-proof" in c for c in data["commands"])
        assert any("-proj" in c for c in data["commands"])

    @pytest.mark.asyncio
    async def test_invalid_dut_name(self) -> None:
        result = await self.jg_cmd(
            tcl_commands="prove -all",
            dut="bad;name",
            proof="ok_proof",
        )
        data = json.loads(result)
        assert "error" in data
        assert "Invalid dut" in data["error"]

    @pytest.mark.asyncio
    async def test_invalid_proof_name(self) -> None:
        result = await self.jg_cmd(
            tcl_commands="prove -all",
            dut="ok_dut",
            proof="bad name",
        )
        data = json.loads(result)
        assert "error" in data
        assert "Invalid proof" in data["error"]

    @pytest.mark.asyncio
    async def test_extra_jg_args(self) -> None:
        result = await self.jg_cmd(
            tcl_commands="prove -all",
            extra_jg_args="-verbose -timeout 300",
        )
        data = json.loads(result)
        assert "error" not in data
        jg_commands = [c for c in data["commands"] if c.startswith("jg ") or c.startswith("'jg'")]
        assert len(jg_commands) == 1
        assert "-verbose" in jg_commands[0]

    @pytest.mark.asyncio
    async def test_invalid_extra_jg_args(self) -> None:
        result = await self.jg_cmd(
            tcl_commands="prove -all",
            extra_jg_args="unterminated 'quote",
        )
        data = json.loads(result)
        assert "error" in data
        assert "extra_jg_args" in data["error"]

    @pytest.mark.asyncio
    async def test_tcl_script_has_header_and_exit(self) -> None:
        result = await self.jg_cmd(tcl_commands="report -summary")
        data = json.loads(result)
        assert data["tcl_script"].startswith("# Auto-generated")
        assert "exit -force" in data["tcl_script"]
        assert "report -summary" in data["tcl_script"]

    @pytest.mark.asyncio
    async def test_cwd_is_workarea(self, monkeypatch, tmp_path) -> None:
        wa = str(tmp_path / "my_workarea")
        monkeypatch.setenv("WORKAREA", wa)
        result = await self.jg_cmd(tcl_commands="prove -all")
        data = json.loads(result)
        assert data["cwd"] == wa

    @pytest.mark.asyncio
    async def test_multiline_tcl(self) -> None:
        tcl = "clock -clear\nreset -clear\nprove -all"
        result = await self.jg_cmd(tcl_commands=tcl)
        data = json.loads(result)
        assert "clock -clear" in data["tcl_script"]
        assert "prove -all" in data["tcl_script"]

    @pytest.mark.asyncio
    async def test_batch_no_gui_flags(self) -> None:
        result = await self.jg_cmd(tcl_commands="prove -all")
        data = json.loads(result)
        jg_commands = [c for c in data["commands"] if c.startswith("jg ") or c.startswith("'jg'")]
        assert len(jg_commands) == 1
        assert "-batch" in jg_commands[0]
        assert "-no_gui" in jg_commands[0]

    @pytest.mark.asyncio
    async def test_mkdir_command_present(self) -> None:
        result = await self.jg_cmd(tcl_commands="prove -all")
        data = json.loads(result)
        assert any("mkdir" in c for c in data["commands"])

    @pytest.mark.asyncio
    async def test_no_proof_no_load_command(self) -> None:
        result = await self.jg_cmd(tcl_commands="prove -all")
        data = json.loads(result)
        assert not any("run_fv" in c for c in data["commands"])

    @pytest.mark.asyncio
    async def test_notes_present(self) -> None:
        result = await self.jg_cmd(tcl_commands="prove -all")
        data = json.loads(result)
        assert "notes" in data
        assert len(data["notes"]) > 0

    @pytest.mark.asyncio
    async def test_all_allowed_apps(self) -> None:
        for app in ["fpv", "cdc", "lpv", "sec", "superlint", "conn",
                     "cov", "spv", "xprop", "fsv", "csr", "rvv", "unr"]:
            result = await self.jg_cmd(tcl_commands="prove -all", app=app)
            data = json.loads(result)
            assert "error" not in data, f"Failed for app={app}"
