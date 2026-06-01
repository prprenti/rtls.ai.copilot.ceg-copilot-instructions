---
name: register-topology
description: Locate registers and fields from generated CRIF topology using the crifd_query API. Use when you need canonical register names, address reverse lookup, or field decode from generated topology.
keywords: crif, register, crifd, topology, canonical name, address, field, decode, lookup, spec2crif, crifxml
mcp_tools: validation/crifd_query
---

# Register Topology Skill

> PURPOSE: Locate registers, discover canonical names, reverse-map addresses, and decode field values from generated CRIF topology.
> WHEN TO USE: Apply before editing register names, validating lookup strings, reverse-mapping programmed addresses, or decoding field values from generated topology output.

**MCP-First Rule:** ALWAYS use the `crifd_query` MCP tool.
NEVER instruct users to call `crifd_query.py` by path from this skill.

The examples below document `crifd_query` tool parameters and expected usage patterns.

## Finding the CRIF File

Before querying, locate the generated CRIF XML or database:

```bash
# Search the full workspace for generated CRIF files
find $WORKAREA \( -name '*.crif.xml' -o -name 'spec2crif*.xml' -o -name '*crif*.xml' -o -name '*.crif.db' \) 2>/dev/null | head -20

# Alternative: use ripgrep for speed
rg --files $WORKAREA | rg 'spec2crif\..*\.xml$|crif\.xml$|\.crif\.db$'
```

If no generated CRIF exists, the register topology is not available in the current workspace or release model. Some released models do not ship CRIF artifacts even when source/register content is present. In that case, stop and state clearly that CRIF/spec2uvm output must be generated or sourced from another build area before the API can query topology.

Do not guess register names from hand-edited source code.

## Routing Guidance

- Use the `crifd_query` MCP tool for exact lookup, discovery, address mapping, and field decode.
- For broad discovery queries, pass `omit_expensive_register_columns=True` and/or `omit_expensive_field_columns=True` to drop verbose columns (Description, RTL_Path, Register_File, Ral_File, Fabric, Scope, FID) without manually enumerating a `columns` list. Explicit `columns`/`field_columns` args always take precedence over these flags.
- Use this skill when the question is about generated register topology: exact names, replicated instances, addresses, fields, and access-path disambiguation.
- Do not use this skill to explain architectural intent from the spec alone; topology answers what was generated, not why the design chose it.
- Do not use this skill to validate runtime programming sequences once the register name is already known.

## Fastest Safe Path

- Use the `crifd_query` MCP tool directly.
- Keep the same proof rule: partial or address-based discovery first, exact confirmation before you change code or configuration.
- Keep the CRIF artifact path and exact register name visible in your answer.

## Decision Tree

**Goal — does this exact register lookup exist?**
  Use `crifd_query(crif=..., query=..., exact=True, first=True, columns="FName,Address,Port_ID", no_fields=True)`.

- Match found = canonical name is valid in current generated output.
- No match = naming mismatch. Discover the correct name before editing code.

**Goal — what is the canonical generated name?**
  Use `crifd_query(crif=..., query=..., names_only=True, limit=20)` with a token or fragment.

- Read the returned family of names before choosing a specific instance.
- Then confirm with `exact=True` on your chosen candidate.

**Goal — I only know the address:**
  Use `crifd_query(crif=..., query="0x...", address=True, first=True, no_fields=True)`.

- Then rerun on the discovered name for fields and details.

**Goal — decode this programmed value into fields:**
  First confirm the register with `exact=True` or `first=True`.
  Then use `crifd_query(..., value="0x...", short=True)` to decode.

**Goal — the result set is very large:**
  Start with `names_only=True`.
  Narrow with a longer suffix, regex, or grep filtering.
  Use `first=True` only once you understand the replication pattern.

## Core Workflows

### 1. Validate a register lookup before test or sim

```text
crifd_query(
  crif="<crif_xml>",
  query="<full_register_name>",
  exact=True,
  first=True,
  columns="FName,Address,Port_ID",
  no_fields=True
)
```

- Match = the current generated topology contains that exact name.
- No match = the name is stale, wrong, or targets the wrong instance family.

### 2. Discover the canonical instance family

```text
crifd_query(
  crif="<crif_xml>",
  query="<name_fragment>",
  names_only=True,
  limit=20,
  omit_expensive_register_columns=True
)
```

Use this when code contains shorthand names, when a token could map to channel/broadcast/arrayed instances, or when you need to understand the replication pattern.

### 3. Reverse-map an address to a register

```text
crifd_query(
  crif="<crif_xml>",
  query="0x<address>",
  address=True,
  first=True,
  no_fields=True
)
```

Useful when you have a programmed address from a log or waveform but need the register name.

### 4. Decode a value into fields

```text
crifd_query(
  crif="<crif_xml>",
  query="<register_name>",
  first=True,
  value="0x<hex>",
  short=True,
  columns="FName,Address",
  field_columns="Name,Range,Value"
)
```

Shows each field with its bit range and decoded value for the given register contents.

### 5. List all fields of a register

```text
crifd_query(
  crif="<crif_xml>",
  query="<register_name>",
  exact=True,
  first=True
)
```

The default output includes all fields with their bit ranges, access modes, and reset values.

## Topology Interpretation Rules

- **Repeated names indicate replication**, not duplicate noise. Channels, ranks, and array indices create multiple instances of the same logical register.
- **`BROADCAST` is not proof that a single-instance lookup is correct.** Broadcast and concrete per-instance registers are different topology targets.
- **Bracketed suffixes** like `[0]` and `[1]` often matter for the final canonical name. Do not drop them.
- **`Port_ID` differences** can distinguish otherwise identical-looking hits that sit on different access paths.
- **A short token match is discovery evidence, not edit-ready evidence.** Always confirm with `exact=True` before using a name in code or test configuration.

Working rule:

- partial search discovers families
- exact search proves the final string

## NEVER Rules

- NEVER use `first=True` on an ambiguous short token as your first query. It can validate the wrong replicated instance and turn a naming guess into a false positive.
- NEVER treat a `names_only=True` hit as proof. Discovery and proof are separate steps: discover with a partial token, then prove with `exact=True` on the final candidate.
- NEVER let the API hide the final proof step. Even when discovery is structured, the chosen register name still needs exact confirmation against generated topology.
- NEVER accept a `BROADCAST` hit as evidence for a per-instance path. Broadcast and concrete instances are different topology targets and often imply different programming intent.
- NEVER patch a register name from intuition after an exact-match failure. Re-run discovery and adopt the canonical generated name from CRIF output.
- NEVER blame code or lookup logic when the CRIF artifact is missing. Missing generated output is a workspace/state problem, not a topology answer.
- NEVER hardcode CRIF file paths into the skill flow. CEG repos and build variants place generated CRIF in different locations, so discovery must stay dynamic.

## Do NOT Use For

- Do not use this skill for spec-only questions where no generated CRIF exists.
- Do not use this skill as proof that software or TB programming matched expectations after writes were issued.

## Error Handling

| Symptom | Likely Cause | Action |
| ------- | ------------ | ------ |
| No matches for an exact name | Name is stale or wrong | Re-run `crifd_query` with `names_only=True` and a shorter token to discover the current canonical name |
| Too many matches | Token is too short or ambiguous | Add more of the suffix, use a longer fragment, or filter with grep |
| `crifd` command not found | Cheetah environment not sourced | Source the workspace environment or verify `hive` is on `PATH` |
| CRIF file not found | Workspace or release model does not ship generated CRIF | Regenerate CRIF/spec2uvm output or use a build area that contains generated CRIF |
