"""Domain-specific VmanagerClient methods — new vamp surface exposed in this PR.

The _VmanagerDomainMixin adds methods for vsif, vsif_groups, vsif_tests,
vsif_hierarchy, vsif_sessions (extras), runtime sessions, run_failure_cluster,
and additional run/failure-cluster mutations.  VmanagerClient inherits from
this mixin to keep the core client module under 600 lines.
"""

from __future__ import annotations

from typing import Any

from ._utils import _DictFilter, _extract_rows, _normalize_single, group_run_failure_clusters, apply_default_projection

# Default slim projection for plan sub-element list queries.
# Covers the full AI-facing column set: identity, structure, Intel custom
# planning attributes, progress, and navigation.  Override by including a
# "projection" key in post_data (including None or []) to get a different
# field set.
PLAN_SUB_ELEMENTS_SLIM_PROJECTION: list[str] = [
    # Identity & navigation
    "element_id",
    "name",
    "full_path",
    "numbering",
    # Structural type (e.g. "Section")
    "vplan_element_kind",
    # Sub Type (e.g. "test.test", "checker")
    "i_type",
    # Intel custom planning attributes
    "i_required_by_milestone",
    "i_steps",
    "i_steps_completed",
    "i_val_level",
    "i_priority",
    "i_reason",
    "i_team",
    "owner",
    "i_is_reviewed",
    "i_plan_status",
    "i_tag",
    "spec_text",
    "i_pkg_impact",
    "i_project",
    # Progress (functional coverage grade as percent)
    "overall_grade",
]

# Default slim projection for VSIF group list queries.
# Covers identity, full hierarchical name, ownership, classification, and
# parent session reference for AI-driven composition and navigation.
# Pass ``"projection"`` in post_data (including None or []) to override.
VSIF_GROUP_SLIM_PROJECTION: list[str] = [
    # Identity
    "id",
    "name",
    # Hierarchy / navigation
    "full_name",
    # Ownership
    "owner",
    "i_team",
    # Classification
    "i_steps",
    # Parent session reference
    "session_id",
]

# Default slim projection for VSIF test list queries.
# Covers identity, execution status, seed, ownership, and parent group/run
# references needed for AI-driven test-level navigation.
# Pass ``"projection"`` in post_data (including None or []) to override.
VSIF_TEST_SLIM_PROJECTION: list[str] = [
    # Identity
    "id",
    "name",
    # Execution status
    "status",
    # Test configuration
    "seed",
    # Ownership
    "owner",
    "i_team",
    # Navigation
    "group_id",
    "run_id",
]

# Default slim projection for VSIF configuration list queries.
# Covers identity, type, ownership, and classification fields for
# AI-driven configuration discovery and navigation.
# Pass ``"projection"`` in post_data (including None or []) to override.
VSIF_CONFIG_SLIM_PROJECTION: list[str] = [
    # Identity
    "id",
    "name",
    # Config type
    "vsif_type",
    # Ownership
    "owner",
    "i_team",
    # Classification
    "i_steps",
    "i_dut",
]


class _VmanagerDomainMixin:
    """Mixin providing the expanded vamp surface methods for VmanagerClient."""

    # -----------------------------------------------------------------------
    # New domain properties
    # -----------------------------------------------------------------------

    @property
    def vsif(self):
        return self._vamp.vsif

    @property
    def vsif_groups(self):
        return self._vamp.vsif_groups

    @property
    def vsif_tests(self):
        return self._vamp.vsif_tests

    @property
    def session(self):
        return self._vamp.session

    @property
    def run_failure_cluster(self):
        return self._vamp.run_failure_cluster

    # -----------------------------------------------------------------------
    # test_run additional methods
    # -----------------------------------------------------------------------

    def update_run(self, post_data: dict) -> dict[str, Any]:
        """Update run attributes (runs/update)."""
        result = self.test_run.update(post_data)
        return {"result": result}

    def associate_run_to_failure_cluster(self, post_data: dict) -> dict[str, Any]:
        """Associate run(s) to a failure cluster (runs/associate-to-failure-cluster)."""
        result = self.test_run.associate_to_failure_cluster(post_data)
        rows = _extract_rows(result)
        return {"rows": rows, "count": len(rows)}

    def dissociate_run_from_failure_cluster(self, post_data: dict) -> dict[str, Any]:
        """Dissociate run(s) from a failure cluster (runs/dissociate-from-failure-cluster)."""
        result = self.test_run.dissociate_from_failure_cluster(post_data)
        rows = _extract_rows(result)
        return {"rows": rows, "count": len(rows)}

    def get_run_rerun_schemes(self) -> dict[str, Any]:
        """Retrieve available rerun schemes (runs/get-rerun-schemes)."""
        result = self.test_run.get_rerun_schemes()
        return {"rerun_schemes": result if isinstance(result, list) else []}

    def get_run_total_count_size(self) -> dict[str, Any]:
        """Retrieve run count and storage-size totals (runs/get-total-count-size)."""
        result = self.test_run.get_total_count_size()
        return result if isinstance(result, dict) else {}

    def extract_run_logs(
        self,
        run_id: int,
        index: int,
        offset: int = 0,
        length: int = 65536,
    ) -> dict[str, Any]:
        """Extract a slice of run logs (runs/extract-logs)."""
        response = self.test_run.extract_logs(
            str(run_id), str(index), str(offset), str(length)
        )
        parser = getattr(getattr(self._vamp, "vapi_requests", None), "parse_response", None)
        parsed = parser(response) if callable(parser) else response
        if isinstance(parsed, (dict, list, str, int, float, bool)) or parsed is None:
            return {"logs": parsed}
        return {"logs": str(parsed)}

    # -----------------------------------------------------------------------
    # failure_cluster additional methods
    # -----------------------------------------------------------------------

    def update_failure_cluster(self, post_data: dict) -> dict[str, Any]:
        """Update failure-cluster attributes (failure-clusters/update)."""
        result = self.failure_cluster.update(post_data)
        return {"result": result}

    def create_failure_cluster(self, post_data: dict) -> dict[str, Any]:
        """Create a failure cluster (failure-clusters/create).  Returns the new cluster ID."""
        new_id = self.failure_cluster.create(post_data)
        return {"id": new_id}

    def delete_failure_clusters(self, filter_dict: dict) -> dict[str, Any]:
        """Delete failure clusters matching a filter dict (failure-clusters/delete)."""
        self.failure_cluster.delete(_DictFilter(filter_dict))
        return {"ok": True}

    # -----------------------------------------------------------------------
    # run_failure_cluster methods
    # -----------------------------------------------------------------------

    def list_run_failure_clusters(self, post_data: dict) -> dict[str, Any]:
        """List run↔failure-cluster associations (run-failure-cluster/list-associated)."""
        rfc = self._vamp.run_failure_cluster
        response = rfc.vapi_requests.post("run-failure-cluster/list-associated", post_data)
        raw = rfc._response_json(response, default=[])
        rows = _extract_rows(raw)
        return {"run_failure_clusters": rows, "count": len(rows)}

    def update_run_failure_cluster_association(self, post_data: dict) -> Any:
        """Update run↔failure-cluster associations (run-failure-cluster/update-associated)."""
        result = self._vamp.run_failure_cluster.update_associated(post_data)
        if isinstance(result, list):
            return {"run_failure_clusters": result, "count": len(result)}
        if isinstance(result, dict):
            return result
        return {"result": result}

    def list_run_failure_clusters_grouped(
        self, post_data: dict, full_detail: bool = False
    ) -> dict[str, Any]:
        """List run↔FC associations grouped by cluster with nested run summaries.

        Calls ``list_run_failure_clusters`` and reshapes the flat rows into
        cluster-centric dicts.  See ``group_run_failure_clusters`` in
        ``_utils.py`` for field-mapping details.

        Args:
            post_data: Same RS filter dict accepted by ``list_run_failure_clusters``.
            full_detail: When ``True``, include extended cluster fields
                (Tag, HSDES_IDS, Unique Tag, Notes).

        Returns:
            Dict with ``"failure_clusters"`` (grouped list) and ``"cluster_count"``.
        """
        base = self.list_run_failure_clusters(post_data)
        rows = base.get("run_failure_clusters", [])
        clusters = group_run_failure_clusters(rows, full_detail=full_detail)
        return {"failure_clusters": clusters, "cluster_count": len(clusters)}

    # -----------------------------------------------------------------------
    # vsif_config methods
    # -----------------------------------------------------------------------

    def list_vsif_configs(self, post_data: dict) -> dict[str, Any]:
        """List VSIF configurations (vsif/configurations/list).

        A slim projection is applied by default so AI callers do not receive
        large per-row payloads.  Pass ``"projection"`` in *post_data*
        (including ``None`` or ``[]``) to override.
        """
        post_data = apply_default_projection(post_data, VSIF_CONFIG_SLIM_PROJECTION)
        results = self.vsif.list(post_data)
        rows = [vars(r) for r in results] if results else []
        return {"vsif_configs": rows, "count": len(rows)}

    def update_vsif_config(self, post_data: dict) -> dict[str, Any]:
        """Update VSIF configuration attributes (vsif/configurations/update)."""
        result = self.vsif.update(post_data)
        return {"result": result}

    # -----------------------------------------------------------------------
    # vsif_groups methods
    # -----------------------------------------------------------------------

    def get_vsif_group(self, group_id: int) -> dict[str, Any]:
        """Fetch a single VSIF group by integer ID (vsif/groups/get)."""
        return _normalize_single(self.vsif_groups.get(group_id))

    def list_vsif_groups(self, post_data: dict) -> dict[str, Any]:
        """List VSIF groups matching an RS specification (vsif/groups/list).

        A slim projection is applied by default so AI callers do not receive
        large per-row payloads.  Pass ``"projection"`` in *post_data*
        (including ``None`` or ``[]``) to override.
        """
        post_data = apply_default_projection(post_data, VSIF_GROUP_SLIM_PROJECTION)
        rows = _extract_rows(self.vsif_groups.list(post_data))
        return {"vsif_groups": rows, "count": len(rows)}

    def create_vsif_group(self, post_data: dict) -> dict[str, Any]:
        """Create a VSIF group (vsif/groups/create).  Returns the new group ID."""
        new_id = self.vsif_groups.create(post_data)
        return {"id": new_id}

    def update_vsif_group(self, post_data: dict) -> dict[str, Any]:
        """Update VSIF group attributes (vsif/groups/update)."""
        result = self.vsif_groups.update(post_data)
        return {"result": result}

    def delete_vsif_groups(self, filter_dict: dict) -> dict[str, Any]:
        """Delete VSIF groups matching a filter dict (vsif/groups/delete)."""
        result = self.vsif_groups.delete(_DictFilter(filter_dict))
        return {"id": result}

    # -----------------------------------------------------------------------
    # vsif_tests methods
    # -----------------------------------------------------------------------

    def get_vsif_test(self, test_id: int) -> dict[str, Any]:
        """Fetch a single VSIF test by integer ID (vsif/tests/get)."""
        return _normalize_single(self.vsif_tests.get(test_id))

    def list_vsif_tests(self, post_data: dict) -> dict[str, Any]:
        """List VSIF tests matching an RS specification (vsif/tests/list).

        A slim projection is applied by default so AI callers do not receive
        large per-row payloads.  Pass ``"projection"`` in *post_data*
        (including ``None`` or ``[]``) to override.
        """
        post_data = apply_default_projection(post_data, VSIF_TEST_SLIM_PROJECTION)
        rows = _extract_rows(self.vsif_tests.list(post_data))
        return {"vsif_tests": rows, "count": len(rows)}

    def create_vsif_test(self, post_data: dict) -> dict[str, Any]:
        """Create a VSIF test (vsif/tests/create).  Returns the new test ID."""
        new_id = self.vsif_tests.create(post_data)
        return {"id": new_id}

    def update_vsif_test(self, post_data: dict) -> dict[str, Any]:
        """Update VSIF test attributes (vsif/tests/update)."""
        result = self.vsif_tests.update(post_data)
        return {"result": result}

    def delete_vsif_tests(self, filter_dict: dict) -> dict[str, Any]:
        """Delete VSIF tests matching a filter dict (vsif/tests/delete)."""
        result = self.vsif_tests.delete(_DictFilter(filter_dict))
        return {"id": result}

    # -----------------------------------------------------------------------
    # vsif_hierarchy methods
    # -----------------------------------------------------------------------

    def get_vsif_hierarchy(self, hierarchy_id: int) -> dict[str, Any]:
        """Fetch a single hierarchy configuration by integer ID (vsif/hierarchy-configurations/get)."""
        return _normalize_single(self.vsif_hierarchy.get(hierarchy_id))

    def list_vsif_hierarchy(
        self, parent_id: int, page_length: int = 100, page_offset: int = 0
    ) -> dict[str, Any]:
        """List hierarchy configurations under a parent entity (vsif/hierarchy-configurations/list)."""
        rows = _extract_rows(self.vsif_hierarchy.list(parent_id, page_length, page_offset))
        return {"vsif_hierarchy": rows, "count": len(rows)}

    def create_vsif_hierarchy(self, post_data: dict) -> dict[str, Any]:
        """Create a hierarchy configuration (vsif/hierarchy-configurations/create)."""
        new_id = self.vsif_hierarchy.create(post_data)
        return {"id": new_id}

    def attach_vsif_hierarchy_groups_to_groups(
        self,
        hierarchy_config_id: int,
        child_groups_filter: dict,
        parent_groups_filter: dict,
    ) -> dict[str, Any]:
        """Attach VSIF groups to VSIF groups (vsif/hierarchy-configurations/attach-groups-to-groups)."""
        self.vsif_hierarchy.attach_groups_to_groups(
            hierarchy_config_id,
            _DictFilter(child_groups_filter),
            _DictFilter(parent_groups_filter),
        )
        return {"ok": True}

    def attach_vsif_hierarchy_groups_to_sessions(
        self,
        hierarchy_config_id: int,
        groups_filter: dict,
        sessions_filter: dict,
    ) -> dict[str, Any]:
        """Attach VSIF groups to VSIF sessions (vsif/hierarchy-configurations/attach-groups-to-sessions)."""
        self.vsif_hierarchy.attach_groups_to_sessions(
            hierarchy_config_id,
            _DictFilter(groups_filter),
            _DictFilter(sessions_filter),
        )
        return {"ok": True}

    def attach_vsif_hierarchy_tests_to_groups(
        self,
        hierarchy_config_id: int,
        tests_filter: dict,
        groups_filter: dict,
    ) -> dict[str, Any]:
        """Attach VSIF tests to VSIF groups (vsif/hierarchy-configurations/attach-tests-to-groups)."""
        self.vsif_hierarchy.attach_tests_to_groups(
            hierarchy_config_id,
            _DictFilter(tests_filter),
            _DictFilter(groups_filter),
        )
        return {"ok": True}

    def attach_vsif_hierarchy_tests_to_sessions(
        self,
        hierarchy_config_id: int,
        tests_filter: dict,
        sessions_filter: dict,
    ) -> dict[str, Any]:
        """Attach VSIF tests to VSIF sessions (vsif/hierarchy-configurations/attach-tests-to-sessions)."""
        self.vsif_hierarchy.attach_tests_to_sessions(
            hierarchy_config_id,
            _DictFilter(tests_filter),
            _DictFilter(sessions_filter),
        )
        return {"ok": True}

    # -----------------------------------------------------------------------
    # vsif_sessions additional methods
    # -----------------------------------------------------------------------

    def get_vsif_session(self, session_id: int) -> dict[str, Any]:
        """Fetch a single VSIF session by integer ID (vsif/sessions/get)."""
        return _normalize_single(self.vsif_sessions.get(session_id))

    def create_vsif_session(self, post_data: dict) -> dict[str, Any]:
        """Create a VSIF session.

        Routes through create_with_permissions which returns the new session ID
        consistently across supported server versions.
        """
        new_id = self.vsif_sessions.create_with_permissions(post_data, None)
        return {"id": new_id}

    def create_vsif_session_with_permissions(self, post_data: dict) -> dict[str, Any]:
        """Create a VSIF session with permissions (vsif/sessions/create-with-permissions)."""
        session_data = post_data.get("session", post_data)
        permissions = post_data.get("permissions", None)
        new_id = self.vsif_sessions.create_with_permissions(session_data, permissions)
        return {"id": new_id}

    def delete_vsif_sessions(self, filter_dict: dict) -> dict[str, Any]:
        """Delete VSIF sessions matching a filter dict (vsif/sessions/delete)."""
        result = self.vsif_sessions.delete(_DictFilter(filter_dict))
        return {"id": result}

    # -----------------------------------------------------------------------
    # runtime session methods
    # -----------------------------------------------------------------------

    def get_session_by_name(self, name: str) -> dict[str, Any]:
        """Fetch a runtime session by exact name (sessions/list with name filter)."""
        result = self._vamp.session.get_session_from_name(name)
        if result is None:
            return {}
        return {"id": result.id, "name": result.name, "config": result.config}

    # -----------------------------------------------------------------------
    # test_plan extended methods
    # -----------------------------------------------------------------------

    def list_vplans(self, post_data: dict | None = None) -> dict[str, Any]:
        """List available vPlans (vplan/list-vplans, §46.51)."""
        rows = _extract_rows(self.test_plan.list_vplans(post_data or {}))
        return {"vplans": rows, "count": len(rows)}

    def get_vplan(self, post_data: dict) -> dict[str, Any]:
        """Get a vPlan by specification (planning/get)."""
        result = self.test_plan.get_vplan(post_data)
        return result if isinstance(result, dict) else {}

    def list_plan_sub_elements(self, post_data: dict) -> dict[str, Any]:
        """List flat vPlan sub-elements (planning/list-sub-elements).

        A slim projection is applied by default so that AI callers do not
        receive large per-row payloads.  Pass ``"projection"`` in *post_data*
        (including ``None`` or ``[]``) to override with a custom field list.
        """
        post_data = apply_default_projection(post_data, PLAN_SUB_ELEMENTS_SLIM_PROJECTION)
        list_sub_elements = getattr(self.test_plan, "list_sub_elements", None)
        if callable(list_sub_elements):
            rows = _extract_rows(list_sub_elements(post_data=post_data))
        else:
            rows = _extract_rows(self.test_plan.list(post_data))
        return {"sub_elements": rows, "count": len(rows)}

    def get_plan_rich_text(self, post_data: dict) -> dict[str, Any]:
        """Get rich text for a vPlan element (planning/get-rich-text-with-check-sum)."""
        result = self.test_plan.get_rich_text(post_data=post_data)
        return result if isinstance(result, dict) else {}

    def add_plan_section(self, post_data: dict) -> dict[str, Any]:
        """Add a section to a vPlan (planning/add-section)."""
        value = self.test_plan.add_section(post_data)
        return {"id": value}

    def add_plan_reference(self, post_data: dict) -> dict[str, Any]:
        """Add a reference to a vPlan (planning/add-reference)."""
        value = self.test_plan.add_reference(post_data)
        return {"id": value}

    def add_plan_metrics_port(self, post_data: dict) -> dict[str, Any]:
        """Add a metrics port to a vPlan (planning/add-metrics-port)."""
        value = self.test_plan.add_metrics_port(post_data)
        return {"id": value}

    def update_plan(self, post_data: dict) -> Any:
        """Update a vPlan (planning/update-plan)."""
        result = self.test_plan.update_plan(post_data)
        return result if isinstance(result, dict) else {"result": result}

    def update_plan_bulk(self, post_data: dict) -> Any:
        """Bulk update vPlan entries (planning/update-bulk)."""
        result = self.test_plan.update_bulk(post_data)
        return result if isinstance(result, dict) else {"result": result}

    def update_plan_section(self, post_data: dict) -> Any:
        """Update a vPlan section (planning/update-section)."""
        result = self.test_plan.update_section(post_data)
        return result if isinstance(result, dict) else {"result": result}

    def update_plan_reference(self, post_data: dict) -> Any:
        """Update a vPlan reference (planning/update-reference)."""
        result = self.test_plan.update_reference(post_data)
        return result if isinstance(result, dict) else {"result": result}

    # -----------------------------------------------------------------------
    # vsif_groups scoped list methods
    # -----------------------------------------------------------------------

    def list_vsif_groups_for_session(
        self,
        sessions_filter_dict: dict,
        extra_data: dict | None = None,
    ) -> dict[str, Any]:
        """List VSIF groups scoped to parent sessions (vsif/groups/list with parentSessions)."""
        rows = _extract_rows(
            self.vsif_groups.list_for_parent_sessions(
                _DictFilter(sessions_filter_dict), extra_data
            )
        )
        return {"vsif_groups": rows, "count": len(rows)}

    def list_vsif_groups_for_group(
        self,
        groups_filter_dict: dict,
        extra_data: dict | None = None,
    ) -> dict[str, Any]:
        """List VSIF groups scoped to parent groups (vsif/groups/list with parentGroups)."""
        rows = _extract_rows(
            self.vsif_groups.list_for_parent_groups(
                _DictFilter(groups_filter_dict), extra_data
            )
        )
        return {"vsif_groups": rows, "count": len(rows)}

    # -----------------------------------------------------------------------
    # vsif_tests scoped list methods
    # -----------------------------------------------------------------------

    def list_vsif_tests_for_session(
        self,
        sessions_filter_dict: dict,
        extra_data: dict | None = None,
    ) -> dict[str, Any]:
        """List VSIF tests scoped to parent sessions (vsif/tests/list with parentSessions)."""
        rows = _extract_rows(
            self.vsif_tests.list_for_parent_sessions(
                _DictFilter(sessions_filter_dict), extra_data
            )
        )
        return {"vsif_tests": rows, "count": len(rows)}

    def list_vsif_tests_for_group(
        self,
        groups_filter_dict: dict,
        extra_data: dict | None = None,
    ) -> dict[str, Any]:
        """List VSIF tests scoped to parent groups (vsif/tests/list with parentGroups)."""
        rows = _extract_rows(
            self.vsif_tests.list_for_parent_groups(
                _DictFilter(groups_filter_dict), extra_data
            )
        )
        return {"vsif_tests": rows, "count": len(rows)}

    # -----------------------------------------------------------------------
    # vsif_config by-name convenience
    # -----------------------------------------------------------------------

    def list_vsif_configs_by_name(
        self, name: str, page_length: int = 1000
    ) -> dict[str, Any]:
        """List VSIF configurations whose name matches a glob pattern."""
        results = self.vsif.get_vsif_config_by_name_match(name, page_length=page_length)
        rows = [vars(r) for r in results] if results else []
        return {"vsif_configs": rows, "count": len(rows)}

    # -----------------------------------------------------------------------
    # run_failure_cluster helper query methods
    # -----------------------------------------------------------------------

    def list_run_failures_for_team(
        self, team: str, days: int = 15
    ) -> dict[str, Any]:
        """List wip/new run failures for a team within the last N days."""
        results = self.run_failure_cluster.get_failures_for_team(team, days)
        rows = [vars(r) for r in results]
        return {"run_failure_clusters": rows, "count": len(rows)}

    def list_run_failures_in_datetime(
        self, days: int = 0, hours: int = 0, minutes: int = 0
    ) -> dict[str, Any]:
        """List wip/new run failures submitted after a rolling time window."""
        results = self.run_failure_cluster.get_failures_in_datetime(
            days=days, hours=hours, minutes=minutes
        )
        rows = [vars(r) for r in results]
        return {"run_failure_clusters": rows, "count": len(rows)}

    def list_run_failures_needs_rerun(self) -> dict[str, Any]:
        """List failed runs with rerun_status == needs_rerun."""
        results = self.run_failure_cluster.get_failures_marked_needs_rerun()
        rows = [vars(r) for r in results]
        return {"run_failure_clusters": rows, "count": len(rows)}

    def list_run_failures_for_result_ids(
        self, result_ids: list[int]
    ) -> dict[str, Any]:
        """List run↔failure-cluster associations for specific run IDs."""
        results = self.run_failure_cluster.get_from_result_ids(result_ids)
        rows = [vars(r) for r in results]
        return {"run_failure_clusters": rows, "count": len(rows)}

    # -----------------------------------------------------------------------
    # failure_cluster associated helper
    # -----------------------------------------------------------------------

    def get_failure_clusters_for_runs(
        self, run_ids: list[int]
    ) -> dict[str, Any]:
        """List failure clusters associated with specific run IDs."""
        results = self.failure_cluster.get_associated_failure_clusters(run_ids)
        rows = [vars(r) for r in results]
        return {"failure_clusters": rows, "count": len(rows)}
