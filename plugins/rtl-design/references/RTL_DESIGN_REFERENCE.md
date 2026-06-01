# RTL Design Agent Reference

## Delegation Map

- `rtl` -> SystemVerilog development conventions
- `cdc` -> VC_CDC CDC/RDC flow
- `lint` -> VC Lint and Open Latch
- `lp` -> VCLP low-power checks
- `sgdft` -> Spyglass DFT checks
- `vc-effm` -> VC-EFFM checks
- `assembly` -> RTL assembly/integration workflow

## Build/Run Standard

1. Check FE readiness first with `fe-setup/check_terminal_ready()`.
2. Use Build-Run plugin skills/tools for execution:
   - Gradle: `build-run/run_grdlbuild`
   - Make: `build-run/run_make`
3. Gather primary logs from `output/grdlbuild/logs/` and flow-specific output trees.

## Primary Log Roots

- grdlbuild summary: `output/grdlbuild/logs/grdlbuild_summary.log`
- task summary: `output/grdlbuild/logs/tasks_summary.log`
- per-task logs: `output/grdlbuild/logs/*.log`
