from __future__ import annotations

from validation_mcp.errors import PaginationPolicyError


_MISSING = object()


def _read_fetch_all_flag(raw_value: object, *, label: str) -> bool:
    if raw_value is None:
        return False
    if isinstance(raw_value, bool):
        return raw_value
    raise ValueError(f"{label} must be a boolean")


def apply_pagination_policy(
    post_data: dict,
    *,
    max_page_length: int,
) -> dict:
    """Validate explicit pagination keys without injecting implicit defaults."""
    safe = dict(post_data)
    raw_fetch_all_snake = safe.pop("fetch_all", _MISSING)
    raw_fetch_all_camel = safe.pop("fetchAll", _MISSING)
    fetch_all_present = (
        raw_fetch_all_snake is not _MISSING or raw_fetch_all_camel is not _MISSING
    )

    if raw_fetch_all_snake is not _MISSING and raw_fetch_all_camel is not _MISSING:
        if raw_fetch_all_snake != raw_fetch_all_camel:
            raise ValueError(
                f"fetch_all and fetchAll must match when both are provided; "
                f"got {raw_fetch_all_snake!r} and {raw_fetch_all_camel!r}"
            )
        raw_fetch_all = raw_fetch_all_snake
    elif raw_fetch_all_snake is not _MISSING:
        raw_fetch_all = raw_fetch_all_snake
    elif raw_fetch_all_camel is not _MISSING:
        raw_fetch_all = raw_fetch_all_camel
    else:
        raw_fetch_all = None

    _read_fetch_all_flag(raw_fetch_all, label="fetch_all")

    if fetch_all_present:
        raise PaginationPolicyError(
            "fetch_all/fetchAll is not supported by validation-mcp list tools; remove the key and request another page explicitly"
        )

    if "pageLength" in safe:
        requested_page_length = safe["pageLength"]
        try:
            page_length = int(requested_page_length)
        except (TypeError, ValueError) as exc:
            raise ValueError("pageLength must be an integer") from exc

        if page_length < 1:
            raise ValueError("pageLength must be >= 1")

        if page_length > max_page_length:
            raise ValueError(f"pageLength must be <= {max_page_length}")

        safe["pageLength"] = page_length

    if "pageOffset" in safe:
        page_offset = safe["pageOffset"]
        try:
            safe["pageOffset"] = int(page_offset)
        except (TypeError, ValueError) as exc:
            raise ValueError("pageOffset must be an integer") from exc

        if safe["pageOffset"] < 0:
            raise ValueError("pageOffset must be >= 0")

    return safe


def clamp_page_length(
    page_length: int,
    *,
    max_page_length: int,
) -> int:
    if page_length < 1:
        raise ValueError("page_length must be >= 1")
    return min(page_length, max_page_length)