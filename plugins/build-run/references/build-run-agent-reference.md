# Build & Run Agent Reference

Use this reference for detailed MCP tool semantics and delegated command payload handling.

## `run_grdlbuild`

Run a Gradle-based build task via the `grdlbuild` wrapper.

```text
run_grdlbuild(task, extra_args="", timeout=600)
```

| Parameter | Type | Description |
|---|---|---|
| `task` | str | Gradle task name (e.g. `all`, `codegen_rtl`, `vc_cdc`, `vc_lp`, `vcssim`, `lint`) |
| `extra_args` | str | Additional CLI arguments (default: `""`) |
| `timeout` | int | Max seconds to wait (default: 600) |

Common tasks:

| Task | Purpose |
|---|---|
| `codegen_rtl` | Generate RTL collateral (run before proofs or simulation) |
| `all` | Run all tasks for a scope |
| `vc_cdc` | Clock-domain crossing analysis |
| `vc_lp` | Low-power analysis |
| `lint` | RTL lint checks |
| `vcssim` | VCS simulation |
| `vcssimmpp` | VCS simulation (multi-processor) |

Common extra_args:

| Flag | Purpose | Example |
|---|---|---|
| `-local` | Run on local machine (default, always include) | `-local` |
| `-nb` | Run on Netbatch (only when user requests) | `-nb` |
| `-dut <name>` | Target a specific DUT | `-dut hubs` |
| `-run_modes <mode>` | Filter by run mode | `-run_modes turnin` |
| `-id` | Ignore dependencies (run only this task) | `-id -local` |
| `-sft` | Start from task (skip earlier deps) | `-sft -local` |
| `-sat` | Start after task (skip task + earlier deps) | `-sat -local` |
| `-st` | Show tasks (dry run) | `-st` |
| `-std` | Show tasks with dependencies | `-std` |

Examples:

```text
run_grdlbuild(task="codegen_rtl")
run_grdlbuild(task="all", extra_args="-dut hubs -run_modes turnin -local")
run_grdlbuild(task="vc_cdc", extra_args="-local")
run_grdlbuild(task="all", extra_args="-st -dut hubs")
```

## `run_make`

Run a `make` target in the repo or a subdirectory.

```text
run_make(target, directory="", timeout=600)
```

| Parameter | Type | Description |
|---|---|---|
| `target` | str | Make target (e.g. `all`, `clean`, `filelist`, `jg_superlint`) |
| `directory` | str | Subdirectory relative to `$WORKAREA` (default: repo root) |
| `timeout` | int | Max seconds to wait (default: 600) |

Examples:

```text
run_make(target="jg_superlint", directory="static/jasper")
run_make(target="clean", directory="static/jasper")
run_make(target="all")
```

## Delegated Command Execution

Any agent or skill may build commands and return them as a JSON object for this
agent to execute. This is the standard pattern for agents that need shell
execution but do not own an execution MCP tool.

### JSON Command Protocol

When you receive a JSON object from another agent's MCP tool, follow this
procedure:

1. Check for `error`; if present, report it and stop.
2. Write script files when payload includes script content.
3. Run commands in order from the `commands` list.
4. Use the payload `cwd` value (typically `$WORKAREA`).
5. Read `notes` for edge-case guidance.

Expected JSON shape:

```json
{
  "commands": ["cmd1", "cmd2", "..."],
  "cwd": "/path/to/workarea",
  "notes": ["guidance string", "..."]
}
```

Optional fields for script-based tools:

```json
{
  "tcl_script": "script content...",
  "tcl_filename": "script_name.tcl",
  "tcl_dir": "$WORKAREA/output/formal/jg_cmd"
}
```

Known delegating example:

| Agent | Tool | What it returns |
|---|---|---|
| `@runfv` | `jg_cmd` | JasperGold batch Tcl commands |
