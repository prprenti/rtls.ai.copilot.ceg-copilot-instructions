---
name: "CDC Code Review Rules"
applyTo: "**/sgcdc/**,**/vccdc/**,**/cdc/**,**/static/cdc/**,**/vc_cdc/**"
description: "Rules for reviewing CDC (Clock Domain Crossing) quality checks. Ensures correct CDC/RDC tool configuration, waiver quality, and flow compliance."
---

# CDC Code Review Rules

Review CDC (Clock Domain Crossing) configuration files and scripts for proper setup, waiver quality, and flow compliance during code review.

**HSD Status Checking:** Automated HSD status verification (checking if HSD is open/closed in tracking system) is not currently integrated into the PR review workflow. Reviewers should verify that temp waivers contain valid 11-digit HSD references but are not required to verify HSD status.

---

## CRITICAL Rules ⚠️ ALL MUST PASS

**All critical rules represent configuration errors that can cause flow failures or loss of waiver tracking.**

---

### CRITICAL/Rule_1: Temp Waivers Must Have HSD Number

All temporary CDC waivers must contain an 11-digit HSD reference in the `-comment` field for tracking. Temp waivers without HSD are not permitted (methodology and subip waiver files excluded from this check).

```tcl
# ❌ Bad: Missing HSD reference
waive_violation -status {Waived_Temp}  -add {HIER_ABSTRACT_MISMATCH} \
    -comment {Created by user on 11-Jan-2026. Need to investigate this issue.} \
    -filter {(BlockInstanceName == "top_module/subsystem")} \
    -app {cdc} -tag {HIER_ABSTRACT_MISMATCH}

# ❌ Bad: Wrong HSD format (only 9 digits)
-comment {HSD#150189286 - investigating sync reset}

# ✅ Good: Correct 11-digit HSD with descriptive comment
waive_violation -status {Waived_Temp}  -add {HIER_ABSTRACT_MISMATCH_INVALID_SUBIP_SYNC_RESET_MISMATCH} \
    -comment {Created by designer on 11-Jan-2026. sync reset attribute propagated to SAM \
              should not be reported due to tool bug. SubIP might not use the reset synchronously/at all. \
              CASE#12345678 STAR#1234567 HSD#12345678901} \
    -filter {(BlockInstanceName == "top_module/subsystem/wrapper/subip_block") AND \
             (BlockName == "subip_block") AND (MisMatchType == "Reset")} \
    -app {cdc} -tag {HIER_ABSTRACT_MISMATCH} -user {designer} -timestamp {11-01-2026 20:58:54}

# ✅ Good: HSD URL reference is also acceptable
waive_violation -status {Waived_Temp} -add {CDC_ASYNC_RST_FLOP} \
    -comment {Investigating reset synchronization issue. https://hsdes.intel.com/appstore/article/#/22019127863} \
    -filter {(Signal == "rst_n")} -app {cdc}
```

**Required Format:** 11-digit HSD reference in `-comment` field (e.g., `HSD#12345678901`, `HSD:12345678901`, `HSD 12345678901`, `HSD12345678901`, or full URL `https://hsdes.intel.com/appstore/article/#/12345678901`)

**Detection:** Search all CDC waiver files for `Waived_Temp` entries. For each match, examine the surrounding `-comment` field and flag any waiver where the comment block does not contain `HSD[#: ]?[0-9]{11}` or an `hsdes.intel.com` URL. Exclude methodology and subip waiver files.

```bash
# Find all temp waivers; review each -comment for a valid 11-digit HSD reference
grep -rn "Waived_Temp" static/{sgcdc,vc_cdc}/
# Pattern to require in -comment: HSD[#: ]?[0-9]{11}  or  hsdes\.intel\.com/appstore/article/#/[0-9]{11}
```

---

### CRITICAL/Rule_2: No Temp Waivers in Permanent Files

Permanent waiver files must not contain `Waived_Temp` status. All temporary waivers belong in temp waiver files only (files with `temp` in filename). Any waiver file without `temp` in the filename is considered a permanent waiver file.

```tcl
# ❌ Bad: Permanent file (design_waivers.tcl) contains temp waiver
waive_violation -status {Waived_Temp} -add {CDC_ASYNC_RST_FLOP} \
    -comment {Temporary waiver until HSD#12345678901 is resolved} \
    -filter {(Signal == "rst_n")} -app {cdc}

# ✅ Good: Permanent file uses Waived status (not Waived_Temp)
waive_violation -status {Waived} -add {CDC_GLITCH_CTRL_CLKREQ_HANDSHAKE} \
    -comment {Approved permanent waiver. 16 cycle hysteresis counter ensures FSM does not respond to quick changes in clkreq/ack signal.} \
    -filter {(GlitchDestInfo:DestObject == "subip/metaflopped_signal") AND (GlitchSourceCount == "5")} \
    -app {cdc} -user {designer} -timestamp {05-01-2026 14:23:10}
```

**Detection:** Search permanent waiver files (any waiver file WITHOUT `temp` in filename, e.g., `*waivers.tcl`, `*perm_waivers.tcl`; paths vary by project and tool: `static/{sgcdc,vc_cdc}/**/`) for `Waived_Temp`. Permanent files must have NO `Waived_Temp` status — any match is a violation.

```bash
# Find permanent waiver files containing Waived_Temp — each result is a violation
find static/ \( -name "*.tcl" -o -name "*.awl" -o -name "*.swl" \) \
  ! -name "*temp*" | xargs grep -ln "Waived_Temp"
```

---

### CRITICAL/Rule_3: No Perm Waivers in Temporary Files

Temporary waiver files (with `temp` in filename) must contain ONLY temporary waivers with `Waived_Temp` status.

```tcl
# ❌ Bad: Temp file (design_temp_waivers.tcl) contains permanent waiver (Waived status)
waive_violation -status {Waived} -add {CDC_ASYNC_RST_FLOP} \
    -comment {This looks permanent but in temp file} \
    -filter {(Signal == "clk")} -app {cdc}

# ❌ Bad: Temp file (design_temp_waivers.tcl) contains permanent waiver (status not explicitly specified)
waive_violation -add {CDC_ASYNC_RST_FLOP} \
    -comment {This looks permanent but in temp file} \
    -filter {(Signal == "clk")} -app {cdc}

# ❌ Bad: Missing Waived_Temp status in temp file
waive_violation -add {HIER_ABSTRACT_MISMATCH} \
    -comment {HSD#12345678901 - sync reset issue} \
    -filter {(BlockInstanceName == "top_module/subsystem")} -app {cdc}

# ✅ Good: Temp file with proper Waived_Temp status
waive_violation -status {Waived_Temp} -add {HIER_ABSTRACT_MISMATCH} \
    -comment {HSD#12345678901 - Investigating sync reset attribute propagation} \
    -filter {(BlockInstanceName == "top_module/subsystem")} -app {cdc}
```

**Disambiguation when `-status` is missing:** A waiver in a temp file with no `-status` field has two possible root causes that require different fixes — determine which applies before resolving:

1. **Accidentally dropped status** — The waiver is genuinely temporary (describes a known in-progress issue) but the `-status {Waived_Temp}` field was omitted. **Fix:** add `-status {Waived_Temp}`.

2. **Permanent waiver misplaced in wrong file** — The waiver is genuinely permanent (comment describes a design decision). **Fix:** move the waiver to the corresponding permanent waiver file and ensure it carries `-status {Waived}` (or no status, which defaults to permanent).

**Detection:** Search temporary waiver files (any waiver file WITH `temp` in filename, e.g., `*temp_waivers.tcl`, `*temp*.awl`; paths vary by project and tool: `static/{sgcdc,vc_cdc}/**/`) for `waive_violation` entries missing `-status {Waived_Temp}`, or entries with `-status {Waived}` (permanent status in a temp file). Temporary files must have ALL waivers with `-status {Waived_Temp}` explicitly set — any `waive_violation` block lacking it is a violation.

```bash
# Find temp waiver files, then look for waive_violation without Waived_Temp or with Waived
find static/ \( -name "*temp*.tcl" -o -name "*temp*.awl" \) | \
  xargs grep -n "waive_violation\|-status {Waived}"
# Flag any waive_violation block that lacks -status {Waived_Temp}
```

---

### CRITICAL/Rule_4: FIXMEs Must Have HSD Number

All FIXME comments in CDC configuration files must have an associated 11-digit HSD reference for tracking. The HSD must appear in the same comment line as the FIXME or in a successive comment line. BOILERPLATE strings are not permitted.

```tcl
# ❌ Bad: FIXME without HSD reference
# FIXME: Update these constraints after design review
lappend constraint_files "\$::env(WORKAREA)/static/vc_cdc/inputs/tests/*/design_constraints.tcl"

# ❌ Bad: FIXME with HSD not in comment
# FIXME: Need to verify reset timing
lappend constraint_files "\$::env(WORKAREA)/static/vc_cdc/inputs/tests/*/design_constraints.tcl"
# HSD is in code somewhere else, not in comment

# ❌ Bad: BOILERPLATE placeholder text
waive_violation -status {Waived_Temp} -add {CDC_ASYNC_RST_FLOP} \
    -comment {BOILERPLATE: Add justification here. HSD#12345678901} \
    -filter {(Signal == "rst")} -app {cdc}

# ✅ Good: FIXME with HSD on same line
# FIXME: Update these constraints after design review - HSD#12345678901
lappend constraint_files "\$::env(WORKAREA)/static/vc_cdc/inputs/tests/*/design_constraints.tcl"

# ✅ Good: FIXME with HSD on successive comment line
# FIXME: Need to verify reset timing
# HSD#12345678901 - Waiting for design clarification
lappend constraint_files "\$::env(WORKAREA)/static/vc_cdc/inputs/tests/*/design_constraints.tcl"

# ✅ Good: FIXME with HSD URL
# FIXME: Update constraints - https://hsdes.intel.com/appstore/article/#/22019127863
lappend constraint_files "\$::env(WORKAREA)/static/vc_cdc/inputs/tests/*/design_constraints.tcl"
```

**Required Format:** 11-digit HSD reference in same comment line or successive comment line (e.g., `HSD#12345678901`, `HSD:12345678901`, `HSD 12345678901`, `HSD12345678901`, or full URL `https://hsdes.intel.com/appstore/article/#/12345678901`)

**Detection:** Search all CDC input files (`static/sgcdc/**`, `static/vc_cdc/**`, or project-specific collateral directories) for `FIXME` and `BOILERPLATE` strings. For each `FIXME` found, verify that the same line or the immediately following comment line contains a valid 11-digit HSD reference. Flag any `BOILERPLATE` string unconditionally.

```bash
# Find all FIXME and BOILERPLATE occurrences in CDC input dirs
grep -rn "FIXME\|BOILERPLATE" static/{sgcdc,vc_cdc}/
# For each FIXME, verify HSD[#: ]?[0-9]{11} or hsdes.intel.com appears on the same or next line
```

---

### CRITICAL/Rule_5: No Hardcoded File Paths

All file paths in CDC configuration must be relative to `$WORKAREA` or `$::env(WORKAREA)`. Hardcoded absolute paths prevent portability and cause flow failures.

```tcl
# ❌ Bad: Hardcoded absolute path
lappend constraint_files "/nfs/site/disks/nvl_rtl_CDC_HUB_wa_01/user/project/static/vc_cdc/inputs/design_constraints.tcl"

# ❌ Bad: User home directory path
source /home/jsmith/cdc_settings.tcl

# ❌ Bad: Hardcoded scratch path
set_constr_abstract_model -module subip_block \
    -sgdc /nfs/scratch/builds/subip.sgdc \
    -instances {subip_inst}

# ✅ Good: Path relative to $WORKAREA (shell script syntax)
source $WORKAREA/static/vc_cdc/inputs/design_constraints.tcl

# ✅ Good: Path relative to $::env(WORKAREA) (TCL syntax)
lappend constraint_files "\$::env(WORKAREA)/static/vc_cdc/inputs/design_constraints.tcl"

# ✅ Good: Using environment variable for abstract path
set_constr_abstract_model -module subip_block \
    -sgdc $::env(WORKAREA)/src/codegen/subip/subip_block.sgdc \
    -instances {subip_inst}
```

**Required:** All file paths must start with `$WORKAREA` or `$::env(WORKAREA)`

**Detection:** Search all CDC configuration files for absolute paths (starting with `/`) that do not reference `$WORKAREA` or `$::env(WORKAREA)`. Any such path is a violation.

```bash
# Find hardcoded absolute paths not using WORKAREA
grep -rn '"/nfs\|"/home\|"/scratch\|= /nfs\|= /home\|source /\|sgdc /\|set_option.*"/[^$]' \
  static/{sgcdc,vc_cdc}/
# Flag any result that bypasses $WORKAREA or $::env(WORKAREA)
```

---

### CRITICAL/Rule_6: SubIP Abstracts from Official Sources Only

All subIP CDC abstracts must be loaded from approved locations: `$WORKAREA/output/`, `$WORKAREA/src/codegen/`, or `$WORKAREA/subip/`. Unauthorized paths can cause incorrect CDC analysis. This applies to both .sgdc files and SAM files.

```tcl
# ❌ Bad: Loading .sgdc from outside repository (no $::env(WORKAREA))
set_constr_abstract_model -module subip_block \
    -sgdc /nfs/site/disks/user_area/local_abstracts/subip.sgdc \
    -instances {subip_inst}

# ❌ Bad: Loading .sgdc from unapproved area within WORKAREA
set_constr_abstract_model -module interface_mux \
    -sgdc $::env(WORKAREA)/static/vc_cdc/interface.sgdc \
    -instances {interface_inst_0}

# ❌ Bad: Loading SAM from outside repository
lappend sam_blocks "sbendpoint /nfs/site/disks/user_area/local_abstracts/SAM_MODELS"

# ❌ Bad: Loading SAM from unapproved area within WORKAREA
lappend sam_blocks "sbendpoint \$::env(WORKAREA)/static/vc_cdc/sbendpoint/SAM_MODELS"

# ✅ Good: Loading .sgdc from official codegen location
set_constr_abstract_model -module interface_mux \
    -sgdc $::env(WORKAREA)/src/codegen/subip/interface_mux/interface_mux_inst_0.sgdc \
    -instances {interface_inst_0}

# ✅ Good: Loading .sgdc from official output location
set_constr_abstract_model -module subip_block \
    -sgdc $::env(WORKAREA)/output/<design>/vc_cdc/subip_block/subip_block.sgdc \
    -instances {top_module/subsystem/subip_inst}

# ✅ Good: Loading SAM from official output location
lappend sam_blocks "sbendpoint \$::env(WORKAREA)/output/hbo/vc_cdc/sbendpoint/vc_cdc_run/cdc/SAM_MODELS"
```

**Approved abstract sources:** `$WORKAREA/output/`, `$WORKAREA/src/codegen/`, `$WORKAREA/subip/`

**Detection:** Find all `set_constr_abstract_model` and `lappend sam_blocks` commands. Flag any whose path does not reference `output/`, `src/codegen/`, or `subip/` under `$WORKAREA`.

```bash
# Find abstract loads from unapproved locations
grep -rn "set_constr_abstract_model\|lappend sam_blocks" static/{sgcdc,vc_cdc}/ | \
  grep -v "output/\|src/codegen/\|subip/"
```

---

### CRITICAL/Rule_7: Only VISA Modules May Load SG Abstracts in VC-CDC

In VC-CDC, Spyglass (SG) abstracts (`.sgdc` files) may only be loaded for VISA modules. All other modules must use SAM abstracts. Only modules matching `*visa_repeater*` or `*visa_*_mux*` patterns are permitted to load `.sgdc` files.

```tcl
# ❌ Bad: Loading .sgdc for non-VISA module
lappend pre_elab_opts "set_constr_abstract_model -module subip_block \
    -sgdc \$::env(WORKAREA)/output/design/vc_cdc/subip_block/subip_block.sgdc \
    -instances {\"top/subip_inst\"}"

# ❌ Bad: Loading .sgdc for interface module (not VISA)
lappend pre_elab_opts "set_constr_abstract_model -module interface_mux \
    -sgdc \$::env(WORKAREA)/src/codegen/interface_mux.sgdc \
    -instances {\"top/interface_inst\"}"

# ✅ Good: Loading .sgdc for VISA mux module
lappend pre_elab_opts "set_constr_abstract_model -module visa_unit_mux_4_s \
    -sgdc \$::env(WORKAREA)/dfx/visa/output/visa_rtl/visa_run/c2c_lib.sgdc/visa_unit_mux_4_s_c2c_1cio_0c.c2c_visa_ulml0_0.sgdc \
    -instances {\"c2c_visa_ulml0_0\"}"

# ✅ Good: Loading .sgdc for VISA repeater module
lappend pre_elab_opts "set_constr_abstract_model -module visa_repeater_2x \
    -sgdc \$::env(WORKAREA)/dfx/visa/output/visa_rtl/visa_run/visa_repeater_2x.sgdc \
    -instances {\"top/visa_rep_inst\"}"

# ✅ Good: Non-VISA module using SAM (not .sgdc)
lappend sam_blocks "subip_block \$::env(WORKAREA)/output/design/vc_cdc/subip_block/vc_cdc_run/cdc/SAM_MODELS"
```

**Allowed module patterns for .sgdc loading:** `*visa_repeater*`, `*visa_*_mux*`

**Detection:** In VC-CDC files only, find all `.sgdc` load commands and check that the associated `-module` argument matches `visa_repeater` or `visa_*_mux`. Any `.sgdc` loaded for a non-VISA module is a violation.

```bash
# Find .sgdc loading in VC-CDC; flag any module not matching VISA patterns
grep -rn "\.sgdc" static/vc_cdc/ | grep -v "visa_repeater\|visa_.*_mux"
```

---

### CRITICAL/Rule_8: Config Must Have Required CDC Flags

Configuration must enable required flags for proper CDC analysis. These are typically set in flow.cfg or other .cfg files.

**Required Flags:**
- `COPY_CODEGEN_FILES = true` — Store abstracts in src/codegen for reuse
- `CDC_STD_BMOD` — Use structural standard cell models for accurate CDC analysis
- `MODEL_SIZE_REDUCTION` — Points to cleanup config file
- `LOCAL_COMPILE = false` — Must be explicitly set to false (ensures standard flow is used)

**Flags with Correct Defaults (optional to set):**
- `USE_JSON = SYN` — Defaults to SYN (synthesis view for correct metaflop identification)
- `READ_HIP_RTL = true` — Defaults to true (analyze HIP RTL internal structure)
- `CDC_LINT_ENABLE = true` — Defaults to true for SGCDC (run CDC Lint tool for flow verification)
- `CDCQA_ENABLE = true` — Defaults to true for VC-CDC (enable CDC quality assurance checks)

```makefile
# ❌ Bad: Missing required flags in flow.cfg

# ❌ Bad: LOCAL_COMPILE not set to false
LOCAL_COMPILE = true  # Must be false to use standard flow

# ❌ Bad: COPY_CODEGEN_FILES set to false
COPY_CODEGEN_FILES = false  # Must be true to store abstracts for reuse

# ❌ Bad: USE_JSON set to RTL instead of SYN
USE_JSON = RTL  # Should use SYN for synthesis view

# ❌ Bad: CDC_STD_BMOD set to empty
CDC_STD_BMOD =  # Must specify path to standard cell models

# ✅ Good: Required flags present (typically in flow.cfg or similar .cfg file)
COPY_CODEGEN_FILES = true       # Store abstracts in src/codegen for reuse
CDC_STD_BMOD = $WORKAREA/baseline_tools/ctech/std_cells_i5.f             # Use structural standard cell models for accurate CDC analysis
MODEL_SIZE_REDUCTION = $WORKAREA/baseline_tools/sgcdc/model_size_reduction.ini  # Points to cleanup config file
LOCAL_COMPILE = false           # Must be set to false to use standard flow
# USE_JSON, READ_HIP_RTL, CDC_LINT_ENABLE, and CDCQA_ENABLE have correct defaults and don't need to be set
```

**Detection:** Check `flow.cfg` and other `.cfg` files for required flags. Flag missing flags, flags set to incorrect values (`LOCAL_COMPILE = true`, `COPY_CODEGEN_FILES = false`, `USE_JSON = RTL`), or `CDC_STD_BMOD`/`MODEL_SIZE_REDUCTION` set to empty.

```bash
# Check presence and values of required flags in cfg files
grep -n "COPY_CODEGEN_FILES\|CDC_STD_BMOD\|MODEL_SIZE_REDUCTION\|LOCAL_COMPILE\|USE_JSON" flow.cfg
# Verify: COPY_CODEGEN_FILES = true, LOCAL_COMPILE = false, CDC_STD_BMOD non-empty, MODEL_SIZE_REDUCTION set
# Flag: USE_JSON = RTL, LOCAL_COMPILE = true, COPY_CODEGEN_FILES = false, or any required flag absent
```

---

### CRITICAL/Rule_9: No Blackboxes in CDC Run

Blackboxing modules in a CDC run hides internal clock domain crossings and produces an incomplete analysis. No blackbox directives are permitted in any CDC input files under `static/sgcdc/**` or `static/vc_cdc/**`.

**VC-CDC blackbox syntax (all forms are forbidden):**

```tcl
# ❌ Bad: VC-CDC set_blackbox command
set_blackbox -design subip_block

# ❌ Bad: lappend bbox_modules
lappend bbox_modules "subip_block"

# ❌ Bad: lappend bbox_modules_files
lappend bbox_modules_files "bbox.txt"

# ❌ Bad: lappend bbox_instances_files
lappend bbox_instances_files "bboxInstances.txt"

# ❌ Bad: lappend bbox_instances
lappend bbox_instances "top_module/subip_inst"
```

**SGCDC blackbox syntax (all forms are forbidden):**

```tcl
# ❌ Bad: set_option stop with single module
set_option stop "subip_block"

# ❌ Bad: set_option stop with multiple modules
set_option stop {subip_block_a subip_block_b}
```

**Search locations:** `static/sgcdc/**` and `static/vc_cdc/**` (all files, recursively)

**Approved alternative:** Use SAM abstracts (`lappend sam_blocks`) or `.sgdc` abstracts (`set_constr_abstract_model`) to represent subIP blocks without blackboxing them.

**Detection:** Search recursively for blackbox directives in all CDC input directories. Any match is a violation.

```bash
# VC-CDC: detect any blackbox directive
grep -rn "set_blackbox\|lappend bbox_modules\|lappend bbox_instances\|lappend bbox_modules_files\|lappend bbox_instances_files" \
  static/vc_cdc/
# SGCDC: detect set_option stop (blackbox equivalent)
grep -rn "set_option stop" static/sgcdc/
```

---

## Configuration Rules

---

### CONFIG/Rule_1: Enable Required Activities (If Using YAML Config)

**Note:** YAML configuration flow is optional. If using YAML config files, they must specify correct activities for RDC and CDC checks.

```yaml
# ❌ Bad: Missing activities section - CDC/RDC won't run
global_env:
  DUT: mydesign

settings:
   ENABLE_AUTO_CONSUMPTION: true

# Missing activities: section means no CDC or RDC checks will execute

# ✅ Good: Complete activities for VC_CDC (cdc activity includes RDC by default)
global_env:
  DUT: mydesign

activities:
    cdc: cdc

# ✅ Good: Complete activities for SGCDC (RDC runs in rdc_verify_struct, CDC in cdc_verify_struct)
global_env:
  DUT: mydesign

activities:
    cdc_verify_struct: cdc_verify_struct
    rdc_verify_struct: cdc_verify_struct rdc_verify_struct
    cdc_verify_funct: cdc_verify_struct cdc_verify_funct
```

**Applies to:** Projects using YAML-based CDC configuration flow only.

**Detection:** Find all YAML configuration files in the CDC directory tree and check for the presence of an `activities:` section. Files missing this section will silently skip CDC and RDC execution.

```bash
# Find YAML config files missing an activities: section
find . -name "*.yaml" | xargs grep -L "^activities:"
# Review each result — missing activities: means no CDC/RDC checks will run
```

---

## Waiver Hygiene Rules

---

### WAIVER/Rule_1: No Auto-Generated Waiver Comments

Waiver comments must be manually written with meaningful justification. Auto-generated templates indicate insufficient review.

```tcl
# ❌ Bad: Auto-generated pattern without technical justification (tool default)
waive_violation -status {Waived_Temp} -add {CDC_ASYNC_RST_FLOP} \
    -comment {Created by jsmith on 10-Mar-2026} \
    -filter {(Signal == "rst")} -app {cdc}

# ❌ Bad: Auto-generated "Waived by" pattern without technical justification
-comment {Waived by jsmith on 10-Mar-2026.}

# ❌ Bad: Generic template without technical detail
-comment {This is a known issue. HSD#12345678901}
-comment {Reviewed by team, looks fine.}

# ✅ Good: Descriptive manual comment with technical justification
waive_violation -status {Waived} -add {CDC_GLITCH_CTRL_CLKREQ_HANDSHAKE} \
    -comment {Approved permanent waiver. 16 cycle hysteresis counter ensures FSM does not respond to quick changes in clkreq/ack signal.} \
    -filter {(GlitchDestInfo:DestObject == "subip/metaflopped_signal") AND (GlitchSourceCount == "5")} \
    -app {cdc} -user {designer} -timestamp {05-01-2026 14:23:10}
```

**Required:** Technical justification explaining why violation is safe, not just "created by" statement.

**Detection:** Search waiver files for auto-generated comment patterns (`Created by`, `Waived by`). Also flag comments that consist solely of authorship/date information with no technical content.

```bash
# Find likely auto-generated comments in waiver files
grep -rn "Created by\|Waived by" static/{sgcdc,vc_cdc}/ | grep -i "comment"
# Manually review flagged comments — reject any lacking technical justification
```

---

### WAIVER/Rule_2: Waivers Must Have Specific Filters
**Best Practice**

Waivers should use specific filters targeting exact instances/signals rather than broad wildcards that could accidentally waive unintended violations.

```tcl
# ⚠️ Acceptable but risky: Broad wildcard filter
waive_violation -status {Waived} -add {CDC_ASYNC_RST_FLOP} \
    -comment {All reset flops in subsystem use async reset by design} \
    -filter {(BlockInstanceName =~ "top_module/subsystem/*")} -app {cdc}

# ✅ Better: Specific instance targeting
waive_violation -status {Waived} -add {CDC_ASYNC_RST_FLOP} \
    -comment {Reset flop uses async reset as specified in design doc section 3.2} \
    -filter {(BlockInstanceName == "top_module/subsystem/reset_controller/rst_flop") AND (Signal == "rst_n")} -app {cdc}
```

**Guideline:** Use specific filters when possible; document scope clearly in comments if wildcards are necessary.

**Detection:** Find waivers using the `=~` wildcard operator in filter expressions. Review each match to assess whether the wildcard scope is justified and documented in the comment.

```bash
# Find waiver filters using wildcard matching
grep -rn "=~" static/{sgcdc,vc_cdc}/ | grep -i "filter\|waive_violation"
# Review each match — broad patterns require explicit justification in the -comment field
```

---

## TCL Script Cleanliness Rules

---

### TCL/Rule_1: run.tcl Whitelisted Commands Only

CDC run.tcl files must contain only approved commands. No unauthorized tool options or debugging commands.

```tcl
# ❌ Bad: Unauthorized commands or options
set_option debug_mode verbose
set_option skip_checks true
exec /nfs/user/tools/custom_script.sh  # External script
puts "DEBUG: User debugging output"

# ❌ Bad: Unapproved config settings
set disable_rdc_from_cdc 1  # Not an approved config setting

# ❌ Bad: Hardcoded user-specific paths
source /home/jsmith/my_custom_settings.tcl

# ✅ Good: Standard whitelisted commands with environment variables
set enable_cam 1
lappend constraint_files "\$::env(WORKAREA)/static/vc_cdc/inputs/tests/design_cdc_test/design_constraints.tcl"
lappend waiver_files "\$::env(WORKAREA)/static/vc_cdc/inputs/tests/design_cdc_test/design_perm_waivers.tcl"
lappend waiver_files "\$::env(WORKAREA)/static/vc_cdc/inputs/tests/design_cdc_test/design_temp_waivers.tcl"

lappend pre_elab_opts "set_constr_abstract_model -module interface_mux \
    -sgdc $::env(WORKAREA)/src/codegen/subip/interface_mux/interface_mux_inst_0.sgdc \
    -instances {interface_inst_0}"

lappend sam_blocks "child_ip           \$::env(WORKAREA)/subip/sip/child_ip/src/codegen/child_ip/vc_cdc/child_ip/vc_cdc_run/cdc/abstract/SAM_MODELS -scenario \"mode_1\" "

# Allowed options: set_option param <value>, set <var> <value>, set_option generate_zip_log yes
set_option generate_zip_log yes
```

**Whitelist:** `source`, `lappend`, `set_constr_abstract_model`, `set_option param`, `set`, `set_option generate_zip_log`

**Detection:** Search `run.tcl` and `run_settings.tcl` files for commands outside the approved whitelist. Flag `exec`, `puts`, `package`, hardcoded `source /` paths, or any `set_option` variant not in the whitelist.

```bash
# Detect unauthorized commands in run scripts
grep -rn "^exec\|^puts\|^package" static/{sgcdc,vc_cdc}/
grep -rn "source /\|set_option debug\|set_option skip\|set_option stop" static/{sgcdc,vc_cdc}/ | \
  grep -i "run\.tcl\|run_settings\.tcl"
```

---

### TCL/Rule_2: compile Required Defines Only

SGCDC analyze.tcl and VC-CDC flow.cfg must set required defines and no others (except approved exceptions).

```tcl
# ❌ Bad: Missing required defines
# (No INTEL_SVA_OFF, No INTEL_NO_PWR_PINS)

# ❌ Bad: Unauthorized defines (SGCDC)
set_option define INTEL_SVA_OFF
set_option define INTEL_NO_PWR_PINS
set_option define MY_CUSTOM_DEBUG_MODE      # Not allowed
set_option define SKIP_CDC_CHECKS           # Not allowed

# ❌ Bad: Unauthorized defines (VC-CDC)
VERILOG_ANALYZE_OPTS  = -format sverilog -verbose +define+INTEL_NO_PWR_PINS+define+INTEL_SVA_OFF +define+MY_CUSTOM_DEBUG_MODE  # MY_CUSTOM_DEBUG_MODE is not allowed

# ✅ Good: Required defines only (plus approved exception) (SGCDC defines are found in analyze.tcl file)
set_option define INTEL_SVA_OFF              # Required: Disable SVA for CDC
set_option define INTEL_NO_PWR_PINS          # Required: Exclude power pins
set_option define SNPS_MEM_CDC_EMUL_WA       # Allowed exception: Synopsys memory CDC emulation workaround

# ✅ Good: Required defines only (plus approved exception) (VC-CDC defines are found in flow.cfg file)
VERILOG_ANALYZE_OPTS  = -format sverilog -verbose +define+INTEL_NO_PWR_PINS+INTEL_SVA_OFF+SNPS_MEM_CDC_EMUL_WA
```

**Required:** `INTEL_SVA_OFF`, `INTEL_NO_PWR_PINS`  
**Allowed Exception:** `SNPS_MEM_CDC_EMUL_WA`  
**All others:** Not permitted

**Detection:** For SGCDC, find all `set_option define` lines in `analyze.tcl` files and flag any define not in the approved list. For VC-CDC, inspect `VERILOG_ANALYZE_OPTS` in `flow.cfg` and flag any `+define+` token outside the approved set.

```bash
# SGCDC: flag unauthorized defines in analyze.tcl
grep -rn "set_option define" static/sgcdc/ | \
  grep -v "INTEL_SVA_OFF\|INTEL_NO_PWR_PINS\|SNPS_MEM_CDC_EMUL_WA"
# VC-CDC: inspect VERILOG_ANALYZE_OPTS defines in flow.cfg
grep -n "VERILOG_ANALYZE_OPTS" flow.cfg
# Extract each +define+ token and flag any not in: INTEL_SVA_OFF, INTEL_NO_PWR_PINS, SNPS_MEM_CDC_EMUL_WA
```

---

## Quick Reference Checklist

Use this checklist during code review to verify CDC configuration files.

### ✅ Waiver Review
- [ ] **HSD format** — All temp waivers contain 11-digit HSD reference (CRITICAL/Rule_1)
- [ ] **No temp in perm** — Permanent waiver files have no `Waived_Temp` status entries (CRITICAL/Rule_2)
- [ ] **No perm in temp** — Temp waiver files use `Waived_Temp` for all entries (CRITICAL/Rule_3)
- [ ] **Comment quality** — No auto-generated "Created by" patterns; all have technical justification (WAIVER/Rule_1)
- [ ] **Filter specificity** — Waivers use specific filters, not broad wildcards (WAIVER/Rule_2)

### ✅ Configuration Review
- [ ] **Activities defined (if using YAML)** — config.yaml has `activities:` section with cdc/rdc (CONFIG/Rule_1)
- [ ] **Config structure (if using YAML)** — YAML syntax valid, required sections present (CONFIG/Rule_1)
- [ ] **No hardcoded paths** — All paths use $WORKAREA or $::env(WORKAREA) (CRITICAL/Rule_5)
- [ ] **Official abstracts** — SubIP abstracts from approved locations only (CRITICAL/Rule_6)
- [ ] **SG abstracts VISA only** — Only VISA modules load .sgdc files in VC-CDC (CRITICAL/Rule_7)
- [ ] **Required flags** — flow.cfg has required flags set correctly (CRITICAL/Rule_8)
- [ ] **No blackboxes** — No blackbox directives in `static/sgcdc/**` or `static/vc_cdc/**` files (CRITICAL/Rule_9)

### ✅ Script Cleanliness
- [ ] **FIXMEs have HSDs** — All FIXME comments have associated HSD reference (CRITICAL/Rule_4)
- [ ] **run.tcl clean** — Only whitelisted commands (TCL/Rule_1)
- [ ] **analyze.tcl defines** — Required defines set, no unauthorized defines (TCL/Rule_2)
- [ ] **Environment variables** — Use `$::env(WORKAREA)`, not hardcoded paths (TCL/Rule_1)

---

## Review Workflow

**During PR Code Review:**
1. Check all items in the checklist above
2. Focus on: Waivers, Configuration structure, Script cleanliness
3. Verify all CRITICAL rules pass

**Files to Review:**

CDC input files (paths vary by project and tool: SGCDC/VC_CDC)

**Common file patterns:**
- `static/{sgcdc,vc_cdc}/**/*.tcl` — TCL scripts (run.tcl, analyze.tcl, constraints)
- `static/{sgcdc,vc_cdc}/**/*waivers*.{tcl,awl}` — Waiver files
- `flow.cfg` or `*.cfg` — Configuration files (always present)
- `config.yaml` or `*.yaml` — YAML configuration files (optional, only if using YAML flow)
- `src/codegen/**/*.sgdc` — Abstract models
- `*.cth`, `Makefile` — Build configuration files

**File naming conventions:**
- Files without `temp` in name — Permanent waivers (VC-CDC: `*.tcl`, SGCDC: `*.awl` or `*.swl`)
- Files with `temp` in name — Temporary waivers (VC-CDC: `*temp*.tcl`, SGCDC: `*temp*.awl`)
- Constraint files — VC-CDC: `*.tcl`, SGCDC: `*.sgcdc`
- `*_run.tcl`, `run_settings.tcl` — Run configuration scripts
- `*cdcqa*.tcl` — CDCQA tool waiver files
