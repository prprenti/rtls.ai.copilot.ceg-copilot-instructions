"""Prompt quality tests for agent markdown files.

Validates structure, frontmatter (name, description, keywords, tools),
naming conventions, and content quality for plugin agent files.
"""

from __future__ import annotations

import re

import pytest

from prompt_quality_helpers import (
    HAS_YAML,
    REPO_ROOT,
    get_agent_files,
    get_manifests,
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


class TestAgentStructure:
    def test_agent_files_exist(self) -> None:
        """There should be at least some agent files."""
        assert len(get_agent_files()) > 0, "No .agent.md files found"

    def test_agent_files_have_heading(self) -> None:
        """Agent .md files should have at least one # heading."""
        no_heading = []
        for f in get_agent_files():
            content = f.read_text(encoding="utf-8", errors="replace")
            text = strip_frontmatter(content)
            if not re.search(r"^#{1,6}\s+\S", text, re.MULTILINE):
                no_heading.append(str(f.relative_to(REPO_ROOT)))
        assert not no_heading, "Agent files without headings:\n" + "\n".join(no_heading)

    def test_agent_files_not_stubs(self) -> None:
        """Agent .md files should have substantive content (>= 100 chars)."""
        stubs = []
        for f in get_agent_files():
            content = f.read_text(encoding="utf-8", errors="replace")
            if len(content.strip()) < 100:
                stubs.append(f"{f.relative_to(REPO_ROOT)} ({len(content.strip())} chars)")
        assert not stubs, "Agent files that are stubs:\n" + "\n".join(stubs)


class TestAgentFrontmatter:
    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_agents_have_frontmatter(self) -> None:
        """Every agent .md file should have YAML frontmatter."""
        missing = []
        for f in get_agent_files():
            content = f.read_text(encoding="utf-8", errors="replace")
            if not content.startswith("---"):
                missing.append(str(f.relative_to(REPO_ROOT)))
        assert not missing, "Agent files without frontmatter:\n" + "\n".join(missing)

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_agents_required_fields(self) -> None:
        """Every agent must have name, description, and keywords."""
        missing = []
        for f in get_agent_files():
            try:
                fm = parse_frontmatter(f)
            except ValueError:
                continue
            if fm is None:
                continue
            for field in ("name", "description", "keywords"):
                if field not in fm:
                    missing.append(f"{f.relative_to(REPO_ROOT)}: missing '{field}'")
        assert not missing, "Agents missing required fields:\n" + "\n".join(missing)

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_agent_name_matches_filename(self) -> None:
        """The frontmatter name should match the filename stem (before .agent.md)."""
        mismatched = []
        for f in get_agent_files():
            try:
                fm = parse_frontmatter(f)
            except ValueError:
                continue
            if fm is None:
                continue
            name = fm.get("name", "")
            # filename: access.agent.md → expected name: access
            # Normalize: hyphens and underscores are equivalent
            expected = f.name.replace(".agent.md", "")
            if name.replace("-", "_") != expected.replace("-", "_"):
                mismatched.append(f"{f.relative_to(REPO_ROOT)}: name='{name}', expected='{expected}'")
        assert not mismatched, "Agent name/filename mismatches:\n" + "\n".join(mismatched)

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_agent_tools_is_list(self) -> None:
        """If tools field is present, it should be a list."""
        bad = []
        for f in get_agent_files():
            try:
                fm = parse_frontmatter(f)
            except ValueError:
                continue
            if fm is None:
                continue
            tools = fm.get("tools")
            if tools is None:
                continue  # optional
            if not isinstance(tools, list):
                bad.append(f"{f.relative_to(REPO_ROOT)}: tools is {type(tools).__name__}, expected list")
        assert not bad, "Agents with invalid tools field:\n" + "\n".join(bad)

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_agent_description_min_length(self) -> None:
        """Agent descriptions should be at least 20 characters."""
        short = []
        for f in get_agent_files():
            try:
                fm = parse_frontmatter(f)
            except ValueError:
                continue
            if fm is None:
                continue
            desc = fm.get("description", "")
            if isinstance(desc, str) and len(desc.strip()) < 20:
                short.append(f"{f.relative_to(REPO_ROOT)}: '{desc}'")
        assert not short, "Agents with short descriptions:\n" + "\n".join(short)

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_agent_tools_are_fully_qualified(self) -> None:
        """If tools field is present, each entry should use native server/tool MCP syntax."""
        bad = []
        for f in get_agent_files():
            try:
                fm = parse_frontmatter(f)
            except ValueError:
                continue
            if fm is None:
                continue
            tools = fm.get("tools")
            if tools is None or not isinstance(tools, list):
                continue
            for tool in tools:
                if not isinstance(tool, str) or not _is_fully_qualified_mcp_tool(tool):
                    bad.append(f"{f.relative_to(REPO_ROOT)}: tool '{tool}'")
        assert not bad, "Agents with non-native MCP tool refs:\n" + "\n".join(bad)


class TestAgentPluginIntegration:
    def test_every_plugin_has_agent(self) -> None:
        """Every plugin that declares agents should have at least one .agent.md."""
        missing = []
        for plugin_dir, data in get_manifests():
            agent_refs = locator_refs(data.get("agents"))
            if not agent_refs:
                continue
            agent_files = [
                plugin_dir / agent_ref
                for agent_ref in agent_refs
                if (plugin_dir / agent_ref).is_file() and agent_ref.endswith(".agent.md")
            ]
            if not agent_files:
                missing.append(plugin_dir.name)
        assert not missing, f"Plugins with 'agents' but no .agent.md: {missing}"
