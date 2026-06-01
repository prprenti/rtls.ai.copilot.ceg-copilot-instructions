# Jasper FPV Command & Workflow Reference

Use this reference after activating the `jg-cmd` skill.

**Scope:** Unified end-to-end formal workflow (runfv + AutoFormal) and exact Jasper command reference.

**Related skills:** `runfv-setup`, `sva-properties`, `proof-debug`

> **MCP-First Rule for JasperGold:** For batch Tcl command execution, ALWAYS use the **`runfv-mcp/jg_cmd`** MCP tool — NEVER run `jg` directly in a terminal for automated/batch workflows.
>
> The `jg_cmd` tool handles Tcl script generation, proof loading, multi-app support (fpv, cdc, lpv, sec, superlint, etc.), and proper error handling.
>
> Direct `jg` invocation is allowed only for manual, interactive GUI sessions. For interactive JasperGold workflows, you may use the `runfv` alias for proof building + launching, or launch `jg` manually when you are not running an automated/batch Tcl flow.

---

**For questions or issues, contact:**
- Primary: vipul.jee.verma@intel.com
- Team PDL: ceg.india.bdc.fv@intel.com

---

## Jasper FPV Cheat Sheet

This file summarizes the most useful Jasper FPV commands, setup flow, and practical usage patterns from the Jasper Apps User Guide 2024.12 and the installed Jasper Command Reference.

Command reference used:

```text
/p/hdk/rtl/cad/x86-64_linux30/jasper/jaspergold/2024.12p002/doc/jasper_command_reference.pdf
```

---

## 0. End-to-End Workflows (Unified)

This section consolidates the practical workflow guidance available in this plugin from:

1. `runfv-setup` (proof setup and environment preparation)
2. `runfv-verify` (property generation, proof execution, and verification flow)
3. `sva-properties` (property authoring guidance)
4. `proof-debug` (proof and counterexample debug workflow)
5. `jg-cmd` (exact Jasper command usage and scripting reference, including AutoFormal-related command patterns)

### 0A. Choose Your Path

1. Path A: Manual runfv proof flow
	- Use when you need full control over proof collateral in `src/val/tb/fpv/<proof_name>/`.
2. Path B: AutoFormal flow
	- Use when you need fast structural/formal lint-style checks and auto-generated setup under `static/jasper/`.
3. Path C: Command-reference mode
	- Use exact Tcl syntax sections in this file when scripting directly in Jasper.

### 0B. Cross-Path Phase Model

Use the same lifecycle for all paths:

1. Prepare environment
2. Create or discover flow artifacts
3. Configure clocks/resets/constraints
4. Run and monitor
5. Triage failures/violations
6. Apply fixes or waivers
7. Re-run and closeout

### 0C. Phase 1: Prepare Environment

For this workspace:

```bash
cd <your_workarea_path>
setenv WORKAREA `pwd`
/p/hdk/bin/cth_psetup -p ddgcth/1.13 -cfg ddgip -read_only
```

Then generate RTL collateral using the MCP tool:
```
run_grdlbuild(task="codegen_rtl")
```

> **MCP-First Rule:** ALWAYS use the **`run_grdlbuild`** MCP tool — NEVER run `grdlbuild` directly in a terminal.
> See the grdlbuild skill documentation for full MCP tool usage.
>
> The formal Gradle build configuration (including `codegen_rtl` dependency and FPV compile/regress tasks) is defined in `$WORKAREA/flows/grdlbuild/formal/build.gradle.kts`.

Environment checks:

```bash
echo $WORKAREA
echo $USER
echo $SITE
```

### 0D. Phase 2: Create/Discover Flow Artifacts

#### Path A (Manual runfv)

1. Verify proof is registered in `src/val/tb/fpv/proofs_container.csv`.
2. Ensure proof directory exists:
	- `src/val/tb/fpv/<proof_name>/cfg/`
	- `src/val/tb/fpv/<proof_name>/src/`
3. Ensure required files exist:
	- cfg: `*_conf.tcl`, `*_pis.tcl`, `*_setup.tcl`, `*_init_prune.tcl`, `*_global_prune.tcl`, `*_verify_prune.tcl`
	- src: `*_map.va`, `*_top.va`, `*_spec.va`, `*_assume.va`, `*_assert.va`, `*_cover.va`, `*_restrict.va`

#### Path B (AutoFormal)

1. Check existing flow first to avoid overwrite:

```bash
bash -c 'if [ -d "$WORKAREA/static/jasper" ]; then echo "EXISTS"; else echo "MISSING"; fi'
```

2. Expected generated structure:
	- `static/jasper/flow_AutoFormal.cfg`
	- `static/jasper/tool.cth`
	- `static/jasper/Makefile`
	- `static/jasper/pre_post_tcl/AutoFormal/*.tcl`

### 0E. Phase 3: Configure Clocks, Resets, and Semantics

#### Path A (Manual runfv proof collateral)

Clock/reset rules consolidated from setup/verify flow:

1. Clock list entries should include `-both_edges` when using proof family convention.
2. Reset expression must use correct polarity and valid Tcl expansion.
3. Use mapped DUT signals from `*_map.va` for properties.

Reset example:

```tcl
set ALL_RST {~clkrst.rst_n}
reset -expression $ALL_RST -non_resettable_regs 0
```

Do not keep reset variable literal with braces at callsite:

```tcl
# avoid this style in this proof family
reset -expression {$ALL_RST}
```

#### Path B (AutoFormal)

1. Confirm `JG_CLOCK_LIST` and `JG_RESET_LIST` in `flow_AutoFormal.cfg`.
2. Confirm categories in `pre_elab.tcl` and assumptions in `pre_superlint.tcl`.
3. Keep third-party/known-noise handling in `slint_waivers.tcl`.

### 0F. Phase 4: Run and Monitor

#### Path A (Manual runfv)

```bash
runfv <proof_name> <dut_module>
tail -f output/formal/<proof_name>/compile/jgproject/jg.log
```

#### Path B (AutoFormal)

Use the `run_make` MCP tool:
```
run_make(target="jg_superlint", directory="static/jasper")
```

> **MCP-First Rule:** ALWAYS use the **`run_make`** MCP tool — NEVER run `make` directly in a terminal.
> Pass `CONFIG=flow_AutoFormal.cfg` explicitly if the Makefile does not default to it:
> ```
> run_make(target="jg_superlint", directory="static/jasper", extra_args="CONFIG=flow_AutoFormal.cfg")
> ```

### 0G. Phase 5: First-Pass Triage

#### Path A (Proof results)

```bash
rg -in "counterexample|\bcex\b|IPF055" output/formal/<proof_name>/compile/jgproject/jg.log
rg -in "proven unreachable|\bunreachable\b|IPF051" output/formal/<proof_name>/compile/jgproject/jg.log
rg -in "SUMMARY|assertions|covers|\bproven\b|\bcex\b|\bcovered\b|\bunreachable\b" output/formal/<proof_name>/compile/jgproject/jg.log
```

#### Path B (AutoFormal violations)

Priority order:

1. High-severity RTL-owned violations
2. Medium-severity RTL-owned violations
3. Third-party IP violations (typically waive with justification)

### 0H. Phase 6: Debug Decision Matrix

Use this owner-first matrix for both proof and AutoFormal issues.

| Symptom | First check | Likely owner | Next action |
| --- | --- | --- | --- |
| CEX on assertion | Trigger/reset/mapping in local proof files | assertion/constraint | Fix assertion trigger, map, or assumptions |
| Unreachable cover | Over-constraint or impossible sequence | assumption/spec | Relax assumptions or rewrite cover intent |
| VIP/CompMon failure | VIP parameter/signal binding | integration/RTL | Validate top.va/spec.va/map.va bindings |
| AutoFormal dead code/FSM/signal violation | Reachability and coding style | RTL or waived IP | Fix RTL if owned, waiver if justified third-party |
| Spec-vs-RTL mismatch | MAS/HAS requirement vs implementation | spec or RTL | Decide: assertion fix vs RTL fix vs spec clarification |

### 0I. Phase 7: Apply Fixes

Fix order:

1. Tcl/config integrity (`*_conf.tcl`, setup files)
2. Reset/clock correctness
3. Assumption legality and scope
4. Assertion semantics and mapped signals
5. RTL change only if property and assumptions are confirmed valid

AutoFormal-specific guidance:

1. Prefer narrow waivers first (tag+module), not broad global waivers.
2. Keep waiver comments with rationale/ticket for owned RTL exceptions.
3. Separate third-party waivers from RTL-owned waivers.

### 0J. Phase 8: Re-Run and Closeout

Closeout checklist:

1. Path A:
	- `cex = 0` for targeted assertions
	- intended covers either `covered` or justified if unreachable
2. Path B:
	- high-priority RTL-owned violations are fixed or tracked
	- waiver file updated only with justified entries
3. Preserve reproducibility:
	- keep final commands and key log paths documented in commit notes

### 0K. Deep Debug Utilities (Optional)

Use debug utilities when log-level triage is insufficient:

1. Utility A: Analyze Simulation Log
2. Utility B: Trace Signal Hierarchical Path
3. Utility C: Configuration and Plusargs Inspection
4. Utility D: Timeline and Sequence Tracker Analysis
5. Utility E: Verdi Waveform Setup
6. Utility F: FSDB Signal Inspection
7. Utility G: Protocol Analysis and Debugging
8. Utility H: Post-Process Analysis

### 0L. Artifact Crosswalk

| Phase | Primary artifacts |
| --- | --- |
| Prepare | `$WORKAREA`, CTH setup, `run_grdlbuild(task="codegen_rtl")` |
| Create/Discover | `proofs_container.csv`, `src/val/tb/fpv/<proof_name>/` or `static/jasper/` |
| Configure | `cfg/*.tcl`, `src/*_{map,assert,assume,cover}.va`, `flow_AutoFormal.cfg` |
| Run | `runfv ...` or `make ... jg_superlint` |
| Triage | `output/formal/*/jgproject/jg.log`, AutoFormal reports |
| Fix/Waive | property collateral, RTL, `slint_waivers.tcl` |
| Closeout | rerun logs, summary status, tracked justifications |

---

## 1. Launch Commands

Launch the FPV app:

```bash
jg -fpv
```

Launch with an existing database or script inputs:

```bash
jg -fpv <database_or_script>
```

---

## 2. Standard FPV Flow

The recommended FPV flow is:

1. Analyze RTL
2. Elaborate design
3. Specify constraints
4. Specify global clock
5. Specify global reset
6. Prove properties
7. Debug properties

For batch usage, this flow maps to Tcl commands executed in order.

---

## 3. Core Tcl Commands

The key Jasper proof-setup commands are:

```tcl
analyze
elaborate
clock
reset
```

These are the basic building blocks for any FPV setup script.

---

## 3A. Exact Tcl Syntax From Jasper Command Reference

The following syntax is taken from the installed Jasper Command Reference.

### analyze

```tcl
analyze ( -vhdl |-vhdl93 |-vhdl2k |-vhdl08
[-alias alias_name target_library]
|-verilog |-v2k |-v95 |-vams
|-sv |-sv05 |-sv09 |-sv12 |-sv17 )
[-req |-psl |-repository repository_id]
[-y dir_name]*
[-v file_name]*
[-lib default_lib_name]
[(-L package_name)+ package_declaration.sv |-L library_name]
[lib_name::]file_name*
[+libext+ext[+ext]*]
[+define(+name[=value])+]
[-f file_name]*
[-f_relative_to_file_location file_name]*
[+incdir+dir_name[+dir_name]*]
[-incdir dir_name]
[-sort]
[-bbox_m string]
[-no_bbox_m string]
[-sfcu |(-mfcu [-cu_name compilation_unit_name])]
```

### elaborate

```tcl
elaborate [-vhdl]
[-sv09_expression_mode]
[-bbox (0 | 1)]
[-bbox_m string]*
[-no_bbox_m string]*
[-bbox_i string]*
[-no_bbox_i string]*
[-bbox_a value]
[-bbox_mul value]
[-bbox_div value]
[-bbox_mod value]
[-bbox_pow value]
[-top [lib_name'.']string['('arch_name')']]
[-inst_top instance_path [-inst_top_hierarchy_mode (preserve | discard)]]
[-parameter param_name param_value]*
[-req |-repository repository_id]
[-create_related_covers {(precondition | late_precondition | infinite_precondition | witness | contrapositive | infinite_contrapositive)+}]
[-mode (verilog | vhdl [-disable_sva_vhdl])]
[-multiple_clock]
[-extract_covergroups]
[-f file_name]*
[(-L package_name)+ package_declaration.sv |-L library_name]
```

### clock

```tcl
clock primary_clock [-both_edges]
clock clock_1 clock_tcl_list [factor [phase]] [-both_edges]
clock -rate ( input_tcl_list clock_signal [-both_edges] |-default clock_signal [-both_edges] |-clear )
clock -rate -task task_name ( task_stopat_tcl_list clock_signal [-both_edges] |-clear )
clock clock_name -factor N [-phase N]
clock clock_name -both_edges -pattern pattern
clock clock_name -from N -to M -both_edges
clock -clear
clock -remove clock_tcl_list
clock -analyze [-include_latches] [-typed_list] [-silent]
clock -list [signal | configuration] [-typed_list] [-silent]
clock -infer
clock -none
```

### reset

```tcl
reset ([-expression] (pin_constraint_list | pin_constraint+) [-max_iterations N [clock clock_signal]])
[(-init_state file_name [-postfix postfix_file_name] [-disable_wildcard] [include_internal])
|(-vcd file_name [-include_internal])
|(-fsdb file_name)
|(-shm file_name)]
[[-postfix postfix_file_name] [-disable_wildcard]]
[-time time [-time_scale (ms | us | ns | ps)] [-exact]]
[ -hier_path path_difference |-hier_map -from source_hier -to destination_hier ]
[-non_resettable_regs value]

reset -formal (pin_constraint_list | pin_constraint+ |-none)
-bound N [-force] [-max_iterations N [-clock clock_signal]]

reset -sequence (seq_file_name [-disable_wildcard] [-include_internal])
|(-vcd file_name [-include_internal])
|(-shm file_name [-time time [-exact]])
|(-fsdb file_name)
[[-postfix postfix_file_name] [-disable_wildcard]]
[-start_formal_cycle cycle [-from_end]]
[-start_condition expression -end_condition expression]
[-start_time time] [-time time]
[-time_scale (ms | us | ns | ps)]
[ -hier_path path_difference |-hier_map -from source_hier -to destination_hier ]
[-non_resettable_regs value]

reset -analyze [-synchronous] [-list (flop | signal)] [-silent]
[-task task_name] [-conflict]

reset -none [-max_iterations N [-clock clock_signal]] [-non_resettable_regs value]
reset -list [signal] [-typed_list] [-silent]
reset -clear
```

### set_engine_mode

```tcl
set_engine_mode
auto
| -auto N
| default
| (B | B4 | Bm | C | C2 | D | G | G2 | H | Hp | Hps | Ht | Hts | I | J | K | L | M | Mp | N | AB | AD | AG | AM | Oh | Q3 | R | Tri | U | U2 | TM | QT)+
```

### set_prove_orchestration

```tcl
set_prove_orchestration (on | off)
```

### prove

```tcl
prove ( -all [-cex_limit number_of_failures]
|-task [task_name_tcl_list] [-cex_limit number_of_failures]
|-property property_name_tcl_list [-regexp] [-evaluate_in_trace property_name_tcl_list] [-cex_limit number_of_failures]
|-instance instance_name [-except subinstance_name+]
| expression )
[-from property_name [-trace_id N] [-cycle N]]
[-on_determined proc]
[-with_helpers]
[-with_proven]
[-bg]
[-force]
[-asserts | -covers]
[-quiet]
[-engine_mode engine_mode_tcl_list]
[-iter N]
[-first_trace_attempt N]
[-per_property_max_time_limit time_limit]
[-per_property_time_limit time_limit]
[-per_property_time_limit_factor N]
[-time_limit time_limit]
[-per_engine_max_jobs N]
[-max_jobs N]
[-orchestration (on | off)]
[-sst [N]]
```

### assert

```tcl
assert expression [-name name] [-task task_name]
| -copy [prop_name]+ [-regexp] [-to task_name]
| -disable [prop_name]+ [-regexp]
| -enable [prop_name]+ [-regexp]
| -delete [prop_name]+ [-regexp]
| -check [prop_name]+ [-regexp] [-task task_name]
| -show [prop_name]+ [-regexp] [-task task_name]
| -list [-task task_name]
| -summary [-task task_name]
```

### assume

```tcl
assume expression [-name name] [-task task_name]
| -copy [prop_name]+ [-regexp] [-to task_name]
| -disable [prop_name]+ [-regexp]
| -enable [prop_name]+ [-regexp]
| -delete [prop_name]+ [-regexp]
| -check [prop_name]+ [-regexp] [-task task_name]
| -show [prop_name]+ [-regexp] [-task task_name]
| -list [-task task_name]
| -summary [-task task_name]
```

### cover

```tcl
cover expression [-name name] [-task task_name]
| -copy [prop_name]+ [-regexp] [-to task_name]
| -disable [prop_name]+ [-regexp]
| -enable [prop_name]+ [-regexp]
| -delete [prop_name]+ [-regexp]
| -check [prop_name]+ [-regexp] [-task task_name]
| -show [prop_name]+ [-regexp] [-task task_name]
| -list [-task task_name]
| -summary [-task task_name]
```

### check_assumptions

```tcl
check_assumptions [-task task_name]
[-all_assumes]
[-external]
[-conflict]
[-dead_end]
[-redundant]
[-coverage]
[-reachable]
[-unreachable]
[-quiet]
[-verbose]
```

### task

```tcl
task

task -create new_task_name
[-set]
[-copy_all]
[-copy_abstractions (all | counter | init_value | reset_value)+]
[-copy_assumes]
[-copy_asserts]
[-copy_covers]
[-copy_related_covers]
[-copy_covergroups]
[-copy_stopats [-copy_ratings]]
[-copy property_name_list [-regexp]]
[-source_task source_task_name]

task -edit target_task_name
[-copy_all]
[-copy_abstractions (all | counter | init_value | reset_value)+]
[-copy_assumes]
[-copy_asserts]
[-copy_covers]
[-copy_related_covers]
[-copy_covergroups]
[-copy_stopats [-copy_ratings]]
[-copy property_name_list [-regexp]]
[-source_task source_task_name]

task -link (task_name)+ [-to inheriting_task_name] [-silent]
task -unlink (task_name)+ [-to inheriting_task_name] [-silent]

task -set task_name
task -remove [task_name]

task -list [-silent]
task -show [task_name] [-silent]
task -num_asserts [task_name]
task -num_covers [task_name]
task -num_assumes [task_name]
```

### get_property_info

```tcl
get_property_info property_name
get_property_info -list { [name] [task] [source_task] [type] [clock] [edge] [command]
[expression] [precondition]
[related_covers] [liveness] [converted] [helper]
[sst]
[app] [file] [pa] [tcl] [error] [disabled]
[deprecated] [status] [related_cover_status]
[pseudo_constant] [assume_bound]
[time] [engine]
[min_length] [max_length] [sst_max_length]
[stem_length] [loop_length] [trace_length]
[proof_effort] [engineL_trail] [eq_prop]
[store_trace] [trace_extension] [intermediate]
[latest_trace_engine]
[num_traces] [trace_id]
[validity_status] [run_status] [target_bound]
[precondition_expression]
[postcondition_expression]
[evaluate_in_trace] [c_property_type]
[related_property_type] [is_related_property]
[is_related_cover] [is_related_assert]
[related_properties] [related_covers]
[related_asserts]} property_name
```

### get_design_info

```tcl
get_design_info

get_design_info -list
([parameter] [local_parameter] [interface_port_parameter]
[interface_port_local_parameter] [constant] [enum]
[output] [input] [inout] [stopat]
[undriven] [undriven_internal] [loop_index] [multiple_driven]
[bbox_mod] [bbox_inst] [bbox_in] [bbox_out] [bbox_inout]
[bbox_in_instance_port] [bbox_out_instance_port]
[bbox_inout_instance_port]
[basic] [counter] [fsm] [fifo] [array [-no_aggregate]]
[register] [flop] [latch] [gate]
[multiplier] [divider] [modulus]
[module] [module_no_param] [module_name] [module_name_no_param]
[instance [-depth N]] [bind_instance [-depth N]]
[interface] [interface_no_param] [interface_instance] [interface_port]
[prim_inst] [prim_mod] [celldefine]
[package] [compilation_unit] [architecture]
[signal] [wire] [property] [assert] [assume] [cover] [macro])+
[-verbosity (high | low | silent)]
[-typed_list] [-silent]
[-file file_name [-force]]
[-filter filter_expression [-regexp] [-case_sensitive]]
[-gui] [-include_hier_path]
[-pattern (sv_packed | sv_assignment)]
[-transitive]

get_design_info -include_config [-instance instance_name]
get_design_info -enum enum_name

get_design_info -instance instance_name
[-list (...) ]
[-verbosity (high | low | silent)]
[-typed_list] [-silent]
[-file file_name [-force]]
[-filter filter_expression [-regexp] [-case_sensitive]]
[-gui] [-include_hier_path]
[-pattern (sv_packed | sv_assignment)]
[-transitive]
```

### report

```tcl
report [-all [-include_type]]
[-file file_name [-force |-append]]
[(-task task_name_tcl_list |-property property_tcl_list)]

report [-info] [-summary]
[-results [-include_type]]
[-detailed]
[-file file_name [-force |-append]]
[(-task task_name_tcl_list |-property property_tcl_list)]

report [-csv [-include_type]]
[-file file_name [-force |-append]]
[(-task task_name_tcl_list |-property property_tcl_list)]

report [-json -file file_name] [-force]
```

### visualize

```tcl
visualize [-cover]
(expression |(-property property_name) [-regexp])
[ -new_window [new_window_name] |-window window_name]
[-engine (engine_mode | {engine_mode+})]
[-proof_time time_limit]
[-annotation {annotation}]
[-batch] [-silent] [-bg]
[(-sig_order sig_order_file_name)|-no_signals]
[-task task_name] [-trace_id id]

visualize -violation
(expression |(-property property_name) [-regexp])
[ -new_window [new_window_name] |-window window_name]
[-engine (engine_mode | {engine_mode+})]
[-proof_time time_limit]
[-annotation {annotation}]
[-batch] [-silent] [-bg]
[(-sig_order sig_order_file_name)|-no_signals]
[-task task_name] [-trace_id id]

visualize -set_target [-cover |-violation]
[-window window_name]
(expression |(-property property_name [-regexp]))

visualize -replot [-new_window [new_window_name]] [-force]
[-engine (engine_mode | {engine_mode+})] [-proof_time time_limit]
[-quiet] [-min_variation]
[-prompt] [-batch] [-silent] [-bg]
[(-sig_order sig_order_file_name)|-no_signals] [-window window_name]

visualize -go_backward [-new_window [new_window_name]] [-force]
[(-sig_order sig_order_file_name)|-no_signals]
[-proof_time time_limit] [-min_variation]
[-batch] [-silent] [-bg] [-window window_name]

visualize -go_forward [-new_window [new_window_name]] [-force]
[(-sig_order sig_order_file_name)|-no_signals]
[-proof_time time_limit] [-min_variation]
[-batch] [-silent] [-bg] [-window window_name]
```

### get_proj_dir

```tcl
get_proj_dir
```

### redirect

```tcl
redirect -file file_name [-force |-append] {command}
```

### Coverage Of Studied Jasper Commands

All Jasper command work extracted in this effort is consolidated in this file.

1. Setup/build commands: analyze, elaborate, clock, reset
2. Solver/orchestration commands: set_engine_mode, set_prove_orchestration, prove
3. Property commands: assert, assume, cover, check_assumptions
4. Task commands: task
5. Debug/introspection commands: get_property_info, get_design_info, get_proj_dir
6. Reporting/trace commands: report, visualize, redirect

Practical command examples and workflow usage are in later sections:

1. [Analyze / Elaborate Flow](#4-analyze--elaborate-flow)
2. [Reset Debug Commands](#7-reset-debug-commands)
3. [Debug Commands Only](#13a-debug-commands-only)
4. [Mapping: Generic Jasper Commands -> Repo runfv Flow](#16-mapping-generic-jasper-commands---repo-runfv-flow)

---

## 4. Analyze / Elaborate Flow

Typical script-level flow:

```tcl
analyze -sv <rtl_and_property_files>
elaborate -top <lib>.<top_module>
```

Useful analyze-related options mentioned in the guide:

```tcl
-y <directory>
+libext+<ext>+<ext>
-v <verilog_library_file>
```

Use these to resolve missing module definitions and non-default file extensions.

---

## 5. Clock Setup

Clock is part of the global proof environment and should be configured before proof.

Example style:

```tcl
clock <clk_signal>
clock <clk_signal> -both_edges
```

In this workspace, proof collateral usually sets the clock in `*_conf.tcl`.

---

## 6. Reset Setup

Reset must be defined before reset analysis, prove, or visualize reset-based flows.

Typical script style:

```tcl
reset -expression <reset_expr>
```

Examples of reset expressions from the guide:

```tcl
reset -expression rst
reset -expression {rst == 1'b1}
```

For active-low reset:

```tcl
reset -expression ~rst_n
```

Important practical note:
- Use the actual expression value, not a literal Tcl variable token in braces when expansion is required.
- Example:

```tcl
set ALL_RST {~clkrst.rst_n}
reset -expression $ALL_RST
```

---

## 7. Reset Debug Commands

Use these when reset behavior is unclear or reset inference is suspicious:

```tcl
reset -analyze
sanity_check -analyze simple_reset
sanity_check -analyze -all
```

These help detect missing or malformed reset conditions before wasting proof time.

---

## 7.5. Pre-Prove Sanity Workflow

Run these checks **before the first `prove`** to catch misconfigurations early and avoid wasting solver time on a broken model.

### Step 1: Design Sanity

```tcl
# Check reset is well-formed
sanity_check -analyze simple_reset

# Run all design sanity checks (clock, reset, connectivity)
sanity_check -analyze -all
```

### Step 2: Assumption Sanity

```tcl
# Run all assumption sanity checks at once
check_assumptions -sanity -task <embedded> -bg

# Or run individual checks:
# Check for contradictory assumptions (model is empty — nothing provable)
check_assumptions -dead_end

# Check for conflicting assumptions (two assumes contradict each other)
check_assumptions -conflict

# Find assumptions whose triggers can never fire
check_assumptions -unreachable

# Find redundant assumptions (implied by others — safe to remove)
check_assumptions -redundant

# See which assumptions were actually used during proof
check_assumptions -coverage
```

### Step 3: Overconstraint Sanity Cover

Add this to your property file or conf.tcl — if unreachable, assumptions are too tight:

```tcl
cover -name endless_trace {1'b1}
cover -set_trace_extension $ endless_trace
```

### Recommended Pre-Prove Checklist

```tcl
# Run in order before first prove:
sanity_check -analyze -all         # 1. Design sanity (clock, reset, connectivity)
check_assumptions -sanity -bg      # 2. All assumption sanity checks at once
check_assumptions -dead_end        # 3. Empty state space?
check_assumptions -conflict        # 4. Contradictory constraints?
check_reset -bg                    # 5. Reset reaches all flops?
check_loop                         # 6. Combinational loops?
# Then: prove -all
```

| Check | Failure Meaning | Action |
|-------|----------------|--------|
| `sanity_check -analyze -all` fails | Clock/reset misconfigured | Fix conf.tcl |
| `check_assumptions -dead_end` fires | Model is overconstrained (nothing reachable) | Remove or relax assumptions |
| `check_assumptions -conflict` fires | Two assumptions contradict each other | Identify conflicting pair, remove one |
| `endless_trace` cover unreachable | Assumptions prevent any valid execution | Bisect assumptions to find culprit |

---

## 8. Proof Orchestration

Recommended default:

```tcl
set_prove_orchestration on
```

If you need manual engine control:

```tcl
set_prove_orchestration off
```

When orchestration is on, Jasper dynamically manages engines and limits.

---

## 8.5. Custom Prove Orchestration Procedures

Write reusable Tcl procs for repeated prove patterns. These reduce manual repetition and provide consistent prove strategies across proofs.

### Basic Prove with Time Limit

```tcl
proc fv_l0_prove {task} {
    set time_limit [get_prove_time_limit]
    puts "-CEG- Custom prove for task: $task with time limit: $time_limit"
    prove -task $task -time_limit $time_limit
}
```

### Prove + Hunt (for undetermined properties)

Split the time budget: prove first, then hunt remaining undetermined properties with `Ht` engine:

```tcl
proc fv_prove_and_hunt {task} {
    task -set $task
    set time_limit [get_prove_time_limit]
    set time_limit_sec [expr int([string range $time_limit 0 [expr [string length $time_limit] - 2]])]
    set half_time [expr $time_limit_sec / 2]

    # Phase 1: Full prove with half the budget
    prove -task $task -time_limit $half_time

    # Phase 2: Hunt remaining undetermined with Ht
    set undetermined [get_property_list -include {type {cover assert} status {undetermined}}]
    if {[llength $undetermined] > 0} {
        hunt -run -auto -task $task -time_limit $half_time
    }
}
```

### Weekly Regression Strategy

In gatekeeper/weekly runs, use extended prove+hunt; in interactive sessions, use simple prove:

```tcl
proc fv_prove_adaptive {task} {
    if { [info exists ::env(GK_FV_SOC_WEEKLY)] } {
        fv_prove_and_hunt $task
    } else {
        fv_l0_prove $task
    }
}
```

### When to Use Custom Prove Procs

| Situation | Recommendation |
|-----------|---------------|
| Single developer, interactive debug | `fv_l0_prove` (simple, fast feedback) |
| Gatekeeper regression | `fv_prove_and_hunt` (maximize convergence) |
| Multi-module complex proofs | Split into tasks, apply `fv_l0_prove` per task |
| Liveness-heavy proofs | Extract liveness to separate task (see §9.5) |

---

## 9. Default Engines

The guide lists these common engines:

1. `Hp` – parallel, optimized for full proofs
2. `Ht` – parallel, optimized for bug hunting
3. `N` – sequential, optimized for full proofs on smaller COI
4. `B` – sequential, optimized for bug hunting

Default Jasper behavior usually uses a set like:

```tcl
set_engine_mode {Ht Hp N B}
```

Only override this when default orchestration is not sufficient.

---

## 9.5. Liveness Property Extraction

Liveness properties (unbounded `eventually` or `s_eventually`) often need different engine strategies than safety properties. Extract them into a dedicated task for targeted solving.

### Identifying Liveness Properties

```tcl
# List all liveness properties in current task
get_property_list -include {type {cover assert} liveness 1 disabled 0}
```

### Extract Liveness to Separate Task

```tcl
proc task_out_liveness {from_task} {
    set liveness_props [get_property_list -include {type {cover assert} liveness 1 disabled 0}]
    if {[llength $liveness_props] == 0} {
        puts "No liveness properties found in $from_task"
        return ""
    }

    set new_task "${from_task}_liveness"

    # Create liveness task with inherited assumptions
    task -create $new_task -copy_assumes -copy $liveness_props -copy_stopats

    # Disable liveness in original task (prove safety separately)
    task -set $from_task
    foreach prop [get_property_list -include {type {cover assert assume} liveness 1}] {
        assert -disable $prop
        cover -disable $prop
    }

    puts "Extracted [llength $liveness_props] liveness properties to task: $new_task"
    return $new_task
}
```

### Prove Liveness with Targeted Engines

```tcl
# Liveness benefits from Ht (bug hunting) for finding CEX
# and longer time limits for convergence
set liveness_task [task_out_liveness <embedded>]
if {$liveness_task ne ""} {
    prove -task $liveness_task -engine_mode {Ht Hp} -time_limit 3600s
}
```

### Interpreting Liveness Results

| Status | Meaning | Action |
|--------|---------|--------|
| proven | Fair path always leads to satisfaction | Property verified |
| cex (stem+loop) | Infinite loop exists that never satisfies | Likely real bug or missing fairness |
| undetermined | Solver couldn't converge | Increase time, add fairness constraints, or abstract |

### Forward-Progress Patterns

For arbiter fairness and liveness, use dedicated checker modules:

```systemverilog
// Instantiate forward-progress checker for each grant
fv_fwd_prg_counter #(.MAX_STARVATION(100)) fwd_prg_req0 (
    .clk(clk), .rst(rst),
    .request(req[0]), .grant(gnt[0])
);
```

---

## 9.6. Deadlock Detection

Jasper detects deadlock as a liveness failure with a **stem+loop** counterexample — a finite path (stem) leading to an infinite repeating cycle (loop) that never makes forward progress.

### check_afv -deadlock

```tcl
# Auto-detect reachable deadlock states (requires AFV app license)
check_afv -deadlock
check_afv -deadlock -max_iterations 100
```

### Detect via Liveness Property (CEX Interpretation)

```tcl
# Assert forward progress — failure with stem+loop = deadlock
assert -name fwd_progress {req |-> s_eventually gnt}
prove -property fwd_progress -strategy {Ht}
```

| CEX Type | Meaning | Action |
|----------|---------|--------|
| `cex (stem+loop)` | True deadlock — infinite loop found | Real bug, escalate to RTL designer |
| `cex (Ht, bounded)` | No progress within N cycles | May be deadlock — inspect trace |
| `undetermined` | Solver couldn't confirm | Add fairness, increase time, or abstract |
| `proven` | No deadlock possible | Property verified |

### Dump Deadlock Trace

```tcl
# Dump the stem+loop CEX to VCD for analysis
redirect -file deadlock_cex.vcd -force {
    visualize -save_vcd -property fwd_progress -include_internal
}
```

### Fairness Assumptions (Rule Out False Deadlocks)

Missing fairness is the most common cause of false deadlock findings in arbiter proofs:

```tcl
# Fairness: arbiter eventually serves every requestor
assume -name fair_arb0 -fairness {req[0] |-> s_eventually gnt[0]}
assume -name fair_arb1 -fairness {req[1] |-> s_eventually gnt[1]}
```

### Deadlock Debug Checklist

1. Check the **loop** portion of the CEX — that's the deadlock cycle
2. Identify which signals are stuck (not transitioning) inside the loop
3. Check for mutual waiting: two modules each waiting for the other
4. Check for missing fairness assumption on arbiter/scheduler
5. Verify `endless_trace` cover is reachable (rule out overconstraint)

---

## 10. Common Proof Controls

The guide highlights these proof settings as the most useful tuning knobs:

1. Proof simplification
2. Cache proof simplification results
3. Use proven directives as assumptions
4. First trace attempt at cycle
5. Max trace length
6. Per-property max time limit
7. Total time limit
8. Per-property time limit
9. Per-property time limit factor
10. Stop after N counterexamples

These are often configured in GUI, but they map to scripted proof settings in Jasper-based flows.

---

## 10.5. Hunt vs. Full Proof Strategy

The `hunt` command is optimized for finding counterexamples quickly, while `prove` targets full proofs. Use them in combination for efficient debug.

### When to Hunt

- First pass on new properties (find bugs before investing in full proof)
- Undetermined properties after initial prove pass
- Properties with known bugs that need CEX for debug

### When to Full-Prove

- Final convergence after fixes are applied
- Properties that passed hunt without CEX (need formal guarantee)
- Gatekeeper regression (prove = sign-off criteria)

### Hunt Command Syntax

```tcl
# Auto-hunt: Jasper picks best strategy for finding CEX
hunt -run -auto -task <task_name> -time_limit 1800s

# Targeted hunt on specific properties
hunt -run -auto -property {prop1 prop2} -time_limit 600s
```

### Split-Budget Strategy (Prove First, Hunt Remainder)

```tcl
# Total budget: 2 hours
# Phase 1: Prove with first hour
prove -all -time_limit 3600s

# Phase 2: Hunt remaining undetermined with second hour
set remaining [get_property_list -include {status {undetermined}}]
if {[llength $remaining] > 0} {
    hunt -run -auto -property $remaining -time_limit 3600s
}
```

### Engine Selection for Hunt vs. Prove

| Goal | Engine Mode | Use Case |
|------|-------------|----------|
| Find bugs fast | `{Ht}` or `{Ht B}` | Initial property debug |
| Full proof | `{Hp N}` | Convergence on proven properties |
| Mixed (default) | `{Ht Hp N B}` | Let orchestration decide |
| Bounded model checking | `{B}` | Short-trace bugs |

---

## 11. ProofGrid / Distributed Runs

ProofGrid modes described by the guide:

1. `local`
2. `shell`
3. `lsf`
4. `oge`
5. `nc`
6. `cluster`

Shell-mode caution from the guide:
- the spawned shell command must remain alive as long as the proof engine job
- otherwise proof jobs can die with connection errors

This matters if you wrap Jasper with custom launcher scripts.

---

## 11.5. Task Management for Multi-Module Proofs

For complex proofs (arbiters, bridges, multi-hierarchy designs), split properties into tasks to manage solver complexity and isolate failures.

### Task Creation Patterns

```tcl
# Create task from specific property families
task -create credit_mgmt -source_task <embedded> \
    -copy {{*credit*} {*crd_rtn*} {*flow_ctrl*}}

task -create data_flow -source_task <embedded> \
    -copy {{*scoreboard*} {*data_integrity*} {*txn_*}}

task -create error_handling -source_task <embedded> \
    -copy {{*err_*} {*poison*} {*timeout*}}
```

### Task-Based Enable/Disable

```tcl
# Disable all, enable by task scope
assert -disable *
cover -disable *
assume -disable *

# Enable only the target proof's properties
assert -enable *fv_<proof_name>*
cover -enable *fv_<proof_name>*
assume -enable *fv_<proof_name>*
```

### Per-Task Prove Commands

```tcl
# Prove each task independently with different strategies
prove -task credit_mgmt -time_limit 1800s
prove -task data_flow -time_limit 3600s
prove -task error_handling -time_limit 600s
```

### Hierarchical Task Organization (IOC-Style)

For multi-module designs like IOC bridges:

```
<embedded> (root task)
├── credit_mgmt      — CFI credit return, IOSF flow control
├── data_flow        — Scoreboard checks, transaction ordering
├── arbitration      — Arbiter fairness, forward progress
├── error_handling   — Poison, timeout, parity
└── liveness         — Extracted via task_out_liveness (see §9.5)
```

### Task Status Queries

```tcl
# Check status per task
task -set credit_mgmt
report -summary

# List all tasks
task -list

# Get property counts by status per task
foreach t [task -list] {
    task -set $t
    set proven [llength [get_property_list -include {status {proven}}]]
    set cex [llength [get_property_list -include {status {cex}}]]
    set undet [llength [get_property_list -include {status {undetermined}}]]
    puts "Task $t: proven=$proven cex=$cex undetermined=$undet"
}
```

### Overconstraint Sanity Check per Task

```tcl
# Always add an endless-trace cover to detect overconstrained models
cover -name endless_trace {1'b1}
cover -set_trace_extension $ endless_trace

# If endless_trace is unreachable, assumptions are overconstrained
```

### When to Use Task Separation

| Condition | Action |
|-----------|--------|
| >50 properties in one proof | Split into logical groups |
| Mix of safety + liveness | Extract liveness to dedicated task |
| Different clock domains | One task per domain |
| Convergence issues | Isolate hard properties into their own task |
| Different time budgets needed | Assign per-task time limits |

---

## 11.6. Proof Structure & ProofGrid Multi-Task Orchestration

Proof Structure (Cadence IP Signoff methodology) organizes proofs into a **tree of tasks** with parent-child relationships. Leaf tasks prove subsets of properties; parent tasks propagate results upward.

### Proof Structure Commands

```tcl
# Query node info (returns dict: children, properties, status)
proof_structure -get_node_info <node_name>

# Propagate leaf results up to parent nodes
proof_structure -propagate

# Get active (non-disabled) assert + cover properties in a task
get_property_list -task <task_name> \
  -include {type {assert cover} disabled 0} \
  -no_task_prefix
```

### Prove a Full Proof Structure Tree (Serial)

Use when you have a single machine and want to prove all tasks in the tree:

```tcl
# psu_prove_all_serial (from proof_structure_utils.tcl — Cadence reference lib)
# Walks tree, proves each node's unique properties, propagates results
psu_prove_all_serial <root_node>

# With extra prove options (e.g., engine override)
psu_prove_all_serial <root_node> "-engine_mode Ht"
```

### Prove a Full Proof Structure Tree (ProofGrid Parallel)

The `psu_run_proofgrid_multitask` pattern runs all tasks in parallel with **exponentially increasing time limits** (10s → 20s → 40s → ...) so no single task starves others:

```tcl
# Fully automatic — walks tree and parallelizes via ProofGrid
set_prove_time_limit 24h
psu_prove_all <root_node>

# Manual: prove specific option sets in parallel with doubling limits
set option_sets [list "-task task_1" "-task task_2" "-property task_3::prop_A"]
psu_run_proofgrid_multitask $option_sets
```

### Background Prove Primitives (used inside ProofGrid orchestration)

```tcl
# Launch a task in background (non-blocking), capture thread ID
set rc [prove -task <task_name> -time 60s -bg]
set thread_id [lindex $rc 1]

# Launch multiple tasks in parallel
prove -task task_1 -bg
prove -task task_2 -bg
prove -wait                          ;# block until ALL background proofs finish

# Get result for a specific thread
set status [prove -wait -thread $thread_id]
# Returns: "proven" | "cex" | "time_limit" | "none" | "unprocessed"
```

### Bug Hunting Orchestration

For undetermined properties after proving, use `hunt` with stagnation restart:

```tcl
# Hunt with 8h stagnation restart, 24h total limit (IBECC pattern)
hunt -run -auto \
  -stagnation_time_limit 8h \
  -stagnation_action restart \
  -time_limit 24h \
  -task <task_name>
```

### Custom fv_prove Wrapper (from IBECC repo)

```tcl
proc fv_prove {task_num task_1 task_2 time_limit} {
  set_prove_time_limit $time_limit
  if {$task_num == 1} {
    prove -task $task_1
  } else {
    prove -task $task_1 -bg
    prove -task $task_2 -bg
    prove -wait
  }
}

# Usage: 1 task
fv_prove 1 my_task {} 4h

# Usage: 2 tasks in parallel
fv_prove 2 safety_task liveness_task 8h
```

### Proof Structure Decision Guide

| Situation | Approach |
|-----------|----------|
| Single flat task, <50 properties | `prove -task <name>` directly |
| Multiple independent subtasks | `psu_prove_all` (parallel ProofGrid) |
| One very hard property hogging time | Isolate to its own leaf task with long limit |
| Want to re-use partial proof results | `proof_structure -propagate` after each run |
| Mix of fast/slow properties | `psu_run_proofgrid_multitask` with exponential limits |

> **Note:** `proof_structure_utils.tcl` is a Cadence-provided library (IP Signoff methodology). Source it explicitly if not auto-loaded: `source $::env(WORKAREA)/src/val/tb/fpv/ibecc/cfg/proof_structure_utils.tcl`

---

## 12. Practical Workspace Flow

For this workspace, the normal proof-launch flow is:

1. Go to workarea root
2. Set `WORKAREA`
3. Enter CTH environment
4. Run the `runfv` alias
5. Monitor `jg.log`

Example:

```bash
cd /path/to/workarea
setenv WORKAREA `pwd`
/p/hdk/bin/cth_psetup -p ddgcth/1.13 -cfg ddgip -read_only
```

Then generate RTL collateral using the MCP tool:
```
run_grdlbuild(task="codegen_rtl")
```

Then launch the proof:
```bash
runfv <proof_name> <dut_module>
```

> **MCP-First Rule:** ALWAYS use the **`run_grdlbuild`** MCP tool — NEVER run `grdlbuild` directly in a terminal.

The local alias behavior is:

```bash
runfv => set d=!:1 && set p=!:2 && run_fv build-proof -dut $d -p $p && run_fv load-proof -dut $d -p $p &
```

---

## 12.5. Abstraction & Complexity Management

Use these commands to reduce proof complexity when convergence fails or proofs time out.

### complexity_manager — Analyze Proof Complexity

```tcl
# Analyze complexity before proving (COI size, state bits, sequential depth)
complexity_manager -analyze

# Analyze a specific property
complexity_manager -analyze -property <prop_name>

# Report complexity metrics for all properties
complexity_manager -report

# Set a complexity threshold (abort proof if exceeded)
complexity_manager -set_limit <value>
```

The report shows **COI size** (cone of influence), **state bits**, and **sequential depth** — the key metrics for deciding whether to black-box, abstract, or split into tasks.

### abstract — Dynamic Abstraction (Post-Elaborate)

Use `abstract` to replace non-essential logic with free variables:

```tcl
# Auto-abstract: remove everything not in COI of current properties
abstract -auto

# Abstract a specific signal (replace with unconstrained input)
abstract -signal <signal_path>

# Abstract an entire module
abstract -module <module_name>

# Remove a specific abstraction
abstract -remove -signal <signal_path>

# List all current abstractions
abstract -list
```

### Black-box Abstraction (at Elaborate time — in pis.tcl)

```tcl
set ELAB_OPTS {
    -bbox_m <module_name>       # black-box all instances of this module
    -bbox_i <instance_path>     # black-box only this specific instance
    -bbox_mul 8                 # abstract multipliers > 8 bits
    -bbox_div 8                 # abstract dividers > 8 bits
    -bbox_mod 8                 # abstract modulo ops > 8 bits
    -bbox_a 4                   # abstract arrays > 4 elements
}
```

### Decision Guide

| Situation | Command | Impact |
|-----------|---------|--------|
| Proof times out, submodule irrelevant | `-bbox_m <mod>` in ELAB_OPTS | May introduce spurious proofs |
| Only one instance should be boxed | `-bbox_i <path>` in ELAB_OPTS | Safer than -bbox_m |
| Large multiplier/divider slowing proof | `-bbox_mul/-bbox_div` in ELAB_OPTS | Replaces arithmetic with free vars |
| Dynamic convergence issue during debug | `abstract -auto` in Tcl console | Removes non-COI logic |
| Specific stuck signal | `abstract -signal <path>` | Make one signal unconstrained |

### Abstraction Safety Warning

> **Abstraction can make a failing property appear proven.** Always verify that black-boxed or abstracted modules are truly irrelevant to the property being checked. Document all abstractions with comments in `pis.tcl`.

---

## 12A. Repo-Specific Example: ibecc_cfi_ififo

Concrete example from this repository:

### Workarea and launch

```bash
cd /nfs/site/disks/val_memss_pma_fv_wa_01/ddgip/dyellini/IBECC/ibecc_tie_ttl/ibecc_tie_ttl
setenv WORKAREA `pwd`
/p/hdk/bin/cth_psetup -p ddgcth/1.13 -cfg ddgip -read_only
```

Then generate RTL collateral using the MCP tool:
```
run_grdlbuild(task="codegen_rtl")
```

Then launch the proof:
```bash
runfv ibecc_cfi_ififo ibecc_cfi_ififo
```

### Clock and reset in proof config

From the proof config used in this repo:

```tcl
clock -clear
reset -clear

set PRIMARY_CLK {clkrst.clk}
if {[lindex $PRIMARY_CLK 0] != "__clk__"} {
	foreach clk $PRIMARY_CLK {
		clock $clk -both_edges
	}
}

set ALL_RST {~clkrst.rst_n}
if {[lindex $ALL_RST 0] != "__reset__"} {
	reset -expression $ALL_RST -non_resettable_regs 0
}
```

### Important repo lesson

Do not write:

```tcl
reset -expression {$ALL_RST}
```

That keeps the Tcl variable literal and can break Jasper reset parsing. Use:

```tcl
reset -expression $ALL_RST
```

### Example assertion style

The `ibecc_cfi_ififo` proof uses local-scope assertions against real RTL intent:

```systemverilog
`FPV_IBECC_ASSERTS_TRIGGER(AST_IFIFO_EMPTY_FULL_MUTEX,
						   1'b1,
						   !(`FV_DUT.empty && `FV_DUT.full),
						   posedge clk, rst,
						   `FPV_IBECC_ERR_MSG("ibecc_cfi_ififo: internal empty and full cannot be high together"));
```

Repo-specific debug lesson:
- `status_o.empty` and `status_o.full` were not the true internal empty/full signals.
- The correct property had to use the internal decoded signals instead.

---

## 13. Log Monitoring

Main compile/proof log:

```bash
tail -f output/formal/<proof_name>/compile/jgproject/jg.log
```

Search for failures:

```bash
rg -in "counterexample|\bcex\b|IPF055" output/formal/<proof_name>/compile/jgproject/jg.log
rg -in "proven unreachable|\bunreachable\b|IPF051" output/formal/<proof_name>/compile/jgproject/jg.log
rg -in "SUMMARY|assertions|covers|\bproven\b|\bcex\b|\bcovered\b|\bunreachable\b" output/formal/<proof_name>/compile/jgproject/jg.log
```

Read context around a failure:

```bash
sed -n '<start>,<end>p' output/formal/<proof_name>/compile/jgproject/jg.log
```

---

## 13A. Debug Commands Only

Use this section when the proof already launches and you only want debug-oriented commands.

### Shell-side triage

```bash
tail -f output/formal/<proof_name>/compile/jgproject/jg.log
rg -in "counterexample|\bcex\b|IPF055" output/formal/<proof_name>/compile/jgproject/jg.log
rg -in "proven unreachable|\bunreachable\b|IPF051" output/formal/<proof_name>/compile/jgproject/jg.log
rg -in "SUMMARY|assertions|covers|\bproven\b|\bcex\b|\bcovered\b|\bunreachable\b" output/formal/<proof_name>/compile/jgproject/jg.log
sed -n '<start>,<end>p' output/formal/<proof_name>/compile/jgproject/jg.log
```

### Jasper reset/clock debug

```tcl
clock -analyze
clock -list configuration
reset -analyze
reset -list signal
sanity_check -analyze simple_reset
sanity_check -analyze -all
```

### Jasper proof control

```tcl
prove -all
prove -all -bg
prove -property <prop_name>
prove -status
prove -wait
prove -stop
```

### Engine control for debug experiments

```tcl
set_prove_orchestration off
set_engine_mode {Ht Hp N B}
prove -all -engine_mode {Ht}
prove -all -engine_mode {B}
```

### What to check first

1. Tcl/config errors in `*_conf.tcl`
2. Reset polarity and reset variable expansion
3. Clock declaration correctness
4. Assumption legality vs environment intent
5. Assertion scope vs RTL ownership
6. Only then engine tuning

---

## 13G. VCD Trace Debug — Reading and Analyzing Waveform Dumps

Use VCD (Value Change Dump) files to debug counterexamples, validate reset
sequences, and analyze signal behavior offline. JasperGold can both produce
and consume VCD files.

### Dumping CEX Traces to VCD

After a counterexample is found, dump the trace for offline analysis:

```tcl
# Dump the current CEX waveform to VCD
visualize -property <prop_name> -batch
redirect -file output/formal/<proof_name>/traces/<prop_name>_cex.vcd -force {
    visualize -save_vcd -property <prop_name>
}

# Alternative: dump to VCD with internal signals included
visualize -property <prop_name> -batch
redirect -file output/formal/<proof_name>/traces/<prop_name>_cex.vcd -force {
    visualize -save_vcd -property <prop_name> -include_internal
}
```

### Dumping All Failed Property Traces

```tcl
# Batch export all CEX traces in one session
foreach prop [get_property_info -list -status cex] {
    set fname "output/formal/<proof_name>/traces/${prop}_cex.vcd"
    redirect -file $fname -force {
        visualize -save_vcd -property $prop
    }
}
```

### Loading VCD for Reset Sequence Debug

Use a VCD file to define the reset sequence (instead of expression-based reset):

```tcl
# Load VCD-based reset sequence
reset -vcd /path/to/reset_trace.vcd

# With internal signal inclusion
reset -vcd /path/to/reset_trace.vcd -include_internal

# Specify starting cycle for formal analysis
reset -sequence -vcd /path/to/reset_trace.vcd -start_formal_cycle 10
```

### Reading VCD Files for Signal Analysis (Shell-Side)

When JasperGold is not running, use command-line tools to inspect VCD files:

```bash
# Check VCD file header (timescale, scope, signals)
head -50 output/formal/<proof_name>/traces/<prop_name>_cex.vcd

# List all signals in the VCD
grep '^\$var' output/formal/<proof_name>/traces/<prop_name>_cex.vcd | \
    awk '{print $4, $5}'

# Find signal transitions for a specific signal
grep -A1 '<signal_id>' output/formal/<proof_name>/traces/<prop_name>_cex.vcd

# Count cycles in the trace (number of timestamp markers)
grep -c '^#' output/formal/<proof_name>/traces/<prop_name>_cex.vcd

# Extract value changes in a time range (e.g., cycles 5-15)
awk '/^#5$/,/^#15$/' output/formal/<proof_name>/traces/<prop_name>_cex.vcd
```

### Python VCD Analysis (Advanced)

For complex trace analysis, use Python to parse and inspect VCD files:

```python
#!/usr/bin/env python3
"""Parse a JasperGold VCD trace and report signal transitions."""
import re
import sys

def parse_vcd(filepath):
    """Parse VCD file and return signal map and value changes."""
    signals = {}  # id -> (name, width)
    changes = {}  # timestamp -> [(id, value)]
    current_time = 0

    with open(filepath, 'r') as f:
        in_header = True
        for line in f:
            line = line.strip()
            if line == '$end' and in_header:
                continue
            if line.startswith('$var'):
                parts = line.split()
                # $var wire 1 ! clk $end
                sig_id = parts[3]
                sig_name = parts[4]
                sig_width = int(parts[2])
                signals[sig_id] = (sig_name, sig_width)
            elif line.startswith('$enddefinitions'):
                in_header = False
            elif not in_header:
                if line.startswith('#'):
                    current_time = int(line[1:])
                    changes.setdefault(current_time, [])
                elif line and line[0] in '01xzXZ':
                    # Single-bit value change: <value><id>
                    val = line[0]
                    sig_id = line[1:]
                    changes.setdefault(current_time, []).append((sig_id, val))
                elif line.startswith('b'):
                    # Multi-bit: b<value> <id>
                    parts = line.split()
                    val = parts[0][1:]
                    sig_id = parts[1]
                    changes.setdefault(current_time, []).append((sig_id, val))
    return signals, changes

def report_signal(filepath, signal_name):
    """Report all transitions of a named signal."""
    signals, changes = parse_vcd(filepath)
    # Find signal ID by name
    target_id = None
    for sid, (name, width) in signals.items():
        if signal_name in name:
            target_id = sid
            break
    if not target_id:
        print(f"Signal '{signal_name}' not found. Available signals:")
        for sid, (name, width) in signals.items():
            print(f"  {name} (width={width})")
        return
    print(f"Transitions for {signals[target_id][0]}:")
    for ts in sorted(changes.keys()):
        for sid, val in changes[ts]:
            if sid == target_id:
                print(f"  @{ts}: {val}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python vcd_reader.py <file.vcd> [signal_name]")
        sys.exit(1)
    vcd_file = sys.argv[1]
    sig = sys.argv[2] if len(sys.argv) > 2 else None
    if sig:
        report_signal(vcd_file, sig)
    else:
        signals, changes = parse_vcd(vcd_file)
        print(f"VCD file: {vcd_file}")
        print(f"Signals: {len(signals)}")
        print(f"Timestamps: {len(changes)}")
        print(f"Total transitions: {sum(len(v) for v in changes.values())}")
        print(f"Time range: 0 to {max(changes.keys()) if changes else 0}")
        print("\nSignal list:")
        for sid, (name, width) in signals.items():
            print(f"  [{sid}] {name} (width={width})")
```

### VCD Debug Workflow Summary

| Step | Command | When to use |
|------|---------|-------------|
| Dump single CEX | `visualize -save_vcd -property <prop>` | Property has CEX, need offline analysis |
| Dump all CEX | Loop over `get_property_info -list -status cex` | Batch export for team review |
| Load VCD as reset | `reset -vcd <file>` | Simulation-derived reset needed |
| Check VCD signals | `grep '^\$var' <file>` | Quick signal list without JG |
| Trace signal | `parse_vcd()` Python script | Deep analysis of signal behavior |
| Compare traces | Diff two VCD files | Before/after RTL fix comparison |

### Key VCD File Format Notes

- VCD files from JasperGold counterexamples typically have short traces (10-100 cycles)
- Signal names use hierarchical paths matching JG elaboration (`dut.module.signal`)
- Timestamp units match the proof timescale (usually `1ns`)
- Multi-bit signals are stored as binary strings (`b1010 <id>`)

### FSDB to VCD Conversion

If a trace is in FSDB (Synopsys/Verdi proprietary format), convert to VCD for offline analysis:

```bash
# Using fsdb2vcd (Synopsys/Verdi utility)
fsdb2vcd input.fsdb -o output.vcd

# With scope filter (reduce file size)
fsdb2vcd input.fsdb -o output.vcd -scope tb.dut

# With time range
fsdb2vcd input.fsdb -o output.vcd -start 0 -end 1000ns

# Check tool availability on your Intel system
which fsdb2vcd
find /p/dt /p/cth -name "fsdb2vcd" 2>/dev/null | head -5
```

### logbook.log vs jg.log — Which to Read First

When debugging a regression failure, two logs are typically present:

| Log | What It Contains | When to Use |
|-----|-----------------|-------------|
| `logbook.log` | TREX harness output — fail conditions, elapsed time, forman property results | **First look** — find failing property name and status quickly |
| `jg.log` | Full JasperGold output — compilation, elaboration, prove engine output | **Deep debug** — compile errors, property status details, solver messages |

**Quick logbook.log triage:**
```bash
# Find failing property and status
grep -E "^-[EI]-|forman|assert|cover|proven|cex|fired|undetermined|Elapsed" logbook.log
```

**logbook.log CEX line format:**
```
-E- PropertyDatabase - <full_hier_prop_name> <type> <status> <depth_info> <solver_time>s <task>
```

Example (from vtu_top_ats_liveness failure):
```
-E- PropertyDatabase - vtu_top.fv_vtu_top_top.genblk16.genblk2[1].T_vtu_FPV_vtu_top_assert_ats_req_eventually_seen_on_gfx_iommu_forward_progress assert cex Ht 1-94 4824.86s <embedded>_liveness
```

---

## 14. Debugging Guidance

When proof fails, debug in this order:

1. Compile or Tcl setup errors
2. Clock/reset correctness
3. Assumption sanity
4. Assertion CEX root cause
5. VCD trace analysis for complex failures
6. Unreachable cover interpretation
7. Engine tuning only after setup correctness is confirmed

Do not tune engines before the environment is correct.

---

## 15. Quick Reference

Minimal Jasper FPV command sequence:

```tcl
analyze ...
elaborate ...
clock ...
reset ...
set_prove_orchestration on
```

Minimal debug sequence:

```tcl
reset -analyze
sanity_check -analyze simple_reset
sanity_check -analyze -all
```

Minimal shell sequence in this repo:

```bash
cd <workarea>
setenv WORKAREA `pwd`
/p/hdk/bin/cth_psetup -p ddgcth/1.13 -cfg ddgip -read_only
runfv <proof_name> <dut_module>
tail -f output/formal/<proof_name>/compile/jgproject/jg.log
```

---

## 16. Mapping: Generic Jasper Commands -> Repo runfv Flow

Use this section when you want to understand where each generic Jasper command is handled in this repository.

### A. Shell entry points (repo flow)

```bash
setenv WORKAREA `pwd`
/p/hdk/bin/cth_psetup -p ddgcth/1.13 -cfg ddgip -read_only
runfv <proof_name> <dut_module>
```

Alias expansion used in this repo:

```bash
runfv => set d=!:1 && set p=!:2 && run_fv build-proof -dut $d -p $p && run_fv load-proof -dut $d -p $p &
```

### B. Command mapping table

1. `analyze`
	Handled by run_fv generated analysis scripts and filelists under:
	- `src/val/tb/fpv/<proof_name>/cfg/*_pis.tcl`
	- `src/val/tb/fpv/common/analysis_commands.tcl`
	- `output/formal/<proof_name>/dot_f/*`

2. `elaborate`
	Handled by run_fv elaboration scripts under:
	- `src/val/tb/fpv/common/elab_command.tcl`
	- `src/val/tb/fpv/<proof_name>/cfg/*_pis.tcl`

3. `clock`
	Defined in proof conf file:
	- `src/val/tb/fpv/<proof_name>/cfg/fv_<proof_name>_conf.tcl`

4. `reset`
	Defined in proof conf file:
	- `src/val/tb/fpv/<proof_name>/cfg/fv_<proof_name>_conf.tcl`

5. `set_engine_mode`
	Usually left to defaults/orchestration unless explicitly set in:
	- `src/val/tb/fpv/<proof_name>/cfg/fv_<proof_name>_conf.tcl`

6. `set_prove_orchestration`
	Usually default on; can be overridden in:
	- `src/val/tb/fpv/<proof_name>/cfg/fv_<proof_name>_conf.tcl`

7. `prove`
	Triggered after build/load by Jasper setup flow; results appear in:
	- `output/formal/<proof_name>/compile/jgproject/jg.log`

### C. Concrete mapping for ibecc_cfi_ififo

1. Proof name / DUT launch:
	`runfv ibecc_cfi_ififo ibecc_cfi_ififo`

2. Clock and reset source:
	- `src/val/tb/fpv/ibecc_cfi_ififo/cfg/fv_ibecc_cfi_ififo_conf.tcl`

3. Property source:
	- `src/val/tb/fpv/ibecc_cfi_ififo/src/fv_ibecc_cfi_ififo_assert.va`
	- `src/val/tb/fpv/ibecc_cfi_ififo/src/fv_ibecc_cfi_ififo_assume.va`
	- `src/val/tb/fpv/ibecc_cfi_ififo/src/fv_ibecc_cfi_ififo_cover.va`

4. Runtime log:
	- `output/formal/ibecc_cfi_ififo/compile/jgproject/jg.log`

### D. Practical interpretation

In this repo, you usually do not run raw `analyze`/`elaborate`/`prove` manually.
Instead, you edit proof collateral (cfg/src/dot_f) and relaunch `runfv`; run_fv then issues those Jasper commands internally.

---

## 14. Proof Simplification Commands

Source: Jasper Apps Command Reference Manual, Product Version 2024.12
(`/p/hdk/rtl/cad/x86-64_linux30/jasper/jaspergold/2024.12p002/doc/jasper_command_reference.pdf`)

### 14A. set_proof_simplification

Controls netlist simplification before proof engines start.

```tcl
set_proof_simplification (on | off)
```

**Default:** `on`

**Description:**
During `prove` and `visualize`, the tool simplifies verification tasks before
actual verification starts. Simplification reduces the size of the netlist to
improve overall performance. View proof netlist size in the Proof Messages tab.

NOTE: In some cases, disabling simplification leads to faster operation,
particularly with engines I, C, and C2. Simplification increases the likelihood
that properties are solved during preprocessing (status: `PRE`).

```tcl
# Disable simplification (can help with engines I, C, C2)
set_proof_simplification off

# Re-enable (default)
set_proof_simplification on
```

See also: `set_cache_proof_simplification`, `set_per_property_simplification`, `prove`

---

### 13B. set_cache_proof_simplification

Turns on (or off) caching of proof simplification results for faster repeated runs.

```tcl
set_cache_proof_simplification (on | off)
```

**Default:** `off`

**Description:**
Caches the simplified netlist from the verification task after the first run.
Subsequent `prove` or `visualize` calls on the same task skip re-simplification
and load the cached result, saving startup time.

Important caveats:
- Cache files are stored in the project directory (can be several MB per result on large designs).
- Clear the cache with: `clear -cache_proof_simplification`
- When caching is enabled, newly proven properties cannot be used to further simplify the netlist, which can affect proof performance.
- A cache hit looks like this in `jg.log`:
  ```
  Performing Proof Simplification...
  0.Hp: Loaded cached simplification result
  Proof Simplification completed in 1.07 s
  ```

```tcl
set_cache_proof_simplification on

# Clear the cache when you want a fresh simplification
clear -cache_proof_simplification
```

See also: `set_proof_simplification`, `clear -cache_proof_simplification`, `prove`

---

### 13C. set_per_property_simplification

Enables a fast, property-specific simplification step run per property inside `prove`.

```tcl
set_per_property_simplification (on | off)
```

**Default:** `off`

**Description:**
When enabled, most single-property engines run an additional simplification step
as part of starting the proof for each individual property. This is cheaper and
faster than `set_proof_simplification` (which simplifies the whole task once).

Applies only to engines: **B, D, M, G, G2, K, I, N, C, C2, AB, AD, AM, AG**.
No direct effect on other engines.

Outcomes:
- Can sometimes prove properties outright during this step.
- Can provide `min_length` / `max_length` bounds.
- May leave a smaller simplified problem for the main engine.
- May provide no benefit in some cases.

```tcl
set_per_property_simplification on
prove -all
```

See also: `prove`

---

### 13D. set_prove_advanced_simplification

Performs property-independent model simplification before running `prove`.

```tcl
set_prove_advanced_simplification (on | off)
```

**Default:** `off`

**Description:**
Runs a structural simplification pass on the full model before the `prove`
command. Unlike `set_proof_simplification`, this step is independent of
which properties are being proven. Can improve engine performance on
structurally complex designs.

NOTE: Does **not** support the SEC App, SPV App, or X-Prop App.
If you attempt to run for those apps when this is enabled, the tool
issues a warning and disables the feature.

```tcl
set_prove_advanced_simplification on
prove -all
```

#### set_prove_advanced_simplification_time_limit

Sets a wall-clock time limit for the advanced simplification pass.

```tcl
set_prove_advanced_simplification_time_limit time_limit
```

**Default:** `300s`

Time limit formats supported:
- ISO 8601: `hh:mm:ss.fff` (e.g., `0:05:00` for 5 minutes)
- Seconds integer: `300`
- Seconds with unit: `300s`

```tcl
set_prove_advanced_simplification on
set_prove_advanced_simplification_time_limit 120s
prove -all
```

See also: `set_prove_advanced_simplification`

---

### 13E. prove -simplification_only

Runs only preprocessing and simplification without invoking the regular formal engines.

```tcl
prove -all -simplification_only
prove -property property_name_tcl_list -simplification_only
prove -task task_name -simplification_only
```

**Description:**
Useful heuristically and in parallel with the regular `prove` command to quickly
identify and resolve properties that are trivial for simplification (status: `PRE`).
This is often faster than waiting for the full engine suite to run.

Important notes:
- `prove -simplification_only` and `prove -engine_mode` are **mutually exclusive** in the same command.
- Overrides the current `set_proof_simplification` setting.
- Restores results from the proof cache if `prove_cache` is on. Disable this behavior with `set_prove_cache off`.

```tcl
# Quick pass: resolve anything simplification can prove without invoking engines
prove -all -simplification_only

# Then run full proof for remaining unresolved properties
prove -all
```

See also: `set_proof_simplification`, `set_cache_proof_simplification`, `prove`

---

### 13F. Simplification Decision Guide

| Situation | Recommended setting |
|---|---|
| Default first run | `set_proof_simplification on` (default — leave as-is) |
| Re-running same task repeatedly | `set_cache_proof_simplification on` |
| Properties unresolved, engines slow | `set_per_property_simplification on` |
| Complex structure, engines not converging | `set_prove_advanced_simplification on` |
| Quick triage: find trivially proven properties | `prove -all -simplification_only` |
| Engines I/C/C2 are slower than expected | `set_proof_simplification off` (try disabling) |

---

## Section 14: Complexity Manager

### 14A. complexity_manager — Launch Complexity Viewer

Displays design statistics to identify COI and complexity hot spots (nets, gates, registers).

```tcl
# Full design (ignores stopats, considers env abstractions)
complexity_manager

# Per-task (respects hard stopats and instance stopats)
complexity_manager -task task_name
complexity_manager -task task_name -include_coi -include_assumption -exclude_constant

# Per-property (respects hard stopats in COI)
complexity_manager -property {prop1 prop2}
complexity_manager -property {prop1 prop2} -include_coi -include_assumption -exclude_constant
```

**Switches:**
| Switch | Description |
|---|---|
| (no args) | Analyze full design logic (no properties/abstractions considered) |
| `-task task_name` | Analyze combined COI of all properties in specified task |
| `-property {list}` | Analyze combined COI of specified properties |
| `-include_coi` | Include logic in the COI of the target |
| `-include_assumption` | Include logic from the assumptions |
| `-exclude_constant` | Exclude logic due to constant propagation |

**Usage pattern — finding proof bottlenecks:**
```tcl
# 1. Check complexity of undetermined properties
complexity_manager -property {<undetermined_prop>} -include_coi

# 2. Compare with/without assumptions to understand constraint impact
complexity_manager -task <embedded> -include_assumption

# 3. Identify large modules to target with stopat/abstract
complexity_manager -task <embedded> -include_coi -exclude_constant
```

See also: `get_design_info`

---

## Section 15: check_reset — Reset Verification

### 15A. Running Reset Analysis

```tcl
# Run reset analysis (invalidates Visualize traces and proof results)
check_reset -run
```

Returns: `completed` (success) or `error`.

### 15B. Excluding Registers from Convergence

```tcl
# Add registers to ignore during convergence checks
check_reset -no_convergence -add {flop1 flop2}

# Remove specific registers from the ignore list
check_reset -no_convergence -remove {flop1} -exact
check_reset -no_convergence -remove {flop*} -regexp

# Clear all ignored registers
check_reset -no_convergence -clear

# List registers currently excluded from convergence
check_reset -no_convergence -list
```

**Notes:**
- Running `check_reset -run` invalidates Visualize traces and proof results
- The tool uses check_reset config during any reset analysis called by other commands (e.g., `prove`, `get_reset_info`)
- Use `set_reset_extended_mode` to turn off check_reset influence on other commands
- `-no_convergence` is supported with `-expression` reset; not supported with `-sequence` reset unless `trace_show_reset false` is set

See also: `get_reset_info`, `reset`

---

## Section 16: Formal Profiler

### 16A. formal_profiler — Profile Engine Work on a Property

Profiles and provides detailed information about an engine's work on a property to find proof bottlenecks.

```tcl
# Start profiling (returns run name)
formal_profiler -property prop:0 -engine_mode B
formal_profiler -property prop:0 -engine_mode M -viewer
formal_profiler -property prop:0 -engine_mode B -file profile.log -force
formal_profiler -property prop:0 -time_limit 30m -initial_bound 5 -report_period 30s

# Report effort for entities from a specific run/bound
formal_profiler -report formalprofiler:1 -bound 4 -signal {sig1 sig2 sig3}
formal_profiler -report formalprofiler:1 -bound 4 -instance {inst1 inst2}
formal_profiler -report -property {prop1 prop2}

# Manage runs
formal_profiler -list
formal_profiler -show {formalprofiler:1 formalprofiler:2}
formal_profiler -show {formalprofiler:1} -list bound
formal_profiler -viewer
formal_profiler -stop
formal_profiler -stop formalprofiler:1
```

**Switches for `-property`:**
| Switch | Description |
|---|---|
| `-engine_mode (B \| M)` | Select engine B (default) or M |
| `-silent` | Suppress info messages in console |
| `-time_limit time` | Set proof maximum run time |
| `-initial_bound N` | Start profiling at this bound (engine B only) |
| `-report_period time` | Report interval during a bound (default 60s; 0 = end-of-bound only) |
| `-viewer` | Open Formal Profiler GUI |
| `-file name [-force]` | Redirect output to file |

**Limitations:**
- Requires background proof
- Supports only one engine thread
- Does not support SPV and XPROP properties
- Does not support word-level transformations/reductions

**Usage pattern — diagnosing convergence issues:**
```tcl
# 1. Start a background proof
prove -property my_prop -bg

# 2. Profile the property
formal_profiler -property my_prop -engine_mode B -viewer

# 3. Check which instances consume most effort
formal_profiler -report -bound 10 -instance {*}

# 4. Apply stopat to high-effort instances
stopat high_effort_instance
```

See also: `prove`, `set_prove_time_limit`

---

## Section 17: stopat — Cut Netlist Traversal

### 17A. stopat — Disconnect Driving Logic

Forces the tool to stop traversing a netlist at a specified signal or instance, disconnecting it from its driving logic. Effective when large logic (e.g., 64-bit address comparison) drives a signal that can take any value.

```tcl
# Apply stopat to signals
stopat signalA
stopat {sig0} {sig1} {sig2} {sig3}
stopat {sig*[3:0]}
stopat {sig*[7]}

# Apply stopat to instance (outputs receive stopats)
stopat inst0

# Conditional stopat (only effective when expression is true)
stopat signalB -condition {!enable}

# Global (environment) stopat
stopat -env signalA

# Task-specific stopat
stopat -task my_task signalA

# Reset-only stopat
stopat -reset signalA
```

### 17B. Listing Stopats

```tcl
# List stopats with driven nets in current task + global
stopat -list

# List user-defined stopats only
stopat -list_user

# List all stopats including undriven signals
stopat -list_all

# Include condition expressions in listing
stopat -list -include_condition

# Silent (return as Tcl values, no print)
stopat -list -silent

# Scoped listing
stopat -env -list
stopat -task my_task -list
stopat -reset -list
```

### 17C. Removing Stopats

```tcl
# Remove specific stopat
stopat -remove signalA
stopat -remove inst0

# Remove from global/task/reset scope
stopat -env -remove signalA
stopat -task my_task -remove signalA
stopat -reset -remove signalA

# Clear all stopats in current task
stopat -clear

# Clear all global stopats
stopat -env -clear
```

**Notes:**
- Supports wildcards (* and ?) in signal names, including bit ranges
- Supports escaped names (including those containing * and ?)
- Context-sensitive: applies to current task unless `-env`, `-task`, or `-reset` is used
- The `reset` command considers global (-env) and reset (-reset) stopats
- Condition expressions support $dff, $dlatch, $past, |->, ##n operators

See also: `clock`, `replace_driver`

---

## Section 18: ProofMaster Configuration

### 18A. proofmaster -config — Control ProofMaster Settings

```tcl
# Enable ProofMaster
set_proofmaster on

# Configure trace handling
proofmaster -config -keep_traces none       ;# none | asserts | all | default
proofmaster -config -cache_traces asserts   ;# none | all | default | asserts

# Auto-delete stale data after N days
proofmaster -config -max_data_age 10
proofmaster -config -prove_cache_max_data_age 7
proofmaster -config -trace_replay_max_data_age 14

# Min trace generation time for caching (skip fast traces)
proofmaster -config -prove_cache_min_trace_time 10s
proofmaster -config -trace_replay_min_trace_time 60s

# Proof cache signature computation time limit
proofmaster -config -prove_cache_time_limit 2m

# Stagnation control
proofmaster -config -stagnation_mode bounds       ;# stop | default | bounds | off
proofmaster -config -stagnation_trigger_type aggressive  ;# relaxed | default | aggressive
proofmaster -config -stagnation_trigger_max_time 30m

# Use-case presets
proofmaster -config -use_case individual      ;# development (default)
proofmaster -config -use_case full_signoff    ;# late-stage, prioritize proven+precondition covers
proofmaster -config -use_case bounds_signoff  ;# late-stage, bounded proofs acceptable
proofmaster -config -use_case regression      ;# prioritize finding CEXs
proofmaster -config -use_case full_signoff -show   ;# preview without executing

# Cross-task trace replay
proofmaster -config -trace_replay_cross_task on
```

### 18B. ProofMaster Defaults

| Parameter | Default |
|---|---|
| `-keep_traces` | all |
| `-cache_traces` | all |
| `-max_data_age` | 0 (unlimited) |
| `-prove_cache_min_trace_time` | 0s |
| `-trace_replay_min_trace_time` | 180s |
| `-prove_cache_time_limit` | 0s |
| `-stagnation_mode` | default |
| `-stagnation_trigger_type` | default |
| `-stagnation_trigger_max_time` | 0s (disabled) |
| `-use_case` | individual |
| `-trace_replay_cross_task` | off |

### 18C. Stagnation Mode Decision Guide

| Situation | Recommended stagnation_mode |
|---|---|
| Proof not converging, want to stop wasting time | `stop` |
| Let tool adapt engine selection on stagnation | `default` |
| Want to extend bounded proofs when stuck | `bounds` |
| Proof is making slow progress, keep trying | `off` |

### 18D. Use-Case Decision Guide

| Scenario | Use-case |
|---|---|
| Developing new proofs interactively | `individual` (default) |
| Weekend/nightly regression — find bugs fast | `regression` |
| Final signoff — need full proofs | `full_signoff` |
| Final signoff — bounded proofs acceptable | `bounds_signoff` |

---

## Section 19: property_triage — Group Similar Failing Properties

```tcl
# Run triage clustering (default medium effort)
property_triage -run
property_triage -run -effort low
property_triage -run -effort high -task task_a
property_triage -run -property {prop1 prop2 prop3} -file triage.csv -force

# Retrieve last clustering result
property_triage -result
property_triage -result -file results.csv -force
property_triage -result -silent
```

**Effort levels:**
| Effort | Behavior |
|---|---|
| `low` | Basic property/trace info; fastest; more groups |
| `medium` (default) | Trace analysis + property info; less restricted comparison |
| `high` | Further trace/property analysis; fewer groups |

Returns a Tcl dictionary with bucket ID, property count, and property names per bucket.

---

## Section 20: Deep Bug Hunting (hunt command)

### 20A. Overview

Bug hunting focuses on finding bugs with a **deep but sparse** search (not exhaustive). Use when:
- You have enough assertions but are no longer making progress with `prove`
- Undetermined properties remain static
- You want to find deep bugs that bounded proofs cannot reach

### 20B. Hunt Strategies Summary

| Strategy | Mode | Default Engine | Liveness | Best For |
|---|---|---|---|---|
| Formal + overconstraint | `formal` | {Ht B Bm Hts} | Yes* | Reducing input space to find bugs faster |
| Bound Swarm | `bound_swarm` | Bm | Yes* | Targeting specific cycle ranges |
| Cycle Swarm | `cycle_swarm` | B | Yes* | Parallelized trace attempts |
| State Swarm | `state_swarm` | L | **No** | Deep state exploration with helper covers |
| Loop Swarm | `loop_swarm` | B | **Only** liveness | Multiple loop lengths in parallel |
| Trace Swarm | `trace_swarm` | {Ht B} | Yes* | Extending from existing cover traces |
| Trace Search | `trace_search` | {B Bm} | Yes* | Depth analysis along entire trace |
| Guidepointing | `guidepoint` | {Hp Ht B L} | Yes* | Following specific cover sequence |
| Simulation | `simulation` | U2 | Only w/ engine U | Random walk through states |

### 20C. Core Hunt Workflow

```tcl
# 1. Configure a strategy
hunt -config -strategy my_strat -mode state_swarm

# 2. (Optional) View strategy settings
hunt -show -strategy my_strat

# 3. (Optional) Add overconstraints
hunt -config -strategy my_strat -add_constraint {!req1}
hunt -config -strategy my_strat -add_constraint {len==4}

# 4. Run hunt
hunt -run -strategy my_strat -task <embedded> -bg -time_limit 12h

# 5. Check results
hunt -report -status
hunt -report -detailed
```

### 20D. hunt -run — Running Hunt

```tcl
# Run on task
hunt -run -strategy strat -task <embedded> -bg

# Run on specific properties
hunt -run -strategy strat -property {prop1 prop2 prop3} -bg

# With time/job limits
hunt -run -strategy strat -task <embedded> -time_limit 4h -max_jobs 10 -bg

# Force re-run on already-determined properties (find more traces)
hunt -run -strategy strat -property {prop1} -force -bg

# Automatic flow (recommended for State Swarm)
hunt -run -task <embedded> -auto -bg
hunt -run -task <embedded> -auto -auto_helper_num 200 -auto_keep_helpers -bg
```

### 20E. State Swarm — Recommended Flow

```tcl
# Generate helper covers for state exploration
cover -generate -auto -num 100

# Configure State Swarm
hunt -config -strategy ss -mode state_swarm -max_jobs 10 -time_limit 12h

# Optional: tune engine L parameters
hunt -config -strategy ss -first_trace_attempt {20%:[1] 80%:[2..40]}

# Run hunt
hunt -run -strategy ss -task <embedded> -bg
```

**Or use the automatic flow (simpler, recommended):**
```tcl
hunt -run -task <embedded> -auto -time_limit 12h -bg
```

### 20F. Bound Swarm — Targeted Cycle Range

```tcl
# Default bound swarm
hunt -config -strategy BS -mode bound_swarm

# Custom interval (cycles 65-200)
hunt -config -strategy BS -mode bound_swarm \
  -first_trace_attempt 65 -max_trace_length 200

# Custom with time factor
hunt -config -strategy BS -mode bound_swarm \
  -max_jobs 4 \
  -first_trace_attempt 1 -max_trace_length 100 \
  -trace_attempt_time_limit 1s \
  -trace_attempt_time_limit_factor 10

hunt -run -strategy BS -task <embedded> -bg
```

### 20G. Formal Strategy with Overconstraining

```tcl
# Configure formal strategy
hunt -config -strategy oc -mode formal

# Add local overconstraints
hunt -config -strategy oc -add_constraint {!req1}
hunt -config -strategy oc -add_constraint {len==4}

# Run
hunt -run -strategy oc -task <embedded> -bg
```

**Common overconstraints:**
- Disable agents/masters: `{!agent_active}`
- Limit packet length: `{pkt_len < 8}`
- Constrain data bus: `{data == '0 || data == '1}`
- Fix config registers: `{cfg_reg == 4'hA}`

### 20H. Trace Swarm + State Swarm Combination

```tcl
# State Swarm to find cover traces
hunt -config -strategy covers_ss -mode state_swarm -target_type cover

# Trace Swarm to hunt from those traces
hunt -config -strategy liveness_ts -mode trace_swarm \
  -target_type assert_liveness -max_jobs 6 -per_trace_time_limit 20s

# Combined run
hunt -run -task . -strategy covers_ss -use_strategy liveness_ts -time_limit 1h -bg
```

### 20I. Trace Search — Depth Analysis Along Traces

```tcl
hunt -config -strategy ts -mode trace_search \
  -target_depth 15 -interval_cycles 10 -max_jobs 20

hunt -run -strategy ts -property {prop_with_trace} -bg
```

### 20J. Hunt Management Commands

```tcl
# List strategies and tags
hunt -list strategy
hunt -list tag

# Show strategy configuration
hunt -show -strategy my_strat
hunt -show -strategy my_strat -silent

# Reporting
hunt -report -status
hunt -report -detailed
hunt -report -engine_config -engine_stats
hunt -report -trace_swarm -tag my_tag -completed

# Save/load strategies
hunt -save my_strat.cfg -strategy my_strat -force
hunt -load my_strat.cfg

# Clear
hunt -clear -strategy my_strat -force
hunt -clear -tag my_tag
```

### 20K. Deadlock Hunting (check_dlh)

```tcl
# Setup
task -create deadlock -set
check_dlh -generate -cover
check_dlh -generate -trap
assert -set_store_trace unlimited *

# Hunt
hunt -run -task deadlock -bg

# Verify deadlock candidates
check_dlh -verify
```

### 20L. Hunt Decision Guide

| Situation | Recommended Strategy |
|---|---|
| General bug hunting, no specific target | `state_swarm` with `-auto` |
| Know the cycle range where bug exists | `bound_swarm` |
| Want to reduce input space | `formal` with `-add_constraint` |
| Have cover traces, want to extend | `trace_swarm` |
| Need depth analysis along traces | `trace_search` |
| Liveness properties stuck | `loop_swarm` or `trace_swarm` |
| Quick random simulation | `simulation` |
| Know the state path to the bug | `guidepoint` with `-path` |
| Deadlock prone design | `check_dlh` flow |

---

## Section 21: check_assumptions — Overconstraint Detection

### 21A. check_assumptions — Verify Assumption Sanity

```tcl
# Run all assumption checks on current task
check_assumptions -task <embedded> -bg

# Run specific checks
check_assumptions -conflict -task <embedded> -bg
check_assumptions -dead_end -task <embedded> -bg
check_assumptions -live -task <embedded> -bg
check_assumptions -deadlock -task <embedded> -bg
check_assumptions -sanity -task <embedded> -bg

# With time/length limits
check_assumptions -task <embedded> -time_limit 30m -max_length 100 -bg

# From a specific property/trace
check_assumptions -from prop_name -trace_id 1 -cycle 5

# Simplification only (no engines)
check_assumptions -all -simplification_only
```

### 21B. Assumption Minimization

```tcl
# Find minimal set of assumptions needed
check_assumptions -minimize -bg

# With required assumptions that cannot be removed
check_assumptions -minimize -required_assumes {critical_assume1 critical_assume2} -bg

# Include environment assumes and clock/reset in analysis
check_assumptions -minimize -include_env_assumes -include_clock -include_reset -bg

# Multiple attempts with time limit
check_assumptions -minimize -attempts 5 -attempts_time_limit 10m -bg
```

### 21C. Viewing Results

```tcl
# Show check_assumptions results
check_assumptions -show
check_assumptions -show -all
check_assumptions -show -dead_end
check_assumptions -show -live
check_assumptions -show -deadlock
```

### 21D. Properties Created by check_assumptions

| Property | CEX means | Impact |
|---|---|---|
| `:noConflict` | Assumptions create unavoidable finite conflict from reset | All proven/unreachable results are **vacuous** |
| `:noDeadEnd` | Reachable state with no valid next cycle | Simulation would deadlock at this state |
| `:live` | Impossible to satisfy all fairness constraints | Liveness results are **vacuous** |
| `:noDeadlock` | Reachable state from which fairness constraints cannot be satisfied | Liveness deadlock found |

### 21E. Overconstraint Debugging Workflow

```tcl
# 1. Check for conflicts (most critical)
check_assumptions -conflict -task <embedded> -bg

# 2. If :noConflict has CEX → assumptions are contradictory
#    Minimize to find which assumptions conflict
check_assumptions -minimize -bg

# 3. Check for dead-ends
check_assumptions -dead_end -task <embedded> -bg

# 4. If :noDeadEnd has CEX → inspect trace to find blocking assumption
#    Open trace in Visualize to see which assumption blocks progress
```

---

## Section 22: autoprove — Automatic Engine Orchestration

### 22A. autoprove — Dynamic Verification Orchestration

Hybrid command that calls `prove` multiple times with dynamically chosen parameters, engines, and execution order to maximize verification results within a given budget.

```tcl
# Prove all properties in all tasks
autoprove -all -bg

# Prove specific tasks
autoprove -task {taskA taskB taskC} -bg

# Prove specific properties
autoprove -property {propA propB propC} -bg

# With time and memory budgets
autoprove -all -time_limit 4h -mem_limit 8g -bg

# Split into chunks for large designs
autoprove -all -time_limit 2h -chunks 4 -bg

# Mode-focused runs
autoprove -all -mode prove -bg          ;# Assertions only
autoprove -all -mode cover -bg          ;# Covers only
autoprove -all -mode hard -bg           ;# Hard-to-prove properties (needs adequate time)
autoprove -all -mode superlint -bg      ;# Superlint-generated properties
autoprove -all -mode coverage -bg       ;# Coverage-generated properties
autoprove -all -mode xprop -bg          ;# X-Prop properties

# Effort control
autoprove -all -effort low -bg          ;# Limited resources (local run)
autoprove -all -effort medium -bg       ;# Default engine set
autoprove -all -effort high -bg         ;# All suitable engines (resource intensive)
autoprove -all -effort user -engines {B D Ht} -bg  ;# Custom engine set

# Additional switches
autoprove -all -with_helpers -bg        ;# Include helper assertions
autoprove -all -with_proven -bg         ;# Use all proven assertions as assumptions
autoprove -all -assumption_lifting -bg  ;# Only use relevant assumption subset
autoprove -all -suppress_traces -bg     ;# Skip trace generation
autoprove -all -dump_trace -dump_trace_type fsdb -dump_trace_dir ./traces -bg
```

### 22B. autoprove Switches

| Switch | Description |
|---|---|
| `-all` | Prove all assertions and covers in all tasks |
| `-task list` | Prove all properties in specified tasks |
| `-property list` | Prove specified properties |
| `-bg` | Run in background |
| `-time_limit time` | Override default 2h time budget |
| `-mem_limit mem` | Override default 2048MB memory budget |
| `-chunks N` | Split job into N subjobs (for large designs) |
| `-mode` | Focus on: prove, cover, hard, superlint, coverage, xprop |
| `-effort` | Engine intensity: low, medium, high, user |
| `-with_helpers` | Include helper assertions |
| `-with_proven` | Use proven assertions as assumptions |
| `-assumption_lifting` | Use only relevant assumptions |
| `-suppress_traces` | Skip trace generation |
| `-keep_traces` | Force trace generation (overrides superlint/coverage default) |
| `-dump_vcd` | Dump VCD for each Covered/Cex property |
| `-dump_trace` | Dump traces as found (shm/vcd/fsdb) |
| `-verbosity N` | Log verbosity (0=silent, default=6) |

### 22C. autoprove vs prove Decision Guide

| Situation | Use |
|---|---|
| Standard proof run | `prove` |
| Want tool to optimize engine/order automatically | `autoprove` |
| Large design, limited resources | `autoprove -effort low -chunks N` |
| Late-stage hard properties | `autoprove -mode hard -time_limit 8h` |
| Quick triage of Superlint/Coverage results | `autoprove -mode superlint` |

See also: `prove`, `get_status`, `set_engine_mode`

---

## Section 23: get_needed_assumptions — Find Irreducible Assumption Set

### 23A. get_needed_assumptions — Assumption Minimization

Systematically disables/enables assumptions via bisection to find the irreducible (minimal) set needed to achieve a target status.

```tcl
# Find minimal assumptions for a proven property
get_needed_assumptions -property my_assert -bg

# For an unreachable cover
get_needed_assumptions -property my_cover -status unreachable -bg

# With specific assumptions to consider
get_needed_assumptions -property my_prop -assumes {assume:0 assume:1 assume:2} -bg

# Include environment, clock, reset in analysis
get_needed_assumptions -property my_prop -include_env_assumes -include_clock -include_reset

# Required assumptions (always included in result)
get_needed_assumptions -property my_prop -required_assumes {assume:0} -bg

# Control effort
get_needed_assumptions -property my_prop -attempts 10 -attempts_time_limit 5m -bg

# Use specific engines
get_needed_assumptions -property my_prop -engine_mode {B Ht} -bg

# From a specific trace state
get_needed_assumptions -property my_prop -from cover_prop -cycle 50 -bg

# Get results of last run
get_needed_assumptions -result
get_needed_assumptions -run_status
```

### 23B. Return Dictionary Keys

| Key | Value |
|---|---|
| `run_status` | not_started, running, completed |
| `exit_status` | completed, attempts_limit, attempts_time_limit, max_trace_length, stopped_by_user, stopped_by_status, stopped_by_remaining, aborted |
| `prove_attempts` | Number of prove attempts made |
| `needed` | Set of needed assumptions |
| `under_approx` | Needed assumptions found before stopping (if stopped early) |
| `needed_reset` | Set of reset constraints (with `-include_reset`) |
| `needed_clock` | Set of clock constraints (with `-include_clock`) |
| `needed_properties` | Set of assertions/covers (with `-include_properties`) |
| `result_task` | Task demonstrating the result (NDD_ASSUMES*) |

### 23C. Use Cases

| Scenario | Command |
|---|---|
| Find conflicting assumptions (overconstraint) | `get_needed_assumptions -property :noConflict -status cex` |
| Cover unexpectedly unreachable | `get_needed_assumptions -property my_cover -status unreachable` |
| Speed up proof by removing unnecessary assumes | `get_needed_assumptions -property my_prop` |
| Identify needed clock/reset constraints | `get_needed_assumptions -property my_prop -include_clock -include_reset` |

### 23D. Overconstraint Debug Flow Using get_needed_assumptions

`get_needed_assumptions` is a key tool for diagnosing overconstraints. When `check_assumptions` detects a problem, use `get_needed_assumptions` to pinpoint which assumptions are causing it:

```tcl
# Step 1: Detect overconstraint
check_assumptions -task <embedded> -bg

# Step 2: If :noConflict has CEX, find which assumptions cause the conflict
get_needed_assumptions -property <embedded>::check_assumes:noConflict -status cex -bg

# Step 3: View results — assumptions in "needed" are the conflicting set
get_needed_assumptions -result
# Any assumption NOT in the "needed" set is safe; those IN "needed" form the minimal conflicting group

# Step 4: For dead_end overconstraints
get_needed_assumptions -property <embedded>::check_assumes:noDeadEnd -status cex -bg

# Step 5: For vacuously-proven assertions (all covers unreachable)
get_needed_assumptions -property my_vacuous_assert -status proven -bg
# Result shows which assumptions are needed for the proof — removing any reveals if proof was vacuous
```

**Key insight:** Assumptions *not* in the returned `needed` set are either redundant or contributing to the overconstraint — they are candidates for removal.

See also: `assume`, `check_assumptions`, `prove`

---

## Section 24: debug_explorer — Why-Path Debug Assistant

### 24A. debug_explorer — Trace Causality Analysis

Creates a "why path" through the waveform showing causality chains from a property trigger to root causes.

```tcl
# Initialize why path from triggering cycle (default: 3 decisions)
debug_explorer -init

# With stop conditions
debug_explorer -init -why_limit 10           ;# Max 10 why operations
debug_explorer -init -decision_limit 5       ;# Max 5 branch decisions
debug_explorer -init -until {sig1 10}        ;# Stop at specific signal/cycle

# Change a decision in the path
debug_explorer -change_decision {sig1 10} {sig2 9}
debug_explorer -change_decision {sig1 10}    ;# Tool selects alternative

# Continue path from where it stopped
debug_explorer -continue
debug_explorer -continue {sig3 8}            ;# Continue from specific node

# Constrain decisions
debug_explorer -constrain {sig1 10} {sig2 9} -force    ;# Force this decision
debug_explorer -constrain {sig1 10} {sig2 9} -forbid   ;# Prevent this decision
debug_explorer -constrain {sig1 10} {sig2 9} -release  ;# Remove constraint

# Dump current path
debug_explorer -dump_path

# With specific Visualize window
debug_explorer -init -visualize_window visualize:1
```

### 24B. Color Coding

| Color | Meaning |
|---|---|
| Gray | Signal-cycle pair with only one possible child |
| Purple | Signal-cycle pair with multiple children (tool selected one) |
| Arrows | Point from signal-cycle to its selected child |

### 24C. Debug Explorer Workflow

```tcl
# 1. Open CEX trace in Visualize
visualize -property failing_assert -new_window

# 2. Initialize why-path
debug_explorer -init

# 3. If path is too short, continue
debug_explorer -continue -decision_limit 3

# 4. If wrong branch taken, change decision
debug_explorer -change_decision {wrong_sig 5} {better_sig 4}

# 5. Export path for reference
debug_explorer -dump_path
```

See also: `visualize`

---

## Section 25: proof_structure — Hierarchical Proof Decomposition

### 25A. proof_structure — Decompose Complex Proofs

Sets up formal methodologies with hierarchical environments and result propagation.

```tcl
# Initialize from current task
proof_structure -init root_node -from <embedded> -copy_all

# Create case split (decompose property by conditions)
proof_structure -create case_split \
  -from root_node \
  -condition {"{cond1}" "{cond2}" "{!cond1 && !cond2}"} \
  -property {my_prop}

# Create hard case split (with validity check)
proof_structure -create hard_case_split \
  -from root_node \
  -condition {"{mode==0}" "{mode==1}" "{mode==2}"} \
  -validity exhaustive

# Create stopat node
proof_structure -create stopat \
  -from root_node \
  -add {complex_signal}

# Create edit node (for manual environment changes)
proof_structure -create edit_node -from root_node

# Create compositional assume-guarantee
proof_structure -create compositional_assume_guarantee \
  -from root_node \
  -property {prop1 prop2}

# Create underconstraint/overconstraint nodes
proof_structure -create underconstraint -from root_node
proof_structure -create overconstraint -from root_node
```

### 25B. Query and Management

```tcl
# Get property info within proof structure
proof_structure -get_property_info my_prop -list {status min_length max_length}
proof_structure -get_property_info my_prop -node case_node1

# Get node info
proof_structure -get_node_info root_node -list {parent children class type}
proof_structure -get_node_list

# Propagate results through the tree
proof_structure -propagate

# Set which results to display
proof_structure -set_visible_results proof_structure  ;# Show propagated results
proof_structure -set_visible_results local            ;# Show per-node results

# Remove a node
proof_structure -remove node_name

# Export node as a new task
proof_structure -export node_name -create new_task

# Unify results from all nodes
proof_structure -unify_results
```

### 25C. When to Use Proof Structure

| Situation | Technique |
|---|---|
| Property fails only in certain modes | Case split by mode |
| Large COI blocking convergence | Stopat node to cut complexity |
| Multiple independent verification goals | Compositional assume-guarantee |
| Need to verify case split covers all states | Hard case split with `-validity exhaustive` |

See also: `task`, `stopat`, `abstract`

---

## Section 26: expert_system — Custom Rule Engine

### 26A. expert_system — Rule Management Overview

Defines custom rules that trigger on design events and provide recommendations.

```tcl
# List all rules
expert_system -rule -list all
expert_system -rule -list custom
expert_system -rule -list built_in

# Enable/disable rules
expert_system -rule -enable rule_id
expert_system -rule -disable rule_id

# Show rule details
expert_system -rule -show rule_id -title -description -trigger

# View rule history
expert_system -rule -history
expert_system -rule -history matched
```

### 26B. Custom Rule Definition

```tcl
# Add a custom rule
expert_system -rule -add my_rule -type general \
  -title "Check for too many assumptions" \
  -description "Warns when task has > 50 assumptions" \
  -procedure my_check_proc \
  -trigger {post_prove_cmd formal_env_change} \
  -category environment

# Edit existing rule
expert_system -rule -edit my_rule -trigger {post_prove_cmd}

# Remove rule
expert_system -rule -remove my_rule
```

### 26C. Waiver Management

```tcl
# Add waiver to suppress specific rule matches
expert_system -waiver -add -signal {clk_*} -comment "Clock signals OK" -regexp
expert_system -waiver -add -property {helper_*} -comment "Helper props" -regexp
expert_system -waiver -add -rule_id built_in_rule_3 -task {debug_*} -comment "Skip in debug"

# List and manage waivers
expert_system -waiver -list
expert_system -waiver -remove waiver_id

# Export/import waivers
expert_system -waiver -export -file waivers.tcl -force
expert_system -waiver -import -file waivers.tcl
```

### 26D. Trigger Events

| Trigger | Fires when |
|---|---|
| `post_analyze_cmd` | After analyze completes |
| `post_elaborate_cmd` | After elaborate completes |
| `netlist_change` | Design netlist changes |
| `clock_change` | Clock configuration changes |
| `reset_change` | Reset configuration changes |
| `formal_env_change` | Formal environment changes |
| `property_change` | Properties added/removed/modified |
| `proof_setting_change` | Proof settings change |
| `post_prove_cmd` | After prove completes |
| `debug_property_start` | Debug session begins |

See also: `check_superlint`

---

## Section 27: Design Query Commands

### 27A. get_fanin — Cone of Influence Analysis

```tcl
# Direct fanin (one level, skipping buffers)
get_fanin signal_name
get_fanin property_name
get_fanin {expression}

# With options
get_fanin signal_name -add_clock_logic        ;# Include clock pin logic
get_fanin signal_name -ignore_weak_driver     ;# Only active drivers
get_fanin signal_name -env                    ;# Full design (ignore task stopats/assumes)
get_fanin signal_name -show_schematic         ;# Open schematic viewer

# Into cell defines
get_fanin -go_into_cell_define signal_name

# Transitive fanin (recursive to primary inputs/stopats)
get_fanin -transitive signal_name
get_fanin -transitive signal_name -env
get_fanin -transitive signal_name -task my_task
get_fanin -transitive signal_name -filter_out {boundary non_boundary}
get_fanin -transitive signal_name -barrier {reg_boundary_sig}
get_fanin -transitive signal_name -avoid_pin {flop_async_reset flop_clock}
get_fanin -transitive signal_name -silent

# Show driving expression
get_fanin -show_expr signal_name
get_fanin -show_expr signal_name -no_constant_propagation
```

### 27B. get_fanout — Forward Trace

```tcl
# Direct fanout
get_fanout signal_name
get_fanout signal_name -show_schematic

# Transitive fanout (to primary outputs)
get_fanout -transitive signal_name
get_fanout -transitive signal_name -silent
get_fanout -transitive signal_name -barrier {output_reg}
```

### 27C. get_flop_info — Register Details

```tcl
# Full info for a flop
get_flop_info flop_name

# Specific attributes
get_flop_info -clock flop_name              ;# Clock signal
get_flop_info -edge flop_name               ;# Sensitivity edge
get_flop_info -data flop_name               ;# Data pin signals
get_flop_info -reset_type flop_name         ;# sync/async/mixed/none
get_flop_info -reset_pin flop_name          ;# Reset signal
get_flop_info -async_reset_pin flop_name    ;# Async reset signal
get_flop_info -sync_reset_pin flop_name     ;# Sync reset signal
get_flop_info -reset_value_pin flop_name    ;# Reset value
get_flop_info -file_name flop_name          ;# Source file
get_flop_info -line flop_name               ;# Source line number

# Multiple flops, compact output
get_flop_info -clock -reset_type -silent {flop1 flop2 flop3}
get_flop_info -bit_blast wide_flop          ;# Expand to individual bits
```

### 27D. get_signal_info — Signal Properties

```tcl
# Signal type (output/input/inout/undriven/MPRAM/logic)
get_signal_info -type signal_name

# Logic type (latch/flop/wire/MPRAM)
get_signal_info -logic signal_name

# Port direction (input/output/inout/undef)
get_signal_info -port_type signal_name

# Bit range and dimensions
get_signal_info -indexes signal_name
get_signal_info -width signal_name
get_signal_info -bit_blast signal_name

# Hierarchy decomposition
get_signal_info -get_module signal_name
get_signal_info -get_instance signal_name
get_signal_info -get_signal signal_name

# Source location
get_signal_info -declaration signal_name -file_name -line
get_signal_info -driver signal_name -file_name -line

# Equivalent signals
get_signal_info -equiv signal_name
get_signal_info -equiv -forward signal_name
```

### 27E. get_signal_list — Signal Enumeration

```tcl
# List all signals matching pattern
get_signal_list -regexp {pattern}
get_signal_list -type input
get_signal_list -type output
get_signal_list -type flop
get_signal_list -type latch
```

### 27F. get_trace_info — Trace Metadata

```tcl
# Get trace info (length, engine, time, job, tag)
get_trace_info 1
# Returns: length 6 engine L time 0.4 job 0.0.L tag {}

# Typical workflow: get trace IDs then query them
set trace_ids [get_property_info -list trace_id my_prop]
foreach tid $trace_ids { puts [get_trace_info $tid] }
```

---

## Section 28: check_xprop — X-Propagation Verification

### 28A. check_xprop — X-Prop Analysis Flow

```tcl
# Initialize X-prop analysis
check_xprop -init
check_xprop -init_control true -sequential
check_xprop -init_data true
check_xprop -init_index true

# Create X-prop assertions
check_xprop -create -control              ;# Control point X-checks
check_xprop -create -data                 ;# Data point X-checks
check_xprop -create -index                ;# Array index X-checks
check_xprop -create -outputs              ;# Output X-checks
check_xprop -create -bbox_inputs          ;# Black-box input X-checks
check_xprop -create -flops_with_reset_pin ;# Flop reset X-checks
check_xprop -create -counters             ;# Counter X-checks
check_xprop -create -fsms                 ;# FSM X-checks

# Create with filtering
check_xprop -create -control -instance {my_inst*} -regexp
check_xprop -create -control -from signal_a -to {signal_b signal_c}
check_xprop -create -control -precond {valid_mode}
check_xprop -create -control -sampling_clock clk_200
check_xprop -create -control -task xprop_task -no_prefix

# X-prop abstractions (reduce complexity)
check_xprop -abstract multiplier
check_xprop -abstract shift -minimum_width 8
check_xprop -abstract adder -exclude_module {small_add} -regexp
check_xprop -abstract -list
check_xprop -abstract -remove abs_name
check_xprop -abstract -clear

# Prove X-prop assertions
check_xprop -prove -bg
check_xprop -prove -task xprop_task -bg
check_xprop -prove -property {xprop_prop1 xprop_prop2} -bg
check_xprop -prove -time_limit 2h -engine_mode {B Ht} -bg
check_xprop -prove -cex_limit 10 -bg     ;# Stop after 10 failures
```

### 28B. X-Prop Waivers

```tcl
# Waive specific properties
check_xprop -waiver -add -property {xprop:ctrl:*clk*} -comment "Clock OK" -regexp

# Waive by category/instance
check_xprop -waiver -add -instance my_inst -category clocks_and_resets -comment "Expected"

# Manage waivers
check_xprop -waiver -list
check_xprop -waiver -remove waiver_id
check_xprop -waiver -export -file_name xprop_waivers.tcl
check_xprop -waiver -import -file_name xprop_waivers.tcl
```

### 28C. X-Prop Reporting

```tcl
# Reports
check_xprop -report source -detailed
check_xprop -report reason -include_failing_properties
check_xprop -report -csv xprop_results.csv
check_xprop -report -html -launch_html_browser
check_xprop -report -status cex -detailed

# Debug highlight
check_xprop -highlight_failure_path
check_xprop -highlight_failure_path -clear
```

---

## Section 29: check_unr — Unreachability Analysis

### 29A. check_unr — Find Unreachable Code

```tcl
# Initialize (import coverage database)
check_unr -init -coverage {block expr toggle fsm}
check_unr -init -coverage {block} -covdb path/to/covdb -dutinst top.dut

# Setup task
check_unr -setup -task my_task

# Enable/disable properties
check_unr -enable_property -all
check_unr -disable_property {prop1 prop2}

# Prove unreachability
check_unr -prove -all -bg
check_unr -prove -task my_task -time_limit 1h -bg
check_unr -prove -engine_mode {B Ht} -bg
check_unr -prove -shallow_analysis -bg        ;# Quick pass

# List results
check_unr -list properties -type unreachable
check_unr -list properties -type reachable
check_unr -list properties -type bounded
check_unr -list properties -type unprocessed

# Partitioned proving (for large designs)
check_unr -generate_partition -threshold 100 -save partition.xml
check_unr -load_partition partition.xml
check_unr -run_partition -max_jobs 8

# Clear
check_unr -clear
```

---

## Section 30: fsm_checks — FSM Verification

### 30A. fsm_checks — State Machine Analysis

```tcl
# List auto-detected FSMs
fsm_checks

# Generate transition reachability covers
fsm_checks -trans

# Generate state reachability covers
fsm_checks -states

# Generate dead-end state covers
fsm_checks -deadend

# Generate cross-state covers (pairs of FSMs)
fsm_checks -cross
fsm_checks -cross -auto -depth 2     ;# Auto-detect FSM pairs within 2 register ranks

# Add user-defined FSM
fsm_checks -add_fsm {{top.fsm_state {0 IDLE 1 ACTIVE 2 DONE}}}

# Add cross specification
fsm_checks -add_cross {{fsm1 fsm2}}

# Remove FSM
fsm_checks -remove_fsm top.fsm_state
```

**Generated task naming:**
| Command | Task format | Property format |
|---|---|---|
| `-trans` | `TRANS__<path_to_FSM>` | `<value>_to_<value>` |
| `-states` | `STATE__<path_to_FSM>` | `<value>` |
| `-deadend` | `DEADEND__<path_to_FSM>` | `<value>_deadend` |
| `-cross` | `CROSS__<FSM1>__<FSM2>` | `<value>_&&_<value>` |

---

## Section 31: check_loop — Combinational Loop Detection

### 31A. check_loop — Find and Resolve Loops

```tcl
# Check for loops from a signal
check_loop signal_name
check_loop signal_name -strict      ;# Only if signal is in loop chain itself

# Check all loops in property's COI
check_loop -property my_prop

# Global scan for all loops
check_loop -global

# With options
check_loop signal_name -classify           ;# Categorize loop type
check_loop signal_name -include_clock      ;# Include clock logic
check_loop signal_name -latch_data         ;# Include latch data paths
check_loop signal_name -silent             ;# Return as Tcl value
check_loop signal_name -limit 5            ;# Max loops to report
check_loop signal_name -show_schematic     ;# Open in schematic viewer
check_loop signal_name -suggest_disables   ;# Suggest signals to break loop
check_loop signal_name -suggest_disables -minimal_group

# Formal loop analysis (glitch, spurious edge)
check_loop -formal glitch spurious_posedge -bg
check_loop -formal -show_schematic
check_loop -formal -show_path
check_loop -formal -suggest_break

# Open loop viewer GUI
check_loop -viewer

# Get next set of loops (pagination)
check_loop signal_name -next_loops
```

---

## Section 32: capture_testcase — Save Debug Package

### 32A. capture_testcase — Archive Testcase

```tcl
# Basic capture (all sourced scripts + design files)
capture_testcase my_testcase

# Include log files
capture_testcase my_testcase -include_logs

# Include additional files
capture_testcase my_testcase -include_files {readme.txt ../scripts/}

# Overwrite existing
capture_testcase my_testcase -force

# Exclude environment variables
capture_testcase my_testcase -exclude_env
```

Creates a compressed archive (.tgz) containing all Tcl scripts, design files, property files, and reset files needed to reproduce the session.

---

## Section 33: debug_handoff — Offline Debug Database

### 33A. debug_handoff — Save and Load Debug Sessions

```tcl
# Save properties to debug database
debug_handoff -save -property {failing_assert1 failing_assert2} my_debug.dho

# Save Visualize window
debug_handoff -save -visualize_window visualize:0 my_debug.dho
debug_handoff -save -visualize_window visualize:0 -no_history my_debug.dho

# Load database (from shell: jg -debug_handoff my_debug.dho)
debug_handoff -load my_debug.dho

# Elaborate in debug mode
debug_handoff -elaborate

# Dump trace table
debug_handoff -dump_trace_table my_debug.dho -file traces.txt

# Confirm flow (verify fixes against saved traces)
debug_handoff -config database my_debug.dho
debug_handoff -config rtl_export on
debug_handoff -export_rtl ./fixed_rtl -force
debug_handoff -reload_rtl -external ./fixed_rtl
debug_handoff -confirm -property {failing_assert1} -report confirm_report.txt
```

**Shell launch:** `jg -debug_handoff my_debug.dho`

---

## Section 34: blackbox_assistant — Reduce Elaboration Complexity

### 34A. blackbox_assistant — Auto Black-Box

```tcl
# Configure with connectivity map (black-box instances not in connection paths)
blackbox_assistant -config -connectivity_map conn.csv
blackbox_assistant -config -connectivity_map conn.csv -export results.f

# Configure by depth (black-box all instances below specified depth)
blackbox_assistant -config -max_depth 2

# Clear configuration
blackbox_assistant -clear
```

After configuration, the next `elaborate` command automatically black-boxes unnecessary instances.

**Notes:**
- Use before `elaborate`
- Not compatible with LPV, CDC, COV, FSV, SUPERLINT, UNR, SEC, SPV, X-Prop, C2RTL
- Does not support designs where connection latency requires clock path preservation

---

## Section 35: Utility Commands

### 35A. auto_setup — Generate Setup Script

```tcl
# Auto-generate analyze/elaborate/clock/reset script
auto_setup -sv -path ./design/rtl -top_mod my_design
auto_setup -sv -suffix v -path ./rtl -top_file top.v -top_mod top
auto_setup -sv -save -file setup.tcl -force
```

**Note:** Generated script is a starting point — verify defines, parameters, clocks, resets.

### 35B. save / restore — Session Persistence

```tcl
# Save session
save my_session.jdb

# Restore session
restore my_session.jdb
restore my_session.jdb -include elaborated_design
```

### 35C. schematic_viewer — Open Schematic

```tcl
# Open schematic for a signal
schematic_viewer signal_name

# Open for property COI
schematic_viewer -property my_prop
```
