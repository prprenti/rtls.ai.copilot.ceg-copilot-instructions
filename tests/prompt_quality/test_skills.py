"""Prompt quality tests for skill markdown files.

Validates structure, frontmatter (name, description, keywords),
content quality, and documentation coverage for plugin skills.
"""

from __future__ import annotations

import re

import pytest

from prompt_quality_helpers import (
    HAS_YAML,
    PLUGINS_DIR,
    REPO_ROOT,
    get_manifests,
    get_skill_files,
    locator_refs,
    parse_frontmatter,
    strip_frontmatter,
)

pytestmark = pytest.mark.prompt_quality


def _is_fully_qualified_mcp_tool(name: str) -> bool:
    """Return True for native Copilot MCP tool refs in frontmatter.

    Native frontmatter references use `server/tool` with alphanumeric,
    dash, and underscore characters in both segments.
    """
    token = name.strip()
    if not token:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*/[A-Za-z0-9][A-Za-z0-9_-]*", token))


class TestSkillStructure:
    def test_skill_files_exist(self) -> None:
        """There should be at least some skill files."""
        assert len(get_skill_files()) > 0, "No skill .md files found"

    def test_skill_files_have_heading(self) -> None:
        """Skill .md files should have at least one # heading."""
        no_heading = []
        for f in get_skill_files():
            content = f.read_text(encoding="utf-8", errors="replace")
            if not content.strip():
                continue
            text = strip_frontmatter(content)
            if not re.search(r"^#{1,6}\s+\S", text, re.MULTILINE):
                no_heading.append(str(f.relative_to(REPO_ROOT)))
        assert not no_heading, "Skill files without headings:\n" + "\n".join(no_heading)

    def test_skill_files_not_stubs(self) -> None:
        """Skill .md files should have substantive content (>= 200 chars)."""
        stubs = []
        for f in get_skill_files():
            content = f.read_text(encoding="utf-8", errors="replace")
            if len(content.strip()) < 200:
                stubs.append(f"{f.relative_to(REPO_ROOT)} ({len(content.strip())} chars)")
        assert not stubs, "Skill files that are stubs:\n" + "\n".join(stubs)

    def test_skill_files_not_too_large(self) -> None:
        """Skill files over 50KB may degrade LLM context quality."""
        too_large = []
        for f in get_skill_files():
            size = f.stat().st_size
            if size > 50_000:
                too_large.append(f"{f.relative_to(REPO_ROOT)} ({size:,} bytes)")
        assert not too_large, "Oversized skill files (>50KB):\n" + "\n".join(too_large)


class TestSkillFrontmatter:
    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_skills_have_frontmatter(self) -> None:
        """Every skill .md file should have YAML frontmatter."""
        missing = []
        for f in get_skill_files():
            content = f.read_text(encoding="utf-8", errors="replace")
            if not content.startswith("---"):
                missing.append(str(f.relative_to(REPO_ROOT)))
        assert not missing, "Skill files without frontmatter:\n" + "\n".join(missing)

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_skills_required_fields(self) -> None:
        """Every skill must have name, description, and keywords in frontmatter."""
        missing = []
        for f in get_skill_files():
            try:
                fm = parse_frontmatter(f)
            except ValueError:
                continue
            if fm is None:
                continue
            for field in ("name", "description", "keywords"):
                if field not in fm:
                    missing.append(f"{f.relative_to(REPO_ROOT)}: missing '{field}'")
        assert not missing, "Skills missing required fields:\n" + "\n".join(missing)

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_skill_description_min_length(self) -> None:
        """Skill descriptions should be at least 20 characters."""
        short = []
        for f in get_skill_files():
            try:
                fm = parse_frontmatter(f)
            except ValueError:
                continue
            if fm is None:
                continue
            desc = fm.get("description", "")
            if isinstance(desc, str) and len(desc.strip()) < 20:
                short.append(f"{f.relative_to(REPO_ROOT)}: '{desc}'")
        assert not short, "Skills with short descriptions:\n" + "\n".join(short)

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_skill_mcp_tools_format(self) -> None:
        """If mcp_tools is present, it should be a non-empty string or list."""
        bad = []
        for f in get_skill_files():
            try:
                fm = parse_frontmatter(f)
            except ValueError:
                continue
            if fm is None:
                continue
            mcp_tools = fm.get("mcp_tools")
            if mcp_tools is None:
                continue  # optional field
            if isinstance(mcp_tools, str) and mcp_tools.strip():
                continue
            if isinstance(mcp_tools, list) and len(mcp_tools) > 0:
                continue
            bad.append(f"{f.relative_to(REPO_ROOT)}: mcp_tools={mcp_tools!r}")
        assert not bad, "Skills with invalid mcp_tools:\n" + "\n".join(bad)

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_skill_names_use_kebab_case(self) -> None:
        """Skill directory names and frontmatter names must be lowercase kebab-case (no underscores)."""
        NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
        bad = []
        for plugin_dir, data in get_manifests():
            for skill_ref in locator_refs(data.get("skills")):
                skill_dir = plugin_dir / skill_ref
                skill_md = skill_dir / "SKILL.md"
                if not skill_md.is_file():
                    continue
                # Check the directory name
                dir_name = skill_dir.name
                if not NAME_RE.fullmatch(dir_name):
                    bad.append(f"{skill_dir.relative_to(REPO_ROOT)}: directory '{dir_name}'")
                # Check the frontmatter name field
                try:
                    fm = parse_frontmatter(skill_md)
                except ValueError:
                    continue
                if fm is None:
                    continue
                name = fm.get("name")
                if isinstance(name, str) and not NAME_RE.fullmatch(name.strip()):
                    bad.append(f"{skill_md.relative_to(REPO_ROOT)}: name '{name.strip()}'")
        assert not bad, (
            "Skill names must be lowercase kebab-case (no underscores):\n"
            + "\n".join(bad)
        )

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_skill_mcp_tools_are_fully_qualified(self) -> None:
        """If mcp_tools is present, each entry should use native server/tool MCP syntax."""
        bad = []
        for f in get_skill_files():
            try:
                fm = parse_frontmatter(f)
            except ValueError:
                continue
            if fm is None:
                continue
            mcp_tools = fm.get("mcp_tools")
            if mcp_tools is None:
                continue
            if isinstance(mcp_tools, str):
                tokens = [t.strip() for t in mcp_tools.split(",") if t.strip()]
            elif isinstance(mcp_tools, list):
                tokens = [t for t in mcp_tools if isinstance(t, str)]
                if len(tokens) != len(mcp_tools):
                    bad.append(f"{f.relative_to(REPO_ROOT)}: mcp_tools has non-string entries")
                    continue
            else:
                continue

            for tool in tokens:
                if not _is_fully_qualified_mcp_tool(tool):
                    bad.append(f"{f.relative_to(REPO_ROOT)}: mcp_tool '{tool}'")

        assert not bad, "Skills with non-native MCP tool refs:\n" + "\n".join(bad)


class TestSkillDiscovery:
    def test_skill_dirs_have_md_files(self) -> None:
        """Plugin skill subdirectories with .py should also have .md docs."""
        if not PLUGINS_DIR.is_dir():
            pytest.skip("plugins directory not found")
        undocumented = []
        for plugin in PLUGINS_DIR.iterdir():
            skills = plugin / "skills"
            if not skills.is_dir():
                continue
            for subdir in skills.iterdir():
                if not subdir.is_dir() or subdir.name.startswith(".") or subdir.name == "__pycache__":
                    continue
                py_files = list(subdir.glob("*.py"))
                md_files = list(subdir.glob("*.md"))
                if py_files and not md_files:
                    undocumented.append(f"{plugin.name}/{subdir.name}")
        assert not undocumented, f"Undocumented skill dirs (no .md): {undocumented}"

    def test_every_plugin_with_skills_has_md(self) -> None:
        """Every plugin that declares skills should have a SKILL.md in each skill directory."""
        missing = []
        for plugin_dir, data in get_manifests():
            skill_refs = locator_refs(data.get("skills"))
            if not skill_refs:
                continue
            for skill_ref in skill_refs:
                skill_dir = plugin_dir / skill_ref
                if skill_dir.is_dir() and not (skill_dir / "SKILL.md").is_file():
                    missing.append(f"{plugin_dir.name}/{skill_ref}")
                elif not skill_dir.is_dir():
                    missing.append(f"{plugin_dir.name}/{skill_ref} (not a directory)")
        assert not missing, f"Plugins with skill dirs missing SKILL.md: {missing}"

    def test_no_duplicate_skill_names_across_plugins(self) -> None:
        """Skill frontmatter names should be unique across all plugins."""
        from collections import Counter
        skill_names: list[str] = []
        for plugin_dir, data in get_manifests():
            for skill_ref in locator_refs(data.get("skills")):
                skill_md = plugin_dir / skill_ref / "SKILL.md"
                if not skill_md.is_file():
                    continue
                try:
                    frontmatter = parse_frontmatter(skill_md)
                except ValueError:
                    frontmatter = None
                skill_name = frontmatter.get("name") if isinstance(frontmatter, dict) else None
                if isinstance(skill_name, str) and skill_name.strip():
                    skill_names.append(f"{skill_name.strip()} ({plugin_dir.name})")
                else:
                    skill_names.append(f"{skill_md.parent.name} ({plugin_dir.name})")
        names_only = [s.split(" (")[0] for s in skill_names]
        dupes = [n for n, c in Counter(names_only).items() if c > 1]
        assert not dupes, f"Duplicate skill names across plugins: {dupes}"
