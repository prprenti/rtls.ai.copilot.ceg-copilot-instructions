# VC-EFFM Reference

## Scope

- VC-EFFM input structure
- Results/output tree interpretation
- Error and waiver file locations

## Build/Run Hook

- Confirm FE readiness before launching EFFM flow.
- Use MCP Build-Run tools:
  - `build-run/run_grdlbuild` for Gradle task execution
  - `build-run/run_make` for make-based debug targets

## Output and Primary Logs

- Main output root is typically `output/<dut>/vc_effm/` (repo-specific naming may vary).
- Primary logs:
  - `output/grdlbuild/logs/grdlbuild_summary.log`
  - `output/grdlbuild/logs/tasks_summary.log`
  - flow session logs under the EFFM run directory

## Input/Config Pointers

- `static/vc_effm/` or repo-equivalent static directory
- flow config and waiver files in that static tree
- `flows/grdlbuild/<dut>/static/` task definitions

## Troubleshooting

- Start with per-task grdlbuild logs to find first failing stage.
- Correlate with EFFM session log and waiver report in run output.
