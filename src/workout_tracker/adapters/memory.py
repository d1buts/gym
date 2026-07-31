from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from uuid import UUID, uuid4

from workout_tracker.adapters.port import (
    AddManagedObject,
    AllocateReserveId,
    ApplyResult,
    ChangePlan,
    ObservedManagedObject,
    ObservedTab,
    ObservedWorkbook,
    RemoveManagedObject,
    ReserveBinding,
    UpdateManagedObject,
)
from workout_tracker.workbook.reconcile import canonicalize_managed_state


_OWNER = "workout_tracker"
_UNMANAGED_TAB_PRESENT = "UNMANAGED_TAB_PRESENT"
_TAB_ORDER = {
    "tab:start": 0,
    "tab:program": 1,
    "tab:sessions": 2,
    "tab:sets": 3,
    "tab:recommendations": 4,
    "tab:lookups": 5,
    "tab:dashboard": 6,
}


class StaleObservedStateError(RuntimeError):
    def __init__(self) -> None:
        self.code = "STALE_OBSERVED_FINGERPRINT"
        super().__init__(self.code)


class ReconciliationConflictError(RuntimeError):
    def __init__(self, conflicts: tuple[str, ...]) -> None:
        self.code = "RECONCILIATION_CONFLICT"
        self.conflicts = conflicts
        super().__init__(self.code)


class ReserveIdGenerationError(RuntimeError):
    def __init__(self) -> None:
        self.code = "RESERVE_ID_GENERATION_INVALID"
        super().__init__(self.code)


def _is_managed(tab: ObservedTab) -> bool:
    return tab.owner == _OWNER and tab.logical_key is not None


def _payload_dict(payload: tuple[tuple[str, object], ...]) -> dict[str, object]:
    return dict(payload)


def _desired_tab(
    payload: tuple[tuple[str, object], ...],
    existing: ObservedTab | None,
) -> ObservedTab:
    values = _payload_dict(payload)
    return ObservedTab(
        logical_key=str(values["logical_key"]),
        title=str(values["title"]),
        owner=_OWNER,
        authority_role=str(values["authority_role"]),
        source_schema_tab=(
            None if values["schema_key"] is None else str(values["schema_key"])
        ),
        is_empty=True if existing is None else existing.is_empty,
        provider_id=None if existing is None else existing.provider_id,
        provider_position=None if existing is None else existing.provider_position,
    )


class InMemoryWorkbookGateway:
    def __init__(
        self,
        tabs: tuple[ObservedTab, ...] = (),
        *,
        managed_objects: tuple[ObservedManagedObject, ...] = (),
        reserve_bindings: tuple[ReserveBinding, ...] = (),
        used_program_version_ids: tuple[str, ...] = (),
        locale: str | None = None,
        time_zone: str | None = None,
        uuid4_generator: Callable[[], UUID] = uuid4,
    ) -> None:
        self._tabs = tuple(tabs)
        self._managed_objects = tuple(managed_objects)
        self._reserve_bindings = tuple(reserve_bindings)
        self._used_program_version_ids = tuple(sorted(used_program_version_ids))
        self._locale = locale
        self._time_zone = time_zone
        self._uuid4_generator = uuid4_generator
        self._managed_order = tuple(
            tab.logical_key
            for tab in tabs
            if _is_managed(tab) and tab.logical_key is not None
        )

    def _normalized_tabs(self) -> tuple[ObservedTab, ...]:
        order = {
            logical_key: index
            for index, logical_key in enumerate(self._managed_order)
        }
        managed = sorted(
            (tab for tab in self._tabs if _is_managed(tab)),
            key=lambda tab: (
                _TAB_ORDER.get(
                    tab.logical_key or "",
                    order.get(tab.logical_key or "", len(order)) + len(_TAB_ORDER),
                ),
                tab.logical_key or "",
            ),
        )
        unmanaged = tuple(tab for tab in self._tabs if not _is_managed(tab))
        return (*managed, *unmanaged)

    def observe(self) -> ObservedWorkbook:
        normalized_tabs = self._normalized_tabs()
        normalized_objects = tuple(
            sorted(
                self._managed_objects,
                key=lambda item: (
                    item.owner or "",
                    item.kind,
                    item.logical_key,
                ),
            )
        )
        normalized_bindings = tuple(
            sorted(
                self._reserve_bindings,
                key=lambda item: (item.entity, item.slot_key),
            )
        )
        snapshot = ObservedWorkbook(
            tabs=normalized_tabs,
            managed_fingerprint="",
            locale=self._locale,
            time_zone=self._time_zone,
            managed_objects=normalized_objects,
            reserve_bindings=normalized_bindings,
            used_program_version_ids=self._used_program_version_ids,
        )
        return ObservedWorkbook(
            tabs=snapshot.tabs,
            managed_fingerprint=canonicalize_managed_state(snapshot),
            locale=snapshot.locale,
            time_zone=snapshot.time_zone,
            managed_objects=snapshot.managed_objects,
            reserve_bindings=snapshot.reserve_bindings,
            used_program_version_ids=snapshot.used_program_version_ids,
        )

    def inject_observed_drift(
        self,
        *,
        tabs: tuple[ObservedTab, ...] | None = None,
        locale: str | None = None,
        time_zone: str | None = None,
    ) -> None:
        if tabs is not None:
            self._tabs = (*self._tabs, *tabs)
        if locale is not None:
            self._locale = locale
        if time_zone is not None:
            self._time_zone = time_zone

    def apply(self, plan: ChangePlan) -> ApplyResult:
        if plan.expected_fingerprint is None:
            return self._apply_legacy_blueprint(plan)

        before = self.observe()
        if before.managed_fingerprint != plan.expected_fingerprint:
            raise StaleObservedStateError()
        if plan.conflicts:
            raise ReconciliationConflictError(plan.conflicts)

        tabs = list(self._tabs)
        objects = list(self._managed_objects)
        bindings = list(self._reserve_bindings)
        locale = self._locale
        time_zone = self._time_zone

        for operation in plan.operations:
            if isinstance(operation, AllocateReserveId):
                if any(item.slot_key == operation.slot_key for item in bindings):
                    continue
                generated = self._uuid4_generator()
                if not isinstance(generated, UUID) or generated.version != 4:
                    raise ReserveIdGenerationError()
                prefix = {"session": "ses_", "set": "set_"}.get(operation.entity)
                if prefix is None:
                    raise ReserveIdGenerationError()
                bindings.append(
                    ReserveBinding(
                        entity=operation.entity,
                        slot_key=operation.slot_key,
                        value=f"{prefix}{generated}",
                    )
                )
                continue

            if isinstance(operation, RemoveManagedObject):
                if operation.kind == "tab":
                    tabs = [
                        tab
                        for tab in tabs
                        if not (
                            _is_managed(tab)
                            and tab.logical_key == operation.logical_key
                        )
                    ]
                else:
                    objects = [
                        item
                        for item in objects
                        if not (
                            item.owner == _OWNER
                            and item.kind == operation.kind
                            and item.logical_key == operation.logical_key
                        )
                    ]
                continue

            if operation.kind == "workbook_properties":
                values = _payload_dict(operation.payload)
                locale = str(values["locale"])
                time_zone = str(values["time_zone"])
                continue

            if operation.kind == "tab":
                current = next(
                    (
                        tab
                        for tab in tabs
                        if _is_managed(tab)
                        and tab.logical_key == operation.logical_key
                    ),
                    None,
                )
                desired_tab = _desired_tab(operation.payload, current)
                tabs = [
                    tab
                    for tab in tabs
                    if not (
                        _is_managed(tab)
                        and tab.logical_key == operation.logical_key
                    )
                ]
                tabs.append(desired_tab)
                continue

            if isinstance(operation, (AddManagedObject, UpdateManagedObject)):
                existing = next(
                    (
                        item
                        for item in objects
                        if item.owner == _OWNER
                        and item.kind == operation.kind
                        and item.logical_key == operation.logical_key
                    ),
                    None,
                )
                objects = [
                    item
                    for item in objects
                    if not (
                        item.owner == _OWNER
                        and item.kind == operation.kind
                        and item.logical_key == operation.logical_key
                    )
                ]
                objects.append(
                    ObservedManagedObject(
                        kind=operation.kind,
                        logical_key=operation.logical_key,
                        payload=operation.payload,
                        provider_id=None if existing is None else existing.provider_id,
                    )
                )

        reserve_values = [item.value for item in bindings]
        if len(reserve_values) != len(set(reserve_values)):
            raise ReserveIdGenerationError()

        self._tabs = tuple(tabs)
        self._managed_order = tuple(
            item.logical_key
            for item in plan.desired_objects
            if item.kind == "tab"
        )
        self._managed_objects = tuple(objects)
        self._reserve_bindings = tuple(bindings)
        self._locale = locale
        self._time_zone = time_zone

        observed = self.observe()
        kinds = tuple(type(operation).__name__ for operation in plan.operations)
        statuses = (
            (_UNMANAGED_TAB_PRESENT,)
            if observed.unmanaged_tabs
            else ()
        )
        return ApplyResult(
            observed=observed,
            changed=bool(plan.operations),
            statuses=statuses,
            before_fingerprint=before.managed_fingerprint,
            after_fingerprint=observed.managed_fingerprint,
            operation_count=len(plan.operations),
            operation_kinds=tuple(
                f"{kind}:{count}"
                for kind, count in sorted(Counter(kinds).items())
            ),
            status="applied" if plan.operations else "noop",
        )

    def _apply_legacy_blueprint(self, plan: ChangePlan) -> ApplyResult:
        if plan.blueprint is None:
            raise ValueError("LEGACY_BLUEPRINT_MISSING")
        before = self.observe()
        unmanaged = tuple(tab for tab in self._tabs if not _is_managed(tab))
        if (
            plan.clean_initialization
            and len(self._tabs) == 1
            and len(unmanaged) == 1
            and unmanaged[0].is_default_blank
            and unmanaged[0].is_empty
            and unmanaged[0].owner is None
            and unmanaged[0].logical_key is None
        ):
            unmanaged = ()

        existing_managed = {
            tab.logical_key: tab
            for tab in self._tabs
            if _is_managed(tab)
        }
        desired_tabs = tuple(
            ObservedTab(
                logical_key=tab.logical_key,
                title=tab.title,
                owner=tab.owner,
                authority_role=tab.authority_role,
                source_schema_tab=tab.source_schema_tab,
                is_empty=(
                    True
                    if existing_managed.get(tab.logical_key) is None
                    else existing_managed[tab.logical_key].is_empty
                ),
                provider_id=(
                    None
                    if existing_managed.get(tab.logical_key) is None
                    else existing_managed[tab.logical_key].provider_id
                ),
                provider_position=(
                    None
                    if existing_managed.get(tab.logical_key) is None
                    else existing_managed[tab.logical_key].provider_position
                ),
            )
            for tab in plan.blueprint.tabs
        )
        self._tabs = (*desired_tabs, *unmanaged)
        self._managed_order = tuple(
            tab.logical_key
            for tab in desired_tabs
            if tab.logical_key is not None
        )
        self._locale = plan.blueprint.properties.locale
        self._time_zone = plan.blueprint.properties.time_zone
        observed = self.observe()
        statuses = (
            (_UNMANAGED_TAB_PRESENT,)
            if observed.unmanaged_tabs
            else ()
        )
        changed = (
            before.managed_fingerprint != observed.managed_fingerprint
            or before.unmanaged_tabs != observed.unmanaged_tabs
        )
        return ApplyResult(
            observed=observed,
            changed=changed,
            statuses=statuses,
            before_fingerprint=before.managed_fingerprint,
            after_fingerprint=observed.managed_fingerprint,
            operation_count=int(changed),
            operation_kinds=("LegacyBlueprintApply:1",) if changed else (),
            status="applied" if changed else "noop",
        )


__all__ = [
    "InMemoryWorkbookGateway",
    "ReconciliationConflictError",
    "ReserveIdGenerationError",
    "StaleObservedStateError",
]
