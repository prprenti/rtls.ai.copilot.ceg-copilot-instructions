from __future__ import annotations

import pytest

from ddgmcp.standard_runs_query import (
    build_standard_runs_filter,
    build_standard_runs_list_request,
    infer_repo_family,
    resolve_standard_runs_query_profile,
)


class TestInferRepoFamily:
    def test_infers_ttl(self) -> None:
        repo_root = "/nfs/site/disks/example/ttl/project"
        assert infer_repo_family(repo_root) == "TTL"

    def test_infers_rzl(self) -> None:
        repo_root = "/nfs/site/disks/example/rzl/project"
        assert infer_repo_family(repo_root) == "RZL"

    def test_infers_nvl(self) -> None:
        repo_root = "/nfs/site/disks/example/nvl/project"
        assert infer_repo_family(repo_root) == "NVL"

    def test_returns_none_when_unknown(self) -> None:
        assert infer_repo_family("/tmp/work") is None


class TestRepoFamilySharedNvlDatabase:
    """Document the shared-backend deployment fact.

    TTL, RZL, and NVL repos all connect to the same ``nvl`` vManager
    database in this environment.  infer_repo_family returns different labels
    for workspace-tagging purposes, but the label does NOT select a separate
    vManager server — the vamp client URL is configured independently.
    """

    def test_ttl_label_is_ttl_not_nvl(self) -> None:
        # Label reflects the workspace family, not the backend DB name.
        # The nvl vManager database is the actual backend for TTL workspaces.
        assert infer_repo_family("/nfs/site/disks/example/ttl/project") == "TTL"

    def test_rzl_label_is_rzl_not_nvl(self) -> None:
        # Label reflects the workspace family, not the backend DB name.
        # The nvl vManager database is the actual backend for RZL workspaces.
        assert infer_repo_family("/nfs/site/disks/example/rzl/project") == "RZL"

    def test_nvl_label_is_nvl(self) -> None:
        assert infer_repo_family("/nfs/site/disks/example/nvl/project") == "NVL"

    def test_all_three_families_have_non_none_label(self) -> None:
        # Confirms none of the three families falls through to unknown.
        for path in (
            "/nfs/site/disks/example/ttl/project",
            "/nfs/site/disks/example/rzl/project",
            "/nfs/site/disks/example/nvl/project",
        ):
            assert infer_repo_family(path) is not None, (
                f"Expected a label for path '{path}'; shared nvl database requires all three to be recognised"
            )


class TestResolveStandardRunsQueryProfile:
    def test_require_dut_flag_enforces_dut(self) -> None:
        with pytest.raises(ValueError, match="dut is required"):
            resolve_standard_runs_query_profile(
                team="hub.memss",
                steppings=["ttl-a0"],
                require_dut=True,
            )

    def test_single_dut_team_can_omit_dut(self) -> None:
        profile = resolve_standard_runs_query_profile(team="hub.ipuss", steppings=["ttl-a0"])
        assert profile.require_dut is False
        assert profile.dut_values == ()

    def test_normalizes_string_inputs(self) -> None:
        profile = resolve_standard_runs_query_profile(
            team="hub.memss",
            dut="memss",
            steppings="ttl-a0",
            repo_root="/nfs/site/disks/example/ttl/project",
        )
        assert profile.repo_family == "TTL"
        assert profile.team_values == ("hub.memss",)
        assert profile.dut_values == ("memss",)
        assert profile.stepping_values == ("ttl-a0",)


class TestBuildStandardRunsFilter:
    def test_ttl_memss_filter_matches_expected_shape(self) -> None:
        actual = build_standard_runs_filter(
            team="hub.memss",
            dut="memss",
            steppings=["ttl-a0"],
            discriminator="c_type",
            require_dut=True,
        )
        assert actual == {
            "c_type": ".ChainedFilter",
            "condition": "AND",
            "chain": [
                {
                    "c_type": ".InFilter",
                    "attName": "status",
                    "operand": "IN",
                    "values": ["failed"],
                },
                {
                    "c_type": ".InFilter",
                    "attName": "i_team",
                    "operand": "IN",
                    "values": ["hub.memss"],
                },
                {
                    "c_type": ".InFilter",
                    "attName": "i_debug_status",
                    "operand": "IN",
                    "values": ["debugged_keep", "new", "wip"],
                },
                {
                    "c_type": ".InFilter",
                    "attName": "i_dut",
                    "operand": "IN",
                    "values": ["memss"],
                },
                {
                    "c_type": ".InFilter",
                    "attName": "i_steps",
                    "operand": "IN",
                    "values": ["ttl-a0"],
                },
                {
                    "c_type": ".AttValueFilter",
                    "attName": "i_for_indicators",
                    "operand": "EQUALS",
                    "attValue": True,
                },
            ],
        }

    def test_ip_team_omits_dut_when_not_provided(self) -> None:
        actual = build_standard_runs_filter(
            team="hub.ipuss",
            steppings=["ttl-a0"],
            discriminator="c_type",
        )
        assert [item["attName"] for item in actual["chain"]] == [
            "status",
            "i_team",
            "i_debug_status",
            "i_steps",
            "i_for_indicators",
        ]

    def test_supports_vamp_style_discriminator(self) -> None:
        actual = build_standard_runs_filter(
            team="hub.ipuss",
            steppings=["ttl-a0"],
            discriminator="@c",
        )
        assert actual["@c"] == ".ChainedFilter"
        assert actual["chain"][0]["@c"] == ".InFilter"

    def test_skip_steppings_omits_i_steps_filter(self) -> None:
        actual = build_standard_runs_filter(
            team="hub.memss",
            dut="memss",
            steppings=["ttl-a0"],
            discriminator="@c",
            require_dut=True,
            skip_steppings=True,
        )
        att_names = [item["attName"] for item in actual["chain"]]
        assert "i_steps" not in att_names

    def test_skip_steppings_false_includes_i_steps_filter(self) -> None:
        actual = build_standard_runs_filter(
            team="hub.memss",
            dut="memss",
            steppings=["ttl-a0"],
            discriminator="@c",
            require_dut=True,
            skip_steppings=False,
        )
        att_names = [item["attName"] for item in actual["chain"]]
        assert "i_steps" in att_names



class TestBuildStandardRunsListRequest:
    def test_builds_request_with_default_paging(self) -> None:
        actual = build_standard_runs_list_request(
            team="hub.memss",
            dut="memss",
            steppings=["ttl-a0"],
            require_dut=True,
        )
        assert actual["pageLength"] == 100
        assert actual["pageOffset"] == 0
        assert actual["settings"] == {"stream-mode": False}

    def test_skip_steppings_propagates_to_filter(self) -> None:
        actual = build_standard_runs_list_request(
            team="hub.memss",
            dut="memss",
            steppings=["ttl-a0"],
            require_dut=True,
            skip_steppings=True,
        )
        att_names = [item["attName"] for item in actual["filter"]["chain"]]
        assert "i_steps" not in att_names
        assert actual["filter"]["condition"] == "AND"
