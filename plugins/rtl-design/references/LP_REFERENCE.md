# VCLP (Low Power) Reference

## FE Readiness (Required First)

Run:

```text
fe-setup/check_terminal_ready()
```

Proceed only when readiness returns `true`.

## Flow Stages

1. Library file generation
2. Compile stage
3. Full-chip and partition tests
4. Optional post-release backslide checks

Typical task grouping:
- Library file generation
- Compile
- Full-chip test runs
- Partition test runs
- Post-release subsystem/backslide checks

## Build-Run Usage

- Use Build-Run plugin grdlbuild skill conventions for task discovery and execution.
- Use MCP `build-run/run_grdlbuild` for flow task execution.
- Use MCP `build-run/run_make` for static debug runs under `static/vclp`.

## Flow and Output Structure

- Main output root: `output/<dut>/vclp/`
- Compile root: `output/<dut>/vclp/vclp_compile/`
- Per-test root: `output/<dut>/vclp/<pass_name>/vclp_run/`
- Backslide report root: `output/<dut>/vclp/`

## Output and Primary Logs

- Main output root: `output/<dut>/vclp/`
- Compile summary: `output/<dut>/vclp/vclp_compile/summary.rpt`
- Test post-run log: `output/<dut>/vclp/<pass_name>/vclp_run/post_run.log`
- Main test session log: `output/<dut>/vclp/<pass_name>/vclp_run/vcst_session.log.gz`
- Backslide report: `output/<dut>/vclp/vclp_backslide_ss_check.rpt`
- grdlbuild summary log: `output/grdlbuild/logs/grdlbuild_summary.log`

## Finding Violations

Primary files:
- `output/<dut>/vclp/<pass_name>/vclp_run/post_run.log`
- `output/<dut>/vclp/<pass_name>/vclp_run/vcst_session.log.gz`
- `output/<dut>/vclp/<pass_name>/vclp_run/INTC_QOR__Violations_Reference.txt`

Compile triage files:
- `output/<dut>/vclp/vclp_compile/vcst_session.log`
- `output/<dut>/vclp/vclp_compile/summary.rpt`

## Pass/Fail Indicators

- Compile pass sentinel: `output/<dut>/vclp/vclp_compile/vclp_compile.PASS`
- Test pass sentinel: `output/<dut>/vclp/<pass_name>/vclp_run/vclp_run.PASS`

If a sentinel file exists, that stage passed.

## Waiver and Error Schemes

- `static/vclp/waivers/`
- `static/vclp/log_parser/vclp_waiver_scheme.yaml`
- `static/vclp/log_parser/vclp_error_scheme.yaml`

## Troubleshooting

Compile-stage issues:
- Verify filelist dependencies completed in Build-Run dependency chain.
- Validate UPF inputs and localized UPF file presence.
- Review compile summary and compile session log.

Test-stage issues:
- Start with `post_run.log`.
- Correlate with session log for full context.
- Check model-size-reduction logs for reduction-specific failures.

Backslide issues:
- Review `vclp_backslide_ss_check.rpt` for regression deltas.

## Related Inputs

- `static/vclp/flow.cfg`
- `static/vclp/waivers/`
- `static/vclp/log_parser/`
- `flows/grdlbuild/<dut>/static/vclp/`

## Related Files

- `static/vclp/Makefile`
- `static/vclp/isospec/`

## Reference Model Output

Released model output is typically under:

`/p/cth/rtl/models/ddgcth/<project>/<cluster>/<model>-latest/output/<dut>/vclp/`
