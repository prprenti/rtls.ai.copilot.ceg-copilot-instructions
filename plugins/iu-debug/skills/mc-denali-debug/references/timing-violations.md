# Denali Timing Violations Reference

## Timing Violations

### `tRFC_VIOLATION`

**What it means:**
- Refresh cycle time (tRFC) not met
- Command issued before refresh completed

**Debug Steps:**

```bash
# Check command sequence after refresh
zcat mc_cmd_trk.out.gz | grep -A 10 "REFRESH"
# Verify tRFC delay before next command
```

### `tRCD_VIOLATION`

**What it means:**
- RAS to CAS delay not met
- Read/Write issued too soon after Activate

**Debug Steps:**

```bash
# Check ACT to RD/WR timing
zcat mc_cmd_trk.out.gz | grep -E "ACT|RD|WR" | head -50
# Calculate time between ACT and subsequent RD/WR
```

### `tRP_VIOLATION`

**What it means:**
- Precharge time not met
- Activate issued too soon after Precharge

### `tRAS_VIOLATION`

**What it means:**
- Row active time not met
- Precharge issued too soon after Activate

## Command Sequence Errors

### `INVALID_COMMAND_SEQUENCE`

**What it means:**
- Command issued in wrong bank state
- Example: Write without prior Activate

**Debug Steps:**

```bash
# Trace command sequence for affected bank
zcat mc_cmd_trk.out.gz | grep "bank.*<bank_num>" | tail -50
# Verify: ACT → RD/WR → PRE sequence
```

## RTL Investigation

### Finding Relevant RTL

```bash
cd $WORKAREA/src/rtl/mc/

# Timing parameter registers
grep -r "trfc\|trcd\|tras\|trp" *.v

# Command scheduler
grep -r "scheduler\|arbiter\|cmd.*queue" *.v

# Bank state tracking
grep -r "bank_state\|row_open\|precharge" *.v
```

### Common RTL Bug Patterns

| Pattern | Symptom | Investigation |
|---------|---------|---------------|
| State machine race | Intermittent failures | Check FSM transitions around error time |
| Counter overflow | Periodic failures | Check counter width and wrap logic |
| Multi-channel sync | Channel-specific errors | Check inter-channel coordination |
| SAGV interaction | Failures after freq change | Check frequency transition handling |

## Timing Parameter Reference

| Parameter | DDR5 (typical) | LPDDR5 (typical) |
|-----------|----------------|------------------|
| tRFC | 350ns-550ns | 280ns-380ns |
| tRCD | 14-18ns | 18-21ns |
| tRP | 14-18ns | 18-21ns |
| tRAS | 32-39ns | 42ns |
| tREFI | 3.9us/7.8us | 3.9us |
