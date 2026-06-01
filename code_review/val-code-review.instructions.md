---
name: "Validation Code Craftsmanship Review"
applyTo: "src/val/**/*.sv,src/val/**/*.svh,**/bin/**/*.py,**/scripts/**/*.py"
description: "Software craftsmanship review for validation code. Applies Clean Code principles from the SWIFT training program (based on Robert C. Martin's Clean Coders series). These rules are ADDITIVE to Copilot's standard functional review."
keywords: clean code, swift, validation, systemverilog, uvm, python, software craftsmanship, naming, functions, solid, tdd, testing
---

# Validation Code Craftsmanship Review
*Based on the SWIFT Software Craftsmanship Training Program — Clean Coders episodes by Robert C. Martin*

> **Scope**: These rules focus exclusively on **software craftsmanship** — readability, maintainability, and testability. They are **additive** to Copilot's default functional review and do not duplicate it. Flag at the `suggestion` level unless a rule indicates a design problem that would impair testability or extensibility, in which case use `warning`.

---

## Naming Rules (SWIFT Yellow Belt — Episode 2)

**Principle**: Names are the primary communication channel in code. A well-named symbol makes the code self-documenting.

---

### NAMING/Rule_1: Names Reveal Intent

A name should answer *why it exists*, *what it does*, and *how it is used* — without requiring a comment.

```systemverilog
// ❌ Bad: abbreviations and opaque names obscure intent
logic [31:0] d;              // elapsed time?
function void chk_rc();      // check what?

// ✅ Good: name reads like documentation
logic [31:0] elapsed_simulation_cycles;
function void check_read_completion();
```

```python
# ❌ Bad
def proc(d, t):
    return d * t

# ✅ Good
def compute_expected_latency(distance_cycles: int, throughput: int) -> int:
    return distance_cycles * throughput
```

---

### NAMING/Rule_2: Avoid Abbreviations and Encodings

Abbreviations force readers to decode before they can understand. The only exception is domain jargon that every team member knows (e.g., `TLB`, `PCIe`, `snoop`).

```systemverilog
// ❌ Bad: cryptic abbreviations
logic [63:0] pnd_wrt_lst [$];
function void proc_wr_rsp();

// ✅ Good: full words, clear meaning
logic [63:0] pending_write_requests [$];
function void process_write_response();
```

---

### NAMING/Rule_3: Method and Field Names Match Their Role

- Methods/tasks (actions) should be **verb phrases**: `verify_`, `check_`, `collect_`, `send_`, `wait_for_`, `get_`
- Classes/units (things) should be **noun phrases**: `memory_controller`, `transaction`, `config`
- Boolean fields/returns should read as propositions: `is_valid`, `has_pending_request`, `was_observed`

```systemverilog
// ❌ Bad: noun used as method name; verb used for a field
function bit response_valid();
bit do_check;  // what does "do" mean?

// ✅ Good
function bit is_response_valid();
bit check_enabled;
```

---

### NAMING/Rule_4: No Magic Numbers

Unnamed literal constants hide their purpose. Give them a name that explains their role. When the value is shared or part of an interface, use a named constant or parameter. When the value is only used inside one function, assigning it to a well-named local variable is also acceptable.

```systemverilog
// ❌ Bad: what does 256 mean? Why 3?
if (transaction_count > 256) `uvm_error("OVERFLOW", "overflow");
#3;

// ✅ Good
localparam int MAX_OUTSTANDING_TRANSACTIONS = 256;
localparam int PIPELINE_DRAIN_CYCLES = 3;

if (transaction_count > MAX_OUTSTANDING_TRANSACTIONS) `uvm_error("OVERFLOW", "overflow");
#(PIPELINE_DRAIN_CYCLES);

// ✅ Also good: function-local names are fine when the value is only used here
function void wait_for_pipeline_drain();
    int pipeline_drain_cycles = 3;
    repeat (pipeline_drain_cycles) @(posedge clk);
endfunction
```

```python
# ❌ Bad: the reader has to guess what 5 and 2 represent
if observed_retry_count >= 5:
    raise RuntimeError("Too many retries")
timeout_cycles = base_cycles * 2

# ✅ Good: shared meaning should be a named constant
MAX_OBSERVED_RETRIES = 5
TIMEOUT_SCALE_FACTOR = 2

if observed_retry_count >= MAX_OBSERVED_RETRIES:
    raise RuntimeError("Too many retries")
timeout_cycles = base_cycles * TIMEOUT_SCALE_FACTOR

# ✅ Also good: a well-named local variable is acceptable when scoped to one function
def compute_timeout_cycles(base_cycles: int) -> int:
    timeout_scale_factor = 2
    return base_cycles * timeout_scale_factor
```

---

## Function / Method Rules (SWIFT Yellow Belt — Episodes 3–4)

**Principle**: Functions should do *one thing*, do it well, and do it only.

---

### FUNCTION/Rule_1: Functions Do One Thing

Treat "and" in a function/task name as a design smell, not an automatic failure.

- It may mean the function is doing more than one thing. Extract responsibilities.
- It may mean the name is at the wrong level of abstraction. Rename to a single higher-level intent if the steps are inseparable.

Use this reviewer prompt: "Is this truly one responsibility at one abstraction level?"

When possible, structure examples and fixes in step-down order: show the high-level orchestration first, then place helper implementations immediately below in the order they are called.

```systemverilog
// ❌ Bad: collects transaction AND validates it AND logs it
function void collect_and_validate_transaction(transaction trans);
    // collect
    transactions_seen.push_back(trans);
    // validate
    if (trans.address > MAX_ADDR) `uvm_error(...);
    // log
    `uvm_info("TRANS", $sformatf("transaction seen: %0h", trans), UVM_LOW)
endfunction

// ✅ Good: each function has a single, named responsibility and high-level intent function is named appropriately.
function void validate_transaction(transaction trans);
    record_transaction(trans);
    validate_transaction_address(trans);
    `uvm_info("TRANS", $sformatf("transaction validated: %0h", trans), UVM_LOW)
endfunction

function void record_transaction(transaction trans);
    transactions_seen.push_back(trans);
endfunction

function void validate_transaction_address(transaction trans);
    if (trans.address > MAX_ADDR) `uvm_error(...);
endfunction

```

---

### FUNCTION/Rule_2: Limit Parameters (Niladic > Monadic > Dyadic > Triadic)

More than two parameters is a signal to introduce a data structure. More than three usually indicates the function is doing too much.

```systemverilog
// ❌ Bad: five parameters obscure the relationship between arguments
function void send_request(logic [31:0] addr, logic [31:0] data, int len, 
                           int tid, request_opcode_t opcode);
    // ...
endfunction

// ✅ Good: group related data; the struct documents the relationship
typedef struct {
    logic [31:0]  address;
    logic [31:0]  data;
    int           length;
    int           tid;
    request_opcode_t opcode;
} request_t;

function void send_request(request_t req);
    // ...
endfunction
```

---

### FUNCTION/Rule_3: Avoid Boolean Flag Arguments

A boolean parameter is a sign that the function has an invisible branch inside it. Extract two functions instead.

```systemverilog
// ❌ Bad: caller has no idea what 1 means at the call site
monitor.check_completion(1);
monitor.check_completion(0);

// ✅ Good: intent is clear at every call site
monitor.check_read_completion();
monitor.check_write_completion();
```

---

### FUNCTION/Rule_4: Command-Query Separation

A function either *changes state* (command) or *returns information* (query) — never both. Side-effects inside query functions make code unpredictable.

```systemverilog
// ❌ Bad: query that also increments a counter (hidden side effect)
function bit is_fifo_empty();
    outstanding_check_count++;   // side effect!
    return (fifo_depth == 0);
endfunction

// ✅ Good: pure query; count the call at the call site if needed
function bit is_fifo_empty();
    return (fifo_depth == 0);
endfunction
```

---

### FUNCTION/Rule_5: Don't Repeat Yourself (DRY)

Duplicated logic means duplicated bugs. Extract shared logic into a named, reusable function.

```systemverilog
// ❌ Bad: the same address range check written twice
function void check_read_transaction(transaction trans);
    if (trans.address < BASE_ADDR || trans.address > BASE_ADDR + REGION_SIZE)
        `uvm_error(...);
    ...
endfunction

function void check_write_transaction(transaction trans);
    if (trans.address < BASE_ADDR || trans.address > BASE_ADDR + REGION_SIZE)
        `uvm_error(...);  // same logic, duplicate code
    ...
endfunction

// ✅ Good: extract once, keep top-level checks at one abstraction level
function void check_read_transaction(transaction trans);
    check_transaction_address_range(trans);
    ...
endfunction

function void check_write_transaction(transaction trans);
    check_transaction_address_range(trans);
    ...
endfunction

function void check_transaction_address_range(transaction trans);
    if (is_address_outside_valid_range(trans.address))
        `uvm_error(...);
endfunction

function bit is_address_outside_valid_range(logic [31:0] address);
    return (address < BASE_ADDR || address > BASE_ADDR + REGION_SIZE);
endfunction
```

```python
# ❌ Bad: duplicate range check logic in two places
def check_read_transaction(transaction):
    if transaction.address < BASE_ADDR or transaction.address > BASE_ADDR + REGION_SIZE:
        raise ValueError("Address outside valid range")
    ...


def check_write_transaction(transaction):
    if transaction.address < BASE_ADDR or transaction.address > BASE_ADDR + REGION_SIZE:
        raise ValueError("Address outside valid range")
    ...


# ✅ Good: extract once, name the shared rule
def check_read_transaction(transaction):
    check_transaction_address_range(transaction)
    ...


def check_write_transaction(transaction):
    check_transaction_address_range(transaction)
    ...


def check_transaction_address_range(transaction):
    if is_address_outside_valid_range(transaction.address):
        raise ValueError("Address outside valid range")


def is_address_outside_valid_range(address: int) -> bool:
    return address < BASE_ADDR or address > BASE_ADDR + REGION_SIZE
```

---

## Comment Rules (SWIFT Yellow Belt — Episode 5)

**Principle**: Comments are a failure to express intent in code. Use them sparingly and purposefully.

---

### COMMENT/Rule_1: No Redundant Comments

A comment that restates what the code already says adds noise and becomes a maintenance burden when the code changes but the comment doesn't.

```systemverilog
// ❌ Bad: comment says exactly what the code says
// Increment the counter
transaction_count++;

// Check if fifo is empty
if (fifo_depth == 0) ...

// ✅ Good: no comment needed — the code is self-documenting
transaction_count++;

if (is_fifo_empty()) ...
```

---

### COMMENT/Rule_2: No Commented-Out Dead Code

Commented-out code accumulates, confuses readers, and is rarely cleaned up. If code should not exist, delete it. Version control is the safety net.

Exception: temporarily disabled code may be acceptable when the team knows it will be restored after a specific trigger. In that case, require a `FIXME` that states why the code is disabled and what event re-enables it, typically including an HSD or equivalent tracking ticket.

```systemverilog
// ❌ Bad: what is this doing here? Is it intentional?
function void check_response(response resp);
    // if (resp.status == ERROR_STATUS) `uvm_error(...);
    if (resp.status == TIMEOUT_STATUS) `uvm_error(...);
    // log_response(resp);
endfunction

// ✅ Good: remove it; git history preserves it if needed
function void check_response(response observed_response);
    if (observed_response.status == TIMEOUT_STATUS) `uvm_error(...);
endfunction

// ✅ Also acceptable: temporary disable with explicit re-enable trigger
function void check_response(response observed_response);
    // FIXME: Re-enable ERROR_STATUS checking after the timeout-classification fix lands;
    // See https://hsdes.intel.com/appstore/article-one/#/2101xxxxxxx
    // if (observed_response.status == ERROR_STATUS) `uvm_error(...);
    if (observed_response.status == TIMEOUT_STATUS) `uvm_error(...);
endfunction
```

---

### COMMENT/Rule_3: Comments Explain WHY, Not WHAT

The only comment worth writing is the one that explains *intent the code cannot express* — a non-obvious algorithmic choice, a workaround for a hardware bug, or a cross-reference to a spec section.

```systemverilog
// ❌ Bad: explains WHAT (already obvious from the code)
// Wait for the DUT to drain its pipeline
#PIPELINE_DRAIN_CYCLES;

// ✅ Good: explains WHY (not obvious — spec reference + workaround)
// HSD-22017xxxxxx: DUT requires 3 extra cycles after reset de-assertion
// before the first transaction can be safely issued (silicon errata).
#POST_RESET_GUARD_CYCLES;
```

```python
# ❌ Bad: comment explains WHAT the code already says
# Sort transactions by timestamp
transactions.sort(key=lambda transaction: transaction.timestamp)

# ✅ Good: comment explains WHY this implementation was chosen
# Keep Python-side ordering stable so equal-timestamp transactions preserve
# the monitor arrival order expected by the scoreboard.
transactions.sort(key=lambda transaction: transaction.timestamp)
```

---

## Testing Rules (SWIFT — Yellow Belt Ep 6; Green Belt Ep 19–21)

**Principle**: Tests are first-class code. Unclean tests rot the test suite and erode confidence in CI.

---

### TEST/Rule_1: Test Names Express Intent

The test name should complete the sentence: *"This test verifies that...\"*. A reader should understand what failure means without reading the test body.

```systemverilog
// ❌ Bad: tells you nothing about what was checked
`TEST(test_1)
    // ...
`ENDTEST

`TEST(test_write)
    // ...
`ENDTEST

// ✅ Good: failure reads like a specification violation
`TEST(write_to_read_only_region_should_trigger_error_response)
    // ...
`ENDTEST

`TEST(back_to_back_reads_should_complete_in_order)
    // ...
`ENDTEST
```

```python
# ❌ Bad
def test_latency():
    ...

# ✅ Good
def test_read_latency_does_not_exceed_spec_maximum():
    ...
```

---

### TEST/Rule_2: One Behavior Per Test

A test that asserts many things makes failures harder to diagnose. Each test should have a single, focused assertion about a single behavior.

```systemverilog
// ❌ Bad: multiple assertions in one test
`TEST(response_fields_are_correct)
    // ... Arrange-Act code here ...
    assert (resp.status == OKAY)
    else `uvm_error("TEST", "response status failed");
    assert (resp.data == EXPECTED_DATA)
    else `uvm_error("TEST", "response data failed");
    assert (resp.tid == REQUEST_TID)
    else `uvm_error("TEST", "response tid failed");
`ENDTEST

// ✅ Good: separate tests, single clear assertion each
`TEST(response_status_is_okay)
    // ... Arrange-Act code here ...
    assert (resp.status == OKAY)
    else `uvm_error("TEST", "response status failed");
`ENDTEST

`TEST(response_data_matches_write_value)
    // ... Arrange-Act code here ...
    assert (resp.data == EXPECTED_DATA)
    else `uvm_error("TEST", "response data failed");
`ENDTEST

`TEST(response_tid_matches_request_tid)
    // ... Arrange-Act code here ...
    assert (resp.tid == REQUEST_TID)
    else `uvm_error("TEST", "response tid failed");
`ENDTEST
```

---

### TEST/Rule_3: Arrange-Act-Assert (AAA) Structure

Every test should have three clearly separated phases. Mixing them makes tests hard to read and debug.

```systemverilog
// ✅ Explicit AAA structure — a reader can immediately find each phase
`TEST(write_then_read_returns_written_value)
    write_request write_req;
    read_response read_resp;

    // Arrange: configure a simple write transaction
    write_req.address = TEST_ADDRESS;
    write_req.data    = KNOWN_DATA_PATTERN;

    // Act: send write, then read back
    driver.send_write(write_req);
    read_resp = driver.send_read(TEST_ADDRESS);

    // Assert: verify the value was retained
    if (read_resp.data !== KNOWN_DATA_PATTERN)
        `uvm_error("MISMATCH", "read-after-write mismatch");
`ENDTEST
```

---

### TEST/Rule_4: FIRST Principles for Checkers

Checkers and monitors should follow FIRST:

| Letter | Meaning | Validation Implication |
|--------|---------|----------------------|
| **F**ast | Checks should not stall simulation | Avoid polling loops; use event-driven callbacks |
| **I**ndependent | Tests should not share mutable state | Use local variables or passed parameters; avoid global counters |
| **R**epeatable | Same result every run | Avoid non-deterministic timing without explicit synchronization |
| **S**elf-validating | Must produce a clear pass/fail | Use `uvm_fatal()` / `uvm_error()` / assertions — never rely on a human to read logs |
| **T**imely | Written before or with the DUT | Prefer writing checkers before the feature is implemented |

```systemverilog
// ❌ Bad: checker uses mutable global state — violates Independent
int global_error_count;
function void check_response(response r);
    global_error_count++;  // shared across all scenarios
endfunction

// ✅ Good: checker is self-contained
function void check_response(response observed_response);
    if (observed_response.status != OKAY) begin
        `uvm_error("CHK", $sformatf("Unexpected response status: %0d", observed_response.status));
    end
endfunction
```

---

## SOLID Rules (SWIFT Orange Belt — Episodes 9–13)

**Principle**: The SOLID principles prevent the design rot that makes codebases brittle and hard to extend.

---

### SOLID/Rule_1: Single Responsibility Principle (SRP) — Episode 9

A class or component should have **one reason to change**. When a class handles protocol monitoring *and* coverage collection *and* scoreboarding, any one of those concerns changing forces changes to the others.

```systemverilog
// ❌ Bad: one class handles three unrelated concerns
class bad_dispatch_agent extends uvm_agent;
    // Concern 1: transaction monitoring
    virtual function void collect_transaction();
        // ...
    endfunction

    // Concern 2: functional coverage
    covergroup dispatch_cov;
        // ...
    endgroup

    // Concern 3: scoreboarding / ordering check
    uint expected_order[$];
    function void check_ordering();
        // ...
    endfunction
endclass

// ✅ Good: each concern lives in its own class
class dispatch_monitor extends uvm_agent; /* monitoring only */ endclass
class dispatch_coverage extends uvm_agent; /* coverage only */ endclass
class dispatch_scoreboard extends uvm_component; /* ordering only */ endclass
```

---

### SOLID/Rule_2: Open/Closed Principle (OCP) — Episode 10

Software entities should be **open for extension, closed for modification**. When adding a new transaction type requires editing an existing checker's `case` or `if-else` chain, consider polymorphism instead.
In SystemVerilog, that abstraction boundary can be expressed with a concrete base class, a virtual class, or an interface class; the key is that new behavior is added by extension, not by editing existing selection logic.

```systemverilog
// ❌ Bad: every new opcode requires modifying this method
function int get_expected_latency(opcode_t opcode);
    case (opcode)
        READ:  return READ_LATENCY_CYCLES;
        WRITE: return WRITE_LATENCY_CYCLES;
        // Must edit here to add ATOMIC — violates OCP
    endcase
endfunction

// ✅ Good: define expected latency polymorphically on the base transaction
// New opcodes extend the class, not this method
class base_transaction;
    virtual function int get_expected_latency();
        `uvm_fatal("TRANS", "Subclass must override get_expected_latency()");
        return -1;
    endfunction
endclass

class read_transaction extends base_transaction;
    function int get_expected_latency();
        return READ_LATENCY_CYCLES;
    endfunction
endclass

class write_transaction extends base_transaction;
    function int get_expected_latency();
        return WRITE_LATENCY_CYCLES;
    endfunction
endclass
```

```python
# ❌ Bad: every new opcode requires editing this function
def get_expected_latency(opcode: str) -> int:
    if opcode == "read":
        return READ_LATENCY_CYCLES
    if opcode == "write":
        return WRITE_LATENCY_CYCLES
    raise ValueError(f"Unsupported opcode: {opcode}")


# ✅ Good: extend by adding a new transaction type
class BaseTransaction:
    def get_expected_latency(self) -> int:
        raise NotImplementedError


class ReadTransaction(BaseTransaction):
    def get_expected_latency(self) -> int:
        return READ_LATENCY_CYCLES


class WriteTransaction(BaseTransaction):
    def get_expected_latency(self) -> int:
        return WRITE_LATENCY_CYCLES
```

---

### SOLID/Rule_3: Liskov Substitution Principle (LSP) — Episode 11

A subtype must be **fully substitutable** for its base type without surprising the caller. A subclass that overrides a method and silently does nothing, or that requires stronger preconditions, violates this principle.

```systemverilog
// ❌ Bad (refused bequest): subclass inherits write behavior it cannot honor
class register_access extends uvm_sequence_item;
    rand logic [31:0] addr;
    rand logic [31:0] data;

    virtual function void apply_write(register_model rm);
        rm.write(addr, data);
    endfunction
endclass

class read_only_register_access extends register_access;
    virtual function void apply_write(register_model rm);
        `uvm_fatal("LSP", "read_only_register_access cannot perform writes")
    endfunction
endclass

// ✅ Good: model capabilities explicitly so each subtype honors its contract
virtual class readable_access extends uvm_sequence_item;
    rand logic [31:0] addr;

    pure virtual function logic [31:0] apply_read(register_model model);
endclass

virtual class writable_access extends uvm_sequence_item;
    rand logic [31:0] addr;
    rand logic [31:0] data;

    pure virtual function void apply_write(register_model model);
endclass

class read_only_register_access extends readable_access;
    virtual function logic [31:0] apply_read(register_model model);
        return model.read(addr);
    endfunction
endclass

class write_register_access extends writable_access;
    virtual function void apply_write(register_model model);
        model.write(addr, data);
    endfunction
endclass
```

---

### SOLID/Rule_4: Interface Segregation Principle (ISP) — Episode 12

No consumer should be forced to depend on methods it does not use. A "fat" class that exposes an unrelated mix of methods creates unnecessary coupling. Prefer focused, role-specific interfaces.

```systemverilog
typedef write_request write_request_queue[$];

// ❌ Bad: class mixes unrelated responsibilities
class monolithic_memory_agent extends uvm_agent;
    // used by scoreboard
    function write_request_queue get_outstanding_writes();
        // ...
    endfunction
    // used by coverage
    function coverage_data get_coverage_data();
        // ...
    endfunction
    // used by power tool only
    function void record_power_event(power_event event);
        // ...
    endfunction
endclass

// ✅ Good: split into focused, single-purpose components
class memory_scoreboard_provider extends uvm_component;
    function write_request_queue get_outstanding_writes();
        // ...
    endfunction
endclass

class memory_coverage_provider extends uvm_component;
    function coverage_data get_coverage_data();
        // ...
    endfunction
endclass
```

---

### SOLID/Rule_5: Dependency Inversion Principle (DIP) — Episode 13

High-level policy (e.g., a checker) should not depend on low-level detail (e.g., a specific bus protocol). Both should depend on an abstraction.
DIP defines dependency direction, not a specific construction pattern: concrete implementations may be selected via configuration, factory wiring, explicit composition code, or dependency injection.

```systemverilog
// ❌ Bad: checker is tightly coupled to AXI-specific details
class read_checker extends uvm_component;
    axi_monitor m_axi_monitor;  // hard dependency on concrete type

    task run_once();
        if (m_axi_monitor.axi_arvalid && m_axi_monitor.axi_rvalid) begin
            check_response(m_axi_monitor.current_axi_transaction);
        end
        // Adding APB requires editing this class (new signals, new branches)
    endtask
endclass

// ✅ Good: high-level checker depends on an abstraction
virtual class transaction_stream;
    pure virtual task get_next_transaction(output base_transaction observed_transaction);
endclass

class read_checker extends uvm_component;
    transaction_stream response_stream;

    task run_once();
        base_transaction observed_transaction;
        response_stream.get_next_transaction(observed_transaction);
        check_response(observed_transaction);
    endtask
endclass

// Low-level adapters depend on the same abstraction
class axi_transaction_stream extends transaction_stream;
    axi_monitor m_axi_monitor;

    task get_next_transaction(output base_transaction observed_transaction);
        observed_transaction = m_axi_monitor.current_axi_transaction;
    endtask
endclass

class apb_transaction_stream extends transaction_stream;
    apb_monitor m_apb_monitor;

    task get_next_transaction(output base_transaction observed_transaction);
        observed_transaction = m_apb_monitor.current_apb_transaction;
    endtask
endclass
```

---

## Refactoring Signals (SWIFT Green Belt — Intro to Refactoring)

The following are *code smells* that warrant a refactoring suggestion, even if the code is functionally correct:

| Smell | What to Flag |
|-------|-------------|
| **Long Method** | Methods longer than ~10 lines — suggest extraction |
| **Large Unit** | Units with many unrelated fields/methods — suggest split by SRP |
| **Shotgun Surgery** | A single change requires edits in many units — suggest consolidation |
| **Feature Envy** | A method uses another unit's data more than its own — suggest moving the method |
| **Data Clumps** | The same 3–4 fields repeatedly appear together — suggest a struct |
| **Primitive Obsession** | Raw integers doing duty as enums or bitfields — suggest a typed enum |
| **Dead Code** | Unreachable code, unused fields, never-called methods — suggest deletion, except temporary disabled code tagged with `FIXME` and an explicit re-enable trigger (for example, HSD ticket) |

---

## Design Pattern Signals (SWIFT Blue Belt — Episodes 25–27, 31–33)

When the pattern below is used *manually* in repeated code, suggest the named pattern:

| Pattern Opportunity | Signal |
|--------------------|--------|
| **Factory** (Ep 26) | Constructor logic replicated at multiple call sites with `if/case` to select type |
| **Strategy** (Ep 27) | Behavior switched by a flag parameter; multiple `if/case` branches doing similar things |
| **Observer** (Ep 31) | A component actively polls another's state or availability in a loop instead of reacting to notification or blocking handoff |
| **Template Method** (Ep 27) | Two methods share the same skeleton with different steps — extract the skeleton |
| **Decorator** (Ep 32) | Wrapper code adding behavior to an existing object duplicated across call sites |
