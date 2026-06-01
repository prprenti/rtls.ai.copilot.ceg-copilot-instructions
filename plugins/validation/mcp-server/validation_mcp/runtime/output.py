from __future__ import annotations

import json
from typing import Any


def render_json_response(value: Any, *, pretty: bool = True) -> str:
    indent = 2 if pretty else None
    return json.dumps(value, indent=indent, sort_keys=True)


def shape_named_list_result(list_key: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {list_key: items, "count": len(items)}