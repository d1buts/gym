from __future__ import annotations

from pathlib import Path

import yaml

from workout_tracker.contracts import load_source_schema, load_workbook_blueprint
from workout_tracker.workbook import FormulaRegistry, compile_desired_workbook
from workout_tracker.contracts import load_program_bootstrap


SCHEMA_PATH = Path("config/schema.yaml")
BLUEPRINT_PATH = Path("config/workbook-blueprint.yaml")
PROGRAM_PATH = Path("config/program-bootstrap.yaml")


def _payload() -> dict[str, object]:
    return yaml.safe_load(BLUEPRINT_PATH.read_text(encoding="utf-8"))


def _contracts():
    schema = load_source_schema(SCHEMA_PATH)
    blueprint = load_workbook_blueprint(BLUEPRINT_PATH, schema)
    program = load_program_bootstrap(PROGRAM_PATH, schema)
    return blueprint, schema, program


def test_blueprint_uses_registry_references_without_ad_hoc_formula_text() -> None:
    payload = _payload()
    registry = FormulaRegistry.metrics_v1()

    assert payload["workbook_contract_version"] == "1.1.0"
    assert {item["formula_id"] for item in payload["formula_registry"]} == set(
        registry.formula_ids
    )
    assert all(
        item == {
            "formula_id": item["formula_id"],
            "formula_version": "metrics-v1",
        }
        for item in payload["formula_registry"]
    )
    assert all(
        placement["formula_id"] in registry.formula_ids
        and placement["formula_version"] == "metrics-v1"
        and placement["value_field"] != placement["status_field"]
        for placement in payload["formula_placements"]
    )


def test_session_and_set_derived_columns_are_protected_metric_status_pairs() -> None:
    payload = _payload()
    placements = payload["formula_placements"]
    by_tab = {}
    for item in placements:
        by_tab.setdefault(item["tab"], []).append(item)

    assert {"Сесії", "Підходи"} <= set(by_tab)
    assert {
        "working_set_count_v1",
        "load_volume_v1",
        "rir_summary_v1",
        "rest_summary_v1",
        "session_completion_v1",
        "data_quality_status_v1",
    } <= {item["formula_id"] for item in by_tab["Сесії"]}
    assert {
        "load_volume_v1",
        "epley_e1rm_v1",
        "data_quality_status_v1",
    } <= {item["formula_id"] for item in by_tab["Підходи"]}

    protected = {
        protection["tab"]: set(protection["fields"])
        for protection in payload["protections"]
        if protection["logical_key"].endswith(":formulas")
    }
    for tab, items in by_tab.items():
        for item in items:
            assert item["value_field"] in protected[tab]
            assert item["status_field"] in protected[tab]


def test_dashboard_order_cards_filters_and_status_sections_are_complete() -> None:
    dashboard = _payload()["dashboard"]
    assert dashboard["section_order"] == [
        "summary_cards",
        "filters",
        "cohort_safe_trends",
        "data_quality_statuses",
    ]
    assert {
        "sessions_per_week_type",
        "working_set_count",
        "rep_volume",
        "comparable_load_volume",
        "best_eligible_e1rm",
    } <= {card["metric_key"] for card in dashboard["summary_cards"]}
    assert all(card["status_field"] and card["formula_version"] == "metrics-v1" for card in dashboard["summary_cards"])
    assert {
        "workout_type",
        "date_range",
        "exercise_variant_id",
        "comparison_cohort_id",
    } <= {item["field"] for item in dashboard["filters"]}
    assert dashboard["progression_status"]["source_kind"] == "deterministic_rules_output"
    assert dashboard["recommendation_status"]["allowed_statuses"] == [
        "proposed",
        "accepted",
        "rejected",
    ]


def test_dashboard_helper_ranges_and_charts_are_cohort_safe_and_keep_null_gaps() -> None:
    dashboard = _payload()["dashboard"]
    helper_ranges = {item["logical_key"]: item for item in dashboard["helper_ranges"]}
    required_cohort_fields = {
        "exercise_variant_id",
        "equipment_id",
        "setup_id",
        "load_basis",
        "comparison_cohort_id",
        "assistance_semantics",
        "metric_value",
        "metric_unit",
        "metric_status",
        "metric_reason",
    }
    for chart in dashboard["charts"]:
        assert chart["helper_range"] in helper_ranges
        helper = helper_ranges[chart["helper_range"]]
        if chart["cohort_required"]:
            assert required_cohort_fields <= set(helper["fields"])
        assert chart["domain"]
        assert chart["series"]
        assert chart["header_count"] == 1
        assert chart["interpolate_nulls"] is False
        assert chart["alt_text"]
        assert chart["textual_status_field"]
        assert chart["geometry"]["width"] >= 480
        assert chart["geometry"]["height"] >= 260


def test_compiled_workbook_retains_dashboard_logical_contract() -> None:
    blueprint, schema, program = _contracts()
    desired = compile_desired_workbook(
        blueprint,
        schema,
        program,
        locale="uk_UA",
        time_zone="America/New_York",
    )

    assert desired.formula_version == "metrics-v1"
    assert len(desired.formula_placements) >= 9
    assert desired.dashboard.section_order[0] == "summary_cards"
    assert all(not chart.interpolate_nulls for chart in desired.dashboard.charts)
