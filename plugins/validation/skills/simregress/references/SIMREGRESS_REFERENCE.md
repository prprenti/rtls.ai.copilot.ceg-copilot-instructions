# Simregress and Trex Reference

Complete reference for simulation regression execution with `simregress` and individual test execution with `trex`.

**Important:** Test runs can take a very long time to complete—often many hours or even longer for large regression suites.

When submitting tests to Netbatch with `-net`, the simregress command returns immediately after job submission. The tests execute asynchronously on the compute cluster.

## Prerequisites

Before running any simregress/trex commands, verify the environment is properly set up per `copilot-instructions.md`.

Use the **@fe-setup** agent to verify and configure the environment.
If `CTH_SETUP_CMD` or `WORKAREA` is missing, the @fe-setup agent will set up the correct terminal.

## Building the Simulation Model

**Critical:** Before running any tests with simregress or trex, you must build the simulation model using grdlbuild. The model must be rebuilt after any code changes.

### Build vcssim or vcssimmpp

Depending on which flow you plan to use, build the corresponding simulation model:

**For vcssim flow (without UPF):**
```bash
grdlbuild vcssim
```

**For vcssimmpp flow (with UPF; multiple power plane):**
```bash
grdlbuild vcssimmpp
```

**How to know which to build:**
- Check the test command line from regression lists or .pass/.fail files
- If you see `-mpp` flag in the test command, build **vcssimmpp**
- Otherwise, build **vcssim**

### When to Rebuild

Rebuild the simulation model:
- **After any code changes** to RTL, testbench, or configuration files
- **Before running any tests** if the model doesn't exist
- **When you see build-related errors** during test execution

### Common Error Indicating Rebuild Needed

If you see this error during test execution:
```
MISC::Model pie was not built with either TIM or DTL. Cannot run with tim
```

This indicates the simulation model was not built or needs to be rebuilt. Run the appropriate grdlbuild command above before re-running tests.

## Deriving Simregress Command from Grdlbuild Collateral

To construct a simregress command line for running regression tests, gather information from your repository's grdlbuild configuration files.

### Step 1: Identify the Regression List

Regression lists are located in the `reglist/` directory. Common patterns:
```bash
ls $WORKAREA/reglist/*/
```

Look for files like:
- `level0.list` - Level 0 regression (smoke tests)
- `level1.list` or `level2.list` - Extended regressions

### Step 2: Determine the DUT (Design Under Test)

The DUT name typically matches:
- A subdirectory under `reglist/` (e.g., `reglist/pie/` → DUT is `pie`)
- Or examine `flows/grdlbuild/regress/build.gradle.kts` for simregress commands with `-dut <name>` patterns

### Step 3: Determine the Simulation Flow

The flow depends on which grdlbuild simulation target you built:

| Grdlbuild Target | Simregress Flow |
|------------------|-----------------|
| `grdlbuild vcssim` | `-flow vcssim` |
| `grdlbuild vcssimmpp` | `-flow vcssimmpp` |

**Important:** Always use the flow matching your most recent grdlbuild simulation build. Building with `vcssim` but running with `-flow vcssimmpp` will fail.

### Step 4: Extract Netbatch Parameters from resources.ini

Open `flows/grdlbuild/resources.ini` to find Netbatch submission parameters.

**For standard regressions**, combine:
1. **[global] default** - Provides pool (`p=`) and queue (`q=`)
2. **[global] regress** - Provides memory class (`c=`)

Example `resources.ini`:
```ini
[global]
default = p=zsc10_normal,q=/ddg/ip/fe/rtl,c=SLES15&&8G
regress = c=SLES15&&12G
```

Extract:
- Pool: `zsc10_normal` → `-P zsc10_normal`
- Queue: `/ddg/ip/fe/rtl` → `-Q /ddg/ip/fe/rtl`
- Class: `SLES15&&12G` → `-C "SLES15&&12G"`

**For other modes** (turnin, mock, filter, release), use the corresponding section:
```ini
[turnin]
default = p=zsc10_critical_gk,q=/ddg/ip2/pie/turnin
```

Combine with `[global] regress` class for memory:
- `-P zsc10_critical_gk -Q /ddg/ip2/pie/turnin -C "SLES15&&12G"`

### Step 5: Construct the Command

Assemble all components:
```bash
simregress -l $WORKAREA/reglist/<dut>/<listfile> -flow <simflow> -dut <dut> -net -P <pool> -Q <queue> -C "<class>"
```

**Example for pie DUT with vcssim:**
```bash
simregress -l $WORKAREA/reglist/pie/level0.list -flow vcssim -dut pie -net -P zsc10_normal -Q /ddg/ip/fe/rtl -C "SLES15&&12G"
```

**Example for pie DUT with vcssimmpp:**
```bash
simregress -l $WORKAREA/reglist/pie/level0.list -flow vcssimmpp -dut pie -net -P zsc10_normal -Q /ddg/ip/fe/rtl -C "SLES15&&12G"
```

### Quick Reference

**Find regression lists:**
```bash
find $WORKAREA/reglist -name "*.list"
```

**Extract netbatch defaults from resources.ini:**
```bash
grep -A1 "^\[global\]" flows/grdlbuild/resources.ini | grep "default ="
grep "^regress " flows/grdlbuild/resources.ini
```

**Generate Netbatch tasks without running (dry-run):**
```bash
simregress -l $WORKAREA/reglist/<dut>/<list> -flow <flow> -dut <dut> -net -no_run -P <P> -Q <Q> -C "<C>"
```

## Generating Waveforms for Debug

To generate FSDB waveform files for debugging, pass additional options to the underlying trex tool.

### Enabling FSDB Generation

Use the `-trex` / `-trex-` delimiters to pass options to trex:

```bash
simregress -l $WORKAREA/reglist/<dut>/<list> -flow <flow> -dut <dut> -net -P <P> -Q <Q> -C "<C>" -trex -fsdb -trex-
```

**Example:**
```bash
simregress -l $WORKAREA/reglist/pie/level0.list -flow vcssim -dut pie -net -P zsc10_normal -Q /ddg/ip/fe/rtl -C "SLES15&&12G" -trex -fsdb -trex-
```

### Preserving Run Directories for Passing Tests

By default, **only failing test directories are retained**. Passing test directories are deleted to save disk space.

To preserve run directories for **all tests** (including passing tests), add the `-save` option:

```bash
simregress -l $WORKAREA/reglist/<dut>/<list> -flow <flow> -dut <dut> -net -P <P> -Q <Q> -C "<C>" -trex -fsdb -trex- -save
```

**Example:**
```bash
simregress -l $WORKAREA/reglist/pie/level0.list -flow vcssim -dut pie -net -P zsc10_normal -Q /ddg/ip/fe/rtl -C "SLES15&&12G" -trex -fsdb -trex- -save
```

### When to Use These Options

- **`-trex -fsdb -trex-`** - Enable FSDB waveform generation for all tests
- **`-save`** - Keep run directories for passing tests (default: only failing tests are saved)

**Use cases:**
- Debugging passing tests or analyzing timing behavior
- Examining waveforms for all tests in a regression
- Preserving full test artifacts for later analysis

## Running Custom Test Lists

Simregress accepts any file containing test command lines via the `-l <list>` argument. This allows flexible test selection beyond standard regression lists.

### Using .fail Files to Rerun Failures

After a regression run, you can rerun only the failed tests by pointing directly to the `.fail` file:

```bash
simregress -l $WORKAREA/regression/<dut>/<listname>.latest/<listname>.fail -flow <flow> -dut <dut> -net -P <P> -Q <Q> -C "<C>"
```

**Example - Rerun failures with FSDB for debug:**
```bash
simregress -l $WORKAREA/regression/pie/level0.list.latest/level0.fail -flow vcssim -dut pie -net -P zsc10_normal -Q /ddg/ip/fe/rtl -C "SLES15&&12G" -trex -fsdb -trex- -save
```

This is useful for:
- Quick iteration on bug fixes without rerunning passing tests
- Generating waveforms only for failed tests to debug issues
- Reducing turnaround time on large regressions

### Creating Custom Lightweight Lists

When working on specific features or fixes, create a custom test list containing only relevant tests:

**1. Copy relevant test lines from the original list:**
```bash
# Extract specific tests by name pattern
grep "pie_ral" $WORKAREA/reglist/pie/level0.list > $WORKAREA/my_custom_tests.list

# Or copy specific test IDs
grep -E "^(1000|1002|1005)" $WORKAREA/reglist/pie/level0.list > $WORKAREA/my_custom_tests.list
```

**2. Run your custom list:**
```bash
simregress -l $WORKAREA/my_custom_tests.list -flow vcssim -dut pie -net -P zsc10_normal -Q /ddg/ip/fe/rtl -C "SLES15&&12G"
```

### Benefits of Custom Lists

**For large level0 regressions:**
- **Faster feedback** - Run only 5-10 relevant tests instead of 100+
- **Focus debugging** - Target tests affected by your code changes
- **Iterate quickly** - Check fixes without full regression overhead
- **Generate selective waveforms** - FSDB only for tests you care about

**Example workflow:**
1. Make code changes to RAL (Register Abstraction Layer)
2. Identify RAL-related tests: `grep ral $WORKAREA/reglist/pie/level0.list > $WORKAREA/ral_tests.list`
3. Run targeted regression: `simregress -l $WORKAREA/ral_tests.list ...`
4. Fix issues, iterate on small set
5. Run full level0 before code submission

**Note:** Custom lists must follow the same format as standard regression lists (test ID, test name, options, etc.).

## Monitoring Test Progress

**Important:** Test runs can take a very long time to complete—often many hours or even longer for large regression suites.

When submitting tests to Netbatch with `-net`, the simregress command returns immediately after job submission. The tests execute asynchronously on the compute cluster.

### Checking Status with lsti

Use the `lsti` command to monitor regression progress:

```bash
lsti -r $WORKAREA/regression/<dut>/<listfile>.latest/<listname>.rpt
```

**Example:**
```bash
lsti -r $WORKAREA/regression/pie/level0.list.latest/level0.rpt
```

### Test Status Values

- **Waiting** - Test is queued in Netbatch, waiting to start
- **Running** - Test is currently executing
- **Pass** - Test completed successfully
- **Fail** - Test failed

### Monitoring Workflow

1. **Submit tests** (returns immediately):
   ```bash
   simregress -l $WORKAREA/reglist/pie/level0.list -flow vcssim -dut pie -net -P zsc10_normal -Q /ddg/ip/fe/rtl -C "SLES15&&12G"
   ```

2. **Check progress periodically** using `lsti -r`:
   ```bash
   lsti -r $WORKAREA/regression/pie/level0.list.latest/level0.rpt
   ```

3. **Poll regularly** until all tests complete (status changes from "Waiting" or "Running" to "Pass" or "Fail")

4. **Be patient** - Wait for all tests to finish before analyzing results. Do not interrupt long-running test executions.

### Reading lsti Output

The `lsti` output shows:
- **Test Name** - Unique test identifier
- **Status** - Current execution state
- **Cycles** - Simulation cycle count (when available)
- **Summary** - Total/Pass/Fail counts and pass percentage

## Output Directory Structure

Simregress creates a structured output directory for each regression run under `$WORKAREA/regression/<dut>/`.

### Directory Naming and Versioning

Each regression run creates a timestamped directory:
```
$WORKAREA/regression/<dut>/<listname>      # First run
$WORKAREA/regression/<dut>/<listname>.1    # Second run
$WORKAREA/regression/<dut>/<listname>.2    # Third run
...
$WORKAREA/regression/<dut>/<listname>.latest    # Symlink to most recent run
```

**Example:**
```bash
regression/pie/
├── level0.list/           # First run
├── level0.list.1/         # Second run
└── level0.list.latest@    # Symlink → level0.list.1
```

Always use `.latest` to reference the most recent run directory.

### Top-Level Files in Run Directory

The main regression directory (`<listname>.latest/`) contains:

#### Summary Files
- **`level0.rpt`** - Main regression report file (used by `lsti -r`)
- **`level0.pass`** - Expanded command lines for all passing tests
- **`level0.fail`** - Expanded command lines for all failing tests

### Individual Test Run Directories

Each test that runs (especially **failed tests**) retains its own directory:

```
$WORKAREA/regression/<dut>/<listname>.latest/<test_unique_name>/
```

**Example:**
```
regression/pie/level0.list.latest/pie_hello_world_test/
```

### Using .pass and .fail Files

The `.pass` and `.fail` files contain the full expanded command line for each test:

**View passing test commands:**
```bash
cat $WORKAREA/regression/<dut>/<listname>.latest/<listname>.pass
```

**View failing test commands:**
```bash
cat $WORKAREA/regression/<dut>/<listname>.latest/<listname>.fail
```

Each line shows:
- Test ID
- Full path to test script
- All command-line arguments
- Simulation options
- Test-specific plusargs and configuration

**Example line from `.fail` file:**
```
1000 /path/to/pie_hello_world_test -dut pie -flow vcssim -seed 1000 -simv_args +UVM_NO_RELNOTES -simv_args- -timeout 5us ...
```

This is useful for:
- **Re-running individual tests** locally for debug
- **Understanding test configuration** and options
- **Reproducing failures** outside of simregress

### Debugging Failed Tests

For failed tests, the test run directory is preserved with all logs and artifacts. Debug in this order:

1. **Check pass/fail status:**
   ```bash
   ls $WORKAREA/regression/<dut>/<listname>.latest/<test_name>/<test_name>.{pass,fail}
   ```

2. **Check postsim.log (post-processing checkers first):**
   ```bash
   cd $WORKAREA/regression/<dut>/<listname>.latest/<test_name>/
   cat postsim.log
   ```
   This shows post-test validation failures (error patterns, assertion checks, coverage issues).

3. **Check logbook.log (complete test execution log):**
   ```bash
   cat logbook.log
   ```
   This contains the complete test output, including all stages of execution.

4. **Check jestr.log (simulation execution):**
   ```bash
   cat jestr.log
   ```
   This shows simulation runtime output and execution details.

5. **Open waveforms (if available):**
   ```bash
   runverdi &
   ```

6. **Get test command for local re-run:**
   ```bash
   grep "^<test_id>" ../level0.fail
   ```

## Identifying Individual Tests

Individual tests can be identified in two ways:

### Method 1: From Regression List Files

Test names are defined directly in the regression list files under `reglist/`:

```bash
cat $WORKAREA/reglist/<dut>/<listfile>
```

Each line has the format:
```
<test_id> <test_name> [options] -seed <seed>
```

Example from `reglist/pie/level0.list`:
```
1000 pie_hello_world_test -dut pie -model pie -seed 1000
1001 pie_ral_creg_test -dut pie -model pie -seed 1001
1002 pie_command_buffer_doa_test -dut pie -model pie -seed 1002 -simv_args +PIE_TESTCASE=1 -simv_args- -dirtag MEMSS_PMA
```

- **Test ID**: First column (1000, 1001, 1002, ...)
- **Test Name**: Second column (pie_hello_world_test, pie_ral_creg_test, ...)
- **Unique Name**: Test name + dirtag when present (e.g., pie_command_buffer_doa_test_MEMSS_PMA)

Important: The test command lines from reglist files are not fully expanded, so they may not be runnable directly due to options added over many lines of the reglist files. Prefer using the expanded command lines from simregress no_run mode described below or the .pass/.fail file from a test run directory.

### Method 2: From Expanded No-Run Output

Generate the expanded test list without running:

```bash
simregress -l $WORKAREA/reglist/<dut>/<list> -flow <flow> -dut <dut> -no_run 
```

This creates:
```
$WORKAREA/regression/<dut>/<listfile>/<listname>.list.no_run
```

Each line shows the full `trex` command with:
- Test ID and name
- All expanded arguments
- Unique test name (via `-uniq_test_name`)
- Full simulation options

**View the expanded tests:**
```bash
cat $WORKAREA/regression/<dut>/<listfile>.latest/<listname>.list.no_run
```

**Example line:**
```
trex  1002   pie_command_buffer_doa_test   -timeout 5us ... -simv_args +PIE_TESTCASE=1 +PIE_MEMSS_PMA_CR_WRITE=1 -simv_args- -dirtag MEMSS_PMA -seed 1002 ... -uniq_test_name pie_command_buffer_doa_test_MEMSS_PMA
```

This is useful for:
- **Understanding test intent** - Arguments reveal modes and stimulus options (e.g., `+PIE_TESTCASE=1`, `+PIE_MEMSS_PMA_CR_WRITE=1`)
- Seeing the exact command that will run for each test
- Debugging test arguments and options
- Identifying unique test names (especially when dirtags are used)

## Running Individual Tests with Trex

Once you've identified a test (using the methods above), you can run it individually using `trex` without going through simregress. This is useful for quick debug iterations, testing specific scenarios, or investigating failures.

### Command Format

```bash
trex <test_name> -dut <dut> -model <model> -seed <seed> [OPTIONS]
```

**Important:** If you see a `-mpp` flag in the test command line, this indicates the test requires the **vcssimmpp** (Multi-Partition Parallel) flow instead of vcssim. You must build vcssimmpp before running such tests:

```bash
grdlbuild vcssimmpp
```

Tests without the `-mpp` flag use the standard vcssim flow:

```bash
grdlbuild vcssim
```

### Getting the Command Line

You can obtain the full command line for a test from several sources:

1. **From simregress .pass or .fail files** (after a regression run):
   ```bash
   # View command for a specific test ID
   grep "^1000" $WORKAREA/regression/pie/level0.list.latest/level0.pass
   ```

2. **From trex .pass or .fail files** (after a trex run):
   ```bash
   # View command from a previous trex run
   cat $WORKAREA/regression/pie/trex/pie_hello_world_test/pie_hello_world_test.fail
   ```

3. **From regression list files** (reglist directory):
   ```bash
   # Copy the test line from reglist/pie/level0.list
   # Example: pie_hello_world_test -dut pie -model pie -seed 1000
   ```

4. **Manual construction** with minimal required arguments:
   ```bash
   trex <test_name> -dut <dut> -model <model> -seed <seed>
   ```

### Basic Examples

**Run a simple test:**
```bash
trex pie_hello_world_test -dut pie -model pie -seed 1000
```

**Run with FSDB waveform generation:**
```bash
trex pie_hello_world_test -dut pie -model pie -seed 1000 -fsdb
```

**Run with test-specific options:**
```bash
trex pie_command_buffer_doa_test -dut pie -model pie -seed 1002 \
  -simv_args +PIE_TESTCASE=1 +PIE_MEMSS_PMA_CR_WRITE=1 -simv_args- \
  -dirtag MEMSS_PMA
```

### FSDB Waveform Generation

The `-fsdb` flag enables waveform dumping for debug:

```bash
trex <test_name> -dut <dut> -model <model> -seed <seed> -fsdb
```

**What it does:**
- Generates an FSDB waveform file in the test run directory
- Essential for waveform-based debugging

**Example FSDB file:**
```bash
# After running with -fsdb:
ls $WORKAREA/regression/<dut>/trex/<test_name>/*.fsdb
# Output: pie_tb.fsdb (226KB or larger depending on simulation length)
```

### Output Location

Trex creates test output under:
```
$WORKAREA/regression/<dut>/trex/<test_name>/
```

**Example:**
```bash
$WORKAREA/regression/pie/trex/pie_hello_world_test/
```

### Files Generated in Test Directory

Each trex run creates a directory containing:

#### Key Files
- **`<test_name>.pass`** or **`<test_name>.fail`** - Full expanded command line and test result
- **`<test_name>.rpt`** - Test report file with execution details
- **`<test_name>.trex`** - Trex-specific metadata

#### Logs
- **`jestr.log`** - Main simulation execution log
- **`logbook.log`** - Complete test execution log
- **`postsim.log`** - Post-simulation processing log

### Identifying Pass/Fail Status

The **most reliable** way to check test results is by looking for the `.pass` or `.fail` file. Trex creates exactly one of these files based on the final result after all post-processing checkers have run.

#### Primary Method: Check for .pass or .fail File

```bash
# List to see which file exists:
ls $WORKAREA/regression/<dut>/trex/<test_name>/<test_name>.{pass,fail} 2>/dev/null
```

**If test passed:**
```bash
# This file exists:
$WORKAREA/regression/<dut>/trex/<test_name>/<test_name>.pass
```

**If test failed:**
```bash
# This file exists:
$WORKAREA/regression/<dut>/trex/<test_name>/<test_name>.fail
```

**Quick check command:**
```bash
cd $WORKAREA/regression/<dut>/trex/<test_name>
if [ -f <test_name>.pass ]; then echo "PASSED"; else echo "FAILED"; fi
```

#### Debugging Failures: Log Inspection Order

When a test fails, investigate in this order:

**1. Check postsim.log first (post-processing checkers):**
```bash
cat $WORKAREA/regression/<dut>/trex/<test_name>/postsim.log
```

This log contains output from post-processing checkers (post_test_manager) that validate simulation results.

**2. Check logbook.log (complete test execution log):**
```bash
cat $WORKAREA/regression/<dut>/trex/<test_name>/logbook.log
```

This log contains the complete test output, including all stages of execution.

**3. Check jestr.log (simulation execution):**
```bash
cat $WORKAREA/regression/<dut>/trex/<test_name>/jestr.log
```

This log shows:
- Simulation command execution
- Runtime simulation output
- Final PASS/FAIL determination
- Simulation statistics (cycles completed, runtime, etc.)

**4. Check terminal output (real-time feedback):**

At the end of the trex run, the terminal displays:
```
PASS/FAIL: PASS
RPT: TEST RESULTS: PASS/FAIL: PASS  RETURN : 0
```

**5. Use exit code in scripts:**
```bash
if trex pie_hello_world_test -dut pie -model pie -seed 1000; then
    echo "Test PASSED"
else
    echo "Test FAILED (check postsim.log, logbook.log, then jestr.log)"
fi
```

### Viewing Results

**Check test status (quick):**
```bash
ls $WORKAREA/regression/<dut>/trex/<test_name>/<test_name>.{pass,fail} 2>/dev/null
```

**View expanded command line:**
```bash
cat $WORKAREA/regression/<dut>/trex/<test_name>/<test_name>.pass   # If passed
# or
cat $WORKAREA/regression/<dut>/trex/<test_name>/<test_name>.fail   # If failed
```

**View simulation log:**
```bash
cat $WORKAREA/regression/<dut>/trex/<test_name>/jestr.log
```

**Open waveforms (if FSDB generated):**
```bash
cd $WORKAREA/regression/<dut>/trex/<test_name>
runverdi &
```

### When to Use Trex vs Simregress

**Use trex for:**
- Quick single-test debug iterations
- Investigating specific test failures discovered in simregress runs
- Testing configuration changes on a small subset of tests
- Local execution without Netbatch overhead
- Generating waveforms for specific tests

**Use simregress for:**
- Running full regression suites
- Gating checks before code submission
- Parallel execution across many tests on Netbatch
- Automated regression tracking and reporting

### Common Workflow

1. **Run regression with simregress** to identify failures
2. **Locate failed test command** in `.fail` file
3. **Run test locally with trex** adding `-fsdb` for waveforms
4. **Debug using waveforms and logs** in the trex output directory
5. **Iterate fixes** by re-running with trex
6. **Verify fix** by running full regression with simregress again
