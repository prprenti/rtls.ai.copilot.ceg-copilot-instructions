# FQN Pointer Update Reference

Use this reference when updating existing FBI templates and regenerating list output.

## Route Through Build Run Grdlbuild Skill

`create_list_file` is a Gradle build target. Route execution through the
Build Run plugin's Grdlbuild skill.

Use that skill to run your repo's create_list_file target via `run_grdlbuild`.

## Update an FQN Pointer

Pointer-only scope rule:
- Do not create or modify `config_<project>.ini` in this workflow.
- If INI changes are needed, load and follow `Repo to FBI Conversion Reference` first.

1. Identify the current FQN in the `.ipx` file.
2. Determine the new FQN from the IP provider or by running:

```bash
ipx ip lineage -ip <old_fqn> -descendants
```

3. Replace only the FQN inside `{{ ipx['...'] }}`.
4. Regenerate via the create_list_file Gradle target.
5. Review logs under `$WORKAREA/output/fbi/`.

## `.ipx` Template Formats

### SIP/RTL line format

```text
<ip_name>,{{ ipx['<library>.<ip_name>@<version>.<branch>'] }}[/optional/subpath],<library_name>
```

### HIP line format

```text
<ip_name>,{{ ipx['<FQN>'] }}[/subpath],<library_name>,{{ ipx['<FQN>'] }}@:<module_name>
```

### Non-FQN and comment lines

- Non-FQN lines can remain plain paths.
- Comment lines start with `#`.

## FQN Notes

FQN syntax:

```text
<library_name>.<ip_name>@<version_number>.<branch_name>
```

New branch syntax (first upload):

```text
<library_name>.<ip_name>@.<branch_name>
```

FQNs are immutable. Any modification creates a new versioned FQN.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `IPHANDOFF_EXEC` is empty | Verify CTH setup and check `cth_query -tool create_list_file` values. |
| `ipx` not found | Source your project's IPX client setup and verify `ipx` is on `PATH`. |
| Migration fails for an FQN | Verify lineage with `ipx ip lineage -ip <FQN>`. |
