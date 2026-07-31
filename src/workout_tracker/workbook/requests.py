from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Mapping

from workout_tracker.adapters.port import (
    AddManagedObject,
    AllocateReserveId,
    ChangeOperation,
    ChangePlan,
    RemoveManagedObject,
    UpdateManagedObject,
)
from workout_tracker.workbook.formulas import FORMULA_VERSION, FormulaRegistry


_ALLOWED_KINDS = frozenset(
    {
        "workbook_properties",
        "tab",
        "headers",
        "program_row",
        "start_link",
        "named_range",
        "validation",
        "layout",
        "formula",
        "protection",
        "filter_view",
        "dashboard",
        "dashboard_filter",
        "dashboard_helper",
        "dashboard_chart",
    }
)
_DEPENDENCY_ORDER = {
    "workbook_properties": 0,
    "tab": 1,
    "headers": 2,
    "program_row": 3,
    "start_link": 3,
    "named_range": 4,
    "validation": 5,
    "layout": 5,
    "formula": 5,
    "dashboard": 5,
    "dashboard_filter": 6,
    "dashboard_helper": 6,
    "protection": 7,
    "filter_view": 7,
    "dashboard_chart": 8,
    "reserve_slot": 9,
}
_REMOVE_REQUESTS = {
    "named_range": ("deleteNamedRange", "namedRangeId"),
    "protection": ("deleteProtectedRange", "protectedRangeId"),
    "filter_view": ("deleteFilterView", "filterId"),
    "dashboard_chart": ("deleteEmbeddedObject", "objectId"),
}
_RESERVE_ID = re.compile(
    r"^(?:ses|set)_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
_COLUMN_TOKEN = re.compile(r"\{column:([a-z][a-z0-9_]*)\}")


class GoogleRequestCompilationError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class GoogleRequestBatch:
    dependency: int
    requests: tuple[dict[str, object], ...]


def _payload(operation: AddManagedObject | UpdateManagedObject) -> dict[str, object]:
    return dict(operation.payload)


def _stable_provider_id(logical_key: str) -> int:
    value = int.from_bytes(
        hashlib.sha256(logical_key.encode("utf-8")).digest()[:4],
        "big",
    )
    return value & 0x7FFFFFFF


def _provider_id(
    logical_key: str,
    provider_ids: Mapping[str, int | str],
) -> int | str:
    return provider_ids.get(logical_key, _stable_provider_id(logical_key))


def _tab_key(value: str) -> str:
    aliases = {
        "Старт": "tab:start",
        "Програма": "tab:program",
        "Сесії": "tab:sessions",
        "Підходи": "tab:sets",
        "Рекомендації": "tab:recommendations",
        "Довідники": "tab:lookups",
        "Дашборд": "tab:dashboard",
    }
    return aliases.get(value, value if value.startswith("tab:") else f"tab:{value}")


def _cell(value: object) -> dict[str, object]:
    if value is None:
        return {}
    if isinstance(value, bool):
        return {"userEnteredValue": {"boolValue": value}}
    if isinstance(value, (int, float)):
        return {"userEnteredValue": {"numberValue": value}}
    return {"userEnteredValue": {"stringValue": str(value)}}


def _column_name(index: int) -> str:
    result = ""
    value = index + 1
    while value:
        value, remainder = divmod(value - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _formula_text(
    payload: Mapping[str, object],
    *,
    registry: FormulaRegistry,
    column_indexes: Mapping[str, Mapping[str, int]],
) -> str:
    formula_id = payload.get("formula_id")
    formula_version = payload.get("formula_version")
    if not isinstance(formula_id, str):
        raise GoogleRequestCompilationError("FORMULA_NOT_ALLOWLISTED")
    try:
        template = registry.get(formula_id)
    except KeyError as exc:
        raise GoogleRequestCompilationError("FORMULA_NOT_ALLOWLISTED") from exc
    if formula_version != FORMULA_VERSION or template.formula_version != formula_version:
        raise GoogleRequestCompilationError("FORMULA_VERSION_MISMATCH")
    tab_key = _tab_key(str(payload.get("tab", template.source_tab)))
    indexes = column_indexes.get(tab_key, {})

    def replace(match: re.Match[str]) -> str:
        field = match.group(1)
        if field not in indexes:
            raise GoogleRequestCompilationError("FORMULA_COLUMN_UNRESOLVED")
        column = _column_name(indexes[field])
        return f"${column}2:${column}"

    return _COLUMN_TOKEN.sub(replace, template.text)


def _grid_range(
    *,
    tab_key: str,
    provider_ids: Mapping[str, int | str],
    start_row: int,
    end_row: int,
    start_column: int,
    end_column: int,
) -> dict[str, object]:
    if min(start_row, start_column) < 0 or end_row <= start_row or end_column <= start_column:
        raise GoogleRequestCompilationError("MANAGED_RANGE_INVALID")
    return {
        "sheetId": _provider_id(tab_key, provider_ids),
        "startRowIndex": start_row,
        "endRowIndex": end_row,
        "startColumnIndex": start_column,
        "endColumnIndex": end_column,
    }


def _compile_formula(
    operation: AddManagedObject | UpdateManagedObject,
    *,
    provider_ids: Mapping[str, int | str],
    column_indexes: Mapping[str, Mapping[str, int]],
    managed_row_limits: Mapping[str, int],
    registry: FormulaRegistry,
) -> dict[str, object]:
    payload = _payload(operation)
    tab_key = _tab_key(str(payload.get("tab", "")))
    formula = _formula_text(
        payload,
        registry=registry,
        column_indexes=column_indexes,
    )
    indexes = column_indexes.get(tab_key, {})
    value_field = payload.get("value_field")
    if not isinstance(value_field, str) or value_field not in indexes:
        raise GoogleRequestCompilationError("FORMULA_TARGET_UNRESOLVED")
    end_row = managed_row_limits.get(tab_key)
    if end_row is None or end_row <= 1:
        raise GoogleRequestCompilationError("MANAGED_RANGE_REQUIRED")
    return {
        "updateCells": {
            "range": _grid_range(
                tab_key=tab_key,
                provider_ids=provider_ids,
                start_row=1,
                end_row=end_row,
                start_column=indexes[value_field],
                end_column=indexes[value_field] + 1,
            ),
            "rows": [
                {
                    "values": [
                        {"userEnteredValue": {"formulaValue": formula}}
                    ]
                }
            ],
            "fields": "userEnteredValue.formulaValue",
        }
    }


def _compile_add_or_update(
    operation: AddManagedObject | UpdateManagedObject,
    *,
    provider_ids: Mapping[str, int | str],
    column_indexes: Mapping[str, Mapping[str, int]],
    managed_row_limits: Mapping[str, int],
    managed_rows: Mapping[str, int],
    registry: FormulaRegistry,
) -> dict[str, object]:
    kind = operation.kind
    payload = _payload(operation)
    is_add = isinstance(operation, AddManagedObject)

    if kind == "workbook_properties":
        return {
            "updateSpreadsheetProperties": {
                "properties": {
                    "locale": payload.get("locale"),
                    "timeZone": payload.get("time_zone"),
                },
                "fields": "locale,timeZone",
            }
        }
    if kind == "tab":
        properties = {
            "sheetId": _provider_id(operation.logical_key, provider_ids),
            "title": payload.get("title"),
        }
        if is_add:
            return {"addSheet": {"properties": properties}}
        return {
            "updateSheetProperties": {
                "properties": properties,
                "fields": "title",
            }
        }
    if kind == "headers":
        tab_key = str(payload.get("tab_key"))
        headers = payload.get("headers")
        if not isinstance(headers, tuple):
            raise GoogleRequestCompilationError("RAW_VALUES_INVALID")
        return {
            "updateCells": {
                "range": _grid_range(
                    tab_key=tab_key,
                    provider_ids=provider_ids,
                    start_row=0,
                    end_row=1,
                    start_column=0,
                    end_column=len(headers),
                ),
                "rows": [{"values": [_cell(value) for value in headers]}],
                "fields": "userEnteredValue.stringValue",
            }
        }
    if kind == "program_row":
        values = payload.get("values")
        if not isinstance(values, tuple):
            raise GoogleRequestCompilationError("RAW_VALUES_INVALID")
        row = managed_rows.get(operation.logical_key)
        if row is None:
            raise GoogleRequestCompilationError("MANAGED_ROW_REQUIRED")
        return {
            "updateCells": {
                "range": _grid_range(
                    tab_key="tab:program",
                    provider_ids=provider_ids,
                    start_row=row,
                    end_row=row + 1,
                    start_column=0,
                    end_column=len(values),
                ),
                "rows": [
                    {"values": [_cell(value) for _, value in values]}
                ],
                "fields": (
                    "userEnteredValue.stringValue,"
                    "userEnteredValue.numberValue,"
                    "userEnteredValue.boolValue"
                ),
            }
        }
    if kind == "formula":
        return _compile_formula(
            operation,
            provider_ids=provider_ids,
            column_indexes=column_indexes,
            managed_row_limits=managed_row_limits,
            registry=registry,
        )

    metadata = {
        "metadataKey": f"workout_tracker:{kind}",
        "metadataValue": operation.logical_key,
        "visibility": "PROJECT",
    }
    if is_add:
        return {"createDeveloperMetadata": {"developerMetadata": metadata}}
    metadata_id = _provider_id(operation.logical_key, provider_ids)
    return {
        "updateDeveloperMetadata": {
            "dataFilters": [
                {"developerMetadataLookup": {"metadataId": metadata_id}}
            ],
            "developerMetadata": metadata,
            "fields": "metadataValue,visibility",
        }
    }


def _compile_remove(
    operation: RemoveManagedObject,
    *,
    provider_ids: Mapping[str, int | str],
) -> dict[str, object]:
    definition = _REMOVE_REQUESTS.get(operation.kind)
    provider_id = provider_ids.get(operation.logical_key)
    if definition is None or provider_id is None:
        raise GoogleRequestCompilationError("REMOVE_NOT_ALLOWLISTED")
    request_name, id_field = definition
    return {request_name: {id_field: provider_id}}


def _compile_reserve(
    operation: AllocateReserveId,
    *,
    provider_ids: Mapping[str, int | str],
    column_indexes: Mapping[str, Mapping[str, int]],
    reserve_rows: Mapping[str, int],
    reserve_values: Mapping[str, str],
) -> dict[str, object]:
    value = reserve_values.get(operation.slot_key)
    if value is None:
        raise GoogleRequestCompilationError("RESERVE_VALUE_REQUIRED")
    if not _RESERVE_ID.fullmatch(value):
        raise GoogleRequestCompilationError("RESERVE_VALUE_INVALID")
    tab_key = {
        "session": "tab:sessions",
        "set": "tab:sets",
    }.get(operation.entity)
    if tab_key is None:
        raise GoogleRequestCompilationError("RESERVE_ENTITY_NOT_ALLOWLISTED")
    field = f"{operation.entity}_id"
    indexes = column_indexes.get(tab_key, {})
    row = reserve_rows.get(operation.slot_key)
    if field not in indexes or row is None:
        raise GoogleRequestCompilationError("RESERVE_TARGET_UNRESOLVED")
    column = indexes[field]
    return {
        "updateCells": {
            "range": _grid_range(
                tab_key=tab_key,
                provider_ids=provider_ids,
                start_row=row,
                end_row=row + 1,
                start_column=column,
                end_column=column + 1,
            ),
            "rows": [{"values": [_cell(value)]}],
            "fields": "userEnteredValue.stringValue",
        }
    }


def compile_google_requests(
    plan: ChangePlan,
    *,
    provider_ids: Mapping[str, int | str] | None = None,
    column_indexes: Mapping[str, Mapping[str, int]] | None = None,
    managed_row_limits: Mapping[str, int] | None = None,
    managed_rows: Mapping[str, int] | None = None,
    reserve_rows: Mapping[str, int] | None = None,
    reserve_values: Mapping[str, str] | None = None,
    formula_registry: FormulaRegistry | None = None,
) -> tuple[GoogleRequestBatch, ...]:
    """Compile a fenced ChangePlan into dependency-ordered Sheets v4 requests.

    The function is pure: it does not authenticate, discover a service, resolve
    a spreadsheet locator, generate identifiers, or perform network I/O.
    """

    if plan.conflicts:
        raise GoogleRequestCompilationError("RECONCILIATION_CONFLICT")
    if plan.expected_fingerprint is None:
        raise GoogleRequestCompilationError("EXPECTED_FINGERPRINT_REQUIRED")
    ids = provider_ids or {}
    columns = column_indexes or {}
    limits = managed_row_limits or {}
    rows = dict(managed_rows or {})
    reserve_target_rows = reserve_rows or {}
    resolved_reserves = reserve_values or {}
    registry = formula_registry or FormulaRegistry.metrics_v1()

    program_operations = sorted(
        (
            operation
            for operation in plan.operations
            if isinstance(operation, (AddManagedObject, UpdateManagedObject))
            and operation.kind == "program_row"
            and operation.logical_key not in rows
        ),
        key=lambda operation: operation.logical_key,
    )
    rows.update(
        {
            operation.logical_key: index
            for index, operation in enumerate(program_operations, start=1)
        }
    )

    compiled: list[tuple[int, dict[str, object]]] = []
    for operation in plan.operations:
        if isinstance(operation, AllocateReserveId):
            request = _compile_reserve(
                operation,
                provider_ids=ids,
                column_indexes=columns,
                reserve_rows=reserve_target_rows,
                reserve_values=resolved_reserves,
            )
            dependency = _DEPENDENCY_ORDER["reserve_slot"]
        elif isinstance(operation, RemoveManagedObject):
            if operation.kind not in _ALLOWED_KINDS:
                raise GoogleRequestCompilationError("CHANGE_KIND_NOT_ALLOWLISTED")
            request = _compile_remove(operation, provider_ids=ids)
            dependency = _DEPENDENCY_ORDER[operation.kind]
        elif isinstance(operation, (AddManagedObject, UpdateManagedObject)):
            if operation.kind not in _ALLOWED_KINDS:
                raise GoogleRequestCompilationError("CHANGE_KIND_NOT_ALLOWLISTED")
            request = _compile_add_or_update(
                operation,
                provider_ids=ids,
                column_indexes=columns,
                managed_row_limits=limits,
                managed_rows=rows,
                registry=registry,
            )
            dependency = _DEPENDENCY_ORDER[operation.kind]
        else:
            raise GoogleRequestCompilationError("CHANGE_TYPE_NOT_ALLOWLISTED")
        if "*" in repr(request):
            raise GoogleRequestCompilationError("WILDCARD_FIELD_MASK_FORBIDDEN")
        compiled.append((dependency, request))

    batches: list[GoogleRequestBatch] = []
    for dependency in sorted({item[0] for item in compiled}):
        batches.append(
            GoogleRequestBatch(
                dependency=dependency,
                requests=tuple(
                    request
                    for item_dependency, request in compiled
                    if item_dependency == dependency
                ),
            )
        )
    return tuple(batches)


__all__ = [
    "GoogleRequestBatch",
    "GoogleRequestCompilationError",
    "compile_google_requests",
]
