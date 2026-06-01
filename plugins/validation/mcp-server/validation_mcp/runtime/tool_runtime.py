from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Callable, TypeVar

from validation_mcp.errors import translate_error_message
from validation_mcp.runtime.output import render_json_response
from validation_mcp.runtime.pagination import apply_pagination_policy, clamp_page_length
from validation_mcp.runtime.query_adapter import normalize_post_data
from validation_mcp.settings import Settings

from . import client_factory


logger = logging.getLogger("validation-mcp.tool-runtime")
T = TypeVar("T")


def coerce_settings(settings_or_repo_root: Settings | str) -> Settings:
    if isinstance(settings_or_repo_root, Settings):
        return settings_or_repo_root
    return Settings.from_env(settings_or_repo_root)


def render_tool_error(settings: Settings, error: Exception) -> str:
    return f"ERROR: {translate_error_message(error, debug=settings.debug_errors)}"


def parse_json_argument(raw_value: str, *, label: str) -> Any:
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON for {label}: {exc}") from exc


def parse_json_array_argument(raw_value: str, *, label: str) -> list[Any]:
    value = parse_json_argument(raw_value, label=label)
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a JSON array")
    return value


def parse_json_object_argument(raw_value: str, *, label: str) -> dict[str, Any]:
    value = parse_json_argument(raw_value, label=label)
    if not isinstance(value, dict):
        raise ValueError(f"{label} must decode to a JSON object")
    return value


def parse_optional_json_argument(raw_value: str, *, label: str, empty_literal: str = "{}") -> Any | None:
    if raw_value.strip() == empty_literal:
        return None
    return parse_json_argument(raw_value, label=label)


def prepare_optional_post_data(
    settings_or_repo_root: Settings | str,
    raw_value: str,
    *,
    label: str,
    paginate: bool,
) -> dict[str, Any] | None:
    post_data = parse_optional_json_argument(raw_value, label=label)
    if post_data is None:
        return None
    return prepare_post_data(settings_or_repo_root, post_data, paginate=paginate)


def prepare_post_data(
    settings_or_repo_root: Settings | str,
    post_data: Any,
    *,
    paginate: bool,
) -> dict[str, Any]:
    if not isinstance(post_data, dict):
        raise ValueError("post_data must decode to a JSON object")

    settings = coerce_settings(settings_or_repo_root)
    normalized_post_data = normalize_post_data(post_data)
    if not paginate:
        return normalized_post_data

    return apply_pagination_policy(
        normalized_post_data,
        max_page_length=settings.max_page_length,
    )


def bounded_page_length(settings_or_repo_root: Settings | str, page_length: int) -> int:
    settings = coerce_settings(settings_or_repo_root)
    return clamp_page_length(page_length, max_page_length=settings.max_page_length)


async def run_vmanager_tool(
    tool_name: str,
    settings_or_repo_root: Settings | str,
    callback: Callable[[Any, Settings], T],
) -> str:
    settings = coerce_settings(settings_or_repo_root)
    started_at = time.perf_counter()

    try:
        client = client_factory.get_vmanager_client(settings)
        result = await asyncio.to_thread(callback, client, settings)
        logger.debug(
            "tool=%s duration_ms=%s success=true",
            tool_name,
            round((time.perf_counter() - started_at) * 1000, 2),
        )
        return render_json_response(result, pretty=settings.pretty_json)
    except asyncio.CancelledError:
        logger.info("tool=%s success=false cancelled=true", tool_name)
        raise
    except Exception as exc:
        if settings.debug_errors:
            logger.exception("tool=%s success=false", tool_name)
        else:
            logger.warning(
                "tool=%s success=false error=%s",
                tool_name,
                translate_error_message(exc, debug=False),
            )
        return render_tool_error(settings, exc)