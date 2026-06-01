"""HSD tools — wrappers for esquery, esinfo, and esupdate CLI commands.

These tools wrap the HSD (HSdes) bug-tracking CLI tools deployed at
``/p/cth/rtl/proj_tools/hsdes/linux-tools/prod/``.  All queries default
to the ``heia_soc`` tenant.  Write operations (update, add comment)
require explicit confirmation to avoid accidental changes.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import shlex
import subprocess
from typing import Optional

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("hsd-mcp.hsd")

# Absolute paths to the HSD CLI tools — these are not on PATH by default
_ESQUERY = "/p/cth/rtl/proj_tools/hsdes/linux-tools/prod/esquery"
_ESINFO = "/p/cth/rtl/proj_tools/hsdes/linux-tools/prod/esinfo"
_ESUPDATE = "/p/cth/rtl/proj_tools/hsdes/linux-tools/prod/esupdate"

_DEFAULT_TENANT = "heia_soc"
_DEFAULT_FIELDS = "family,release,component,id,title"
_HSD_LINK = "https://hsdes.intel.com/appstore/article-one/#"


async def _run_hsd_cli(cmd: str, timeout: int = 60) -> str:
    """Run an HSD CLI command and return output."""
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return f"ERROR: HSD command timed out after {timeout}s"

    out = stdout.decode(errors="replace")
    if proc.returncode != 0:
        err = stderr.decode(errors="replace")
        out += f"\n--- STDERR ---\n{err}\n--- Exit code: {proc.returncode} ---"
    return out


def _check_hsd_tools() -> Optional[str]:
    """Return an error message if HSD CLIs are not accessible."""
    import os
    missing = []
    for tool, path in [("esquery", _ESQUERY), ("esinfo", _ESINFO), ("esupdate", _ESUPDATE)]:
        if not os.path.isfile(path) or not os.access(path, os.X_OK):
            missing.append(f"  {tool}: {path} (not found or not executable)")
    if missing:
        return "HSD CLI tools not accessible:\n" + "\n".join(missing)
    return None


# ---------------------------------------------------------------------------
# Release field extraction from GkHsdOverrides config
# ---------------------------------------------------------------------------
def _git_config_val(repo_root: str, key: str) -> str:
    """Read a single git config value."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", key],
            capture_output=True, text=True, cwd=repo_root, timeout=5,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return ""


def _get_hsd_releases(repo_root: str) -> list[str]:
    """Extract HSD Release values from the GkHsdOverrides config file.

    Looks for keys in ``$Repository_HSD_Config`` whose value hash contains
    ``turnin_ar_name => "turnin_ip"`` and ``release_ar_name => "release_ip"``.
    Those key names are the valid Release values for this repo/branch.

    File resolution order:
      1. ``cfg/gk/GkHsdOverrides.<stepping>.<cluster>.<branch>.cfg``
      2. ``cfg/gk/GkHsdOverrides.<stepping>.<cluster>.cfg``
    """
    workarea = os.environ.get("WORKAREA", repo_root)
    stepping = _git_config_val(workarea, "intel.stepping")
    cluster = _git_config_val(workarea, "intel.cluster")
    if not stepping or not cluster:
        return []

    # Determine current branch
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=workarea, timeout=5,
        ).stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        branch = ""

    # Try branch-specific file first, then fallback
    candidates = []
    if branch:
        candidates.append(
            os.path.join(workarea, "cfg", "gk",
                         f"GkHsdOverrides.{stepping}.{cluster}.{branch}.cfg")
        )
    candidates.append(
        os.path.join(workarea, "cfg", "gk",
                     f"GkHsdOverrides.{stepping}.{cluster}.cfg")
    )

    cfg_path = None
    for c in candidates:
        # Follow symlinks but skip broken ones
        resolved = os.path.realpath(c) if os.path.islink(c) else c
        if os.path.isfile(resolved):
            cfg_path = resolved
            break

    if cfg_path is None:
        return []

    # Parse the Perl-style config:
    #   'release-name' => {
    #       turnin_ar_name => "turnin_ip", release_ar_name => "release_ip",
    #   },
    try:
        with open(cfg_path, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except OSError:
        return []

    # Match each key => { ... } block in $Repository_HSD_Config
    releases: list[str] = []
    block_pattern = re.compile(
        r"'([^']+)'\s*=>\s*\{([^}]+)\}", re.DOTALL
    )
    for match in block_pattern.finditer(content):
        key_name = match.group(1)
        block_body = match.group(2)
        has_turnin = re.search(
            r'turnin_ar_name\s*=>\s*["\']turnin_ip["\']', block_body
        )
        has_release = re.search(
            r'release_ar_name\s*=>\s*["\']release_ip["\']', block_body
        )
        if has_turnin and has_release:
            releases.append(key_name)

    return releases


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------
def register_hsd_tools(mcp: FastMCP, repo_root: str) -> None:
    """Register HSD (HSdes) bug-tracking tools on the MCP server."""

    @mcp.tool()
    async def hsd_query(
        eql: str,
        fields: str = _DEFAULT_FIELDS,
        max_results: int = 50,
        timeout: int = 60,
    ) -> str:
        """Run an EQL query against HSD and return results in CSV format.

        Args:
            eql: EQL WHERE clause (e.g. "subject='bugeco' AND status='open'
                 AND family='TITAN LAKE'").  Do NOT include the WHERE keyword.
            fields: Comma-separated field names to display
                    (default: family,release,component,id,title).
            max_results: Maximum rows to return (default 50).
            timeout: Max seconds to wait (default 60).

        Returns CSV-formatted query results.

        When to use: Searching for bugs, features, tasks, or ECOs in HSD.
        Keywords: hsd, hsdes, bug, bugeco, feature, task, eco, eql, esquery.
        For richer analysis with historical context, consider the codesign MCP.
        """
        err = _check_hsd_tools()
        if err:
            return err

        cmd = (
            f"{_ESQUERY} -where {shlex.quote(eql)} "
            f"-show {shlex.quote(fields)} "
            f"-max {int(max_results)} -csv"
        )
        return await _run_hsd_cli(cmd, timeout=timeout)

    @mcp.tool()
    async def hsd_get_article(article_id: str, timeout: int = 30) -> str:
        """Fetch a single HSD article by its numeric ID.

        Args:
            article_id: The HSD article ID (numeric string).
            timeout: Max seconds to wait.

        Returns the article details.
        Link: {_HSD_LINK}/<article_id>

        When to use: Looking up a specific bug, feature, task, or ECO by ID.
        Keywords: hsd, article, bug, bugeco, feature.
        """
        err = _check_hsd_tools()
        if err:
            return err

        # Validate article_id is numeric
        clean_id = article_id.strip()
        if not clean_id.isdigit():
            return f"Invalid article ID: {article_id!r} — must be numeric."

        cmd = f"{_ESQUERY} {clean_id}"
        result = await _run_hsd_cli(cmd, timeout=timeout)
        result += f"\n\nHSD Link: {_HSD_LINK}/{clean_id}"
        return result

    @mcp.tool()
    async def hsd_field_info(
        subject: str = "",
        field: str = "",
        tenant: str = _DEFAULT_TENANT,
        timeout: int = 30,
    ) -> str:
        """Get HSD schema information — subjects, fields, or allowed values.

        Args:
            subject: HSD subject (e.g. "bugeco", "feature", "task").
                     If empty, lists all subjects for the tenant.
            field: Field name (e.g. "release", "status", "component").
                   If empty, lists all fields for the subject.
            tenant: HSD tenant (default: heia_soc).
            timeout: Max seconds to wait.

        Returns schema information.

        When to use: Validating field values before a query, discovering
        which fields or subjects exist, or checking allowed enum values.
        Keywords: hsd, schema, field, esinfo, subject, allowed values.
        """
        err = _check_hsd_tools()
        if err:
            return err

        # Build the dotted path
        path = tenant
        if subject:
            # Validate subject name (alphanumeric + underscores)
            if not all(c.isalnum() or c == "_" for c in subject):
                return f"Invalid subject: {subject!r}"
            path += f".{subject}"
            if field:
                if not all(c.isalnum() or c in "_." for c in field):
                    return f"Invalid field: {field!r}"
                path += f".{field}"

        cmd = f"{_ESINFO} {shlex.quote(path)}"
        return await _run_hsd_cli(cmd, timeout=timeout)

    @mcp.tool()
    async def hsd_update_article(
        article_id: str,
        updates: str,
        confirm: bool = False,
        timeout: int = 30,
    ) -> str:
        """Update fields on an HSD article.

        **Safety:** This tool previews the command by default.  Set
        confirm=True to actually execute the update.

        Args:
            article_id: The HSD article ID (numeric string).
            updates: Space-separated field=value pairs
                     (e.g. "status=resolved owner=geruhl").
            confirm: If False (default), returns a preview of the command
                     without executing.  Set True to execute.
            timeout: Max seconds to wait.

        Returns preview or execution result.

        When to use: Updating bug status, owner, or other fields.
        Keywords: hsd, update, esupdate, modify, change status.
        """
        err = _check_hsd_tools()
        if err:
            return err

        clean_id = article_id.strip()
        if not clean_id.isdigit():
            return f"Invalid article ID: {article_id!r} — must be numeric."

        if not updates.strip():
            return "No updates provided."

        # Sanitize updates — split and re-quote each field=value pair
        try:
            tokens = shlex.split(updates)
        except ValueError as exc:
            return f"Invalid updates format: {exc}"

        for token in tokens:
            if "=" not in token and not token.startswith("-"):
                return (
                    f"Invalid update token: {token!r} — expected field=value "
                    "or -flag format."
                )

        safe_updates = " ".join(shlex.quote(t) for t in tokens)
        cmd = f"{_ESUPDATE} {clean_id} {safe_updates}"

        if not confirm:
            return (
                f"HSD update preview (NOT executed):\n\n"
                f"  {cmd}\n\n"
                f"To execute, call hsd_update_article with confirm=True.\n"
                f"Article link: {_HSD_LINK}/{clean_id}"
            )

        return await _run_hsd_cli(cmd, timeout=timeout)

    @mcp.tool()
    def get_hsd_release() -> str:
        """Get the HSD Release field value(s) for the current repository.

        Extracts Release values from the GkHsdOverrides config file in
        ``cfg/gk/``.  The Release field is required for many HSD queries
        (e.g. filtering bugs by release).

        Returns the release value(s), or a message asking the user to
        provide one if the config file is not found.

        When to use: Before running hsd_query when you need the release
        field value, or when the user asks about HSD bugs for this repo.
        Keywords: hsd, release, GkHsdOverrides, scoping.
        """
        releases = _get_hsd_releases(repo_root)
        if not releases:
            workarea = os.environ.get("WORKAREA", repo_root)
            stepping = _git_config_val(workarea, "intel.stepping")
            cluster = _git_config_val(workarea, "intel.cluster")
            return (
                "Could not determine HSD Release from GkHsdOverrides config.\n"
                f"  Looked for: cfg/gk/GkHsdOverrides.{stepping}.{cluster}.[branch].cfg\n"
                f"  WORKAREA: {workarea}\n\n"
                "Please provide the Release field value you want to query."
            )

        if len(releases) == 1:
            return f"HSD Release for this repo: {releases[0]}"

        lines = ["HSD Releases for this repo:"]
        for r in releases:
            lines.append(f"  - {r}")
        lines.append("\nUse the appropriate release value for your HSD query.")
        return "\n".join(lines)

    @mcp.tool()
    async def hsd_add_comment(
        article_id: str,
        comment: str,
        confirm: bool = False,
        timeout: int = 30,
    ) -> str:
        """Add a comment to an HSD article.

        **Safety:** This tool previews the command by default.  Set
        confirm=True to actually post the comment.

        Args:
            article_id: The HSD article ID (numeric string).
            comment: The comment text to add.
            confirm: If False (default), returns a preview.  Set True
                     to execute.
            timeout: Max seconds to wait.

        Returns preview or execution result.

        When to use: Adding notes or status updates to a bug or task.
        Keywords: hsd, comment, note, esupdate.
        """
        err = _check_hsd_tools()
        if err:
            return err

        clean_id = article_id.strip()
        if not clean_id.isdigit():
            return f"Invalid article ID: {article_id!r} — must be numeric."

        if not comment.strip():
            return "Empty comment — nothing to add."

        cmd = f"{_ESUPDATE} {clean_id} -comment {shlex.quote(comment)}"

        if not confirm:
            return (
                f"HSD comment preview (NOT executed):\n\n"
                f"  {cmd}\n\n"
                f"To post, call hsd_add_comment with confirm=True.\n"
                f"Article link: {_HSD_LINK}/{clean_id}"
            )

        return await _run_hsd_cli(cmd, timeout=timeout)

    @mcp.tool()
    async def hsd_clone_article(
        article_id: str,
        release: str,
        component: str = "",
        title: str = "",
        confirm: bool = False,
        timeout: int = 60,
    ) -> str:
        """Clone an HSD article into the ``bugeco`` subject for a new release with updated fields.

        **Safety:** This tool previews the command by default.  Set
        confirm=True to actually execute the clone.

        Note:
            The clone is always created in the ``{_DEFAULT_TENANT}.bugeco`` subject.
            Cloning into other subjects is not currently supported by this tool.

        Args:
            article_id: The HSD article ID to clone (numeric string).
            release: The new release value for the clone (required).
            component: Optional component to set (e.g., "sspma.ip.top.val").
                      If empty, keeps original component.
            title: Optional title for the clone. If empty or whitespace-only,
                   the original article title is kept unchanged.
            confirm: If False (default), returns a preview of the command
                     without executing.  Set True to execute.
            timeout: Max seconds to wait (default 60).

        Returns preview or execution result with new clone ID.

        When to use: Creating a copy of an existing HSD for a different release
        or component in the ``bugeco`` subject, such as cloning a baseline
        tools update HSD from one repo to another.
        Keywords: hsd, clone, copy, esupdate, duplicate, -cloneto.

        Example:
            Clone HSD 22022161937 from ioc-ttl-h-a0 to sspma-ttl-h-a0:
            hsd_clone_article(
                article_id="22022161937",
                release="sspma-ttl-h-a0",
                component="sspma.ip.top.val",
                title="SSPMA TTL baseline tools update to 2025.06.eng.008",
                confirm=True
            )
        """
        err = _check_hsd_tools()
        if err:
            return err

        clean_id = article_id.strip()
        if not clean_id.isdigit():
            return f"Invalid article ID: {article_id!r} — must be numeric."

        clean_release = release.strip()
        if not clean_release:
            return "Release field is required for cloning."

        clean_component = component.strip()
        clean_title = title.strip()

        # Build the field updates
        field_updates = [f"release={shlex.quote(clean_release)}"]

        if clean_component:
            field_updates.append(f"component={shlex.quote(clean_component)}")

        if clean_title:
            field_updates.append(f"title={shlex.quote(clean_title)}")

        updates_str = " ".join(field_updates)
        # NOTE: This tool intentionally only clones into the bugeco subject for the
        # default tenant (i.e., {_DEFAULT_TENANT}.bugeco). Cloning into other HSD
        # subjects (features, tasks, etc.) is not supported here.
        cmd = f"{_ESUPDATE} -cloneto {_DEFAULT_TENANT}.bugeco {clean_id} {updates_str}"

        if not confirm:
            return (
                f"HSD clone preview (NOT executed):\n\n"
                f"  {cmd}\n\n"
                f"This will create a clone of article {clean_id} in "
                f"{_DEFAULT_TENANT}.bugeco with:\n"
                f"  - release: {clean_release}\n" +
                (f"  - component: {clean_component}\n" if clean_component else "") +
                (f"  - title: {clean_title}\n" if clean_title else "  - title: [kept from original article]\n") +
                f"\nTo execute, call hsd_clone_article with confirm=True.\n"
                f"Original article link: {_HSD_LINK}/{clean_id}"
            )

        result = await _run_hsd_cli(cmd, timeout=timeout)

        # Try to extract the new clone ID from the output
        clone_match = re.search(r"Created Clone ID (\d+)", result)
        if clone_match:
            new_id = clone_match.group(1)
            result += f"\n\nNew clone link: {_HSD_LINK}/{new_id}"

        return result
