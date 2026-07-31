from __future__ import annotations

import pytest

from workout_tracker.adapters.port import UpdateManagedObject


pytestmark = pytest.mark.google_uat

EXPECTED_TABS = (
    "Старт",
    "Програма",
    "Сесії",
    "Підходи",
    "Рекомендації",
    "Довідники",
    "Дашборд",
)


def test_clean_workbook_initializes_exact_managed_state(
    google_uat_session,
) -> None:
    desired = google_uat_session.desired
    initial = google_uat_session.initial

    assert (initial.locale, initial.time_zone) != (
        "uk_UA",
        "America/New_York",
    ), "clean target must begin with at least one managed property mismatch"

    observed = google_uat_session.initialize()
    plan = google_uat_session.first_plan
    assert plan is not None
    assert any(
        isinstance(operation, UpdateManagedObject)
        and operation.kind == "workbook_properties"
        for operation in plan.operations
    )
    assert observed.locale == "uk_UA"
    assert observed.time_zone == "America/New_York"
    assert tuple(tab.title for tab in observed.tabs) == EXPECTED_TABS

    rows = tuple(dict(row.values) for row in desired.program_rows)
    assert len(rows) == 31
    assert {row["workout_type"] for row in rows} == {
        "Верх — сила",
        "Низ — сила",
        "Верх — гіпертрофія",
        "Низ — гіпертрофія",
    }
    lower_c1 = next(
        row
        for row in rows
        if row["workout_type"] == "Низ — гіпертрофія"
        and row["block_code"] == "C1"
    )
    assert lower_c1["exercise_variant_id"] == "dumbbell_romanian_deadlift"
    assert lower_c1["equipment_id"] == "dumbbell"

    expected_objects = {
        (item.kind, item.logical_key)
        for item in plan.desired_objects
    }
    observed_objects = {
        (item.kind, item.logical_key)
        for item in observed.managed_objects
    }
    assert expected_objects <= observed_objects
    assert len(observed.reserve_bindings) == sum(
        pool.capacity for pool in desired.reserve_pools
    )
