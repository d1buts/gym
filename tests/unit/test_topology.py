from pathlib import Path

from workout_tracker.contracts import (
    load_source_schema,
    load_workbook_blueprint,
)


SCHEMA_PATH = Path("config/schema.yaml")
BLUEPRINT_PATH = Path("config/workbook-blueprint.yaml")

EXPECTED_TABS = (
    ("tab:start", "Старт", "user_interface", None),
    (
        "tab:program",
        "Програма",
        "operational_program_prescriptions",
        "program",
    ),
    ("tab:sessions", "Сесії", "training_facts", "sessions"),
    ("tab:sets", "Підходи", "training_facts", "sets"),
    (
        "tab:recommendations",
        "Рекомендації",
        "recommendation_journal",
        "recommendations",
    ),
    ("tab:lookups", "Довідники", "configuration_projection", None),
    ("tab:dashboard", "Дашборд", "derived", None),
)


def _load_blueprint():
    assert BLUEPRINT_PATH.is_file(), "managed workbook topology is missing"
    return load_workbook_blueprint(
        BLUEPRINT_PATH,
        load_source_schema(SCHEMA_PATH),
    )


def test_blueprint_has_exact_managed_tab_topology() -> None:
    blueprint = _load_blueprint()

    actual = tuple(
        (
            tab.logical_key,
            tab.title,
            tab.authority_role,
            tab.source_schema_tab,
        )
        for tab in blueprint.tabs
    )

    assert actual == EXPECTED_TABS
    assert len({tab.logical_key for tab in blueprint.tabs}) == 7
    assert len({tab.title for tab in blueprint.tabs}) == 7


def test_blueprint_pins_workbook_properties_and_versions() -> None:
    blueprint = _load_blueprint()

    assert blueprint.workbook_contract_version == "1.1.0"
    assert blueprint.schema_version == "1.1.0"
    assert blueprint.formula_version == "metrics-v1"
    assert blueprint.program_bootstrap_version == "program-v1.0.0"
    assert blueprint.properties.locale == "uk_UA"
    assert blueprint.properties.time_zone == "America/New_York"


def test_only_domain_tabs_link_to_the_authoritative_source_schema() -> None:
    source_schema = load_source_schema(SCHEMA_PATH)
    blueprint = _load_blueprint()

    linked = {
        tab.title: tab.source_schema_tab
        for tab in blueprint.tabs
        if tab.source_schema_tab is not None
    }

    assert linked == {
        "Програма": "program",
        "Сесії": "sessions",
        "Підходи": "sets",
        "Рекомендації": "recommendations",
    }
    assert tuple(linked) == source_schema.source.required_tabs
    assert all(
        tab.source_schema_tab is None
        for tab in blueprint.tabs
        if tab.title in {"Старт", "Довідники", "Дашборд"}
    )


def test_logical_tab_identity_does_not_use_mutable_provider_coordinates() -> None:
    from workout_tracker.adapters.port import ObservedTab

    tab = ObservedTab(
        logical_key="tab:sessions",
        title="Сесії",
        owner="workout_tracker",
        authority_role="training_facts",
        source_schema_tab="sessions",
        provider_id="provider-sheet-123",
        provider_position=42,
    )

    assert tab.logical_key == "tab:sessions"
    assert tab.provider_id != tab.logical_key
    assert str(tab.provider_position) not in tab.logical_key
