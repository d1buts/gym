from __future__ import annotations

from pathlib import Path

import pytest
import yaml


FIXTURE_PATH = Path("tests/fixtures/metrics-v1.yaml")
FORMULAS_PATH = Path("src/workout_tracker/workbook/formulas.py")


def _fixture() -> dict[str, object]:
    return yaml.safe_load(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_metrics_v1_fixture_matrix_has_required_cases() -> None:
    payload = _fixture()
    cases = payload["cases"]
    assert payload["formula_version"] == "metrics-v1"
    assert len(cases) >= 20
    case_ids = {case["case_id"] for case in cases}
    for required in (
        "working_sets_valid_kg",
        "working_sets_incomplete_unilateral",
        "working_sets_warmup",
        "working_sets_skipped_and_void",
        "rep_volume_empty_scope",
        "load_volume_exact_lb_conversion",
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
        "session_completion",
    ):
        assert required in case_ids


def test_fixture_numbers_do_not_cross_the_decimal_boundary_as_float() -> None:
    def assert_no_float(value: object) -> None:
        assert not isinstance(value, float)
        if isinstance(value, dict):
            for child in value.values():
                assert_no_float(child)
        elif isinstance(value, list):
            for child in value:
                assert_no_float(child)

    assert_no_float(_fixture())


def test_metrics_v1_oracle_matches_every_canonical_case() -> None:
    assert FORMULAS_PATH.is_file(), "metrics-v1 oracle is missing"
    from workout_tracker.workbook.formulas import evaluate_fixture_case

    for case in _fixture()["cases"]:
        assert evaluate_fixture_case(case) == case["expected"], case["case_id"]


def test_formula_registry_is_pinned_and_resolves_only_logical_headers() -> None:
    assert FORMULAS_PATH.is_file(), "metrics-v1 formula registry is missing"
    from workout_tracker.workbook.formulas import FORMULA_VERSION, FormulaRegistry

    registry = FormulaRegistry.metrics_v1()
    assert FORMULA_VERSION == "metrics-v1"
    assert set(registry.formula_ids) == {
        "working_set_count_v1",
        "rep_volume_v1",
        "load_volume_v1",
        "maximum_comparable_load_v1",
        "epley_e1rm_v1",
        "rir_summary_v1",
        "rest_summary_v1",
        "session_completion_v1",
        "data_quality_status_v1",
    }
    for formula_id in registry.formula_ids:
        template = registry.get(formula_id)
        assert template.formula_version == FORMULA_VERSION
        assert template.text.startswith("=")
        assert "ROW(" not in template.text.upper()
        assert "INDIRECT(" not in template.text.upper()
        assert template.value_field
        assert template.status_field


@pytest.mark.parametrize(
    "formula_id",
    ["load_volume_v1", "maximum_comparable_load_v1", "epley_e1rm_v1"],
)
def test_scalar_metric_templates_require_cohort_boundaries(formula_id: str) -> None:
    assert FORMULAS_PATH.is_file(), "metrics-v1 formula registry is missing"
    from workout_tracker.workbook.formulas import FormulaRegistry

    template = FormulaRegistry.metrics_v1().get(formula_id)
    assert {
        "exercise_variant_id",
        "equipment_id",
        "setup_id",
        "load_basis",
        "comparison_cohort_id",
    } <= set(template.required_columns)
