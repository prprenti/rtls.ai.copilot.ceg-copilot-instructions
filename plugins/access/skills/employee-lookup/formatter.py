"""
formatter.py - Output formatting and key validation for CDIS lookup results.

Extracted from employee_lookup.py to follow Single Responsibility Principle.
Each formatter is a strategy (Strategy Pattern) — easy to extend with
new formats without modifying existing code (Open/Closed Principle).
"""

from __future__ import annotations

import json
import sys
from abc import ABC, abstractmethod


# ---------------------------------------------------------------------------
# Constants (shared with employee_lookup.py)
# ---------------------------------------------------------------------------

AVAILABLE_KEYS = [
    "Agency", "BldgCode", "BookName", "ccMailName", "CellNum", "Department",
    "Dept", "Deptfunc", "DomainAddress", "Emptype", "Entity",
    "ExportCountryCo", "ExportCountryGr", "FaxNum", "Fname",
    "GLCostCenterCod", "GLCostCenterDes", "GLDivisionCode", "GLDivisionDesc",
    "GLGroupCode", "GLGroupDesc", "GLSuperGroupCod", "GLSuperGroupDes",
    "HomePageURL", "HrdName", "HrdWWID", "IDSID", "isCC", "LastUpdateDate",
    "Lname", "Location", "MailStop", "MgrName", "MgrWWID", "MI", "MsgNum",
    "Nickname", "OfficeLoc", "OrgUnitCode", "OrgUnitDescr", "PagerNum",
    "PhoneNum", "PostOffice", "Region", "SiteCode", "StatCode", "StatDate",
    "TermDate", "Worldwid", "WWID",
]

DEFAULT_KEYS = ["IDSID"]


def validate_keys(keys: list[str]) -> list[str]:
    """Validate requested keys against AVAILABLE_KEYS.  Warn on unknowns."""
    valid = []
    for k in keys:
        if k in AVAILABLE_KEYS:
            valid.append(k)
        else:
            print(f"Warning: Unknown key: {k}", file=sys.stderr)
    return valid if valid else list(DEFAULT_KEYS)


# ---------------------------------------------------------------------------
# Abstract formatter (Open/Closed Principle)
# ---------------------------------------------------------------------------

class ResultFormatter(ABC):
    """Base class for result formatters."""

    @abstractmethod
    def format(self, results: list[dict], keys: list[str]) -> str:
        """Return the formatted string for *results* restricted to *keys*."""


# ---------------------------------------------------------------------------
# Concrete formatters
# ---------------------------------------------------------------------------

class CsvFormatter(ResultFormatter):
    """Comma-separated values."""

    def format(self, results: list[dict], keys: list[str]) -> str:
        if not results:
            return ""
        lines = [",".join(keys)]
        for row in results:
            lines.append(",".join(str(row.get(k, "")) for k in keys))
        return "\n".join(lines)


class TableFormatter(ResultFormatter):
    """Human-readable aligned table."""

    def format(self, results: list[dict], keys: list[str]) -> str:
        if not results:
            return ""
        widths = {
            k: max(len(k), max((len(str(r.get(k, ""))) for r in results), default=0))
            for k in keys
        }
        lines = [
            " | ".join(k.ljust(widths[k]) for k in keys),
            "-+-".join("-" * widths[k] for k in keys),
        ]
        for row in results:
            lines.append(" | ".join(str(row.get(k, "")).ljust(widths[k]) for k in keys))
        return "\n".join(lines)


class JsonFormatter(ResultFormatter):
    """JSON array of objects."""

    def format(self, results: list[dict], keys: list[str]) -> str:
        if not results:
            return ""
        output = [{k: row.get(k, "") for k in keys} for row in results]
        return json.dumps(output, indent=2)


# ---------------------------------------------------------------------------
# Factory (avoids if/elif chains in callers)
# ---------------------------------------------------------------------------

_FORMATTERS: dict[str, type[ResultFormatter]] = {
    "csv": CsvFormatter,
    "table": TableFormatter,
    "json": JsonFormatter,
}


def get_formatter(format_type: str) -> ResultFormatter:
    """Return a formatter instance for *format_type*.

    Raises ValueError for unknown types.
    """
    cls = _FORMATTERS.get(format_type)
    if cls is None:
        raise ValueError(
            f"Unknown format '{format_type}'. "
            f"Choose from: {', '.join(_FORMATTERS)}"
        )
    return cls()


def format_results(results: list[dict], keys: list[str], format_type: str = "csv") -> str:
    """Convenience wrapper: format *results* and return the string."""
    return get_formatter(format_type).format(results, keys)


def output_results(results: list[dict], keys: list[str], format_type: str = "csv") -> str:
    """Format, print, and return the results string (CLI convenience)."""
    text = format_results(results, keys, format_type)
    if text:
        print(text)
    return text
