#!/usr/bin/env python3
# ------------------------------------------------------------------------------
# employee_lookup.py - Intel CDIS Employee Lookup Utility (Python port)
# Copyright 6/13/19 by Intel Corporation.
# This information is the confidential and proprietary property of Intel
# Corporation and the possession or use of this file requires a written license
# from Intel Corporation.
# ------------------------------------------------------------------------------
#
# Usage:
#   employee_lookup.py <PDL_NAME> [-k key1,key2,key3] [-d] [-f csv|table|json]
#   employee_lookup.py -u <ID1,ID2,ID3> [-k key1,key2,key3] [-d] [-f csv|table|json]
#   employee_lookup.py --file <filename> [-k key1,key2,key3] [-d] [-f csv|table|json]
#   employee_lookup.py -e <email1,email2,...> [-k key1,key2,key3] [-d] [-f csv|table|json]
#   employee_lookup.py --email-file <filename> [-k key1,key2,key3] [-d] [-f csv|table|json]
#   employee_lookup.py --list-keys
#
# Options:
#   -u, --users ID1,ID2     Comma-separated list of IDs (auto-detects WWID vs IDSID)
#   --file <filename>       Read IDs from file (one per line, auto-detects type)
#   -e, --emails E1,E2      Comma-separated list of email addresses
#   --email-file <filename> Read email addresses from file (one per line)
#   -k, --keys KEY1,KEY2    Comma-separated list of keys to output
#   -d, --debug             Enable debug output
#   -f, --format FORMAT     Output format: csv, table, json (default: csv)
#   --list-keys             List all available CDIS keys
#   -h, --help              Show this help message
#
# ID Auto-Detection:
#   - All digits (e.g., 12345678) → treated as WWID
#   - Contains letters (e.g., jsmith) → treated as IDSID
#
# Examples:
#   employee_lookup.py myteam-pdl
#   employee_lookup.py myteam-pdl -k IDSID,DomainAddress,MgrName
#   employee_lookup.py -u jsmith -k WWID,DomainAddress,GLCostCenterDes -f table
#   employee_lookup.py -u jsmith,bjones,kwilson -k BookName,DomainAddress
#   employee_lookup.py -u 12345678,23456789 -k IDSID,BookName
#   employee_lookup.py -u jsmith,12345678 -k IDSID,WWID,BookName  # Mixed types OK
#   employee_lookup.py --file users.txt -k IDSID,DomainAddress
#   employee_lookup.py -e john.smith@intel.com,jane.doe@corp.intel.com -k WWID,IDSID
#   employee_lookup.py --email-file emails.txt -k WWID,BookName
#   employee_lookup.py --list-keys

from __future__ import annotations

import argparse
import os
import re
import sys

# Add the directory containing this script to the path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from command_runner import CommandRunner, SubprocessCommandRunner
from formatter import (  # noqa: F401 – re-exported for backward-compat
    AVAILABLE_KEYS, # type: ignore
    DEFAULT_KEYS,
    output_results,
    validate_keys,
)


_LDAP_DOMAINS: list[str | None] = [
    None,
    "DC=ger,DC=corp,DC=intel,DC=com",
]

# ---------------------------------------------------------------------------
# Module-level default runner (created lazily so tests can override)
# ---------------------------------------------------------------------------
_default_runner: CommandRunner | None = None


def _get_default_runner() -> CommandRunner:
    """Return (and cache) the default SubprocessCommandRunner."""
    global _default_runner  # noqa: PLW0603
    if _default_runner is None:
        _default_runner = SubprocessCommandRunner()
    return _default_runner


# ---------------------------------------------------------------------------
# Pure helper functions
# ---------------------------------------------------------------------------


def is_wwid(identifier: str) -> bool:
    """Return True if identifier is all digits (WWID)."""
    return identifier.strip().isdigit()


def parse_cdis_output(cdis_str: str, identifier: str, verbose: bool = False) -> dict | None:
    """Parse key=value output from the cdislookup system command."""
    if "No matches" in cdis_str:
        print(f"Error: Could not find {identifier}", file=sys.stderr)
        return None

    data: dict[str, str] = {}
    for line in cdis_str.strip().split("\n"):
        if "=" in line:
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


def extract_idsid_from_vastool(vastool_output: str) -> str:
    """Extract a bare IDSID from vastool output like 'sAMAccountName: jsmith'."""
    idsid = vastool_output.strip()
    if ": " in idsid:
        idsid = idsid.split(": ", 1)[1].strip()
    return re.sub(r"^\w+:\s*", "", idsid).strip()


def normalise_email(email: str) -> str:
    """Normalize email for lookup without forcing intel.com domains.

    If no domain is provided, default to intel.com for convenience.
    """
    email = email.strip().lower()
    if "@" not in email:
        email += "@intel.com"
    return email


# ---------------------------------------------------------------------------
# Core lookup class (Dependency Injection via constructor)
# ---------------------------------------------------------------------------


class EmployeeLookupService:
    """Encapsulates all CDIS lookup operations.

    Accepts a CommandRunner so that callers (and tests) can inject their
    own implementation (Dependency Inversion Principle).
    """

    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._runner = runner or _get_default_runner()

    # -- single-user lookups ------------------------------------------------

    def lookup_by_idsid(self, idsid: str, verbose: bool = False) -> dict | None:
        """Look up a single user by IDSID."""
        if verbose:
            print(f"DEBUG: Looking up IDSID = {idsid}", file=sys.stderr)
        result = self._runner.run(f"/usr/intel/bin/cdislookup -i {idsid}", verbose=verbose)
        return parse_cdis_output(result, idsid, verbose=verbose)

    def lookup_by_wwid(self, wwid: str, verbose: bool = False) -> dict | None:
        """Look up a single user by WWID."""
        if verbose:
            print(f"DEBUG: Looking up WWID = {wwid}", file=sys.stderr)
        result = self._runner.run(f"/usr/intel/bin/cdislookup -w {wwid}", verbose=verbose)
        return parse_cdis_output(result, wwid, verbose=verbose)

    def lookup_user(self, identifier: str, verbose: bool = False) -> dict | None:
        """Auto-detect ID type and look up a single user."""
        identifier = identifier.strip()
        if not identifier:
            return None
        if is_wwid(identifier):
            return self.lookup_by_wwid(identifier, verbose=verbose)
        return self.lookup_by_idsid(identifier, verbose=verbose)

    # -- bulk lookups -------------------------------------------------------

    def lookup_users(self, identifiers: list[str], verbose: bool = False) -> list[dict]:
        """Look up multiple users (auto-detect type for each)."""
        results = []
        for ident in identifiers:
            data = self.lookup_user(ident, verbose=verbose)
            if data:
                results.append(data)
        return results

    def lookup_from_file(self, filename: str, verbose: bool = False) -> list[dict]:
        """Read IDs from a file (one per line) and look them up."""
        if not os.path.exists(filename):
            print(f"Error: File not found: {filename}", file=sys.stderr)
            return []
        with open(filename, "r") as f:
            ids = [line.strip() for line in f if line.strip()]
        if verbose:
            print(f"DEBUG: Looking up {len(ids)} users from file {filename}", file=sys.stderr)
        return self.lookup_users(ids, verbose=verbose)

    def _get_group_members(self, pdl_name: str, verbose: bool = False) -> list[str]:
        """Get the list of employee names in a PDL using groupmembers command."""
        if verbose:
            print(f"DEBUG: Getting members of PDL {pdl_name}", file=sys.stderr)
        try:
            members_str = self._runner.run(
                f"/usr/intel/bin/groupmembers -aU '{pdl_name}'", verbose=verbose
            )
            employee_names = [n.strip() for n in members_str.strip().split("\n") if n.strip()]
            if verbose:
                print(f"DEBUG: Found {len(employee_names)} members in PDL {pdl_name}", file=sys.stderr)
            return employee_names
        except Exception as e:
            print(f"Error: Failed to get members of PDL {pdl_name}: {e}", file=sys.stderr)
            return []

    def _get_vastool_idsid(self, employee_names: list[str], verbose: bool = False) -> list[str]:
        """Get the IDSID for an employee name using vastool."""
        results = []
        for name in employee_names:
            vastool_output = self._runner.run(
                f'/opt/quest/bin/vastool attrs "{name}" sAMAccountName', verbose=verbose
            )
            idsid = extract_idsid_from_vastool(vastool_output)
            if not idsid:
                continue
            data = self.lookup_by_idsid(idsid, verbose=verbose)
            if data:
                results.append(data)
        return results        

    def lookup_pdl(self, pdl_name: str, verbose: bool = False) -> list[dict]:
        """Look up all members of a PDL (by group name)."""
        employee_names = self._get_group_members(pdl_name, verbose=verbose)
        results = self._get_vastool_idsid(employee_names, verbose=verbose)
        return results

    # -- email lookups ------------------------------------------------------

    def _resolve_email_to_idsid(self, email: str, verbose: bool = False) -> str | None:
        """Resolve an email address to an IDSID using vastool LDAP search."""
        email = normalise_email(email)
        if verbose:
            print(f"DEBUG: Looking up IDSID for email: {email}", file=sys.stderr)

        for domain in _LDAP_DOMAINS:
            if domain:
                cmd = (
                    f'/opt/quest/bin/vastool search -b "{domain}" '
                    f'"(&(objectClass=user)(mail={email}))" sAMAccountName'
                )
            else:
                cmd = (
                    '/opt/quest/bin/vastool search '
                    f'"(&(objectClass=user)(mail={email}))" sAMAccountName'
                )

            try:
                result = self._runner.run(cmd, verbose=verbose)
                for line in result.strip().split("\n"):
                    if "sAMAccountName:" not in line:
                        continue
                    idsid = extract_idsid_from_vastool(line)
                    if idsid:
                        if verbose:
                            origin = domain or "default"
                            print(f"DEBUG: Found IDSID {idsid} from {origin} domain", file=sys.stderr)
                        return idsid
            except Exception as e:
                if verbose:
                    origin = domain or "default"
                    print(f"DEBUG: Failed {origin} domain lookup for {email}: {e}", file=sys.stderr)

        return None

    def lookup_email(self, email: str, verbose: bool = False) -> dict | None:
        """Look up a single user by email address."""
        normalized_email = normalise_email(email)
        idsid = self._resolve_email_to_idsid(normalized_email, verbose=verbose)
        if not idsid:
            print(f"Error: Could not find IDSID for {normalized_email}", file=sys.stderr)
            return None

        data = self.lookup_by_idsid(idsid, verbose=verbose)
        if not data:
            return None

        data["_email"] = normalized_email
        data["_idsid"] = idsid
        return data

    def lookup_emails(self, emails: list[str], verbose: bool = False) -> list[dict]:
        """Look up multiple users by email address."""
        results = []
        for email in emails:
            data = self.lookup_email(email, verbose=verbose)
            if data:
                results.append(data)
        return results

    def lookup_emails_from_file(self, filename: str, verbose: bool = False) -> list[dict]:
        """Read email addresses from a file (one per line) and look them up."""
        if not os.path.exists(filename):
            print(f"Error: File not found: {filename}", file=sys.stderr)
            return []
        with open(filename, "r") as f:
            emails = [line.strip() for line in f if line.strip()]
        if verbose:
            print(f"DEBUG: Looking up {len(emails)} emails from file {filename}", file=sys.stderr)
        return self.lookup_emails(emails, verbose=verbose)


# ---------------------------------------------------------------------------
# Module-level convenience functions (backward-compatible thin wrappers)
# ---------------------------------------------------------------------------

def lookup_by_idsid(idsid: str, verbose: bool = False) -> dict | None:
    """Module-level shortcut — delegates to EmployeeLookupService."""
    return EmployeeLookupService().lookup_by_idsid(idsid, verbose=verbose)


def lookup_by_wwid(wwid: str, verbose: bool = False) -> dict | None:
    return EmployeeLookupService().lookup_by_wwid(wwid, verbose=verbose)


def lookup_user(identifier: str, verbose: bool = False) -> dict | None:
    return EmployeeLookupService().lookup_user(identifier, verbose=verbose)


def lookup_users(identifiers: list[str], verbose: bool = False) -> list[dict]:
    return EmployeeLookupService().lookup_users(identifiers, verbose=verbose)


def lookup_from_file(filename: str, verbose: bool = False) -> list[dict]:
    return EmployeeLookupService().lookup_from_file(filename, verbose=verbose)


def lookup_pdl(pdl_name: str, verbose: bool = False) -> list[dict]:
    return EmployeeLookupService().lookup_pdl(pdl_name, verbose=verbose)


def lookup_email(email: str, verbose: bool = False) -> dict | None:
    return EmployeeLookupService().lookup_email(email, verbose=verbose)


def lookup_emails(emails: list[str], verbose: bool = False) -> list[dict]:
    return EmployeeLookupService().lookup_emails(emails, verbose=verbose)


def lookup_emails_from_file(filename: str, verbose: bool = False) -> list[dict]:
    return EmployeeLookupService().lookup_emails_from_file(filename, verbose=verbose)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Intel CDIS Employee Lookup Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
ID Auto-Detection:
  - All digits (e.g., 12345678) → treated as WWID
  - Contains letters (e.g., jsmith) → treated as IDSID

Examples:
    %(prog)s myteam-pdl
    %(prog)s myteam-pdl -k IDSID,DomainAddress,MgrName
  %(prog)s -u jsmith -k WWID,DomainAddress,GLCostCenterDes -f table
  %(prog)s -u jsmith,bjones,kwilson -k BookName,DomainAddress
  %(prog)s -u 12345678,23456789 -k IDSID,BookName
  %(prog)s -u jsmith,12345678 -k IDSID,WWID,BookName
  %(prog)s --file users.txt -k IDSID,DomainAddress
    %(prog)s -e john.smith@intel.com,jane.doe@corp.intel.com -k WWID,IDSID
    %(prog)s --email-file emails.txt -k WWID,BookName
  %(prog)s --list-keys
""",
    )

    parser.add_argument("pdl", nargs="?", help="PDL/group name (e.g., myteam-pdl)")
    parser.add_argument(
        "-u", "--users",
        help="Comma-separated list of IDs (auto-detects WWID vs IDSID)",
    )
    parser.add_argument("--file", dest="filename", help="Read IDs from file (one per line)")
    parser.add_argument(
        "-e", "--emails",
        help="Comma-separated list of email addresses",
    )
    parser.add_argument(
        "--email-file",
        dest="email_filename",
        help="Read email addresses from file (one per line)",
    )
    parser.add_argument(
        "-k", "--keys", default="IDSID",
        help="Comma-separated list of keys to output (default: IDSID)",
    )
    parser.add_argument(
        "-f", "--format", choices=["csv", "table", "json"], default="csv",
        help="Output format (default: csv)",
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    parser.add_argument(
        "--list-keys", action="store_true", help="List all available CDIS keys",
    )

    args = parser.parse_args()

    # --list-keys
    if args.list_keys:
        print("Available CDIS Keys:")
        print("-" * 40)
        for i in range(0, len(AVAILABLE_KEYS), 4):
            chunk = AVAILABLE_KEYS[i : i + 4]
            print("".join(k.ljust(18) for k in chunk))
        sys.exit(0)

    # Parse and validate keys
    keys = validate_keys([k.strip() for k in args.keys.split(",")])

    # Determine mode and execute
    if args.users:
        user_list = [u.strip() for u in args.users.split(",")]
        if args.debug:
            print(f"Looking up {len(user_list)} users", file=sys.stderr)
        results = lookup_users(user_list, verbose=args.debug)

    elif args.emails:
        email_list = [e.strip() for e in args.emails.split(",") if e.strip()]
        if args.debug:
            print(f"Looking up {len(email_list)} emails", file=sys.stderr)
        results = lookup_emails(email_list, verbose=args.debug)

    elif args.email_filename:
        results = lookup_emails_from_file(args.email_filename, verbose=args.debug)

    elif args.filename:
        results = lookup_from_file(args.filename, verbose=args.debug)

    elif args.pdl:
        results = lookup_pdl(args.pdl, verbose=args.debug)

    else:
        parser.print_help()
        sys.exit(1)

    output_results(results, keys, args.format)


if __name__ == "__main__":
    main()
