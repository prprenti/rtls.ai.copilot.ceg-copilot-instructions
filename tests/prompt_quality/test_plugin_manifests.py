"""Prompt quality tests for plugin manifests (plugin.json + .mcp.json).

Validates plugin structure, required fields, naming conventions,
version format, cross-references to agents/skills/MCP servers,
and ensures no orphan plugin directories.
"""

from __future__ import annotations

import json
import re
import re
import subprocess

import pytest

from prompt_quality_helpers import (
    PLUGINS_DIR,
    REPO_ROOT,
    get_manifests,
    locator_refs,
)

pytestmark = pytest.mark.prompt_quality


class TestPluginManifestStructure:
    def test_plugins_exist(self) -> None:
        """There should be at least one plugin."""
        assert len(get_manifests()) > 0, "No plugins found under plugins/"

    def test_required_fields(self) -> None:
        """Every plugin.json must have name, description, and version."""
        missing = []
        for plugin_dir, data in get_manifests():
            for field in ("name", "description", "version"):
                if field not in data:
                    missing.append(f"{plugin_dir.name}: missing '{field}'")
        assert not missing, "plugin.json missing required fields:\n" + "\n".join(missing)

    def test_name_follows_convention(self) -> None:
        """Plugin names should be lowercase kebab-case up to 64 chars."""
        name_re = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
        bad = []
        for plugin_dir, data in get_manifests():
            name = data.get("name", "")
            if not name_re.match(name):
                bad.append(f"{plugin_dir.name}: name '{name}' is not lowercase kebab-case or exceeds 64 chars")
        assert not bad, "Plugin naming violations:\n" + "\n".join(bad)

    def test_version_semver(self) -> None:
        """Plugin versions should follow semver (major.minor.patch)."""
        semver_re = re.compile(r"^\d+\.\d+\.\d+$")
        bad = []
        for plugin_dir, data in get_manifests():
            version = data.get("version", "")
            if not semver_re.match(version):
                bad.append(f"{plugin_dir.name}: version '{version}' is not semver")
        assert not bad, "Non-semver plugin versions:\n" + "\n".join(bad)

    def test_description_min_length(self) -> None:
        """Plugin descriptions should be at least 20 characters."""
        short = []
        for plugin_dir, data in get_manifests():
            desc = data.get("description", "")
            if len(desc.strip()) < 20:
                short.append(f"{plugin_dir.name}: '{desc}'")
        assert not short, "Plugins with short descriptions:\n" + "\n".join(short)

    def test_keywords_are_lowercase(self) -> None:
        """Plugin keywords should be lowercase strings."""
        bad = []
        for plugin_dir, data in get_manifests():
            keywords = data.get("keywords", [])
            if not isinstance(keywords, list):
                bad.append(f"{plugin_dir.name}: keywords is not a list")
                continue
            for kw in keywords:
                if not isinstance(kw, str):
                    bad.append(f"{plugin_dir.name}: keyword {kw!r} is not a string")
                elif kw != kw.lower():
                    bad.append(f"{plugin_dir.name}: keyword '{kw}' is not lowercase")
        assert not bad, "Plugin keyword violations:\n" + "\n".join(bad)


class TestPluginCrossReferences:
    def test_locator_fields_have_string_values(self) -> None:
        """Locator fields must be strings or lists of strings without empty items."""
        invalid = []
        for plugin_dir, data in get_manifests():
            for field_name in ("agents", "skills", "commands", "mcpServers", "lspServers"):
                try:
                    locator_refs(data.get(field_name))
                except ValueError as exc:
                    invalid.append(f"{plugin_dir.name}: {field_name}: {exc}")
        assert not invalid, "Invalid locator fields:\n" + "\n".join(invalid)

    def test_mcp_servers_ref_exists(self) -> None:
        """If plugin.json declares mcpServers, the referenced path must be a manifest file."""
        missing = []
        for plugin_dir, data in get_manifests():
            for mcp_ref in locator_refs(data.get("mcpServers")):
                mcp_path = plugin_dir / mcp_ref
                if not mcp_path.is_file():
                    missing.append(f"{plugin_dir.name}: {mcp_ref} not found as a file")
        assert not missing, "Missing MCP server paths:\n" + "\n".join(missing)

    def test_agents_ref_resolves(self) -> None:
        """If plugin.json declares agents path, it should exist."""
        missing = []
        for plugin_dir, data in get_manifests():
            for agents_ref in locator_refs(data.get("agents")):
                agents_path = plugin_dir / agents_ref
                if not agents_path.exists():
                    missing.append(f"{plugin_dir.name}: agents path '{agents_ref}' not found")
        assert not missing, "Missing agents paths:\n" + "\n".join(missing)

    def test_skills_ref_resolves(self) -> None:
        """If plugin.json declares skills path, it should be a directory with SKILL.md."""
        missing = []
        for plugin_dir, data in get_manifests():
            for skills_ref in locator_refs(data.get("skills")):
                skills_path = plugin_dir / skills_ref
                if not skills_path.is_dir():
                    missing.append(f"{plugin_dir.name}: skills path '{skills_ref}' is not a directory")
                elif not (skills_path / "SKILL.md").is_file():
                    missing.append(f"{plugin_dir.name}: skills path '{skills_ref}' has no SKILL.md")
        assert not missing, "Missing or invalid skills paths:\n" + "\n".join(missing)

    def test_skills_refs_are_skill_directories(self) -> None:
        """Skill refs must be skill directory paths (skills/<name>), not file paths."""
        invalid = []
        for plugin_dir, data in get_manifests():
            for skills_ref in locator_refs(data.get("skills")):
                if not re.fullmatch(r"skills/[a-z0-9][a-z0-9-]*", skills_ref):
                    invalid.append(f"{plugin_dir.name}: '{skills_ref}' must match skills/<kebab-name>")
        assert not invalid, "Non-canonical skills paths:\n" + "\n".join(invalid)


class TestMcpJsonValidity:
    def test_mcp_json_valid(self) -> None:
        """Every .mcp.json should be valid JSON with required stdio fields."""
        invalid = []
        for plugin_dir, data in get_manifests():
            for mcp_ref in locator_refs(data.get("mcpServers")):
                mcp_path = plugin_dir / mcp_ref
                if not mcp_path.is_file():
                    continue
                try:
                    mcp_data = json.loads(mcp_path.read_text(encoding="utf-8"))
                    servers = mcp_data.get("mcpServers", {})
                    if isinstance(servers, dict):
                        for name, cfg in servers.items():
                            if "command" not in cfg:
                                invalid.append(f"{plugin_dir.name}/{mcp_ref}: server '{name}' has no 'command'")
                except json.JSONDecodeError as e:
                    invalid.append(f"{plugin_dir.name}/{mcp_ref}: {e}")
        assert not invalid, "Invalid .mcp.json files:\n" + "\n".join(invalid)


class TestNoOrphanPlugins:
    def test_every_plugin_dir_has_manifest(self) -> None:
        """Every directory under plugins/ should have a plugin.json."""
        if not PLUGINS_DIR.is_dir():
            pytest.skip("plugins directory not found")
        orphans = []
        for d in sorted(PLUGINS_DIR.iterdir()):
            if not d.is_dir() or d.name.startswith(".") or d.name == "__pycache__":
                continue
            if not (d / "plugin.json").is_file():
                orphans.append(d.name)
        assert not orphans, f"Plugin dirs without plugin.json: {orphans}"


class TestMarketplace:
    MARKETPLACE_PATH = REPO_ROOT / ".github" / "plugin" / "marketplace.json"

    def test_marketplace_exists(self) -> None:
        """marketplace.json must exist in .github/plugin/."""
        assert self.MARKETPLACE_PATH.is_file(), (
            f"Missing {self.MARKETPLACE_PATH.relative_to(REPO_ROOT)}"
        )

    def test_marketplace_valid_json(self) -> None:
        """marketplace.json must be valid JSON."""
        if not self.MARKETPLACE_PATH.is_file():
            pytest.skip("marketplace.json not found")
        data = json.loads(self.MARKETPLACE_PATH.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_marketplace_required_fields(self) -> None:
        """marketplace.json must have name, owner, and plugins."""
        if not self.MARKETPLACE_PATH.is_file():
            pytest.skip("marketplace.json not found")
        data = json.loads(self.MARKETPLACE_PATH.read_text(encoding="utf-8"))
        for field in ("name", "owner", "plugins"):
            assert field in data, f"marketplace.json missing required field '{field}'"
        assert isinstance(data["owner"], dict) and "name" in data["owner"], (
            "marketplace.json owner must have a 'name' field"
        )

    def test_all_plugins_registered_in_marketplace(self) -> None:
        """Every plugin with a plugin.json must appear in marketplace.json."""
        if not self.MARKETPLACE_PATH.is_file():
            pytest.skip("marketplace.json not found")
        data = json.loads(self.MARKETPLACE_PATH.read_text(encoding="utf-8"))
        marketplace_names = {p["name"] for p in data["plugins"]}
        missing = []
        for plugin_dir, manifest in get_manifests():
            name = manifest["name"]
            if name not in marketplace_names:
                missing.append(name)
        assert not missing, (
            f"Plugins not registered in marketplace.json: {missing}"
        )

    # The GitHub OWNER/REPO identifier for this repository, used to decide
    # whether an OWNER/REPO:PATH source should be validated locally.
    _THIS_REPO = "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions"

    @classmethod
    def _is_remote_url(cls, source: str) -> bool:
        """True if source is an absolute URL (https, http, git@)."""
        return source.startswith(("https://", "http://", "git@"))

    @classmethod
    def _is_local_path(cls, source: str) -> bool:
        """True if source is a relative or absolute filesystem path."""
        return source.startswith((".", "/"))

    @classmethod
    def _resolve_github_subdir(cls, source: str) -> str | None:
        """Resolve an OWNER/REPO:PATH source to a local path if it's this repo."""
        repo_part, path_part = source.split(":", 1)
        if repo_part == cls._THIS_REPO:
            return path_part
        return None

    @classmethod
    def _is_github_repo_ref(cls, source: str) -> bool:
        """True if source looks like OWNER/REPO (no colon, not a local path)."""
        return "/" in source and not source.startswith("plugins")

    @classmethod
    def _resolve_source(cls, source) -> str | None:
        """Return a local path to validate, or None if the source is remote.

        Supported formats:
        - Structured object (``{"source": "github", "repo": "...", "path": "..."}``)
          → return path if repo matches this repo, else None
        - Relative path (``plugins/foo``) → return as-is
        - ``OWNER/REPO:PATH`` where OWNER/REPO matches this repo → return PATH
        - ``OWNER/REPO:PATH`` for another repo → return None (remote)
        - ``OWNER/REPO`` (no colon) → return None (remote, root-level plugin)
        - URL (``https://...``) → return None (remote)
        """
        if isinstance(source, dict):
            repo = source.get("repo", "")
            path = source.get("path", "")
            if repo == cls._THIS_REPO and path:
                return path
            return None
        if cls._is_remote_url(source):
            return None
        if cls._is_local_path(source):
            return source
        if ":" in source:
            return cls._resolve_github_subdir(source)
        if cls._is_github_repo_ref(source):
            return None
        return source

    def test_marketplace_sources_exist(self) -> None:
        """Local plugin source paths in marketplace.json must exist."""
        if not self.MARKETPLACE_PATH.is_file():
            pytest.skip("marketplace.json not found")
        data = json.loads(self.MARKETPLACE_PATH.read_text(encoding="utf-8"))
        missing = []
        for entry in data["plugins"]:
            source = entry.get("source", "")
            local_path = self._resolve_source(source)
            if local_path is None:
                continue  # remote source — can't validate locally
            path = REPO_ROOT / local_path
            if not path.is_dir():
                missing.append(f"{entry['name']}: {source}")
        assert not missing, (
            "Marketplace plugin sources not found:\n" + "\n".join(missing)
        )

    def test_marketplace_names_match_manifests(self) -> None:
        """Plugin names in marketplace.json must match their plugin.json."""
        if not self.MARKETPLACE_PATH.is_file():
            pytest.skip("marketplace.json not found")
        data = json.loads(self.MARKETPLACE_PATH.read_text(encoding="utf-8"))
        mismatches = []
        for entry in data["plugins"]:
            source = entry.get("source", "")
            local_path = self._resolve_source(source)
            if local_path is None:
                continue  # remote source — can't validate locally
            manifest_path = REPO_ROOT / local_path / "plugin.json"
            if not manifest_path.is_file():
                continue
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if entry["name"] != manifest["name"]:
                mismatches.append(
                    f"{source}: marketplace says '{entry['name']}', "
                    f"plugin.json says '{manifest['name']}'"
                )
        assert not mismatches, (
            "Name mismatches:\n" + "\n".join(mismatches)
        )

    def test_marketplace_version_bumped_on_change(self) -> None:
        """metadata.version must be bumped when the plugins array changes.

        Compares the current branch's marketplace.json against main.
        If the plugins array differs but metadata.version is unchanged,
        the test fails — this ensures the deploy stamp detects updates.
        """
        if not self.MARKETPLACE_PATH.is_file():
            pytest.skip("marketplace.json not found")

        marketplace_rel = str(
            self.MARKETPLACE_PATH.relative_to(REPO_ROOT)
        )

        # Detect if we're on the main branch — nothing to compare
        try:
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, timeout=10,
                cwd=str(REPO_ROOT),
            )
            if branch.returncode == 0 and branch.stdout.strip() == "main":
                pytest.skip("On main branch — no comparison target")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("git not available")

        # Read main branch version of marketplace.json
        try:
            result = subprocess.run(
                ["git", "show", f"main:{marketplace_rel}"],
                capture_output=True, text=True, timeout=10,
                cwd=str(REPO_ROOT),
            )
            if result.returncode != 0:
                pytest.skip(
                    "marketplace.json does not exist on main "
                    "(new file or detached HEAD)"
                )
            main_data = json.loads(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError,
                json.JSONDecodeError):
            pytest.skip("Could not read marketplace.json from main branch")

        current_data = json.loads(
            self.MARKETPLACE_PATH.read_text(encoding="utf-8")
        )

        # Canonicalize plugins arrays for comparison
        main_plugins = json.dumps(
            main_data.get("plugins", []), sort_keys=True, separators=(",", ":")
        )
        current_plugins = json.dumps(
            current_data.get("plugins", []), sort_keys=True, separators=(",", ":")
        )

        if main_plugins == current_plugins:
            return  # No plugin changes — version bump not required

        main_version = main_data.get("metadata", {}).get("version", "")
        current_version = current_data.get("metadata", {}).get("version", "")

        assert current_version != main_version, (
            f"marketplace.json plugins changed but metadata.version "
            f"was not bumped (still '{current_version}'). "
            f"Bump the version so the deploy stamp detects the update."
        )
