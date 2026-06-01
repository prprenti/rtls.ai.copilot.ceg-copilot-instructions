"""vManager run↔failure-cluster association tools — RunFailureClusterData family."""

from __future__ import annotations

from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = Any

from validation_mcp.settings import SettingsOrRepoRoot
from validation_mcp.runtime import (
    parse_json_argument,
    parse_json_array_argument,
    prepare_post_data,
    run_vmanager_tool,
)


def register_run_failure_cluster_tools(mcp: FastMCP, settings_or_repo_root: SettingsOrRepoRoot) -> None:
    """Register run↔failure-cluster association tools."""

    @mcp.tool()
    async def vamp_run_failure_cluster_list(post_data_json: str) -> str:
        """List run↔failure-cluster associations.

        ``post_data_json`` should decode to an RS-style JSON object with an
        optional filter and any explicit paging keys you want to send.

        When supplied, ``pageLength`` must be between 1 and the configured
        maximum page length; oversized explicit values return an error instead
        of being clamped.

        Returns JSON with ``run_failure_clusters`` and ``count`` fields.
        """
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=True,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_run_failure_cluster_list",
            settings_or_repo_root,
            lambda client, _settings: client.list_run_failure_clusters(post_data),
        )

    @mcp.tool()
    async def vamp_run_failure_cluster_list_grouped(
        post_data_json: str,
        full_detail: bool = False,
    ) -> str:
        """List run↔failure-cluster associations grouped by cluster.

        ``post_data_json`` should decode to an RS-style JSON object with an
        optional filter and any explicit paging keys you want to send.
        Set ``full_detail`` to include more run-level fields inside each group.

        When supplied, ``pageLength`` must be between 1 and the configured
        maximum page length; oversized explicit values return an error instead
        of being clamped.

        Returns JSON with ``failure_clusters`` and ``cluster_count`` fields.
        """
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=True,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_run_failure_cluster_list_grouped",
            settings_or_repo_root,
            lambda client, _settings: client.list_run_failure_clusters_grouped(post_data, full_detail),
        )

    @mcp.tool()
    async def vamp_run_failure_cluster_update_association(post_data_json: str) -> str:
        """Update run↔failure-cluster associations."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_run_failure_cluster_update_association",
            settings_or_repo_root,
            lambda client, _settings: client.update_run_failure_cluster_association(post_data),
        )

    @mcp.tool()
    async def vamp_run_failures_for_team(
        team: str,
        days: int = 15,
    ) -> str:
        """List wip/new failed runs for a team within the last N days."""
        return await run_vmanager_tool(
            "vamp_run_failures_for_team",
            settings_or_repo_root,
            lambda client, _settings: client.list_run_failures_for_team(team, days),
        )

    @mcp.tool()
    async def vamp_run_failures_in_datetime(
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
    ) -> str:
        """List wip/new failed runs submitted after a rolling time window."""
        return await run_vmanager_tool(
            "vamp_run_failures_in_datetime",
            settings_or_repo_root,
            lambda client, _settings: client.list_run_failures_in_datetime(days, hours, minutes),
        )

    @mcp.tool()
    async def vamp_run_failures_needs_rerun() -> str:
        """List failed runs whose rerun_status is needs_rerun."""
        return await run_vmanager_tool(
            "vamp_run_failures_needs_rerun",
            settings_or_repo_root,
            lambda client, _settings: client.list_run_failures_needs_rerun(),
        )

    @mcp.tool()
    async def vamp_run_failures_for_result_ids(result_ids_json: str) -> str:
        """List run↔failure-cluster associations for specific run IDs."""
        try:
            result_ids = parse_json_array_argument(result_ids_json, label="result_ids_json")
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_run_failures_for_result_ids",
            settings_or_repo_root,
            lambda client, _settings: client.list_run_failures_for_result_ids(result_ids),
        )
