# MC ECC Syndrome Mismatch Debug Reference

## Overview

**Checker:** `mc_ecc_chk`  
**Location:** `$WORKAREA/src/val/griffin/agents/mc_ecc/`  
**Purpose:** Validates ECC encoding, syndrome computation, and error correction

## Common Failures

### 1. Syndrome Mismatch

**Error Pattern:**
```
GRIFFIN_FATAL: [McEccChk] ECC syndrome mismatch
Address: 0x1234_5678
Expected syndrome: 0x3F, Computed: 0x2E
Data: 0xDEADBEEF_CAFEBABE
```

**Debug Steps:**
```bash
# 1. Check ECC tracker for the failing address
zcat mc_ecc_trk.out.gz | grep "1234_5678" | head -5

# 2. Extract data and ECC bits
# Format: TIME ADDR DATA ECC_BITS SYNDROME

# 3. Verify ECC polynomial manually (for SECDED)
# H-matrix multiplication should give syndrome
```

### 2. Uncorrectable Error Not Flagged

**Error Pattern:**
```
GRIFFIN_ERROR: [McEccChk] 2-bit error not flagged as uncorrectable
```

**Debug Steps:**
```bash
# 1. Check error injection log
zcat mc_error_inject.log.gz | grep "<address>"

# 2. Verify RTL UE detection
grep -r "ue_flag\|uncorrectable" $WORKAREA/src/rtl/mc/ecc/*.v
```

### 3. Corrected Data Wrong

**Error Pattern:**
```
GRIFFIN_FATAL: [McEccChk] Corrected data mismatch
Original: 0x1234, Corrected: 0x1235, Expected: 0x1234
```

**Debug Steps:**
```bash
# 1. Identify bit flip position
# XOR original and expected to find flipped bit

# 2. Check syndrome-to-bit mapping table in RTL
grep -r "syndrome_decode\|bit_position" $WORKAREA/src/rtl/mc/ecc/*.v
```

## ECC Modes

| Mode | Capability | Syndrome Width |
|------|------------|----------------|
| SECDED | 1-bit correct, 2-bit detect | 8 bits (64b data) |
| SDEC | 2-symbol correct | 16+ bits |
| On-Die ECC | Transparent to MC | N/A |

## Debug Data Format

```
ECC Tracker Fields:
TIME         - Simulation time in ps
TRANS_TYPE   - RD/WR/SCRUB
ADDR         - System address
DATA         - 64B cache line
ECC_BITS     - Computed ECC (8B for SECDED)
SYNDROME     - Computed syndrome
ERROR_TYPE   - NONE/CE/UE
CORRECTED    - Corrected data (if CE)
```

## RTL Files

```bash
$WORKAREA/src/rtl/mc/ecc/mc_ecc_enc.v       # ECC encoder
$WORKAREA/src/rtl/mc/ecc/mc_ecc_dec.v       # ECC decoder
$WORKAREA/src/rtl/mc/ecc/mc_ecc_syndrome.v  # Syndrome compute
$WORKAREA/src/rtl/mc/ecc/mc_ecc_correct.v   # Bit correction
```
