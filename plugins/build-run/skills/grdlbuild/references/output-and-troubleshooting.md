# Output and Troubleshooting

Use this reference after running `run_grdlbuild` through the main skill.

## Output Layout

All output is written under:

- `output/grdlbuild/` relative to `$WORKAREA`

Primary logs:

- `output/grdlbuild/logs/grdlbuild_summary.log`
- `output/grdlbuild/logs/tasks_summary.log`
- `output/grdlbuild/logs/<project>.<task>.log`

Netbatch artifacts:

- `output/grdlbuild/nbtasks/*.nbtask`
- `output/grdlbuild/nbtasks/*.nbtask.feeder_data`

Prediction and conditional logs:

- `output/grdlbuild/prediction_logs/prediction_*.log`
- `output/grdlbuild/condLogs/conditionals_summary`
- `output/grdlbuild/condLogs/*_cond.log`

## Quick Log Reads

```bash
cat output/grdlbuild/logs/grdlbuild_summary.log
cat output/grdlbuild/logs/tasks_summary.log
cat output/grdlbuild/logs/<project>.<task>.log
cat output/grdlbuild/condLogs/conditionals_summary
```

## Environment Failures

If the tool reports "Environment not ready":

1. Ensure `CTH_SETUP_CMD` exists.
2. Ensure `WORKAREA` exists and points to a real directory.
3. Delegate setup to `@fe-setup` or `@env-detect`.
4. Re-run the same `run_grdlbuild` call.

## Common Recovery Patterns

Retry a single failed stage:

```bash
grdlbuild <failed_task_path> -id -local
```

Resume flow from failed stage:

```bash
grdlbuild <failed_task_path> -sft -local
```

Preview planned tasks before rerun:

```bash
grdlbuild -st all -dut hubs -run_modes turnin
```
