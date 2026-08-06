---
phase: 01-standalone-workbook-and-four-programs
plan: 05
subsystem: workbook-input-model
tags: [pydantic, tdd, mobile-ux, google-sheets, stable-ids]
dependency-graph:
  requires:
    - "01-03 exact seven-tab topology and credential-free gateway"
    - "01-04 schema 1.1.0 and audited 31-row program bootstrap"
  provides:
    - "Mobile-first Ukrainian manual-entry, navigation and protection contract"
    - "Pure immutable DesiredWorkbook compiler"
    - "Stable logical session/set reserve capacity without UUID allocation"
    - "Session/version-fenced child-set activation rule"
  affects: [01-06, 01-07, 01-08, 01-09, phase-02]
tech-stack:
  added: []
  patterns:
    - "Schema-derived exact headers, validations and formats compiled by stable logical key"
    - "Input-first append zones separate editable facts from enforced protected system/formula fields"
    - "Reserve capacity uses deterministic logical slots; identity allocation remains at a later apply boundary"
key-files:
  created:
    - src/workout_tracker/workbook/__init__.py
    - src/workout_tracker/workbook/model.py
    - tests/contract/test_input_contract.py
    - tests/unit/test_workbook_model.py
  modified:
    - config/workbook-blueprint.yaml
    - src/workout_tracker/contracts/blueprint.py
    - tests/contract/test_contract_loading.py
key-decisions:
  - "Manual input zones expose factual entry first while primary IDs, version fields, timestamps and formula caches remain protected."
  - "DesiredWorkbook contains only deterministic reserve slot keys and capacity; this plan does not allocate UUIDs."
  - "A set is activatable only when session_id exists in the active-session map and its program_version_id matches exactly."
patterns-established:
  - "Workbook UX objects are frozen value objects keyed by repository-owned logical identity."
  - "Permitted missing input remains blank/NULL and is paired with explicit Ukrainian status text and symbol, never synthetic zero."
requirements-completed: []
coverage:
  - id: D1
    description: "Mobile-first Старт navigation, four one-tap complex filters, append-only input zones, Ukrainian hints/statuses, concrete widths and enforced protections are contract-defined."
    requirement: REQ-WBK-03
    verification:
      - kind: unit
        ref: "tests/contract/test_input_contract.py"
        status: pass
      - kind: integration
        ref: "uv run pytest -q tests/contract/test_input_contract.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Pure compiler resolves seven tabs, exact schema headers/roles, 31 program rows, ranges, filters, validations, formats, protections and layouts."
    requirement: REQ-WBK-03
    verification:
      - kind: unit
        ref: "tests/unit/test_workbook_model.py"
        status: pass
      - kind: integration
        ref: "uv run pytest -q tests/unit/test_workbook_model.py tests/contract/test_input_contract.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "Deterministic reserve slots carry no allocated session/set UUID, and set activation requires an existing session with the same program version."
    requirement: REQ-WBK-03
    verification:
      - kind: unit
        ref: "tests/unit/test_workbook_model.py#test_compilation_is_pure_repeatable_and_contains_no_allocated_session_ids"
        status: pass
      - kind: unit
        ref: "tests/unit/test_workbook_model.py#test_set_activation_requires_existing_session_and_matching_program_version"
        status: pass
    human_judgment: false
duration: 13min
completed: 2026-07-30
status: complete
---

# Phase 01 Plan 05: Mobile Manual Input and Desired Workbook Summary

**Мобільний український input contract із захищеними system/formula zones та чистий deterministic `DesiredWorkbook` compiler для 31 program row і stable logical reserve slots**

## Performance

- **Duration:** 13 хв
- **Started:** 2026-07-30T23:25:35Z
- **Completed:** 2026-07-30T23:38:17Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- `Старт` тепер має exact mobile-first content: наступний комплекс, останню завершену сесію, чотири one-tap links, коротку ручну інструкцію та redacted sync/backup status.
- `Сесії` і `Підходи` мають append-only input-first zones, schema-derived validation/help/formats, stable named ranges, конкретні widths і enforced protections для identity, version, timestamp та formula fields.
- Pure compiler без Google, environment lookup або host locale/timezone створює immutable logical-keyed state для семи tabs, 31 program rows, 152 validation objects, filters, ranges, protections і layouts.
- Session/set reserve capacity представлено лише deterministic keys `reserve:session:*` і `reserve:set:*`; UUID allocation не входить до цього plan, а inactive reserve rows не є operational facts.

## Task Commits

TDD gates зафіксовано атомарно:

1. **Task 1 RED: mobile input contract assertions** — `d79e342` (test)
2. **Task 1 GREEN: safe mobile workbook blueprint** — `3ea4d36` (feat)
3. **Task 2 RED: desired workbook compiler assertions** — `b9afdbb` (test)
4. **Task 2 GREEN: pure desired workbook compiler** — `1fc5167` (feat)

## Files Created/Modified

- `config/workbook-blueprint.yaml` — navigation, palette, status text/symbols, validation policy, ranges, filters, input zones, protections and layouts.
- `src/workout_tracker/contracts/blueprint.py` — frozen typed models and cross-contract validation for the expanded blueprint.
- `src/workout_tracker/workbook/model.py` — immutable desired-state objects and pure compiler.
- `src/workout_tracker/workbook/__init__.py` — public workbook compiler exports.
- `tests/contract/test_input_contract.py` — mobile, validation, input-order and protection contract.
- `tests/unit/test_workbook_model.py` — purity, compilation, reserve and activation tests.
- `tests/contract/test_contract_loading.py` — strict fixture aligned with the complete blueprint shape.

## Decisions Made

- Foreign `session_id` and `program_item_id` selectors remain in the set input sequence with strict named-range validation; primary `set_id`, program version, timestamps and formula values remain enforced protected fields.
- Empty nullable cells compile with `allow_blank=true`, explicit `Немає даних` presentation and no zero substitution.
- Locale `uk_UA` and timezone `America/New_York` are mandatory explicit compiler inputs and fail closed when mismatched.
- `REQ-WBK-03` is implemented and proven offline but remains Pending until required Phase 1 live mobile UAT passes.

## TDD Evidence

- **Task 1 RED:** five intended tests collected and failed only on assertion `mobile input contract is missing`.
- **Task 1 GREEN:** targeted input/contract/topology suite passed `20 passed`; final contract suite passed.
- **Task 2 RED:** five intended tests collected and failed only on assertion `pure desired workbook compiler is missing`.
- **Task 2 GREEN:** plan suites passed `10 passed`; full default suite passed `57 passed`.
- **REFACTOR:** separate refactor commits were unnecessary.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Expanded the strict blueprint contract model**
- **Found during:** Task 1 (mobile input contract)
- **Issue:** `WorkbookBlueprint` rejected every newly required presentation/input key because the plan listed only YAML and new tests, while the existing Pydantic boundary was intentionally `extra="forbid"`.
- **Fix:** Added frozen typed models and semantic cross-contract validation, then updated the existing valid-contract fixture to use the complete repository blueprint.
- **Files modified:** `src/workout_tracker/contracts/blueprint.py`, `tests/contract/test_contract_loading.py`
- **Verification:** `uv run pytest -q tests/contract/test_input_contract.py tests/contract/test_contract_loading.py tests/unit/test_topology.py` — 20 passed.
- **Committed in:** `3ea4d36`

---

**Total deviations:** 1 auto-fixed (1 blocking).
**Impact on plan:** The strict validation boundary now accepts and validates the required blueprint instead of bypassing it; no scope expansion or external behavior was added.

## Issues Encountered

- One ad-hoc compiler acceptance command initially omitted the project `src/` import path. Re-running it with `PYTHONPATH=src`, consistent with pytest configuration, passed; product code and documented test commands were unchanged.

## Authentication Gates

None.

## Known Stubs

None.

## User Setup Required

None - Google credentials, live Sheet locator, network access and UUID allocation are outside this offline plan.

## Verification

- `uv run pytest -q tests/unit/test_workbook_model.py tests/contract/test_input_contract.py` — 10 passed.
- `uv run pytest -q` — 57 passed.
- All repository YAML parsed through `yaml.safe_load`.
- Pure compile acceptance produced 7 tabs, 31 program rows and 152 validation objects.
- Source scan found no Google imports, environment reads, UUID4 allocation or positional identity in the workbook compiler.
- `git diff --check`, scoped secret/live-locator scan and stub scan — pass.

## Next Phase Readiness

Plan 01-06 can consume the pure desired state for formula/metric compilation. Plan 01-06 was not started.

## Self-Check: PASSED

- All seven created/modified primary files exist.
- Commits `d79e342`, `3ea4d36`, `b9afdbb` and `1fc5167` exist in history.
- Both task acceptance gates, plan verification, full suite, YAML parse and privacy checks passed.
- `REQ-WBK-03` remains Pending until required live mobile UAT.

---
*Phase: 01-standalone-workbook-and-four-programs*
*Completed: 2026-07-30*
