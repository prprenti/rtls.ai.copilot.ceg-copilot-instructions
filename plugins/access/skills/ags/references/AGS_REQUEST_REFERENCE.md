# AGS Request Reference (Destructive)

Safety category: DESTRUCTIVE / STATE-CHANGING.

Use this reference for actions that create, modify, approve, deny, revoke, or remove AGS access.
Always confirm target, scope, and justification before running commands.

## Scope

- Use this file for direct `ags` CLI request/revoke/approve/deny operations.
- For Ruby automated queue processing, use [AGS_APPROVAL_REFERENCE.md](AGS_APPROVAL_REFERENCE.md).

## Safety Rules

- Always require a detailed justification for request/revoke/bulk operations.
- For bulk approve/deny, run with `--debug` first to preview scope.
- Do not proceed with unclear names or incomplete filters.
- Prefer narrow filters over `--all` when possible.

If a command fails, check command syntax/options first:
every AGS command layer supports `-h` (for example, `ags -h`, `ags bulk -h`, `ags bulk approve -h`).

## State-Changing Command Patterns

```bash
# Request access
ags request {entitlement|role|workgroup} --name "NAME" [--user USER] --justification "REASON"

# Revoke access
ags revoke {entitlement|role|workgroup} --name "NAME" [--user USER] --justification "REASON"

# Bulk request/remove
ags bulk request --name "NAME" {--file users.txt | --users user1,user2} --justification "REASON"
ags bulk remove --name "NAME" {--file users.txt | --users user1,user2} --justification "REASON"

# Approve/deny single
ags approve --id WORK_ITEM_ID
ags deny --id WORK_ITEM_ID --comment "REASON"

# Bulk approve/deny (preview first)
ags bulk approve [filters...] --all --debug
ags bulk approve [filters...] --all
ags bulk deny [filters...] --all --comment "REASON" --debug
ags bulk deny [filters...] --all --comment "REASON"
```

## Required Inputs

Request/Revoke/Bulk:
- Target name (`--name`)
- User scope (`--user`, `--users`, or `--file`) when applicable
- Detailed business justification (`--justification`)

Deny:
- Work item ID (`--id`) or bulk filters
- Denial reason (`--comment`)

## High-Confidence Workflow

1. Verify target entity first (read-only):
```bash
ags identify --name "NAME"
ags show role --name "NAME"
```
2. Build smallest safe command.
3. Preview with `--debug` for bulk approvals/denials.
4. Execute real command.
5. Check results:
```bash
ags status --id WORK_ITEM_ID
ags status --requestee USER
```

## Bulk Operations Runtime Note

Bulk operations are expected to be slow (2-5 seconds per user due to API rate limiting).
Do not abort long-running bulk commands unless user requests cancellation.

## Related Reference

For automated approval queue processing with `skills/ags/ags-approval-flow.rb`, see [AGS_APPROVAL_REFERENCE.md](AGS_APPROVAL_REFERENCE.md).
