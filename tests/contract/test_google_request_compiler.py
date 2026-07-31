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
GOOGLE_GATEWAY_PATH = Path(
    "src/workout_tracker/adapters/google_sheets.py"
)
CLI_PATH = Path("src/workout_tracker/cli.py")


def _require_request_compiler() -> None:
    assert REQUESTS_PATH.is_file(), "typed Google request compiler is missing"


def _require_google_gateway() -> None:
    assert GOOGLE_GATEWAY_PATH.is_file(), "guarded Google gateway is missing"
    assert CLI_PATH.is_file(), "credential-free setup CLI is missing"


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


def test_preflight_rejects_unsafe_permissions_before_authentication(
    tmp_path: Path,
) -> None:
    _require_google_gateway()
    from workout_tracker.adapters.google_sheets import (
        GoogleSheetsGateway,
        GoogleSheetsGatewayError,
        GoogleUATPreflight,
    )

    secure = tmp_path / "private"
    secure.mkdir(mode=0o700)
    client = secure / "client.json"
    token = secure / "token.json"
    client.write_text('{"installed": {}}', encoding="utf-8")
    token.write_text("{}", encoding="utf-8")
    client.chmod(0o644)
    token.chmod(0o600)
    calls: list[str] = []
    gate = GoogleUATPreflight(
        explicit_apply=True,
        source_alias="disposable_test",
        expected_title="Disposable test workbook",
        disposable=True,
        spreadsheet_locator="test-only-locator",
        client_secret_file=client,
        token_file=token,
    )
    gateway = GoogleSheetsGateway(
        gate,
        credentials_loader=lambda *_: calls.append("auth"),
        service_factory=lambda *_: calls.append("service"),
    )

    with pytest.raises(GoogleSheetsGatewayError) as caught:
        gateway.observe()

    assert caught.value.code == "CREDENTIAL_FILE_PERMISSIONS_UNSAFE"
    assert str(caught.value) == "CREDENTIAL_FILE_PERMISSIONS_UNSAFE"
    assert str(client) not in str(caught.value)
    assert calls == []

    client.chmod(0o600)
    secure.chmod(0o755)
    with pytest.raises(GoogleSheetsGatewayError) as caught:
        gateway.observe()
    assert caught.value.code == "CREDENTIAL_DIRECTORY_PERMISSIONS_UNSAFE"
    assert str(secure) not in str(caught.value)
    assert calls == []


def test_preflight_uses_fixed_properties_and_minimum_sheets_scope_only(
    tmp_path: Path,
) -> None:
    _require_google_gateway()
    from workout_tracker.adapters.google_sheets import (
        DESIRED_LOCALE,
        DESIRED_TIME_ZONE,
        MINIMUM_SHEETS_SCOPE,
        GoogleSheetsGatewayError,
        GoogleUATPreflight,
    )

    secure = tmp_path / "private"
    secure.mkdir(mode=0o700)
    client = secure / "client.json"
    token = secure / "token.json"
    client.write_text('{"installed": {}}', encoding="utf-8")
    token.write_text("{}", encoding="utf-8")
    client.chmod(0o600)
    token.chmod(0o600)

    assert DESIRED_LOCALE == "uk_UA"
    assert DESIRED_TIME_ZONE == "America/New_York"
    assert MINIMUM_SHEETS_SCOPE == (
        "https://www.googleapis.com/auth/spreadsheets"
    )
    assert "drive" not in MINIMUM_SHEETS_SCOPE

    invalid = GoogleUATPreflight(
        explicit_apply=True,
        source_alias="disposable_test",
        expected_title="Disposable test workbook",
        disposable=True,
        spreadsheet_locator="test-only-locator",
        client_secret_file=client,
        token_file=token,
        desired_locale="en_US",
    )
    with pytest.raises(GoogleSheetsGatewayError) as caught:
        invalid.validate_local(require_apply=True)
    assert caught.value.code == "DESIRED_WORKBOOK_PROPERTIES_INVALID"


def test_gateway_repairs_property_drift_but_requires_exact_post_state(
    tmp_path: Path,
) -> None:
    _require_google_gateway()
    from workout_tracker.adapters.google_sheets import (
        GoogleSheetsGateway,
        GoogleSheetsGatewayError,
        GoogleUATPreflight,
    )
    from workout_tracker.adapters.port import ObservedWorkbook

    secure = tmp_path / "private"
    secure.mkdir(mode=0o700)
    client = secure / "client.json"
    token = secure / "token.json"
    client.write_text('{"installed": {}}', encoding="utf-8")
    token.write_text("{}", encoding="utf-8")
    client.chmod(0o600)
    token.chmod(0o600)
    gate = GoogleUATPreflight(
        explicit_apply=True,
        source_alias="disposable_test",
        expected_title="Disposable test workbook",
        disposable=True,
        spreadsheet_locator="test-only-locator",
        client_secret_file=client,
        token_file=token,
    )
    before = ObservedWorkbook(
        tabs=(),
        managed_fingerprint="a" * 64,
        locale="en_US",
        time_zone="Etc/UTC",
    )
    still_drifted = ObservedWorkbook(
        tabs=(),
        managed_fingerprint="b" * 64,
        locale="en_US",
        time_zone="Etc/UTC",
    )
    observations = iter((before, still_drifted))
    gateway = GoogleSheetsGateway(
        gate,
        observed_loader=lambda _service, _locator: next(observations),
        credentials_loader=lambda *_: object(),
        service_factory=lambda *_: object(),
        batch_executor=lambda *_: None,
    )
    plan = _plan(
        UpdateManagedObject(
            kind="workbook_properties",
            logical_key="workbook:properties",
            payload=canonical_payload(
                {"locale": "uk_UA", "time_zone": "America/New_York"}
            ),
        )
    )

    with pytest.raises(GoogleSheetsGatewayError) as caught:
        gateway.apply(plan)

    assert caught.value.code == "POST_APPLY_PROPERTIES_MISMATCH"


def test_external_errors_and_cli_output_are_redacted(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _require_google_gateway()
    from workout_tracker.adapters.google_sheets import (
        GoogleSheetsGateway,
        GoogleSheetsGatewayError,
        GoogleUATPreflight,
    )
    from workout_tracker.cli import main

    assert main(["google-dry-run"]) == 0
    dry_run = capsys.readouterr().out
    assert "status" in dry_run
    for forbidden in ("token", "credential", "locator", "spreadsheet"):
        assert forbidden not in dry_run.lower()

    secure = tmp_path / "private"
    secure.mkdir(mode=0o700)
    client = secure / "client.json"
    token = secure / "token.json"
    client.write_text('{"installed": {}}', encoding="utf-8")
    token.write_text("{}", encoding="utf-8")
    client.chmod(0o600)
    token.chmod(0o600)
    sensitive = "raw-provider-body-and-test-locator"
    gate = GoogleUATPreflight(
        explicit_apply=True,
        source_alias="disposable_test",
        expected_title="Disposable test workbook",
        disposable=True,
        spreadsheet_locator="test-only-locator",
        client_secret_file=client,
        token_file=token,
    )
    gateway = GoogleSheetsGateway(
        gate,
        credentials_loader=lambda *_: (_ for _ in ()).throw(
            RuntimeError(sensitive)
        ),
    )

    with pytest.raises(GoogleSheetsGatewayError) as caught:
        gateway.observe()
    assert caught.value.code == "GOOGLE_AUTH_FAILED"
    assert sensitive not in str(caught.value)


def test_gateway_source_has_no_drive_or_service_account_fallback() -> None:
    _require_google_gateway()
    source = GOOGLE_GATEWAY_PATH.read_text(encoding="utf-8").lower()

    assert "service_account" not in source
    assert "drive.googleapis" not in source
    assert "permissions()." not in source
    assert "files()." not in source
