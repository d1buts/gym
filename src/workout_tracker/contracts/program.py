from __future__ import annotations

import json
import re
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
from uuid import UUID

import yaml
from pydantic import Field, ValidationError, field_validator, model_validator

from workout_tracker.contracts.source_schema import (
    ContractValidationError,
    SourceSchema,
    StrictModel,
)


_ID_NAMESPACE = UUID("46de4809-02f2-4a92-8e55-c1a9d98c3f59")
_SENTINEL_SLUGS = frozenset(
    {"standard", "unspecified", "unknown", "bodyweight"}
)
_EXPECTED_COUNTS = {
    "upper_strength": 8,
    "lower_strength": 7,
    "upper_hypertrophy": 8,
    "lower_hypertrophy": 8,
}
_DEFINITION_FIELDS = (
    "workout_type",
    "block_code",
    "exercise_order",
    "exercise_family_id",
    "exercise_variant_id",
    "comparison_cohort_id",
    "equipment_id",
    "setup_id",
    "exercise_name",
    "primary_muscle_group_id",
    "set_role",
    "target_sets",
    "prescribed_optional",
    "measurement_kind",
    "laterality",
    "target_reps_min",
    "target_reps_max",
    "target_duration_seconds_min",
    "target_duration_seconds_max",
    "target_rir_min",
    "target_rir_max",
    "rest_seconds_min",
    "rest_seconds_max",
    "load_increment_value",
    "load_increment_unit",
    "load_increment_basis",
    "expected_implement_count",
    "priority",
    "technical_notes",
)


def _fail(code: str, digest: str, *, count: int = 1) -> None:
    raise ContractValidationError(
        code,
        count=count,
        contract_sha256=digest,
    )


def _deterministic_uuid(prefix: str, semantic_key: str) -> str:
    digest = sha256(f"{_ID_NAMESPACE}:{semantic_key}".encode()).digest()
    raw = bytearray(digest[:16])
    raw[6] = (raw[6] & 0x0F) | 0x40
    raw[8] = (raw[8] & 0x3F) | 0x80
    return f"{prefix}{UUID(bytes=bytes(raw))}"


def _semantic_key(
    bootstrap_version: str,
    workout_type: str,
    block_code: str,
    exercise_order: int,
) -> str:
    return (
        f"{bootstrap_version}:{workout_type}:"
        f"{block_code}:{exercise_order}"
    )


def program_definition_sha256(
    prescription: Mapping[str, Any],
) -> str:
    canonical = {
        field: prescription.get(field)
        for field in _DEFINITION_FIELDS
    }
    payload = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(payload.encode()).hexdigest()


class ProgramPrescription(StrictModel):
    program_item_id: str
    semantic_key: str
    source_file: str
    source_section: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    definition_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: str
    workout_type: str
    block_code: str = Field(pattern=r"^[A-Z][0-9]$")
    exercise_order: int = Field(ge=1, le=100)
    exercise_family_id: str = Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")
    exercise_variant_id: str = Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")
    comparison_cohort_id: str | None = Field(
        default=None,
        pattern=r"^coh_[0-9a-f]{64}$",
    )
    equipment_id: str | None = Field(
        default=None,
        pattern=r"^[a-z][a-z0-9_]{1,63}$",
    )
    setup_id: str | None = Field(
        default=None,
        pattern=r"^[a-z][a-z0-9_]{1,63}$",
    )
    exercise_name: str = Field(min_length=1, max_length=200)
    primary_muscle_group_id: str = Field(
        pattern=r"^[a-z][a-z0-9_]{1,63}$"
    )
    set_role: str
    target_sets: int = Field(ge=1, le=20)
    prescribed_optional: bool
    measurement_kind: str
    laterality: str
    target_reps_min: int | None = Field(default=None, ge=1, le=1000)
    target_reps_max: int | None = Field(default=None, ge=1, le=1000)
    target_duration_seconds_min: int | None = Field(
        default=None, gt=0, le=86400
    )
    target_duration_seconds_max: int | None = Field(
        default=None, gt=0, le=86400
    )
    target_rir_min: int = Field(ge=0, le=10)
    target_rir_max: int = Field(ge=0, le=10)
    rest_seconds_min: int | None = Field(default=None, ge=0, le=3600)
    rest_seconds_max: int | None = Field(default=None, ge=0, le=3600)
    load_increment_value: int | float | None = Field(
        default=None, gt=0, le=1000
    )
    load_increment_unit: str | None = None
    load_increment_basis: str | None = None
    expected_implement_count: int | None = Field(default=None, ge=1, le=8)
    priority: int = Field(ge=1, le=5)
    technical_notes: str | None = Field(default=None, max_length=5000)

    @field_validator("equipment_id", "setup_id")
    @classmethod
    def no_sentinel_slug(cls, value: str | None) -> str | None:
        if value in _SENTINEL_SLUGS:
            raise ValueError("sentinel program values are forbidden")
        return value

    @model_validator(mode="after")
    def ranges_and_measurement_are_consistent(self) -> "ProgramPrescription":
        if (self.rest_seconds_min is None) != (self.rest_seconds_max is None):
            raise ValueError("rest bounds must both be null or both present")
        if (
            self.rest_seconds_min is not None
            and self.rest_seconds_max is not None
            and self.rest_seconds_min > self.rest_seconds_max
        ):
            raise ValueError("rest minimum exceeds maximum")
        if self.target_rir_min > self.target_rir_max:
            raise ValueError("RIR minimum exceeds maximum")
        reps = (self.target_reps_min, self.target_reps_max)
        duration = (
            self.target_duration_seconds_min,
            self.target_duration_seconds_max,
        )
        if self.measurement_kind == "repetitions":
            if None in reps or any(value is not None for value in duration):
                raise ValueError("repetition target is invalid")
        elif self.measurement_kind == "duration":
            if None in duration or any(value is not None for value in reps):
                raise ValueError("duration target is invalid")
        else:
            raise ValueError("unsupported program measurement kind")
        if (
            self.target_reps_min is not None
            and self.target_reps_max is not None
            and self.target_reps_min > self.target_reps_max
        ):
            raise ValueError("repetition minimum exceeds maximum")
        if (
            self.target_duration_seconds_min is not None
            and self.target_duration_seconds_max is not None
            and self.target_duration_seconds_min
            > self.target_duration_seconds_max
        ):
            raise ValueError("duration minimum exceeds maximum")
        increment = (
            self.load_increment_value,
            self.load_increment_unit,
            self.load_increment_basis,
        )
        if any(value is not None for value in increment) and any(
            value is None for value in increment
        ):
            raise ValueError("load increment fields must be a complete triple")
        return self


class ProgramBootstrap(StrictModel):
    program_bootstrap_version: str = Field(
        pattern=r"^program-v[0-9]+\.[0-9]+\.[0-9]+$"
    )
    schema_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    id_namespace: str
    program_version_id: str
    program_version: str
    program_version_status: str
    source_revision: int = Field(ge=1)
    published_at: str
    prescriptions: tuple[ProgramPrescription, ...]


def _read_yaml(path: str | Path) -> tuple[dict[str, Any], str]:
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise ContractValidationError(
            "CONTRACT_READ_FAILED",
            count=1,
            contract_sha256="0" * 64,
        ) from exc
    digest = sha256(raw).hexdigest()
    try:
        payload = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ContractValidationError(
            "CONTRACT_YAML_INVALID",
            count=1,
            contract_sha256=digest,
        ) from exc
    if not isinstance(payload, dict):
        _fail("CONTRACT_SHAPE_INVALID", digest)
    return payload, digest


def _column_nullability(schema: SourceSchema, tab: str) -> dict[str, bool]:
    source_tab = schema.tab(tab)
    assert source_tab is not None
    return {column.field: column.nullable for column in source_tab.columns}


def _validate_schema_1_1(schema: SourceSchema, digest: str) -> None:
    if (
        schema.contract.schema_version != "1.1.0"
        or schema.versions.schema.current != "1.1.0"
    ):
        _fail("SCHEMA_VERSION_UNSUPPORTED", digest)
    program = _column_nullability(schema, "program")
    if any(
        not program[field]
        for field in (
            "rest_seconds_min",
            "rest_seconds_max",
            "equipment_id",
            "setup_id",
            "comparison_cohort_id",
        )
    ):
        _fail("PROGRAM_NULLABILITY_CONTRACT_INVALID", digest)
    performed_set = _column_nullability(schema, "sets")
    if any(
        performed_set[field]
        for field in ("equipment_id", "setup_id", "comparison_cohort_id")
    ):
        _fail("PERFORMED_SET_CONTRACT_WEAKENED", digest)


def _prevalidate_rows(
    payload: dict[str, Any],
    digest: str,
) -> list[dict[str, Any]]:
    rows = payload.get("prescriptions")
    if not isinstance(rows, list):
        _fail("CONTRACT_SHAPE_INVALID", digest)
    for row in rows:
        if not isinstance(row, dict):
            _fail("CONTRACT_SHAPE_INVALID", digest)
        for required_hash in ("source_sha256", "definition_sha256"):
            if required_hash not in row:
                _fail("CONTRACT_SHAPE_INVALID", digest)
        rest_min = row.get("rest_seconds_min")
        rest_max = row.get("rest_seconds_max")
        if (rest_min is None) != (rest_max is None):
            _fail("PROGRAM_REST_PAIR_INVALID", digest)
        if (
            rest_min is not None
            and rest_max is not None
            and rest_min > rest_max
        ):
            _fail("PROGRAM_REST_RANGE_INVALID", digest)
        if any(
            row.get(field) in _SENTINEL_SLUGS
            for field in ("equipment_id", "setup_id")
        ):
            _fail("PROGRAM_SENTINEL_VALUE_FORBIDDEN", digest)
        if (
            row.get("comparison_cohort_id") is not None
            and (
                row.get("equipment_id") is None
                or row.get("setup_id") is None
            )
        ):
            _fail("PROGRAM_COHORT_WITHOUT_SETUP", digest)
    return rows


def _validate_source_hash(row: ProgramPrescription, digest: str) -> None:
    try:
        source_digest = sha256(Path(row.source_file).read_bytes()).hexdigest()
    except OSError:
        _fail("PROGRAM_SOURCE_UNAVAILABLE", digest)
    if source_digest != row.source_sha256:
        _fail("PROGRAM_SOURCE_HASH_MISMATCH", digest)


def _validate_semantics(
    bootstrap: ProgramBootstrap,
    digest: str,
    used_definition_hashes: Mapping[str, str] | None,
) -> None:
    if bootstrap.id_namespace != str(_ID_NAMESPACE):
        _fail("DETERMINISTIC_ID_NAMESPACE_MISMATCH", digest)
    if bootstrap.schema_version != "1.1.0":
        _fail("SCHEMA_VERSION_UNSUPPORTED", digest)
    expected_program_id = _deterministic_uuid(
        "pver_", bootstrap.program_bootstrap_version
    )
    if bootstrap.program_version_id != expected_program_id:
        _fail("DETERMINISTIC_ID_MISMATCH", digest)
    if (
        bootstrap.program_version != bootstrap.program_bootstrap_version
        or bootstrap.program_version_status != "active"
    ):
        _fail("PROGRAM_VERSION_METADATA_INVALID", digest)

    item_ids = [item.program_item_id for item in bootstrap.prescriptions]
    duplicate_count = len(item_ids) - len(set(item_ids))
    if duplicate_count:
        _fail("DUPLICATE_PROGRAM_ITEM_ID", digest, count=duplicate_count)
    counts = Counter(item.workout_type for item in bootstrap.prescriptions)
    if counts != _EXPECTED_COUNTS or len(bootstrap.prescriptions) != 31:
        _fail("PROGRAM_PRESCRIPTION_COUNT_INVALID", digest)

    for item in bootstrap.prescriptions:
        expected_key = _semantic_key(
            bootstrap.program_bootstrap_version,
            item.workout_type,
            item.block_code,
            item.exercise_order,
        )
        if re.search(r"(?:^|:)row(?:_|:)?[0-9]+", item.semantic_key):
            _fail("ROW_POSITION_USED_AS_IDENTITY", digest)
        if item.semantic_key != expected_key:
            mutable_tokens = {
                item.exercise_name.casefold().replace(" ", "_"),
                item.exercise_family_id,
                item.exercise_variant_id,
            }
            if any(token in item.semantic_key.casefold() for token in mutable_tokens):
                _fail("MUTABLE_TEXT_USED_AS_IDENTITY", digest)
            _fail("SEMANTIC_KEY_INVALID", digest)
        expected_item_id = _deterministic_uuid("prg_", expected_key)
        if item.program_item_id != expected_item_id:
            _fail("DETERMINISTIC_ID_MISMATCH", digest)
        _validate_source_hash(item, digest)
        computed_hash = program_definition_sha256(item.model_dump())
        if computed_hash != item.definition_sha256:
            _fail("PROGRAM_DEFINITION_HASH_MISMATCH", digest)
        if (
            used_definition_hashes is not None
            and item.program_item_id in used_definition_hashes
            and used_definition_hashes[item.program_item_id]
            != item.definition_sha256
        ):
            _fail("PROGRAM_VERSION_CONFLICT", digest)


def load_program_bootstrap(
    path: str | Path,
    source_schema: SourceSchema,
    *,
    used_definition_hashes: Mapping[str, str] | None = None,
) -> ProgramBootstrap:
    payload, digest = _read_yaml(path)
    _validate_schema_1_1(source_schema, digest)
    _prevalidate_rows(payload, digest)
    try:
        bootstrap = ProgramBootstrap.model_validate(payload)
    except ValidationError as exc:
        raise ContractValidationError(
            "CONTRACT_SHAPE_INVALID",
            count=exc.error_count(),
            contract_sha256=digest,
        ) from exc
    _validate_semantics(bootstrap, digest, used_definition_hashes)
    return bootstrap


__all__ = [
    "ProgramBootstrap",
    "ProgramPrescription",
    "load_program_bootstrap",
    "program_definition_sha256",
]
