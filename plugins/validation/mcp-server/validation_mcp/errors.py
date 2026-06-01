from __future__ import annotations


class ToolExecutionError(RuntimeError):
    pass


class PaginationPolicyError(ValueError):
    pass


def translate_error_message(error: Exception, *, debug: bool) -> str:
    rendered = str(error).strip() or error.__class__.__name__
    if not debug:
        rendered = rendered.splitlines()[0]
    return rendered


def format_tool_error(tool_name: str, error: Exception, *, debug: bool) -> str:
    return f"{tool_name} failed: {translate_error_message(error, debug=debug)}"