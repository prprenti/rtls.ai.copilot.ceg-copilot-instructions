"""
test_command_runner.py - Unit tests for command_runner module.

Relocated from common_repo_skills/cdislookup/ to tests/cdislookup/.
"""

import json
import pytest

from command_runner import (
    CommandError,
    CommandResult,
    CommandRunner,
    ResourceNotFoundError,
    SubprocessCommandRunner,
)


# ---------------------------------------------------------------------------
# A concrete fake for tests (also proves the ABC works)
# ---------------------------------------------------------------------------

class FakeCommandRunner(CommandRunner):
    """In-memory test double: returns pre-canned responses keyed by command."""

    def __init__(self, responses: dict[str, CommandResult] | None = None) -> None:
        self.responses: dict[str, CommandResult] = responses or {}
        self.history: list[str] = []

    def add(self, cmd: str, stdout: str, returncode: int = 0) -> None:
        self.responses[cmd] = CommandResult(stdout=stdout, returncode=returncode)

    def run_raw(self, cmd: str, timeout: int = 1200, verbose: bool = False) -> CommandResult:
        self.history.append(cmd)
        if cmd in self.responses:
            return self.responses[cmd]
        return CommandResult(stdout="", returncode=0)

    def run(self, cmd: str, timeout: int = 1200, verbose: bool = False) -> str:
        result = self.run_raw(cmd, timeout, verbose)
        if result.returncode != 0:
            # Reuse the production error-raising logic
            SubprocessCommandRunner._raise_for_error(cmd, result)
        return result.stdout


# ---------------------------------------------------------------------------
# Tests: CommandResult
# ---------------------------------------------------------------------------

class TestCommandResult:
    def test_namedtuple_fields(self) -> None:
        r = CommandResult(stdout="hello", returncode=0)
        assert r.stdout == "hello"
        assert r.returncode == 0

    def test_immutable(self) -> None:
        r = CommandResult(stdout="x", returncode=1)
        with pytest.raises(AttributeError):
            r.stdout = "y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Tests: error hierarchy
# ---------------------------------------------------------------------------

class TestCommandError:
    def test_basic_error(self) -> None:
        err = CommandError("ls", 1, "not found")
        assert err.cmd == "ls"
        assert err.returncode == 1
        assert "not found" in str(err)

    def test_resource_not_found_is_command_error(self) -> None:
        err = ResourceNotFoundError("curl ...", 1, '{"message": "Not Found"}')
        assert isinstance(err, CommandError)


# ---------------------------------------------------------------------------
# Tests: FakeCommandRunner (doubles as ABC verification)
# ---------------------------------------------------------------------------

class TestFakeCommandRunner:
    def test_run_returns_stdout(self) -> None:
        runner = FakeCommandRunner()
        runner.add("echo hi", "hi")
        assert runner.run("echo hi") == "hi"

    def test_run_raises_on_nonzero_rc(self) -> None:
        runner = FakeCommandRunner()
        runner.add("fail", "oops", returncode=1)
        with pytest.raises(CommandError):
            runner.run("fail")

    def test_run_raises_resource_not_found(self) -> None:
        body = json.dumps({"message": "Not Found"})
        runner = FakeCommandRunner()
        runner.add("api call", body, returncode=1)
        with pytest.raises(ResourceNotFoundError):
            runner.run("api call")

    def test_records_history(self) -> None:
        runner = FakeCommandRunner()
        runner.add("a", "1")
        runner.add("b", "2")
        runner.run("a")
        runner.run("b")
        assert runner.history == ["a", "b"]


# ---------------------------------------------------------------------------
# Tests: SubprocessCommandRunner (integration – echo only)
# ---------------------------------------------------------------------------

class TestSubprocessCommandRunner:
    def test_echo(self) -> None:
        runner = SubprocessCommandRunner()
        result = runner.run("echo hello")
        assert result == "hello"

    def test_nonzero_exit_raises(self) -> None:
        runner = SubprocessCommandRunner()
        with pytest.raises(CommandError):
            runner.run("exit 1")
