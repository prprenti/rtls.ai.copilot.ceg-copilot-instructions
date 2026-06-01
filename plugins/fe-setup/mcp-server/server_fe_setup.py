"""FE Setup MCP Server — repo lookup, environment detection, and git config inspection.

Usage:
    uv run server_fe_setup.py          # stdio transport (default, used by VS Code)
"""

from __future__ import annotations

import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

from fe_setup import register_fe_setup_tools

# ---------------------------------------------------------------------------
# Logging — goes to stderr only (stdout is reserved for MCP JSON-RPC)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("fe-setup-mcp")

# ---------------------------------------------------------------------------
# Resolve the plugin directory (plugins/fe-setup/)
# ---------------------------------------------------------------------------
_here = os.path.dirname(os.path.abspath(__file__))        # mcp-server/
PLUGIN_DIR = os.path.dirname(_here)                       # plugins/fe-setup/

# ---------------------------------------------------------------------------
# Create the MCP server instance
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "fe-setup-mcp",
    instructions="""\
FE Setup MCP server for CEG design repositories.

## Tools

### Repo Catalog
  - list_repos → browse all repos from ceg_repos.yml, optionally filtered
  - get_repo_info → look up a repo by name/keyword, returns setup + clone commands

### Terminal Environment
  - check_terminal_setup → verify current terminal has the correct CTH setup
  - check_terminal_ready → boolean readiness check for setup presence + WORKAREA

### Workspace Inspection
  - inspect_workspace_git_config → read [intel] section from .git/config
  - match_remote_to_repo → match a remote URL to a known repo, derive [intel] values
""",
)

register_fe_setup_tools(mcp, PLUGIN_DIR)


def main():
    """Run the MCP server (stdio transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
