---
name: netbatch
description: Diagnose NetBatch job state, feeder liveness, queue pressure, and pool or class resolution in CEG compute environments. Use when jobs are waiting, feeders look stuck, or pool and qslot settings are unclear.
keywords: netbatch, nbstatus, nbtask, nbjob, feeder, qslot, pool, class, farm, regression, waiting, stuck, job, cancel
---

# NetBatch Diagnosis Skill

> PURPOSE: Investigate NetBatch scheduler state, feeder health, queue pressure, and safe stop decisions.
> WHEN TO USE: Apply when jobs are waiting too long, regressions appear stuck, feeder state is unclear, qslot capacity is suspected, or a task may need to be stopped without losing history.

## Core Principle: Investigate First, Act Later

**Start read-only. Do not submit, cancel, or mutate until root cause is confirmed.**

## Routing Guidance

- Use this skill for scheduler-state questions: job wait reasons, feeder health, qslot pressure, class constraints, and safe stop decisions.
- Do not use this skill for failure-content triage inside completed runs.
- Do not use this skill for session composition or testlist editing.

## Decision Guide

- Jobs are waiting right now: start with `qslots`, then inspect live `jobs` fields such as `Status` and `WaitReason`.
- Feeder might be dead or wedged: check feeder artifacts in the regression directory first, then confirm with `nbstatus feeders`.
- Need to stop work without losing history: identify the task ID and feeder target, then use `nbtask stop`.
- Need facts about completed or older jobs: switch to `--history` mode and use only history-safe fields.

## Investigation Workflow

### Step 1 — Check feeder liveness

Regressions are dispatched by a feeder process. Check if it is still active:

```bash
# A sentinel file indicates the feeder is running
ls <regression_dir>/.ifeed_is_running    # present → feeder running; absent → feeder exited
```

If absent and jobs are still expected, the feeder may have crashed. Check feeder logs in the regression directory.

### Step 2 — Qslot health snapshot

Check the queue depth and health for your team's qslot:

```bash
nbstatus qslots --target <your_pool> \
  --fields Name,Status,Running,Waiting,ShouldGet,GettingNow \
  --format lc-keys-json-script \
  "Name=='<your_qslot>'"
```

- `Status: "open:active"` + `Waiting: 0` = healthy
- High `Waiting` count = queue pressure
- `Status` not `open:active` = qslot may be disabled or draining

Replace `<your_pool>` and `<your_qslot>` with your team's NetBatch pool and qslot path. These are typically defined in your workspace's CTH configuration or documented in your team's regression setup.

### Step 3 — Group activity by user/status

See who is consuming capacity on your qslot:

```bash
nbstatus jobs --target <your_pool> \
  --fields User,Status,Class \
  --format lc-keys-json-script \
  --group-by User,Status \
  "Qslot=='<your_qslot>'"
```

### Step 4 — Drill into your jobs

```bash
nbstatus jobs --target <your_pool> \
  --fields Fullid,Status,WaitReason,Class,Task,Workstation,TimeInRunning \
  --format lc-keys-json-script \
  "Qslot=='<your_qslot>'&&User=='$USER'"

# Filter by task name
nbstatus jobs --target <your_pool> \
  --fields Fullid,Status,WaitReason,Task,TimeInRunning \
  --format lc-keys-json-script \
  "Task=='<your_task_name>'"
```

### Step 5 — Full detail on a single job

```bash
nbstatus jobs --target <your_pool> \
  --fields Fullid,Status,WaitReason,Cmdline,JobLogFile,Class,SubmitTime,JobTrace \
  --format json \
  --number 1 \
  "Qslot=='<your_qslot>'&&User=='$USER'"
```

`Cmdline` shows the full simulation command; `JobTrace` shows VP-to-PPM routing decisions.

### Step 6 — Historical jobs

```bash
nbstatus jobs --target <your_pool> \
  --history 48h \
  --fields Fullid,User,ExitStatus,Task,FinishTime \
  --format lc-keys-json-script \
  "Qslot=='<your_qslot>'&&User=='$USER'"
```

> **History field restriction**: `Status` and `TimeInRunning` fail with error 246 in `--history` mode. Safe history fields: `Fullid`, `User`, `ExitStatus`, `Task`, `FinishTime`, `SubmitTime`, `Cmd`, `Class`, `Workstation`.

### Step 7 — Active feeders

```bash
nbstatus feeders --target <your_pool> \
  --fields Name,Status,User,Host,StartTime,WorkArea \
  --format table \
  "User=='$USER'"
```

### Step 8 — Workstation load (hung or slow jobs)

```bash
/var/netstar/bin/nbadmin workstation status | awk '/Load: /    {print $2}'
/var/netstar/bin/nbadmin workstation status | awk '/CPUCount:/ {print $2}'
```

If `Load` exceeds `CPUCount`, the host is saturated and jobs will run slowly.

## nbstatus Quick Reference

### Key Subcommands

| Subcommand | Use |
| ---------- | --- |
| `jobs` | Job state, fields, timing — primary investigation tool |
| `qslots` | Queue depth and health |
| `feeders` | Active regressions: user, host, workarea |
| `problems` | Scheduler-reported health issues |
| `schema-fields` | Discover valid field names for a subcommand |

### Key Fields for `nbstatus jobs`

| Field | History? | Purpose |
| ----- | :------: | ------- |
| `Fullid` | Yes | Full job ID (`pool.NNNNN`) |
| `Status` | No | `Run` / `Wait` / `Wait Remote` |
| `WaitReason` | No | Why job is waiting |
| `Task` | Yes | Feeder task name |
| `Cmdline` | Yes | Full command line |
| `Class` | Yes | Class constraint (e.g., `SLES15&&32G`) |
| `ExitStatus` | Yes | `0` = pass, nonzero = fail |
| `JobLogFile` | Yes | Log filename |
| `TimeInRunning` | No | Wall-clock time since dispatch |
| `Qslot` | Yes | Use in filter expressions |

### Filter Syntax

```bash
# AND with &&; OR is not supported — run separate queries
# String values single-quoted inside double-quoted shell strings
"Qslot=='<your_qslot>'&&User=='$USER'"
"Status=='Wait'"
"Task=='<your_task_name>'"
```

### WaitReason Decoder

| WaitReason | Meaning | Action |
| ---------- | ------- | ------ |
| `not candidate yet` | VP received job but has not dispatched to PPM | Normal lag — wait briefly, not an error |
| `no available resource` | No matching workstation free | Queue pressure — check qslot capacity |
| `exec limit` | Job hit execution time limit | Job needs more time or is hanging — investigate |

### ExitStatus Decoder

Classify terminal jobs from `nbstatus jobs --history` before blaming the workload itself.

| ExitStatus | Meaning | First checks |
| ---------- | ------- | ------------ |
| `-4` | Executable could not be started | Verify the executable path exists on the execution site, is executable, has a valid interpreter, and was not submitted as one quoted shell string like `"cmd -arg"`. |
| `-6` | Job leader died before normal execution | Inspect host-local NetBatch internal logs if available; this usually points to workstation-local process creation or host health issues. |
| `-7` | Waiting job removed by user or tool | The payload never ran. Check task cancellation, `nbjob remove`, feeder cancellation, or higher-level automation cleanup. |
| `-8` | Running job killed by non-root remote request | Inspect `JobKiller` or `KillReason` in NB Console if available, then correlate with pool command logs. |
| `-10` | Task-level aggregate failure | Drill into the individual jobs. This status is a summary, not the root cause. |
| `-13` | Root-side kill request | Often memory pressure or explicit root removal. Check `KillReason`, compare requested class versus observed memory usage, and inspect root or pool command logs if memory evidence is weak. |
| `-14` | Job resubmitted after kill | Commonly memory victim selection on an overloaded host. Compare reservation versus observed usage. |
| `-30` / `-32` / `-33` / `-35` | Log file open or create failure | Check the resolved log path, directory existence on the execution host, write permissions, and whether multiple jobs collide on the same filename. |
| `-36` | Interactive client or socket failure | The submitting `nbjob` client died or disconnected. Verify submission-host stability for interactive or blocking jobs. |
| `-48` | Failed to `chdir` to work dir | Confirm the working directory exists and is accessible from the selected workstation. |
| `-50` | Log write failed after job started | Check disk fullness, inode exhaustion, quota, and whether the NFS path disappeared mid-run. |
| `-58` / `-62` / `-66` | Process died from signal | Usually application-side crash or external `SIGTERM`, not a scheduler wait-state issue. |
| `-300` | Dispatch fail | Internal NetBatch dispatch problem. If it does not auto-recover, inspect PPM or workstation-manager logs. |
| `-303` | `--pre-exec` failed | Read `PreExecExitStatus` and classify that nested exit code before analyzing the main job. |
| `-305` | Removed with `nbjob remove --force` | Identify the remover via `JobKiller` and pool command logs. |
| `-308` | Job not synced | Workstation-side state disappeared; this is common after reinstall or local state wipe. |
| `-340` | Privileged pre-exec failed | Usually NetBatch internal setup around disk reservation, sandboxing, or container preparation. |
| `-1004` | Killed by local disk usage cap | The job exceeded the local disk-space guardrail. Inspect scratch usage and cleanup policy. |
| `-1900` | Resubmitted by workstation memory policy | Host approached memory or swap exhaustion. Treat this as strong memory-pressure evidence. |
| `-3002` | Killed on run-away or exec limit | Check job or qslot exec limits. This is usually an expected policy kill. |
| `-3005` | Job constraints exceeded | Review job and qslot constraint settings. NetBatch does not always identify the exact clause that tripped. |
| `-3006` | Interactive client disconnected | For interactive jobs, the client stopped consuming output. |
| `-3017` | Feeder task canceled | Inspect the parent task exit reason and the tool log that triggered feeder cancellation. |
| `-3020` | Delegate job could not connect back to feeder | Usually delegate or feeder networking incompatibility, routing, or host-placement issue. |
| `-3023` | Job removed by nbfeeder | Search the feeder command log for `remove` near the kill time. |
| `-3027` | Delegate was killed | Find the delegate and diagnose its exit status; a common underlying cause is a delegate memory kill such as `-13`. |
| `-6002` | Recovery from persistency failed | Often workstation crash, reboot, or workstation-manager restart during job completion. |

### Cross-Team Heuristics

- `ExitStatus=-13` plus a message like `Job killed by super user request` is not enough by itself to conclude out-of-memory. Corroborate with reservation versus observed usage or a concrete `KillReason`.
- If observed peak memory materially exceeds the reserved class, do not keep retrying the same class. Move to the next valid team-approved memory tier and record the sizing evidence.
- If many jobs die immediately with `NB_JOBEXITSTATUS=255`, inspect generated launcher inputs and wrapper scripts before blaming the scheduler. Malformed tasklists, manifests, reglists, or quoting bugs can fail post-processing uniformly.

### Failure Triage Order

When a job is terminal, classify in this order:

1. Was it ever dispatched?
If it died while waiting, prefer `WaitReason`, `-7`, and feeder or task cancellation paths.

2. Did NetBatch fail before the payload started?
Prefer `-4`, `-6`, `-30`, `-32`, `-33`, `-35`, `-48`, `-303`, and `-340` before blaming the workload.

3. Was it scheduler-killed after dispatch?
Prefer `-8`, `-13`, `-14`, `-1900`, `-3002`, `-3005`, `-3017`, `-3023`, and `-3027`, then inspect `JobKiller`, `KillReason`, exec limits, delegate failure, or parent-task cancellation.

4. Did the payload itself crash?
Prefer `-58`, `-62`, and `-66`, then switch to workload-local logs and crash artifacts.

## Stopping NetBatch Tasks

> **Use `nbtask stop`, NOT `nbtask delete`.** `stop` kills remaining jobs and preserves the task in scheduler history. `delete` removes the record and loses debug evidence.

### Stopping a grdlbuild task

Build tasks use a per-user login-node daemon; the target name is hostname-anchored:

```bash
# 1. Find task name and feeder target
cat $WORKAREA/output/grdlbuild/nbtasks/<taskname>_*.nbtask.feeder_data
# feederTarget:grdlbuild_<username>_<hostname>

# 2. Stop the task
nbtask stop --target grdlbuild_<username>_<hostname> <task_id>

# 3. Kill any local gradle process still waiting
ps aux | grep "[g]rdlbuild\|[g]radle"
kill <pids>
```

### Stopping a simregress (ifeed) task

Simulation regressions use a shared persistent nbfeeder daemon — multiple regressions share one daemon instance:

```bash
# 1. Get task ID and feeder target from ifeed.log
grep "Task Id\|--name" <regression_dir>/ifeed.log
# Task Id : 63
# --name <user>_<host>_<site>_<pid>_<timestamp>

# 2. Stop the task
nbtask stop --target <feeder_target_from_above> <task_id>

# 3. Verify feeder exits
ls <regression_dir>/.ifeed_is_running    # should disappear
```

> If `ifeed.log` is unavailable, find your feeder target via:
> `nbstatus feeders --target <your_pool> --fields Name,Status,User,NumRunning --format table "User=='$USER'"`

## Finding Your Pool and Qslot

If you don't know your team's NetBatch pool and qslot:

```bash
# Check CTH configuration for NetBatch settings
grep -ri 'pool\|qslot\|nbqueue\|nbclass' $WORKAREA/cfg/ $WORKAREA/verif/ 2>/dev/null | head -20

# Check for a nb_settings script
find $WORKAREA/scripts -name 'nb_settings*' 2>/dev/null

# Ask a running feeder
nbstatus feeders --target <any_known_pool> \
  --fields Name,User,Host \
  --format table \
  "User=='$USER'"
```

Pool and qslot paths are repo- and team-specific. Consult your team's documentation or workspace configuration if these methods don't return results.

## Repo Discovery Before Live Queries

Before calling `nbstatus`, first mine the repo for the queue vocabulary it already uses.

```bash
# Strongest signals in validation repos
rg -n '\.nbclass|NBPOOL|NBQSLOT|Qslot|nbqueue|\.ifeed_is_running|ifeed.log' $WORKAREA -g '!subip/**' | head -40

# Common locations for queue/class evidence
rg -n '\.nbclass' $WORKAREA/reglist $WORKAREA/src $WORKAREA/dfx 2>/dev/null | head -20
rg -n 'NBPOOL|NBQSLOT|Qslot|nbqueue' $WORKAREA/verif $WORKAREA/flows $WORKAREA/scripts 2>/dev/null | head -20
```

Use what you find to choose the live query inputs:

- `.nbclass (...)` tells you the class constraint even when no pool is visible yet.
- `NBPOOL`, `NBQSLOT`, or `Qslot` in Makefiles, JSON, or `tool.cth` files tells you the target pool and queue.
- `.ifeed_is_running` and `ifeed.log` confirm feeder-based execution patterns.

Avoid broad searches for the plain word `pool`; they produce many false positives unrelated to NetBatch.

## NEVER Rules

- NEVER use `nbtask delete` for normal cleanup. It destroys scheduler history and removes the evidence you need for later diagnosis; use `nbtask stop` instead.
- NEVER mix `--history` with `Status` or `TimeInRunning`. NetBatch returns error 246 there, so that query shape wastes time and hides the real signal.
- NEVER start with `--history` when the issue is an active wait or dispatch problem. History mode drops the live fields you need to explain why a job is stalled.
- NEVER cancel jobs before checking feeder state, qslot pressure, and `WaitReason`. Many "stuck" cases are just queue pressure or upstream dispatch lag, not broken jobs.
- NEVER treat a missing `.ifeed_is_running` file as automatic failure. The feeder may have exited normally, so confirm completion artifacts before declaring a crash.
- NEVER start repo discovery with a broad search for `pool`. It produces noisy false positives; start with `.nbclass`, `NBPOOL`, `NBQSLOT`, `Qslot`, and feeder artifacts.
- NEVER default to table output for scripted analysis. Prefer JSON so downstream filtering stays lossless and stable.
- NEVER classify `ExitStatus=-13` as definite out-of-memory from the status code alone. Confirm with memory usage, `KillReason`, or root-side evidence.
- NEVER treat `ExitStatus=-10` as the root cause. It only says the overall task failed.
- NEVER assume mass `NB_JOBEXITSTATUS=255` means scheduler instability first. Inspect generated input files and wrapper scripts before escalating to infrastructure.

## Do NOT Use For

- Do not use this skill to decide whether a failing test is functionally bad after the scheduler has already run it.
- Do not use this skill to compose or edit test sessions, groups, or testlists.
