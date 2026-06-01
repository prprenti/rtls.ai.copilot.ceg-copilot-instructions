---
applyTo: "src/val/griffin**,**/*griffin*.prompt.md"
---

# Overview
Griffin is a Python-based framework for post-processing checkers and coverage in pre-silicon validation. It operates on UTDB traces and provides a structured methodology for building reusable, fast, and robust validation agents.

# Griffin Repo and Agent Setup

## Create a New Griffin Agent
```
python <griffin_repo>/scripts/new_collateral/create_new_agent.py \
  --user_name <username> \
  --dut <dut_name> \
  --agent_name <agent_name> \
  --griffin_dir <griffin_directory> \
  [--ut_dir <ut_directory>] [--chk] [--cov] [--no_qry] [--no_ral] [--no_fal]
```
args explanation:  
--chk: Only checker  
--cov: Only coverage  
--no_qry: Do not generate query collateral/
--no_ral: Add if Saola PyRal support isn't needed  
--no_fal: Add if Saola PyFal support isn't needed  

## Directory Structure
```
src/val/griffin/
├── agents/
│   ├── <agent_name>/
│   │   ├── <agent_name>_chk.py
│   │   ├── <agent_name>_params.py
│   │   ├── <agent_name>_qry.py
│   │   ├── <agent_name>_error.py
│   │   └── ...
├── common/
│   ├── <dut>_common_base/
│   │   ├── <dut>_cfg.py
│   │   ├── <dut>_params.py
│   ├── <dut>_common_queries/
│   │   ├── <interface>_qry.py
│   │   ├── <interface>_rec.py
│   │   └── ...
└── ...
```

# Core Griffin Components (Original Text Retained)
Config – Stores configuration knobs and provides getter/setter functions.  
Query – Connects Griffin agents to UTDBs.  
Record – Wrapper for UTDB query results (rows).  
Params – Stores parameters for agents and unit tests.  
Error – Contains error codes/messages for agents.  
Checker Agent – Main executable for checking logic.  

# Griffin API Syntax and Usage
To access the database use self.DB.all

## GRIFFIN_CHECK
Checks a condition and throws an error if the condition fails. Also tracks coverage.

```python
GRIFFIN_CHECK(
    cond=<boolean_condition>,
    time=<timestamp>,
    bucket="<error_bucket>",
    coverpoint_name="<coverage_point>",
    debug_msg=f"Debug info: {var1}, {var2}",
    fatal=<True|False>  # Optional
)
```

Example:
```python
for rec in self.template_qry.all_recs:
    GRIFFIN_CHECK(
        cond=(rec.r.ADDRESS != BAD_ADDRESS),
        time=rec.r.TIME,
        bucket="Bad Address Was Seen",
        coverpoint_name="Bad_Address_Check",
        debug_msg=f"	ADDRESS : {rec.r.ADDRESS}
	URI_TID : {rec.r.URI_TID}"
    )
```

## GRIFFIN_MSG and GRIFFIN_DBG (Original)
```python
GRIFFIN_MSG(time=<timestamp>, msg="This is an info message")
GRIFFIN_DEBUG(time=<timestamp>, msg="This is a debug message")
GRIFFIN_FATAL(time=<timestamp>, bucket="<error_bucket>",debug_msg="<debug msg>")
```

## Tlu and Sal Classes (Original Pattern)
Used for tracking state and signal changes over time.
```python
self.fsm = Tlu(name='FSM', throw_exception_when_no_value_is_recorded=False)
self.reset = Sal(name='RESET')

self.fsm.set_value_provider(self.abc_fsm_qry.all_recs,
                            time_field_name='time',
                            item_field_name='state')
self.reset.set_value_provider(self.abc_sig_qry.get_all_reset_signal_toggle(),
                              value_field_name='VALUE')

self.fsm.get_first_item()
self.fsm.get_last_item()
self.fsm.get_last_item_at_or_prior_to_time(time)
self.reset.get_value_at_time(time)
self.reset.get_all_value_changes_prior_to_time(end_time)
```

## EOT Usage
Represents "end of test" time.
```python
GRIFFIN_CHECK(
    cond=response_arrived,
    time=EOT(),
    bucket='Response never arrived',
    debug_msg='Response never arrived at EOT'
)
```

## Sorting Example
```python
end_times = timewindow_startstop_times + [EOT()]
for start, end in zip(start_times, end_times):
    window = [rec for rec in my_records if start <= rec.TIME < end]
    GRIFFIN_CHECK(
        cond=len(window) > 23,
        time=end,
        bucket="Too many records in timewindow!",
        debug_msg=f"From {start} to {end}, saw {len(window)} records."
    )
```

## Common CLI Arguments (Original)
--test_dir/-t, --output_dir/-o, --logdb_dir/-ld, --debug/-d,  
--ok_error_file/-oef, --postsim_append/-pa, --log_suffix/-ls,  
--return_code_zero/-rcz, --griffin_args_file/-ga, --disable_file_args/-dfa  

#  Agent Lifecycle Summary
1. __init__: obtain cfg via CommonUtils.get_cfg(); early-exit if knob disabled.  
2. connect(): call connect_to_db() for each qry.  
3. run(): orchestrate (grouping, sub-check execution or coverage sampling).  

#  Enable Knob Pattern
```python
if not self.cfg.get_val_by_name(MY_AGENT_CHK_EN):
    self.griffin_exit()
```
Keep *_CHK_EN / *_COV_EN in params file.

#  Canonical Checker Template
```python
from griffin_collaterals.griffin_report import GRIFFIN_CHECK, GRIFFIN_ERROR
from common.pkg_common_base.pkg_common_base import PkgBaseChk
from common.pkg_common_utils.pkg_common_utils import PkgCommonUtils
from common.pkg_common_base.pkg_cfg import PkgCfg
from agents.example.example_params import EXAMPLE_DB, EXAMPLE_CHK_EN
from agents.example.example_qry import ExampleQry

class ExampleChk(PkgBaseChk):
    def __init__(self):
        self.cfg: PkgCfg = PkgCommonUtils.get_cfg()
        if not self.cfg.get_val_by_name(EXAMPLE_CHK_EN):
            self.griffin_exit()
        self.qry = ExampleQry()

    def connect(self):
        self.qry.connect_to_db(EXAMPLE_DB)

    def run(self):
        for rec in self.qry.all_recs:
            GRIFFIN_CHECK(
                cond=rec.FIELD_OK,
                time=rec.TIME,
                bucket="EXAMPLE_FIELD_ERR",
                debug_msg=f"	FIELD : {rec.FIELD}
	TIME  : {rec.TIME}"
            )
```

```

#  Sub-Check Pattern (From PRE / Monitor / Data Agents)
```python
class SomeSubChk:
    def set_data(self, all_recs_for_scope, aux_index):
        self.should_call_check = <predicate>
        # precompute filtered lists / states here

    def check(self):
        if not self.should_call_check:
            return
        # emit errors or checks
```
Always separate data phase (set_data) from evaluation phase (check) for reuse and clarity.

#  Data Integrity Pattern (Based on ccf_data_chk)
Key Steps Per Address:
1. Group recs by address.  
2. Derive orig request per TID: `get_original_rec_by_tid`.  
3. Accumulate partial data (both halves) → reconstruct full cacheline:  
   `CcfClrCommonUtils.get_full_cacheline_data_from_both_data_recs()`  
4. Compute expected line using contextual recs & GO semantics.  
5. Diff on mismatch: `CcfClrCommonUtils.get_diff_string(actual, expected)`.

#  PRE / PCLS Decision Summary
Determine if PRE is:
- PCLS-derived (miss path with prior encoding record) OR
- CBO-calculated (LLC hit path).
Supporting helpers (examples):
- `CcfCboUtils.get_llc_state_for_first_accepted_cbo`
- `CcfCboUtils.is_prefetch_promoted`
- `CcfPreUtils.is_upi_nc`
- Snoops classification: `snoop_fwd_fe`, `snoop_fwd_m`, `snoop_miss`
Return enumerated constant (`DATA_PRE_*` / `RSP_PRE_*`) — never literal magic numbers.

#  Monitor Modeling (ccf_monitor_chk)
Two internal models:
- Snapshot (CcfRefMonitorArray): time-indexed events → query historical state.
- Tracker (CcfMonitorTracker): incremental state + overflow reasoning.
Populate snapshot:
```python
new_event = CcfMonitorEvent(lpid, address, opcode, set_monitor_during_reject, cbo_pass_rec)
ref_monitor_array.add_event(cbo_id, time, new_event)
ref_monitor_array.sort_db()
ref_monitor_array.arrange_db()
```
Hit evaluation per transaction:
```python
snapshot = ref_monitor_array.get_current_monitor_array(time, cbo_id)
expect_hit = snapshot and snapshot.is_monitor_hit(addr)
```

#  BIOS Mailbox → PKGC Achievement (b2b_pkgc_chk)
Algorithm:
1. Parse mailbox DATA (disable bitmask) → derive highest enabled PKGC target.  
2. For each target, scan forward for matching PKGC entry + subsequent bootfsm-down in same window.  
3. Build parallel lists: expected_pkgc vs entered_pkgc.  
4. `GRIFFIN_CHECK(cond=(entered==expected), bucket=NOT_ALL_PKGC_ACHIEVED_ERROR, time=last_mailbox_time)`.

#  Coverage Best Practices
- Define all bins before sampling (`griffin_cov_sample`).
- Avoid huge Cartesian crosses; create focused crosses only.
- Use stable symbolic constants (e.g. MAX_NUM_OF_CBO) not raw integers.
- Dynamic binning: pre-compute set of seen values to keep bin count bounded.

#  Error & Debug Message Guidelines
Include fields (tab-aligned):
```
	Req Opcode     : {req}
	Failing Opcode : {opc}
	TID            : {tid}
	Address        : {hex(addr)}
	LLC State      : {state}
	Non Coherent   : {is_nc}
	Expected       : {hex(exp)}
	Actual         : {hex(act)}
```
Use hex for encoding/value comparisons; show diff string for data.

#  Performance Tips
- Pre-index once per dimension: by TID, by address.
- Use list/set/dict comprehensions instead of repeated loops.
- Use any()/all() for predicate aggregation.
- Avoid recomputing expensive classification inside loops (cache in locals).

#  Unit Test Pattern (See test_b2b_pkgc_chk)
```python
default_knobs = {B2B_PKGC_CHK_EN: 1}
self.mock_griffin_cfg(PkgCfg, default_knobs)
self.initialize_class_under_test(B2bPkgcChk)
db = self.create_db_from_header(db_name=IOSF_SB_DB, header_attributes=iosf_sb_log_header_attributes)
logger = IosfSbLogger(db)
logger.add_mailbox_addr(timestamp=10, data='0000001d EOM')
self.run_cut()
self.assertEqual([], self.get_griffin_errors_list())
```

#  Quick Authoring Checklist
- [ ] *_params.py defines *_CHK_EN / *_COV_EN
- [ ] Early exit if knob disabled
- [ ] connect() only wires DBs
- [ ] run() orchestrates (no deep logic in __init__)
- [ ] Sub-check separation (set_data + check)
- [ ] Coverage bins defined before sampling
- [ ] Structured debug messages
- [ ] Unit test: one pass + one fail
- [ ] No magic numbers (use params/constants)

