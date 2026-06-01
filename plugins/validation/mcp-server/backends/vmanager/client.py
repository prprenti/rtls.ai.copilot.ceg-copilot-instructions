from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

try:
    from ...standard_runs_query import build_standard_runs_list_request, normalize_values
except ImportError:  # pragma: no cover - repo-root test layout
    from standard_runs_query import build_standard_runs_list_request, normalize_values

from ._utils import _DictFilter, _extract_rows, _extract_group_value, apply_default_projection  # noqa: F401 — re-export for tests
from ._client_domain import _VmanagerDomainMixin, PLAN_SUB_ELEMENTS_SLIM_PROJECTION

# Default slim projection for run list queries.
# Covers identity, status, triage/ownership, timing, location, and classification
# fields needed for AI-driven triage and consistent with the grouped failure-cluster
# run summary schema.  Pass ``"projection"`` in post_data (including None or [])
# to override — any presence of the key suppresses injection.
RUN_SLIM_PROJECTION: list[str] = [
    # Identity
    "id",
    "name",
    # Status / triage
    "status",
    "i_debug_status",
    "i_debugger",
    # Classification
    "i_team",
    "i_dut",
    "i_steps",
    "i_for_indicators",
    # Timing & location
    "end_time",
    "dir_tag",
    "i_gridl",
    # Rerun tracking
    "i_is_rerun",
    "i_auto_rerun_status",
    # Build context
    "i_testlist_id",
    "i_model_version",
]

# Default slim projection for session list queries.
# Covers identity, status, ownership, classification, timing, and config
# reference fields needed for AI-driven session navigation and composition.
# Pass ``"projection"`` in post_data (including None or []) to override.
SESSION_SLIM_PROJECTION: list[str] = [
    # Identity
    "id",
    "name",
    # Status
    "status",
    # Ownership
    "owner",
    "i_team",
    # Classification
    "i_steps",
    "i_dut",
    # Timing
    "created_time",
    "modification_time",
    # Config reference for navigation
    "vsif_id",
]

# Default slim projection for failure cluster list queries.
# Covers identity, triage status, ownership, run count, steppings, timing,
# and cross-reference fields needed for AI-driven triage.  Aligns with the
# cluster-level fields surfaced by the grouped run-failure-cluster summary.
# Pass ``"projection"`` in post_data (including None or []) to override.
FAILURE_CLUSTER_SLIM_PROJECTION: list[str] = [
    # Identity
    "id",
    "name",
    # Status / triage
    "debug_status",
    "debugger",
    "owner",
    # Classification / scope
    "i_steps",
    # Run count
    "number_of_entities",
    # Timing
    "end_time",
    # Cross-references
    "unique_tag",
    "hsdes_ids",
]


class VmanagerBackendUnavailable(RuntimeError):
    pass


def _repo_root_from_file() -> Path:
    return Path(__file__).resolve().parents[3]


def _candidate_vamp_sys_paths(_repo_root: Path) -> list[str]:
    """Return extra sys.path entries needed to import vamp.

    The standard path needs no extra entries because vmanager-vamp is
    installed by ``uv sync``. Extra entries are only used for the
    CEGMCP_VAMP_PATH escape hatch.
    """
    candidates: list[str] = []
    env_path = os.environ.get("CEGMCP_VAMP_PATH")
    if env_path:
        raw_path = Path(env_path).expanduser()
        if (raw_path / "vamp" / "__init__.py").is_file():
            candidates.append(str(raw_path))
        elif (raw_path / "__init__.py").is_file() and raw_path.name == "vamp":
            candidates.append(str(raw_path.parent))
    return candidates


def _load_vamp_class(repo_root: Path) -> type:
    importlib.invalidate_caches()
    for candidate in _candidate_vamp_sys_paths(repo_root):
        if candidate not in sys.path:
            sys.path.insert(0, candidate)

    try:
        return importlib.import_module("vamp").Vamp
    except ImportError as exc:
        raise VmanagerBackendUnavailable(
            "vManager backend not available: 'vamp' module not found.\n"
            "The vmanager-vamp package should be installed automatically by ddgmcp/setup.sh.\n"
            "Re-run bootstrap: cd ddgmcp && uv sync\n"
            "Override: set CEGMCP_VAMP_PATH to either /path/to/parent/of/vamp/ "
            "or /path/to/vamp/"
        ) from exc



def classify_team_name(team_name: str) -> str:
    normalized = team_name.strip().lower()
    if "hub" in {part for part in normalized.split(".") if part} or normalized.startswith("hub."):
        return "hub"
    if normalized.startswith("iu."):
        return "iu"
    if normalized.startswith("ip."):
        return "ip"
    return "other"


def derive_dut_from_team_name(team_name: str) -> str | None:
    normalized = team_name.strip().lower()
    parts = [part for part in normalized.split(".") if part]
    if len(parts) < 2:
        return None

    kind = classify_team_name(normalized)
    if kind in {"iu", "ip"}:
        return parts[1]

    if kind == "hub":
        try:
            hub_index = parts.index("hub")
        except ValueError:
            return parts[1]

        for part in parts[hub_index + 1 :]:
            if part != "hub":
                return part
        return None

    return None


def derive_dut_values(
    team: str | list[str] | tuple[str, ...],
    dut: str | list[str] | tuple[str, ...] | None = None,
) -> tuple[tuple[str, ...], bool]:
    if dut is not None:
        return normalize_values(dut, "dut"), False

    derived_values: list[str] = []
    for team_name in normalize_values(team, "team"):
        derived = derive_dut_from_team_name(team_name)
        if not derived:
            raise ValueError(
                f"Unable to derive dut from team '{team_name}'. Pass dut explicitly."
            )
        if derived not in derived_values:
            derived_values.append(derived)
    return tuple(derived_values), True


class VmanagerClient(_VmanagerDomainMixin):
    def __init__(
        self,
        repo_root: str | None = None,
        *,
        vamp_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.repo_root = Path(repo_root) if repo_root else _repo_root_from_file()
        factory = vamp_factory or _load_vamp_class(self.repo_root)
        self._vamp = factory()

    @property
    def test_run(self):
        return self._vamp.test_run

    @property
    def failure_cluster(self):
        return self._vamp.failure_cluster

    @property
    def vsif_hierarchy(self):
        return self._vamp.vsif_hierarchy

    @property
    def vsif_sessions(self):
        return self._vamp.vsif_sessions

    @property
    def test_plan(self):
        return self._vamp.test_plan

    def list_runs(self, post_data: dict) -> dict[str, Any]:
        """List runs matching an RS specification.

        Returns a dict with "runs" (list of row dicts) and "count".
        A slim projection is applied by default so AI callers do not receive
        large per-row payloads.  Pass ``"projection"`` in *post_data*
        (including ``None`` or ``[]``) to override.
        """
        post_data = apply_default_projection(post_data, RUN_SLIM_PROJECTION)
        rows = _extract_rows(self.test_run.list(post_data))
        return {"runs": rows, "count": len(rows)}

    def list_failure_clusters(self, post_data: dict) -> dict[str, Any]:
        """List failure clusters matching an RS specification.

        Returns a dict with "failure_clusters" (list of row dicts) and "count".
        A slim projection is applied by default so AI callers do not receive
        large per-row payloads.  Pass ``"projection"`` in *post_data*
        (including ``None`` or ``[]``) to override.
        """
        post_data = apply_default_projection(post_data, FAILURE_CLUSTER_SLIM_PROJECTION)
        rows = _extract_rows(self.failure_cluster.list(post_data))
        return {"failure_clusters": rows, "count": len(rows)}

    def count_failure_clusters(self, post_data: dict) -> dict[str, Any]:
        """Count failure clusters matching an RS specification."""
        n = self.failure_cluster.count(post_data)
        return {"count": n}

    def count_runs(self, post_data: dict) -> dict[str, Any]:
        """Count runs matching an RS specification."""
        n = self.test_run.count(post_data)
        return {"count": n}

    def build_standard_runs_request(
        self,
        *,
        team: str | list[str] | tuple[str, ...],
        steppings: str | list[str] | tuple[str, ...],
        dut: str | list[str] | tuple[str, ...] | None = None,
        page_length: int = 100,
        page_offset: int = 0,
        skip_steppings: bool = False,
    ) -> tuple[dict[str, Any], tuple[str, ...], bool]:
        dut_values, was_derived = derive_dut_values(team=team, dut=dut)
        request = build_standard_runs_list_request(
            team=team,
            steppings=steppings,
            dut=dut_values,
            repo_root=str(self.repo_root),
            page_length=page_length,
            page_offset=page_offset,
            require_dut=True,
            skip_steppings=skip_steppings,
        )
        return request, dut_values, was_derived

    def get_run(self, run_id: int) -> dict[str, Any]:
        """Fetch a single run by integer ID.

        Returns the run dict, or an empty dict if no matching run is found.
        """
        post_data = {
            "filter": {
                "@c": ".AttValueFilter",
                "attName": "id",
                "attValue": run_id,
                "operand": "EQUALS",
            }
        }
        rows = _extract_rows(self.test_run.list(post_data))
        return rows[0] if rows else {}

    def get_failure_cluster(self, cluster_id: int) -> dict[str, Any]:
        """Fetch a single failure cluster by integer ID.

        Returns the cluster dict, or an empty dict if not found.
        """
        post_data = {
            "filter": {
                "@c": ".AttValueFilter",
                "attName": "id",
                "attValue": cluster_id,
                "operand": "EQUALS",
            }
        }
        rows = _extract_rows(self.failure_cluster.list(post_data))
        return rows[0] if rows else {}

    def list_sessions(self, post_data: dict) -> dict[str, Any]:
        """List VSIF sessions matching an RS specification.

        Returns a dict with "sessions" (list of row dicts) and "count".
        A slim projection is applied by default so AI callers do not receive
        large per-row payloads.  Pass ``"projection"`` in *post_data*
        (including ``None`` or ``[]``) to override.
        """
        post_data = apply_default_projection(post_data, SESSION_SLIM_PROJECTION)
        rows = _extract_rows(self.vsif_sessions.list(post_data))
        return {"sessions": rows, "count": len(rows)}

    def count_sessions(self, post_data: dict) -> dict[str, Any]:
        """Count VSIF sessions matching an RS specification.

        Falls back to a list-and-count when vsif_sessions does not expose a
        native count() method (the current vamp version does not).
        """
        count_fn = getattr(self.vsif_sessions, "count", None)
        if callable(count_fn):
            n = count_fn(post_data)
        else:
            n = len(_extract_rows(self.vsif_sessions.list(post_data)))
        return {"count": n}

    def list_plan_entries(self, post_data: dict) -> dict[str, Any]:
        """List test plan entries using the compatibility wrapper.

        When the underlying vamp TestPlanQueries object does not expose a
        generic list() method, this falls back to planning/list-sub-elements.
        Returns a dict with "plan_entries" (list of row dicts) and "count".
        """
        post_data = apply_default_projection(post_data, PLAN_SUB_ELEMENTS_SLIM_PROJECTION)
        plan_list = getattr(self.test_plan, "list", None)
        if callable(plan_list):
            rows = _extract_rows(plan_list(post_data))
        else:
            rows = self.list_plan_sub_elements(post_data)["sub_elements"]
        return {"plan_entries": rows, "count": len(rows)}

    def count_plan_entries(self, post_data: dict) -> dict[str, Any]:
        """Count test plan entries using the compatibility wrapper.

        If the backend does not expose a direct count() method, count the rows
        returned by planning/list-sub-elements instead.
        """
        plan_count = getattr(self.test_plan, "count", None)
        if callable(plan_count):
            n = plan_count(post_data)
            if n is not None:
                return {"count": n}

        n = self.list_plan_sub_elements(post_data)["count"]
        return {"count": n}

    def query_standard_runs(
        self,
        *,
        team: str | list[str] | tuple[str, ...],
        steppings: str | list[str] | tuple[str, ...],
        dut: str | list[str] | tuple[str, ...] | None = None,
        page_length: int = 100,
        page_offset: int = 0,
        skip_steppings: bool = False,
    ) -> dict[str, Any]:
        team_values = normalize_values(team, "team")
        stepping_values = normalize_values(steppings, "steppings")
        request, dut_values, dut_was_derived = self.build_standard_runs_request(
            team=team_values,
            steppings=stepping_values,
            dut=dut,
            page_length=page_length,
            page_offset=page_offset,
            skip_steppings=skip_steppings,
        )
        request = apply_default_projection(request, RUN_SLIM_PROJECTION)
        try:
            raw = self.test_run.list(request)
        except Exception as exc:
            raise RuntimeError(
                f"{exc}\n[ddgmcp] Request body sent:\n{json.dumps(request, indent=2, default=str)}"
            ) from exc
        rows = _extract_rows(raw)
        return {
            "request": request,
            "runs": rows,
            "count": len(rows),
            "team_profile": {
                "team_values": list(team_values),
                "stepping_values": list(stepping_values),
                "dut_values": list(dut_values),
                "dut_was_derived": dut_was_derived,
                "skip_steppings": skip_steppings,
                "team_kinds": {team_name: classify_team_name(team_name) for team_name in team_values},
            },
        }
