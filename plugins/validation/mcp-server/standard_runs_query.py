from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_FAILED_STATUSES = ("failed",)
DEFAULT_DEBUG_STATUSES = ("debugged_keep", "new", "wip")


@dataclass(frozen=True)
class StandardRunsQueryProfile:
    repo_family: str | None
    team_values: tuple[str, ...]
    stepping_values: tuple[str, ...]
    dut_values: tuple[str, ...]
    require_dut: bool
    status_values: tuple[str, ...] = DEFAULT_FAILED_STATUSES
    debug_status_values: tuple[str, ...] = DEFAULT_DEBUG_STATUSES
    require_for_indicators: bool = True


def infer_repo_family(repo_root: str | None) -> str | None:
    """Infer a repo-family label from the workspace path.

    Returns one of "TTL", "RZL", "NVL", "MTL", or None (unknown).
    The returned label is **informational only** — it identifies the design
    family so callers can tag queries or display context, but it does NOT
    control which vManager backend server the vamp client connects to.

    Deployment note (shared ``nvl`` database):
        In this environment, TTL, RZL, and NVL repos all connect to the
        **same** ``nvl`` vManager database.  A TTL or RZL workspace will
        return "TTL" or "RZL" here, but queries against it still hit the
        ``nvl`` backend — there is no separate TTL or RZL vManager instance.
        The vamp client URL is configured independently of this label.
    """
    if not repo_root:
        return None
    repo_path = str(Path(repo_root)).lower()
    if "/ttl/" in repo_path or "/ttlh78/" in repo_path:
        return "TTL"
    if "/rzl/" in repo_path:
        return "RZL"
    if "/nvl/" in repo_path:
        return "NVL"
    if "/mtl/" in repo_path:
        return "MTL"
    return None


def normalize_values(values: str | list[str] | tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if isinstance(values, str):
        normalized = (values,)
    else:
        normalized = tuple(value for value in values if value)
    if not normalized:
        raise ValueError(f"{field_name} must contain at least one value")
    return normalized


def resolve_standard_runs_query_profile(
    team: str | list[str] | tuple[str, ...],
    steppings: str | list[str] | tuple[str, ...],
    dut: str | list[str] | tuple[str, ...] | None = None,
    repo_root: str | None = None,
    require_dut: bool = False,
) -> StandardRunsQueryProfile:
    team_values = normalize_values(team, "team")
    stepping_values = normalize_values(steppings, "steppings")
    dut_values = normalize_values(dut, "dut") if dut is not None else ()
    if require_dut and not dut_values:
        teams = ", ".join(team_values)
        raise ValueError(f"dut is required for multi-dut team profile(s): {teams}")
    return StandardRunsQueryProfile(
        repo_family=infer_repo_family(repo_root),
        team_values=team_values,
        stepping_values=stepping_values,
        dut_values=dut_values,
        require_dut=require_dut,
    )


def _filter_key(discriminator: str) -> str:
    if discriminator not in {"c_type", "@c"}:
        raise ValueError("discriminator must be 'c_type' or '@c'")
    return discriminator


def _in_filter(att_name: str, values: tuple[str, ...], discriminator: str, operand: str = "IN") -> dict:
    return {
        _filter_key(discriminator): ".InFilter",
        "attName": att_name,
        "operand": operand,
        "values": list(values),
    }


def _att_value_filter(att_name: str, value, discriminator: str, operand: str = "EQUALS") -> dict:
    return {
        _filter_key(discriminator): ".AttValueFilter",
        "attName": att_name,
        "operand": operand,
        "attValue": value,
    }


def build_standard_runs_filter(
    team: str | list[str] | tuple[str, ...],
    steppings: str | list[str] | tuple[str, ...],
    dut: str | list[str] | tuple[str, ...] | None = None,
    repo_root: str | None = None,
    discriminator: str = "@c",
    debug_statuses: tuple[str, ...] = DEFAULT_DEBUG_STATUSES,
    statuses: tuple[str, ...] = DEFAULT_FAILED_STATUSES,
    require_for_indicators: bool = True,
    require_dut: bool = False,
    skip_steppings: bool = False,
) -> dict:
    profile = resolve_standard_runs_query_profile(
        team=team,
        steppings=steppings,
        dut=dut,
        repo_root=repo_root,
        require_dut=require_dut,
    )
    chain = [
        _in_filter("status", tuple(statuses), discriminator),
        _in_filter("i_team", profile.team_values, discriminator),
        _in_filter("i_debug_status", tuple(debug_statuses), discriminator),
    ]
    if profile.dut_values:
        chain.append(_in_filter("i_dut", profile.dut_values, discriminator))
    if not skip_steppings:
        chain.append(_in_filter("i_steps", profile.stepping_values, discriminator))
    if require_for_indicators:
        chain.append(_att_value_filter("i_for_indicators", True, discriminator))
    return {
        _filter_key(discriminator): ".ChainedFilter",
        "condition": "AND",
        "chain": chain,
    }


def build_standard_runs_list_request(
    team: str | list[str] | tuple[str, ...],
    steppings: str | list[str] | tuple[str, ...],
    dut: str | list[str] | tuple[str, ...] | None = None,
    repo_root: str | None = None,
    discriminator: str = "@c",
    page_length: int = 100,
    page_offset: int = 0,
    require_dut: bool = False,
    skip_steppings: bool = False,
) -> dict:
    return {
        "filter": build_standard_runs_filter(
            team=team,
            steppings=steppings,
            dut=dut,
            repo_root=repo_root,
            discriminator=discriminator,
            require_dut=require_dut,
            skip_steppings=skip_steppings,
        ),
        "pageLength": page_length,
        "pageOffset": page_offset,
        "settings": {"stream-mode": False},
    }