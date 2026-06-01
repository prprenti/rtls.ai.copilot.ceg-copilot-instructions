"""
run_unix_command.py - Legacy shim for backward compatibility.

New code should use command_runner.CommandRunner / SubprocessCommandRunner
directly.  These functions delegate to the new implementation.
"""

from __future__ import annotations

import os
import sys
import warnings

# Ensure script directory is importable
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from command_runner import (  # noqa: E402
    CommandError,
    CommandResult,
    ResourceNotFoundError,
    SubprocessCommandRunner,
)

_runner = SubprocessCommandRunner()


def run_command_capture_errors(
    cmd: str, timeout: int = 1200, verbose: bool = False
) -> tuple[str, int]:
    """Run *cmd* and return ``(stdout, returncode)`` — never raises."""
    warnings.warn(
        "run_command_capture_errors() is deprecated; use SubprocessCommandRunner.run_raw()",
        DeprecationWarning,
        stacklevel=2,
    )
    result = _runner.run_raw(cmd, timeout=timeout, verbose=verbose)
    return result.stdout, result.returncode


def run_command(cmd: str, timeout: int = 1200, verbose: bool = False) -> str:
    """Run *cmd* and return stdout.  Raises on error."""
    warnings.warn(
        "run_command() is deprecated; use SubprocessCommandRunner.run()",
        DeprecationWarning,
        stacklevel=2,
    )
    return _runner.run(cmd, timeout=timeout, verbose=verbose)
