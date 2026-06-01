---
name: "SystemVerilog RTL Code Review Rules"
applyTo: "src/**/rtl/*.sv,src/**/rtl/*.vs,src/**/rtl/*.svh,src/**/rtl/*.vh"
description: "Rules for reviewing SystemVerilog RTL code for functional bugs and lint violations. Focus on critical bugs that can cause silicon failures, and use examples to identify issues and corrections."
keywords: rtl, systemverilog, code review, lint, silicon bug prevention
---

# SystemVerilog RTL Code Review Rules
*Developed by Rob Slater, Tsvi Mostovicz, Ron Rais, Shay Shushan, and AISG Team*

Review SystemVerilog RTL code for bugs and lint violations. Use bad examples to identify issues and good examples for corrections.

---

## Bug Rules ⚠️ ALL CRITICAL

**All bug rules represent CRITICAL functional errors that can cause silicon failures.** Each must be carefully reviewed.

---

### BUGS/Rule_1: FIFO Empty/Full Detection
FIFO empty signal must use state machine state, not pointer comparison (pointers match when full due to wraparound).

```systemverilog
// ❌ Bad: Pointer comparison fails when full
always_comb FifoEmpty = (RdPtrS100H[PTR_WIDTH:0] == WrPtrS100H[PTR_WIDTH:0]);

// ✅ Good: Use state machine
always_comb FifoEmpty = (FifoStateS100H == FIFO_EMPTY);
```

---

### BUGS/Rule_2: Array Index Swap
Array indices swapped when accessing multi-dimensional arrays (read/write index order).

```systemverilog
// ❌ Bad: Indices swapped [gi][j] vs definition [gj][gi]
assign rdwr_hzd[gj][gi] = re_i[gi] && we_i[gj] && (rd_addr_i[gi] == wr_addr_i[gj]);
if(rdwr_hzd[gi][j]) rd_data_fwd[gi] = wr_data_i[j];  // Wrong order

// ✅ Good: Consistent indexing
if(rdwr_hzd[j][gi]) rd_data_fwd[gi] = wr_data_i[j];  // Matches definition
```

---

### BUGS/Rule_3: Counter Overflow
Counter increments without bounds checking causes overflow.

```systemverilog
// ❌ Bad: No bounds checking
if (enable) count <= count + 1;

// ✅ Good: Explicit saturation
if (enable) count <= (count == 4'b1111) ? 4'b1111 : count + 1;
```

---

### BUGS/Rule_4: Signal Naming Convention Violation
Assignment from 'H' (active-high) suffix to 'L' (active-low) suffix signal violates naming convention.

```systemverilog
// ❌ Bad: H to L assignment
assign IsAddDPUnitAllUopVM305L = IsAddDPUnitAllUopVM305H;

// ✅ Good: H to H assignment
assign IsAddDPUnitAllUopVTwoM305H = IsAddDPUnitAllUopVOneM305H;
```

---

### BUGS/Rule_5: Copy/Paste Error
Repeated code with incorrect signal names from copy/paste.

```systemverilog
// ❌ Bad: Wrong enable signal (U112H instead of U113H)
`EN_MSFF(ReqOpcodeU113H, ReqOpcodeU112H, clk, ReqValidU112H)
`EN_MSFF(ReqOpcodeU114H, ReqOpcodeU113H, clk, ReqValidU112H)

// ✅ Good: Matching enable
`EN_MSFF(ReqOpcodeU113H, ReqOpcodeU112H, clk, ReqValidU112H)
`EN_MSFF(ReqOpcodeU114H, ReqOpcodeU113H, clk, ReqValidU113H)

// ❌ Bad: Duplicate enum values
PmonAmapIncr = (CfgPmonUnitMask[0] & (AmapTgtS512H == OQI_DEST_DRAM)) |
               (CfgPmonUnitMask[1] & (AmapTgtS512H == OQI_DEST_DRAM)) |  // Duplicate
               (CfgPmonUnitMask[7] & (AmapTgtS512H == OQI_DEST_CONF_P2P));  // Duplicate

// ✅ Good: Unique enum values
PmonAmapIncr = (CfgPmonUnitMask[0] & (AmapTgtS512H == OQI_DEST_DRAM)) |
               (CfgPmonUnitMask[1] & (AmapTgtS512H == OQI_DEST_ABORT)) |
               (CfgPmonUnitMask[7] & (AmapTgtS512H == OQI_DEST_REM_P2P));
```

---

### BUGS/Rule_6: Missing Array Index on Single-Bit Array
Compiles cleanly, simulates without errors, but causes **silent functional failures in silicon**.

Single-bit array (e.g., `[7:7]`, `[5:5]`) referenced without bit index causes type mismatch. SystemVerilog treats it as array reference instead of bit value, breaking clock gates, power logic, etc.

```systemverilog
// ❌ Bad: Missing [7] - treats as array, not bit
node [7:7] fubEnM304H;
fubEnPwrM304H[7] = fubEnM304H | sirstorpwrOvrM3n2H;  // Type mismatch

// ✅ Good: Explicit [7] index
fubEnPwrM304H[7] = fubEnM304H[7] | sirstorpwrOvrM3n2H;

// ❌ Bad: Clock gate enable without bit select
logic [5:5] enableSignal;
`CORE_ICG_PH1(ClkOut, ClkIn, 1'b1, enableSignal | reset, 1'b0)

// ✅ Good: Explicit [5] index
`CORE_ICG_PH1(ClkOut, ClkIn, 1'b1, enableSignal[5] | reset, 1'b0)

// ✅ Exception: Flop output (LHS of flop macro)
`CORE_MSFF(fubEnM304H, fubEnM303H, clk)  // OK: Array structure transferred
```

**Detection**: Find all `[N:N]` declarations, verify every reference includes `[N]` except flop LHS.

---

### BUGS/Rule_7: Initializing logic in declaration
The code works in simulation, but will not synthesize to the desired value because it's treated as an initial statement.

```systemverilog
// ❌ Bad: initialization during declaration
logic my_sig = 1'b1;

// ✅ Good: initialization after declaration.  This case uses a set MSFF.
logic my_sig;
always_ff @(posedge clk or posedge set) begin
   if (set)
      my_sig <= 1'b1;
   else
      my_sig <= d;
end

// ✅ Good: initialization after declaration.  This case uses modification after initialization.
logic my_sig;
always @(*) begin
   my_sig = 1'b1;
   if (cond_a)
      my_sig = 1'b0;
end
```

---

## Lint Rules

### LINT/Rule_1: Out of Bounds
Array index exceeds declared bounds.
```systemverilog
// ❌ Bad: in[2] out of bounds [1:0]
input wire in[1:0]; assign out = in[2];
// ✅ Good
assign out = in[1];
```

---

### LINT/Rule_2: Parallel Case Violation
Case items overlap in `parallel_case`.
```systemverilog
// ❌ Bad: 2'b1x overlaps 2'b11
(* parallel_case *)casex(sel)
    2'b1x: out = in1;
    2'b11: out = in2;
endcase
// ✅ Good
(* parallel_case *)casex(sel)
    2'b10: out = in1;
    2'b11: out = in2;
endcase
```

---

### LINT/Rule_3: Case Not Full
Missing default clause or uncovered values.
```systemverilog
// ❌ Bad: No default
casex (sel)
    3'b11?: out = ^in;
    3'b10x: out = |in;
endcase
// ✅ Good
casex (sel)
    3'b11?: out = ^in;
    3'b10x: out = |in;
    default: out = ~|in;
endcase
```

---

### LINT/Rule_4: Infinite Loop
Loop condition never becomes false.
```systemverilog
// ❌ Bad: i increments instead of decrements
for (int i=5; i>0; i++) out[i] = in1[i];
// ✅ Good
for (int i=5; i>0; i--) out[i] = in1[i];
```

---

### LINT/Rule_5: Non-Static Loop Bounds
Loop bounds not statically computable for synthesis.
```systemverilog
// ❌ Bad: in2 not static
for (int i=0; i<in2; i++) out[i] = in1[i];
// ✅ Good
for (int i=0; i<int'(in2); i++) out[i] = in1[i];
```

---

### LINT/Rule_6: System Task as Function
System task used where it cannot return value.
```systemverilog
// ❌ Bad: $display cannot return value
out = $display(in);
// ✅ Good
out = in; $display(in);
```

---

### LINT/Rule_7: Recursive Call
Non-synthesizable recursive function/task calls.
```systemverilog
// ❌ Bad: foo calls goo calls foo
function foo; foo = goo(n, m); endfunction
function goo; goo = foo(x, y); endfunction
// ✅ Good
function goo; goo = x + y; endfunction
```

---

### LINT/Rule_8: Negative Bound
Array declaration with negative bound.
```systemverilog
// ❌ Bad
logic bad[7:-1];
// ✅ Good
logic bad[7:6];
```

---

### LINT/Rule_9: Excessive Parameters
Module instantiation has more parameters than definition.
```systemverilog
// ❌ Bad: 3 params provided, 2 defined
module son #(parameter x=10, y=20)(output int out1);
son #(22, 33, 48) s2 (out1);
// ✅ Good
son #(3, 4) s2 (out1);
```

---

### LINT/Rule_10 & 11: Reset Polarity Mismatch
Reset condition polarity doesn't match edge sensitivity.
```systemverilog
// ❌ Bad: negedge rst with non-inverted condition
always @(posedge clock or negedge rst)
    if (rst) q <= rstd;  // Should be ~rst
// ✅ Good
always @(posedge clock or negedge rst)
    if (~rst) q <= rstd;

// ❌ Bad: posedge rst with inverted condition
always @(posedge clock or posedge rst)
    if (~rst) q <= 1'b0;  // Should be rst
// ✅ Good
always @(posedge clock or posedge rst)
    if (rst) q <= 1'b0;
```

---

### LINT/Rule_12: Non-Constant Reset Value
Non-constant reset value creates glitches.
```systemverilog
// ❌ Bad: rstd can glitch
if (rst) q <= rstd;
// ✅ Good
if (rst) q <= (rstd) ? '1 : '0;
```

---

### LINT/Rule_13: Constant Width Mismatch
Constant width doesn't match parameter width.
```systemverilog
// ❌ Bad: 32-bit constants truncated to 3-bit parameter
module son #(parameter [2:0] x=10, y=20);
// ✅ Good: Use unsized constants
module son #(parameter [2:0] x='0, y='1);
```

---

### LINT/Rule_14: Undeclared Signal
Signal used but not declared, implicit net created.
```systemverilog
// ❌ Bad: 'a' undefined
assign a = ~in; assign out = a;
// ✅ Good
logic a; assign a = ~in;
```

---

### LINT/Rule_15: Ignored Event Control
Event control on statement ignored in always block.
```systemverilog
// ❌ Bad: Event on statement
always begin @(posedge clk) a = b; end
// ✅ Good: Event in sensitivity list
always @(posedge clk) begin a = b; end
```

---

### LINT/Rule_16: Cross-Module Write
Writing to signal in another module via hierarchical reference.
```systemverilog
// ❌ Bad: Write to s1.a
assign s1.a = in1;
// ✅ Good: Use ports
son s1(in1);
```

---

### LINT/Rule_17: Macro Redefinition
Macro redefined without `undef.
```systemverilog
// ❌ Bad
`define mm 1
`define mm 2  // Redefinition
// ✅ Good
`define mm 1
`define mm1 2  // Different name
```

---

### LINT/Rule_18: Sized Constant Truncation
Explicitly sized constant larger than target.
```systemverilog
// ❌ Bad: 11-bit to 8-bit
wire [7:0] ss = 11'b0;
// ✅ Good
wire [7:0] ss = 8'b0;
```

---

### LINT/Rule_19: Unconnected Port
Module instantiation has unconnected ports.
```systemverilog
// ❌ Bad: Missing ports
son s1(in1, out1);  // in2 unconnected
// ✅ Good
son s1(in1, in2, out1);
```

---

### LINT/Rule_20: Parameter Should Be Localparam
Internal parameter should be localparam when module has parameter port list.
```systemverilog
// ❌ Bad: parameter in body when #(parameter list) exists
module son #(parameter x=10, y=20);
    parameter a=3, b=4;  // Should be localparam
// ✅ Good
module son #(parameter x=10, y=20);
    localparam a=3, b=4;
```

---

### LINT/Rule_21: Non-Constant Async Reset
Async reset assigns non-constant value, causing glitches if value changes during reset.
```systemverilog
// ❌ Bad: rstd changes during rst cause RTL/synthesis mismatch
always @(posedge clock or posedge rst)
    if (rst) q <= rstd;
// ✅ Good
always @(posedge clock or posedge rst)
    if (rst) q <= 1'b0;
```

---

### LINT/Rule_22: Width Extension
Expression implicitly extended to wider context.
```systemverilog
// ❌ Bad: 3-bit extended to 6-bit
input bit [2:0] in; foo(in, out);  // foo expects 6-bit
// ✅ Good
foo(bit6'(in), out);  // Explicit cast
```

---

### LINT/Rule_23: Width Truncation with Data Loss
Expression wider than context, data truncated.
```systemverilog
// ❌ Bad: 4-bit truncated to 3-bit
output wire [2:0] o1;
assign o1 = i1;  // i1 is [3:0]
// ✅ Good
assign o1 = i1[2:0];  // Explicit
```

---

### LINT/Rule_24: Unassigned Signal
Signal read but never assigned.
```systemverilog
// ❌ Bad: foo never assigned
logic foo; assign out = foo;
// ✅ Good
logic foo; assign foo = 1'b0;
```

---

### LINT/Rule_25: Non-Synthesizable Case with X/Z
Case item with X/Z compared to non-constant.
```systemverilog
// ❌ Bad: 2'b1x not synthesizable
case(sel)
    2'b1x: out = in1;
// ✅ Good
case(sel)
    2'b10: out = in1;
```

---

## Quick Reference Checklist

### Critical Bug Patterns
- [ ] **Pipeline stages** - All signals in calculations use correct stage (Rule_1)
- [ ] **FIFO logic** - Empty/full use state machine, not pointers (Rule_2)
- [ ] **Array indexing** - No swapped read/write indices (Rule_3)
- [ ] **Counter bounds** - Explicit saturation/overflow handling (Rule_4)
- [ ] **Signal naming** - No H→L assignments (Rule_5)
- [ ] **Copy/paste** - No duplicated constants, wrong enables, or stage mismatches (Rule_6)
- [ ] **Single-bit arrays** - All `[N:N]` refs include `[N]` except flop LHS (Rule_9)

### Key Lint Checks
- [ ] **Bounds** - All array/bit accesses within declared range (Rule_1)
- [ ] **Case coverage** - All cases have defaults, no overlaps in parallel_case (Rule_2, 3)
- [ ] **Loops** - Terminate correctly, static bounds (Rule_4, 5)
- [ ] **Reset polarity** - Condition matches edge (posedge→rst, negedge→~rst) (Rule_10, 11)
- [ ] **Reset values** - Constants only in async reset (Rule_12, 21)
- [ ] **Width matching** - No implicit extension/truncation (Rule_13, 18, 22, 23)
- [ ] **Declarations** - All signals declared, proper parameter/localparam (Rule_14, 20)
- [ ] **Connectivity** - All ports connected, no cross-module writes (Rule_16, 19)

### Best Practices
- [ ] Blocks >7 lines have labels
- [ ] Clear comments on purpose, inputs, outputs, assumptions
- [ ] Use `logic` over `reg`, `enum`/`struct`/`typedef` for clarity
- [ ] Consistent 4-space indentation, aligned operators, no trailing whitespace

---

**Review Process**: Check bug patterns first (functional errors), then lint rules (synthesis/style issues). Reference examples for corrections.

