"""Tests for the expanded vManager tools and client methods (new surface in this PR).

Covers every new tool registered by the new submodules and every new client
method, using fake/dummy payloads — no live vManager access required.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from backends.vmanager.client import VmanagerClient
from tools.vmanager import register_vmanager_tools

# Pull in the shared MockFastMCP for tool-registration tests.
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from conftest import MockFastMCP  # noqa: E402


# ---------------------------------------------------------------------------
# Fake data-class objects for new client properties
# ---------------------------------------------------------------------------


class FakeVsifConfig:
    def __init__(self, list_return=None, update_return="OK"):
        self._list_return = list_return or []
        self._update_return = update_return

    def list(self, post_data):
        return self._list_return

    def update(self, post_data):
        return self._update_return


class FakeVsifGroups:
    def __init__(self, get_return=None, list_return=None, create_return=None, update_return="OK", delete_return=5):
        self._get_return = get_return or {}
        self._list_return = list_return if list_return is not None else []
        self._create_return = create_return
        self._update_return = update_return
        self._delete_return = delete_return
        self.last_filter = None

    def get(self, group_id):
        return self._get_return

    def list(self, data):
        return self._list_return

    def create(self, data):
        return self._create_return

    def update(self, data):
        return self._update_return

    def delete(self, filter_obj):
        self.last_filter = filter_obj.get()
        return self._delete_return


class FakeVsifTests:
    def __init__(self, get_return=None, list_return=None, create_return=None, update_return="OK", delete_return=3):
        self._get_return = get_return or {}
        self._list_return = list_return if list_return is not None else []
        self._create_return = create_return
        self._update_return = update_return
        self._delete_return = delete_return
        self.last_filter = None

    def get(self, test_id):
        return self._get_return

    def list(self, data):
        return self._list_return

    def create(self, data):
        return self._create_return

    def update(self, data):
        return self._update_return

    def delete(self, filter_obj):
        self.last_filter = filter_obj.get()
        return self._delete_return


class FakeVsifHierarchy:
    def __init__(self, get_return=None, list_return=None, create_return=None):
        self._get_return = get_return or {}
        self._list_return = list_return if list_return is not None else []
        self._create_return = create_return
        self.attach_calls = []

    def get(self, hierarchy_id):
        return self._get_return

    def list(self, parent_id, page_length=100, page_offset=0):
        return self._list_return

    def create(self, data):
        return self._create_return

    def attach_groups_to_groups(self, hc_id, child_filter, parent_filter):
        self.attach_calls.append(("g2g", hc_id, child_filter.get(), parent_filter.get()))

    def attach_groups_to_sessions(self, hc_id, groups_filter, sessions_filter):
        self.attach_calls.append(("g2s", hc_id, groups_filter.get(), sessions_filter.get()))

    def attach_tests_to_groups(self, hc_id, tests_filter, groups_filter):
        self.attach_calls.append(("t2g", hc_id, tests_filter.get(), groups_filter.get()))

    def attach_tests_to_sessions(self, hc_id, tests_filter, sessions_filter):
        self.attach_calls.append(("t2s", hc_id, tests_filter.get(), sessions_filter.get()))


class FakeVsifSessionsExt:
    """Supports get/create/create_with_permissions/delete beyond list/count."""
    def __init__(
        self,
        get_return=None,
        list_return=None,
        count_return=None,
        create_return=1,
        create_with_perm_return=42,
        delete_return=1,
    ):
        self._get_return = get_return or {}
        self._list_return = list_return if list_return is not None else []
        self._count_return = count_return
        self._create_return = create_return
        self._create_with_perm_return = create_with_perm_return
        self._delete_return = delete_return
        self.last_filter = None

    def get(self, session_id):
        return self._get_return

    def list(self, data):
        return self._list_return

    def count(self, data):
        return self._count_return

    def create(self, session_data):
        return self._create_return

    def create_with_permissions(self, session_data, permissions=None):
        return self._create_with_perm_return

    def delete(self, filter_obj):
        self.last_filter = filter_obj.get()
        return self._delete_return


class FakeSessionData:
    def __init__(self, session_result=None):
        self._session_result = session_result

    def get_session_from_name(self, name):
        return self._session_result


class _FakeSessionResult:
    def __init__(self, session_id, name, config):
        self.id = session_id
        self.name = name
        self.config = config


class FakeRunFailureClusterData:
    """Fake with direct vapi_requests to allow raw-response bypass."""

    def __init__(self, raw_response=None, update_result=None):
        self._raw = raw_response if raw_response is not None else []
        self._update_result = update_result
        self.vapi_requests = _FakeVapiRequests(self._raw)
        self.last_update_data = None

    def _response_json(self, response, default=None):
        return response if response is not None else default

    def update_associated(self, post_data):
        self.last_update_data = post_data
        return self._update_result


class _FakeVapiRequests:
    def __init__(self, response):
        self._response = response

    def post(self, endpoint, data):
        return self._response


class FakeTestRunExt:
    """Extended fake for new run methods (update/associate/dissociate/schemes/total/logs)."""

    def __init__(
        self,
        responses=None,
        update_return="updated",
        assoc_return=None,
        dissoc_return=None,
        schemes_return=None,
        total_count_return=None,
        extract_logs_return=None,
    ):
        self._responses = list(responses or [])
        self._update_return = update_return
        self._assoc_return = assoc_return if assoc_return is not None else []
        self._dissoc_return = dissoc_return if dissoc_return is not None else []
        self._schemes_return = schemes_return if schemes_return is not None else []
        self._total_count_return = total_count_return if total_count_return is not None else {}
        self._extract_logs_return = extract_logs_return
        self.requests = []

    def list(self, post_data):
        self.requests.append(post_data)
        if not self._responses:
            return []
        return self._responses.pop(0)

    def count(self, post_data):
        return None

    def update(self, post_data):
        return self._update_return

    def associate_to_failure_cluster(self, post_data):
        return self._assoc_return

    def dissociate_from_failure_cluster(self, post_data):
        return self._dissoc_return

    def get_rerun_schemes(self):
        return self._schemes_return

    def get_total_count_size(self):
        return self._total_count_return

    def extract_logs(self, request_id, index, offset, length):
        self.requests.append(
            {
                "request_id": request_id,
                "index": index,
                "offset": offset,
                "length": length,
            }
        )
        return self._extract_logs_return


class FakeFailureClusterDataExt:
    """Extended fake for new failure cluster methods (update/create/delete)."""

    def __init__(
        self,
        list_response=None,
        count_response=None,
        update_return="fc_updated",
        create_return=99,
        delete_return=None,
    ):
        self._list_response = list_response or []
        self._count_response = count_response
        self._update_return = update_return
        self._create_return = create_return
        self._delete_return = delete_return
        self.last_delete_filter = None
        self.requests = []

    def list(self, post_data):
        self.requests.append(post_data)
        return self._list_response

    def count(self, post_data):
        return self._count_response

    def update(self, post_data):
        return self._update_return

    def create(self, data):
        return self._create_return

    def delete(self, filter_obj):
        self.last_delete_filter = filter_obj.get()
        return self._delete_return


class FakeVampFull:
    """Complete fake Vamp to test all new properties."""

    def __init__(self, **kwargs):
        self.test_run = kwargs.get("test_run") or FakeTestRunExt()
        self.failure_cluster = kwargs.get("failure_cluster") or FakeFailureClusterDataExt()
        self.vsif = kwargs.get("vsif") or FakeVsifConfig()
        self.vsif_groups = kwargs.get("vsif_groups") or FakeVsifGroups()
        self.vsif_tests = kwargs.get("vsif_tests") or FakeVsifTests()
        self.vsif_hierarchy = kwargs.get("vsif_hierarchy") or FakeVsifHierarchy()
        self.vsif_sessions = kwargs.get("vsif_sessions") or FakeVsifSessionsExt()
        self.session = kwargs.get("session") or FakeSessionData()
        self.run_failure_cluster = kwargs.get("run_failure_cluster") or FakeRunFailureClusterData()
        self.test_plan = kwargs.get("test_plan") or object()
        self.vapi_requests = type(
            "Req", (), {"api_base_path": "https://example.test/nvl", "username": "tester"}
        )()


# ---------------------------------------------------------------------------
# TestVmanagerClientNewProperties
# ---------------------------------------------------------------------------


class TestVmanagerClientNewProperties:
    def test_vsif_property_delegates(self):
        fake = FakeVampFull()
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)
        assert client.vsif is fake.vsif

    def test_vsif_groups_property_delegates(self):
        fake = FakeVampFull()
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)
        assert client.vsif_groups is fake.vsif_groups

    def test_vsif_tests_property_delegates(self):
        fake = FakeVampFull()
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)
        assert client.vsif_tests is fake.vsif_tests

    def test_session_property_delegates(self):
        fake = FakeVampFull()
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)
        assert client.session is fake.session

    def test_run_failure_cluster_property_delegates(self):
        fake = FakeVampFull()
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)
        assert client.run_failure_cluster is fake.run_failure_cluster


# ---------------------------------------------------------------------------
# TestVmanagerClientRunMethods (new)
# ---------------------------------------------------------------------------


class TestVmanagerClientRunMethods:
    def test_update_run_returns_result_dict(self):
        fake_tr = FakeTestRunExt(update_return="run updated OK")
        fake = FakeVampFull(test_run=fake_tr)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.update_run({"filter": {}, "update": {"i_debug_status": "zbb"}})

        assert result == {"result": "run updated OK"}

    def test_associate_run_to_failure_cluster_normalizes_list(self):
        fake_tr = FakeTestRunExt(assoc_return=[{"id": 1, "cluster_id": 5}])
        fake = FakeVampFull(test_run=fake_tr)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.associate_run_to_failure_cluster({"runIds": [1], "clusterId": 5})

        assert result["count"] == 1
        assert result["rows"][0]["id"] == 1

    def test_associate_run_empty_response(self):
        fake_tr = FakeTestRunExt(assoc_return=[])
        fake = FakeVampFull(test_run=fake_tr)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.associate_run_to_failure_cluster({})

        assert result == {"rows": [], "count": 0}

    def test_dissociate_run_from_failure_cluster(self):
        fake_tr = FakeTestRunExt(dissoc_return=[{"ok": True}])
        fake = FakeVampFull(test_run=fake_tr)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.dissociate_run_from_failure_cluster({"runIds": [1]})

        assert result["count"] == 1

    def test_get_run_rerun_schemes_returns_list(self):
        schemes = [{"name": "scheme_a"}, {"name": "scheme_b"}]
        fake_tr = FakeTestRunExt(schemes_return=schemes)
        fake = FakeVampFull(test_run=fake_tr)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.get_run_rerun_schemes()

        assert result == {"rerun_schemes": schemes}

    def test_get_run_rerun_schemes_handles_non_list(self):
        fake_tr = FakeTestRunExt(schemes_return=None)
        fake = FakeVampFull(test_run=fake_tr)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.get_run_rerun_schemes()

        assert result == {"rerun_schemes": []}

    def test_get_run_total_count_size_returns_dict(self):
        totals = {"count": 1000, "sizeGB": 42.5}
        fake_tr = FakeTestRunExt(total_count_return=totals)
        fake = FakeVampFull(test_run=fake_tr)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.get_run_total_count_size()

        assert result == totals

    def test_get_run_total_count_size_handles_empty(self):
        fake_tr = FakeTestRunExt(total_count_return={})
        fake = FakeVampFull(test_run=fake_tr)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.get_run_total_count_size() == {}

    def test_extract_run_logs_wraps_text_payload(self):
        fake_tr = FakeTestRunExt(extract_logs_return="first log line\nsecond log line")
        fake = FakeVampFull(test_run=fake_tr)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.extract_run_logs(run_id=77, index=3, offset=10, length=20)

        assert result == {"logs": "first log line\nsecond log line"}
        assert fake_tr.requests[-1] == {
            "request_id": "77",
            "index": "3",
            "offset": "10",
            "length": "20",
        }


# ---------------------------------------------------------------------------
# TestVmanagerClientFailureClusterMethods (new)
# ---------------------------------------------------------------------------


class TestVmanagerClientFailureClusterMethods:
    def test_update_failure_cluster(self):
        fake_fc = FakeFailureClusterDataExt(update_return="fc updated")
        fake = FakeVampFull(failure_cluster=fake_fc)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.update_failure_cluster({"filter": {}, "update": {"owner": "newowner"}})

        assert result == {"result": "fc updated"}

    def test_create_failure_cluster_returns_id(self):
        fake_fc = FakeFailureClusterDataExt(create_return=77)
        fake = FakeVampFull(failure_cluster=fake_fc)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.create_failure_cluster({"name": "new_bucket", "owner": "me"})

        assert result == {"id": 77}

    def test_delete_failure_clusters_passes_filter_and_returns_ok(self):
        fake_fc = FakeFailureClusterDataExt()
        fake = FakeVampFull(failure_cluster=fake_fc)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)
        filt = {"c_type": ".AttValueFilter", "attName": "owner", "attValue": "me", "operand": "EQUALS"}

        result = client.delete_failure_clusters(filt)

        assert result == {"ok": True}
        assert fake_fc.last_delete_filter == filt


# ---------------------------------------------------------------------------
# TestVmanagerClientRunFailureClusterMethods
# ---------------------------------------------------------------------------


class TestVmanagerClientRunFailureClusterMethods:
    def test_list_run_failure_clusters_returns_raw_rows(self):
        raw_rows = [{"id": 10, "failure_cluster.id": 1}, {"id": 11, "failure_cluster.id": 2}]
        fake_rfc = FakeRunFailureClusterData(raw_response=raw_rows)
        fake = FakeVampFull(run_failure_cluster=fake_rfc)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_run_failure_clusters({"filter": {}})

        assert result["count"] == 2
        assert result["run_failure_clusters"] == raw_rows

    def test_list_run_failure_clusters_handles_empty(self):
        fake_rfc = FakeRunFailureClusterData(raw_response=[])
        fake = FakeVampFull(run_failure_cluster=fake_rfc)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_run_failure_clusters({"filter": {}})

        assert result == {"run_failure_clusters": [], "count": 0}

    def test_update_run_failure_cluster_association_passes_data(self):
        expected_result = [{"id": 5, "cluster_id": 9}]
        fake_rfc = FakeRunFailureClusterData(update_result=expected_result)
        fake = FakeVampFull(run_failure_cluster=fake_rfc)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.update_run_failure_cluster_association({"runId": 5, "clusterId": 9})

        assert result == {"run_failure_clusters": expected_result, "count": 1}
        assert fake_rfc.last_update_data == {"runId": 5, "clusterId": 9}

    def test_update_run_failure_cluster_association_dict_response(self):
        fake_rfc = FakeRunFailureClusterData(update_result={"ok": True})
        fake = FakeVampFull(run_failure_cluster=fake_rfc)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.update_run_failure_cluster_association({})

        assert result == {"ok": True}


# ---------------------------------------------------------------------------
# TestVmanagerClientVsifConfigMethods
# ---------------------------------------------------------------------------


class _VsifConfigResult:
    """Minimal stand-in for the real VsifConfigResult domain object."""
    def __init__(self):
        self.team = "ip.mc"
        self.name = "mc_config"
        self.owner = "joe"
        self.qslot = "slot1"
        self.queue = "q1"
        self.nbclass = "xlarge"
        self.disk_path = "/tmp/results"


class TestVmanagerClientVsifConfigMethods:
    def test_list_vsif_configs_converts_domain_objects(self):
        result_obj = _VsifConfigResult()
        fake_vsif = FakeVsifConfig(list_return=[result_obj])
        fake = FakeVampFull(vsif=fake_vsif)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_vsif_configs({"pageLength": 1000})

        assert result["count"] == 1
        row = result["vsif_configs"][0]
        assert row["name"] == "mc_config"
        assert row["team"] == "ip.mc"

    def test_list_vsif_configs_empty(self):
        fake_vsif = FakeVsifConfig(list_return=[])
        fake = FakeVampFull(vsif=fake_vsif)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_vsif_configs({})

        assert result == {"vsif_configs": [], "count": 0}

    def test_update_vsif_config_returns_result(self):
        fake_vsif = FakeVsifConfig(update_return="config updated")
        fake = FakeVampFull(vsif=fake_vsif)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.update_vsif_config({"filter": {}, "update": {"i_nbclass": "smallmem"}})

        assert result == {"result": "config updated"}


# ---------------------------------------------------------------------------
# TestVmanagerClientVsifGroupsMethods
# ---------------------------------------------------------------------------


class TestVmanagerClientVsifGroupsMethods:
    def test_get_vsif_group_found(self):
        fake_grp = FakeVsifGroups(get_return={"id": 1, "name": "grp_a"})
        fake = FakeVampFull(vsif_groups=fake_grp)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.get_vsif_group(1) == {"id": 1, "name": "grp_a"}

    def test_get_vsif_group_not_found_returns_empty(self):
        fake_grp = FakeVsifGroups(get_return=None)
        fake = FakeVampFull(vsif_groups=fake_grp)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.get_vsif_group(999) == {}

    def test_list_vsif_groups_normalizes(self):
        rows = [{"id": 1, "name": "g1"}, {"id": 2, "name": "g2"}]
        fake_grp = FakeVsifGroups(list_return=rows)
        fake = FakeVampFull(vsif_groups=fake_grp)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_vsif_groups({"filter": {}})

        assert result == {"vsif_groups": rows, "count": 2}

    def test_create_vsif_group_returns_id(self):
        fake_grp = FakeVsifGroups(create_return=7)
        fake = FakeVampFull(vsif_groups=fake_grp)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.create_vsif_group({"name": "new_grp"})

        assert result == {"id": 7}

    def test_update_vsif_group_returns_result(self):
        fake_grp = FakeVsifGroups(update_return="group updated")
        fake = FakeVampFull(vsif_groups=fake_grp)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.update_vsif_group({"filter": {}, "update": {"name": "new_name"}})

        assert result == {"result": "group updated"}

    def test_delete_vsif_groups_passes_filter(self):
        fake_grp = FakeVsifGroups(delete_return=5)
        fake = FakeVampFull(vsif_groups=fake_grp)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)
        filt = {"c_type": ".AttValueFilter", "attName": "name", "attValue": "grp_x", "operand": "EQUALS"}

        result = client.delete_vsif_groups(filt)

        assert result == {"id": 5}
        assert fake_grp.last_filter == filt


# ---------------------------------------------------------------------------
# TestVmanagerClientVsifTestsMethods
# ---------------------------------------------------------------------------


class TestVmanagerClientVsifTestsMethods:
    def test_get_vsif_test_found(self):
        fake_tst = FakeVsifTests(get_return={"id": 10, "name": "tb_boot"})
        fake = FakeVampFull(vsif_tests=fake_tst)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.get_vsif_test(10) == {"id": 10, "name": "tb_boot"}

    def test_get_vsif_test_not_found_returns_empty(self):
        fake_tst = FakeVsifTests(get_return=None)
        fake = FakeVampFull(vsif_tests=fake_tst)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.get_vsif_test(0) == {}

    def test_list_vsif_tests_normalizes(self):
        rows = [{"id": 1, "name": "TC_boot"}]
        fake_tst = FakeVsifTests(list_return=rows)
        fake = FakeVampFull(vsif_tests=fake_tst)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_vsif_tests({"filter": {}})

        assert result == {"vsif_tests": rows, "count": 1}

    def test_create_vsif_test_returns_id(self):
        fake_tst = FakeVsifTests(create_return=11)
        fake = FakeVampFull(vsif_tests=fake_tst)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.create_vsif_test({"name": "TC_new"}) == {"id": 11}

    def test_update_vsif_test_returns_result(self):
        fake_tst = FakeVsifTests(update_return="test updated")
        fake = FakeVampFull(vsif_tests=fake_tst)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.update_vsif_test({}) == {"result": "test updated"}

    def test_delete_vsif_tests_passes_filter(self):
        fake_tst = FakeVsifTests(delete_return=3)
        fake = FakeVampFull(vsif_tests=fake_tst)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)
        filt = {"attName": "name", "attValue": "tc_x"}

        result = client.delete_vsif_tests(filt)

        assert result == {"id": 3}
        assert fake_tst.last_filter == filt


# ---------------------------------------------------------------------------
# TestVmanagerClientVsifHierarchyMethods
# ---------------------------------------------------------------------------


class TestVmanagerClientVsifHierarchyMethods:
    def test_get_vsif_hierarchy_found(self):
        fake_h = FakeVsifHierarchy(get_return={"id": 20, "name": "hc_a"})
        fake = FakeVampFull(vsif_hierarchy=fake_h)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.get_vsif_hierarchy(20) == {"id": 20, "name": "hc_a"}

    def test_get_vsif_hierarchy_not_found(self):
        fake_h = FakeVsifHierarchy(get_return=None)
        fake = FakeVampFull(vsif_hierarchy=fake_h)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.get_vsif_hierarchy(0) == {}

    def test_list_vsif_hierarchy_normalizes(self):
        rows = [{"id": 20, "name": "hc_a"}, {"id": 21, "name": "hc_b"}]
        fake_h = FakeVsifHierarchy(list_return=rows)
        fake = FakeVampFull(vsif_hierarchy=fake_h)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_vsif_hierarchy(100)

        assert result == {"vsif_hierarchy": rows, "count": 2}

    def test_create_vsif_hierarchy_returns_id(self):
        fake_h = FakeVsifHierarchy(create_return=50)
        fake = FakeVampFull(vsif_hierarchy=fake_h)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.create_vsif_hierarchy({"name": "hc_new"}) == {"id": 50}

    def test_attach_groups_to_groups_returns_ok(self):
        fake_h = FakeVsifHierarchy()
        fake = FakeVampFull(vsif_hierarchy=fake_h)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)
        child = {"attName": "id", "attValue": 1}
        parent = {"attName": "id", "attValue": 2}

        result = client.attach_vsif_hierarchy_groups_to_groups(10, child, parent)

        assert result == {"ok": True}
        assert fake_h.attach_calls == [("g2g", 10, child, parent)]

    def test_attach_groups_to_sessions_returns_ok(self):
        fake_h = FakeVsifHierarchy()
        fake = FakeVampFull(vsif_hierarchy=fake_h)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.attach_vsif_hierarchy_groups_to_sessions(
            10, {"attName": "id", "attValue": 1}, {"attName": "name", "attValue": "s1"}
        )

        assert result == {"ok": True}
        assert fake_h.attach_calls[0][0] == "g2s"

    def test_attach_tests_to_groups_returns_ok(self):
        fake_h = FakeVsifHierarchy()
        fake = FakeVampFull(vsif_hierarchy=fake_h)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.attach_vsif_hierarchy_tests_to_groups(
            10, {"attName": "id", "attValue": 5}, {"attName": "id", "attValue": 1}
        )

        assert result == {"ok": True}
        assert fake_h.attach_calls[0][0] == "t2g"

    def test_attach_tests_to_sessions_returns_ok(self):
        fake_h = FakeVsifHierarchy()
        fake = FakeVampFull(vsif_hierarchy=fake_h)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.attach_vsif_hierarchy_tests_to_sessions(
            10, {"attName": "id", "attValue": 5}, {"attName": "name", "attValue": "s1"}
        )

        assert result == {"ok": True}
        assert fake_h.attach_calls[0][0] == "t2s"


# ---------------------------------------------------------------------------
# TestVmanagerClientVsifSessionsExt
# ---------------------------------------------------------------------------


class TestVmanagerClientVsifSessionsExt:
    def test_get_vsif_session_found(self):
        fake_s = FakeVsifSessionsExt(get_return={"id": 100, "name": "weekly_a0"})
        fake = FakeVampFull(vsif_sessions=fake_s)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.get_vsif_session(100) == {"id": 100, "name": "weekly_a0"}

    def test_get_vsif_session_not_found(self):
        fake_s = FakeVsifSessionsExt(get_return=None)
        fake = FakeVampFull(vsif_sessions=fake_s)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.get_vsif_session(0) == {}

    def test_create_vsif_session_returns_id(self):
        fake_s = FakeVsifSessionsExt(create_with_perm_return=42)
        fake = FakeVampFull(vsif_sessions=fake_s)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.create_vsif_session({"name": "my_session"})

        assert result == {"id": 42}

    def test_create_vsif_session_with_permissions_returns_id(self):
        fake_s = FakeVsifSessionsExt(create_with_perm_return=42)
        fake = FakeVampFull(vsif_sessions=fake_s)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.create_vsif_session_with_permissions(
            {"session": {"name": "my_session"}, "permissions": {"user1": "WRITE"}}
        )

        assert result == {"id": 42}

    def test_create_vsif_session_with_permissions_defaults_permissions_none(self):
        fake_s = FakeVsifSessionsExt(create_with_perm_return=99)
        fake = FakeVampFull(vsif_sessions=fake_s)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)
        # No "permissions" key in post_data
        result = client.create_vsif_session_with_permissions({"session": {"name": "bare"}})

        assert result == {"id": 99}

    def test_delete_vsif_sessions_passes_filter(self):
        fake_s = FakeVsifSessionsExt(delete_return=1)
        fake = FakeVampFull(vsif_sessions=fake_s)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)
        filt = {"attName": "name", "attValue": "weekly_a0"}

        result = client.delete_vsif_sessions(filt)

        assert result == {"id": 1}
        assert fake_s.last_filter == filt


# ---------------------------------------------------------------------------
# TestVmanagerClientSessionMethods (runtime session)
# ---------------------------------------------------------------------------


class TestVmanagerClientSessionMethods:
    def test_get_session_by_name_found(self):
        result_obj = _FakeSessionResult(session_id=55, name="ttl_weekly", config="cfg_a")
        fake_sd = FakeSessionData(session_result=result_obj)
        fake = FakeVampFull(session=fake_sd)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.get_session_by_name("ttl_weekly")

        assert result == {"id": 55, "name": "ttl_weekly", "config": "cfg_a"}

    def test_get_session_by_name_not_found_returns_empty(self):
        fake_sd = FakeSessionData(session_result=None)
        fake = FakeVampFull(session=fake_sd)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.get_session_by_name("nonexistent") == {}


# ---------------------------------------------------------------------------
# Tool-layer tests — new run tools
# ---------------------------------------------------------------------------


class TestNewRunTools:
    def test_run_update_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def update_run(self, post_data): return {"result": "run updated"}

        monkeypatch.setattr("tools.vmanager._runs.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_run_update"](post_data_json='{"filter": {}}')
        )
        assert json.loads(result) == {"result": "run updated"}

    def test_run_update_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(mock_mcp.tools["vamp_run_update"](post_data_json="bad"))
        assert result.startswith("ERROR: invalid JSON")

    def test_run_associate_to_failure_cluster_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def associate_run_to_failure_cluster(self, post_data):
                return {"rows": [], "count": 0}

        monkeypatch.setattr("tools.vmanager._runs.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_run_associate_to_failure_cluster"](post_data_json='{}')
        )
        assert json.loads(result) == {"rows": [], "count": 0}

    def test_run_associate_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_run_associate_to_failure_cluster"](post_data_json="{bad}")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_run_dissociate_from_failure_cluster_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def dissociate_run_from_failure_cluster(self, post_data):
                return {"rows": [{"id": 1}], "count": 1}

        monkeypatch.setattr("tools.vmanager._runs.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_run_dissociate_from_failure_cluster"](post_data_json='{}')
        )
        assert json.loads(result)["count"] == 1

    def test_run_dissociate_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_run_dissociate_from_failure_cluster"](post_data_json="!")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_run_rerun_schemes_get_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def get_run_rerun_schemes(self): return {"rerun_schemes": ["default", "custom"]}

        monkeypatch.setattr("tools.vmanager._runs.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_run_rerun_schemes_get"]())
        assert json.loads(result) == {"rerun_schemes": ["default", "custom"]}

    def test_run_total_count_size_get_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def get_run_total_count_size(self): return {"count": 500, "sizeGB": 10.2}

        monkeypatch.setattr("tools.vmanager._runs.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_run_total_count_size_get"]())
        assert json.loads(result) == {"count": 500, "sizeGB": 10.2}

    def test_run_extract_logs_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass

            def extract_run_logs(self, run_id, index, offset, length):
                assert (run_id, index, offset, length) == (7, 2, 10, 50)
                return {"logs": "slice"}

        monkeypatch.setattr("tools.vmanager._runs.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_run_extract_logs"](run_id=7, index=2, offset=10, length=50)
        )
        assert json.loads(result) == {"logs": "slice"}


# ---------------------------------------------------------------------------
# Tool-layer tests — new failure cluster tools
# ---------------------------------------------------------------------------


class TestNewFailureClusterTools:
    def test_failure_cluster_update_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def update_failure_cluster(self, post_data): return {"result": "updated"}

        monkeypatch.setattr("tools.vmanager._failure_clusters.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_failure_cluster_update"](post_data_json='{"filter": {}}')
        )
        assert json.loads(result) == {"result": "updated"}

    def test_failure_cluster_update_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_failure_cluster_update"](post_data_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_failure_cluster_create_returns_id(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def create_failure_cluster(self, post_data): return {"id": 99}

        monkeypatch.setattr("tools.vmanager._failure_clusters.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_failure_cluster_create"](post_data_json='{"name": "new"}')
        )
        assert json.loads(result) == {"id": 99}

    def test_failure_cluster_create_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_failure_cluster_create"](post_data_json="{bad}")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_failure_cluster_delete_returns_ok(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def delete_failure_clusters(self, filter_dict): return {"ok": True}

        monkeypatch.setattr("tools.vmanager._failure_clusters.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_failure_cluster_delete"](filter_json='{"attName": "owner"}')
        )
        assert json.loads(result) == {"ok": True}

    def test_failure_cluster_delete_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_failure_cluster_delete"](filter_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")


# ---------------------------------------------------------------------------
# Tool-layer tests — run-failure-cluster tools
# ---------------------------------------------------------------------------


class TestRunFailureClusterTools:
    def test_run_failure_cluster_list_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_run_failure_clusters(self, post_data):
                return {"run_failure_clusters": [{"id": 5}], "count": 1}

        monkeypatch.setattr(
            "tools.vmanager._run_failure_clusters.VmanagerClient", FakeClient
        )

        result = asyncio.run(
            mock_mcp.tools["vamp_run_failure_cluster_list"](post_data_json='{"filter": {}}')
        )
        assert json.loads(result)["count"] == 1

    def test_run_failure_cluster_list_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_run_failure_cluster_list"](post_data_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_run_failure_cluster_update_association_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def update_run_failure_cluster_association(self, post_data):
                return {"ok": True}

        monkeypatch.setattr(
            "tools.vmanager._run_failure_clusters.VmanagerClient", FakeClient
        )

        result = asyncio.run(
            mock_mcp.tools["vamp_run_failure_cluster_update_association"](
                post_data_json='{"runId": 1}'
            )
        )
        assert json.loads(result) == {"ok": True}

    def test_run_failure_cluster_update_association_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_run_failure_cluster_update_association"](
                post_data_json="bad"
            )
        )
        assert result.startswith("ERROR: invalid JSON")


# ---------------------------------------------------------------------------
# Tool-layer tests — vsif_config tools
# ---------------------------------------------------------------------------


class TestVsifConfigTools:
    def test_vsif_config_list_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_vsif_configs(self, post_data):
                return {"vsif_configs": [{"name": "cfg_a", "team": "ip.mc"}], "count": 1}

        monkeypatch.setattr("tools.vmanager._vsif_config.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_config_list"](post_data_json='{}')
        )
        payload = json.loads(result)
        assert payload["count"] == 1
        assert payload["vsif_configs"][0]["name"] == "cfg_a"

    def test_vsif_config_list_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(mock_mcp.tools["vamp_vsif_config_list"](post_data_json="bad"))
        assert result.startswith("ERROR: invalid JSON")

    def test_vsif_config_update_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def update_vsif_config(self, post_data): return {"result": "config updated"}

        monkeypatch.setattr("tools.vmanager._vsif_config.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_config_update"](post_data_json='{"filter": {}}')
        )
        assert json.loads(result) == {"result": "config updated"}

    def test_vsif_config_update_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_config_update"](post_data_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")


# ---------------------------------------------------------------------------
# Tool-layer tests — vsif_groups tools
# ---------------------------------------------------------------------------


class TestVsifGroupsTools:
    def test_vsif_group_get_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def get_vsif_group(self, group_id):
                assert group_id == 7
                return {"id": 7, "name": "grp_a"}

        monkeypatch.setattr("tools.vmanager._vsif_groups.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_vsif_group_get"](group_id=7))
        assert json.loads(result)["id"] == 7

    def test_vsif_groups_list_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_vsif_groups(self, post_data):
                return {"vsif_groups": [{"id": 1}], "count": 1}

        monkeypatch.setattr("tools.vmanager._vsif_groups.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_vsif_groups_list"](post_data_json='{}'))
        assert json.loads(result)["count"] == 1

    def test_vsif_groups_list_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(mock_mcp.tools["vamp_vsif_groups_list"](post_data_json="bad"))
        assert result.startswith("ERROR: invalid JSON")

    def test_vsif_group_create_returns_id(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def create_vsif_group(self, post_data): return {"id": 88}

        monkeypatch.setattr("tools.vmanager._vsif_groups.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_group_create"](post_data_json='{"name": "grp"}')
        )
        assert json.loads(result) == {"id": 88}

    def test_vsif_group_create_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_group_create"](post_data_json="{bad}")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_vsif_group_update_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def update_vsif_group(self, post_data): return {"result": "grp updated"}

        monkeypatch.setattr("tools.vmanager._vsif_groups.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_group_update"](post_data_json='{"filter": {}}')
        )
        assert json.loads(result) == {"result": "grp updated"}

    def test_vsif_group_update_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_group_update"](post_data_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_vsif_group_delete_returns_id(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def delete_vsif_groups(self, filter_dict):
                assert "attName" in filter_dict
                return {"id": 5}

        monkeypatch.setattr("tools.vmanager._vsif_groups.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_group_delete"](
                filter_json='{"attName": "name", "attValue": "grp_x"}'
            )
        )
        assert json.loads(result) == {"id": 5}

    def test_vsif_group_delete_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_group_delete"](filter_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")


# ---------------------------------------------------------------------------
# Tool-layer tests — vsif_tests tools
# ---------------------------------------------------------------------------


class TestVsifTestsTools:
    def test_vsif_test_get_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def get_vsif_test(self, test_id): return {"id": 10, "name": "TC_boot"}

        monkeypatch.setattr("tools.vmanager._vsif_tests.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_vsif_test_get"](test_id=10))
        assert json.loads(result)["name"] == "TC_boot"

    def test_vsif_tests_list_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_vsif_tests(self, post_data):
                return {"vsif_tests": [{"id": 1}, {"id": 2}], "count": 2}

        monkeypatch.setattr("tools.vmanager._vsif_tests.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_vsif_tests_list"](post_data_json='{}'))
        assert json.loads(result)["count"] == 2

    def test_vsif_tests_list_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(mock_mcp.tools["vamp_vsif_tests_list"](post_data_json="bad"))
        assert result.startswith("ERROR: invalid JSON")

    def test_vsif_test_create_returns_id(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def create_vsif_test(self, post_data): return {"id": 77}

        monkeypatch.setattr("tools.vmanager._vsif_tests.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_test_create"](post_data_json='{"name": "TC"}')
        )
        assert json.loads(result) == {"id": 77}

    def test_vsif_test_create_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_test_create"](post_data_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_vsif_test_update_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def update_vsif_test(self, post_data): return {"result": "test updated"}

        monkeypatch.setattr("tools.vmanager._vsif_tests.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_test_update"](post_data_json='{"filter": {}}')
        )
        assert json.loads(result) == {"result": "test updated"}

    def test_vsif_test_update_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_test_update"](post_data_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_vsif_test_delete_returns_id(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def delete_vsif_tests(self, filter_dict): return {"id": 3}

        monkeypatch.setattr("tools.vmanager._vsif_tests.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_test_delete"](filter_json='{"attName": "name"}')
        )
        assert json.loads(result) == {"id": 3}

    def test_vsif_test_delete_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_test_delete"](filter_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")


# ---------------------------------------------------------------------------
# Tool-layer tests — vsif_hierarchy tools
# ---------------------------------------------------------------------------


class TestVsifHierarchyTools:
    def test_vsif_hierarchy_get_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def get_vsif_hierarchy(self, hierarchy_id): return {"id": 20, "name": "hc_a"}

        monkeypatch.setattr("tools.vmanager._vsif_hierarchy.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_vsif_hierarchy_get"](hierarchy_id=20))
        assert json.loads(result)["id"] == 20

    def test_vsif_hierarchy_list_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_vsif_hierarchy(self, parent_id, page_length, page_offset):
                assert parent_id == 100
                return {"vsif_hierarchy": [{"id": 20}], "count": 1}

        monkeypatch.setattr("tools.vmanager._vsif_hierarchy.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_hierarchy_list"](parent_id=100)
        )
        assert json.loads(result)["count"] == 1

    def test_vsif_hierarchy_create_returns_id(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def create_vsif_hierarchy(self, post_data): return {"id": 50}

        monkeypatch.setattr("tools.vmanager._vsif_hierarchy.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_hierarchy_create"](post_data_json='{"name": "hc"}')
        )
        assert json.loads(result) == {"id": 50}

    def test_vsif_hierarchy_create_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_hierarchy_create"](post_data_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_vsif_hierarchy_attach_groups_to_groups_returns_ok(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        calls = []

        class FakeClient:
            def __init__(self, repo_root): pass
            def attach_vsif_hierarchy_groups_to_groups(self, hc_id, child, parent):
                calls.append((hc_id, child, parent))
                return {"ok": True}

        monkeypatch.setattr("tools.vmanager._vsif_hierarchy.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_hierarchy_attach_groups_to_groups"](
                hierarchy_config_id=10,
                child_groups_filter_json='{"attName": "id", "attValue": 1}',
                parent_groups_filter_json='{"attName": "id", "attValue": 2}',
            )
        )
        assert json.loads(result) == {"ok": True}
        assert calls[0][0] == 10

    def test_vsif_hierarchy_attach_groups_to_groups_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_hierarchy_attach_groups_to_groups"](
                hierarchy_config_id=1,
                child_groups_filter_json="bad",
                parent_groups_filter_json="{}",
            )
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_vsif_hierarchy_attach_groups_to_sessions_returns_ok(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def attach_vsif_hierarchy_groups_to_sessions(self, hc_id, grp, sess):
                return {"ok": True}

        monkeypatch.setattr("tools.vmanager._vsif_hierarchy.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_hierarchy_attach_groups_to_sessions"](
                hierarchy_config_id=10,
                groups_filter_json='{}',
                sessions_filter_json='{}',
            )
        )
        assert json.loads(result) == {"ok": True}

    def test_vsif_hierarchy_attach_tests_to_groups_returns_ok(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def attach_vsif_hierarchy_tests_to_groups(self, hc_id, tst, grp):
                return {"ok": True}

        monkeypatch.setattr("tools.vmanager._vsif_hierarchy.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_hierarchy_attach_tests_to_groups"](
                hierarchy_config_id=10,
                tests_filter_json='{}',
                groups_filter_json='{}',
            )
        )
        assert json.loads(result) == {"ok": True}

    def test_vsif_hierarchy_attach_tests_to_sessions_returns_ok(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def attach_vsif_hierarchy_tests_to_sessions(self, hc_id, tst, sess):
                return {"ok": True}

        monkeypatch.setattr("tools.vmanager._vsif_hierarchy.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_hierarchy_attach_tests_to_sessions"](
                hierarchy_config_id=10,
                tests_filter_json='{}',
                sessions_filter_json='{}',
            )
        )
        assert json.loads(result) == {"ok": True}


# ---------------------------------------------------------------------------
# Tool-layer tests — vsif_sessions new tools
# ---------------------------------------------------------------------------


class TestVsifSessionsNewTools:
    def test_vsif_session_get_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def get_vsif_session(self, session_id): return {"id": 100, "name": "weekly_a0"}

        monkeypatch.setattr("tools.vmanager._vsif_sessions.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_vsif_session_get"](session_id=100))
        assert json.loads(result)["name"] == "weekly_a0"

    def test_vsif_session_create_returns_id(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def create_vsif_session(self, post_data): return {"id": 42}

        monkeypatch.setattr("tools.vmanager._vsif_sessions.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_session_create"](
                post_data_json='{"name": "new_session"}'
            )
        )
        assert json.loads(result) == {"id": 42}

    def test_vsif_session_create_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_session_create"](post_data_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_vsif_session_create_with_permissions_returns_id(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def create_vsif_session_with_permissions(self, post_data): return {"id": 42}

        monkeypatch.setattr("tools.vmanager._vsif_sessions.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_session_create_with_permissions"](
                post_data_json='{"session": {"name": "s1"}}'
            )
        )
        assert json.loads(result) == {"id": 42}

    def test_vsif_session_create_with_permissions_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_session_create_with_permissions"](
                post_data_json="bad"
            )
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_vsif_session_delete_returns_id(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def delete_vsif_sessions(self, filter_dict): return {"id": 1}

        monkeypatch.setattr("tools.vmanager._vsif_sessions.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_session_delete"](
                filter_json='{"attName": "name", "attValue": "old_sess"}'
            )
        )
        assert json.loads(result) == {"id": 1}

    def test_vsif_session_delete_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_session_delete"](filter_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")


# ---------------------------------------------------------------------------
# Tool-layer tests — runtime sessions
# ---------------------------------------------------------------------------


class TestSessionTools:
    def test_session_get_by_name_found(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def get_session_by_name(self, name):
                assert name == "ttl_weekly"
                return {"id": 55, "name": "ttl_weekly", "config": "cfg_a"}

        monkeypatch.setattr("tools.vmanager._sessions.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_session_get_by_name"](name="ttl_weekly")
        )
        payload = json.loads(result)
        assert payload["id"] == 55
        assert payload["config"] == "cfg_a"

    def test_session_get_by_name_not_found(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def get_session_by_name(self, name): return {}

        monkeypatch.setattr("tools.vmanager._sessions.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_session_get_by_name"](name="nonexistent")
        )
        assert json.loads(result) == {}


# ---------------------------------------------------------------------------
# Smoke: all 70 tools are registered
# ---------------------------------------------------------------------------


class TestAllToolsRegistered:
    EXPECTED_TOOLS = [
        # Existing (11)
        "vamp_standard_runs_list",
        "vamp_runs_list",
        "vamp_runs_count",
        "vamp_run_get",
        "vamp_failure_cluster_list",
        "vamp_failure_cluster_count",
        "vamp_failure_cluster_get",
        "vamp_sessions_list",
        "vamp_sessions_count",
        "vamp_plan_list",
        "vamp_plan_count",
        # New run tools (6)
        "vamp_run_update",
        "vamp_run_associate_to_failure_cluster",
        "vamp_run_dissociate_from_failure_cluster",
        "vamp_run_rerun_schemes_get",
        "vamp_run_total_count_size_get",
        "vamp_run_extract_logs",
        # New failure cluster tools (4)
        "vamp_failure_cluster_update",
        "vamp_failure_cluster_create",
        "vamp_failure_cluster_delete",
        "vamp_failure_clusters_for_runs",
        # New run-failure-cluster tools (6)
        "vamp_run_failure_cluster_list",
        "vamp_run_failure_cluster_update_association",
        "vamp_run_failures_for_team",
        "vamp_run_failures_in_datetime",
        "vamp_run_failures_needs_rerun",
        "vamp_run_failures_for_result_ids",
        # New vsif_config tools (3)
        "vamp_vsif_config_list",
        "vamp_vsif_config_update",
        "vamp_vsif_config_list_by_name",
        # New vsif_groups tools (7)
        "vamp_vsif_group_get",
        "vamp_vsif_groups_list",
        "vamp_vsif_group_create",
        "vamp_vsif_group_update",
        "vamp_vsif_group_delete",
        "vamp_vsif_groups_list_for_session",
        "vamp_vsif_groups_list_for_group",
        # New vsif_tests tools (7)
        "vamp_vsif_test_get",
        "vamp_vsif_tests_list",
        "vamp_vsif_test_create",
        "vamp_vsif_test_update",
        "vamp_vsif_test_delete",
        "vamp_vsif_tests_list_for_session",
        "vamp_vsif_tests_list_for_group",
        # New vsif_hierarchy tools (7)
        "vamp_vsif_hierarchy_get",
        "vamp_vsif_hierarchy_list",
        "vamp_vsif_hierarchy_create",
        "vamp_vsif_hierarchy_attach_groups_to_groups",
        "vamp_vsif_hierarchy_attach_groups_to_sessions",
        "vamp_vsif_hierarchy_attach_tests_to_groups",
        "vamp_vsif_hierarchy_attach_tests_to_sessions",
        # New vsif_sessions tools (4)
        "vamp_vsif_session_get",
        "vamp_vsif_session_create",
        "vamp_vsif_session_create_with_permissions",
        "vamp_vsif_session_delete",
        # New runtime session tool (1)
        "vamp_session_get_by_name",
        # New plan tools (11)
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
        "vamp_plan_find",
    ]

    def test_all_68_tools_registered(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        for tool_name in self.EXPECTED_TOOLS:
            assert tool_name in mock_mcp.tools, f"missing tool: {tool_name}"
        assert len(mock_mcp.tools) == len(self.EXPECTED_TOOLS), (
            f"tool count mismatch: got {sorted(mock_mcp.tools)} "
            f"expected {sorted(self.EXPECTED_TOOLS)}"
        )


# ===========================================================================
# NEW — fakes and tests for the 20 additional tools added in this PR
# ===========================================================================

# ---------------------------------------------------------------------------
# Shared fake helpers for new test classes
# ---------------------------------------------------------------------------


class _FakeRfcResult:
    """Minimal fake that mimics a RunFailureClusterResult for serialization tests."""
    def __init__(self, result_id=1, status="failed", team="ip.mc", bucket_id=5, bucket_name="bkt"):
        self.result_id = result_id
        self.status = status
        self.team = team
        self.bucket_id = bucket_id
        self.bucket_name = bucket_name
        self.cmd_line = "/run"
        self.debug_status = "new"
        self.debugger = ""
        self.dut = "mc"
        self.end_time = 0
        self.is_rerun = False
        self.model_version = "1.0"
        self.result_directory = "/tmp/run"
        self.rerun_status = "none"
        self.session_name = "ttl_weekly"
        self.unique_tag = "tag1"


class _FakeFcResultObj:
    """Minimal fake that mimics a FailureClusterResult object."""
    def __init__(self, fc_id=10, name="bkt_a", owner="me"):
        self.id = fc_id
        self.name = name
        self.owner = owner
        self.associated = True
        self.bucket_status = "open"
        self.description = "desc"
        self.for_indicators = False
        self.hsdes_ids = ""
        self.index = 0
        self.last_update = 0
        self.notes = ""
        self.number_of_entities = 1
        self.submitted_date = 0
        self.unique_tag = "u1"
        self.updated_by_vmgr = ""


class FakeRunFailureClusterHelpers:
    """Extended fake for RunFailureClusterData helper query methods."""

    def __init__(self, for_team=None, in_datetime=None, needs_rerun=None, from_ids=None):
        self._for_team = for_team or []
        self._in_datetime = in_datetime or []
        self._needs_rerun = needs_rerun or []
        self._from_ids = from_ids or []
        self.last_team = None
        self.last_days = None
        self.last_datetime_kwargs = {}
        self.last_ids = None

        # Provide vapi_requests so existing update_associated path still works.
        self.vapi_requests = type("R", (), {"post": lambda self, e, d: []})()

    def get_failures_for_team(self, team, days=15):
        self.last_team = team
        self.last_days = days
        return self._for_team

    def get_failures_in_datetime(self, days=0, hours=0, minutes=0):
        self.last_datetime_kwargs = {"days": days, "hours": hours, "minutes": minutes}
        return self._in_datetime

    def get_failures_marked_needs_rerun(self):
        return self._needs_rerun

    def get_from_result_ids(self, result_ids):
        self.last_ids = result_ids
        return self._from_ids

    def update_associated(self, post_data):
        return []

    def _response_json(self, response, default=None):
        return response or default


class FakeFailureClusterWithAssoc:
    """Extended fake for FailureClusterData with get_associated_failure_clusters."""

    def __init__(self, assoc_return=None, **kwargs):
        self._assoc_return = assoc_return or []
        self._list_response = kwargs.get("list_response", [])
        self._count_response = kwargs.get("count_response", None)
        self.requests = []

    def list(self, post_data):
        self.requests.append(post_data)
        return self._list_response

    def count(self, post_data):
        return self._count_response

    def update(self, post_data):
        return "updated"

    def create(self, data):
        return 1

    def delete(self, filter_obj):
        pass

    def get_associated_failure_clusters(self, run_ids):
        return self._assoc_return


class FakeVsifGroupsScoped:
    """Extends FakeVsifGroups with scoped list support."""

    def __init__(self, list_return=None):
        self._list_return = list_return if list_return is not None else []
        self.last_parent_sessions_filter = None
        self.last_parent_groups_filter = None

    def get(self, group_id):
        return {}

    def list(self, data):
        return self._list_return

    def list_for_parent_sessions(self, filter_obj, data=None):
        self.last_parent_sessions_filter = filter_obj.get()
        return self._list_return

    def list_for_parent_groups(self, filter_obj, data=None):
        self.last_parent_groups_filter = filter_obj.get()
        return self._list_return

    def create(self, data):
        return 1

    def update(self, data):
        return "ok"

    def delete(self, filter_obj):
        return 1


class FakeVsifTestsScoped:
    """Extends FakeVsifTests with scoped list support."""

    def __init__(self, list_return=None):
        self._list_return = list_return if list_return is not None else []
        self.last_parent_sessions_filter = None
        self.last_parent_groups_filter = None

    def get(self, test_id):
        return {}

    def list(self, data):
        return self._list_return

    def list_for_parent_sessions(self, filter_obj, data=None):
        self.last_parent_sessions_filter = filter_obj.get()
        return self._list_return

    def list_for_parent_groups(self, filter_obj, data=None):
        self.last_parent_groups_filter = filter_obj.get()
        return self._list_return

    def create(self, data):
        return 1

    def update(self, data):
        return "ok"

    def delete(self, filter_obj):
        return 1


class FakeVsifConfigWithName:
    """Extends FakeVsifConfig with get_vsif_config_by_name_match."""

    def __init__(self, list_return=None):
        self._list_return = list_return or []
        self.last_name = None
        self.last_page_length = None

    def list(self, post_data):
        return self._list_return

    def get_vsif_config_by_name_match(self, name, page_length=1000):
        self.last_name = name
        self.last_page_length = page_length
        return self._list_return

    def update(self, post_data):
        return "ok"


class FakeTestPlanFull:
    """Full fake for TestPlanQueries with all new methods."""

    def __init__(
        self,
        list_return=None,
        count_return=None,
        list_vplans_return=None,
        list_sub_elements_return=None,
        get_vplan_return=None,
        rich_text_return=None,
        add_section_return=None,
        add_reference_return=None,
        add_metrics_port_return=None,
        update_plan_return=None,
        update_bulk_return=None,
        update_section_return=None,
        update_reference_return=None,
    ):
        self._list_return = list_return or []
        self._count_return = count_return
        self._list_vplans_return = list_vplans_return or []
        self._list_sub_elements_return = list_sub_elements_return or []
        self._get_vplan_return = get_vplan_return or {}
        self._rich_text_return = rich_text_return or {}
        self._add_section_return = add_section_return
        self._add_reference_return = add_reference_return
        self._add_metrics_port_return = add_metrics_port_return
        self._update_plan_return = update_plan_return or {}
        self._update_bulk_return = update_bulk_return or {}
        self._update_section_return = update_section_return or {}
        self._update_reference_return = update_reference_return or {}
        self.requests = []

    def list(self, post_data):
        self.requests.append(post_data)
        return self._list_return

    def count(self, post_data):
        return self._count_return

    def list_vplans(self, post_data=None):
        return self._list_vplans_return

    def list_sub_elements(
        self,
        vplan_name=None,
        hierarchy=None,
        selection=None,
        page_length=10000,
        post_data=None,
    ):
        self.requests.append(post_data)
        return self._list_sub_elements_return

    def get_vplan(self, post_data):
        return self._get_vplan_return

    def get_rich_text(self, post_data=None, **kwargs):
        return self._rich_text_return

    def add_section(self, post_data, headers=None):
        return self._add_section_return

    def add_reference(self, post_data, headers=None):
        return self._add_reference_return

    def add_metrics_port(self, post_data, headers=None):
        return self._add_metrics_port_return

    def update_plan(self, post_data, headers=None):
        return self._update_plan_return

    def update_bulk(self, post_data, headers=None):
        return self._update_bulk_return

    def update_section(self, post_data, headers=None):
        return self._update_section_return

    def update_reference(self, post_data, headers=None):
        return self._update_reference_return


def _make_vamp_full(**kwargs):
    """Build a FakeVampFull substituting any provided kwargs."""
    return FakeVampFull(**kwargs)


# ---------------------------------------------------------------------------
# TestVmanagerClientPlanExtMethods
# ---------------------------------------------------------------------------


class TestVmanagerClientPlanExtMethods:
    def test_list_plan_sub_elements_returns_dict(self):
        plan = FakeTestPlanFull(list_sub_elements_return=[{"id": "e1", "name": "FeatureA"}])
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_plan_sub_elements(
            {"sticky-context": {"vplan": "vp_a", "db-vplan": True}}
        )

        assert result == {"sub_elements": [{"id": "e1", "name": "FeatureA"}], "count": 1}

    def test_list_vplans_returns_dict(self):
        plan = FakeTestPlanFull(list_vplans_return=[{"name": "vp_a"}, {"name": "vp_b"}])
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_vplans()

        assert result == {"vplans": [{"name": "vp_a"}, {"name": "vp_b"}], "count": 2}

    def test_list_vplans_unwraps_vplans_key(self):
        """Wrapped {"vplans": [...]} API response is normalized through _extract_rows."""
        plan = FakeTestPlanFull()
        plan._list_vplans_return = {"vplans": [{"name": "vp_a"}, {"name": "vp_b"}]}
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_vplans()

        assert result == {"vplans": [{"name": "vp_a"}, {"name": "vp_b"}], "count": 2}

    def test_list_vplans_wrapped_with_count_field_discarded(self):
        """Wrapped response with extra count field: rows are extracted, count recomputed."""
        plan = FakeTestPlanFull()
        plan._list_vplans_return = {"vplans": [{"id": 1, "name": "vp_x"}], "count": 99}
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_vplans()

        assert result["vplans"] == [{"id": 1, "name": "vp_x"}]
        assert result["count"] == 1

    def test_list_vplans_empty(self):
        plan = FakeTestPlanFull(list_vplans_return=[])
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.list_vplans() == {"vplans": [], "count": 0}

    def test_get_vplan_returns_dict(self):
        plan = FakeTestPlanFull(get_vplan_return={"name": "vp_a", "id": 1})
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.get_vplan({"sticky-context": {"vplan": "vp_a"}})

        assert result == {"name": "vp_a", "id": 1}

    def test_get_vplan_empty_returns_empty_dict(self):
        plan = FakeTestPlanFull(get_vplan_return={})
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.get_vplan({}) == {}

    def test_get_plan_rich_text_returns_dict(self):
        plan = FakeTestPlanFull(rich_text_return={"content": "<p>hi</p>", "checksum": "abc"})
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.get_plan_rich_text({"sticky-context": {"vplan": "vp_a"}})

        assert result["checksum"] == "abc"

    def test_add_plan_section_returns_id(self):
        plan = FakeTestPlanFull(add_section_return=101)
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.add_plan_section({"name": "sec_1"}) == {"id": 101}

    def test_add_plan_reference_returns_id(self):
        plan = FakeTestPlanFull(add_reference_return=202)
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.add_plan_reference({"name": "ref_1"}) == {"id": 202}

    def test_add_plan_metrics_port_returns_id(self):
        plan = FakeTestPlanFull(add_metrics_port_return=303)
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.add_plan_metrics_port({"name": "mp_1"}) == {"id": 303}

    def test_update_plan_returns_dict(self):
        plan = FakeTestPlanFull(update_plan_return={"status": "ok"})
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.update_plan({"update": {}}) == {"status": "ok"}

    def test_update_plan_wraps_string_result(self):
        plan = FakeTestPlanFull(update_plan_return="updated")
        plan._update_plan_return = "updated"  # override to str
        # Patch get_vplan to return str (simulating exotic endpoint)
        plan.update_plan = lambda post_data, headers=None: "updated"  # type: ignore
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.update_plan({}) == {"result": "updated"}

    def test_update_plan_bulk_returns_dict(self):
        plan = FakeTestPlanFull(update_bulk_return={"updated": 3})
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.update_plan_bulk({}) == {"updated": 3}

    def test_update_plan_section_returns_dict(self):
        plan = FakeTestPlanFull(update_section_return={"result": "section updated"})
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.update_plan_section({}) == {"result": "section updated"}

    def test_update_plan_reference_returns_dict(self):
        plan = FakeTestPlanFull(update_reference_return={"result": "ref updated"})
        fake = _make_vamp_full(test_plan=plan)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.update_plan_reference({}) == {"result": "ref updated"}


# ---------------------------------------------------------------------------
# TestVmanagerClientVsifScopedMethods
# ---------------------------------------------------------------------------


class TestVmanagerClientVsifScopedMethods:
    def test_list_vsif_groups_for_session_normalizes(self):
        rows = [{"id": 1, "name": "g1"}]
        fake_grp = FakeVsifGroupsScoped(list_return=rows)
        fake = _make_vamp_full(vsif_groups=fake_grp)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)
        filt = {"attName": "name", "attValue": "weekly_a0"}

        result = client.list_vsif_groups_for_session(filt)

        assert result == {"vsif_groups": rows, "count": 1}
        assert fake_grp.last_parent_sessions_filter == filt

    def test_list_vsif_groups_for_session_empty(self):
        fake_grp = FakeVsifGroupsScoped(list_return=[])
        fake = _make_vamp_full(vsif_groups=fake_grp)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.list_vsif_groups_for_session({}) == {"vsif_groups": [], "count": 0}

    def test_list_vsif_groups_for_group_normalizes(self):
        rows = [{"id": 2, "name": "g2"}]
        fake_grp = FakeVsifGroupsScoped(list_return=rows)
        fake = _make_vamp_full(vsif_groups=fake_grp)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)
        filt = {"attName": "id", "attValue": 10}

        result = client.list_vsif_groups_for_group(filt)

        assert result == {"vsif_groups": rows, "count": 1}
        assert fake_grp.last_parent_groups_filter == filt

    def test_list_vsif_tests_for_session_normalizes(self):
        rows = [{"id": 5, "name": "TC_boot"}]
        fake_tst = FakeVsifTestsScoped(list_return=rows)
        fake = _make_vamp_full(vsif_tests=fake_tst)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)
        filt = {"attName": "name", "attValue": "weekly_a0"}

        result = client.list_vsif_tests_for_session(filt)

        assert result == {"vsif_tests": rows, "count": 1}
        assert fake_tst.last_parent_sessions_filter == filt

    def test_list_vsif_tests_for_group_normalizes(self):
        rows = [{"id": 6, "name": "TC_init"}]
        fake_tst = FakeVsifTestsScoped(list_return=rows)
        fake = _make_vamp_full(vsif_tests=fake_tst)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)
        filt = {"attName": "id", "attValue": 2}

        result = client.list_vsif_tests_for_group(filt)

        assert result == {"vsif_tests": rows, "count": 1}
        assert fake_tst.last_parent_groups_filter == filt


# ---------------------------------------------------------------------------
# TestVmanagerClientVsifConfigByName
# ---------------------------------------------------------------------------


class TestVmanagerClientVsifConfigByName:
    def test_list_vsif_configs_by_name_converts_objects(self):
        obj = _VsifConfigResult()
        fake_vsif = FakeVsifConfigWithName(list_return=[obj])
        fake = _make_vamp_full(vsif=fake_vsif)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_vsif_configs_by_name("mc_*")

        assert result["count"] == 1
        assert result["vsif_configs"][0]["name"] == "mc_config"
        assert fake_vsif.last_name == "mc_*"

    def test_list_vsif_configs_by_name_empty(self):
        fake_vsif = FakeVsifConfigWithName(list_return=[])
        fake = _make_vamp_full(vsif=fake_vsif)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.list_vsif_configs_by_name("no_match") == {"vsif_configs": [], "count": 0}

    def test_list_vsif_configs_by_name_passes_page_length(self):
        fake_vsif = FakeVsifConfigWithName(list_return=[])
        fake = _make_vamp_full(vsif=fake_vsif)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        client.list_vsif_configs_by_name("mc_*", page_length=500)

        assert fake_vsif.last_page_length == 500


# ---------------------------------------------------------------------------
# TestVmanagerClientRunFailureHelpers
# ---------------------------------------------------------------------------


class TestVmanagerClientRunFailureHelpers:
    def test_list_run_failures_for_team_returns_serialized_rows(self):
        results = [_FakeRfcResult(result_id=1, team="ip.mc")]
        fake_rfc = FakeRunFailureClusterHelpers(for_team=results)
        fake = _make_vamp_full(run_failure_cluster=fake_rfc)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_run_failures_for_team("ip.mc", days=7)

        assert result["count"] == 1
        assert result["run_failure_clusters"][0]["team"] == "ip.mc"
        assert fake_rfc.last_team == "ip.mc"
        assert fake_rfc.last_days == 7

    def test_list_run_failures_for_team_empty(self):
        fake_rfc = FakeRunFailureClusterHelpers(for_team=[])
        fake = _make_vamp_full(run_failure_cluster=fake_rfc)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.list_run_failures_for_team("ip.mc") == {"run_failure_clusters": [], "count": 0}

    def test_list_run_failures_in_datetime_returns_rows(self):
        results = [_FakeRfcResult(result_id=2)]
        fake_rfc = FakeRunFailureClusterHelpers(in_datetime=results)
        fake = _make_vamp_full(run_failure_cluster=fake_rfc)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_run_failures_in_datetime(days=1, hours=2, minutes=30)

        assert result["count"] == 1
        assert fake_rfc.last_datetime_kwargs == {"days": 1, "hours": 2, "minutes": 30}

    def test_list_run_failures_needs_rerun_returns_rows(self):
        results = [_FakeRfcResult(result_id=3)]
        fake_rfc = FakeRunFailureClusterHelpers(needs_rerun=results)
        fake = _make_vamp_full(run_failure_cluster=fake_rfc)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_run_failures_needs_rerun()

        assert result["count"] == 1

    def test_list_run_failures_for_result_ids_passes_ids(self):
        results = [_FakeRfcResult(result_id=10), _FakeRfcResult(result_id=11)]
        fake_rfc = FakeRunFailureClusterHelpers(from_ids=results)
        fake = _make_vamp_full(run_failure_cluster=fake_rfc)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.list_run_failures_for_result_ids([10, 11])

        assert result["count"] == 2
        assert fake_rfc.last_ids == [10, 11]


# ---------------------------------------------------------------------------
# TestVmanagerClientFailureClustersForRuns
# ---------------------------------------------------------------------------


class TestVmanagerClientFailureClustersForRuns:
    def test_get_failure_clusters_for_runs_returns_serialized(self):
        objs = [_FakeFcResultObj(fc_id=7, name="bkt_x")]
        fake_fc = FakeFailureClusterWithAssoc(assoc_return=objs)
        fake = _make_vamp_full(failure_cluster=fake_fc)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.get_failure_clusters_for_runs([1, 2, 3])

        assert result["count"] == 1
        assert result["failure_clusters"][0]["name"] == "bkt_x"
        assert result["failure_clusters"][0]["id"] == 7

    def test_get_failure_clusters_for_runs_empty(self):
        fake_fc = FakeFailureClusterWithAssoc(assoc_return=[])
        fake = _make_vamp_full(failure_cluster=fake_fc)
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        assert client.get_failure_clusters_for_runs([]) == {"failure_clusters": [], "count": 0}


# ---------------------------------------------------------------------------
# Tool-layer tests — new plan tools
# ---------------------------------------------------------------------------


class TestNewPlanTools:
    def test_plan_list_sub_elements_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass

            def list_plan_sub_elements(self, post_data):
                return {"sub_elements": [{"id": "e1", "name": "FeatureA"}], "count": 1}

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)
        result = asyncio.run(
            mock_mcp.tools["vamp_plan_list_sub_elements"](
                post_data_json='{"sticky-context": {"vplan": "vp_a", "db-vplan": true}}'
            )
        )
        assert json.loads(result) == {
            "sub_elements": [{"id": "e1", "name": "FeatureA"}],
            "count": 1,
        }

    def test_plan_list_sub_elements_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(
            mock_mcp.tools["vamp_plan_list_sub_elements"](post_data_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_plan_list_vplans_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_vplans(self, post_data): return {"vplans": [{"name": "vp_a"}], "count": 1}

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_plan_list_vplans"](post_data_json="{}"))
        payload = json.loads(result)
        assert payload["count"] == 1
        assert payload["vplans"][0]["name"] == "vp_a"

    def test_plan_list_vplans_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(mock_mcp.tools["vamp_plan_list_vplans"](post_data_json="bad"))
        assert result.startswith("ERROR: invalid JSON")

    def test_plan_get_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def get_vplan(self, post_data): return {"name": "my_plan", "id": 1}

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)
        result = asyncio.run(mock_mcp.tools["vamp_plan_get"](post_data_json='{"sticky-context": {}}'))
        assert json.loads(result)["id"] == 1

    def test_plan_get_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(mock_mcp.tools["vamp_plan_get"](post_data_json="bad"))
        assert result.startswith("ERROR: invalid JSON")

    def test_plan_get_rich_text_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def get_plan_rich_text(self, post_data): return {"content": "hello", "checksum": "x"}

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)
        result = asyncio.run(mock_mcp.tools["vamp_plan_get_rich_text"](post_data_json="{}"))
        assert json.loads(result)["checksum"] == "x"

    def test_plan_get_rich_text_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(mock_mcp.tools["vamp_plan_get_rich_text"](post_data_json="bad"))
        assert result.startswith("ERROR: invalid JSON")

    def test_plan_add_section_returns_id(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def add_plan_section(self, post_data): return {"id": 55}

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)
        result = asyncio.run(mock_mcp.tools["vamp_plan_add_section"](post_data_json='{"name": "s1"}'))
        assert json.loads(result) == {"id": 55}

    def test_plan_add_section_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(mock_mcp.tools["vamp_plan_add_section"](post_data_json="bad"))
        assert result.startswith("ERROR: invalid JSON")

    def test_plan_add_reference_returns_id(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def add_plan_reference(self, post_data): return {"id": 66}

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)
        result = asyncio.run(mock_mcp.tools["vamp_plan_add_reference"](post_data_json='{}'))
        assert json.loads(result) == {"id": 66}

    def test_plan_add_reference_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(mock_mcp.tools["vamp_plan_add_reference"](post_data_json="bad"))
        assert result.startswith("ERROR: invalid JSON")

    def test_plan_add_metrics_port_returns_id(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def add_plan_metrics_port(self, post_data): return {"id": 77}

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)
        result = asyncio.run(mock_mcp.tools["vamp_plan_add_metrics_port"](post_data_json='{}'))
        assert json.loads(result) == {"id": 77}

    def test_plan_add_metrics_port_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(mock_mcp.tools["vamp_plan_add_metrics_port"](post_data_json="bad"))
        assert result.startswith("ERROR: invalid JSON")

    def test_plan_update_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def update_plan(self, post_data): return {"status": "ok"}

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)
        result = asyncio.run(mock_mcp.tools["vamp_plan_update"](post_data_json='{}'))
        assert json.loads(result) == {"status": "ok"}

    def test_plan_update_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(mock_mcp.tools["vamp_plan_update"](post_data_json="bad"))
        assert result.startswith("ERROR: invalid JSON")

    def test_plan_update_bulk_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def update_plan_bulk(self, post_data): return {"updated": 3}

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)
        result = asyncio.run(mock_mcp.tools["vamp_plan_update_bulk"](post_data_json='{}'))
        assert json.loads(result) == {"updated": 3}

    def test_plan_update_bulk_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(mock_mcp.tools["vamp_plan_update_bulk"](post_data_json="bad"))
        assert result.startswith("ERROR: invalid JSON")

    def test_plan_update_section_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def update_plan_section(self, post_data): return {"result": "section ok"}

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)
        result = asyncio.run(mock_mcp.tools["vamp_plan_update_section"](post_data_json='{}'))
        assert json.loads(result) == {"result": "section ok"}

    def test_plan_update_section_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(mock_mcp.tools["vamp_plan_update_section"](post_data_json="bad"))
        assert result.startswith("ERROR: invalid JSON")

    def test_plan_update_reference_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def update_plan_reference(self, post_data): return {"result": "ref ok"}

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)
        result = asyncio.run(mock_mcp.tools["vamp_plan_update_reference"](post_data_json='{}'))
        assert json.loads(result) == {"result": "ref ok"}

    def test_plan_update_reference_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(mock_mcp.tools["vamp_plan_update_reference"](post_data_json="bad"))
        assert result.startswith("ERROR: invalid JSON")


# ---------------------------------------------------------------------------
# Tool-layer tests — vsif_groups scoped list tools
# ---------------------------------------------------------------------------


class TestVsifGroupsScopedTools:
    def test_list_for_session_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_vsif_groups_for_session(self, filt, extra):
                return {"vsif_groups": [{"id": 1}], "count": 1}

        monkeypatch.setattr("tools.vmanager._vsif_groups.VmanagerClient", FakeClient)
        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_groups_list_for_session"](
                sessions_filter_json='{"attName": "name", "attValue": "s1"}'
            )
        )
        assert json.loads(result)["count"] == 1

    def test_list_for_session_rejects_bad_filter_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_groups_list_for_session"](
                sessions_filter_json="bad"
            )
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_list_for_group_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_vsif_groups_for_group(self, filt, extra):
                return {"vsif_groups": [{"id": 2}], "count": 1}

        monkeypatch.setattr("tools.vmanager._vsif_groups.VmanagerClient", FakeClient)
        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_groups_list_for_group"](
                groups_filter_json='{"attName": "id", "attValue": 10}'
            )
        )
        assert json.loads(result)["count"] == 1

    def test_list_for_group_rejects_bad_filter_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_groups_list_for_group"](groups_filter_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")


# ---------------------------------------------------------------------------
# Tool-layer tests — vsif_tests scoped list tools
# ---------------------------------------------------------------------------


class TestVsifTestsScopedTools:
    def test_list_for_session_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_vsif_tests_for_session(self, filt, extra):
                return {"vsif_tests": [{"id": 5}], "count": 1}

        monkeypatch.setattr("tools.vmanager._vsif_tests.VmanagerClient", FakeClient)
        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_tests_list_for_session"](
                sessions_filter_json='{"attName": "name", "attValue": "s1"}'
            )
        )
        assert json.loads(result)["count"] == 1

    def test_list_for_session_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_tests_list_for_session"](sessions_filter_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_list_for_group_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_vsif_tests_for_group(self, filt, extra):
                return {"vsif_tests": [{"id": 6}], "count": 1}

        monkeypatch.setattr("tools.vmanager._vsif_tests.VmanagerClient", FakeClient)
        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_tests_list_for_group"](
                groups_filter_json='{"attName": "id", "attValue": 2}'
            )
        )
        assert json.loads(result)["count"] == 1

    def test_list_for_group_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(
            mock_mcp.tools["vamp_vsif_tests_list_for_group"](groups_filter_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")


# ---------------------------------------------------------------------------
# Tool-layer tests — vsif_config list_by_name tool
# ---------------------------------------------------------------------------


class TestVsifConfigListByNameTool:
    def test_list_by_name_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_vsif_configs_by_name(self, name, page_length=1000):
                assert name == "mc_*"
                return {"vsif_configs": [{"name": "mc_config"}], "count": 1}

        monkeypatch.setattr("tools.vmanager._vsif_config.VmanagerClient", FakeClient)
        result = asyncio.run(mock_mcp.tools["vamp_vsif_config_list_by_name"](name="mc_*"))
        payload = json.loads(result)
        assert payload["count"] == 1
        assert payload["vsif_configs"][0]["name"] == "mc_config"

    def test_list_by_name_passes_page_length(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        captured = {}

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_vsif_configs_by_name(self, name, page_length=1000):
                captured["page_length"] = page_length
                return {"vsif_configs": [], "count": 0}

        monkeypatch.setattr("tools.vmanager._vsif_config.VmanagerClient", FakeClient)
        asyncio.run(mock_mcp.tools["vamp_vsif_config_list_by_name"](name="mc_*", page_length=250))
        assert captured["page_length"] == 250


# ---------------------------------------------------------------------------
# Tool-layer tests — run_failure_cluster helper tools
# ---------------------------------------------------------------------------


class TestRunFailureHelperTools:
    def test_run_failures_for_team_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_run_failures_for_team(self, team, days):
                assert team == "ip.mc"
                assert days == 7
                return {"run_failure_clusters": [{"team": "ip.mc"}], "count": 1}

        monkeypatch.setattr("tools.vmanager._run_failure_clusters.VmanagerClient", FakeClient)
        result = asyncio.run(
            mock_mcp.tools["vamp_run_failures_for_team"](team="ip.mc", days=7)
        )
        assert json.loads(result)["count"] == 1

    def test_run_failures_in_datetime_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_run_failures_in_datetime(self, days, hours, minutes):
                return {"run_failure_clusters": [], "count": 0}

        monkeypatch.setattr("tools.vmanager._run_failure_clusters.VmanagerClient", FakeClient)
        result = asyncio.run(
            mock_mcp.tools["vamp_run_failures_in_datetime"](days=1, hours=2, minutes=30)
        )
        assert json.loads(result) == {"run_failure_clusters": [], "count": 0}

    def test_run_failures_needs_rerun_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_run_failures_needs_rerun(self):
                return {"run_failure_clusters": [{"id": 9}], "count": 1}

        monkeypatch.setattr("tools.vmanager._run_failure_clusters.VmanagerClient", FakeClient)
        result = asyncio.run(mock_mcp.tools["vamp_run_failures_needs_rerun"]())
        assert json.loads(result)["count"] == 1

    def test_run_failures_for_result_ids_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def list_run_failures_for_result_ids(self, ids):
                return {"run_failure_clusters": [{"id": i} for i in ids], "count": len(ids)}

        monkeypatch.setattr("tools.vmanager._run_failure_clusters.VmanagerClient", FakeClient)
        result = asyncio.run(
            mock_mcp.tools["vamp_run_failures_for_result_ids"](result_ids_json="[10, 11, 12]")
        )
        payload = json.loads(result)
        assert payload["count"] == 3

    def test_run_failures_for_result_ids_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(
            mock_mcp.tools["vamp_run_failures_for_result_ids"](result_ids_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_run_failures_for_result_ids_rejects_non_list(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(
            mock_mcp.tools["vamp_run_failures_for_result_ids"](result_ids_json='{"id": 1}')
        )
        assert result.startswith("ERROR:")


# ---------------------------------------------------------------------------
# Tool-layer tests — failure_clusters_for_runs tool
# ---------------------------------------------------------------------------


class TestFailureClustersForRunsTool:
    def test_failure_clusters_for_runs_returns_json(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass
            def get_failure_clusters_for_runs(self, run_ids):
                assert run_ids == [1, 2]
                return {"failure_clusters": [{"id": 99, "name": "bkt"}], "count": 1}

        monkeypatch.setattr("tools.vmanager._failure_clusters.VmanagerClient", FakeClient)
        result = asyncio.run(
            mock_mcp.tools["vamp_failure_clusters_for_runs"](run_ids_json="[1, 2]")
        )
        payload = json.loads(result)
        assert payload["count"] == 1
        assert payload["failure_clusters"][0]["name"] == "bkt"

    def test_failure_clusters_for_runs_rejects_bad_json(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(
            mock_mcp.tools["vamp_failure_clusters_for_runs"](run_ids_json="bad")
        )
        assert result.startswith("ERROR: invalid JSON")

    def test_failure_clusters_for_runs_rejects_non_list(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]
        result = asyncio.run(
            mock_mcp.tools["vamp_failure_clusters_for_runs"](run_ids_json='{"id": 1}')
        )
        assert result.startswith("ERROR:")


# ---------------------------------------------------------------------------
# count_sessions fallback — vsif_sessions has no native count() in vamp
# ---------------------------------------------------------------------------


class TestVmanagerClientCountSessionsFallback:
    def test_count_sessions_uses_fallback_when_no_count_method(self):
        """count_sessions must fall back to listing+counting when count() absent."""

        class NoCountSessions:
            def list(self, post_data):
                return [{"id": 1, "name": "sess_a"}, {"id": 2, "name": "sess_b"}]

        fake = FakeVampFull(vsif_sessions=NoCountSessions())
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.count_sessions({})

        assert result == {"count": 2}

    def test_count_sessions_uses_native_count_when_available(self):
        """count_sessions uses vsif_sessions.count() if the method exists."""

        class WithCountSessions:
            def list(self, post_data):
                return []

            def count(self, post_data):
                return 42

        fake = FakeVampFull(vsif_sessions=WithCountSessions())
        client = VmanagerClient(repo_root="/tmp", vamp_factory=lambda: fake)

        result = client.count_sessions({})

        assert result == {"count": 42}


# ---------------------------------------------------------------------------
# TestPlanFind — vamp_plan_find tool and discovery helper
# ---------------------------------------------------------------------------


class TestPlanFind:
    """Tests for the vamp_plan_find discovery tool."""

    def test_plan_find_rejects_empty_fragment(self):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        result = asyncio.run(mock_mcp.tools["vamp_plan_find"](name_fragment="   "))

        assert result == "ERROR: name_fragment must not be empty or whitespace"

    def test_plan_find_returns_matching_by_substring(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass

            def list_vplans(self, post_data):
                return {
                    "vplans": [
                        {"name": "memss_regression_ttl"},
                        {"name": "nvl_regression_plan"},
                        {"name": "memss_feature_validation"},
                    ],
                    "count": 3,
                }

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_plan_find"](name_fragment="memss"))
        payload = json.loads(result)
        assert payload["count"] == 2
        assert payload["total_checked"] == 3
        assert payload["fragment"] == "memss"
        names = [vp["name"] for vp in payload["vplans"]]
        assert "memss_regression_ttl" in names
        assert "memss_feature_validation" in names
        assert "nvl_regression_plan" not in names

    def test_plan_find_case_insensitive_by_default(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass

            def list_vplans(self, post_data):
                return {"vplans": [{"name": "MEMSS_Plan"}, {"name": "nvl_plan"}], "count": 2}

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_plan_find"](name_fragment="memss"))
        payload = json.loads(result)
        assert payload["count"] == 1
        assert payload["vplans"][0]["name"] == "MEMSS_Plan"

    def test_plan_find_case_sensitive_flag(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass

            def list_vplans(self, post_data):
                return {"vplans": [{"name": "MEMSS_Plan"}, {"name": "memss_plan"}], "count": 2}

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)

        result = asyncio.run(
            mock_mcp.tools["vamp_plan_find"](name_fragment="memss", case_sensitive=True)
        )
        payload = json.loads(result)
        assert payload["count"] == 1
        assert payload["vplans"][0]["name"] == "memss_plan"

    def test_plan_find_no_match_returns_empty(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass

            def list_vplans(self, post_data):
                return {"vplans": [{"name": "nvl_plan"}], "count": 1}

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_plan_find"](name_fragment="memss"))
        payload = json.loads(result)
        assert payload["count"] == 0
        assert payload["total_checked"] == 1
        assert payload["vplans"] == []

    def test_plan_find_backend_error_returns_error_string(self, monkeypatch: pytest.MonkeyPatch):
        mock_mcp = MockFastMCP("test-mcp")
        register_vmanager_tools(mock_mcp, "/tmp/repo")  # pyright: ignore[reportArgumentType]

        class FakeClient:
            def __init__(self, repo_root): pass

            def list_vplans(self, post_data):
                raise RuntimeError("backend unavailable")

        monkeypatch.setattr("tools.vmanager._plan.VmanagerClient", FakeClient)

        result = asyncio.run(mock_mcp.tools["vamp_plan_find"](name_fragment="x"))
        assert result.startswith("ERROR:")



