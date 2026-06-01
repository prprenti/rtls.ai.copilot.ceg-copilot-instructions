# MC Refresh Checker Debug Reference

## Checker Overview

**Checker:** `mc_refresh_chk` (McRefreshChecker)  
**Location:** `$WORKAREA/src/val/griffin/agents/mc_refresh/`  
**Purpose:** Validates refresh command timing, coverage, and JEDEC compliance

## Common Failures

### 1. Refresh Not Issued to All Banks

**Error Pattern:**
```
GRIFFIN_FATAL: [McRefreshChecker] Bank 3 not refreshed within tREFI window
Channel 0, Rank 0: Banks refreshed = [0,1,2,4,5,6,7], Missing = [3]
```

**Debug Steps:**
```bash
# 1. Check refresh tracker for bank coverage
zcat mc_refresh_trk.out.gz | grep "rank.*0" | awk '{print $NF}' | sort | uniq -c
# Should show equal counts for all banks

# 2. Find the missing bank's last refresh
zcat mc_refresh_trk.out.gz | grep "bank.*3" | tail -10

# 3. Check if SAGV transition interrupted refresh
zcat mc_sagv_retention_trk.out.gz | grep -B 5 -A 5 "<error_time>"
```

### 2. tREFI Violation

**Error Pattern:**
```
GRIFFIN_ERROR: [McRefreshChecker] tREFI violation
Time between refreshes: 8.2us, Max allowed: 7.8us
```

**Debug Steps:**
```bash
# 1. Calculate actual refresh intervals
zcat mc_refresh_trk.out.gz | awk '{print $1}' | \
  awk 'NR>1{print $1-prev}{prev=$1}' | sort -n | tail -10

# 2. Look for refresh suppression periods
zcat mc_power_tracker.log.gz | grep -E "self_refresh|power_down" | tail -20

# 3. Check for C-state blocking refresh
zcat test.log.gz | grep -i "c_state\|cstate" | tail -20
```

### 3. Refresh During Self-Refresh

**Error Pattern:**
```
GRIFFIN_ERROR: [McRefreshChecker] Refresh issued during self-refresh state
```

**Debug Steps:**
```bash
# 1. Check self-refresh state timeline
zcat mc_self_refresh_trk.out.gz | awk '$1 > <time-1000> && $1 < <time+1000>'

# 2. Correlate with refresh commands
zcat mc_refresh_trk.out.gz | awk '$1 > <time-1000> && $1 < <time+1000>'

# 3. Check state machine transitions
zcat mc_power_tracker.log.gz | grep -E "SR_ENTRY|SR_EXIT" | tail -20
```

## Per-Bank Refresh (LPDDR5/LPDDR6)

### REFPB Requirements

LPDDR5/6 uses Per-Bank Refresh which requires:
1. All banks must receive one refresh before any bank gets a second
2. Bank groups must be refreshed in order (BG0 → BG1 → BG2 → BG3)

### Checking REFPB Compliance

```bash
# Track refresh per bank group
zcat mc_refresh_trk.out.gz | grep "REFPB" | awk '{print $3, $4}' | sort | uniq -c

# Verify ordering
zcat mc_refresh_trk.out.gz | grep "REFPB" | awk '{print $1, $3, $4}' | head -50
```

## RTL Investigation

**Key RTL files:**
```bash
$WORKAREA/src/rtl/mc/mc_refresh_sch.v       # Refresh scheduler
$WORKAREA/src/rtl/mc/mc_refresh_cnt.v       # Refresh counter
$WORKAREA/src/rtl/mc/mc_bank_refresh.v      # Per-bank refresh logic
```

**Signals to check:**
- `refresh_req`, `refresh_ack`
- `bank_refresh_cnt[N]`
- `trefi_cnt`, `trefi_max`
- `all_banks_refreshed`

## Timing Parameters

| Parameter | DDR5 | LPDDR5 | LPDDR6 |
|-----------|------|--------|--------|
| tREFI | 3.9us/7.8us | 3.9us | 1.95us |
| tRFC | 350ns-550ns | 280ns-380ns | 200ns-300ns |
| tRFCpb | N/A | 90ns-140ns | 60ns-100ns |
