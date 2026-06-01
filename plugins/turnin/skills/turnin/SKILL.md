---
name: turnin
description: Turn in or mock turn in code changes for CEG design repositories — handles working-tree prep, repo-type routing, code review, Intel submission, GitHub PRs, and pipeline status
keywords: turnin, mock, submit, code review, PR, open_code_review, gatekeeper, pipeline
mcp_tools: turnin/run_turnin, turnin/turnin_query, turnin/turnin_my_status, turnin/turnin_pipeline_query, turnin/gatekeeper_list_turnins, turnin/gatekeeper_read_log, turnin/gatekeeper_latest_status
---

# Turnin Skill

> **PURPOSE:** Route CEG repositories through the correct submission path and keep state-changing actions approval-gated.
> **WHEN TO USE:** Apply when a user asks to turn in code, run a mock turnin, refresh an Intel code review, create a GitHub PR, or inspect turnin or pipeline status.

**MCP-First Rule:** ALWAYS use MCP tools — NEVER run `turnin` or `turnininfo` directly in a terminal.

| MCP Tool | Purpose |
|----------|---------|
| `run_turnin` | Execute turnin, open_code_review, and mock commands |
| `turnin_query` | Query a specific turnin ID |
| `turnin_my_status` | List your recent turnins |
| `turnin_pipeline_query` | Show pipeline status |
| `gatekeeper_list_turnins` | List GATEKEEPER/ turnin sessions |
| `gatekeeper_read_log` | Read a gatekeeper log file |
| `gatekeeper_latest_status` | Quick summary of most recent turnin |

## Core Decisions

Classify the request before taking action:

- **Status or diagnostics only**: Read-only checks. No approval required.
- **GitHub PR workflow**: Standard GitHub flow. Keep separate from Intel turnin flow.
- **Intel submission or mock turnin**: Any `open_code_review`, `turnin`, refresh, retry, or mock auto-submit requires explicit user approval before execution.

Route based on `.git/config`:
- No `[intel]` section + `github.com` remote → **GitHub Path**: push branch, create PR.
- `[intel]` section present → **Intel Path**: use `run_turnin` for all submission commands.

Never mix the two paths in one workflow. Never assume stepping, cluster, or project from another repo.

## Working Tree Pre-Check

Run `git status` before any real submission or repo-head mock. A clean tree is required.

For uncommitted changes, prompt the user to: add & commit (only files needed), discard (requires confirmation), or ignore (add to `.gitignore`). Status-only requests and `-no_clone` mocks do not require a clean tree.

## Intel Workflow (summary)

1. **Verify environment** — delegate to `@fe-setup` or `@env-detect` first.
2. **Check for existing code review** — check `GATEKEEPER/code_review_debug.log`:
   - If file exists: extract `head.ref` from JSON after `"Pull request details: "` and offer to update (`--force`) or create new.
   - If not: ask for PR title/description, then call `run_turnin(command="open_code_review --title ... --body ... --feature_branch <branch>")`.
3. **Submit** — after `open_code_review` succeeds, get cluster/stepping/project from `git config --get intel.<field>`, then ask for approval before calling `run_turnin(command="turnin -c <cluster> -s <stepping> -b master -proj <project>")`.

See [Intel Workflow Reference](references/TURNIN_WORKFLOW_REFERENCE.md) for the Intel configuration table, mock decision tree, and detailed mock routing rules.

## Status Checks

- `turnin_query` — query by turnin ID
- `turnin_my_status` — your pending submissions
- `turnin_pipeline_query` — pipeline status
- `gatekeeper_list_turnins` / `gatekeeper_read_log` / `gatekeeper_latest_status` — GATEKEEPER/ log access

## NEVER Rules

- NEVER run `turnin` or `turnininfo` in a terminal — use MCP tools.
- NEVER submit or refresh a code review without explicit user approval.
- NEVER discard or reset local files without explicit user approval.
- NEVER mix the GitHub PR path with the Intel turnin path by default.
- NEVER assume repo-specific stepping, cluster, or project from another CEG repo.
- NEVER present a mock as equivalent to a completed submission.
- NEVER add unrelated staged files to a submission to clean the tree.
- NEVER treat `-mock -no_clone` as proof the change merges cleanly with repo head.

## Examples

- Nominal: User requests mock turnin on Intel repo → verify environment → determine mock mode (see [Workflow Reference](references/TURNIN_WORKFLOW_REFERENCE.md)) → require approval for any `-submit` path → call `run_turnin`.
- Edge: No `[intel]` config but GitHub remote → GitHub PR path, ask before publishing branch.
- Edge: Update existing review → read `GATEKEEPER/code_review_debug.log`, extract `head.ref`, call `open_code_review --feature_branch <ref> --force` via `run_turnin`.

## Do NOT Use For

- Deep pipeline forensics after submission is running.
- Repo-specific policy that overrides shared CEG guidance.

## Further Reference

- [Intel Workflow Reference](references/TURNIN_WORKFLOW_REFERENCE.md) — Intel config table, mock decision tree, mock routing rules
- [Gatekeeper Reference](references/GATEKEEPER_REFERENCE.md) — turnin/turnininfo command syntax, GATEKEEPER/ log layout, troubleshooting
