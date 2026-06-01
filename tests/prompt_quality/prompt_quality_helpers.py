"""Shared constants and helpers for prompt-quality tests."""

from __future__ import annotations

import json
import yaml
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Root of the repository
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PLUGINS_DIR = REPO_ROOT / "plugins"

# Directories containing instruction files
INSTRUCTION_DIRS = [
    REPO_ROOT / "uncommon_repo_instructions",
]

# Directories containing skill files
SKILL_DIRS = [
    *(PLUGINS_DIR.glob("*/skills") if PLUGINS_DIR.is_dir() else []),
    REPO_ROOT / "uncommon_repo_skills",
]


# ── Collection helpers ──────────────────────────────────────────────

def _collect_instruction_files() -> list[Path]:
    files = []
    for d in INSTRUCTION_DIRS:
        if d.is_dir():
            for md in d.rglob("*.instructions.md"):
                files.append(md)
    return files


def _collect_skill_files() -> list[Path]:
    files = []
    for d in SKILL_DIRS:
        if d.is_dir():
            for md in d.rglob("*.md"):
                # Skip dotfiles/cache directories and reference support material
                if any(
                    part.startswith(".") or part == "__pycache__" or part == "references"
                    for part in md.parts
                ):
                    continue
                files.append(md)
    return files


def _collect_agent_files() -> list[Path]:
    if not PLUGINS_DIR.is_dir():
        return []
    return sorted(PLUGINS_DIR.glob("*/*.agent.md"))


def _collect_all_md_files() -> list[Path]:
    return _collect_instruction_files() + _collect_skill_files() + _collect_agent_files()


def _load_plugin_manifests() -> list[tuple[Path, dict]]:
    if not PLUGINS_DIR.is_dir():
        return []
    manifests = []
    for pj in sorted(PLUGINS_DIR.glob("*/plugin.json")):
        data = json.loads(pj.read_text(encoding="utf-8"))
        manifests.append((pj.parent, data))
    return manifests


def locator_refs(value: object) -> list[str]:
    """Normalize manifest locator fields that may be a string or a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ValueError("locator must not be empty")
        return [stripped]
    if isinstance(value, list):
        refs: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError(f"locator entries must be strings: {item!r}")
            stripped = item.strip()
            if not stripped:
                raise ValueError("locator entries must not be empty strings")
            refs.append(stripped)
        return refs
    raise ValueError(f"locator must be a string or list of strings, got {type(value).__name__}")


# ── Cached accessors ────────────────────────────────────────────────

_INSTRUCTION_FILES: list[Path] | None = None
_SKILL_FILES: list[Path] | None = None
_AGENT_FILES: list[Path] | None = None
_ALL_MD_FILES: list[Path] | None = None
_MANIFESTS: list[tuple[Path, dict]] | None = None


def get_instruction_files() -> list[Path]:
    global _INSTRUCTION_FILES
    if _INSTRUCTION_FILES is None:
        _INSTRUCTION_FILES = _collect_instruction_files()
    return _INSTRUCTION_FILES


def get_skill_files() -> list[Path]:
    global _SKILL_FILES
    if _SKILL_FILES is None:
        _SKILL_FILES = _collect_skill_files()
    return _SKILL_FILES


def get_agent_files() -> list[Path]:
    global _AGENT_FILES
    if _AGENT_FILES is None:
        _AGENT_FILES = _collect_agent_files()
    return _AGENT_FILES


def get_all_md_files() -> list[Path]:
    global _ALL_MD_FILES
    if _ALL_MD_FILES is None:
        _ALL_MD_FILES = _collect_all_md_files()
    return _ALL_MD_FILES


def get_manifests() -> list[tuple[Path, dict]]:
    global _MANIFESTS
    if _MANIFESTS is None:
        _MANIFESTS = _load_plugin_manifests()
    return _MANIFESTS


# ── Frontmatter parsing ────────────────────────────────────────────

def parse_frontmatter(path: Path) -> dict | None:
    """Extract and parse YAML frontmatter from a markdown file.

    Returns the parsed dict, or None if no frontmatter is present.
    Raises ValueError on malformed frontmatter.
    """
    content = path.read_text(encoding="utf-8", errors="replace")
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end < 0:
        raise ValueError("unclosed front-matter")
    fm_text = content[3:end]
    data = yaml.safe_load(fm_text)
    if data is not None and not isinstance(data, dict):
        raise ValueError("front-matter is not a dict")
    return data or {}


def strip_frontmatter(content: str) -> str:
    """Return content with YAML frontmatter removed."""
    if content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            return content[end + 3:]
    return content
