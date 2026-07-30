from __future__ import annotations

import sys
from pathlib import Path

from workout_tracker.contracts import (
    load_source_schema,
    load_workbook_blueprint,
)


SCHEMA_PATH = Path("config/schema.yaml")
BLUEPRINT_PATH = Path("config/workbook-blueprint.yaml")


def _blueprint():
    return load_workbook_blueprint(
        BLUEPRINT_PATH,
        load_source_schema(SCHEMA_PATH),
    )


def test_memory_gateway_applies_exact_topology_without_google_state() -> None:
    from workout_tracker.adapters.memory import InMemoryWorkbookGateway
    from workout_tracker.adapters.port import ChangePlan

    gateway = InMemoryWorkbookGateway()
    result = gateway.apply(ChangePlan(blueprint=_blueprint()))

    assert result.changed is True
    assert result.statuses == ()
    assert tuple(tab.title for tab in result.observed.managed_tabs) == (
        "Старт",
        "Програма",
        "Сесії",
        "Підходи",
        "Рекомендації",
        "Довідники",
        "Дашборд",
    )
    assert not any(
        name == "google" or name.startswith("google.")
        for name in sys.modules
    )


def test_unowned_tab_is_reported_and_preserved() -> None:
    from workout_tracker.adapters.memory import InMemoryWorkbookGateway
    from workout_tracker.adapters.port import ChangePlan, ObservedTab

    extra = ObservedTab(title="Мої нотатки", is_empty=False)
    gateway = InMemoryWorkbookGateway(tabs=(extra,))

    result = gateway.apply(ChangePlan(blueprint=_blueprint()))

    assert "UNMANAGED_TAB_PRESENT" in result.statuses
    assert extra in result.observed.unmanaged_tabs
    assert any(tab.title == "Мої нотатки" for tab in gateway.observe().tabs)


def test_clean_initialization_removes_only_the_sole_default_blank_tab() -> None:
    from workout_tracker.adapters.memory import InMemoryWorkbookGateway
    from workout_tracker.adapters.port import ChangePlan, ObservedTab

    default_blank = ObservedTab(
        title="Аркуш1",
        is_empty=True,
        is_default_blank=True,
        provider_id="provider-sheet-123",
        provider_position=0,
    )
    gateway = InMemoryWorkbookGateway(tabs=(default_blank,))

    result = gateway.apply(
        ChangePlan(blueprint=_blueprint(), clean_initialization=True)
    )

    assert result.changed is True
    assert result.statuses == ()
    assert default_blank not in result.observed.tabs
    assert len(result.observed.tabs) == 7


def test_default_blank_is_preserved_outside_explicit_clean_initialization() -> None:
    from workout_tracker.adapters.memory import InMemoryWorkbookGateway
    from workout_tracker.adapters.port import ChangePlan, ObservedTab

    default_blank = ObservedTab(
        title="Аркуш1",
        is_empty=True,
        is_default_blank=True,
    )
    gateway = InMemoryWorkbookGateway(tabs=(default_blank,))

    result = gateway.apply(ChangePlan(blueprint=_blueprint()))

    assert "UNMANAGED_TAB_PRESENT" in result.statuses
    assert default_blank in result.observed.unmanaged_tabs


def test_default_blank_is_preserved_when_it_is_not_the_only_initial_tab() -> None:
    from workout_tracker.adapters.memory import InMemoryWorkbookGateway
    from workout_tracker.adapters.port import ChangePlan, ObservedTab

    default_blank = ObservedTab(
        title="Аркуш1",
        is_empty=True,
        is_default_blank=True,
    )
    notes = ObservedTab(title="Мої нотатки", is_empty=False)
    gateway = InMemoryWorkbookGateway(tabs=(default_blank, notes))

    result = gateway.apply(
        ChangePlan(blueprint=_blueprint(), clean_initialization=True)
    )

    assert "UNMANAGED_TAB_PRESENT" in result.statuses
    assert result.observed.unmanaged_tabs == (default_blank, notes)


def test_managed_fingerprint_ignores_provider_ids_and_positions() -> None:
    from workout_tracker.adapters.memory import InMemoryWorkbookGateway
    from workout_tracker.adapters.port import ObservedTab

    blueprint = _blueprint()
    first_variant = tuple(
        ObservedTab(
            logical_key=tab.logical_key,
            title=tab.title,
            owner=tab.owner,
            authority_role=tab.authority_role,
            source_schema_tab=tab.source_schema_tab,
            provider_id=f"first-provider-{index}",
            provider_position=index,
        )
        for index, tab in enumerate(blueprint.tabs, start=1)
    )
    second_variant = tuple(
        ObservedTab(
            logical_key=tab.logical_key,
            title=tab.title,
            owner=tab.owner,
            authority_role=tab.authority_role,
            source_schema_tab=tab.source_schema_tab,
            provider_id=f"second-provider-{index}",
            provider_position=100 - index,
        )
        for index, tab in enumerate(reversed(blueprint.tabs), start=1)
    )
    first = InMemoryWorkbookGateway(tabs=first_variant).observe()
    second = InMemoryWorkbookGateway(tabs=second_variant).observe()

    assert second.managed_fingerprint == first.managed_fingerprint
    assert tuple(tab.logical_key for tab in second.managed_tabs) == tuple(
        tab.logical_key for tab in first.managed_tabs
    )


def test_repeat_apply_is_logically_idempotent() -> None:
    from workout_tracker.adapters.memory import InMemoryWorkbookGateway
    from workout_tracker.adapters.port import ChangePlan

    gateway = InMemoryWorkbookGateway()
    plan = ChangePlan(blueprint=_blueprint())

    first = gateway.apply(plan)
    second = gateway.apply(plan)

    assert first.changed is True
    assert second.changed is False
    assert second.observed.managed_fingerprint == first.observed.managed_fingerprint
