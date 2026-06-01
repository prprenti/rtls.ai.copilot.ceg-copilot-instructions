# CTH Query Reference

Use this reference when the `cth-query` skill needs deeper command examples,
output interpretation details, or fallback diagnosis.

## Primary Method: `cth_query`

```bash
# Resolve an env variable to its CTH value (use this first)
cth_query -tool <tool> ENVS <KEY> -resolve -q

# Resolve a parameter
cth_query -tool <tool> PARAMS <key> -resolve -q

# Get a tool version pin
cth_query -tool <tool> TOOLVERSION <vip_name> -resolve -q

# Resolve env variable to an absolute filesystem path
cth_query -tool <tool> ENVS <KEY> -resolve_path -q

# Show which CTH source file defines the variable (no resolution)
cth_query -tool <tool> -source ENVS <KEY>
```

The command is on PATH in workspaces sourced under liteinfra.

## Tool Name Selection

| What you are resolving | Use `-tool` |
|---|---|
| VCS, UVM, Denali, SAOLA, VIPCAT | `vcssim` |
| MPP simulation tools | `vcssimmpp` |
| Backend infra, rails, voltage | `backend` |
| DVT analysis flow | `dvt` |
| Other flows | flow directory name under `verif/` or `flows/` |

## Verified Commands (MEMSS Workspace)

```bash
cth_query -tool vcssim ENVS VCS_HOME -resolve -q
cth_query -tool vcssim ENVS UVM_HOME -resolve -q
cth_query -tool vcssim TOOLVERSION vipcat -resolve -q
cth_query -tool backend PARAMS voltage_conditions_root -resolve -q
cth_query -tool backend PARAMS rails_xml -resolve -q
cth_query -tool vcssim -source ENVS UVM_HOME
cth_query -tool vcssim ENVS UVM_HOME -resolve_path -q
```

## Output Interpretation

- `-resolve` returns the active CTH value (often workspace-relative).
- `-resolve_path` returns an absolute filesystem path.
- `-source` returns where the key is defined in CTH files.

Use `-resolve` for authoritative flow values and only use `-resolve_path` when
an absolute path is required for filesystem checks.

## Fallback: Reading `tool.cth`

Fallback is appropriate only when:

- `cth_query` cannot answer the question (for example, listing all keys in a section)
- You need dependent-variable structure from a CTH block
- The command returns empty and you are diagnosing tool/key mismatches

Find candidate files:

```bash
find $WORKAREA -path '*/tool.cth' 2>/dev/null | head -40
```

Common locations:

```text
$WORKAREA/verif/<flow>/tool.cth
$WORKAREA/flows/<flow>/tool.cth
$WORKAREA/tool.cth
```

## Never Rules

- Never manually parse `tool.cth` first when `cth_query` can resolve it.
- Never hardcode resolved paths in code/docs.
- Never treat `-resolve` and `-resolve_path` as interchangeable.
- Never assume an empty query means key/tool absence before checking spelling/tool scope.
- Never hardcode `-tool vcssim` for all flows.
- Never hardcode the absolute binary path to `cth_query`.

## Do Not Use For

- Runtime compile/sim failure debugging once active tool path is already known.
- Inferring intended upgrade direction from source history.
