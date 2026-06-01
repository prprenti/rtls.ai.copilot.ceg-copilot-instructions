# SVA Property & Macro Reference

---

## Complete Intel Checker Macro Library

### A. Combinational Checkers (ASSERTC/ASSUMEC/COVERC)

**1. MUTEXED** - At most one bit high (allows X/Z)
```systemverilog
`FV_<CLUSTER>_ASSERTC_MUTEXED(name, sig, rst, MSG)
`FV_<CLUSTER>_ASSUMEC_MUTEXED(name, sig, rst, MSG)
`FV_<CLUSTER>_COVERC_MUTEXED(name, sig, rst, MSG)
```

**2. ONE_HOT** - Exactly one bit high (no X/Z)
```systemverilog
`FV_<CLUSTER>_ASSERTC_ONE_HOT(name, sig, rst, MSG)
`FV_<CLUSTER>_ASSUMEC_ONE_HOT(name, sig, rst, MSG)
`FV_<CLUSTER>_COVERC_ONE_HOT(name, sig, rst, MSG)
```

**3. KNOWN_DRIVEN** - No X/Z values
```systemverilog
`FV_<CLUSTER>_ASSERTC_KNOWN_DRIVEN(name, sig, rst, MSG)
`FV_<CLUSTER>_ASSUMEC_KNOWN_DRIVEN(name, sig, rst, MSG)
```

**4. RANGE** - Signal within range [low, high]
```systemverilog
`FV_<CLUSTER>_ASSERTC_RANGE(name, sig, low, high, rst, MSG)
`FV_<CLUSTER>_ASSUMEC_RANGE(name, sig, low, high, rst, MSG)
```

**5. FORBIDDEN** - Condition must never be true
```systemverilog
`FV_<CLUSTER>_ASSERTC_FORBIDDEN(name, prop, rst, MSG)
`FV_<CLUSTER>_ASSUMEC_FORBIDDEN(name, prop, rst, MSG)
```

**6. TRIGGER** - Implication (combinational)
```systemverilog
`FV_<CLUSTER>_ASSERTC_TRIGGER(name, trig, sig, rst, MSG)
`FV_<CLUSTER>_ASSUMEC_TRIGGER(name, trig, sig, rst, MSG)
```

### B. Sequential Checkers (ASSERTS/ASSUMES/COVERS)

These checkers require a clock for sampling design signals.

**1. Basic Sequential Assertion**
```systemverilog
`FV_<CLUSTER>_ASSERTS(name, property, clk, rst, MSG)
`FV_<CLUSTER>_ASSUMES(name, property, clk, rst, MSG)
`FV_<CLUSTER>_COVERS(name, property, clk, rst, MSG)
```

**2. TRIGGER** - Same-cycle implication (trig |-> prop)
```systemverilog
`FV_<CLUSTER>_ASSERTS_TRIGGER(name, trig, prop, clk, rst, MSG)
`FV_<CLUSTER>_ASSUMES_TRIGGER(name, trig, prop, clk, rst, MSG)
`FV_<CLUSTER>_COVERS_TRIGGER(name, trig, prop, clk, rst, MSG)
```

**3. DELAYED_TRIGGER** - Next-cycle implication (trig |-> ##delay prop)
```systemverilog
`FV_<CLUSTER>_ASSERTS_DELAYED_TRIGGER(name, trig, delay, prop, clk, rst, MSG)
`FV_<CLUSTER>_ASSUMES_DELAYED_TRIGGER(name, trig, delay, prop, clk, rst, MSG)
`FV_<CLUSTER>_COVERS_DELAYED_TRIGGER(name, trig, delay, prop, clk, rst, MSG)
// delay: Number of clock cycles (integer parameter)
```

**4. EVENTUALLY_HOLDS** - Liveness (en |-> s_eventually prop)
```systemverilog
`FV_<CLUSTER>_ASSERTS_EVENTUALLY_HOLDS(name, en, prop, clk, rst, MSG)
`FV_<CLUSTER>_ASSUMES_EVENTUALLY_HOLDS(name, en, prop, clk, rst, MSG)
```

**5. STABLE** - Signal stable when condition holds
```systemverilog
`FV_<CLUSTER>_ASSERTS_STABLE(name, sig, when_cond, clk, rst, MSG)
`FV_<CLUSTER>_ASSUMES_STABLE(name, sig, when_cond, clk, rst, MSG)
```

**6. MUTEXED/ONE_HOT** - Sequential versions
```systemverilog
`FV_<CLUSTER>_ASSERTS_MUTEXED(name, sig, clk, rst, MSG)
`FV_<CLUSTER>_ASSERTS_ONE_HOT(name, sig, clk, rst, MSG)
```

**7. FORBIDDEN** - Condition never true (clocked)
```systemverilog
`FV_<CLUSTER>_ASSERTS_FORBIDDEN(name, cond, clk, rst, MSG)
`FV_<CLUSTER>_ASSUMES_FORBIDDEN(name, cond, clk, rst, MSG)
```

**8. REQ_GRANTED** - Request eventually granted
```systemverilog
`FV_<CLUSTER>_ASSERTS_REQ_GRANTED(name, req, gnt, clk, rst, MSG)
`FV_<CLUSTER>_ASSUMES_REQ_GRANTED(name, req, gnt, clk, rst, MSG)
```

### C. Coverage Macros

Use cover-specific message macro:
```systemverilog
`FV_<CLUSTER>_COVER_MSG("Description of coverage goal")
```

---

## Common Design Patterns → Properties

### Pattern 1: Arbiter
**RTL:** Multiple requests, one-hot grants, fairness

**Properties:**
```systemverilog
// One-hot grants
//`FV_<CLUSTER>_ASSERTS_MUTEXED(T_<cluster>_FPV_arb_assert_one_winner,
//    grant_vec, clk, rst, `ERR_MSG("Multiple grants"));

// Grant needs request
//`FV_<CLUSTER>_ASSERTS_TRIGGER(T_<cluster>_FPV_arb_assert_grant_needs_req,
//    grant[i], req[i],
//    clk, rst, `ERR_MSG("Grant without request"));

// Liveness
//`FV_<CLUSTER>_ASSERTS_EVENTUALLY_HOLDS(T_<cluster>_FPV_arb_assert_req_granted,
//    req[i], grant[i],
//    clk, rst, `ERR_MSG("Request never granted"));
```

### Pattern 2: FIFO/Buffer
**RTL:** Write/read pointers, full/empty flags, count

**Properties:**
```systemverilog
// No overflow
//`FV_<CLUSTER>_ASSERTS_FORBIDDEN(T_<cluster>_FPV_fifo_assert_no_overflow,
//    wr_en && full,
//    rst, `ERR_MSG("Write when full"));

// No underflow
//`FV_<CLUSTER>_ASSERTS_FORBIDDEN(T_<cluster>_FPV_fifo_assert_no_underflow,
//    rd_en && empty,
//    rst, `ERR_MSG("Read when empty"));

// Count correctness
//`FV_<CLUSTER>_ASSERTS_TRIGGER(T_<cluster>_FPV_fifo_assert_count_inc,
//    wr_en && !rd_en && !full,
//    ##1 count == $past(count) + 1,
//    clk, rst, `ERR_MSG("Count not incremented"));
```

### Pattern 3: Handshake Protocol
**RTL:** valid/ready or req/ack

**Properties:**
```systemverilog
// Data stable during valid
//`FV_<CLUSTER>_ASSERTS_STABLE(T_<cluster>_FPV_proto_assert_data_stable,
//    data, valid && !ready,
//    clk, rst, `ERR_MSG("Data changed before ready"));

// Valid sticky (assumption)
//`FV_<CLUSTER>_ASSUMES_DELAYED_TRIGGER(T_<cluster>_FPV_proto_assume_valid_sticky,
//    valid && !ready, 1, valid,
//    clk, rst, `ERR_MSG("Valid not sticky"));
```

### Pattern 4: State Machine
**RTL:** State enum, transitions

**Properties:**
```systemverilog
// Legal states only
//`FV_<CLUSTER>_ASSERTS_ONE_HOT(T_<cluster>_FPV_fsm_assert_state_onehot,
//    state_vec, clk, rst,
//    `ERR_MSG("State not one-hot"));

// Transition correctness
//`FV_<CLUSTER>_ASSERTS_TRIGGER(T_<cluster>_FPV_fsm_assert_idle_to_busy,
//    (state == IDLE) && start,
//    ##1 state == BUSY,
//    clk, rst, `ERR_MSG("Invalid transition"));
```

### Pattern 5: Protocol Verification with VIP/CompMon (CFI & AXI4 Bridge Designs)

**When to use:**
- **CFI-only designs:** RTL implements CFI protocol (use CFI CompMon steps only - Step 3)
- **AXI4↔CFI bridges:** RTL converts between AXI4 and CFI (use all steps)
- **AXI4↔AXI4 with buffers:** Bidirectional AXI4 with clock crossing (see Pattern 5b below)

**Protocol Verification Strategy:**
- ✅ **AXI4 side:** Bind Cadence `axi4_master` VIP (handles ALL AXI protocol checks)
- ✅ **CFI side:** Instantiate `FVCompMonCFI` (handles ALL CFI protocol checks)
- ✅ **Bridge logic:** Write properties ONLY for transformation/FSM/flow control
- ❌ **NEVER** write properties for standard protocol features

---

#### **Step 1: AXI4 ABVIP Integration (top.va)**

**⚠️ CRITICAL: Before proceeding, verify ALL signal names from RTL (see Rule 6)**

**File location:** Include at top of `fv_<proof>_top.va`
```systemverilog
`include "axi4_master.sv"
```

**Bind to DUT:** After `endmodule` (outside proof top module)
```systemverilog
`ifdef FPV_RESTRICT_<proof_name>
   bind <dut_module> fv_<proof>_top fv_<proof>_top (.*);

   // Bind AXI4 Master VIP for port 0
   `ifdef FPV_AXI_P0_ENABLE
       bind <dut_module> axi4_master #(
           .ADDR_WIDTH (48),
           .DATA_WIDTH (512),
           .LEN_WIDTH(4),
           .AWUSER_WIDTH(11),
           .WUSER_WIDTH(11),
           .BUSER_WIDTH(11),
           .ARUSER_WIDTH(11),
           .RUSER_WIDTH(11),
           .ID_WIDTH(8),
           .MAX_PENDING(21),
           .MAXLEN(15),
           .DATA_BEFORE_CONTROL_ON(0),
           .DATA_ACCEPT_WITH_OR_AFTER_CONTROL(1)
       ) axi_master_p0 (
           .aclk            (vpu_clk),
           .aresetn         (reset_b),

           // Write Address Channel
           .awid            (axi_awaddr_in[0].awid),
           .awaddr          (axi_awaddr_in[0].awaddr),
           .awlen           (axi_awaddr_in[0].awlen),
           .awsize          (axi_awaddr_in[0].awsize),
           .awburst         (axi_awaddr_in[0].awburst),
           .awlock          (axi_awaddr_in[0].awlock),
           .awcache         (axi_awaddr_in[0].awcache),
           .awprot          (axi_awaddr_in[0].awprot),
           .awvalid         (axi_awaddr_in[0].awvalid),
           .awready         (awready[0]),
           .awqos           (axi_awaddr_in[0].awqos),
           .awregion        (axi_awaddr_in[0].awregion),
           .awuser          (axi_awaddr_in[0].awuser),

           // Write Data Channel
           .wuser           (axi_wdata_in[0].wuser),
           .wdata           (axi_wdata_in[0].wdata),
           .wstrb           (axi_wdata_in[0].wstrb),
           .wlast           (axi_wdata_in[0].wlast),
           .wvalid          (axi_wdata_in[0].wvalid),
           .wready          (wready[0]),

           // Write Response Channel
           .bid             (axi_wresp_out[0].bid),
           .bresp           (axi_wresp_out[0].bresp),
           .bvalid          (axi_wresp_out[0].bvalid),
           .bready          (bready[0]),
           .buser           (axi_wresp_out[0].buser),

           // Read Address Channel
           .arid            (axi_araddr_in[0].arid),
           .araddr          (axi_araddr_in[0].araddr),
           .arlen           (axi_araddr_in[0].arlen),
           .arsize          (axi_araddr_in[0].arsize),
           .arburst         (axi_araddr_in[0].arburst),
           .arlock          (axi_araddr_in[0].arlock),
           .arcache         (axi_araddr_in[0].arcache),
           .arprot          (axi_araddr_in[0].arprot),
           .arvalid         (axi_araddr_in[0].arvalid),
           .arready         (arready[0]),
           .arqos           (axi_araddr_in[0].arqos),
           .arregion        (axi_araddr_in[0].arregion),
           .aruser          (axi_araddr_in[0].aruser),

           // Read Data Channel
           .rid             (axi_rdata_out[0].rid),
           .rdata           (axi_rdata_out[0].rdata),
           .rresp           (axi_rdata_out[0].rresp),
           .rlast           (axi_rdata_out[0].rlast),
           .rvalid          (axi_rdata_out[0].rvalid),
           .rready          (rready[0]),
           .ruser           (axi_rdata_out[0].ruser)
       );
   `endif

   // Repeat for additional ports (P1, P2...) with FPV_AXI_P1_ENABLE, etc.
`endif
```

**Key VIP Parameters:**
- `ADDR_WIDTH`: AXI address bus width (typically 48)
- `DATA_WIDTH`: AXI data bus width (typically 512)
- `ID_WIDTH`: Transaction ID width (typically 8)
- `MAX_PENDING`: Outstanding transaction limit
- `MAXLEN`: Maximum burst length

---

#### **Step 2: AXI Signal Mapping (map.va)**

**Map AXI structs from RTL:**
```systemverilog
// Import AXI interface types
parameter NUM_AXI_PORTS = <dut>.NUM_AXI_PORTS;

// AXI channel structs (use RTL's typedef)
axi_interface::axi_awaddr [NUM_AXI_PORTS-1:0] axi_awaddr_in;
axi_interface::axi_wdata  [NUM_AXI_PORTS-1:0] axi_wdata_in;
axi_interface::axi_araddr [NUM_AXI_PORTS-1:0] axi_araddr_in;
axi_interface::axi_wresp  [NUM_AXI_PORTS-1:0] axi_wresp_out;
axi_interface::axi_rdata  [NUM_AXI_PORTS-1:0] axi_rdata_out;

// Map to RTL signals
assign axi_awaddr_in = <dut>.axi_awaddr_in;
assign axi_wdata_in = <dut>.axi_wdata_in;
assign axi_araddr_in = <dut>.axi_araddr_in;
assign axi_wresp_out = <dut>.axi_wresp_out;
assign axi_rdata_out = <dut>.axi_rdata_out;

// Map ready signals (individual per port)
logic [NUM_AXI_PORTS-1:0] awready, wready, arready, bready, rready;
assign awready = <dut>.awready;
assign wready = <dut>.wready;
assign arready = <dut>.arready;
assign bready = <dut>.bready;
assign rready = <dut>.rready;
```

---

#### **Step 3: CFI CompMon Integration (spec.va)**

**⚠️ CRITICAL: Before proceeding, verify ALL CFI signal names and struct fields from RTL (see Rule 6)**

**Define CFI structs for each port:**
```systemverilog
`ifdef FPV_RESTRICT_<proof_name>
   `ifdef FPV_AXI_P0_ENABLE

       // Init Struct (connection handshake)
       cfi_init_struct cfi_init_a2f_p0 = '{
           txcon_req: <dut>.cfi_txcon_req[0],
           rxcon_ack: <dut>.cfi_txcon_ack[0]
       };

       // REQ Channel Transaction Struct
       cfi_txn_struct cfi_txn_req_a2f_p0 = '{
           cmd_valid:       <dut>.cfi_a2f_req[0].is_valid,
           cmd_early_valid: <dut>.cfi_a2f_req[0].early_valid,
           protocol_id:     <dut>.cfi_a2f_req[0].protocol_id,
           vc_id:           <dut>.cfi_a2f_req[0].vc_id,
           shared_credit:   <dut>.cfi_a2f_req[0].shared_credit,
           null_packet:     <dut>.cfi_a2f_req[0].null_packet,
           header:          <dut>.cfi_a2f_req[0].header,
           dst_id:          <dut>.cfi_a2f_req[0].dst_id,
           rctrl:           <dut>.cfi_a2f_req[0].rctrl,
           trace_packet:    <dut>.cfi_a2f_req[0].trace_packet,
           header_parity:   0,
           poison: 0, payload_par: 0, eop: 0, payload: 0,
           internal_usage_data_valid: 0
       };

       // REQ Channel Credit Struct
       cfi_credit_struct cfi_credit_req_a2f_p0 = '{
           crd_valid:   <dut>.cfi_a2f_req_credit[0].rxcrd_valid,
           crd_vc_id:   <dut>.cfi_a2f_req_credit[0].rxcrd_vc_id,
           crd_shared:  <dut>.cfi_a2f_req_credit[0].rxcrd_shared,
           null_credit: <dut>.cfi_a2f_req_credit[0].rxcrd_null_credit
       };

       // DATA Channel (similar structure)
       cfi_txn_struct cfi_txn_data_a2f_p0 = '{
           cmd_valid:       <dut>.cfi_a2f_data[0].is_valid,
           cmd_early_valid: <dut>.cfi_a2f_data[0].early_valid,
           protocol_id:     <dut>.cfi_a2f_data[0].protocol_id,
           vc_id:           <dut>.cfi_a2f_data[0].vc_id,
           shared_credit:   <dut>.cfi_a2f_data[0].shared_credit,
           null_packet:     <dut>.cfi_a2f_data[0].null_packet,
           header:          <dut>.cfi_a2f_data[0].header,
           dst_id:          <dut>.cfi_a2f_data[0].dst_id,
           rctrl:           <dut>.cfi_a2f_data[0].rctrl,
           trace_packet:    <dut>.cfi_a2f_data[0].trace_packet,
           header_parity:   <dut>.cfi_a2f_data[0].header_parity,
           poison: 0, payload_par: 0, eop: 0, payload: 0,
           internal_usage_data_valid: 0
       };

       cfi_credit_struct cfi_credit_data_a2f_p0 = '{
           crd_valid:   <dut>.cfi_a2f_data_credit[0].rxcrd_valid,
           crd_vc_id:   <dut>.cfi_a2f_data_credit[0].rxcrd_vc_id,
           crd_shared:  <dut>.cfi_a2f_data_credit[0].rxcrd_shared,
           null_credit: <dut>.cfi_a2f_data_credit[0].rxcrd_null_credit
       };

       // Block struct (typically unused in AXI bridges)
       cfi_block_struct cfi_block_p0 = '{
           block_txn:       '0,
           block_crd_flow:  '0
       };

       // Instantiate FVCompMonCFI
       FVCompMonCFI #(
           .AGENT_IS_DUT(1),              // DUT is transmitter
           .REQ_USED(1),                  // Enable REQ channel
           .DATA_USED(1),                 // Enable DATA channel
           .RSP_USED(0),                  // Disable RSP channel (AXI→CFI is unidirectional)
           `ifdef FPV_BOUNDED
           .USING_BOUND(1),
           .LATENCY_BOUND(5),
           `endif
           .REQ_AMOUNT_VCS({'d0,'d0,'d0,'d0,'d0,'d8,'d0,'d8}),    // VC depths
           .DATA_AMOUNT_VCS({'d0,'d0,'d8,'d0,'d0,'d0,'d0,'d0}),   // VC depths
           .RSP_AMOUNT_VCS({'d0,'d0,'d0,'d0,'d0,'d0,'d0,'d0}),
           .SHARED_CREDIT_MAX_AMOUNT({'d8,'d8,'d8}),
           .BLOCK_PACKET_LATENCY({'0,'0,'0}),
           .BLOCK_CREDIT_LATENCY({'0,'0,'0})
       ) a2f_compmon_p0 (
           .cfi_clk(clk),
           .fsm_clk(clk),
           .cross_domain_clk(clk),
           .rst(rst),

           // Init
           .cfi_init(cfi_init_a2f_p0),

           // REQ channel
           .cfi_credit_req(cfi_credit_req_a2f_p0),
           .cfi_txn_req(cfi_txn_req_a2f_p0),
           .cfi_block_req(cfi_block_p0),

           // DATA channel
           .cfi_credit_data(cfi_credit_data_a2f_p0),
           .cfi_txn_data(cfi_txn_data_a2f_p0),
           .cfi_block_data(cfi_block_p0)
       );
   `endif
`endif
```

---

#### **Step 4: What NOT to Verify (VIP/CompMon Handles)**

**AXI4 Master VIP checks (DO NOT write properties):**
- ❌ AWVALID/AWREADY, WVALID/WREADY handshakes
- ❌ ARVALID/ARREADY, RVALID/RREADY handshakes
- ❌ BVALID/BREADY response handshake
- ❌ Burst types (FIXED, INCR, WRAP)
- ❌ Burst length (AWLEN/ARLEN) compliance
- ❌ Data strobes (WSTRB) validity
- ❌ RLAST generation
- ❌ Response codes (BRESP/RRESP)
- ❌ Outstanding transaction tracking
- ❌ Address alignment

**CFI CompMon checks (DO NOT write properties):**
- ❌ Credit-based flow control
- ❌ Credit return protocol
- ❌ VC arbitration
- ❌ Protocol_id validity
- ❌ Header format compliance
- ❌ Early_valid timing
- ❌ Connection handshake (con_req/con_ack)

---

#### **Step 5: What TO Verify (Bridge-Specific Logic)**

**Bridge transformation logic (write properties for these):**
- ✅ Bridge FSM: State transitions for AXI→CFI conversion
- ✅ Transaction decomposition: 1 AXI burst → N CFI packets (assert count relationship)
- ✅ Address mapping: AXI AWADDR/ARADDR → CFI header field
- ✅ Data packing: AXI data beats → CFI payload
- ✅ Back-pressure translation: CFI no-credits → AXI not-ready
- ✅ Error propagation: CFI error → AXI BRESP/RRESP
- ✅ ID preservation: AXI transaction ID → CFI routing field

**Example 1: Bridge FSM Transitions**
```systemverilog
// In map.va - Map FSM state
typedef enum {IDLE, AXI_ACCEPTING, SENDING_CFI, WAITING_RESP} bridge_state_t;
bridge_state_t bridge_state;
assign bridge_state = <dut>.fsm_state;

// In assert.va - Check FSM transitions
//`FV_<CLUSTER>_ASSERTS_DELAYED_TRIGGER(T_<cluster>_FPV_axi2cfi_assert_fsm_idle_to_accept,
//    (bridge_state == IDLE) && axi_awvalid && axi_awready,
//    1,
//    bridge_state == AXI_ACCEPTING,
//    clk, rst, `ERR_MSG("FSM did not transition to AXI_ACCEPTING"));

//`FV_<CLUSTER>_ASSERTS_DELAYED_TRIGGER(T_<cluster>_FPV_axi2cfi_assert_fsm_accept_to_send,
//    (bridge_state == AXI_ACCEPTING) && axi_wlast && axi_wvalid && axi_wready,
//    1,
//    bridge_state == SENDING_CFI,
//    clk, rst, `ERR_MSG("FSM did not transition to SENDING_CFI after WLAST"));
```

**Example 2: Back-Pressure Propagation**
```systemverilog
// In spec.va - Track credit availability
logic cfi_req_credits_avail;
logic cfi_data_credits_avail;
assign cfi_req_credits_avail = (<dut>.cfi_req_crd_cnt > 0);
assign cfi_data_credits_avail = (<dut>.cfi_data_crd_cnt > 0);

// In assert.va - Check back-pressure
//`FV_<CLUSTER>_ASSERTS_TRIGGER(T_<cluster>_FPV_axi2cfi_assert_backpressure_awready,
//    !cfi_req_credits_avail && (bridge_state == IDLE),
//    !awready[0],
//    clk, rst, `ERR_MSG("AWREADY not deasserted when CFI REQ credits exhausted"));

//`FV_<CLUSTER>_ASSERTS_TRIGGER(T_<cluster>_FPV_axi2cfi_assert_backpressure_wready,
//    !cfi_data_credits_avail && (bridge_state == AXI_ACCEPTING),
//    !wready[0],
//    clk, rst, `ERR_MSG("WREADY not deasserted when CFI DATA credits exhausted"));
```

**Example 3: Transaction Count Balance**
```systemverilog
// In spec.va - Track transaction flow
logic [7:0] fv_axi_write_count;
logic [7:0] fv_cfi_req_count;
logic [7:0] fv_cfi_data_count;

always_ff @(posedge clk) begin
    if (rst) begin
        fv_axi_write_count <= 0;
        fv_cfi_req_count <= 0;
        fv_cfi_data_count <= 0;
    end else begin
        // Count AXI write transactions
        if (axi_awvalid && axi_awready) fv_axi_write_count <= fv_axi_write_count + 1;

        // Count CFI REQ packets
        if (<dut>.cfi_a2f_req[0].is_valid && cfi_req_credits_avail)
            fv_cfi_req_count <= fv_cfi_req_count + 1;

        // Count CFI DATA packets
        if (<dut>.cfi_a2f_data[0].is_valid && cfi_data_credits_avail)
            fv_cfi_data_count <= fv_cfi_data_count + 1;
    end
end

// In assert.va - Verify count relationship
//`FV_<CLUSTER>_ASSERTS(T_<cluster>_FPV_axi2cfi_assert_req_count_balance,
//    fv_cfi_req_count == fv_axi_write_count,  // 1 AXI write = 1 CFI REQ
//    clk, rst, `ERR_MSG("CFI REQ count mismatch with AXI write count"));

//`FV_<CLUSTER>_ASSERTS(T_<cluster>_FPV_axi2cfi_assert_data_count_reasonable,
//    fv_cfi_data_count <= (fv_axi_write_count * 16),  // Max 16 beats per burst
//    clk, rst, `ERR_MSG("CFI DATA count exceeds reasonable limit"));
```

**Example 4: Address Mapping**
```systemverilog
// In spec.va - Capture AXI address
logic [47:0] fv_last_axi_awaddr;
always_ff @(posedge clk) begin
    if (axi_awvalid && axi_awready)
        fv_last_axi_awaddr <= axi_awaddr_in[0].awaddr;
end

// In assert.va - Check CFI header contains AXI address
//`FV_<CLUSTER>_ASSERTS_TRIGGER(T_<cluster>_FPV_axi2cfi_assert_addr_in_header,
//    <dut>.cfi_a2f_req[0].is_valid,
//    <dut>.cfi_a2f_req[0].header[47:0] == fv_last_axi_awaddr,
//    clk, rst, `ERR_MSG("CFI header does not contain AXI AWADDR"));
```

---

#### **Verification Checklist: Before Writing Properties**

**Ask yourself:**
1. ❓ "Is this checking AXI protocol handshakes?" → ❌ **DON'T WRITE** (axi4_master VIP checks)
2. ❓ "Is this checking CFI credit protocol?" → ❌ **DON'T WRITE** (FVCompMonCFI checks)
3. ❓ "Is this checking bridge FSM transitions?" → ✅ **WRITE property**
4. ❓ "Is this checking AXI→CFI data transformation?" → ✅ **WRITE property**
5. ❓ "Is this checking flow control translation?" → ✅ **WRITE property**
6. ❓ "Is this checking address/ID mapping?" → ✅ **WRITE property**

**Common Mistakes to Avoid:**
```systemverilog
// ❌ WRONG: Checking AXI burst compliance (VIP already checks)
//`FV_<CLUSTER>_ASSERTS_TRIGGER(wrong_axi_check,
//    axi_awvalid && axi_awready,
//    axi_awlen <= 15,  // ← axi4_master VIP already checks this!
//    clk, rst, `ERR_MSG("..."));

// ❌ WRONG: Checking CFI credit return (CompMon already checks)
//`FV_<CLUSTER>_ASSERTS_TRIGGER(wrong_cfi_check,
//    <dut>.cfi_req_crd_rtn_valid,
//    <dut>.cfi_req_crd_cnt <= MAX_CREDITS,  // ← CompMon already checks!
//    clk, rst, `ERR_MSG("..."));

// ✅ CORRECT: Checking bridge-specific logic
//`FV_<CLUSTER>_ASSERTS_TRIGGER(correct_bridge_check,
//    (bridge_state == IDLE) && axi_awvalid && axi_awready,
//    ##1 bridge_state != IDLE,  // ← Bridge FSM behavior
//    clk, rst, `ERR_MSG("Bridge FSM stuck in IDLE"));
```

---

### Pattern 5b: Bidirectional AXI4 Verification (AXI4-to-AXI4 with FIFOs/Buffers)

**When to use:** RTL has AXI4 interfaces on both sides (e.g., axi_gfifos, clock crossing FIFOs, reorder buffers)

**Design pattern:**
```
         _____________                 _____________
        | axi4_master |  ====> DUT ====>  | axi4_slave |
        |_____________|  (SLAVE)    (MASTER) |____________|
             (VIP)          clkA   clkB          (VIP)
                            AXI_A  AXI_B
```

**Key Concept:**
- **axi4_master VIP** monitors the **slave interface** (where AXI transactions enter)
- **axi4_slave VIP** monitors the **master interface** (where AXI transactions exit)
- Both VIPs check protocol compliance on their respective interfaces
- Write properties for: FIFO control, clock crossing behavior, transaction ordering

---

#### **Step 1: Include Both VIPs (top.va)**

```systemverilog
`include "axi4_master.sv"
`include "axi4_slave.sv"
```

---

#### **Step 2: Bind Both VIPs to DUT (top.va)**

**Bind axi4_master to monitor SLAVE interface (side A - input):**
```systemverilog
`ifdef FPV_RESTRICT_<proof_name>
   bind <dut_module> fv_<proof>_top fv_<proof>_top (.*);

   // Bind axi4_master VIP to SLAVE interface (clkA domain)
   bind <dut_module> axi4_master #(
       .ADDR_WIDTH (48),
       .DATA_WIDTH (512),
       .LEN_WIDTH(5),
       .AWUSER_WIDTH(11),
       .WUSER_WIDTH(11),
       .BUSER_WIDTH(11),
       .ARUSER_WIDTH(11),
       .RUSER_WIDTH(11),
       .ID_WIDTH(8),
       .MAX_PENDING(21),
       .MAXLEN(15),
       .DATA_BEFORE_CONTROL_ON(0),
       .DATA_ACCEPT_WITH_OR_AFTER_CONTROL(1),
       .XCHECKS_ON(1),      // Enable X-checks
       .COVERAGE_ON(1)      // Enable functional coverage
   ) axi_gfifo_A_is_slave (
       .aclk            (clkA),
       .aresetn         (~reset_A),

       // Write Address Channel (IP to DUT)
       .awid            (axi_awaddr_A.awid),
       .awaddr          (axi_awaddr_A.awaddr),
       .awlen           (axi_awaddr_A.awlen),
       .awsize          (axi_awaddr_A.awsize),
       .awburst         (axi_awaddr_A.awburst),
       .awlock          (axi_awaddr_A.awlock),
       .awcache         (axi_awaddr_A.awcache),
       .awprot          (axi_awaddr_A.awprot),
       .awvalid         (axi_awaddr_A.awvalid),
       .awready         (axi_awaddr_awready_A),
       .awqos           (axi_awaddr_A.awqos),
       .awregion        (axi_awaddr_A.awregion),
       .awuser          (axi_awaddr_A.awuser),

       // Write Data Channel (IP to DUT)
       .wuser           (axi_wdata_A.wuser),
       .wdata           (axi_wdata_A.wdata),
       .wstrb           (axi_wdata_A.wstrb),
       .wlast           (axi_wdata_A.wlast),
       .wvalid          (axi_wdata_A.wvalid),
       .wready          (axi_wdata_wready_A),

       // Write Response Channel (DUT to IP)
       .bid             (axi_bresp_A.bid),
       .bresp           (axi_bresp_A.bresp),
       .bvalid          (axi_bresp_A.bvalid),
       .buser           (axi_bresp_A.buser),
       .bready          (axi_bresp_bready_A),

       // Read Address Channel (IP to DUT)
       .arid            (axi_araddr_A.arid),
       .araddr          (axi_araddr_A.araddr),
       .arlen           (axi_araddr_A.arlen),
       .arsize          (axi_araddr_A.arsize),
       .arburst         (axi_araddr_A.arburst),
       .arlock          (axi_araddr_A.arlock),
       .arcache         (axi_araddr_A.arcache),
       .arprot          (axi_araddr_A.arprot),
       .arvalid         (axi_araddr_A.arvalid),
       .aruser          (axi_araddr_A.aruser),
       .arregion        (axi_araddr_A.arregion),
       .arqos           (axi_araddr_A.arqos),
       .arready         (axi_araddr_arready_A),

       // Read Data Channel (DUT to IP)
       .rid             (axi_rdata_A.rid),
       .rdata           (axi_rdata_A.rdata),
       .rresp           (axi_rdata_A.rresp),
       .rlast           (axi_rdata_A.rlast),
       .rvalid          (axi_rdata_A.rvalid),
       .ruser           (axi_rdata_A.ruser),
       .rready          (axi_rdata_rready_A)
   );

   // Bind axi4_slave VIP to MASTER interface (clkB domain)
   bind <dut_module> axi4_slave #(
       .ADDR_WIDTH(48),
       .DATA_WIDTH(512),
       .LEN_WIDTH(5),
       .AWUSER_WIDTH(11),
       .WUSER_WIDTH(11),
       .BUSER_WIDTH(11),
       .ARUSER_WIDTH(11),
       .RUSER_WIDTH(11),
       .ID_WIDTH(8),
       .MAX_PENDING(21),
       .MAXLEN(15),
       .DATA_BEFORE_CONTROL_ON(0),
       .DATA_ACCEPT_WITH_OR_AFTER_CONTROL(1),
       .XCHECKS_ON(1),      // Enable X-checks
       .COVERAGE_ON(1)      // Enable functional coverage
   ) axi_gfifo_B_is_master (
       .aclk           (clkB),
       .aresetn        (~reset_B),

       // Write Address Channel (DUT to OP)
       .awid            (axi_awaddr_B.awid),
       .awaddr          (axi_awaddr_B.awaddr),
       .awlen           (axi_awaddr_B.awlen),
       .awsize          (axi_awaddr_B.awsize),
       .awburst         (axi_awaddr_B.awburst),
       .awlock          (axi_awaddr_B.awlock),
       .awprot          (axi_awaddr_B.awprot),
       .awqos           (axi_awaddr_B.awqos),
       .awregion        (axi_awaddr_B.awregion),
       .awuser          (axi_awaddr_B.awuser),
       .awcache         (axi_awaddr_B.awcache),
       .awvalid         (axi_awaddr_B.awvalid),
       .awready         (axi_awaddr_awready_B),

       // Write Data Channel (DUT to OP)
       .wdata           (axi_wdata_B.wdata),
       .wstrb           (axi_wdata_B.wstrb),
       .wuser           (axi_wdata_B.wuser),
       .wlast           (axi_wdata_B.wlast),
       .wvalid          (axi_wdata_B.wvalid),
       .wready          (axi_wdata_wready_B),

       // Write Response Channel (OP to DUT)
       .bid             (axi_bresp_B.bid),
       .bresp           (axi_bresp_B.bresp),
       .buser           (axi_bresp_B.buser),
       .bvalid          (axi_bresp_B.bvalid),
       .bready          (axi_bresp_bready_B),

       // Read Address Channel (DUT to OP)
       .arid            (axi_araddr_B.arid),
       .araddr          (axi_araddr_B.araddr),
       .arlen           (axi_araddr_B.arlen),
       .arsize          (axi_araddr_B.arsize),
       .arburst         (axi_araddr_B.arburst),
       .arlock          (axi_araddr_B.arlock),
       .arprot          (axi_araddr_B.arprot),
       .arqos           (axi_araddr_B.arqos),
       .arregion        (axi_araddr_B.arregion),
       .aruser          (axi_araddr_B.aruser),
       .arcache         (axi_araddr_B.arcache),
       .arvalid         (axi_araddr_B.arvalid),
       .arready         (axi_araddr_arready_B),

       // Read Data Channel (OP to DUT)
       .rid            (axi_rdata_B.rid),
       .rdata          (axi_rdata_B.rdata),
       .rlast          (axi_rdata_B.rlast),
       .ruser          (axi_rdata_B.ruser),
       .rvalid         (axi_rdata_B.rvalid),
       .rready         (axi_rdata_rready_B),
       .rresp          (axi_rdata_B.rresp)
   );
`endif
```

**Key Differences from Single VIP:**
- **Two VIP instances:** One master, one slave
- **Two clock domains:** clkA and clkB
- **Bidirectional naming:** _A for slave side, _B for master side
- **Direction comments:** "IP to DUT" vs "DUT to OP" clarify data flow

---

#### **Step 3: Signal Mapping (map.va)**

**Map both interfaces with clear naming:**
```systemverilog
`define FV_DUT <dut_module_name>

// Clock and reset for both domains
logic clkA, clkB;
logic rst_A, rst_B;
assign clkA = `FV_DUT.clkA;
assign clkB = `FV_DUT.clkB;
assign rst_A = `FV_DUT.reset_A;
assign rst_B = `FV_DUT.reset_B;

// ========================================================================
// AXI Channel Mappings - Interface A (Slave Side)
// ========================================================================

// Write Address Channel A
axi_pkg::t_axi_awaddr  axi_awaddr_A;
logic                  axi_awaddr_awready_A;
assign axi_awaddr_A         = `FV_DUT.axi_awaddr_A;
assign axi_awaddr_awready_A = `FV_DUT.axi_awaddr_awready_A;

// Write Data Channel A
axi_pkg::t_axi_wdata   axi_wdata_A;
logic                  axi_wdata_wready_A;
assign axi_wdata_A        = `FV_DUT.axi_wdata_A;
assign axi_wdata_wready_A = `FV_DUT.axi_wdata_wready_A;

// Write Response Channel A
axi_pkg::t_axi_bresp   axi_bresp_A;
logic                  axi_bresp_bready_A;
assign axi_bresp_A        = `FV_DUT.axi_bresp_A;
assign axi_bresp_bready_A = `FV_DUT.axi_bresp_bready_A;

// Read Address Channel A
axi_pkg::t_axi_araddr  axi_araddr_A;
logic                  axi_araddr_arready_A;
assign axi_araddr_A         = `FV_DUT.axi_araddr_A;
assign axi_araddr_arready_A = `FV_DUT.axi_araddr_arready_A;

// Read Data Channel A
axi_pkg::t_axi_rdata   axi_rdata_A;
logic                  axi_rdata_rready_A;
assign axi_rdata_A        = `FV_DUT.axi_rdata_A;
assign axi_rdata_rready_A = `FV_DUT.axi_rdata_rready_A;

// ========================================================================
// AXI Channel Mappings - Interface B (Master Side)
// ========================================================================

// Write Address Channel B
axi_pkg::t_axi_awaddr  axi_awaddr_B;
logic                  axi_awaddr_awready_B;
assign axi_awaddr_B         = `FV_DUT.axi_awaddr_B;
assign axi_awaddr_awready_B = `FV_DUT.axi_awaddr_awready_B;

// Write Data Channel B
axi_pkg::t_axi_wdata   axi_wdata_B;
logic                  axi_wdata_wready_B;
assign axi_wdata_B        = `FV_DUT.axi_wdata_B;
assign axi_wdata_wready_B = `FV_DUT.axi_wdata_wready_B;

// Write Response Channel B
axi_pkg::t_axi_bresp   axi_bresp_B;
logic                  axi_bresp_bready_B;
assign axi_bresp_B        = `FV_DUT.axi_bresp_B;
assign axi_bresp_bready_B = `FV_DUT.axi_bresp_bready_B;

// Read Address Channel B
axi_pkg::t_axi_araddr  axi_araddr_B;
logic                  axi_araddr_arready_B;
assign axi_araddr_B         = `FV_DUT.axi_araddr_B;
assign axi_araddr_arready_B = `FV_DUT.axi_araddr_arready_B;

// Read Data Channel B
axi_pkg::t_axi_rdata   axi_rdata_B;
logic                  axi_rdata_rready_B;
assign axi_rdata_B        = `FV_DUT.axi_rdata_B;
assign axi_rdata_rready_B = `FV_DUT.axi_rdata_rready_B;

// ========================================================================
// FIFO/Buffer Status Signals (if applicable)
// ========================================================================

logic  AxiAwaddrFifoIsEmpty_B, AxiAwaddrFifoIsFull_A;
logic  AxiAraddrFifoIsEmpty_B, AxiAraddrFifoIsFull_A;
logic  AxiWdataFifoIsEmpty_B,  AxiWdataFifoIsFull_A;
logic  AxiRdataFifoIsEmpty_A,  AxiRdataFifoIsFull_B;
logic  AxiBrespFifoIsEmpty_A,  AxiBrespFifoIsFull_B;

assign AxiAwaddrFifoIsEmpty_B = `FV_DUT.axi_awaddr_fifo.FifoIsEmpty_B;
assign AxiAwaddrFifoIsFull_A  = `FV_DUT.axi_awaddr_fifo.FifoIsFull_A;
assign AxiAraddrFifoIsEmpty_B = `FV_DUT.axi_araddr_fifo.FifoIsEmpty_B;
assign AxiAraddrFifoIsFull_A  = `FV_DUT.axi_araddr_fifo.FifoIsFull_A;
assign AxiWdataFifoIsEmpty_B  = `FV_DUT.axi_wdata_fifo.FifoIsEmpty_B;
assign AxiWdataFifoIsFull_A   = `FV_DUT.axi_wdata_fifo.FifoIsFull_A;
assign AxiRdataFifoIsEmpty_A  = `FV_DUT.axi_rdata_fifo.FifoIsEmpty_B;
assign AxiRdataFifoIsFull_B   = `FV_DUT.axi_rdata_fifo.FifoIsFull_A;
assign AxiBrespFifoIsEmpty_A  = `FV_DUT.axi_bresp_fifo.FifoIsEmpty_B;
assign AxiBrespFifoIsFull_B   = `FV_DUT.axi_bresp_fifo.FifoIsFull_A;
```

---

#### **Step 4: What to Verify (DUT-Specific Logic)**

**Both VIPs handle protocol checks, write properties for:**

**1. FIFO/Buffer Behavior:**
```systemverilog
// In assert.va - Check no overflow
//`FV_<CLUSTER>_ASSERTS_FORBIDDEN(T_<cluster>_FPV_axi_gfifo_assert_no_awaddr_overflow,
//    axi_awaddr_A.awvalid && axi_awaddr_awready_A && AxiAwaddrFifoIsFull_A,
//    rst_A, `ERR_MSG("Write address FIFO overflow"));

// In assert.va - Check no underflow
//`FV_<CLUSTER>_ASSERTS_FORBIDDEN(T_<cluster>_FPV_axi_gfifo_assert_no_awaddr_underflow,
//    axi_awaddr_B.awvalid && axi_awaddr_awready_B && AxiAwaddrFifoIsEmpty_B,
//    rst_B, `ERR_MSG("Write address FIFO underflow"));
```

**2. Clock Crossing Correctness:**
```systemverilog
// In assert.va - Verify CDC synchronization
//`FV_<CLUSTER>_ASSERTS_EVENTUALLY_HOLDS(T_<cluster>_FPV_axi_gfifo_assert_awaddr_crosses,
//    axi_awaddr_A.awvalid && axi_awaddr_awready_A,
//    axi_awaddr_B.awvalid,
//    clkB, rst_B, `ERR_MSG("Write address did not cross to clkB domain"));
```

**3. Transaction Ordering (if required):**
```systemverilog
// In spec.va - Track transaction IDs
logic [7:0] last_awid_A;
logic [7:0] last_awid_B;

always_ff @(posedge clkA) begin
    if (axi_awaddr_A.awvalid && axi_awaddr_awready_A)
        last_awid_A <= axi_awaddr_A.awid;
end

always_ff @(posedge clkB) begin
    if (axi_awaddr_B.awvalid && axi_awaddr_awready_B)
        last_awid_B <= axi_awaddr_B.awid;
end

// In assert.va - Check ID preservation
//`FV_<CLUSTER>_ASSERTS_TRIGGER(T_<cluster>_FPV_axi_gfifo_assert_awid_preserved,
//    axi_awaddr_B.awvalid && axi_awaddr_awready_B,
//    axi_awaddr_B.awid == last_awid_A,
//    clkB, rst_B, `ERR_MSG("AWID not preserved across clock domains"));
```

**4. Back-Pressure Propagation:**
```systemverilog
// In assert.va - Check back-pressure from B to A
//`FV_<CLUSTER>_ASSERTS_TRIGGER(T_<cluster>_FPV_axi_gfifo_assert_backpressure_awaddr,
//    AxiAwaddrFifoIsFull_A,
//    !axi_awaddr_awready_A,
//    clkA, rst_A, `ERR_MSG("AWREADY not deasserted when FIFO full"));
```

---

#### **Verification Checklist for Bidirectional AXI4**

**What VIPs check (DO NOT write properties):**
- ❌ AXI protocol compliance on BOTH interfaces (VIPs handle this)
- ❌ Handshake correctness (VALID/READY on both sides)
- ❌ Burst compliance (AWLEN, ARLEN, WLAST, RLAST)
- ❌ Response integrity (BRESP, RRESP)

**What to verify (WRITE properties):**
- ✅ FIFO overflow/underflow conditions
- ✅ Clock domain crossing correctness
- ✅ Transaction ID preservation (if required)
- ✅ Transaction ordering (if design maintains order)
- ✅ Back-pressure propagation between domains
- ✅ Empty/full flag correctness
- ✅ Data integrity across clock domains

---

#### **Reference Proof**

Complete working example:
- **Location:** `/nfs/site/disks/vipuljee_wa01/HML/AXI2CFI/26WW04_1/src/val/tb/fpv/vpu_btrs/axi_gfifos/`
- **Files:** `fv_axi_gfifos_top.va`, `fv_axi_gfifos_map.va`
- **Pattern:** Bidirectional AXI4 with clock crossing FIFOs

---

## Best Practices

### Property Writing
1. Start simple (basic protocol checks)
2. Add complex properties incrementally
3. Use meaningful error messages
4. Group related properties with comments
5. ALWAYS comment ALL property lines

### Debugging
1. Check compilation errors FIRST
2. Analyze UNREACHABLE before CEX
3. Document fix rationale
4. Track escalating CEX depth (if relaxing timing)
5. Iterate: fix → rebuild → rerun → analyze

### Performance
1. Use appropriate macros (avoid raw SVA)
2. Keep properties focused
3. Use helper signals in spec.va
4. Leverage FPV_RESTRICT for liveness

---

## Common Mistakes

1. **Using temporal operators inside property arguments:**
   - ❌ `ASSERTS_TRIGGER(name, state == A, ##1 state == B, ...)`
   - ❌ `ASSERTS_TRIGGER(name, trig, ##[1:6] prop, ...)`
   - ❌ `ASSERTS_TRIGGER(name, en, prop || ##1 prop, ...)`
   - ✅ `ASSERTS_DELAYED_TRIGGER(name, state == A, 1, state == B, ...)`
   - ✅ `ASSERTS_EVENTUALLY_HOLDS(name, trig, prop, ...)`
   - **Why Wrong:** Property argument expects Boolean expression, not temporal sequence
   - **Symptom:** Compilation errors, invalid SVA syntax
   - **Fix:** Use correct macro (`DELAYED_TRIGGER`, `EVENTUALLY_HOLDS`) with delay as parameter

2. **Using raw SVA instead of macros:**
   - ❌ `ASSERTS(name, a |-> b, ...)`
   - ✅ `ASSERTS_TRIGGER(name, a, b, ...)`

3. **Adding signal declarations in property files:**
   - ❌ `logic sig; assign sig = ...;` in assert.va
   - ✅ Add to map.va only

4. **Not commenting property lines:**
   - ❌ Uncommented properties
   - ✅ ALL lines commented with //

5. **Using DUT paths instead of mapped names:**
   - ❌ `FV_DUT.Winner` in properties
   - ✅ `winner` (mapped in map.va)

6. **Assuming macros exist:**
   - ❌ Using ASSERTS_IMPLICATION
   - ✅ Verify with grep first

7. **Writing protocol properties manually:**
   - ❌ Writing AXI handshake checks (VIP already does this)
   - ❌ Writing CFI credit protocol checks (CompMon already does this)
   - ✅ Use axi4_master VIP for AXI protocol
   - ✅ Use FVCompMonCFI for CFI protocol
   - ✅ Write properties ONLY for bridge logic (FSM, transformation, mapping)

---

## Quick Reference

### Protocol Checker Locations

**AXI4 Master VIP:**
- **File:** `axi4_master.sv`
- **Usage:** Include in top.va, bind to DUT
- **Path:** Typically available in Cadence VIPcat library
- **Reference proof (single-ended):** `/nfs/site/disks/vipuljee_wa01/HML/AXI2CFI/26WW04_1/src/val/tb/fpv/vpu_btrs/axi2cfi/`

**AXI4 Slave VIP:**
- **File:** `axi4_slave.sv`
- **Usage:** Include in top.va, bind to DUT (for bidirectional AXI4 verification)
- **Reference proof (bidirectional):** `/nfs/site/disks/vipuljee_wa01/HML/AXI2CFI/26WW04_1/src/val/tb/fpv/vpu_btrs/axi_gfifos/`

**CFI CompMon:**
- **Location:** `/p/hdk/rtl/proj_tools/cdg_val_fv_utils/CFICM_012/CFI_Compmons/`
- **Module:** `FVCompMonCFI`
- **Usage:** Instantiate in spec.va with struct-based interfaces
- **Structs:** cfi_init_struct, cfi_txn_struct, cfi_credit_struct, cfi_block_struct

### Intel Checker Macros (Common)

**Assertions:**
- `ASSERTS_TRIGGER(name, trig, prop, clk, rst, MSG)` - Same-cycle: trig |-> prop
- `ASSERTS_DELAYED_TRIGGER(name, trig, delay, prop, clk, rst, MSG)` - Next-cycle: trig |-> ##delay prop
  - **delay is integer parameter** (1, 2, 3, etc.)
  - **prop is Boolean expression** (NO temporal operators!)
- `ASSERTS_EVENTUALLY_HOLDS(name, en, prop, clk, rst, MSG)` - Unbounded: en |-> s_eventually prop
- `ASSERTS_STABLE(name, sig, start_ev, end_ev, clk, rst, MSG)` - Signal stable between events
- `ASSERTS_MUTEXED(name, sig, clk, rst, MSG)` - At most one bit high
- `ASSERTS_ONE_HOT(name, sig, clk, rst, MSG)` - Exactly one bit high
- `ASSERTS_FORBIDDEN(name, cond, clk, rst, MSG)` - Condition never true

**Assumptions:**
- `ASSUMES_TRIGGER`
- `ASSUMES_EVENTUALLY_HOLDS`
- `ASSUMES_STABLE`

**Covers:**
- `COVERS`
- `COVERS_TRIGGER`

### Message Macros
- Assertions: `` `ERR_MSG("description") ``
- Covers: `` `FV_<CLUSTER>_COVER_MSG("description") ``

### Protocol Checker Integration Quick Steps

**For AXI4↔CFI Bridge:**
1. Include `axi4_master.sv` in top.va
2. Bind axi4_master to DUT with ALL AXI signals
3. Define CFI structs in spec.va (init, txn, credit, block)
4. Instantiate FVCompMonCFI with channel enables and VC configs
5. Map signals in map.va (AXI structs, CFI signals)
6. Write properties ONLY for bridge FSM, transformation, and mapping

**For Bidirectional AXI4 (AXI4↔AXI4 with FIFO/Buffer):**
1. Include both `axi4_master.sv` and `axi4_slave.sv` in top.va
2. Bind axi4_master to SLAVE interface (input side, e.g., clkA domain)
3. Bind axi4_slave to MASTER interface (output side, e.g., clkB domain)
4. Map signals with clear naming convention (_A for input, _B for output)
5. Map FIFO status signals (empty/full flags) in map.va
6. Write properties ONLY for: FIFO control, CDC behavior, transaction ordering, back-pressure

**For Other Protocol Bridges:**
- Find appropriate VIP/CompMon for each protocol
- DO NOT write manual protocol properties
- Focus properties on bridge-specific logic only

---

### Pattern 6: Scoreboard / Reference Model

**RTL:** Transaction tracking with expected vs actual comparison (bridges, data-path logic, reorder buffers).

**Architecture (in spec.va):**
```systemverilog
// Define a reference model that tracks expected behaviour
// Use map.va signals — never DUT internal paths in properties

// Scoreboard approach: track "in-flight" transactions
// 1. Capture input transaction on ingress valid
// 2. Predict expected output
// 3. Compare when output valid fires

// Example: data integrity check for a bridge
//logic [DATA_W-1:0] captured_data;
//logic data_captured;

// Capture on ingress
//always_ff @(posedge clk or posedge rst) begin
//    if (rst) begin
//        data_captured <= '0;
//        captured_data <= '0;
//    end else if (ingress_valid && ingress_ready) begin
//        captured_data <= ingress_data;
//        data_captured <= 1'b1;
//    end else if (egress_valid && egress_ready) begin
//        data_captured <= 1'b0;
//    end
//end
```

**Properties:**
```systemverilog
// Data integrity: output matches captured input (for pass-through)
//`FV_<CLUSTER>_ASSERTS_TRIGGER(T_<cluster>_FPV_sb_assert_data_integrity,
//    egress_valid && egress_ready && data_captured,
//    egress_data == captured_data,
//    clk, rst, `ERR_MSG("Scoreboard: output data mismatch"));

// No lost transactions: every input eventually produces output
//`FV_<CLUSTER>_ASSERTS_EVENTUALLY_HOLDS(T_<cluster>_FPV_sb_assert_no_lost_txn,
//    ingress_valid && ingress_ready,
//    egress_valid && egress_ready,
//    clk, rst, `ERR_MSG("Scoreboard: transaction lost"));

// No spurious outputs: egress only when something was captured
//`FV_<CLUSTER>_ASSERTS_TRIGGER(T_<cluster>_FPV_sb_assert_no_spurious,
//    egress_valid,
//    data_captured,
//    clk, rst, `ERR_MSG("Scoreboard: spurious output without input"));
```

**When to use:** Data-path bridges, reorder buffers, protocol converters, credit-based flows where end-to-end integrity matters.

---

### Pattern 7: Multi-Clock Domain Proofs

**RTL:** Designs with multiple clock domains (CDC crossings, async FIFOs, dual-clock bridges).

**Clock Setup (conf.tcl):**
```tcl
# Declare all clocks with -both_edges
clock -clear
clock prim0_clk -both_edges
clock side_clk -both_edges

# For async domains: tell Jasper clocks are unrelated
set_clock_groups -asynchronous -group {prim0_clk} -group {side_clk}
```

**Signal Mapping (map.va):**
```systemverilog
// Separate namespace macros per clock domain
`define FAST_DOM `TOP.fast_domain
`define SLOW_DOM `TOP.slow_domain

// Map domain-specific signals
logic fast_clk, slow_clk;
assign fast_clk = `FAST_DOM.clk;
assign slow_clk = `SLOW_DOM.clk;

// Map CDC boundary signals
logic [W-1:0] gray_wr_ptr_sync;
assign gray_wr_ptr_sync = `SLOW_DOM.wr_ptr_gray_synced;
```

**Properties:**
```systemverilog
// Gray-code pointer stability across domain
`FV_<CLUSTER>_ASSERTS_TRIGGER(T_<cluster>_FPV_cdc_assert_gray_onehot_change,
    $changed(gray_wr_ptr_sync),
    $onehot(gray_wr_ptr_sync ^ $past(gray_wr_ptr_sync)),
    slow_clk, rst, `ERR_MSG("Gray pointer changed >1 bit"));

// FIFO coherency: read ptr never passes write ptr
`FV_<CLUSTER>_ASSERTS_TRIGGER(T_<cluster>_FPV_cdc_assert_no_overflow,
    1'b1,
    !(rd_ptr_gray == wr_ptr_gray && !empty_flag),
    slow_clk, rst, `ERR_MSG("CDC FIFO overflow"));

// Metastability assumption: synchronized signal is stable for at least 2 cycles
`FV_<CLUSTER>_ASSUMES_STABLE(T_<cluster>_FPV_cdc_assume_sync_stable,
    sync_out, $rose(sync_out), $fell(sync_out),
    slow_clk, rst, `ERR_MSG("Sync output not stable"));
```

**Task Separation for Multi-Clock:**
```tcl
# Create separate tasks per clock domain
task -create fast_domain -source_task <embedded> -copy {{*fast*} {*prim0*}}
task -create slow_domain -source_task <embedded> -copy {{*slow*} {*side*}}
task -create cdc_crossing -source_task <embedded> -copy {{*cdc*} {*sync*} {*gray*}}

# Prove each domain independently
prove -task fast_domain -time_limit 1800s
prove -task slow_domain -time_limit 1800s
prove -task cdc_crossing -time_limit 3600s
```

**When to use:** Async FIFO designs, clock-domain bridges, any DUT with `set_clock_groups -asynchronous`.
