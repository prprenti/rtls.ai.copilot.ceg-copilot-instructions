---
name: "Build & Run Code Review Rules"
applyTo: "**/src/**/*.v*, **/src/**/*.sv*, **/src/*.f, **filelists/**/*.f, **/cfg/*_xProp.cfg, **/*analysis_opts.f*"
description: "Rules for reviewing Build & Run quality checks. Ensures compilation correctness, tool versions, and proper simulation configuration."
---

# Build & Run Code Review Rules
*Derived from IPQC rule metadata for category 1 (Build & Run)*

Review Build & Run artifacts for quality and compliance with IPDS standards. These checks ensure correct VCS compilation, proper tool versions, and simulation configuration.

---

## Bug Rules ⚠️ ALL CRITICAL

**All bug rules represent CRITICAL functional errors that can cause silicon failures.** Each must be carefully reviewed.

---
### BUGS/Rule_1: Duplicate Files Under Search Path Directories
Detect duplicated files in `*.f` files. Duplicated files can lead to the wrong file being compiled with no warning.

```systemverilog
// ❌ Bad: duplicated file name across search path directories
$ip/src/rtl/file1.v
$ip/src/rtl/file2.v
$ip/subip/foo/src/rtl/file1.v

// ✅ Good: no duplicated file names across search path directories
$ip/src/rtl/file1.v
$ip/src/rtl/file2.v
$ip/subip/foo/src/rtl/file3.v
```

---
### BUGS/Rule_2: Duplicated Directories Under Search Path Directories
Detect duplicated directories in `*.f` files when used with `-y` or `-v` directives. Duplicated directories can lead to the wrong file being compiled with no warning.  Strongly suggest that `-y` and `-v` directives should be changed to use specific file names.

```systemverilog
// ❌ Bad: duplicated directory name across search path directories
-y $ip/src/rtl/
-v $ip/src/foo/
-y $ip/src/rtl

// ✅ Good: no duplicated directory names across search path directories
-y $ip/src/rtl/
-v $ip/src/rtl/
-y $ip/src/foo/
```

---

### BUGS/Rule_3: Baseline Tools Version Check
If baseline_tools link target is updated, it should be to a target containing a newer version.

```
// ❌ Bad: New baseline_tools version tag is lexically older than the previous version
old: /p/cth/pu_tu/prd/baseline_tools/ddgcth/2023.12.sp1.p1.038/
new: /p/cth/pu_tu/prd/baseline_tools/ddgcth/2023.06.p1.050/

// ✅ Good: New baseline_tools version is lexically newer than the previous version
old: /p/cth/pu_tu/prd/baseline_tools/ddgcth/2023.12.sp1.p1.038/
new: /p/cth/pu_tu/prd/baseline_tools/ddgcth/2024.01.sp1.p1.001/
```

---

## Quick Reference Checklist
- [ ] **Duplicate files** — No duplicate filenames across search path directories (BUGS/Rule_1)
- [ ] **Duplicate directories** — No duplicate `-y` or `-v` directories in `*.f` files (BUGS/Rule_2)
- [ ] **Baseline tools** — `baseline_tools` softlink points to a newer version (BUGS/Rule_3)
