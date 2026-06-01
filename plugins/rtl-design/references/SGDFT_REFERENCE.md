# SGDFT Reference

## Flow Stages

1. Compile stage
2. Partition runs
3. Optional indicators aggregation

## Build-Run Usage

- Discover and run SGDFT tasks using MCP `build-run/run_grdlbuild`.
- For direct debug/GUI flows, use MCP `build-run/run_make` in `static/sgdft`.

## Output and Primary Logs

- Main output root: `output/<dut>/sgdft/`
- Compile summary: `output/<dut>/sgdft/sgdft_compile/compile.summary.rpt`
- Partition summary: `output/<dut>/sgdft/<partition>/sgdft_run/INTELREPORT/<partition>_SIP_RTL_1.0/summary.rpt`
- Main partition log: `output/<dut>/sgdft/<partition>/sgdft_run/INTELREPORT/<partition>_SIP_RTL_1.0/spyglass.log`
- Indicators report: `output/<dut>/sgdft/indicators/violations_report.csv`
- grdlbuild summary log: `output/grdlbuild/logs/grdlbuild_summary.log`

## Related Inputs

- `static/sgdft/flow.cfg`
- `static/sgdft/inputs/`
- `flows/grdlbuild/<dut>/static/sgdft/`
