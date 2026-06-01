"""vManager run tools — TestRunData family (runs/*)."""

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


def _csv_values(raw: str) -> tuple[str, ...]:
    values = tuple(part.strip() for part in raw.split(",") if part.strip())
    if not values:
        raise ValueError("value list must contain at least one entry")
    return values


def register_run_tools(mcp: FastMCP, settings_or_repo_root: SettingsOrRepoRoot) -> None:
    """Register run-related vManager tools."""

    @mcp.tool()
    async def vamp_standard_runs_list(
        team: str,
        steppings: str,
        dut: str = "",
        page_length: int = 100,
        page_offset: int = 0,
        skip_steppings: bool = False,
    ) -> str:
        """List runs using the standard query shape (status + team + dut + steppings).

        A slim projection covering identity, status, triage, classification,
        timing, location, rerun tracking, and build context is applied by default
        so responses are AI-sized.  The projected field list is visible in the
        returned ``"request"`` key.  There is no override path for this tool;
        use ``vamp_runs_list`` with an explicit ``"projection"`` key for custom
        field sets.

        Args:
            team: One team or a comma-separated list of teams.
            steppings: One stepping or a comma-separated list of steppings.
            dut: Optional DUT or comma-separated DUT list. When omitted, the tool derives
                DUT from the team naming convention and still sends an i_dut filter.
            page_length: Number of rows to request. Values above the server cap are
                clamped to the configured maximum page length.
            page_offset: Starting offset for paging.
            skip_steppings: When True, omits the i_steps filter entirely. Use this
                for discovery when the exact stepping label is unknown or when
                a previous call failed with a backend 400 caused by an invalid
                i_steps value. The emitted request will reflect the omission.

        Returns JSON describing the emitted runs/list request and the returned rows.
        """
        try:
            team_values = _csv_values(team)
            stepping_values = _csv_values(steppings)
            dut_values = _csv_values(dut) if dut.strip() else None
            bounded_length = bounded_page_length(settings_or_repo_root, page_length)
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_standard_runs_list",
            settings_or_repo_root,
            lambda client, _settings: client.query_standard_runs(
                team=team_values,
                steppings=stepping_values,
                dut=dut_values,
                page_length=bounded_length,
                page_offset=page_offset,
                skip_steppings=skip_steppings,
            ),
        )

    @mcp.tool()
    async def vamp_runs_list(post_data_json: str) -> str:
        """List runs matching an RS specification.

        A slim projection covering identity, status, triage, classification,
        timing, location, rerun tracking, and build context is applied by
        default so responses stay AI-sized. Include a ``"projection"`` key in
        ``post_data_json`` to override it, for example ``null`` for all fields
        or a custom list such as ``["id", "name", "status"]``.

        When supplied, ``pageLength`` must be between 1 and the configured
        maximum page length; oversized explicit values return an error instead
        of being clamped.

        Returns JSON with ``runs`` and ``count`` fields.
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
            "vamp_runs_list",
            settings_or_repo_root,
            lambda client, _settings: client.list_runs(post_data),
        )

    @mcp.tool()
    async def vamp_runs_count(post_data_json: str) -> str:
        """Count runs matching an RS specification."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_runs_count",
            settings_or_repo_root,
            lambda client, _settings: client.count_runs(post_data),
        )

    @mcp.tool()
    async def vamp_run_get(run_id: int) -> str:
        """Fetch a single run by integer ID."""
        return await run_vmanager_tool(
            "vamp_run_get",
            settings_or_repo_root,
            lambda client, _settings: client.get_run(run_id),
        )

    @mcp.tool()
    async def vamp_run_update(post_data_json: str) -> str:
        """Update run attributes."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_run_update",
            settings_or_repo_root,
            lambda client, _settings: client.update_run(post_data),
        )

    @mcp.tool()
    async def vamp_run_associate_to_failure_cluster(post_data_json: str) -> str:
        """Associate run(s) to a failure cluster."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_run_associate_to_failure_cluster",
            settings_or_repo_root,
            lambda client, _settings: client.associate_run_to_failure_cluster(post_data),
        )

    @mcp.tool()
    async def vamp_run_dissociate_from_failure_cluster(post_data_json: str) -> str:
        """Dissociate run(s) from a failure cluster."""
        try:
            post_data = prepare_post_data(
                settings_or_repo_root,
                parse_json_argument(post_data_json, label="post_data"),
                paginate=False,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

        return await run_vmanager_tool(
            "vamp_run_dissociate_from_failure_cluster",
            settings_or_repo_root,
            lambda client, _settings: client.dissociate_run_from_failure_cluster(post_data),
        )

    @mcp.tool()
    async def vamp_run_rerun_schemes_get() -> str:
        """Retrieve available rerun schemes."""
        return await run_vmanager_tool(
            "vamp_run_rerun_schemes_get",
            settings_or_repo_root,
            lambda client, _settings: client.get_run_rerun_schemes(),
        )

    @mcp.tool()
    async def vamp_run_total_count_size_get() -> str:
        """Retrieve run count and storage-size totals."""
        return await run_vmanager_tool(
            "vamp_run_total_count_size_get",
            settings_or_repo_root,
            lambda client, _settings: client.get_run_total_count_size(),
        )

    @mcp.tool()
    async def vamp_run_extract_logs(
        run_id: int,
        index: int,
        offset: int = 0,
        length: int = 65536,
    ) -> str:
        """Extract a slice of run logs."""
        return await run_vmanager_tool(
            "vamp_run_extract_logs",
            settings_or_repo_root,
            lambda client, _settings: client.extract_run_logs(run_id, index, offset, length),
        )
