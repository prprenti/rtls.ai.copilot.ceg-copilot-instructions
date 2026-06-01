from __future__ import annotations

import json
import subprocess
import sys

import pytest

from prompt_quality_helpers import REPO_ROOT


pytestmark = pytest.mark.prompt_quality


def test_plugin_marketplace_entry_help_is_populated() -> None:
    script = REPO_ROOT / "scripts" / "create_plugin_marketplace_entry.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    help_text = result.stdout
    assert "Emit marketplace JSON for a single plugin repository" in help_text
    assert "owner/repo source to include" in help_text
    assert "marketplace entry" in help_text
    assert "branch, tag, or commit to include" in help_text
    assert "plugin root path within the source repository" in help_text


def test_plugin_marketplace_entry_emits_expected_json() -> None:
    script = REPO_ROOT / "scripts" / "create_plugin_marketplace_entry.py"
    plugin_root = REPO_ROOT / "plugins" / "block-diagram"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--repo-root",
            str(plugin_root),
            "--repo",
            "intel-innersource/example-plugin-repo",
            "--ref",
            "main",
            "--path",
            "plugin-root",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    emitted = json.loads(result.stdout)
    assert emitted["name"] == "ceg-block-diagram"
    assert emitted["source"] == {
        "source": "github",
        "repo": "intel-innersource/example-plugin-repo",
        "ref": "main",
        "path": "plugin-root",
    }
    assert emitted["skills"] == ["skills/graphviz-dot"]


def test_plugin_marketplace_entry_reports_invalid_root_cleanly() -> None:
    script = REPO_ROOT / "scripts" / "create_plugin_marketplace_entry.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 1, result.stderr + result.stdout
    assert "requires a single-plugin repository root" in result.stderr.lower()
    assert "traceback" not in result.stderr.lower()