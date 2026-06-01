"""vManager VSIF group tools — VsifGroupsData family (vsif/groups/*)."""

from __future__ import annotations

from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = Any

from validation_mcp.settings import SettingsOrRepoRoot
from validation_mcp.runtime import (
    parse_json_argument,
    parse_json_object_argument,
    prepare_optional_post_data,
    prepare_post_data,
    run_vmanager_tool,
)


def register_vsif_group_tools(mcp: FastMCP, settings_or_repo_root: SettingsOrRepoRoot) -> None:
    """Register VSIF group tools."""

    @mcp.tool()
    async def vamp_vsif_group_get(group_id: int) -> str:
        """Fetch a single VSIF group by integer ID."""
        return await run_vmanager_tool(
            "vamp_vsif_group_get",
            settings_or_repo_root,
            lambda client, _settings: client.get_vsif_group(group_id),
        )

    @mcp.tool()
    async def vamp_vsif_groups_list(post_data_json: str) -> str:
        """List VSIF groups matching an RS specification.

        A slim projection covering identity, hierarchy, ownership,
        classification, and parent-session reference fields is applied by
        default. Include a ``"projection"`` key in ``post_data_json`` to
        override it, using ``null`` for all fields or a custom field list.

        When supplied, ``pageLength`` must be between 1 and the configured
        maximum page length; oversized explicit values return an error instead
        of being clamped.

        Returns JSON with ``vsif_groups`` and ``count`` fields.
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
            "vamp_vsif_groups_list",
            settings_or_repo_root,
            lambda client, _settings: client.list_vsif_groups(post_data),
        )

    @mcp.tool()
    async def vamp_vsif_group_create(post_data_json: str) -> str:
        """Create a VSIF group."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_group_create",
            settings_or_repo_root,
            lambda client, _settings: client.create_vsif_group(post_data),
        )

    @mcp.tool()
    async def vamp_vsif_group_update(post_data_json: str) -> str:
        """Update VSIF group attributes."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_group_update",
            settings_or_repo_root,
            lambda client, _settings: client.update_vsif_group(post_data),
        )

    @mcp.tool()
    async def vamp_vsif_group_delete(filter_json: str) -> str:
        """Delete VSIF groups matching a filter."""
        try:
            filter_dict = parse_json_object_argument(filter_json, label="filter")
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_group_delete",
            settings_or_repo_root,
            lambda client, _settings: client.delete_vsif_groups(filter_dict),
        )

    @mcp.tool()
    async def vamp_vsif_groups_list_for_session(
        sessions_filter_json: str,
        post_data_json: str = "{}",
    ) -> str:
        """List VSIF groups scoped to parent sessions.

        ``sessions_filter_json`` must decode to the parent-session filter.
        ``post_data_json`` may supply optional RS fields such as ``projection``
        or explicit paging keys; the untouched default ``"{}"`` preserves the
        backend default behavior by sending no extra body.

        When supplied, ``pageLength`` must be between 1 and the configured
        maximum page length; oversized explicit values return an error instead
        of being clamped.

        Returns JSON with ``vsif_groups`` and ``count`` fields.
        """
        try:
            sessions_filter = parse_json_object_argument(sessions_filter_json, label="sessions_filter")
            extra_data = prepare_optional_post_data(
                settings_or_repo_root,
                post_data_json,
                label="post_data",
                paginate=True,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_groups_list_for_session",
            settings_or_repo_root,
            lambda client, _settings: client.list_vsif_groups_for_session(sessions_filter, extra_data),
        )

    @mcp.tool()
    async def vamp_vsif_groups_list_for_group(
        groups_filter_json: str,
        post_data_json: str = "{}",
    ) -> str:
        """List VSIF groups scoped to parent groups.

        ``groups_filter_json`` must decode to the parent-group filter.
        ``post_data_json`` may supply optional RS fields such as ``projection``
        or explicit paging keys; the untouched default ``"{}"`` preserves the
        backend default behavior by sending no extra body.

        When supplied, ``pageLength`` must be between 1 and the configured
        maximum page length; oversized explicit values return an error instead
        of being clamped.

        Returns JSON with ``vsif_groups`` and ``count`` fields.
        """
        try:
            groups_filter = parse_json_object_argument(groups_filter_json, label="groups_filter")
            extra_data = prepare_optional_post_data(
                settings_or_repo_root,
                post_data_json,
                label="post_data",
                paginate=True,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_groups_list_for_group",
            settings_or_repo_root,
            lambda client, _settings: client.list_vsif_groups_for_group(groups_filter, extra_data),
        )
