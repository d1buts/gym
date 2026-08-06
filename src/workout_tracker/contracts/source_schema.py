from __future__ import annotations

import re
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class ContractValidationError(ValueError):
    """Privacy-safe repository contract failure."""

    def __init__(self, code: str, *, count: int, contract_sha256: str) -> None:
        self.code = code
        self.count = count
        self.contract_sha256 = contract_sha256
        super().__init__(
            f"{code}: count={count}; sha256={contract_sha256}"
        )


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RequiredSource(StrictModel):
    source: str
    required: bool


class ContractMetadata(StrictModel):
    id: str
    schema_version: str
    status: str
    effective_date: str
    documentation_locale: str
    spreadsheet_locale: RequiredSource
    spreadsheet_time_zone: RequiredSource
    encoding: str
    documentation: str


class SchemaVersion(StrictModel):
    current: str
    accepted: tuple[str, ...]
    pattern: str


class PatternVersion(StrictModel):
    current: str
    pattern: str


class ProgramVersion(StrictModel):
    pattern: str
    value_is_supplied_by: str


class Versions(StrictModel):
    schema_config: SchemaVersion = Field(alias="schema")
    program: ProgramVersion
    normalizer: PatternVersion
    formulas: PatternVersion

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )

    @property
    def schema(self) -> SchemaVersion:
        return self.schema_config


class SchemaAuthority(StrictModel):
    owner: Literal["git"]
    path: str


class ProgramAuthority(StrictModel):
    owner: Literal["google_sheets"]
    tab: str
    version_key: str
    human_bootstrap_sources: tuple[str, ...]
    git_mirror_if_created: str
    git_mirror_authoritative: Literal[False]


class TrainingFactsAuthority(StrictModel):
    owner: Literal["google_sheets"]
    tabs: tuple[str, ...]


class RecommendationAuthority(StrictModel):
    owner: Literal["google_sheets"]
    tab: str


class SheetCalculationAuthority(StrictModel):
    owner: Literal["google_sheets_formulas"]
    authoritative: Literal[False]
    use_as_analytical_evidence: Literal[False]


class LocalDerivedAuthority(StrictModel):
    owner: Literal["local_pipeline"]
    authoritative_for_source_facts: Literal[False]
    requires: tuple[str, ...]


class Authority(StrictModel):
    schema_config: SchemaAuthority = Field(alias="schema")
    program_prescriptions: ProgramAuthority
    training_facts: TrainingFactsAuthority
    recommendation_journal: RecommendationAuthority
    sheet_calculations: SheetCalculationAuthority
    local_derived_data: LocalDerivedAuthority

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )

    @property
    def schema(self) -> SchemaAuthority:
        return self.schema_config


class SpreadsheetIdPolicy(StrictModel):
    storage: str
    config_key: str
    value_in_contract: None


class SourceVersion(StrictModel):
    preferred: str
    fallback: str


class SourceConfig(StrictModel):
    system: Literal["google_sheets"]
    spreadsheet_id: SpreadsheetIdPolicy
    required_tabs: tuple[str, ...]
    header_row: int
    blank_cell_policy: Literal["null"]
    row_number_is_identity: bool
    source_version: SourceVersion


class Description(StrictModel):
    description: str


class DataClasses(StrictModel):
    source_fact: Description
    sheet_calculated: Description
    local_derived: Description


class PatternDefinition(StrictModel):
    pattern: str


class IdFormats(StrictModel):
    program_item_id: PatternDefinition
    program_version_id: PatternDefinition
    session_id: PatternDefinition
    set_id: PatternDefinition
    recommendation_id: PatternDefinition
    snapshot_id: PatternDefinition


class LegacyBackfill(StrictModel):
    mode: str
    persist_to_source_before_import: bool
    normalizer_must_not_backfill: bool


class IdPolicy(StrictModel):
    generation_owner: str
    immutable: bool
    row_position_forbidden: bool
    content_derived_fallback_forbidden: bool
    missing_id_action: str
    legacy_backfill: LegacyBackfill
    formats: IdFormats


class CompleteSnapshotAbsence(StrictModel):
    local_action: str
    source_fact_inference: str
    partial_snapshot_action: str


class RevisionPolicy(StrictModel):
    field: str
    first_revision: int
    increment_on_source_fact_change: bool
    entity_key: str
    immutable_local_version_key: tuple[str, ...]
    same_revision_different_payload: str
    lower_revision_after_higher_revision: str
    physical_delete_forbidden: bool
    deletion_representation: str
    complete_snapshot_absence: CompleteSnapshotAbsence


class WorkoutType(StrictModel):
    source_label: str
    internal_alias: str


class CanonicalWorkoutTypes(StrictModel):
    upper_strength: WorkoutType
    lower_strength: WorkoutType
    upper_hypertrophy: WorkoutType
    lower_hypertrophy: WorkoutType
    sheet_accepts_internal_alias: bool


class Enums(StrictModel):
    program_version_status: tuple[str, ...]
    program_item_status: tuple[str, ...]
    session_status: tuple[str, ...]
    set_status: tuple[str, ...]
    set_role: tuple[str, ...]
    measurement_kind: tuple[str, ...]
    laterality: tuple[str, ...]
    load_unit: tuple[str, ...]
    load_basis: tuple[str, ...]
    generated_by: tuple[str, ...]
    recommendation_scope: tuple[str, ...]
    recommendation_type: tuple[str, ...]
    recommendation_status: tuple[str, ...]
    recommendation_outcome: tuple[str, ...]


class TypeDefinition(StrictModel):
    type: str
    pattern: str | None = None
    format: str | None = None
    minimum: int | float | None = None
    max_length: int | None = None


class CommonTypes(StrictModel):
    schema_version: TypeDefinition
    program_version: TypeDefinition
    source_revision: TypeDefinition
    date: TypeDefinition
    datetime: TypeDefinition
    short_text: TypeDefinition
    long_text: TypeDefinition
    canonical_slug: TypeDefinition
    comparison_cohort_id: TypeDefinition
    sha256: TypeDefinition


class ColumnDefinition(StrictModel):
    field: str
    header: str
    nullable: bool
    data_class: Literal["source_fact", "sheet_calculated", "local_derived"]
    type: str | None = None
    type_ref: str | None = None
    pattern_ref: str | None = None
    enum_ref: str | None = None
    enum_source_ref: str | None = None
    schema_ref: str | None = None
    pattern: str | None = None
    allowed: tuple[str, ...] | None = None
    minimum: int | float | None = None
    exclusive_minimum: int | float | None = None
    maximum: int | float | None = None
    min_length: int | None = None
    max_length: int | None = None

    @model_validator(mode="after")
    def has_one_type_source(self) -> "ColumnDefinition":
        if (self.type is None) == (self.type_ref is None):
            raise ValueError("column requires exactly one type source")
        return self


class GroupEntity(StrictModel):
    name: str
    key: str
    invariant_fields: tuple[str, ...]


class SourceTab(StrictModel):
    title: str
    authority_role: str
    entity: str
    primary_key: str
    columns: tuple[ColumnDefinition, ...]
    group_entity: GroupEntity | None = None


class SheetTabs(StrictModel):
    program: SourceTab
    sessions: SourceTab
    sets: SourceTab
    recommendations: SourceTab


class LocalModelDefinition(StrictModel):
    data_class: Literal["local_derived"]
    fields: tuple[str, ...] | None = None
    identity_uses_source_row_number: bool | None = None
    primary_key: tuple[str, ...] | None = None
    component_side_values: tuple[str, ...] | None = None
    logical_set_credit: int | None = None
    required_lineage: tuple[str, ...] | None = None


class EvidenceProperty(StrictModel):
    type: str
    pattern_ref: str | None = None
    allowed: tuple[str, ...] | None = None
    min_length: int | None = None
    max_length: int | None = None


class EvidenceProperties(StrictModel):
    snapshot_id: EvidenceProperty
    entity_type: EvidenceProperty
    entity_id: EvidenceProperty


class EvidenceReference(StrictModel):
    type: Literal["object"]
    required: tuple[str, ...]
    properties: EvidenceProperties


class LocalModels(StrictModel):
    source_record_version: LocalModelDefinition
    set_component: LocalModelDefinition
    normalized_record: LocalModelDefinition
    metric_result: LocalModelDefinition
    evidence_reference: EvidenceReference


class RequireByMeasurement(StrictModel):
    repetitions: tuple[str, ...]
    duration: tuple[str, ...]
    repetitions_and_duration: tuple[str, ...]


class ConditionalRule(StrictModel):
    id: str
    entity: str
    when: str
    require: tuple[str, ...] | None = None
    assert_: str | None = Field(default=None, alias="assert")
    forbid: tuple[str, ...] | None = None
    require_by_measurement: RequireByMeasurement | None = None

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )


class Severity(StrictModel):
    accepted_into_mirror: bool
    scope: str
    advances_mirror_head: bool | None = None


class Severities(StrictModel):
    fatal: Severity
    error: Severity
    warning: Severity
    info: Severity


class ValidationRule(StrictModel):
    code: str
    severity: str
    applies_to: str
    condition: str


class ValidationPolicy(StrictModel):
    severity_order: tuple[str, ...]
    severities: Severities
    rules: tuple[ValidationRule, ...]


class SourceSchema(StrictModel):
    contract: ContractMetadata
    versions: Versions
    authority: Authority
    source: SourceConfig
    data_classes: DataClasses
    id_policy: IdPolicy
    revision_policy: RevisionPolicy
    canonical_workout_types: CanonicalWorkoutTypes
    enums: Enums
    common_types: CommonTypes
    sheet_tabs: SheetTabs
    local_models: LocalModels
    conditional_rules: tuple[ConditionalRule, ...]
    validation: ValidationPolicy

    def tab(self, key: str) -> SourceTab | None:
        return {
            "program": self.sheet_tabs.program,
            "sessions": self.sheet_tabs.sessions,
            "sets": self.sheet_tabs.sets,
            "recommendations": self.sheet_tabs.recommendations,
        }.get(key)


def _load_yaml(path: str | Path) -> tuple[Any, str]:
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
        return yaml.safe_load(raw), digest
    except yaml.YAMLError as exc:
        raise ContractValidationError(
            "CONTRACT_YAML_INVALID", count=1, contract_sha256=digest
        ) from exc


def _validate_source_semantics(schema: SourceSchema, digest: str) -> None:
    if schema.source.row_number_is_identity or not schema.id_policy.row_position_forbidden:
        raise ContractValidationError(
            "ROW_POSITION_USED_AS_IDENTITY", count=1, contract_sha256=digest
        )
    if (
        schema.contract.schema_version != schema.versions.schema.current
        or schema.contract.schema_version not in schema.versions.schema.accepted
    ):
        raise ContractValidationError(
            "SCHEMA_VERSION_UNSUPPORTED", count=1, contract_sha256=digest
        )
    if (
        re.fullmatch(
            schema.versions.schema.pattern,
            schema.versions.schema.current,
        )
        is None
        or re.fullmatch(
            schema.versions.normalizer.pattern,
            schema.versions.normalizer.current,
        )
        is None
        or re.fullmatch(
            schema.versions.formulas.pattern,
            schema.versions.formulas.current,
        )
        is None
    ):
        raise ContractValidationError(
            "VERSION_REFERENCE_INVALID", count=1, contract_sha256=digest
        )

    expected_tabs = (
        (
            schema.sheet_tabs.program,
            schema.authority.program_prescriptions.tab,
            "operational_program_prescriptions",
        ),
        (
            schema.sheet_tabs.sessions,
            schema.authority.training_facts.tabs[0],
            "training_facts",
        ),
        (
            schema.sheet_tabs.sets,
            schema.authority.training_facts.tabs[1],
            "training_facts",
        ),
        (
            schema.sheet_tabs.recommendations,
            schema.authority.recommendation_journal.tab,
            "recommendation_journal",
        ),
    )
    enum_names = set(Enums.model_fields)
    common_type_names = set(CommonTypes.model_fields)
    format_names = set(IdFormats.model_fields)
    for tab, expected_title, expected_role in expected_tabs:
        if tab.title != expected_title or tab.authority_role != expected_role:
            raise ContractValidationError(
                "OWNERSHIP_POLICY_INVALID", count=1, contract_sha256=digest
            )
        fields = [column.field for column in tab.columns]
        duplicate_count = len(fields) - len(set(fields))
        if duplicate_count:
            raise ContractValidationError(
                "DUPLICATE_LOGICAL_KEY",
                count=duplicate_count,
                contract_sha256=digest,
            )
        if tab.primary_key not in fields:
            raise ContractValidationError(
                "STABLE_ID_MISSING_OR_INVALID",
                count=1,
                contract_sha256=digest,
            )
        for column in tab.columns:
            if (
                column.type_ref is not None
                and column.type_ref.removeprefix("common_types.")
                not in common_type_names
            ):
                raise ContractValidationError(
                    "TYPE_REFERENCE_UNKNOWN", count=1, contract_sha256=digest
                )
            if (
                column.enum_ref is not None
                and column.enum_ref.removeprefix("enums.") not in enum_names
            ):
                raise ContractValidationError(
                    "ENUM_REFERENCE_UNKNOWN", count=1, contract_sha256=digest
                )
            if column.pattern_ref is not None:
                match = re.fullmatch(
                    r"id_policy\.formats\.([a-z][a-z0-9_]*)\.pattern",
                    column.pattern_ref,
                )
                version_pattern_ref = column.pattern_ref in {
                    "versions.formulas.pattern",
                    "versions.normalizer.pattern",
                }
                if not version_pattern_ref and (
                    match is None or match.group(1) not in format_names
                ):
                    raise ContractValidationError(
                        "PATTERN_REFERENCE_UNKNOWN",
                        count=1,
                        contract_sha256=digest,
                    )


def load_source_schema(path: str | Path) -> SourceSchema:
    payload, digest = _load_yaml(path)
    try:
        schema = SourceSchema.model_validate(payload)
    except ValidationError as exc:
        raise ContractValidationError(
            "CONTRACT_SHAPE_INVALID",
            count=exc.error_count(),
            contract_sha256=digest,
        ) from exc
    _validate_source_semantics(schema, digest)
    return schema
