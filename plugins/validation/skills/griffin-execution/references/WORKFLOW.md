# Griffin Execution Workflow Details

## Step-by-Step Instructions

### Step 1: Navigate to Test Area

**Action**: Change to the test directory containing simulation outputs

```bash
cd <TEST_AREA>
```

**Verify**:
- `jestr.log` or `jestr.log.gz` exists
- `jem/` directory exists
- `opera_output/` directory exists

### Step 2: Prepare Required Files

**Action**: Decompress files if compressed

```bash
# Check if compressed
ls -la jestr.log*
ls -la jem/

# Decompress if needed
gunzip jestr.log.gz
gunzip jem/*.gz
```

**Skip if**: Files already uncompressed

### Step 3: Extract Griffin Command

**Action**: Locate command from previous execution logs

**Path**: `<TEST_AREA>/opera_output/logs/griffin_<agent_name>.log`

**Example agents**:
- `griffin_cfi_protocol_checker.log`
- `griffin_coverage_collector.log`
- `griffin_performance_monitor.log`

**Extract command**:
```bash
# List available agent logs
ls opera_output/logs/griffin*

# Read command (usually near start of log)
head -100 opera_output/logs/griffin_<agent>.log | grep -A5 "command\|Command\|COMMAND"
```

### Step 4: Execute Griffin Agent

**Action**: Run the extracted command

**Command template**:
```bash
griffin [agent_options] -input <files> -output <report_dir> [flags]
```

**Common flags**:
- `-verbose`: Detailed output
- `-agent <name>`: Specific agent
- `-report <path>`: Report location
- `-config <file>`: Config file

**Execution**:
```bash
# Run synchronously (most Griffin agents complete quickly)
<extracted_griffin_command>
```

### Step 5: Review Results

**Check terminal output**:
- Overall PASS/FAIL status
- Violation count
- Error messages

**Check report files**:
```bash
# List generated reports
ls -la opera_output/reports/

# Read summary
cat opera_output/reports/<agent>_summary.txt
```

## Common Agent Types

| Agent Type | Purpose | Output |
|------------|---------|--------|
| Protocol Checker | Verify protocol compliance | Violations list |
| Coverage Collector | Process coverage data | Coverage report |
| Performance Monitor | Analyze latency/throughput | Performance metrics |
| Assertion Checker | Review assertion activity | Assertion summary |

## Troubleshooting

### Files Not Found
```bash
# Check if test completed
ls -la <TEST_AREA>/
# Check for compressed files
find . -name "*.gz" -type f
```

### Griffin Command Missing
```bash
# Search all logs for griffin
grep -r "griffin" opera_output/logs/
# Check if opera ran
ls -la opera_output/
```

### Permission Errors
```bash
# Check file permissions
ls -la jestr.log jem/
# Make readable if needed
chmod -R u+r jem/
```

## Output Format Example

```
🔧 Griffin Execution:

📂 Test Area: /path/to/test
🎯 Agent: cfi_protocol_checker

📝 Command:
cd /path/to/test
gunzip jestr.log.gz jem/*
griffin -agent cfi_checker -input jem/ -verbose

📊 Results:
Status: PASS
Violations: 0
Warnings: 2

📄 Reports: opera_output/reports/cfi_checker_report.html
```
