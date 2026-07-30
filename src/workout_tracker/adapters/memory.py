from __future__ import annotations

import hashlib
import json

from workout_tracker.adapters.port import (
    ApplyResult,
    ChangePlan,
    ObservedTab,
    ObservedWorkbook,
)


_OWNER = "workout_tracker"
_UNMANAGED_TAB_PRESENT = "UNMANAGED_TAB_PRESENT"


def _is_managed(tab: ObservedTab) -> bool:
    return tab.owner == _OWNER and tab.logical_key is not None


def _managed_fingerprint(
    tabs: tuple[ObservedTab, ...],
    *,
    locale: str | None,
    time_zone: str | None,
) -> str:
    managed_state = [
        {
            "logical_key": tab.logical_key,
            "title": tab.title,
            "owner": tab.owner,
            "authority_role": tab.authority_role,
            "source_schema_tab": tab.source_schema_tab,
        }
        for tab in tabs
        if _is_managed(tab)
    ]
    payload = {
        "locale": locale,
        "time_zone": time_zone,
        "tabs": managed_state,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class InMemoryWorkbookGateway:
    def __init__(
        self,
        tabs: tuple[ObservedTab, ...] = (),
        *,
        locale: str | None = None,
        time_zone: str | None = None,
    ) -> None:
        self._tabs = tabs
        self._locale = locale
        self._time_zone = time_zone
        self._managed_order = tuple(
            sorted(
                tab.logical_key
                for tab in tabs
                if _is_managed(tab) and tab.logical_key is not None
            )
        )

    def _normalized_tabs(self) -> tuple[ObservedTab, ...]:
        order = {
            logical_key: index
            for index, logical_key in enumerate(self._managed_order)
        }
        managed = sorted(
            (tab for tab in self._tabs if _is_managed(tab)),
            key=lambda tab: (
                order.get(tab.logical_key or "", len(order)),
                tab.logical_key or "",
            ),
        )
        unmanaged = tuple(tab for tab in self._tabs if not _is_managed(tab))
        return (*managed, *unmanaged)

    def observe(self) -> ObservedWorkbook:
        normalized_tabs = self._normalized_tabs()
        return ObservedWorkbook(
            tabs=normalized_tabs,
            managed_fingerprint=_managed_fingerprint(
                normalized_tabs,
                locale=self._locale,
                time_zone=self._time_zone,
            ),
            locale=self._locale,
            time_zone=self._time_zone,
        )

    def apply(self, plan: ChangePlan) -> ApplyResult:
        before = self.observe()
        original_managed_order = tuple(
            tab.logical_key for tab in self._tabs if _is_managed(tab)
        )
        existing_managed = {
            tab.logical_key: tab
            for tab in self._tabs
            if _is_managed(tab)
        }
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

        desired_tabs = tuple(
            self._desired_tab(tab, existing_managed.get(tab.logical_key))
            for tab in plan.blueprint.tabs
        )
        desired_order = tuple(tab.logical_key for tab in desired_tabs)

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
            or original_managed_order != desired_order
            or before.unmanaged_tabs != observed.unmanaged_tabs
        )
        return ApplyResult(
            observed=observed,
            changed=changed,
            statuses=statuses,
        )

    @staticmethod
    def _desired_tab(tab, existing: ObservedTab | None) -> ObservedTab:
        return ObservedTab(
            logical_key=tab.logical_key,
            title=tab.title,
            owner=tab.owner,
            authority_role=tab.authority_role,
            source_schema_tab=tab.source_schema_tab,
            is_empty=True if existing is None else existing.is_empty,
            provider_id=None if existing is None else existing.provider_id,
            provider_position=(
                None if existing is None else existing.provider_position
            ),
        )
