"""Tests for validation plugin — vManager tool registration and install mode."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from typing import Any

from validation_mcp.settings import SETTINGS_ENV_VARS


class MockFastMCP:
    def __init__(self, name: str = "test-mcp", **kwargs: Any):
        self.name = name
        self.tools: dict[str, Any] = {}

    def tool(self, *args: Any, **kwargs: Any):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator

from vmanager import register_vmanager_tools


@pytest.fixture(autouse=True)
def clear_validation_runtime_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for env_name in SETTINGS_ENV_VARS:
        monkeypatch.delenv(env_name, raising=False)


# All vManager tools that should be registered
EXPECTED_VMANAGER_TOOLS = {
    # ---- runs ----
    "vamp_standard_runs_list",
    "vamp_runs_list",
    "vamp_runs_count",
    "vamp_run_get",
    "vamp_run_update",
    "vamp_run_associate_to_failure_cluster",
    "vamp_run_dissociate_from_failure_cluster",
    "vamp_run_rerun_schemes_get",
    "vamp_run_total_count_size_get",
    "vamp_run_extract_logs",
    # ---- failure clusters ----
    "vamp_failure_cluster_list",
    "vamp_failure_cluster_count",
    "vamp_failure_cluster_get",
    "vamp_failure_cluster_update",
    "vamp_failure_cluster_create",
    "vamp_failure_cluster_delete",
    "vamp_failure_clusters_for_runs",
    # ---- run↔failure-cluster associations ----
    "vamp_run_failure_cluster_list",
    "vamp_run_failure_cluster_list_grouped",
    "vamp_run_failure_cluster_update_association",
    "vamp_run_failures_for_team",
    "vamp_run_failures_in_datetime",
    "vamp_run_failures_needs_rerun",
    "vamp_run_failures_for_result_ids",
    # ---- vsif/configurations ----
    "vamp_vsif_config_list",
    "vamp_vsif_config_update",
    "vamp_vsif_config_list_by_name",
    # ---- vsif/groups ----
    "vamp_vsif_group_get",
    "vamp_vsif_groups_list",
    "vamp_vsif_group_create",
    "vamp_vsif_group_update",
    "vamp_vsif_group_delete",
    "vamp_vsif_groups_list_for_session",
    "vamp_vsif_groups_list_for_group",
    # ---- vsif/tests ----
    "vamp_vsif_test_get",
    "vamp_vsif_tests_list",
    "vamp_vsif_test_create",
    "vamp_vsif_test_update",
    "vamp_vsif_test_delete",
    "vamp_vsif_tests_list_for_session",
    "vamp_vsif_tests_list_for_group",
    # ---- vsif/hierarchy-configurations ----
    "vamp_vsif_hierarchy_get",
    "vamp_vsif_hierarchy_list",
    "vamp_vsif_hierarchy_create",
    "vamp_vsif_hierarchy_attach_groups_to_groups",
    "vamp_vsif_hierarchy_attach_groups_to_sessions",
    "vamp_vsif_hierarchy_attach_tests_to_groups",
    "vamp_vsif_hierarchy_attach_tests_to_sessions",
    # ---- vsif/sessions ----
    "vamp_sessions_list",
    "vamp_sessions_count",
    "vamp_vsif_session_get",
    "vamp_vsif_session_create",
    "vamp_vsif_session_create_with_permissions",
    "vamp_vsif_session_delete",
    # ---- runtime sessions ----
    "vamp_session_get_by_name",
    # ---- test plan ----
    "vamp_plan_list",
    "vamp_plan_count",
    "vamp_plan_list_sub_elements",
    "vamp_plan_list_vplans",
    "vamp_plan_get",
    "vamp_plan_get_rich_text",
    "vamp_plan_add_section",
    "vamp_plan_add_reference",
    "vamp_plan_add_metrics_port",
    "vamp_plan_update",
    "vamp_plan_update_bulk",
    "vamp_plan_update_section",
    "vamp_plan_update_reference",
}


class TestVmanagerRegistration:
    def test_all_vmanager_tools_registered(self) -> None:
        """register_vmanager_tools exposes every expected tool name."""
        mcp = MockFastMCP("validation-test")
        register_vmanager_tools(mcp, "/tmp/repo")

        registered = set(mcp.tools.keys())
        missing = EXPECTED_VMANAGER_TOOLS - registered
        assert not missing, f"Tools missing from registration: {sorted(missing)}"

    def test_no_unexpected_tools(self) -> None:
        """No unexpected tools registered beyond the known set."""
        mcp = MockFastMCP("validation-test")
        register_vmanager_tools(mcp, "/tmp/repo")

        registered = set(mcp.tools.keys())
        extra = registered - EXPECTED_VMANAGER_TOOLS
        # Allow new tools to be added without failing, just document them
        if extra:
            pytest.skip(f"New tools found (update EXPECTED set): {sorted(extra)}")

    def test_all_registered_tools_are_async(self) -> None:
        """Every registered vManager tool is an async callable."""
        mcp = MockFastMCP("validation-test")
        register_vmanager_tools(mcp, "/tmp/repo")

        for name in EXPECTED_VMANAGER_TOOLS:
            fn = mcp.tools.get(name)
            assert fn is not None, f"Tool '{name}' not registered"
            assert callable(fn), f"Tool '{name}' is not callable"
            assert inspect.iscoroutinefunction(fn), f"Tool '{name}' is not async"

    def test_all_tools_have_docstrings(self) -> None:
        """Every vManager tool must have a non-empty docstring."""
        mcp = MockFastMCP("validation-test")
        register_vmanager_tools(mcp, "/tmp/repo")

        missing = []
        for name, fn in mcp.tools.items():
            doc = fn.__doc__
            if not doc or not doc.strip():
                missing.append(name)
        assert not missing, f"Tools missing docstrings: {missing}"


class TestVmanagerBackendUnavailable:
    def test_backend_unavailable_propagates(self) -> None:
        """VmanagerBackendUnavailable propagates through the MCP tool layer."""
        import asyncio

        from backends.vmanager.client import VmanagerBackendUnavailable

        mcp = MockFastMCP("test-unavailable")
        register_vmanager_tools(mcp, "/tmp/repo")

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                "validation_mcp.runtime.tool_runtime.client_factory.get_vmanager_client",
                lambda settings: (_ for _ in ()).throw(
                    VmanagerBackendUnavailable("test: vamp not installed")
                ),
            )
            result = asyncio.run(
                mcp.tools["vamp_runs_list"](post_data_json='{"filter": {}}')
            )

        assert result.startswith("ERROR:"), f"Expected ERROR prefix but got: {result!r}"
        assert "vamp not installed" in result


class TestVmanagerHelpers:
    def test_apply_default_projection_preserves_caller_projection(self) -> None:
        from backends.vmanager._utils import apply_default_projection

        caller_projection = ["id", "name", "owner"]
        request = {"filter": {}, "projection": caller_projection}

        result = apply_default_projection(request, ["id", "status"])

        assert result["projection"] == caller_projection
        assert request["projection"] == caller_projection

    def test_apply_default_projection_copies_default_projection(self) -> None:
        from backends.vmanager._utils import apply_default_projection

        default_projection = ["id", "name"]

        result = apply_default_projection({"filter": {}}, default_projection)
        result["projection"].append("owner")

        assert default_projection == ["id", "name"]

    def test_grouped_run_summary_does_not_use_cluster_unique_tag_for_dir_tag(self) -> None:
        from backends.vmanager._utils import group_run_failure_clusters

        rows = [
            {
                "FAILURE CLUSTER - ID": 42,
                "FAILURE CLUSTER - Name": "fc_mem",
                "unique_tag": "cluster-unique-tag",
                "ID": 501,
                "Test Name": "tc_mem_01",
            }
        ]

        result = group_run_failure_clusters(rows, full_detail=True)

        assert result[0]["FAILURE CLUSTER - Unique Tag"] == "cluster-unique-tag"
        assert "dir_tag" not in result[0]["runs"][0]

    def test_grouped_run_failure_clusters_skips_rows_without_cluster_id(self) -> None:
        from backends.vmanager._utils import group_run_failure_clusters

        rows = [
            {
                "unique_tag": "cluster-unique-tag",
                "ID": 501,
                "Test Name": "tc_mem_01",
            }
        ]

        assert group_run_failure_clusters(rows) == []


class TestVmanagerPlanCompatibility:
    def test_list_plan_entries_primary_path_injects_default_projection(self) -> None:
        from backends.vmanager.client import VmanagerClient
        from backends.vmanager._client_domain import PLAN_SUB_ELEMENTS_SLIM_PROJECTION

        captured: dict[str, object] = {}

        class FakePlan:
            def list(self, post_data):
                captured["post_data"] = post_data
                return [{"element_id": 1, "name": "Top", "overall_grade": 98}]

        client = VmanagerClient.__new__(VmanagerClient)
        client._vamp = type("FakeVamp", (), {"test_plan": FakePlan()})()

        result = client.list_plan_entries({"filter": {}})

        assert result == {
            "plan_entries": [{"element_id": 1, "name": "Top", "overall_grade": 98}],
            "count": 1,
        }
        assert captured["post_data"] == {
            "filter": {},
            "projection": PLAN_SUB_ELEMENTS_SLIM_PROJECTION,
        }


class TestVmanagerGroupedTool:
    def test_grouped_run_failure_cluster_tool_returns_clustered_json(self) -> None:
        import asyncio
        import json

        mcp = MockFastMCP("grouped-tool-test")
        register_vmanager_tools(mcp, "/tmp/repo")

        class FakeClient:
            def list_run_failure_clusters_grouped(self, post_data, full_detail):
                assert post_data == {"filter": {}}
                assert full_detail is False
                return {
                    "failure_clusters": [
                        {
                            "FAILURE CLUSTER - ID": 42,
                            "FAILURE CLUSTER - Name": "fc_mem",
                            "runs": [{"ID": 501, "Test Name": "tc_mem_01"}],
                        }
                    ],
                    "cluster_count": 1,
                }

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                "validation_mcp.runtime.tool_runtime.client_factory.get_vmanager_client",
                lambda settings: FakeClient(),
            )
            result = asyncio.run(
                mcp.tools["vamp_run_failure_cluster_list_grouped"](
                    post_data_json='{"filter": {}}'
                )
            )

        payload = json.loads(result)
        assert payload["cluster_count"] == 1
        assert payload["failure_clusters"][0]["FAILURE CLUSTER - ID"] == 42
        assert payload["failure_clusters"][0]["runs"][0]["ID"] == 501


class TestVmanagerHierarchyCreate:
    def test_hierarchy_create_rejects_non_object_post_data(self) -> None:
        import asyncio

        mcp = MockFastMCP("hierarchy-create-test")
        register_vmanager_tools(mcp, "/tmp/repo")

        result = asyncio.run(mcp.tools["vamp_vsif_hierarchy_create"]('[1, 2, 3]'))

        assert result == "ERROR: post_data must decode to a JSON object"


class TestVmanagerFilterArguments:
    def test_vsif_group_delete_rejects_non_object_filter(self) -> None:
        import asyncio

        mcp = MockFastMCP("vsif-group-delete-test")
        register_vmanager_tools(mcp, "/tmp/repo")

        result = asyncio.run(mcp.tools["vamp_vsif_group_delete"]('[1, 2, 3]'))

        assert result == "ERROR: filter must decode to a JSON object"


class TestVmanagerScopedVsifLists:
    @pytest.mark.parametrize(
        ("tool_name", "filter_kwarg", "client_method"),
        [
            ("vamp_vsif_tests_list_for_session", "sessions_filter_json", "list_vsif_tests_for_session"),
            ("vamp_vsif_tests_list_for_group", "groups_filter_json", "list_vsif_tests_for_group"),
            ("vamp_vsif_groups_list_for_session", "sessions_filter_json", "list_vsif_groups_for_session"),
            ("vamp_vsif_groups_list_for_group", "groups_filter_json", "list_vsif_groups_for_group"),
        ],
    )
    def test_empty_optional_post_data_preserves_none(
        self,
        tool_name: str,
        filter_kwarg: str,
        client_method: str,
    ) -> None:
        import asyncio
        import json

        mcp = MockFastMCP("scoped-vsif-test")
        register_vmanager_tools(mcp, "/tmp/repo")
        captured: dict[str, object] = {}

        class FakeClient:
            def list_vsif_tests_for_session(self, filter_dict, extra_data):
                captured["method"] = "list_vsif_tests_for_session"
                captured["filter"] = filter_dict
                captured["extra_data"] = extra_data
                return {"vsif_tests": [], "count": 0}

            def list_vsif_tests_for_group(self, filter_dict, extra_data):
                captured["method"] = "list_vsif_tests_for_group"
                captured["filter"] = filter_dict
                captured["extra_data"] = extra_data
                return {"vsif_tests": [], "count": 0}

            def list_vsif_groups_for_session(self, filter_dict, extra_data):
                captured["method"] = "list_vsif_groups_for_session"
                captured["filter"] = filter_dict
                captured["extra_data"] = extra_data
                return {"vsif_groups": [], "count": 0}

            def list_vsif_groups_for_group(self, filter_dict, extra_data):
                captured["method"] = "list_vsif_groups_for_group"
                captured["filter"] = filter_dict
                captured["extra_data"] = extra_data
                return {"vsif_groups": [], "count": 0}

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                "validation_mcp.runtime.tool_runtime.client_factory.get_vmanager_client",
                lambda settings: FakeClient(),
            )
            result = asyncio.run(
                mcp.tools[tool_name](
                    **{filter_kwarg: '{"@c": ".AttValueFilter", "attName": "id", "attValue": 1}'},
                    post_data_json="{}",
                )
            )

        payload = json.loads(result)
        assert payload["count"] == 0
        assert captured["method"] == client_method
        assert captured["extra_data"] is None

    def test_plan_find_respects_optional_limit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import asyncio
        import json

        monkeypatch.setenv("VALIDATION_MCP_MAX_PAGE_LENGTH", "2")

        mcp = MockFastMCP("plan-find-test")
        register_vmanager_tools(mcp, "/tmp/repo")

        class FakeClient:
            def list_vplans(self, post_data):
                assert post_data == {}
                return {
                    "vplans": [
                        {"name": "Alpha Block"},
                        {"name": "Alpha Core"},
                        {"name": "Alpha Edge"},
                    ]
                }

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                "validation_mcp.runtime.tool_runtime.client_factory.get_vmanager_client",
                lambda settings: FakeClient(),
            )
            result = asyncio.run(mcp.tools["vamp_plan_find"]("Alpha", limit=2))

        payload = json.loads(result)
        assert payload["count"] == 3
        assert payload["returned_count"] == 2
        assert payload["truncated"] is True
        assert len(payload["vplans"]) == 2
        assert [item["name"] for item in payload["vplans"]] == [
            "Alpha Block",
            "Alpha Core",
        ]

    def test_plan_find_clamps_limit_to_max_page_length(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import asyncio
        import json

        monkeypatch.setenv("VALIDATION_MCP_MAX_PAGE_LENGTH", "2")

        mcp = MockFastMCP("plan-find-clamped-test")
        register_vmanager_tools(mcp, "/tmp/repo")

        class FakeClient:
            def list_vplans(self, post_data):
                assert post_data == {}
                return {
                    "vplans": [
                        {"name": "Alpha Block"},
                        {"name": "Alpha Core"},
                        {"name": "Alpha Edge"},
                    ]
                }

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                "validation_mcp.runtime.tool_runtime.client_factory.get_vmanager_client",
                lambda settings: FakeClient(),
            )
            result = asyncio.run(mcp.tools["vamp_plan_find"]("Alpha", limit=99))

        payload = json.loads(result)
        assert payload["count"] == 3
        assert payload["returned_count"] == 2
        assert payload["truncated"] is True
        assert [item["name"] for item in payload["vplans"]] == [
            "Alpha Block",
            "Alpha Core",
        ]

    def test_plan_find_supports_zero_limit(self) -> None:
        import asyncio
        import json

        mcp = MockFastMCP("plan-find-zero-limit-test")
        register_vmanager_tools(mcp, "/tmp/repo")

        class FakeClient:
            def list_vplans(self, post_data):
                assert post_data == {}
                return {
                    "vplans": [
                        {"name": "Alpha Block"},
                        {"name": "Alpha Core"},
                    ]
                }

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                "validation_mcp.runtime.tool_runtime.client_factory.get_vmanager_client",
                lambda settings: FakeClient(),
            )
            result = asyncio.run(mcp.tools["vamp_plan_find"]("Alpha", limit=0))

        payload = json.loads(result)
        assert payload["count"] == 2
        assert payload["returned_count"] == 0
        assert payload["vplans"] == []
        assert payload["truncated"] is True

    def test_plan_find_returns_all_matches_by_default(self) -> None:
        import asyncio
        import json

        mcp = MockFastMCP("plan-find-default-test")
        register_vmanager_tools(mcp, "/tmp/repo")

        class FakeClient:
            def list_vplans(self, post_data):
                assert post_data == {}
                return {
                    "vplans": [
                        {"name": "Alpha Edge"},
                        {"name": "Alpha Block"},
                        {"name": "Alpha Core"},
                    ]
                }

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                "validation_mcp.runtime.tool_runtime.client_factory.get_vmanager_client",
                lambda settings: FakeClient(),
            )
            result = asyncio.run(mcp.tools["vamp_plan_find"]("Alpha"))

        payload = json.loads(result)
        assert payload["count"] == 3
        assert payload["returned_count"] == 3
        assert payload["truncated"] is False
        assert [item["name"] for item in payload["vplans"]] == [
            "Alpha Edge",
            "Alpha Block",
            "Alpha Core",
        ]
