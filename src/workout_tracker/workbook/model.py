from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from workout_tracker.contracts import (
    ProgramBootstrap,
    SourceSchema,
    WorkbookBlueprint,
)
from workout_tracker.contracts.blueprint import (
    DashboardBlueprint,
    FormulaPlacementBlueprint,
)


class DesiredWorkbookCompilationError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class DesiredColumn:
    field: str
    header: str
    data_class: str
    nullable: bool
    editable: bool
    protected: bool


@dataclass(frozen=True, slots=True)
class DesiredTab:
    logical_key: str
    title: str
    authority_role: str
    schema_key: str | None
    column_order: tuple[str, ...]
    headers: tuple[str, ...]
    columns: tuple[DesiredColumn, ...]


@dataclass(frozen=True, slots=True)
class DesiredProgramRow:
    logical_key: str
    values: tuple[tuple[str, object], ...]

    def value(self, field: str) -> object:
        return dict(self.values)[field]


@dataclass(frozen=True, slots=True)
class DesiredNamedRange:
    logical_key: str
    name: str
    source_kind: str
    source_ref: str
    values: tuple[str, ...] | None
    operational_only: bool


@dataclass(frozen=True, slots=True)
class DesiredFilterView:
    logical_key: str
    tab: str
    title: str
    workout_label: str
    source_field: str


@dataclass(frozen=True, slots=True)
class DesiredStartLink:
    label: str
    symbol: str
    filter_view_key: str
    tap_count: int


@dataclass(frozen=True, slots=True)
class DesiredValidation:
    logical_key: str
    schema_key: str
    field: str
    value_type: str
    allow_blank: bool
    strict_reject: bool
    help_text: str
    number_format: str | None
    named_range_key: str | None
    allowed_values: tuple[str, ...] | None
    pattern: str | None
    minimum: int | float | None
    exclusive_minimum: int | float | None
    maximum: int | float | None


@dataclass(frozen=True, slots=True)
class DesiredProtection:
    logical_key: str
    tab: str
    fields: tuple[str, ...]
    enforced: bool
    warning_only: bool


@dataclass(frozen=True, slots=True)
class DesiredColumnWidth:
    field: str
    pixels: int


@dataclass(frozen=True, slots=True)
class DesiredLayout:
    logical_key: str
    tab: str
    freeze_rows: int
    decorative_merged_cells: bool
    column_widths: tuple[DesiredColumnWidth, ...]


@dataclass(frozen=True, slots=True)
class ReservePool:
    logical_key: str
    entity: str
    capacity: int
    slot_keys: tuple[str, ...]
    primary_key: str
    inactive_rows_are_facts: bool


@dataclass(frozen=True, slots=True)
class DesiredWorkbook:
    workbook_contract_version: str
    schema_version: str
    formula_version: str
    program_bootstrap_version: str
    locale: str
    time_zone: str
    tabs: tuple[DesiredTab, ...]
    program_rows: tuple[DesiredProgramRow, ...]
    named_ranges: tuple[DesiredNamedRange, ...]
    filter_views: tuple[DesiredFilterView, ...]
    start_links: tuple[DesiredStartLink, ...]
    validations: tuple[DesiredValidation, ...]
    protections: tuple[DesiredProtection, ...]
    layouts: tuple[DesiredLayout, ...]
    reserve_pools: tuple[ReservePool, ...]
    formula_placements: tuple[FormulaPlacementBlueprint, ...]
    dashboard: DashboardBlueprint

    def tab_by_schema_key(self, schema_key: str) -> DesiredTab | None:
        return next(
            (tab for tab in self.tabs if tab.schema_key == schema_key),
            None,
        )

    def named_range(self, logical_key: str) -> DesiredNamedRange | None:
        return next(
            (item for item in self.named_ranges if item.logical_key == logical_key),
            None,
        )

    def validation(
        self,
        schema_key: str,
        field: str,
    ) -> DesiredValidation | None:
        return next(
            (
                item
                for item in self.validations
                if item.schema_key == schema_key and item.field == field
            ),
            None,
        )

    def reserve_pool(self, entity: str) -> ReservePool:
        return next(item for item in self.reserve_pools if item.entity == entity)

    def can_activate_set(
        self,
        *,
        session_id: str,
        program_version_id: str,
        active_sessions: Mapping[str, str],
    ) -> bool:
        return (
            bool(session_id)
            and bool(program_version_id)
            and active_sessions.get(session_id) == program_version_id
        )


def _workout_labels(schema: SourceSchema) -> tuple[str, ...]:
    workout_types = schema.canonical_workout_types
    return (
        workout_types.upper_strength.source_label,
        workout_types.lower_strength.source_label,
        workout_types.upper_hypertrophy.source_label,
        workout_types.lower_hypertrophy.source_label,
    )


def _workout_label_by_alias(schema: SourceSchema) -> dict[str, str]:
    workout_types = schema.canonical_workout_types
    items = (
        workout_types.upper_strength,
        workout_types.lower_strength,
        workout_types.upper_hypertrophy,
        workout_types.lower_hypertrophy,
    )
    return {item.internal_alias: item.source_label for item in items}


def _resolve_path(root: object, path: str) -> object:
    value = root
    for part in path.split("."):
        value = getattr(value, part)
    return value


def _column_type(schema: SourceSchema, column) -> str:
    if column.type is not None:
        return column.type
    assert column.type_ref is not None
    resolved = _resolve_path(schema, column.type_ref)
    return resolved.type


def _column_pattern(schema: SourceSchema, column) -> str | None:
    if column.pattern is not None:
        return column.pattern
    if column.pattern_ref is not None:
        resolved = _resolve_path(schema, column.pattern_ref)
        return resolved if isinstance(resolved, str) else resolved.pattern
    if column.type_ref is not None:
        resolved = _resolve_path(schema, column.type_ref)
        return resolved.pattern
    return None


def _number_format(value_type: str, blueprint: WorkbookBlueprint) -> str | None:
    policy = blueprint.validation_policy
    return {
        "date": policy.date_format,
        "datetime": policy.datetime_format,
        "decimal": policy.decimal_format,
        "integer": policy.integer_format,
    }.get(value_type)


def _compile_tabs(
    blueprint: WorkbookBlueprint,
    schema: SourceSchema,
) -> tuple[DesiredTab, ...]:
    zones = {item.schema_tab: item for item in blueprint.managed_input_zones}
    tabs: list[DesiredTab] = []
    for tab in blueprint.tabs:
        source_tab = schema.tab(tab.source_schema_tab) if tab.source_schema_tab else None
        if source_tab is None:
            tabs.append(
                DesiredTab(
                    logical_key=tab.logical_key,
                    title=tab.title,
                    authority_role=tab.authority_role,
                    schema_key=None,
                    column_order=(),
                    headers=(),
                    columns=(),
                )
            )
            continue
        zone = zones.get(tab.source_schema_tab)
        order = (
            zone.column_order
            if zone is not None
            else tuple(column.field for column in source_tab.columns)
        )
        by_field = {column.field: column for column in source_tab.columns}
        columns = tuple(
            DesiredColumn(
                field=field,
                header=by_field[field].header,
                data_class=by_field[field].data_class,
                nullable=by_field[field].nullable,
                editable=zone is not None and field in zone.editable_columns,
                protected=zone is None or field in zone.protected_columns,
            )
            for field in order
        )
        tabs.append(
            DesiredTab(
                logical_key=tab.logical_key,
                title=tab.title,
                authority_role=tab.authority_role,
                schema_key=tab.source_schema_tab,
                column_order=tuple(order),
                headers=tuple(column.header for column in columns),
                columns=columns,
            )
        )
    return tuple(tabs)


def _compile_program_rows(
    program: ProgramBootstrap,
    schema: SourceSchema,
) -> tuple[DesiredProgramRow, ...]:
    source_tab = schema.sheet_tabs.program
    labels = _workout_label_by_alias(schema)
    rows: list[DesiredProgramRow] = []
    for item in program.prescriptions:
        payload = item.model_dump()
        payload.update(
            {
                "schema_version": program.schema_version,
                "program_version_id": program.program_version_id,
                "program_version": program.program_version,
                "program_version_status": program.program_version_status,
                "source_revision": program.source_revision,
                "published_at": program.published_at,
                "workout_type": labels[item.workout_type],
            }
        )
        rows.append(
            DesiredProgramRow(
                logical_key=f"program_row:{item.semantic_key}",
                values=tuple(
                    (column.field, payload.get(column.field))
                    for column in source_tab.columns
                ),
            )
        )
    return tuple(rows)


def _compile_named_ranges(
    blueprint: WorkbookBlueprint,
    schema: SourceSchema,
    program: ProgramBootstrap,
) -> tuple[DesiredNamedRange, ...]:
    result: list[DesiredNamedRange] = []
    for item in blueprint.named_ranges:
        values: tuple[str, ...] | None
        if item.source_kind == "schema_workout_types":
            values = _workout_labels(schema)
        elif item.source_kind == "schema_enum":
            values = tuple(_resolve_path(schema, item.source_ref))
        elif item.source_ref.endswith(".program_version_id"):
            values = (program.program_version_id,)
        elif item.source_ref.endswith(".program_item_id"):
            values = tuple(
                row.program_item_id
                for row in program.prescriptions
                if row.status == "active"
            )
        else:
            values = None
        result.append(
            DesiredNamedRange(
                logical_key=item.logical_key,
                name=item.name,
                source_kind=item.source_kind,
                source_ref=item.source_ref,
                values=values,
                operational_only=item.operational_only,
            )
        )
    return tuple(result)


def _compile_validations(
    blueprint: WorkbookBlueprint,
    schema: SourceSchema,
) -> tuple[DesiredValidation, ...]:
    named_range_by_source = {
        item.source_ref: item.logical_key for item in blueprint.named_ranges
    }
    validations: list[DesiredValidation] = []
    for schema_key in ("program", "sessions", "sets", "recommendations"):
        source_tab = schema.tab(schema_key)
        assert source_tab is not None
        for column in source_tab.columns:
            value_type = _column_type(schema, column)
            enum_source = column.enum_ref or column.enum_source_ref
            named_range_key = (
                named_range_by_source.get(enum_source)
                if enum_source is not None
                else None
            )
            allowed_values = (
                tuple(column.allowed)
                if column.allowed is not None
                else None
            )
            if column.enum_ref is not None:
                allowed_values = tuple(_resolve_path(schema, column.enum_ref))
            elif column.enum_source_ref is not None:
                allowed_values = _workout_labels(schema)
            help_text = (
                blueprint.validation_policy.nullable_help_text
                if column.nullable
                else blueprint.validation_policy.required_help_text
            )
            if enum_source is not None or allowed_values is not None:
                help_text = f"{blueprint.validation_policy.enum_help_text} {help_text}"
            validations.append(
                DesiredValidation(
                    logical_key=f"validation:{schema_key}:{column.field}",
                    schema_key=schema_key,
                    field=column.field,
                    value_type=value_type,
                    allow_blank=column.nullable,
                    strict_reject=blueprint.validation_policy.strict_reject,
                    help_text=help_text,
                    number_format=_number_format(value_type, blueprint),
                    named_range_key=named_range_key,
                    allowed_values=allowed_values,
                    pattern=_column_pattern(schema, column),
                    minimum=column.minimum,
                    exclusive_minimum=column.exclusive_minimum,
                    maximum=column.maximum,
                )
            )
    return tuple(validations)


def _compile_reserve_pools(
    blueprint: WorkbookBlueprint,
) -> tuple[ReservePool, ...]:
    pools: list[ReservePool] = []
    for zone in blueprint.managed_input_zones:
        entity = zone.schema_tab.removesuffix("s")
        digits = max(3, len(str(zone.reserve_capacity)))
        slots = tuple(
            f"{zone.reserve_slot_prefix}{ordinal:0{digits}d}"
            for ordinal in range(1, zone.reserve_capacity + 1)
        )
        pools.append(
            ReservePool(
                logical_key=f"reserve_pool:{entity}",
                entity=entity,
                capacity=zone.reserve_capacity,
                slot_keys=slots,
                primary_key=zone.primary_key,
                inactive_rows_are_facts=zone.activation.inactive_rows_are_facts,
            )
        )
    return tuple(pools)


def compile_desired_workbook(
    blueprint: WorkbookBlueprint,
    schema: SourceSchema,
    program: ProgramBootstrap,
    *,
    locale: str,
    time_zone: str,
) -> DesiredWorkbook:
    if locale != blueprint.properties.locale or locale != "uk_UA":
        raise DesiredWorkbookCompilationError("WORKBOOK_LOCALE_MISMATCH")
    if (
        time_zone != blueprint.properties.time_zone
        or time_zone != "America/New_York"
    ):
        raise DesiredWorkbookCompilationError("WORKBOOK_TIME_ZONE_MISMATCH")
    if (
        blueprint.schema_version != schema.versions.schema.current
        or program.schema_version != schema.versions.schema.current
    ):
        raise DesiredWorkbookCompilationError("SCHEMA_VERSION_MISMATCH")
    if blueprint.program_bootstrap_version != program.program_bootstrap_version:
        raise DesiredWorkbookCompilationError("PROGRAM_VERSION_MISMATCH")

    return DesiredWorkbook(
        workbook_contract_version=blueprint.workbook_contract_version,
        schema_version=schema.versions.schema.current,
        formula_version=blueprint.formula_version,
        program_bootstrap_version=program.program_bootstrap_version,
        locale=locale,
        time_zone=time_zone,
        tabs=_compile_tabs(blueprint, schema),
        program_rows=_compile_program_rows(program, schema),
        named_ranges=_compile_named_ranges(blueprint, schema, program),
        filter_views=tuple(
            DesiredFilterView(
                logical_key=item.logical_key,
                tab=item.tab,
                title=item.title,
                workout_label=item.workout_label,
                source_field=item.source_field,
            )
            for item in blueprint.filter_views
        ),
        start_links=tuple(
            DesiredStartLink(
                label=item.label,
                symbol=item.symbol,
                filter_view_key=item.target_filter_view,
                tap_count=item.tap_count,
            )
            for item in blueprint.presentation.start.complex_links
        ),
        validations=_compile_validations(blueprint, schema),
        protections=tuple(
            DesiredProtection(
                logical_key=item.logical_key,
                tab=item.tab,
                fields=item.fields,
                enforced=item.enforced,
                warning_only=item.warning_only,
            )
            for item in blueprint.protections
        ),
        layouts=tuple(
            DesiredLayout(
                logical_key=item.logical_key,
                tab=item.tab,
                freeze_rows=item.freeze_rows,
                decorative_merged_cells=item.decorative_merged_cells,
                column_widths=tuple(
                    DesiredColumnWidth(field=width.field, pixels=width.pixels)
                    for width in item.column_widths
                ),
            )
            for item in blueprint.tab_layouts
        ),
        reserve_pools=_compile_reserve_pools(blueprint),
        formula_placements=blueprint.formula_placements,
        dashboard=blueprint.dashboard,
    )


__all__ = [
    "DesiredWorkbook",
    "DesiredWorkbookCompilationError",
    "compile_desired_workbook",
]
