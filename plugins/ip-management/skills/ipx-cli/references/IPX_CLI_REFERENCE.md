# IPX CLI Reference

### IPX Client Setup (REQUIRED)

```bash
source /p/ipx/cad/ipxclient/prod/setup/ph3_ipxclient.setup
```

## Scope and Routing

- Use this reference for full `ipx` operational detail.
- Prefer `ip_release` skill for upload/release workflows.
- Prefer FBI skill for local migration/cache-oriented workflows.

---

## Safety Policy and Approval Gate

Many `ipx` commands are state-modifying and can have information security
impact. Treat them as irreversible unless proven otherwise.

### Safe Commands (read-only, no approval needed)

| Command | Why it's safe |
|---|---|
| `ipx ip compare` | Read-only comparison |
| `ipx ip lineage` | Read-only lineage tracing |
| `ipx ip sitesync` | Pushes existing data to remote BIC caches |
| `ipx ip getbom` | Read-only BOM query |
| `ipx ip manifest` | Read-only manifest generation |
| `ipx ip tree` | Read-only BOM hierarchy display |
| `ipx settings` | Read-only environment report |
| `ipx job list / status` | Read-only job queries |
| `ipx workspace list` | Read-only workspace listing |
| Any command with `-h` | Help text only |

### Destructive Commands (require explicit approval)

Before executing any destructive command, the assistant must:

1. Show the exact command.
2. Explain intended effect.
3. Warn that the action is destructive/irreversible.
4. Remind user to use `ip_release` for uploads and FBI for migration flows.
5. Wait for explicit user confirmation.

| Command | Risk |
|---|---|
| `ipx ip upload` | Overwrites files; creates new immutable FQN |
| `ipx ip create` | Wrong permissions can expose restricted data |
| `ipx ip branch` | BOM/permission inheritance may be incorrect |
| `ipx ip release` | Cannot be un-released |
| `ipx ip migrate` | Wrong target causes namespace pollution |
| `ipx ip editbom` | Can break downstream consumers |
| `ipx ip editperm` | Security-critical permission changes |
| `ipx ip download` | Can overwrite local files |
| `ipx ip siterm` | Consumers may lose cached data access |
| `ipx admin syncperm` | Security-critical bulk permission sync |

## IP FQN (Fully Qualified Name)

All IPX commands that accept IP identifiers operate on **FQNs**. Parameters
named `REF`, `CMP`, `IPS`, `IP`, and `source_fqn` all refer to FQNs.

FQN syntax: `<library>.<ip_name>@<version>.<branch>`

For full FQN syntax details, see the FBI skill's reference.

---

## Global Options

| Option | Description |
|---|---|
| `-h, --help` | Show help message |
| `-verbose, --verbose` | Show verbose messaging |
| `-logfile LOGFILE` | Set logfile (use `'none'` to disable) |
| `-quiet, --quiet` | Only display warning and higher |
| `-scratch-dir SCRATCH_DIR` | Alternate staging directory |
| `--save_api_calls FILE` | Save API calls for debug/replay |

---

## Top-Level Commands

```
ipx {admin,ip,job,login,settings,workspace} [options]
```

| Command | Description |
|---|---|
| `admin` | Admin commands (e.g., permission sync) |
| `ip` | Commands that operate on IPs (primary group) |
| `job` | Job queue management |
| `login` | Login to Pi and P4 |
| `settings` | Report current environment |
| `workspace` (`ws`) | Manipulate Percipient workspaces |

---

## `ipx ip compare`

Compare two IP versions or an IPV against a local path.

**Aliases:** `ipx ip diff`

```
ipx ip compare -reference <IPV> -compare <IPV> [options]
ipx ip compare -reference <IPV> -path <local_path> [options]
```

| Option | Description |
|---|---|
| `-reference REF` | FQN of the baseline |
| `-compare CMP` / `-cmp CMP` | FQN to compare against |
| `-path PATH` | Compare IPV to a local path |
| `-format {json,text}` | Output format (default: text) |
| `-exclude EXPR [...]` | Regex to exclude paths |
| `-outfile OUTFILE` | Write output to file |
| `-file` | List file diffs |
| `-perm` | List permission diffs |
| `-prop` | List property diffs |
| `-unixgroup` | List unixgroup diffs |
| `-bom` | List BOM diffs |
| `-paranoid` | Force MD5 comparison |

### Examples

```bash
# Compare two versions
ipx ip compare -reference mylib.myip@1.0.main -compare mylib.myip@2.0.main -file -bom

# Compare against local directory
ipx ip compare -reference mylib.myip@1.0.main -path /path/to/local -file

# Exclude test dirs, JSON output
ipx ip compare -reference mylib.myip@1.0.main -compare mylib.myip@2.0.main -file -exclude ".*test.*" -format json

# Write to file
ipx ip compare -reference mylib.myip@1.0.main -compare mylib.myip@2.0.main -file -bom -prop -outfile report.txt

# Paranoid (MD5) comparison
ipx ip compare -reference mylib.myip@1.0.main -compare mylib.myip@2.0.main -file -paranoid
```

### Diff Categories

- `-file` — File content differences
- `-bom` — BOM (child IP resources) differences
- `-perm` — Permission (ACL) differences
- `-prop` — Property (metadata) differences
- `-unixgroup` — Unix group ownership differences

---

## `ipx ip lineage`

Trace lineage (ancestry/descendancy) of IP versions.

```
ipx ip lineage -ip <IPV> [IPV ...] [options]
```

| Option | Description |
|---|---|
| `-ip IP [...]` | FQNs to trace |
| `-ancestors` | Find ancestors (default) |
| `-descendants` | Find descendants |
| `-allver` | Show all intermediate versions |
| `-trunk` | Show TRUNK lines |
| `-format {text,json,flatjson}` | Output format |

### Examples

```bash
ipx ip lineage -ip mylib.myip@3.0.main
ipx ip lineage -ip mylib.myip@1.0.main -descendants
ipx ip lineage -ip mylib.myip@3.0.main -ancestors -allver
ipx ip lineage -ip mylib.myip@3.0.main -trunk
ipx ip lineage -ip mylib.myip@3.0.main -ancestors -format json
ipx ip lineage -ip mylib.ip_a@1.0.main mylib.ip_b@2.0.dev
```

### Understanding Output

- **Ancestors** — traces backwards to the origin
- **Descendants** — traces forwards to all derived branches/versions
- **`-allver`** — shows every version (not just branch-points)
- **`-trunk`** — includes TRUNK line info

---

## `ipx ip sitesync`

Push IP data to other sites' BIC (Build IP Cache).

```
ipx ip sitesync -ips <IP> [IP ...] -sites <SITE> [SITE ...] [options]
ipx ip sitesync -csv <csvfile> [options]
```

| Option | Description |
|---|---|
| `-ips IPS [...]` | FQNs to sync |
| `-sites SITES [...]` | Target sites |
| `-wait` | Wait for completion |
| `-csv CSV` | CSV file for batch ops |

### CSV Format

```csv
fqn,sites
mylib.myip@line,site1 site2
```

### Examples

```bash
ipx ip sitesync -ips mylib.myip@main -sites sc
ipx ip sitesync -ips mylib.myip@main -sites sc fm pg
ipx ip sitesync -ips mylib.ip_a@main mylib.ip_b@main -sites sc fm -wait
ipx ip sitesync -csv sync_manifest.csv -wait
```

---

## Destructive / State-Modifying IP Subcommands

> **WARNING:** All commands below modify state. Do not run without explicit
> user approval. Use `ip_release` for uploads and `FBI` for migration.

### `ipx ip branch`

Branch an existing IP to create a new line.

```
ipx ip branch -ip <IP> -newline <NAME> [options]
```

| Option | Description |
|---|---|
| `-ip IP` | IP to branch |
| `-newline NEWLINE` | New line name |
| `-prefix PREFIX` | Prefix for new line |
| `-hier` | Branch all child resources |
| `-release / -no-release` | Release after creation |
| `-files FILES` | Directory of files to install |
| `-bom BOM [...]` | Attach child IPs |
| `-csv CSV` | CSV for batch branching |

### `ipx ip create`

Create a new IP.

```
ipx ip create -ip <lib.ipname[@line]> [options]
```

| Option | Description |
|---|---|
| `-ip IP` | IP to create |
| `-dm-type {P4,CONT,FS}` | VCS system |
| `-template {hip,sip,vip}` | IP template type |
| `-release / -no-release` | Release after creation |
| `-files FILES` | Directory of files |
| `-bom BOM [...]` | Attach child IPs |
| `-prop KEY=VAL [...]` | Set properties |

### `ipx ip upload`

Upload files to an existing IP line.

```
ipx ip upload -ip <IP> -files <DIR> [options]
```

| Option | Description |
|---|---|
| `-ip IP` | IP to upload |
| `-files FILES` | File directory |
| `-incremental` | Don't remove existing files first |
| `-release [{ifchanged}]` | Release after upload |
| `-allow-duplicate` | Allow duplicate upload |

### `ipx ip setprop`

Set properties on IPs.

```
ipx ip setprop -ip <IP> [...] -prop <KEY=VALUE> [...]
```

### `ipx ip migrate`

Migrate (duplicate) an IP to a target line.

**Aliases:** `ipx ip duplicate`

```
ipx ip migrate -source_fqn <FQN> -target_ipl <target_line> [options]
```

| Option | Description |
|---|---|
| `-source_fqn IP` | Source FQN |
| `-target_ipl TARGET` | Target IP line |
| `-extract` | Extract files during migration |
| `-nowait` | Don't wait for server-side completion |

### `ipx ip download`

Download IPs to a local path.

```
ipx ip download -ip <IP> -path <DIR> [options]
```

| Option | Description |
|---|---|
| `-ip IP` | IP to download |
| `-path PATH` | Root install directory |
| `-hierarchical` | Download child IPs |
| `-incremental` | Allow incremental |
| `-filter REGEX` | Filter files |

### `ipx ip editbom`

Edit the BOM for an IP.

```
ipx ip editbom -ip <IP> [-add FQN ...] [-remove FQN ...] [-set FQN ...]
```

### `ipx ip editperm`

Modify IP/IPL permissions.

```
ipx ip editperm -ip <IP> [-add PERM ...] [-set PERM ...] [-remove PERM ...]
```

Permission format: `[ug]:group[:rwo]`

| Option | Description |
|---|---|
| `-add / -change` | Add/change permissions |
| `-set` | Set exactly |
| `-remove` | Remove |
| `-hier` | Apply hierarchically |

### `ipx ip getbom`

```
ipx ip getbom -ip <IP> [-format {text,json,xml}]
```

### `ipx ip manifest`

```
ipx ip manifest -ip <IPV> [...] [-outfile FILE] [-format {json,xml,csv}]
```

### `ipx ip release`

Release an existing IP line.

```
ipx ip release -ip <IP> [options]
```

### `ipx ip siterm`

Remove IP from PiCache at specified sites.

```
ipx ip siterm -ips <IP> [...] -sites <SITE> [...] [-wait]
```

### `ipx ip tree`

List the IP tree (BOM hierarchy).

```
ipx ip tree -ip <IPV> [...] [-format {text,json}]
```

---

## Non-IP Commands

### `ipx login`

```
ipx login [-username USER] [-password PW] [-force] [-min-time-left TIME]
```

### `ipx settings`

```
ipx settings [-format {json,xml,text}]
```

### `ipx admin syncperm`

```
ipx admin syncperm -ip <IP> [...]
```

### `ipx job`

| Subcommand | Description |
|---|---|
| `ipx job list [-all] [-state {pending,running,completed}]` | List jobs |
| `ipx job status -jobid <ID> [...]` | Query job status |
| `ipx job rerun -jobid <ID> [...]` | Rerun failed jobs |

### `ipx workspace`

| Subcommand | Description |
|---|---|
| `ipx workspace list [-ws WS ...] [-user USER]` | List workspaces |
| `ipx workspace remove [-ws WS ...] [-auto] [-remove]` | Remove stale workspaces |

**Aliases:** `ipx ws list`, `ipx ws rm`
