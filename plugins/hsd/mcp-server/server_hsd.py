"""HSD Bug Tracking MCP Server — HSD queries, articles, updates, and cloning.

Usage:
    uv run server.py          # stdio transport (default, used by VS Code)
"""

from __future__ import annotations

import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

from hsd import register_hsd_tools

# ---------------------------------------------------------------------------
# Logging — goes to stderr only (stdout is reserved for MCP JSON-RPC)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("hsd-mcp")

# ---------------------------------------------------------------------------
# Resolve the plugin root (parent of mcp-server/)
# ---------------------------------------------------------------------------
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Create the MCP server instance
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "hsd-mcp",
    instructions="""\
HSD (HSdes) Bug Tracking MCP server for CEG design repositories.

## Tools

### HSD Queries & Articles
  - get_hsd_release → get the HSD Release field for the current repo
  - hsd_query → run an EQL query against HSD
  - hsd_get_article → fetch a single article by ID
  - hsd_field_info → inspect HSD schema (subjects, fields, allowed values)

### HSD Modifications (preview-first for safety)
  - hsd_update_article → update fields on an article
  - hsd_add_comment → add a comment to an article
  - hsd_clone_article → clone an article to a new release
""",
)

register_hsd_tools(mcp, PLUGIN_ROOT)


def main():
    """Run the MCP server (stdio transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
