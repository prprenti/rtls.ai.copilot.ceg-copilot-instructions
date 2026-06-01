# Copilot Instructions — Plugin Repo Development

This repository develops GitHub Copilot plugins, agents, skills, MCP server
configs, and code review instructions for CEG design repositories.
`copy-me-to-copilot-instructions.md` is the consumer-repo orchestration template.
This file is for work on the plugin repository itself.

Use these documents as the authority, in this order:

1. GitHub Copilot CLI plugin docs:
   - https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating
   - https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-marketplace
2. Agent Skills open standard:
   - https://agentskills.io/home
3. Repo-local publishing and validation code:
   - `scripts/validate_plugin_metadata.py`
   - `tests/prompt_quality/`

If upstream docs show a permissive shape and this repository enforces a
stricter publishing rule, follow the stricter repo rule for checked-in content
and say so explicitly in docs.

---

## Package Manager and Validation

This repo uses `uv` for dependency management and execution.

| Item | Value |
|------|-------|
| Binary | `/p/cth/rtl/cad/x86-64_linux44/astral/uv/latest/uv` |
| Python strategy | `python-preference = "only-system"` |
| Run commands | `uv run <command>` |
| Sync deps | `uv sync` |

When documenting or invoking plugin-local scripts:

- Prefer `uv run <path-to-script>` over bare `python`.
- Use deployment-safe paths relative to the plugin root (for example,
  `skills/employee-lookup/employee_lookup.py`).
- Do not hardcode repository-layout paths such as
  `plugins/access/skills/...` in plugin-facing docs, because installed
  plugins are not guaranteed to run from this repo root.

If `uv` cannot reach PyPI on the Intel network, export the Intel proxies first:

```bash
export HTTP_PROXY=http://proxy-dmz.intel.com:911
export HTTPS_PROXY=http://proxy-dmz.intel.com:912
export no_proxy=.intel.com,127.0.0.1
```

### Makefile Commands (Recommended)

For convenience, a `Makefile` at the repository root provides standard shortcuts for development tasks:

```bash
# Comprehensive validation (apply updates → check metadata → test quality → run all tests)
make validate              # Full validation pipeline

# Individual validation steps
make validate-apply        # Update generated marketplace fields from manifests
make validate-check        # Check metadata and remote plugin sources
make test-quality          # Run prompt-quality test suite only
make test-all              # Run all tests only

# Setup
make sync                  # Sync dependencies
```

The `make validate` target performs a complete validation pipeline:
1. Updates generated marketplace fields (`validate-apply`)
2. Validates all local and remote plugin metadata (`validate-check`)
3. Runs prompt-quality tests (`test-quality`)
4. Runs all tests (`test-all`)

Run `make help` to see all available commands.

### Manual Validation Commands

If you prefer explicit command-line invocation:

```bash
UV=/p/cth/rtl/cad/x86-64_linux44/astral/uv/latest/uv

# Update generated marketplace diagram from local plugins
$UV run python scripts/validate_plugin_metadata.py --apply

# Validate local and remote plugins (requires GitHub authentication)
export GH_TOKEN=$(gh auth token)
$UV run python scripts/validate_plugin_metadata.py --check --check-remotes --github-token-env GH_TOKEN

# Prompt-quality suite
$UV run pytest tests/prompt_quality/ -v

# All tests
$UV run pytest
```

---

## CI/CD Validation Pipeline

The `.github/workflows/check.yml` GitHub Actions workflow runs a comprehensive validation pipeline on every pull request:

1. **Update generated artifacts** — Rewrites marketplace diagram and metadata fields
2. **Validate plugin metadata** — Checks local and remote plugin sources with GitHub authentication
3. **Run prompt-quality tests** — Tests for prompt engineering quality standards
4. **Run all tests** — Full test suite including unit and integration tests
5. **Commit generated files** — Auto-commits any updated artifacts to the PR branch (non-fork PRs only)

This ensures that:
- Generated marketplace files stay in sync with source manifests
- Remote plugins are always validated for accessibility and correctness
- Code quality standards are enforced automatically
- PR authors see up-to-date artifacts without manual regeneration

The workflow uses `secrets.GITHUB_TOKEN` for GitHub API authentication, allowing it to access `intel-innersource` repositories without requiring additional setup.

---

### Remote Plugin Validation

Remote validation is performed by default on all validation checks. The validator fetches and validates plugin manifests from external repositories. This requires GitHub authentication because remote plugins are hosted in `intel-innersource` repositories.

**Token handling:**
- **Local development**: Token automatically fetched from `gh auth token` when running `make validate` or `make validate-check`
- **GitHub Actions (CI)**: `secrets.GITHUB_TOKEN` automatically provided via `.github/workflows/check.yml`

Remote validation warnings are non-blocking — the validation passes even if individual remote plugins have issues.

When you change Python in the validator or related prompt-quality checks, also run:

```bash
$UV run ruff check scripts/validate_plugin_metadata.py tests/prompt_quality/
$UV run python -m compileall scripts/validate_plugin_metadata.py
```

---

## Upstream Plugin Model vs Repo Policy

GitHub's plugin docs define the upstream plugin surface:

- A plugin directory must contain `plugin.json`.
- It may also contain agents, skills, hooks, and MCP configuration.
- GitHub examples show optional `agents/`, `skills/`, `hooks.json`, and `.mcp.json`.

This repository uses a stricter hosting and publishing convention for checked-in
plugins:

- Agent files live at plugin root as explicit `*.agent.md` files.
- Skill entrypoints live at `skills/<skill-name>/SKILL.md`.
- Optional skill support material lives inside the same skill directory.
- MCP server config lives at plugin root as `.mcp.json`.
- MCP implementation code, when present, lives under `mcp-server/`.
- Hooks are supported upstream, but this repo does not currently ship plugin
  `hooks.json` files. If you add hooks, also extend docs and tests rather than
  assuming existing coverage.

### Current hosted plugin shape

```text
plugins/<plugin-name>/
├── plugin.json
├── <agent>.agent.md                 # zero or more root-level agent files
├── .mcp.json                        # optional
├── mcp-server/                      # optional
│   ├── pyproject.toml
│   ├── server_<name>.py
│   ├── <module>.py
│   └── tests/
└── skills/                          # optional
    └── <skill-name>/
        ├── SKILL.md                 # required skill entrypoint
        ├── scripts/                 # optional executable helpers
        ├── references/              # optional on-demand docs
        ├── assets/                  # optional templates/resources
        └── *.py                     # optional local support code
```

The repo currently hosts these plugins:

| Plugin | Directory | MCP | Skills |
|--------|-----------|:---:|:------:|
| ceg-build-run | `plugins/build-run` | ✓ | ✓ |
| ceg-block-diagram | `plugins/block-diagram` | — | ✓ |
| ceg-rtl-design | `plugins/rtl-design` | — | — |
| ceg-validation | `plugins/validation` | ✓ | ✓ |
| ceg-access | `plugins/access` | ✓ | ✓ |
| ceg-hsd | `plugins/hsd` | ✓ | — |
| ceg-ip-management | `plugins/ip-management` | — | ✓ |
| ceg-runfv | `plugins/runfv` | ✓ | ✓ |
| ceg-turnin | `plugins/turnin` | ✓ | ✓ |
| ceg-fe-setup | `plugins/fe-setup` | ✓ | — |

---

## `plugin.json` Publishing Contract

Upstream GitHub examples allow bare directory locators such as `"skills/"`.
This repository uses explicit skill directory paths instead of bare locators.
The validator rewrites generator-owned component fields to explicit paths for
deterministic diffs, stable publishing, and easier review.

Checked-in `plugin.json` files in this repo should follow this contract:

| Field | Required | Repo rule |
|------|:--------:|-----------|
| `name` | ✓ | Lowercase kebab-case, max 64 chars |
| `description` | ✓ | Meaningful summary, at least 20 chars |
| `version` | ✓ | Semantic version |
| `keywords` | ✓ | Non-empty lowercase string list |
| `agents` | optional | Explicit `*.agent.md` file paths |
| `skills` | optional | Explicit `skills/<name>` directory paths |
| `mcpServers` | optional | Explicit manifest path, usually `".mcp.json"` |
| `commands` | optional | Explicit `.md` command file paths if used |

Example:

```json
{
  "name": "ceg-access",
  "description": "AGS entitlement management and CDIS employee directory lookups",
  "version": "0.1.0",
  "keywords": ["ags", "cdis", "access", "entitlements", "employee-lookup"],
  "agents": ["access.agent.md"],
  "skills": [
    "skills/ags",
    "skills/employee-lookup"
  ],
  "mcpServers": ".mcp.json"
}
```

Important distinctions:

- Current local plugin names happen to use a `ddg-` prefix, but validation only
  requires lowercase kebab-case. Do not document `ddg-` as a hard rule.
- `plugin.json` is the authored source of truth for local plugins.
- `.github/plugin/marketplace.json` is generated for local entries and should
  not be hand-maintained for mirrored fields.

---

## Agent Conventions

Each hosted agent is a root-level `*.agent.md` file with YAML frontmatter.

Current repo rules enforced by `tests/prompt_quality/test_agents.py`:

- Frontmatter must exist.
- `name`, `description`, and `keywords` are required.
- `name` must match the filename stem before `.agent.md`.
- `tools`, if present, must be a list.
- Body must not be a stub and should include headings.

GitHub's plugin docs allow placing agents under an `agents/` directory.
This repo does not currently do that; keep checked-in plugin agents at plugin root
unless the repo-wide convention changes deliberately.

---

## Skill Conventions

Agent Skills follow the upstream open standard from agentskills.io:

- A skill is a directory containing `SKILL.md`.
- The `name` in `SKILL.md` should match the parent directory name.
- Skills support progressive disclosure: discovery uses metadata, full
  instructions load on activation, and support files load only when referenced.

### Repo skill policy

This repository is stricter than the minimum upstream standard:

- `SKILL.md` must be the only published skill entrypoint referenced from
  `plugin.json` and `marketplace.json`.
- `references/` is for secondary documentation, not additional skill entrypoints.
- `scripts/` and local helper files may exist inside the skill directory.
- `references/`, `scripts/`, and `assets/` should be referenced from `SKILL.md`
  using relative paths.

### Naming rules

Skill directory names and the `name` field in `SKILL.md` frontmatter must use
lowercase kebab-case — the same `^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$`
pattern enforced for plugin names. Underscores are **not** allowed.

Good: `sva-properties`, `ip-release`, `hsd-query`
Bad: `sva_properties`, `ip_release`, `hsd_query`

Note: MCP tool identifiers are runtime tool IDs, not skill names.

### MCP tool reference formats (native)

Use the native MCP reference format for the surface you are editing:

- Agent/skill frontmatter (`tools`, `mcp_tools`): `server/tool`
  - Example: `build-run/run_grdlbuild`
- Copilot CLI permissions (`--allow-tool`, `--deny-tool`): `SERVER(tool)` or `SERVER`
  - Example: `build-run(run_grdlbuild)`
- Runtime-sanitized IDs may appear as `server-tool` in telemetry/internal listings.
  - Do not author `server-tool` in checked-in frontmatter.

Rules:

- Do not use unscoped shorthand tool names in frontmatter.
- Allow letters, numbers, dashes (`-`), and underscores (`_`) in server/tool segments.
- Keep examples and docs consistent with the native format for their target surface.

Example skill layout:

```text
skills/grdlbuild/
├── SKILL.md
├── references/
│   └── REFERENCE.md
├── scripts/
│   └── helper.py
└── assets/
    └── template.txt
```

### Execution and path policy

For skill documentation and examples that run local scripts:

- Use `uv run` for Python script execution.
- Prefer plugin-root-relative script paths in examples, not repo-root paths.
- Good: `uv run skills/employee-lookup/employee_lookup.py -u jsmith`
- Bad: `uv run plugins/access/skills/employee-lookup/employee_lookup.py -u jsmith`
- Bad: `/p/.../plugins/access/skills/.../employee_lookup.py`

This keeps skill commands portable across local development, marketplace
installs, and packaged plugin deployments.

### Reference support

Reference material is explicitly supported and should be used for large,
secondary, or low-frequency details.

- Put the activation summary and workflow in `SKILL.md`.
- Put large supporting docs in `references/`.
- Link them relatively from `SKILL.md`, for example:

```markdown
See [the deeper reference](references/REFERENCE.md).
```

- Do not list `references/*.md` in `plugin.json` or `marketplace.json`.
- Keep `SKILL.md` concise enough for activation. Move bulky reference material
  out of the main file when practical.
- Reference files are **excluded** from prompt-quality checks (frontmatter,
  headings, stub detection). They do not need YAML frontmatter or the
  structure required of `SKILL.md` entrypoints.

### Current repo checks for skills

`tests/prompt_quality/test_skills.py` currently enforces:

- frontmatter exists
- required fields: `name`, `description`, `keywords`
- `name` and directory use lowercase kebab-case (no underscores)
- body has a heading
- body is substantive (not a stub)
- file is not oversized
- `mcp_tools`, if present, is a non-empty string or list
- no duplicate skill names across plugins
- `references/` subdirectories are excluded from all skill checks above

The validator additionally enforces that published skill refs are explicit
`skills/<name>` directory paths, each containing a `SKILL.md` entrypoint.

---

## Marketplace Conventions

GitHub's marketplace docs define the baseline shape:

- `.github/plugin/marketplace.json` is the standard marketplace location.
- Upstream also recognizes `.claude-plugin/marketplace.json`.
- The only required marketplace component is `marketplace.json`.
- GitHub examples use `source` paths relative to repo root.

This repository standardizes on `.github/plugin/marketplace.json` and uses the
validator to keep local entries synchronized with local `plugin.json` files.

### `source` field guidance

When writing docs or editing publisher logic, keep these distinctions explicit:

- Upstream marketplace examples use repo-relative paths such as `plugins/foo`.
- This repository's validator also supports:
  - repo-relative local paths
  - GitHub `OWNER/REPO:PATH` strings
  - GitHub repository URLs
  - structured GitHub source objects with `repo`, `path`, and optional `ref` / `sha` / `commit`
- For externally hosted plugins, prefer a source shape that keeps the hosting
  repo and plugin root explicit.
- If you want `--check-remotes` to fetch and compare a remote `plugin.json`, use
  a structured source with an explicit `ref`, `sha`, or `commit`.

### Local publishing workflow

For local plugins hosted in this repo:

1. Edit the plugin's `plugin.json`.
2. Keep generated component refs explicit.
3. Append a minimal marketplace entry if adding a new plugin.
4. Run:

```bash
$UV run python scripts/validate_plugin_metadata.py --apply
$UV run python scripts/validate_plugin_metadata.py --check
```

5. Run the relevant prompt-quality checks:

```bash
$UV run pytest tests/prompt_quality/test_plugin_manifests.py -v
$UV run pytest tests/prompt_quality/test_skills.py -v
```

### Local CLI testing

GitHub's plugin docs note that CLI installs are cached. When testing a local
plugin after edits, reinstall it so Copilot CLI refreshes the cache:

```bash
copilot plugin install ./plugins/<name>
copilot plugin list
```

Useful interactive checks:

```text
/plugin list
/agent
/skills list
```

---

## MCP Server Conventions

When a plugin has an MCP server:

- root config is `.mcp.json`
- implementation code lives under `mcp-server/`
- `server_<name>.py` creates the `FastMCP` instance
- server logging goes to stderr, not stdout
- keep `mcp-server/pyproject.toml` minimal
- each `mcp-server/` directory must have a committed `uv.lock` file

### Required `.mcp.json` environment keys

Each plugin's `.mcp.json` must set these environment variables in the server's
`env` block so `uv` can resolve, install, and run in frozen mode on the Intel
network:

| Key | Purpose | Example value |
|-----|---------|---------------|
| `WORKAREA` | Workspace root for tool runtime | `${workspaceFolder}` |
| `UV_FROZEN` | Prevent `uv` from modifying the lock file at runtime | `1` |
| `UV_PROJECT_ENVIRONMENT` | Isolate the venv per plugin | `${workspaceFolder}/.vscode/.<plugin>-mcp-venv` |
| `UV_CONCURRENT_INSTALLS` | Limit parallel install jobs | `4` |
| `UV_CONCURRENT_BUILDS` | Limit parallel build jobs | `4` |
| `UV_CONCURRENT_DOWNLOADS` | Limit parallel downloads | `8` |
| `HTTP_PROXY` | Intel corporate proxy (uppercase) | `http://proxy-dmz.intel.com:911` |
| `HTTPS_PROXY` | Intel corporate proxy (uppercase) | `http://proxy-dmz.intel.com:912` |
| `http_proxy` | Intel corporate proxy (lowercase) | `http://proxy-dmz.intel.com:911` |
| `https_proxy` | Intel corporate proxy (lowercase) | `http://proxy-dmz.intel.com:912` |
| `no_proxy` | Bypass list | `intel.com,.intel.com,localhost,127.0.0.0/8,10.0.0.0/8,192.168.0.0/16,134.134.0.0/16,.azure-api.net,azurewebsites.net` |

Both upper- and lowercase proxy variables are required because different
libraries check different casings.

### Dependency locking

Every plugin `mcp-server/` project must have a `uv.lock` checked in alongside
its `pyproject.toml`. Generate or refresh the lock file from inside the
plugin's `mcp-server/` directory.

Use the same `uv` version for lock generation that the plugin uses at runtime.
The runtime `uv` version is defined in the plugin's root `.mcp.json`; do not
use `latest/uv` here, because a different `uv` version can produce a lockfile
format or revision that the pinned runtime binary cannot consume.

```bash
# Copy the `command` path from plugins/<plugin-name>/.mcp.json
UV=<uv-path-from-plugin-root-.mcp.json-command>
cd plugins/<plugin-name>/mcp-server
$UV lock
```

If `uv` cannot reach PyPI on the Intel network, export the Intel proxies first:

```bash
export HTTP_PROXY=http://proxy-dmz.intel.com:911
export HTTPS_PROXY=http://proxy-dmz.intel.com:912
export no_proxy=.intel.com,127.0.0.1
```

Re-run `$UV lock` after any change to `pyproject.toml` dependencies and commit
the updated `uv.lock`.

Repo-specific operational rules:

- Tool implementations that pass user strings to shell commands must sanitize inputs.
- File-reading tools must guard against path traversal.
- Prefer shared build/setup tools from existing plugins rather than cloning that logic.

### Shared tool reuse

Do not create duplicate build and environment helpers when existing plugin tools
already own that responsibility.

- Reuse `ceg-build-run` MCP tools such as `run_grdlbuild` and `run_make`.
- Reuse `ceg-fe-setup` tooling for repo matching, terminal setup checks, and
  workspace/environment discovery.

If an agent or skill depends on these, declare the relevant tools and link the
corresponding shared skill documentation.

---

## Code Review Instruction Files

`code_review/` contains scoped `.instructions.md` rule sets used for automated
review. These are not plugin skills.

Current checked-in rule sets:

- `build-run-code-review.instructions.md`
- `cdc-code-review.instructions.md`
- `rtl-code-review.instructions.md`
- `rtl-lint-code-review.instructions.md`

Current repo expectations:

- use targeted `applyTo` scopes
- include `description` and `keywords` in frontmatter
- provide concrete bad/good examples
- include grep-able or otherwise mechanical detection guidance
- organize by severity and keep rule IDs unique

Avoid documenting vague or repo-wide `**/*` review scopes as acceptable.

---

## Test Map

The prompt-quality suite is the live contract for checked-in authoring.

| Test file | Current purpose |
|-----------|-----------------|
| `test_plugin_manifests.py` | `plugin.json` required fields, lowercase kebab-case names, lowercase keywords, explicit `SKILL.md` refs, marketplace consistency |
| `test_agents.py` | agent frontmatter, filename/name match, tools-list shape, content quality |
| `test_skills.py` | skill frontmatter, size/quality checks, duplicate-name checks, skill discovery expectations |
| `test_instructions.py` | instruction frontmatter, `applyTo` sanity, anti-patterns |
| `test_validate_plugin_metadata.py` | publisher/validator behavior, source parsing, generation rules, remote validation behavior |
| `test_create_plugin_marketplace_entry.py` | emitted single-plugin marketplace entry shape |

When behavior changes, update docs and tests together.

---

## Quick Commands

```bash
UV=/p/cth/rtl/cad/x86-64_linux44/astral/uv/latest/uv

# Setup
$UV sync

# Validate local and remote plugins
export GH_TOKEN=$(gh auth token)
$UV run python scripts/validate_plugin_metadata.py --check --check-remotes --github-token-env GH_TOKEN

# Or use the Makefile (recommended):
make validate

# Rewrite local generated fields
$UV run python scripts/validate_plugin_metadata.py --apply

# Prompt-quality suite
$UV run pytest tests/prompt_quality/ -v

# Full tests
$UV run pytest

# Add this repo as a marketplace
copilot plugin marketplace add intel-innersource/rtls.ai.copilot.ceg-copilot-instructions

# Install a local plugin for iterative testing
copilot plugin install ./plugins/build-run
```
