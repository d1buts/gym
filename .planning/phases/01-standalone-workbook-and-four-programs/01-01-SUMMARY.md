---
phase: 01-standalone-workbook-and-four-programs
plan: 01
subsystem: infrastructure
tags: [python, uv, pytest, dependency-policy, google-sheets]
dependency-graph:
  requires: []
  provides:
    - "Python 3.12+ uv project runtime"
    - "Exact D-20 direct dependency policy and committed lock"
    - "Offline-default pytest collection with opt-in google_uat marker"
  affects: [01-02, 01-03, 01-04, 01-05, 01-06, 01-07, 01-08, 01-09]
tech-stack:
  added:
    - "uv 0.12.0"
    - "pydantic 2.13.4"
    - "PyYAML 6.0.3"
    - "google-api-python-client 2.198.0"
    - "google-auth 2.56.2"
    - "pytest 9.1.1"
  patterns:
    - "Bounded direct dependencies with exact transitive resolution in uv.lock"
    - "Live Google UAT disabled unless a dedicated runner explicitly opts in"
key-files:
  created:
    - uv.lock
    - src/workout_tracker/__init__.py
    - tests/conftest.py
    - tests/contract/test_dependency_policy.py
  modified:
    - pyproject.toml
key-decisions:
  - "D-20 remains the exact five-package direct allowlist; no additional direct packages were introduced."
  - "The owner-approved canonical google-auth source is googleapis/google-cloud-python/tree/main/packages/google-auth."
requirements-completed: []
coverage:
  - id: D1
    description: "Official uv runtime is available and resolves a Python 3.12+ interpreter."
    verification:
      - kind: integration
        ref: "command -v uv && uv --version && uv python find '>=3.12'"
        status: pass
    human_judgment: false
  - id: D2
    description: "The exact D-20 dependency set is source-mapped, locked, synced, importable, and regression-tested."
    verification:
      - kind: integration
        ref: "uv lock --check && uv sync --locked"
        status: pass
      - kind: unit
        ref: "tests/contract/test_dependency_policy.py#test_dependency_policy_matches_approved_d20_set_and_sources"
        status: pass
      - kind: integration
        ref: "uv run python -c import-approved-packages"
        status: pass
    human_judgment: false
  - id: D3
    description: "Default pytest collection requires no Google authorization and keeps google_uat disabled."
    verification:
      - kind: unit
        ref: "tests/contract/test_dependency_policy.py#test_google_uat_requires_explicit_live_runner_opt_in"
        status: pass
      - kind: integration
        ref: "uv run pytest -q --collect-only"
        status: pass
    human_judgment: false
duration: 28min
completed: 2026-07-30
status: complete
---

# Phase 01 Plan 01: Python Toolchain and Dependency Policy Summary

**Офіційний uv bootstrap, точний D-20 allowlist із committed lockfile та offline-default pytest boundary для майбутнього Google UAT**

## Performance

- **Duration:** 28 хв
- **Started:** 2026-07-30T22:07:18Z
- **Completed:** 2026-07-30T22:34:58Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Підтверджено офіційний `uv 0.12.0` і Python 3.12+ runtime до dependency resolution.
- Live PyPI metadata повторно підтвердила всі п’ять схвалених назв і source mappings, включно з перенесеним `google-auth`; exact resolution збережено в `uv.lock`.
- Pytest contract забороняє зайві direct dependencies, а `google_uat` за замовчуванням не виконується без explicit opt-in dedicated runner.

## Task Commits

Кожен результат зафіксовано атомарно:

1. **Task 1: Bootstrap uv from the official installer when absent** — `2befdc8` (chore)
2. **Task 2 RED: Add failing dependency policy contract** — `222f68a` (test)
3. **Task 2 GREEN: Enforce approved package policy and exact lock** — `1e66600` (chore)

Окреме рішення checkpoint щодо migrated `google-auth` source зафіксовано в `a30f8fa`.

## Files Created/Modified

- `pyproject.toml` — Python 3.12+ metadata, bounded D-20 dependencies, pytest paths/marker і approved source policy.
- `uv.lock` — exact 33-package resolution для схваленого direct set.
- `src/workout_tracker/__init__.py` — початкова package version.
- `tests/conftest.py` — offline-default skip для `google_uat` до explicit dedicated-runner opt-in.
- `tests/contract/test_dependency_policy.py` — exact direct-package/source allowlist і opt-in regression contract.

## Decisions Made

- Canonical `google-auth` source після upstream migration — `googleapis/google-cloud-python/tree/main/packages/google-auth`; archived repository більше не використовується.
- Direct dependency set лишається рівно `pydantic`, `PyYAML`, `google-api-python-client`, `google-auth` і `pytest`; останній належить лише до development group.

## TDD Evidence

- **RED:** `uv run --with 'pytest>=9.1,<10' pytest -q tests/contract/test_dependency_policy.py` collected the intended test and failed only because runtime dependencies were still empty.
- **GREEN:** dependency declarations, D-20 source policy, lockfile та offline UAT gate додано; contract suite і full default suite дають `2 passed`.
- **REFACTOR:** окремий refactor не знадобився.

## Deviations from Plan

None - plan executed exactly as revised after the approved checkpoint.

## Issues Encountered

- Попередній canonical `google-auth` repository виявився archived. Fail-closed checkpoint спрацював як заплановано; owner окремо схвалив migrated source, а повторний live PyPI metadata check підтвердив його перед lock generation.

## Authentication Gates

None.

## Known Stubs

None.

## User Setup Required

None - external Google configuration не потрібна для цього plan.

## Verification

- `uv lock --check` — pass.
- `uv sync --locked` — pass.
- `uv run pytest -q tests/contract/test_dependency_policy.py` — 2 passed.
- `uv run pytest -q --collect-only` — 2 collected without external state.
- `uv run pytest -q` — 2 passed.
- Imports `pydantic`, `yaml`, `google.auth`, `googleapiclient`, `pytest` — pass.
- All repository YAML parsed with `yaml.safe_load`; `git diff --check` and scoped privacy scan — pass.

## Next Phase Readiness

Plan 01-02 може використовувати locked Python environment і pytest contract infrastructure. External Google credentials та live Sheet locator досі не потрібні й залишаються поза Git.

## Self-Check: PASSED

- Усі п’ять key files існують.
- Task commits `2befdc8`, `222f68a` і `1e66600` присутні в history.
- Plan-level verification і acceptance criteria пройшли.

---
*Phase: 01-standalone-workbook-and-four-programs*
*Completed: 2026-07-30*
