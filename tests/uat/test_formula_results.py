from __future__ import annotations

import time

import pytest

from workout_tracker.workbook import evaluate_fixture_case


pytestmark = pytest.mark.google_uat

REQUIRED_CASES = {
    "working_sets_incomplete_unilateral",
    "working_sets_warmup",
    "working_sets_skipped_and_void",
    "load_volume_missing_load",
    "load_volume_mixed_cohort",
    "load_volume_machine_level",
    "maximum_load_decimal_tie",
    "maximum_load_bodyweight",
    "e1rm_one_rep",
    "e1rm_twelve_reps_without_rir",
    "e1rm_thirteen_reps",
    "e1rm_assistance",
    "rir_summary_missing",
    "rest_summary_paired_set",
    "invalid_source_record",
}


def test_formula_dashboard_results_match_canonical_contract(
    google_uat_session,
    canonical_metric_cases,
) -> None:
    observed = google_uat_session.initialize()
    desired = google_uat_session.desired

    by_id = {str(case["case_id"]): case for case in canonical_metric_cases}
    assert REQUIRED_CASES <= set(by_id)
    for case in canonical_metric_cases:
        assert evaluate_fixture_case(case) == case["expected"]
        expected = case["expected"]
        if expected["status"] in {
            "missing",
            "invalid",
            "incomparable",
            "not_applicable",
        }:
            assert expected["value"] is None
            assert expected["exclusion_reasons"]

    expected_by_key = {
        (item.kind, item.logical_key): item.payload
        for item in google_uat_session.first_plan.desired_objects
        if item.kind
        in {
            "formula",
            "dashboard",
            "dashboard_filter",
            "dashboard_helper",
            "dashboard_chart",
        }
    }
    deadline = time.monotonic() + 15
    observed_by_key: dict[tuple[str, str], object] = {}
    while time.monotonic() < deadline:
        observed = google_uat_session.gateway.observe()
        observed_by_key = {
            (item.kind, item.logical_key): item.payload
            for item in observed.managed_objects
        }
        if expected_by_key.keys() <= observed_by_key.keys():
            break
    assert expected_by_key.keys() <= observed_by_key.keys()
    assert all(
        observed_by_key[key] == payload
        for key, payload in expected_by_key.items()
    )

    dashboard = desired.dashboard
    assert {
        "sessions_per_week_type",
        "working_set_count",
        "rep_volume",
        "comparable_load_volume",
        "best_eligible_e1rm",
    } == {card.metric_key for card in dashboard.summary_cards}
    assert {item.field for item in dashboard.filters} == {
        "workout_type",
        "date_range",
        "exercise_variant_id",
        "comparison_cohort_id",
    }
    assert all(item.one_cohort_per_series for item in dashboard.helper_ranges)
    assert all(item.null_for_unavailable for item in dashboard.helper_ranges)
    assert all(not item.interpolate_nulls for item in dashboard.charts)
    assert all(item.textual_status_field for item in dashboard.charts)
