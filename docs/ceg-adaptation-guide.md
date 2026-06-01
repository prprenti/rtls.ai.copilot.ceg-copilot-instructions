# CEG Repository Adaptation Guide

This document outlines how to create a CEG (Central Engineering Group) specific variant from the CEG copilot instructions repository.

## Overview

Since CEG has no significant workflow differences from CEG, this adaptation is primarily a **rebranding effort** that involves:
- Renaming plugins from `ddg-*` to `ceg-*`
- Updating documentation references
- Adapting marketplace entries
- Preserving all functionality and structure

## Repository Setup

### 1. Create New Repository
```bash
# Create new repository in Intel innersource
# Suggested name: rtls.ai.copilot.ceg-copilot-instructions
```

### 2. Copy Repository Structure
Copy the entire CEG repository structure, preserving:
- All plugin directories under `plugins/`
- Script infrastructure in `scripts/`
- Test suites in `tests/`
- Documentation in `docs/`
- Validation and publishing tools

## Global Changes Required

### Plugin Name Mapping

All plugins should be renamed from `ddg-*` to `ceg-*`:

| CEG Plugin | CEG Plugin |
|------------|------------|
| ceg-access | ceg-access |
| ceg-block-diagram | ceg-block-diagram |
| ceg-build-run | ceg-build-run |
| ceg-fe-setup | ceg-fe-setup |
| ceg-hsd | ceg-hsd |
| ceg-ip-management | ceg-ip-management |
| ceg-rtl-design | ceg-rtl-design |
| ceg-runfv | ceg-runfv |
| ceg-turnin | ceg-turnin |
| ceg-validation | ceg-validation |

### Text Replacements

Apply these text replacements throughout the repository:

| Original | Replacement | Scope |
|----------|-------------|-------|
| `CEG` | `CEG` | Documentation, comments |
| `ddg-` | `ceg-` | Plugin names, tool names |
| `Central Engineering Group` | `Central Engineering Group` | Full name references |
| `rtls.ai.copilot.ceg-copilot-instructions` | `rtls.ai.copilot.ceg-copilot-instructions` | Repository references |

**Exception**: Keep tool/workflow names that are universal (e.g., Cheetah, grdlbuild, NetBatch) unchanged.

## File-by-File Adaptation

### plugin.json Files

Each `plugins/*/plugin.json` must be updated:

**Before (CEG):**
```json
{
  "name": "ceg-access",
  "description": "AGS entitlement management and CDIS employee directory lookups",
  "version": "0.1.0",
  "keywords": ["ags", "cdis", "access", "entitlements", "employee-lookup"],
  "agents": ["access.agent.md"],
  "skills": ["skills/ags", "skills/employee-lookup"],
  "mcpServers": ".mcp.json"
}
```

**After (CEG):**
```json
{
  "name": "ceg-access",
  "description": "AGS entitlement management and CDIS employee directory lookups",
  "version": "0.1.0",
  "keywords": ["ags", "cdis", "access", "entitlements", "employee-lookup", "ceg"],
  "agents": ["access.agent.md"],
  "skills": ["skills/ags", "skills/employee-lookup"],
  "mcpServers": ".mcp.json"
}
```

**Changes:**
- Update `name` field: `ddg-*` → `ceg-*`
- Add `"ceg"` to `keywords` array
- Keep `version` as-is or reset to `0.1.0` for CEG launch
- Preserve all other fields

### Agent Files (*.agent.md)

Update YAML frontmatter in agent files:

**Changes needed:**
- Update `keywords` to include `"ceg"`
- Update any CEG-specific descriptions to reference CEG
- Preserve tool lists and functionality

**Example:**
```yaml
---
name: access
description: AGS entitlement management and employee directory lookup for CEG workflows
keywords: [ags, cdis, access, employee-lookup, ceg]
tools: [access/lookup_employee, access/query_ags_group]
---
```

### Skill Files (SKILL.md)

Update YAML frontmatter in `skills/*/SKILL.md` files:

**Changes needed:**
- Add `"ceg"` to `keywords`
- Update MCP tool references if they include plugin names
- Update skill descriptions to reference CEG where appropriate

**Example MCP tool reference:**
```yaml
mcp_tools:
  - ceg-access/lookup_employee
  - ceg-access/query_ags_group
```

### MCP Configuration (.mcp.json)

Update server names in `.mcp.json` files:

**Before:**
```json
{
  "mcpServers": {
    "build-run": {
      "command": "/p/cth/rtl/cad/x86-64_linux44/astral/uv/0.5.19/uv",
      "args": ["run", "--project", "mcp-server", "server_build_run.py"]
    }
  }
}
```

**After:**
```json
{
  "mcpServers": {
    "ceg-build-run": {
      "command": "/p/cth/rtl/cad/x86-64_linux44/astral/uv/0.5.19/uv",
      "args": ["run", "--project", "mcp-server", "server_build_run.py"]
    }
  }
}
```

**Note:** Only update the server key name. Keep command paths and arguments unchanged.

### MCP Server Python Code

Update server registration names in `mcp-server/server_*.py` files:

**Before:**
```python
mcp = FastMCP("build-run")
```

**After:**
```python
mcp = FastMCP("ceg-build-run")
```

### Marketplace Configuration

Create `.github/plugin/marketplace.json` for CEG:

```json
{
  "marketplace": {
    "name": "CEG Copilot Plugins",
    "description": "GitHub Copilot plugins for Central Engineering Group workflows",
    "repo": "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions",
    "plugins": [
      {
        "name": "ceg-access",
        "description": "AGS entitlement management and CDIS employee directory lookups",
        "version": "0.1.0",
        "keywords": ["ags", "cdis", "access", "entitlements", "employee-lookup", "ceg"],
        "source": "plugins/access"
      },
      // ... additional plugins
    ]
  }
}
```

### Documentation Files

Update these key documentation files:

#### README.md
- Replace "CEG" with "CEG" throughout
- Update repository name references
- Update installation commands to reference CEG plugins

#### .github/copilot-instructions.md
- Update header to "Copilot Instructions — CEG Plugin Repo Development"
- Replace repository name references
- Update plugin table to show CEG plugin names

#### copy-me-to-copilot-instructions.md
- Update consumer repo template for CEG
- Replace CEG references with CEG
- Update marketplace add command

### Code Review Instructions

Files in `code_review/` can generally be kept as-is since they contain universal coding standards. Optionally add CEG-specific review rules if needed.

### Test Files

Update test files in `tests/`:

**Changes needed:**
- Update expected plugin names in assertions
- Update marketplace validation tests
- Keep validation logic unchanged

**Example:**
```python
# Before
assert plugin["name"] == "ceg-access"

# After
assert plugin["name"] == "ceg-access"
```

## Validation After Adaptation

Run these commands to validate the CEG repository:

```bash
UV=/p/cth/rtl/cad/x86-64_linux44/astral/uv/latest/uv

# Sync dependencies
$UV sync

# Update generated marketplace fields
$UV run python scripts/validate_plugin_metadata.py --apply

# Validate all plugin metadata
export GH_TOKEN=$(gh auth token)
$UV run python scripts/validate_plugin_metadata.py --check --github-token-env GH_TOKEN

# Run prompt-quality tests
$UV run pytest tests/prompt_quality/ -v

# Run all tests
$UV run pytest
```

Or use the Makefile:
```bash
make validate
```

## Installation and Testing

### Add CEG Marketplace
```bash
copilot plugin marketplace add intel-innersource/rtls.ai.copilot.ceg-copilot-instructions
```

### Install Individual Plugin
```bash
copilot plugin install intel-innersource/rtls.ai.copilot.ceg-copilot-instructions:plugins/access
```

### Verify Installation
```bash
copilot plugin list
```

In Copilot Chat:
```
/plugin list
/agent
/skills list
```

## Implementation Checklist

- [ ] Create new CEG repository
- [ ] Copy entire CEG repository structure
- [ ] Update all `plugin.json` files (name, keywords)
- [ ] Update all agent `*.agent.md` files
- [ ] Update all skill `SKILL.md` files
- [ ] Update all `.mcp.json` files (server names)
- [ ] Update MCP server Python files (FastMCP registration)
- [ ] Create CEG `marketplace.json`
- [ ] Update `README.md`
- [ ] Update `.github/copilot-instructions.md`
- [ ] Update `copy-me-to-copilot-instructions.md`
- [ ] Update test files
- [ ] Run validation suite
- [ ] Test local plugin installation
- [ ] Document CEG-specific conventions (if any emerge)

## Maintenance Synchronization

Since CEG and CEG share the same workflows, consider:

1. **Periodic sync**: Pull updates from CEG repo and apply CEG rebranding
2. **Shared upstream**: Consider a common base repository with organization-specific overlays
3. **Cross-testing**: Test plugin changes in both CEG and CEG contexts

## Additional Considerations

### Environment Variables
Keep all environment variables unchanged (e.g., `WORKAREA`, proxy settings) unless CEG has different infrastructure.

### Tool Paths
Keep all tool paths unchanged (e.g., `/p/cth/rtl/cad/...`) unless CEG uses different tool installations.

### Intel-Specific Services
Services like AGS, CDIS, HSD, NetBatch are Intel-wide and should work identically for CEG.

### Future Divergence
If CEG workflows diverge from CEG in the future:
- Document differences in a `docs/ceg-specific-workflows.md` file
- Create CEG-specific skills or agents as needed
- Update this adaptation guide accordingly

## Support and Questions

For questions about the adaptation process:
- Review the original CEG repository documentation
- Consult the validation scripts in `scripts/`
- Run the test suite to catch issues early
- Refer to GitHub's plugin documentation: https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating
