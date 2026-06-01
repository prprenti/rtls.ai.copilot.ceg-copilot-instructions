"""vManager VSIF session tools — VsifSessionsData family (vsif/sessions/*)."""

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
    prepare_post_data,
    run_vmanager_tool,
)


def register_vsif_session_tools(mcp: FastMCP, settings_or_repo_root: SettingsOrRepoRoot) -> None:
    """Register VSIF session tools."""

    @mcp.tool()
    async def vamp_sessions_list(post_data_json: str) -> str:
        """List VSIF sessions matching an RS specification.

        A slim projection covering identity, status, ownership,
        classification, timing, and VSIF config reference fields is applied by
        default so responses stay AI-sized. Include an explicit
        ``"projection"`` key in ``post_data_json`` to override it.

        When supplied, ``pageLength`` must be between 1 and the configured
        maximum page length; oversized explicit values return an error instead
        of being clamped.
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
            "vamp_sessions_list",
            settings_or_repo_root,
            lambda client, _settings: client.list_sessions(post_data),
        )

    @mcp.tool()
    async def vamp_sessions_count(post_data_json: str) -> str:
        """Count VSIF sessions matching an RS specification.

        ``post_data_json`` must decode to a JSON object with the RS filter body
        to send to vManager. Pagination keys, when present, are forwarded
        unchanged to the backend count path.
        """
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_sessions_count",
            settings_or_repo_root,
            lambda client, _settings: client.count_sessions(post_data),
        )

    @mcp.tool()
    async def vamp_vsif_session_get(session_id: int) -> str:
        """Fetch a single VSIF session by integer ID."""
        return await run_vmanager_tool(
            "vamp_vsif_session_get",
            settings_or_repo_root,
            lambda client, _settings: client.get_vsif_session(session_id),
        )

    @mcp.tool()
    async def vamp_vsif_session_create(post_data_json: str) -> str:
        """Create a VSIF session."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_session_create",
            settings_or_repo_root,
            lambda client, _settings: client.create_vsif_session(post_data),
        )

    @mcp.tool()
    async def vamp_vsif_session_create_with_permissions(post_data_json: str) -> str:
        """Create a VSIF session with permissions."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_session_create_with_permissions",
            settings_or_repo_root,
            lambda client, _settings: client.create_vsif_session_with_permissions(post_data),
        )

    @mcp.tool()
    async def vamp_vsif_session_delete(filter_json: str) -> str:
        """Delete VSIF sessions matching a filter."""
        try:
            filter_dict = parse_json_object_argument(filter_json, label="filter")
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_session_delete",
            settings_or_repo_root,
            lambda client, _settings: client.delete_vsif_sessions(filter_dict),
        )
