"""Tests for the optional vManager backend client and MCP tool."""

from __future__ import annotations

import asyncio
import json

import pytest

from backends.vmanager.client import (
    VmanagerClient,
    _extract_rows,
    classify_team_name,
    derive_dut_from_team_name,
)
from tools.vmanager import register_vmanager_tools
from conftest import MockFastMCP


class FakeTestRunData:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.requests: list[dict] = []

    def list(self, post_data: dict):
        self.requests.append(post_data)
        if not self.responses:
            raise AssertionError("No fake responses left for test_run.list")
        return self.responses.pop(0)

    def count(self, post_data: dict):
        self.requests.append(post_data)
        return self._count_response


class FakeFailureClusterData:
    def __init__(self, list_response=None, count_response=None) -> None:
        self._list_response = list_response
        self._count_response = count_response
        self.requests: list[dict] = []

    def list(self, post_data: dict):
        self.requests.append(post_data)
        return self._list_response

    def count(self, post_data: dict):
        self.requests.append(post_data)
        return self._count_response


class FakeVsifSessions:
    def __init__(self, list_response=None, count_response=None) -> None:
        self._list_response = list_response
        self._count_response = count_response
        self.requests: list[dict] = []

    def list(self, post_data: dict):
        self.requests.append(post_data)
        return self._list_response

    def count(self, post_data: dict):
        self.requests.append(post_data)
        return self._count_response


class FakeTestPlan:
    def __init__(self, list_response=None, count_response=None) -> None:
        self._list_response = list_response
        self._count_response = count_response
        self.requests: list[dict] = []

    def list(self, post_data: dict):
        self.requests.append(post_data)
        return self._list_response

    def count(self, post_data: dict):
        self.requests.append(post_data)
        return self._count_response


class FakeVamp:
    def __init__(
        self,
        responses: list[object],
        *,
        failure_cluster=None,
        run_count=None,
        vsif_sessions=None,
        test_plan=None,
    ) -> None:
        fake_run = FakeTestRunData(responses)
        fake_run._count_response = run_count
        self.test_run = fake_run
        self.failure_cluster = failure_cluster or FakeFailureClusterData()
        self.vsif_hierarchy = object()
        self.vsif_sessions = vsif_sessions if vsif_sessions is not None else FakeVsifSessions()
        self.test_plan = test_plan if test_plan is not None else FakeTestPlan()
        self.vapi_requests = type("Req", (), {"api_base_path": "https://example.test/nvl", "username": "tester"})()


class TestVmanagerClient:
    def test_classify_team_name(self) -> None:
        assert classify_team_name("hub.memss") == "hub"
        assert classify_team_name("hub.memss.hub") == "hub"
        assert classify_team_name("hub.vpuss") == "hub"
        assert classify_team_name("iu.sncu") == "iu"
        assert classify_team_name("ip.mc") == "ip"

    def test_derive_dut_from_team_name(self) -> None:
        assert derive_dut_from_team_name("ip.mc") == "mc"
        assert derive_dut_from_team_name("iu.sncu") == "sncu"
        assert derive_dut_from_team_name("hub.memss") == "memss"
        assert derive_dut_from_team_name("hub.memss.hub") == "memss"
        assert derive_dut_from_team_name("hub.vpuss") == "vpuss"

    def test_query_standard_runs_emits_standard_request(self) -> None:
        fake_vamp = FakeVamp([[{"id": 1234, "status": "failed"}]])
        client = VmanagerClient(repo_root="/nfs/site/disks/example/ttl/project", vamp_factory=lambda: fake_vamp)

        actual = client.query_standard_runs(
            team="hub.ipuss",
            steppings="ttl-a0",
        )

        assert actual["team_profile"]["dut_was_derived"] is True
        assert actual["team_profile"]["dut_values"] == ["ipuss"]
        assert actual["runs"] == [{"id": 1234, "status": "failed"}]
        request = fake_vamp.test_run.requests[0]
        assert request["filter"]["condition"] == "AND"
        assert [item["attName"] for item in request["filter"]["chain"]] == [
            "status",
            "i_team",
            "i_debug_status",
            "i_dut",
            "i_steps",
            "i_for_indicators",
        ]

    def test_query_standard_runs_uses_explicit_dut_when_provided(self) -> None:
        fake_vamp = FakeVamp([[{"id": 7, "status": "failed"}]])
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        actual = client.query_standard_runs(
            team="hub.memss.hub",
            steppings="ttl-a0",
            dut="hubs",
        )

        assert actual["team_profile"]["dut_was_derived"] is False
        assert actual["team_profile"]["dut_values"] == ["hubs"]

    def test_query_standard_runs_defaults_hub_team_to_subsystem_dut(self) -> None:
        fake_vamp = FakeVamp([[{"id": 8, "status": "failed"}]])
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        actual = client.query_standard_runs(
            team="hub.memss.hub",
            steppings="ttl-a0",
        )

        assert actual["team_profile"]["dut_was_derived"] is True
        assert actual["team_profile"]["dut_values"] == ["memss"]

    def test_query_standard_runs_skip_steppings_omits_i_steps(self) -> None:
        fake_vamp = FakeVamp([[{"id": 9, "status": "failed"}]])
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        actual = client.query_standard_runs(
            team="hub.memss",
            steppings="unknown-step",
            dut="memss",
            skip_steppings=True,
        )

        assert actual["team_profile"]["skip_steppings"] is True
        request = fake_vamp.test_run.requests[0]
        att_names = [item["attName"] for item in request["filter"]["chain"]]
        assert "i_steps" not in att_names

    def test_query_standard_runs_error_includes_request_body(self) -> None:
        class BoomTestRun:
            def list(self, post_data):
                raise RuntimeError("400 Bad Request")

        class BoomVamp:
            test_run = BoomTestRun()

        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: BoomVamp())

        with pytest.raises(RuntimeError) as exc_info:
            client.query_standard_runs(team="hub.memss", steppings="bad-step", dut="memss")

        assert "[ddgmcp] Request body sent:" in str(exc_info.value)
        assert "i_steps" in str(exc_info.value)


class TestRegisterVmanagerTools:
    def test_standard_runs_tool_returns_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root: str) -> None:
                assert repo_root == "/tmp/repo"

            def query_standard_runs(self, **kwargs):
                assert kwargs["team"] == ("hub.ipuss",)
                assert kwargs["steppings"] == ("ttl-a0",)
                assert kwargs["dut"] is None
                assert kwargs["skip_steppings"] is False
                return {"runs": [{"id": 7}], "team_profile": {"dut_was_derived": True}, "request": {"pageLength": 25}}

        monkeypatch.setattr("tools.vmanager._runs.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_standard_runs_list"](
                team="hub.ipuss",
                steppings="ttl-a0",
                page_length=25,
            )
        )
        payload = json.loads(result)
        assert payload["runs"] == [{"id": 7}]
        assert payload["request"]["pageLength"] == 25

    def test_standard_runs_tool_skip_steppings_passes_through(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root: str) -> None:
                pass

            def query_standard_runs(self, **kwargs):
                assert kwargs["skip_steppings"] is True
                return {"runs": [], "team_profile": {}, "request": {}}

        monkeypatch.setattr("tools.vmanager._runs.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_standard_runs_list"](
                team="hub.memss",
                steppings="any-value",
                dut="memss",
                skip_steppings=True,
            )
        )
        assert "ERROR" not in result
        assert json.loads(result)["runs"] == []

    def test_standard_runs_tool_surfaces_validation_errors(self) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_standard_runs_list"](
                team="",
                steppings="ttl-a0",
            )
        )
        assert result.startswith("ERROR:")


class TestVmanagerClientNewMethods:
    def test_list_failure_clusters_normalizes_list_response(self) -> None:
        fake_fc = FakeFailureClusterData(
            list_response=[{"id": 1, "name": "bucket_a"}, {"id": 2, "name": "bucket_b"}]
        )
        fake_vamp = FakeVamp([], failure_cluster=fake_fc)
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)
        rs = {"filter": {"c_type": ".AttValueFilter", "attName": "owner", "attValue": "me", "operand": "EQUALS"}}

        result = client.list_failure_clusters(rs)

        assert result["count"] == 2
        assert result["failure_clusters"] == [{"id": 1, "name": "bucket_a"}, {"id": 2, "name": "bucket_b"}]
        assert fake_fc.requests[0] == rs

    def test_count_failure_clusters_returns_count_dict(self) -> None:
        fake_fc = FakeFailureClusterData(count_response=42)
        fake_vamp = FakeVamp([], failure_cluster=fake_fc)
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)
        rs = {"filter": {}}

        result = client.count_failure_clusters(rs)

        assert result == {"count": 42}
        assert fake_fc.requests[0] == rs

    def test_count_failure_clusters_handles_none_response(self) -> None:
        fake_fc = FakeFailureClusterData(count_response=None)
        fake_vamp = FakeVamp([], failure_cluster=fake_fc)
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.count_failure_clusters({"filter": {}})

        assert result == {"count": None}

    def test_count_runs_returns_count_dict(self) -> None:
        fake_vamp = FakeVamp([], run_count=17)
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)
        rs = {"filter": {}}

        result = client.count_runs(rs)

        assert result == {"count": 17}
        assert fake_vamp.test_run.requests[0] == rs

    def test_new_properties_delegate_to_vamp(self) -> None:
        fake_vamp = FakeVamp([])
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        assert client.failure_cluster is fake_vamp.failure_cluster
        assert client.vsif_hierarchy is fake_vamp.vsif_hierarchy
        assert client.vsif_sessions is fake_vamp.vsif_sessions
        assert client.test_plan is fake_vamp.test_plan


class TestNewVmanagerTools:
    def test_failure_cluster_list_returns_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root: str) -> None:
                pass

            def list_failure_clusters(self, post_data: dict):
                return {"failure_clusters": [{"id": 9, "name": "foo"}], "count": 1}

        monkeypatch.setattr("tools.vmanager._failure_clusters.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_failure_cluster_list"](
                post_data_json='{"filter": {}}'
            )
        )
        payload = json.loads(result)
        assert payload["count"] == 1
        assert payload["failure_clusters"][0]["id"] == 9

    def test_failure_cluster_list_rejects_bad_json(self) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_failure_cluster_list"](post_data_json="not-json")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_failure_cluster_count_returns_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root: str) -> None:
                pass

            def count_failure_clusters(self, post_data: dict):
                return {"count": 7}

        monkeypatch.setattr("tools.vmanager._failure_clusters.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_failure_cluster_count"](
                post_data_json='{"filter": {}}'
            )
        )
        assert json.loads(result) == {"count": 7}

    def test_failure_cluster_count_rejects_bad_json(self) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_failure_cluster_count"](post_data_json="{bad}")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_runs_count_returns_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root: str) -> None:
                pass

            def count_runs(self, post_data: dict):
                return {"count": 33}

        monkeypatch.setattr("tools.vmanager._runs.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_runs_count"](post_data_json='{"filter": {}}')
        )
        assert json.loads(result) == {"count": 33}

    def test_runs_count_rejects_bad_json(self) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_runs_count"](post_data_json="[]not-json")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_runs_list_returns_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root: str) -> None:
                pass

            def list_runs(self, post_data: dict):
                return {"runs": [{"id": 5, "status": "failed"}], "count": 1}

        monkeypatch.setattr("tools.vmanager._runs.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_runs_list"](post_data_json='{"filter": {}}')
        )
        payload = json.loads(result)
        assert payload["count"] == 1
        assert payload["runs"][0]["id"] == 5

    def test_runs_list_rejects_bad_json(self) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_runs_list"](post_data_json="{invalid")
        )
        assert result.startswith("ERROR: invalid JSON")


class TestExtractRows:
    def test_none_payload_returns_empty(self) -> None:
        from backends.vmanager.client import _extract_rows

        assert _extract_rows(None) == []

    def test_list_key_none_returns_empty(self) -> None:
        from backends.vmanager.client import _extract_rows

        assert _extract_rows({"list": None}) == []

    def test_items_key_none_returns_empty(self) -> None:
        from backends.vmanager.client import _extract_rows

        assert _extract_rows({"items": None}) == []

    def test_data_key_none_returns_empty(self) -> None:
        from backends.vmanager.client import _extract_rows

        assert _extract_rows({"data": None}) == []

    def test_plain_dict_without_candidate_key_is_wrapped(self) -> None:
        from backends.vmanager.client import _extract_rows

        assert _extract_rows({"id": 1, "status": "passed"}) == [{"id": 1, "status": "passed"}]

    def test_empty_list_payload_returns_empty(self) -> None:
        from backends.vmanager.client import _extract_rows

        assert _extract_rows([]) == []

    def test_list_key_with_empty_list_returns_empty(self) -> None:
        from backends.vmanager.client import _extract_rows

        assert _extract_rows({"list": []}) == []

    def test_list_key_with_rows_returns_rows(self) -> None:
        from backends.vmanager.client import _extract_rows

        rows = [{"id": 1}, {"id": 2}]
        assert _extract_rows({"list": rows}) == rows


class TestVmanagerClientListRuns:
    def test_list_runs_normalizes_list_response(self) -> None:
        fake_vamp = FakeVamp([[{"id": 10, "status": "passed"}]])
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)
        rs = {"filter": {"c_type": ".AttValueFilter", "attName": "status", "attValue": "passed", "operand": "EQUALS"}}

        result = client.list_runs(rs)

        assert result["count"] == 1
        assert result["runs"] == [{"id": 10, "status": "passed"}]
        assert fake_vamp.test_run.requests[0] == rs

    def test_list_runs_returns_empty_on_empty_response(self) -> None:
        fake_vamp = FakeVamp([[]])
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.list_runs({"filter": {}})

        assert result == {"runs": [], "count": 0}

    def test_list_runs_handles_none_list_key_in_response(self) -> None:
        fake_vamp = FakeVamp([{"list": None}])
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.list_runs({"filter": {}})

        assert result == {"runs": [], "count": 0}


# ---------------------------------------------------------------------------
# Tests for get_run / get_failure_cluster
# ---------------------------------------------------------------------------


class TestVmanagerClientGetMethods:
    def test_get_run_returns_matching_row(self) -> None:
        fake_vamp = FakeVamp([[{"id": 42, "status": "failed"}]])
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.get_run(42)

        assert result == {"id": 42, "status": "failed"}
        sent = fake_vamp.test_run.requests[0]
        assert sent["filter"]["attName"] == "id"
        assert sent["filter"]["attValue"] == 42
        assert sent["filter"]["operand"] == "EQUALS"

    def test_get_run_returns_empty_when_not_found(self) -> None:
        fake_vamp = FakeVamp([[]])
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.get_run(999)

        assert result == {}

    def test_get_run_normalizes_list_key_response(self) -> None:
        fake_vamp = FakeVamp([{"list": [{"id": 7, "status": "passed"}]}])
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.get_run(7)

        assert result == {"id": 7, "status": "passed"}

    def test_get_failure_cluster_returns_matching_row(self) -> None:
        fake_fc = FakeFailureClusterData(list_response=[{"id": 101, "name": "bucket_x"}])
        fake_vamp = FakeVamp([], failure_cluster=fake_fc)
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.get_failure_cluster(101)

        assert result == {"id": 101, "name": "bucket_x"}
        sent = fake_fc.requests[0]
        assert sent["filter"]["attName"] == "id"
        assert sent["filter"]["attValue"] == 101

    def test_get_failure_cluster_returns_empty_when_not_found(self) -> None:
        fake_fc = FakeFailureClusterData(list_response=[])
        fake_vamp = FakeVamp([], failure_cluster=fake_fc)
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.get_failure_cluster(9999)

        assert result == {}


# ---------------------------------------------------------------------------
# Tests for list_sessions / count_sessions / list_plan_entries / count_plan_entries
# ---------------------------------------------------------------------------


class TestVmanagerClientVsifPlanMethods:
    def test_list_sessions_normalizes_list_response(self) -> None:
        sessions = [{"id": 1001, "name": "weekly_a0"}, {"id": 1002, "name": "weekly_b0"}]
        fake_vsif = FakeVsifSessions(list_response=sessions)
        fake_vamp = FakeVamp([], vsif_sessions=fake_vsif)
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)
        rs = {"filter": {"c_type": ".AttValueFilter", "attName": "name", "attValue": "weekly%", "operand": "CONTAINS"}}

        result = client.list_sessions(rs)

        assert result == {"sessions": sessions, "count": 2}
        assert fake_vsif.requests[0] == rs

    def test_list_sessions_returns_empty_on_none_response(self) -> None:
        fake_vsif = FakeVsifSessions(list_response=None)
        fake_vamp = FakeVamp([], vsif_sessions=fake_vsif)
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.list_sessions({"filter": {}})

        assert result == {"sessions": [], "count": 0}

    def test_count_sessions_returns_count_dict(self) -> None:
        fake_vsif = FakeVsifSessions(count_response=5)
        fake_vamp = FakeVamp([], vsif_sessions=fake_vsif)
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.count_sessions({"filter": {}})

        assert result == {"count": 5}

    def test_count_sessions_handles_none_response(self) -> None:
        fake_vsif = FakeVsifSessions(count_response=None)
        fake_vamp = FakeVamp([], vsif_sessions=fake_vsif)
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.count_sessions({"filter": {}})

        assert result == {"count": None}

    def test_list_plan_entries_normalizes_list_response(self) -> None:
        entries = [{"id": 2001, "name": "TC_boot"}, {"id": 2002, "name": "TC_init"}]
        fake_plan = FakeTestPlan(list_response=entries)
        fake_vamp = FakeVamp([], test_plan=fake_plan)
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)
        rs = {"filter": {}}

        result = client.list_plan_entries(rs)

        assert result == {"plan_entries": entries, "count": 2}
        assert fake_plan.requests[0] == rs

    def test_list_plan_entries_returns_empty_on_none_response(self) -> None:
        fake_plan = FakeTestPlan(list_response=None)
        fake_vamp = FakeVamp([], test_plan=fake_plan)
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.list_plan_entries({"filter": {}})

        assert result == {"plan_entries": [], "count": 0}

    def test_list_plan_entries_falls_back_to_list_sub_elements(self) -> None:
        class FallbackPlan:
            def __init__(self) -> None:
                self.requests: list[dict] = []

            def list_sub_elements(self, post_data=None, **kwargs):
                self.requests.append(post_data)
                return [{"id": 2001, "name": "TC_boot"}]

        fake_plan = FallbackPlan()
        fake_vamp = FakeVamp([], test_plan=fake_plan)
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)
        rs = {"sticky-context": {"vplan": "demo", "db-vplan": True}}

        result = client.list_plan_entries(rs)

        assert result == {"plan_entries": [{"id": 2001, "name": "TC_boot"}], "count": 1}
        assert fake_plan.requests[0] == rs

    def test_count_plan_entries_returns_count_dict(self) -> None:
        fake_plan = FakeTestPlan(count_response=12)
        fake_vamp = FakeVamp([], test_plan=fake_plan)
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.count_plan_entries({"filter": {}})

        assert result == {"count": 12}

    def test_count_plan_entries_handles_none_response(self) -> None:
        fake_plan = FakeTestPlan(count_response=None)
        fake_vamp = FakeVamp([], test_plan=fake_plan)
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.count_plan_entries({"filter": {}})

        assert result == {"count": 0}

    def test_count_plan_entries_falls_back_to_list_sub_elements(self) -> None:
        class FallbackPlan:
            def list_sub_elements(self, post_data=None, **kwargs):
                return [{"id": 1}, {"id": 2}, {"id": 3}]

        fake_vamp = FakeVamp([], test_plan=FallbackPlan())
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.count_plan_entries(
            {"sticky-context": {"vplan": "demo", "db-vplan": True}}
        )

        assert result == {"count": 3}


# ---------------------------------------------------------------------------
# Tests for query_standard_runs normalization fix
# ---------------------------------------------------------------------------


class TestQueryStandardRunsNormalization:
    def test_normalizes_dict_response_with_list_key(self) -> None:
        """Backend returning {"list": [...]} is unwrapped correctly."""
        fake_vamp = FakeVamp([{"list": [{"id": 55, "status": "failed"}]}])
        client = VmanagerClient(repo_root="/nfs/site/disks/example/nvl/project", vamp_factory=lambda: fake_vamp)

        result = client.query_standard_runs(team="hub.memss", steppings="nvl-a0")

        assert result["runs"] == [{"id": 55, "status": "failed"}]
        assert result["count"] == 1

    def test_returns_count_field(self) -> None:
        fake_vamp = FakeVamp([[{"id": 1}, {"id": 2}]])
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.query_standard_runs(team="hub.memss", steppings="nvl-a0")

        assert result["count"] == 2
        assert len(result["runs"]) == 2

    def test_empty_response_gives_empty_count(self) -> None:
        fake_vamp = FakeVamp([[]])
        client = VmanagerClient(repo_root="/tmp/repo", vamp_factory=lambda: fake_vamp)

        result = client.query_standard_runs(team="hub.memss", steppings="nvl-a0")

        assert result["runs"] == []
        assert result["count"] == 0


# ---------------------------------------------------------------------------
# MCP tool tests for the 6 new tools
# ---------------------------------------------------------------------------


class TestNewVmanagerToolsRound2:
    def test_run_get_returns_json_for_found_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root: str) -> None:
                pass

            def get_run(self, run_id: int):
                assert run_id == 42
                return {"id": 42, "status": "failed", "name": "test_boot_sd1234"}

        monkeypatch.setattr("tools.vmanager._runs.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_run_get"](run_id=42))
        payload = json.loads(result)
        assert payload["id"] == 42
        assert payload["status"] == "failed"

    def test_run_get_returns_empty_json_when_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root: str) -> None:
                pass

            def get_run(self, run_id: int):
                return {}

        monkeypatch.setattr("tools.vmanager._runs.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_run_get"](run_id=9999))
        assert json.loads(result) == {}

    def test_failure_cluster_get_returns_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root: str) -> None:
                pass

            def get_failure_cluster(self, cluster_id: int):
                assert cluster_id == 101
                return {"id": 101, "name": "bucket_alpha", "owner": "jsmith"}

        monkeypatch.setattr("tools.vmanager._failure_clusters.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_failure_cluster_get"](cluster_id=101))
        payload = json.loads(result)
        assert payload["id"] == 101
        assert payload["name"] == "bucket_alpha"

    def test_failure_cluster_get_returns_empty_when_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root: str) -> None:
                pass

            def get_failure_cluster(self, cluster_id: int):
                return {}

        monkeypatch.setattr("tools.vmanager._failure_clusters.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_failure_cluster_get"](cluster_id=9999))
        assert json.loads(result) == {}

    def test_sessions_list_returns_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root: str) -> None:
                pass

            def list_sessions(self, post_data: dict):
                return {"sessions": [{"id": 1001, "name": "weekly_a0"}], "count": 1}

        monkeypatch.setattr("tools.vmanager._vsif_sessions.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_sessions_list"](post_data_json='{"filter": {}}'))
        payload = json.loads(result)
        assert payload["count"] == 1
        assert payload["sessions"][0]["name"] == "weekly_a0"

    def test_sessions_list_rejects_bad_json(self) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(mock_mcp.tools["vamp_sessions_list"](post_data_json="{bad"))
        assert result.startswith("ERROR: invalid JSON")

    def test_sessions_count_returns_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root: str) -> None:
                pass

            def count_sessions(self, post_data: dict):
                return {"count": 8}

        monkeypatch.setattr("tools.vmanager._vsif_sessions.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_sessions_count"](post_data_json='{"filter": {}}'))
        assert json.loads(result) == {"count": 8}

    def test_sessions_count_rejects_bad_json(self) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(mock_mcp.tools["vamp_sessions_count"](post_data_json="not-json"))
        assert result.startswith("ERROR: invalid JSON")

    def test_plan_list_returns_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root: str) -> None:
                pass

            def list_plan_entries(self, post_data: dict):
                return {
                    "plan_entries": [
                        {"id": 2001, "name": "TC_boot", "vplan_element_kind": "TC"},
                        {"id": 2002, "name": "TC_init", "vplan_element_kind": "TC"},
                    ],
                    "count": 2,
                }

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_plan_list"](post_data_json='{"filter": {}}'))
        payload = json.loads(result)
        assert payload["count"] == 2
        assert payload["plan_entries"][0]["name"] == "TC_boot"

    def test_plan_list_rejects_bad_json(self) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(mock_mcp.tools["vamp_plan_list"](post_data_json="[bad"))
        assert result.startswith("ERROR: invalid JSON")

    def test_plan_count_returns_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root: str) -> None:
                pass

            def count_plan_entries(self, post_data: dict):
                return {"count": 47}

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_plan_count"](post_data_json='{"filter": {}}'))
        assert json.loads(result) == {"count": 47}

    def test_plan_count_rejects_bad_json(self) -> None:
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(mock_mcp.tools["vamp_plan_count"](post_data_json="{not-json"))
        assert result.startswith("ERROR: invalid JSON")
