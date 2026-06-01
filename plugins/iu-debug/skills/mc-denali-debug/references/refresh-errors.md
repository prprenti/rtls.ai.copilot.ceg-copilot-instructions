# Denali Refresh Errors Reference

## Refresh Protocol Violations

### `REFPB_NOT_ISSUED_TO_ALL_BANKS` (LPDDR6)

**What it means:**
- LPDDR6 Per-Bank Refresh requires issuing refresh to **all banks** before any individual bank can receive another refresh
- RTL issued refresh to specific banks without completing all-bank refresh cycle
- Violates JEDEC JESD209-6

**Debug Steps:**

```bash
# 1. Identify affected banks and channels
zcat test.log.gz | grep "REFPB_NOT_ISSUED_TO_ALL_BANKS"
# Extract: Channel, Device, Subchannel, BankGroup, Bank

# 2. Check refresh tracker for command sequence
zcat mc_refresh_trk.out.gz | grep -A 5 -B 5 "133692176"  # Use error timestamp
# Verify all banks in all bank groups received refresh

# 3. Check RTL refresh scheduler
cd $WORKAREA/src/rtl/mc/
grep -r "per.*bank.*refresh\|pb.*refresh\|refpb" *.v

# 4. Verify DRAM configuration from .rpt file
# - Technology: LPDDR6
# - Number of banks per bank group
# - SAGV configuration

# 5. Check if SAGV transitions affected refresh
zcat mc_sagv_retention_trk.out.gz | grep -B 20 "133692176"
```

**JEDEC Reference:** JESD209-6, Section: Refresh Operations, Per-Bank Refresh

### `REFRESH_NOT_VALID_NOW` (LPDDR5/LPDDR6)

**What it means:**
- Refresh command issued while DRAM is in Self-Refresh state
- Violates JEDEC JESD209-5 Section 6.2
- MC power management and refresh coordination bug

**Debug Steps:**

```bash
# 1. Check self-refresh state timing
zcat mc_self_refresh_trk.out.gz | awk '$1 > <error_time-10000> && $1 < <error_time+10000>'

# 2. Check power tracker for C-states
zcat mc_power_tracker.log.gz | awk '$1 > <error_time-10000> && $1 < <error_time+10000>'

# 3. Check SAGV transitions (often trigger self-refresh)
zcat mc_sagv_retention_trk.out.gz | awk '$1 > <error_time-50000> && $1 < <error_time+10000>'
```

**Common Root Causes:**
- SAGV transition enters self-refresh without pausing refresh
- Self-refresh exit sequence incomplete when refresh restarts
- Multi-channel coordination issue
- Power management state machine race condition

**JEDEC Reference:** JESD209-5/6, Section 6.2 (Power Modes)

### `REFRESH_VIOLATION` (DDR5/LPDDR5)

**What it means:**
- Refresh interval (tREFI) violated
- Too much time between refresh commands
- Risk of data loss due to DRAM cell charge decay

**Debug Steps:**

```bash
# 1. Calculate refresh intervals
zcat mc_refresh_trk.out.gz | awk '{if(NR>1) print $1-prev; prev=$1}' | sort -n
# Compare against tREFI spec (typically 7.8us for DDR5)

# 2. Look for refresh suppression
zcat mc_power_tracker.log.gz | grep -B 5 -A 5 "<error_timestamp>"
```

## Concrete Failure Example

**Failure:** `*Denali* Error: REFRESH_NOT_VALID_NOW @96667745 ps :: Refresh command for bg #0 bank #0 is invalid as chip is in SelfRefresh state.`

**Analysis:**
```bash
# 1. Check self-refresh state around error time
zcat mc_self_refresh_trk.out.gz | awk '$1 > 96660000 && $1 < 96670000'
# Shows: SR_ENTRY at 96665000, still in SR at error time

# 2. Check SAGV transition
zcat mc_sagv_retention_trk.out.gz | awk '$1 > 96660000 && $1 < 96670000'
# Shows: Frequency change at 96664000 triggered self-refresh

# 3. Root cause: Refresh scheduler didn't check SR state before issuing REF
```

**Resolution:** RTL bug - refresh FSM needs to check `self_refresh_active` signal before issuing refresh.
