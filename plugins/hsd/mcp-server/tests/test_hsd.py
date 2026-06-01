"""Tests for HSD plugin — tools/hsd.py."""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hsd import (
    _check_hsd_tools,
    _get_hsd_releases,
    _run_hsd_cli,
    register_hsd_tools,
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


@pytest.fixture()
def tmp_perl_cfg(tmp_path: Path) -> Path:
    cfg_dir = tmp_path / "cfg" / "gk"
    cfg_dir.mkdir(parents=True)
    content = textwrap.dedent("""\
        $Repository_HSD_Config = {
            'PTL-A0-release' => {
                turnin_ar_name => "turnin_ip",
                release_ar_name => "release_ip",
                component => "my_ip",
            },
            'PTL-A0-main' => {
                turnin_ar_name => "turnin_ip",
                release_ar_name => "release_ip",
                component => "my_ip",
            },
            'NOT-A-RELEASE' => {
                some_other_key => "value",
            },
        };
    """)
    (cfg_dir / "GkHsdOverrides.A0.my_cluster.cfg").write_text(content)
    return tmp_path


# ===================================================================
# _run_hsd_cli
# ===================================================================

class TestRunHsdCli:
    @pytest.mark.asyncio
    async def test_successful_command(self) -> None:
        proc = make_async_process(stdout="query results", returncode=0)
        with patch("asyncio.create_subprocess_shell", return_value=proc):
            result = await _run_hsd_cli("esquery test")
            assert "query results" in result

    @pytest.mark.asyncio
    async def test_nonzero_exit(self) -> None:
        proc = make_async_process(stdout="partial", stderr="error", returncode=1)
        with patch("asyncio.create_subprocess_shell", return_value=proc):
            result = await _run_hsd_cli("esquery bad")
            assert "STDERR" in result
            assert "Exit code: 1" in result

    @pytest.mark.asyncio
    async def test_timeout(self) -> None:
        proc = make_async_process()
        proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        with patch("asyncio.create_subprocess_shell", return_value=proc):
            result = await _run_hsd_cli("slow", timeout=1)
            assert "timed out" in result


# ===================================================================
# _check_hsd_tools
# ===================================================================

class TestCheckHsdTools:
    def test_tools_missing(self) -> None:
        with patch("os.path.isfile", return_value=False):
            result = _check_hsd_tools()
            assert result is not None
            assert "not found" in result

    def test_tools_present(self) -> None:
        with patch("os.path.isfile", return_value=True):
            with patch("os.access", return_value=True):
                result = _check_hsd_tools()
                assert result is None


# ===================================================================
# _get_hsd_releases — Perl config parsing
# ===================================================================

class TestGetHsdReleases:
    def test_valid_config(self, tmp_perl_cfg: Path) -> None:
        workarea = str(tmp_perl_cfg)
        with patch("hsd._git_config_val") as mock_git:
            mock_git.side_effect = lambda repo, key: {
                "intel.stepping": "A0",
                "intel.cluster": "my_cluster",
            }.get(key, "")
            with patch("subprocess.run") as mock_sp:
                mock_sp.return_value = subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="main\n"
                )
                with patch.dict(os.environ, {"WORKAREA": workarea}):
                    releases = _get_hsd_releases(workarea)
                    assert "PTL-A0-release" in releases
                    assert "PTL-A0-main" in releases
                    # NOT-A-RELEASE should NOT be included
                    assert "NOT-A-RELEASE" not in releases

    def test_no_config_file(self, tmp_path: Path) -> None:
        with patch("hsd._git_config_val", return_value="A0"):
            with patch("subprocess.run") as mock_sp:
                mock_sp.return_value = subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="main\n"
                )
                with patch.dict(os.environ, {"WORKAREA": str(tmp_path)}):
                    releases = _get_hsd_releases(str(tmp_path))
                    assert releases == []

    def test_missing_stepping(self, tmp_path: Path) -> None:
        with patch("hsd._git_config_val", return_value=""):
            releases = _get_hsd_releases(str(tmp_path))
            assert releases == []


# ===================================================================
# hsd_query tool
# ===================================================================

class TestHsdQueryTool:
    @pytest.mark.asyncio
    async def test_tools_not_available(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._check_hsd_tools", return_value="HSD not installed"):
            result = await mcp.tools["hsd_query"]("status='open'")
            assert "HSD not installed" in result

    @pytest.mark.asyncio
    async def test_successful_query(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._check_hsd_tools", return_value=None):
            with patch("hsd._run_hsd_cli", return_value="id,title\n123,bug"):
                result = await mcp.tools["hsd_query"]("status='open'")
                assert "123" in result


# ===================================================================
# hsd_get_article tool
# ===================================================================

class TestHsdGetArticleTool:
    @pytest.mark.asyncio
    async def test_invalid_id(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._check_hsd_tools", return_value=None):
            result = await mcp.tools["hsd_get_article"]("not-a-number")
            assert "Invalid article ID" in result

    @pytest.mark.asyncio
    async def test_valid_id(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._check_hsd_tools", return_value=None):
            with patch("hsd._run_hsd_cli", return_value="article details"):
                result = await mcp.tools["hsd_get_article"]("12345")
                assert "article details" in result
                assert "HSD Link" in result


# ===================================================================
# hsd_field_info tool
# ===================================================================

class TestHsdFieldInfoTool:
    @pytest.mark.asyncio
    async def test_invalid_subject(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._check_hsd_tools", return_value=None):
            result = await mcp.tools["hsd_field_info"](subject="bad;inject")
            assert "Invalid subject" in result

    @pytest.mark.asyncio
    async def test_list_subjects(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._check_hsd_tools", return_value=None):
            with patch("hsd._run_hsd_cli", return_value="bugeco\nfeature"):
                result = await mcp.tools["hsd_field_info"]()
                assert "bugeco" in result


# ===================================================================
# hsd_update_article tool (preview-first safety)
# ===================================================================

class TestHsdUpdateArticleTool:
    @pytest.mark.asyncio
    async def test_preview_by_default(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._check_hsd_tools", return_value=None):
            result = await mcp.tools["hsd_update_article"](
                article_id="99999", updates="status=resolved"
            )
            assert "preview" in result.lower()
            assert "NOT executed" in result

    @pytest.mark.asyncio
    async def test_invalid_id(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._check_hsd_tools", return_value=None):
            result = await mcp.tools["hsd_update_article"](
                article_id="abc", updates="status=resolved"
            )
            assert "Invalid article ID" in result

    @pytest.mark.asyncio
    async def test_empty_updates(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._check_hsd_tools", return_value=None):
            result = await mcp.tools["hsd_update_article"](
                article_id="99999", updates=""
            )
            assert "No updates" in result


# ===================================================================
# hsd_add_comment tool (preview-first safety)
# ===================================================================

class TestHsdAddCommentTool:
    @pytest.mark.asyncio
    async def test_preview_by_default(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._check_hsd_tools", return_value=None):
            result = await mcp.tools["hsd_add_comment"](
                article_id="99999", comment="test comment"
            )
            assert "preview" in result.lower()
            assert "NOT executed" in result

    @pytest.mark.asyncio
    async def test_empty_comment(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._check_hsd_tools", return_value=None):
            result = await mcp.tools["hsd_add_comment"](
                article_id="99999", comment="  "
            )
            assert "Empty comment" in result


# ===================================================================
# hsd_clone_article tool (preview-first safety)
# ===================================================================

class TestHsdCloneArticleTool:
    @pytest.mark.asyncio
    async def test_preview_by_default(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._check_hsd_tools", return_value=None):
            result = await mcp.tools["hsd_clone_article"](
                article_id="99999", release="new-release"
            )
            assert "preview" in result.lower()
            assert "NOT executed" in result
            assert "new-release" in result

    @pytest.mark.asyncio
    async def test_invalid_id(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._check_hsd_tools", return_value=None):
            result = await mcp.tools["hsd_clone_article"](
                article_id="abc", release="rel"
            )
            assert "Invalid article ID" in result

    @pytest.mark.asyncio
    async def test_empty_release(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._check_hsd_tools", return_value=None):
            result = await mcp.tools["hsd_clone_article"](
                article_id="99999", release=""
            )
            assert "required" in result.lower()


# ===================================================================
# get_hsd_release tool
# ===================================================================

class TestGetHsdReleaseTool:
    def test_single_release(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._get_hsd_releases", return_value=["PTL-A0-release"]):
            result = mcp.tools["get_hsd_release"]()
            assert "PTL-A0-release" in result

    def test_multiple_releases(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._get_hsd_releases", return_value=["PTL-A0-rel", "PTL-A0-main"]):
            result = mcp.tools["get_hsd_release"]()
            assert "PTL-A0-rel" in result
            assert "PTL-A0-main" in result

    def test_no_releases(self, tmp_path: Path) -> None:
        mcp = MockFastMCP()
        register_hsd_tools(mcp, str(tmp_path))
        with patch("hsd._get_hsd_releases", return_value=[]):
            result = mcp.tools["get_hsd_release"]()
            assert "Could not determine" in result
