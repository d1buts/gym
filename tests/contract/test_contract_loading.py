from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from workout_tracker.contracts import (
    ContractValidationError,
    load_source_schema,
    load_workbook_blueprint,
)


SCHEMA_PATH = Path("config/schema.yaml")


def _valid_blueprint() -> dict[str, object]:
    return {
        "workbook_contract_version": "1.0.0",
        "schema_version": "1.1.0",
        "formula_version": "metrics-v1",
        "program_bootstrap_version": "program-v1.0.0",
        "owner": "workout_tracker",
        "properties": {
            "locale": "uk_UA",
            "time_zone": "America/New_York",
        },
        "formula_registry": [
            {
                "formula_id": "session_status",
                "formula_version": "metrics-v1",
                "text": '=IF(A2="","",A2)',
            }
        ],
        "tabs": [
            {
                "logical_key": "tab:program",
                "title": "Програма",
                "owner": "workout_tracker",
                "authority_role": "operational_program_prescriptions",
                "source_schema_tab": "program",
                "managed_objects": [
                    {
                        "logical_key": "formula:program_status",
                        "kind": "formula",
                        "owner": "workout_tracker",
                        "source_column_refs": ["program_item_id"],
                        "formula_id": "session_status",
                    }
                ],
            },
            {
                "logical_key": "tab:start",
                "title": "Старт",
                "owner": "workout_tracker",
                "authority_role": "user_interface",
                "managed_objects": [],
            },
        ],
    }


def _write_yaml(path: Path, payload: object) -> Path:
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def test_valid_repository_contracts_load_as_frozen_typed_models(
    tmp_path: Path,
) -> None:
    source_schema = load_source_schema(SCHEMA_PATH)
    assert source_schema is not None
    blueprint = load_workbook_blueprint(
        _write_yaml(tmp_path / "blueprint.yaml", _valid_blueprint()),
        source_schema,
    )

    assert source_schema.contract.schema_version == "1.1.0"
    assert source_schema.sheet_tabs.program.columns[0].data_class == "source_fact"
    assert source_schema.sheet_tabs.sessions.columns[-1].data_class == "sheet_calculated"
    assert blueprint.tabs[0].managed_objects[0].formula_id == "session_status"

    with pytest.raises(ValidationError):
        source_schema.contract.schema_version = "2.0.0"
    with pytest.raises(ValidationError):
        blueprint.owner = "other"


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (lambda value: value.update({"unexpected": True}), "CONTRACT_SHAPE_INVALID"),
        (lambda value: value.pop("schema_version"), "CONTRACT_SHAPE_INVALID"),
        (
            lambda value: value.update({"schema_version": "9.9.9"}),
            "SCHEMA_VERSION_UNSUPPORTED",
        ),
        (
            lambda value: value["tabs"].append(deepcopy(value["tabs"][0])),
            "DUPLICATE_LOGICAL_KEY",
        ),
        (
            lambda value: value["tabs"][0].update({"logical_key": "tab:row_12"}),
            "ROW_POSITION_USED_AS_IDENTITY",
        ),
        (
            lambda value: value["tabs"][0].update({"owner": "google"}),
            "OWNERSHIP_POLICY_INVALID",
        ),
        (
            lambda value: value["tabs"][0]["managed_objects"][0].update(
                {"formula_id": "not_registered"}
            ),
            "FORMULA_NOT_REGISTERED",
        ),
        (
            lambda value: value["tabs"][0]["managed_objects"][0].update(
                {"source_column_refs": ["not_a_source_column"]}
            ),
            "SOURCE_COLUMN_UNKNOWN",
        ),
    ],
)
def test_blueprint_failures_are_closed_and_coded(
    tmp_path: Path,
    mutation,
    expected_code: str,
) -> None:
    payload = _valid_blueprint()
    mutation(payload)

    with pytest.raises(ContractValidationError) as raised:
        load_workbook_blueprint(
            _write_yaml(tmp_path / "invalid.yaml", payload),
            load_source_schema(SCHEMA_PATH),
        )

    assert raised.value.code == expected_code
    assert raised.value.count >= 1
    assert len(raised.value.contract_sha256) == 64


def test_source_schema_rejects_unknown_fields_and_row_identity(
    tmp_path: Path,
) -> None:
    payload = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    payload["sheet_tabs"]["program"]["columns"][0]["unexpected"] = "forbidden"

    with pytest.raises(ContractValidationError) as unknown:
        load_source_schema(_write_yaml(tmp_path / "unknown.yaml", payload))
    assert unknown.value.code == "CONTRACT_SHAPE_INVALID"

    payload = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    payload["source"]["row_number_is_identity"] = True
    with pytest.raises(ContractValidationError) as positional:
        load_source_schema(_write_yaml(tmp_path / "positional.yaml", payload))
    assert positional.value.code == "ROW_POSITION_USED_AS_IDENTITY"


def test_diagnostics_never_echo_contract_payload_or_sensitive_context(
    tmp_path: Path,
) -> None:
    payload = _valid_blueprint()
    payload["credential_path"] = "/private/oauth-client.json"
    payload["notes"] = "pain and health context must remain private"
    payload["token"] = "secret-token-value"
    path = _write_yaml(tmp_path / "live-sheet-locator.yaml", payload)

    with pytest.raises(ContractValidationError) as raised:
        load_workbook_blueprint(path, load_source_schema(SCHEMA_PATH))

    diagnostic = str(raised.value)
    assert raised.value.code == "CONTRACT_SHAPE_INVALID"
    assert "count=" in diagnostic
    assert "sha256=" in diagnostic
    for sensitive in (
        "oauth-client",
        "pain and health",
        "secret-token",
        "live-sheet-locator",
        "credential_path",
        "notes",
        "token",
    ):
        assert sensitive not in diagnostic
