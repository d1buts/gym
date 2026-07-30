from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from workout_tracker.contracts import WorkbookBlueprint


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
class ObservedWorkbook:
    tabs: tuple[ObservedTab, ...]
    managed_fingerprint: str

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


@dataclass(frozen=True, slots=True)
class ChangePlan:
    blueprint: WorkbookBlueprint
    clean_initialization: bool = False


@dataclass(frozen=True, slots=True)
class ApplyResult:
    observed: ObservedWorkbook
    changed: bool
    statuses: tuple[str, ...] = ()


class WorkbookGateway(Protocol):
    def observe(self) -> ObservedWorkbook: ...

    def apply(self, plan: ChangePlan) -> ApplyResult: ...
