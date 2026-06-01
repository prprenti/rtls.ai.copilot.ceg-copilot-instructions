# Repo to FBI Conversion Reference

Use this reference when converting a repository from list-file based integration to FBI templates.

## Security First Inputs

Config INI risk note:
- `config_<project>.ini` controls destination IPX library and Unix-group access.
- Incorrect values can expose proprietary IP to unauthorized groups.
- Never guess these values.

Before creating or modifying config files, collect and confirm:

1. Destination IPX library
2. Unix group for access control
3. Whether SIP and HIP content need different permissions

Do not proceed until these values are explicitly provided.

Use these required prompts before INI creation/update:
1. "What is the destination IPX library for this repo?"
2. "What Unix group should be used to secure content in this repo?"
3. "Do you need different permissions for HIP versus SIP content?"

## Conversion Checklist

1. Start from the bundled reference templates: [Makefile](Makefile), [Makefile.convert](Makefile.convert).
2. Create `integration/create_list_file/config_<project>.ini` with validated values.
3. Discover repo-specific `.list` files in `filelists/` (include `*hip.list`, `*sip.list`, `*vip.list`, and similar variants).
4. Run conversion using one method: convert each discovered file with `uv run skills/fbi/scripts/list_to_fqn.py -f <listfile>`, or update and run `Makefile.convert` with the same plugin-local script path.
5. Verify generated `.ipx` output and FQN extraction.
6. In `flows/grdlbuild/common/build.gradle.kts`, create the `create_list_files_*` BuildTask stages and update `moab` dependencies so MOAB relies on the create_list_files stage(s).
7. Run the new create_list_file stage via Build Run plugin Grdlbuild skill.
8. Remove migrated `.list` files and add `.gitignore` entries (for example, `filelists/**/*.list`) so `.list` files cannot be committed going forward.
9. Validate generated outputs/logs and check in FBI assets.

## Config INI File

The config INI controls migration behavior and security boundary.

Template:

```ini
[ipx#<section_name>]
    module_name = iplist.ipx
    jinja_var = <variable_name>
    mode = migrate
    dest_lib = <destination_ipx_library>
    unixgroup = <unix_group>
    skip_lineage_check = true
```

Field notes:

- `module_name`: use `iplist.ipx`
- `jinja_var`: Jinja variable used by template lines
- `mode`: typically `migrate`
- `dest_lib`: destination IPX library
- `unixgroup`: security group for migrated content
- `skip_lineage_check`: lineage behavior toggle

Example with two destinations:

```ini
[ipx#ttl]
    module_name = iplist.ipx
    jinja_var = ipx
    mode = migrate
    dest_lib = ttlh78
    unixgroup = ttlh78
    skip_lineage_check = true

[ipx#ttlbx]
    module_name = iplist.ipx
    jinja_var = bxipx
    mode = migrate
    dest_lib = ttlbxh78
    unixgroup = ttlbxh78
    skip_lineage_check = true
```

## Conversion Workflow

1. Start from the bundled reference templates:
    - [Makefile](Makefile)
    - [Makefile.convert](Makefile.convert)
2. Create `integration/create_list_file/config_<project>.ini` with validated values.
3. Discover all repo-specific list files first (names vary by repo). Search in `filelists/`
   for patterns like `*hip.list`, `*sip.list`, and `*vip.list` (and similar variants)
   before conversion.

```bash
find filelists -type f \( -name '*hip.list' -o -name '*sip.list' -o -name '*vip.list' \) | sort
```

4. Run conversion using one method:

- Direct per-file conversion:

```bash
uv run skills/fbi/scripts/list_to_fqn.py -f filelists/<name>.list
```

- Or update `Makefile.convert` script invocations to use the same plugin-local path and run that make target.

```bash
uv run skills/fbi/scripts/list_to_fqn.py -f <listfile>
```

5. Review generated templates and verify FQN extraction.

6. Add create_list_file stages in `flows/grdlbuild/common/build.gradle.kts` using the same local pattern as existing `BuildTask` entries in that file.

Stage-definition pattern to follow (do not copy an entire file; add/adjust only relevant stages):

```kotlin
task<BuildTask>("create_list_files_<scope>") {
    dut("<dut1>", "<dut2>")
    runDir("$WORKAREA")
    commandLine("/usr/bin/make -f $WORKAREA/integration/create_list_file/Makefile all LIST_TEMPLATES='<space-separated templates>'")
    useNBResource("MEM4G")
    setGkUtilsScalar("EARLY_KILL", "1")
}
```

MOAB/dependency wiring guidance:
- Locate the `moab` stage in the same `flows/grdlbuild/common/build.gradle.kts`.
- Update MOAB dependency (`dependsOn(...)`) to include the relevant `create_list_files_*` stage(s).
- Keep create_list_file stages in the same dependency chain that feeds work required before `moab`-dependent turnin/release checks.
- Follow existing in-file dependency style (`dependsOn("...")`) rather than introducing a new flow model.

7. Run the new stage through the Build Run plugin's Grdlbuild skill.
8. Remove migrated `.list` files and update `.gitignore` to block future `.list` commits.

```bash
cd "$WORKAREA"
find filelists -type f \( -name '*.list' \) -delete
printf '\nfilelists/**/*.list\n' >> .gitignore
```

9. Validate generated `.list` files and logs.
10. Check in FBI assets and template files.

## Verification

After conversion:

- Generated output exists under `$WORKAREA/filelists/`
- Logs exist under `$WORKAREA/output/fbi/`
- Template variable names match config sections
- Access control values map to intended library and unix group
- `.list` files are removed from source control paths and covered by `.gitignore`

## What create_list_file does

When the Gradle target runs, create_list_file:

1. Reads `.ipx` templates.
2. Parses Jinja FQN references.
3. Migrates referenced IPs per config INI.
4. Resolves FQN to local paths.
5. Writes rendered `.list` output files.
