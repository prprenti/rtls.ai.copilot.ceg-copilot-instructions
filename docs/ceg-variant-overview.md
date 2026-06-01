# CEG Variant Creation - Complete Package

This document serves as the master index for creating a CEG (Central Engineering Group) specific variant of the CEG copilot instructions repository.

## What This Package Includes

This package provides everything needed to create a complete CEG variant:

1. **[CEG Adaptation Guide](ceg-adaptation-guide.md)** - Comprehensive strategy document
2. **[CEG Quick Start Guide](ceg-quick-start.md)** - Step-by-step execution instructions
3. **[CEG Conversion Examples](ceg-conversion-examples.md)** - Before/after file comparisons
4. **[Automation Script](../scripts/convert_to_ceg.py)** - Python script for automated conversion

## Executive Summary

### What is CEG?
Central Engineering Group (CEG) is an Intel organization that uses the same workflows as the Central Engineering Group (CEG) but needs its own branded plugin repository.

### What Changes?
The CEG variant is a **rebranding** of the CEG repository:
- Plugin names: `ddg-*` → `ceg-*`
- MCP server names: Same transformation
- Keywords: Add `"ceg"` to all plugins, agents, and skills
- Documentation: Update org references
- Repository name: `ceg-copilot-instructions` → `ceg-copilot-instructions`

### What Stays the Same?
- All functionality and tool implementations
- Directory structure and file layout
- Validation and testing infrastructure
- MCP server logic
- Build commands and workflows

## Quick Start (TL;DR)

```bash
# 1. Clone CEG repository
git clone https://github.com/intel-innersource/rtls.ai.copilot.ceg-copilot-instructions.git
cd rtls.ai.copilot.ceg-copilot-instructions

# 2. Run automated conversion
UV=/p/cth/rtl/cad/x86-64_linux44/astral/uv/latest/uv
$UV run python scripts/convert_to_ceg.py \
  --source . \
  --target ../rtls.ai.copilot.ceg-copilot-instructions

# 3. Validate
cd ../rtls.ai.copilot.ceg-copilot-instructions
make validate

# 4. Create GitHub repo and push
git init
git add .
git commit -m "Initial CEG copilot instructions repository"
gh repo create intel-innersource/rtls.ai.copilot.ceg-copilot-instructions --internal --source .
git push -u origin main

# 5. Install marketplace
copilot plugin marketplace add intel-innersource/rtls.ai.copilot.ceg-copilot-instructions
```

## Documentation Structure

### For Planning and Understanding

**Start here:** [CEG Adaptation Guide](ceg-adaptation-guide.md)
- Comprehensive overview of the conversion process
- Detailed file-by-file adaptation rules
- Plugin name mapping table
- MCP configuration guidelines
- Validation procedures
- Maintenance strategy

**See examples:** [CEG Conversion Examples](ceg-conversion-examples.md)
- Before/after comparisons for all file types
- Visual representation of changes
- Summary tables
- What stays the same vs what changes

### For Execution

**Follow this:** [CEG Quick Start Guide](ceg-quick-start.md)
- Step-by-step instructions
- Command-line examples
- Validation procedures
- Testing guidelines
- Troubleshooting tips

**Use this:** [Conversion Script](../scripts/convert_to_ceg.py)
- Automated Python script
- Handles all file transformations
- Dry-run mode for preview
- Comprehensive logging

## Plugin Mapping Reference

| CEG Plugin | CEG Plugin | Description |
|------------|------------|-------------|
| ceg-access | ceg-access | AGS entitlement management and CDIS employee directory |
| ceg-block-diagram | ceg-block-diagram | Block diagram generation and visualization |
| ceg-build-run | ceg-build-run | Build system automation (grdlbuild, make, NetBatch) |
| ceg-fe-setup | ceg-fe-setup | Frontend environment setup and repo cloning |
| ceg-hsd | ceg-hsd | HSD ticketing system integration |
| ceg-ip-management | ceg-ip-management | IP release and management workflows |
| ceg-rtl-design | ceg-rtl-design | RTL design workflows (CDC, lint, low-power) |
| ceg-runfv | ceg-runfv | Formal verification automation |
| ceg-turnin | ceg-turnin | Code submission and pipeline monitoring |
| ceg-validation | ceg-validation | Validation workflows and test management |

## Conversion Workflow

```
┌─────────────────────┐
│  CEG Repository     │
│  (Source)           │
└──────────┬──────────┘
           │
           │ scripts/convert_to_ceg.py
           ▼
┌─────────────────────┐
│  Process Files      │
│  - plugin.json      │
│  - .mcp.json        │
│  - *.agent.md       │
│  - SKILL.md         │
│  - server_*.py      │
│  - Documentation    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  CEG Repository     │
│  (Target)           │
└──────────┬──────────┘
           │
           │ make validate
           ▼
┌─────────────────────┐
│  Validation         │
│  - Metadata check   │
│  - Prompt quality   │
│  - Test suite       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  GitHub Publish     │
│  - Create repo      │
│  - Push code        │
│  - Add marketplace  │
└─────────────────────┘
```

## Key Benefits

### For CEG Users
- ✓ CEG-branded plugins and tools
- ✓ Familiar CEG workflows preserved
- ✓ Organization-specific naming
- ✓ Easy discovery in marketplace
- ✓ Consistent with CEG identity

### For Maintainers
- ✓ Automated conversion process
- ✓ Easy synchronization with CEG updates
- ✓ Validation ensures correctness
- ✓ Minimal maintenance overhead
- ✓ Clear documentation

### For the Organization
- ✓ Separate plugin namespaces
- ✓ Independent versioning
- ✓ Organization-specific customization potential
- ✓ Shared workflow compatibility
- ✓ Reduced naming conflicts

## File Structure After Conversion

```
rtls.ai.copilot.ceg-copilot-instructions/
├── docs/
│   ├── ceg-adaptation-guide.md        # This package
│   ├── ceg-quick-start.md
│   ├── ceg-conversion-examples.md
│   └── ceg-variant-overview.md
├── plugins/
│   ├── access/                        # ceg-access
│   │   ├── plugin.json               # name: "ceg-access"
│   │   ├── .mcp.json                 # server: "ceg-access"
│   │   ├── access.agent.md           # keywords: [..., "ceg"]
│   │   ├── mcp-server/
│   │   │   └── server_access.py      # FastMCP("ceg-access")
│   │   └── skills/
│   │       ├── ags/SKILL.md          # mcp_tools: ceg-access/*
│   │       └── employee-lookup/SKILL.md
│   ├── build-run/                     # ceg-build-run
│   │   ├── plugin.json
│   │   ├── .mcp.json
│   │   ├── build-run.agent.md
│   │   ├── mcp-server/
│   │   └── skills/
│   └── [... 8 more plugins ...]
├── scripts/
│   ├── convert_to_ceg.py             # Conversion automation
│   ├── validate_plugin_metadata.py
│   └── ...
├── tests/
│   └── prompt_quality/               # Updated for CEG
├── .github/
│   ├── plugin/
│   │   └── marketplace.json          # CEG marketplace
│   └── copilot-instructions.md       # CEG repo docs
├── README.md                          # Updated for CEG
└── Makefile                           # Validation commands
```

## Success Criteria

Your CEG variant is complete when:

- [ ] All 10 plugins renamed to `ceg-*`
- [ ] All MCP servers renamed to `ceg-*`
- [ ] All plugins have `"ceg"` in keywords
- [ ] All documentation references CEG
- [ ] Validation passes: `make validate`
- [ ] Local plugin installation works
- [ ] GitHub repository created and pushed
- [ ] Marketplace added successfully
- [ ] At least one plugin tested end-to-end

## Estimated Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Understanding | 30 min | Review documentation and examples |
| Conversion | 5 min | Run automated conversion script |
| Validation | 10 min | Run test suite and fix any issues |
| GitHub Setup | 15 min | Create repo and push code |
| Testing | 30 min | Install and test plugins |
| **Total** | **~90 min** | Complete CEG variant creation |

## Support and Resources

### Internal Documentation
- [CEG Adaptation Guide](ceg-adaptation-guide.md) - Strategy and details
- [CEG Quick Start](ceg-quick-start.md) - Step-by-step execution
- [CEG Examples](ceg-conversion-examples.md) - Before/after comparisons

### External Resources
- [GitHub Copilot Plugins](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating) - Official docs
- [Agent Skills Standard](https://agentskills.io/home) - Open standard
- [MCP Documentation](https://modelcontextprotocol.io/) - Protocol reference

### Tools
- `scripts/convert_to_ceg.py` - Automated conversion
- `scripts/validate_plugin_metadata.py` - Validation
- `Makefile` - Build and test commands

## Frequently Asked Questions

### Q: Can I customize CEG plugins beyond rebranding?
**A:** Yes! After conversion, you can add CEG-specific features, agents, skills, or plugins. Just follow the same structure and validation process.

### Q: How do I sync updates from CEG?
**A:** Periodically re-run the conversion script on the updated CEG repo, then merge the changes into your CEG repo.

### Q: What if CEG workflows diverge from CEG?
**A:** Document the differences in `docs/ceg-specific-workflows.md` and add CEG-specific plugins as needed.

### Q: Can both CEG and CEG plugins coexist?
**A:** Yes! Users can install plugins from both marketplaces. The `ceg-*` and `ddg-*` naming prevents conflicts.

### Q: Do I need to modify the conversion script?
**A:** No for basic rebranding. Yes if you need additional transformations specific to CEG.

## Next Steps

1. **Read** [CEG Quick Start Guide](ceg-quick-start.md)
2. **Run** the conversion script
3. **Validate** the output
4. **Test** locally
5. **Publish** to GitHub
6. **Announce** to CEG team

## Maintenance Plan

### Regular Tasks
- **Weekly:** Check for CEG updates
- **Monthly:** Sync useful CEG changes to CEG
- **Quarterly:** Review plugin usage and gather feedback

### Update Process
```bash
# In CEG repo
git pull

# Re-convert to new CEG directory
$UV run python scripts/convert_to_ceg.py --source . --target ../ceg-new

# Compare and merge
diff -r ../ceg-copilot-instructions ../ceg-new

# Validate and push
cd ../ceg-copilot-instructions
make validate
git commit -am "Sync with CEG updates"
git push
```

## Contact and Support

For questions about:
- **Conversion process:** Review this documentation
- **Technical issues:** Check validation output and error messages
- **CEG-specific needs:** Document in `docs/ceg-specific-features.md`
- **General plugin development:** Refer to GitHub's official docs

---

**Document Version:** 1.0  
**Created:** June 2026  
**Last Updated:** June 2026  
**Status:** Ready for use
