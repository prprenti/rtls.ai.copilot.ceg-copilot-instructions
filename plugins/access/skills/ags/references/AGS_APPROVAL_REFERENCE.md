# AGS Approval Reference (Ruby Workflow)

Safety category: DESTRUCTIVE / STATE-CHANGING.

This reference is only for the automated approval queue workflow script:

- `skills/ags/ags-approval-flow.rb`

Do not use this workflow for routine `ags request`, `ags revoke`, `ags approve`, or `ags deny` commands. Those stay in direct `ags` CLI usage.

## When To Use This

Use the Ruby workflow when the user asks to:
- process pending approvals
- run an approval queue workflow
- dry-run queue processing
- generate an approval script from queue items

## Script Commands

```bash
# Process pending approvals
skills/ags/ags-approval-flow.rb

# Preview only (no execution)
skills/ags/ags-approval-flow.rb --dry-run

# Write output to a specific script file
skills/ags/ags-approval-flow.rb --output my-approvals.sh

# Evaluate queue for another approver (dry-run only)
skills/ags/ags-approval-flow.rb --approver jsmith --dry-run
```

If a command fails, check usage/options first:
the script command layer supports `-h` (for example, `skills/ags/ags-approval-flow.rb -h`).

## What The Workflow Does

- Reads pending approval items.
- Applies approval/deny logic based on badge/org/justification content.
- Produces an output script and review sections for human follow-up.

## Output Expectations

The workflow can emit:
- approve commands
- deny commands
- unmatched/manual-review entries

Treat output as state-changing guidance; review before execution when needed.

## Integration With Employee Lookup

The workflow uses employee lookup to validate identifiers and org context:

```bash
uv run skills/employee-lookup/employee_lookup.py ...
```

## Guardrails

- This workflow is not a substitute for explicit direct `ags` commands.
- For normal request/revoke/approve/deny operations, use `ags` CLI directly.
- For large queues, prefer `--dry-run` first.
