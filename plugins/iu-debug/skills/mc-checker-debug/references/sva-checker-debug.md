# SVA Assertion Debug Reference

## SVA Assertion Failures

**Bucket Pattern:** `SVA::MC::*`

### Debug Steps

```bash
# 1. Find SVA module and signal
# Example: SVA::MC::dfi_ch0_cmd_valid → DFI channel 0 command valid

# 2. Check assertion definition
cd $WORKAREA/src/val/sva/mc/
grep -r "dfi_ch0_cmd_valid" *.sv

# 3. Find assertion trigger time
zcat test.log.gz | grep -i "sva.*fail\|assert.*fail" | head -10

# 4. Check waveform at assertion time
# Load fsdb, go to assertion time, check signal values
```

### Common SVA Categories

| Pattern | Check |
|---------|-------|
| `dfi_*` | DFI interface protocol |
| `cmd_*` | Command protocol |
| `timing_*` | DRAM timing parameters |
| `coherency_*` | Data coherency |

## Specific Checker Debug Guides

### mc_mrs_chk (Mode Register Set Checker)

**Purpose:** Validates MRS command sequences and mode register values

**Common Failures:**
- Wrong MR value programmed
- MRS sequence order violation
- Timing between MRS commands

**Debug Steps:**

```bash
# 1. Check MRS tracker
zcat mc_mrs_trk.out.gz | grep -E "MR[0-9]+" | tail -50

# 2. Compare expected vs actual MR values
zcat griffin/griffin_postsim_mc_mrs_chk.log.gz | grep -E "expected|actual|mismatch"

# 3. Check RTL MRS programming
cd $WORKAREA/src/rtl/mc/
grep -r "mrs\|mode_register" *.v
```

### mc_refresh_chk (Refresh Checker)

**Purpose:** Validates refresh command timing and coverage

**Common Failures:**
- Refresh not issued to all banks
- tREFI violation
- Refresh during wrong state

**Debug Steps:**

```bash
# 1. Check refresh tracker
zcat mc_refresh_trk.out.gz | tail -100

# 2. Check per-bank refresh status
zcat mc_refresh_trk.out.gz | awk '{print $2, $3}' | sort | uniq -c
# Should show equal count for all banks

# 3. Check Griffin log for specific violation
zcat griffin/griffin_postsim_mc_refresh_chk.log.gz | grep -B 5 "FAIL\|ERROR"
```

### mc_pm_control_chk (Power Management Checker)

**Purpose:** Validates power state transitions and timing

**Common Failures:**
- Invalid state transition
- Timing violation during C-state entry/exit
- Command during power-down

**Debug Steps:**

```bash
# 1. Check power tracker
zcat mc_power_tracker.log.gz | grep -E "C[0-9]|power|idle" | tail -50

# 2. Find state transition around error
zcat mc_power_tracker.log.gz | awk '$1 > <error_time-1000> && $1 < <error_time+1000>'

# 3. Check Griffin log
zcat griffin/griffin_postsim_mc_pm_control_chk.log.gz | tail -100
```

### mc_address_translation

**Purpose:** Validates address mapping (system → DRAM)

**Common Failures:**
- Address decoded to wrong channel/rank/bank
- Interleave calculation error
- Row/column bit mapping

**Debug Steps:**

```bash
# 1. Get failing address
zcat test.log.gz | grep -i "address.*error\|translation" | head -10

# 2. Check address mapping config
cat <test_path>/*.rpt | grep -i "interleave\|address\|hash"

# 3. Manually decode address
# Apply interleave formula to verify expected vs actual
```

## Concrete Failure Example

**Failure:** `GRIFFIN_FATAL::McMrsChecker KeyError: (2, 0, 0)`

**Analysis:**
1. KeyError (2, 0, 0) = channel 2, device 0, rank 0 not found
2. Checker didn't initialize tracking for this channel/rank combination
3. Test configuration has more channels than checker expected

**Resolution:**
```bash
# 1. Check test config
cat *.rpt | grep "NUM_CH"  # Shows NUM_CH=4

# 2. Check checker initialization
grep "for.*channel" mc_mrs_checker.py  # Shows range(2) - only 2 channels!

# 3. Fix: Update checker to handle all channels
```
