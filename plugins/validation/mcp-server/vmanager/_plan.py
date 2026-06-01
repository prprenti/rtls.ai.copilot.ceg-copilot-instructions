"""vManager test-plan tools — TestPlanQueries family (planning/*, vplan/*)."""

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


def register_plan_tools(mcp: FastMCP, settings_or_repo_root: SettingsOrRepoRoot) -> None:
    """Register test-plan vManager tools."""

    @mcp.tool()
    async def vamp_plan_list(post_data_json: str) -> str:
        """List test plan entries using the compatibility wrapper.

        When the backend lacks a generic plan list endpoint, this tool falls
        back to the flat sub-element listing path. Include a ``"projection"``
        key in ``post_data_json`` to override any default field selection.

        When supplied, ``pageLength`` must be between 1 and the configured
        maximum page length; oversized explicit values return an error instead
        of being clamped.

        Returns JSON with ``plan_entries`` and ``count`` fields.
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
            "vamp_plan_list",
            settings_or_repo_root,
            lambda client, _settings: client.list_plan_entries(post_data),
        )

    @mcp.tool()
    async def vamp_plan_list_sub_elements(post_data_json: str) -> str:
        """List flat vPlan sub-elements.

        A slim projection covering identity, structure, planning attributes,
        progress, and navigation fields is applied by default. Include a
        ``"projection"`` key in ``post_data_json`` to override it, using
        ``null`` for all fields or a custom field list.

        When supplied, ``pageLength`` must be between 1 and the configured
        maximum page length; oversized explicit values return an error instead
        of being clamped.

        Returns JSON with ``sub_elements`` and ``count`` fields.
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
            "vamp_plan_list_sub_elements",
            settings_or_repo_root,
            lambda client, _settings: client.list_plan_sub_elements(post_data),
        )

    @mcp.tool()
    async def vamp_plan_count(post_data_json: str) -> str:
        """Count test plan entries matching an RS specification."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_plan_count",
            settings_or_repo_root,
            lambda client, _settings: client.count_plan_entries(post_data),
        )

    @mcp.tool()
    async def vamp_plan_list_vplans(post_data_json: str = "{}") -> str:
        """List available vPlans."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_plan_list_vplans",
            settings_or_repo_root,
            lambda client, _settings: client.list_vplans(post_data),
        )

    @mcp.tool()
    async def vamp_plan_get(post_data_json: str) -> str:
        """Get a vPlan by specification."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_plan_get",
            settings_or_repo_root,
            lambda client, _settings: client.get_vplan(post_data),
        )

    @mcp.tool()
    async def vamp_plan_get_rich_text(post_data_json: str) -> str:
        """Get rich text for a vPlan element."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_plan_get_rich_text",
            settings_or_repo_root,
            lambda client, _settings: client.get_plan_rich_text(post_data),
        )

    @mcp.tool()
    async def vamp_plan_add_section(post_data_json: str) -> str:
        """Add a section to a vPlan."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_plan_add_section",
            settings_or_repo_root,
            lambda client, _settings: client.add_plan_section(post_data),
        )

    @mcp.tool()
    async def vamp_plan_add_reference(post_data_json: str) -> str:
        """Add a reference to a vPlan."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_plan_add_reference",
            settings_or_repo_root,
            lambda client, _settings: client.add_plan_reference(post_data),
        )

    @mcp.tool()
    async def vamp_plan_add_metrics_port(post_data_json: str) -> str:
        """Add a metrics port to a vPlan."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_plan_add_metrics_port",
            settings_or_repo_root,
            lambda client, _settings: client.add_plan_metrics_port(post_data),
        )

    @mcp.tool()
    async def vamp_plan_update(post_data_json: str) -> str:
        """Update a vPlan."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_plan_update",
            settings_or_repo_root,
            lambda client, _settings: client.update_plan(post_data),
        )

    @mcp.tool()
    async def vamp_plan_update_bulk(post_data_json: str) -> str:
        """Bulk update vPlan entries."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_plan_update_bulk",
            settings_or_repo_root,
            lambda client, _settings: client.update_plan_bulk(post_data),
        )

    @mcp.tool()
    async def vamp_plan_update_section(post_data_json: str) -> str:
        """Update a vPlan section."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_plan_update_section",
            settings_or_repo_root,
            lambda client, _settings: client.update_plan_section(post_data),
        )

    @mcp.tool()
    async def vamp_plan_update_reference(post_data_json: str) -> str:
        """Update a vPlan reference."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_plan_update_reference",
            settings_or_repo_root,
            lambda client, _settings: client.update_plan_reference(post_data),
        )

    @mcp.tool()
    async def vamp_plan_find(
        name_fragment: str,
        case_sensitive: bool = False,
        limit: int | None = None,
    ) -> str:
        """Find vPlans whose name contains a given fragment.

        By default this returns every match to preserve the long-standing tool
        contract and preserves the backend order. Pass ``limit`` to request a
        bounded subset; ``0`` returns no matches, and positive values above
        the configured maximum page length are clamped to that cap. The limit
        only bounds returned matches; this tool still fetches the full vPlan
        list from the backend before filtering.
        """
        if not name_fragment.strip():
            return "ERROR: name_fragment must not be empty or whitespace"

        if limit is not None and limit < 0:
            return "ERROR: limit must be >= 0"

        if limit is None:
            bounded_limit = None
        elif limit == 0:
            bounded_limit = 0
        else:
            bounded_limit = bounded_page_length(settings_or_repo_root, limit)

        def _find_matches(client, _settings):
            result = client.list_vplans({})
            all_vplans = result.get("vplans", [])
            if case_sensitive:
                matching = [vp for vp in all_vplans if name_fragment in (vp.get("name") or "")]
            else:
                fragment_lower = name_fragment.lower()
                matching = [
                    vp for vp in all_vplans
                    if fragment_lower in (vp.get("name") or "").lower()
                ]
            limited = matching[:bounded_limit] if bounded_limit is not None else matching
            return {
                "vplans": limited,
                "count": len(matching),
                "returned_count": len(limited),
                "total_checked": len(all_vplans),
                "fragment": name_fragment,
                "truncated": len(limited) < len(matching),
            }

        return await run_vmanager_tool(
            "vamp_plan_find",
            settings_or_repo_root,
            _find_matches,
        )
