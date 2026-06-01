# IDI Tracker Fields

## Common Tracker Fields

| Field | Description | Typical Source |
|-------|-------------|----------------|
| `Src` | Source agent/component | `trans.src_agent_name` |
| `Dest` | Destination agent | `trans.dest_agent_name` |
| `Addr` | Address | `trans.address` |
| `Opcode` | Operation code | `trans.opcode` |
| `Data` | Transaction data | `trans.data` |
| `Time` | Simulation time | Automatic |

## Tracing Field Values

### Step 1: Identify Tracker File
For IDI protocol: `subip/vip/idi_vc/idi/idi_tracker.sv`

### Step 2: Find writeValue Calls
```bash
grep -n 'writeValue("<field>"' idi_tracker.sv
```

### Step 3: Analyze Code Context
```systemverilog
// Example pattern in tracker
function void log_request(idi_transaction trans);
  writeValue("Src", trans.src_agent_name);  // ← Found
  writeValue("Dest", trans.dest_agent_name);
  writeValue("Addr", $sformatf("%h", trans.address));
endfunction
```

### Step 4: Trace Value Source
- Check transaction field population
- Follow assignment chain backwards
- Verify with waveform if needed

## Table Tracker Infrastructure

**Key Class**: `idi_vc_table_tracker`  
**Location**: `src/table_tracker/table_tracker.sv`

```systemverilog
// Key method
function void writeValue(string header, string value);
  // Assigns value to field in log line buffer
endfunction
```

## Debug Workflow

1. Identify unexpected field value in idi.log
2. Search for `writeValue("<field>"` in tracker
3. Trace value source (transaction, config, computed)
4. Check event context (when is field written?)
5. Verify with waveforms if needed
