"""Shared utilities for the vManager backend client modules."""

from __future__ import annotations

from typing import Any


class _DictFilter:
    """Thin adapter that satisfies the vamp FilterBase interface for client-side wrappers.

    vamp delete/attach methods expect a ``FilterBase`` object whose ``.get()``
    method returns the raw filter dict.  This shim lets the client accept plain
    dicts and delegate cleanly without importing the vamp FilterBase class.
    """

    def __init__(self, d: dict) -> None:
        self._d = d

    def get(self) -> dict:
        return self._d


def _json_safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe_value(item) for item in value]
    if hasattr(value, "__dict__"):
        return {str(key): _json_safe_value(item) for key, item in vars(value).items()}
    return str(value)


def _normalize_single(obj: Any) -> dict[str, Any]:
    """Convert a backend object to a plain dict safe for json.dumps."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return {str(key): _json_safe_value(value) for key, value in obj.items()}
    if hasattr(obj, "__dict__"):
        return {str(key): _json_safe_value(value) for key, value in vars(obj).items()}
    return {}


def _extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("list", "items", "entities", "results", "data", "vplans"):
            if key in payload:
                value = payload[key]
                if isinstance(value, list):
                    return [row for row in value if isinstance(row, dict)]
                return []
        return [payload]
    return []


def apply_default_projection(post_data: dict, default_projection: list) -> dict:
    """Return *post_data* with *default_projection* injected when the caller omits "projection".

    Rules:
    - If "projection" is absent from *post_data*, returns a **new** dict that is
      identical to *post_data* except that ``"projection": default_projection`` is
      added.
    - If "projection" is present in *post_data* (including ``None`` or ``[]``),
      returns *post_data* unchanged — the caller's explicit choice is preserved.
    - The caller's original dict is **never mutated**.
    """
    if "projection" in post_data:
        return post_data
    return {**post_data, "projection": list(default_projection)}


def _extract_group_value(row: dict[str, Any], field_name: str) -> str | None:
    value = row.get(field_name)
    if isinstance(value, str) and value.strip():
        return value.strip()

    for container_name in ("groupingValues", "groupValues", "attributes", "atts", "group"):
        container = row.get(container_name)
        if isinstance(container, dict):
            nested = container.get(field_name)
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
    return None


# ---------------------------------------------------------------------------
# Grouped failure-cluster helpers
# ---------------------------------------------------------------------------

_SENTINEL = object()


def _first_present(row: dict[str, Any], *keys: str) -> Any:
    """Return the first value found in ``row`` for any of the given keys, or ``None``."""
    for key in keys:
        val = row.get(key, _SENTINEL)
        if val is not _SENTINEL:
            return val
    return None


def _set_if_present(
    target: dict[str, Any], out_key: str, row: dict[str, Any], *source_keys: str
) -> None:
    """Set ``target[out_key]`` from the first matching key in ``row``. No-op if none match."""
    val = _first_present(row, *source_keys)
    if val is not None:
        target[out_key] = val


def _build_cluster_summary(row: dict[str, Any], full_detail: bool) -> dict[str, Any]:
    """Extract cluster-level fields from a flat run↔cluster row."""
    s: dict[str, Any] = {}
    _set_if_present(s, "FAILURE CLUSTER - ID", row, "FAILURE CLUSTER - ID", "bucket_id", "cluster_id")
    _set_if_present(s, "FAILURE CLUSTER - Name", row, "FAILURE CLUSTER - Name", "bucket_name", "cluster_name")
    _set_if_present(s, "End Time", row, "End Time", "end_time")
    _set_if_present(s, "Debugger", row, "Debugger", "debugger")
    _set_if_present(s, "Debug Status", row, "Debug Status", "debug_status", "i_debug_status")
    _set_if_present(s, "Steppings", row, "Steppings", "steppings", "i_steps")
    _set_if_present(s, "Number Of Entities", row, "Number Of Entities", "number_of_entities")
    if full_detail:
        _set_if_present(s, "Tag", row, "Tag", "tag", "i_tag")
        _set_if_present(s, "FAILURE CLUSTER - HSDES_IDS", row, "FAILURE CLUSTER - HSDES_IDS", "hsdes_ids")
        _set_if_present(s, "FAILURE CLUSTER - Unique Tag", row, "FAILURE CLUSTER - Unique Tag", "unique_tag")
        _set_if_present(s, "FAILURE CLUSTER - Notes", row, "FAILURE CLUSTER - Notes", "notes")
    return s


def _build_run_summary(row: dict[str, Any]) -> dict[str, Any]:
    """Extract run-level fields from a flat run↔cluster row."""
    s: dict[str, Any] = {}
    _set_if_present(s, "ID", row, "ID", "id", "result_id")
    _set_if_present(s, "Test Name", row, "Test Name", "test_name")
    _set_if_present(s, "Test ID", row, "Test ID", "test_id")
    _set_if_present(s, "Duration (sec.)", row, "Duration (sec.)", "duration", "duration_sec")
    _set_if_present(s, "Debug Status", row, "Debug Status", "debug_status", "i_debug_status")
    _set_if_present(s, "Debugger", row, "Debugger", "debugger")
    _set_if_present(s, "dir_tag", row, "dir_tag", "result_directory")
    _set_if_present(s, "Directory Exists", row, "Directory Exists", "directory_exists")
    _set_if_present(s, "Auto Rerun Status", row, "Auto Rerun Status", "rerun_status", "auto_rerun_status")
    _set_if_present(s, "Is Rerun", row, "Is Rerun", "is_rerun")
    _set_if_present(s, "Model Version", row, "Model Version", "model_version")
    _set_if_present(s, "Steppings", row, "Steppings", "steppings", "dut", "i_steps")
    _set_if_present(s, "Testlist ID", row, "Testlist ID", "testlist_id")
    _set_if_present(s, "Gridl", row, "Gridl", "gridl", "cmd_line")
    _set_if_present(s, "End Time", row, "End Time", "end_time")
    return s


def group_run_failure_clusters(
    rows: list[dict[str, Any]], full_detail: bool = False
) -> list[dict[str, Any]]:
    """Group flat run↔cluster rows into cluster summaries with nested run lists.

    Each output dict contains default cluster fields plus a ``"runs"`` list of
    per-run field dicts.  When ``full_detail=True``, additional cluster-level
    fields (Tag, HSDES_IDS, Unique Tag, Notes) are also included.

    Key mapping uses robust fallbacks: raw API names (e.g. ``"FAILURE CLUSTER - ID"``)
    are tried first, then snake_case equivalents.  Keys absent in a row are
    silently omitted from the output.

    Args:
        rows: Flat list of run↔cluster association row dicts.
        full_detail: When ``True``, include extended cluster fields.

    Returns:
        List of cluster dicts in first-seen order; each has a ``"runs"`` key.
    """
    clusters: dict[Any, dict[str, Any]] = {}
    cluster_order: list[Any] = []

    for row in rows:
        cluster_id = _first_present(row, "FAILURE CLUSTER - ID", "bucket_id", "cluster_id")
        if cluster_id is None:
            continue
        if cluster_id not in clusters:
            cluster_order.append(cluster_id)
            clusters[cluster_id] = _build_cluster_summary(row, full_detail)
            clusters[cluster_id]["runs"] = []
        run_entry = _build_run_summary(row)
        if run_entry:
            clusters[cluster_id]["runs"].append(run_entry)

    return [clusters[k] for k in cluster_order]
