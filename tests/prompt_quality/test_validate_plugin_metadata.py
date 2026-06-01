from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from prompt_quality_helpers import REPO_ROOT


pytestmark = pytest.mark.prompt_quality


def _manual_remote_validation_enabled() -> bool:
    opt_in = os.getenv("CEG_VALIDATE_REMOTE_PLUGIN_SOURCES", "").strip().lower()
    return (
        opt_in in {"1", "true", "yes"}
        and bool(os.getenv("GITHUB_TOKEN"))
        and not bool(os.getenv("GITHUB_ACTIONS"))
    )


def _load_validate_plugin_metadata_module():
    script = REPO_ROOT / "scripts" / "validate_plugin_metadata.py"
    spec = importlib.util.spec_from_file_location("validate_plugin_metadata", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_plugin_metadata_requirements_help_is_populated() -> None:
    script = REPO_ROOT / "scripts" / "validate_plugin_metadata.py"
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
    assert "Validate or apply published plugin metadata requirements" in help_text
    assert "repository root containing either" in help_text
    assert ".github/plugin/marketplace.json or a root-level" in help_text
    assert "repo-root" in help_text
    assert "/home/ubuntu/Github/rtls.ai.copilot.ceg-copilot-instructions" not in help_text
    lower_help = help_text.lower()
    assert "local marketplace" in lower_help
    assert "plugin.json for same-repository entries" in lower_help
    assert "validation mode: auto-detect from repo layout" in help_text
    assert "canonical owner/repo name used to recognize" in help_text
    assert "generated from plugin.json" in help_text
    assert "emit-marketplace-entry" not in help_text
    assert "owner/repo source to include in emitted marketplace" not in help_text
    assert "branch, tag, or commit to include in emitted" not in help_text
    assert "plugin root path within the source repository" not in help_text


def test_plugin_metadata_requirements_are_applied(capsys) -> None:
    module = _load_validate_plugin_metadata_module()
    rc = module.main(["--repo-root", str(REPO_ROOT), "--check"])
    captured = capsys.readouterr()
    assert rc == 0, captured.err + captured.out
    assert "check passed" in captured.err.lower()


def test_plugin_metadata_requirements_default_to_check_with_message(capsys) -> None:
    module = _load_validate_plugin_metadata_module()
    rc = module.main(["--repo-root", str(REPO_ROOT)])
    captured = capsys.readouterr()
    assert rc == 0, captured.err + captured.out
    assert "defaulting to read-only validation" in captured.err.lower()
    assert "check passed" in captured.err.lower()


def test_plugin_metadata_requirements_finds_repo_root_from_scripts_dir(
    capsys, monkeypatch
) -> None:
    module = _load_validate_plugin_metadata_module()
    # Simulate running from scripts/ directory by pointing __file__ at the script
    script_path = str(REPO_ROOT / "scripts" / "validate_plugin_metadata.py")
    monkeypatch.setattr(module, "__file__", script_path)
    rc = module.main([])
    captured = capsys.readouterr()
    assert rc == 0, captured.err + captured.out
    assert "running check in marketplace mode" in captured.err.lower()
    assert "check passed" in captured.err.lower()


def test_plugin_metadata_requirements_apply_reports_noop(capsys) -> None:
    module = _load_validate_plugin_metadata_module()
    rc = module.main(["--repo-root", str(REPO_ROOT), "--apply"])
    captured = capsys.readouterr()
    assert rc == 0, captured.err + captured.out
    assert "no local metadata changes were required" in captured.err.lower()


def test_remote_fetch_uses_github_contents_api_urls() -> None:
    module = _load_validate_plugin_metadata_module()
    manifest_url = module.plugin_manifest_api_url(
        "intel-innersource/frameworks.validation.presilicon.vip.plusarg-utils",
        "main",
        "copilot_plugin",
    )
    component_url = module.github_contents_api_url(
        "intel-innersource/applications.services.design-system.cth-ai-fe-rtl-unit-test.repo",
        "main",
        "skills/unit-test.md",
    )
    assert manifest_url == (
        "https://api.github.com/repos/"
        "intel-innersource/frameworks.validation.presilicon.vip.plusarg-utils/"
        "contents/copilot_plugin/plugin.json?ref=main"
    )
    assert component_url == (
        "https://api.github.com/repos/"
        "intel-innersource/applications.services.design-system.cth-ai-fe-rtl-unit-test.repo/"
        "contents/skills/unit-test.md?ref=main"
    )


def test_same_repo_github_string_source_resolves_locally() -> None:
    module = _load_validate_plugin_metadata_module()
    resolved = module.resolve_local_source(
        REPO_ROOT,
        "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions:plugins/build-run",
        "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions",
    )
    assert resolved == REPO_ROOT / "plugins" / "build-run"


def test_same_repo_github_string_root_source_resolves_locally() -> None:
    module = _load_validate_plugin_metadata_module()
    resolved, error = module.resolve_local_source_with_error(
        REPO_ROOT,
        "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions:./",
        "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions",
    )
    assert error is None
    assert resolved == REPO_ROOT


def test_same_repo_structured_root_source_resolves_locally() -> None:
    module = _load_validate_plugin_metadata_module()
    resolved, error = module.resolve_local_source_with_error(
        REPO_ROOT,
        {
            "source": "github",
            "repo": "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions",
            "path": "./",
        },
        "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions",
    )
    assert error is None
    assert resolved == REPO_ROOT


def test_same_repo_github_url_source_resolves_locally() -> None:
    module = _load_validate_plugin_metadata_module()
    resolved, error = module.resolve_local_source_with_error(
        REPO_ROOT,
        "https://github.com/intel-innersource/rtls.ai.copilot.ceg-copilot-instructions",
        "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions",
    )
    assert error is None
    assert resolved == REPO_ROOT


def test_non_github_same_repo_object_is_not_resolved_locally() -> None:
    module = _load_validate_plugin_metadata_module()
    resolved, error = module.resolve_local_source_with_error(
        REPO_ROOT,
        {
            "source": "url",
            "repo": "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions",
            "path": "plugins/build-run",
            "url": "https://github.com/intel-innersource/example-repo",
        },
        "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions",
    )
    assert error is None
    assert resolved is None


def test_remote_source_parts_support_owner_repo_path_strings() -> None:
    module = _load_validate_plugin_metadata_module()
    assert module.remote_source_parts("intel-innersource/example-repo:plugin-root") == (
        "intel-innersource/example-repo",
        None,
        "plugin-root",
    )


def test_parse_github_source_string_rejects_non_repo_shapes() -> None:
    module = _load_validate_plugin_metadata_module()
    assert module.parse_github_source_string("owner/repo/subdir") is None
    assert module.parse_github_source_string("owner/repo/extra:plugin-root") is None


def test_remote_source_parts_support_github_url_strings() -> None:
    module = _load_validate_plugin_metadata_module()
    assert module.remote_source_parts("https://github.com/intel-innersource/example-repo") == (
        "intel-innersource/example-repo",
        None,
        "",
    )


def test_github_repo_from_url_rejects_browser_subpaths() -> None:
    module = _load_validate_plugin_metadata_module()
    assert module.github_repo_from_url("https://github.com/org/repo/tree/main/copilot_plugin") is None


def test_remote_source_parts_support_git_subdir_objects() -> None:
    module = _load_validate_plugin_metadata_module()
    assert module.remote_source_parts(
        {
            "source": "git-subdir",
            "url": "https://github.com/example/repo",
            "ref": "main",
            "path": "copilot_plugin",
        }
    ) == ("example/repo", "main", "copilot_plugin")


def test_remote_source_parts_support_url_objects() -> None:
    module = _load_validate_plugin_metadata_module()
    assert module.remote_source_parts(
        {
            "source": "url",
            "url": "https://github.com/example/repo",
            "ref": "main",
        }
    ) == ("example/repo", "main", "")


def test_apply_rewrites_generated_component_fields(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    plugin_root = tmp_path / "plugin"
    plugin_root.mkdir()
    (plugin_root / "fresh.agent.md").write_text("# Agent\n\nBody\n", encoding="utf-8")
    (plugin_root / "plugin.json").write_text(
        json.dumps(
            {
                "name": "ddg-example",
                "description": "Example plugin description",
                "version": "0.1.0",
                "keywords": ["example"],
                "skills": ["skills/stale.md"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.RunResult()
    manifest = module.apply_local_plugin_requirements(plugin_root, apply=True, result=result)

    assert manifest["agents"] == ["fresh.agent.md"]
    assert "skills" not in manifest


def test_apply_generates_skill_refs_from_skill_md_only(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    plugin_root = tmp_path / "plugin"
    skill_root = plugin_root / "skills" / "test-skill"
    skill_root.mkdir(parents=True)
    (skill_root / "SKILL.md").write_text("---\nname: test-skill\ndescription: test skill\n---\n", encoding="utf-8")
    (skill_root / "REFERENCE.md").write_text("# Extra notes\n", encoding="utf-8")
    (plugin_root / "plugin.json").write_text(
        json.dumps(
            {
                "name": "ddg-example",
                "description": "Example plugin description",
                "version": "0.1.0",
                "keywords": ["example"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.RunResult()
    manifest = module.apply_local_plugin_requirements(plugin_root, apply=True, result=result)

    assert manifest["skills"] == ["skills/test-skill"]


def test_apply_does_not_write_invalid_manifest(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    plugin_root = tmp_path / "plugin"
    plugin_root.mkdir()
    manifest_path = plugin_root / "plugin.json"
    original_text = json.dumps(
        {
            "name": "ddg-example",
            "description": "Example plugin description",
            "version": "0.1.0",
            "keywords": ["Example"],
        }
    ) + "\n"
    manifest_path.write_text(original_text, encoding="utf-8")

    result = module.RunResult()
    module.apply_local_plugin_requirements(plugin_root, apply=True, result=result)

    assert result.violations
    assert manifest_path.read_text(encoding="utf-8") == original_text


def test_plugin_metadata_validation_enforces_documented_field_contract() -> None:
    module = _load_validate_plugin_metadata_module()
    result = module.RunResult()

    module.validate_required_plugin_fields(
        REPO_ROOT / "plugins" / "example" / "plugin.json",
        {
            "name": "example-plugin",
            "description": "too short",
            "version": "0.1.0-dev",
            "keywords": ["Example"],
        },
        result,
    )

    messages = [violation.message for violation in result.violations]
    assert "description must be at least 20 characters" in messages
    assert "version must be semantic version (X.Y.Z): '0.1.0-dev'" in messages
    assert "keyword must be lowercase: 'Example'" in messages


def test_marketplace_apply_does_not_rewrite_local_manifests_before_full_validation(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    plugin_root = tmp_path / "plugins" / "example"
    plugin_root.mkdir(parents=True)
    (plugin_root / "example.agent.md").write_text("# Agent\n\nBody\n", encoding="utf-8")
    manifest_path = plugin_root / "plugin.json"
    original_text = json.dumps(
        {
            "name": "ddg-example",
            "description": "Example plugin description",
            "version": "0.1.0",
            "keywords": ["example"],
        }
    ) + "\n"
    manifest_path.write_text(original_text, encoding="utf-8")
    marketplace_dir = tmp_path / ".github" / "plugin"
    marketplace_dir.mkdir(parents=True)
    (marketplace_dir / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "plugins",
                "owner": {"name": "owner"},
                "metadata": {"version": "0.1.0"},
                "plugins": [
                    {
                        "name": "ddg-example",
                        "description": "Example plugin description",
                        "version": "0.1.0",
                    }
                ],
            }
        ) + "\n",
        encoding="utf-8",
    )

    result = module.RunResult()
    args = argparse.Namespace(apply=True, check_remotes=False, this_repo=module.DEFAULT_THIS_REPO)
    module.apply_marketplace_requirements(tmp_path, args, result)

    assert result.violations
    assert manifest_path.read_text(encoding="utf-8") == original_text


def test_discover_local_manifests_reports_duplicate_names(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    plugins_root = tmp_path / "plugins"
    first = plugins_root / "first"
    second = plugins_root / "second"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    manifest = {
        "name": "ddg-duplicate",
        "description": "Duplicate plugin description",
        "version": "0.1.0",
        "keywords": ["duplicate"],
    }
    (first / "plugin.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    (second / "plugin.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")

    result = module.RunResult()
    manifests = module.discover_local_manifests(tmp_path, apply=False, result=result)

    assert list(manifests) == ["ddg-duplicate"]
    assert any("duplicate local plugin name 'ddg-duplicate'" in violation.message for violation in result.violations)


def test_marketplace_local_source_must_match_plugin_name(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    plugins_root = tmp_path / "plugins"
    first = plugins_root / "first"
    second = plugins_root / "second"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    for plugin_dir, name in ((first, "ddg-first"), (second, "ddg-second")):
        (plugin_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": name,
                    "description": f"{name} description",
                    "version": "0.1.0",
                    "keywords": [name.removeprefix("ddg-")],
                }
            )
            + "\n",
            encoding="utf-8",
        )
    marketplace_dir = tmp_path / ".github" / "plugin"
    marketplace_dir.mkdir(parents=True)
    (marketplace_dir / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "plugins",
                "owner": {"name": "owner"},
                "plugins": [
                    {
                        "name": "ddg-first",
                        "description": "ddg-first description",
                        "version": "0.1.0",
                        "source": {
                            "source": "github",
                            "repo": "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions",
                            "path": "plugins/second",
                        },
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.RunResult()
    args = argparse.Namespace(apply=False, check_remotes=False, this_repo=module.DEFAULT_THIS_REPO)
    module.apply_marketplace_requirements(tmp_path, args, result)

    assert any("source resolves to plugins/second/plugin.json for plugin 'ddg-second'" in violation.message for violation in result.violations)


def test_marketplace_invalid_same_repo_source_is_reported_not_raised(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    plugins_root = tmp_path / "plugins"
    first = plugins_root / "first"
    first.mkdir(parents=True)
    (first / "plugin.json").write_text(
        json.dumps(
            {
                "name": "ddg-first",
                "description": "ddg-first description",
                "version": "0.1.0",
                "keywords": ["first"],
            }
        ) + "\n",
        encoding="utf-8",
    )
    marketplace_dir = tmp_path / ".github" / "plugin"
    marketplace_dir.mkdir(parents=True)
    marketplace_path = marketplace_dir / "marketplace.json"
    original_text = json.dumps(
        {
            "name": "plugins",
            "owner": {"name": "owner"},
            "metadata": {"version": "0.1.0"},
            "plugins": [
                {
                    "name": "ddg-first",
                    "description": "ddg-first description",
                    "version": "0.1.0",
                    "source": {
                        "source": "github",
                        "repo": "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions",
                        "path": "../broken",
                    },
                }
            ],
        }
    ) + "\n"
    marketplace_path.write_text(original_text, encoding="utf-8")

    result = module.RunResult()
    args = argparse.Namespace(apply=True, check_remotes=False, this_repo=module.DEFAULT_THIS_REPO)
    module.apply_marketplace_requirements(tmp_path, args, result)

    assert any("same-repository source path '../broken'" in violation.message for violation in result.violations)
    assert marketplace_path.read_text(encoding="utf-8") == original_text


def test_marketplace_entry_requires_description_version_and_source(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    marketplace_dir = tmp_path / ".github" / "plugin"
    marketplace_dir.mkdir(parents=True)
    (marketplace_dir / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "plugins",
                "owner": {"name": "owner"},
                "plugins": [
                    {
                        "name": "ddg-example",
                    }
                ],
            }
        ) + "\n",
        encoding="utf-8",
    )

    result = module.RunResult()
    args = argparse.Namespace(apply=False, check_remotes=False, this_repo=module.DEFAULT_THIS_REPO)
    module.apply_marketplace_requirements(tmp_path, args, result)

    messages = [violation.message for violation in result.violations]
    assert "missing required field 'description'" in messages
    assert "missing required field 'version'" in messages
    assert "missing required field 'source'" in messages


def test_marketplace_entry_validates_declared_metadata_values(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    marketplace_dir = tmp_path / ".github" / "plugin"
    marketplace_dir.mkdir(parents=True)
    (marketplace_dir / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "plugins",
                "owner": {"name": "owner"},
                "plugins": [
                    {
                        "name": "External Plugin",
                        "description": "short",
                        "version": "latest",
                        "keywords": ["Example"],
                        "source": "intel-innersource/example-repo:plugin-root",
                    }
                ],
            }
        ) + "\n",
        encoding="utf-8",
    )

    result = module.RunResult()
    args = argparse.Namespace(apply=False, check_remotes=False, this_repo=module.DEFAULT_THIS_REPO)
    module.apply_marketplace_requirements(tmp_path, args, result)

    messages = [violation.message for violation in result.violations]
    assert "name must be kebab-case, lowercase, and at most 64 characters: 'External Plugin'" in messages
    assert "description must be at least 20 characters" in messages
    assert "version must be semver: 'latest'" in messages
    assert "keyword must be lowercase: 'Example'" in messages


def test_marketplace_rejects_non_string_structured_source_fields(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    marketplace_dir = tmp_path / ".github" / "plugin"
    marketplace_dir.mkdir(parents=True)
    (marketplace_dir / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "plugins",
                "owner": {"name": "owner"},
                "plugins": [
                    {
                        "name": "external-plugin",
                        "description": "External plugin description",
                        "version": "1.0.0",
                        "source": {
                            "source": "github",
                            "repo": ["example/repo"],
                            "ref": ["main"],
                        },
                    }
                ],
            }
        ) + "\n",
        encoding="utf-8",
    )

    result = module.RunResult()
    args = argparse.Namespace(apply=False, check_remotes=False, this_repo=module.DEFAULT_THIS_REPO)
    module.apply_marketplace_requirements(tmp_path, args, result)

    messages = [violation.message for violation in result.violations]
    assert "external-plugin: source.repo must be a string" in messages
    assert "external-plugin: source.ref must be a string" in messages


def test_marketplace_rejects_non_object_top_level_metadata(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    marketplace_dir = tmp_path / ".github" / "plugin"
    marketplace_dir.mkdir(parents=True)
    (marketplace_dir / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "plugins",
                "owner": {"name": "owner"},
                "metadata": [],
                "plugins": [],
            }
        ) + "\n",
        encoding="utf-8",
    )

    result = module.RunResult()
    args = argparse.Namespace(apply=True, check_remotes=False, this_repo=module.DEFAULT_THIS_REPO)
    module.apply_marketplace_requirements(tmp_path, args, result)

    messages = [violation.message for violation in result.violations]
    assert "metadata must be an object" in messages


def test_marketplace_accepts_git_subdir_source_objects(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    marketplace_dir = tmp_path / ".github" / "plugin"
    marketplace_dir.mkdir(parents=True)
    (marketplace_dir / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "plugins",
                "owner": {"name": "owner"},
                "plugins": [
                    {
                        "name": "external-plugin",
                        "description": "External plugin description",
                        "version": "1.0.0",
                        "source": {
                            "source": "git-subdir",
                            "url": "https://github.com/example/repo",
                            "ref": "main",
                            "path": "copilot_plugin",
                        },
                    }
                ],
            }
        ) + "\n",
        encoding="utf-8",
    )

    result = module.RunResult()
    args = argparse.Namespace(apply=False, check_remotes=False, this_repo=module.DEFAULT_THIS_REPO)
    module.apply_marketplace_requirements(tmp_path, args, result)

    assert not result.violations


def test_marketplace_accepts_url_source_objects(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    marketplace_dir = tmp_path / ".github" / "plugin"
    marketplace_dir.mkdir(parents=True)
    (marketplace_dir / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "plugins",
                "owner": {"name": "owner"},
                "plugins": [
                    {
                        "name": "external-plugin",
                        "description": "External plugin description",
                        "version": "1.0.0",
                        "source": {
                            "source": "url",
                            "url": "https://github.com/example/repo",
                            "ref": "main",
                        },
                    }
                ],
            }
        ) + "\n",
        encoding="utf-8",
    )

    result = module.RunResult()
    args = argparse.Namespace(apply=False, check_remotes=False, this_repo=module.DEFAULT_THIS_REPO)
    module.apply_marketplace_requirements(tmp_path, args, result)

    assert not result.violations


def test_marketplace_external_sources_allow_named_refs(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    marketplace_dir = tmp_path / ".github" / "plugin"
    marketplace_dir.mkdir(parents=True)
    (marketplace_dir / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "plugins",
                "owner": {"name": "owner"},
                "plugins": [
                    {
                        "name": "external-plugin",
                        "description": "External plugin description",
                        "version": "1.0.0",
                        "source": {
                            "source": "github",
                            "repo": "example/repo",
                            "ref": "main",
                        },
                    }
                ],
            }
        ) + "\n",
        encoding="utf-8",
    )

    result = module.RunResult()
    args = argparse.Namespace(apply=False, check_remotes=False, this_repo=module.DEFAULT_THIS_REPO)
    module.apply_marketplace_requirements(tmp_path, args, result)

    assert not any("40-character commit SHA" in violation.message for violation in result.violations)
    assert not any("external source needs ref, sha, or commit" in violation.message for violation in result.violations)


def test_marketplace_external_owner_repo_path_string_passes_plain_check(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    marketplace_dir = tmp_path / ".github" / "plugin"
    marketplace_dir.mkdir(parents=True)
    (marketplace_dir / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "plugins",
                "owner": {"name": "owner"},
                "plugins": [
                    {
                        "name": "external-plugin",
                        "description": "External plugin description",
                        "version": "1.0.0",
                        "source": "intel-innersource/example-repo:plugin-root",
                    }
                ],
            }
        ) + "\n",
        encoding="utf-8",
    )

    result = module.RunResult()
    args = argparse.Namespace(apply=False, check_remotes=False, this_repo=module.DEFAULT_THIS_REPO)
    module.apply_marketplace_requirements(tmp_path, args, result)

    assert not result.violations


def test_marketplace_external_github_url_string_passes_plain_check(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    marketplace_dir = tmp_path / ".github" / "plugin"
    marketplace_dir.mkdir(parents=True)
    (marketplace_dir / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "plugins",
                "owner": {"name": "owner"},
                "plugins": [
                    {
                        "name": "external-plugin",
                        "description": "External plugin description",
                        "version": "1.0.0",
                        "source": "https://github.com/intel-innersource/example-repo",
                    }
                ],
            }
        ) + "\n",
        encoding="utf-8",
    )

    result = module.RunResult()
    args = argparse.Namespace(apply=False, check_remotes=False, this_repo=module.DEFAULT_THIS_REPO)
    module.apply_marketplace_requirements(tmp_path, args, result)

    assert not result.violations


def test_marketplace_external_owner_repo_path_string_needs_ref_for_remote_fetch(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    marketplace_dir = tmp_path / ".github" / "plugin"
    marketplace_dir.mkdir(parents=True)
    (marketplace_dir / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "plugins",
                "owner": {"name": "owner"},
                "plugins": [
                    {
                        "name": "external-plugin",
                        "description": "External plugin description",
                        "version": "1.0.0",
                        "source": "intel-innersource/example-repo:plugin-root",
                    }
                ],
            }
        ) + "\n",
        encoding="utf-8",
    )

    result = module.RunResult()
    args = argparse.Namespace(
        apply=False,
        check_remotes=True,
        this_repo=module.DEFAULT_THIS_REPO,
        github_token_env="GITHUB_TOKEN",
    )
    module.apply_marketplace_requirements(tmp_path, args, result)

    assert any(
        "external-plugin: external source needs ref, sha, or commit for remote fetchability"
        in warning
        for warning in result.warnings
    )


def test_promoted_marketplace_entry_removes_stale_mirrored_fields() -> None:
    module = _load_validate_plugin_metadata_module()
    promoted = module.promoted_marketplace_entry(
        {
            "name": "ddg-example",
            "description": "old description",
            "version": "0.0.1",
            "keywords": ["old"],
            "category": "legacy-category",
            "tags": ["legacy-tag"],
            "agents": ["legacy.agent.md"],
            "source": {
                "source": "github",
                "repo": "intel-innersource/rtls.ai.copilot.ceg-copilot-instructions",
                "path": "plugins/example",
            },
        },
        {
            "name": "ddg-example",
            "description": "new description",
            "version": "0.1.0",
            "keywords": ["current"],
        },
    )
    assert promoted["description"] == "new description"
    assert promoted["version"] == "0.1.0"
    assert promoted["keywords"] == ["current"]
    assert "category" not in promoted
    assert "tags" not in promoted
    assert "agents" not in promoted


def test_local_marketplace_drift_points_back_to_plugin_manifest() -> None:
    module = _load_validate_plugin_metadata_module()
    result = module.RunResult()
    module.validate_current_matches_expected(
        REPO_ROOT / ".github" / "plugin" / "marketplace.json",
        {"name": "ddg-example", "description": "old"},
        {"name": "ddg-example", "description": "new"},
        ("name", "description"),
        result,
        generator_owner="plugins/example/plugin.json",
    )
    assert result.violations == [
        module.Violation(
            str(REPO_ROOT / ".github" / "plugin" / "marketplace.json"),
            "description should be 'new'; local marketplace entries are generated from plugins/example/plugin.json",
        )
    ]


def test_local_marketplace_drift_reports_stale_optional_metadata() -> None:
    module = _load_validate_plugin_metadata_module()
    result = module.RunResult()
    module.validate_marketplace_metadata_matches_manifest(
        REPO_ROOT / ".github" / "plugin" / "marketplace.json",
        {
            "name": "ddg-example",
            "description": "Example plugin",
            "version": "0.1.0",
            "tags": ["legacy"],
        },
        {
            "name": "ddg-example",
            "description": "Example plugin",
            "version": "0.1.0",
        },
        result,
        subject="ddg-example",
    )
    assert any("ddg-example: tags should be omitted because the manifest does not declare it" in violation.message for violation in result.violations)


def test_build_marketplace_entry_uses_mirrored_manifest_projection() -> None:
    module = _load_validate_plugin_metadata_module()
    entry = module.build_marketplace_entry(
        {
            "name": "ddg-example",
            "description": "Example plugin",
            "version": "0.1.0",
            "keywords": ["example"],
            "category": "verification",
            "tags": ["portable"],
            "skills": ["skills/example.md"],
        },
        repo="intel-innersource/example",
        ref="main",
        path="plugin-root",
    )
    assert entry == {
        "name": "ddg-example",
        "description": "Example plugin",
        "version": "0.1.0",
        "keywords": ["example"],
        "category": "verification",
        "tags": ["portable"],
        "source": {
            "source": "github",
            "repo": "intel-innersource/example",
            "ref": "main",
            "path": "plugin-root",
        },
        "skills": ["skills/example.md"],
    }


def test_build_marketplace_entry_normalizes_root_path() -> None:
    module = _load_validate_plugin_metadata_module()
    entry = module.build_marketplace_entry(
        {
            "name": "ddg-example",
            "description": "Example plugin",
            "version": "0.1.0",
            "keywords": ["example"],
        },
        repo="intel-innersource/example",
        ref="main",
        path="./",
    )
    assert entry["source"] == {
        "source": "github",
        "repo": "intel-innersource/example",
        "ref": "main",
    }


def test_build_marketplace_entry_rejects_invalid_path() -> None:
    module = _load_validate_plugin_metadata_module()
    with pytest.raises(ValueError, match="path must not escape the plugin root"):
        module.build_marketplace_entry(
            {
                "name": "ddg-example",
                "description": "Example plugin",
                "version": "0.1.0",
                "keywords": ["example"],
            },
            repo="intel-innersource/example",
            path="../plugin",
        )


def test_remote_validation_warns_on_legacy_metadata_only_refs() -> None:
    module = _load_validate_plugin_metadata_module()
    result = module.RunResult()
    module.validate_remote_component_refs(
        manifest_url="https://api.github.com/repos/example/repo/contents/plugin.json?ref=main",
        repo="example/repo",
        ref="main",
        plugin_path="",
        data={"agents": ["agents/"], "skills": ["skills/", "./"]},
        token="dummy",
        result=result,
        strict_metadata=False,
    )
    assert not result.violations
    assert any("agents ref 'agents/' is metadata-only" in warning for warning in result.warnings)
    assert any("skills ref 'skills/' is metadata-only" in warning for warning in result.warnings)
    assert any("skills ref './' is metadata-only" in warning for warning in result.warnings)


def test_remote_validation_enforces_required_and_forbidden_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_validate_plugin_metadata_module()
    entry = {
        "name": "remote-plugin",
        "source": {
            "source": "github",
            "repo": "example/repo",
            "ref": "main",
            "path": "",
        },
    }
    result = module.RunResult()
    monkeypatch.setenv("GITHUB_TOKEN", "dummy-token")
    monkeypatch.setattr(
        module,
        "fetch_remote_json",
        lambda url, *, token: {
            "name": "remote-plugin",
            "description": "Remote plugin",
            "version": "0.1.0",
            "capabilities": ["legacy"],
        },
    )
    monkeypatch.setattr(module, "fetch_remote_text", lambda url, *, token: None)

    module.validate_remote_source(
        entry,
        argparse.Namespace(github_token_env="GITHUB_TOKEN"),
        result,
        REPO_ROOT / ".github" / "plugin" / "marketplace.json",
    )

    warnings = result.warnings
    assert any("missing required field 'keywords'" in warning for warning in warnings)
    assert any("keywords must be a non-empty list" in warning for warning in warnings)
    assert any("consumer-private field 'capabilities'" in warning for warning in warnings)


def test_remote_validation_reports_non_object_json_as_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_validate_plugin_metadata_module()
    entry = {
        "name": "remote-plugin",
        "source": {
            "source": "github",
            "repo": "example/repo",
            "ref": "main",
            "path": "",
        },
    }
    result = module.RunResult()
    monkeypatch.setenv("GITHUB_TOKEN", "dummy-token")
    monkeypatch.setattr(
        module,
        "fetch_remote_json",
        lambda url, *, token: (_ for _ in ()).throw(ValueError("remote JSON root must be an object")),
    )

    module.validate_remote_source(
        entry,
        argparse.Namespace(github_token_env="GITHUB_TOKEN"),
        result,
        REPO_ROOT / ".github" / "plugin" / "marketplace.json",
    )

    assert any("remote JSON root must be an object" in warning for warning in result.warnings)


def test_remote_validation_checks_marketplace_metadata_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_validate_plugin_metadata_module()
    entry = {
        "name": "remote-plugin",
        "description": "Old description",
        "version": "0.0.1",
        "source": {
            "source": "github",
            "repo": "example/repo",
            "ref": "1234567890abcdef1234567890abcdef12345678",
        },
    }
    result = module.RunResult()
    monkeypatch.setenv("GITHUB_TOKEN", "dummy-token")
    monkeypatch.setattr(
        module,
        "fetch_remote_json",
        lambda url, *, token: {
            "name": "remote-plugin",
            "description": "Remote description",
            "version": "1.2.3",
            "keywords": ["remote"],
        },
    )
    monkeypatch.setattr(module, "fetch_remote_text", lambda url, *, token: None)

    module.validate_remote_source(
        entry,
        argparse.Namespace(github_token_env="GITHUB_TOKEN"),
        result,
        REPO_ROOT / ".github" / "plugin" / "marketplace.json",
    )

    warnings = result.warnings
    assert any("remote-plugin: description should be 'Remote description'" in warning for warning in warnings)
    assert any("remote-plugin: version should be '1.2.3'" in warning for warning in warnings)
    assert any("remote-plugin: keywords should be ['remote']" in warning for warning in warnings)


def test_remote_validation_warns_on_legacy_metadata_only_refs_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_validate_plugin_metadata_module()
    entry = {
        "name": "remote-plugin",
        "source": {
            "source": "github",
            "repo": "example/repo",
            "ref": "main",
            "path": "",
        },
    }
    result = module.RunResult()
    monkeypatch.setenv("GITHUB_TOKEN", "dummy-token")
    monkeypatch.setattr(
        module,
        "fetch_remote_json",
        lambda url, *, token: {
            "name": "remote-plugin",
            "description": "Remote plugin description",
            "version": "1.0.0",
            "keywords": ["remote"],
            "skills": ["skills/"],
        },
    )
    monkeypatch.setattr(module, "fetch_remote_text", lambda url, *, token: None)

    module.validate_remote_source(
        entry,
        argparse.Namespace(github_token_env="GITHUB_TOKEN"),
        result,
        REPO_ROOT / ".github" / "plugin" / "marketplace.json",
    )

    assert any("skills ref 'skills/' is metadata-only; use explicit files" in warning for warning in result.warnings)


def test_remote_validation_attempts_anonymous_fetch_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_validate_plugin_metadata_module()
    entry = {
        "name": "remote-plugin",
        "source": {
            "source": "github",
            "repo": "example/repo",
            "ref": "main",
        },
    }
    result = module.RunResult()
    seen_tokens: list[str] = []

    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(
        module,
        "fetch_remote_json",
        lambda url, *, token: seen_tokens.append(token) or {
            "name": "remote-plugin",
            "description": "Remote plugin description",
            "version": "1.0.0",
            "keywords": ["remote"],
        },
    )
    monkeypatch.setattr(module, "fetch_remote_text", lambda url, *, token: None)

    module.validate_remote_source(
        entry,
        argparse.Namespace(github_token_env="GITHUB_TOKEN"),
        result,
        REPO_ROOT / ".github" / "plugin" / "marketplace.json",
    )

    assert seen_tokens == [""]


def test_validate_explicit_component_refs_enforces_expected_file_types(tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    plugin_root = tmp_path / "plugin"
    plugin_root.mkdir()
    (plugin_root / "README.md").write_text("# Readme\n", encoding="utf-8")
    (plugin_root / "notes.txt").write_text("notes\n", encoding="utf-8")

    result = module.RunResult()
    module.validate_explicit_component_refs(
        plugin_root / "plugin.json",
        plugin_root,
        {
            "agents": ["README.md"],
            "skills": ["notes.txt"],
        },
        result,
    )

    messages = [violation.message for violation in result.violations]
    assert "agents ref 'README.md' must point to an explicit .agent.md file" in messages
    assert "skills ref 'notes.txt' must be a skill directory path (e.g. skills/my-skill)" in messages


def test_load_repo_dotenv_sets_missing_values_without_overwriting(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_validate_plugin_metadata_module()
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "# comment\n"
        "GITHUB_TOKEN=from-dotenv\n"
        "export OTHER_VAR=other-value\n"
        "QUOTED=\"quoted value\"\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("OTHER_VAR", "already-set")
    monkeypatch.delenv("QUOTED", raising=False)

    module.load_repo_dotenv(tmp_path)

    assert os.environ["GITHUB_TOKEN"] == "from-dotenv"
    assert os.environ["OTHER_VAR"] == "already-set"
    assert os.environ["QUOTED"] == "quoted value"


@pytest.mark.skipif(
    not _manual_remote_validation_enabled(),
    reason=(
        "remote plugin checks need CEG_VALIDATE_REMOTE_PLUGIN_SOURCES=1 and "
        "GITHUB_TOKEN outside GitHub Actions"
    ),
)
def test_remote_plugin_sources_are_fetchable() -> None:
    script = REPO_ROOT / "scripts" / "validate_plugin_metadata.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--repo-root",
            str(REPO_ROOT),
            "--check",
            "--check-remotes",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout