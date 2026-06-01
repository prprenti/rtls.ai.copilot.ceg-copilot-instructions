"""vManager tools package — registers all endpoint-oriented vManager MCP tools.

Submodules correspond to vamp data-class families:
  _runs               — TestRunData tools
  _failure_clusters   — FailureClusterData tools
  _run_failure_clusters — RunFailureClusterData tools
  _vsif_config        — VsifConfigData tools
  _vsif_groups        — VsifGroupsData tools
  _vsif_tests         — VsifTestsData tools
  _vsif_hierarchy     — VsifHierarchyData tools
  _vsif_sessions      — VsifSessionsData tools (and list/count from the old vsif_sessions)
  _sessions           — SessionData (runtime sessions) tools
  _plan               — TestPlanQueries tools
"""

from __future__ import annotations

from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = Any

from validation_mcp.settings import SettingsOrRepoRoot
from validation_mcp.runtime import coerce_settings

from ._runs import register_run_tools
from ._failure_clusters import register_failure_cluster_tools
from ._run_failure_clusters import register_run_failure_cluster_tools
from ._vsif_config import register_vsif_config_tools
from ._vsif_groups import register_vsif_group_tools
from ._vsif_tests import register_vsif_test_tools
from ._vsif_hierarchy import register_vsif_hierarchy_tools
from ._vsif_sessions import register_vsif_session_tools
from ._sessions import register_session_tools
from ._plan import register_plan_tools


def register_vmanager_tools(mcp: FastMCP, settings_or_repo_root: SettingsOrRepoRoot) -> None:
    """Register all vManager-backed tools on the MCP server."""
    settings = coerce_settings(settings_or_repo_root)
    register_run_tools(mcp, settings)
    register_failure_cluster_tools(mcp, settings)
    register_run_failure_cluster_tools(mcp, settings)
    register_vsif_config_tools(mcp, settings)
    register_vsif_group_tools(mcp, settings)
    register_vsif_test_tools(mcp, settings)
    register_vsif_hierarchy_tools(mcp, settings)
    register_vsif_session_tools(mcp, settings)
    register_session_tools(mcp, settings)
    register_plan_tools(mcp, settings)
