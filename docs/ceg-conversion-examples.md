# CEG Conversion Examples

This document shows before/after examples of files converted from CEG to CEG.

## Plugin Manifest (plugin.json)

### Before (CEG)
```json
{
  "name": "ceg-build-run",
  "description": "Build system automation and execution for Cheetah workflows",
  "version": "0.2.0",
  "keywords": ["grdlbuild", "make", "netbatch", "build", "cheetah"],
  "agents": ["build-run.agent.md", "kotlin.agent.md", "mako.agent.md"],
  "skills": [
    "skills/grdlbuild",
    "skills/make"
  ],
  "mcpServers": ".mcp.json"
}
```

### After (CEG)
```json
{
  "name": "ceg-build-run",
  "description": "Build system automation and execution for Cheetah workflows",
  "version": "0.2.0",
  "keywords": ["grdlbuild", "make", "netbatch", "build", "cheetah", "ceg"],
  "agents": ["build-run.agent.md", "kotlin.agent.md", "mako.agent.md"],
  "skills": [
    "skills/grdlbuild",
    "skills/make"
  ],
  "mcpServers": ".mcp.json"
}
```

**Changes:**
- ✓ `name`: `ceg-build-run` → `ceg-build-run`
- ✓ `keywords`: Added `"ceg"`
- ✓ All other fields preserved

---

## MCP Configuration (.mcp.json)

### Before (CEG)
```json
{
  "mcpServers": {
    "build-run": {
      "command": "/p/cth/rtl/cad/x86-64_linux44/astral/uv/0.5.19/uv",
      "args": [
        "run",
        "--project",
        "mcp-server",
        "server_build_run.py"
      ],
      "env": {
        "WORKAREA": "${workspaceFolder}",
        "UV_FROZEN": "1"
      }
    }
  }
}
```

### After (CEG)
```json
{
  "mcpServers": {
    "ceg-build-run": {
      "command": "/p/cth/rtl/cad/x86-64_linux44/astral/uv/0.5.19/uv",
      "args": [
        "run",
        "--project",
        "mcp-server",
        "server_build_run.py"
      ],
      "env": {
        "WORKAREA": "${workspaceFolder}",
        "UV_FROZEN": "1"
      }
    }
  }
}
```

**Changes:**
- ✓ Server name: `build-run` → `ceg-build-run`
- ✓ Command and args preserved
- ✓ Environment variables preserved

---

## MCP Server Code (server_*.py)

### Before (CEG)
```python
#!/usr/bin/env python3
"""
MCP server for build and run operations.
"""
from mcp import FastMCP
import subprocess
from pathlib import Path

# Create FastMCP server
mcp = FastMCP("build-run")

@mcp.tool()
def run_grdlbuild(
    target: str,
    dut: str = "",
    flow: str = "",
    model: str = ""
) -> str:
    """Run grdlbuild command."""
    # Implementation...
    pass
```

### After (CEG)
```python
#!/usr/bin/env python3
"""
MCP server for build and run operations.
"""
from mcp import FastMCP
import subprocess
from pathlib import Path

# Create FastMCP server
mcp = FastMCP("ceg-build-run")

@mcp.tool()
def run_grdlbuild(
    target: str,
    dut: str = "",
    flow: str = "",
    model: str = ""
) -> str:
    """Run grdlbuild command."""
    # Implementation...
    pass
```

**Changes:**
- ✓ FastMCP registration: `"build-run"` → `"ceg-build-run"`
- ✓ Tool implementations preserved
- ✓ All functionality unchanged

---

## Agent File (*.agent.md)

### Before (CEG)
```markdown
---
name: build-run
description: Automate Cheetah build workflows using grdlbuild, make, and NetBatch
keywords: [grdlbuild, make, netbatch, build, cheetah, automation]
tools:
  - build-run/run_grdlbuild
  - build-run/run_make
  - build-run/query_netbatch_job
---

# Build and Run Agent

This agent helps automate CEG build workflows using Cheetah build systems.

## Capabilities

- Run grdlbuild for specific targets
- Execute make commands
- Submit and monitor NetBatch jobs
```

### After (CEG)
```markdown
---
name: build-run
description: Automate Cheetah build workflows using grdlbuild, make, and NetBatch
keywords: [grdlbuild, make, netbatch, build, cheetah, automation, ceg]
tools:
  - ceg-build-run/run_grdlbuild
  - ceg-build-run/run_make
  - ceg-build-run/query_netbatch_job
---

# Build and Run Agent

This agent helps automate CEG build workflows using Cheetah build systems.

## Capabilities

- Run grdlbuild for specific targets
- Execute make commands
- Submit and monitor NetBatch jobs
```

**Changes:**
- ✓ `keywords`: Added `"ceg"`
- ✓ `tools`: MCP tool references updated to `ceg-build-run/*`
- ✓ Description: `CEG` → `CEG`

---

## Skill File (SKILL.md)

### Before (CEG)
```markdown
---
name: grdlbuild
description: Run and monitor grdlbuild commands for CEG Cheetah workflows
keywords: [grdlbuild, build, cheetah, compilation]
mcp_tools:
  - build-run/run_grdlbuild
  - build-run/parse_grdlbuild_log
---

# grdlbuild Skill

Automate CEG grdlbuild workflows including target selection, execution, and log analysis.

## When to Use

Use this skill when you need to:
- Compile RTL using grdlbuild
- Run specific build targets
```

### After (CEG)
```markdown
---
name: grdlbuild
description: Run and monitor grdlbuild commands for CEG Cheetah workflows
keywords: [grdlbuild, build, cheetah, compilation, ceg]
mcp_tools:
  - ceg-build-run/run_grdlbuild
  - ceg-build-run/parse_grdlbuild_log
---

# grdlbuild Skill

Automate CEG grdlbuild workflows including target selection, execution, and log analysis.

## When to Use

Use this skill when you need to:
- Compile RTL using grdlbuild
- Run specific build targets
```

**Changes:**
- ✓ `description`: `CEG` → `CEG`
- ✓ `keywords`: Added `"ceg"`
- ✓ `mcp_tools`: Tool references updated to `ceg-build-run/*`
- ✓ Body text: `CEG` → `CEG`

---

## Marketplace Configuration

### Before (CEG)
```json
{
  "marketplace": {
    "name": "CEG Copilot Plugins",
    "description": "GitHub Copilot plugins for Central Engineering Group workflows",
    "repo": "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions",
    "plugins": [
      {
        "name": "ceg-build-run",
        "description": "Build system automation and execution",
        "version": "0.2.0",
        "keywords": ["grdlbuild", "make", "netbatch", "build"],
        "source": "plugins/build-run"
      }
    ]
  }
}
```

### After (CEG)
```json
{
  "marketplace": {
    "name": "CEG Copilot Plugins",
    "description": "GitHub Copilot plugins for Central Engineering Group workflows",
    "repo": "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions",
    "plugins": [
      {
        "name": "ceg-build-run",
        "description": "Build system automation and execution",
        "version": "0.2.0",
        "keywords": ["grdlbuild", "make", "netbatch", "build", "ceg"],
        "source": "plugins/build-run"
      }
    ]
  }
}
```

**Changes:**
- ✓ Marketplace `name`: `CEG` → `CEG`
- ✓ Marketplace `description`: `Central Engineering Group` → `Central Engineering Group`
- ✓ Marketplace `repo`: `ceg-copilot-instructions` → `ceg-copilot-instructions`
- ✓ Plugin `name`: `ceg-build-run` → `ceg-build-run`
- ✓ Plugin `keywords`: Added `"ceg"`

---

## README.md

### Before (CEG)
```markdown
# CEG Copilot Instructions

This repository contains GitHub Copilot plugins, agents, and skills for Central Engineering Group (CEG) workflows.

## Installation

Add the CEG marketplace:

```bash
copilot plugin marketplace add intel-innersource/rtls.ai.copilot.ceg-copilot-instructions
```

Install plugins:

```bash
copilot plugin install intel-innersource/rtls.ai.copilot.ceg-copilot-instructions:plugins/build-run
```

## Available Plugins

- `ceg-build-run` - Build system automation
- `ceg-fe-setup` - Frontend environment setup
```

### After (CEG)
```markdown
# CEG Copilot Instructions

This repository contains GitHub Copilot plugins, agents, and skills for Central Engineering Group (CEG) workflows.

## Installation

Add the CEG marketplace:

```bash
copilot plugin marketplace add intel-innersource/rtls.ai.copilot.ceg-copilot-instructions
```

Install plugins:

```bash
copilot plugin install intel-innersource/rtls.ai.copilot.ceg-copilot-instructions:plugins/build-run
```

## Available Plugins

- `ceg-build-run` - Build system automation
- `ceg-fe-setup` - Frontend environment setup
```

**Changes:**
- ✓ Title: `CEG` → `CEG`
- ✓ Organization name: `Central Engineering Group` → `Central Engineering Group`
- ✓ Repository references: `ceg-copilot-instructions` → `ceg-copilot-instructions`
- ✓ Plugin names: `ddg-*` → `ceg-*`

---

## Test Files

### Before (CEG)
```python
def test_plugin_names():
    """Test that all plugins follow naming convention."""
    plugins = load_plugins()
    for plugin in plugins:
        assert plugin["name"].startswith("ddg-")
        assert plugin["name"] == plugin["name"].lower()
```

### After (CEG)
```python
def test_plugin_names():
    """Test that all plugins follow naming convention."""
    plugins = load_plugins()
    for plugin in plugins:
        assert plugin["name"].startswith("ceg-")
        assert plugin["name"] == plugin["name"].lower()
```

**Changes:**
- ✓ Test assertions: `ddg-` → `ceg-`

---

## Summary of Changes

| Category | Change Type | Example |
|----------|-------------|---------|
| Plugin names | Text replacement | `ceg-build-run` → `ceg-build-run` |
| MCP server names | Text replacement | `build-run` → `ceg-build-run` |
| Keywords | Addition | `keywords: [..., "ceg"]` |
| Tool references | Text replacement | `build-run/tool` → `ceg-build-run/tool` |
| Documentation | Text replacement | `CEG` → `CEG` |
| Organization | Text replacement | `Central Engineering Group` → `Central Engineering Group` |
| Repository | Text replacement | `ceg-copilot-instructions` → `ceg-copilot-instructions` |

## What Stays the Same

- ✓ All functionality and tool implementations
- ✓ Directory structure
- ✓ Validation scripts and test infrastructure
- ✓ MCP server implementation logic
- ✓ Skill and agent content (except org references)
- ✓ Build commands and tool paths
- ✓ Environment variables and configuration
- ✓ File and directory layouts
- ✓ Version control structure

## Automation

The `scripts/convert_to_ceg.py` script handles all these transformations automatically, ensuring:
- Consistent naming across all files
- Proper JSON formatting
- Preserved functionality
- Complete file coverage
- Validation-ready output
