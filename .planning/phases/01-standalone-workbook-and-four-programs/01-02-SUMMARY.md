---
phase: 01-standalone-workbook-and-four-programs
plan: 02
subsystem: contracts
tags: [pydantic, pyyaml, contracts, privacy, tdd]
dependency-graph:
  requires:
    - "01-01 locked Python 3.12+ uv environment"
    - "Normative config/schema.yaml source contract"
  provides:
    - "Frozen extra-forbid SourceSchema contract and safe loader"
    - "Frozen WorkbookBlueprint, TabBlueprint and ManagedObjectBlueprint contracts"
    - "Fail-closed version, authority, identity, formula and reference validation"
    - "Privacy-safe contract diagnostics containing only code, count and SHA-256"
  affects: [01-03, 01-04, 01-05, 01-06, 01-07, 01-08]
tech-stack:
  added: []
  patterns:
    - "yaml.safe_load before typed validation"
    - "Pydantic frozen extra-forbid repository boundaries"
    - "Cross-contract semantic validation before gateway access"
    - "Redacted code/count/hash-only failures"
key-files:
  created:
    - src/workout_tracker/contracts/__init__.py
    - src/workout_tracker/contracts/blueprint.py
    - src/workout_tracker/contracts/source_schema.py
    - src/workout_tracker/adapters/__init__.py
    - tests/contract/test_contract_loading.py
  modified:
    - pyproject.toml
key-decisions:
  - "Workbook-managed identity uses namespaced logical keys and explicitly rejects row, column, position, index and provider-ID semantics."
  - "Repository contract failures cross the public boundary only as a stable code, error count and contract SHA-256."
requirements-completed: []
coverage:
  - id: D1
    description: "Valid source-schema and blueprint YAML load into immutable typed contracts."
    verification:
      - kind: unit
        ref: "tests/contract/test_contract_loading.py#test_valid_repository_contracts_load_as_frozen_typed_models"
        status: pass
    human_judgment: false
  - id: D2
    description: "Unknown shape, invalid versions, duplicate/positional identity, invalid ownership, unregistered formulas and unknown source columns fail closed."
    verification:
      - kind: unit
        ref: "tests/contract/test_contract_loading.py#test_blueprint_failures_are_closed_and_coded"
        status: pass
      - kind: unit
        ref: "tests/contract/test_contract_loading.py#test_source_schema_rejects_unknown_fields_and_row_identity"
        status: pass
    human_judgment: false
  - id: D3
    description: "Diagnostics do not expose payloads, notes, locator names, credential paths or tokens."
    verification:
      - kind: unit
        ref: "tests/contract/test_contract_loading.py#test_diagnostics_never_echo_contract_payload_or_sensitive_context"
        status: pass
    human_judgment: false
duration: 7min
completed: 2026-07-30
status: complete
---

# Phase 01 Plan 02: Strict Repository Contracts Summary

**Fail-closed Pydantic contracts для source schema та workbook blueprint із safe YAML parsing, stable logical identity і redacted code/count/hash diagnostics**

## Performance

- **Duration:** 7 хв
- **Started:** 2026-07-30T22:39:47Z
- **Completed:** 2026-07-30T22:46:27Z
- **Tasks:** 1
- **Files modified:** 6

## Accomplishments

- `config/schema.yaml` тепер завантажується через повністю typed, frozen та `extra="forbid"` boundary; окремі моделі зберігають відмінність між `source_fact`, `sheet_calculated` і `local_derived`.
- Workbook blueprint contract перевіряє schema/formula/bootstrap versions, exact authority roles, source-column references, managed ownership, formula registry та унікальні stable logical keys до будь-якого gateway access.
- Row/column/index/provider identity semantics відхиляються, а всі публічні contract failures містять лише stable code, count і SHA-256 contract bytes без raw payload.

## Task Commits

TDD task зафіксовано окремими атомарними gates:

1. **RED: failure matrix і importable contract boundary** — `21d8a55` (test)
2. **GREEN: strict source/workbook loaders і semantic validation** — `bab6506` (feat)

## Files Created/Modified

- `src/workout_tracker/contracts/source_schema.py` — strict source-contract models, safe loader, cross-reference/authority validation і redacted error boundary.
- `src/workout_tracker/contracts/blueprint.py` — immutable workbook/tab/object/formula models і cross-contract semantic validation.
- `src/workout_tracker/contracts/__init__.py` — public contract exports.
- `src/workout_tracker/adapters/__init__.py` — credential-free adapter package boundary без Google imports.
- `tests/contract/test_contract_loading.py` — valid/frozen case та fail-closed identity, ownership, version, formula, shape і privacy matrix.
- `pyproject.toml` — pytest `src/` import path для коректної collection installless project.

## Decisions Made

- Managed logical keys мають namespaced snake-case форму; частини, що означають row, column, mutable position/index або provider ID, не можуть бути identity.
- Formula text існує лише у version-matching registry entries; managed objects посилаються на `formula_id`, а не містять ad-hoc formula payload.
- Validation exceptions навмисно не прокидають Pydantic/PyYAML payload details через public boundary.

## TDD Evidence

- **RED:** після виправлення setup collection defect targeted pytest зібрав intended test і впав на точному assertion `source_schema is not None`.
- **GREEN:** 11 contract-loading tests пройшли; full default suite також пройшов.
- **REFACTOR:** окремий refactor commit не знадобився; warning-free field aliases додано до GREEN до його commit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Налаштовано pytest import path для `src/` layout**

- **Found during:** Task 1 RED gate
- **Issue:** Initial test collection завершилася `ModuleNotFoundError`, що за plan не є допустимим RED.
- **Fix:** Додано `pythonpath = ["src"]` до існуючої pytest configuration; після цього intended test collected і впав лише на відсутній contract behavior assertion.
- **Files modified:** `pyproject.toml`
- **Verification:** targeted RED pytest collected one test; GREEN і full suites pass.
- **Commit:** `21d8a55`

**Total deviations:** 1 auto-fixed blocking setup issue. **Impact:** лише test import configuration; dependency policy і runtime boundary не змінено.

## Issues Encountered

Після setup correction інших issues не було.

## Authentication Gates

None.

## Known Stubs

None.

## User Setup Required

None - Google credentials, live Sheet locator і зовнішній network state цьому plan не потрібні.

## Verification

- `uv lock --check` — pass.
- `uv run pytest -q tests/contract/test_contract_loading.py` — 11 passed.
- `uv run pytest -q` — pass.
- Усі repository YAML parsed через `yaml.safe_load`.
- Contract import boundary не завантажує `google` або `googleapiclient`.
- `git diff --check`, scoped credential/live-locator scan і requirements coverage — pass.

## Next Phase Readiness

Plan 01-03 може створювати exact seven-tab `config/workbook-blueprint.yaml` та offline gateway, імпортуючи stable strict interfaces без повторного тлумачення repository YAML. Plan 01-03 не розпочинався.

## Self-Check: PASSED

- Усі шість key files існують.
- TDD commits `21d8a55` і `bab6506` присутні в history.
- Task acceptance criteria та plan-level verification пройшли.

---
*Phase: 01-standalone-workbook-and-four-programs*
*Completed: 2026-07-30*
