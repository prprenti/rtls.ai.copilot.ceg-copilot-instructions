"""Turnin command tools — turnin execution and turnininfo queries."""

from __future__ import annotations

import asyncio
import logging
import os
import shlex
import subprocess
from typing import Optional

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("turnin-mcp.commands")

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


def _git_config(repo_root: str, key: str) -> str:
    """Read a git config value from the repo."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", key],
            capture_output=True,
            text=True,
            cwd=repo_root,
            timeout=5,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return ""


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------
def register_turnin_command_tools(mcp: FastMCP, repo_root: str) -> None:
    """Register turnin command tools on the MCP server."""

    @mcp.tool()
    async def run_turnin(
        message: str,
        files: list[str] | None = None,
        extra_args: str = "",
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> str:
        """Run the turnin (code submission) command.

        This stages files, creates a commit, and submits via the turnin
        workflow. See the turnin skill for the full workflow.

        Args:
            message: Commit/turnin message.
            files: Optional list of files to turnin. If empty, all staged
                   changes are used.
            extra_args: Additional turnin arguments.
            timeout: Max seconds to wait.

        Returns turnin output.
        """
        env_err = _check_env(repo_root)
        if env_err:
            return f"Environment not ready:\n{env_err}"

        workarea = os.environ.get("WORKAREA", repo_root)

        cmd = f"turnin -m {shlex.quote(message)}"
        if files:
            cmd += " " + " ".join(shlex.quote(f) for f in files)
        if extra_args:
            try:
                cmd += f" {_sanitize_extra_args(extra_args)}"
            except ValueError as exc:
                return str(exc)

        return await _run_shell(cmd, workarea, timeout=timeout)

    @mcp.tool()
    async def turnin_query(
        turnin_id: str,
        extra_args: str = "",
        timeout: int = 60,
    ) -> str:
        """Get the status of a specific turnin by its ID.

        Args:
            turnin_id: The turnin identifier (numeric or full ID string).
            extra_args: Additional turnininfo arguments
                        (e.g. "-history", "-report").
            timeout: Max seconds to wait.

        Returns turnininfo output for the specified turnin.

        When to use: Checking the status, history, or report of a known
        turnin.  Keywords: turnin, turnininfo, status, pipeline, submit.
        """
        env_err = _check_env(repo_root)
        if env_err:
            return f"Environment not ready:\n{env_err}"

        cmd = f"turnininfo {shlex.quote(turnin_id.strip())}"
        if extra_args:
            try:
                cmd += f" {_sanitize_extra_args(extra_args)}"
            except ValueError as exc:
                return str(exc)

        workarea = os.environ.get("WORKAREA", repo_root)
        return await _run_shell(cmd, workarea, timeout=timeout)

    @mcp.tool()
    async def turnin_my_status(
        days: int = 7,
        show_all: bool = False,
        timeout: int = 60,
    ) -> str:
        """List the current user's recent turnins.

        Args:
            days: Number of days to look back (default 7).
            show_all: Include completed/cancelled turnins (default False,
                      which shows only pending).
            timeout: Max seconds to wait.

        Returns a list of the user's turnins.

        When to use: Checking "what are my turnins", "my pending turnins",
        "my recent submissions".
        Keywords: my turnins, pending, recent, turnininfo.
        """
        env_err = _check_env(repo_root)
        if env_err:
            return f"Environment not ready:\n{env_err}"

        cmd = f"turnininfo -my -days {int(days)}"
        if show_all:
            cmd += " -all"

        workarea = os.environ.get("WORKAREA", repo_root)
        return await _run_shell(cmd, workarea, timeout=timeout)

    @mcp.tool()
    async def turnin_pipeline_query(
        extra_args: str = "",
        pending_only: bool = True,
        timeout: int = 60,
    ) -> str:
        """Query turnins in the current repo's pipeline.

        Automatically derives cluster, stepping, and branch from the repo's
        git configuration.

        Args:
            extra_args: Additional turnininfo arguments.
            pending_only: If True (default), show only pending turnins.
            timeout: Max seconds to wait.

        Returns turnins for the repo's pipeline.

        When to use: Checking what turnins are in the pipeline, what's
        pending, or the state of the gatekeeper queue.
        Keywords: pipeline, pending, turnininfo, gatekeeper, queue.
        """
        env_err = _check_env(repo_root)
        if env_err:
            return f"Environment not ready:\n{env_err}"

        workarea = os.environ.get("WORKAREA", repo_root)

        cluster = _git_config(workarea, "intel.cluster")
        stepping = _git_config(workarea, "intel.stepping")
        # Branch from git HEAD
        try:
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, cwd=workarea, timeout=5,
            ).stdout.strip()
        except (subprocess.TimeoutExpired, OSError):
            branch = ""

        if not cluster or not stepping:
            return (
                "Cannot determine pipeline — git config intel.cluster or "
                "intel.stepping is not set."
            )

        cmd = f"turnininfo -c {shlex.quote(cluster)} -s {shlex.quote(stepping)}"
        if branch:
            cmd += f" -b {shlex.quote(branch)}"
        if pending_only:
            cmd += " -pending"
        if extra_args:
            try:
                cmd += f" {_sanitize_extra_args(extra_args)}"
            except ValueError as exc:
                return str(exc)

        return await _run_shell(cmd, workarea, timeout=timeout)
