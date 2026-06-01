---
name: vamp-composer
description: Manage VSIF sessions, groups, tests, and hierarchy configurations via cegMCP tools. Full CRUD and hierarchy-attach operations are now exposed; use this skill for both inspection and composition workflows.
keywords: vmanager, vamp, hierarchy, session inspection, session config, testlist, group, test, composition, attach, link, vsif
---

# vManager Composer Skill

> PURPOSE: Manage session configuration via cegMCP tools. cegMCP now exposes full CRUD for VSIF sessions, groups, tests, and hierarchy configurations, including attach operations.
> WHEN TO USE: Apply when users ask to inspect existing sessions, create or update sessions/groups/tests, or execute hierarchy-attach workflows.

## When To Use

Use this skill when the task is about:

- listing or inspecting session-level settings such as queue, timeout, notify, or run status (`vamp_sessions_list`, `vamp_sessions_count`)
- fetching, creating, or deleting VSIF sessions (`vamp_vsif_session_get`, `vamp_vsif_session_create`, `vamp_vsif_session_create_with_permissions`, `vamp_vsif_session_delete`)
- managing VSIF groups: get/list/create/update/delete (`vamp_vsif_group_get`, `vamp_vsif_groups_list`, `vamp_vsif_group_create`, `vamp_vsif_group_update`, `vamp_vsif_group_delete`); scoped list variants that filter by parent session or group are in Core Routing
- managing VSIF tests: get/list/create/update/delete (`vamp_vsif_test_get`, `vamp_vsif_tests_list`, `vamp_vsif_test_create`, `vamp_vsif_test_update`, `vamp_vsif_test_delete`); scoped list variants that filter by parent session or group are in Core Routing
- VSIF hierarchy configurations: get/list/create and attaching groups/tests to groups/sessions (`vamp_vsif_hierarchy_get`, `vamp_vsif_hierarchy_list`, `vamp_vsif_hierarchy_create`, `vamp_vsif_hierarchy_attach_*`)
- VSIF configuration inspection or update (`vamp_vsif_config_list`, `vamp_vsif_config_update`)

Do not use this skill for failure triage or coverage-plan navigation.

## Backend Check

- Confirm whether the backend exposes separate session, group, and test operations or only a subset.
- Verify whether create calls attach objects to the intended parent automatically or require a separate association step.
- **Shared database (TTL / RZL / NVL):** In this environment, TTL, RZL, and NVL repos all connect to the same `nvl` vManager database. There is no separate TTL or RZL vManager instance. Use the `nvl` database name in all vManager URLs and planning payloads regardless of which design family the workspace belongs to.

## Core Routing

Capability groups exposed by cegMCP today:

- **Session inventory**: list and count VSIF sessions via RS filter (`vamp_sessions_list`, `vamp_sessions_count`); fetch a single session by ID (`vamp_vsif_session_get`)
- **Session mutations**: create with or without permissions (`vamp_vsif_session_create`, `vamp_vsif_session_create_with_permissions`); delete by filter (`vamp_vsif_session_delete`)
- **Group operations**: fetch, list, list scoped to parent sessions or groups, create, update, and delete (`vamp_vsif_group_get`, `vamp_vsif_groups_list`, `vamp_vsif_groups_list_for_session`, `vamp_vsif_groups_list_for_group`, `vamp_vsif_group_create`, `vamp_vsif_group_update`, `vamp_vsif_group_delete`)
- **Test operations**: fetch, list, list scoped to parent sessions or groups, create, update, and delete (`vamp_vsif_test_get`, `vamp_vsif_tests_list`, `vamp_vsif_tests_list_for_session`, `vamp_vsif_tests_list_for_group`, `vamp_vsif_test_create`, `vamp_vsif_test_update`, `vamp_vsif_test_delete`)
- **Hierarchy configuration**: fetch, list, and create hierarchy-configuration objects; attach groups or tests to sessions or groups (`vamp_vsif_hierarchy_get`, `vamp_vsif_hierarchy_list`, `vamp_vsif_hierarchy_create`, `vamp_vsif_hierarchy_attach_groups_to_sessions`, `vamp_vsif_hierarchy_attach_groups_to_groups`, `vamp_vsif_hierarchy_attach_tests_to_sessions`, `vamp_vsif_hierarchy_attach_tests_to_groups`)
- **VSIF configuration**: list configurations by filter or name pattern; update attributes (`vamp_vsif_config_list`, `vamp_vsif_config_list_by_name`, `vamp_vsif_config_update`)
- **Convenience lookup**: fetch a runtime session by name for name-to-ID resolution (`vamp_session_get_by_name`); runtime session IDs are not VSIF session IDs — use `vamp_sessions_list` for all VSIF session operations

## Default Hierarchy Model

- Prefer `session -> groups -> tests` as the authored structure.
- Direct tests under a session can exist, but treat them as an explicit exception to verify, not the default composition pattern.
- For hierarchy audits, verify both groups under the session and tests under each group.

## Live-Proven VSIF BKMs

> These BKMs apply when working against the vManager backend. All operations listed are now callable via cegMCP tools.

- Session create requires `name`.
- Live session create may not return a useful count or ID. Re-list by exact name to recover the entity ID.
- **Runtime session IDs from `vamp_session_get_by_name` are not VSIF session IDs.** `mcp_ddgmcp_vamp_session_get_by_name` succeeds for runtime session names (e.g. `1w__nvl__nvl-a0__ljpll__iu.ljpll`) and returns numeric IDs, but those IDs belong to the runtime session namespace. Passing one directly to `vamp_vsif_session_get` returns `ID ... Not found for type P_SESSION`. To work with VSIF sessions, use `vamp_sessions_list` with a name filter to obtain a VSIF session ID before calling any VSIF session operation.
- Minimal disposable create payloads that worked live were `{"name": "..."}` for sessions, groups, and tests.
- Some backends create standalone groups and tests first, then require a separate attach step. Do not assume parent linkage is accepted during create.
- Relation traversal belongs in top-level relation fields such as `parentSessions` and `parentGroups`, using raw filter specs.
- Group and test attach calls require a real hierarchy-configuration object. Plain session IDs, group IDs, or configuration IDs are not interchangeable with a hierarchy-configuration ID.
- A minimal hierarchy-configuration create can be as small as `name` plus `configurationCondition: TRUE`.
- For grouped hierarchy validation, checking direct session tests is insufficient. Verify groups under the session and tests under each group.

## cegMCP Tool-Layer BKMs

> These practices are confirmed by direct tool invocation tests on the registered MCP tool surface.

- **Tool-first always**: invoke `vamp_vsif_groups_list`, `vamp_vsif_tests_list`, `vamp_sessions_list`, etc. directly via cegMCP. Never reach past the tool layer to the raw client unless the server is unavailable.
- **VSIF list tools return wrapped objects**: `vamp_vsif_groups_list` returns `{"vsif_groups": [...], "count": N}`; `vamp_vsif_tests_list` returns `{"vsif_tests": [...], "count": N}`. Key on `"vsif_groups"` or `"vsif_tests"` then index items.
- **Session-listing tools return wrapped objects**: `vamp_sessions_list` returns `{"sessions": [...], "count": N}`. Key on `"sessions"`, not positional index.
- **Hierarchy list also returns a wrapped object**: `vamp_vsif_hierarchy_list` returns `{"vsif_hierarchy": [...], "count": N}`.
- **Empty-filter always works**: passing `{}` as `post_data_json` is a valid list request for all VSIF list tools — confirmed by smoke tests. Use it to probe entity counts before applying filters.
- **Post-write verification is mandatory**: create and attach calls may not surface errors inline. Always re-list and confirm placement after any write. Use exact-ID `EQUALS` filters on `id` for targeted confirmation.
- **`vamp_vsif_config_list` returns a wrapped object**: the tool returns `{"vsif_configs": [...], "count": N}`. Key on `"vsif_configs"` then index items.
- **Error prefix unchanged**: all tools return `ERROR: ...` strings for invalid input or backend failures — check before parsing JSON.

## Safe Attach Flow

> This flow can be executed entirely via cegMCP tools.

1. Create or locate the session (`vamp_vsif_session_create` / `vamp_sessions_list`).
2. Create or locate the group (`vamp_vsif_group_create` / `vamp_vsif_groups_list`).
3. Create or locate the test (`vamp_vsif_test_create` / `vamp_vsif_tests_list`).
4. Create or locate the hierarchy configuration (`vamp_vsif_hierarchy_create` / `vamp_vsif_hierarchy_list`).
5. Attach groups to sessions (`vamp_vsif_hierarchy_attach_groups_to_sessions`).
6. Attach tests to groups (`vamp_vsif_hierarchy_attach_tests_to_groups`).
7. Re-list the hierarchy and confirm placement (`vamp_vsif_hierarchy_list`).

## Example Shapes

Minimal hierarchy-configuration create (pass as `post_data_json` to `vamp_vsif_hierarchy_create`):

```json
{
  "name": "dummy_hierarchy_config",
  "configurationCondition": "TRUE"
}
```

Attach group to session:

```json
{
  "hierarchyConfiguration": 12345,
  "groups": {
    "@c": ".AttValueFilter",
    "attName": "id",
    "attValue": 2001,
    "operand": "EQUALS"
  },
  "sessions": {
    "@c": ".AttValueFilter",
    "attName": "id",
    "attValue": 1001,
    "operand": "EQUALS"
  }
}
```

Attach test to group:

```json
{
  "hierarchyConfiguration": 12345,
  "tests": {
    "@c": ".AttValueFilter",
    "attName": "id",
    "attValue": 3001,
    "operand": "EQUALS"
  },
  "groups": {
    "@c": ".AttValueFilter",
    "attName": "id",
    "attValue": 2001,
    "operand": "EQUALS"
  }
}
```

## Practical Inspection and Update Flow

1. List sessions via `vamp_sessions_list` to find the target entity.
2. Confirm whether the user needs read-only inspection or a hierarchy edit.
3. For read queries, use `vamp_sessions_count` or `vamp_sessions_list` with targeted RS filters.
4. For write operations, use the appropriate create/update/attach/delete tools from the Core Routing capability groups above.
5. After any write, re-list and confirm hierarchy placement and status.

## Never Do This

- Do not assume create APIs automatically attach new entities to the intended parent.
- Do not assume a plain session, group, or configuration ID can be used anywhere a hierarchy-configuration ID is required.
- Do not pass a runtime session ID (from `vamp_session_get_by_name`) directly to `vamp_vsif_session_get`; the runtime and VSIF ID namespaces are not interchangeable.
- Do not verify hierarchy edits by checking only direct session tests.
- Do not delete groups or tests for short-lived bring-down requests when an off-state preserves history.
- Do not carry repo-specific naming patterns or hierarchy conventions into another CEG domain without verification.

## Examples

### Nominal Case

User asks: "Create a dummy session, group, and test, then wire them together."

- Create the three standalone entities.
- Create a disposable hierarchy configuration.
- Attach group to session, then test to group.
- Verify with relation traversal.

### Edge Case

User asks: "The attach call rejected my config ID."

- Check whether the API expects a hierarchy-configuration ID instead of a plain configuration ID.
- Create or look up the correct hierarchy object.
- Retry and re-list the hierarchy.

## Do NOT Use For

- Do not use this skill for failed-run or grouped-failure triage; use `vamp_analysis`.
- Do not use this skill for plan hierarchy or coverage-gap inspection; use `vamp_plan`.
