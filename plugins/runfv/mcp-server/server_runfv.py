"""RunFV Formal Verification MCP Server — JasperGold batch Tcl execution.

Usage:
    uv run server_runfv.py    # stdio transport (default, used by VS Code)
"""

from __future__ import annotations

import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

from jg_cmd import register_jg_cmd_tools

# ---------------------------------------------------------------------------
# Logging — goes to stderr only (stdout is reserved for MCP JSON-RPC)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("runfv-mcp")

# ---------------------------------------------------------------------------
# Resolve the plugin root (parent of mcp-server/)
# ---------------------------------------------------------------------------
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Create the MCP server instance
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "runfv-mcp",
    instructions="""\
RunFV Formal Verification MCP server for CEG design repositories.

## Tools

### JasperGold Command Builder
  - jg_cmd → build a JasperGold batch command and Tcl script content.
    Returns a JSON object with shell commands and Tcl script that the
    @build-run agent should execute in a CTH-configured terminal.
""",
)

register_jg_cmd_tools(mcp, PLUGIN_ROOT)


def main():
    """Run the MCP server (stdio transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
