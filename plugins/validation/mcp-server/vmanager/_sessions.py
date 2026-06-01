"""vManager runtime session tools — SessionData family (sessions/*)."""

from __future__ import annotations

from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = Any

from validation_mcp.settings import SettingsOrRepoRoot
from validation_mcp.runtime import run_vmanager_tool


def register_session_tools(mcp: FastMCP, settings_or_repo_root: SettingsOrRepoRoot) -> None:
    """Register runtime session tools."""

    @mcp.tool()
    async def vamp_session_get_by_name(name: str) -> str:
        """Fetch a runtime session by exact name."""
        return await run_vmanager_tool(
            "vamp_session_get_by_name",
            settings_or_repo_root,
            lambda client, _settings: client.get_session_by_name(name),
        )
