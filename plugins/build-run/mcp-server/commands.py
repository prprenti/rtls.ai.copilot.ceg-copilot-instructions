"""Command tools — whitelisted shell command execution for build flows."""

from __future__ import annotations

import asyncio
import logging
import os
import shlex
from typing import Optional

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("ceg-mcp.commands")

# Default timeout for commands (seconds)
_DEFAULT_TIMEOUT = 600  # 10 minutes


def _sanitize_extra_args(extra_args: str) -> str:
    """Parse extra_args through shlex to neutralise shell metacharacters."""
    if not extra_args:
        return ""
    try:
        tokens = shlex.split(extra_args)
    except ValueError as exc:
        raise ValueError(f"Invalid extra_args: {exc}") from exc
    return " ".join(shlex.quote(t) for t in tokens)


async def _run_shell(
    cmd: str,
    cwd: str,
    timeout: int = _DEFAULT_TIMEOUT,
    env_extra: Optional[dict[str, str]] = None,
) -> str:
    """Run a shell command and return combined output."""
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    logger.info("Running: %s (cwd=%s, timeout=%ds)", cmd, cwd, timeout)

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env=env,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return f"ERROR: command timed out after {timeout}s.\nPartial output may be lost."

    out = stdout.decode(errors="replace")
    err = stderr.decode(errors="replace")

    result = out
    if err:
        result += f"\n--- STDERR ---\n{err}"
    if proc.returncode != 0:
        result += f"\n--- Exit code: {proc.returncode} ---"
    return result


def _check_env(repo_root: str) -> Optional[str]:
    """Return an error message if the CTH environment is not set up."""
    issues = []
    if not os.environ.get("CTH_SETUP_CMD"):
        issues.append(
            "CTH_SETUP_CMD is not set — use the @fe-setup agent to "
            "configure the environment for this repository."
        )
    workarea = os.environ.get("WORKAREA", "")
    if not workarea:
        issues.append(
            "WORKAREA is not set — use the @fe-setup agent to clone "
            "and configure the repository environment."
        )
    elif not os.path.isdir(workarea):
        issues.append(f"WORKAREA={workarea} is not a valid directory.")
    return "\n".join(issues) if issues else None


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------
def register_command_tools(mcp: FastMCP, repo_root: str) -> None:
    """Register command-execution tools on the MCP server."""

    @mcp.tool()
    async def check_environment() -> str:
        """Check whether the CTH build environment is properly configured.

        Verifies that CTH_SETUP_CMD, WORKAREA, and RTLMODELS are set, and
        that key tools (grdlbuild, turnin, make) are on PATH.
        Returns a status summary.
        """
        lines = []

        # CTH setup
        cth = os.environ.get("CTH_SETUP_CMD", "")
        lines.append(f"CTH_SETUP_CMD: {'OK (' + cth + ')' if cth else 'MISSING'}")

        # WORKAREA
        wa = os.environ.get("WORKAREA", "")
        if wa and os.path.isdir(wa):
            lines.append(f"WORKAREA: OK ({wa})")
        elif wa:
            lines.append(f"WORKAREA: SET but invalid ({wa})")
        else:
            lines.append("WORKAREA: MISSING")

        # RTLMODELS
        rtl = os.environ.get("RTLMODELS", "")
        lines.append(f"RTLMODELS: {'OK (' + rtl + ')' if rtl else 'MISSING'}")

        # Tool availability
        for tool in ["grdlbuild", "turnin", "turnininfo", "make"]:
            result = await _run_shell(f"which {tool}", repo_root, timeout=5)
            found = "exit code" not in result.lower() and result.strip()
            lines.append(f"{tool}: {'OK (' + result.strip().split(chr(10))[0] + ')' if found else 'NOT FOUND'}")

        return "\n".join(lines)

    @mcp.tool()
    async def run_grdlbuild(
        task: str,
        extra_args: str = "",
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> str:
        """Run a grdlbuild task in the repo workspace.

        grdlbuild is the Gradle-based build wrapper used for CDC, lint,
        simulation, and other EDA flows.

        Args:
            task: The grdlbuild task to run (e.g. "vc_cdc", "vc_lp",
                  "vcssim", "lint").
            extra_args: Additional arguments to pass to grdlbuild.
            timeout: Max seconds to wait (default 600).

        Returns stdout/stderr and exit code.
        """
        env_err = _check_env(repo_root)
        if env_err:
            return f"Environment not ready:\n{env_err}"

        # Validate task name (alphanumeric, underscores, hyphens)
        if not all(c.isalnum() or c in "_-" for c in task):
            return f"Invalid task name: {task!r}"

        cmd = f"grdlbuild {shlex.quote(task)}"
        if extra_args:
            try:
                cmd += f" {_sanitize_extra_args(extra_args)}"
            except ValueError as exc:
                return str(exc)

        workarea = os.environ.get("WORKAREA", repo_root)
        return await _run_shell(cmd, workarea, timeout=timeout)

    @mcp.tool()
    async def run_make(
        target: str,
        directory: str = "",
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> str:
        """Run a make target in the repo or a subdirectory.

        Args:
            target: The make target (e.g. "all", "clean", "filelist").
            directory: Subdirectory to run in, relative to WORKAREA.
                       Defaults to the repo root.
            timeout: Max seconds to wait.

        Returns make output.
        """
        env_err = _check_env(repo_root)
        if env_err:
            return f"Environment not ready:\n{env_err}"

        workarea = os.environ.get("WORKAREA", repo_root)
        cwd = os.path.join(workarea, directory) if directory else workarea

        if not os.path.isdir(cwd):
            return f"Directory does not exist: {cwd}"

        # Validate target (no shell injection)
        if not all(c.isalnum() or c in "_-./:" for c in target):
            return f"Invalid make target: {target!r}"

        cmd = f"make {shlex.quote(target)}"
        return await _run_shell(cmd, cwd, timeout=timeout)

