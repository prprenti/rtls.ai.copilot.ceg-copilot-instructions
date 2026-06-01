# CFI Protocol Violations

## Common Violation Types

| Violation | Description | Checker |
|-----------|-------------|---------|
| Valid/Ready handshake | Improper valid/ready protocol | cfi_vc handshake checker |
| Packet format | Invalid header/payload encoding | cfi_vc format checker |
| Credit overflow | Credits exceed maximum | cfi_vc credit checker |
| Out-of-order | Transaction ordering violation | cfi_vc ordering checker |

## Debug Commands

```bash
# Find protocol violations
grep -i "protocol.*error\|violation" jestr.log

# Check CFI VIP errors
grep "cfi_vc.*ERROR" jestr.log

# Review specific VC activity
grep "CFI_DEV_VC0" CFI_DEV_VC0_full_txn_tracker_cfi_txn_tracker.log
```

## CFI Error Categories

### 1. Credit Management Errors
- Credit count underflow/overflow
- Credit return timing violation
- Credit allocation mismatch

### 2. Protocol Compliance Errors
- Valid without ready
- Data without valid
- Missing acknowledgment

### 3. Configuration Errors
- VC not enabled but traffic attempted
- Credit allocation mismatch DEV/CTL
- Buffer size insufficient

### 4. Performance Issues
- Excessive credit blocking
- High latency credit return
- Throughput degradation

## Investigation Checklist

- [ ] Check error message for specific violation type
- [ ] Review CFI tracker logs around failure time
- [ ] Verify VC configuration in config tracker
- [ ] Check credit state in waveforms
- [ ] Compare against CFI specification
