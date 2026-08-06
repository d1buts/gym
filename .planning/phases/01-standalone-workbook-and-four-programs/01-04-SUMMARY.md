---
phase: 01-standalone-workbook-and-four-programs
plan: 04
subsystem: program-contract
tags: [pydantic, pyyaml, tdd, stable-ids, schema-migration]
dependency-graph:
  requires:
    - "01-02 strict SourceSchema contract and safe YAML loader"
    - "01-03 exact Програма workbook topology"
  provides:
    - "Audited four-complex 31-prescription bootstrap"
    - "Schema 1.1.0 nullable program-prescription migration"
    - "Deterministic UUID4-shaped program IDs and immutable definition conflicts"
    - "Source locator, source hash and canonical definition hash validation"
  affects: [01-05, 01-06, 01-07, 01-08, phase-02, phase-03]
tech-stack:
  added: []
  patterns:
    - "Pinned namespace plus semantic key with forced RFC UUID version/variant bits"
    - "Unknown program facts remain NULL while performed-set facts stay strict"
    - "Used program definition hashes fail closed instead of mutating history"
key-files:
  created:
    - config/program-bootstrap.yaml
    - src/workout_tracker/contracts/program.py
    - tests/contract/test_program_bootstrap.py
  modified:
    - config/schema.yaml
    - config/workbook-blueprint.yaml
    - config/progression-rules.yaml
    - docs/architecture/DATA_MODEL.md
    - src/workout_tracker/contracts/__init__.py
    - tests/contract/test_contract_loading.py
    - tests/unit/test_topology.py
key-decisions:
  - "Program-level unknown rest is represented only by a NULL pair; half-known or reversed bounds fail closed."
  - "Program equipment/setup/cohort may be NULL, but cohort must be NULL whenever equipment or setup is absent; performed-set fields remain non-null."
  - "Lower Hypertrophy C1 is pinned to Dumbbell Romanian deadlift with dumbbell equipment and NULL setup/cohort."
  - "REQ-WBK-02 remains Pending until the required Phase 1 Google UAT despite complete offline implementation and automated verification."
requirements-completed: []
coverage:
  - id: D1
    description: "Four repository complexes are transcribed as exactly 31 prescriptions with exact 8/7/8/8 counts and row-level semantics."
    requirement: REQ-WBK-02
    verification:
      - kind: unit
        ref: "tests/contract/test_program_bootstrap.py#test_all_31_prescriptions_match_the_markdown_sources_exactly"
        status: pass
      - kind: integration
        ref: "uv run pytest -q tests/contract/test_program_bootstrap.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Schema 1.1.0 preserves unknown prescribed rest/equipment/setup/cohort as NULL without weakening performed sets."
    requirement: REQ-WBK-02
    verification:
      - kind: unit
        ref: "tests/contract/test_program_bootstrap.py#test_schema_1_1_nullability_is_narrow_and_paired"
        status: pass
      - kind: unit
        ref: "tests/contract/test_program_bootstrap.py#test_missing_data_guards_fail_closed"
        status: pass
    human_judgment: false
  - id: D3
    description: "Stable source-owned IDs, source hashes and definition hashes reject positional/text identity and used-version drift."
    requirement: REQ-WBK-02
    verification:
      - kind: unit
        ref: "tests/contract/test_program_bootstrap.py#test_ids_are_unique_uuid4_shaped_and_pinned_to_semantic_keys"
        status: pass
      - kind: unit
        ref: "tests/contract/test_program_bootstrap.py#test_used_program_version_conflicts_instead_of_mutating"
        status: pass
    human_judgment: false
duration: 10min
completed: 2026-07-30
status: complete
---

# Phase 01 Plan 04: Audited Four-Program Bootstrap Summary

**Точна 31-row transcription чотирьох комплексів зі schema 1.1.0, source/definition hashes, deterministic stable IDs і fail-closed immutable version semantics**

## Performance

- **Duration:** 10 хв
- **Started:** 2026-07-30T23:11:48Z
- **Completed:** 2026-07-30T23:21:37Z
- **Tasks:** 1
- **Files modified:** 10

## Accomplishments

- Зафіксовано рівно 31 prescription: `upper_strength=8`, `lower_strength=7`, `upper_hypertrophy=8`, `lower_hypertrophy=8`, включно з unequal pair, unilateral logical sets, duration-per-side і optional Lower Strength D1.
- Schema `1.1.0` дозволяє лише source-unknown program rest/equipment/setup/cohort як `NULL`, перевіряє paired rest та cohort guard і не послаблює actual performed-set facts.
- Pinned semantic-key algorithm створює стабільні UUID4-shaped IDs, а source/definition hashes і used-definition preconditions блокують silent mutation.
- Lower Hypertrophy C1 збережено тільки як `Dumbbell Romanian deadlift`; barbell variant потребуватиме нової program version.

## Task Commits

TDD gates зафіксовано атомарно:

1. **RED: exhaustive audited bootstrap contract** — `c2407b0` (test)
2. **GREEN: schema 1.1.0, 31-row fixture and strict loader** — `43e9a15` (feat)

## Files Created/Modified

- `config/program-bootstrap.yaml` — один active program version і 31 typed prescriptions із stable IDs, locators та hashes.
- `src/workout_tracker/contracts/program.py` — frozen bootstrap models, safe loader, deterministic IDs, range/null/cohort/source/hash/drift validation.
- `tests/contract/test_program_bootstrap.py` — exhaustive 31-row semantic matrix та negative regression cases.
- `config/schema.yaml` — schema `1.1.0` і narrow nullable program fields.
- `config/workbook-blueprint.yaml` — current schema reference `1.1.0`.
- `config/progression-rules.yaml` — current schema reference `1.1.0`.
- `docs/architecture/DATA_MODEL.md` — normative unknown/rest/cohort semantics для schema `1.1.0`.
- `src/workout_tracker/contracts/__init__.py` — public program contract exports.
- `tests/contract/test_contract_loading.py` і `tests/unit/test_topology.py` — schema migration regression references.

## Decisions Made

- ID identity складається лише з pinned namespace, bootstrap version, workout type, block code й semantic exercise order; row number та mutable exercise text виключені.
- Source-known equipment збережено, але material setup не домислюється; тому dependent comparison cohort лишається `NULL`.
- `definition_sha256` охоплює operational prescription semantics, а `source_sha256` version-fences cited Markdown source bytes.
- `REQ-WBK-02` не позначено Complete до required Google UAT відповідно до repository completion policy.

## TDD Evidence

- **RED:** 21 intended tests collected; targeted test failed only on deterministic assertion `program bootstrap loader is not implemented`.
- **GREEN:** targeted bootstrap suite дала `21 passed`; повний default suite — `47 passed`.
- **REFACTOR:** окремий refactor commit не знадобився.

## Deviations from Plan

None - plan executed exactly as revised after both approved decision checkpoints.

## Issues Encountered

Один ad-hoc Python acceptance command спочатку не успадкував pytest `src/` import path; повторний запуск із explicit `PYTHONPATH=src` пройшов. Documented pytest commands і product code не змінювалися.

## Authentication Gates

None.

## Known Stubs

None.

## User Setup Required

None - Google credentials, live Sheet locator і network access цьому plan не потрібні.

## Verification

- `uv run pytest -q tests/contract/test_program_bootstrap.py` — 21 passed.
- `uv run pytest -q` — 47 passed.
- Усі repository YAML parsed через `yaml.safe_load`.
- Program loader acceptance підтвердив exact counts `8/7/8/8` і total `31`.
- `git diff --check`, schema-reference scan, privacy scan, stub scan і 26/26 requirement-to-phase coverage — pass.
- RED `c2407b0` передує GREEN `43e9a15`.

## Next Phase Readiness

Plan 01-05 може використовувати validated program rows і schema `1.1.0` для workbook input/validation projection. Plan 01-05 не розпочинався.

## Self-Check: PASSED

- Усі п’ять primary plan artifacts існують.
- RED commit `c2407b0` і GREEN commit `43e9a15` присутні в history.
- Task acceptance criteria, plan verification, full suite і privacy checks пройшли.

---
*Phase: 01-standalone-workbook-and-four-programs*
*Completed: 2026-07-30*
