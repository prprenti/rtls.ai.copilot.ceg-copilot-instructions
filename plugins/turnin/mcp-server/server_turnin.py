"""Turnin & Gatekeeper MCP Server — turnin execution and gatekeeper log access.

Usage:
    uv run server.py          # stdio transport (default, used by VS Code)
"""

from __future__ import annotations

import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

from turnin_commands import register_turnin_command_tools
from gatekeeper import register_gatekeeper_tools

# ---------------------------------------------------------------------------
# Logging — goes to stderr only (stdout is reserved for MCP JSON-RPC)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("turnin-mcp")

# ---------------------------------------------------------------------------
# Resolve the plugin root (parent of mcp-server/)
# ---------------------------------------------------------------------------
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Create the MCP server instance
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "turnin-mcp",
    instructions="""\
Turnin & Gatekeeper MCP server for CEG design repositories.

## Tools

### Turnin Commands
  - run_turnin → execute a turnin (code submission)
  - turnin_query → check status of a specific turnin ID
  - turnin_my_status → list current user's recent turnins
  - turnin_pipeline_query → show pipeline status for the repo

### Gatekeeper Logs
  - gatekeeper_list_turnins → list all turnin sessions in GATEKEEPER/
  - gatekeeper_read_log → read a specific log file by date/PID/type
  - gatekeeper_latest_status → quick summary of most recent turnin
""",
)

register_turnin_command_tools(mcp, PLUGIN_ROOT)
register_gatekeeper_tools(mcp, PLUGIN_ROOT)


def main():
    """Run the MCP server (stdio transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
