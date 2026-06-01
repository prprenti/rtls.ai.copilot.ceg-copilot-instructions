"""vManager VSIF test tools — VsifTestsData family (vsif/tests/*)."""

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


def register_vsif_test_tools(mcp: FastMCP, settings_or_repo_root: SettingsOrRepoRoot) -> None:
    """Register VSIF test tools."""

    @mcp.tool()
    async def vamp_vsif_test_get(test_id: int) -> str:
        """Fetch a single VSIF test by integer ID."""
        return await run_vmanager_tool(
            "vamp_vsif_test_get",
            settings_or_repo_root,
            lambda client, _settings: client.get_vsif_test(test_id),
        )

    @mcp.tool()
    async def vamp_vsif_tests_list(post_data_json: str) -> str:
        """List VSIF tests matching an RS specification.

        A slim projection covering identity, execution status, seed,
        ownership, and parent group/run reference fields is applied by
        default. Include a ``"projection"`` key in ``post_data_json`` to
        override it, using ``null`` for all fields or a custom field list.

        When supplied, ``pageLength`` must be between 1 and the configured
        maximum page length; oversized explicit values return an error instead
        of being clamped.

        Returns JSON with ``vsif_tests`` and ``count`` fields.
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
            "vamp_vsif_tests_list",
            settings_or_repo_root,
            lambda client, _settings: client.list_vsif_tests(post_data),
        )

    @mcp.tool()
    async def vamp_vsif_test_create(post_data_json: str) -> str:
        """Create a VSIF test."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_test_create",
            settings_or_repo_root,
            lambda client, _settings: client.create_vsif_test(post_data),
        )

    @mcp.tool()
    async def vamp_vsif_test_update(post_data_json: str) -> str:
        """Update VSIF test attributes."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_test_update",
            settings_or_repo_root,
            lambda client, _settings: client.update_vsif_test(post_data),
        )

    @mcp.tool()
    async def vamp_vsif_test_delete(filter_json: str) -> str:
        """Delete VSIF tests matching a filter."""
        try:
            filter_dict = parse_json_object_argument(filter_json, label="filter")
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_test_delete",
            settings_or_repo_root,
            lambda client, _settings: client.delete_vsif_tests(filter_dict),
        )

    @mcp.tool()
    async def vamp_vsif_tests_list_for_session(
        sessions_filter_json: str,
        post_data_json: str = "{}",
    ) -> str:
        """List VSIF tests scoped to parent sessions.

        ``sessions_filter_json`` must decode to the parent-session filter.
        ``post_data_json`` may supply optional RS fields such as ``projection``
        or explicit paging keys; the untouched default ``"{}"`` preserves the
        backend default behavior by sending no extra body.

        When supplied, ``pageLength`` must be between 1 and the configured
        maximum page length; oversized explicit values return an error instead
        of being clamped.

        Returns JSON with ``vsif_tests`` and ``count`` fields.
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
            "vamp_vsif_tests_list_for_session",
            settings_or_repo_root,
            lambda client, _settings: client.list_vsif_tests_for_session(sessions_filter, extra_data),
        )

    @mcp.tool()
    async def vamp_vsif_tests_list_for_group(
        groups_filter_json: str,
        post_data_json: str = "{}",
    ) -> str:
        """List VSIF tests scoped to parent groups.

        ``groups_filter_json`` must decode to the parent-group filter.
        ``post_data_json`` may supply optional RS fields such as ``projection``
        or explicit paging keys; the untouched default ``"{}"`` preserves the
        backend default behavior by sending no extra body.

        When supplied, ``pageLength`` must be between 1 and the configured
        maximum page length; oversized explicit values return an error instead
        of being clamped.

        Returns JSON with ``vsif_tests`` and ``count`` fields.
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
            "vamp_vsif_tests_list_for_group",
            settings_or_repo_root,
            lambda client, _settings: client.list_vsif_tests_for_group(groups_filter, extra_data),
        )
