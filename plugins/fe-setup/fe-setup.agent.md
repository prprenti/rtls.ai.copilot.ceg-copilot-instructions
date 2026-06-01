---
name: fe-setup
displayName: FE Setup & Clone
description: Frontend environment setup and repository cloning — runs cth_psetup, clones repos from ceg_repos.yml, sets WORKAREA, and manages terminal sessions
keywords: setup, clone, cth_psetup, psetup, repo, environment, workarea, terminal
mcp_tools: ['fe-setup/list_repos', 'fe-setup/get_repo_info', 'fe-setup/check_terminal_setup', 'fe-setup/check_terminal_ready', 'fe-setup/inspect_workspace_git_config', 'fe-setup/match_remote_to_repo']
---

# FE Setup & Clone Agent

This agent sets up the CTH frontend environment, clones design repos, and
manages terminal sessions to ensure commands run in the correct environment.

## MCP Tools Available

- **list_repos** — browse all repos from ceg_repos.yml, optionally filtered by group
- **get_repo_info** — look up a repo by name/keyword, returns setup + clone commands
- **check_terminal_ready** — boolean check: setup exists and WORKAREA is set
- **inspect_workspace_git_config** — read [intel] section from .git/config
- **match_remote_to_repo** — match a remote URL to a known repo, derive [intel] values

---

## Workflow: Setup & Clone a Repo

### Step 1 — Identify the repo

When the user says "clone the punit" or "set up hub", call `get_repo_info` with
the relevant search term.  The tool soft-matches against repo keywords and path
components.

- **Single match** → proceed with the returned setup/clone commands.
- **Multiple matches** → present the list and ask the user to pick.
- **No matches** → show the full catalog.

> **Tip:** Check the user's `copilot-instructions.md` for directives like
> "I'm working on the punit repo's ttl-a0 branch" — use those as search context.

### Step 2 — Check terminal environment

Call `check_terminal_ready()`.

| Result | Action |
|--------|--------|
| `true` | Reuse the current terminal — skip to Step 4 |
| `false` | Open a new terminal (see Step 3) |

### Step 3 — Open a new terminal with the correct setup

Open a **named** terminal using the pattern `<cfg>/<cluster>`:
- e.g. `ttlh78/hub`, `ddgip/punit`

If a terminal with that name already exists, reuse it instead of creating a new one.

Run the setup command (the one from `get_repo_info`, which includes `-read_only`):
```bash
/p/cth/bin/cth_psetup -p ddgcth -cfg ttlh78 -read_only
```

### Step 4 — Clone the repo

Check the user's `copilot-instructions.md` for a preferred clone destination
directory.  If no directive exists, prompt the user for the desired path.

Run the clone command:
```bash
git clone /p/cth/rtl/git_repos/ddgcth/ttl/gk/ttlh78/hub-ttlh78-a0 --branch ttl-a0 /path/to/destination
```

### Step 5 — Set WORKAREA

After cloning, export WORKAREA to the clone directory:
```bash
export WORKAREA=/path/to/destination
```

---

## Important Rules

1. **Never modify the setup command** — use it exactly as returned by `get_repo_info`.
   The `-read_only` flag is already included.
2. **Always check terminal environment** before running setup — avoid redundant setups.
3. **Terminal naming** follows the `<cfg>/<cluster>` convention for easy identification.
4. **Reuse terminals** that already have the matching setup.
5. **Clone destination** must come from user directives or explicit user input — never guess.
