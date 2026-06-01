# AGS Show Reference (Non-Destructive)

Safety category: NON-DESTRUCTIVE.

Use this reference for read-only AGS workflows: search, inspect, identify, membership, and status checks.
Do not perform request/revoke/approve/deny actions from this file.

## Read-Only Command Patterns

```bash
# Search entities
ags search role --name "PARTIAL_NAME"
ags search entitlement --name "PARTIAL_NAME"
ags search workgroup --name "PARTIAL_NAME"

# Identify entity type
ags identify --name "NAME"

# Show details
ags show user --user USER [--filter {entitlement|role|workgroup|unixgroup}] [--include-source]
ags show role --name "NAME" [--include-users] [--filter show_entitlements]
ags show entitlement --name "NAME" [--include-users]
ags show workgroup --name "NAME"

# List members
ags members --name "NAME" [--type {entitlement|role|workgroup|pdl}] [--filter {worker|generic|all}]

# Check status (read-only)
ags status --id WORK_ITEM_ID
ags status --request-id REQUEST_ID
ags status --approver USER
ags status --requester USER
ags status --requestee USER
```

## Common Lookup Flows

### Find the correct role then inspect entitlements

```bash
ags search role --name "RTL"
ags show role --name "RTL_Developer" --filter show_entitlements
```

### Check user access and source

```bash
ags show user --user jsmith --include-source --format table
```

### Export members for review/audit

```bash
ags members --name "Privileged-Admin-Role" --format csv > members.csv
```

## Useful Output Options

```bash
--format {table|json|csv|script}
--fields field1,field2,field3
--fields all
```

## Troubleshooting (Read-Only)

If a command fails, check command syntax/options first:
every AGS command layer supports `-h` (for example, `ags -h`, `ags show -h`, `ags show role -h`).

Entity not found:
```bash
ags search role --name "partial-name"
ags identify --name "uncertain-name"
```

Permission/visibility issues:
```bash
ags show role --name "Role-Name" --fields all
```

Need to compare user access:
```bash
ags show diff --user1 user_a --user2 user_b
```
