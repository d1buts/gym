from __future__ import annotations

from workout_tracker.adapters.port import (
    ApplyResult,
    ChangePlan,
    ObservedTab,
    ObservedWorkbook,
)


class InMemoryWorkbookGateway:
    def __init__(self, tabs: tuple[ObservedTab, ...] = ()) -> None:
        self._tabs = tabs

    def observe(self) -> ObservedWorkbook:
        return ObservedWorkbook(
            tabs=self._tabs,
            managed_fingerprint=repr(self._tabs),
        )

    def apply(self, plan: ChangePlan) -> ApplyResult:
        return ApplyResult(observed=self.observe(), changed=False)
