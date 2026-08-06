from __future__ import annotations

import pytest

from workout_tracker.workbook.reconcile import plan_setup


pytestmark = pytest.mark.google_uat


def test_second_setup_is_exact_no_op_and_preserves_ids(
    google_uat_session,
) -> None:
    first = google_uat_session.initialize()
    first_bindings = {
        binding.slot_key: binding.value
        for binding in first.reserve_bindings
    }
    assert len(first_bindings) == len(first.reserve_bindings)
    assert len(set(first_bindings.values())) == len(first_bindings)

    second_observation = google_uat_session.gateway.observe()
    second_plan = plan_setup(
        google_uat_session.desired,
        second_observation,
    )

    assert second_plan.conflicts == ()
    assert second_plan.operations == ()
    assert second_observation.managed_fingerprint == first.managed_fingerprint
    assert {
        binding.slot_key: binding.value
        for binding in second_observation.reserve_bindings
    } == first_bindings

    managed_keys = tuple(
        (item.kind, item.logical_key)
        for item in second_observation.managed_objects
    )
    assert len(managed_keys) == len(set(managed_keys))
    program_ids = tuple(
        dict(row.values)["program_item_id"]
        for row in google_uat_session.desired.program_rows
    )
    assert len(program_ids) == len(set(program_ids)) == 31
