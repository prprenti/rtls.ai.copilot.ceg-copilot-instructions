# CFI Credit Return Debug

## Credit Flow Mechanism

### Key Parameters
- **Return Credit Max Delay**: 10 cycles (default)
  - After `tx_rxcrd_block` asserts, max 10 more valid transactions can be sent
- **D2D Link Credit Threshold**: 22 credits

### Credit Blocking Signals
```systemverilog
// Credit block assertion
d2d_tb.GCD.CFI_DEV_VC0_ti.cfi_vc_rsp_rx[0].block_crd_flow

// Credit valid signal (de-asserts ~9 cycles after block)
d2d_tb.GCD.CFI_DEV_VC0_ti.cfi_vc_rsp_rx[0].crd_valid
```

### Expected Credit Flow Behavior
1. When credits drop below threshold (22), `block_crd_flow` asserts
2. After block assertion, up to 10 more valid transactions allowed
3. After ~9 cycles, `crd_valid` de-asserts
4. Credit return resumes when credits replenished

## Configuration Path

```systemverilog
// In src/val/tb/env/d2d_gtc_env.sv
m_cfi_vc[cfi_vc_index].m_cfi_vc_agent_cfg.return_credit_max_delay = 
    `CFGg.picker.d2d_cfi_return_credit_max_delay;
```

**Systeminit switch**: `D2D_CFI_RETURN_CREDIT_MAX_DELAY`

## Debug Steps for Credit Issues

```bash
# 1. Check credit threshold assertion
grep "block_crd_flow" CFI_*_tracker.log

# 2. Count valid transactions after block
grep "crd_valid" CFI_*_tracker.log | grep "@<time_of_block>"

# 3. Verify credit return timing
# Look for credit return packets in tracker

# 4. Check waveform signals
# Load FSDB and search for:
#   - d2d_tb.GCD.CFI_DEV_VC*.block_crd_flow
#   - d2d_tb.GCD.CFI_DEV_VC*.crd_valid
#   - Credit counter signals
```

## Common Credit Issues

| Issue | Symptom | Check |
|-------|---------|-------|
| Credit underflow | Link pool underflow error | Credit return timing |
| Credit overflow | Credits exceed max | Credit initialization |
| Stuck credits | No progress | block_crd_flow stuck |
