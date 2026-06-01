# VAMP Fold-In Plan

## Goal

Fold `/home/ubuntu/Github/applications.services.design-system.vamp-mcp-server.repo` into `/home/ubuntu/Github/rtls.ai.copilot.ceg-copilot-instructions/plugins/validation/mcp-server` without losing validation MCP breadth, while importing the standalone server's cleaner runtime architecture, safer pagination, explicit settings/auth handling, and benchmark discipline.

The target must be:

- robust and reliable
- maintainable and easy to evolve
- DRY and cleanly layered
- neutral or favorable in token usage, caching behavior, latency, and cost
- neutral or favorable in complexity relative to the benefit

## What Exists Today

### Standalone VAMP MCP server

Strengths:

- packaged cleanly as a Python module
- clear entrypoint and server factory
- explicit settings and auth resolution
- centralized error formatting
- centralized pagination policy
- centralized list-result shaping
- typed request models for read-oriented tools
- benchmark harness that measures payload size, token footprint, and latency

Primary surface:

- runs: `runs_get`, `runs_count`, `runs_list`
- failure clusters: `failure_clusters_get`, `failure_clusters_count`, `failure_clusters_list`
- planning: `planning_list_vplans`, `planning_list_sub_elements`, `planning_get_rich_text`
- sessions: `sessions_list`
- VSIF: `vsif_groups_list`, `vsif_tests_list`

### Validation MCP server

Strengths:

- much broader vManager feature surface
- already owns the plugin entrypoint and deployment path
- has useful slim projections for AI-sized responses
- includes domain-specific helpers such as standard runs queries, grouped failure-cluster views, VSIF CRUD, plan mutation tools, and register-topology tooling

Current weaknesses:

- repeated wrapper logic across many tool files
- per-tool `json.loads` and `json.dumps(indent=2, sort_keys=True)` boilerplate
- per-tool `VmanagerClient(...)` construction
- error handling encoded as ad hoc `"ERROR: ..."` strings
- no centralized pagination/cost guardrails
- no explicit shared settings/auth module
- no benchmark/perf regression harness
- flat repo-local import patterns with test-only import fallbacks

## Strategy Decision

Use the validation MCP server as the destination codebase.

Keep these validation pieces as the long-term source of truth:

- the broader vManager backend surface in `backends/vmanager/client.py`
- the domain mixin in `backends/vmanager/_client_domain.py`
- the standard-runs helper in `standard_runs_query.py`
- the register-topology module as a separate concern

Port these standalone VAMP ideas into validation instead of copying the whole standalone repo:

- settings/auth resolution
- server factory
- shared runtime wrapper for tool execution
- pagination policy
- output shaping
- query adapter patterns
- benchmark harness
- typed request validation where it reduces boilerplate enough to justify itself

Do not merge by vendoring the standalone package into the validation repo.

Do not keep two independent VAMP client stacks long term.

Do not expose duplicate tool-name aliases by default inside the validation plugin, because that increases tool-list size, selection ambiguity, and token cost. If compatibility with the standalone tool names is required, implement it as an opt-in registration profile or separate compatibility entrypoint, not the default validation profile.

## Capability Mapping

Use one implementation surface in validation with these outcomes:

| Standalone VAMP capability | Validation status | Destination approach |
| --- | --- | --- |
| `runs_get`, `runs_count`, `runs_list` | already present as `vamp_run_get`, `vamp_runs_count`, `vamp_runs_list` | keep validation names as canonical, port read-runtime helpers underneath |
| `failure_clusters_get`, `failure_clusters_count`, `failure_clusters_list` | already present as `vamp_failure_cluster_get`, `vamp_failure_cluster_count`, `vamp_failure_cluster_list` | same as above |
| `planning_list_vplans`, `planning_list_sub_elements`, `planning_get_rich_text` | already present as `vamp_plan_list_vplans`, `vamp_plan_list_sub_elements`, `vamp_plan_get_rich_text` | same as above |
| `vsif_groups_list`, `vsif_tests_list` | already present as `vamp_vsif_groups_list`, `vamp_vsif_tests_list` | same as above |
| `sessions_list` | only partial overlap; validation separates runtime session lookup from VSIF session list/count | keep semantics distinct; do not force a false merge |
| typed request models | missing | add only for read-heavy tools and compatibility surfaces |
| pagination guardrails | missing | port and enforce centrally |
| structured list envelope | missing | use internally first, then decide exposure contract deliberately |
| benchmark CLI / perf checks | missing | port as internal validation tooling |

Unique validation-only surface to preserve during the fold-in:

- standard runs query builder and helper tool
- run mutation tools
- run log extraction
- run-failure-cluster association and grouped summaries
- failure-cluster create/update/delete
- VSIF config, group, test, hierarchy, and session CRUD
- plan mutation tools
- register-topology tools

## Concrete Duplicated Logic To Remove

The highest-value DRY target is the repeated tool wrapper pattern across `vmanager/_*.py`:

- parse JSON input
- instantiate `VmanagerClient`
- call one backend method in `asyncio.to_thread`
- catch backend errors and stringify them
- pretty-print the result with `json.dumps(..., indent=2, sort_keys=True)`

That pattern should be replaced by shared runtime helpers so each tool file only declares:

- request schema or parser
- backend method binding
- result shaping policy
- tool metadata and docstring

Other duplicated or fragmented behavior to centralize:

- auth/env resolution
- default page length and max page length policy
- `fetch_all` policy
- log formatting
- error formatting
- client creation and optional caching
- common list/count/get registration for read-only families

## Recommended Target Architecture

Create a real package boundary inside `plugins/validation/mcp-server` and migrate toward this shape:

```text
plugins/validation/mcp-server/
├── validation_mcp/
│   ├── __init__.py
│   ├── server.py
│   ├── settings.py
│   ├── errors.py
│   ├── benchmarks.py
│   ├── runtime/
│   │   ├── client_factory.py
│   │   ├── tool_runtime.py
│   │   ├── pagination.py
│   │   ├── output.py
│   │   └── query_adapter.py
│   ├── backends/
│   │   └── vmanager/
│   │       ├── client.py
│   │       ├── _client_domain.py
│   │       └── _utils.py
│   ├── tools/
│   │   ├── runs.py
│   │   ├── failure_clusters.py
│   │   ├── plans.py
│   │   ├── sessions.py
│   │   ├── vsif.py
│   │   ├── mutations.py
│   │   └── profiles/
│   │       ├── validation_profile.py
│   │       └── vamp_compat_profile.py
│   └── register_topology.py
├── server_validation.py
├── standard_runs_query.py
├── tests/
└── reference/
    └── vamp_plan.md
```

Notes:

- `server_validation.py` should become a thin shim to `validation_mcp.server.main` so the existing plugin entrypoint remains stable.
- `register_topology.py` should move under the package or import through the package, but remain isolated from vManager runtime concerns.
- `standard_runs_query.py` can remain top-level initially to reduce churn, then move under the package once import paths are stabilized.
- Do not introduce the standalone repo's `fastmcp` dependency if `mcp.server.fastmcp` already satisfies runtime needs. Port the pattern, not the second MCP runtime.

## Dependency and Packaging Plan

### Python and dependency policy

Keep validation's current Python baseline unless there is a hard blocker.

Preferred dependency plan:

- keep `mcp[cli]`
- add `vmanager-vamp` explicitly to `plugins/validation/mcp-server/pyproject.toml`
- add explicit `tool.uv.sources` for Intel devpi, matching the standalone repo's dependency resolution model
- add `tool.uv.system-certs = true`
- only add `pydantic>=2.x` if typed request models provide enough schema clarity and MCP tool ergonomics to justify the dependency

If the team wants to avoid `pydantic`, use frozen dataclasses and explicit validators for the initial fold-in. The important part is centralized validation, not the exact library.

### Auth and environment policy

Move auth resolution into one settings module.

The settings layer should own:

- `VAPI_BASE_PATH`
- `VMGR_USER` with a cross-platform current-user fallback
- `VAPI_PASSWORD`
- `VMGR_TOKEN_PATH`
- `VAPI_VERIFY`
- default and max page length
- debug-error mode
- optional client-caching mode
- log level
- transport mode if needed later

Also update plugin runtime configuration so private-index resolution is reliable:

- keep existing proxy env vars in `.mcp.json`
- add `UV_SYSTEM_CERTS=1` if needed in this environment
- document the auth env contract in validation MCP docs, because it is currently implicit

## Client and Caching Strategy

Introduce a shared `client_factory` in validation.

Recommended behavior:

- default to a bounded cache keyed by effective settings, not a single global mutable singleton
- keep the cache small, for example `maxsize=4`, so distinct auth contexts do not explode memory
- construct the backend client in one place only
- make cache use configurable so debugging can force per-call construction

Reliability gate:

- before enabling client reuse by default, run a focused concurrency test to confirm the underlying `Vamp` object is safe to share across concurrent tool calls
- if the `Vamp` object is not thread-safe, cache only immutable auth/config resolution and create a new lightweight client wrapper per call

This avoids a blind latency optimization that could become a correctness bug.

## Output Strategy

Do not change the validation server's external output contract casually.

Recommended sequence:

1. Adopt structured Python dict/list responses internally.
2. Use shared output-shaping helpers for list-style tools.
3. Preserve current field names for validation tools.
4. Keep the existing outer contract for legacy tools until consumers are audited.
5. Only then decide whether to stop returning pretty-printed JSON strings from the default profile.

Important cost guidance:

- `json.dumps(..., indent=2, sort_keys=True)` should not remain the long-term default for MCP tool responses; it adds bytes and tokens without user value
- structured list envelopes or compact JSON are preferable
- if legacy string output must remain temporarily, benchmark it against the new structured path and deprecate it explicitly

## Pagination and Token/Latency Guardrails

The fold-in should import the standalone server's safety posture directly.

Required guardrails:

- central default page length, not per-tool ad hoc paging
- central maximum page length hard cap
- `fetch_all` unsupported until multi-page aggregation is implemented deliberately
- list responses should carry enough paging metadata to continue safely
- slim projections stay enabled by default for runs, failure clusters, plan sub-elements, VSIF lists, and sessions
- broad list tools should encourage count-first or filtered queries first
- optional `include_count` behavior should be explicit and measurable

Acceptance target:

- token footprint is neutral or lower for common read tools relative to today's validation MCP output
- p95 latency is neutral or better for common read tools relative to today's validation MCP output

## Tool Registration Strategy

### Default validation profile

Keep the current validation tool names as canonical in the plugin:

- `vamp_*`
- `crifd_query`

This avoids unnecessary tool-surface expansion.

### Optional standalone compatibility profile

If external users still need the standalone tool names, expose them only through:

- a separate registration profile, or
- a separate entrypoint/script

Do not register both `runs_list` and `vamp_runs_list` by default in the plugin process unless usage data proves the duplication is worth the cost.

## Implementation Phases

### Phase 0: Baseline and decision gates

Work:

- inventory the exact overlapping tools and unique validation-only tools
- capture current validation behavior for representative read tools
- capture current payload size and latency baselines for representative validation outputs
- decide whether request validation will use `pydantic` or lightweight internal validators
- decide whether client reuse is safe after a concurrency check

Representative baseline tools:

- `vamp_runs_list`
- `vamp_runs_count`
- `vamp_run_get`
- `vamp_failure_cluster_list`
- `vamp_plan_list_sub_elements`
- `vamp_plan_list_vplans`
- `vamp_vsif_groups_list`
- `vamp_vsif_tests_list`

Exit criteria:

- documented current output examples
- documented payload and latency baseline
- explicit decision on request-validation library
- explicit decision on safe client caching mode

### Phase 1: Package the validation MCP server cleanly

Work:

- create `validation_mcp/` package
- move server entrypoint logic into `validation_mcp.server`
- make `server_validation.py` a thin compatibility shim
- remove repo-root import fallbacks where possible
- keep tests green during each move

Exit criteria:

- existing plugin entrypoint still works
- imports no longer depend on being executed from a special cwd
- tests continue to run from repo root

### Phase 2: Introduce shared settings and client factory

Work:

- add `validation_mcp.settings`
- add `validation_mcp.runtime.client_factory`
- make backend construction flow through one place
- update `pyproject.toml` with explicit `vmanager-vamp` and Intel devpi source config
- update `.mcp.json` and docs if runtime env additions are required

Exit criteria:

- one authoritative auth/config path exists
- no tool instantiates `VmanagerClient` directly
- dependency resolution is explicit and reproducible

### Phase 3: Port shared runtime helpers

Work:

- add centralized `errors.py`
- add centralized `tool_runtime.py`
- add centralized `pagination.py`
- add centralized `output.py`
- add centralized `query_adapter.py`
- keep existing `standard_runs_query.py` logic as the standard-query domain helper

Exit criteria:

- read-only tool wrappers stop duplicating parse/call/error/log logic
- page caps and fetch-all policy are enforced centrally
- list-style tools can share one shaping path

### Phase 4: Migrate overlapping read-only VAMP tools first

Work:

- refactor runs read tools onto the shared runtime
- refactor failure-cluster read tools onto the shared runtime
- refactor planning read tools onto the shared runtime
- refactor VSIF list tools onto the shared runtime
- keep current validation names and semantics intact
- optionally expose the standalone names in a non-default compatibility profile

This phase should deliver the most benefit with the least risk, because it targets the largest architectural overlap between the two repos.

Exit criteria:

- overlapping read tools share the new runtime path
- behavior remains backward compatible for the validation profile
- output, pagination, and error semantics are tested centrally

### Phase 5: Migrate validation-only mutation and helper tools

Work:

- refactor run mutation tools
- refactor failure-cluster mutation tools
- refactor VSIF CRUD and hierarchy tools
- refactor plan mutation tools
- refactor grouped association helpers
- preserve domain-specific result shapes where they help users

Exit criteria:

- mutation tools share the same client factory and error/log policy
- only domain-specific behavior remains in tool modules
- no repeated wrapper boilerplate remains across `vmanager/_*.py`

### Phase 6: Add benchmarks and regression gates

Work:

- port the benchmark harness concepts from the standalone repo
- measure structured output vs current pretty-printed strings
- add perf regression checks for representative list tools
- store benchmark reports only if they are useful for team review; do not add needless surface area

Exit criteria:

- token and payload measurements exist for key list tools
- p95 latency and payload-size regressions have a visible gate
- any output-contract change is backed by measurements

### Phase 7: Cleanup and compatibility decisions

Work:

- remove dead wrapper paths
- remove duplicated helper logic
- decide whether the standalone repo remains as a thin compatibility wrapper, a docs-only stub, or is retired fully
- if needed, provide a separate compatibility entrypoint that registers standalone names without inflating the default plugin tool surface

Exit criteria:

- one maintained implementation exists
- no duplicate runtime layers remain
- compatibility policy is explicit and documented

## Testing and Validation Plan

At minimum, expand validation MCP tests to include:

- server registration tests for the default validation profile
- optional compatibility-profile registration tests if aliases are added
- settings/auth resolution tests
- pagination policy tests
- list-envelope shaping tests
- benchmark helper tests
- backend-unavailable tests
- concurrency/caching safety tests for the client factory
- representative read-tool tests for runs, failure clusters, planning, VSIF groups, and VSIF tests
- representative mutation-tool tests to ensure refactors do not change semantics accidentally

Recommended command set during implementation:

```bash
UV=<path-to-uv>
$UV run pytest plugins/validation/mcp-server/tests -v
$UV run pytest <path-to-standalone-vamp-repo>/tests -v
$UV run python -m compileall plugins/validation/mcp-server
```

If linting is configured for this tree, add a focused lint/type pass for the touched package as part of each phase.

## Key Risks and Mitigations

1. Tool-name duplication can increase tool-selection cost and confuse agents.
Mitigation: keep validation names canonical and make standalone aliases opt-in only.

2. Blind client caching can introduce concurrency bugs.
Mitigation: gate cache enablement behind a thread-safety check and config flag.

3. Output-contract changes can break existing consumers.
Mitigation: move internal shaping first, then change outward contracts deliberately and with tests.

4. Validation currently relies on implicit environment/auth behavior.
Mitigation: centralize and document auth/env handling before broad refactors.

5. Adding a second MCP runtime library would create needless complexity.
Mitigation: port the architecture patterns, not the standalone runtime dependency.

6. Broad list tools can regress token usage quickly.
Mitigation: keep slim projections, cap page sizes centrally, and benchmark payload size.

7. Packaging refactors can break current plugin launch commands.
Mitigation: keep `server_validation.py` as a shim until the new package path is stable.

8. Session semantics are not identical between the two repos.
Mitigation: keep runtime sessions and VSIF sessions as separate capability families.

9. The validation repo may still contain import-fallback patterns after partial refactors.
Mitigation: remove them phase by phase behind passing tests rather than in one large rewrite.

10. Over-scoping the migration will delay value.
Mitigation: deliver read-only overlap first, then mutation tools, then cleanup.

## Recommended End State

The final implementation should look like this in practice:

- one maintained validation MCP codebase
- one vManager backend client stack
- one shared settings/auth path
- one shared client factory
- one shared error/logging path
- one shared pagination policy
- one shared list-output shaping policy
- read-only and mutation tools split cleanly by responsibility
- register-topology kept separate from VAMP/vManager runtime logic
- benchmark and payload checks available to prevent token/latency regressions
- optional standalone-name compatibility handled without inflating the default plugin tool list

## Explicit Non-Goals

Avoid these unless a later requirement proves they are necessary:

- running two independent VAMP backends in the same codebase long term
- copying the standalone repo wholesale into the validation plugin
- enabling duplicate tool aliases by default
- changing every tool output contract in one step
- adding streamable HTTP transport immediately if the validation plugin only needs stdio
- adding new abstraction layers that do not remove real duplication

## Most Important Implementation Principle

Use the validation MCP server's backend breadth as the foundation, and use the standalone VAMP MCP server's runtime architecture as the refactor template.

That yields the smallest-risk path that is still a real architectural improvement:

- no duplicated client stacks
- no unnecessary feature loss
- no avoidable tool-surface expansion
- a measurable path to lower token cost and better latency discipline
- a codebase that is substantially easier to maintain and evolve
