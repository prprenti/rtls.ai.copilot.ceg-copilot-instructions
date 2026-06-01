"""vManager failure-cluster tools — FailureClusterData family (failure-clusters/*)."""

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
    parse_json_object_argument,
    prepare_post_data,
    run_vmanager_tool,
)


def register_failure_cluster_tools(mcp: FastMCP, settings_or_repo_root: SettingsOrRepoRoot) -> None:
    """Register failure-cluster vManager tools."""

    @mcp.tool()
    async def vamp_failure_cluster_list(post_data_json: str) -> str:
        """List failure clusters matching an RS specification.

        A slim projection covering identity, triage status, ownership, run
        count, timing, and cross-reference fields is applied by default.
        Include a ``"projection"`` key in ``post_data_json`` to override it,
        using ``null`` for all fields or a custom field list.

        When supplied, ``pageLength`` must be between 1 and the configured
        maximum page length; oversized explicit values return an error instead
        of being clamped.

        Returns JSON with ``failure_clusters`` and ``count`` fields.
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
            "vamp_failure_cluster_list",
            settings_or_repo_root,
            lambda client, _settings: client.list_failure_clusters(post_data),
        )

    @mcp.tool()
    async def vamp_failure_cluster_count(post_data_json: str) -> str:
        """Count failure clusters matching an RS specification."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_failure_cluster_count",
            settings_or_repo_root,
            lambda client, _settings: client.count_failure_clusters(post_data),
        )

    @mcp.tool()
    async def vamp_failure_cluster_get(cluster_id: int) -> str:
        """Fetch a single failure cluster by integer ID."""
        return await run_vmanager_tool(
            "vamp_failure_cluster_get",
            settings_or_repo_root,
            lambda client, _settings: client.get_failure_cluster(cluster_id),
        )

    @mcp.tool()
    async def vamp_failure_cluster_update(post_data_json: str) -> str:
        """Update failure-cluster attributes."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_failure_cluster_update",
            settings_or_repo_root,
            lambda client, _settings: client.update_failure_cluster(post_data),
        )

    @mcp.tool()
    async def vamp_failure_cluster_create(post_data_json: str) -> str:
        """Create a failure cluster."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_failure_cluster_create",
            settings_or_repo_root,
            lambda client, _settings: client.create_failure_cluster(post_data),
        )

    @mcp.tool()
    async def vamp_failure_cluster_delete(filter_json: str) -> str:
        """Delete failure clusters matching a filter."""
        try:
            filter_dict = parse_json_object_argument(filter_json, label="filter")
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_failure_cluster_delete",
            settings_or_repo_root,
            lambda client, _settings: client.delete_failure_clusters(filter_dict),
        )

    @mcp.tool()
    async def vamp_failure_clusters_for_runs(run_ids_json: str) -> str:
        """List failure clusters associated with specific run IDs."""
        try:
            run_ids = parse_json_array_argument(run_ids_json, label="run_ids_json")
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_failure_clusters_for_runs",
            settings_or_repo_root,
            lambda client, _settings: client.get_failure_clusters_for_runs(run_ids),
        )
