---
name: vamp-plan
description: Browse and update validation-plan hierarchy in vManager-style backends via cegMCP tools. Use for vPlan structure queries, mapping audits, coverage-gap identification, and scratch-plan mutations.
keywords: vmanager, vamp, vplan, validation plan, coverage gap, hierarchy, mapping, TC
---

# vManager Plan Skill

> PURPOSE: Navigate validation-plan hierarchies and audit mapping coverage via cegMCP plan tools. cegMCP now exposes both read and planning-write operations, including section, reference, metrics-port, and update endpoints.
> WHEN TO USE: Apply when users ask to find a plan, inspect section structure, read plan notes, audit mapped versus unmapped coverage, or perform controlled scratch-plan mutations.

## When To Use

Use this skill when the task is about:

- finding the right validation plan (`vamp_plan_list`, `vamp_plan_count`)
- exploring plan sections and leaves
- checking whether a feature is mapped or still uncovered
- reading plan notes or section descriptions
- creating scratch sections or references
- attaching scratch metrics ports
- updating plan, section, or reference metadata

Do not use this skill for run triage or testlist CRUD.

## Backend Check

- Confirm the active backend exposes planning APIs before assuming plan data is queryable.
- Verify whether rich text, hierarchy, and coverage status come from one endpoint or separate calls.
- For multi-step planning mutations, verify whether the backend uses sticky-session routing headers and a reusable routing OID.

## Core Routing

Capability groups exposed by cegMCP today:

- **Plan listing**: discover which plans exist (`vamp_plan_list`, `vamp_plan_count`); search by name fragment when the exact name is unknown (`vamp_plan_find`)
- **Hierarchy navigation**: inspect root sections, subsections, and leaves via filtered list queries (`vamp_plan_list`); list sub-elements directly via the planning endpoint (`vamp_plan_list_sub_elements`)
- **Coverage inspection**: check mapped vs. unmapped content against a session or run set (done via filtered `vamp_plan_list` queries using status and mapping fields; no discrete coverage tool exists in the current surface)
- **Rich text retrieval**: fetch section descriptions or notes via `vamp_plan_get_rich_text`; rich text is NOT returned in list responses — it requires a separate call with `sticky-context` and optionally `element-id`
- **Scratch writes**: create sections, references, and metrics ports via `vamp_plan_add_section`, `vamp_plan_add_reference`, and `vamp_plan_add_metrics_port`
- **Plan updates**: mutate plan, section, reference, or bulk plan content via `vamp_plan_update`, `vamp_plan_update_section`, `vamp_plan_update_reference`, and `vamp_plan_update_bulk`

## Live-Proven Planning BKMs

> Read and write BKMs below apply to the current cegMCP plan surface. The cegMCP tool layer forwards these payload shapes to the underlying planning endpoints.

- Planning list calls can explode into hundreds of fields per row. If the backend supports projection, use a slim selection and suppress null inflation.
- Some fields that seem obvious, such as `id`, are not always valid planning-list projection fields. Use known-safe fields first and expand only after validation.
- Structure-only planning work can still require `sticky-context` and `runs-rs`. A no-match filter such as `id == 0` is a safe default.
- The default response still exposes useful verification fields such as `name`, `full_path`, `vplan_element_kind`, and `sub_type_vmgr`.
- `add-section` uses `parent` and `sub-type`. It does not use `parentPath`, `parent-path`, or `parent_path`.
- `add-metrics-port` uses `parent` and `kind`, with `kind: COVERAGE` working for scratch coverage leaves.
- Safe scratch write flow is section first, then metrics port or reference under the created parent path.
- Re-list the modified subtree after every write and verify by `full_path` plus element kind.

## cegMCP Tool-Layer BKMs

> These practices are confirmed by direct tool invocation tests against dummy-backed plan MCP tool functions.

- **Tool-first always**: call `vamp_plan_list_vplans`, `vamp_plan_list`, `vamp_plan_get`, etc. via the registered MCP surface. Do not construct raw client calls when the tool is available.
- **`vamp_plan_list_vplans` accepts empty payload**: passing `{}` as `post_data_json` is valid and returns a `{"vplans": [...], "count": N}` wrapped object. Use this as the discovery starting point before narrowing to a specific plan.
- **Result shape for list-vplans**: `{"vplans": [{"id": ..., "name": ...}, ...], "count": N}`. Key on `"vplans"` for the entries and `"count"` for the total; do not expect a bare list.
- **JSON-string input**: all plan tools take `post_data_json: str`. Always pass a serialized JSON string, even if the payload is a near-empty `{}`.
- **Exact-ID follow-up for mutations**: after `vamp_plan_list_vplans` returns candidate plan IDs, use `vamp_plan_get` with a payload that includes `sticky-context` anchored to the recovered plan name before any write.
- **`vamp_plan_get` requires an exact existing vPlan name.** Guesses such as `memss`, `ljpll`, or `nvl` return `Failed finding vplan named ...`. Use `vamp_plan_find` with a name fragment when the full name is unknown. When plan-discovery tools are not exposed in the active deployment, source the exact vPlan name from external context — such as the project config, a known session name, or operator input — before invoking `vamp_plan_get` or any write that anchors to a plan. Planning bootstrap is weak without a concrete name.
- **Post-write re-list is mandatory**: `vamp_plan_add_section`, `vamp_plan_add_reference`, and `vamp_plan_add_metrics_port` may return a bare ID or minimal confirmation. Always re-list the subtree with `vamp_plan_list` and verify `full_path` and element kind before declaring success.
- **Rich text is a separate call**: `vamp_plan_get_rich_text` requires `post_data_json` with at least a `sticky-context` key; optionally include `element-id` and `rich-text-attribute-name`. Do not expect rich text fields in `vamp_plan_list` or `vamp_plan_list_sub_elements` responses.
- **Error prefix unchanged**: any bad-JSON input or backend failure returns an `ERROR: ...` string. Always inspect the result string before `json.loads()`.

## Query Routing

- If the user is browsing structure, start with hierarchy metadata only and avoid coverage-heavy queries.
- If the user is auditing gaps, query actionable leaves with mapping and status fields instead of container totals alone.
- If the user needs explanation or intent, fetch rich text only after isolating the relevant sections.

## Safe Scratch Flow

> This flow can be executed through cegMCP plan tools.

1. Confirm the target plan is explicitly disposable.
2. Build `sticky-context` with the plan name, backend flags such as `db-vplan`, and a no-match `runs-rs` filter.
3. Add the section node first with `vamp_plan_add_section`.
4. Re-list and recover the new `full_path`.
5. Add the metrics port or reference under that parent with `vamp_plan_add_metrics_port` or `vamp_plan_add_reference`.
6. Re-list the subtree and verify both nodes.

## Example Shapes

> These shapes are the JSON payloads to pass into the cegMCP plan-write tools.

Scratch TC create:

```json
{
  "name": "dummy_tc",
  "parent": "foo/tests/Directed Tests",
  "sub-type": "TC",
  "sticky-context": {
    "vplan": "f",
    "db-vplan": true,
    "runs-rs": {
      "filter": {
        "@c": ".AttValueFilter",
        "attName": "id",
        "attValue": 0,
        "operand": "EQUALS"
      }
    }
  }
}
```

Scratch coverage leaf create:

```json
{
  "name": "dummy_cov",
  "parent": "foo/tests/Directed Tests/dummy_tc",
  "kind": "COVERAGE",
  "sticky-context": {
    "vplan": "f",
    "db-vplan": true,
    "runs-rs": {
      "filter": {
        "@c": ".AttValueFilter",
        "attName": "id",
        "attValue": 0,
        "operand": "EQUALS"
      }
    }
  }
}
```

## Never Do This

- Do not assume the active deployment exposes planning tools just because the skill exists.
- Do not request full default entity payloads when the backend supports projection.
- Do not experiment on a production or ambiguous plan when a scratch plan exists.
- Do not use `add-section` with `parentPath`, `parent-path`, or `parent_path`; the live backend expects `parent`.
- Do not omit `runs-rs` from `sticky-context` when the backend requires it, even for structure-only work.
- Do not add a metrics port before confirming the parent section path exists.
- Do not guess or infer a vPlan name for `vamp_plan_get`; when discovery tools are absent from the deployment, source the exact name from external context before proceeding.

## Examples

### Nominal Case

User asks: "Add a disposable TC with a coverage child under the scratch plan."

- Confirm the scratch plan path.
- Create the TC with `add-section`.
- Re-list and recover the new `full_path`.
- Create the coverage child with `add-metrics-port`.
- Re-list and verify both nodes.

### Edge Case

User asks: "Why did the plan create fail when I used `parentPath`?"

- Switch to the live field names `parent` and `sub-type`.
- Retry only on a disposable plan.
- Verify by subtree re-list, not by assuming the returned name is enough.

## Do NOT Use For

- Do not use this skill for session, group, or test composition changes; use `vamp_composer`.
- Do not use this skill for run disposition or grouped-failure ownership updates; use `vamp_analysis`.
