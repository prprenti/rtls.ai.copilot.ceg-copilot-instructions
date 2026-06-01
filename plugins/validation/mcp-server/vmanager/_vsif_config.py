"""vManager VSIF configuration tools — VsifConfigData family (vsif/configurations/*)."""

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
    prepare_post_data,
    run_vmanager_tool,
)


def register_vsif_config_tools(mcp: FastMCP, settings_or_repo_root: SettingsOrRepoRoot) -> None:
    """Register VSIF configuration tools."""

    @mcp.tool()
    async def vamp_vsif_config_list(post_data_json: str) -> str:
        """List VSIF configurations.

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
            "vamp_vsif_config_list",
            settings_or_repo_root,
            lambda client, _settings: client.list_vsif_configs(post_data),
        )

    @mcp.tool()
    async def vamp_vsif_config_update(post_data_json: str) -> str:
        """Update VSIF configuration attributes."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_config_update",
            settings_or_repo_root,
            lambda client, _settings: client.update_vsif_config(post_data),
        )

    @mcp.tool()
    async def vamp_vsif_config_list_by_name(
        name: str,
        page_length: int = 1000,
    ) -> str:
        """List VSIF configurations whose name matches a pattern.

        ``page_length`` is clamped to the configured maximum page length.
        """
        try:
            bounded_length = bounded_page_length(settings_or_repo_root, page_length)
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_vsif_config_list_by_name",
            settings_or_repo_root,
            lambda client, _settings: client.list_vsif_configs_by_name(name, bounded_length),
        )
