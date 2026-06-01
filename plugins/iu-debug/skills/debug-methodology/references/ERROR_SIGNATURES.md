# Error Signature Classification

## Error Type → Initial Action

| Signature Pattern | Error Type | Initial Action |
|-------------------|------------|----------------|
| `UVM_ERROR @ <time>: [<checker>]` | Checker error | Find checker source, understand trigger |
| `UVM_FATAL @ <time>` | Critical failure | Check for resource exhaustion or deadlock |
| `TIMEOUT @ <time>` | Watchdog timeout | Look for missing events, blocked transactions |
| `*Denali* Error:` | DRAM protocol | Route to `mc-denali-debug` |
| `GRIFFIN_FATAL` | Post-processing | Route to `mc-pp-debug` |
| `PROTOCOL_VIOLATION` | Protocol rule broken | Find VIP checker, review spec |
| `ASSERTION_FAILURE` | SVA assertion | Locate assertion, check conditions |
| `MISMATCH` | Data comparison | Compare expected vs actual in logs |

## Common Checker Name Patterns

| Pattern | Component | Typical Issues |
|---------|-----------|----------------|
| `[*_CHECKER]` | UVM checker | Protocol/data violations |
| `[*_MONITOR]` | UVM monitor | Unexpected transactions |
| `[*_SCOREBOARD]` | UVM scoreboard | Data mismatches |
| `SVA::*` | SVA assertion | RTL property violations |
| `*_chk` | Component checker | Module-specific errors |

## Error Context Extraction

```bash
# Extract full error context
grep -B10 -A10 "UVM_ERROR" jestr.log | head -50

# Get all unique error types
grep -o "UVM_ERROR.*\[.*\]" jestr.log | sort -u

# Count errors by type
grep "UVM_ERROR" jestr.log | grep -o "\[.*\]" | sort | uniq -c | sort -rn
```

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| `UVM_INFO` | Informational | Usually ignore unless debugging |
| `UVM_WARNING` | Warning | Review if related to failure |
| `UVM_ERROR` | Error | Primary debug target |
| `UVM_FATAL` | Fatal | Immediate root cause or consequence |
