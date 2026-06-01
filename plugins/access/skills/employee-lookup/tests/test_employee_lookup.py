"""
test_employee_lookup.py - Unit tests for the employee_lookup module.

These tests use FakeCommandRunner so no external commands are executed.
"""

from __future__ import annotations

from employee_lookup import (
    EmployeeLookupService,
    extract_idsid_from_vastool,
    is_wwid,
    normalise_email,
    parse_cdis_output,
)
from test_command_runner import FakeCommandRunner


def _make_cdis_response(**fields: str) -> str:
    return "\n".join(f"{k}={v}" for k, v in fields.items())


class TestHelpers:
    def test_is_wwid(self) -> None:
        assert is_wwid("12345678") is True
        assert is_wwid("jsmith") is False

    def test_parse_output(self) -> None:
        raw = "IDSID=jsmith\nWWID=12345678\nBookName=Smith, John"
        out = parse_cdis_output(raw, "jsmith")
        assert out == {
            "IDSID": "jsmith",
            "WWID": "12345678",
            "BookName": "Smith, John",
        }

    def test_extract_idsid(self) -> None:
        assert extract_idsid_from_vastool("sAMAccountName: jsmith") == "jsmith"

    def test_normalise_email(self) -> None:
        assert normalise_email("John.Smith@Corp.Intel.com") == "john.smith@corp.intel.com"
        assert normalise_email("jsmith") == "jsmith@intel.com"


class TestEmployeeLookupService:
    def test_lookup_by_idsid(self) -> None:
        runner = FakeCommandRunner()
        runner.add(
            "/usr/intel/bin/cdislookup -i jsmith",
            _make_cdis_response(IDSID="jsmith", WWID="11111111"),
        )
        svc = EmployeeLookupService(runner)
        out = svc.lookup_by_idsid("jsmith")
        assert out is not None
        assert out["IDSID"] == "jsmith"

    def test_lookup_user_auto_wwid(self) -> None:
        runner = FakeCommandRunner()
        runner.add(
            "/usr/intel/bin/cdislookup -w 99999999",
            _make_cdis_response(WWID="99999999"),
        )
        svc = EmployeeLookupService(runner)
        out = svc.lookup_user("99999999")
        assert out is not None
        assert out["WWID"] == "99999999"

    def test_lookup_pdl(self) -> None:
        runner = FakeCommandRunner()
        runner.add(
            "/usr/intel/bin/groupmembers -aU 'team-pdl'",
            "Smith, John\nJones, Bob",
        )
        runner.add(
            '/opt/quest/bin/vastool attrs "Smith, John" sAMAccountName',
            "sAMAccountName: jsmith",
        )
        runner.add(
            '/opt/quest/bin/vastool attrs "Jones, Bob" sAMAccountName',
            "sAMAccountName: bjones",
        )
        runner.add("/usr/intel/bin/cdislookup -i jsmith", _make_cdis_response(IDSID="jsmith"))
        runner.add("/usr/intel/bin/cdislookup -i bjones", _make_cdis_response(IDSID="bjones"))

        svc = EmployeeLookupService(runner)
        out = svc.lookup_pdl("team-pdl")
        assert len(out) == 2

    def test_lookup_email(self) -> None:
        runner = FakeCommandRunner()
        runner.add(
            '/opt/quest/bin/vastool search "(&(objectClass=user)(mail=john.smith@intel.com))" sAMAccountName',
            "sAMAccountName: jsmith",
        )
        runner.add(
            "/usr/intel/bin/cdislookup -i jsmith",
            _make_cdis_response(IDSID="jsmith", WWID="11111111"),
        )
        svc = EmployeeLookupService(runner)
        out = svc.lookup_email("john.smith@intel.com")
        assert out is not None
        assert out["IDSID"] == "jsmith"
        assert out["_email"] == "john.smith@intel.com"

    def test_lookup_email_not_found(self) -> None:
        runner = FakeCommandRunner()
        runner.add(
            '/opt/quest/bin/vastool search "(&(objectClass=user)(mail=nobody@intel.com))" sAMAccountName',
            "",
        )
        runner.add(
            '/opt/quest/bin/vastool search -b "DC=ger,DC=corp,DC=intel,DC=com" "(&(objectClass=user)(mail=nobody@intel.com))" sAMAccountName',
            "",
        )
        svc = EmployeeLookupService(runner)
        assert svc.lookup_email("nobody") is None
