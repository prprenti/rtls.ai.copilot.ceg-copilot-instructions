# Log File Patterns by Protocol

## Common Log Files (All IUs)

| Log File | Content | Search Commands |
|----------|---------|-----------------|
| `postsim.log` | Post-simulation summary, final status | `grep -i "error\|fail\|pass" postsim.log` |
| `jestr.log` | Main simulation log, UVM messages | `grep -i "uvm_error\|uvm_fatal" jestr.log` |
| `sequence_trk_uvm.log` | UVM sequence execution trace | `grep "<seq_name>" sequence_trk_uvm.log` |
| `RAL_access_trk_uvm.log` | Register access log (RAL) | `grep "<reg_name>" RAL_access_trk_uvm.log` |

## D2D / CFI Protocol Logs

| Log File | Content |
|----------|---------|
| `CFI_DEV_VC*_tracker.log` | DEV side VC transactions |
| `CFI_CTL_VC*_tracker.log` | CTL side VC transactions |
| `CFI_*_config_tracker.log` | VC configuration changes |
| `CFI_*_full_txn_tracker_cfi_txn_tracker.log` | Complete transaction details |
| `D2D_CFI_merged_trk.log` | Aggregated CFI activity |

## HBO / IDI Protocol Logs

| Log File | Content |
|----------|---------|
| `idi.log` | IDI protocol events |
| `idi_logdb` | IDI log database (converted) |
| `idi_*_tracker.log` | IDI transaction traces |

## MC / Memory Controller Logs

| Log File | Content |
|----------|---------|
| `denali.log` | Denali memory model events |
| `griffin_*.log` | Griffin checker output |
| `mc_*_tracker.log` | MC transaction traces |

## Log Analysis Workflow

```bash
# 1. Get failure timestamp from postsim
grep -i "error\|fail" postsim.log | head -5

# 2. Find context in main log
grep -B20 -A10 "<error_signature>" jestr.log

# 3. Search protocol-specific trackers
grep "@<failure_time>" *_tracker.log

# 4. Extract time window (±100ns around failure)
awk '/@12245ns/,/@12445ns/' protocol_tracker.log
```
