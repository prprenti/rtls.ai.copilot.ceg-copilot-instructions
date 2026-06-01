# Debug Reference — CDC, VIP/CompMon, and Decision Matrix

---

## CDC-Specific Debug Patterns

### Pattern A: Cross-Domain Arithmetic

- **Symptom:** CEX or UNDETERMINED on occupancy/counter comparisons
- **Root Cause:** Arithmetic across clock domains (counter_A - counter_B)
- **Example:** `fv_occupancy = fv_in_count (clkA) - fv_out_count (clkB)`
- **Analysis:** Clock phase differences mean subtraction doesn't reflect real-time state
- **Solution:** Comment out — requires proper CDC synchronization logic

### Pattern B: Bounded Liveness with CDC

- **Symptom:** CEX showing livelock (stem + loop) with bounded eventually
- **Root Cause:** CDC + backpressure = non-deterministic latency
- **Example:** `##[1:N] output_valid` fails in CDC FIFO
- **Analysis:** Transaction may take arbitrary cycles due to clock ratio + backpressure
- **Solution:** Comment out — bounded liveness fundamentally incompatible with CDC

### Pattern C: Reset Isolation in CDC

- **Symptom:** UNREACHABLE for reset isolation properties
- **Root Cause:** Post-reset proof start means reset never asserts
- **Example:** `IS_CLK_CROSSING && rstA && !rstB` when proof starts with resets deasserted
- **Solution:** Comment out — cannot verify in post-reset configuration

---

## VIP/CompMon Failure Triage

**VIP/CompMon failures often indicate REAL bugs or missing constraints.**

### A. Identify VIP/CompMon Property

Check property name prefix in session log:

```bash
# AXI4 Master VIP properties
grep "axi4.*ASSERT\|axi4.*CHECK" jg_session_N.log

# AXI4 Slave VIP properties
grep "axi4_slave.*ASSERT\|axi4_slave.*CHECK" jg_session_N.log

# CFI CompMon properties
grep "FVCompMonCFI\|cfi_.*_assert" jg_session_N.log
```

Common naming patterns:
- AXI4 VIP: `axi4_master.ASSERT_*`, `axi4_slave.CHECK_*`
- CFI CompMon: `FVCompMonCFI.*assert_*`, `cfi_req_credit_*`

### B. Locate VIP/CompMon Source Code

```bash
# AXI4 ABVIP
find /p/hdk/rtl/cad -name "axi4_master.sv" 2>/dev/null | head -1
find $WORKAREA/src/val/tb/fpv -name "axi4_master.sv"
grep -A 10 "property.*ASSERT.*AWVALID" <vip_path>/axi4_master.sv

# CFI CompMon
cd /p/hdk/rtl/proj_tools/cdg_val_fv_utils/CFICM_012/CFI_Compmons/
ls -la
grep -rn "assert.*credit.*return" .
grep -rn "assert.*vc_id.*valid" .
```

### C. Common Check Tables

**AXI4 ABVIP Common Checks:**

| Property Pattern | What It Checks | Common Failure Cause |
|-----------------|----------------|---------------------|
| `AWVALID_STABLE` | AWVALID stays high until AWREADY | DUT deasserts AWVALID before handshake |
| `WDATA_AFTER_AWADDR` | Write data follows write address | DUT sends WDATA before AWADDR accepted |
| `WSTRB_VALID` | Write strobe matches data width | Incorrect WSTRB calculation |
| `BURST_LENGTH` | AWLEN matches actual data beats | DUT sends wrong number of data beats |
| `RLAST_ALIGNMENT` | RLAST on correct beat | DUT asserts RLAST early/late |
| `OUTSTANDING_LIMIT` | Respects MAX_PENDING transactions | DUT exceeds transaction limit |
| `ADDR_ALIGNMENT` | Address aligned to size | Misaligned address for burst size |

**CFI CompMon Common Checks:**

| Property Pattern | What It Checks | Common Failure Cause |
|-----------------|----------------|---------------------|
| `credit_return_valid` | Credit return protocol correctness | DUT returns credits incorrectly |
| `no_txn_without_credit` | Transaction sent only with credits | DUT sends packet when credits=0 |
| `vc_id_in_range` | VC_ID within configured range | DUT uses invalid VC_ID |
| `protocol_id_valid` | Protocol_ID matches expected | Wrong protocol_id in header |
| `header_format` | Header fields valid | Malformed CFI header |
| `early_valid_timing` | early_valid asserted before cmd_valid | DUT timing violation |
| `shared_credit_limit` | Shared credits don't exceed limit | Credit accounting error |

### D. Debugging Strategy

**Step 1: Read the failing property definition**

```bash
# Example: AXI4 AWVALID_STABLE failure
grep -A 20 "property.*AWVALID.*stable\|AWVALID.*until.*AWREADY" axi4_master.sv

# Example output:
# property AWVALID_STABLE;
#   @(posedge aclk) disable iff (!aresetn)
#   awvalid && !awready |=> awvalid;
# endproperty
```

**Step 2: Understand the requirement**
- **AWVALID_STABLE:** Once AWVALID is asserted, it must stay high until AWREADY handshake
- **Failure meaning:** DUT deasserted AWVALID before master responded with AWREADY
- **This is a REAL BUG** — violates AXI protocol

**Step 3: Analyze CEX waveform**

Use the `runfv-mcp/jg_cmd` MCP tool to build the batch command, then pass the returned commands to the **@build-run** agent for execution:
```
runfv-mcp/jg_cmd(tcl_commands="visualize -violation <property_name>", app="fpv", dut="<dut>", proof="<proof>")
```
The tool returns a JSON object with shell commands and a Tcl script. Use the @build-run agent to write the script and run the commands in a CTH-configured terminal.

For interactive GUI debugging:
```bash
# In JasperGold GUI: Tools → Visualize → Counterexample
# Look for:
# - Clock cycle where AWVALID drops
# - Check if AWREADY was high (if yes, handshake occurred - VIP bug unlikely)
# - Check if AWREADY was low (if yes, DUT violated protocol - REAL BUG)
```

**Step 4: Check for missing constraints**

AXI4 ABVIP and CFI CompMon already contain all necessary protocol assumptions. Failures typically indicate:

1. **REAL RTL BUG** (most common) — DUT violated protocol specification
2. **VIP/CompMon parameter mismatch** — Configuration doesn't match DUT
3. **NOT missing assumptions** — Protocol assumptions already in VIP/CompMon

```bash
# Verify VIP parameters match DUT configuration in top.va:
# - ADDR_WIDTH, DATA_WIDTH, ID_WIDTH match RTL
# - MAX_PENDING matches DUT's transaction buffer depth
# - MAXLEN matches DUT's maximum burst length

# Verify CompMon parameters match DUT in spec.va:
# - REQ_AMOUNT_VCS array matches DUT's VC usage
# - DATA_AMOUNT_VCS array matches DUT's VC usage
# - SHARED_CREDIT_MAX_AMOUNT matches DUT's credit limits
```

Common parameter mismatches:
```systemverilog
// ❌ WRONG: VIP MAX_PENDING=21 but DUT only supports 8 outstanding transactions
// → VIP will fail when DUT correctly rejects 9th transaction
// FIX: Change .MAX_PENDING(8) in VIP instantiation

// ❌ WRONG: CompMon VC5 depth=8 but DUT only allocates 4 credits for VC5
// → CompMon will fail when DUT correctly stops at 4 credits
// FIX: Change .REQ_AMOUNT_VCS({'d0,'d0,'d0,'d0,'d0,'d4,'d0,'d8})

// ❌ WRONG: VIP DATA_WIDTH=512 but DUT has 256-bit interface
// → VIP will fail on data width mismatches
// FIX: Change .DATA_WIDTH(256) in VIP instantiation
```

**Step 5: Determine root cause**

| Scenario | Root Cause | Action |
|----------|-----------|--------|
| CEX shows DUT violated protocol spec | **REAL BUG** | Escalate to RTL designer |
| CEX shows impossible scenario (e.g., credits<0) | **Credit accounting bug** | Escalate to RTL designer |
| Property unreachable precondition | **Configuration mismatch** | Check VIP/CompMon parameters vs RTL config |
| VIP parameter limit exceeded | **Parameter mismatch** | Update VIP/CompMon parameters to match DUT |
| CEX in reset sequence | **Reset protocol issue** | Escalate to RTL designer |

**Do NOT add manual assumptions for protocol compliance — VIP/CompMon already includes them.**

### E. Common VIP/CompMon Failure Patterns

**Pattern 1: AXI Outstanding Transaction Limit**

Failure: `axi4_master.CHECK_MAX_OUTSTANDING`
Meaning: DUT issued more transactions than `MAX_PENDING` allows

```systemverilog
// Check VIP parameter in top.va
// .MAX_PENDING(21)  ← Should match DUT's actual capability
// If DUT only supports 8: FIX → .MAX_PENDING(8)
// If DUT should support 21 but fails: REAL BUG → escalate
```

**Pattern 2: CFI Credit Underflow**

Failure: `FVCompMonCFI.assert_no_txn_without_credit`
Meaning: DUT sent CFI packet when credit count was zero

```systemverilog
// REAL BUG — DUT violated credit protocol
// Check in RTL:
// 1. Credit counter increment/decrement logic
// 2. Transaction gating condition (should check crd_cnt > 0)
// 3. Credit return timing
// Escalate to RTL designer
```

**Pattern 3: AXI Burst Length Mismatch**

Failure: `axi4_master.CHECK_WLAST_COUNT`
Meaning: WLAST asserted on wrong beat (AWLEN said N beats, but WLAST on beat M)

```systemverilog
// Check RTL burst counter logic
// Common bug: Off-by-one in beat count
// AWLEN=3 means 4 beats (AWLEN+1)
// Escalate to RTL designer
```

**Pattern 4: CFI VC_ID Out of Range**

Failure: `FVCompMonCFI.assert_vc_id_valid`
Meaning: DUT used VC_ID that wasn't configured in CompMon

```systemverilog
// Check CompMon instantiation in spec.va:
// .REQ_AMOUNT_VCS({'d0,'d0,'d0,'d0,'d0,'d8,'d0,'d8})
//                  VC0 VC1 VC2 VC3 VC4 VC5 VC6 VC7
// Only VC5 and VC7 configured (depth 8)
// If DUT sends on VC2, CompMon fails
// Solution 1: Update CompMon config to match DUT's VC usage
// Solution 2: If DUT is wrong, escalate to RTL designer
```

### F. VIP/CompMon Failure Checklist

Before escalating as RTL bug:

- [ ] Verified VIP parameters match DUT configuration (widths, depths, limits)
- [ ] Checked CompMon VC configuration matches DUT's VC usage
- [ ] Checked CompMon credit limits match DUT's credit allocation
- [ ] Verified CEX waveform shows actual protocol violation (not parameter mismatch)
- [ ] Confirmed VIP/CompMon parameters are correct for this DUT

If all checks pass and CEX shows clear protocol violation → **ESCALATE TO RTL DESIGNER**

Common mistake to avoid:
```systemverilog
// ❌ WRONG: Adding manual AXI protocol assumptions
//`FV_<CLUSTER>_ASSUMES_STABLE(T_assume_awvalid_stable,
//    awvalid, !awready,  // ← VIP already checks this!
//    clk, rst, MSG);

// ❌ WRONG: Adding manual CFI credit assumptions
//`FV_<CLUSTER>_ASSUMES(T_assume_no_negative_credits,
//    cfi_crd_cnt >= 0,  // ← CompMon already checks this!
//    clk, rst, MSG);

// ✅ CORRECT: Only verify VIP/CompMon parameters match DUT
// Then trust VIP/CompMon to check protocol compliance
```

---

## Spec-vs-RTL-vs-Assertion Decision Matrix

When MAS/spec text, RTL behavior, and properties appear inconsistent, classify the issue before editing collateral.

### Step 1: Check Property Scope

- A local property file should verify local RTL equations and local state transitions.
- Do not force cross-block sequencing requirements into a local counter/property block unless the required signals are explicitly mapped and owned by that block.

### Step 2: Classify the Mismatch Source

| Class | Description |
|-------|-------------|
| **Assertion bug** | Property equation/trigger does not match RTL equation/timing |
| **Assumption gap** | CEX requires illegal environment stimulus, and protocol/system guarantee exists |
| **Mapping bug** | `map.va` polarity/path/alias mismatch causes false property semantics |
| **RTL bug** | Legal stimulus violates explicit spec requirement and property correctly captures intent |
| **Spec ambiguity** | Spec text is incomplete/ambiguous for the exact scenario |

### Step 3: Choose the Fix by Class

| Class | Fix |
|-------|-----|
| Assertion bug | Fix trigger/equation/alignment (e.g., reset polarity, `$past` first-cycle guards) |
| Assumption gap | Add minimal protocol-true assumptions; avoid masking real RTL issues |
| Mapping bug | Fix mapped signal names/polarity in `map.va` |
| RTL bug | Keep property; report/fix RTL |
| Spec ambiguity | Document open question; avoid over-constraining assumptions |

### Step 4: Document Intent In-Code

- Add concise comments explaining why the property/assumption is local-scope valid.
- Explicitly state when deeper ordering is enforced in another block (e.g., scheduler/RDB), not in the local counter module.

### Step 5: Revalidate with Fresh Logs

- Re-run proof, re-check `IPF055`/`IPF051`, and confirm no new blind spots were introduced.

---

## Configuration Parameter Impact

After categorizing results, identify parameter values that may cause vacuous properties:

```bash
# Find parameter values in session log
grep "parameter.*IS_CLK_CROSSING" jg_session_N.log
grep "parameter.*STALL_FLOP_ON_OUTPUT" jg_session_N.log
grep "parameter.*FLOP_ON_OUTPUT" jg_session_N.log
```

Common vacuous property patterns:
- Property requires `!PARAM` but `PARAM=1` → precondition unreachable
- Property requires `PARAM_A && !PARAM_B` but config has opposite → unreachable
- Property requires `IS_CLK_CROSSING=0` in CDC mode → bypass logic unreachable
- Reset properties when `reset -expression` starts deasserted → reset timing unreachable
