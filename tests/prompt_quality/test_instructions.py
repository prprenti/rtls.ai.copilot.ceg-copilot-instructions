"""Prompt quality tests for .instructions.md files.

Validates structure, frontmatter, content quality, and anti-patterns
in instruction files.
"""

from __future__ import annotations

import re
from collections import Counter

import pytest

from prompt_quality_helpers import (
    HAS_YAML,
    REPO_ROOT,
    get_instruction_files,
    get_all_md_files,
    parse_frontmatter,
    strip_frontmatter,
)

pytestmark = pytest.mark.prompt_quality


class TestInstructionFileStructure:
    def test_instruction_files_exist(self) -> None:
        """There should be at least some instruction files."""
        files = get_instruction_files()
        assert len(files) > 0, "No .instructions.md files found"

    def test_every_file_has_heading(self) -> None:
        """Every markdown file should have at least one # heading."""
        no_heading = []
        for f in get_all_md_files():
            content = f.read_text(encoding="utf-8", errors="replace")
            if not content.strip():
                continue
            text = strip_frontmatter(content)
            if not re.search(r"^#{1,6}\s+\S", text, re.MULTILINE):
                no_heading.append(str(f.relative_to(REPO_ROOT)))
        assert not no_heading, f"Files without headings:\n" + "\n".join(no_heading)

    def test_files_not_stubs(self) -> None:
        """Instruction files should have substantive content (>= 200 chars)."""
        stubs = []
        for f in get_instruction_files():
            content = f.read_text(encoding="utf-8", errors="replace")
            if len(content.strip()) < 200:
                stubs.append(f"{f.relative_to(REPO_ROOT)} ({len(content.strip())} chars)")
        assert not stubs, f"Instruction files that are stubs:\n" + "\n".join(stubs)

    def test_files_not_too_large(self) -> None:
        """Files over 50KB may degrade LLM context quality.

        Exempt uncommon_repo_instructions/ and plugin agent files
        which may be intentionally large.
        """
        exempt_prefixes = ("uncommon_repo_instructions",)
        too_large = []
        for f in get_all_md_files():
            rel = str(f.relative_to(REPO_ROOT))
            if rel.startswith(exempt_prefixes):
                continue
            if f.name.endswith(".agent.md"):
                continue
            size = f.stat().st_size
            if size > 50_000:
                too_large.append(f"{rel} ({size:,} bytes)")
        assert not too_large, f"Oversized files (>50KB):\n" + "\n".join(too_large)


class TestInstructionFrontmatter:
    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_valid_yaml_frontmatter(self) -> None:
        """When YAML front-matter is present, it should be valid YAML."""
        invalid = []
        for f in get_all_md_files():
            try:
                parse_frontmatter(f)
            except ValueError as e:
                invalid.append(f"{f.relative_to(REPO_ROOT)}: {e}")
        assert not invalid, "Invalid YAML front-matter:\n" + "\n".join(invalid)

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_instruction_required_fields(self) -> None:
        """Every .instructions.md must have description and keywords.

        Exempt uncommon_repo_instructions/ which may be auto-generated.
        """
        exempt_prefixes = ("uncommon_repo_instructions",)
        missing = []
        for f in get_instruction_files():
            rel = str(f.relative_to(REPO_ROOT))
            if rel.startswith(exempt_prefixes):
                continue
            try:
                fm = parse_frontmatter(f)
            except ValueError:
                continue  # caught by test_valid_yaml_frontmatter
            if fm is None:
                missing.append(f"{rel}: no frontmatter")
                continue
            for field in ("description", "keywords"):
                if field not in fm:
                    missing.append(f"{rel}: missing '{field}'")
        assert not missing, "Instructions missing required fields:\n" + "\n".join(missing)

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_description_min_length(self) -> None:
        """Instruction descriptions should be at least 20 characters.

        Exempt uncommon_repo_instructions/.
        """
        exempt_prefixes = ("uncommon_repo_instructions",)
        short = []
        for f in get_instruction_files():
            rel = str(f.relative_to(REPO_ROOT))
            if rel.startswith(exempt_prefixes):
                continue
            try:
                fm = parse_frontmatter(f)
            except ValueError:
                continue
            if fm is None:
                continue
            desc = fm.get("description", "")
            if isinstance(desc, str) and len(desc.strip()) < 20:
                short.append(f"{rel}: '{desc}'")
        assert not short, "Instructions with short descriptions:\n" + "\n".join(short)


class TestApplyToDirectives:
    def test_apply_to_glob_syntax(self) -> None:
        """applyTo directives should use valid-looking glob patterns."""
        bad = []
        glob_valid = re.compile(r'^["\']?[\w./*?{}\[\],\s-]+["\']?$')
        for f in get_all_md_files():
            content = f.read_text(encoding="utf-8", errors="replace")
            for match in re.finditer(r"applyTo[>:\s]+([^\n<]+)", content, re.IGNORECASE):
                pattern = match.group(1).strip()
                if not pattern:
                    continue
                if not glob_valid.match(pattern):
                    bad.append(f"{f.relative_to(REPO_ROOT)}: '{pattern}'")
        assert not bad, f"Invalid applyTo glob patterns:\n" + "\n".join(bad)


class TestPromptAntiPatterns:
    def test_no_identity_confusion(self) -> None:
        """Instructions should not contain 'you are an AI' style phrases."""
        identity_pat = re.compile(
            r"you are (a|an) (AI|artificial intelligence|language model|LLM|chatbot)",
            re.IGNORECASE,
        )
        found = []
        for f in get_instruction_files():
            content = f.read_text(encoding="utf-8", errors="replace")
            if identity_pat.search(content):
                found.append(str(f.relative_to(REPO_ROOT)))
        assert not found, f"Files with identity confusion:\n" + "\n".join(found)

    def test_no_excessive_repetition(self) -> None:
        """Check for same sentence repeated 5+ times (copy-paste error).

        Reference manuals and structured docs legitimately repeat patterns.
        Use a threshold of 6 and exempt structural lines and uncommon/wip dirs.
        """
        exempt_prefixes = ("uncommon_repo_instructions",)
        structural = re.compile(
            r"^(\||#{1,6}\s|```|---|-\s|\*\s|>\s|\d+\.\s)"
        )
        found = []
        for f in get_instruction_files():
            rel = str(f.relative_to(REPO_ROOT))
            if rel.startswith(exempt_prefixes):
                continue
            content = f.read_text(encoding="utf-8", errors="replace")
            lines = [l.strip() for l in content.splitlines() if l.strip()]
            if len(lines) < 20:
                continue
            counts = Counter(
                l for l in lines
                if len(l) > 40 and not structural.match(l)
            )
            dupes = {l: c for l, c in counts.items() if c >= 6}
            if dupes:
                found.append(f"{f.relative_to(REPO_ROOT)}: {len(dupes)} repeated lines")
        assert not found, f"Files with excessive repetition:\n" + "\n".join(found)



