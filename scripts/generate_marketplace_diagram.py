#!/usr/bin/env python3
"""Generate docs/plugin-marketplace-diagram.html from .github/plugin/marketplace.json.

Usage:
    uv run python scripts/generate_marketplace_diagram.py          # default output
    uv run python scripts/generate_marketplace_diagram.py -o out.html
    uv run python scripts/generate_marketplace_diagram.py --fetch-remotes
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.request
import urllib.error
from html import escape
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_JSON = REPO_ROOT / ".github" / "plugin" / "marketplace.json"
DEFAULT_HTML_OUTPUT = REPO_ROOT / "docs" / "plugin-marketplace-diagram.html"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_marketplace(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    return data.get("plugins", [])


def is_local(plugin: dict) -> bool:
    src = plugin.get("source", {})
    if isinstance(src, str):
        return not src.startswith("http")
    repo = src.get("repo", "")
    return repo == "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions"


def _resolve_mcp_inline(plugin: dict) -> None:
    """If mcpServers is already an inline dict, store it as _mcp_resolved."""
    mcp = plugin.get("mcpServers")
    if isinstance(mcp, dict):
        plugin["_mcp_resolved"] = mcp


def resolve_local_components(plugin: dict) -> dict:
    """Fill agents/skills/mcpServers from the local plugin.json when missing."""
    src = plugin.get("source", {})
    rel_path = src.get("path", "") if isinstance(src, dict) else src
    pjson = REPO_ROOT / rel_path / "plugin.json"
    if not pjson.is_file():
        return plugin
    local = json.loads(pjson.read_text())
    for key in ("agents", "skills", "mcpServers"):
        if key not in plugin and key in local:
            plugin[key] = local[key]
    # Resolve MCP server names
    mcp_ref = plugin.get("mcpServers", local.get("mcpServers"))
    if isinstance(mcp_ref, dict):
        # Inline server definitions
        plugin["_mcp_resolved"] = mcp_ref
    elif isinstance(mcp_ref, str):
        # External .mcp.json file
        mcp_path = REPO_ROOT / rel_path / mcp_ref
        if mcp_path.is_file():
            try:
                plugin["_mcp_resolved"] = json.loads(mcp_path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
    return plugin


def _fetch_via_gh_cli(repo: str, ref: str, file_path: str) -> dict | None:
    """Fetch a file from GitHub using ``gh api`` (handles auth + proxy)."""
    gh = shutil.which("gh")
    if not gh:
        return None
    # /repos/{owner}/{repo}/contents/{path}?ref={ref}
    api_path = f"/repos/{repo}/contents/{file_path}?ref={ref}"
    result = subprocess.run(
        [gh, "api", api_path, "-q", ".content"],
        capture_output=True, text=True, timeout=15,
    )
    if result.returncode != 0:
        return None
    import base64
    return json.loads(base64.b64decode(result.stdout.strip()))


def _list_remote_dir(repo: str, ref: str, dir_path: str) -> list[dict] | None:
    """List files in a remote GitHub directory via ``gh api``.

    Returns a list of dicts with ``name`` and ``type`` keys, or None on failure.
    """
    gh = shutil.which("gh")
    if not gh:
        return None
    dir_path = dir_path.rstrip("/")
    api_path = f"/repos/{repo}/contents/{dir_path}?ref={ref}"
    result = subprocess.run(
        [gh, "api", api_path],
        capture_output=True, text=True, timeout=15,
    )
    if result.returncode != 0:
        return None
    data = json.loads(result.stdout)
    if isinstance(data, list):
        return [{"name": e["name"], "type": e["type"]} for e in data]
    return None


def _resolve_remote_dirs(plugin: dict, repo: str, ref: str, plugin_path: str) -> None:
    """Expand bare directory strings for agents/skills into explicit file lists."""
    agents_val = plugin.get("agents")
    if isinstance(agents_val, str):
        # "./" means repo-root-relative; otherwise relative to plugin_path
        if agents_val.startswith("./"):
            dir_path = agents_val[2:].rstrip("/")
        else:
            dir_path = "/".join(p for p in [plugin_path, agents_val.rstrip("/")] if p)
        entries = _list_remote_dir(repo, ref, dir_path)
        if entries:
            plugin["agents"] = [
                e["name"] for e in entries
                if e["name"].endswith(".agent.md")
            ]

    skills_val = plugin.get("skills")
    if isinstance(skills_val, str):
        if skills_val.startswith("./"):
            dir_path = skills_val[2:].rstrip("/")
        else:
            dir_path = "/".join(p for p in [plugin_path, skills_val.rstrip("/")] if p)
        entries = _list_remote_dir(repo, ref, dir_path)
        if entries:
            plugin["skills"] = [
                f"skills/{e['name']}" for e in entries
                if e["type"] == "dir"
            ]


def _fetch_via_urllib(repo: str, ref: str, file_path: str) -> dict | None:
    """Fetch a raw file from GitHub via urllib (needs HTTPS_PROXY for Intel)."""
    url = f"https://raw.githubusercontent.com/{repo}/{ref}/{file_path}"
    req = urllib.request.Request(url, headers={"User-Agent": "ddg-marketplace-gen"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def fetch_remote_plugin_json(plugin: dict) -> dict:
    """Fetch plugin.json from GitHub for external plugins and merge components."""
    src = plugin.get("source", {})
    if not isinstance(src, dict):
        return plugin
    repo = src.get("repo", "")
    ref = src.get("ref", src.get("sha", src.get("commit", "main")))
    path = src.get("path", "")
    parts = [p for p in [path, "plugin.json"] if p]
    file_path = "/".join(parts)
    try:
        # Prefer gh CLI (authenticated, proxy-aware)
        remote = _fetch_via_gh_cli(repo, ref, file_path)
        # Fall back to raw.githubusercontent.com
        if remote is None:
            remote = _fetch_via_urllib(repo, ref, file_path)
        if remote:
            for key in ("agents", "skills", "mcpServers"):
                if key not in plugin and key in remote:
                    plugin[key] = remote[key]
            _resolve_mcp_inline(plugin)
            # Resolve bare directory strings for agents/skills
            _resolve_remote_dirs(plugin, repo, ref, path)
            # If mcpServers is a file path, fetch it too
            mcp_ref = plugin.get("mcpServers")
            if isinstance(mcp_ref, str) and "_mcp_resolved" not in plugin:
                mcp_parts = [p for p in [path, mcp_ref] if p]
                mcp_file = "/".join(mcp_parts)
                mcp_data = _fetch_via_gh_cli(repo, ref, mcp_file)
                if mcp_data is None:
                    mcp_data = _fetch_via_urllib(repo, ref, mcp_file)
                if isinstance(mcp_data, dict):
                    plugin["_mcp_resolved"] = mcp_data
    except (urllib.error.URLError, json.JSONDecodeError, OSError,
            subprocess.TimeoutExpired) as exc:
        print(f"  warning: could not fetch remote plugin.json for {plugin['name']}: {exc}",
              file=sys.stderr)
    return plugin


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def agent_names(plugin: dict) -> list[str]:
    raw = plugin.get("agents", [])
    if isinstance(raw, str):
        print(f"  warning: {plugin['name']}: 'agents' is a string, expected a list",
              file=sys.stderr)
        raw = [raw]
    names = []
    for a in raw:
        name = a.removeprefix("agents/").removesuffix(".agent.md")
        if name:  # skip bare directory locators like "agents/"
            names.append(name)
    return names


def skill_names(plugin: dict) -> list[str]:
    raw = plugin.get("skills", [])
    if isinstance(raw, str):
        print(f"  warning: {plugin['name']}: 'skills' is a string, expected a list",
              file=sys.stderr)
        raw = [raw]
    names = []
    for s in raw:
        # Skip bare directory locators (e.g. "skills/", "autobots/skills/")
        if s.rstrip("/").endswith("skills") or s.rstrip("/").endswith("agents"):
            continue
        name = s.removeprefix("skills/").removesuffix("/SKILL.md").rstrip("/")
        if name:
            names.append(name)
    return names


def has_mcp(plugin: dict) -> bool:
    return "mcpServers" in plugin


def mcp_names(plugin: dict) -> list[str]:
    """Return the list of MCP server names declared by a plugin.

    Supports both inline dict and file-path string forms of mcpServers.
    """
    mcp = plugin.get("mcpServers")
    if mcp is None:
        return []
    # If _mcp_resolved was populated by resolve_local_components / fetch, use it
    resolved = plugin.get("_mcp_resolved", mcp if isinstance(mcp, dict) else None)
    if isinstance(resolved, dict):
        # .mcp.json wraps in {"servers": {...}}, inline may use top-level keys
        servers = resolved.get("servers", resolved.get("mcpServers", resolved))
        if isinstance(servers, dict) and servers:
            # Filter out non-server metadata keys
            return [k for k in servers if isinstance(servers[k], dict)]
    # Fallback: single generic entry
    return ["MCP"]


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

CSS = """\
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body { height: 100%; }
  body { background: #1a1a2e; font-family: 'Segoe UI', system-ui, sans-serif; color: #e0e0e0; padding: 4px; display: flex; flex-direction: column; height: 100vh; }
  .banner { background: #2c3e50; text-align: center; padding: 4px 8px; border-radius: 4px 4px 0 0; font-size: 13px; font-weight: 600; }
  .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 3px; flex: 1; padding: 3px; background: #16213e; border-radius: 0 0 4px 4px; align-content: start; }
  .card { background: #0f3460; border: 1px solid #1a4a7a; border-radius: 3px; overflow: hidden; }
  .card.external { border-color: #6b3a00; }
  .card-title { background: #1a365d; padding: 2px 5px; font-size: 10px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .card.external .card-title { background: #6b3a00; }
  .card-desc { padding: 1px 5px; font-size: 8px; color: #94a3b8; }
  .card-body { padding: 2px 4px 3px; display: flex; flex-wrap: wrap; gap: 1px; }
  .tag { font-size: 8px; padding: 0px 3px; border-radius: 2px; white-space: nowrap; line-height: 14px; }
  .tag-agent { background: #4a90d9; color: #fff; }
  .tag-skill { background: #5cb85c; color: #fff; }
  .tag-mcp   { background: #f0ad4e; color: #fff; }
  .legend { padding: 3px 8px; font-size: 9px; display: flex; gap: 8px; align-items: center; justify-content: center; }
  .legend span { padding: 1px 5px; border-radius: 2px; font-size: 8px; }"""


def render_card(plugin: dict, external: bool) -> str:
    cls = ' class="card external"' if external else ' class="card"'
    suffix = " \u2197" if external else ""
    name = escape(plugin["name"])
    desc = escape(plugin.get("description", ""))

    tags: list[str] = []
    for a in agent_names(plugin):
        tags.append(f'      <span class="tag tag-agent">\U0001f916 {escape(a)}</span>')
    for s in skill_names(plugin):
        tags.append(f'      <span class="tag tag-skill">\U0001f4da {escape(s)}</span>')
    for m in mcp_names(plugin):
        tags.append(f'      <span class="tag tag-mcp">\u2699\ufe0f {escape(m)}</span>')

    tag_block = "\n".join(tags)
    return f"""\
  <div{cls}>
    <div class="card-title">{name}{suffix}</div>
    <div class="card-desc">{desc}</div>
    <div class="card-body">
{tag_block}
    </div>
  </div>"""


def generate_html(plugins: list[dict]) -> str:
    total_agents = sum(len(agent_names(p)) for p in plugins)
    total_skills = sum(len(skill_names(p)) for p in plugins)
    total_mcp = sum(len(mcp_names(p)) for p in plugins)
    total_plugins = len(plugins)

    banner = (
        f"\U0001f50c {total_plugins} Plugins \u00b7 "
        f"\U0001f916 {total_agents} Agents \u00b7 "
        f"\U0001f4da {total_skills} Skills \u00b7 "
        f"\u2699\ufe0f {total_mcp} MCP Servers"
    )

    cards = "\n\n".join(
        render_card(p, external=not is_local(p))
        for p in plugins
    )

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CEG Copilot Plugin Marketplace</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="banner">{banner}</div>
<div class="grid">

{cards}

</div>
<div class="legend">
  <b>Legend:</b>
  <span class="tag-agent" style="padding:1px 5px;border-radius:2px;">\U0001f916 Agent</span>
  <span class="tag-skill" style="padding:1px 5px;border-radius:2px;">\U0001f4da Skill</span>
  <span class="tag-mcp" style="padding:1px 5px;border-radius:2px;">\u2699\ufe0f MCP Server</span>
  <span style="background:#6b3a00;color:#fff;padding:1px 5px;border-radius:2px;">\u2197 External</span>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate plugin marketplace HTML diagram from marketplace.json"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=DEFAULT_HTML_OUTPUT,
        help=f"Output HTML path (default: {DEFAULT_HTML_OUTPUT.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--marketplace",
        type=Path,
        default=MARKETPLACE_JSON,
        help="Path to marketplace.json",
    )
    parser.add_argument(
        "--fetch-remotes",
        action="store_true",
        help="Fetch plugin.json from GitHub for external plugins that lack component data",
    )
    args = parser.parse_args()

    plugins = load_marketplace(args.marketplace)

    for p in plugins:
        if is_local(p):
            resolve_local_components(p)
        elif args.fetch_remotes:
            fetch_remote_plugin_json(p)

    html = generate_html(plugins)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html)

    print(
        f"Generated {args.output.relative_to(REPO_ROOT)} "
        f"({len(plugins)} plugins)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
