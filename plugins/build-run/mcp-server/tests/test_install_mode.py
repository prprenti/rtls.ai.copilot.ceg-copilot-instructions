"""Install-mode validation: proves the package works when imported from the build-run plugin.

These tests exercise the packaged import shape — i.e., the same import paths a
consumer would use when the package is installed or when ``uv run server_build_run.py`` is
invoked from within the ``plugins/build-run/mcp-server/`` directory.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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

# Repo root is the directory containing the ``plugins/`` directory.
REPO_ROOT = Path(__file__).resolve().parents[4]
MCP_SERVER_DIR = REPO_ROOT / "plugins" / "build-run" / "mcp-server"


# ---------------------------------------------------------------------------
# Flat-import shape from the ddgmcp/ directory (simulates: uv run server_ddg.py)
# ---------------------------------------------------------------------------


def test_flat_imports_resolve_from_mcp_server_directory() -> None:
    """Flat-path imports (as used in server_build_run.py) resolve when cwd is mcp-server/."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; sys.path.insert(0, '.'); "
                "from commands import register_command_tools; "
                "print('flat-import-ok')"
            ),
        ],
        cwd=MCP_SERVER_DIR,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, f"Flat import failed:\n{result.stderr}"
    assert "flat-import-ok" in result.stdout


# ---------------------------------------------------------------------------
# Tool inventory — expected tools are registered
# ---------------------------------------------------------------------------


def test_command_tools_registered() -> None:
    """register_command_tools exposes the expected tool names."""
    from commands import register_command_tools

    mock_mcp = MockFastMCP("install-mode-test")
    register_command_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

    expected = {"check_environment", "run_grdlbuild", "run_make"}
    registered = set(mock_mcp.tools.keys())
    missing = expected - registered
    assert not missing, f"Tools missing from registration: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Packaging metadata — ceg-mcp entrypoint shape exists
# ---------------------------------------------------------------------------


def test_server_entry_point_function_exists() -> None:
    """server_build_run.main is importable and callable."""
    server_path = MCP_SERVER_DIR / "server_build_run.py"
    source = server_path.read_text()
    assert "def main()" in source, "server_build_run.py missing 'def main()'"
    assert "mcp.run(" in source, "server_build_run.py missing 'mcp.run(' call in main"


def test_pyproject_toml_declares_build_run_mcp_script() -> None:
    """build-run-mcp script entrypoint is declared in mcp-server/pyproject.toml."""
    pyproject = (MCP_SERVER_DIR / "pyproject.toml").read_text()
    assert 'build-run-mcp = "server_build_run:main"' in pyproject, (
        "mcp-server/pyproject.toml missing 'build-run-mcp = \"server_build_run:main\"' script entry"
    )
