# Griffin Agent Integration Details

## Step 1: Gather Agent Requirements

**Questions to clarify**:

1. **Agent name**: What should the agent be called?
   - Follow pattern: `<module>_<feature>_chk` or `<module>_<feature>_cov`
   - Example: `d2d_sb_fuzz_chk`, `d2d_clk_req_checker_chk`

2. **Agent type**: 
   - `--chk` for checker (validates correctness)
   - `--cov` for coverage (collects metrics)
   - Both for combined agent

3. **DUT name**: Module being validated
   - Example: `d2d`, `fdi`, `cfi`

4. **Purpose**: What feature/protocol to validate?

## Step 2: Navigate to WORKAREA

```bash
cd $WORKAREA

# Verify structure
ls -la src/val/griffin/agents/
ls -la cfg/opera/griffin/
ls -la src/val/griffin/logdb_cfg/
```

**Expected paths**:
- `$WORKAREA/src/val/griffin/agents/` - Agent Python files
- `$WORKAREA/cfg/opera/griffin/build.gradle.kts` - Build config
- `$WORKAREA/src/val/griffin/logdb_cfg/griffin_ptm_generate.py` - PTM config

## Step 3: Create Agent with Scaffold Script

**Command**:
```bash
python <GRIFFIN_REPO>/scripts/new_collateral/create_new_agent.py \
  --user_name <YOUR_IDSID> \
  --dut <DUT_NAME> \
  --agent_name <AGENT_BASE_NAME> \
  --griffin_dir $WORKAREA/src/val/griffin \
  --chk
```

**Example for d2d_sb_fuzz_chk**:
```bash
python $GRIFFIN_REPO/scripts/new_collateral/create_new_agent.py \
  --user_name johndoe \
  --dut d2d \
  --agent_name d2d_sb_fuzz \
  --griffin_dir $WORKAREA/src/val/griffin \
  --chk
```

**Generated files**:
- `src/val/griffin/agents/d2d_sb_fuzz_chk.py` - Main agent code
- Supporting config files

## Step 4: Implement Validation Logic

**Edit generated file**:
```python
# src/val/griffin/agents/<agent_name>.py

class <AgentName>Agent:
    def __init__(self, config):
        # Initialize agent
        pass
    
    def validate(self, transaction):
        # Add validation logic here
        # Return True for pass, False for fail
        pass
    
    def report(self):
        # Generate validation report
        pass
```

## Step 5: Add to Opera Build (build.gradle.kts)

**File**: `$WORKAREA/cfg/opera/griffin/build.gradle.kts`

**Add to griffinAgents list**:
```kotlin
val griffinAgents = listOf(
    // Existing agents...
    "d2d_protocol_chk",
    "d2d_coverage_cov",
    // Add new agent
    "d2d_sb_fuzz_chk"  // <-- Add here
)
```

## Step 6: Add to PTM Execution (griffin_ptm_generate.py)

**File**: `$WORKAREA/src/val/griffin/logdb_cfg/griffin_ptm_generate.py`

**Add agent to command list**:
```python
GRIFFIN_AGENTS = [
    # Existing agents...
    "d2d_protocol_chk",
    # Add new agent
    "d2d_sb_fuzz_chk",  # <-- Add here
]
```

## Step 7: Build and Verify

```bash
# Build with grdlbuild
grdlbuild griffin

# Verify agent appears in build output
ls -la $WORKAREA/build/griffin/agents/

# Run on a test to verify
cd <TEST_AREA>
griffin -agent d2d_sb_fuzz_chk -input jem/ -verbose
```

## Troubleshooting

### Script Not Found
```bash
# Verify GRIFFIN_REPO is set
echo $GRIFFIN_REPO

# Or find script location
find /path/to/repos -name "create_new_agent.py"
```

### Build Errors
```bash
# Clean and rebuild
grdlbuild clean
grdlbuild griffin

# Check for syntax errors in agent file
python -m py_compile src/val/griffin/agents/<agent>.py
```

### Agent Not Running
```bash
# Verify agent in PTM config
grep "<agent_name>" src/val/griffin/logdb_cfg/griffin_ptm_generate.py

# Check opera logs
cat opera_output/logs/griffin_<agent>.log
```

## Output Format

```
🔧 Griffin Agent Setup:

📋 Agent: d2d_sb_fuzz_chk
📁 Type: Checker
🎯 DUT: d2d

📝 Created Files:
- src/val/griffin/agents/d2d_sb_fuzz_chk.py

📝 Integration:
- Added to cfg/opera/griffin/build.gradle.kts
- Added to src/val/griffin/logdb_cfg/griffin_ptm_generate.py

🔨 Next Steps:
1. Implement validation logic in agent file
2. Build: grdlbuild griffin
3. Test: Run on sample test
```
