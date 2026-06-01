"""Tests for FE Setup plugin — fe_setup.py."""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml

from fe_setup import (
    _extract_cfg,
    _extract_repo_name,
    _flatten_repos,
    _load_repos,
    _match_repos,
    _normalize_setup_cmd,
    _parse_intel_from_path,
    register_fe_setup_tools,
)


# ---------------------------------------------------------------------------
# MockFastMCP — same pattern as HSD tests
# ---------------------------------------------------------------------------

class MockFastMCP:
    def __init__(self, name: str = "test-mcp", **kwargs: Any):
        self.name = name
        self.tools: dict[str, Any] = {}

    def tool(self, *args: Any, **kwargs: Any):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


# ---------------------------------------------------------------------------
# Sample YML data
# ---------------------------------------------------------------------------

SAMPLE_YML = {
    "defaults": {"repo_branch": "master"},
    "groups": [
        {
            "cheetah_setup_command": "/p/cth/bin/cth_psetup -p ddgcth -cfg ttlh78",
            "repos": [
                {
                    "path": "/p/cth/rtl/git_repos/ddgcth/ttl/gk/ttlh78/hub-ttlh78-a0",
                    "keywords": ["hub", "TTL SoC"],
                },
                {
                    "path": "/p/cth/rtl/git_repos/ddgcth/ttl/gk/ttlh78/memss-ttlh78-trunk",
                    "keywords": ["memss", "memory subsystem"],
                },
            ],
        },
        {
            "cheetah_setup_command": "/p/cth/bin/cth_psetup -p ddgcth -cfg ddgip",
            "repos": [
                {
                    "path": "/p/cth/rtl/git_repos/ddgcth/ddgip/gk/punit-ddgip-trunk",
                    "repo_branch": "ttl-a0",
                    "keywords": ["punit", "power management", "power unit"],
                },
                {
                    "path": "/p/cth/rtl/git_repos/ddgcth/ddgip/gk/dmu-ddgip-trunk",
                    "repo_branch": "rzl-a0",
                    "keywords": ["dmu", "display management", "rzl"],
                },
            ],
        },
    ],
}


@pytest.fixture()
def tmp_plugin(tmp_path: Path) -> Path:
    """Create a temp plugin dir with a ceg_repos.yml."""
    yml_path = tmp_path / "ceg_repos.yml"
    yml_path.write_text(yaml.dump(SAMPLE_YML, default_flow_style=False))
    return tmp_path


@pytest.fixture()
def sample_repos() -> list[dict[str, Any]]:
    """Return flattened repos from SAMPLE_YML."""
    return _flatten_repos(SAMPLE_YML)


# ===================================================================
# Helper functions
# ===================================================================

class TestExtractRepoName:
    def test_simple(self) -> None:
        assert _extract_repo_name("/p/cth/rtl/git_repos/ddgcth/ttl/gk/ttlh78/hub-ttlh78-a0") == "hub-ttlh78-a0"

    def test_trailing_slash(self) -> None:
        assert _extract_repo_name("/p/cth/rtl/git_repos/ddgcth/ddgip/gk/punit-ddgip-trunk/") == "punit-ddgip-trunk"


class TestExtractCfg:
    def test_normal(self) -> None:
        assert _extract_cfg("/p/cth/bin/cth_psetup -p ddgcth -cfg ttlh78") == "ttlh78"

    def test_no_cfg(self) -> None:
        assert _extract_cfg("some random command") == ""

    def test_cfg_at_end(self) -> None:
        assert _extract_cfg("-cfg ddgip") == "ddgip"


class TestNormalizeSetupCmd:
    def test_strips_read_only(self) -> None:
        cmd = "/p/cth/bin/cth_psetup -p ddgcth -cfg ttlh78 -read_only"
        assert _normalize_setup_cmd(cmd) == "/p/cth/bin/cth_psetup -p ddgcth -cfg ttlh78"

    def test_collapses_whitespace(self) -> None:
        cmd = "/p/cth/bin/cth_psetup  -p  ddgcth   -cfg   ttlh78"
        assert _normalize_setup_cmd(cmd) == "/p/cth/bin/cth_psetup -p ddgcth -cfg ttlh78"

    def test_no_change_needed(self) -> None:
        cmd = "/p/cth/bin/cth_psetup -p ddgcth -cfg ddgip"
        assert _normalize_setup_cmd(cmd) == cmd


class TestParseIntelFromPath:
    def test_hub(self) -> None:
        path = "/p/cth/rtl/git_repos/ddgcth/ttl/gk/ttlh78/hub-ttlh78-a0"
        cmd = "/p/cth/bin/cth_psetup -p ddgcth -cfg ttlh78"
        result = _parse_intel_from_path(path, cmd)
        assert result["cluster"] == "hub"
        assert result["stepping"] == "ttlh78-a0"
        assert result["domain"] == "ddgcth"
        assert result["project"] == "ttlh78"

    def test_punit(self) -> None:
        path = "/p/cth/rtl/git_repos/ddgcth/ddgip/gk/punit-ddgip-trunk"
        cmd = "/p/cth/bin/cth_psetup -p ddgcth -cfg ddgip"
        result = _parse_intel_from_path(path, cmd)
        assert result["cluster"] == "punit"
        assert result["stepping"] == "ddgip-trunk"
        assert result["domain"] == "ddgcth"
        assert result["project"] == "ddgip"

    def test_underscore_cluster(self) -> None:
        path = "/p/cth/rtl/git_repos/ddgcth/ddgip/gk/c2c_sbmisc-ttlbxh78-trunk"
        cmd = "/p/cth/bin/cth_psetup -p ddgcth -cfg ttlbxh78"
        result = _parse_intel_from_path(path, cmd)
        assert result["cluster"] == "c2c_sbmisc"
        assert result["stepping"] == "ttlbxh78-trunk"


class TestFlattenRepos:
    def test_count(self) -> None:
        repos = _flatten_repos(SAMPLE_YML)
        assert len(repos) == 4

    def test_default_branch(self) -> None:
        repos = _flatten_repos(SAMPLE_YML)
        hub = [r for r in repos if r["name"] == "hub-ttlh78-a0"][0]
        assert hub["repo_branch"] == "master"

    def test_override_branch(self) -> None:
        repos = _flatten_repos(SAMPLE_YML)
        punit = [r for r in repos if r["name"] == "punit-ddgip-trunk"][0]
        assert punit["repo_branch"] == "ttl-a0"

    def test_setup_cmd_attached(self) -> None:
        repos = _flatten_repos(SAMPLE_YML)
        punit = [r for r in repos if r["name"] == "punit-ddgip-trunk"][0]
        assert "ddgip" in punit["setup_cmd"]


# ===================================================================
# _match_repos
# ===================================================================

class TestMatchRepos:
    def test_exact_keyword(self, sample_repos: list) -> None:
        matches = _match_repos("punit", sample_repos)
        assert len(matches) == 1
        assert matches[0]["name"] == "punit-ddgip-trunk"

    def test_partial_keyword(self, sample_repos: list) -> None:
        matches = _match_repos("memory", sample_repos)
        assert len(matches) == 1
        assert matches[0]["name"] == "memss-ttlh78-trunk"

    def test_case_insensitive(self, sample_repos: list) -> None:
        matches = _match_repos("HUB", sample_repos)
        assert len(matches) == 1
        assert matches[0]["name"] == "hub-ttlh78-a0"

    def test_multiple_matches(self, sample_repos: list) -> None:
        matches = _match_repos("display", sample_repos)
        assert len(matches) == 1  # only dmu has "display management"

    def test_no_matches(self, sample_repos: list) -> None:
        matches = _match_repos("nonexistent", sample_repos)
        assert len(matches) == 0

    def test_empty_query_returns_all(self, sample_repos: list) -> None:
        matches = _match_repos("", sample_repos)
        assert len(matches) == len(sample_repos)

    def test_matches_by_name(self, sample_repos: list) -> None:
        matches = _match_repos("dmu-ddgip", sample_repos)
        assert len(matches) == 1
        assert matches[0]["name"] == "dmu-ddgip-trunk"


# ===================================================================
# _load_repos
# ===================================================================

class TestLoadRepos:
    def test_valid_yml(self, tmp_plugin: Path) -> None:
        # Clear lru_cache between tests
        _load_repos.cache_clear()
        data = _load_repos(str(tmp_plugin))
        assert "groups" in data
        assert len(data["groups"]) == 2

    def test_missing_file(self, tmp_path: Path) -> None:
        _load_repos.cache_clear()
        with pytest.raises(FileNotFoundError):
            _load_repos(str(tmp_path))

    def test_malformed_yml(self, tmp_path: Path) -> None:
        _load_repos.cache_clear()
        (tmp_path / "ceg_repos.yml").write_text(": invalid: yaml: [[[")
        with pytest.raises(yaml.YAMLError):
            _load_repos(str(tmp_path))


# ===================================================================
# list_repos tool
# ===================================================================

class TestListReposTool:
    def test_full_list(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin)) # type: ignore
        result = mcp.tools["list_repos"]()
        assert "hub-ttlh78-a0" in result
        assert "punit-ddgip-trunk" in result
        assert "Total: 4" in result

    def test_filtered_list(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        result = mcp.tools["list_repos"](group_filter="ddgip")
        assert "punit-ddgip-trunk" in result
        assert "hub-ttlh78-a0" not in result

    def test_empty_filter_result(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        result = mcp.tools["list_repos"](group_filter="nonexistent")
        assert "No repos found" in result


# ===================================================================
# get_repo_info tool
# ===================================================================

class TestGetRepoInfoTool:
    def test_single_match(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        result = mcp.tools["get_repo_info"]("punit")
        assert "punit-ddgip-trunk" in result
        assert "-read_only" in result
        assert "git clone" in result
        assert "export WORKAREA" in result

    def test_single_match_branch(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        result = mcp.tools["get_repo_info"]("punit")
        assert "--branch ttl-a0" in result

    def test_multiple_matches(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        # "mem" matches both memss and dmu (display management)
        # Actually let's use a query that matches by path
        result = mcp.tools["get_repo_info"]("ddgip")
        assert "Multiple repos match" in result
        assert "punit-ddgip-trunk" in result
        assert "dmu-ddgip-trunk" in result

    def test_no_match(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        result = mcp.tools["get_repo_info"]("nonexistent")
        assert "No repos match" in result
        assert "Available repos" in result

    def test_default_branch_no_flag(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        result = mcp.tools["get_repo_info"]("hub")
        # hub uses default branch "master", so --branch should not appear
        assert "--branch" not in result


# ===================================================================
# check_terminal_ready tool
# ===================================================================

class TestCheckTerminalReadyTool:
    def test_match(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        with patch.dict(os.environ, {
            "CTH_SETUP_CMD": "/p/cth/bin/cth_psetup -p ddgcth -cfg ttlh78",
            "WORKAREA": "/tmp/workarea",
        }):
            result = mcp.tools["check_terminal_ready"]()
            assert result is True

    def test_missing_workarea(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        with patch.dict(os.environ, {
            "CTH_SETUP_CMD": "/p/cth/bin/cth_psetup -p ddgcth -cfg ttlh78",
        }):
            result = mcp.tools["check_terminal_ready"]()
            assert result is False

    def test_missing_setup(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        with patch.dict(os.environ, {"WORKAREA": "/tmp/workarea"}, clear=True):
            result = mcp.tools["check_terminal_ready"]()
            assert result is False

    def test_missing_both(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        with patch.dict(os.environ, {}, clear=True):
            result = mcp.tools["check_terminal_ready"]()
            assert result is False


# ===================================================================
# inspect_workspace_git_config tool
# ===================================================================

class TestInspectWorkspaceGitConfigTool:
    def test_not_a_repo(self, tmp_path: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_path))  # type: ignore
        result = json.loads(mcp.tools["inspect_workspace_git_config"](str(tmp_path)))
        assert result["status"] == "NOT_A_REPO"

    def test_no_workarea(self, tmp_path: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_path))  # type: ignore
        with patch.dict(os.environ, {}, clear=True):
            result = json.loads(mcp.tools["inspect_workspace_git_config"](""))
            assert result["status"] == "NOT_A_REPO"

    def test_intel_section_present(self, tmp_path: Path) -> None:
        _load_repos.cache_clear()
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_path))  # type: ignore

        def mock_git_cfg(key):
            vals = {
                "intel.stepping": "ttlh78-a0",
                "intel.cluster": "hub",
                "intel.project": "ttlh78",
                "intel.domain": "ddgcth",
            }
            return vals.get(key, "")

        with patch("fe_setup.subprocess.run") as mock_run:
            mock_run.side_effect = lambda args, **kw: type("R", (), {
                "stdout": mock_git_cfg(args[3]),
                "returncode": 0,
            })()
            result = json.loads(mcp.tools["inspect_workspace_git_config"](str(tmp_path)))
            assert result["status"] == "OK"
            assert result["stepping"] == "ttlh78-a0"
            assert result["cluster"] == "hub"
            assert result["project"] == "ttlh78"
            assert result["domain"] == "ddgcth"

    def test_no_intel_section_with_remote(self, tmp_path: Path) -> None:
        _load_repos.cache_clear()
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_path))  # type: ignore

        call_count = [0]

        def mock_git_cfg(args, **kw):
            call_count[0] += 1
            key = args[3]
            if key == "remote.origin.url":
                return type("R", (), {"stdout": "/p/cth/rtl/git_repos/ddgcth/ddgip/gk/punit-ddgip-trunk", "returncode": 0})()
            return type("R", (), {"stdout": "", "returncode": 1})()

        with patch("fe_setup.subprocess.run", side_effect=mock_git_cfg):
            result = json.loads(mcp.tools["inspect_workspace_git_config"](str(tmp_path)))
            assert result["status"] == "NO_INTEL_SECTION"
            assert "punit" in result["remote_origin_url"]


# ===================================================================
# match_remote_to_repo tool
# ===================================================================

class TestMatchRemoteToRepoTool:
    def test_exact_match(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        result = json.loads(
            mcp.tools["match_remote_to_repo"](
                "/p/cth/rtl/git_repos/ddgcth/ddgip/gk/punit-ddgip-trunk"
            )
        )
        assert result["status"] == "MATCH"
        assert result["intel_config"]["cluster"] == "punit"
        assert result["intel_config"]["stepping"] == "ddgip-trunk"
        assert result["intel_config"]["domain"] == "ddgcth"
        assert result["intel_config"]["project"] == "ddgip"
        assert len(result["fix_commands"]) == 4
        assert any("intel.cluster" in c for c in result["fix_commands"])

    def test_no_match(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        result = json.loads(
            mcp.tools["match_remote_to_repo"]("/some/unknown/repo")
        )
        assert result["status"] == "NO_MATCH"

    def test_empty_url(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        result = json.loads(mcp.tools["match_remote_to_repo"](""))
        assert result["status"] == "NO_MATCH"

    def test_trailing_slash(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        result = json.loads(
            mcp.tools["match_remote_to_repo"](
                "/p/cth/rtl/git_repos/ddgcth/ttl/gk/ttlh78/hub-ttlh78-a0/"
            )
        )
        assert result["status"] == "MATCH"
        assert result["intel_config"]["cluster"] == "hub"

    def test_hub_intel_values(self, tmp_plugin: Path) -> None:
        _load_repos.cache_clear()
        mcp = MockFastMCP()
        register_fe_setup_tools(mcp, str(tmp_plugin))  # type: ignore
        result = json.loads(
            mcp.tools["match_remote_to_repo"](
                "/p/cth/rtl/git_repos/ddgcth/ttl/gk/ttlh78/hub-ttlh78-a0"
            )
        )
        assert result["intel_config"]["cluster"] == "hub"
        assert result["intel_config"]["stepping"] == "ttlh78-a0"
        assert result["intel_config"]["domain"] == "ddgcth"
        assert result["intel_config"]["project"] == "ttlh78"
        assert result["setup_cmd"] == "/p/cth/bin/cth_psetup -p ddgcth -cfg ttlh78"
