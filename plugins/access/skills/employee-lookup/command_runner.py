"""
command_runner.py - Abstraction for running shell commands.

Provides a Protocol-based interface (CommandRunner) so that production code
uses SubprocessCommandRunner while unit tests can inject a fake/mock.

This replaces the old run_unix_command.py with:
  - Proper error hierarchy instead of eval() on output
  - Dependency-injection-friendly design (Interface Segregation / DIP)
  - Single Responsibility: only runs commands, no output parsing
"""

from __future__ import annotations

import json
import sys
from abc import ABC, abstractmethod
from subprocess import PIPE, STDOUT, Popen  # nosec B404
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

class CommandResult(NamedTuple):
    """Immutable result of a shell command execution."""
    stdout: str
    returncode: int


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class CommandError(Exception):
    """Raised when a shell command fails."""

    def __init__(self, cmd: str, returncode: int, output: str) -> None:
        self.cmd = cmd
        self.returncode = returncode
        self.output = output
        super().__init__(f"Command failed (rc={returncode}): {cmd}\n{output}")


class ResourceNotFoundError(CommandError):
    """Raised when the command output indicates a 'Not Found' resource."""


# ---------------------------------------------------------------------------
# Abstract interface (Dependency Inversion Principle)
# ---------------------------------------------------------------------------

class CommandRunner(ABC):
    """Abstract interface for running shell commands."""

    @abstractmethod
    def run(self, cmd: str, timeout: int = 1200, verbose: bool = False) -> str:
        """Run *cmd* and return stripped stdout.

        Raises CommandError (or a subclass) on failure.
        """

    @abstractmethod
    def run_raw(self, cmd: str, timeout: int = 1200, verbose: bool = False) -> CommandResult:
        """Run *cmd* and return the full CommandResult (stdout + returncode)."""


# ---------------------------------------------------------------------------
# Production implementation
# ---------------------------------------------------------------------------

class SubprocessCommandRunner(CommandRunner):
    """Runs commands via subprocess.Popen (production implementation)."""

    def run_raw(self, cmd: str, timeout: int = 1200, verbose: bool = False) -> CommandResult:
        if verbose:
            print(f"Running Command: {cmd}")
        proc = Popen(  # nosec B602
            cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True
        )
        stdout_bytes, _ = proc.communicate(timeout=timeout)
        return CommandResult(
            stdout=stdout_bytes.decode("utf-8").rstrip(),
            returncode=proc.returncode,
        )

    def run(self, cmd: str, timeout: int = 1200, verbose: bool = False) -> str:
        result = self.run_raw(cmd, timeout, verbose)
        if result.returncode != 0:
            self._raise_for_error(cmd, result)
        return result.stdout

    # ------------------------------------------------------------------
    @staticmethod
    def _raise_for_error(cmd: str, result: CommandResult) -> None:
        """Inspect output and raise the most specific error possible."""
        # Try to detect a JSON-style "Not Found" message (API responses)
        try:
            # Only look at the first JSON object in the output
            candidate = result.stdout.split("}", 1)[0] + "}"
            payload = json.loads(candidate)
            if payload.get("message") == "Not Found":
                raise ResourceNotFoundError(cmd, result.returncode, result.stdout)
        except (json.JSONDecodeError, KeyError, IndexError):
            pass

        raise CommandError(cmd, result.returncode, result.stdout)
