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
    duplicate_count = len(logical_keys) - len(set(logical_keys))
    duplicate_formulas = len(formula_ids) - len(set(formula_ids))
    if duplicate_count or duplicate_formulas:
        _fail("DUPLICATE_LOGICAL_KEY", duplicate_count + duplicate_formulas, digest)

    registered_formulas = set(formula_ids)
    tab_keys = {tab.logical_key for tab in blueprint.tabs}
    for tab in blueprint.tabs:
        _validate_logical_key(tab.logical_key, digest)
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
            _validate_logical_key(item.logical_key, digest)
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
