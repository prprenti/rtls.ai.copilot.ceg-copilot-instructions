---
name: "RTL+Lint Code Review Rules"
applyTo: "**/vc_lint/**,**/lint/**,**/static/vc_lint/**"
description: "Pre-run waiver and SAM checks for VC Lint code reviews."
---

# Pre-Run Waiver & SAM Checks

These checks are derived from the `vclint_run_pre_check` suite (`static/vc_lint/scripts/vclint_run_pre_check/`). They run **before** the lint execution to catch configuration and waiver issues early. When reviewing waiver or SAM changes, apply these rules.

---

### Pre-Check 1: SAM Model Path Validation

**Applies to:** `static/vc_lint/inputs/load_sam_modules.tcl` (or `static/vc_lint/inputs/<DUT>/<DUT>_load_sam_modules.tcl`)

**What it checks:** Every SAM path referenced in `load_sam_modules.tcl` must point to an existing directory on disk. A missing SAM_MODELS path will cause the lint run to fail hours later with inflated runtime.

**Detection method:** For each entry in the `sam_blocks` list, extract the path (second whitespace-delimited token) and verify the directory exists.

**When reviewing `load_sam_modules.tcl` changes:**
- [ ] Every `lappend sam_blocks` entry has a valid, resolvable path as its second token
- [ ] New SAM entries reference paths that exist in the current release model or subIP drop
- [ ] Removed SAM entries are intentional (module is no longer abstracted or has been blackboxed)

---

### Pre-Check 2a: Perm/Temp Waiver File Segregation

**Applies to:** All files in `static/vc_lint/waivers/`

**What it checks:** Permanent and temporary waivers must be in the correct files — no mixing allowed.

**Rules:**
- A waiver with `-status Waived_Temp` (case-insensitive) is a **temp waiver** and must only appear in a file whose name contains `temp`.
- A waiver **without** `-status Waived_Temp` is a **perm waiver** and must only appear in a file whose name does **not** contain `temp`.

**When reviewing waiver file changes:**
- [ ] No `-status Waived_Temp` entries in perm waiver files
- [ ] No entries missing `-status Waived_Temp` in temp waiver files
- [ ] New waivers are placed in the correct file based on their permanence

---

### Pre-Check 2b: No Statement Filter on Structural Rules

**Applies to:** All waiver files in `static/vc_lint/waivers/`

**What it checks:** For structural-check lint rules, the `-filter` field must **not** contain a `Statement` sub-field. Statement-level filtering on structural rules can mask real issues.

**Structural-check rules (statement filter prohibited):**
`70094`, `70601`, `70602`, `70606`, `70612`, `CombLoop`, `FewSeqOnCG`, `FlopClockConstant`, `FlopEConst`, `FlopFeedbackRace-ML`, `FlopSRConst`, `LatchEnableConstant`, `STARC05-1.4.3.4`, `STARC05-2.4.1.5`, `sim_race07`

**When reviewing waiver changes:**
- [ ] If the `-tag` matches any of the above rules, the `-filter` must not contain `(Statement`
- [ ] If a structural rule needs waiving, use module/instance/signal-level filters only

---

### Pre-Check 2c: User Field Presence

**Applies to:** All waiver files in `static/vc_lint/waivers/`

**What it checks:** Every `waive_violation` entry must contain a `-user` field identifying the owner.

**When reviewing waiver changes:**
- [ ] Every waiver line has a `-user {<idsid>}` field
- [ ] The `-user` field is not empty

---

### Pre-Check 2d: No Timestamp Field in Waivers

**Applies to:** All waiver files in `static/vc_lint/waivers/`

**What it checks:** The `-timestamp` field is prohibited in waivers. It should not be present.

**When reviewing waiver changes:**
- [ ] No waiver contains a `-timestamp` field

---

### Pre-Check 2e: Proper Waiver Justification

**Applies to:** All waiver files in `static/vc_lint/waivers/`

**What it checks:** The `-comment` field must contain a meaningful, human-written justification. Auto-generated comments are not acceptable.

**Detection pattern:** Flags any `-comment` matching `created by <word>` (case-insensitive).

**When reviewing waiver changes:**
- [ ] The `-comment` explains **why** the violation cannot be fixed in RTL
- [ ] The `-comment` does not match the pattern `created by ...` (auto-generated text)

---

### Pre-Check 2f: BugECO Required in Temp Waivers

**Applies to:** Temp waiver files in `static/vc_lint/waivers/` (files with `temp` in the name)

**What it checks:** Every temporary waiver must reference a valid 11-digit HSD BugECO ID in its `-comment` field. This ensures every temp waiver is tracked to a bug that will eventually be resolved.

**Accepted HSD reference formats in `-comment`:**
- `HSD: 12345678901` (preferred)
- `HSD12345678901`, `HSD-12345678901`, `HSD 12345678901`
- `https://hsdes.intel.com/appstore/article/#/12345678901`
- `https://hsdes.intel.com/appstore/article-one/#/article/12345678901`

**When reviewing temp waiver changes:**
- [ ] Every temp waiver's `-comment` contains an 11-digit HSD ID in one of the accepted formats
- [ ] The referenced HSD is relevant to the violation being waived

---

## Quick Reference Checklist

### Pre-Run Checks
- [ ] **SAM paths valid** — All `sam_blocks` paths in `load_sam_modules.tcl` resolve to existing directories (Pre-Check 1)
- [ ] **Perm/temp segregation** — Temp waivers only in temp files, perm only in perm files (Pre-Check 2a)
- [ ] **No statement filter on structural rules** — Structural-check rules not waived with Statement filter (Pre-Check 2b)
- [ ] **User field present** — Every waiver has a `-user` field (Pre-Check 2c)
- [ ] **No timestamp field** — No waivers contain `-timestamp` (Pre-Check 2d)
- [ ] **Proper justification** — No auto-generated `-comment` text (Pre-Check 2e)
- [ ] **BugECO in temp waivers** — Every temp waiver references a valid 11-digit HSD (Pre-Check 2f)
