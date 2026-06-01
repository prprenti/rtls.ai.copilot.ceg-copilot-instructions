"""
test_formatter.py - Unit tests for the formatter module.

Relocated from common_repo_skills/cdislookup/ to tests/cdislookup/.
"""

import json
import pytest

from formatter import (
    AVAILABLE_KEYS,
    CsvFormatter,
    JsonFormatter,
    TableFormatter,
    format_results,
    get_formatter,
    output_results,
    validate_keys,
)


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_ROWS = [
    {"IDSID": "jsmith", "WWID": "11111111", "BookName": "Smith, John"},
    {"IDSID": "bjones", "WWID": "22222222", "BookName": "Jones, Bob"},
]


# ---------------------------------------------------------------------------
# CsvFormatter
# ---------------------------------------------------------------------------

class TestCsvFormatter:
    def test_header_and_rows(self) -> None:
        fmt = CsvFormatter()
        text = fmt.format(SAMPLE_ROWS, ["IDSID", "WWID"])
        lines = text.split("\n")
        assert lines[0] == "IDSID,WWID"
        assert lines[1] == "jsmith,11111111"
        assert lines[2] == "bjones,22222222"

    def test_empty_results(self) -> None:
        assert CsvFormatter().format([], ["IDSID"]) == ""

    def test_missing_key_gives_empty(self) -> None:
        text = CsvFormatter().format([{"IDSID": "x"}], ["IDSID", "WWID"])
        assert text.split("\n")[1] == "x,"


# ---------------------------------------------------------------------------
# TableFormatter
# ---------------------------------------------------------------------------

class TestTableFormatter:
    def test_alignment(self) -> None:
        text = TableFormatter().format(SAMPLE_ROWS, ["IDSID", "BookName"])
        lines = text.split("\n")
        assert "IDSID" in lines[0]
        assert "---" in lines[1]  # separator
        assert len(lines) == 4  # header + sep + 2 data rows

    def test_empty_results(self) -> None:
        assert TableFormatter().format([], ["IDSID"]) == ""


# ---------------------------------------------------------------------------
# JsonFormatter
# ---------------------------------------------------------------------------

class TestJsonFormatter:
    def test_valid_json(self) -> None:
        text = JsonFormatter().format(SAMPLE_ROWS, ["IDSID", "WWID"])
        data = json.loads(text)
        assert len(data) == 2
        assert data[0]["IDSID"] == "jsmith"

    def test_only_requested_keys(self) -> None:
        text = JsonFormatter().format(SAMPLE_ROWS, ["WWID"])
        data = json.loads(text)
        assert list(data[0].keys()) == ["WWID"]

    def test_empty_results(self) -> None:
        assert JsonFormatter().format([], ["IDSID"]) == ""


# ---------------------------------------------------------------------------
# get_formatter factory
# ---------------------------------------------------------------------------

class TestGetFormatter:
    def test_csv(self) -> None:
        assert isinstance(get_formatter("csv"), CsvFormatter)

    def test_table(self) -> None:
        assert isinstance(get_formatter("table"), TableFormatter)

    def test_json(self) -> None:
        assert isinstance(get_formatter("json"), JsonFormatter)

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown format"):
            get_formatter("xml")


# ---------------------------------------------------------------------------
# format_results convenience wrapper
# ---------------------------------------------------------------------------

class TestFormatResults:
    def test_csv_via_wrapper(self) -> None:
        text = format_results(SAMPLE_ROWS, ["IDSID"], "csv")
        assert "jsmith" in text

    def test_json_via_wrapper(self) -> None:
        text = format_results(SAMPLE_ROWS, ["IDSID"], "json")
        assert json.loads(text)[0]["IDSID"] == "jsmith"


# ---------------------------------------------------------------------------
# output_results (prints + returns)
# ---------------------------------------------------------------------------

class TestOutputResults:
    def test_prints_and_returns(self, capsys: pytest.CaptureFixture[str]) -> None:
        text = output_results(SAMPLE_ROWS, ["IDSID"], "csv")
        captured = capsys.readouterr()
        assert "jsmith" in captured.out
        assert text == captured.out.strip()

    def test_empty_returns_empty(self) -> None:
        assert output_results([], ["IDSID"]) == ""


# ---------------------------------------------------------------------------
# validate_keys
# ---------------------------------------------------------------------------

class TestValidateKeys:
    def test_valid_keys_pass_through(self) -> None:
        assert validate_keys(["IDSID", "WWID"]) == ["IDSID", "WWID"]

    def test_unknown_keys_filtered(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = validate_keys(["IDSID", "BOGUS"])
        assert result == ["IDSID"]

    def test_all_unknown_falls_back_to_default(self) -> None:
        result = validate_keys(["NOPE"])
        assert result == ["IDSID"]

    def test_available_keys_not_empty(self) -> None:
        assert len(AVAILABLE_KEYS) > 40
