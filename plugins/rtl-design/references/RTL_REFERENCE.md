# RTL Development Reference

## Focus Areas

- Signal naming and consistency with local patterns
- Macro usage from repo-local macro definition files
- Clocking and pipeline-stage integrity
- Instrumental (`_inst`) signal strategy for debug/assertion checks

## Build/Run Hook

- For repo-local compile/lint/debug make targets, use MCP `build-run/run_make`.
- Prefer static-analysis sub-agents (`cdc`, `lint`, `lp`, `sgdft`, `vc-effm`) for methodology-specific flows.

## Common Verification Artifacts

- Primary outputs and logs are flow-specific and produced under `output/<dut>/...`.
- For static signoff logs, use the domain-specific references in this directory.

## Typical Exploration Pattern

- Use semantic and text search to trace existing signal patterns.
- Confirm interface direction/width consistency before introducing new ports.
- Validate macro conventions from existing repo modules before coding new logic.
