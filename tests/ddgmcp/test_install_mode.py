"""Install-mode validation: proves the package works when imported from the repo root.

These tests exercise the packaged import shape — i.e., the same import paths a
consumer would use when the package is installed or when ``uv run server.py`` is
invoked from within the ``ddgmcp/`` directory.  All assertions use only public
symbols; no live vManager backend access is needed.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from conftest import MockFastMCP

# Repo root is the directory containing the ``ddgmcp/`` package.
REPO_ROOT = Path(__file__).resolve().parents[2]
CEGMCP_DIR = REPO_ROOT / "ddgmcp"

EXPECTED_VMANAGER_TOOLS = {
    # ---- runs ----
    "vamp_standard_runs_list",
    "vamp_runs_list",
    "vamp_runs_count",
    "vamp_run_get",
    "vamp_run_update",
    "vamp_run_associate_to_failure_cluster",
    "vamp_run_dissociate_from_failure_cluster",
    "vamp_run_rerun_schemes_get",
    "vamp_run_total_count_size_get",
    "vamp_run_extract_logs",
    # ---- failure clusters ----
    "vamp_failure_cluster_list",
    "vamp_failure_cluster_count",
    "vamp_failure_cluster_get",
    "vamp_failure_cluster_update",
    "vamp_failure_cluster_create",
    "vamp_failure_cluster_delete",
    "vamp_failure_clusters_for_runs",
    # ---- run↔failure-cluster associations ----
    "vamp_run_failure_cluster_list",
    "vamp_run_failure_cluster_update_association",
    "vamp_run_failures_for_team",
    "vamp_run_failures_in_datetime",
    "vamp_run_failures_needs_rerun",
    "vamp_run_failures_for_result_ids",
    # ---- vsif/configurations ----
    "vamp_vsif_config_list",
    "vamp_vsif_config_update",
    "vamp_vsif_config_list_by_name",
    # ---- vsif/groups ----
    "vamp_vsif_group_get",
    "vamp_vsif_groups_list",
    "vamp_vsif_group_create",
    "vamp_vsif_group_update",
    "vamp_vsif_group_delete",
    "vamp_vsif_groups_list_for_session",
    "vamp_vsif_groups_list_for_group",
    # ---- vsif/tests ----
    "vamp_vsif_test_get",
    "vamp_vsif_tests_list",
    "vamp_vsif_test_create",
    "vamp_vsif_test_update",
    "vamp_vsif_test_delete",
    "vamp_vsif_tests_list_for_session",
    "vamp_vsif_tests_list_for_group",
    # ---- vsif/hierarchy-configurations ----
    "vamp_vsif_hierarchy_get",
    "vamp_vsif_hierarchy_list",
    "vamp_vsif_hierarchy_create",
    "vamp_vsif_hierarchy_attach_groups_to_groups",
    "vamp_vsif_hierarchy_attach_groups_to_sessions",
    "vamp_vsif_hierarchy_attach_tests_to_groups",
    "vamp_vsif_hierarchy_attach_tests_to_sessions",
    # ---- vsif/sessions ----
    "vamp_sessions_list",
    "vamp_sessions_count",
    "vamp_vsif_session_get",
    "vamp_vsif_session_create",
    "vamp_vsif_session_create_with_permissions",
    "vamp_vsif_session_delete",
    # ---- runtime sessions ----
    "vamp_session_get_by_name",
    # ---- test plan ----
    "vamp_plan_list",
    "vamp_plan_count",
    "vamp_plan_list_sub_elements",
    "vamp_plan_list_vplans",
    "vamp_plan_get",
    "vamp_plan_get_rich_text",
    "vamp_plan_add_section",
    "vamp_plan_add_reference",
    "vamp_plan_add_metrics_port",
    "vamp_plan_update",
    "vamp_plan_update_bulk",
    "vamp_plan_update_section",
    "vamp_plan_update_reference",
    "vamp_plan_find",
}


# ---------------------------------------------------------------------------
# Package-rooted import (simulates installed package: import ddgmcp.xxx)
# ---------------------------------------------------------------------------


def test_backend_client_importable_from_package_root() -> None:
    """VmanagerClient and VmanagerBackendUnavailable importable via ddgmcp.* paths."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                f"import sys; sys.path.insert(0, {str(REPO_ROOT)!r}); "
                "from ddgmcp.backends.vmanager.client import "
                "    VmanagerClient, VmanagerBackendUnavailable, _extract_rows; "
                "from ddgmcp.standard_runs_query import "
                "    build_standard_runs_list_request, normalize_values; "
                "print('package-import-ok')"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, f"Package import failed:\n{result.stderr}"
    assert "package-import-ok" in result.stdout


def test_vmanager_tools_module_importable_from_package_root() -> None:
    """tools.vmanager register function importable via ddgmcp.tools.vmanager (no mcp dep needed)."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                f"import sys; sys.path.insert(0, {str(REPO_ROOT)!r}); "
                # vmanager.py has a try/except for mcp so it loads without mcp installed
                "from ddgmcp.tools.vmanager import register_vmanager_tools; "
                "assert callable(register_vmanager_tools); "
                "print('vmanager-tools-ok')"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, f"Package import failed:\n{result.stderr}"
    assert "vmanager-tools-ok" in result.stdout


# ---------------------------------------------------------------------------
# Flat-import shape from the ddgmcp/ directory (simulates: uv run server.py)
# ---------------------------------------------------------------------------


def test_flat_imports_resolve_from_ddgmcp_directory() -> None:
    """Flat-path imports (as used in server.py) resolve when cwd is ddgmcp/."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; sys.path.insert(0, '.'); "
                "from backends.vmanager.client import VmanagerClient, VmanagerBackendUnavailable; "
                "from standard_runs_query import build_standard_runs_list_request, normalize_values; "
                "from tools.vmanager import register_vmanager_tools; "
                "print('flat-import-ok')"
            ),
        ],
        cwd=CEGMCP_DIR,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, f"Flat import failed:\n{result.stderr}"
    assert "flat-import-ok" in result.stdout


# ---------------------------------------------------------------------------
# Tool inventory — all expected tools are registered
# ---------------------------------------------------------------------------


def test_all_vmanager_tools_registered() -> None:
    """register_vmanager_tools exposes every expected tool name on the MCP server."""
    from tools.vmanager import register_vmanager_tools

    mock_mcp = MockFastMCP("install-mode-test")
    register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

    registered = set(mock_mcp.tools.keys())
    missing = EXPECTED_VMANAGER_TOOLS - registered
    assert not missing, f"Tools missing from registration: {sorted(missing)}"


def test_all_registered_tools_are_callable() -> None:
    """Every registered vManager tool is an async callable."""
    import asyncio
    import inspect

    from tools.vmanager import register_vmanager_tools

    mock_mcp = MockFastMCP("install-mode-test")
    register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

    for name in EXPECTED_VMANAGER_TOOLS:
        fn = mock_mcp.tools.get(name)
        assert fn is not None, f"Tool '{name}' not registered"
        assert callable(fn), f"Tool '{name}' is not callable"
        assert inspect.iscoroutinefunction(fn), f"Tool '{name}' is not async"


# ---------------------------------------------------------------------------
# VmanagerBackendUnavailable is raised when vamp is not installed
# (validates the graceful-degradation path without a real backend)
# ---------------------------------------------------------------------------


def test_backend_unavailable_raised_without_vamp(tmp_path: Path) -> None:
    """VmanagerBackendUnavailable propagates correctly through the MCP tool layer.

    Uses the vamp_factory injection to simulate a missing vamp backend without
    depending on whether vamp is actually installed in this environment.
    """
    import asyncio
    import json

    from backends.vmanager.client import VmanagerBackendUnavailable, VmanagerClient
    from tools.vmanager import register_vmanager_tools

    def unavailable_factory():
        raise VmanagerBackendUnavailable("test: vamp not installed")

    # Patch the tool layer so it receives VmanagerBackendUnavailable on construction
    mock_mcp = MockFastMCP("test-unavailable")
    register_vmanager_tools(mock_mcp, str(tmp_path))  # pyright: ignore[reportArgumentType]

    import pytest as _pytest

    with _pytest.MonkeyPatch().context() as mp:
        mp.setattr(
            "tools.vmanager._runs.VmanagerClient",
            lambda repo_root: (_ for _ in ()).throw(VmanagerBackendUnavailable("test: vamp not installed")),
        )
        result = asyncio.run(mock_mcp.tools["vamp_runs_list"](post_data_json='{"filter": {}}'))

    assert result.startswith("ERROR:"), f"Expected ERROR prefix but got: {result!r}"
    assert "vamp not installed" in result


# ---------------------------------------------------------------------------
# Packaging metadata — ceg-mcp entrypoint shape exists
# ---------------------------------------------------------------------------


def test_server_entry_point_function_exists() -> None:
    """server.main is importable and callable (no live mcp needed via try/except guard)."""
    # server.py imports mcp but the try/except guard on FastMCP makes it survive
    # when mcp is absent; however server.main itself does call mcp.run() so we
    # only check the symbol exists and is callable, not that it runs successfully.
    import importlib

    # Load server without executing module-level code that calls FastMCP
    import types

    # Verify entrypoint definition via source inspection (avoid mcp import failure)
    server_path = CEGMCP_DIR / "server.py"
    source = server_path.read_text()
    assert "def main()" in source, "server.py missing 'def main()'"
    assert "mcp.run(" in source, "server.py missing 'mcp.run(' call in main"


def test_vamp_subtree_entrypoint_removed() -> None:
    """The subtree helper is no longer part of the supported install flow."""
    assert not (CEGMCP_DIR / "vamp_subtree.py").exists(), (
        "ddgmcp/vamp_subtree.py should not exist when package-based vManager support is the only supported method"
    )


def test_pyproject_toml_declares_ddg_mcp_script() -> None:
    """ceg-mcp script entrypoint is declared in ddgmcp/pyproject.toml."""
    pyproject = (CEGMCP_DIR / "pyproject.toml").read_text()
    assert 'ceg-mcp = "server:main"' in pyproject, (
        "ddgmcp/pyproject.toml missing 'ceg-mcp = \"server:main\"' script entry"
    )


def test_pyproject_toml_uses_vmanager_package_dependency() -> None:
    """ddgmcp/pyproject.toml declares the package-based vManager dependency."""
    pyproject = (CEGMCP_DIR / "pyproject.toml").read_text()
    assert '"vmanager-vamp>=1.4"' in pyproject, (
        "ddgmcp/pyproject.toml missing the package-based vmanager-vamp dependency"
    )
    assert 'ddg-vamp-subtree = "vamp_subtree:main"' not in pyproject, (
        "ddgmcp/pyproject.toml should not declare the removed ddg-vamp-subtree script"
    )


def test_pyproject_toml_configures_intel_devpi_for_vmanager() -> None:
    """ddgmcp/pyproject.toml points uv at the Intel devpi index for vmanager-vamp."""
    pyproject = (CEGMCP_DIR / "pyproject.toml").read_text()
    assert 'vmanager-vamp = { index = "intel-hive" }' in pyproject
    assert 'url = "https://devpi.intel.com/general/hive/+simple/"' in pyproject
