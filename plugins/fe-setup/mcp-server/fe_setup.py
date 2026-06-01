"""FE Setup tools — repo lookup, terminal detection, and git config inspection.

These tools read ``ceg_repos.yml`` to provide programmatic access to
repository metadata, setup commands, and environment detection for
CEG design repos.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from functools import lru_cache
from typing import Any, Optional

import yaml
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("fe-setup-mcp.fe_setup")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _yml_path(plugin_dir: str) -> str:
    """Return the absolute path to ceg_repos.yml in the plugin directory."""
    return os.path.join(plugin_dir, "ceg_repos.yml")


@lru_cache(maxsize=1)
def _load_repos(plugin_dir: str) -> dict[str, Any]:
    """Load and parse ceg_repos.yml.  Cached after first call."""
    path = _yml_path(plugin_dir)
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _extract_repo_name(path: str) -> str:
    """Extract the short repo name from a full path (last component)."""
    return os.path.basename(path.rstrip("/"))


def _extract_cfg(setup_cmd: str) -> str:
    """Extract the ``-cfg`` value from a setup command string."""
    match = re.search(r"-cfg\s+(\S+)", setup_cmd)
    return match.group(1) if match else ""


def _extract_domain(setup_cmd: str) -> str:
    """Extract the ``-p`` (domain) value from a setup command string."""
    match = re.search(r"-p\s+(\S+)", setup_cmd)
    return match.group(1) if match else ""


def _parse_intel_from_path(repo_path: str, setup_cmd: str) -> dict[str, str]:
    """Derive [intel] config values from a repo path.

    Path format: ``/p/cth/rtl/git_repos/<domain>/**/<reponame>``
    Repo name split on first ``-`` → cluster (left), stepping (right).
    Domain from path, project from ``-cfg`` in setup command.
    """
    repo_name = _extract_repo_name(repo_path)

    # Split on first '-' — cluster never contains '-'
    parts = repo_name.split("-", 1)
    cluster = parts[0]
    stepping = parts[1] if len(parts) > 1 else ""

    # Domain: component right after git_repos/
    domain = ""
    segments = repo_path.replace("\\", "/").split("/")
    for i, seg in enumerate(segments):
        if seg == "git_repos" and i + 1 < len(segments):
            domain = segments[i + 1]
            break

    project = _extract_cfg(setup_cmd)

    return {
        "stepping": stepping,
        "cluster": cluster,
        "project": project,
        "domain": domain,
    }


def _normalize_setup_cmd(cmd: str) -> str:
    """Normalize a setup command for comparison.

    Strips ``-read_only``, collapses whitespace.
    """
    normalized = re.sub(r"\s+-read_only\b", "", cmd)
    normalized = re.sub(r"-read_only\s+", "", normalized)
    return " ".join(normalized.split())


def _flatten_repos(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten groups into a list of repo dicts, each with setup_cmd attached."""
    default_branch = data.get("defaults", {}).get("repo_branch", "master")
    result = []
    for group in data.get("groups", []):
        setup_cmd = group.get("cheetah_setup_command", "")
        for repo in group.get("repos", []):
            entry = {
                "path": repo["path"],
                "repo_branch": repo.get("repo_branch", default_branch),
                "keywords": repo.get("keywords", []),
                "setup_cmd": setup_cmd,
                "name": _extract_repo_name(repo["path"]),
            }
            result.append(entry)
    return result


def _match_repos(query: str, repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Soft-match a query against repo keywords and path components.

    Case-insensitive substring matching against keywords and repo name.
    """
    q = query.lower().strip()
    if not q:
        return repos

    matches = []
    for repo in repos:
        searchable = [kw.lower() for kw in repo["keywords"]]
        searchable.append(repo["name"].lower())
        searchable.append(repo["path"].lower())

        if any(q in item for item in searchable):
            matches.append(repo)

    return matches


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

def register_fe_setup_tools(mcp: FastMCP, plugin_dir: str) -> None:
    """Register FE setup tools on the MCP server."""

    @mcp.tool()
    def list_repos(group_filter: str = "") -> str:
        """List all repos from ceg_repos.yml.

        Args:
            group_filter: Optional filter — only show repos whose setup
                command contains this string (e.g. "ttlh78", "ddgip").

        Returns a formatted table of repos with name, path, branch,
        keywords, and setup command.

        When to use: Browsing available repos, or finding repos for a
        particular project/cfg.
        Keywords: repos, list, available, browse, catalog.
        """
        data = _load_repos(plugin_dir)
        repos = _flatten_repos(data)

        if group_filter:
            gf = group_filter.lower()
            repos = [r for r in repos if gf in r["setup_cmd"].lower()]

        if not repos:
            return "No repos found matching the filter."

        lines = [f"{'Name':<35} {'Branch':<15} {'Keywords':<40} {'Setup -cfg'}"]
        lines.append("-" * 110)
        for r in repos:
            kw = ", ".join(r["keywords"])
            cfg = _extract_cfg(r["setup_cmd"])
            lines.append(f"{r['name']:<35} {r['repo_branch']:<15} {kw:<40} {cfg}")

        lines.append(f"\nTotal: {len(repos)} repo entries")
        return "\n".join(lines)

    @mcp.tool()
    def get_repo_info(query: str) -> str:
        """Look up a repo by name/keyword and return setup + clone commands.

        Soft-matches the query against repo keywords and path components.
        - Single match: returns full info with exact commands.
        - Multiple matches: returns the list for the user to pick.
        - No matches: returns the full catalog.

        The setup command always includes ``-read_only``.  The clone
        command uses a ``<desired_path>`` placeholder — the agent should
        check the user's copilot-instructions for a preferred clone
        directory, or prompt the user.

        Args:
            query: Search term (e.g. "punit", "hub", "display").

        Returns repo info with setup command, clone command, and
        WORKAREA export command.

        When to use: User wants to set up, clone, or get info about a
        specific repo.
        Keywords: setup, clone, repo, info, get, psetup.
        """
        data = _load_repos(plugin_dir)
        repos = _flatten_repos(data)
        matches = _match_repos(query, repos)

        if len(matches) == 1:
            r = matches[0]
            setup = f"{r['setup_cmd']} -read_only"
            clone = f"git clone {r['path']}"
            if r["repo_branch"] != "master":
                clone += f" --branch {r['repo_branch']}"
            clone += " <desired_path>"
            cfg = _extract_cfg(r["setup_cmd"])
            terminal_name = f"{cfg}/{r['name'].split('-', 1)[0]}"

            lines = [
                f"Repo:           {r['name']}",
                f"Path:           {r['path']}",
                f"Branch:         {r['repo_branch']}",
                f"Keywords:       {', '.join(r['keywords'])}",
                f"",
                f"Setup command:  {setup}",
                f"Clone command:  {clone}",
                f"After clone:    export WORKAREA=<clone_path>",
                f"Terminal name:  {terminal_name}",
            ]
            return "\n".join(lines)

        if len(matches) > 1:
            lines = [f"Multiple repos match '{query}'. Please pick one:\n"]
            for i, r in enumerate(matches, 1):
                branch = r["repo_branch"]
                lines.append(f"  {i}. {r['name']} (branch: {branch})")
            return "\n".join(lines)

        # No matches — show everything
        lines = [f"No repos match '{query}'. Available repos:\n"]
        for r in repos:
            lines.append(f"  - {r['name']} (branch: {r['repo_branch']})")
        return "\n".join(lines)

    @mcp.tool()
    def check_terminal_setup(needed_setup_cmd: str) -> str:
        """Check if the current terminal has the correct CTH setup.

        Compares ``$CTH_SETUP_CMD`` to the needed setup command,
        normalizing whitespace and ignoring ``-read_only``.

        Args:
            needed_setup_cmd: The setup command required for the target
                repo (from ``get_repo_info``).

        Returns:
            - ``MATCH`` — current terminal has the right setup.
            - ``MISMATCH: current=<cmd>, needed=<cmd>`` — different setup.
            - ``NO_SETUP: CTH_SETUP_CMD is not set`` — no setup run.

        When to use: Before running commands, to verify the terminal
        environment matches the target repo.
        Keywords: terminal, detect, environment, setup, mismatch.
        """
        current = os.environ.get("CTH_SETUP_CMD", "")
        if not current:
            return "NO_SETUP: CTH_SETUP_CMD is not set"

        norm_current = _normalize_setup_cmd(current)
        norm_needed = _normalize_setup_cmd(needed_setup_cmd)

        if norm_current == norm_needed:
            return "MATCH"

        return f"MISMATCH: current={norm_current}, needed={norm_needed}"

    @mcp.tool()
    def check_terminal_ready() -> bool:
        """Check if the current terminal is generally ready.

        A terminal is considered ready when both:
        - ``$CTH_SETUP_CMD`` is set (a setup window is active)
        - ``$WORKAREA`` is set (workspace context is configured)

        Returns:
            ``True`` if ready, else ``False``.

        When to use: Fast readiness probe before commands that require an
        initialized setup window and workarea. Use ``check_terminal_setup``
        separately when validating setup command match to a specific repo.
        Keywords: terminal ready, environment, setup, WORKAREA, boolean.
        """
        has_setup = bool(os.environ.get("CTH_SETUP_CMD", "").strip())
        has_workarea = bool(os.environ.get("WORKAREA", "").strip())
        return has_setup and has_workarea

    @mcp.tool()
    def inspect_workspace_git_config(workarea: str = "") -> str:
        """Read the [intel] section from the workspace's .git/config.

        Args:
            workarea: Path to the workspace root.  Defaults to
                ``$WORKAREA`` if empty.

        Returns JSON with one of:
            - ``{"status": "OK", "stepping": "...", ...}``
            - ``{"status": "NO_INTEL_SECTION", "remote_origin_url": "..."}``
            - ``{"status": "NOT_A_REPO", "message": "..."}``

        When to use: Checking the current workspace identity, or
        detecting repos cloned without a proper setup.
        Keywords: git config, intel, stepping, cluster, project, domain.
        """
        wa = workarea or os.environ.get("WORKAREA", "")
        if not wa:
            return json.dumps({
                "status": "NOT_A_REPO",
                "message": "No workarea specified and WORKAREA is not set",
            })

        git_dir = os.path.join(wa, ".git")
        if not os.path.isdir(git_dir):
            return json.dumps({
                "status": "NOT_A_REPO",
                "message": f"No .git directory found at {wa}",
            })

        def _git_cfg(key: str) -> str:
            try:
                result = subprocess.run(
                    ["git", "config", "--get", key],
                    capture_output=True, text=True, cwd=wa, timeout=5,
                )
                return result.stdout.strip()
            except (subprocess.TimeoutExpired, OSError):
                return ""

        stepping = _git_cfg("intel.stepping")
        cluster = _git_cfg("intel.cluster")
        project = _git_cfg("intel.project")
        domain = _git_cfg("intel.domain")

        if stepping or cluster or project or domain:
            return json.dumps({
                "status": "OK",
                "stepping": stepping,
                "cluster": cluster,
                "project": project,
                "domain": domain,
            })

        # No [intel] section — get remote URL for orphan clone detection
        remote_url = _git_cfg("remote.origin.url")
        return json.dumps({
            "status": "NO_INTEL_SECTION",
            "remote_origin_url": remote_url,
        })

    @mcp.tool()
    def match_remote_to_repo(remote_url: str) -> str:
        """Match a git remote URL against repos in ceg_repos.yml.

        If the remote URL matches a known repo path, derives the
        ``[intel]`` config values and returns ``git config`` commands
        the agent can run to fix the clone.

        Args:
            remote_url: The ``remote.origin.url`` value from
                ``.git/config``.

        Returns JSON with:
            - ``{"status": "MATCH", ..., "fix_commands": [...]}``
            - ``{"status": "NO_MATCH", "message": "..."}``

        When to use: After ``inspect_workspace_git_config`` returns
        ``NO_INTEL_SECTION`` — to detect orphan clones and offer repair.
        Keywords: remote, origin, orphan clone, match, intel config.
        """
        if not remote_url or not remote_url.strip():
            return json.dumps({
                "status": "NO_MATCH",
                "message": "Empty remote URL",
            })

        url = remote_url.strip().rstrip("/")

        data = _load_repos(plugin_dir)
        repos = _flatten_repos(data)

        for repo in repos:
            repo_path = repo["path"].rstrip("/")
            if url == repo_path or url.endswith(repo_path):
                intel = _parse_intel_from_path(repo_path, repo["setup_cmd"])
                fix_cmds = [
                    f"git config intel.stepping {intel['stepping']}",
                    f"git config intel.cluster {intel['cluster']}",
                    f"git config intel.project {intel['project']}",
                    f"git config intel.domain {intel['domain']}",
                ]
                return json.dumps({
                    "status": "MATCH",
                    "repo_path": repo_path,
                    "repo_branch": repo["repo_branch"],
                    "setup_cmd": repo["setup_cmd"],
                    "intel_config": intel,
                    "fix_commands": fix_cmds,
                })

        return json.dumps({
            "status": "NO_MATCH",
            "message": f"Remote URL '{url}' does not match any known repo",
        })
