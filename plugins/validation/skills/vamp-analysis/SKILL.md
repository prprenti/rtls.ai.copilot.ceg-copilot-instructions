---
name: vamp-analysis
description: Inspect failed runs and failure clusters in vManager-style backends via cegMCP read tools. Use to review run status, examine failure clusters, and diagnose regression results.
keywords: vmanager, vamp, failure inspection, run listing, failure cluster, regression analysis
---

# vManager Failure Analysis Skill

> PURPOSE: Inspect failed runs and grouped-failure objects via cegMCP tools. Write operations — updating run attributes, failure cluster ownership, notes, and status — are now also exposed by cegMCP.
> WHEN TO USE: Apply when users ask to list failed runs, inspect individual run details, or examine grouped-failure records after regressions complete.

## When To Use

Use this skill when the task is about:

- listing failed or stopped runs
- fetching a single run's failure text and current state
- reviewing grouped failures and bucket context
- identifying unowned or untriaged runs before deciding on debug action

Do not use this skill for testlist composition changes or vPlan hierarchy audits.

## First Decision

Before editing anything, answer these two questions:

- Is the user acting on a specific failed run or on a reusable grouped-failure record?
- In this deployment, which object actually owns debugger, owner, notes, and status?

If that is unclear, inspect first and defer edits.

## Backend Check

- Confirm the active backend actually exposes run and failure-group operations before assuming anything is writable.
- If both run-level and group-level updates exist, verify which object owns debugger, owner, notes, and status in that deployment.

## Core Routing

Capability groups exposed by cegMCP today:

- **Run inventory**: list failed or stopped runs, optionally filtered by debug state (`vamp_standard_runs_list`, `vamp_runs_list`, `vamp_runs_count`); retrieve global run count and storage size (`vamp_run_total_count_size_get`); list available rerun schemes (`vamp_run_rerun_schemes_get`)
- **Run detail**: fetch a single run and inspect failure text, assignment, and notes (`vamp_run_get`); extract a slice of run logs (`vamp_run_extract_logs`)
- **Run mutations**: update run attributes such as debug status and debugger assignment (`vamp_run_update`); associate or dissociate runs from failure clusters (`vamp_run_associate_to_failure_cluster`, `vamp_run_dissociate_from_failure_cluster`)
- **Failure-group inspection**: list and fetch grouped-failure records (`vamp_failure_cluster_list`, `vamp_failure_cluster_count`, `vamp_failure_cluster_get`); look up clusters associated with specific run IDs (`vamp_failure_clusters_for_runs`)
- **Failure-group mutations**: update cluster notes, owner, and status (`vamp_failure_cluster_update`); create or delete clusters (`vamp_failure_cluster_create`, `vamp_failure_cluster_delete`)
- **Run↔cluster associations**: list and update run-to-cluster associations (`vamp_run_failure_cluster_list`, `vamp_run_failure_cluster_list_grouped`, `vamp_run_failure_cluster_update_association`).  For cluster-centric triage prefer `vamp_run_failure_cluster_list_grouped`: it collapses the flat per-run rows into one summary entry per distinct bucket with a nested `"runs"` list, substantially reducing token load.  Use `full_detail=true` to include Tag, HSDES_IDS, and Notes per cluster.
- **Convenience run-failure queries**: list failed runs scoped by team, time window, rerun status, or result IDs (`vamp_run_failures_for_team`, `vamp_run_failures_in_datetime`, `vamp_run_failures_needs_rerun`, `vamp_run_failures_for_result_ids`)

## Live-Proven BKMs

- Treat triage as a run-first workflow. Cluster ownership is often stewardship, not the per-run engineer assignment.
- Use `@c` as the filter-type discriminator in all RS filter payloads; do not use `c_type`. If you switch to the raw `vamp` library instead of cegMCP tooling, regenerate filters with the library helpers rather than copying cegMCP JSON.
- TTL, RZL, and NVL all use the shared `nvl` vManager database/instance in this environment. Do not treat TTL or RZL as needing their own `VAPI_BASE_PATH` override just because they are not named NVL. Only set `VAPI_BASE_PATH` in the cegMCP server environment when the project is known to use a different backend than the shared `nvl` instance (for example, MTL); otherwise queries may return silently empty or wrong-scope data.
- Placeholder owners such as service accounts or automation identities should not be treated as human ownership.
- Prefer exact-ID queries after a list step to narrow results before deeper inspection.

## cegMCP Tool-Layer BKMs

> These practices are confirmed by direct tool invocation tests against dummy-backed MCP tool functions.

- **Tool-first always**: reach for `vamp_runs_list`, `vamp_failure_cluster_list`, etc. directly — never bypass the cegMCP layer to call raw client methods unless the MCP server is unavailable.
- **Minimal RS filter payload**: the tool layer accepts any valid dict for `post_data_json`; an empty filter `{"filter": {}}` exercises the full round-trip from JSON parsing through client dispatch. Do not send null or omit the key.
- **JSON-string input, not dict**: every RS-filter tool takes `post_data_json: str`, not a Python dict. Always `json.dumps(...)` before passing.
- **Exact-ID follow-up pattern**: after a list call returns candidate IDs, anchor the next call to a single ID via an `EQUALS` filter on `id`. This avoids pagination drift and accidental multi-match mutations.
- **Result shape**: `vamp_runs_list` returns `{"runs": [...], "count": N}`. `vamp_failure_cluster_list` returns `{"failure_clusters": [...], "count": N}`. `vamp_run_failure_cluster_list` returns `{"run_failure_clusters": [...], "count": N}`. The `vamp_run_failures_*` convenience tools (`vamp_run_failures_for_team`, `vamp_run_failures_in_datetime`, `vamp_run_failures_needs_rerun`, `vamp_run_failures_for_result_ids`) also return run↔cluster failure records in the same `{"run_failure_clusters": [...], "count": N}` wrapped shape as `vamp_run_failure_cluster_list`. Always key on these top-level names, not positional index.
- **Error prefix**: any tool error (bad JSON, backend unavailable, validation failure) comes back as a plain string starting with `ERROR:`. Check for this before `json.loads()`.
- **Runtime session lookup**: `vamp_session_get_by_name` returns `{}` for a session that does not exist — not an error string. Treat an empty-dict result as "not found" rather than a failure.

## Practical Triage Flow

1. Query failed or stopped runs via `vamp_standard_runs_list` (team/stepping) or `vamp_runs_list` (custom RS filter).
2. Remove obviously known infra or already-owned items from the candidate set.
3. For cluster-centric triage, call `vamp_run_failure_cluster_list_grouped` with the same RS filter to get one entry per distinct failure bucket with a nested `"runs"` list.  This is the **preferred path** when the goal is understanding which runs failed in which cluster bucket.  Use `full_detail=true` to include Tag, HSDES_IDS, and Notes.
4. For targeted single-run inspection, use `vamp_run_get` to inspect failure text and current state.
5. Use `vamp_failure_cluster_list` or `vamp_failure_cluster_get` to check grouped-failure context when the cluster ID is already known.
6. Update ownership, debug status, or notes via `vamp_run_update` or `vamp_failure_cluster_update` as appropriate.

## Example Shapes

Retrieval-spec filter:

```json
{"@c": ".AttValueFilter", "attName": "id", "attValue": 12345, "operand": "EQUALS"}
```

## Never Do This

- Do not change group-level owner fields when the real intent is to assign a run debugger.
- Do not continue triage based on guessed operations if the deployment does not expose vManager support.
- Do not import repo-specific owner names, bucket taxonomies, or status conventions into another CEG domain.

## Examples

### Nominal Case

User asks: "Show me the failed runs that still need ownership."

- Query failed or stopped runs via `vamp_standard_runs_list` or `vamp_runs_list`.
- Filter out already-owned or infra-flagged runs.
- Use `vamp_run_get` to inspect the top candidates.
- Report findings; update ownership or debug status via `vamp_run_update` or `vamp_failure_cluster_update`.

### Edge Case

User asks: "I need to assign this run and update the bucket notes."

- Read current run state with `vamp_run_get` and cluster context with `vamp_failure_cluster_get`.
- Report current state and ownership clearly.
- Update run attributes via `vamp_run_update`; update cluster notes or owner via `vamp_failure_cluster_update`.

## Do NOT Use For

- Do not use this skill to edit sessions, groups, or tests; use `vamp_composer`.
- Do not use this skill to inspect validation-plan structure or mapping coverage; use `vamp_plan`.
