from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4

from workout_tracker.adapters.memory import (
    InMemoryWorkbookGateway,
    ReconciliationConflictError,
    StaleObservedStateError,
)
from workout_tracker.adapters.port import (
    AllocateReserveId,
    ApplyResult,
    ChangePlan,
    ObservedManagedObject,
    ObservedTab,
    ObservedWorkbook,
)
from workout_tracker.workbook.reconcile import canonicalize_managed_state
from workout_tracker.workbook.requests import compile_google_requests


DESIRED_LOCALE = "uk_UA"
DESIRED_TIME_ZONE = "America/New_York"
MINIMUM_SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"
_OWNER = "workout_tracker"


class GoogleSheetsGatewayError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class GoogleUATPreflight:
    explicit_apply: bool
    source_alias: str
    expected_title: str
    disposable: bool
    spreadsheet_locator: str
    client_secret_file: Path
    token_file: Path
    desired_locale: str = DESIRED_LOCALE
    desired_time_zone: str = DESIRED_TIME_ZONE

    def validate_local(self, *, require_apply: bool) -> None:
        if require_apply and not self.explicit_apply:
            raise GoogleSheetsGatewayError("EXPLICIT_APPLY_REQUIRED")
        if (
            self.desired_locale != DESIRED_LOCALE
            or self.desired_time_zone != DESIRED_TIME_ZONE
        ):
            raise GoogleSheetsGatewayError(
                "DESIRED_WORKBOOK_PROPERTIES_INVALID"
            )
        if (
            not self.disposable
            or not self.source_alias
            or "test" not in self.source_alias.lower()
            or not self.expected_title
            or not self.spreadsheet_locator
        ):
            raise GoogleSheetsGatewayError("TARGET_PREFLIGHT_UNSAFE")
        _validate_secret_file(self.client_secret_file)
        _validate_secret_file(self.token_file)

    @classmethod
    def from_environment(cls, *, explicit_apply: bool) -> GoogleUATPreflight:
        required = {
            "source_alias": os.environ.get("WORKOUT_TEST_SOURCE_ALIAS"),
            "expected_title": os.environ.get("WORKOUT_TEST_EXPECTED_TITLE"),
            "spreadsheet_locator": os.environ.get("WORKOUT_TEST_SHEET_ID"),
            "client_secret_file": os.environ.get(
                "WORKOUT_GOOGLE_CLIENT_SECRET_FILE"
            ),
            "token_file": os.environ.get("WORKOUT_GOOGLE_TOKEN_FILE"),
        }
        if any(not value for value in required.values()):
            raise GoogleSheetsGatewayError("LOCAL_CONFIGURATION_MISSING")
        return cls(
            explicit_apply=explicit_apply,
            source_alias=str(required["source_alias"]),
            expected_title=str(required["expected_title"]),
            disposable=os.environ.get("WORKOUT_TEST_DISPOSABLE") == "1",
            spreadsheet_locator=str(required["spreadsheet_locator"]),
            client_secret_file=Path(str(required["client_secret_file"])),
            token_file=Path(str(required["token_file"])),
        )


def _mode(path: Path) -> int:
    try:
        return path.stat().st_mode & 0o777
    except OSError as exc:
        raise GoogleSheetsGatewayError("CREDENTIAL_FILE_UNAVAILABLE") from None


def _validate_secret_file(path: Path) -> None:
    if not path.is_file():
        raise GoogleSheetsGatewayError("CREDENTIAL_FILE_UNAVAILABLE")
    if _mode(path) != 0o600:
        raise GoogleSheetsGatewayError("CREDENTIAL_FILE_PERMISSIONS_UNSAFE")
    parent = path.parent
    if not parent.is_dir() or _mode(parent) != 0o700:
        raise GoogleSheetsGatewayError(
            "CREDENTIAL_DIRECTORY_PERMISSIONS_UNSAFE"
        )


def _load_installed_credentials(
    token_file: Path,
    client_secret_file: Path,
) -> object:
    try:
        client_config = json.loads(client_secret_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise GoogleSheetsGatewayError("OAUTH_CLIENT_CONFIG_INVALID") from None
    if (
        not isinstance(client_config, dict)
        or set(client_config) != {"installed"}
        or not isinstance(client_config["installed"], dict)
    ):
        raise GoogleSheetsGatewayError("OAUTH_CLIENT_TYPE_INVALID")

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        credentials = Credentials.from_authorized_user_file(
            str(token_file),
            scopes=[MINIMUM_SHEETS_SCOPE],
        )
        granted = set(credentials.scopes or ())
        if granted and granted != {MINIMUM_SHEETS_SCOPE}:
            raise GoogleSheetsGatewayError("OAUTH_SCOPE_UNSAFE")
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        if not credentials.valid:
            raise GoogleSheetsGatewayError("OAUTH_TOKEN_INVALID")
        return credentials
    except GoogleSheetsGatewayError:
        raise
    except Exception:
        raise GoogleSheetsGatewayError("GOOGLE_AUTH_FAILED") from None


def _build_service(credentials: object) -> object:
    try:
        from googleapiclient.discovery import build

        return build(
            "sheets",
            "v4",
            credentials=credentials,
            cache_discovery=False,
        )
    except Exception:
        raise GoogleSheetsGatewayError("GOOGLE_CLIENT_FAILED") from None


def _metadata_objects(
    metadata: list[dict[str, object]],
) -> tuple[ObservedManagedObject, ...]:
    result: list[ObservedManagedObject] = []
    for item in metadata:
        key = item.get("metadataKey")
        value = item.get("metadataValue")
        if (
            not isinstance(key, str)
            or not key.startswith(f"{_OWNER}:")
            or not isinstance(value, str)
        ):
            continue
        kind = key.removeprefix(f"{_OWNER}:")
        result.append(
            ObservedManagedObject(
                kind=kind,
                logical_key=value,
                payload=(),
                provider_id=str(item.get("metadataId", "")) or None,
            )
        )
    return tuple(result)


def _observe_from_google(
    service: object,
    preflight: GoogleUATPreflight,
) -> ObservedWorkbook:
    try:
        resource = (
            service.spreadsheets()  # type: ignore[attr-defined]
            .get(
                spreadsheetId=preflight.spreadsheet_locator,
                includeGridData=False,
                fields=(
                    "spreadsheetId,properties(title,locale,timeZone),"
                    "sheets(properties(sheetId,title,index)),"
                    "developerMetadata(metadataId,metadataKey,metadataValue,"
                    "visibility,location)"
                ),
            )
            .execute()
        )
    except Exception:
        raise GoogleSheetsGatewayError("GOOGLE_API_READ_FAILED") from None
    if not isinstance(resource, dict):
        raise GoogleSheetsGatewayError("GOOGLE_RESPONSE_INVALID")
    properties = resource.get("properties")
    if not isinstance(properties, dict):
        raise GoogleSheetsGatewayError("GOOGLE_RESPONSE_INVALID")
    if (
        resource.get("spreadsheetId") != preflight.spreadsheet_locator
        or properties.get("title") != preflight.expected_title
    ):
        raise GoogleSheetsGatewayError("TARGET_IDENTITY_MISMATCH")

    metadata = resource.get("developerMetadata", [])
    if not isinstance(metadata, list):
        raise GoogleSheetsGatewayError("GOOGLE_RESPONSE_INVALID")
    logical_by_sheet: dict[int, str] = {}
    for item in metadata:
        if not isinstance(item, dict):
            continue
        location = item.get("location")
        if (
            item.get("metadataKey") == f"{_OWNER}:tab"
            and isinstance(item.get("metadataValue"), str)
            and isinstance(location, dict)
            and isinstance(location.get("sheetId"), int)
        ):
            logical_by_sheet[location["sheetId"]] = str(
                item["metadataValue"]
            )
    sheets = resource.get("sheets", [])
    if not isinstance(sheets, list):
        raise GoogleSheetsGatewayError("GOOGLE_RESPONSE_INVALID")
    tabs: list[ObservedTab] = []
    for sheet in sheets:
        sheet_properties = (
            sheet.get("properties") if isinstance(sheet, dict) else None
        )
        if not isinstance(sheet_properties, dict):
            continue
        sheet_id = sheet_properties.get("sheetId")
        logical_key = (
            logical_by_sheet.get(sheet_id)
            if isinstance(sheet_id, int)
            else None
        )
        tabs.append(
            ObservedTab(
                title=str(sheet_properties.get("title", "")),
                logical_key=logical_key,
                owner=_OWNER if logical_key else None,
                provider_id=str(sheet_id) if sheet_id is not None else None,
                provider_position=(
                    int(sheet_properties["index"])
                    if isinstance(sheet_properties.get("index"), int)
                    else None
                ),
            )
        )
    snapshot = ObservedWorkbook(
        tabs=tuple(tabs),
        managed_fingerprint="",
        locale=(
            str(properties["locale"])
            if properties.get("locale") is not None
            else None
        ),
        time_zone=(
            str(properties["timeZone"])
            if properties.get("timeZone") is not None
            else None
        ),
        managed_objects=_metadata_objects(
            [item for item in metadata if isinstance(item, dict)]
        ),
    )
    return ObservedWorkbook(
        tabs=snapshot.tabs,
        managed_fingerprint=canonicalize_managed_state(snapshot),
        locale=snapshot.locale,
        time_zone=snapshot.time_zone,
        managed_objects=snapshot.managed_objects,
    )


def _default_batch_executor(
    service: object,
    locator: str,
    requests: tuple[dict[str, object], ...],
) -> None:
    try:
        (
            service.spreadsheets()  # type: ignore[attr-defined]
            .batchUpdate(
                spreadsheetId=locator,
                body={
                    "requests": list(requests),
                    "includeSpreadsheetInResponse": False,
                },
            )
            .execute()
        )
    except Exception:
        raise GoogleSheetsGatewayError("GOOGLE_API_WRITE_FAILED") from None


def _uuid_sequence(values: tuple[UUID, ...]) -> Callable[[], UUID]:
    iterator: Iterator[UUID] = iter(values)
    return lambda: next(iterator)


class _CredentialsLoader(Protocol):
    def __call__(self, token_file: Path, client_secret_file: Path) -> object: ...


class GoogleSheetsGateway:
    def __init__(
        self,
        preflight: GoogleUATPreflight,
        *,
        credentials_loader: _CredentialsLoader = _load_installed_credentials,
        service_factory: Callable[[object], object] = _build_service,
        observed_loader: (
            Callable[[object, str], ObservedWorkbook] | None
        ) = None,
        batch_executor: (
            Callable[
                [object, str, tuple[dict[str, object], ...]],
                None,
            ]
            | None
        ) = None,
    ) -> None:
        self._preflight = preflight
        self._credentials_loader = credentials_loader
        self._service_factory = service_factory
        self._observed_loader = observed_loader
        self._batch_executor = batch_executor or _default_batch_executor
        self._service: object | None = None

    def _client(self, *, require_apply: bool) -> object:
        self._preflight.validate_local(require_apply=require_apply)
        if self._service is not None:
            return self._service
        try:
            credentials = self._credentials_loader(
                self._preflight.token_file,
                self._preflight.client_secret_file,
            )
            self._service = self._service_factory(credentials)
        except GoogleSheetsGatewayError:
            raise
        except Exception:
            raise GoogleSheetsGatewayError("GOOGLE_AUTH_FAILED") from None
        return self._service

    def observe(self) -> ObservedWorkbook:
        service = self._client(require_apply=False)
        if self._observed_loader is not None:
            try:
                return self._observed_loader(
                    service,
                    self._preflight.spreadsheet_locator,
                )
            except GoogleSheetsGatewayError:
                raise
            except Exception:
                raise GoogleSheetsGatewayError("GOOGLE_API_READ_FAILED") from None
        return _observe_from_google(service, self._preflight)

    def apply(self, plan: ChangePlan) -> ApplyResult:
        service = self._client(require_apply=True)
        before = self.observe()
        if plan.expected_fingerprint != before.managed_fingerprint:
            raise GoogleSheetsGatewayError("STALE_OBSERVED_FINGERPRINT")
        if plan.conflicts:
            raise GoogleSheetsGatewayError("RECONCILIATION_CONFLICT")

        generated = tuple(
            uuid4()
            for operation in plan.operations
            if isinstance(operation, AllocateReserveId)
        )
        if plan.desired_objects:
            simulator = InMemoryWorkbookGateway(
                tabs=before.tabs,
                managed_objects=before.managed_objects,
                reserve_bindings=before.reserve_bindings,
                used_program_version_ids=before.used_program_version_ids,
                locale=before.locale,
                time_zone=before.time_zone,
                uuid4_generator=_uuid_sequence(generated),
            )
            try:
                expected = simulator.apply(plan).observed
            except (StaleObservedStateError, ReconciliationConflictError):
                raise GoogleSheetsGatewayError(
                    "RECONCILIATION_CONFLICT"
                ) from None
        else:
            expected = ObservedWorkbook(
                tabs=before.tabs,
                managed_fingerprint="",
                locale=DESIRED_LOCALE,
                time_zone=DESIRED_TIME_ZONE,
                managed_objects=before.managed_objects,
                reserve_bindings=before.reserve_bindings,
                used_program_version_ids=before.used_program_version_ids,
            )

        allocated = {
            binding.slot_key: binding.value
            for binding in expected.reserve_bindings
            if binding.slot_key
            not in {item.slot_key for item in before.reserve_bindings}
        }
        headers = {
            str(dict(item.payload).get("tab_key")): tuple(
                dict(item.payload).get("column_order", ())
            )
            for item in plan.desired_objects
            if item.kind == "headers"
        }
        columns = {
            tab_key: {
                str(field): index
                for index, field in enumerate(fields)
            }
            for tab_key, fields in headers.items()
        }
        limits = {
            "tab:sessions": 1
            + sum(
                operation.entity == "session"
                for operation in plan.operations
                if isinstance(operation, AllocateReserveId)
            )
            + len(
                [
                    item
                    for item in before.reserve_bindings
                    if item.entity == "session"
                ]
            ),
            "tab:sets": 1
            + sum(
                operation.entity == "set"
                for operation in plan.operations
                if isinstance(operation, AllocateReserveId)
            )
            + len(
                [
                    item
                    for item in before.reserve_bindings
                    if item.entity == "set"
                ]
            ),
        }
        reserve_rows = {
            operation.slot_key: int(operation.slot_key.rsplit(":", 1)[1])
            for operation in plan.operations
            if isinstance(operation, AllocateReserveId)
        }
        provider_ids: dict[str, int | str] = {
            tab.logical_key: int(tab.provider_id)
            for tab in before.managed_tabs
            if tab.logical_key
            and tab.provider_id
            and tab.provider_id.isdigit()
        }
        batches = compile_google_requests(
            plan,
            provider_ids=provider_ids,
            column_indexes=columns,
            managed_row_limits=limits,
            reserve_rows=reserve_rows,
            reserve_values=allocated,
        )
        for batch in batches:
            self._batch_executor(
                service,
                self._preflight.spreadsheet_locator,
                batch.requests,
            )

        post = self.observe()
        if (
            post.locale != DESIRED_LOCALE
            or post.time_zone != DESIRED_TIME_ZONE
        ):
            raise GoogleSheetsGatewayError("POST_APPLY_PROPERTIES_MISMATCH")
        if plan.desired_objects and (
            post.managed_fingerprint != expected.managed_fingerprint
        ):
            raise GoogleSheetsGatewayError("COLLABORATOR_DRIFT_CONFLICT")
        return ApplyResult(
            observed=post,
            changed=bool(plan.operations),
            before_fingerprint=before.managed_fingerprint,
            after_fingerprint=post.managed_fingerprint,
            operation_count=len(plan.operations),
            operation_kinds=tuple(
                type(operation).__name__ for operation in plan.operations
            ),
        )


__all__ = [
    "DESIRED_LOCALE",
    "DESIRED_TIME_ZONE",
    "MINIMUM_SHEETS_SCOPE",
    "GoogleSheetsGateway",
    "GoogleSheetsGatewayError",
    "GoogleUATPreflight",
]
