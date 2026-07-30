from __future__ import annotations

import re
from pathlib import Path

import pytest

from workout_tracker.contracts import (
    load_program_bootstrap,
    load_source_schema,
    load_workbook_blueprint,
)


MODEL_PATH = Path("src/workout_tracker/workbook/model.py")
SCHEMA_PATH = Path("config/schema.yaml")
BLUEPRINT_PATH = Path("config/workbook-blueprint.yaml")
PROGRAM_PATH = Path("config/program-bootstrap.yaml")


def _contracts():
    schema = load_source_schema(SCHEMA_PATH)
    blueprint = load_workbook_blueprint(BLUEPRINT_PATH, schema)
    program = load_program_bootstrap(PROGRAM_PATH, schema)
    return blueprint, schema, program


def _compile():
    assert MODEL_PATH.is_file(), "pure desired workbook compiler is missing"
    from workout_tracker.workbook import compile_desired_workbook

    blueprint, schema, program = _contracts()
    return compile_desired_workbook(
        blueprint,
        schema,
        program,
        locale="uk_UA",
        time_zone="America/New_York",
    )


def test_compiler_resolves_exact_tabs_headers_roles_and_program_rows() -> None:
    desired = _compile()
    _, schema, _ = _contracts()

    assert desired.locale == "uk_UA"
    assert desired.time_zone == "America/New_York"
    assert tuple(tab.title for tab in desired.tabs) == (
        "Старт",
        "Програма",
        "Сесії",
        "Підходи",
        "Рекомендації",
        "Довідники",
        "Дашборд",
    )
    assert len(desired.program_rows) == 31
    assert {
        row.value("workout_type")
        for row in desired.program_rows
    } == {
        "Верх — сила",
        "Низ — сила",
        "Верх — гіпертрофія",
        "Низ — гіпертрофія",
    }

    for schema_key in ("program", "sessions", "sets", "recommendations"):
        source_tab = schema.tab(schema_key)
        assert source_tab is not None
        desired_tab = desired.tab_by_schema_key(schema_key)
        assert desired_tab is not None
        assert desired_tab.headers == tuple(
            column.header
            for field in desired_tab.column_order
            for column in source_tab.columns
            if column.field == field
        )
        assert set(desired_tab.column_order) == {
            column.field for column in source_tab.columns
        }
        assert {
            column.field: column.data_class
            for column in desired_tab.columns
        } == {
            column.field: column.data_class
            for column in source_tab.columns
        }


def test_compiler_resolves_named_ranges_filters_validations_and_formats() -> None:
    desired = _compile()
    _, schema, _ = _contracts()

    workout_types = desired.named_range("named_range:workout_types")
    assert workout_types is not None
    assert workout_types.values == (
        "Верх — сила",
        "Низ — сила",
        "Верх — гіпертрофія",
        "Низ — гіпертрофія",
    )
    sessions = desired.named_range("named_range:active_session_ids")
    assert sessions is not None
    assert sessions.values is None
    assert sessions.operational_only is True

    assert tuple(link.filter_view_key for link in desired.start_links) == tuple(
        view.logical_key for view in desired.filter_views
    )
    assert len(desired.filter_views) == 4

    for schema_key in ("sessions", "sets"):
        source_tab = schema.tab(schema_key)
        assert source_tab is not None
        for source_column in source_tab.columns:
            validation = desired.validation(schema_key, source_column.field)
            assert validation is not None
            assert validation.allow_blank is source_column.nullable
            assert validation.help_text
            if source_column.enum_ref:
                assert validation.named_range_key is not None
            if validation.value_type == "date":
                assert validation.number_format == "yyyy-mm-dd"
            if validation.value_type == "datetime":
                assert validation.number_format == "yyyy-mm-dd hh:mm"

    assert all(item.enforced and not item.warning_only for item in desired.protections)
    assert all(not layout.decorative_merged_cells for layout in desired.layouts)


def test_compilation_is_pure_repeatable_and_contains_no_allocated_session_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TZ", "Pacific/Kiritimati")
    monkeypatch.setenv("LANG", "C")
    first = _compile()
    second = _compile()

    assert second == first
    serialized = repr(first)
    assert re.search(r"ses_[0-9a-f-]{36}", serialized) is None
    assert re.search(r"set_[0-9a-f-]{36}", serialized) is None
    assert first.reserve_pool("session").slot_keys[0] == "reserve:session:001"
    assert first.reserve_pool("session").slot_keys[-1] == "reserve:session:128"
    assert first.reserve_pool("set").slot_keys[0] == "reserve:set:0001"
    assert first.reserve_pool("set").slot_keys[-1] == "reserve:set:2048"
    assert first.reserve_pool("session").capacity == 128
    assert first.reserve_pool("set").capacity == 2048


def test_locale_and_timezone_are_explicit_and_fail_closed() -> None:
    assert MODEL_PATH.is_file(), "pure desired workbook compiler is missing"
    from workout_tracker.workbook import (
        DesiredWorkbookCompilationError,
        compile_desired_workbook,
    )

    blueprint, schema, program = _contracts()
    with pytest.raises(TypeError):
        compile_desired_workbook(blueprint, schema, program)  # type: ignore[call-arg]
    with pytest.raises(DesiredWorkbookCompilationError) as locale:
        compile_desired_workbook(
            blueprint,
            schema,
            program,
            locale="en_US",
            time_zone="America/New_York",
        )
    assert locale.value.code == "WORKBOOK_LOCALE_MISMATCH"
    with pytest.raises(DesiredWorkbookCompilationError) as time_zone:
        compile_desired_workbook(
            blueprint,
            schema,
            program,
            locale="uk_UA",
            time_zone="UTC",
        )
    assert time_zone.value.code == "WORKBOOK_TIME_ZONE_MISMATCH"


def test_set_activation_requires_existing_session_and_matching_program_version() -> None:
    desired = _compile()
    active_sessions = {
        "ses_00000000-0000-4000-8000-000000000001": (
            "pver_00000000-0000-4000-8000-000000000002"
        )
    }

    assert desired.can_activate_set(
        session_id="ses_00000000-0000-4000-8000-000000000001",
        program_version_id="pver_00000000-0000-4000-8000-000000000002",
        active_sessions=active_sessions,
    )
    assert not desired.can_activate_set(
        session_id="ses_00000000-0000-4000-8000-000000000099",
        program_version_id="pver_00000000-0000-4000-8000-000000000002",
        active_sessions=active_sessions,
    )
    assert not desired.can_activate_set(
        session_id="ses_00000000-0000-4000-8000-000000000001",
        program_version_id="pver_00000000-0000-4000-8000-000000000099",
        active_sessions=active_sessions,
    )

    session_pool = desired.reserve_pool("session")
    set_pool = desired.reserve_pool("set")
    assert session_pool.inactive_rows_are_facts is False
    assert set_pool.inactive_rows_are_facts is False
