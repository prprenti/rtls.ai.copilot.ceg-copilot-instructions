"""Register topology tools — structured CRIF register/field lookups."""

from __future__ import annotations

import asyncio
import logging
import os
import shlex
from typing import Optional

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("validation-mcp.register_topology")


async def _run_helper_json(cmd: str, timeout: int = 30) -> str:
    """Run a structured helper script and return its stdout unchanged."""
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, _stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return f"ERROR: command timed out after {timeout}s"
    return stdout.decode(errors="replace")


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------
def register_register_topology_tools(mcp: FastMCP, repo_root: str) -> None:
    """Register register topology tools on the MCP server."""

    @mcp.tool()
    async def crifd_query(
        crif: str,
        query: str,
        exact: bool = False,
        regex: bool = False,
        address: bool = False,
        names_only: bool = False,
        first: bool = False,
        limit: int = 0,
        value: str = "",
        no_fields: bool = False,
        columns: str = "",
        field_columns: str = "",
        pid: str = "",
        short: bool = False,
        omit_expensive_register_columns: bool = False,
        omit_expensive_field_columns: bool = False,
        indent: int = 2,
        timeout: int = 10,
    ) -> str:
        """Run the register_topology helper script for structured `hive crifd` queries.

        Args:
            crif: Path to the CRIF XML or DB file.
            query: Register name, fragment, regex, or hex address.
            exact: Use exact name match.
            regex: Use case-insensitive regex matching.
            address: Interpret `query` as an address lookup.
            names_only: Return only matching register names.
            first: Limit output to the first match.
            limit: Cap returned results while preserving total_count. Use 0 for no limit.
            value: Decode field values for this raw register value.
            no_fields: Omit field detail from output.
            columns: Comma-separated register-level columns to keep.
            field_columns: Comma-separated field-level columns to keep.
            pid: Filter by port ID.
            short: Suppress descriptions.
            omit_expensive_register_columns: Strip Description, RTL_Path, Register_File,
                Ral_File, Fabric, Scope, FID from register output. No-op when columns is set.
            omit_expensive_field_columns: Strip Description from field output.
                No-op when field_columns is set.
            indent: JSON indent width. Use 0 for compact output.
            timeout: Helper timeout in seconds. Default 10.

        Returns structured JSON from `crifd_query.py`.
        """
        skills_dir = os.path.join(repo_root, "skills", "register-topology")
        helper_py = os.path.join(skills_dir, "crifd_query.py")

        if not os.path.isfile(helper_py):
            return (
                f"crifd_query.py not found at {helper_py}. "
                "Ensure the register_topology skill is installed."
            )

        if limit < 0:
            return "limit must be >= 0"
        if indent < 0:
            return "indent must be >= 0"
        if timeout <= 0:
            return "timeout must be > 0"
        mode_flags = sum(bool(flag) for flag in (exact, regex, address))
        if mode_flags > 1:
            return "exact, regex, and address are mutually exclusive"

        parts = [
            "python3",
            shlex.quote(helper_py),
            "--crif",
            shlex.quote(crif),
            "--query",
            shlex.quote(query),
            "--indent",
            shlex.quote(str(indent)),
            "--timeout",
            shlex.quote(str(timeout)),
        ]
        if exact:
            parts.append("--exact")
        if regex:
            parts.append("--regex")
        if address:
            parts.append("--address")
        if names_only:
            parts.append("--names-only")
        if first:
            parts.append("--first")
        if limit:
            parts.extend(["--limit", shlex.quote(str(limit))])
        if value:
            parts.extend(["--value", shlex.quote(value)])
        if no_fields:
            parts.append("--no-fields")
        if columns:
            parts.extend(["--columns", shlex.quote(columns)])
        if field_columns:
            parts.extend(["--field-columns", shlex.quote(field_columns)])
        if pid:
            parts.extend(["--pid", shlex.quote(pid)])
        if short:
            parts.append("--short")
        if omit_expensive_register_columns:
            parts.append("--omit-expensive-register-columns")
        if omit_expensive_field_columns:
            parts.append("--omit-expensive-field-columns")

        cmd = " ".join(parts)
        return await _run_helper_json(cmd, timeout=max(timeout + 2, 5))
