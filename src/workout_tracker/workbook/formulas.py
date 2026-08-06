from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Mapping


FORMULA_VERSION = "metrics-v1"
LB_TO_KG = Decimal("0.45359237")
_ONE_DECIMAL = Decimal("0.1")
_WORKING_ROLES = frozenset({"working", "backoff"})
_MASS_UNITS = frozenset({"kg", "lb"})
_COHORT_FIELDS = (
    "exercise_family_id",
    "exercise_variant_id",
    "equipment_id",
    "setup_id",
    "comparison_cohort_id",
    "load_basis",
    "implement_count",
    "laterality",
    "resistance_direction",
)


@dataclass(frozen=True, slots=True)
class FormulaTemplate:
    formula_id: str
    formula_version: str
    source_tab: str
    value_field: str
    status_field: str
    required_columns: tuple[str, ...]
    text: str


def _template(
    formula_id: str,
    *,
    source_tab: str,
    value_field: str,
    status_field: str,
    required_columns: tuple[str, ...],
    expression: str,
) -> FormulaTemplate:
    return FormulaTemplate(
        formula_id=formula_id,
        formula_version=FORMULA_VERSION,
        source_tab=source_tab,
        value_field=value_field,
        status_field=status_field,
        required_columns=required_columns,
        text=f'=LET(metric_version,"{FORMULA_VERSION}",{expression})',
    )


_COMMON_SET_COLUMNS = (
    "set_id",
    "session_id",
    "status",
    "set_role",
    "laterality",
)
_LOAD_COLUMNS = (
    *_COMMON_SET_COLUMNS,
    "exercise_family_id",
    "exercise_variant_id",
    "equipment_id",
    "setup_id",
    "comparison_cohort_id",
    "load_value",
    "load_unit",
    "load_basis",
    "implement_count",
)

_TEMPLATES = (
    _template(
        "working_set_count_v1",
        source_tab="Підходи",
        value_field="working_set_count_sheet",
        status_field="risk_flags_sheet",
        required_columns=_COMMON_SET_COLUMNS,
        expression='IF({column:session_id}="","",COUNTUNIQUE(FILTER({column:set_id},{column:status}="completed",REGEXMATCH({column:set_role},"^(working|backoff)$"))))',
    ),
    _template(
        "rep_volume_v1",
        source_tab="Підходи",
        value_field="rep_volume_sheet",
        status_field="data_quality_status_sheet",
        required_columns=(
            *_COMMON_SET_COLUMNS,
            "reps_total",
            "reps_left",
            "reps_right",
        ),
        expression='IF({column:session_id}="","",SUM(FILTER({column:movement_repetitions},{column:eligible_working_set}=TRUE)))',
    ),
    _template(
        "load_volume_v1",
        source_tab="Підходи",
        value_field="volume_sheet",
        status_field="data_quality_status_sheet",
        required_columns=_LOAD_COLUMNS,
        expression='IF({column:session_id}="","",IF({column:comparison_cohort_id}="","",SUM(FILTER({column:comparable_load_volume},{column:eligible_working_set}=TRUE))))',
    ),
    _template(
        "maximum_comparable_load_v1",
        source_tab="Підходи",
        value_field="maximum_comparable_load_sheet",
        status_field="data_quality_status_sheet",
        required_columns=_LOAD_COLUMNS,
        expression='IF({column:session_id}="","",IF({column:comparison_cohort_id}="","",MAX(FILTER({column:comparable_load},{column:eligible_working_set}=TRUE))))',
    ),
    _template(
        "epley_e1rm_v1",
        source_tab="Підходи",
        value_field="e1rm_sheet",
        status_field="data_quality_status_sheet",
        required_columns=(*_LOAD_COLUMNS, "reps_total", "reps_left", "reps_right"),
        expression='IF({column:session_id}="","",IF({column:e1rm_eligible}=TRUE,{column:load_kg}*(30+{column:repetitions_for_effort})/30,""))',
    ),
    _template(
        "rir_summary_v1",
        source_tab="Підходи",
        value_field="average_rir_sheet",
        status_field="data_quality_status_sheet",
        required_columns=(*_COMMON_SET_COLUMNS, "rir"),
        expression='IF({column:session_id}="","",IFERROR(AVERAGE(FILTER({column:rir},{column:eligible_working_set}=TRUE)),""))',
    ),
    _template(
        "rest_summary_v1",
        source_tab="Підходи",
        value_field="average_rest_seconds_sheet",
        status_field="data_quality_status_sheet",
        required_columns=(
            *_COMMON_SET_COLUMNS,
            "exercise_variant_id",
            "equipment_id",
            "setup_id",
            "comparison_cohort_id",
            "rest_seconds",
        ),
        expression='IF({column:session_id}="","",IFERROR(AVERAGE(FILTER({column:rest_seconds},{column:eligible_rest}=TRUE)),""))',
    ),
    _template(
        "session_completion_v1",
        source_tab="Сесії",
        value_field="completion_status_sheet",
        status_field="data_quality_status_sheet",
        required_columns=("session_id", "status", "expected_set_count"),
        expression='IF({column:session_id}="","",IF({column:status}="complete","complete","incomplete"))',
    ),
    _template(
        "data_quality_status_v1",
        source_tab="Сесії",
        value_field="data_quality_status_sheet",
        status_field="data_quality_reason_sheet",
        required_columns=("session_id", "status"),
        expression='IF({column:session_id}="","",IF({column:status}="complete","ok","missing"))',
    ),
)


class FormulaRegistry:
    def __init__(self, templates: tuple[FormulaTemplate, ...]) -> None:
        by_id = {template.formula_id: template for template in templates}
        if len(by_id) != len(templates):
            raise ValueError("DUPLICATE_FORMULA_ID")
        if any(template.formula_version != FORMULA_VERSION for template in templates):
            raise ValueError("FORMULA_VERSION_MISMATCH")
        self._templates: Mapping[str, FormulaTemplate] = MappingProxyType(by_id)

    @classmethod
    def metrics_v1(cls) -> FormulaRegistry:
        return cls(_TEMPLATES)

    @property
    def formula_ids(self) -> tuple[str, ...]:
        return tuple(self._templates)

    def get(self, formula_id: str) -> FormulaTemplate:
        try:
            return self._templates[formula_id]
        except KeyError as exc:
            raise KeyError(f"FORMULA_NOT_REGISTERED:{formula_id}") from exc


def _result(
    value: str | int | None,
    unit: str,
    status: str,
    reasons: set[str] | list[str] | tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "value": value,
        "unit": unit,
        "status": status,
        "exclusion_reasons": sorted(set(reasons)),
    }


def _base_reasons(row: Mapping[str, object]) -> tuple[set[str], str | None]:
    reasons: set[str] = set()
    if row.get("valid", True) is not True:
        return {"SOURCE_RECORD_QUARANTINED"}, "invalid"
    if row.get("session_status", "complete") != "complete":
        return {"SESSION_NOT_COMPLETE"}, "missing"
    if row.get("status") != "completed":
        return {"SET_NOT_COMPLETED"}, "excluded"
    if row.get("set_role") == "warmup":
        return {"SET_ROLE_WARMUP"}, "excluded"
    if row.get("set_role") not in _WORKING_ROLES:
        return {"SET_ROLE_UNSUPPORTED"}, "excluded"
    if row.get("laterality") == "unilateral_both":
        has_reps = row.get("reps_left") is not None and row.get("reps_right") is not None
        has_duration = (
            row.get("duration_seconds_left") is not None
            and row.get("duration_seconds_right") is not None
        )
        if not has_reps and not has_duration:
            return {"UNILATERAL_COMPONENT_INCOMPLETE"}, "invalid"
    return reasons, None


def _eligible_rows(
    rows: list[Mapping[str, object]],
) -> tuple[list[Mapping[str, object]], set[str], str | None]:
    eligible: list[Mapping[str, object]] = []
    reasons: set[str] = set()
    fatal_status: str | None = None
    for row in rows:
        row_reasons, disposition = _base_reasons(row)
        reasons.update(row_reasons)
        if disposition is None:
            eligible.append(row)
        elif disposition in {"invalid", "missing"}:
            fatal_status = disposition
    return eligible, reasons, fatal_status


def _movement_repetitions(row: Mapping[str, object]) -> int | None:
    laterality = row.get("laterality")
    if laterality in {"bilateral", "alternating_total"}:
        value = row.get("reps_total")
        return int(value) if value is not None else None
    if laterality == "unilateral_both":
        left = row.get("reps_left")
        right = row.get("reps_right")
        return int(left) + int(right) if left is not None and right is not None else None
    if laterality == "left_only":
        value = row.get("reps_left")
        return int(value) if value is not None else None
    if laterality == "right_only":
        value = row.get("reps_right")
        return int(value) if value is not None else None
    return None


def _effort_repetitions(row: Mapping[str, object]) -> int | None:
    if row.get("laterality") in {"bilateral", "alternating_total"}:
        value = row.get("reps_total")
        return int(value) if value is not None else None
    for field in ("reps_left", "reps_right"):
        value = row.get(field)
        if value is not None:
            return int(value)
    return None


def _cohort(row: Mapping[str, object]) -> tuple[object, ...] | None:
    material = (
        row.get("exercise_family_id"),
        row.get("exercise_variant_id"),
        row.get("equipment_id"),
        row.get("setup_id"),
        row.get("comparison_cohort_id"),
    )
    if any(value in (None, "") for value in material):
        return None
    return tuple(row.get(field) for field in _COHORT_FIELDS)


def _load(row: Mapping[str, object]) -> tuple[Decimal | None, str, set[str]]:
    reasons: set[str] = set()
    basis = row.get("load_basis")
    if basis == "bodyweight_only":
        return None, "kg", {"BODYWEIGHT_ONLY"}
    if basis == "assistance":
        return None, "kg", {"ASSISTED_LOAD"}
    value = row.get("load_value")
    if value is None:
        return None, "kg", {"LOAD_MISSING"}
    unit = row.get("load_unit")
    if unit not in {"kg", "lb", "machine_level"}:
        return None, "kg", {"LOAD_UNIT_UNKNOWN"}
    quantity = Decimal(str(value))
    if basis == "per_implement":
        count = row.get("implement_count")
        if count is None:
            return None, "kg", {"IMPLEMENT_COUNT_MISSING"}
        quantity *= Decimal(int(count))
    elif basis not in {"total_external", "machine_stack"}:
        return None, "kg", {"LOAD_BASIS_UNKNOWN"}
    if unit == "lb":
        quantity *= LB_TO_KG
        unit = "kg"
    return quantity, str(unit), reasons


def _display_decimal(value: Decimal) -> str:
    rounded = value.quantize(_ONE_DECIMAL, rounding=ROUND_HALF_EVEN)
    text = format(rounded, "f").rstrip("0").rstrip(".")
    return "0" if text in {"", "-0"} else text


def _evaluate_count(rows: list[Mapping[str, object]]) -> dict[str, object]:
    eligible, reasons, fatal = _eligible_rows(rows)
    if fatal is not None:
        return _result(None, "count", fatal, reasons)
    return _result(len({row["set_id"] for row in eligible}), "count", "ok", reasons)


def _evaluate_reps(rows: list[Mapping[str, object]]) -> dict[str, object]:
    eligible, reasons, fatal = _eligible_rows(rows)
    if fatal is not None:
        return _result(None, "rep", fatal, reasons)
    values = [_movement_repetitions(row) for row in eligible]
    if not values or all(value is None for value in values):
        reasons.add("REPS_MISSING")
        return _result(None, "rep", "missing", reasons)
    if any(value is None for value in values):
        reasons.add("REPS_MISSING")
    return _result(
        sum(value for value in values if value is not None),
        "rep",
        "partial" if "REPS_MISSING" in reasons else "ok",
        reasons,
    )


def _evaluate_load_metric(
    rows: list[Mapping[str, object]],
    *,
    mode: str,
) -> dict[str, object]:
    eligible, reasons, fatal = _eligible_rows(rows)
    default_unit = "kg·rep" if mode == "volume" else "kg"
    if fatal is not None:
        return _result(None, default_unit, fatal, reasons)
    if not eligible:
        reasons.add("LOAD_MISSING")
        return _result(None, default_unit, "missing", reasons)
    cohorts = {_cohort(row) for row in eligible}
    if None in cohorts:
        reasons.add("COHORT_DIMENSION_MISSING")
        return _result(None, default_unit, "incomparable", reasons)
    if len(cohorts) != 1:
        reasons.add("COHORT_MISMATCH")
        return _result(None, default_unit, "incomparable", reasons)
    loaded = [_load(row) for row in eligible]
    for _, _, row_reasons in loaded:
        reasons.update(row_reasons)
    if reasons & {"BODYWEIGHT_ONLY", "ASSISTED_LOAD"} and all(
        quantity is None for quantity, _, _ in loaded
    ):
        return _result(None, default_unit, "not_applicable", reasons)
    if any(quantity is None for quantity, _, _ in loaded):
        return _result(None, default_unit, "missing", reasons)
    units = {unit for _, unit, _ in loaded}
    if len(units) != 1:
        reasons.add("COHORT_MISMATCH")
        return _result(None, default_unit, "incomparable", reasons)
    unit = next(iter(units))
    quantities = [quantity for quantity, _, _ in loaded if quantity is not None]
    if mode == "maximum":
        value = max(quantities)
        result_unit = unit
    else:
        reps = [_movement_repetitions(row) for row in eligible]
        if any(value is None for value in reps):
            reasons.add("REPS_MISSING")
            return _result(None, f"{unit}·rep", "missing", reasons)
        value = sum(
            quantity * Decimal(repetition)
            for quantity, repetition in zip(quantities, reps, strict=True)
            if repetition is not None
        )
        result_unit = f"{unit}·rep"
    return _result(_display_decimal(value), result_unit, "ok", reasons)


def _evaluate_e1rm(rows: list[Mapping[str, object]]) -> dict[str, object]:
    eligible, reasons, fatal = _eligible_rows(rows)
    if fatal is not None:
        return _result(None, "kg", fatal, reasons)
    if not eligible:
        return _result(None, "kg", "missing", {"LOAD_MISSING", *reasons})
    cohorts = {_cohort(row) for row in eligible}
    if None in cohorts:
        return _result(
            None,
            "kg",
            "incomparable",
            {"COHORT_DIMENSION_MISSING", *reasons},
        )
    if len(cohorts) != 1:
        return _result(None, "kg", "incomparable", {"COHORT_MISMATCH", *reasons})
    estimates: list[Decimal] = []
    for row in eligible:
        basis = row.get("load_basis")
        if basis in {"assistance", "bodyweight_only", "added_to_bodyweight"}:
            reasons.add(
                "ASSISTED_LOAD" if basis == "assistance" else "BODYWEIGHT_ONLY"
            )
            reasons.add("LOAD_BASIS_UNSUPPORTED_FOR_E1RM")
        if row.get("resistance_direction") != "higher_is_harder":
            reasons.add("RESISTANCE_DIRECTION_UNSUPPORTED")
        load, unit, load_reasons = _load(row)
        reasons.update(load_reasons)
        reps = _effort_repetitions(row)
        if reps is None:
            reasons.add("REPS_MISSING")
        elif not 1 <= reps <= 12:
            reasons.add("E1RM_REPS_OUT_OF_RANGE")
        if unit not in _MASS_UNITS:
            reasons.add("LOAD_UNIT_NOT_MASS")
        if reasons:
            continue
        assert load is not None and reps is not None
        estimates.append((load * Decimal(30 + reps)) / Decimal(30))
    if estimates:
        return _result(_display_decimal(max(estimates)), "kg", "ok", reasons)
    not_applicable = reasons & {
        "ASSISTED_LOAD",
        "BODYWEIGHT_ONLY",
        "LOAD_BASIS_UNSUPPORTED_FOR_E1RM",
        "E1RM_REPS_OUT_OF_RANGE",
        "LOAD_UNIT_NOT_MASS",
        "RESISTANCE_DIRECTION_UNSUPPORTED",
    }
    return _result(
        None,
        "kg",
        "not_applicable" if not_applicable else "missing",
        reasons,
    )


def _evaluate_mean(
    rows: list[Mapping[str, object]],
    *,
    field: str,
    unit: str,
    missing_reason: str,
) -> dict[str, object]:
    eligible, reasons, fatal = _eligible_rows(rows)
    if fatal is not None:
        return _result(None, unit, fatal, reasons)
    values = [
        Decimal(str(row[field]))
        for row in eligible
        if row.get(field) is not None
    ]
    if not values:
        reasons.add(missing_reason)
        return _result(None, unit, "missing", reasons)
    if len(values) < len(eligible):
        reasons.add(missing_reason)
    with localcontext() as context:
        context.prec = 28
        context.rounding = ROUND_HALF_EVEN
        mean = sum(values) / Decimal(len(values))
    if unit == "s" and mean == mean.to_integral_value():
        value: str | int = int(mean)
    else:
        value = _display_decimal(mean)
    return _result(value, unit, "partial" if len(values) < len(eligible) else "ok", reasons)


def evaluate_fixture_case(case: Mapping[str, object]) -> dict[str, object]:
    formula_id = str(case["formula_id"])
    payload = case["input"]
    if not isinstance(payload, Mapping):
        raise ValueError("FIXTURE_INPUT_INVALID")
    raw_rows = payload.get("sets", [])
    if not isinstance(raw_rows, list) or any(
        not isinstance(row, Mapping) for row in raw_rows
    ):
        raise ValueError("FIXTURE_INPUT_INVALID")
    rows = list(raw_rows)
    if formula_id == "working_set_count_v1":
        return _evaluate_count(rows)
    if formula_id == "rep_volume_v1":
        return _evaluate_reps(rows)
    if formula_id == "load_volume_v1":
        return _evaluate_load_metric(rows, mode="volume")
    if formula_id == "maximum_comparable_load_v1":
        return _evaluate_load_metric(rows, mode="maximum")
    if formula_id == "epley_e1rm_v1":
        return _evaluate_e1rm(rows)
    if formula_id == "rir_summary_v1":
        return _evaluate_mean(
            rows,
            field="rir",
            unit="rir",
            missing_reason="RIR_MISSING",
        )
    if formula_id == "rest_summary_v1":
        return _evaluate_mean(
            rows,
            field="rest_seconds",
            unit="s",
            missing_reason="REST_NOT_OBSERVED",
        )
    if formula_id == "data_quality_status_v1":
        _, reasons, fatal = _eligible_rows(rows)
        return _result(None, "status", fatal or "ok", reasons)
    if formula_id == "session_completion_v1":
        session = payload.get("session")
        if not isinstance(session, Mapping):
            return _result(None, "status", "missing", {"SESSION_NOT_COMPLETE"})
        completed = sum(row.get("status") != "void" for row in rows)
        if (
            session.get("status") == "complete"
            and session.get("expected_set_count") == completed
        ):
            return _result("complete", "status", "ok")
        return _result(None, "status", "invalid", {"SESSION_NOT_COMPLETE"})
    raise KeyError(f"FORMULA_NOT_REGISTERED:{formula_id}")


__all__ = [
    "FORMULA_VERSION",
    "FormulaRegistry",
    "FormulaTemplate",
    "evaluate_fixture_case",
]
