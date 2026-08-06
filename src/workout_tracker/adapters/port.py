from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from workout_tracker.contracts import WorkbookBlueprint


CanonicalPayload = tuple[tuple[str, object], ...]


@dataclass(frozen=True, slots=True)
class ObservedTab:
    title: str
    logical_key: str | None = None
    owner: str | None = None
    authority_role: str | None = None
    source_schema_tab: str | None = None
    is_empty: bool = True
    is_default_blank: bool = False
    provider_id: str | None = None
    provider_position: int | None = None


@dataclass(frozen=True, slots=True)
class ObservedManagedObject:
    kind: str
    logical_key: str
    payload: CanonicalPayload
    owner: str | None = "workout_tracker"
    provider_id: str | None = None


@dataclass(frozen=True, slots=True)
class ReserveBinding:
    entity: str
    slot_key: str
    value: str
    occupied: bool = False


@dataclass(frozen=True, slots=True)
class ObservedWorkbook:
    tabs: tuple[ObservedTab, ...]
    managed_fingerprint: str
    locale: str | None = None
    time_zone: str | None = None
    managed_objects: tuple[ObservedManagedObject, ...] = ()
    reserve_bindings: tuple[ReserveBinding, ...] = ()
    used_program_version_ids: tuple[str, ...] = ()

    @property
    def managed_tabs(self) -> tuple[ObservedTab, ...]:
        return tuple(
            tab
            for tab in self.tabs
            if tab.owner == "workout_tracker" and tab.logical_key is not None
        )

    @property
    def unmanaged_tabs(self) -> tuple[ObservedTab, ...]:
        return tuple(tab for tab in self.tabs if tab not in self.managed_tabs)

    @property
    def unmanaged_objects(self) -> tuple[ObservedManagedObject, ...]:
        return tuple(
            item for item in self.managed_objects
            if item.owner != "workout_tracker"
        )


@dataclass(frozen=True, slots=True)
class AddManagedObject:
    kind: str
    logical_key: str
    payload: CanonicalPayload


@dataclass(frozen=True, slots=True)
class UpdateManagedObject:
    kind: str
    logical_key: str
    payload: CanonicalPayload


@dataclass(frozen=True, slots=True)
class RemoveManagedObject:
    kind: str
    logical_key: str


@dataclass(frozen=True, slots=True)
class AllocateReserveId:
    entity: str
    slot_key: str


ChangeOperation = (
    AddManagedObject
    | UpdateManagedObject
    | RemoveManagedObject
    | AllocateReserveId
)


@dataclass(frozen=True, slots=True)
class ChangePlan:
    blueprint: WorkbookBlueprint | None = None
    clean_initialization: bool = False
    expected_fingerprint: str | None = None
    operations: tuple[ChangeOperation, ...] = ()
    conflicts: tuple[str, ...] = ()
    desired_objects: tuple[ObservedManagedObject, ...] = ()


@dataclass(frozen=True, slots=True)
class ApplyResult:
    observed: ObservedWorkbook
    changed: bool
    statuses: tuple[str, ...] = ()
    before_fingerprint: str = ""
    after_fingerprint: str = ""
    operation_count: int = 0
    operation_kinds: tuple[str, ...] = ()
    status: str = "ok"


class WorkbookGateway(Protocol):
    def observe(self) -> ObservedWorkbook: ...

    def apply(self, plan: ChangePlan) -> ApplyResult: ...
