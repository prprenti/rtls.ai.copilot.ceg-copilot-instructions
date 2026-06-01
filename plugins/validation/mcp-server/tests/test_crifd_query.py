"""Focused tests for the register_topology crifd_query helper."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys

import pytest

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


HELPER_PATH = REPO_ROOT / "plugins" / "validation" / "skills" / "register-topology" / "crifd_query.py"
SAMPLE_REGISTER_OUTPUT = """\
CACHE: /tmp/cache-entry
Register
+-----------+---------+---------+---------------+
| FName     | Address | Port_ID | Register_File |
+===========+=========+=========+===============+
| MC.REG0   | 0xe190  | 0x12    | MC_RF         |
+-----------+---------+---------+---------------+

Fields
+------+-------+--------+-------------+
| Name | Range | Access | Description |
+======+=======+========+=============+
| EN   | 0     | RW     | Enable bit  |
+------+-------+--------+-------------+
"""


@pytest.fixture()
def crifd_query_module():
    spec = importlib.util.spec_from_file_location("test_crifd_query_module", HELPER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestParseOutput:
    def test_parse_table_output_with_fields(self, crifd_query_module) -> None:
        parsed = crifd_query_module._parse_output(
            SAMPLE_REGISTER_OUTPUT,
            include_fields=True,
            columns=["FName", "Address"],
            field_columns=["Name", "Access"],
            short=False,
            limit=None,
        )

        assert parsed["count"] == 1
        assert parsed["total_count"] == 1
        assert parsed["registers"] == [
            {
                "FName": "MC.REG0",
                "Address": "0xe190",
                "fields": [{"Name": "EN", "Access": "RW"}],
            }
        ]

    def test_omit_expensive_register_columns_strips_register_file(self, crifd_query_module) -> None:
        parsed = crifd_query_module._parse_output(
            SAMPLE_REGISTER_OUTPUT,
            include_fields=False,
            columns=None,
            field_columns=None,
            short=False,
            limit=None,
            omit_expensive_reg_columns=True,
        )
        reg = parsed["registers"][0]
        assert "Register_File" not in reg
        assert "FName" in reg
        assert "Address" in reg
        assert "Port_ID" in reg

    def test_omit_expensive_field_columns_strips_description(self, crifd_query_module) -> None:
        parsed = crifd_query_module._parse_output(
            SAMPLE_REGISTER_OUTPUT,
            include_fields=True,
            columns=None,
            field_columns=None,
            short=False,
            limit=None,
            omit_expensive_field_columns=True,
        )
        field = parsed["registers"][0]["fields"][0]
        assert "Description" not in field
        assert "Name" in field
        assert "Access" in field

    def test_explicit_columns_wins_over_omit_flag(self, crifd_query_module) -> None:
        parsed = crifd_query_module._parse_output(
            SAMPLE_REGISTER_OUTPUT,
            include_fields=True,
            columns=["FName", "Register_File"],
            field_columns=["Name", "Description"],
            short=False,
            limit=None,
            omit_expensive_reg_columns=True,
            omit_expensive_field_columns=True,
        )
        reg = parsed["registers"][0]
        assert "Register_File" in reg
        assert "FName" in reg
        assert "Address" not in reg
        field = parsed["registers"][0]["fields"][0]
        assert "Description" in field
        assert "Access" not in field


class TestMainExitBehavior:
    def test_successful_query_outputs_parsed_json(
        self,
        crifd_query_module,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            crifd_query_module.subprocess,
            "run",
            lambda *args, **kwargs: subprocess.CompletedProcess(
                args=args[0],
                returncode=0,
                stdout=SAMPLE_REGISTER_OUTPUT,
                stderr="",
            ),
        )
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "crifd_query.py",
                "--crif",
                "/tmp/mock.xml",
                "--query",
                "MC.REG0",
                "--columns",
                "FName,Address",
                "--field-columns",
                "Name,Access",
            ],
        )

        crifd_query_module.main()

        payload = json.loads(capsys.readouterr().out)
        assert payload["count"] == 1
        assert payload["query"] == "MC.REG0"
        assert payload["crif"] == "/tmp/mock.xml"
        assert payload["registers"][0]["fields"] == [{"Name": "EN", "Access": "RW"}]

    def test_no_match_returns_exit_code_1_and_empty_payload(
        self,
        crifd_query_module,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            crifd_query_module.subprocess,
            "run",
            lambda *args, **kwargs: subprocess.CompletedProcess(
                args=args[0],
                returncode=1,
                stdout="No registers were matched\n",
                stderr="",
            ),
        )
        monkeypatch.setattr(
            sys,
            "argv",
            ["crifd_query.py", "--crif", "/tmp/mock.xml", "--query", "MISSING.REG"],
        )

        with pytest.raises(SystemExit) as excinfo:
            crifd_query_module.main()

        assert excinfo.value.code == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload == {
            "registers": [],
            "count": 0,
            "total_count": 0,
            "query": "MISSING.REG",
            "crif": "/tmp/mock.xml",
        }

    def test_omit_expensive_register_columns_cli_flag(
        self,
        crifd_query_module,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            crifd_query_module.subprocess,
            "run",
            lambda *args, **kwargs: subprocess.CompletedProcess(
                args=args[0],
                returncode=0,
                stdout=SAMPLE_REGISTER_OUTPUT,
                stderr="",
            ),
        )
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "crifd_query.py",
                "--crif", "/tmp/mock.xml",
                "--query", "MC.REG0",
                "--omit-expensive-register-columns",
            ],
        )

        crifd_query_module.main()

        payload = json.loads(capsys.readouterr().out)
        reg = payload["registers"][0]
        assert "Register_File" not in reg
        assert "FName" in reg

    def test_omit_expensive_field_columns_cli_flag(
        self,
        crifd_query_module,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            crifd_query_module.subprocess,
            "run",
            lambda *args, **kwargs: subprocess.CompletedProcess(
                args=args[0],
                returncode=0,
                stdout=SAMPLE_REGISTER_OUTPUT,
                stderr="",
            ),
        )
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "crifd_query.py",
                "--crif", "/tmp/mock.xml",
                "--query", "MC.REG0",
                "--omit-expensive-field-columns",
            ],
        )

        crifd_query_module.main()

        payload = json.loads(capsys.readouterr().out)
        field = payload["registers"][0]["fields"][0]
        assert "Description" not in field
        assert "Name" in field

    def test_nonzero_crifd_failure_returns_error_payload_and_exit_code_2(
        self,
        crifd_query_module,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            crifd_query_module.subprocess,
            "run",
            lambda *args, **kwargs: subprocess.CompletedProcess(
                args=args[0],
                returncode=7,
                stdout="",
                stderr="fatal: failed to read CRIF\n",
            ),
        )
        monkeypatch.setattr(
            sys,
            "argv",
            ["crifd_query.py", "--crif", "/tmp/bad.xml", "--query", "MC.REG0"],
        )

        with pytest.raises(SystemExit) as excinfo:
            crifd_query_module.main()

        assert excinfo.value.code == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["error"] == "hive crifd failed"
        assert payload["returncode"] == 7
        assert payload["stderr"] == "fatal: failed to read CRIF"
        assert payload["query"] == "MC.REG0"
        assert payload["crif"] == "/tmp/bad.xml"
        assert payload["cmd"] == ["hive", "crifd", "-crif", "/tmp/bad.xml", "MC.REG0"]