# VC Lint / Open Latch Reference

## FE Readiness (Required First)

Run:

```text
fe-setup/check_terminal_ready()
```

Proceed only when readiness returns `true`.

## Build-Run Usage (Authoritative)

- Use the Build-Run plugin grdlbuild skill conventions as the primary execution path.
- Execute Gradle tasks via MCP `build-run/run_grdlbuild`.
- Execute make targets via MCP `build-run/run_make` in `static/vc_lint`.
- Any direct CLI examples below are for manual triage/reference only.

---

## Overview

The VC Lint and VC OL flows use **Synopsys VC Static (VC Lint)** for RTL lint checking and **VC OL (Open Latch)** for open-latch detection. Both flows share the same VC Static platform and a common compile step, but run with different rulesets and waiver configurations.

- **VC Lint** runs the full methodology rules (plus NVL-program and IP-local overrides) to catch RTL coding issues.
- **VC OL** runs *only* the `OpenLatch.tcl` ruleset to detect unintended transparent latches.

Both are invoked from `$WORKAREA/static/vc_lint/` — there is no separate `static/vc_ol/` directory. The OL flow uses `make ol_run` with a different TCL settings file (`ol_run_settings.tcl`).

### Determining the DUT

The `<DUT>` variable varies from repo to repo. To find the DUT(s) for any repo, look for design config files:

```bash
ls $WORKAREA/cfg/*.design.cfg
```

Each file `$WORKAREA/cfg/<DUT>.design.cfg` corresponds to a DUT name. For example, `cfg/punit.design.cfg` means `<DUT>=punit`. A repo may have multiple DUTs.

The DUT is also set in `$WORKAREA/static/vc_lint/flow.cfg` as the `DUT` variable. Example: for the punit repo, `<DUT>=punit`. All paths below use `<DUT>` as a placeholder.

> **Multiple DUTs:** A repo may define more than one DUT (multiple `*.design.cfg` files). If the user does not specify which DUT to run, ask them to choose one before proceeding.

---

## Input Structure

### `$WORKAREA/static/vc_lint/` — Top-Level Configuration

| File | Purpose |
|---|---|
| `Makefile` | IP-local Makefile. Sets `CHEETAH_RTL_ROOT` (via `cth_query`), netbatch defaults (`NBPOOL=zsc10_normal`, `NBQSLOT=/ddg/ip/fe/rtl`). Includes `baseline_tools/vc_lint/Makefile`. Defines local `lint_qc` target. |
| `flow.cfg` | Main flow configuration. Sets `DUT=<DUT>`, `TOP_MODULE_NAME=<DUT>`, `PASS=<DUT>` (example for punit repo: `punit`). Enables `USE_SAM_AUTOGEN=true`. Points to `inputs/run_settings.tcl` and `inputs/sam_autogen.tcl`. Sets VCS analyze options. |
| `tool.cth` | Tool version pinning: `VCLINT_VERSION`, `VCLINT_METHODOLOGY_VERSION`, `VCCOMMON_METHODOLOGY_VERSION`, `lint_global_repo_version`. |
| `output` | **Symlink** → `../../output/<DUT>/vc_lint`. Convenience shortcut to the output area. |

### `$WORKAREA/static/vc_lint/inputs/` — Run and Module-Specific Configuration

| File | Purpose |
|---|---|
| `run_settings.tcl` | **Main lint run settings.** Enables `create_sam`, `clean_compress`, `enable_mlrca`. Blackboxes 2 SRAM HIPs. Loads 3 layers of rulesets (baseline_tools, IP-local, global repo). Loads 7 waiver files (global → sub-IP → punit permanent → MBIST). |
| `ol_run_settings.tcl` | **Open Latch run settings.** Overrides the ruleset to *only* `OpenLatch.tcl` (`lset rulesets 0`). Adds OL-specific parameter overrides (`OLParamOv.tcl`). Loads OL-specific waivers. Also blackboxes SRAMs + `Xm_nvl_23ww43Xttop`. |
| `sam_autogen.tcl` | **SAM abstraction auto-generation.** Runs parallel netbatch jobs (8 processes, `wait_time 120`). Auto-generates SAM for 5 sub-blocks: `cpc_cri_ctrl_cfg2`, `cpc_cri_master`, `crislvunit_wrapper`, `dtf_obs`, `Xm_nvl_23ww43Xttop`. |
| `LintRulesOv.tcl` | **IP-local rule override.** Currently promotes `W287a` to Error severity. |
| `scripts/lint_waiver_analyze.py` | Analyzes waiver files — counts temp vs permanent waivers, checks for backslide against maximums, produces `waiver_info.txt` and `waiver_csv.csv` reports. Has separate handling for OL waivers (detects `ol_` prefix in filenames). |
| `scripts/lint_postrun_clean.py` | Cleans up large internal files after lint/OL runs to save disk space. Removes `.internal` dirs, `work` dir, `OpenLatch.csv`, `openlatchviolation.rpt`, etc. |

### `$WORKAREA/static/vc_lint/waivers/` — IP-Level Waiver Files

> Waiver filenames are typically prefixed with the DUT name (e.g., `punit_*` for the punit repo). The prefix will match the repo's `<DUT>`.

| File | Purpose |
|---|---|
| `punit_vclint_waivers.awl.tcl` | Main permanent lint waivers (~100+ entries). Covers rules: STARC05, FlopEConst, FlopClockConstant, W362a, W287a, W116, sim_race07, etc. Each waiver has an owner (`-user`) and comment. |
| `punit_ol_waivers.awl.tcl` | Open Latch specific waivers. Permanent waivers for MBIST/SRAM latch isolation patterns (`ctech_lib_latch_p` in memory wrappers). |
| `punit_subips.awl.tcl` | Waivers for sub-IP code issues (CDTF, Xtensa, fuse puller STAP, sbebase clock gate). |
| `punit_nvl_mbist.awl.tcl` | MBIST/BISR-specific waivers (Tessent-generated code). Rules: DefaultState, W116, W121. |

> **All waiver files must use the `.awl.tcl` extension** (per IPQC rule clnt.17_433).

---

## Configuration Layers

VC Lint uses a 3-layer rule override model, loaded in order by `run_settings.tcl`:

| Layer | File | Scope |
|---|---|---|
| 1. Baseline (NVL-program) | `$WORKAREA/baseline_tools/vc_lint/inputs/LintRulesOv.tcl` | Promotes ~20 rules to Error severity (FewSeqOnCG, AlwaysCombExhaustive-ML, DefaultState, etc.). Disables noisy rules (clock_used_as_data, FileHdr, etc.). |
| 2. IP-local | `$WORKAREA/static/vc_lint/inputs/LintRulesOv.tcl` | DUT-specific overrides (example for punit repo: promotes W287a to Error). |
| 3. Global repo | `$LINT_GLOBAL_REPO/inputs/LintRulesOv.tcl` | Centrally managed by the Lint WG. |

Rules at a later layer override earlier layers.

---

## Key Configuration File Details

### `flow.cfg`

Key points:
- `COMPILE_OPTS_FILE` must reference `baseline_tools` (per IPQC rule clnt.17_441).
- `VCS_ELAB_OPTS` must NOT be set in `flow.cfg`.
- The compile defines (from `analyze.f`) include: `FL_SYNTHESIS_ON`, `INTEL_SVA_OFF`, `SVA_OFF`, `ASSERT_OFF`, `INTEL_NO_PWR_PINS`.

### `run_settings.tcl` — Lint Run

Required settings (per IPQC rule clnt.17_445):
- `set create_sam 1` — Generate SAM abstracts for downstream integration
- `set write_sam_opts "-stop_copy_kdb"` — Avoid copying KDB files
- `set clean_compress 1` — Compress/zip files after running
- `set enable_mlrca 1` — Multi-Level Root Cause Analysis

Blackboxed modules (repo-specific — check your `run_settings.tcl`):
```tcl
lappend bbox_modules "<module_name_1>"
lappend bbox_modules "<module_name_2>"
```

### `ol_run_settings.tcl` — Open Latch Run

Required settings (per IPQC rule clnt.17_445):
- `set clean_compress 1`
- `set enable_mlrca 1`

Key differences from lint:
```tcl
## Run open latch rule only — replaces the default methodology ruleset
lset rulesets 0 "$::env(VC_METHODOLOGY_LINT)/rules/OpenLatch.tcl"

## Override to old reporting style (minimizes need to tweak existing waivers)
lappend rulesets "$::env(LINT_GLOBAL_REPO)/inputs/OLParamOv.tcl"
```

Extra blackbox for OL (repo-specific — check your `ol_run_settings.tcl`):
```tcl
lappend bbox_modules "<additional_module>"
```

### `sam_autogen.tcl` — SAM Abstraction Auto-Generation

Required settings (per IPQC rule clnt.17_446):
- `set write_sam_opts "-stop_copy_kdb"`
- `set clean_compress 1`
- `post_elab_opts` must include `-wait_time 120`

Auto-generated SAM blocks (repo-specific — check your `sam_autogen.tcl`):
```tcl
lappend autogen_sam_blocks "<subip_module_1>"
lappend autogen_sam_blocks "<subip_module_2>"
## ... one entry per sub-IP to abstract
```

---

## Black-Box Specification

Sometimes Lint must ignore certain modules in its analysis — typically analog HIPs for which RTL is not provided, purposely non-synthesizable code, or modules otherwise incompatible with Lint analysis.

- Such modules are often indicated via an `ErrorAnalyzeBBox` violation in the design-read stage.
- **Verify** that any module you blackbox truly should not be analyzed (per IPQC rule clnt.17_435: no unexpected blackboxes).
- A blackbox is communicated via the `bbox_modules` option:
  - In `run_settings.tcl` — for modules to blackbox during the main lint run
  - In `ol_run_settings.tcl` — for modules to blackbox during the OL run (should include all of `run_settings.tcl` blackboxes plus any additional)
  - In `sam_autogen.tcl` — for modules inside another module being abstracted

```tcl
## Example: blackboxing analog HIPs without RTL
lappend bbox_modules "<analog_hip_module_1>"
lappend bbox_modules "<analog_hip_module_2>"
```

---

## SAM (Static Abstraction Model) Specification

Lint is run at various hierarchy levels. When running at a top level that includes sub-IPs, it is redundant to re-analyze code that was already linted at the lower level. VC supports **SAM (Static Abstraction Model)** to abstract lower-level IPs — the abstracted module's internal code is not analyzed, but its interface is still included in top-level analysis.

> **Important:** SAM refers to all abstracts. The `sam_autogen` stage refers only to SAM for sub-IP abstracts that are **auto-generated** for use in your top-level run.

### Types of SAM Usage

| Type | Description | Configuration |
|---|---|---|
| **Auto-generated** | Top level generates SAM for its sub-IPs | `sam_autogen.tcl`: `lappend autogen_sam_blocks "<module>"` |
| **Imported from sub-IP** | Sub-IP provides pre-built SAM in its drop | `run_settings.tcl`: `set use_sam 1` + `lappend sam_blocks ...` |
| **Exported to higher level** | IP generates its own SAM for a parent run | `run_settings.tcl`: `set create_sam 1`; output in `SAM_MODELS/` |

### Loading SAM from Sub-IPs

In `run_settings.tcl` (or a separate `load_sam_modules.tcl`):

```tcl
set use_sam 1

## Syntax:
lappend sam_blocks "<module_name>  <path_to_SAM_MODELS>"
```

To add abstracts for an IP, append one `sam_blocks` entry per module. For example:

```tcl
## Loading SAM for clkproxy:
lappend sam_blocks "clkproxy  $::env(WORKAREA)/subip/sip/hub_clkproxy/src/codegen/clkproxy/vc_lint/SAM_MODELS"

## Adding abstracts for another IP (e.g., punit):
lappend sam_blocks "punit  $::env(WORKAREA)/subip/sip/punit/src/codegen/punit/vc_lint/SAM_MODELS"
```

The `<path_to_SAM_MODELS>` should resolve to an existing `SAM_MODELS/` directory — typically from a sub-IP's `src/codegen/<ip>/vc_lint/SAM_MODELS` or from a release model drop.

#### Loading SAM for specific instances

When multiple instances of the same module exist with different parameters:

```tcl
## Same top name, different instances:
lappend sam_blocks "d2d_hnoc  /path/to/d2d_hnoc0/SAM_MODELS -instances {par_mfs_data0/d2d_hnoc0}"
lappend sam_blocks "d2d_hnoc  /path/to/d2d_hnoc1/SAM_MODELS -instances {par_mfs_data1/d2d_hnoc1}"

## Different top name (use -alias):
lappend sam_blocks "vtu_top_south  /path/to/vtu_top_south/SAM_MODELS/ -instances {par_ivtu/ivtu_wrap/ivtu} -alias {vtu_top}"
lappend sam_blocks "vtu_top_north  /path/to/vtu_top_north/SAM_MODELS/ -instances {par_saf_svtu/svtu_wrap/svtu} -alias {vtu_top}"
```

> **Note:** The `-alias` switch had a bug in earlier versions; it is fixed from `V-2023.12-SP2-4` onwards.

### Exporting SAM to Higher Levels

When `set create_sam 1` is enabled in `run_settings.tcl`, the generated SAM is placed in:
```
output/<DUT>/vc_lint/<DUT>/vc_lint_run/SAM_MODELS/
```

To export this SAM to a higher-level run, it must be moved from `output/` into `src/codegen/vc_lint/`. Long-term, Cheetah will handle this copy automatically; short-term, it may need to be done manually.

> SAM abstract files are **not human-readable**. They reside inside a `.internal` directory within `SAM_MODELS/`.

---

## Waiver Hierarchy

### Lint Waivers (loaded in order by `run_settings.tcl`)

1. `$LINT_GLOBAL_WAIVER/waivers/nvl_global_waivers.awl.tcl` — NVL-program global
2. `$LINT_GLOBAL_WAIVER/waivers/dfx_global_waivers.awl.tcl` — DFX global
3. `$LINT_GLOBAL_WAIVER/waivers/sbr_global_waivers.awl.tcl` — Sideband global
4. `$LINT_GLOBAL_WAIVER/waivers/sbe_global_waivers.awl.tcl` — SBE global
5. `$WORKAREA/static/vc_lint/waivers/<DUT>_subips.awl.tcl` — Sub-IP waivers (e.g., `punit_subips.awl.tcl`)
6. `$WORKAREA/static/vc_lint/waivers/<DUT>_vclint_waivers.awl.tcl` — DUT permanent waivers (e.g., `punit_vclint_waivers.awl.tcl`)
7. `$WORKAREA/static/vc_lint/waivers/<DUT>_nvl_mbist.awl.tcl` — MBIST waivers (e.g., `punit_nvl_mbist.awl.tcl`)

### OL Waivers (loaded in order by `ol_run_settings.tcl`)

1. `$LINT_GLOBAL_REPO/waivers/ol_global_waivers.awl.tcl` — Global repo OL waivers
2. `$WORKAREA/baseline_tools/vc_lint/waivers/ol_global_waivers.awl.tcl` — Baseline OL waivers
3. `$WORKAREA/static/vc_lint/waivers/<DUT>_ol_waivers.awl.tcl` — DUT OL waivers (e.g., `punit_ol_waivers.awl.tcl`)

### Waiver Methodology

Lint waivers prevent error violations from causing run failures. Key principles:

- **Only files inside `$WORKAREA` can be modified.** Files outside the workarea (e.g., from `baseline_tools`, global repos, or sub-IP drops) cannot be edited — they can only be waived (temp or perm).
- **All waivers are temporary by default.** Unless the user explicitly requests a permanent waiver, always create a temp waiver. When a user asks to add a waiver, confirm: *"Should this be a temporary waiver (default) or a permanent waiver?"*
- **Minimize waivers.** Given a choice between waiving vs. fixing code, the code should be fixed. Waivers from previous projects should be re-examined — remove them if the underlying issue can be fixed.
- **Do not copy sub-IP waivers.** Sub-IPs that have Lint run at their local level should be abstracted (use SAM) at the higher level. There should be no need to import their waivers.
- **VC-Lint waiver format differs from Spyglass Lint.** Do not blindly convert inherited SG waivers. Instead, review VC Lint violations and manually port/recode only truly needed waivers.

### Permanent vs Temporary Waivers

| Type | `-status` value | Criteria | Requirements |
|---|---|---|---|
| **Permanent** | `-status Waived`, `-status {Waived}`, or **no** `-status` switch at all | Closely reviewed, confirmed required, clearly documented | Must have thorough `-comment`, be reviewed by Lint WG (clnt.17_447) |
| **Temporary** | `-status Waived_Temp` or `-status {Waived_Temp}` | Added until it can be removed or closely reviewed | File has `temp` in its name **and** waiver has `-status Waived_Temp` |

### Waiver Syntax

```tcl
waive_violation -app Lint -add {<unique_id>} -tag {<rule_tag>} \
  -filter {(<field>=~"<pattern>") AND ...} \
  -comment {<justification>} -user {<owner_idsid>}
```

**Parameters:**
- `-app Lint` — Use for most violations. For design-read violations, use `-app design` instead.
- `-add {<unique_id>}` — **Required.** Must be unique; duplicate names cause waivers to be ignored. Suggested format: `idsid_tag_date_identifier` (e.g., `adwood_AlwaysFalseTrue_20230118_01`).
- `-tag {<rule_tag>}` — The lint rule being waived.
- `-filter {<conditions>}` — Conditions to match specific violations (paths, modules, signals, etc.).
- `-comment {<text>}` — **Required.** Well-documented explanation of why the violation must be waived and cannot be fixed.
- `-user {<idsid>}` — **Required.** Owner responsible for the waiver.
- `-status Waived_Temp` — Add this for all temporary waivers. Omit `-status` (or use `-status Waived`) for permanent waivers.

**Additional rules:**
- OL waiver filenames use the `ol_` prefix to trigger separate counting in `lint_waiver_analyze.py`.
- All permanent waivers must be submitted for review by the Lint WG (per IPQC rule clnt.17_447).
- All waiver files must use the `.awl.tcl` extension (per IPQC rule clnt.17_433).

---

## Output Structure

All outputs go to `$WORKAREA/output/<DUT>/vc_lint/`. The symlink `static/vc_lint/output` points here for convenience.

```
$WORKAREA/output/<DUT>/vc_lint/
├── flow_inputs/                              # Config logs (config.log, env.dump, per-stage config logs)
├── flow_outputs/                             # indicators.json
│
├── vc_lint_compile/                          # Compile pass output
│   ├── analyze/                              # VCS analyze output
│   ├── work/                                 # VCS work library
│   ├── vc_lint_compile.PASS                  # Sentinel: compile passed
│   ├── vc_lint_compile.summary.rpt           # Compile summary report
│   └── vc_lint.combinelog                    # Combined compile log
│
├── vc_lint_sam_autogen/                      # SAM auto-generation output
│   ├── vcjobs/                               # Per-IP generated abstract logs
│   │   └── {ip}_{params}_paramdir/*          #   ({ip} = autogen_sam_blocks entries)
│   ├── SAM_MODELS/                           # Per-IP actual abstract files
│   │   └── {ip}_{params}/.internal/*         #   (NOT human-readable)
│   ├── SAM_paramtcls/                        # Per-IP parameter TCL files
│   ├── nblog/                                # Netbatch job logs
│   ├── sam_logdir/                           # SAM generation logs
│   ├── vcst_session.log                      # SAM autogen session log
│   ├── vc_lint_sam_autogen.PASS              # Sentinel: SAM autogen passed
│   └── vc_lint_sam_autogen.summary.rpt       # SAM autogen summary report
│
├── <DUT>/                                    # Main lint run (DUT = punit)
│   └── vc_lint_run/
│       ├── reports/                          # VC-Lint run reports
│       ├── vcst_rtdb/                        # Run-time database
│       │   └── reports/
│       │       └── waiver.rpt.gz             # Waiver report (compressed)
│       ├── SAM_MODELS/                       # SAM models from this run
│       ├── gui/                              # GUI session data
│       ├── vcst_session.log                  # Main lint session log (PASS/FAIL)
│       ├── vc_lint_run.PASS                  # Sentinel: lint run passed
│       ├── vc_lint_run.summary.rpt           # Lint run summary report
│       └── vc_lint.combinelog                # Combined lint run log
│
└── vc_ol_run/                                # Open Latch run
    └── vc_lint_run/
        ├── reports/                          # OL run reports
        │   ├── blackbox.rpt                  # Blackbox report
        │   ├── OpenLatch.csv                 # OL violations CSV (removed by postrun_clean)
        │   └── openlatchviolation.rpt        # OL violation report (removed by postrun_clean)
        ├── vcst_rtdb/                        # Run-time database
        │   └── reports/
        │       └── waiver.rpt.gz             # OL waiver report (compressed)
        ├── gui/                              # GUI session data
        ├── vcst_session.log                  # OL session log (PASS/FAIL)
        ├── vc_lint_run.PASS                  # Sentinel: OL run passed
        ├── vc_lint_run.summary.rpt           # OL run summary report
        └── vc_lint.combinelog                # Combined OL run log
```

> **Note:** `vc_ol_run/vc_lint_run/` does NOT contain `SAM_MODELS/` — SAM generation is disabled for OL.

---

## VC Lint vs VC OL Comparison

| Aspect | VC Lint | VC OL (Open Latch) |
|---|---|---|
| **Ruleset** | Full methodology rules + 3-layer overrides | Only `OpenLatch.tcl` + `OLParamOv.tcl` |
| **Make target** | `make run` | `make ol_run` (`PASS=vc_ol_run`) |
| **SAM autogen** | Yes (prerequisite step) | No (`USE_SAM_AUTOGEN=false`) |
| **`COPY_CODEGEN_FILES`** | Default (true) | Disabled (`false`) |
| **Output directory** | `output/<DUT>/vc_lint/<DUT>/vc_lint_run/` | `output/<DUT>/vc_lint/vc_ol_run/vc_lint_run/` |
| **Waivers** | 7 files (global → sub-IP → punit → MBIST) | 3 files (global repo OL → baseline OL → punit OL) |
| **Blackboxes** | 2 SRAM HIPs | 2 SRAM HIPs + `Xm_nvl_23ww43Xttop` |
| **NB resources** | MEM28G_4C (heavy) | MEM8G_2C (lighter) |
| **Key reports** | `vcst_session.log`, `waiver.rpt.gz`, `blackbox.rpt` | Same + `OpenLatch.csv`, `openlatchviolation.rpt` (cleaned post-run) |
| **IPQC check** | clnt.17_429 | clnt.17_430 |

---

## Invocation

### Make Targets (from `$WORKAREA/static/vc_lint/`)

```bash
cd $WORKAREA/static/vc_lint

make compile                  # Compile RTL for lint (shared by lint and OL)
make sam_autogen              # Generate SAM abstracts (lint only, requires compile)
make run                      # Run full lint (requires sam_autogen)
make ol_run                   # Run Open Latch (requires compile, no sam_autogen)
make gui                      # Open lint results in VC Static GUI
make ol_gui                   # Open OL results in VC Static GUI
make lint_qc                  # Run waiver analysis (lint_waiver_analyze.py)
make lint_postrun_clean       # Clean up large files to save disk space
```

The `ol_run` target is defined in `baseline_tools/vc_lint/Makefile` as:
```makefile
ol_run:
	make run PASS=vc_ol_run RUN_SETTINGS_FILE=inputs/ol_run_settings.tcl USE_SAM_AUTOGEN=false COPY_CODEGEN_FILES=false
```

### Gradle/GK Pipeline

Task definitions are in `$WORKAREA/flows/grdlbuild/static/vc_lint/build.gradle.kts`.

To list all stages and their dependencies for vc_lint:
```bash
grdlbuild vc_lint -st                    # List all vc_lint stages
grdlbuild vc_lint -dut <DUT> -st         # List stages for a specific DUT
grdlbuild vc_lint -std                   # List stages with dependencies
```

| Task | Command | Depends On | NB Resource |
|---|---|---|---|
| `vclint_compile` | `make compile MODEL_SIZE_REDUCTION=''` | `:filelists_rtl` | — |
| `vclint_autogen` | `make sam_autogen COPY_CODEGEN_FILES=false MODEL_SIZE_REDUCTION=''` | `vclint_compile` | MEM8G_2C |
| `vclint_ol_run` | `make ol_run MODEL_SIZE_REDUCTION=''` | `vclint_compile` | MEM8G_2C |
| `vclint_run` | `make run` | `vclint_autogen` | MEM28G_4C |
| `vc_lint_qc` | `make lint_qc DUT=<DUT>` | `vclint_run`, `vclint_ol_run` | — |
| `vc_lint_postrun_clean` | `make lint_postrun_clean DUT=<DUT>` | `vclint_run`, `vclint_ol_run` | — |

All main tasks run in modes: `local`, `turnin`, `release`, `mock`, `filter`, `drop`.

> **Note:** `MODEL_SIZE_REDUCTION=''` is explicitly cleared in compile, autogen, and ol_run. Model size reduction must only occur as part of `lint_postrun_clean` (per IPQC rule clnt.17_434).

#### Running via grdlbuild

```bash
# Run all vc_lint stages (resolves full dependency chain automatically):
grdlbuild vc_lint -local

# Run individual stages locally:
grdlbuild vclint_compile -local          # Step 1: Compile RTL
grdlbuild vclint_autogen -local          # Step 2: SAM autogen (depends on compile)
grdlbuild vclint_run -local              # Step 3: Full lint run (depends on autogen)
grdlbuild vclint_ol_run -local           # Step 2b: Open Latch run (depends on compile)

# Post-run stages (depend on both vclint_run and vclint_ol_run):
grdlbuild vc_lint_qc -local              # Waiver analysis
grdlbuild vc_lint_postrun_clean -local   # Disk cleanup

# Run a single stage WITHOUT its dependencies:
grdlbuild vclint_run -id -local

# Run on Netbatch instead of local (only if needed):
grdlbuild vclint_run -nb
```

#### Key Differences: Make vs grdlbuild

| Aspect | Make flow | grdlbuild flow |
|---|---|---|
| Invocation | `cd $WORKAREA/static/vc_lint && make <target>` | `grdlbuild <task> -local` from anywhere |
| Dependencies | Manual (you must run steps in order) | Automatic (grdlbuild resolves the full chain) |
| `MODEL_SIZE_REDUCTION` | You must pass `MODEL_SIZE_REDUCTION=''` manually | Already configured in `build.gradle.kts` |
| Filelists | Must be generated beforehand | `:filelists_rtl` dependency handled automatically |
| NB resources | Manual `NBPOOL`/`NBQSLOT` | Configured per-task via `useNBResource()` in `build.gradle.kts`; resource definitions in `flows/grdlbuild/resources.ini` |

---

## Tool Versions

Defined in `$WORKAREA/static/vc_lint/tool.cth`:

| Variable | Value |
|---|---|
| `VCLINT_VERSION` | `V-2023.12-SP2-5-B4-2` |
| `VCLINT_METHODOLOGY_VERSION` | `2.02.20.25ww16` |
| `VCCOMMON_METHODOLOGY_VERSION` | `2.04.08.25ww11` |
| `lint_global_repo_version` | `latest` |

Versions must match or exceed the project-required spec at `/p/hdk/rtl/proj_tools/tools_ver/<project>/latest/<stepping-milestone>.dat` (per IPQC rule clnt.17_431).

### Checking Current Tool Versions

Query the currently configured versions using `cth_query`:

```bash
cth_query -tool vc_lint toolversion VCLINT_VERSION
cth_query -tool vc_lint toolversion VCLINT_METHODOLOGY_VERSION
cth_query -tool vc_lint toolversion VCCOMMON_METHODOLOGY_VERSION
```

### Updating Tool Versions

If the required versions (e.g., from a version update request) do not match the values returned by `cth_query`, update `$WORKAREA/static/vc_lint/tool.cth`.

The file uses INI-style format under the `[toolversion]` section:

```ini
[toolversion]
VCLINT_VERSION               = V-2023.12-SP2-10-B4-2
VCLINT_METHODOLOGY_VERSION   = 2.03.04.26ww02
VCCOMMON_METHODOLOGY_VERSION = 2.06.02.26ww06
lint_global_repo_version     = latest
```

**Steps:**
1. Run the `cth_query` commands above to check the current versions.
2. Compare against the required versions.
3. If they differ, edit `$WORKAREA/static/vc_lint/tool.cth` and update the corresponding values.
4. Re-run `cth_query` to confirm the change took effect.

> **Note:** `lint_global_repo_version` is typically left as `latest` unless a specific version is required.

---

## Environment Requirements

| Variable | Description | How Set |
|---|---|---|
| `WORKAREA` | Root of cloned repo | `export WORKAREA=/path/to/repo` |
| `CTH_SETUP_CMD` | CTH environment flag | Set by the @fe-setup agent |
| `CHEETAH_RTL_ROOT` | Root of Cheetah-RTL CAD tools | Resolved via `cth_query -tool vc_lint ENVS CHEETAH_RTL_ROOT` |
| `LINT_GLOBAL_REPO` | Global lint repository (rules, waivers) | Resolved via `cth_query -tool vc_lint envs LINT_GLOBAL_REPO` |
| `LINT_GLOBAL_WAIVER` | Global lint waiver directory | Resolved via `cth_query -tool vc_lint envs LINT_GLOBAL_WAIVER` |
| `VC_METHODOLOGY_LINT` | Synopsys VC methodology path | Set by the VC Static tool (contains `rules/OpenLatch.tcl`) |
| `NBPOOL` | Netbatch pool | Default: `zsc10_normal` |
| `NBQSLOT` | Netbatch queue slot | Default: `/ddg/ip/fe/rtl` |

---

## Utility Scripts

### `lint_waiver_analyze.py`

Located at `$WORKAREA/static/vc_lint/inputs/scripts/lint_waiver_analyze.py`.

Invoked by `make lint_qc`:
```bash
lint_waiver_analyze.py \
  $WORKAREA/static/vc_lint/waivers \
  -o $WORKAREA/output/<DUT>/vc_lint/waiver_info.txt \
  -x $WORKAREA/output/<DUT>/vc_lint/waiver_csv.csv \
  -c $WORKAREA/output/<DUT>/vc_lint/<DUT>/vc_lint_run/vcst_rtdb/reports/waiver.rpt.gz \
  -cl $WORKAREA/output/<DUT>/vc_lint/vc_ol_run/vc_lint_run/vcst_rtdb/reports/waiver.rpt.gz
```

**What it does:**
- Counts temporary vs permanent waivers per rule
- Checks for backslide against maximum allowed waiver counts
- Produces `waiver_info.txt` (human-readable summary) and `waiver_csv.csv` (machine-parseable)
- Separately handles OL waivers (files with `ol_` prefix)

### `lint_postrun_clean.py`

Located at `$WORKAREA/static/vc_lint/inputs/scripts/lint_postrun_clean.py`.

Invoked by `make lint_postrun_clean`. Removes large internal files including:
- `.internal` directories (SAM internals)
- `work/` directories
- `OpenLatch.csv` and `openlatchviolation.rpt`
- Other large intermediate files

---

## Key Reports and Where to Find Them

| Report | Location | Description |
|---|---|---|
| Lint session log | `output/<DUT>/vc_lint/<DUT>/vc_lint_run/vcst_session.log` | Main pass/fail determination for lint |
| OL session log | `output/<DUT>/vc_lint/vc_ol_run/vc_lint_run/vcst_session.log` | Main pass/fail determination for OL |
| Lint waiver report | `output/<DUT>/vc_lint/<DUT>/vc_lint_run/vcst_rtdb/reports/waiver.rpt.gz` | Detailed waiver match report (compressed) |
| OL waiver report | `output/<DUT>/vc_lint/vc_ol_run/vc_lint_run/vcst_rtdb/reports/waiver.rpt.gz` | OL waiver match report (compressed) |
| Blackbox report | `output/<DUT>/vc_lint/<DUT>/vc_lint_run/reports/blackbox.rpt` | Lists blackboxed modules |
| Compile summary | `output/<DUT>/vc_lint/vc_lint_compile/vc_lint_compile.summary.rpt` | Compile pass summary |
| Lint run summary | `output/<DUT>/vc_lint/<DUT>/vc_lint_run/vc_lint_run.summary.rpt` | Lint run pass summary |
| OL run summary | `output/<DUT>/vc_lint/vc_ol_run/vc_lint_run/vc_lint_run.summary.rpt` | OL run pass summary |
| SAM autogen summary | `output/<DUT>/vc_lint/vc_lint_sam_autogen/vc_lint_sam_autogen.summary.rpt` | SAM autogen pass summary |
| Violations report | `output/<DUT>/vc_lint/<DUT>/vc_lint_run/reports/violations.rpt` | All unwaived violations with details — **most useful for analysis** |
| Design read violations | `output/<DUT>/vc_lint/<DUT>/vc_lint_run/reports/report_read_violations_verbose.rpt` | Design-read-stage violation details |
| Waiver analysis | `output/<DUT>/vc_lint/waiver_info.txt` | Human-readable waiver count summary |
| Waiver CSV | `output/<DUT>/vc_lint/waiver_csv.csv` | Machine-parseable waiver report |
| Pass sentinels | `*.PASS` files in each stage directory | Presence indicates the stage passed |

### Understanding `vcst_session.log`

The `vcst_session.log` is the top-level log for any VC-Lint stage. The summary at the bottom contains:
- **VCST counts** — Error/warning counts are listed directly in the session log
- **DESIGN_READ counts** — Details in `reports/report_read_violations_verbose.rpt`
- **VIOLATION counts** — Details in `reports/violations.rpt`
- **Exit status** and **runtime information**

The `vcst_rtdb/reports/` area contains Spyglass-Lint-style reports — same data presented in a different format. The most useful file there is `waiver.rpt` (or `waiver.rpt.gz`), which lists each waiver and the violations it matched.

---

## Common Issues and Troubleshooting

### Compile Failures
- Check `output/<DUT>/vc_lint/vc_lint_compile/vc_lint.combinelog` for VCS compile errors.
- Missing files: Ensure `filelists_rtl` has been generated (`make` from `gen_filelist/` or the `:filelists_rtl` Gradle dependency).
- Macro conflicts: Look for duplicated guarding macros (IPQC rule clnt.17_39).

### Lint Run Failures
- Check `vcst_session.log` for the error summary.
- New errors after RTL changes: Review the `vc_lint_run.summary.rpt` for newly introduced violations.
- Waiver not matching: Verify the filter pattern in the waiver file matches the current violation path/rule exactly.

### OL Run Failures
- Same troubleshooting as lint, but check `vc_ol_run/vc_lint_run/vcst_session.log`.
- If an IP was added as an autogen SAM block but still fails in OL, consider adding it to `bbox_modules` in `ol_run_settings.tcl`.
- The Open Latch rule does **not** use abstracts. The run should complete flat without them. If you see large numbers of errors or excessive run time, use `bbox_modules` for modules that would normally be abstracted.

### Enabling OL in a New Repo

If OL is not yet configured in a repo:

1. Ensure `baseline_tools` is at version `2023.06.eng.005` or later.
2. Copy `ol_run_settings.tcl` from `baseline_tools/repo_seed_template/static/vc_lint/inputs/` to `static/vc_lint/inputs/`.
3. Customize `ol_run_settings.tcl`:
   - Copy all `bbox_modules` lines from your `run_settings.tcl`
   - Update `waiver_files` to load your local DUT's OL waiver file (e.g., `<DUT>_ol_waivers.awl.tcl`)
4. Create an OL waiver file in `static/vc_lint/waivers/` (e.g., `<DUT>_ol_waivers.awl.tcl`).
5. Run OL after lint compile: `make ol_run`

### SAM Autogen Failures
- Check `vc_lint_sam_autogen/vcst_session.log` and `nblog/` for netbatch job failures.
- Timeout issues: The `wait_time` is set to 120 seconds in `sam_autogen.tcl`; complex blocks may need more.
- Per-IP logs are in `vcjobs/{ip}_{params}_paramdir/`.

### Waiver QC Failures
- `lint_waiver_analyze.py` reports backslide: A new waiver was added that exceeds the maximum allowed count for a rule.
- Missing `-user`: Every waiver must have an owner IDSID.
- Wrong extension: Waiver files must end in `.awl.tcl`.

### Disk Space
- Run `make lint_postrun_clean` after both lint and OL pass to remove large intermediate files.
- `MODEL_SIZE_REDUCTION` must NOT be set during compile/autogen/OL stages — it runs only during `lint_postrun_clean`.

---

## IPQC Rules Reference

The following automated IPQC checks apply to VC Lint/OL. See `$WORKAREA/.github/copilot/rtl-lint-code-review.instructions.md` for full details.

| Rule | Description |
|---|---|
| clnt.17_39 | No duplicated guarding macros across RTL files |
| clnt.17_428 | VC Lint waivers within tolerances; all waivers have owners |
| clnt.17_429 | VC Lint running, passing, and gating in GK |
| clnt.17_430 | VC OL running, passing, and gating in GK |
| clnt.17_431 | Correct VC-Lint tool and methodology versions |
| clnt.17_432 | No FIXMEs in `static/vc_lint` configuration files |
| clnt.17_433 | Waiver files from approved locations, `.awl.tcl` extension |
| clnt.17_434 | `MODEL_SIZE_REDUCTION` only in `lint_postrun_clean` stage |
| clnt.17_435 | No unexpected blackboxed cells (analog HIPs only) |
| clnt.17_437 | SAM file generation occurring in lint run |
| clnt.17_440 | `COPY_CODEGEN_FILES` and `MODEL_SIZE_REDUCTION` not set in SAM/OL flows |
| clnt.17_441 | `flow.cfg` uses `baseline_tools` for compile opts; no `VCS_ELAB_OPTS` |
| clnt.17_442 | No local stage definitions (`lint_qc`, `lint_postrun_clean`, `ol_run`, `ol_gui`) in Makefile |
| clnt.17_445 | Required TCL settings present in `run_settings.tcl` and `ol_run_settings.tcl` |
| clnt.17_446 | SAM autogen TCL has required performance/stability settings |
| clnt.17_447 | All permanent waivers reviewed by Lint WG |

---
