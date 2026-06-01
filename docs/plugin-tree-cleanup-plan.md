# Plugin Tree Cleanup Plan (Access-Style)

This runbook standardizes the Access plugin cleanup pattern for every plugin tree:
- remove unnecessary MCP dependencies
- simplify skills into activation-first docs
- split deep content into references
- simplify agents to top-level skill routing
- normalize deployable command paths

Use this per plugin at `plugins/<plugin-name>/`.

## 1. Scope and Decision Gate

For each plugin, decide first:

1. Is MCP actually required for core capability?
2. Can functionality be delivered via direct CLI/scripts in skills?
3. If MCP is optional, remove it and route through skills.

If MCP is required, keep it but still do skill/agent simplification and path cleanup.

## 2. Baseline Inventory (Per Plugin)

From repo root:

```bash
PLUGIN=plugins/<plugin-name>

ls -la "$PLUGIN"
find "$PLUGIN" -maxdepth 3 -type f | sort
```

Collect these facts:
- `plugin.json` components (`agents`, `skills`, `mcpServers`)
- plugin-local `pyproject.toml` presence and contents
- agent files at plugin root (`*.agent.md`)
- skills under `skills/*/SKILL.md`
- references under `skills/*/references/*.md`
- script entrypoints used by skills

## 3. MCP Removal Workflow (When Not Needed)

### 3.1 Remove MCP wiring

- Remove `mcpServers` from plugin manifest.
- Delete plugin `.mcp.json`.
- Delete `mcp-server/` directory.
- Remove MCP-tool instructions from agent/skills.

### 3.2 Keep behavior via direct execution

- Keep scripts under skill directories.
- Route command examples through deployable, plugin-root-relative paths.
- Ensure each plugin has a plugin-local `pyproject.toml` so `uv` runs from plugin root.
- For Python, prefer:

```bash
uv run skills/<skill-name>/<script>.py ...
```

### 3.3 Validate no stale MCP references

```bash
rg -n "mcpServers|\.mcp\.json|mcp-server|FastMCP|MCP" "$PLUGIN"
```

## 4. Skill Simplification Pattern

Apply to each `skills/<name>/SKILL.md`:

1. Keep SKILL.md short (activation-first):
   - purpose
   - direct-execution rule
   - quick-start examples
   - routing guidance
   - links to references
2. Move bulky details to `references/`:
   - long command trees
   - exhaustive options tables
   - extended examples
   - troubleshooting depth
3. Split references by safety/intent where useful:
   - show/read-only
   - request/state-changing
   - approval/workflow-specific

### 4.1 Path policy in skills and references

- Use plugin-root-relative paths in command examples.
- Avoid repository-layout paths like `plugins/<name>/...` in runtime examples.
- Avoid environment-specific absolute paths.

## 5. Agent Simplification Pattern

Apply to each `*.agent.md`:

1. Route through top-level skills only.
2. Do not directly route to nested `references/*.md`.
3. Do not directly route to helper script internals unless absolutely required.
4. Keep routing explicit:
   - which skill handles which user intent
   - destructive vs non-destructive guardrails

Recommended agent routing language:
- "Always route through the `<skill-name>` skill first; the skill chooses the underlying command path."

## 6. Naming and Structure Normalization

For each plugin:

- Skill directory names: lowercase kebab-case.
- `name` in SKILL frontmatter matches skill directory name.
- Agent file name stem matches agent frontmatter `name`.
- `plugin.json` skills list references explicit `skills/<name>` directories.
- MCP tool names referenced in agent/skill docs and frontmatter must use native Copilot MCP reference formats.

### 6.1 Native MCP Tool Reference Requirement

When MCP tools are referenced, use native formats for each surface:

- Agent/skill frontmatter (`tools`, `mcp_tools`): use `server/tool`.
- Copilot CLI permission controls (`--allow-tool`, `--deny-tool`): use `SERVER(tool)` or `SERVER`.
- Copilot runtime/telemetry may show sanitized model tool IDs such as `server-tool`; do not author these in frontmatter.
- Identifier segments may include letters, numbers, dashes (`-`), and underscores (`_`).
- In instructional prose and examples, prefer native forms over shorthand aliases.
- Do not introduce unscoped short names when a native server-scoped reference is available.

## 7. Validation Checklist (Per Plugin)

Run from repo root:

```bash
UV=/p/cth/rtl/cad/x86-64_linux44/astral/uv/latest/uv
PLUGIN=plugins/<plugin-name>

# Required: plugin-local uv project file
test -f "$PLUGIN/pyproject.toml"

# Optional: inspect plugin-local uv metadata quickly
cat "$PLUGIN/pyproject.toml"

# Rewrite generated metadata fields
$UV run python scripts/validate_plugin_metadata.py --apply

# Validate metadata contracts
$UV run python scripts/validate_plugin_metadata.py --check

# Prompt quality focus
$UV run pytest tests/prompt_quality/test_plugin_manifests.py -v
$UV run pytest tests/prompt_quality/test_agents.py -v
$UV run pytest tests/prompt_quality/test_skills.py -v
```

Optional full suites:

```bash
$UV run pytest tests/prompt_quality/ -v
$UV run pytest
```

## 8. Per-Plugin Done Criteria

A plugin is done when all are true:

- No unnecessary MCP assets remain.
- Plugin has local `pyproject.toml` suitable for `uv` execution.
- SKILL.md files are concise and activation-focused.
- Deep content moved to references and linked.
- Agent routes via top-level skills only.
- Runtime command examples are deployable and plugin-root-relative.
- No stale paths (`plugins/<name>/...` or absolute install paths) in runtime examples.
- MCP tools are referenced with native server-scoped identifiers in frontmatter and skill/agent instructions.
- Metadata and prompt-quality tests pass.

## 9. Fast Execution Loop (Repeat for each plugin)

1. Inventory plugin tree.
2. Decide MCP keep/remove.
3. Apply MCP changes (if removing).
4. Simplify skills and split references.
5. Simplify agent routing.
6. Normalize paths and ensure plugin-local `pyproject.toml` exists.
7. Validate and fix findings.
8. Move to next plugin.

## 10. Suggested Order Across Repository

Run this sequence to reduce cross-plugin dependency churn:

1. Plugins with no hard MCP dependency first.
2. Plugins already script/CLI-heavy next.
3. Plugins with shared references/agent overlap after that.
4. Strongly MCP-dependent plugins last.

## 11. Risk Controls

- Do not remove MCP when a plugin feature depends on external tool APIs unavailable via scripts.
- Keep behavior parity notes in commit/PR summaries.
- Prefer small per-plugin commits over a single large repo-wide change.

## 12. Practical Grep Commands

Useful scans while cleaning:

```bash
# Absolute or repo-layout runtime paths that should be normalized
rg -n "/p/|plugins/.*/skills/" plugins/<plugin-name>

# Direct references to nested references in agent files
rg -n "references/.*\.md" plugins/<plugin-name>/*.agent.md

# Direct script routing from agent files
rg -n "\.py|\.rb|uv run" plugins/<plugin-name>/*.agent.md

# MCP tool references to verify naming consistency
rg -n "^tools:|^mcp_tools:|run_[a-z0-9_]+|[a-z0-9_]+_query" plugins/<plugin-name>
```

---

Use this runbook as the standard template for each plugin migration pass.
