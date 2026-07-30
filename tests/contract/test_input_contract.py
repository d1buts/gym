from __future__ import annotations

from pathlib import Path

import yaml

from workout_tracker.contracts import load_source_schema


BLUEPRINT_PATH = Path("config/workbook-blueprint.yaml")
SCHEMA_PATH = Path("config/schema.yaml")

WORKOUT_LABELS = (
    "Верх — сила",
    "Низ — сила",
    "Верх — гіпертрофія",
    "Низ — гіпертрофія",
)


def _blueprint_payload() -> dict[str, object]:
    payload = yaml.safe_load(BLUEPRINT_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    assert "presentation" in payload, "mobile input contract is missing"
    return payload


def _by_key(items: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(item["logical_key"]): item for item in items}


def test_start_is_mobile_first_and_links_all_four_complexes() -> None:
    payload = _blueprint_payload()
    presentation = payload["presentation"]
    assert isinstance(presentation, dict)
    start = presentation["start"]
    assert isinstance(start, dict)

    assert start["primary_action_columns"] == ["A", "B"]
    assert start["decorative_merged_cells"] is False
    assert start["shows"] == [
        "next_complex",
        "last_completed_session",
        "complex_links",
        "manual_guidance",
        "sync_backup_status",
    ]
    links = start["complex_links"]
    assert isinstance(links, list)
    assert tuple(link["label"] for link in links) == WORKOUT_LABELS
    assert len({link["target_filter_view"] for link in links}) == 4
    assert all(link["tap_count"] == 1 for link in links)
    assert start["redacted_status"]["allowed_fields"] == [
        "status_code",
        "contract_version",
        "record_count",
    ]
    assert start["redacted_status"]["forbidden_fields"] == [
        "sheet_locator",
        "credential_path",
        "notes",
        "health_context",
    ]


def test_visual_language_never_uses_color_alone() -> None:
    payload = _blueprint_payload()
    presentation = payload["presentation"]
    assert isinstance(presentation, dict)
    palette = presentation["palette"]
    assert isinstance(palette, dict)

    accents = palette["workout_accents"]
    assert isinstance(accents, list)
    assert tuple(accent["label"] for accent in accents) == WORKOUT_LABELS
    assert len({accent["color"] for accent in accents}) == 4
    assert all(accent["symbol"] and accent["label"] for accent in accents)

    statuses = presentation["status_styles"]
    assert isinstance(statuses, list)
    assert {
        "missing_required",
        "invalid_bundle",
        "duplicate_id",
        "pending_recommendation",
        "nullable_missing",
    } <= {status["code"] for status in statuses}
    assert all(status["symbol"] and status["label"] for status in statuses)
    nullable = next(
        status for status in statuses if status["code"] == "nullable_missing"
    )
    assert nullable["display_value"] is None
    assert nullable["label"] == "Немає даних"


def test_session_and_set_input_zones_are_input_first_and_append_only() -> None:
    payload = _blueprint_payload()
    zones = payload["managed_input_zones"]
    assert isinstance(zones, list)
    by_key = _by_key(zones)
    source_schema = load_source_schema(SCHEMA_PATH)

    for logical_key, schema_key in (
        ("input_zone:sessions", "sessions"),
        ("input_zone:sets", "sets"),
    ):
        zone = by_key[logical_key]
        source_tab = source_schema.tab(schema_key)
        assert source_tab is not None
        expected_fields = {column.field for column in source_tab.columns}
        editable = zone["editable_columns"]
        protected = zone["protected_columns"]
        assert isinstance(editable, list)
        assert isinstance(protected, list)

        assert zone["append_only"] is True
        assert zone["freeze_rows"] == 1
        assert zone["decorative_merged_cells"] is False
        assert set(editable).isdisjoint(protected)
        assert set(editable) | set(protected) == expected_fields
        assert zone["column_order"] == editable + protected
        assert zone["input_fill"] != zone["system_fill"]
        assert zone["protection"]["enforced"] is True
        assert zone["protection"]["warning_only"] is False
        assert zone["primary_key"] in protected

    sessions = by_key["input_zone:sessions"]
    sets = by_key["input_zone:sets"]
    assert sessions["editable_columns"][:3] == [
        "session_date",
        "workout_type",
        "status",
    ]
    assert sets["editable_columns"][:3] == [
        "session_id",
        "program_item_id",
        "status",
    ]
    assert sets["activation"]["foreign_key"] == "session_id"
    assert sets["activation"]["foreign_key_named_range"] == (
        "named_range:active_session_ids"
    )
    assert sets["activation"]["version_match"] == (
        "program_version_id == referenced session.program_version_id"
    )


def test_validation_formats_named_ranges_and_diagnostics_are_declared_once() -> None:
    payload = _blueprint_payload()
    schema = load_source_schema(SCHEMA_PATH)
    validation = payload["validation_policy"]
    assert isinstance(validation, dict)

    assert validation["schema_derived"] is True
    assert validation["strict_reject"] is True
    assert validation["nullable_blank_is_null"] is True
    assert validation["invalid_value_is_zero"] is False
    assert validation["help_text_locale"] == "uk-UA"
    assert validation["filtered_rows_included"] is True
    assert validation["date_format"] == "yyyy-mm-dd"
    assert validation["datetime_format"] == "yyyy-mm-dd hh:mm"
    assert validation["decimal_format"] == "0.00"
    assert validation["integer_format"] == "0"

    ranges = payload["named_ranges"]
    assert isinstance(ranges, list)
    by_key = _by_key(ranges)
    enum_refs = {
        column.enum_ref
        for tab_key in ("sessions", "sets")
        for column in schema.tab(tab_key).columns  # type: ignore[union-attr]
        if column.enum_ref is not None
    }
    assert enum_refs <= {
        item.get("source_ref")
        for item in ranges
        if item.get("source_kind") == "schema_enum"
    }
    assert {
        "named_range:workout_types",
        "named_range:active_program_versions",
        "named_range:active_program_items",
        "named_range:active_session_ids",
    } <= set(by_key)
    assert by_key["named_range:active_session_ids"]["operational_only"] is True

    diagnostics = payload["quality_diagnostics"]
    assert isinstance(diagnostics, dict)
    assert diagnostics["source_ref"] == "schema.conditional_rules"
    assert diagnostics["missing_nullable_value"] == "nullable_missing"
    assert diagnostics["missing_required_value"] == "missing_required"
    assert diagnostics["write_zero_for_missing"] is False


def test_filter_views_widths_and_protections_have_stable_logical_identity() -> None:
    payload = _blueprint_payload()
    views = payload["filter_views"]
    assert isinstance(views, list)
    assert tuple(view["workout_label"] for view in views) == WORKOUT_LABELS
    assert len({view["logical_key"] for view in views}) == 4
    assert all(view["tab"] == "Програма" for view in views)

    layouts = payload["tab_layouts"]
    assert isinstance(layouts, list)
    layout_by_key = _by_key(layouts)
    for key in ("layout:start", "layout:sessions", "layout:sets"):
        layout = layout_by_key[key]
        assert layout["freeze_rows"] >= 1
        assert layout["decorative_merged_cells"] is False
        assert layout["column_widths"]

    sessions_widths = layout_by_key["layout:sessions"]["column_widths"]
    sets_widths = layout_by_key["layout:sets"]["column_widths"]
    assert sessions_widths[:3] == [
        {"field": "session_date", "pixels": 104},
        {"field": "workout_type", "pixels": 150},
        {"field": "status", "pixels": 112},
    ]
    assert sets_widths[:3] == [
        {"field": "session_id", "pixels": 154},
        {"field": "program_item_id", "pixels": 154},
        {"field": "status", "pixels": 112},
    ]

    protections = payload["protections"]
    assert isinstance(protections, list)
    assert all(item["enforced"] is True for item in protections)
    assert all(item["warning_only"] is False for item in protections)
    assert all(item["logical_key"].startswith("protection:") for item in protections)
