# Employee Lookup Reference

This reference is the condensed deep-dive companion to the employee-lookup skill.
Use this file for quick command patterns, AGS handoffs, and troubleshooting.

## Execution Rules

- Run Python via UV.
- Use plugin-root-relative script paths for deployment portability.
- Preferred command prefix:

```bash
uv run skills/employee-lookup/employee_lookup.py
```

## Lookup Modes

### IDSID and WWID

```bash
# Single or comma-separated IDs (auto-detects IDSID vs WWID)
uv run skills/employee-lookup/employee_lookup.py -u jsmith
uv run skills/employee-lookup/employee_lookup.py -u 12345678
uv run skills/employee-lookup/employee_lookup.py -u jsmith,12345678,bjones
```

Detection rules:
- All digits -> WWID
- Contains letters -> IDSID

### PDL

```bash
uv run skills/employee-lookup/employee_lookup.py my-team-pdl
uv run skills/employee-lookup/employee_lookup.py my-team-pdl -k IDSID,BookName,DomainAddress -f table
```

### Email

```bash
uv run skills/employee-lookup/employee_lookup.py -e john.smith@intel.com
uv run skills/employee-lookup/employee_lookup.py -e john.smith@intel.com,jane.doe@intel.com -k WWID,IDSID
uv run skills/employee-lookup/employee_lookup.py --email-file emails.txt -k WWID
```

### File Input

```bash
uv run skills/employee-lookup/employee_lookup.py --file users.txt
uv run skills/employee-lookup/employee_lookup.py --file users.txt -k IDSID,BookName,DomainAddress -f csv
```

## Output and Keys

Output formats:

- csv (default)
- table
- json

List all keys:

```bash
uv run skills/employee-lookup/employee_lookup.py --list-keys
```

Common key sets:

- Identity: IDSID,WWID,BookName
- Contact: BookName,DomainAddress,PhoneNum,CellNum
- Org hierarchy: BookName,OrgUnitDescr,MgrName,GLDivisionDesc
- Cost center: IDSID,BookName,GLCostCenterCod,GLCostCenterDes
- AGS-ready: IDSID,WWID,DomainAddress

## AGS Handoff Patterns

For full approval and request workflows, pair this with the [AGS skill](../../ags/SKILL.md).

```bash
# Build AGS bulk-input user list from PDL
uv run skills/employee-lookup/employee_lookup.py my-team-pdl -k IDSID > users.txt
ags bulk request --name "Some-Role" --file users.txt --justification "..."

# Convert WWID export to IDSID list
uv run skills/employee-lookup/employee_lookup.py --file ags_export_wwids.txt -k IDSID > user_ids.txt
```

## Troubleshooting

If a command fails, check usage/options first:
the command layer supports `-h` (for example, `uv run skills/employee-lookup/employee_lookup.py -h`).
If key names are failing, run `uv run skills/employee-lookup/employee_lookup.py --list-keys`.

No matches:

- Verify ID/email spelling.
- Add BookName,TermDate to confirm inactive users.

Empty PDL results:

- Verify the exact group name.
- Confirm the group exists and has members.

Unknown key warnings:

- Use --list-keys and exact key names.

File errors:

- Check path/readability.
- Use one value per line in input files.

## Runtime Dependencies

- Access to Intel network
- /usr/intel/bin/cdislookup
- /usr/intel/bin/groupmembers (PDL mode)
- /opt/quest/bin/vastool (email resolution)
