"""Focused readiness tests for the package-based vManager runtime contract."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestModuleImports:
    def test_utils_exports_normalize_single(self) -> None:
        from backends.vmanager._utils import _DictFilter, _extract_rows, _extract_group_value, _normalize_single

        assert callable(_extract_rows)
        assert callable(_extract_group_value)
        assert callable(_normalize_single)
        assert _DictFilter({"k": "v"}).get() == {"k": "v"}

    def test_vmanager_modules_import(self) -> None:
        modules = [
            "standard_runs_query",
            "backends.vmanager",
            "backends.vmanager.client",
            "tools.vmanager",
            "tools.vmanager._runs",
            "tools.vmanager._failure_clusters",
            "tools.vmanager._vsif_groups",
            "tools.vmanager._vsif_sessions",
            "tools.vmanager._plan",
        ]
        for module_name in modules:
            assert importlib.import_module(module_name) is not None


class TestCandidateVampSysPaths:
    def test_empty_when_no_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from backends.vmanager.client import _candidate_vamp_sys_paths

        monkeypatch.delenv("CEGMCP_VAMP_PATH", raising=False)
        assert _candidate_vamp_sys_paths(tmp_path) == []

    def test_parent_of_vamp_dir_is_accepted(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from backends.vmanager.client import _candidate_vamp_sys_paths

        vamp_parent = tmp_path / "custom"
        (vamp_parent / "vamp").mkdir(parents=True)
        (vamp_parent / "vamp" / "__init__.py").write_text("")
        monkeypatch.setenv("CEGMCP_VAMP_PATH", str(vamp_parent))
        assert _candidate_vamp_sys_paths(tmp_path) == [str(vamp_parent)]

    def test_vamp_dir_itself_is_accepted(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from backends.vmanager.client import _candidate_vamp_sys_paths

        vamp_dir = tmp_path / "vamp"
        vamp_dir.mkdir()
        (vamp_dir / "__init__.py").write_text("")
        monkeypatch.setenv("CEGMCP_VAMP_PATH", str(vamp_dir))
        assert _candidate_vamp_sys_paths(tmp_path) == [str(tmp_path)]


class TestBackendUnavailable:
    def test_client_raises_when_vamp_cannot_load(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from backends.vmanager.client import VmanagerBackendUnavailable, VmanagerClient

        monkeypatch.delenv("CEGMCP_VAMP_PATH", raising=False)
        with patch(
            "backends.vmanager.client._load_vamp_class",
            side_effect=VmanagerBackendUnavailable("absent"),
        ):
            with pytest.raises(VmanagerBackendUnavailable, match="absent"):
                VmanagerClient(repo_root=str(tmp_path))


class TestPackageReadiness:
    def test_vamp_is_importable(self) -> None:
        import vamp

        assert hasattr(vamp, "Vamp")
        assert callable(vamp.Vamp)


class TestStandardRunsQuery:
    def test_request_uses_live_vmanager_discriminator(self, tmp_path: Path) -> None:
        from backends.vmanager.client import VmanagerClient

        mock_vamp = MagicMock()
        mock_vamp.test_run.list.return_value = []
        mock_vamp.failure_cluster.list.return_value = []
        mock_vamp.vsif_sessions.list.return_value = []
        mock_vamp.test_plan.list.return_value = []

        client = VmanagerClient(repo_root=str(tmp_path), vamp_factory=lambda: mock_vamp)
        result = client.query_standard_runs(
            team=("hub.memss.hub",),
            steppings=("a0",),
            dut=("mc",),
        )

        request = result["request"]
        steps_filter = next(entry for entry in request["filter"]["chain"] if entry["attName"] == "i_steps")
        assert request["filter"]["@c"] == ".ChainedFilter"
        assert steps_filter["operand"] == "IN"


class TestNormalizeSingle:
    def test_dict_passthrough(self) -> None:
        from backends.vmanager._utils import _normalize_single

        payload = {"id": 1, "name": "x"}
        assert _normalize_single(payload) == payload

    def test_object_is_json_safe(self) -> None:
        from backends.vmanager._utils import _normalize_single

        class Obj:
            def __init__(self) -> None:
                self.id = 5
                self.name = "group_a"

        assert json.loads(json.dumps(_normalize_single(Obj()))) == {"id": 5, "name": "group_a"}

    def test_object_with_nested_non_primitive_values_is_json_safe(self, tmp_path: Path) -> None:
        from backends.vmanager._utils import _normalize_single

        class Nested:
            def __init__(self) -> None:
                self.location = tmp_path / "artifact"

        class Obj:
            def __init__(self) -> None:
                self.id = 7
                self.tags = {"kind": "session", "paths": [tmp_path / "a", tmp_path / "b"]}
                self.nested = Nested()

        normalized = _normalize_single(Obj())
        assert json.loads(json.dumps(normalized)) == {
            "id": 7,
            "tags": {
                "kind": "session",
                "paths": [str(tmp_path / "a"), str(tmp_path / "b")],
            },
            "nested": {"location": str(tmp_path / "artifact")},
        }


class TestVsifGetNormalization:
    def _make_client(self, mock_vamp: MagicMock):
        from backends.vmanager.client import VmanagerClient

        return VmanagerClient(repo_root="/tmp", vamp_factory=lambda: mock_vamp)

    def test_vsif_group_get_normalizes_backend_object(self) -> None:
        class FakeGroup:
            def __init__(self) -> None:
                self.id = 42
                self.name = "weekly_a0"

        mock_vamp = MagicMock()
        mock_vamp.vsif_groups.get.return_value = FakeGroup()

        client = self._make_client(mock_vamp)
        result = client.get_vsif_group(42)
        assert json.loads(json.dumps(result)) == {"id": 42, "name": "weekly_a0"}

    def test_vsif_session_create_returns_id(self) -> None:
        mock_vamp = MagicMock()
        mock_vamp.vsif_sessions.create_with_permissions.return_value = 88

        client = self._make_client(mock_vamp)
        assert client.create_vsif_session({"name": "weekly_a0"}) == {"id": 88}