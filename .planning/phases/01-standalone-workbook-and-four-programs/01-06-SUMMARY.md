---
phase: 01-standalone-workbook-and-four-programs
plan: 06
subsystem: workbook-metrics-dashboard
tags: [decimal, metrics-v1, google-sheets, dashboard, tdd, cohort-safety]
dependency-graph:
  requires:
    - "01-05 mobile input contract and immutable DesiredWorkbook compiler"
    - "schema 1.1.0 source facts and sheet_calculated boundaries"
  provides:
    - "Pinned metrics-v1 FormulaRegistry and deterministic offline fixture oracle"
    - "Canonical normal, missing, invalid and incomparable metric matrix"
    - "Versioned cohort-safe dashboard, derived placements and chart contract"
  affects: [01-07, 01-08, 01-09, phase-03]
tech-stack:
  added: []
  patterns:
    - "Formula text exists only in a Git-owned registry; blueprint stores stable ID and version references"
    - "Every displayed scalar is paired with an explicit status/reason and unavailable values remain NULL"
    - "Trend helpers retain exact cohort dimensions and charts preserve NULL gaps"
key-files:
  created:
    - src/workout_tracker/workbook/formulas.py
    - tests/fixtures/metrics-v1.yaml
    - tests/unit/test_metrics_fixtures.py
    - tests/contract/test_dashboard_contract.py
  modified:
    - config/workbook-blueprint.yaml
    - src/workout_tracker/contracts/blueprint.py
    - src/workout_tracker/workbook/model.py
    - src/workout_tracker/workbook/__init__.py
    - tests/contract/test_contract_loading.py
    - tests/unit/test_topology.py
key-decisions:
  - "Formula templates remain solely in FormulaRegistry; workbook-blueprint.yaml carries only formula_id and formula_version references."
  - "A nullable program cohort never authorizes comparison: performed metrics require complete exact variant, equipment, setup, load basis and cohort dimensions."
  - "Dashboard order is fixed as cards, filters, cohort-safe trends, then data-quality statuses; charts never interpolate NULL gaps."
patterns-established:
  - "Canonical YAML cases drive the same deterministic oracle contract later used for live Sheet assertions."
  - "Decimal precision 28, ROUND_HALF_EVEN and exact 0.45359237 lb-to-kg conversion are calculation-boundary invariants."
requirements-completed: []
coverage:
  - id: D1
    description: "Canonical metrics-v1 fixtures and offline oracle enforce working-set eligibility, exact units, e1RM 1–12 and explicit NULL/status outcomes."
    requirement: REQ-WBK-04
    verification:
      - kind: unit
        ref: "tests/unit/test_metrics_fixtures.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Workbook blueprint defines versioned protected derived placements and a complete cohort-safe dashboard with accessible null-preserving charts."
    requirement: REQ-WBK-04
    verification:
      - kind: integration
        ref: "tests/contract/test_dashboard_contract.py"
        status: pass
    human_judgment: false
duration: 9min
completed: 2026-07-30
status: complete
---

# Phase 01 Plan 06: Pinned Metrics and Cohort-Safe Dashboard Summary

**Pinned `metrics-v1` FormulaRegistry with Decimal fixture oracle and a high-contrast dashboard contract that preserves cohort boundaries, NULL gaps and explicit quality statuses**

## Performance

- **Duration:** 9 хв
- **Started:** 2026-07-30T23:42:03Z
- **Completed:** 2026-07-30T23:50:27Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments

- Створено canonical fixture matrix для valid kg/lb, unilateral, warm-up, skipped/void, missing load/RIR, mixed cohort, machine level, assistance/bodyweight, e1RM 1/12/13, Decimal tie, paired rest, invalid record та empty scope.
- Реалізовано immutable `FormulaRegistry` і offline oracle лише для pinned `metrics-v1`; arithmetic використовує `Decimal`, precision 28, `ROUND_HALF_EVEN` та exact lb conversion.
- `Дашборд` тепер має compact cards, explicit filters, cohort-complete helper ranges, accessible charts із `interpolate_nulls=false`, textual statuses, deterministic progression display і recommendation lifecycle display без обчислення рекомендацій.

## Task Commits

TDD gates зафіксовано атомарно:

1. **Task 1 RED: canonical metrics-v1 fixture matrix** — `74659a8` (test)
2. **Task 1 GREEN: pinned fixture oracle and formula registry** — `ca97d9c` (feat)
3. **Task 2 RED: complete dashboard contract** — `9a55fd7` (test)
4. **Task 2 GREEN: cohort-safe dashboard blueprint and compilation** — `7b581c6` (feat)

## Files Created/Modified

- `src/workout_tracker/workbook/formulas.py` — registry, exact Decimal arithmetic, eligibility/cohort gates and canonical fixture evaluator.
- `tests/fixtures/metrics-v1.yaml` — shared semantic cases with value/NULL, unit, status and sorted exclusion reasons.
- `tests/unit/test_metrics_fixtures.py` — fixture matrix, no-float boundary, registry and cohort regression tests.
- `tests/contract/test_dashboard_contract.py` — cards, filters, placements, helpers, charts, statuses and compiled dashboard assertions.
- `config/workbook-blueprint.yaml` — contract version 1.1.0, formula references, protected placements and complete dashboard.
- `src/workout_tracker/contracts/blueprint.py` — strict frozen dashboard/formula placement models and fail-closed semantic validation.
- `src/workout_tracker/workbook/model.py` — compiled desired state now retains formula version, placements and dashboard.
- `src/workout_tracker/workbook/__init__.py` — public metric registry/oracle exports.
- `tests/contract/test_contract_loading.py` and `tests/unit/test_topology.py` — strict contract fixture and version regression updates.

## Decisions Made

- Formula templates are not duplicated in YAML. The blueprint references only stable `formula_id` plus `metrics-v1`, preventing source text from entering executable formula construction.
- Mass-based kg/lb can share a unit family only after exact conversion; `machine_level` stays separate, while assistance/bodyweight and incomplete cohort dimensions produce explicit non-value results.
- `REQ-WBK-04` is implemented and proven offline but remains Pending until the later live Google formula/chart UAT confirms provider recalculation and rendering.

## TDD Evidence

- **Task 1 RED:** seven tests collected; five failed only on intended assertions that the metrics oracle/registry was absent.
- **Task 1 GREEN:** `uv run pytest -q tests/unit/test_metrics_fixtures.py` — 7 passed.
- **Task 2 RED:** five tests collected and failed only on missing blueprint version, formula placements, dashboard and compiled dashboard state.
- **Task 2 GREEN:** combined metric/dashboard/contract/model suite — 28 passed.
- **REFACTOR:** no separate refactor commit was needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Expanded strict blueprint and desired-state models**
- **Found during:** Task 2 (dashboard contract)
- **Issue:** The existing Pydantic boundary used `extra="forbid"` and `DesiredWorkbook` had no typed formula-placement/dashboard fields, so the required blueprint additions could not load or reach later reconciliation.
- **Fix:** Added frozen typed dashboard/formula placement models, fail-closed semantic checks and compiled desired-state fields; aligned the existing strict contract and topology regressions with workbook contract 1.1.0.
- **Files modified:** `src/workout_tracker/contracts/blueprint.py`, `src/workout_tracker/workbook/model.py`, `tests/contract/test_contract_loading.py`, `tests/unit/test_topology.py`
- **Verification:** Full suite passed 69 tests.
- **Committed in:** `7b581c6`

---

**Total deviations:** 1 auto-fixed (1 blocking).
**Impact on plan:** Required contract data remains validated and immutable instead of bypassing the established Pydantic boundary; no external service, persistence or recommendation logic was added.

## Issues Encountered

- The first full-suite run found one stale topology assertion pinned to workbook contract `1.0.0`; updating that regression to the planned dashboard contract `1.1.0` resolved the only failure.

## Authentication Gates

None.

## Known Stubs

None. Formula `{column:...}` tokens are intentional registry templates resolved later from compiled logical headers; they are not runtime mock data or UI placeholders.

## User Setup Required

None — this plan is fully offline. Google credentials and a disposable test Spreadsheet remain reserved for the guarded transport/UAT plans.

## Verification

- `uv run pytest -q tests/unit/test_metrics_fixtures.py tests/contract/test_dashboard_contract.py` — 12 passed.
- `uv run pytest -q` — 69 passed.
- All 7 repository YAML files parsed through `yaml.safe_load`.
- `git diff --check` and scoped credential/live-locator scan passed.
- Formula registry contains exactly the nine pinned IDs; YAML contains no formula text.

## Next Phase Readiness

Plan 01-07 can reconcile compiled formula placements, helper ranges and charts by stable logical key. Plan 01-07 was not started.

## Self-Check: PASSED

- All ten created/modified implementation and test files exist.
- Commits `74659a8`, `ca97d9c`, `9a55fd7` and `7b581c6` exist in history.
- Both task acceptance gates, plan verification, full suite, YAML parse, privacy scan and stub/threat review passed.
- `REQ-WBK-04` remains Pending until required live formula/chart UAT.

---
*Phase: 01-standalone-workbook-and-four-programs*
*Completed: 2026-07-30*
