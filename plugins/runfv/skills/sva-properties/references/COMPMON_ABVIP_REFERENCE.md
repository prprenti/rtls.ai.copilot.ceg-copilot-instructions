
# CompMon & ABVIP Hookup Reference

**Scope:** Hooking up, configuring, and debugging Compliance Monitors (CompMon) and Assertion-Based Verification IP (ABVIP) in Jasper FPV environments.

**Covers three protocol monitors:**
- **CFI CompMon** (`FVCompMonCFI`) — Coherent Fabric Interface compliance
- **IOSF Sideband CompMon** (`iosf_sb_ifc_compliance`) — IOSF Sideband protocol compliance
- **AXI3 ABVIP** (`axi3_master` / `axi3_slave`) — AXI3 handshake and data integrity

**Related skills/agent:** `jg-cmd`, `runfv-setup`, `runfv-verify`

---

**For questions or issues, contact:**
- Primary: iddhimah@intel.com
- Team PDL: ceg.india.bdc.fv@intel.com

---

## CompMon / ABVIP Cheat Sheet

| Monitor | Module Name | Location |
|---------|-------------|----------|
| CFI CompMon | `FVCompMonCFI` | `/p/hdk/rtl/proj_tools/cdg_val_fv_utils/CFICM_012/CFI_Compmons/FVCompMonCFI.sv` |
| CFI AIP (bind) | `fvcto_cfi_aip` | `/p/hdk/rtl/proj_tools/cdg_val_fv_utils/CFICM_012/CFI_Compmons/FVCompMonCFI.sv` |
| IOSF SB CompMon | `iosf_sb_ifc_compliance` | `/p/hdk/cad/abvip/iosf_abvip/1.3_2025/1.3_2025/MAIN/dot_f_files/sideband_compliance.f` |
| AXI3 ABVIP (slave-side) | `axi3_master` | `/p/cth/rtl/cad/x86-64_linux26/cadence/vipcat/.../tools/abvip/axi3/rtl/axi3_master.sv` |
| AXI3 ABVIP (master-side) | `axi3_slave` | `/p/cth/rtl/cad/x86-64_linux26/cadence/vipcat/.../tools/abvip/axi3/rtl/axi3_slave.sv` |

**Reference Implementation:** `$WORKAREA/src/val/tb/fpv/axi2mmio/src/` (or via `$RTLMODELS/ttl/axi2nc/axi2nc-ttlbxh78-trunk-latest/src/val/tb/fpv/axi2mmio/src/`)

---

## 0. End-to-End CompMon Hookup Workflow

### 0A. Decision — Which monitors do you need?

```bash
# Identify interfaces on the DUT
grep -n "cfi_"                       src/rtl/<dut>/<dut>.sv | head -30   # CFI
grep -n "axi_target\|axi_originator" src/rtl/<dut>/<dut>.sv | head -30   # AXI3
grep -n "MNPPUT\|TNPPUT\|iosf_sb"   src/rtl/<dut>/<dut>.sv | head -30   # IOSF SB
```

| Interface Found | Monitor to Use |
|-----------------|----------------|
| `cfi_*_tx_*` / `cfi_*_rx_*` | CFI CompMon |
| `axi_target_*` (DUT is slave) | `axi3_master` ABVIP |
| `axi_originator_*` (DUT is master) | `axi3_slave` ABVIP |
| `MNPPUT`, `TNPPUT`, `SIDE_ISM_*` | IOSF SB CompMon |

### 0B. Hookup Steps (all monitor types)

1. Check FPV filelist for ABVIP library paths (§1)
2. Read DUT's `fv_<dut>_map.va` for signal aliases
3. Create CompMon instantiation file: `fv_<dut>_<protocol>_CompMon.va`
4. Add `include` to `fv_<dut>_top.va` inside `` `ifdef FPV_RESTRICT ``
5. Optionally add `set_define FPV_BOUNDED` in `fv_<dut>_setup.tcl`
6. For an interactive/manual Jasper GUI sanity check, run: `jg -fpv fv_<dut>_setup.tcl`, then verify with `get_assertion *compmon*` (use `runfv-mcp/jg_cmd` for scripted or batch flows)

---

## 1. FPV Filelist — Verify ABVIP Library Paths

Before starting, confirm the required libraries are in your FPV filelist:

```bash
find $WORKAREA/filelists/val/ -name "*fpv*" -type f
grep -n "abvip\|vipcat\|CFI_Compmons\|sideband_compliance" filelists/val/<project>_fpv_lib.f
```

**Expected entries per monitor:**

| Monitor | Pattern to Find in Filelist |
|---------|----------------------------|
| AXI3 ABVIP | `.../cadence/vipcat/.../tools/abvip/axi3/rtl/axi3_master.sv` |
| AXI3 ABVIP | `.../cadence/vipcat/.../tools/abvip/axi3/rtl/axi3_slave.sv` |
| IOSF SB CompMon | `.../iosf_abvip/1.3_2025/.../dot_f_files/sideband_compliance.f` |
| CFI CompMon | `.../cdg_val_fv_utils/CFICM_012/CFI_Compmons/FVCompMonCFI.sv` |

**Validated paths (AXI2NC project):**

```
/p/cth/rtl/cad/x86-64_linux26/cadence/vipcat/vipcat_11.30.108-23_Nov_2025_08_15_02/tools/abvip/axi3/rtl/axi3_master.sv
/p/cth/rtl/cad/x86-64_linux26/cadence/vipcat/vipcat_11.30.108-23_Nov_2025_08_15_02/tools/abvip/axi3/rtl/axi3_slave.sv
/p/hdk/cad/abvip/iosf_abvip/1.3_2025/1.3_2025/MAIN/dot_f_files/sideband_compliance.f
/p/hdk/rtl/proj_tools/cdg_val_fv_utils/CFICM_012/CFI_Compmons/FVCompMonCFI.sv
```

---

## 2. CFI CompMon

### 2A. Key Parameters

| Parameter | TX (A2F, DUT drives) | RX (F2A, DUT receives) |
|-----------|----------------------|------------------------|
| `AGENT_IS_DUT` | `1` | `0` |
| `REQ_USED` | `0` (usually) | `0` (usually) |
| `DATA_USED` | `1` | `1` |
| `RSP_USED` | `1` | `1` |
| `ENABLE_PROTOCOL_AWARE` | `1` | `1` |
| `ENABLE_DATA_FSM` | `1` | `1` |
| `DATA_IS_64B` | `1` (64B payload) | `1` |

**VC Credit Configuration (UPI.NC protocol — used in AXI2MMIO):**

| Direction | Channel | VC | Credits (Dedicated) | Shared |
|-----------|---------|-----|---------------------|--------|
| TX (A2F) | RSP | VC0_NDR (3'b000) | 8 | 8 |
| TX (A2F) | DATA | VC0_DRS (3'b000) | 8 | 8 |
| RX (F2A) | DATA | VC0_NCB (3'b110) | 4 | 8 |
| RX (F2A) | DATA | VC0_NCS (3'b111) | 4 | 8 |

```systemverilog
// Credit parameters for TX (adjust VCs per protocol):
.REQ_AMOUNT_VCS({'d0, 'd0, 'd0, 'd0, 'd0, 'd0, 'd0, 'd8}),  // VC0_DRS: 8
.RSP_AMOUNT_VCS({'d0, 'd0, 'd0, 'd0, 'd0, 'd0, 'd0, 'd8}),  // VC0_NDR: 8
.SHARED_CREDIT_MAX_AMOUNT({'d8, 'd8, 'd0}),  // {RSP, DATA, REQ}
```

### 2B. Required Structs

```systemverilog
// Connection handshake struct (TX side)
cfi_init_struct cfi_init_a2f = '{
    txcon_req: `FV_DUT.cfi_a2f_tx_con_req,
    rxcon_ack: `FV_DUT.cfi_a2f_tx_con_ack
};

// RSP channel transaction struct
cfi_txn_struct cfi_txn_rsp_a2f = '{
    cmd_valid:       `FV_DUT.cfi_a2f_tx_rsp_is_valid,
    cmd_early_valid: `FV_DUT.cfi_a2f_tx_rsp_early_valid,
    cmd_eop:         `FV_DUT.cfi_a2f_tx_rsp_header[0],
    protocol_id:     `FV_DUT.cfi_a2f_tx_rsp_protocol_id,
    vc_id:           {2'b0, `FV_DUT.cfi_a2f_tx_rsp_vc_id},  // zero-extend to 3b
    dstid:           `FV_DUT.cfi_a2f_tx_rsp_dstid,
    header:          `FV_DUT.cfi_a2f_tx_rsp_header,
    rctrl:           `FV_DUT.cfi_a2f_tx_rsp_rctrl,
    null_packet:     `FV_DUT.cfi_a2f_tx_rsp_null_packet,
    trace_packet:    `FV_DUT.cfi_a2f_tx_rsp_trace_packet,
    rxcrd_valid:     `FV_DUT.cfi_a2f_tx_rsp_rxcrd_valid,
    block:           `FV_DUT.cfi_a2f_tx_rsp_block
};
```

### 2C. Instantiation Template

```systemverilog
`ifdef FPV_RESTRICT
FVCompMonCFI #(
    .AGENT_IS_DUT(1),
    .REQ_USED(0), .DATA_USED(1), .RSP_USED(1),
    .REQ_AMOUNT_VCS({'d0,'d0,'d0,'d0,'d0,'d0,'d0,'d8}),
    .RSP_AMOUNT_VCS({'d0,'d0,'d0,'d0,'d0,'d0,'d0,'d8}),
    .SHARED_CREDIT_MAX_AMOUNT({'d8,'d8,'d0}),
    .ENABLE_PROTOCOL_AWARE(1),
    .ENABLE_DATA_FSM(1),
    .DATA_IS_64B(1)
) fv_a2f_cfi_compmon (
    .clk(axi_clk),
    .rst(axi_reset),           // active-HIGH reset
    .init(cfi_init_a2f),
    .txn_rsp(cfi_txn_rsp_a2f),
    .txn_data(cfi_txn_data_a2f)
);
`endif
```

> **Reset polarity:** CFI CompMon uses **active-HIGH reset** (`rst`). Invert if DUT has active-low: `.rst(~rst_b)`

### 2D. Signal Widths Reference

| Signal | Width | Notes |
|--------|-------|-------|
| RSP header | 21 bits | Protocol-specific fields |
| RSP rctrl | 2 bits | Response control |
| DATA header | 44 bits | Wider than RSP |
| DATA payload | 256 bits | 64B = 256 bits |
| DATA parity | 4 bits | One per 64B |
| vc_id | 3 bits | Zero-extend from DUT's narrower field |

### 2E. Jasper Tcl — CFI CompMon

```tcl
# Verify CompMon assertions are loaded
get_assertion *compmon*
get_assertion *a2f_cfi_compmon*
get_assertion *f2a_cfi_compmon*

# Get proof results per instance
get_proof_result *a2f_cfi_compmon*
get_proof_result *f2a_cfi_compmon*

# Disable non-applicable assertions (shared credits not in use)
assert -disable *shared_credit*
assert -disable *block*

# Debug: prove only CFI assertions
assert -disable *
assert -enable *cfi_compmon*
prove -task {<embedded>}

# Optional: bounded proving for faster initial check
# In setup.tcl:
set_define FPV_BOUNDED
```

### 2F. CFI AIP (`fvcto_cfi_aip`) — Cadence Bind-Based Monitor

An alternative to `FVCompMonCFI` is Cadence's **CFI AIP** (`fvcto_cfi_aip`), used via SystemVerilog `bind` statements. This is the preferred approach when the DUT ports map directly to CFI channel signals (REQ/RSP/DATA with per-channel credits).

**Location:** `/p/hdk/rtl/proj_tools/cdg_val_fv_utils/CFICM_012/CFI_Compmons/FVCompMonCFI.sv`

**Key differences from FVCompMonCFI:**

| Aspect | FVCompMonCFI | fvcto_cfi_aip |
|--------|-------------|---------------|
| Hookup style | Instantiation inside `ifdef FPV_RESTRICT` | SystemVerilog `bind` statement |
| Signal connection | Via structs (`cfi_init_struct`, `cfi_txn_struct`) | Direct port-to-port mapping |
| Reset polarity | Active-HIGH (`.rst`) | Active-LOW (`.reset_b`) |
| Bind target | N/A (manually instantiated) | `bind <module> fvcto_cfi_aip #(...) <inst>(...)` |
| Channel enables | `REQ_USED`, `DATA_USED`, `RSP_USED` | `A2F_REQ_EN`, `A2F_RSP_EN`, `A2F_DATA_EN`, `F2A_*` |

**Direction convention (from monitored module's perspective):**
- **A2F** = Agent-to-Fabric = signals the bound module **receives** (inputs to it)
- **F2A** = Fabric-to-Agent = signals the bound module **transmits** (outputs from it)

**Bind target selection:**
- Bind to the **module whose ports directly carry the CFI signals**
- If signals are internal wires (not ports), bind to the enclosing module and use the wire names
- If signals are ports of a sub-module (e.g., `mem_traffic_inj_top`), bind directly to that sub-module for cleaner port-level access

**Example — binding to `mem_traffic_inj_top` (TIE):**

```systemverilog
bind mem_traffic_inj_top fvcto_cfi_aip #(
  .AIP_FABRIC(1), .AIP_AGENT(0), .AIP_MONITOR(0),
  .ENABLE_EVENTUAL_CHECKS(1),
  // ... credit/VC parameters ...
  .A2F_REQ_EN(0), .A2F_RSP_EN(1), .A2F_DATA_EN(1),
  .F2A_REQ_EN(1), .F2A_RSP_EN(0), .F2A_DATA_EN(1),
  .VC_ID_WIDTH(3), .PROT_ID_WIDTH(2)
) fvcto_cfi_aip_inst_tie (
  .clk(clk),
  .reset_b(~rst),    // Invert active-high module reset
  .A2F_txcon_req(tie_rx_con_req),
  .A2F_rxcon_ack(tie_rx_con_ack),
  // ... port connections ...
);
```

**Critical learnings & pitfalls:**

| Issue | Symptom | Fix |
|-------|---------|-----|
| Parameter not found: `DISABLE_SHARED_CRD_INITIALIZE_FIRST` | `VERI-1184` compile error | Remove — not present in all `fvcto_cfi_aip` versions |
| Parameter not found: `DISABLE_DED_CRD_USE_FIRST` | `VERI-1184` compile error | Remove — not present in all `fvcto_cfi_aip` versions |
| `vc_id` width mismatch | Width warning or incorrect credit tracking | Zero-extend 1-bit VC to 3 bits: `.A2F_rsp_vc_id({2'b00, tie_rx_ndr_vc_id})` |
| Wrong bind target module | Signals not accessible (hierarchical refs needed) | Bind to the module that owns the ports, not parent |
| Reset polarity error | Assertions fire immediately | `fvcto_cfi_aip` uses **active-LOW** `.reset_b` — invert if module has active-high `rst` |

**Version-dependent parameters:**

The following parameters exist in **some** versions of `fvcto_cfi_aip` but not all. Always verify against the version in your FPV filelist before using:

```
DISABLE_SHARED_CRD_INITIALIZE_FIRST   — not in cfi_abvip/1.0_2023_11_06
DISABLE_DED_CRD_USE_FIRST             — not in cfi_abvip/1.0_2023_11_06
```

Check available parameters: `grep "parameter" /p/hdk/cad/abvip/cfi_abvip/<version>/MAIN/src/fvcto_cfi_aip.sv | head -60`

---

## 3. IOSF Sideband CompMon

### 3A. Key Parameters

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `IOSF_MONITOR` | `0` | Not in pure monitor mode |
| `IOSF_FABRIC` | `1` | Fabric-side monitoring (most common) |
| `IOSF_AGENT` | `0` | Not in agent mode |
| `PAYLOAD_BANDWIDTH` | `32` | 32-bit sideband payload |
| `Sai_Width` | `7` | Security Attributes width |
| `MAX_AGENT_NP_CREDITS` | `8` | Max non-posted credits (agent→fabric) |
| `MAX_AGENT_PC_CREDITS` | `8` | Max posted/completion credits |
| `MAX_PENDING_REQUESTS` | `1` | Outstanding transactions |
| `eh_support` | `1'b1` | Extended header support |
| `sai_support` | `1'b1` | SAI field support |

### 3B. ISM State Encoding

```
Agent ISM (3-bit):
  3'b000 = IDLE        3'b001 = IDLEREQ
  3'b011 = ACTIVE      3'b010 = ACTIVEREQ
  3'b100 = CREDITREQ   3'b101 = CREDITINIT
  3'b110 = CREDITDONE

Fabric ISM (3-bit):
  Same except 3'b110 = CREDITACK (not CREDITDONE)

Power-up sequence:
  IDLE → CREDITREQ → CREDITINIT → CREDITDONE/CREDITACK → ACTIVE
```

### 3C. Signal Naming Convention

```
M* = Master-driven outputs (DUT → Fabric)
T* = Target-driven inputs  (Fabric → DUT)

Credit classes:
  NP = Non-Posted (reads, config)
  PC = Posted/Completion (writes, completions)

Examples:
  MNPPUT  — Master Non-Posted put (DUT sends NP message)
  TNPPUT  — Target Non-Posted put (Fabric sends NP message)
  MNPCUP  — Master Non-Posted credit update (from fabric to agent)
  TNPCUP  — Target Non-Posted credit update (from agent to fabric)
```

### 3D. Instantiation Template

```systemverilog
`ifdef FPV_RESTRICT
iosf_sb_ifc_compliance #(
    .PAYLOAD_BANDWIDTH(32),
    .IOSF_MONITOR(0), .IOSF_FABRIC(1), .IOSF_AGENT(0),
    .Sai_Width(7),
    .MAX_AGENT_NP_CREDITS(8), .MAX_AGENT_PC_CREDITS(8),
    .MAX_FABRIC_NP_CREDITS(8), .MAX_FABRIC_PC_CREDITS(8),
    .MAX_PENDING_REQUESTS(1),
    .eh_support(1'b1), .sai_support(1'b1),
    .Agent_ISM_Reset_IDLE(1'b1), .Fabric_ISM_Reset_IDLE(1'b1)
) fv_iosf_sb_ifc_compliance (
    .side_clk  (side_clk),
    .side_rst_b(~sbreset_async),   // active-LOW reset (invert active-high)
    // Master interface (DUT → Fabric)
    .mnpput    (`FV_DUT.iosf_sb_master_MNPPUT),
    .mpcput    (`FV_DUT.iosf_sb_master_MPCPUT),
    .meom      (`FV_DUT.iosf_sb_master_MEOM),
    .mpayload  (`FV_DUT.iosf_sb_master_MPAYLOAD),
    .tnpcup    (`FV_DUT.iosf_sb_master_TNPCUP),
    .tpccup    (`FV_DUT.iosf_sb_master_TPCCUP),
    // Target interface (Fabric → DUT)
    .tnpput    (`FV_DUT.iosf_sb_master_TNPPUT),
    .tpcput    (`FV_DUT.iosf_sb_master_TPCPUT),
    .teom      (`FV_DUT.iosf_sb_master_TEOM),
    .tpayload  (`FV_DUT.iosf_sb_master_TPAYLOAD),
    .mnpcup    (`FV_DUT.iosf_sb_master_MNPCUP),
    .mpccup    (`FV_DUT.iosf_sb_master_MPCCUP),
    // Power management
    .side_ism_fabric(`FV_DUT.iosf_sb_master_SIDE_ISM_FABRIC),
    .side_ism_agent (`FV_DUT.iosf_sb_master_SIDE_ISM_AGENT)
);
`endif
```

> **Reset polarity:** IOSF SB CompMon uses **active-LOW reset** (`side_rst_b`). Invert active-high reset.

> **Status note:** In AXI2NC, IOSF SB CompMon is currently **disabled** (commented out in `fv_axi2mmio_top.va`). Uncomment the `include` line to activate.

### 3E. Jasper Tcl — IOSF SB CompMon

```tcl
# List IOSF SB assertions
get_assertion *iosf_sb*
get_assertion *credit*
get_assertion *ism*

# Debug specific domains
visualize -window w1 *credit* *cup*        ;# credit signals
visualize -window w2 *side_ism*            ;# ISM state signals
visualize -window w3 *payload* *eom* *put* ;# data path

# Disable non-critical checks
assert -disable *parity*
assert -disable *multicast*

# Prove only IOSF SB assertions
assert -disable *
assert -enable *iosf_sb*
prove -task {<embedded>}
```

---

## 4. AXI3 ABVIP

### 4A. Component Selection

```
DUT has AXI slave interface (target):
    → Use axi3_master  (checks DUT slave compliance)
    → assumes on master signals (free input); asserts on slave signals

DUT has AXI master interface (originator):
    → Use axi3_slave   (checks DUT master compliance)
    → asserts on master signals (checks DUT); assumes on slave signals
```

### 4B. Key Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| `ID_WIDTH` | Design-specific | AXI transaction ID width |
| `ADDR_WIDTH` | Design-specific | Address bus width |
| `DATA_WIDTH` | `512` | 512-bit data bus (AXI2NC) |
| `LEN_WIDTH` | `4` | **AXI3 only** — always 4 bits (max 16 beats) |
| `WUSER_WIDTH` | `32` | Zero-extend narrower user signals |
| `BUSER_WIDTH` | `32` | |
| `RUSER_WIDTH` | `32` | |
| `USER_SIGNALS_ON` | `0` | Disable if user signals not checked |
| `MAX_PENDING` | `16` | Outstanding transaction limit |
| `XCHECKS_ON` | `1` | X/Z checking enabled |
| `RST_CHECKS_ON` | `0` | Disable — formal tools handle reset |
| `READ_INTERLEAVE_ON` | `1` | AXI3 allows read interleaving |
| `WRITE_INTERLEAVE_ON` | `1` | AXI3 allows write interleaving |

### 4C. Critical Signal Handling

**Always slice `awlen`/`arlen` to 4 bits for AXI3:**
```systemverilog
// ❌ Wrong — full width
.awlen(axi_originator_awlen)

// ✅ Correct — AXI3 LEN is always 4 bits
.awlen(axi_originator_awlen[3:0])
.arlen(axi_originator_arlen[3:0])
```

**Always zero-extend USER signals to 32 bits:**
```systemverilog
// ❌ Wrong — width mismatch
.awuser(axi_target_awuser_mstrid)

// ✅ Correct — zero-extend to ABVIP's 32-bit USER
.awuser({{(32-AXI_AWUSER_WIDTH){1'b0}}, axi_target_awuser_mstrid})
```

**Always invert reset (ABVIP uses active-LOW):**
```systemverilog
// ❌ Wrong
.aresetn(axi_rst)

// ✅ Correct
.aresetn(~axi_rst)
```

### 4D. Instantiation Template (Target Interface — DUT is AXI slave)

```systemverilog
`ifdef FPV_RESTRICT
axi3_master #(
    .ID_WIDTH   (AXI_ID_WIDTH),
    .ADDR_WIDTH (AXI_ADDR_WIDTH),
    .DATA_WIDTH (AXI_DATA_WIDTH),
    .LEN_WIDTH  (4),
    .WUSER_WIDTH(32), .BUSER_WIDTH(32), .RUSER_WIDTH(32),
    .USER_SIGNALS_ON(0),
    .MAX_PENDING(16),
    .XCHECKS_ON(1),
    .RST_CHECKS_ON(0),
    .READ_INTERLEAVE_ON(1), .WRITE_INTERLEAVE_ON(1)
) fv_axi3_master (
    .aclk   (axi_clk),
    .aresetn(~axi_rst),
    // Write Address channel
    .awid   (`FV_DUT.axi_target_awid),
    .awaddr (`FV_DUT.axi_target_awaddr),
    .awlen  (`FV_DUT.axi_target_awlen[3:0]),   // Slice to 4-bit
    .awsize (`FV_DUT.axi_target_awsize),
    .awburst(`FV_DUT.axi_target_awburst),
    .awlock (`FV_DUT.axi_target_awlock),
    .awcache(`FV_DUT.axi_target_awcache),
    .awprot (`FV_DUT.axi_target_awprot),
    .awvalid(`FV_DUT.axi_target_awvalid),
    .awready(`FV_DUT.axi_target_awready),
    // Write Data channel
    .wdata  (`FV_DUT.axi_target_wdata),
    .wstrb  (`FV_DUT.axi_target_wstrb),
    .wlast  (`FV_DUT.axi_target_wlast),
    .wvalid (`FV_DUT.axi_target_wvalid),
    .wready (`FV_DUT.axi_target_wready),
    // Write Response channel
    .bid    (`FV_DUT.axi_target_bid),
    .bresp  (`FV_DUT.axi_target_bresp),
    .bvalid (`FV_DUT.axi_target_bvalid),
    .bready (`FV_DUT.axi_target_bready),
    // Read Address channel
    .arid   (`FV_DUT.axi_target_arid),
    .araddr (`FV_DUT.axi_target_araddr),
    .arlen  (`FV_DUT.axi_target_arlen[3:0]),   // Slice to 4-bit
    .arsize (`FV_DUT.axi_target_arsize),
    .arburst(`FV_DUT.axi_target_arburst),
    .arlock (`FV_DUT.axi_target_arlock),
    .arcache(`FV_DUT.axi_target_arcache),
    .arprot (`FV_DUT.axi_target_arprot),
    .arvalid(`FV_DUT.axi_target_arvalid),
    .arready(`FV_DUT.axi_target_arready),
    // Read Data channel
    .rid    (`FV_DUT.axi_target_rid),
    .rdata  (`FV_DUT.axi_target_rdata),
    .rresp  (`FV_DUT.axi_target_rresp),
    .rlast  (`FV_DUT.axi_target_rlast),
    .rvalid (`FV_DUT.axi_target_rvalid),
    .rready (`FV_DUT.axi_target_rready)
);
`endif
```

### 4E. Common AXI3 Assertions (Auto-generated by ABVIP)

| Assertion | Checks |
|-----------|--------|
| `awvalid_stable` | AWVALID held until AWREADY |
| `awaddr_stable` | AWADDR stable while AWVALID & ~AWREADY |
| `wlast_with_last_beat` | WLAST asserted on final write beat |
| `bid_match` | BID matches outstanding AWID |
| `no_x_on_awvalid` | No X/Z on control signals |
| `arvalid_stable` | ARVALID held until ARREADY |
| `rdata_stable` | RDATA stable while RVALID & ~RREADY |
| `rlast_correct` | RLAST on beat matching ARLEN |

### 4F. Jasper Tcl — AXI3 ABVIP

```tcl
# Verify ABVIP assertions loaded
get_assertion *axi3_master*
get_assertion *axi3_slave*
get_assertion *fv_axi3*

# Get proof results
get_proof_result *fv_axi3*

# Debug specific channel failures
visualize -window w1 *awvalid* *awready* *awaddr*    ;# Write address
visualize -window w2 *wvalid*  *wready*  *wlast*     ;# Write data
visualize -window w3 *arvalid* *arready* *rvalid*    ;# Read channels

# Disable noisy checks for initial debug
assert -disable *parity*
assert -disable *interleave*

# Prove only AXI assertions
assert -disable *
assert -enable *axi3*
prove -task {<embedded>}

# Optional bounded mode (faster convergence for ABVIP)
# In setup.tcl:
set_define FPV_BOUNDED
```

---

## 5. Top File Integration Pattern

All CompMon / ABVIP instances go inside `` `ifdef FPV_RESTRICT `` in `fv_<dut>_top.va`:

```systemverilog
// fv_<dut>_top.va
`include "fv_<dut>_bind.va"
`include "fv_<dut>_map.va"
`include "fv_<dut>_prop.va"

`ifdef FPV_RESTRICT
// CompMon / ABVIP instances (add as needed per interface)
`include "fv_<dut>_CFI_CompMon.va"
`include "fv_<dut>_AXI3_ABVIP.va"
// `include "fv_<dut>_IOSFSB_CompMon.va"  // uncomment when IOSF SB is modeled
`endif
```

---

## 6. Setup Tcl Options for CompMon

```tcl
# In fv_<dut>_setup.tcl, after loading proof:

# Enable bounded proof mode (faster for ABVIP — limits depth to ~20 cycles)
set_define FPV_BOUNDED

# Selectively disable assertions after load:
assert -disable *shared_credit*   ;# CFI: shared credits not in use
assert -disable *parity*          ;# AXI: skip parity if not modeled
assert -disable *multicast*       ;# IOSF: skip multicast if not applicable

# Dedicated CompMon-only debug session
assert -disable *
assert -enable *compmon*
assert -enable *axi3*
assert -enable *iosf_sb*
prove -task {<embedded>} -time_limit 2h
```

---

## 7. Troubleshooting

### CFI CompMon

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `unreachable` on credit checks | VC credits never initialized | Check `txcon_req`/`rxcon_ack` handshake assumptions |
| `cex` on `shared_credit_max` | Shared credit count exceeds `SHARED_CREDIT_MAX_AMOUNT` | Adjust parameter or add assumption |
| No assertions loaded | `FPV_RESTRICT` not defined | Add `set_define FPV_RESTRICT` in setup.tcl |
| Struct assignment error | Signal width mismatch | Zero-extend `vc_id` to 3 bits |

### CFI AIP (`fvcto_cfi_aip`)

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `VERI-1184`: parameter `DISABLE_SHARED_CRD_INITIALIZE_FIRST` not found | Parameter absent in `cfi_abvip/1.0_2023_11_06` | Remove the parameter from bind instantiation |
| `VERI-1184`: parameter `DISABLE_DED_CRD_USE_FIRST` not found | Parameter absent in `cfi_abvip/1.0_2023_11_06` | Remove the parameter from bind instantiation |
| `VDB-9017`: Module could not be elaborated | Cascading from parameter errors above | Fix all `VERI-1184` errors first |
| Assertions fire at time 0 | Wrong reset polarity | Use `.reset_b(~rst)` for active-low; check module's reset port |
| Width mismatch on `vc_id` connection | DUT has 1-bit VC, compmon expects 3-bit | Zero-extend: `.A2F_rsp_vc_id({2'b00, signal})` |
| Signals not found in bind scope | Binding to wrong module (signals are internal wires in parent) | Bind to the sub-module that has them as ports |

### IOSF SB CompMon

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `unreachable` on credit assertions | ISM never reaches ACTIVE | Check ISM power-up sequence assumptions |
| `cex` on `credit_underflow` | Agent uses more credits than received | Add credit bound constraints |
| ISM stuck at IDLE | Reset polarity wrong or never deasserts | Check `side_rst_b` polarity and reset assumptions |

### AXI3 ABVIP

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `awlen` width mismatch compile error | Passing full-width len to 4-bit port | Slice: `.awlen(awlen[3:0])` |
| `aresetn` X at start | Active-high reset passed without invert | Fix: `.aresetn(~axi_rst)` |
| `bid_match` CEX | DUT returns wrong BID | Real protocol bug — escalate to designer |
| `awvalid_stable` CEX | AWVALID deasserted before AWREADY | Real protocol bug or missing env assumption |
| No assertions after `prove` | USER signals width mismatch | Zero-extend: `{{(32-W){1'b0}}, user_sig}` |

---

## 8. Reset Polarity Summary

| Monitor | Reset Port | Polarity | Typical Connection |
|---------|-----------|----------|--------------------|
| CFI CompMon | `rst` | Active **HIGH** | `.rst(axi_reset)` |
| IOSF SB CompMon | `side_rst_b` | Active **LOW** | `.side_rst_b(~sbreset_async)` |
| AXI3 ABVIP | `aresetn` | Active **LOW** | `.aresetn(~axi_rst)` |

---

## 9. Quick Validation Checklist

```
CFI CompMon:
✅ AGENT_IS_DUT=1 for TX (DUT drives), =0 for RX
✅ vc_id zero-extended to 3 bits in struct
✅ DATA header=44b, RSP header=21b
✅ reset is active-HIGH (.rst)
✅ VC credits match protocol (UPI.NC: VC0_NDR/VC0_DRS/VC0_NCB/VC0_NCS)

IOSF SB CompMon:
✅ IOSF_FABRIC=1, IOSF_AGENT=0 for fabric-side monitoring
✅ side_rst_b is active-LOW (invert active-high reset)
✅ MNPCUP/MPCCUP vs TNPCUP/TPCCUP direction correct
✅ ISM power-up: IDLE → CREDITREQ → CREDITINIT → CREDITDONE → ACTIVE

AXI3 ABVIP:
✅ axi3_master for DUT-is-slave; axi3_slave for DUT-is-master
✅ LEN_WIDTH=4 (AXI3 always 4-bit length)
✅ awlen/arlen sliced to [3:0]
✅ USER signals zero-extended to 32 bits
✅ aresetn is active-LOW (invert active-high reset)
✅ RST_CHECKS_ON=0 (formal tools handle reset)
```
