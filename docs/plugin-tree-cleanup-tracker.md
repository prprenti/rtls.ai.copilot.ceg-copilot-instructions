# Plugin Tree Cleanup Tracker

Use this tracker with docs/plugin-tree-cleanup-plan.md.

Status values:
- not-started
- in-progress
- done
- blocked

## Tracker

| Plugin | Status | MCP Decision | Has pyproject.toml | Skill Simplified | References Split | Agent Simplified | Path Cleanup | FQ MCP Tools | Validation | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| access | in-progress | removed | yes | yes | yes | yes | yes | pending | pending | baseline pattern plugin |
| block-diagram | not-started | TBD | no | no | no | no | no | not-run | not-run |  |
| build-run | in-progress | keep | yes | yes | yes | yes | yes | pending | pending | MCP retained by decision; no MCP removal planned for this pass |
| fe-setup | not-started | TBD | no | no | no | no | no | not-run | not-run |  |
| hsd | done | keep (security+release-parse+preview-safety) | yes | yes | yes | yes | yes | done | done | MCP retained: injection guards, get_hsd_release config parser, confirm=False preview enforcement |
| ip-management | not-started | TBD | no | no | no | no | no | not-run | not-run |  |
| mc-debug | not-started | TBD | no | no | no | no | no | not-run | not-run |  |
| rtl-design | not-started | TBD | no | no | no | no | no | not-run | not-run |  |
| runfv | done | keep (Jasper batch command builder `runfv-mcp/jg_cmd`) | yes | yes | yes | yes | yes | done | done (local) | local metadata+prompt-quality passed; remote check run was interrupted by terminal signal |
| turnin | done | keep (run_turnin + gatekeeper log tools) | yes | yes | yes | yes | yes | done | done | SKILL.md simplified; Intel workflow + mock tree moved to TURNIN_WORKFLOW_REFERENCE.md |
| validation | not-started | TBD | no | no | no | no | no | not-run | not-run |  |

## Per-Plugin Checklist

For each plugin:

1. Inventory tree and decide MCP keep/remove.
2. Ensure plugin-local pyproject.toml exists.
3. Simplify SKILL.md into activation-first.
4. Move deep details into references.
5. Simplify agent to top-level skill routing.
6. Clean runtime paths to plugin-root-relative.
7. Verify MCP tools are referenced with fully qualified identifiers in frontmatter and docs.
8. Run metadata and prompt-quality validation.

## Validation Command Template

```bash
UV=/p/cth/rtl/cad/x86-64_linux44/astral/uv/latest/uv
PLUGIN=plugins/<plugin-name>

test -f "$PLUGIN/pyproject.toml"
export GH_TOKEN=$(gh auth token)
$UV run python scripts/validate_plugin_metadata.py --apply
$UV run python scripts/validate_plugin_metadata.py --check --check-remotes --github-token-env GH_TOKEN

# Or use Makefile:
make validate
make validate-apply

$UV run pytest tests/prompt_quality/test_plugin_manifests.py -v
$UV run pytest tests/prompt_quality/test_agents.py -v
$UV run pytest tests/prompt_quality/test_skills.py -v
```
