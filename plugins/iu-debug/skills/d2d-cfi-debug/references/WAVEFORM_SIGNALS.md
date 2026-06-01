# CFI Waveform Signals

## Critical Signals to Monitor

### Credit Flow
```systemverilog
d2d_tb.GCD.CFI_DEV_VC*.block_crd_flow    // Credit blocking
d2d_tb.GCD.CFI_DEV_VC*.crd_valid         // Credit valid
d2d_tb.GCD.CFI_DEV_VC*.crd_return        // Credit return
d2d_tb.GCD.CFI_DEV_VC*.crd_count         // Credit counter
```

### Data Transfer
```systemverilog
d2d_tb.GCD.CFI_DEV_VC*.tx_valid          // Transmit valid
d2d_tb.GCD.CFI_DEV_VC*.tx_ready          // Transmit ready
d2d_tb.GCD.CFI_DEV_VC*.tx_data           // Transmit data
d2d_tb.GCD.CFI_DEV_VC*.rx_valid          // Receive valid
d2d_tb.GCD.CFI_DEV_VC*.rx_data           // Receive data
```

### Control Path
```systemverilog
d2d_tb.GCD.CFI_DEV_VC*.vc_enable         // VC enable
d2d_tb.GCD.CFI_DEV_VC*.vc_state          // VC state machine
```

### DFS (Dynamic Frequency Scaling)
```systemverilog
d2d_tb.*.dfs_state                       // DFS state
d2d_tb.*.freq_ratio                      // Frequency ratio
```

## Waveform Debug Workflow

1. **Navigate to failure time** (from postsim.log timestamp)
2. **Add credit signals** first to check flow
3. **Add data signals** to verify transactions
4. **Check timing relationships** between valid/ready
5. **Verify state machine** transitions

## Signal Grouping Recommendations

```
Group: CFI_Credits
  - block_crd_flow
  - crd_valid
  - crd_return
  - crd_count

Group: CFI_Data
  - tx_valid
  - tx_ready
  - tx_data
  - rx_valid
  - rx_data

Group: CFI_Control
  - vc_enable
  - vc_state
```
