"""vManager VSIF hierarchy tools — VsifHierarchyData family (vsif/hierarchy-configurations/*)."""

from __future__ import annotations

from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = Any

from validation_mcp.settings import SettingsOrRepoRoot
from validation_mcp.runtime import (
    bounded_page_length,
    parse_json_argument,
    parse_json_object_argument,
    prepare_post_data,
    run_vmanager_tool,
)


def register_vsif_hierarchy_tools(mcp: FastMCP, settings_or_repo_root: SettingsOrRepoRoot) -> None:
    """Register VSIF hierarchy configuration tools."""

    @mcp.tool()
    async def vamp_vsif_hierarchy_get(hierarchy_id: int) -> str:
        """Fetch a single hierarchy configuration by integer ID."""
        return await run_vmanager_tool(
            "vamp_vsif_hierarchy_get",
            settings_or_repo_root,
            lambda client, _settings: client.get_vsif_hierarchy(hierarchy_id),
        )

    @mcp.tool()
    async def vamp_vsif_hierarchy_list(
        parent_id: int,
        page_length: int = 100,
        page_offset: int = 0,
    ) -> str:
        """List hierarchy configurations under a VSIF parent entity."""
        try:
            bounded_length = bounded_page_length(settings_or_repo_root, page_length)
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_hierarchy_list",
            settings_or_repo_root,
            lambda client, _settings: client.list_vsif_hierarchy(parent_id, bounded_length, page_offset),
        )

    @mcp.tool()
    async def vamp_vsif_hierarchy_create(post_data_json: str) -> str:
        """Create a hierarchy configuration."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_hierarchy_create",
            settings_or_repo_root,
            lambda client, _settings: client.create_vsif_hierarchy(post_data),
        )

    @mcp.tool()
    async def vamp_vsif_hierarchy_attach_groups_to_groups(
        hierarchy_config_id: int,
        child_groups_filter_json: str,
        parent_groups_filter_json: str,
    ) -> str:
        """Attach VSIF groups to VSIF groups under a hierarchy configuration."""
        try:
            child_filter = parse_json_object_argument(child_groups_filter_json, label="child_groups_filter")
            parent_filter = parse_json_object_argument(parent_groups_filter_json, label="parent_groups_filter")
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_hierarchy_attach_groups_to_groups",
            settings_or_repo_root,
            lambda client, _settings: client.attach_vsif_hierarchy_groups_to_groups(
                hierarchy_config_id,
                child_filter,
                parent_filter,
            ),
        )

    @mcp.tool()
    async def vamp_vsif_hierarchy_attach_groups_to_sessions(
        hierarchy_config_id: int,
        groups_filter_json: str,
        sessions_filter_json: str,
    ) -> str:
        """Attach VSIF groups to VSIF sessions under a hierarchy configuration."""
        try:
            groups_filter = parse_json_object_argument(groups_filter_json, label="groups_filter")
            sessions_filter = parse_json_object_argument(sessions_filter_json, label="sessions_filter")
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_hierarchy_attach_groups_to_sessions",
            settings_or_repo_root,
            lambda client, _settings: client.attach_vsif_hierarchy_groups_to_sessions(
                hierarchy_config_id,
                groups_filter,
                sessions_filter,
            ),
        )

    @mcp.tool()
    async def vamp_vsif_hierarchy_attach_tests_to_groups(
        hierarchy_config_id: int,
        tests_filter_json: str,
        groups_filter_json: str,
    ) -> str:
        """Attach VSIF tests to VSIF groups under a hierarchy configuration."""
        try:
            tests_filter = parse_json_object_argument(tests_filter_json, label="tests_filter")
            groups_filter = parse_json_object_argument(groups_filter_json, label="groups_filter")
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_hierarchy_attach_tests_to_groups",
            settings_or_repo_root,
            lambda client, _settings: client.attach_vsif_hierarchy_tests_to_groups(
                hierarchy_config_id,
                tests_filter,
                groups_filter,
            ),
        )

    @mcp.tool()
    async def vamp_vsif_hierarchy_attach_tests_to_sessions(
        hierarchy_config_id: int,
        tests_filter_json: str,
        sessions_filter_json: str,
    ) -> str:
        """Attach VSIF tests to VSIF sessions under a hierarchy configuration."""
        try:
            tests_filter = parse_json_object_argument(tests_filter_json, label="tests_filter")
            sessions_filter = parse_json_object_argument(sessions_filter_json, label="sessions_filter")
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_hierarchy_attach_tests_to_sessions",
            settings_or_repo_root,
            lambda client, _settings: client.attach_vsif_hierarchy_tests_to_sessions(
                hierarchy_config_id,
                tests_filter,
                sessions_filter,
            ),
        )
