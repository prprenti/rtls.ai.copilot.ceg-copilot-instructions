# MC Unit Test Debug Reference

## Unit Test Framework Details

**Framework:** VUnit (version 23.04.001)  
**Test Location:** `$WORKAREA/src/val/tb/*/unit_tests/`  
**Test Pattern:** `*_tests.sv`

### Key Components

| Component | Purpose |
|-----------|---------|
| Test Suites | Groups of related tests (e.g., `mc_repository_suite`) |
| Test Fixtures | Setup/teardown for tests |
| Test Cases | Individual test functions using VUnit macros |

## Running Unit Tests

### Method 1: Using gtc (PREFERRED)

**`gtc` is the preferred tool for re-running unit tests from existing test directories.**

```bash
# Re-run an existing test (WAIT for completion - takes ~1 minute)
gtc -run /path/to/regression/mc/mc_unit_tests.list.5/mc_config_resolver_unit_test

# Just get the command without running
gtc /path/to/test/directory

# Re-run with fsdb waveform
gtc -f -run /path/to/test/directory

# Re-run with compile
gtc -c -run /path/to/test/directory
```

**Common gtc options:**
| Option | Purpose |
|--------|---------|
| `-run` | Execute immediately (wait for completion!) |
| `-f` / `-fsdb` | Add fsdb waveform dumping |
| `-c` | Add compile step before run |
| `-o` | Overwrite old test results |
| `-no_seed` | Remove seed for random re-runs |
| `-in_reg` / `-rir` | Run in regression directory |

### Method 2: Using trex Directly

Use `gtc` to extract the command from an existing test, then run it:

```bash
# Get command from passing reference
gtc $BAK_LATEST_TURNIN/regression/mc/mc_unit_tests.list.5/mc_event_pool_test

# Copy the trex command and run in your workspace
cd $WORKAREA
trex 1022 mc_event_pool_test -no_global_test_options -vunit -vunit_args -inc $WORKAREA/src/val/tb/mc_event_pool/unit_tests/mc_event_pool_vunit_unittests_inc.f -vunit_args- -dut mc -save -flow vcssim -seed 1022
```

### Finding Test References

```bash
# List available unit test results
ls $BAK_LATEST_TURNIN/regression/mc/mc_unit_tests.list*/

# View unit test list for test names and seeds
cat $WORKAREA/reglist/mc/unit_tests/mc_unit_tests.list
```

## Common Unit Test Failures

### 1. Event Synchronization Issues

**Symptoms:**
- Test hangs or times out
- Assertions about event ordering fail
- Multiple threads waiting on same event

**Debug Steps:**

```bash
# Check event pool log for timing
cat <test_path>/mc_event_pool.log | grep -E "wait|trigger|observer"

# Common issue: wait_ptrigger() only wakes ONE thread
# Solution: Use wait_trigger() to wake ALL waiting threads
```

### 2. Test Fixture Setup Failures

**Symptoms:**
```
VUnit: Setup failed for test 'test_name'
Error: Could not initialize fixture
```

**Debug Steps:**

```bash
# Check fixture initialization
grep -A 20 "virtual function void setup" <test_file>.sv

# Verify required components exist
grep "uvm_config_db" <test_file>.sv
```

### 3. Assertion Failures

**Symptoms:**
```
VUnit: CHECK failed: expected X, got Y
```

**Debug Steps:**

```bash
# Find the failing check in test code
grep -n "CHECK\|ASSERT" $WORKAREA/src/val/tb/<component>/unit_tests/*_tests.sv

# Check test log for context
zcat <test_path>/test.log.gz | grep -B 10 "CHECK failed"
```

## Concrete Failure Example

**Failure:** `mc_event_pool_test` hangs with timeout

**Analysis:**
```bash
# 1. Check event pool log
cat mc_event_pool.log | grep -E "wait|trigger"
# Shows: Thread A waiting on event, Thread B also waiting

# 2. Identify synchronization issue
# Found: Code uses wait_ptrigger() which only wakes ONE thread
# Multiple threads waiting → only first one wakes

# 3. Root cause: Should use wait_trigger() to wake ALL waiting threads
```

**Resolution:** Replace `wait_ptrigger()` with `wait_trigger()` when multiple threads may wait on same event.
