from __future__ import annotations

from typing import Any


def _normalize_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return normalize_post_data(value)
    if isinstance(value, list):
        return [_normalize_json_value(item) for item in value]
    return value


def normalize_post_data(post_data: dict[str, Any]) -> dict[str, Any]:
    """Copy JSON-decoded post data while recursively cloning nested dicts and lists."""
    normalized: dict[str, Any] = {}
    for key, value in post_data.items():
        normalized[key] = _normalize_json_value(value)
    return normalized