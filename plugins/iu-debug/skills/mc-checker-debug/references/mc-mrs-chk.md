# MC MRS Checker Debug Reference

## Checker Overview

**Checker:** `mc_mrs_chk` (McMrsChecker)  
**Location:** `$WORKAREA/src/val/griffin/agents/mc_mrs/`  
**Purpose:** Validates Mode Register Set (MRS) command sequences and values

## Common Failures

### 1. MR Value Mismatch

**Error Pattern:**
```
GRIFFIN_FATAL: [McMrsChecker] MR value mismatch
Expected MR3 = 0x45, Actual = 0x44
```

**Debug Steps:**
```bash
# 1. Check MRS tracker
zcat mc_mrs_trk.out.gz | grep "MR3" | tail -20

# 2. Find the discrepancy time
zcat griffin/griffin_postsim_mc_mrs_chk.log.gz | grep -B 10 "mismatch"

# 3. Check RTL MRS programming
cd $WORKAREA/src/rtl/mc/
grep -r "mr3\|MR3" *.v | head -20
```

**Common Root Causes:**
- RTL not updating MR value after SAGV transition
- Incorrect MR field encoding
- Multi-rank MR programming order

### 2. MRS Sequence Violation

**Error Pattern:**
```
GRIFFIN_ERROR: [McMrsChecker] MRS sequence violation - MR13 before MR3
```

**Debug Steps:**
```bash
# 1. Check MRS command order
zcat mc_mrs_trk.out.gz | grep -E "TIME|MR[0-9]+" | head -50

# 2. Verify JEDEC sequence requirements
# DDR5: MR0 → MR1 → MR2 → MR3 → ... → MR8
# LPDDR5: Specific OPC/OCA sequence

# 3. Check RTL sequencer
grep -r "mrs_seq\|sequence" $WORKAREA/src/rtl/mc/*.v
```

### 3. KeyError for Missing Channel/Rank

**Error Pattern:**
```
GRIFFIN_FATAL: [McMrsChecker] KeyError: (2, 0, 0)
```

**What (2, 0, 0) means:** (channel=2, device=0, rank=0)

**Debug Steps:**
```bash
# 1. Check checker initialization
grep -A 30 "__init__\|initialize" mc_mrs_checker.py

# 2. Verify test configuration has channel 2
cat <test_path>/*.rpt | grep -i "channels\|num_ch"

# 3. Check if checker handles all channels
grep -E "for.*channel\|channel.*range" mc_mrs_checker.py
```

## RTL Investigation

**Key RTL files:**
```bash
$WORKAREA/src/rtl/mc/mc_mrs_fsm.v         # MRS state machine
$WORKAREA/src/rtl/mc/mc_init_seq.v        # Init sequence
$WORKAREA/src/rtl/mc/mc_sagv_mrs.v        # SAGV MRS handling
```

**Signal names to check:**
- `mrs_valid`, `mrs_addr`, `mrs_data`
- `mrs_seq_state`, `mrs_done`
- `sagv_mrs_update`

## JEDEC References

| Spec | MRS Section |
|------|-------------|
| DDR5 JESD79-5 | Section 4.8 Mode Registers |
| LPDDR5 JESD209-5 | Section 4.6 Mode Registers |
| LPDDR6 JESD209-6 | Section 4.6 Mode Registers |
