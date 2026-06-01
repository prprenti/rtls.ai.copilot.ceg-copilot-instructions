#!/usr/bin/env python3
"""crifd_query.py — Structured JSON wrapper for `hive crifd`.

Usage:
  crifd_query.py --crif PATH --query TOKEN [OPTIONS]

Query mode (mutually exclusive):
  --exact      exact name match
  --regex      case-insensitive regex (forwarded to hive crifd -regex)
  --address    address lookup (e.g. 0xe190)
  (default)    prefix / startswith match

Output options:
  --names-only              list matching register names only (no table)
  --first                   limit output to the first match
  --limit N                 cap returned results while preserving total_count
  --value 0xHEX             decode field values for this register value
  --no-fields               omit field detail (passes -remove_fields to crifd)
  --columns COL[,COL]       keep only these register-level columns in JSON
  --field-columns COL[,COL] keep only these field-level columns in JSON
  --pid 0xNN                filter by port ID
  --short                   suppress descriptions
  --omit-expensive-register-columns
                            strip Description, RTL_Path, Register_File, Ral_File, Fabric, Scope,
                            FID from register output (no-op when --columns is specified)
  --omit-expensive-field-columns
                            strip Description from field output (no-op when --field-columns is specified)
  --indent N                JSON indent width (0 = compact; default 2)
  --timeout N               helper timeout in seconds (default 10)

Exit codes:
  0  matches found
  1  no matches
  2  crifd error / invocation failure
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from itertools import pairwise

_EXPENSIVE_REGISTER_COLUMNS: frozenset[str] = frozenset({
    "Description", "RTL_Path", "Register_File", "Ral_File", "Fabric", "Scope", "FID",
})
_EXPENSIVE_FIELD_COLUMNS: frozenset[str] = frozenset({"Description"})


def _split_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _col_spans(sep_line: str) -> list[tuple[int, int]]:
    """Return list of (left_plus, right_plus) index pairs for each column."""
    positions = [index for index, char in enumerate(sep_line) if char == "+"]
    return list(pairwise(positions))


def _extract_raw(line: str, span: tuple[int, int]) -> str:
    """Return raw (unstripped) cell content between two + positions."""
    left, right = span
    if left + 1 >= len(line):
        return ""
    return line[left + 1:right]


def _smart_join(accumulated: str, new_part: str) -> str:
    """Join wrapped cell segments without damaging identifiers and prose."""
    if not accumulated:
        return new_part
    if " " in accumulated or " " in new_part:
        return accumulated + " " + new_part
    if accumulated[-1] in "_.[" or (new_part and new_part[0] in "_."):
        return accumulated + new_part
    return accumulated + " " + new_part


def _parse_table_block(lines: list[str]) -> list[dict[str, str]]:
    """Parse one ASCII box-drawing table into a list of row dicts."""
    lines = [line for line in lines if line.strip()]
    separator_indexes = [index for index, line in enumerate(lines) if line.startswith("+")]
    if not separator_indexes:
        return []

    spans = _col_spans(lines[separator_indexes[0]])
    if not spans:
        return []

    equal_index = next(
        (index for index, line in enumerate(lines) if line.startswith("+") and "=" in line),
        None,
    )
    if equal_index is None:
        return []

    close_index = next(
        (index for index in range(equal_index + 1, len(lines)) if lines[index].startswith("+")),
        len(lines),
    )

    first_plus = separator_indexes[0]
    header_lines = [line for line in lines[first_plus + 1:equal_index] if line.startswith("|")]
    headers = ["" for _ in spans]
    for line in header_lines:
        for index, span in enumerate(spans):
            raw = _extract_raw(line, span).strip()
            if raw:
                headers[index] = _smart_join(headers[index], raw)

    data_lines = [line for line in lines[equal_index + 1:close_index] if line.startswith("|")]
    if not data_lines:
        return []

    row_groups: list[list[str]] = []
    current: list[str] = []
    for line in data_lines:
        second_column = _extract_raw(line, spans[1]).strip() if len(spans) > 1 else ""
        if second_column and current:
            row_groups.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        row_groups.append(current)

    result: list[dict[str, str]] = []
    for group in row_groups:
        cells = ["" for _ in spans]
        for line in group:
            for index, span in enumerate(spans):
                raw = _extract_raw(line, span).strip()
                if raw:
                    cells[index] = _smart_join(cells[index], raw)
        result.append(dict(zip(headers, cells, strict=False)))

    return result


def _find_table_end(lines: list[str], start: int) -> int:
    """Return the index just past the closing +---+ of a table."""
    found_equal = False
    for index in range(start, len(lines)):
        if lines[index].startswith("+") and "=" in lines[index]:
            found_equal = True
        elif lines[index].startswith("+") and found_equal:
            return index + 1
    return len(lines)


def _parse_output(
    text: str,
    include_fields: bool,
    columns: list[str] | None,
    field_columns: list[str] | None,
    short: bool,
    limit: int | None,
    omit_expensive_reg_columns: bool = False,
    omit_expensive_field_columns: bool = False,
) -> dict[str, object]:
    """Convert raw crifd stdout into a structured dict."""
    lines = [line for line in text.splitlines() if not line.startswith("CACHE:")]

    if not any(line.startswith("+") for line in lines):
        names = [line.strip() for line in lines if line.strip()]
        total_count = len(names)
        if limit is not None:
            names = names[:limit]
        return {
            "mode": "names_only",
            "names": names,
            "count": len(names),
            "total_count": total_count,
        }

    column_set = set(columns) if columns else None
    field_column_set = set(field_columns) if field_columns else None
    registers: list[dict[str, object]] = []
    index = 0

    while index < len(lines):
        if lines[index].strip() != "Register":
            index += 1
            continue

        register_start = index + 1
        register_end = _find_table_end(lines, register_start)

        register_rows = _parse_table_block(lines[register_start:register_end])
        register_record = register_rows[0] if register_rows else {}
        if column_set:
            register_record = {key: value for key, value in register_record.items() if key in column_set}
        elif omit_expensive_reg_columns:
            register_record = {key: value for key, value in register_record.items() if key not in _EXPENSIVE_REGISTER_COLUMNS}

        next_index = register_end
        while next_index < len(lines) and not lines[next_index].strip():
            next_index += 1

        fields_data: list[dict[str, str]] = []
        if next_index < len(lines) and lines[next_index].strip() == "Fields":
            fields_start = next_index + 1
            fields_end = _find_table_end(lines, fields_start)
            if include_fields:
                fields_data = _parse_table_block(lines[fields_start:fields_end])
                if short:
                    for field in fields_data:
                        field.pop("Description", None)
                if field_column_set:
                    fields_data = [
                        {key: value for key, value in field.items() if key in field_column_set}
                        for field in fields_data
                    ]
                elif omit_expensive_field_columns:
                    fields_data = [
                        {key: value for key, value in field.items() if key not in _EXPENSIVE_FIELD_COLUMNS}
                        for field in fields_data
                    ]
            index = fields_end
        else:
            index = next_index

        entry = dict(register_record)
        if include_fields:
            entry["fields"] = fields_data
        registers.append(entry)

    total_count = len(registers)
    if limit is not None:
        registers = registers[:limit]

    return {
        "registers": registers,
        "count": len(registers),
        "total_count": total_count,
    }


def _build_cmd(args: argparse.Namespace) -> list[str]:
    cmd = ["hive", "crifd", "-crif", args.crif, args.query]
    if args.exact:
        cmd.append("-exact")
    if args.regex:
        cmd.append("-regex")
    if args.address:
        cmd.append("-address")
    if args.names_only:
        cmd.append("-print_names_only")
    if args.first:
        cmd.append("-first")
    if args.value:
        cmd += ["-value", args.value]
    if args.short:
        cmd.append("-short")
    if args.no_fields:
        cmd.append("-remove_fields")
    if args.pid:
        cmd += ["-pid", args.pid]
    return cmd


def _emit_error_json(
    message: str,
    cmd: list[str],
    indent: int,
    query: str | None = None,
    crif: str | None = None,
    returncode: int | None = None,
    stdout: str | None = None,
    stderr: str | None = None,
) -> None:
    payload: dict[str, object] = {
        "error": message,
        "cmd": cmd,
    }
    if query is not None:
        payload["query"] = query
    if crif is not None:
        payload["crif"] = crif
    if returncode is not None:
        payload["returncode"] = returncode
    if stdout:
        payload["stdout"] = stdout
    if stderr:
        payload["stderr"] = stderr
    print(json.dumps(payload, indent=indent or None))


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--crif", required=True, metavar="PATH", help="CRIF XML or DB file path")
    parser.add_argument("--query", required=True, metavar="TOKEN", help="Register name, fragment, regex, or hex address")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--exact", action="store_true", help="Exact name match")
    mode.add_argument("--regex", action="store_true", help="case-insensitive regex (forwarded to hive crifd -regex)")
    mode.add_argument("--address", action="store_true", help="Lookup by hex address (e.g. 0xe190)")

    parser.add_argument("--names-only", action="store_true", help="Return matching register names only")
    parser.add_argument("--first", action="store_true", help="Limit to first match")
    parser.add_argument("--limit", type=int, metavar="N", help="Cap returned results while preserving total_count")
    parser.add_argument("--value", metavar="0xHEX", help="Decode field values for this raw register value")
    parser.add_argument("--no-fields", action="store_true", help="Omit field detail from output")
    parser.add_argument("--columns", metavar="COL[,COL]", help="Comma-separated register-level columns to keep (e.g. FName,Address,Port_ID,Register_File)")
    parser.add_argument("--field-columns", metavar="COL[,COL]", help="Comma-separated field-level columns to keep (e.g. Name,Range,Access,Value)")
    parser.add_argument("--pid", metavar="0xNN", help="Filter by port ID")
    parser.add_argument("--short", action="store_true", help="Suppress descriptions")
    parser.add_argument("--omit-expensive-register-columns", action="store_true", help="Strip Description, RTL_Path, Register_File, Ral_File, Fabric, Scope, FID from register output (no-op when --columns is specified)")
    parser.add_argument("--omit-expensive-field-columns", action="store_true", help="Strip Description from field output (no-op when --field-columns is specified)")
    parser.add_argument("--indent", type=int, default=2, metavar="N", help="JSON indent (0=compact, default 2)")
    parser.add_argument("--timeout", type=int, default=10, metavar="SECONDS", help="Command timeout in seconds (default 10)")
    args = parser.parse_args()

    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be >= 0")
    if args.indent < 0:
        parser.error("--indent must be >= 0")
    if args.timeout <= 0:
        parser.error("--timeout must be > 0")

    columns = _split_csv(args.columns)
    field_columns = _split_csv(args.field_columns)
    cmd = _build_cmd(args)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout, check=False)
    except FileNotFoundError:
        _emit_error_json("hive crifd not found in PATH", cmd, args.indent)
        sys.exit(2)
    except subprocess.TimeoutExpired:
        _emit_error_json(f"hive crifd timed out after {args.timeout}s", cmd, args.indent)
        sys.exit(2)

    stdout = proc.stdout
    stderr = proc.stderr.strip()
    no_match = "No registers were matched" in stdout or "No registers were matched" in stderr
    if no_match:
        if args.names_only:
            payload: dict[str, object] = {
                "mode": "names_only",
                "names": [],
                "count": 0,
                "total_count": 0,
                "query": args.query,
                "crif": args.crif,
            }
        else:
            payload = {
                "registers": [],
                "count": 0,
                "total_count": 0,
                "query": args.query,
                "crif": args.crif,
            }
        print(json.dumps(payload, indent=args.indent or None))
        sys.exit(1)

    if proc.returncode != 0:
        _emit_error_json(
            "hive crifd failed",
            cmd,
            args.indent,
            query=args.query,
            crif=args.crif,
            returncode=proc.returncode,
            stdout=stdout.strip(),
            stderr=stderr,
        )
        sys.exit(2)

    include_fields = not args.no_fields and not args.names_only
    parsed = _parse_output(
        stdout, include_fields, columns, field_columns, args.short, args.limit,
        omit_expensive_reg_columns=args.omit_expensive_register_columns,
        omit_expensive_field_columns=args.omit_expensive_field_columns,
    )
    parsed["query"] = args.query
    parsed["crif"] = args.crif
    print(json.dumps(parsed, indent=args.indent or None))

    if parsed.get("count", 0) == 0 and parsed.get("mode") != "names_only":
        sys.exit(1)


if __name__ == "__main__":
    main()