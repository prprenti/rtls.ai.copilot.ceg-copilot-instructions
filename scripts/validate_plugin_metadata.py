#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

FORBIDDEN_PUBLISHED_FIELDS = {
    "capabilities",
    "capabilityId",
    "executionClass",
    "componentRef",
    "endpointRef",
}
COMPONENT_FIELDS = ("agents", "skills", "commands", "mcpServers", "lspServers")
MARKETPLACE_METADATA_FIELDS = (
    "name",
    "description",
    "version",
    "keywords",
    "category",
    "tags",
)
PROMOTED_MARKETPLACE_FIELDS = (
    "keywords",
    "category",
    "tags",
    *COMPONENT_FIELDS,
)
PLUGIN_FIELD_ORDER = (
    "name",
    "description",
    "version",
    "keywords",
    "category",
    "tags",
    "agents",
    "skills",
    "commands",
    "mcpServers",
    "lspServers",
)
MARKETPLACE_PLUGIN_FIELD_ORDER = (
    "name",
    "description",
    "version",
    "keywords",
    "category",
    "tags",
    "source",
    "agents",
    "skills",
    "commands",
    "mcpServers",
    "lspServers",
)
MARKETPLACE_MIRRORED_FIELDS = (
    "name",
    "description",
    "version",
    *PROMOTED_MARKETPLACE_FIELDS,
)
DEFAULT_THIS_REPO = "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions"
IGNORED_PATH_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
}
MARKETPLACE_PATH = Path(".github") / "plugin" / "marketplace.json"
PLUGIN_PATH = Path("plugin.json")
DESCRIPTION_MIN_LENGTH = 20
NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?$")
STRICT_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?"
    r"(?:\+[0-9A-Za-z.-]+)?$"
)


class Violation:
    def __init__(self, path: str, message: str) -> None:
        self.path = path
        self.message = message

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Violation):
            return NotImplemented
        return self.path == other.path and self.message == other.message

    def __repr__(self) -> str:
        return f"Violation(path={self.path!r}, message={self.message!r})"


class RunResult:
    def __init__(self) -> None:
        self.changed: set[Path] = set()
        self.violations: list[Violation] = []
        self.warnings: list[str] = []

    def fail(self, path: Path | str, message: str) -> None:
        self.violations.append(Violation(str(path), message))

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def merge_result_as_warnings(target: RunResult, source: RunResult) -> None:
    for violation in source.violations:
        target.warn(f"{violation.path}: {violation.message}")
    target.warnings.extend(source.warnings)


def format_validation_message(subject: str | None, message: str) -> str:
    return f"{subject}: {message}" if subject else message


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: JSON root must be an object")
    return data


def detect_repo_mode(root: Path) -> str | None:
    if (root / MARKETPLACE_PATH).is_file():
        return "marketplace"
    if (root / PLUGIN_PATH).is_file():
        return "plugin"
    return None


def resolve_repo_root(explicit_root: Path | None, script_path: Path) -> Path:
    if explicit_root is not None:
        return explicit_root.resolve()

    seen: set[Path] = set()
    search_roots = [Path.cwd().resolve(), script_path.resolve().parent.parent]
    for start in search_roots:
        for candidate in (start, *start.parents):
            if candidate in seen:
                continue
            seen.add(candidate)
            if detect_repo_mode(candidate) is not None:
                return candidate

    raise ValueError(
        "Could not locate a repository root containing .github/plugin/marketplace.json "
        "or plugin.json. Use --repo-root to select one explicitly."
    )


def resolve_mode(root: Path, requested_mode: str) -> str:
    detected_mode = detect_repo_mode(root)
    if requested_mode == "auto":
        if detected_mode is None:
            raise ValueError(
                f"{root}: could not determine mode automatically because neither "
                ".github/plugin/marketplace.json nor plugin.json exists."
            )
        return detected_mode
    if requested_mode == "marketplace":
        if detected_mode != "marketplace":
            raise ValueError(f"{root}: marketplace mode requires .github/plugin/marketplace.json")
        return requested_mode
    if detected_mode != "plugin":
        raise ValueError(f"{root}: plugin mode requires a root-level plugin.json")
    return requested_mode


def _parse_dotenv_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith("export "):
        stripped = stripped[len("export ") :].strip()
    if "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    name = key.strip()
    if not name:
        return None
    raw_value = value.strip()
    if len(raw_value) >= 2 and raw_value[0] == raw_value[-1] and raw_value[0] in {"'", '"'}:
        raw_value = raw_value[1:-1]
    return name, raw_value


def load_repo_dotenv(root: Path) -> None:
    dotenv_path = root / ".env"
    if not dotenv_path.is_file():
        return
    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_dotenv_line(line)
        if parsed is None:
            continue
        name, value = parsed
        os.environ.setdefault(name, value)


def ordered_dict(data: dict[str, Any], field_order: tuple[str, ...]) -> dict[str, Any]:
    ordered: dict[str, Any] = {}
    for key in field_order:
        if key in data:
            ordered[key] = data[key]
    for key, value in data.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def write_json_if_changed(path: Path, data: dict[str, Any], result: RunResult) -> None:
    rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current != rendered:
        path.write_text(rendered, encoding="utf-8")
        result.changed.add(path)


def normalize_rel_path(path_text: str) -> str:
    raw = path_text.strip()
    if not raw:
        raise ValueError("path must not be empty")
    path = PurePosixPath(raw)
    if path.is_absolute():
        raise ValueError("path must be relative")
    parts: list[str] = []
    for part in path.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            raise ValueError("path must not escape the plugin root")
        parts.append(part)
    if not parts:
        raise ValueError("path must not normalize to the plugin root")
    return "/".join(parts)


def normalize_optional_root_path(path_text: str) -> str:
    raw = path_text.strip()
    if not raw:
        return ""
    path = PurePosixPath(raw)
    if not [part for part in path.parts if part not in {"", "."}]:
        return ""
    return normalize_rel_path(raw)


def validated_component_refs(
    path: Path | str,
    field_name: str,
    value: object,
    result: RunResult,
) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            result.fail(path, f"{field_name} must not be empty")
            return []
        return [stripped]
    if not isinstance(value, list):
        result.fail(path, f"{field_name} must be a string or list of strings")
        return []

    refs: list[str] = []
    for item in value:
        if not isinstance(item, str):
            result.fail(path, f"{field_name} entries must be strings: {item!r}")
            continue
        stripped = item.strip()
        if not stripped:
            result.fail(path, f"{field_name} entries must not be empty strings")
            continue
        refs.append(stripped)
    return refs


def is_remote_url_source(source: str) -> bool:
    return source.startswith(("http://", "https://", "git@"))


def is_local_path_source(source: str) -> bool:
    return source.startswith((".", "/", "plugins/"))


def parse_github_repo_identifier(repo_text: str) -> str | None:
    raw = repo_text.strip().rstrip("/")
    if not raw or not GITHUB_REPO_RE.fullmatch(raw):
        return None
    return raw.removesuffix(".git")


def parse_github_source_string(source: str) -> tuple[str, str] | None:
    raw = source.strip()
    if not raw or is_remote_url_source(raw):
        return None
    if ":" in raw:
        repo_part, path_part = raw.split(":", 1)
        repo = parse_github_repo_identifier(repo_part)
        if repo is not None and path_part.strip():
            return repo, path_part.strip()
        return None
    if not is_local_path_source(raw):
        repo = parse_github_repo_identifier(raw)
        if repo is not None:
            return repo, ""
    return None


def resolve_repo_relative_path(root: Path, path_text: str) -> Path:
    normalized_path = normalize_optional_root_path(path_text)
    return root / normalized_path if normalized_path else root


def resolve_local_source_with_error(
    root: Path,
    source: object,
    this_repo: str,
) -> tuple[Path | None, str | None]:
    if isinstance(source, str):
        if is_remote_url_source(source):
            repo = github_repo_from_url(source)
            if repo is None or repo.lower() != this_repo.lower():
                return None, None
            return root, None
        github_source = parse_github_source_string(source)
        if github_source is not None:
            repo, path = github_source
            if repo.lower() != this_repo.lower():
                return None, None
            try:
                return resolve_repo_relative_path(root, path), None
            except ValueError as exc:
                return None, f"same-repository source path {path!r}: {exc}"
        try:
            return resolve_repo_relative_path(root, source), None
        except ValueError as exc:
            return None, f"local source path {source!r}: {exc}"
    if isinstance(source, dict):
        source_type = source.get("source")
        if source_type is not None and not isinstance(source_type, str):
            return None, None
        if (source_type or "").strip().lower() != "github":
            return None, None
        repo_value = source.get("repo", "")
        path_value = source.get("path", "")
        if repo_value is not None and not isinstance(repo_value, str):
            return None, None
        if path_value is not None and not isinstance(path_value, str):
            return None, None
        repo = repo_value.strip() if isinstance(repo_value, str) else ""
        path = path_value.strip() if isinstance(path_value, str) else ""
        if repo.lower() != this_repo.lower():
            return None, None
        try:
            return resolve_repo_relative_path(root, path), None
        except ValueError as exc:
            return None, f"same-repository source path {path!r}: {exc}"
    return None, None


def ignored_path(path: Path) -> bool:
    return any(part in IGNORED_PATH_PARTS for part in path.parts)


def is_metadata_only_component_ref(ref: str) -> bool:
    stripped = ref.strip()
    if not stripped:
        return False
    if stripped in {".", "./", "agents", "agents/", "skills", "skills/", "commands", "commands/"}:
        return True
    return stripped.endswith("/")


def explicit_agent_refs(plugin_root: Path) -> list[str]:
    return sorted(
        path.relative_to(plugin_root).as_posix()
        for path in plugin_root.rglob("*.agent.md")
        if path.is_file() and not ignored_path(path)
    )


def explicit_skill_refs(plugin_root: Path) -> list[str]:
    skills_root = plugin_root / "skills"
    if not skills_root.is_dir():
        return []
    return sorted(
        path.parent.relative_to(plugin_root).as_posix()
        for path in skills_root.rglob("SKILL.md")
        if path.is_file() and not ignored_path(path)
    )


def explicit_command_refs(plugin_root: Path) -> list[str]:
    commands_root = plugin_root / "commands"
    if not commands_root.is_dir():
        return []
    return sorted(
        path.relative_to(plugin_root).as_posix()
        for path in commands_root.rglob("*.md")
        if path.is_file() and not ignored_path(path)
    )


def expected_component_updates(plugin_root: Path) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    agents = explicit_agent_refs(plugin_root)
    skills = explicit_skill_refs(plugin_root)
    commands = explicit_command_refs(plugin_root)
    if agents:
        updates["agents"] = agents
    if skills:
        updates["skills"] = skills
    if commands:
        updates["commands"] = commands
    if (plugin_root / ".mcp.json").is_file():
        updates["mcpServers"] = ".mcp.json"
    if (plugin_root / ".lsp.json").is_file():
        updates["lspServers"] = ".lsp.json"
    return updates


def validate_required_plugin_fields(
    path: Path | str,
    data: dict[str, Any],
    result: RunResult,
) -> None:
    validate_metadata_fields(
        path,
        data,
        result,
        required_fields=("name", "description", "version", "keywords"),
        require_keywords=True,
        version_pattern=STRICT_SEMVER_RE,
        version_requirement="semantic version (X.Y.Z)",
    )


def validate_metadata_fields(
    path: Path | str,
    data: dict[str, Any],
    result: RunResult,
    *,
    required_fields: tuple[str, ...],
    require_keywords: bool,
    version_pattern: re.Pattern[str] = SEMVER_RE,
    version_requirement: str = "semver",
) -> None:
    for key in required_fields:
        if key not in data:
            result.fail(path, f"missing required field {key!r}")
    name = data.get("name")
    if "name" in data:
        if not isinstance(name, str) or not name.strip():
            result.fail(path, "name must be a non-empty string")
        else:
            stripped_name = name.strip()
            if stripped_name != name:
                result.fail(path, "name must not have leading or trailing whitespace")
            if not NAME_RE.fullmatch(stripped_name):
                result.fail(path, f"name must be kebab-case, lowercase, and at most 64 characters: {name!r}")

    description = data.get("description")
    if "description" in data:
        if not isinstance(description, str) or not description.strip():
            result.fail(path, "description must be a non-empty string")
        elif len(description.strip()) < DESCRIPTION_MIN_LENGTH:
            result.fail(path, f"description must be at least {DESCRIPTION_MIN_LENGTH} characters")

    version = data.get("version")
    if "version" in data:
        if not isinstance(version, str) or not version.strip():
            result.fail(path, "version must be a non-empty string")
        elif not version_pattern.fullmatch(version.strip()):
            result.fail(path, f"version must be {version_requirement}: {version!r}")

    if "keywords" not in data and not require_keywords:
        return
    if not isinstance(data.get("keywords"), list) or not data.get("keywords"):
        result.fail(path, "keywords must be a non-empty list")
    for keyword in data.get("keywords", []):
        if not isinstance(keyword, str) or not keyword.strip():
            result.fail(path, f"invalid keyword {keyword!r}")
        elif keyword != keyword.lower():
            result.fail(path, f"keyword must be lowercase: {keyword!r}")


def validate_required_marketplace_entry_fields(
    path: Path | str,
    data: dict[str, Any],
    result: RunResult,
) -> None:
    validate_metadata_fields(
        path,
        data,
        result,
        required_fields=("name", "description", "version", "source"),
        require_keywords=False,
        version_pattern=SEMVER_RE,
        version_requirement="semver",
    )
    if "source" in data:
        source = data.get("source")
        if source is None:
            result.fail(path, "source must not be empty")
        elif isinstance(source, str) and not source.strip():
            result.fail(path, "source must not be empty")
        elif isinstance(source, dict) and not source:
            result.fail(path, "source must not be empty")


def validate_component_ref_kind(
    path: Path | str,
    field_name: str,
    ref: str,
    normalized_ref: str,
    result: RunResult,
) -> bool:
    if field_name == "agents" and not normalized_ref.endswith(".agent.md"):
        result.fail(path, f"{field_name} ref {ref!r} must point to an explicit .agent.md file")
        return False
    if field_name == "skills" and not re.fullmatch(r"skills/[a-z0-9][a-z0-9-]*", normalized_ref):
        result.fail(path, f"{field_name} ref {ref!r} must be a skill directory path (e.g. skills/my-skill)")
        return False
    if field_name == "commands" and not normalized_ref.endswith(".md"):
        result.fail(path, f"{field_name} ref {ref!r} must point to an explicit .md file")
        return False
    return True


def reject_forbidden_fields(
    path: Path | str,
    data: dict[str, Any],
    result: RunResult,
) -> None:
    for key in sorted(FORBIDDEN_PUBLISHED_FIELDS & set(data)):
        result.fail(
            path,
            f"published plugin metadata must not include consumer-private field {key!r}",
        )


def validate_explicit_component_refs(
    path: Path | str,
    plugin_root: Path,
    data: dict[str, Any],
    result: RunResult,
) -> None:
    for field_name in ("agents", "skills", "commands"):
        for ref in validated_component_refs(path, field_name, data.get(field_name), result):
            if is_metadata_only_component_ref(ref):
                result.fail(
                    path,
                    f"{field_name} ref {ref!r} is metadata-only; use explicit files",
                )
                continue
            try:
                normalized = normalize_rel_path(ref)
            except ValueError as exc:
                result.fail(path, f"{field_name} ref {ref!r}: {exc}")
                continue
            if not validate_component_ref_kind(path, field_name, ref, normalized, result):
                continue
            target = plugin_root / normalized
            if field_name == "skills":
                if not (target / "SKILL.md").is_file():
                    result.fail(path, f"{field_name} ref {ref!r} does not contain a SKILL.md")
            elif not target.is_file():
                result.fail(path, f"{field_name} ref {ref!r} does not exist")
    for field_name in ("mcpServers", "lspServers"):
        value = data.get(field_name)
        if isinstance(value, dict):
            result.fail(
                path,
                (
                    f"inline {field_name} is metadata-only in published plugin metadata; "
                    "use a manifest path for inspection"
                ),
            )
            continue
        for ref in validated_component_refs(path, field_name, value, result):
            try:
                normalized = normalize_rel_path(ref)
            except ValueError as exc:
                result.fail(path, f"{field_name} ref {ref!r}: {exc}")
                continue
            if not (plugin_root / normalized).is_file():
                result.fail(path, f"{field_name} ref {ref!r} does not exist")


def validate_current_matches_expected(
    path: Path,
    current: dict[str, Any],
    expected: dict[str, Any],
    keys: tuple[str, ...],
    result: RunResult,
    *,
    generator_owner: str | None = None,
    omission_reason: str = "should be omitted",
    subject: str | None = None,
) -> None:
    for key in keys:
        if key in expected and current.get(key) != expected[key]:
            if generator_owner is not None:
                result.fail(path, format_validation_message(subject, (
                    f"{key} should be {expected[key]!r}; local marketplace entries are generated "
                    f"from {generator_owner}"
                )))
            else:
                result.fail(path, format_validation_message(subject, f"{key} should be {expected[key]!r}"))
        if key not in expected and key in current:
            if generator_owner is not None:
                result.fail(path, format_validation_message(subject, (
                    f"{key} should be omitted because local marketplace entries are generated "
                    f"from {generator_owner}"
                )))
            else:
                result.fail(path, format_validation_message(subject, f"{key} {omission_reason}"))


def with_generated_component_fields(data: dict[str, Any], component_updates: dict[str, Any]) -> dict[str, Any]:
    rewritten = {
        key: value
        for key, value in data.items()
        if key not in COMPONENT_FIELDS
    }
    rewritten.update(component_updates)
    return rewritten


def apply_local_plugin_requirements(
    plugin_root: Path,
    *,
    apply: bool,
    result: RunResult,
) -> dict[str, Any]:
    manifest_path = plugin_root / "plugin.json"
    data = load_json(manifest_path)
    initial_violation_count = len(result.violations)
    validate_required_plugin_fields(manifest_path, data, result)
    reject_forbidden_fields(manifest_path, data, result)

    component_updates = expected_component_updates(plugin_root)
    expected = with_generated_component_fields(data, component_updates)
    validate_explicit_component_refs(manifest_path, plugin_root, expected, result)
    if apply and len(result.violations) == initial_violation_count:
        rewritten = with_generated_component_fields(data, component_updates)
        write_json_if_changed(
            manifest_path,
            ordered_dict(rewritten, PLUGIN_FIELD_ORDER),
            result,
        )
        return ordered_dict(rewritten, PLUGIN_FIELD_ORDER)

    validate_current_matches_expected(
        manifest_path,
        data,
        expected,
        COMPONENT_FIELDS,
        result,
        omission_reason="should be omitted because no matching files exist",
    )
    return ordered_dict(expected, PLUGIN_FIELD_ORDER)


def resolve_local_source(root: Path, source: object, this_repo: str) -> Path | None:
    resolved, _error = resolve_local_source_with_error(root, source, this_repo)
    return resolved


def mirrored_marketplace_fields_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        key: manifest[key]
        for key in MARKETPLACE_MIRRORED_FIELDS
        if key in manifest
    }


def promoted_marketplace_entry(
    entry: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    promoted = {
        key: value
        for key, value in entry.items()
        if key not in MARKETPLACE_MIRRORED_FIELDS
    }
    promoted.update(mirrored_marketplace_fields_from_manifest(manifest))
    return ordered_dict(promoted, MARKETPLACE_PLUGIN_FIELD_ORDER)


def local_marketplace_manifest_label(plugin_dir: Path, root: Path) -> str:
    return str((plugin_dir / "plugin.json").relative_to(root))


def validate_marketplace_metadata_matches_manifest(
    path: Path,
    entry: dict[str, Any],
    manifest: dict[str, Any],
    result: RunResult,
    *,
    subject: str | None = None,
    generator_owner: str | None = None,
    omission_reason: str = "should be omitted because the manifest does not declare it",
) -> None:
    validate_current_matches_expected(
        path,
        entry,
        mirrored_marketplace_fields_from_manifest(manifest),
        MARKETPLACE_METADATA_FIELDS,
        result,
        generator_owner=generator_owner,
        omission_reason=omission_reason,
        subject=subject,
    )


def bump_marketplace_patch_version(marketplace: dict[str, Any]) -> None:
    metadata = marketplace.get("metadata")
    if metadata is None:
        metadata = {}
        marketplace["metadata"] = metadata
    elif not isinstance(metadata, dict):
        raise ValueError("marketplace metadata must be an object")
    version = str(metadata.get("version", "0.0.0"))
    parts = version.split(".")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        parts[2] = str(int(parts[2]) + 1)
        metadata["version"] = ".".join(parts)


def discover_local_manifests(
    root: Path,
    *,
    apply: bool,
    result: RunResult,
) -> dict[str, tuple[Path, dict[str, Any]]]:
    plugins_root = root / "plugins"
    if not plugins_root.is_dir():
        return {}
    manifests: dict[str, tuple[Path, dict[str, Any]]] = {}
    for plugin_dir in sorted(plugins_root.iterdir()):
        manifest_path = plugin_dir / "plugin.json"
        if not plugin_dir.is_dir() or not manifest_path.is_file():
            continue
        manifest = apply_local_plugin_requirements(
            plugin_dir,
            apply=apply,
            result=result,
        )
        name = manifest.get("name")
        if isinstance(name, str) and name:
            if name in manifests:
                existing_dir, _existing_manifest = manifests[name]
                result.fail(
                    manifest_path,
                    f"duplicate local plugin name {name!r}; already declared in {existing_dir / 'plugin.json'}",
                )
                continue
            manifests[name] = (plugin_dir, manifest)
    return manifests


def validate_external_marketplace_source(
    path: Path,
    name: str,
    source: object,
    result: RunResult,
) -> tuple[str, str, str] | None:
    if isinstance(source, dict) and not validate_source_object_string_fields(path, name, source, result):
        return None
    remote = remote_source_parts(source)
    if remote is None:
        result.fail(path, f"{name}: source must be a supported local path or GitHub source")
        return None
    repo, ref, plugin_path = remote
    if not repo:
        result.fail(path, f"{name}: source repo must not be empty")
        return None
    try:
        normalize_optional_root_path(plugin_path)
    except ValueError as exc:
        result.fail(path, f"{name}: external source path {plugin_path!r}: {exc}")
        return None
    return repo, ref or "", plugin_path


def validate_source_object_string_fields(
    path: Path | str,
    subject: str,
    source: dict[str, Any],
    result: RunResult,
) -> bool:
    valid = True
    for field_name in ("source", "repo", "path", "url", "ref", "sha", "commit"):
        value = source.get(field_name)
        if value is None or isinstance(value, str):
            continue
        result.fail(path, format_validation_message(subject, f"source.{field_name} must be a string"))
        valid = False
    return valid


def apply_marketplace_requirements(
    root: Path,
    args: argparse.Namespace,
    result: RunResult,
) -> None:
    marketplace_path = root / ".github" / "plugin" / "marketplace.json"
    marketplace = load_json(marketplace_path)
    metadata = marketplace.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        result.fail(marketplace_path, "metadata must be an object")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        result.fail(marketplace_path, "plugins must be a list")
        return

    local_manifests = discover_local_manifests(root, apply=False, result=result)
    local_manifests_by_dir = {
        plugin_dir.resolve(): (name, manifest)
        for name, (plugin_dir, manifest) in local_manifests.items()
    }
    seen: set[str] = set()
    original_plugins = json.dumps(plugins, sort_keys=True, separators=(",", ":"))
    updated_plugins: list[dict[str, Any]] = []

    for raw_entry in plugins:
        if not isinstance(raw_entry, dict):
            result.fail(marketplace_path, "plugin entries must be objects")
            continue
        entry = dict(raw_entry)
        validate_required_marketplace_entry_fields(marketplace_path, entry, result)
        name = str(entry.get("name", "")).strip()
        if not name:
            result.fail(marketplace_path, "plugin entry missing name")
            continue
        if name in seen:
            result.fail(marketplace_path, f"duplicate plugin entry {name!r}")
        seen.add(name)
        reject_forbidden_fields(marketplace_path, entry, result)
        source = entry.get("source")
        local_root, local_source_error = resolve_local_source_with_error(root, source, args.this_repo)
        if local_source_error is not None:
            result.fail(marketplace_path, f"{name}: {local_source_error}")
            updated_plugins.append(ordered_dict(entry, MARKETPLACE_PLUGIN_FIELD_ORDER))
            continue
        if local_root is not None:
            resolved_local_root = local_root.resolve()
            local_manifest_entry = local_manifests_by_dir.get(resolved_local_root)
            if local_manifest_entry is None:
                result.fail(
                    marketplace_path,
                    f"{name}: source resolves to {resolved_local_root.relative_to(root)} but no local plugin.json was found there",
                )
                updated_plugins.append(ordered_dict(entry, MARKETPLACE_PLUGIN_FIELD_ORDER))
                continue
            resolved_name, manifest = local_manifest_entry
            if resolved_name != name:
                result.fail(
                    marketplace_path,
                    (
                        f"{name}: source resolves to {resolved_local_root.relative_to(root)}/plugin.json "
                        f"for plugin {resolved_name!r}"
                    ),
                )
                updated_plugins.append(ordered_dict(entry, MARKETPLACE_PLUGIN_FIELD_ORDER))
                continue
            plugin_dir = resolved_local_root
            desired_entry = promoted_marketplace_entry(entry, manifest)
            if not args.apply:
                validate_marketplace_metadata_matches_manifest(
                    marketplace_path,
                    entry,
                    manifest,
                    result,
                    subject=name,
                    generator_owner=local_marketplace_manifest_label(plugin_dir, root),
                )
                validate_current_matches_expected(
                    marketplace_path,
                    entry,
                    desired_entry,
                    COMPONENT_FIELDS,
                    result,
                    generator_owner=local_marketplace_manifest_label(plugin_dir, root),
                    subject=name,
                )
            updated_plugins.append(desired_entry if args.apply else entry)
        else:
            remote = validate_external_marketplace_source(marketplace_path, name, source, result)
            if args.check_remotes and remote is not None:
                validate_remote_source(entry, args, result, marketplace_path, remote=remote)
            updated_plugins.append(ordered_dict(entry, MARKETPLACE_PLUGIN_FIELD_ORDER))

    for name in sorted(set(local_manifests) - seen):
        result.fail(marketplace_path, f"local plugin {name!r} is missing from marketplace")

    if args.apply and not result.violations:
        discover_local_manifests(root, apply=True, result=result)
        marketplace["plugins"] = updated_plugins
        new_plugins = json.dumps(updated_plugins, sort_keys=True, separators=(",", ":"))
        if new_plugins != original_plugins:
            bump_marketplace_patch_version(marketplace)
        write_json_if_changed(marketplace_path, marketplace, result)


def remote_source_parts(source: object) -> tuple[str, str | None, str] | None:
    if isinstance(source, str):
        if is_remote_url_source(source):
            repo = github_repo_from_url(source)
            if not repo:
                return None
            return repo, None, ""
        github_source = parse_github_source_string(source)
        if github_source is None:
            return None
        repo, path = github_source
        return repo, None, path
    if not isinstance(source, dict):
        return None
    source_type_value = source.get("source", "")
    if source_type_value is not None and not isinstance(source_type_value, str):
        return None
    source_type = source_type_value.lower() if isinstance(source_type_value, str) else ""

    ref: str | None = None
    for field_name in ("sha", "commit", "ref"):
        value = source.get(field_name)
        if value is None:
            continue
        if not isinstance(value, str):
            return None
        stripped = value.strip()
        if stripped:
            ref = stripped
            break
    if source_type == "github":
        repo_value = source.get("repo", "")
        path_value = source.get("path", "")
        if repo_value is not None and not isinstance(repo_value, str):
            return None
        if path_value is not None and not isinstance(path_value, str):
            return None
        repo = repo_value.strip() if isinstance(repo_value, str) else ""
        path = path_value.strip() if isinstance(path_value, str) else ""
        return repo, ref, path
    if source_type in {"git-subdir", "url"}:
        url_value = source.get("url", "")
        if url_value is not None and not isinstance(url_value, str):
            return None
        repo = github_repo_from_url(url_value if isinstance(url_value, str) else "")
        if not repo:
            return None
        path_value = source.get("path", "")
        if path_value is not None and not isinstance(path_value, str):
            return None
        path = path_value.strip() if source_type == "git-subdir" and isinstance(path_value, str) else ""
        return repo, ref, path
    return None


def github_repo_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    if (parsed.hostname or "").lower() != "github.com":
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        return None
    return parse_github_repo_identifier(f"{parts[0]}/{parts[1]}")


def github_contents_api_url(repo: str, ref: str, path: str) -> str:
    suffix = normalize_optional_root_path(path) or "plugin.json"
    encoded_suffix = quote(suffix, safe="/")
    query = urlencode({"ref": ref})
    return f"https://api.github.com/repos/{repo}/contents/{encoded_suffix}?{query}"


def plugin_manifest_api_url(repo: str, ref: str, plugin_path: str) -> str:
    normalized_plugin_path = normalize_optional_root_path(plugin_path)
    suffix = f"{normalized_plugin_path}/plugin.json" if normalized_plugin_path else "plugin.json"
    return github_contents_api_url(repo, ref, suffix)


def fetch_remote_json(url: str, *, token: str) -> dict[str, Any]:
    headers = {"Accept": "application/vnd.github.raw+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=20) as response:
        text = response.read().decode("utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("remote JSON root must be an object")
    return data


def fetch_remote_text(url: str, *, token: str) -> None:
    headers = {"Accept": "application/vnd.github.raw"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=20) as response:
        response.read(1)


def fetch_remote_api_json(url: str, *, token: str) -> Any:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=20) as response:
        text = response.read().decode("utf-8")
    return json.loads(text)


def resolve_remote_symlinked_path(
    *,
    repo: str,
    ref: str,
    remote_path: str,
    token: str,
) -> str | None:
    parts = [part for part in remote_path.split("/") if part]
    if not parts:
        return None

    # Probe each prefix; if a prefix is a git symlink, resolve it and rebuild the path.
    for idx in range(1, len(parts) + 1):
        prefix = "/".join(parts[:idx])
        url = github_contents_api_url(repo, ref, prefix)
        try:
            payload = fetch_remote_api_json(url, token=token)
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
            continue

        if not isinstance(payload, dict):
            continue

        if payload.get("type") != "symlink":
            continue

        target_raw = str(payload.get("target", "")).strip()
        if not target_raw:
            return None

        base_dir = "/".join(parts[: idx - 1])
        target_path = PurePosixPath(base_dir) / target_raw if base_dir else PurePosixPath(target_raw)
        try:
            resolved_prefix = normalize_rel_path(str(target_path))
        except ValueError:
            return None

        suffix = "/".join(parts[idx:])
        return f"{resolved_prefix}/{suffix}" if suffix else resolved_prefix

    return None


def validate_remote_component_refs(
    *,
    manifest_url: str,
    repo: str,
    ref: str,
    plugin_path: str,
    data: dict[str, Any],
    token: str,
    result: RunResult,
    strict_metadata: bool = True,
) -> None:
    normalized_plugin_path = normalize_optional_root_path(plugin_path)
    for field_name in COMPONENT_FIELDS:
        value = data.get(field_name)
        if isinstance(value, dict):
            message = (
                f"inline {field_name} is metadata-only in published plugin metadata; "
                "use a manifest path"
            )
            if strict_metadata:
                result.fail(f"remote:{manifest_url}", message)
            else:
                result.warn(f"remote:{manifest_url}: {message}")
            continue
        for component_ref in validated_component_refs(f"remote:{manifest_url}", field_name, value, result):
            if is_metadata_only_component_ref(component_ref):
                message = f"{field_name} ref {component_ref!r} is metadata-only; use explicit files"
                if strict_metadata:
                    result.fail(f"remote:{manifest_url}", message)
                else:
                    result.warn(f"remote:{manifest_url}: {message}")
                continue
            try:
                normalized_ref = normalize_rel_path(component_ref)
            except ValueError as exc:
                result.fail(f"remote:{manifest_url}", f"{field_name} ref {component_ref!r}: {exc}")
                continue
            if not validate_component_ref_kind(
                f"remote:{manifest_url}",
                field_name,
                component_ref,
                normalized_ref,
                result,
            ):
                continue
            remote_path = f"{normalized_plugin_path}/{normalized_ref}" if normalized_plugin_path else normalized_ref
            url = github_contents_api_url(repo, ref, remote_path)
            try:
                fetch_remote_text(url, token=token)
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                symlink_target = None
                if isinstance(exc, HTTPError) and exc.code == 404:
                    symlink_target = resolve_remote_symlinked_path(
                        repo=repo,
                        ref=ref,
                        remote_path=remote_path,
                        token=token,
                    )
                    if symlink_target:
                        try:
                            fetch_remote_text(github_contents_api_url(repo, ref, symlink_target), token=token)
                            continue
                        except (HTTPError, URLError, TimeoutError, OSError):
                            pass

                if symlink_target:
                    result.fail(
                        f"remote:{manifest_url}",
                        f"{field_name} ref {component_ref!r} is not fetchable: {exc}; also failed via symlink-resolved path {symlink_target!r}",
                    )
                else:
                    result.fail(f"remote:{manifest_url}", f"{field_name} ref {component_ref!r} is not fetchable: {exc}")


def validate_remote_source(
    entry: dict[str, Any],
    args: argparse.Namespace,
    result: RunResult,
    path: Path,
    *,
    remote: tuple[str, str, str] | None = None,
) -> None:
    entry_name = str(entry.get("name", "")).strip() or "remote plugin"
    source = entry.get("source")
    if remote is None and isinstance(source, dict):
        source_result = RunResult()
        if not validate_source_object_string_fields(path, entry_name, source, source_result):
            merge_result_as_warnings(result, source_result)
            return

    resolved_remote = remote or remote_source_parts(source)
    if resolved_remote is None:
        return
    repo, ref, plugin_path = resolved_remote
    if not ref:
        result.warn(f"{entry_name}: external source needs ref, sha, or commit for remote fetchability")
        return
    token = os.getenv(args.github_token_env, "")
    manifest_url = plugin_manifest_api_url(repo, ref, plugin_path)
    try:
        data = fetch_remote_json(manifest_url, token=token)
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as exc:
        result.warn(f"{entry_name}: failed to fetch remote plugin.json from {manifest_url}: {exc}")
        return
    remote_result = RunResult()
    validate_required_plugin_fields(
        f"remote:{manifest_url}",
        data,
        remote_result,
    )
    reject_forbidden_fields(f"remote:{manifest_url}", data, remote_result)
    validate_marketplace_metadata_matches_manifest(
        path,
        entry,
        data,
        remote_result,
        subject=entry_name,
        omission_reason=f"should be omitted because remote plugin.json at {manifest_url} does not declare it",
    )
    validate_remote_component_refs(
        manifest_url=manifest_url,
        repo=repo,
        ref=ref,
        plugin_path=plugin_path,
        data=data,
        token=token,
        result=remote_result,
        strict_metadata=True,
    )
    merge_result_as_warnings(result, remote_result)


def build_marketplace_entry(
    manifest: dict[str, Any],
    *,
    repo: str = "OWNER/REPO",
    ref: str = "",
    path: str = "",
) -> dict[str, Any]:
    source: dict[str, str] = {"source": "github", "repo": repo.strip() or "OWNER/REPO"}
    if ref:
        source["ref"] = ref
    normalized_path = normalize_optional_root_path(path)
    if normalized_path:
        source["path"] = normalized_path
    entry = mirrored_marketplace_fields_from_manifest(manifest)
    entry["source"] = source
    return ordered_dict(entry, MARKETPLACE_PLUGIN_FIELD_ORDER)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate or apply published plugin metadata requirements for a plugin marketplace "
            "repository or a single plugin repository. Local marketplace metadata is derived from "
            "plugin.json for same-repository entries."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=argparse.SUPPRESS,
        help=(
            "repository root containing either .github/plugin/marketplace.json or a root-level plugin.json; "
            "if omitted, search upward from the current directory and the script location"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "marketplace", "plugin"),
        default="auto",
        help=(
            "validation mode: auto-detect from repo layout, validate a marketplace repo, "
            "or validate a single-plugin repo"
        ),
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="read-only validation mode")
    action.add_argument(
        "--apply",
        action="store_true",
        help="rewrite local JSON files, including local marketplace fields generated from plugin.json",
    )
    parser.add_argument(
        "--check-remotes",
        action="store_true",
        help="validate pinned external GitHub plugin sources during local or manual runs",
    )
    parser.add_argument(
        "--github-token-env",
        default="GITHUB_TOKEN",
        help="env var name for local or manual GitHub API authentication",
    )
    parser.add_argument(
        "--this-repo",
        default=DEFAULT_THIS_REPO,
        help="canonical owner/repo name used to recognize marketplace entries that point back to this repository",
    )
    return parser.parse_args(argv)


def selected_action(args: argparse.Namespace) -> str:
    return "apply" if args.apply else "check"


def emit_status(message: str) -> None:
    print(message, file=sys.stderr)


def emit_success_summary(
    *,
    args: argparse.Namespace,
    mode: str,
    result: RunResult,
) -> None:
    remote_suffix = " with remote validation" if args.check_remotes else ""
    if args.apply:
        if result.changed:
            emit_status(
                f"Apply completed in {mode} mode{remote_suffix}; updated {len(result.changed)} file(s)."
            )
            return
        emit_status(
            f"Apply completed in {mode} mode{remote_suffix}; no local metadata changes were required."
        )
        return
    emit_status(f"Check passed in {mode} mode{remote_suffix}.")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        root = resolve_repo_root(getattr(args, "repo_root", None), Path(__file__))
        mode = resolve_mode(root, args.mode)
        load_repo_dotenv(root)
    except ValueError as exc:
        emit_status(str(exc))
        return 1

    result = RunResult()
    if selected_action(args) == "check" and not args.check:
        emit_status("No action flag supplied; defaulting to read-only validation.")
    emit_status(
        f"Running {selected_action(args)} in {mode} mode"
        f"{' with remote validation' if args.check_remotes else ''}."
    )
    try:
        if mode == "marketplace":
            apply_marketplace_requirements(root, args, result)
        else:
            apply_local_plugin_requirements(root, apply=args.apply, result=result)
    except (FileNotFoundError, ValueError) as exc:
        emit_status(str(exc))
        return 1

    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if result.violations:
        for violation in result.violations:
            print(f"{violation.path}: {violation.message}", file=sys.stderr)
        return 1
    emit_success_summary(args=args, mode=mode, result=result)
    if args.apply and result.changed:
        for path in sorted(result.changed):
            print(f"updated {path.relative_to(root)}")

    # Regenerate the HTML marketplace diagram to stay in sync
    if mode == "marketplace":
        try:
            from generate_marketplace_diagram import (
                fetch_remote_plugin_json,
                generate_html,
                is_local,
                load_marketplace,
                resolve_local_components,
            )

            marketplace_path = root / MARKETPLACE_PATH
            plugins = load_marketplace(marketplace_path)
            for p in plugins:
                if is_local(p):
                    resolve_local_components(p)
                else:
                    fetch_remote_plugin_json(p)

            for gen_func, filename in [
                (generate_html, "plugin-marketplace-diagram.html"),
            ]:
                content = gen_func(plugins)
                diagram_path = root / "docs" / filename
                diagram_path.parent.mkdir(parents=True, exist_ok=True)
                current = diagram_path.read_text(encoding="utf-8") if diagram_path.exists() else ""
                if current != content:
                    diagram_path.write_text(content, encoding="utf-8")
                    emit_status(f"Regenerated {diagram_path.relative_to(root)}")
                    result.changed.add(diagram_path)
                else:
                    emit_status(f"{diagram_path.relative_to(root)} is up to date.")
        except Exception as exc:
            emit_status(f"warning: could not regenerate marketplace diagrams: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))