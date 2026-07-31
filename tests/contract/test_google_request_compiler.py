from __future__ import annotations

from pathlib import Path

import pytest

from workout_tracker.adapters.port import (
    AddManagedObject,
    AllocateReserveId,
    ChangePlan,
    RemoveManagedObject,
    UpdateManagedObject,
)
from workout_tracker.workbook.reconcile import canonical_payload


REQUESTS_PATH = Path("src/workout_tracker/workbook/requests.py")


def _require_request_compiler() -> None:
    assert REQUESTS_PATH.is_file(), "typed Google request compiler is missing"


def _plan(*operations) -> ChangePlan:
    return ChangePlan(
        expected_fingerprint="a" * 64,
        operations=tuple(operations),
    )


def test_compiler_emits_only_allowlisted_requests_with_exact_masks() -> None:
    _require_request_compiler()
    from workout_tracker.workbook.requests import compile_google_requests

    plan = _plan(
        UpdateManagedObject(
            kind="workbook_properties",
            logical_key="workbook:properties",
            payload=canonical_payload(
                {"locale": "uk_UA", "time_zone": "America/New_York"}
            ),
        ),
        AddManagedObject(
            kind="tab",
            logical_key="tab:start",
            payload=canonical_payload(
                {
                    "logical_key": "tab:start",
                    "title": "Старт",
                    "authority_role": "user_interface",
                    "schema_key": None,
                    "headers": (),
                    "column_order": (),
                    "columns": (),
                }
            ),
        ),
        AddManagedObject(
            kind="headers",
            logical_key="headers:sessions",
            payload=canonical_payload(
                {
                    "tab_key": "tab:sessions",
                    "headers": ("Дата", "=UNTRUSTED"),
                    "column_order": ("session_date", "notes"),
                    "columns": (),
                }
            ),
        ),
    )

    batches = compile_google_requests(
        plan,
        provider_ids={"tab:start": 100, "tab:sessions": 101},
    )
    requests = tuple(
        request for batch in batches for request in batch.requests
    )

    assert tuple(tuple(request) for request in requests) == (
        ("updateSpreadsheetProperties",),
        ("addSheet",),
        ("updateCells",),
    )
    assert requests[0]["updateSpreadsheetProperties"]["fields"] == (
        "locale,timeZone"
    )
    assert requests[1]["addSheet"]["properties"]["title"] == "Старт"
    assert requests[2]["updateCells"]["fields"] == (
        "userEnteredValue.stringValue"
    )
    assert requests[2]["updateCells"]["rows"][0]["values"][1] == {
        "userEnteredValue": {"stringValue": "=UNTRUSTED"}
    }
    assert "*" not in repr(requests)
    assert "drive" not in repr(requests).lower()
    assert "permission" not in repr(requests).lower()
    assert "sharing" not in repr(requests).lower()


def test_formula_channel_uses_only_the_pinned_registry() -> None:
    _require_request_compiler()
    from workout_tracker.workbook.requests import (
        GoogleRequestCompilationError,
        compile_google_requests,
    )

    valid = AddManagedObject(
        kind="formula",
        logical_key="formula:sessions:completion",
        payload=canonical_payload(
            {
                "logical_key": "formula:sessions:completion",
                "tab": "Сесії",
                "formula_id": "session_completion_v1",
                "formula_version": "metrics-v1",
                "value_field": "observed_set_count_sheet",
                "status_field": "risk_flags_sheet",
                "unit_field": None,
            }
        ),
    )
    request = compile_google_requests(
        _plan(valid),
        provider_ids={"tab:sessions": 101},
        column_indexes={
            "tab:sessions": {
                "session_id": 0,
                "status": 1,
                "expected_set_count": 2,
                "observed_set_count_sheet": 3,
            }
        },
        managed_row_limits={"tab:sessions": 129},
    )[0].requests[0]

    formula = request["updateCells"]["rows"][0]["values"][0][
        "userEnteredValue"
    ]["formulaValue"]
    assert formula.startswith('=LET(metric_version,"metrics-v1"')
    assert "{column:" not in formula
    assert request["updateCells"]["fields"] == (
        "userEnteredValue.formulaValue"
    )

    injected = UpdateManagedObject(
        kind="formula",
        logical_key="formula:sessions:completion",
        payload=canonical_payload(
            {
                "formula_id": "=IMPORTRANGE(\"foreign\",\"A1\")",
                "formula_version": "metrics-v1",
                "tab": "Сесії",
                "value_field": "observed_set_count_sheet",
            }
        ),
    )
    with pytest.raises(GoogleRequestCompilationError) as caught:
        compile_google_requests(_plan(injected))
    assert caught.value.code == "FORMULA_NOT_ALLOWLISTED"


def test_reserve_allocation_requires_an_apply_resolved_uuid4() -> None:
    _require_request_compiler()
    from workout_tracker.workbook.requests import (
        GoogleRequestCompilationError,
        compile_google_requests,
    )

    operation = AllocateReserveId(
        entity="session",
        slot_key="reserve:session:001",
    )
    with pytest.raises(GoogleRequestCompilationError) as caught:
        compile_google_requests(_plan(operation))
    assert caught.value.code == "RESERVE_VALUE_REQUIRED"

    request = compile_google_requests(
        _plan(operation),
        provider_ids={"tab:sessions": 101},
        column_indexes={"tab:sessions": {"session_id": 0}},
        reserve_rows={"reserve:session:001": 1},
        reserve_values={
            "reserve:session:001": (
                "ses_00000000-0000-4000-8000-000000000001"
            )
        },
    )[0].requests[0]
    assert request["updateCells"]["range"] == {
        "sheetId": 101,
        "startRowIndex": 1,
        "endRowIndex": 2,
        "startColumnIndex": 0,
        "endColumnIndex": 1,
    }
    assert request["updateCells"]["fields"] == (
        "userEnteredValue.stringValue"
    )


def test_unknown_changes_and_unowned_removal_fail_before_requests() -> None:
    _require_request_compiler()
    from workout_tracker.workbook.requests import (
        GoogleRequestCompilationError,
        compile_google_requests,
    )

    for operation, code in (
        (
            AddManagedObject(
                kind="arbitrary_range",
                logical_key="range:foreign",
                payload=canonical_payload({"a1": "A:Z"}),
            ),
            "CHANGE_KIND_NOT_ALLOWLISTED",
        ),
        (
            RemoveManagedObject(
                kind="tab",
                logical_key="tab:foreign",
            ),
            "REMOVE_NOT_ALLOWLISTED",
        ),
    ):
        with pytest.raises(GoogleRequestCompilationError) as caught:
            compile_google_requests(_plan(operation))
        assert caught.value.code == code
