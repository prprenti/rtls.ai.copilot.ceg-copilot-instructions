"""CEG MCP Server — build commands and repo context tools.

This server provides the core build/make execution and environment
introspection tools used by CEG Copilot plugins.  Domain-specific tools
(HSD, AGS, vManager, gatekeeper, etc.) have moved to their respective
plugin MCP servers under plugins/.

Usage:
    uv run server_build_run.py          # stdio transport (default, used by VS Code)
    uv run server_build_run.py --help   # show options
"""

from __future__ import annotations

import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

from commands import register_command_tools

# ---------------------------------------------------------------------------
# Logging — goes to stderr only (stdout is reserved for MCP JSON-RPC)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("ceg-mcp")

# ---------------------------------------------------------------------------
# Resolve the plugin root (parent of mcp-server/).  Uses realpath so a
# deploy symlink resolves correctly.
# ---------------------------------------------------------------------------
_here = os.path.dirname(os.path.realpath(__file__))  # mcp-server/
PLUGIN_ROOT = os.path.dirname(_here)                 # plugin root

# ---------------------------------------------------------------------------
# Create the MCP server instance
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "ceg-mcp",
    instructions="""\
CEG Build MCP server — provides core build execution tools for CEG
design repositories.

## Tools

### Build & EDA Flows
  - check_environment → verify CTH setup (CTH_SETUP_CMD, WORKAREA, RTLMODELS)
  - run_grdlbuild → Gradle-based build wrapper (CDC, lint, LP, SGDFT, simulation)
  - run_make → Makefile targets in repo subdirectories
""",
)

# ---------------------------------------------------------------------------
# Register tool groups
# ---------------------------------------------------------------------------
register_command_tools(mcp, PLUGIN_ROOT)


def main() -> None:
    """Entry point for the MCP server."""
    logger.info("Starting ceg-mcp server (plugin_root=%s)", PLUGIN_ROOT)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
