from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path
from uuid import UUID

import pytest

from workout_tracker.contracts import (
    load_program_bootstrap,
    load_source_schema,
    load_workbook_blueprint,
)
from workout_tracker.workbook import compile_desired_workbook


SCHEMA_PATH = Path("config/schema.yaml")
BLUEPRINT_PATH = Path("config/workbook-blueprint.yaml")
PROGRAM_PATH = Path("config/program-bootstrap.yaml")
RECONCILE_PATH = Path("src/workout_tracker/workbook/reconcile.py")


def _desired():
    schema = load_source_schema(SCHEMA_PATH)
    blueprint = load_workbook_blueprint(BLUEPRINT_PATH, schema)
    program = load_program_bootstrap(PROGRAM_PATH, schema)
    return compile_desired_workbook(
        blueprint,
        schema,
        program,
        locale="uk_UA",
        time_zone="America/New_York",
    )


class _UuidSequence:
    def __init__(self) -> None:
        self.next_value = 0x100000

    def __call__(self) -> UUID:
        value = UUID(f"00000000-0000-4000-8000-{self.next_value:012x}")
        self.next_value += 1
        return value


def _require_reconciliation() -> None:
    assert RECONCILE_PATH.is_file(), "pure reconciliation behavior is missing"


def test_clean_apply_then_full_second_cycle_is_an_exact_noop() -> None:
    _require_reconciliation()
    from workout_tracker.adapters.memory import InMemoryWorkbookGateway
    from workout_tracker.adapters.port import AllocateReserveId
    from workout_tracker.workbook.reconcile import plan_setup

    desired = _desired()
    ids = _UuidSequence()
    gateway = InMemoryWorkbookGateway(uuid4_generator=ids)

    first_observed = gateway.observe()
    first_plan = plan_setup(desired, first_observed)
    first_result = gateway.apply(first_plan)
    first_post = gateway.observe()
    first_bindings = first_post.reserve_bindings

    assert len(
        [
            operation
            for operation in first_plan.operations
            if isinstance(operation, AllocateReserveId)
        ]
    ) == 128 + 2048
    assert first_result.before_fingerprint == first_observed.managed_fingerprint
    assert first_result.after_fingerprint == first_post.managed_fingerprint
    assert len({binding.value for binding in first_bindings}) == len(first_bindings)
    assert all(
        re.fullmatch(
            r"(?:ses|set)_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
            r"[89ab][0-9a-f]{3}-[0-9a-f]{12}",
            binding.value,
        )
        for binding in first_bindings
    )

    desired_again = _desired()
    second_plan = plan_setup(desired_again, gateway.observe())
    second_result = gateway.apply(second_plan)

    assert second_plan.operations == ()
    assert second_result.operation_count == 0
    assert second_result.changed is False
    assert gateway.observe().reserve_bindings == first_bindings
    assert gateway.observe().managed_fingerprint == first_post.managed_fingerprint


def test_partial_state_repairs_only_missing_keys_and_preserves_bindings() -> None:
    _require_reconciliation()
    from workout_tracker.adapters.memory import InMemoryWorkbookGateway
    from workout_tracker.adapters.port import AllocateReserveId, ReserveBinding
    from workout_tracker.workbook.reconcile import plan_setup

    desired = _desired()
    persisted = (
        ReserveBinding(
            entity="session",
            slot_key="reserve:session:001",
            value="ses_00000000-0000-4000-8000-000000000111",
            occupied=True,
        ),
        ReserveBinding(
            entity="set",
            slot_key="reserve:set:0001",
            value="set_00000000-0000-4000-8000-000000000222",
            occupied=False,
        ),
    )
    gateway = InMemoryWorkbookGateway(
        reserve_bindings=persisted,
        uuid4_generator=_UuidSequence(),
    )

    plan = plan_setup(desired, gateway.observe())
    allocations = tuple(
        operation
        for operation in plan.operations
        if isinstance(operation, AllocateReserveId)
    )
    result = gateway.apply(plan)

    assert len(allocations) == 128 + 2048 - len(persisted)
    assert not any(
        operation.slot_key in {binding.slot_key for binding in persisted}
        for operation in allocations
    )
    assert all(binding in result.observed.reserve_bindings for binding in persisted)
    assert plan_setup(desired, result.observed).operations == ()


def test_already_correct_state_and_provider_reordering_are_noops() -> None:
    _require_reconciliation()
    from workout_tracker.adapters.memory import InMemoryWorkbookGateway
    from workout_tracker.workbook.reconcile import plan_setup

    desired = _desired()
    gateway = InMemoryWorkbookGateway(uuid4_generator=_UuidSequence())
    gateway.apply(plan_setup(desired, gateway.observe()))
    correct = gateway.observe()

    reordered = tuple(
        replace(
            tab,
            provider_id=f"provider-{index}",
            provider_position=1000 - index,
        )
        for index, tab in enumerate(reversed(correct.tabs), start=1)
    )
    equivalent = InMemoryWorkbookGateway(
        tabs=reordered,
        managed_objects=tuple(reversed(correct.managed_objects)),
        reserve_bindings=tuple(reversed(correct.reserve_bindings)),
        locale=correct.locale,
        time_zone=correct.time_zone,
    ).observe()

    assert equivalent.managed_fingerprint == correct.managed_fingerprint
    assert plan_setup(desired, equivalent).operations == ()


def test_managed_drift_yields_one_logical_update_without_recreation() -> None:
    _require_reconciliation()
    from workout_tracker.adapters.memory import InMemoryWorkbookGateway
    from workout_tracker.adapters.port import UpdateManagedObject
    from workout_tracker.workbook.reconcile import plan_setup

    desired = _desired()
    gateway = InMemoryWorkbookGateway(uuid4_generator=_UuidSequence())
    gateway.apply(plan_setup(desired, gateway.observe()))
    correct = gateway.observe()
    target = next(
        item
        for item in correct.managed_objects
        if item.kind == "named_range"
    )
    drifted_target = replace(target, payload=(("drift", True),))
    drifted = InMemoryWorkbookGateway(
        tabs=correct.tabs,
        managed_objects=tuple(
            drifted_target if item == target else item
            for item in correct.managed_objects
        ),
        reserve_bindings=correct.reserve_bindings,
        locale=correct.locale,
        time_zone=correct.time_zone,
    ).observe()

    plan = plan_setup(desired, drifted)

    assert plan.operations == (
        UpdateManagedObject(
            kind=target.kind,
            logical_key=target.logical_key,
            payload=next(
                item.payload
                for item in plan.desired_objects
                if item.kind == target.kind
                and item.logical_key == target.logical_key
            ),
        ),
    )


def test_unowned_collision_is_explicit_and_never_broadly_removed() -> None:
    _require_reconciliation()
    from workout_tracker.adapters.memory import InMemoryWorkbookGateway
    from workout_tracker.adapters.port import (
        ObservedManagedObject,
        RemoveManagedObject,
    )
    from workout_tracker.workbook.reconcile import plan_setup

    desired = _desired()
    unowned = ObservedManagedObject(
        kind="named_range",
        logical_key="named_range:workout_types",
        payload=(("name", "personal_range"),),
        owner=None,
        provider_id="provider-object-9",
    )
    observed = InMemoryWorkbookGateway(managed_objects=(unowned,)).observe()

    plan = plan_setup(desired, observed)

    assert plan.conflicts == ("UNOWNED_LOGICAL_KEY_CONFLICT",)
    assert not any(
        isinstance(operation, RemoveManagedObject)
        for operation in plan.operations
    )
    assert unowned in observed.unmanaged_objects


def test_stale_observed_fingerprint_fails_before_any_apply() -> None:
    _require_reconciliation()
    from workout_tracker.adapters.memory import (
        InMemoryWorkbookGateway,
        StaleObservedStateError,
    )
    from workout_tracker.workbook.reconcile import plan_setup

    desired = _desired()
    gateway = InMemoryWorkbookGateway(uuid4_generator=_UuidSequence())
    stale_plan = plan_setup(desired, gateway.observe())
    gateway.inject_observed_drift(locale="en_US")

    with pytest.raises(StaleObservedStateError) as caught:
        gateway.apply(stale_plan)

    assert caught.value.code == "STALE_OBSERVED_FINGERPRINT"
    assert gateway.observe().managed_objects == ()
    assert gateway.observe().reserve_bindings == ()


def test_used_program_version_drift_is_preserved_as_conflict() -> None:
    _require_reconciliation()
    from workout_tracker.adapters.memory import InMemoryWorkbookGateway
    from workout_tracker.workbook.reconcile import plan_setup

    desired = _desired()
    gateway = InMemoryWorkbookGateway(uuid4_generator=_UuidSequence())
    gateway.apply(plan_setup(desired, gateway.observe()))
    correct = gateway.observe()
    target = next(
        item
        for item in correct.managed_objects
        if item.kind == "program_row"
    )
    version_id = dict(target.payload)["values"]
    program_version_id = dict(version_id)["program_version_id"]
    drifted_target = replace(target, payload=(("drift", True),))
    drifted = InMemoryWorkbookGateway(
        tabs=correct.tabs,
        managed_objects=tuple(
            drifted_target if item == target else item
            for item in correct.managed_objects
        ),
        reserve_bindings=correct.reserve_bindings,
        used_program_version_ids=(program_version_id,),
        locale=correct.locale,
        time_zone=correct.time_zone,
    ).observe()

    plan = plan_setup(desired, drifted)

    assert plan.conflicts == ("USED_PROGRAM_VERSION_IMMUTABLE",)
    assert plan.operations == ()
