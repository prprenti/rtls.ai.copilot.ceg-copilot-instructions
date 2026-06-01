from __future__ import annotations

import asyncio

import pytest

from validation_mcp.runtime import client_factory
from validation_mcp.runtime.pagination import apply_pagination_policy
from validation_mcp.runtime.query_adapter import normalize_post_data
from validation_mcp.runtime.tool_runtime import parse_json_object_argument, run_vmanager_tool
from validation_mcp.server import create_mcp, plugin_root_for
from validation_mcp.settings import Settings


def test_settings_from_env_reads_validation_defaults(monkeypatch) -> None:
    monkeypatch.setenv("VMGR_USER", "jdoe")
    monkeypatch.setenv("VALIDATION_MCP_MAX_PAGE_LENGTH", "80")

    settings = Settings.from_env("/tmp/repo")

    assert settings.repo_root == "/tmp/repo"
    assert settings.username == "jdoe"
    assert settings.max_page_length == 80
    assert settings.pretty_json is True
    assert settings.enable_client_cache is False


def test_settings_allows_minimal_construction() -> None:
    settings = Settings(repo_root="/tmp/repo")

    assert settings.api_base_path is None
    assert settings.username is None
    assert settings.password is None
    assert settings.token_path is None
    assert settings.verify is None


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("1", True),
        ("true", True),
        ("0", False),
        ("false", False),
        ("/etc/ssl/custom-ca.pem", "/etc/ssl/custom-ca.pem"),
    ],
)
def test_settings_from_env_parses_verify_values(
    monkeypatch: pytest.MonkeyPatch,
    raw_value: str,
    expected: bool | str,
) -> None:
    monkeypatch.setenv("VAPI_VERIFY", raw_value)

    settings = Settings.from_env("/tmp/repo")

    assert settings.verify == expected


def test_settings_from_env_treats_blank_verify_as_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VAPI_VERIFY", "   ")

    settings = Settings.from_env("/tmp/repo")

    assert settings.verify is None


def test_settings_from_env_reads_pretty_json_toggle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VALIDATION_MCP_PRETTY_JSON", "false")

    settings = Settings.from_env("/tmp/repo")

    assert settings.pretty_json is False


def test_settings_from_env_reports_invalid_page_length(monkeypatch) -> None:
    monkeypatch.setenv("VALIDATION_MCP_MAX_PAGE_LENGTH", "abc")

    with pytest.raises(
        ValueError,
        match=r"^VALIDATION_MCP_MAX_PAGE_LENGTH must be an integer, got 'abc'$",
    ):
        Settings.from_env("/tmp/repo")


@pytest.mark.parametrize("raw_value", ["0", "-1"])
def test_settings_from_env_rejects_non_positive_page_length(
    monkeypatch: pytest.MonkeyPatch,
    raw_value: str,
) -> None:
    monkeypatch.setenv("VALIDATION_MCP_MAX_PAGE_LENGTH", raw_value)

    with pytest.raises(
        ValueError,
        match=rf"^VALIDATION_MCP_MAX_PAGE_LENGTH must be >= 1, got {int(raw_value)!r}$",
    ):
        Settings.from_env("/tmp/repo")


def test_parse_json_object_argument_rejects_non_object_json() -> None:
    with pytest.raises(ValueError, match=r"^filter must decode to a JSON object$"):
        parse_json_object_argument('[1, 2, 3]', label="filter")


def test_apply_pagination_policy_caps_page_length() -> None:
    with pytest.raises(ValueError, match=r"^pageLength must be <= 100$"):
        apply_pagination_policy(
            {"filter": {}, "pageLength": 500},
            max_page_length=100,
        )


def test_apply_pagination_policy_preserves_absent_paging_keys() -> None:
    post_data = apply_pagination_policy(
        {"filter": {}},
        max_page_length=100,
    )

    assert post_data == {"filter": {}}


def test_apply_pagination_policy_rejects_unimplemented_fetch_all() -> None:
    with pytest.raises(
        ValueError,
        match=r"^fetch_all/fetchAll is not supported by validation-mcp list tools; remove the key and request another page explicitly$",
    ):
        apply_pagination_policy(
            {"filter": {}, "fetch_all": True, "fetchAll": True},
            max_page_length=100,
        )


def test_apply_pagination_policy_rejects_explicit_false_fetch_all() -> None:
    with pytest.raises(
        ValueError,
        match=r"^fetch_all/fetchAll is not supported by validation-mcp list tools; remove the key and request another page explicitly$",
    ):
        apply_pagination_policy(
            {"filter": {}, "fetch_all": False},
            max_page_length=100,
        )


def test_apply_pagination_policy_rejects_non_boolean_fetch_all() -> None:
    with pytest.raises(ValueError, match=r"^fetch_all must be a boolean$"):
        apply_pagination_policy(
            {"filter": {}, "fetch_all": "false"},
            max_page_length=100,
        )


def test_apply_pagination_policy_reports_mismatched_fetch_all_values() -> None:
    with pytest.raises(
        ValueError,
        match=r"^fetch_all and fetchAll must match when both are provided; got False and True$",
    ):
        apply_pagination_policy(
            {"filter": {}, "fetch_all": False, "fetchAll": True},
            max_page_length=100,
        )


def test_settings_with_overrides_allows_explicit_none() -> None:
    settings = Settings(
        repo_root="/tmp/repo",
        api_base_path="https://example.test",
        username="jdoe",
        password="secret-password",
        token_path="/tmp/token",
        verify="1",
    )

    updated = settings.with_overrides(password=None, verify=None)

    assert updated.password is None
    assert updated.verify is None


def test_normalize_post_data_preserves_explicit_none_values() -> None:
    normalized = normalize_post_data(
        {
            "filter": {"attName": "name", "attValue": None},
            "projection": None,
            "items": [{"id": 1, "note": None}],
        }
    )

    assert normalized == {
        "filter": {"attName": "name", "attValue": None},
        "projection": None,
        "items": [{"id": 1, "note": None}],
    }


def test_plugin_root_for_returns_plugin_root() -> None:
    server_file = "/tmp/ws/plugins/validation/mcp-server/validation_mcp/server.py"

    assert plugin_root_for(server_file) == "/tmp/ws/plugins/validation"


def test_create_mcp_instructions_list_actual_session_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeFastMCP:
        def __init__(self, name: str, **kwargs: object):
            captured["name"] = name
            captured.update(kwargs)

    monkeypatch.setattr("validation_mcp.server.FastMCP", FakeFastMCP)
    monkeypatch.setattr("validation_mcp.server.register_vmanager_tools", lambda mcp, settings: None)
    monkeypatch.setattr(
        "validation_mcp.server.register_register_topology_tools",
        lambda mcp, repo_root: None,
    )

    settings = Settings(
        repo_root="/tmp/repo",
        api_base_path=None,
        username=None,
        password=None,
        token_path=None,
        verify=None,
    )

    create_mcp(settings)

    instructions = str(captured["instructions"])
    assert "vamp_vsif_group_get, vamp_vsif_groups_list/create/update/delete" in instructions
    assert "vamp_vsif_test_get, vamp_vsif_tests_list/create/update/delete" in instructions
    assert "vamp_vsif_groups_list/get/create/update/delete" not in instructions
    assert "vamp_vsif_tests_list/get/create/update/delete" not in instructions
    assert "vamp_sessions_list, vamp_sessions_count" in instructions
    assert "vamp_vsif_session_get/create/create_with_permissions/delete" in instructions
    assert "vamp_vsif_session_list" not in instructions
    assert "vamp_plan_find" in instructions
    assert "vamp_plan_update_bulk" in instructions
    assert "vamp_plan_update_section" in instructions
    assert "vamp_plan_update_reference" in instructions


def test_settings_repr_redacts_secret_fields() -> None:
    settings = Settings(
        repo_root="/tmp/repo",
        api_base_path="https://example.test",
        username="jdoe",
        password="secret-password",
        token_path="/tmp/token",
        verify=None,
    )

    rendered = repr(settings)
    assert "secret-password" not in rendered
    assert "/tmp/token" not in rendered


def test_run_vmanager_tool_returns_error_string_when_debug_enabled(monkeypatch) -> None:
    settings = Settings(
        repo_root="/tmp/repo",
        api_base_path=None,
        username=None,
        password=None,
        token_path=None,
        verify=None,
        debug_errors=True,
    )

    monkeypatch.setattr(
        "validation_mcp.runtime.tool_runtime.client_factory.get_vmanager_client",
        lambda _settings: object(),
    )

    result = asyncio.run(
        run_vmanager_tool(
            "demo_tool",
            settings,
            lambda _client, _settings: (_ for _ in ()).throw(RuntimeError("boom\nmore detail")),
        )
    )

    assert result == "ERROR: boom\nmore detail"


def test_run_vmanager_tool_logs_success_at_debug(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    settings = Settings(repo_root="/tmp/repo")

    monkeypatch.setattr(
        "validation_mcp.runtime.tool_runtime.client_factory.get_vmanager_client",
        lambda _settings: object(),
    )

    with caplog.at_level("DEBUG", logger="validation-mcp.tool-runtime"):
        result = asyncio.run(
            run_vmanager_tool(
                "demo_tool",
                settings,
                lambda _client, _settings: {"ok": True},
            )
        )

    assert result == '{\n  "ok": true\n}'
    assert any(
        record.levelname == "DEBUG" and "tool=demo_tool" in record.message
        for record in caplog.records
    )


def test_run_vmanager_tool_can_render_compact_json(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(repo_root="/tmp/repo", pretty_json=False)

    monkeypatch.setattr(
        "validation_mcp.runtime.tool_runtime.client_factory.get_vmanager_client",
        lambda _settings: object(),
    )

    result = asyncio.run(
        run_vmanager_tool(
            "demo_tool",
            settings,
            lambda _client, _settings: {"ok": True},
        )
    )

    assert result == '{"ok": true}'


def test_run_vmanager_tool_truncates_error_when_debug_disabled(monkeypatch) -> None:
    settings = Settings(
        repo_root="/tmp/repo",
        api_base_path=None,
        username=None,
        password=None,
        token_path=None,
        verify=None,
        debug_errors=False,
    )

    monkeypatch.setattr(
        "validation_mcp.runtime.tool_runtime.client_factory.get_vmanager_client",
        lambda _settings: object(),
    )

    result = asyncio.run(
        run_vmanager_tool(
            "demo_tool",
            settings,
            lambda _client, _settings: (_ for _ in ()).throw(RuntimeError("boom\nmore detail")),
        )
    )

    assert result == "ERROR: boom"


def test_get_vmanager_client_without_cache_builds_each_time(monkeypatch: pytest.MonkeyPatch) -> None:
    client_factory.clear_client_cache()
    created_clients: list[object] = []

    def fake_new_client(_settings: Settings) -> object:
        client = object()
        created_clients.append(client)
        return client

    monkeypatch.setattr(client_factory, "_new_vmanager_client", fake_new_client)

    settings = Settings(repo_root="/tmp/repo")

    first = client_factory.get_vmanager_client(settings)
    second = client_factory.get_vmanager_client(settings)

    assert first is not second
    assert len(created_clients) == 2


def test_get_vmanager_client_with_cache_reuses_matching_client(monkeypatch: pytest.MonkeyPatch) -> None:
    client_factory.clear_client_cache()
    created_clients: list[object] = []

    def fake_new_client(_settings: Settings) -> object:
        client = object()
        created_clients.append(client)
        return client

    monkeypatch.setattr(client_factory, "_new_vmanager_client", fake_new_client)

    settings = Settings(repo_root="/tmp/repo", enable_client_cache=True)

    first = client_factory.get_vmanager_client(settings)
    second = client_factory.get_vmanager_client(settings)

    assert first is second
    assert len(created_clients) == 1


def test_get_vmanager_client_cache_evicts_lru_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    client_factory.clear_client_cache()
    created_clients: list[str] = []

    def fake_new_client(settings: Settings) -> str:
        client = f"client-{settings.repo_root}-{len(created_clients)}"
        created_clients.append(client)
        return client

    monkeypatch.setattr(client_factory, "_new_vmanager_client", fake_new_client)

    cached_settings = [
        Settings(repo_root=f"/tmp/repo-{index}", enable_client_cache=True)
        for index in range(5)
    ]

    first_client = client_factory.get_vmanager_client(cached_settings[0])
    for settings in cached_settings[1:]:
        client_factory.get_vmanager_client(settings)

    replacement_client = client_factory.get_vmanager_client(cached_settings[0])

    assert first_client != replacement_client
    assert len(created_clients) == 6


def test_clear_client_cache_forces_rebuild(monkeypatch: pytest.MonkeyPatch) -> None:
    client_factory.clear_client_cache()
    created_clients: list[object] = []

    def fake_new_client(_settings: Settings) -> object:
        client = object()
        created_clients.append(client)
        return client

    monkeypatch.setattr(client_factory, "_new_vmanager_client", fake_new_client)

    settings = Settings(repo_root="/tmp/repo", enable_client_cache=True)

    first = client_factory.get_vmanager_client(settings)
    client_factory.clear_client_cache()
    second = client_factory.get_vmanager_client(settings)

    assert first is not second
    assert len(created_clients) == 2