from __future__ import annotations

import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

from register_topology import register_register_topology_tools
from validation_mcp.settings import Settings
from vmanager import register_vmanager_tools


logger = logging.getLogger("validation-mcp")


def _parse_log_level(log_level: str) -> int:
    normalized = log_level.strip().upper()
    allowed_levels = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }
    return allowed_levels.get(normalized, logging.INFO)


def plugin_root_for(server_file: str) -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(server_file))))


def configure_logging(log_level: str) -> None:
    logging.basicConfig(
    level=_parse_log_level(log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )


def create_mcp(settings: Settings) -> FastMCP:
    mcp = FastMCP(
        "validation-mcp",
        instructions="""\
Validation & Test Management MCP server for CEG design repositories.

## Tools

### vManager — Runs & Failure Analysis
  - vamp_runs_list, vamp_runs_count, vamp_standard_runs_list
  - vamp_run_get, vamp_run_update
  - vamp_failure_cluster_list/count/get/create/update/delete

### vManager — VSIF Configuration
  - vamp_vsif_config_list/update
  - vamp_vsif_group_get, vamp_vsif_groups_list/create/update/delete
  - vamp_vsif_test_get, vamp_vsif_tests_list/create/update/delete
  - vamp_vsif_hierarchy_list/get/create/attach_*
  - vamp_sessions_list, vamp_sessions_count
  - vamp_vsif_session_get/create/create_with_permissions/delete

### vManager — Validation Plans
  - vamp_plan_list, vamp_plan_list_sub_elements, vamp_plan_count, vamp_plan_list_vplans
  - vamp_plan_get, vamp_plan_get_rich_text, vamp_plan_find
  - vamp_plan_add_section, vamp_plan_add_reference, vamp_plan_add_metrics_port
  - vamp_plan_update, vamp_plan_update_bulk, vamp_plan_update_section, vamp_plan_update_reference

### Register Topology
  - crifd_query → structured CRIF register/field lookups
""",
    )

    register_vmanager_tools(mcp, settings)
    register_register_topology_tools(mcp, settings.repo_root)
    return mcp


def main() -> None:
    settings = Settings.from_env(plugin_root_for(__file__))
    configure_logging(settings.log_level)
    logger.info("Starting validation MCP server")
    create_mcp(settings).run(transport="stdio")