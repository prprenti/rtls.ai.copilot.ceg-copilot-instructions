# IU-Specific RTL Paths

## Repository Path Pattern

```
$GIT_REPOS/ddgip/gk/<iu>-ddgip-trunk/
```

## IU Directory Mappings

| IU | Repository Path | RTL Location |
|----|-----------------|--------------|
| **D2D FDI** | `$GIT_REPOS/ddgip/gk/fdi-ddgip-trunk/` | `src/d2d/rtl/`, `src/codegen/` |
| **HBO** | `$GIT_REPOS/ddgip/gk/hbo-ddgip-trunk/` | `src/hbo/rtl/`, `src/codegen/` |
| **DMU** | `$GIT_REPOS/ddgip/gk/dmu-ddgip-trunk/` | `src/dmu/rtl/`, `src/codegen/` |
| **SNCU** | `$GIT_REPOS/ddgip/gk/sncu-ddgip-trunk/` | `src/sncu/rtl/`, `src/codegen/` |
| **MC** | `$GIT_REPOS/ddgip/gk/mc-ddgip-trunk/` | `src/mc/rtl/`, `src/codegen/` |

## Common RTL Directories

| Directory | Content |
|-----------|---------|
| `src/<iu>/rtl/` | Main RTL source files |
| `src/codegen/` | Auto-generated RTL |
| `subip/` | Submodule IP blocks |
| `subip/vip/` | Verification IP (VIP) |

## VIP Locations by Protocol

| Protocol | VIP Path |
|----------|----------|
| CFI | `$WORKAREA/subip/vip/cfi_vc/` |
| IDI | `$WORKAREA/subip/vip/idi_vc/` |
| NOC | `$WORKAREA/subip/vip/noc_vc/` |
| IOSF | `$WORKAREA/subip/vip/iosf_vc/` |

## RTL Investigation Commands

```bash
# Find module definition
grep -rn "module <module_name>" src/<iu>/rtl/

# Search for signal in RTL
grep -rn "<signal_name>" src/<iu>/rtl/

# Find state machine
grep -rn "case.*state\|enum.*state" src/<iu>/rtl/

# Locate VIP checker
find subip/vip -name "*checker*.sv" -o -name "*monitor*.sv"
```
