# Griffin/UTDB Debug Reference

## Griffin Framework Overview

Griffin is the Python-based validation framework for post-simulation checking.

### Data Flow

```
Simulation → Trackers (log files) → UTDB (database) → Griffin Checkers → Pass/Fail
```

### Key Locations

| Component | Location |
|-----------|----------|
| MC Checkers | `$WORKAREA/src/val/griffin/agents/mc_*/` |
| PMA Checkers | `$WORKAREA/src/val/griffin/agents/pma_*/` |
| Griffin Logs | `<test_path>/griffin/griffin_postsim_*.log.gz` |
| Opera Logs | `<test_path>/opera_output/logs/griffin.*.log.gz` |

## Common Griffin Failure Patterns

### 1. Python Exceptions (KeyError, IndexError)

**Symptoms:**
```python
GRIFFIN_FATAL: [McMrsChecker] Griffin detected an exception (KeyError) during execution
KeyError: (2, 0, 0)
```

**What This Means:**
- Checker tried to access data that doesn't exist in its tracking dictionary
- Common causes:
  1. Missing initialization for channel/rank/bank combinations
  2. Expected events weren't logged during simulation
  3. Configuration mismatch

**Debug Steps:**

```bash
# 1. Identify the missing key pattern
# Example: KeyError: (2, 0, 0) = (channel=2, device=0, rank=0)

# 2. Check checker initialization
cd $WORKAREA/src/val/griffin/agents/mc_mrs/
grep -A 30 "__init__\|initialize\|setup" mc_mrs_checker.py

# 3. Check if events were logged
zcat <test_path>/mc_refresh_trk.out.gz | grep "channel.*2.*rank.*0"

# 4. Check test configuration
cat <test_path>/*.rpt | grep -E "channels|ranks|sagv"

# 5. Check recent checker changes
cd $WORKAREA/src/val/griffin/agents/mc_mrs/
git log --oneline -20 mc_mrs_checker.py
```

**Typical Fixes:**
- Add initialization for missing channel/rank/bank combinations
- Add null checks before accessing dictionary keys
- Update checker to handle new configurations

### 2. Data Structure Mismatches

**Symptoms:**
```python
GRIFFIN_ERROR: Expected dictionary key 'field_name' not found in record
AttributeError: 'NoneType' object has no attribute 'TIME'
```

**Debug Steps:**

```bash
# 1. Check UTDB record structure
cd $WORKAREA/src/val/utdb/
grep -r "record_type_name" *.py

# 2. Examine actual tracker log field names
zcat <test_path>/mc_refresh_trk.out.gz | head -50

# 3. Verify checker expectations match tracker output
cd $WORKAREA/src/val/griffin/agents/<checker_name>/
grep "record\[.*\]\|record\..*" *.py
```

### 3. Preloader Log Parsing Issues

**Symptoms:**
```python
GRIFFIN_FATAL: [McWrCoherencyChk] ddr wr data was not found in the expected queue
# Byte mismatches at specific positions
```

**Root Cause:** 
`CORRUPTED_DATA` field in preloader logs uses underscore (`_`) as separator, causing parsing bugs.

**Debug Steps:**

```bash
# 1. Check Griffin log for data mismatches
zcat <test_path>/griffin/griffin_postsim_mc_wr_coherency_chk.log.gz | grep -A 10 "GRIFFIN_FATAL"

# 2. Check preloader log for the address
zcat <test_path>/mc_preloader.log.gz | grep "CFI_ADDR=<address>"
# Compare DATA vs CORRUPTED_DATA fields

# 3. Examine checker's field selection logic
cd $WORKAREA/src/val/griffin/agents/mc_wr_coherency/
grep -A 20 "corrupted_data\|CORRUPTED_DATA" mc_wr_coherency_chk.py
```

### 4. Timing/Synchronization Issues

**Symptoms:**
```python
GRIFFIN_ERROR: Event not found at expected time
GRIFFIN_FATAL: Missing transaction in window [T1, T2]
```

**Debug Steps:**

```bash
# 1. Check tracker timestamps
zcat <test_path>/mc_*_trk.out.gz | awk '{print $1}' | sort -n | head -20

# 2. Verify time windows in checker
grep -E "window|time_range|tolerance" $WORKAREA/src/val/griffin/agents/<checker>/*.py

# 3. Check for clock domain issues
zcat <test_path>/test.log.gz | grep -i "clock\|freq\|sagv"
```

## UTDB Issues

### Database Upload Failures

**Symptoms:**
```
UTDB ERROR: Failed to upload record
UTDB: Connection timeout
```

**Debug Steps:**

```bash
# Check UTDB logs
ls <test_path>/utdb*.log*

# Verify database connectivity
echo $UTDB_SERVER

# Check record format
zcat <test_path>/mc_*_trk.out.gz | head -5
```

## Griffin Log Analysis

### Finding the Right Log

```bash
# List all Griffin logs
ls <test_path>/griffin/griffin_postsim_*.log*

# Search for specific checker
zcat <test_path>/griffin/griffin_postsim_mc_mrs_chk.log.gz | tail -100

# Find errors across all logs
zgrep -l "GRIFFIN_FATAL\|GRIFFIN_ERROR" <test_path>/griffin/*.log.gz
```

### Key Log Patterns

| Pattern | Meaning |
|---------|---------|
| `GRIFFIN_FATAL` | Checker failed with critical error |
| `GRIFFIN_ERROR` | Checker encountered error but continued |
| `KeyError:` | Missing dictionary key |
| `IndexError:` | Array index out of bounds |
| `AttributeError:` | Accessing attribute on None |

## Concrete Failure Example

**Failure:** `GRIFFIN_FATAL: [McWrCoherencyChk] ddr wr data was not found in the expected queue`

**Analysis:**
```bash
# 1. Check Griffin log for context
zcat griffin/griffin_postsim_mc_wr_coherency_chk.log.gz | grep -A 10 "FATAL"
# Shows: byte 21 mismatch: expected 0x76, got 0xf6

# 2. Check preloader log for the address
zcat mc_preloader.log.gz | grep "CFI_ADDR=0x12345678"
# Shows: CORRUPTED_DATA field has underscore separator issue

# 3. Root cause: CORRUPTED_DATA parsing bug with underscore
```

**Resolution:** Checker incorrectly parsed CORRUPTED_DATA field due to underscore separator.
