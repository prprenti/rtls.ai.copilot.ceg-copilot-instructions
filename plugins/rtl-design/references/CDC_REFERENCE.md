# CDC / RDC Reference

## FE Readiness (Required First)

Run:

```text
fe-setup/check_terminal_ready()
```

Proceed only when readiness returns `true`.

## Flow Stages

1. Compile stage (shared by CDC and RDC)
2. Block-level CDC tests (SAM generation)
3. Full-chip CDC test
4. Optional SVA setup and post-processing

## Build-Run Usage

- Discover tasks through the Build-Run grdlbuild skill/task-discovery flow.
- Run tasks through MCP tool `build-run/run_grdlbuild`.
- For direct debugging targets, run make through `build-run/run_make` in `static/vc_cdc`.

## Flow and Output Structure

- Main output root: `output/<dut>/vc_cdc/`
- Compile stage root: `output/<dut>/vc_cdc/vc_cdc_compile/`
- Block-level run root: `output/<dut>/vc_cdc/<block>/vc_cdc_run/cdc/`
- Top-level run root: `output/<dut>/vc_cdc/<dut>/vc_cdc_run/cdc/`
- Reports root: `output/<dut>/vc_cdc/<dut>/vc_cdc_run/cdc/reports/`

## Output and Primary Logs

- Main output root: `output/<dut>/vc_cdc/`
- Compile summary: `output/<dut>/vc_cdc/vc_cdc_compile/vc_cdc_compile.summary.rpt`
- Main run summary: `output/<dut>/vc_cdc/<dut>/vc_cdc_run/cdc/vc_cdc_run.summary.rpt`
- Main session log: `output/<dut>/vc_cdc/<dut>/vc_cdc_run/cdc/vcst_session.log`
- Violation summary: `output/<dut>/vc_cdc/<dut>/vc_cdc_run/cdc/reports/violations_summary.rpt.gz`
- grdlbuild summary log: `output/grdlbuild/logs/grdlbuild_summary.log`

## Finding Violations

- Primary summary: `reports/violations_summary.rpt.gz`
- Detailed CDC report: `reports/cdc_detailed_report.rpt.gz`
- RDC-specific corruption report: `reports/RDC_CORRUPT_OBSERVED.csv.gz`
- Full run context: `vcst_session.log`

Common categories to check in summary reports:
- `CORRUPTION / RESET`
- `SETUP / CLKPROP`
- `SETUP_HIER / HIERCDC`
- `SYNC / UNSYNC`

## Pass/Fail Indicators

- Compile pass sentinel: `output/<dut>/vc_cdc/vc_cdc_compile/vc_cdc_compile.PASS`
- Main run pass sentinel: `output/<dut>/vc_cdc/<dut>/vc_cdc_run/cdc/vc_cdc_run.PASS`
- CDCQA pass sentinel: `output/<dut>/vc_cdc/<dut>/vc_cdc_run/cdc/<dut>.cdc.cdcqa.PASS`

If a sentinel file exists, that stage passed.

## Common Violation Tags

CDC tags:
- `CDC_UNSYNC_NOSCHEME`
- `CDC_UNSYNC_ASYNCRESET`
- `CDC_UNSYNC_MULTIBIT`
- `CDC_RECONVERGENCE`

RDC tags:
- `RDC_CORRUPT_POTENTIAL`
- `RDC_CORRUPT_OBSERVED`
- `RDC_UNSYNC`

Hierarchy/setup tags:
- `HIER_ABSTRACT_MISMATCH`
- `SETUP_OUTPUT_CONSTRAINED_MULTICLOCK_DRIVER`
- `SETUP_PORT_CONSTRAINED`

## Common Reports

- CDC detailed report: `reports/cdc_detailed_report.rpt.gz`
- RDC corruption report: `reports/RDC_CORRUPT_OBSERVED.csv.gz`
- Waiver report: `reports/waiver.rpt.gz`

## Waiver Files

- `static/vc_cdc/waivers/`
- `static/vc_cdc/cdcqa_waivers.txt`
- `static/vc_cdc/inputs/` (constraint/waiver inputs)

## Troubleshooting

Compile-stage triage:
- Check compile summary report first.
- Check grdlbuild task logs under `output/grdlbuild/logs/`.
- Validate prerequisite stages in the Build-Run task dependency graph.

Run-stage triage:
- Start with `violations_summary.rpt.gz`.
- Drill down with `cdc_detailed_report.rpt.gz` and session log.
- For block abstraction issues, verify `SAM_MODELS/` presence under block outputs.

## Related Inputs

- `static/vc_cdc/flow.cfg`
- `static/vc_cdc/inputs/`
- `static/vc_cdc/waivers/`
- `flows/grdlbuild/<project>/static/vccdc/`

## Reference Model Output

Released model output is typically under:

`/p/cth/rtl/models/ddgcth/<project>/<cluster>/<model>-latest/output/<dut>/vc_cdc/`
