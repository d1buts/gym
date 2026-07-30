from __future__ import annotations

from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
import yaml

import workout_tracker.contracts as contracts


SCHEMA_PATH = Path("config/schema.yaml")
BOOTSTRAP_PATH = Path("config/program-bootstrap.yaml")


def _row(
    workout_type: str,
    block_code: str,
    exercise_order: int,
    exercise_name: str,
    exercise_family_id: str,
    exercise_variant_id: str,
    equipment_id: str | None,
    target_sets: int,
    laterality: str,
    target_reps: tuple[int, int] | None,
    target_duration_seconds: tuple[int, int] | None,
    target_rir: tuple[int, int],
    rest_seconds: tuple[int, int] | None,
    *,
    prescribed_optional: bool = False,
) -> dict[str, object]:
    day = {
        "upper_strength": "01 upper strength.md",
        "lower_strength": "02 lower strength.md",
        "upper_hypertrophy": "03 upper hypertrophy.md",
        "lower_hypertrophy": "04 lower hypertrophy.md",
    }[workout_type]
    return {
        "workout_type": workout_type,
        "block_code": block_code,
        "exercise_order": exercise_order,
        "exercise_name": exercise_name,
        "exercise_family_id": exercise_family_id,
        "exercise_variant_id": exercise_variant_id,
        "equipment_id": equipment_id,
        "setup_id": None,
        "comparison_cohort_id": None,
        "target_sets": target_sets,
        "prescribed_optional": prescribed_optional,
        "measurement_kind": (
            "duration" if target_duration_seconds is not None else "repetitions"
        ),
        "laterality": laterality,
        "target_reps_min": target_reps[0] if target_reps else None,
        "target_reps_max": target_reps[1] if target_reps else None,
        "target_duration_seconds_min": (
            target_duration_seconds[0] if target_duration_seconds else None
        ),
        "target_duration_seconds_max": (
            target_duration_seconds[1] if target_duration_seconds else None
        ),
        "target_rir_min": target_rir[0],
        "target_rir_max": target_rir[1],
        "rest_seconds_min": rest_seconds[0] if rest_seconds else None,
        "rest_seconds_max": rest_seconds[1] if rest_seconds else None,
        "source_file": f"4-day upper lower program/{day}",
        "source_section": f"Блок {block_code[0]}",
    }


EXPECTED_ROWS = (
    _row(
        "upper_strength", "A1", 1, "Жим штанги лежачи",
        "bench_press", "barbell_bench_press", "barbell",
        4, "bilateral", (4, 6), None, (2, 2), (60, 75),
    ),
    _row(
        "upper_strength", "A2", 2, "Cable curl",
        "elbow_flexion", "cable_curl", "cable_stack",
        3, "bilateral", (8, 12), None, (2, 2), (75, 90),
    ),
    _row(
        "upper_strength", "B1", 3, "Precor lat pulldown",
        "vertical_pull", "precor_lat_pulldown", "precor_pulldown_seated_row",
        4, "bilateral", (5, 8), None, (1, 2), (60, 75),
    ),
    _row(
        "upper_strength", "B2", 4, "Cable pushdown",
        "elbow_extension", "cable_pushdown", "cable_stack",
        3, "bilateral", (8, 12), None, (1, 2), (60, 75),
    ),
    _row(
        "upper_strength", "C1", 5, "Precor shoulder press",
        "vertical_press", "precor_shoulder_press", "precor_multi_press",
        3, "bilateral", (6, 8), None, (2, 2), (75, 90),
    ),
    _row(
        "upper_strength", "C2", 6, "Precor seated row",
        "horizontal_pull", "precor_seated_row", "precor_pulldown_seated_row",
        3, "bilateral", (6, 10), None, (2, 2), (75, 90),
    ),
    _row(
        "upper_strength", "D1", 7, "Cable lateral raise",
        "shoulder_abduction", "cable_lateral_raise", "cable_stack",
        2, "bilateral", (12, 20), None, (1, 1), (30, 45),
    ),
    _row(
        "upper_strength", "D2", 8, "Face pull",
        "rear_delt_pull", "face_pull", None,
        2, "bilateral", (12, 20), None, (1, 2), (30, 45),
    ),
    _row(
        "lower_strength", "A1", 1, "Присідання зі штангою",
        "squat", "barbell_back_squat", "barbell",
        4, "bilateral", (4, 6), None, (2, 2), (75, 90),
    ),
    _row(
        "lower_strength", "A2", 2, "Pallof press",
        "anti_rotation", "pallof_press", None,
        3, "unilateral_both", (10, 15), None, (2, 3), (75, 90),
    ),
    _row(
        "lower_strength", "B1", 3, "Barbell Romanian deadlift",
        "hip_hinge", "barbell_romanian_deadlift", "barbell",
        3, "bilateral", (5, 8), None, (2, 2), (75, 90),
    ),
    _row(
        "lower_strength", "B2", 4, "Precor calf extension",
        "plantar_flexion", "precor_calf_extension", "precor_leg_press_calf_extension",
        3, "bilateral", (8, 12), None, (1, 2), (75, 90),
    ),
    _row(
        "lower_strength", "C1", 5, "Precor leg press",
        "squat", "precor_leg_press", "precor_leg_press_calf_extension",
        3, "bilateral", (6, 10), None, (2, 2), (60, 75),
    ),
    _row(
        "lower_strength", "C2", 6, "Cable crunch",
        "spinal_flexion", "cable_crunch", "cable_stack",
        3, "bilateral", (10, 15), None, (1, 2), (60, 75),
    ),
    _row(
        "lower_strength", "D1", 7, "Bulgarian split squat",
        "unilateral_squat", "bulgarian_split_squat", None,
        2, "unilateral_both", (8, 10), None, (2, 2), None,
        prescribed_optional=True,
    ),
    _row(
        "upper_hypertrophy", "A1", 1, "Incline dumbbell press",
        "bench_press", "incline_dumbbell_press", "dumbbell",
        3, "bilateral", (8, 12), None, (1, 2), (60, 75),
    ),
    _row(
        "upper_hypertrophy", "A2", 2, "Precor seated row",
        "horizontal_pull", "precor_seated_row", "precor_pulldown_seated_row",
        3, "bilateral", (8, 12), None, (1, 2), (60, 75),
    ),
    _row(
        "upper_hypertrophy", "B1", 3, "Precor lat pulldown",
        "vertical_pull", "precor_lat_pulldown", "precor_pulldown_seated_row",
        3, "bilateral", (8, 12), None, (1, 2), (45, 75),
    ),
    _row(
        "upper_hypertrophy", "B2", 4, "Cable fly",
        "horizontal_adduction", "cable_fly", "cable_stack",
        3, "bilateral", (10, 15), None, (1, 2), (45, 75),
    ),
    _row(
        "upper_hypertrophy", "C1", 5, "Cable lateral raise",
        "shoulder_abduction", "cable_lateral_raise", "cable_stack",
        3, "bilateral", (12, 20), None, (0, 2), (30, 45),
    ),
    _row(
        "upper_hypertrophy", "C2", 6, "Cable reverse fly",
        "shoulder_horizontal_abduction", "cable_reverse_fly", "cable_stack",
        3, "bilateral", (12, 20), None, (0, 2), (30, 45),
    ),
    _row(
        "upper_hypertrophy", "D1", 7, "Cable overhead triceps extension",
        "elbow_extension", "cable_overhead_triceps_extension", "cable_stack",
        2, "bilateral", (10, 15), None, (0, 2), (30, 45),
    ),
    _row(
        "upper_hypertrophy", "D2", 8, "Hammer curl",
        "elbow_flexion", "hammer_curl", None,
        2, "bilateral", (10, 15), None, (0, 2), (30, 45),
    ),
    _row(
        "lower_hypertrophy", "A1", 1, "Precor leg press",
        "squat", "precor_leg_press", "precor_leg_press_calf_extension",
        3, "bilateral", (10, 15), None, (1, 2), (60, 75),
    ),
    _row(
        "lower_hypertrophy", "A2", 2, "Precor calf extension",
        "plantar_flexion", "precor_calf_extension", "precor_leg_press_calf_extension",
        3, "bilateral", (12, 20), None, (1, 1), (60, 75),
    ),
    _row(
        "lower_hypertrophy", "B1", 3, "Bulgarian split squat",
        "unilateral_squat", "bulgarian_split_squat", None,
        3, "unilateral_both", (8, 12), None, (1, 2), (60, 75),
    ),
    _row(
        "lower_hypertrophy", "B2", 4, "Cable crunch",
        "spinal_flexion", "cable_crunch", "cable_stack",
        3, "bilateral", (10, 15), None, (1, 2), (60, 75),
    ),
    _row(
        "lower_hypertrophy", "C1", 5, "Dumbbell Romanian deadlift",
        "hip_hinge", "dumbbell_romanian_deadlift", "dumbbell",
        3, "bilateral", (8, 12), None, (1, 2), (60, 75),
    ),
    _row(
        "lower_hypertrophy", "C2", 6, "Side plank",
        "anti_lateral_flexion", "side_plank", None,
        3, "unilateral_both", None, (25, 45), (2, 3), (45, 60),
    ),
    _row(
        "lower_hypertrophy", "D1", 7, "Barbell hip thrust",
        "hip_extension", "barbell_hip_thrust", "barbell",
        3, "bilateral", (8, 12), None, (1, 2), (45, 60),
    ),
    _row(
        "lower_hypertrophy", "D2", 8, "TRX hamstring curl",
        "knee_flexion", "trx_hamstring_curl", "trx",
        3, "bilateral", (10, 15), None, (1, 2), (45, 60),
    ),
)

EXPECTED_PROGRAM_ITEM_IDS = (
    "prg_dad38a4f-f497-427e-b55b-147faa6654a3",
    "prg_27afb1ab-589a-4451-9ee5-cfc9621f77da",
    "prg_554df3f1-a6aa-43e2-88ef-c397bceaed25",
    "prg_ad20d18b-c16a-4cb7-83a5-cdfc31ab0239",
    "prg_669ca91a-3063-45ec-9f07-c35b13c0ee97",
    "prg_962eed0c-4fe7-4cc2-a95c-84845636cf01",
    "prg_ffa83918-d1c6-4e82-b849-b5b62b02fa73",
    "prg_b663c5b7-2f23-4755-951a-a7d62feeceaf",
    "prg_e82b9106-f947-4802-a5b0-7c38bdf7afa8",
    "prg_50bd9589-7993-4bd1-adff-99ee3d986ecb",
    "prg_386c4a0c-0b15-4ebc-8cae-3ad0322073d0",
    "prg_6562370d-a1df-41dd-9125-a0c44541e797",
    "prg_347a9eab-1563-453e-ac27-f122d1eeabc6",
    "prg_8c1441f6-3677-476a-8261-ad0ef309546a",
    "prg_c4e578fe-a2e9-4c9a-9dd4-a86b9424d190",
    "prg_e7c5798d-cf46-4cd2-a987-4923980652a8",
    "prg_5a137a8a-8a10-4099-ab50-8cb721811c59",
    "prg_9ce07e27-c339-4dc2-851b-c5a6863b80e0",
    "prg_8cd938a3-addd-46fa-a931-eaeb6e486a29",
    "prg_1c875832-bc64-4a62-a029-40cdc7ee2cd5",
    "prg_109d77b9-3285-41d0-94ac-2de3e76f18b8",
    "prg_06b16df2-9f02-490a-ae55-8a2f9f2d4fa1",
    "prg_0b1579f4-58cf-4e03-ae83-62d90155264c",
    "prg_e054490d-85a9-489e-b8fb-fb5d76052cb8",
    "prg_bc096d23-c58a-436e-a78a-4bf35fd5ea5f",
    "prg_13580e68-3fcb-4362-b010-0a271a48a5de",
    "prg_b5f04ab5-518e-4f02-8ae5-07ae5810d697",
    "prg_28be0392-0b52-45f3-9877-69d147c78fa5",
    "prg_9ef33bad-167c-4cf8-8808-8397e2a23435",
    "prg_037bdac4-5e07-4fa4-9e56-33ffbf556db0",
    "prg_05d5f906-aa92-4254-98a7-29735c1cc280",
)


def _load():
    assert hasattr(contracts, "load_program_bootstrap"), (
        "program bootstrap loader is not implemented"
    )
    return contracts.load_program_bootstrap(
        BOOTSTRAP_PATH,
        contracts.load_source_schema(SCHEMA_PATH),
    )


def _payload() -> dict[str, Any]:
    assert BOOTSTRAP_PATH.exists(), "program bootstrap fixture is not implemented"
    return yaml.safe_load(BOOTSTRAP_PATH.read_text(encoding="utf-8"))


def _write_yaml(path: Path, payload: object) -> Path:
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _mutated_load(
    tmp_path: Path,
    payload: dict[str, Any],
    *,
    used_definition_hashes: dict[str, str] | None = None,
):
    return contracts.load_program_bootstrap(
        _write_yaml(tmp_path / "program-bootstrap.yaml", payload),
        contracts.load_source_schema(SCHEMA_PATH),
        used_definition_hashes=used_definition_hashes,
    )


def _public_row(item: object) -> dict[str, object]:
    return {
        field: getattr(item, field)
        for field in EXPECTED_ROWS[0]
    }


def test_bootstrap_contract_is_available() -> None:
    bootstrap = _load()
    assert bootstrap is not None


def test_all_31_prescriptions_match_the_markdown_sources_exactly() -> None:
    bootstrap = _load()
    assert tuple(_public_row(item) for item in bootstrap.prescriptions) == EXPECTED_ROWS
    assert Counter(item.workout_type for item in bootstrap.prescriptions) == {
        "upper_strength": 8,
        "lower_strength": 7,
        "upper_hypertrophy": 8,
        "lower_hypertrophy": 8,
    }
    assert len(bootstrap.prescriptions) == 31


def test_unequal_pairs_unilateral_duration_and_optional_semantics_are_preserved() -> None:
    bootstrap = _load()
    by_key = {
        (item.workout_type, item.block_code): item
        for item in bootstrap.prescriptions
    }
    assert by_key["upper_strength", "A1"].target_sets == 4
    assert by_key["upper_strength", "A2"].target_sets == 3
    assert by_key["lower_strength", "D1"].prescribed_optional is True
    assert by_key["lower_strength", "D1"].rest_seconds_min is None
    assert by_key["lower_hypertrophy", "B1"].laterality == "unilateral_both"
    assert by_key["lower_hypertrophy", "C2"].measurement_kind == "duration"
    assert by_key["lower_hypertrophy", "C2"].laterality == "unilateral_both"


def test_d18_is_exactly_the_dumbbell_rdl_boundary() -> None:
    bootstrap = _load()
    c1 = next(
        item
        for item in bootstrap.prescriptions
        if (item.workout_type, item.block_code)
        == ("lower_hypertrophy", "C1")
    )
    assert c1.exercise_name == "Dumbbell Romanian deadlift"
    assert c1.exercise_variant_id == "dumbbell_romanian_deadlift"
    assert c1.equipment_id == "dumbbell"
    assert c1.setup_id is None
    assert c1.comparison_cohort_id is None


def test_schema_1_1_nullability_is_narrow_and_paired() -> None:
    schema = contracts.load_source_schema(SCHEMA_PATH)
    assert schema.contract.schema_version == "1.1.0"
    assert schema.versions.schema.current == "1.1.0"
    program_columns = {
        column.field: column for column in schema.sheet_tabs.program.columns
    }
    set_columns = {
        column.field: column for column in schema.sheet_tabs.sets.columns
    }
    for field in (
        "rest_seconds_min",
        "rest_seconds_max",
        "equipment_id",
        "setup_id",
        "comparison_cohort_id",
    ):
        assert program_columns[field].nullable is True
    for field in ("equipment_id", "setup_id", "comparison_cohort_id"):
        assert set_columns[field].nullable is False


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (
            lambda p: p["prescriptions"][0].update({"rest_seconds_max": None}),
            "PROGRAM_REST_PAIR_INVALID",
        ),
        (
            lambda p: p["prescriptions"][0].update(
                {"rest_seconds_min": 90, "rest_seconds_max": 60}
            ),
            "PROGRAM_REST_RANGE_INVALID",
        ),
        (
            lambda p: p["prescriptions"][0].update(
                {"comparison_cohort_id": "coh_" + "a" * 64}
            ),
            "PROGRAM_COHORT_WITHOUT_SETUP",
        ),
        (
            lambda p: p["prescriptions"][0].update({"setup_id": "standard"}),
            "PROGRAM_SENTINEL_VALUE_FORBIDDEN",
        ),
        (
            lambda p: p["prescriptions"][14].update({"equipment_id": "bodyweight"}),
            "PROGRAM_SENTINEL_VALUE_FORBIDDEN",
        ),
        (
            lambda p: p["prescriptions"][0].update({"equipment_id": "unknown"}),
            "PROGRAM_SENTINEL_VALUE_FORBIDDEN",
        ),
    ],
)
def test_missing_data_guards_fail_closed(
    tmp_path: Path,
    mutation,
    expected_code: str,
) -> None:
    payload = _payload()
    mutation(payload)
    with pytest.raises(contracts.ContractValidationError) as raised:
        _mutated_load(tmp_path, payload)
    assert raised.value.code == expected_code


def test_ids_are_unique_uuid4_shaped_and_pinned_to_semantic_keys() -> None:
    bootstrap = _load()
    assert bootstrap.program_version_id == (
        "pver_39f699e6-a583-488f-9ef7-ca9ee4e61b7c"
    )
    actual_ids = tuple(item.program_item_id for item in bootstrap.prescriptions)
    assert actual_ids == EXPECTED_PROGRAM_ITEM_IDS
    assert len(set(actual_ids)) == 31
    for value in (bootstrap.program_version_id, *actual_ids):
        parsed = UUID(value.split("_", 1)[1])
        assert parsed.version == 4
        assert parsed.variant == "specified in RFC 4122"


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (
            lambda p: p["prescriptions"][1].update(
                {"program_item_id": p["prescriptions"][0]["program_item_id"]}
            ),
            "DUPLICATE_PROGRAM_ITEM_ID",
        ),
        (
            lambda p: p["prescriptions"][0].update(
                {"semantic_key": "program-v1.0.0:upper_strength:row_1"}
            ),
            "ROW_POSITION_USED_AS_IDENTITY",
        ),
        (
            lambda p: p["prescriptions"][0].update(
                {"semantic_key": "program-v1.0.0:upper_strength:bench_press"}
            ),
            "MUTABLE_TEXT_USED_AS_IDENTITY",
        ),
        (
            lambda p: p["prescriptions"][0].update(
                {"program_item_id": "prg_00000000-0000-4000-8000-000000000000"}
            ),
            "DETERMINISTIC_ID_MISMATCH",
        ),
        (
            lambda p: p["prescriptions"][0].pop("definition_sha256"),
            "CONTRACT_SHAPE_INVALID",
        ),
        (
            lambda p: p["prescriptions"][0].pop("source_sha256"),
            "CONTRACT_SHAPE_INVALID",
        ),
    ],
)
def test_identity_and_hash_failures_are_rejected(
    tmp_path: Path,
    mutation,
    expected_code: str,
) -> None:
    payload = _payload()
    mutation(payload)
    with pytest.raises(contracts.ContractValidationError) as raised:
        _mutated_load(tmp_path, payload)
    assert raised.value.code == expected_code


def test_definition_hash_detects_fixture_tampering(tmp_path: Path) -> None:
    payload = _payload()
    payload["prescriptions"][0]["exercise_name"] = "Mutable renamed exercise"
    with pytest.raises(contracts.ContractValidationError) as raised:
        _mutated_load(tmp_path, payload)
    assert raised.value.code == "PROGRAM_DEFINITION_HASH_MISMATCH"


def test_used_program_version_conflicts_instead_of_mutating(
    tmp_path: Path,
) -> None:
    original = _load()
    used = {
        item.program_item_id: item.definition_sha256
        for item in original.prescriptions
    }
    payload = deepcopy(_payload())
    payload["prescriptions"][0]["exercise_name"] = "Changed used definition"
    payload["prescriptions"][0]["definition_sha256"] = (
        contracts.program_definition_sha256(payload["prescriptions"][0])
    )
    with pytest.raises(contracts.ContractValidationError) as raised:
        _mutated_load(tmp_path, payload, used_definition_hashes=used)
    assert raised.value.code == "PROGRAM_VERSION_CONFLICT"


def test_bootstrap_is_frozen_and_source_hashes_match_repository_files() -> None:
    bootstrap = _load()
    with pytest.raises(Exception):
        bootstrap.program_version_id = "pver_00000000-0000-4000-8000-000000000000"
    for item in bootstrap.prescriptions:
        assert len(item.source_sha256) == 64
        assert len(item.definition_sha256) == 64

