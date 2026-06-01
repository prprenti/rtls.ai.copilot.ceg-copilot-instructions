# CEG Repository Quick Start Guide

This guide provides step-by-step instructions for creating and deploying a CEG (Central Engineering Group) specific variant of the CEG copilot instructions repository.

## Prerequisites

- Access to Intel innersource GitHub
- Python 3.11+ with `uv` installed
- GitHub CLI (`gh`) authenticated
- Access to CEG repository: `intel-innersource/rtls.ai.copilot.ceg-copilot-instructions`

## Step 1: Clone CEG Repository

```bash
# Clone the CEG repository
git clone https://github.com/intel-innersource/rtls.ai.copilot.ceg-copilot-instructions.git
cd rtls.ai.copilot.ceg-copilot-instructions
```

## Step 2: Run the Conversion Script

The automated conversion script handles all the rebranding from CEG to CEG.

### Preview Changes (Dry Run)

First, preview what changes will be made:

```bash
UV=/p/cth/rtl/cad/x86-64_linux44/astral/uv/latest/uv

$UV run python scripts/convert_to_ceg.py \
  --source . \
  --target ../rtls.ai.copilot.ceg-copilot-instructions \
  --dry-run
```

This will show you all the changes without modifying any files.

### Perform the Conversion

Once you're satisfied with the preview, run the actual conversion:

```bash
$UV run python scripts/convert_to_ceg.py \
  --source . \
  --target ../rtls.ai.copilot.ceg-copilot-instructions
```

This creates a complete CEG repository with all plugins renamed and adapted.

## Step 3: Review the Converted Repository

Navigate to the new CEG repository and review the changes:

```bash
cd ../rtls.ai.copilot.ceg-copilot-instructions
```

Key files to review:
- `plugins/*/plugin.json` - Plugin names should be `ceg-*`
- `plugins/*/.mcp.json` - Server names should be `ceg-*`
- `plugins/*/mcp-server/server_*.py` - FastMCP registrations updated
- `.github/plugin/marketplace.json` - CEG marketplace configuration
- `README.md` - Updated for CEG
- `.github/copilot-instructions.md` - Updated instructions

## Step 4: Validate the CEG Repository

Run the validation suite to ensure everything is correct:

```bash
UV=/p/cth/rtl/cad/x86-64_linux44/astral/uv/latest/uv

# Sync dependencies
$UV sync

# Update generated marketplace fields
$UV run python scripts/validate_plugin_metadata.py --apply

# Validate all plugin metadata (requires GitHub token)
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

### Expected Results

All tests should pass with CEG plugin names:
- ✓ Plugin names follow `ceg-*` pattern
- ✓ All plugins have `'ceg'` in keywords
- ✓ MCP server names are `ceg-*`
- ✓ Agent and skill frontmatter updated
- ✓ Marketplace entries valid

## Step 5: Create CEG Repository on GitHub

```bash
# Initialize git repository
git init
git add .
git commit -m "Initial CEG copilot instructions repository"

# Create repository on GitHub (use GitHub CLI or web interface)
gh repo create intel-innersource/rtls.ai.copilot.ceg-copilot-instructions \
  --internal \
  --description "GitHub Copilot plugins for Central Engineering Group workflows" \
  --source .

# Push to GitHub
git push -u origin main
```

## Step 6: Test Plugin Installation Locally

Before publishing, test the plugins locally:

```bash
# Install a single plugin from local path
copilot plugin install ./plugins/build-run

# Verify installation
copilot plugin list

# Test in Copilot Chat
# Open VS Code and try these commands:
#   /plugin list
#   /agent
#   /skills list
```

## Step 7: Add CEG Marketplace

Once the repository is pushed to GitHub, add the CEG marketplace:

```bash
copilot plugin marketplace add intel-innersource/rtls.ai.copilot.ceg-copilot-instructions
```

Verify the marketplace is added:

```bash
copilot plugin marketplace list
```

## Step 8: Install CEG Plugins

Install individual plugins from the marketplace:

```bash
# Install specific plugins
copilot plugin install intel-innersource/rtls.ai.copilot.ceg-copilot-instructions:plugins/build-run
copilot plugin install intel-innersource/rtls.ai.copilot.ceg-copilot-instructions:plugins/access
copilot plugin install intel-innersource/rtls.ai.copilot.ceg-copilot-instructions:plugins/fe-setup

# Or install all plugins at once using the bulk install script
./bulk_install.sh
```

## Step 9: Verify Plugin Functionality

Test each plugin to ensure it works correctly:

### Test build-run Plugin

```bash
# In a Cheetah workarea, try:
/agent build-run
# Ask: "Run grdlbuild for my current project"
```

### Test access Plugin

```bash
/agent access
# Ask: "Look up employee jsmith"
# Ask: "Check AGS group permissions for my-group"
```

### Test fe-setup Plugin

```bash
/agent fe-setup
# Ask: "Set up my frontend environment"
```

## Conversion Details

The conversion script automatically handles:

### Plugin Names
- `ceg-access` → `ceg-access`
- `ceg-build-run` → `ceg-build-run`
- `ceg-fe-setup` → `ceg-fe-setup`
- And all other plugins...

### MCP Server Names
- `build-run` → `ceg-build-run`
- `access` → `ceg-access`
- And all other MCP servers...

### Keywords
Adds `'ceg'` to all plugin, agent, and skill keyword lists.

### Documentation
Updates all references to:
- Organization: CEG → CEG
- Full name: Central Engineering Group → Central Engineering Group
- Repository: ceg-copilot-instructions → ceg-copilot-instructions

## Troubleshooting

### Issue: Conversion script fails

**Solution:** Ensure you have Python 3.11+ and proper file permissions:
```bash
python --version  # Should be 3.11 or higher
chmod +x scripts/convert_to_ceg.py
```

### Issue: Validation fails

**Solution:** Check the specific test failures:
```bash
# Run specific test file
$UV run pytest tests/prompt_quality/test_plugin_manifests.py -v

# Check for common issues:
# - Plugin names must be lowercase kebab-case
# - All plugins need 'ceg' in keywords
# - MCP server names must match in .mcp.json and Python files
```

### Issue: MCP tools not working

**Solution:** Verify MCP server configuration:
1. Check `.mcp.json` has correct server names (`ceg-*`)
2. Check `mcp-server/server_*.py` has matching `FastMCP("ceg-*")` names
3. Ensure `uv.lock` file exists in each `mcp-server/` directory

### Issue: Plugin installation fails

**Solution:** Verify the repository is accessible:
```bash
# Test repository access
gh repo view intel-innersource/rtls.ai.copilot.ceg-copilot-instructions

# Ensure you're authenticated
gh auth status
```

## Maintenance and Updates

### Syncing with CEG Changes

When CEG repository gets updates you want to adopt:

1. **Manual sync:**
   ```bash
   # In CEG repo
   cd rtls.ai.copilot.ceg-copilot-instructions
   git pull
   
   # Convert to CEG again
   $UV run python scripts/convert_to_ceg.py \
     --source . \
     --target ../rtls.ai.copilot.ceg-copilot-instructions-new
   
   # Compare and merge changes
   diff -r ../rtls.ai.copilot.ceg-copilot-instructions ../rtls.ai.copilot.ceg-copilot-instructions-new
   ```

2. **Automated approach:**
   Consider setting up a GitHub Action to periodically check for CEG updates and create a PR with converted changes.

### Adding CEG-Specific Features

If CEG needs features not in CEG:

1. Create new plugins in `plugins/ceg-specific-plugin/`
2. Follow the same structure as existing plugins
3. Add to marketplace.json
4. Run validation: `make validate`
5. Document in `docs/ceg-specific-features.md`

## Directory Structure Overview

```
rtls.ai.copilot.ceg-copilot-instructions/
├── plugins/
│   ├── access/              # ceg-access
│   ├── block-diagram/       # ceg-block-diagram
│   ├── build-run/           # ceg-build-run
│   ├── fe-setup/            # ceg-fe-setup
│   ├── hsd/                 # ceg-hsd
│   ├── ip-management/       # ceg-ip-management
│   ├── rtl-design/          # ceg-rtl-design
│   ├── runfv/               # ceg-runfv
│   ├── turnin/              # ceg-turnin
│   └── validation/          # ceg-validation
├── scripts/
│   ├── convert_to_ceg.py    # Conversion script
│   ├── validate_plugin_metadata.py
│   └── ...
├── tests/
│   └── prompt_quality/      # Quality checks
├── docs/
│   ├── ceg-adaptation-guide.md
│   └── ceg-quick-start.md
├── .github/
│   └── plugin/
│       └── marketplace.json # CEG marketplace
├── README.md                # Updated for CEG
└── Makefile                 # Build and validation
```

## Next Steps

After successful deployment:

1. **Announce to CEG team:** Share the marketplace installation instructions
2. **Create user documentation:** Add CEG-specific usage examples
3. **Monitor usage:** Check for issues and collect feedback
4. **Iterate:** Add new CEG-specific plugins as needed
5. **Stay synced:** Periodically sync useful updates from CEG repo

## Support

For issues or questions:
- Review [CEG Adaptation Guide](ceg-adaptation-guide.md)
- Check GitHub's [plugin documentation](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating)
- Contact repository maintainers
- Review validation output for specific errors

## References

- [CEG Adaptation Guide](ceg-adaptation-guide.md) - Detailed conversion documentation
- [CEG Repository](https://github.com/intel-innersource/rtls.ai.copilot.ceg-copilot-instructions) - Original source
- [GitHub Copilot Plugins Docs](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating)
- [Agent Skills Standard](https://agentskills.io/home)
