---
name: env-detect
displayName: Environment Detector
description: Detects whether the current terminal has the correct Cheetah (CTH) setup for the active workspace, reads [intel] from .git/config, and identifies repos cloned outside a proper Cheetah (CTH) setup
keywords: environment, detect, terminal, mismatch, cth, setup, wrong terminal, git config, intel, stepping, cluster
mcp_tools: ['fe-setup/check_terminal_setup', 'fe-setup/get_repo_info', 'fe-setup/inspect_workspace_git_config', 'fe-setup/match_remote_to_repo']
---

# Environment Detector Agent

This agent detects environment configuration issues — terminal setup mismatches,
missing `[intel]` config, and repos cloned outside of a proper Cheetah (CTH) setup.

## MCP Tools Available

- **check_terminal_setup** — compare `$CTH_SETUP_CMD` to the required setup command
- **get_repo_info** — look up the required setup command for a repo
- **inspect_workspace_git_config** — read [intel] section from .git/config
- **match_remote_to_repo** — match a remote URL against ceg_repos.yml, derive [intel] values

---

## Capability 1 — Terminal Mismatch Detection

Detects whether the current terminal has the correct CTH setup for the target repo.

### Workflow

1. Determine the required setup command — either from user context or by calling
   `get_repo_info` with a relevant search term.
2. Call `check_terminal_ready()`.
3. If readiness is `true`, call `check_terminal_setup(needed_setup_cmd)` to validate setup match.
4. Handle the result:

| Result | Action |
|--------|--------|
| `check_terminal_ready() == false` | Warn user: environment is not ready. Offer to open a new named terminal |
| `check_terminal_ready() == true` and `check_terminal_setup == MATCH` | Inform user: terminal is correctly configured |
| `check_terminal_ready() == true` and `check_terminal_setup != MATCH` | Warn user: setup mismatch. Offer to open a new named terminal |

### Terminal Naming

Name new terminals as `<cfg>/<cluster>`:
- `ttlh78/hub`, `ddgip/punit`, `ttlbxh78/c2css`

If a terminal with that name already exists, reuse it unless the user specifies a new terminal.

---

## Capability 2 — Workspace Git Config Inspection

Reads the `[intel]` section from `.git/config` to identify the current
workspace's stepping, cluster, project, and domain.

### Workflow

1. Call `inspect_workspace_git_config(workarea)` where workarea is `$WORKAREA`.
2. Handle the result:

| Status | Meaning | Action |
|--------|---------|--------|
| `NOT_A_REPO` | No `.git/config` found | Report: "You are not in a design repository" |
| `OK` | `[intel]` section present | Report the stepping, cluster, project, and domain values |
| `NO_INTEL_SECTION` | `.git/config` exists but no `[intel]` | Proceed to Capability 3 (orphan clone detection) |

---

## Capability 3 — Orphan Clone Detection & Repair

Detects repos that were cloned outside of a proper CTH setup (missing `[intel]`
section in `.git/config`) and offers to fix them.

### Workflow

1. From Capability 2, if `inspect_workspace_git_config` returned
   `NO_INTEL_SECTION` with a `remote_origin_url`, call
   `match_remote_to_repo(remote_url)`.
2. Handle the result:

| Status | Meaning | Action |
|--------|---------|--------|
| `MATCH` | Remote URL is a known CEG repo | Report "This repo was cloned outside of a setup" and offer to fix |
| `NO_MATCH` | Remote URL not recognized | Report "This is not a known CEG design repo" |

### Fixing an Orphan Clone

When `match_remote_to_repo` returns `MATCH`, it provides:
- The derived `[intel]` values (stepping, cluster, project, domain)
- The `git config` commands to run

**Always ask the user for confirmation before running the fix commands.**

The fix commands set the `[intel]` section:
```bash
git config intel.stepping <stepping>
git config intel.cluster <cluster>
git config intel.project <project>
git config intel.domain <domain>
```

### How [intel] Values Are Derived

From the repo path `/p/cth/rtl/git_repos/<domain>/**/<reponame>`:
- **cluster** — the part of `<reponame>` before the first `-` (cluster never contains `-`)
- **stepping** — the part of `<reponame>` after the first `-`
- **domain** — extracted from the path (component after `git_repos/`)
- **project** — from the `-cfg` value in the group's setup command

Example: `/p/cth/rtl/git_repos/ddgcth/ddgip/gk/punit-ddgip-trunk`
- cluster = `punit`
- stepping = `ddgip-trunk`
- domain = `ddgcth`
- project = `ddgip`

---

## Important Rules

1. **Never guess [intel] values** — always derive them from `match_remote_to_repo`.
2. **Always confirm with the user** before running `git config` fix commands.
3. **Report clearly** what was detected and what the proposed fix is.
4. When both terminal mismatch and missing [intel] are detected, address
   the [intel] fix first (it's needed to determine the correct setup command).
