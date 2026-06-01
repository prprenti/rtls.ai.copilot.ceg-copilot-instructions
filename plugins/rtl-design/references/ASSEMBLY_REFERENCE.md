# RTL Assembly Reference

## Scope

- Partition and top-level connectivity updates
- Codegen/integration touchpoints
- Common integration issues and handoff checks

## Build/Run Hook

- Confirm FE readiness before running integration targets.
- Use MCP `build-run/run_make` for assembly/integration make targets.

## Output and Primary Logs

- Primary output path is repo-specific (commonly under `output/<dut>/...`).
- Primary execution logs include:
  - `output/grdlbuild/logs/grdlbuild_summary.log` (if grdlbuild-driven dependencies ran)
  - target-specific make logs in the invoked static/flow directory

## Notes

- If a repo has a dedicated assembly/static directory, run targets there via `run_make`.
- Keep connectivity edits aligned with existing partition interface patterns.
