from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Mapping

from pydantic import BaseModel

from workout_tracker.adapters.port import (
    AddManagedObject,
    AllocateReserveId,
    CanonicalPayload,
    ChangeOperation,
    ChangePlan,
    ObservedManagedObject,
    ObservedWorkbook,
    RemoveManagedObject,
    UpdateManagedObject,
)
from workout_tracker.workbook.model import DesiredWorkbook


OWNER = "workout_tracker"
UNOWNED_LOGICAL_KEY_CONFLICT = "UNOWNED_LOGICAL_KEY_CONFLICT"
USED_PROGRAM_VERSION_IMMUTABLE = "USED_PROGRAM_VERSION_IMMUTABLE"

_KIND_ORDER = {
    "workbook_properties": 0,
    "tab": 1,
    "headers": 2,
    "program_row": 3,
    "start_link": 3,
    "reserve_slot": 3,
    "named_range": 4,
    "validation": 5,
    "layout": 5,
    "formula": 5,
    "protection": 6,
    "filter_view": 6,
    "dashboard": 6,
    "dashboard_filter": 6,
    "dashboard_helper": 6,
    "dashboard_chart": 7,
}
_TAB_ORDER = {
    "tab:start": 0,
    "tab:program": 1,
    "tab:sessions": 2,
    "tab:sets": 3,
    "tab:recommendations": 4,
    "tab:lookups": 5,
    "tab:dashboard": 6,
}


class ManagedStateError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _canonical_value(value: object) -> object:
    if isinstance(value, BaseModel):
        return _canonical_value(value.model_dump(mode="python"))
    if is_dataclass(value) and not isinstance(value, type):
        return _canonical_value(asdict(value))
    if isinstance(value, Enum):
        return _canonical_value(value.value)
    if isinstance(value, Mapping):
        return tuple(
            (str(key), _canonical_value(item))
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        )
    if isinstance(value, (tuple, list)):
        return tuple(_canonical_value(item) for item in value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def canonical_payload(value: object) -> CanonicalPayload:
    canonical = _canonical_value(value)
    if not isinstance(canonical, tuple) or any(
        not isinstance(item, tuple) or len(item) != 2
        for item in canonical
    ):
        raise TypeError("managed object payload must canonicalize to a mapping")
    return canonical


def _json_value(value: object) -> object:
    if (
        isinstance(value, tuple)
        and all(
            isinstance(item, tuple)
            and len(item) == 2
            and isinstance(item[0], str)
            for item in value
        )
    ):
        return {key: _json_value(item) for key, item in value}
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value


def canonicalize_managed_state(observed: ObservedWorkbook) -> str:
    managed_tabs = sorted(
        (
            {
                "logical_key": tab.logical_key,
                "title": tab.title,
                "owner": tab.owner,
                "authority_role": tab.authority_role,
                "source_schema_tab": tab.source_schema_tab,
            }
            for tab in observed.managed_tabs
        ),
        key=lambda item: str(item["logical_key"]),
    )
    managed_objects = sorted(
        (
            {
                "kind": item.kind,
                "logical_key": item.logical_key,
                "payload": _json_value(item.payload),
                "owner": item.owner,
            }
            for item in observed.managed_objects
            if item.owner == OWNER and item.kind != "tab"
        ),
        key=lambda item: (str(item["kind"]), str(item["logical_key"])),
    )
    bindings = sorted(
        (
            {
                "entity": binding.entity,
                "slot_key": binding.slot_key,
                "value": binding.value,
                "occupied": binding.occupied,
            }
            for binding in observed.reserve_bindings
        ),
        key=lambda item: (str(item["entity"]), str(item["slot_key"])),
    )
    payload = {
        "locale": observed.locale,
        "time_zone": observed.time_zone,
        "tabs": managed_tabs,
        "objects": managed_objects,
        "reserve_bindings": bindings,
        "used_program_version_ids": sorted(observed.used_program_version_ids),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _object(kind: str, logical_key: str, value: object) -> ObservedManagedObject:
    return ObservedManagedObject(
        kind=kind,
        logical_key=logical_key,
        payload=canonical_payload(value),
    )


def _desired_objects(desired: DesiredWorkbook) -> tuple[ObservedManagedObject, ...]:
    objects: list[ObservedManagedObject] = [
        _object(
            "workbook_properties",
            "workbook:properties",
            {"locale": desired.locale, "time_zone": desired.time_zone},
        )
    ]
    for tab in desired.tabs:
        objects.append(_object("tab", tab.logical_key, tab))
        if tab.headers:
            objects.append(
                _object(
                    "headers",
                    f"headers:{tab.logical_key.split(':', 1)[1]}",
                    {
                        "tab_key": tab.logical_key,
                        "column_order": tab.column_order,
                        "headers": tab.headers,
                        "columns": tab.columns,
                    },
                )
            )
    objects.extend(
        _object("program_row", row.logical_key, row)
        for row in desired.program_rows
    )
    objects.extend(
        _object("named_range", item.logical_key, item)
        for item in desired.named_ranges
    )
    objects.extend(
        _object("filter_view", item.logical_key, item)
        for item in desired.filter_views
    )
    objects.extend(
        _object(
            "start_link",
            f"start_link:{item.filter_view_key.removeprefix('filter_view:')}",
            item,
        )
        for item in desired.start_links
    )
    objects.extend(
        _object("validation", item.logical_key, item)
        for item in desired.validations
    )
    objects.extend(
        _object("protection", item.logical_key, item)
        for item in desired.protections
    )
    objects.extend(
        _object("layout", item.logical_key, item)
        for item in desired.layouts
    )
    objects.extend(
        _object("formula", item.logical_key, item)
        for item in desired.formula_placements
    )
    objects.append(_object("dashboard", desired.dashboard.logical_key, desired.dashboard))
    objects.extend(
        _object("dashboard_filter", item.logical_key, item)
        for item in desired.dashboard.filters
    )
    objects.extend(
        _object("dashboard_helper", item.logical_key, item)
        for item in desired.dashboard.helper_ranges
    )
    objects.extend(
        _object("dashboard_chart", item.logical_key, item)
        for item in desired.dashboard.charts
    )
    for pool in desired.reserve_pools:
        objects.extend(
            _object(
                "reserve_slot",
                slot_key,
                {"entity": pool.entity, "slot_key": slot_key},
            )
            for slot_key in pool.slot_keys
        )
    return tuple(
        sorted(
            objects,
            key=lambda item: (
                _KIND_ORDER.get(item.kind, 99),
                item.kind,
                (
                    f"{_TAB_ORDER.get(item.logical_key, 999):03d}"
                    if item.kind == "tab"
                    else item.logical_key
                ),
            ),
        )
    )


def _index(
    objects: tuple[ObservedManagedObject, ...],
    *,
    owner: str | None,
) -> dict[tuple[str, str], ObservedManagedObject]:
    selected = tuple(item for item in objects if item.owner == owner)
    keys = tuple((item.kind, item.logical_key) for item in selected)
    if len(keys) != len(set(keys)):
        raise ManagedStateError("DUPLICATE_MANAGED_LOGICAL_KEY")
    return dict(zip(keys, selected, strict=True))


def _program_version_id(item: ObservedManagedObject) -> str | None:
    if item.kind != "program_row":
        return None
    values = dict(item.payload).get("values")
    if not isinstance(values, tuple):
        return None
    return dict(values).get("program_version_id")  # type: ignore[return-value]


def _operation_sort_key(operation: ChangeOperation) -> tuple[int, str, str, int]:
    kind = getattr(operation, "kind", "reserve_slot")
    logical_key = getattr(operation, "logical_key", getattr(operation, "slot_key", ""))
    action_order = {
        AddManagedObject: 0,
        UpdateManagedObject: 1,
        AllocateReserveId: 2,
        RemoveManagedObject: 3,
    }
    return (
        _KIND_ORDER.get(kind, 99),
        f"{_TAB_ORDER.get(logical_key, 999):03d}" if kind == "tab" else kind,
        logical_key,
        action_order[type(operation)],
    )


def plan_setup(
    desired: DesiredWorkbook,
    observed: ObservedWorkbook,
) -> ChangePlan:
    desired_objects = _desired_objects(desired)
    desired_index = {
        (item.kind, item.logical_key): item for item in desired_objects
    }
    if len(desired_index) != len(desired_objects):
        raise ManagedStateError("DUPLICATE_DESIRED_LOGICAL_KEY")

    managed = _index(observed.managed_objects, owner=OWNER)
    unowned = tuple(
        item for item in observed.managed_objects if item.owner != OWNER
    )
    conflicts: set[str] = set()
    desired_logical_keys = {item.logical_key for item in desired_objects}
    if any(item.logical_key in desired_logical_keys for item in unowned):
        conflicts.add(UNOWNED_LOGICAL_KEY_CONFLICT)

    operations: list[ChangeOperation] = []
    for key, desired_item in desired_index.items():
        if desired_item.kind in {"tab", "workbook_properties", "reserve_slot"}:
            continue
        current = managed.get(key)
        if current is None:
            operations.append(
                AddManagedObject(
                    kind=desired_item.kind,
                    logical_key=desired_item.logical_key,
                    payload=desired_item.payload,
                )
            )
        elif current.payload != desired_item.payload:
            version_id = _program_version_id(desired_item)
            if version_id in observed.used_program_version_ids:
                conflicts.add(USED_PROGRAM_VERSION_IMMUTABLE)
            else:
                operations.append(
                    UpdateManagedObject(
                        kind=desired_item.kind,
                        logical_key=desired_item.logical_key,
                        payload=desired_item.payload,
                    )
                )

    observed_tabs = {
        tab.logical_key: tab
        for tab in observed.managed_tabs
        if tab.logical_key is not None
    }
    for desired_tab in (item for item in desired_objects if item.kind == "tab"):
        current = observed_tabs.get(desired_tab.logical_key)
        if current is None:
            operations.append(
                AddManagedObject(
                    kind="tab",
                    logical_key=desired_tab.logical_key,
                    payload=desired_tab.payload,
                )
            )
        else:
            current_payload = canonical_payload(
                {
                    "logical_key": current.logical_key,
                    "title": current.title,
                    "authority_role": current.authority_role,
                    "schema_key": current.source_schema_tab,
                    "column_order": (),
                    "headers": (),
                    "columns": (),
                }
            )
            desired_tab_payload = dict(desired_tab.payload)
            comparable_desired = canonical_payload(
                {
                    "logical_key": desired_tab_payload["logical_key"],
                    "title": desired_tab_payload["title"],
                    "authority_role": desired_tab_payload["authority_role"],
                    "schema_key": desired_tab_payload["schema_key"],
                    "column_order": (),
                    "headers": (),
                    "columns": (),
                }
            )
            if current_payload != comparable_desired:
                operations.append(
                    UpdateManagedObject(
                        kind="tab",
                        logical_key=desired_tab.logical_key,
                        payload=desired_tab.payload,
                    )
                )

    properties = next(
        item for item in desired_objects if item.kind == "workbook_properties"
    )
    if (observed.locale, observed.time_zone) != (
        desired.locale,
        desired.time_zone,
    ):
        operations.append(
            UpdateManagedObject(
                kind=properties.kind,
                logical_key=properties.logical_key,
                payload=properties.payload,
            )
        )

    desired_reserve_slots = {
        item.logical_key: dict(item.payload)["entity"]
        for item in desired_objects
        if item.kind == "reserve_slot"
    }
    binding_by_slot = {
        binding.slot_key: binding for binding in observed.reserve_bindings
    }
    if len(binding_by_slot) != len(observed.reserve_bindings):
        raise ManagedStateError("DUPLICATE_RESERVE_SLOT")
    values = tuple(binding.value for binding in observed.reserve_bindings)
    if len(values) != len(set(values)):
        raise ManagedStateError("DUPLICATE_RESERVE_ID")
    for slot_key, entity in desired_reserve_slots.items():
        if slot_key not in binding_by_slot:
            operations.append(
                AllocateReserveId(entity=str(entity), slot_key=slot_key)
            )

    for key, current in managed.items():
        if current.kind in {"tab", "workbook_properties", "reserve_slot"}:
            continue
        if key not in desired_index:
            version_id = _program_version_id(current)
            if version_id in observed.used_program_version_ids:
                conflicts.add(USED_PROGRAM_VERSION_IMMUTABLE)
            else:
                operations.append(
                    RemoveManagedObject(
                        kind=current.kind,
                        logical_key=current.logical_key,
                    )
                )

    ordered_conflicts = tuple(sorted(conflicts))
    return ChangePlan(
        expected_fingerprint=observed.managed_fingerprint,
        operations=(
            ()
            if ordered_conflicts
            else tuple(sorted(operations, key=_operation_sort_key))
        ),
        conflicts=ordered_conflicts,
        desired_objects=desired_objects,
    )


__all__ = [
    "ManagedStateError",
    "canonicalize_managed_state",
    "plan_setup",
]
