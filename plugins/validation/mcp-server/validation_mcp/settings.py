from __future__ import annotations

import getpass
import os
from dataclasses import dataclass, field, replace


SETTINGS_ENV_VARS = (
    "VAPI_BASE_PATH",
    "VMGR_USER",
    "VAPI_PASSWORD",
    "VMGR_TOKEN_PATH",
    "VAPI_VERIFY",
    "VALIDATION_MCP_MAX_PAGE_LENGTH",
    "VALIDATION_MCP_DEBUG_ERRORS",
    "VALIDATION_MCP_LOG_LEVEL",
    "VALIDATION_MCP_PRETTY_JSON",
)


def _read_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw_value!r}") from exc


def _read_positive_int(name: str, default: int) -> int:
    value = _read_int(name, default)
    if value < 1:
        raise ValueError(f"{name} must be >= 1, got {value!r}")
    return value


def _read_verify(name: str) -> bool | str | None:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return None

    normalized = raw_value.strip()
    if normalized == "":
        return None

    lowered = normalized.lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return normalized


def _default_username() -> str | None:
    try:
        return getpass.getuser()
    except (OSError, KeyError):
        return os.environ.get("USER") or os.environ.get("USERNAME")


@dataclass(frozen=True)
class Settings:
    repo_root: str
    api_base_path: str | None = None
    username: str | None = None
    password: str | None = field(default=None, repr=False)
    token_path: str | None = field(default=None, repr=False)
    verify: bool | str | None = None
    max_page_length: int = 100
    debug_errors: bool = False
    log_level: str = "INFO"
    pretty_json: bool = True
    # Internal-only experimental toggle. Do not expose via environment until
    # shared-client thread safety is verified.
    enable_client_cache: bool = False

    @classmethod
    def from_env(cls, repo_root: str) -> "Settings":
        return cls(
            repo_root=repo_root,
            api_base_path=os.environ.get("VAPI_BASE_PATH"),
            username=os.environ.get("VMGR_USER") or _default_username(),
            password=os.environ.get("VAPI_PASSWORD"),
            token_path=os.environ.get("VMGR_TOKEN_PATH"),
            verify=_read_verify("VAPI_VERIFY"),
            max_page_length=_read_positive_int("VALIDATION_MCP_MAX_PAGE_LENGTH", 100),
            debug_errors=_read_bool("VALIDATION_MCP_DEBUG_ERRORS", False),
            log_level=os.environ.get("VALIDATION_MCP_LOG_LEVEL", "INFO"),
            pretty_json=_read_bool("VALIDATION_MCP_PRETTY_JSON", True),
        )

    def with_overrides(self, **kwargs: object) -> "Settings":
        return replace(self, **kwargs)


SettingsOrRepoRoot = Settings | str