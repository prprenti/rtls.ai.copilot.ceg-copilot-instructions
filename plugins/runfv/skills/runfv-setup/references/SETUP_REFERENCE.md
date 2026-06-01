# RunFV Setup Reference

Use this reference after activating the `runfv-setup` skill.

**Related skills:** `sva-properties`, `proof-debug`, `jg-cmd`

---

## Complete Workflow (Phases 1-5)

### PHASE 1: Pre-Creation Check

**Step 1: Check proofs_container.csv**
```bash
grep "<proof_name>" $WORKAREA/src/val/tb/fpv/proofs_container.csv
```

**Step 1.a:** If proof EXISTS for same RTL top:
- Inform user that proof already exists
- Wait for user's next instruction
- **DO NOT run RunFV API**

**Step 1.b:** If proof DOES NOT exist:
1. Extract `proof_dir` from proofs_container.csv (typically: `$WORKAREA/src/val/tb/fpv`)
2. Extract `lib` from proofs_container.csv (typically: `{dut_name}_ip_lib`)
3. Extract `dut` from `$CLUSTER_NAME` environment variable
4. Set `proof_name` = top RTL module name provided by user

**Step 1.c:** Present to user and confirm:
```
Extracted values:
- dut = <extracted_dut>
- proof_name = <extracted_proof_name>
- proof_dir = <extracted_proof_dir>
- lib = <extracted_lib>

Please confirm if correct before proceeding to Phase 2.
```

### PHASE 2: Proof Creation

**Step 1: Execute RunFV Command**
```bash
cd $WORKAREA
run_fv create-proof -dut <dut> -p <proof_name> -t <proof_name> -w <proof_dir> -l <lib> -f fpv
```

**CRITICAL:**
- `-f fpv` is FIXED (never change)
- `-dut` uses cluster name (e.g., `<cluster>`), NOT library name (e.g., `<cluster>_ip_lib`)
- `-p` and `-t` use same value (proof_name = top module name)

**Generated Structure:**
```
<proof_dir>/<proof_name>/
├── cfg/
│   ├── fv_<proof>_conf.tcl
│   ├── fv_<proof>_global_prune.tcl
│   ├── fv_<proof>_pis.tcl
│   └── fv_<proof>_setup.tcl
└── src/
    ├── fv_<proof>_top.va
    ├── fv_<proof>_map.va
    ├── fv_<proof>_spec.va
    ├── fv_<proof>_assert.va
    ├── fv_<proof>_assume.va
    └── fv_<proof>_cover.va
```

### 🛑 MANDATORY CHECKPOINT BEFORE PHASE 3 🛑

**STOP! Complete this checklist:**

1. **COUNT PHASE 3 STEPS**
   - Phase 3 has exactly 6 STEPS
   - Step 1: conf.tcl
   - Step 2: global_prune.tcl
   - Step 3: pis.tcl
   - Step 4: map.va
   - Step 5: Properties (SKIP - handled by runfv_verify follow-on workflow)
   - Step 6: Filelist

2. **VERIFY SYNTAX REQUIREMENTS**
   - Clock needs -both_edges flag
   - Reset uses ~ for active-low (_b/_n suffix)
   - Extract ALL clocks and ALL resets

3. **READ RTL MODULE COMPLETELY**
   - Extract ALL input ports
   - Identify ALL clocks
   - Identify ALL resets
   - Verify every signal exists before using

### PHASE 3: Proof Configuration (6 Steps)

**Step 1: Update fv_<proof>_conf.tcl**

🛑 **MANDATORY: Read RTL First**

```bash
# Find RTL file
find $WORKAREA/src/<cluster>/rtl -name "*<module>*.sv" -o -name "*<module>*.vs"

# Read module declaration
# Extract ALL ports (input/output)
# Identify clocks (clk, clock, ck*)
# Identify resets (rst, reset, *_b, *_n)
```

**Clock Configuration:**
```tcl
# ALWAYS add -both_edges flag to EVERY clock
clock -clear
clock <clock_name1> -both_edges
clock <clock_name2> -both_edges

# EXCLUDE from clocks (these are NOT clocks):
# - Signals with 'gate', 'gated' (e.g., clk_gate_b, fscan_clkungate)
# - Signals with '_en', '_enable' (e.g., clk_en, clock_enable)
# - Signals with 'bypass' (e.g., clk_bypass)
```

**Reset Configuration:**
```tcl
# Combine ALL resets in ONE expression with single braces
reset -clear
reset -expression { <reset1> <reset2> <reset3> }

# Polarity Rules (look at port NAME only):
# - Port ends with _b or _n → Use ~port_name
# - Port has NO _b/_n suffix → Use port_name as-is

# Examples:
# rst_b → ~rst_b
# reset_n → ~reset_n
# rst → rst
# sva_reset → sva_reset

# Multiple resets example:
reset -expression { ~rst_b reset sva_reset }
```

🛑 **CRITICAL Syntax:**
- **ALWAYS use braces `{ }` around reset expression**
- **NEVER use multiple separate reset lines**
- **ONE expression with ALL resets space-separated**
- **⚠️ NO COMMENTED LINES inside braces `{ }`** — Comments inside braces cause Tcl parse errors
  - ❌ `reset -expression { ~rst_b  # reset # reset_n }`
  - ✅ `reset -expression { ~rst_b reset_n }`
- **⚠️ SIGNAL NAMES ARE CASE-SENSITIVE in TCL files**
  - `Qclk` ≠ `qclk` ≠ `QClk`
  - Always verify exact case from RTL port declarations
  - Example: `clock qclk -both_edges` (not `Qclk`)

**Step 2: Update fv_<proof>_global_prune.tcl**

Search RTL for scan/VISA signals:
```systemverilog
// VISA signals: visa_*
// Scan signals: fscan_*
```

Add assumptions:
```tcl
# VISA Enable
assume -env -name global_prune_visa_enabled { visa_enabled == '0 }

# Scan Interface
assume -env -name global_prune_fscan_mode { fscan_mode == '0 }
assume -env -name global_prune_fscan_shiften { fscan_shiften == '0 }
assume -env -name global_prune_fscan_clkungate { fscan_clkungate == '0 }

# Active-low scan signals (_b suffix)
assume -env -name global_prune_fscan_byprst_b { fscan_byprst_b == 1'b1 }
```

**Step 3: Update fv_<proof>_pis.tcl**

Add commented parameter override examples:
```tcl
# Parameter Overrides (OPTIONAL - user can uncomment as needed)
# -parameter <param_name> <value>
# -parameter BUFFER_SIZE 8
# -parameter ENC_GRAY 1

# Black-boxing (OPTIONAL - user can uncomment as needed)
# -bbox_m <module_name>
# -bbox_i <instance_path>
```

**Step 4: Update fv_<proof>_map.va**

🛑 **CRITICAL: Uncomment `define FV_DUT FIRST**

```systemverilog
// Step 0: MUST DO FIRST
`define FV_DUT <actual_module_name>

// Step 1: Map clocks and resets (ACTIVE - uncommented)
logic clk;
logic rst;

assign clk = `FV_DUT.<clock_signal>;
assign rst = ~`FV_DUT.<reset_signal_b>;  // Use ~ for active-low

// Step 2: Add FUNCTIONAL signals as COMMENTED
// ⚠️ EXCLUDE visa_* and fscan_* (already pruned in global_prune.tcl)

//logic sig1;
//logic sig2;
//assign sig1 = `FV_DUT.<rtl_sig1>;
//assign sig2 = `FV_DUT.<rtl_sig2>;
```

**Reset Polarity Rules:**
```systemverilog
// Properties expect ACTIVE-HIGH reset (rst=1 means "in reset")
// If RTL reset is ACTIVE-LOW, apply ~ inversion

// Port: rst_b → map.va: assign rst = ~`FV_DUT.rst_b;
// Port: reset_n → map.va: assign rst = ~`FV_DUT.reset_n;
// Port: rst → map.va: assign rst = `FV_DUT.rst;
```

**Self-Check:**
- ✓ Only clk/rst declarations are uncommented?
- ✓ Only clk/rst assigns are uncommented?
- ✓ ALL other signals are commented with //?
- ✓ NO visa_* or fscan_* signals in map.va?

**Step 5: Develop Properties (Generic Rules)**

Property authoring is covered in **Phase 4** below. For advanced property strategies, use the `sva-properties` skill.

**Step 6: Update Cluster Filelist**

File: `filelists/val/<cluster_name>_fpv_lib.f`

Add two entries:
```
# Property files section
$VAR/src/val/tb/fpv/<proof_name>/src/fv_<proof_name>_top.va

# Include directories section
+incdir+$VAR/src/val/tb/fpv/<proof_name>/src/
```

Where `$VAR` must match the existing filelist style (`$ip` or `$WORKAREA`).

🛑 **Filelist edit rules (MANDATORY):**
- Add each entry on a **new line** only.
- Never concatenate two `+incdir+` entries on one line.
- Never concatenate two file path entries on one line.
- Preserve neighboring formatting style (prefix variable, slash style, ordering).

Quick check after edit:
```bash
grep -n "<proof_name>\|+incdir+" $WORKAREA/filelists/val/<cluster_name>_fpv_lib.f
```

### Phase 3 Completion Verification

**MANDATORY: State completion with specifics:**

```
Phase 3 Complete - All 6 steps finished:
 ✓ Step 1: conf.tcl - Clock (list clocks) and Reset (list resets) configured + prove -bg -all at end
 ✓ Step 2: global_prune.tcl - Scan/VISA signals pruned
 ✓ Step 3: pis.tcl - Parameter override examples added
 ✓ Step 4: map.va - Signal mappings (clk/rst active, X functional commented, all DUT macros defined)
 ✓ Step 5: Properties - handed off to Phase 4 (Generic Property Authoring)
 ✓ Step 6: Filelist - <cluster>_fpv_lib.f updated
 ✓ Verification: No duplicate content found in any created file
```

🛑 **POST-CREATION DUPLICATE CHECK (MANDATORY):**
After creating ALL files, verify no file has duplicate content:
```bash
grep -c "^//  File" src/val/tb/fpv/<proof>/src/*.va
# Each MUST be 1. If count > 1, the file has duplicate content — keep the comprehensive version only.
```
**PREVENTION:** Never write a file twice. Never write a skeleton then append a full version. Decide final content BEFORE calling create_file.
If duplicates found: for `.va` files keep the more comprehensive (second) version; for `.tcl` files keep the first version.

### PHASE 4: Generic Property Authoring

Use RTL as single source of truth. For every property, first identify the exact RTL equation or protocol intent, then write the property against mapped signals.

**Step 1: Assumptions (`*_assume.va`)**
- Constrain only environment inputs, not DUT outputs/internal derived signals unless explicitly modeling legal protocol behavior.
- Prefer stability assumptions for configuration/control registers that are programmed out-of-band.
- Add legality assumptions for threshold/range fields (for example, non-zero limits, reserved count less than max count).
- Add mutual-exclusion assumptions for competing winner/grant interfaces where arbitration guarantees onehot/onehot0.
- Keep assumptions realistic and minimal; avoid over-constraining behavior that DUT logic must prove.

Template examples:
```systemverilog
`FPV_<CLUSTER>_ASSUMES_TRIGGER(ASM_<PROOF>_<NAME>,
                           <trigger>,
                           <property>,
                           posedge clk, rst, `FPV_<CLUSTER>_ERR_MSG("<message>"));
```

**Step 2: Assertions (`*_assert.va`)**
- Assert RTL combinational equations directly (increment/decrement equations, next-state equations, threshold equations).
- Assert sequential alignment for flopped outputs using `$past(...)`.
- Assert implications/ordering that must always hold (for example, stricter block implies broader block).
- Keep assertions local and explain intent in error text.

Template examples:
```systemverilog
`FPV_<CLUSTER>_ASSERTS_TRIGGER(AST_<PROOF>_<NAME>,
                           <trigger>,
                           <property>,
                           posedge clk, rst, `FPV_<CLUSTER>_ERR_MSG("<message>"));
```

**Step 3: Covers (`*_cover.va`)**
- Add reachability covers for key activity signals (inc/dec, grant/valid, state transitions).
- Add boundary covers around threshold edges (equal to max, max-1, first block assertion).
- Add both combinational and flopped output visibility when block/credit logic is pipelined.
- Keep covers concise and targeted to bring-up and convergence diagnostics.

Template examples:
```systemverilog
`FPV_<CLUSTER>_COVERS(COV_<PROOF>_<NAME>,
                  <cover_expression>,
                  posedge clk, rst,);
```

**Property Authoring Checklist (Mandatory)**
- Verify all signal names and case directly from RTL (`qclk` vs `Qclk` are different).
- Ensure reset polarity is mapped consistently (`rst = ~rst_b` for active-low RTL resets).
- **🚨 ALWAYS terminate every `FPV_*` macro invocation with a semicolon (`;`).** The macros expand to concurrent assertion statements that require `;` in SystemVerilog. Missing semicolons cause Jasper `VERI-1137` syntax errors on the *next* macro (misleading location).
  - ❌ `` `FPV_IBECC_ASSERTS_TRIGGER(name, trig, prop, posedge clk, rst, `FPV_IBECC_ERR_MSG("msg")) ``
  - ✅ `` `FPV_IBECC_ASSERTS_TRIGGER(name, trig, prop, posedge clk, rst, `FPV_IBECC_ERR_MSG("msg")); ``
- Do not put commented tokens inside TCL braces `{}` (parser-sensitive).
- Keep map.va signal namespace consistent using one DUT macro (for example, `` `define FV_DUT <module> ``).
- Add no more than necessary constraints before assertions; tighten only after seeing inconclusive traces.

For advanced property strategies, use the `sva-properties` skill.

### PHASE 5: Build and Load Proof

Provide instructions:
```bash
# Step 1: Create output directory
mkdir -p $WORKAREA/output/formal
cd $WORKAREA

# Step 2: Build proof
run_fv build-proof -dut <cluster_name> -p <proof_name>

# CRITICAL: -dut uses cluster name, NOT library name
# Example: -dut <cluster> (not <cluster>_ip_lib)

# Step 3: Load proof (opens JasperGold GUI)
run_fv load-proof -dut <cluster_name> -p <proof_name>

# Step 4: Run the proof (in the Jasper TCL console)
prove -bg -all
```

#### Environment Prerequisites

Before running `run_fv build-proof` or `run_fv load-proof`, the CTH environment **must** be sourced:
```bash
cd $WORKAREA
source /p/hdk/bin/cth_psetup -p ddgcth/1.13 -cfg ddgip -read_only
```

Failure to source this environment results in:
```
ERROR: Could not find value for 'run_fv_exec' or 'run_fv_path' in [PARAMS] section!
```

#### Jasper GUI Session Management

🛑 **NEVER open a duplicate JasperGold GUI for the same proof.**

Before launching `run_fv load-proof`, ALWAYS check if a session already exists:
```bash
# Check for active lock files
find $WORKAREA/output/formal/<proof_name>/compile/jgproject -name "*.lock" 2>/dev/null
```

- If a `.lock` file exists and the owning process is still running → **reuse the existing GUI session**
- If the `.lock` file is stale (owning process dead) → remove the lock, then load:
  ```bash
  rm -f $WORKAREA/output/formal/<proof_name>/compile/jgproject/*.lock
  run_fv load-proof -dut <cluster> -p <proof_name>
  ```

#### Running Proofs in the Jasper Console

When the user asks to "run the proof", the command to execute in the **Jasper TCL console** is:
```tcl
prove -bg -all
```

This runs all assertions, assumptions, and covers in the background. The `run_fv load-proof` command opens an interactive GUI — TCL commands cannot be piped from the terminal.

---

## Common FPV Infrastructure

### Filelists Structure

**Location:** `$WORKAREA/filelists/val/`

**Key Files:**
- `<cluster>_fpv_lib.f` - Main FPV library filelist
- `<cluster>_fpv_lib_opts.f` - Compilation options
- `global_opts.f` - Global options

### Intel Checkers Library

**Location:** `$WORKAREA/src/val/tb/fpv/intel_checkers/`

**Key Files:**
- `fv_{CLUSTER}_sva_library_pkg.vs` - Package definitions
- `fv_{CLUSTER}_intel_checkers_core.vs` - Core checker macros

### Proof Registry

**File:** `$WORKAREA/src/val/tb/fpv/proofs_container.csv`

**Format:**
```
proof_name,proof_dir,top,lib,flow,proof_registration
<cluster>,src/val/tb/fpv,<cluster>,<cluster>_ip_lib,fpv,REGISTERED
```

---

## Configuration Modularization

For complex proofs, split configuration into modular TCL files. This pattern scales to multi-hierarchy, multi-domain proofs (arbiters, bridges, multi-module designs).

### Standard File Split

```
<proof_name>/cfg/
├── fv_<proof>_conf.tcl           # Clock, reset, task setup, include directives
├── fv_<proof>_pis.tcl            # Analyze/elaborate flags, parameter overrides
├── fv_<proof>_init_prune.tcl     # Reset-phase constraints (active during reset)
├── fv_<proof>_verify_prune.tcl   # Post-reset constraints (active after reset)
├── fv_<proof>_global_prune.tcl   # Global assumptions (scan/VISA/debug isolation)
└── reset.seq                     # Optional: reset sequence file for complex resets
```

### Responsibility Split

| File | Purpose | When to Modify |
|------|---------|---------------|
| `*_conf.tcl` | Clock/reset declarations, task creation, include directives | Adding clocks, changing reset, creating tasks |
| `*_pis.tcl` | `ANALYZE_OPTS`, `ELAB_OPTS`, parameter overrides, black-boxing | Compilation errors, adding defines, black-boxing modules |
| `*_init_prune.tcl` | Constraints active **during reset** only | Fixing reset-phase failures |
| `*_verify_prune.tcl` | Constraints active **after reset** only | Fixing post-reset overconstraint |
| `*_global_prune.tcl` | Always-active scan/VISA/debug isolation | Adding new scan/debug signal assumptions |

### Include Pattern in conf.tcl

```tcl
# In fv_<proof>_conf.tcl:
clock -clear
reset -clear

# Clock/reset setup
clock prim0_clk -both_edges
reset -expression { ~rst_b }

# Include phase-specific prunes
include "$::env(WORKAREA)/src/val/tb/fpv/<proof>/cfg/fv_<proof>_init_prune.tcl"
include "$::env(WORKAREA)/src/val/tb/fpv/<proof>/cfg/fv_<proof>_verify_prune.tcl"

# MANDATORY: Auto-run proofs on load
prove -bg -all
```

### Common PIS Patterns (fv_<proof>_pis.tcl)

```tcl
set ANALYZE_OPTS {
    +define+FPV                       # FPV mode identifier
    +define+FPV_RESTRICT              # Enable FPV-specific RTL code
    +define+SVA_LIB_SVA2009           # SVA library mode
    +define+SVA_LIB_COVER_ENABLE      # Coverage tracking
    +define+FPV_LIVENESS              # Enable liveness properties
    +define+INTEL_INST_ON             # Instrumentation
}

set ELAB_OPTS {
    -bbox_m <module_to_blackbox>      # Black-box unneeded modules
    -no_related_covers                # Skip auto-generated covers
    -create_related_covers {precondition late_precondition infinite_precondition witness}
}
```

---

## Namespace Macro Patterns for Signal Mapping

For multi-hierarchy proofs, use `define`-based namespaces in `map.va` to keep signal paths maintainable and DRY.

### Basic Namespace Pattern

```systemverilog
// Define hierarchy macros (single point of change)
`define FV_DUT <module_name>
`define TOP ioc
`define NCI `TOP.iop_nci_top_i
`define RRTRK `TOP.ioc_downstream

// Use macros for all signal mappings
logic clk, rst;
assign clk = `TOP.prim0_clk;
assign rst = `TOP.MPResetF004H;

// Functional signals use namespace macros
logic [7:0] credit_count;
assign credit_count = `NCI.credit_cnt;

logic req_valid;
assign req_valid = `RRTRK.req_vld;
```

### Struct-Typed Signal Mapping (for interface-heavy designs)

```systemverilog
// Import struct types from design package
import nsi_pkg::*;

// Map structured interfaces
t_nsi_data_interface ReqInF230H;
assign ReqInF230H = `TOP.RX_Data1OutF912H;

// Map register banks
iop_regs_bank_registers_t RegBank;
assign RegBank = `TOP.registers;
```

### When to Use Namespace Macros

| Condition | Recommendation |
|-----------|---------------|
| Single-module proof (flat) | Simple `\`define FV_DUT <mod>` is sufficient |
| Multi-hierarchy proof | Define macros per sub-block (`\`define NCI`, `\`define RRTRK`) |
| Interface-heavy designs | Import struct types and use typed assigns |
| Deeply nested signals | Chain macros: `\`define DEEP \`TOP.a.b.c.d` |

---

## Pruning Strategy

Pruning isolates irrelevant logic to help proof convergence. Use a layered approach.

### Global Pruning (always active)

```tcl
# Scan/DFT isolation
assume -env -name global_prune_fscan_mode { fscan_mode == '0 }
assume -env -name global_prune_fscan_shiften { fscan_shiften == '0 }
assume -env -name global_prune_fscan_clkungate { fscan_clkungate == '0 }

# VISA debug isolation
assume -env -name global_prune_visa_enabled { visa_enabled == '0 }

# Active-low scan signals
assume -env -name global_prune_fscan_byprst_b { fscan_byprst_b == 1'b1 }
```

### Selective Enable/Disable Pattern

For proofs with many properties, selectively enable only target property families:

```tcl
# Disable all first
assert -disable *
cover -disable *
assume -disable *

# Enable only this proof's properties
assert -enable *fv_<proof_name>*
cover -enable *fv_<proof_name>*
assume -enable *fv_<proof_name>*

# Disable specific known-broken or deferred properties
assert -disable *T_<cluster>_DEFERRED_*
```

### Overconstraint Sanity Check

Always add an endless-trace cover to detect overconstrained models:

```tcl
# If this cover becomes unreachable, assumptions are too tight
cover -name endless_trace {1'b1}
cover -set_trace_extension $ endless_trace
```

### Environment Assumptions for Overconstraint Debug

Use `-env` flag for assumptions that explicitly isolate unused interfaces:

```tcl
# Document intent: these channels are unused in this proof
assume -env -name OVERCONSTRAINT_No_SB {SbInBus963H == '0}
assume -env -name OVERCONSTRAINT_No_P2P {P2PDataBidVecF210H == '0}
assume -env -name OVERCONSTRAINT_No_CFI_Rx_Link0 {RX_Data0OutF912H == '0}
```

### Layered Pruning Decision Guide

| Layer | File | Scope | Examples |
|-------|------|-------|----------|
| Global | `*_global_prune.tcl` | All properties, always | scan, VISA, debug |
| Init | `*_init_prune.tcl` | During reset only | Power-on constraints |
| Verify | `*_verify_prune.tcl` | After reset only | Steady-state constraints |
| Selective | In `*_conf.tcl` | Per property family | `assert -enable *credit*` |

---

## Error Handling

**Common Mistakes:**

1. **Wrong -dut parameter:**
   - ❌ `run_fv build-proof -dut <cluster>_ip_lib -p proof`
   - ✅ `run_fv build-proof -dut <cluster> -p proof`

2. **Missing -both_edges on clocks:**
   - ❌ `clock ckfifoN1N00`
   - ✅ `clock ckfifoN1N00 -both_edges`

3. **Wrong reset polarity:**
   - ❌ `reset -expression { ~rst }` (when rst has no _b/_n)
   - ✅ `reset -expression { rst }`

4. **Multiple reset expressions:**
   - ❌ `reset -expression { ~rst_b }` then `reset -expression { sva_reset }`
   - ✅ `reset -expression { ~rst_b sva_reset }`

5. **Uncommenting all signals in map.va:**
   - ❌ Uncommenting data/control signals
   - ✅ Only clk/rst active, others commented

6. **Case sensitivity in signal mapping:**
   - ❌ `clock Qclk -both_edges` (when RTL has lowercase `qclk`)
   - ✅ `clock qclk -both_edges` (must match RTL exactly)
   - ❌ `reset -expression { ~RST_B }` (when RTL port is lowercase `rst_b`)
   - ✅ `reset -expression { ~rst_b }` (extract exact case from port list)

7. **Comments inside braces in TCL expressions:**
   - ❌ `reset -expression { ~rst_b  # active-low reset reset_n }`
   - ✅ `reset -expression { ~rst_b reset_n }` (keep comments outside braces)
   - ❌ `clock -expression { clk  # main clock }`
   - ✅ `# Main clock` then `clock clk -both_edges`

8. **Concatenating entries on the same line in `*_fpv_lib.f`:**
   - ❌ `+incdir+$ip/src/val/tb/fpv/module_a/src+incdir+$ip/src/val/tb/fpv/module_b/src`
   - ✅ Each `+incdir+` entry must be on its own line:
     ```
     +incdir+$ip/src/val/tb/fpv/module_a/src
     +incdir+$ip/src/val/tb/fpv/module_b/src
     ```
   - ❌ `$ip/src/val/tb/fpv/module_a/src/fv_module_a_top.va$ip/src/val/tb/fpv/module_b/src/fv_module_b_top.va`
   - ✅ Same rule applies to file path entries — one path per line, no concatenation

---

## Quick Reference

### RunFV Commands

**Create Proof:**
```bash
run_fv create-proof -dut <cluster> -p <proof> -t <proof> -w <dir> -l <lib> -f fpv
```

**Build Proof:**
```bash
run_fv build-proof -dut <cluster> -p <proof>
```

**Load Proof:**
```bash
# Check for existing session first — NEVER open duplicate GUI
find $WORKAREA/output/formal/<proof>/compile/jgproject -name "*.lock" 2>/dev/null
# If no active session:
run_fv load-proof -dut <cluster> -p <proof>
```

**Run Proof:**

🛑 **MANDATORY:** `prove -bg -all` must be included at the end of `*_conf.tcl` (under the "Automatic code" section) so proofs auto-run on load. Do NOT rely on the user manually running this in the Jasper TCL console.

### File Locations

```
$WORKAREA/
├── src/val/tb/fpv/
│   ├── proofs_container.csv
│   ├── intel_checkers/
│   └── <proof_name>/
│       ├── cfg/
│       └── src/
├── filelists/val/
│   └── <cluster>_fpv_lib.f
└── output/formal/
```

---

## Proof Removal

To completely remove a proof from the repo, given a `<proof_name>`:

### Steps

1. **Delete the proof source directory:**
   ```bash
   rm -rf $WORKAREA/src/val/tb/fpv/<proof_name>/
   ```

2. **Delete the formal build output directory (if exists):**
   ```bash
   rm -rf $WORKAREA/output/formal/<proof_name>/
   ```

3. **Remove references from the FPV filelist** (`filelists/val/<cluster>_fpv_lib.f`):
   - Remove the `+incdir+` line: `+incdir+$ip/src/val/tb/fpv/<proof_name>/src/`
   - Remove the source file line: `$ip/src/val/tb/fpv/<proof_name>/src/fv_<proof_name>_top.va`

4. **Remove the entry from `proofs_container.csv`:**
   - Delete the line matching `<proof_name>` in `src/val/tb/fpv/proofs_container.csv`

### What NOT to Remove

Do **not** remove design artifacts that are not proof-specific:
- RTL source files (e.g., `src/rtl/.../<proof_name>.sv`)
- Coverage files (e.g., `src/val/coverage/<proof_name>_cov.svh`)
- Codegen/VISA files (e.g., `src/codegen/...`)
- RTL filelists (`filelists/rtl.f`, `filelists/<cluster>_lib.rtl.f`)
- Sequence library files (e.g., `src/val/tb/seqlib/`)

### Verification

After removal, confirm no dangling references:
```bash
grep -r "<proof_name>" $WORKAREA/filelists/ $WORKAREA/src/val/tb/fpv/proofs_container.csv
```

---

## When to Use This Skill

✅ **Use runfv_setup skill for:**
- Creating new proof directory structure
- Configuring clocks and resets
- Setting up signal mappings
- Adding scan/VISA assumptions
- Updating filelists
- Preparing environment for properties

❌ **Do NOT use runfv_setup skill for:**
- Advanced property generation at full block scope (use runfv_verify guidance)
- Building proofs (user does this)
- Debugging proof results (use runfv_verify guidance)
- Deep convergence tuning and abstraction strategy (use runfv_verify guidance)

---

## Success Criteria

Phase 1-5 complete when:
- ✅ Proof directory created
- ✅ conf.tcl configured with ALL clocks/resets
- ✅ global_prune.tcl configured with scan/VISA
- ✅ map.va has clk/rst active, others commented
- ✅ assumptions/assertions/covers added with generic property rules
- ✅ Filelist updated
- ✅ Ready for build and advanced convergence work (runfv_verify guidance)

---

*For advanced property generation, convergence, and debug, use runfv_verify guidance*
