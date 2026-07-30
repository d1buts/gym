from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import ValidationError, model_validator

from workout_tracker.contracts.source_schema import (
    ContractValidationError,
    SourceSchema,
    StrictModel,
    _load_yaml,
)


OWNER = "workout_tracker"
AUTHORITY_ROLES = frozenset(
    {
        "operational_program_prescriptions",
        "training_facts",
        "recommendation_journal",
        "user_interface",
        "configuration_projection",
        "derived",
    }
)
IDENTITY_PART = re.compile(r"^[a-z][a-z0-9_]*$")
POSITIONAL_IDENTITY = re.compile(
    r"(^|_)(row|column|position|index|sheet_id|grid_id|google_id)(_|$)"
)


class WorkbookProperties(StrictModel):
    locale: str
    time_zone: str


class WorkoutAccent(StrictModel):
    internal_alias: str
    label: str
    color: str
    symbol: str


class Palette(StrictModel):
    background: str
    surface: str
    text: str
    muted_text: str
    input_fill: str
    system_fill: str
    border: str
    error_fill: str
    warning_fill: str
    success_fill: str
    workout_accents: tuple[WorkoutAccent, ...]


class ComplexLink(StrictModel):
    internal_alias: str
    label: str
    symbol: str
    target_filter_view: str
    tap_count: int


class RedactedStatus(StrictModel):
    label: str
    allowed_fields: tuple[str, ...]
    forbidden_fields: tuple[str, ...]


class StartPresentation(StrictModel):
    primary_action_columns: tuple[str, ...]
    decorative_merged_cells: Literal[False]
    shows: tuple[str, ...]
    next_complex_label: str
    last_session_label: str
    manual_guidance: tuple[str, ...]
    complex_links: tuple[ComplexLink, ...]
    redacted_status: RedactedStatus


class StatusStyle(StrictModel):
    code: str
    label: str
    symbol: str
    foreground: str
    background: str
    display_value: str | None


class Presentation(StrictModel):
    palette: Palette
    start: StartPresentation
    status_styles: tuple[StatusStyle, ...]


class ValidationPolicyBlueprint(StrictModel):
    schema_derived: Literal[True]
    strict_reject: Literal[True]
    nullable_blank_is_null: Literal[True]
    invalid_value_is_zero: Literal[False]
    help_text_locale: Literal["uk-UA"]
    filtered_rows_included: Literal[True]
    date_format: str
    datetime_format: str
    decimal_format: str
    integer_format: str
    required_help_text: str
    nullable_help_text: str
    enum_help_text: str
    invalid_help_text: str


class QualityDiagnosticsBlueprint(StrictModel):
    source_ref: Literal["schema.conditional_rules"]
    missing_nullable_value: str
    missing_required_value: str
    invalid_bundle: str
    duplicate_id: str
    write_zero_for_missing: Literal[False]


class NamedRangeBlueprint(StrictModel):
    logical_key: str
    name: str
    source_kind: Literal[
        "schema_workout_types",
        "schema_enum",
        "active_records",
    ]
    source_ref: str
    status_filter: str | None = None
    operational_only: bool


class FilterViewBlueprint(StrictModel):
    logical_key: str
    tab: str
    title: str
    workout_label: str
    source_field: str


class ActivationBlueprint(StrictModel):
    active_when: str
    inactive_rows_are_facts: Literal[False]
    prerequisite_named_range: str | None = None
    prerequisite_field: str | None = None
    foreign_key: str | None = None
    foreign_key_named_range: str | None = None
    version_match: str | None = None
    program_item_named_range: str | None = None


class ProtectionPolicyBlueprint(StrictModel):
    enforced: Literal[True]
    warning_only: Literal[False]


class ManagedInputZoneBlueprint(StrictModel):
    logical_key: str
    tab: str
    schema_tab: Literal["sessions", "sets"]
    append_only: Literal[True]
    reserve_capacity: int
    reserve_slot_prefix: str
    primary_key: str
    freeze_rows: int
    decorative_merged_cells: Literal[False]
    input_fill: str
    system_fill: str
    editable_columns: tuple[str, ...]
    protected_columns: tuple[str, ...]
    column_order: tuple[str, ...]
    activation: ActivationBlueprint
    protection: ProtectionPolicyBlueprint


class ProtectionBlueprint(StrictModel):
    logical_key: str
    tab: str
    fields: tuple[str, ...]
    enforced: Literal[True]
    warning_only: Literal[False]


class ColumnWidthBlueprint(StrictModel):
    field: str
    pixels: int


class TabLayoutBlueprint(StrictModel):
    logical_key: str
    tab: str
    freeze_rows: int
    decorative_merged_cells: Literal[False]
    column_widths: tuple[ColumnWidthBlueprint, ...]


class FormulaBlueprint(StrictModel):
    formula_id: str
    formula_version: str
    text: str


class ManagedObjectBlueprint(StrictModel):
    logical_key: str
    kind: Literal[
        "chart",
        "conditional_format",
        "filter_view",
        "formula",
        "managed_range",
        "named_range",
        "protection",
        "validation",
    ]
    owner: Literal["workout_tracker"]
    source_column_refs: tuple[str, ...] = ()
    formula_id: str | None = None
    dependencies: tuple[str, ...] = ()


class TabBlueprint(StrictModel):
    logical_key: str
    title: str
    owner: Literal["workout_tracker"]
    authority_role: str
    source_schema_tab: str | None = None
    managed_objects: tuple[ManagedObjectBlueprint, ...] = ()


class WorkbookBlueprint(StrictModel):
    workbook_contract_version: str
    schema_version: str
    formula_version: str
    program_bootstrap_version: str
    owner: Literal["workout_tracker"]
    properties: WorkbookProperties
    formula_registry: tuple[FormulaBlueprint, ...]
    presentation: Presentation
    validation_policy: ValidationPolicyBlueprint
    quality_diagnostics: QualityDiagnosticsBlueprint
    named_ranges: tuple[NamedRangeBlueprint, ...]
    filter_views: tuple[FilterViewBlueprint, ...]
    managed_input_zones: tuple[ManagedInputZoneBlueprint, ...]
    protections: tuple[ProtectionBlueprint, ...]
    tab_layouts: tuple[TabLayoutBlueprint, ...]
    tabs: tuple[TabBlueprint, ...]

    @model_validator(mode="after")
    def versions_are_present(self) -> "WorkbookBlueprint":
        for value in (
            self.workbook_contract_version,
            self.schema_version,
            self.formula_version,
            self.program_bootstrap_version,
        ):
            if not value.strip():
                raise ValueError("version references must be non-empty")
        return self


def _fail(code: str, count: int, digest: str) -> None:
    raise ContractValidationError(
        code,
        count=count,
        contract_sha256=digest,
    )


def _validate_logical_key(value: str, digest: str) -> None:
    parts = value.split(":")
    if len(parts) < 2 or any(not IDENTITY_PART.fullmatch(part) for part in parts):
        _fail("STABLE_ID_MISSING_OR_INVALID", 1, digest)
    if POSITIONAL_IDENTITY.search("_".join(parts)):
        _fail("ROW_POSITION_USED_AS_IDENTITY", 1, digest)


def _validate_blueprint_semantics(
    blueprint: WorkbookBlueprint,
    source_schema: SourceSchema,
    digest: str,
) -> None:
    if blueprint.schema_version not in source_schema.versions.schema.accepted:
        _fail("SCHEMA_VERSION_UNSUPPORTED", 1, digest)
    if blueprint.formula_version != source_schema.versions.formulas.current:
        _fail("FORMULA_VERSION_UNSUPPORTED", 1, digest)
    if (
        re.fullmatch(
            source_schema.versions.schema.pattern,
            blueprint.workbook_contract_version,
        )
        is None
        or re.fullmatch(
            r"[a-z][a-z0-9_-]*-v[0-9]+(?:\.[0-9]+\.[0-9]+)?",
            blueprint.program_bootstrap_version,
        )
        is None
    ):
        _fail("PROGRAM_VERSION_UNKNOWN", 1, digest)

    formula_ids = [formula.formula_id for formula in blueprint.formula_registry]
    logical_keys = [tab.logical_key for tab in blueprint.tabs]
    for tab in blueprint.tabs:
        logical_keys.extend(item.logical_key for item in tab.managed_objects)
    logical_keys.extend(item.logical_key for item in blueprint.named_ranges)
    logical_keys.extend(item.logical_key for item in blueprint.filter_views)
    logical_keys.extend(item.logical_key for item in blueprint.managed_input_zones)
    logical_keys.extend(item.logical_key for item in blueprint.protections)
    logical_keys.extend(item.logical_key for item in blueprint.tab_layouts)
    duplicate_count = len(logical_keys) - len(set(logical_keys))
    duplicate_formulas = len(formula_ids) - len(set(formula_ids))
    if duplicate_count or duplicate_formulas:
        _fail("DUPLICATE_LOGICAL_KEY", duplicate_count + duplicate_formulas, digest)

    registered_formulas = set(formula_ids)
    tab_keys = {tab.logical_key for tab in blueprint.tabs}
    tab_by_title = {tab.title: tab for tab in blueprint.tabs}
    named_range_keys = {item.logical_key for item in blueprint.named_ranges}
    filter_view_keys = {item.logical_key for item in blueprint.filter_views}
    for logical_key in logical_keys:
        _validate_logical_key(logical_key, digest)

    for tab in blueprint.tabs:
        if tab.owner != OWNER or tab.authority_role not in AUTHORITY_ROLES:
            _fail("OWNERSHIP_POLICY_INVALID", 1, digest)

        source_tab = (
            source_schema.tab(tab.source_schema_tab)
            if tab.source_schema_tab is not None
            else None
        )
        if tab.source_schema_tab is not None and source_tab is None:
            _fail("SOURCE_TAB_UNKNOWN", 1, digest)
        if source_tab is not None and tab.authority_role != source_tab.authority_role:
            _fail("OWNERSHIP_POLICY_INVALID", 1, digest)
        source_columns = (
            {column.field for column in source_tab.columns}
            if source_tab is not None
            else set()
        )

        for item in tab.managed_objects:
            if item.owner != OWNER:
                _fail("OWNERSHIP_POLICY_INVALID", 1, digest)
            if item.formula_id is not None and item.formula_id not in registered_formulas:
                _fail("FORMULA_NOT_REGISTERED", 1, digest)
            if item.kind == "formula" and item.formula_id is None:
                _fail("FORMULA_NOT_REGISTERED", 1, digest)
            unknown_columns = set(item.source_column_refs) - source_columns
            if unknown_columns:
                _fail("SOURCE_COLUMN_UNKNOWN", len(unknown_columns), digest)
            unknown_dependencies = set(item.dependencies) - (
                tab_keys | set(logical_keys)
            )
            if unknown_dependencies:
                _fail("MANAGED_REFERENCE_UNKNOWN", len(unknown_dependencies), digest)

    expected_workout_types = tuple(
        item.source_label
        for item in (
            source_schema.canonical_workout_types.upper_strength,
            source_schema.canonical_workout_types.lower_strength,
            source_schema.canonical_workout_types.upper_hypertrophy,
            source_schema.canonical_workout_types.lower_hypertrophy,
        )
    )
    accents = blueprint.presentation.palette.workout_accents
    links = blueprint.presentation.start.complex_links
    if (
        tuple(item.label for item in accents) != expected_workout_types
        or tuple(item.label for item in links) != expected_workout_types
        or len({item.color for item in accents}) != 4
        or any(not item.symbol for item in accents)
        or any(not item.symbol or item.tap_count != 1 for item in links)
        or any(item.target_filter_view not in filter_view_keys for item in links)
    ):
        _fail("MOBILE_NAVIGATION_CONTRACT_INVALID", 1, digest)

    status_styles = blueprint.presentation.status_styles
    if (
        len({item.code for item in status_styles}) != len(status_styles)
        or any(not item.label or not item.symbol for item in status_styles)
    ):
        _fail("STATUS_STYLE_INVALID", 1, digest)

    for item in blueprint.named_ranges:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", item.name) is None:
            _fail("NAMED_RANGE_INVALID", 1, digest)
        if item.source_kind == "active_records" and item.status_filter is None:
            _fail("NAMED_RANGE_INVALID", 1, digest)

    for view in blueprint.filter_views:
        tab = tab_by_title.get(view.tab)
        if (
            tab is None
            or tab.source_schema_tab != "program"
            or view.source_field != "workout_type"
            or view.workout_label not in expected_workout_types
        ):
            _fail("FILTER_VIEW_INVALID", 1, digest)

    for zone in blueprint.managed_input_zones:
        source_tab = source_schema.tab(zone.schema_tab)
        if source_tab is None or tab_by_title.get(zone.tab) is None:
            _fail("SOURCE_TAB_UNKNOWN", 1, digest)
        source_fields = tuple(column.field for column in source_tab.columns)
        configured = (*zone.editable_columns, *zone.protected_columns)
        if (
            zone.reserve_capacity < 1
            or zone.input_fill == zone.system_fill
            or zone.primary_key != source_tab.primary_key
            or tuple(zone.column_order) != configured
            or len(set(configured)) != len(configured)
            or set(configured) != set(source_fields)
            or zone.primary_key not in zone.protected_columns
        ):
            _fail("INPUT_ZONE_CONTRACT_INVALID", 1, digest)
        activation_refs = (
            zone.activation.prerequisite_named_range,
            zone.activation.foreign_key_named_range,
            zone.activation.program_item_named_range,
        )
        if any(
            value is not None and value not in named_range_keys
            for value in activation_refs
        ):
            _fail("MANAGED_REFERENCE_UNKNOWN", 1, digest)

    for protection in blueprint.protections:
        tab = tab_by_title.get(protection.tab)
        if tab is None or tab.source_schema_tab is None:
            _fail("SOURCE_TAB_UNKNOWN", 1, digest)
        source_tab = source_schema.tab(tab.source_schema_tab)
        assert source_tab is not None
        source_fields = {column.field for column in source_tab.columns}
        if not protection.fields or not set(protection.fields) <= source_fields:
            _fail("SOURCE_COLUMN_UNKNOWN", 1, digest)

    for layout in blueprint.tab_layouts:
        tab = tab_by_title.get(layout.tab)
        if (
            tab is None
            or layout.freeze_rows < 1
            or any(width.pixels < 48 for width in layout.column_widths)
            or len({width.field for width in layout.column_widths})
            != len(layout.column_widths)
        ):
            _fail("TAB_LAYOUT_INVALID", 1, digest)
        if tab.source_schema_tab is not None:
            source_tab = source_schema.tab(tab.source_schema_tab)
            assert source_tab is not None
            if {width.field for width in layout.column_widths} != {
                column.field for column in source_tab.columns
            }:
                _fail("TAB_LAYOUT_INVALID", 1, digest)

    for formula in blueprint.formula_registry:
        if formula.formula_version != blueprint.formula_version:
            _fail("FORMULA_VERSION_UNSUPPORTED", 1, digest)
        if not formula.text.startswith("="):
            _fail("FORMULA_NOT_REGISTERED", 1, digest)


def load_workbook_blueprint(
    path: str | Path,
    source_schema: SourceSchema,
) -> WorkbookBlueprint:
    payload, digest = _load_yaml(path)
    try:
        blueprint = WorkbookBlueprint.model_validate(payload)
    except ValidationError as exc:
        errors = exc.errors(include_input=False, include_context=False)
        ownership_count = sum(
            error["type"] == "literal_error"
            and error.get("loc", ())[-1:] == ("owner",)
            for error in errors
        )
        code = (
            "OWNERSHIP_POLICY_INVALID"
            if ownership_count
            else "CONTRACT_SHAPE_INVALID"
        )
        raise ContractValidationError(
            code,
            count=exc.error_count(),
            contract_sha256=digest,
        ) from exc
    _validate_blueprint_semantics(blueprint, source_schema, digest)
    return blueprint
