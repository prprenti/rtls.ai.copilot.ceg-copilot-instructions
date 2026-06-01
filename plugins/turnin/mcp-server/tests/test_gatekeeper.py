"""Tests for turnin plugin — tools/gatekeeper.py."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from gatekeeper import (
    _gk_dir,
    _safe_read,
    register_gatekeeper_tools,
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


@pytest.fixture()
def tmp_gk(tmp_path: Path) -> Path:
    gk = tmp_path / "GATEKEEPER"
    gk.mkdir()
    (gk / "turnin.2025-03-01_10-30-00.log").write_text("turnin started\nresult: PASS")
    (gk / "turnin.2025-03-01_10-30-00.id").write_text("12345")
    (gk / "turnin.2025-03-05_14-00-00.log").write_text("turnin started\nresult: FAIL")
    (gk / "gk_pre_turnin_checks.99999.log").write_text("check 1: PASS\ncheck 2: PASS")
    (gk / "gk_post_submit_hook.99999.log").write_text("post-submit complete")
    (gk / "turnin_files_changed.99999").write_text("src/rtl/foo.sv\nsrc/rtl/bar.sv")
    (gk / "code_review_url.99999.txt").write_text("https://github.com/repo/pull/42")
    return tmp_path


# ===================================================================
# _gk_dir
# ===================================================================

class TestGkDir:
    def test_uses_workarea_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WORKAREA", "/my/workarea")
        assert _gk_dir("/repo") == "/my/workarea/GATEKEEPER"

    def test_falls_back_to_repo_root(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("WORKAREA", raising=False)
        assert _gk_dir("/my/repo") == "/my/repo/GATEKEEPER"


# ===================================================================
# _safe_read — path traversal guard
# ===================================================================

class TestSafeRead:
    def test_file_outside_base_rejected(self, tmp_path: Path) -> None:
        gk = tmp_path / "GATEKEEPER"
        gk.mkdir()
        secret = tmp_path / "secret.txt"
        secret.write_text("top secret")
        result = _safe_read(str(secret), str(gk))
        assert "path traversal" in result.lower()

    def test_file_inside_base_allowed(self, tmp_path: Path) -> None:
        gk = tmp_path / "GATEKEEPER"
        gk.mkdir()
        log = gk / "test.log"
        log.write_text("log content")
        result = _safe_read(str(log), str(gk))
        assert "log content" in result

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        gk = tmp_path / "GATEKEEPER"
        gk.mkdir()
        result = _safe_read(str(gk / "missing.log"), str(gk))
        assert "not found" in result.lower()

    def test_symlink_traversal_blocked(self, tmp_path: Path) -> None:
        gk = tmp_path / "GATEKEEPER"
        gk.mkdir()
        secret = tmp_path / "secret.txt"
        secret.write_text("top secret")
        link = gk / "link.txt"
        link.symlink_to(secret)
        result = _safe_read(str(link), str(gk))
        assert "path traversal" in result.lower()

    def test_truncation_at_max_bytes(self, tmp_path: Path) -> None:
        gk = tmp_path / "GATEKEEPER"
        gk.mkdir()
        big = gk / "big.log"
        big.write_text("x" * 1000)
        result = _safe_read(str(big), str(gk), max_bytes=100)
        assert len(result) < 200  # 100 bytes + truncation message
        assert "truncated" in result.lower()


# ===================================================================
# gatekeeper_list_turnins tool
# ===================================================================

class TestGatekeeperListTurnins:
    def test_no_gatekeeper_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WORKAREA", str(tmp_path))
        mcp = MockFastMCP()
        register_gatekeeper_tools(mcp, str(tmp_path))
        result = mcp.tools["gatekeeper_list_turnins"]()
        assert "not found" in result.lower()

    def test_empty_gatekeeper_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        gk = tmp_path / "GATEKEEPER"
        gk.mkdir()
        monkeypatch.setenv("WORKAREA", str(tmp_path))
        mcp = MockFastMCP()
        register_gatekeeper_tools(mcp, str(tmp_path))
        result = mcp.tools["gatekeeper_list_turnins"]()
        assert "No turnin logs" in result

    def test_turnin_logs_listed(self, tmp_gk: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WORKAREA", str(tmp_gk))
        mcp = MockFastMCP()
        register_gatekeeper_tools(mcp, str(tmp_gk))
        result = mcp.tools["gatekeeper_list_turnins"]()
        assert "2025-03-01" in result
        assert "2025-03-05" in result


# ===================================================================
# gatekeeper_read_log tool
# ===================================================================

class TestGatekeeperReadLog:
    def test_latest_turnin_log(self, tmp_gk: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WORKAREA", str(tmp_gk))
        mcp = MockFastMCP()
        register_gatekeeper_tools(mcp, str(tmp_gk))
        result = mcp.tools["gatekeeper_read_log"](log_type="turnin")
        # Latest should be the 2025-03-05 log
        assert "FAIL" in result

    def test_specific_date_filter(self, tmp_gk: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WORKAREA", str(tmp_gk))
        mcp = MockFastMCP()
        register_gatekeeper_tools(mcp, str(tmp_gk))
        result = mcp.tools["gatekeeper_read_log"](
            identifier="2025-03-01", log_type="turnin"
        )
        assert "PASS" in result

    def test_invalid_log_type(self, tmp_gk: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WORKAREA", str(tmp_gk))
        mcp = MockFastMCP()
        register_gatekeeper_tools(mcp, str(tmp_gk))
        result = mcp.tools["gatekeeper_read_log"](log_type="invalid_type")
        assert "Unknown log_type" in result

    def test_preturnin_log(self, tmp_gk: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WORKAREA", str(tmp_gk))
        mcp = MockFastMCP()
        register_gatekeeper_tools(mcp, str(tmp_gk))
        result = mcp.tools["gatekeeper_read_log"](log_type="preturnin")
        assert "PASS" in result


# ===================================================================
# gatekeeper_latest_status tool
# ===================================================================

class TestGatekeeperLatestStatus:
    def test_latest_status(self, tmp_gk: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WORKAREA", str(tmp_gk))
        mcp = MockFastMCP()
        register_gatekeeper_tools(mcp, str(tmp_gk))
        result = mcp.tools["gatekeeper_latest_status"]()
        # Should include latest turnin log and pre-turnin check
        assert "Latest Turnin Log" in result
        assert "Pre-Turnin Check" in result

    def test_no_gatekeeper_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WORKAREA", str(tmp_path))
        mcp = MockFastMCP()
        register_gatekeeper_tools(mcp, str(tmp_path))
        result = mcp.tools["gatekeeper_latest_status"]()
        assert "not found" in result.lower()
