# Gatekeeper Reference

> **MCP-First Rule:** ALWAYS use MCP tools instead of running commands directly:
> - **`run_turnin`** for `turnin` commands
> - **`turnin_query`** for `turnininfo <id>` lookups
> - **`turnin_my_status`** for `turnininfo -my` queries
> - **`turnin_pipeline_query`** for pipeline status
> - **`gatekeeper_list_turnins`**, **`gatekeeper_read_log`**, **`gatekeeper_latest_status`** for GATEKEEPER/ log access

---

## Key Commands

### turnin

**Required Options:**
- `-c <cluster>` — Cluster name (e.g., `hub`)
- `-s <stepping>` — Stepping identifier (e.g., `ttlh78-a0`)
- `-b <branch>` — Branch name (default: `master`)
- `-proj <project>` — Project name (default from config)

**Basic Turnin:**
```bash
turnin -c <cluster> -s <stepping> -b master -proj <project>
```

**With Comments:**
```bash
turnin -c <cluster> -s <stepping> -b master -proj <project> -comments "Description of changes"
```

**With Bug/ECO References:**
```bash
turnin -c <cluster> -s <stepping> -b master -proj <project> -bugs "12345, 67890" -ecos "11111"
```

**Mock Turnin Options:**
- `-mock` — Run build and regression commands in local area (does not submit)
- `-mock -submit` — Run mock and submit if successful
- `-mock -no_clone` — Mock without cloning/merging with master repo
- `-mock -clone` — Mock with clone and merge (default)

**Other Useful Options:**
- `-commands` — Print build and regression commands without executing
- `-info` — Information about the pipeline
- `-motd` — Show active announcements
- `-cancel <id>` — Remove turnin from pipeline
- `-maillist "user1,user2"` — Additional email recipients

### turnininfo

**Query by Turnin ID:**
```bash
turnininfo <id>
turnininfo -id <id>
```

**Query Your Turnins:**
```bash
turnininfo -my                    # Your pending turnins
turnininfo -my -all               # Your pending and completed turnins
turnininfo -my -days 7            # Your turnins from last 7 days
turnininfo -my -recent            # Your turnins from last day
```

**Query by Pipeline:**
```bash
turnininfo -c <cluster> -s <stepping> -b <branch>
turnininfo -c <cluster> -s <stepping> -b <branch> -pending
turnininfo -c <cluster> -s <stepping> -b <branch> -all
```

**Query by User:**
```bash
turnininfo -user <username>
turnininfo -user <username> -all
```

**Query by Bug/ECO:**
```bash
turnininfo -bug <bug_id>
turnininfo -eco <eco_id>
```

**Output Formats:**
- `-short` — Brief output
- `-long` — Longer output
- `-report` — Turnin report data
- `-history` — Historical data about the turnin
- `-comments` — Display user comments column
- `-format json -output <file>` — JSON output to file

---

## GATEKEEPER Directory

The `GATEKEEPER/` directory in the repository root contains all log information for turnins.

### Turnin Logs
- `turnin.<timestamp>.log` — Main turnin log with full details
- `turnin.<timestamp>.id` — Contains the turnin ID number
- `turnin_comments` — User-provided turnin comments
- `turnin_changelog.<pid>` — Git changelog of commits being submitted
- `turnin_files_changed.<pid>` — List of files changed in the turnin

### Code Review Logs
- `code_review_debug.log` — Detailed code review process log
- `code_review_url.<pid>.txt` — URL to the GitHub pull request

### Pre-turnin and Post-submit Hooks
- `preturnin.command` / `preturnin.<pid>.command` — Pre-turnin check commands
- `preturnin.env` / `preturnin.<pid>.env` — Environment for pre-turnin checks
- `gk_pre_turnin_checks.<pid>.log` — Pre-turnin check results
- `post_submit.command` / `post_submit.<pid>.command` — Post-submit hook commands
- `gk_post_submit_hook.<pid>.log` — Post-submit hook results

### Finding the Turnin ID

1. **From the ID file:**
   ```bash
   cat GATEKEEPER/turnin.*.id
   ```

2. **From the turnin log:**
   ```bash
   grep "Received turnin" GATEKEEPER/turnin.*.log
   ```

3. **From monitoring section** — Look for "To monitor your turnin" in the log.

---

## Common Workflows

### Check Status of Your Pending Turnins
```bash
turnininfo -my
```

### Monitor a Specific Turnin
```bash
turnininfo <turnin_id>
turnininfo <turnin_id> -history
```

### View Pipeline Information
```bash
turnin -c <cluster> -s <stepping> -b master -info
```

### List Power Users for Help
```bash
turnin -c <cluster> -s <stepping> -b master -list_powerusers
```

### Cancel a Turnin
```bash
turnin -cancel <id> -reason "Reason for cancellation"
```

### Check What Commands Would Run
```bash
turnin -c <cluster> -s <stepping> -b master -commands
```

---

## Troubleshooting

### Check Pre-turnin Failures
```bash
cat GATEKEEPER/gk_pre_turnin_checks.*.log
```

### Check Code Review Issues
```bash
cat GATEKEEPER/code_review_debug.log
```

### View Files That Were Changed
```bash
cat GATEKEEPER/turnin_files_changed.*
```

### View Commit History Being Submitted
```bash
cat GATEKEEPER/turnin_changelog.*
```
