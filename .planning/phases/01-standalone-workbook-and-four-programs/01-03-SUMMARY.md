---
phase: 01-standalone-workbook-and-four-programs
plan: 03
subsystem: workbook-topology
tags: [google-sheets, topology, gateway, pydantic, tdd]
dependency-graph:
  requires:
    - "01-02 strict SourceSchema and WorkbookBlueprint contracts"
  provides:
    - "Exact versioned seven-tab managed workbook topology"
    - "Credential-free WorkbookGateway observe/apply port"
    - "Non-destructive in-memory gateway with stable managed fingerprints"
  affects: [01-04, 01-05, 01-06, 01-07, 01-08, 01-09]
tech-stack:
  added: []
  patterns:
    - "Stable logical keys own managed identity; provider IDs and positions are observations only"
    - "Managed fingerprints hash normalized structural fields and workbook properties"
    - "Unowned workbook state is preserved and surfaced through stable status codes"
key-files:
  created:
    - config/workbook-blueprint.yaml
    - src/workout_tracker/adapters/port.py
    - src/workout_tracker/adapters/memory.py
    - tests/contract/test_gateway_contract.py
    - tests/unit/test_topology.py
  modified: []
key-decisions:
  - "Managed fingerprints include only stable managed structure plus locale/timezone; provider IDs and positions are excluded."
  - "Default-tab cleanup requires an explicit clean-initialization plan and a sole empty unowned tab marked as the provider default."
requirements-completed: []
coverage:
  - id: D1
    description: "Versioned blueprint defines exactly seven managed tabs in the required Ukrainian order, with four authoritative schema links and pinned workbook properties."
    requirement: "REQ-WBK-01"
    verification:
      - kind: unit
        ref: "tests/unit/test_topology.py"
        status: pass
      - kind: integration
        ref: "uv run pytest -q tests/unit/test_topology.py tests/contract/test_contract_loading.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Credential-free gateway observes and applies normalized topology while preserving unowned tabs and tightly restricting default-tab cleanup."
    requirement: "REQ-WBK-01"
    verification:
      - kind: unit
        ref: "tests/contract/test_gateway_contract.py"
        status: pass
      - kind: integration
        ref: "uv run pytest -q tests/unit/test_topology.py tests/contract/test_contract_loading.py tests/contract/test_gateway_contract.py"
        status: pass
    human_judgment: false
duration: 6min
completed: 2026-07-30
status: complete
---

# Phase 01 Plan 03: Exact Workbook Topology and Offline Gateway Summary

**Точний семивкладковий workbook blueprint із credential-free gateway, стабільним managed fingerprint і fail-visible збереженням unowned state**

## Performance

- **Duration:** 6 хв
- **Started:** 2026-07-30T22:50:55Z
- **Completed:** 2026-07-30T22:57:16Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- `config/workbook-blueprint.yaml` фіксує рівно сім managed вкладок у порядку `Старт`, `Програма`, `Сесії`, `Підходи`, `Рекомендації`, `Довідники`, `Дашборд`, а також exact `uk_UA` і `America/New_York`.
- Чотири authoritative вкладки зв’язані з відповідними domain tabs `config/schema.yaml`; три support tabs явно лишаються non-authoritative.
- Offline gateway застосовує exact topology без Google imports, credentials, environment secrets або live locator; unowned tabs зберігаються зі status `UNMANAGED_TAB_PRESENT`.
- Clean-init exception видаляє лише єдину порожню unowned default tab за explicit flag; повторне застосування того самого blueprint дає logical no-op.

## Task Commits

Кожен TDD gate зафіксовано атомарно:

1. **Task 1 RED: Exact topology assertions** — `63c74a9` (test)
2. **Task 1 GREEN: Versioned seven-tab blueprint** — `bfbd675` (feat)
3. **Task 2 RED: Offline gateway behavior contract** — `8dcf8bf` (test)
4. **Task 2 GREEN: Credential-free non-destructive gateway** — `6ef3f05` (feat)

## Files Created/Modified

- `config/workbook-blueprint.yaml` — exact managed tab order, authority links, locale/timezone і version roots.
- `src/workout_tracker/adapters/port.py` — immutable `ObservedTab`, `ObservedWorkbook`, `ChangePlan`, `ApplyResult` та `WorkbookGateway`.
- `src/workout_tracker/adapters/memory.py` — offline observe/apply implementation, canonical fingerprint і guarded clean initialization.
- `tests/unit/test_topology.py` — exact topology, versions, authority та stable identity assertions.
- `tests/contract/test_gateway_contract.py` — shared gateway behavior для isolation, preservation, cleanup restriction, fingerprints та idempotency.

## Decisions Made

- Managed fingerprint не містить provider ID, provider position або unowned content; він залежить лише від canonical managed structure та desired workbook properties.
- Unowned tab ніколи не видаляється за title heuristic. Cleanup дозволений лише для явно позначеної provider-default tab, якщо вона порожня, unowned і єдина до initialization.
- `REQ-WBK-01` реалізовано й автоматично доведено offline, але requirement лишається `Pending` до обов’язкового Phase 1 Google UAT згідно з repository completion policy.

## TDD Evidence

- **Task 1 RED:** три intended topology tests collected і впали лише на assertion `managed workbook topology is missing`.
- **Task 1 GREEN:** exact topology blueprint додано; topology та prior contract suite дали `14 passed`.
- **Task 2 RED:** сім intended gateway cases collected і впали на конкретних missing-behavior assertions для apply, status, cleanup, fingerprint та idempotency.
- **Task 2 GREEN:** gateway behavior реалізовано; targeted suite дала `13 passed`, plan-level suite — `24 passed`, full default suite — `26 passed`.
- **REFACTOR:** окремі refactor commits не знадобилися.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Один ad-hoc acceptance script спочатку не бачив `src/` layout поза pytest configuration; повторний запуск із explicit `PYTHONPATH=src` пройшов. Product code і documented pytest commands не змінювалися.

## Authentication Gates

None.

## Known Stubs

None.

## User Setup Required

None - Google credentials, network access і live Sheet locator цьому plan не потрібні.

## Verification

- `uv run pytest -q tests/unit/test_topology.py tests/contract/test_contract_loading.py tests/contract/test_gateway_contract.py` — 24 passed.
- `uv run pytest -q` — 26 passed.
- `config/schema.yaml` і `config/workbook-blueprint.yaml` parsed через `yaml.safe_load`.
- Exact topology/non-destructive acceptance script — pass.
- Gateway source scan підтвердив відсутність Google imports і environment secret access.
- `git diff --check`, scoped credential/live-locator scan і stub scan — pass.

## Next Phase Readiness

Plan 01-04 може додавати чотири versioned program complexes до stable `Програма` topology через той самий strict blueprint/gateway boundary. Plan 01-04 не розпочинався.

## Self-Check: PASSED

- Усі п’ять key files існують.
- Commits `63c74a9`, `bfbd675`, `8dcf8bf` і `6ef3f05` присутні в history.
- Обидва task acceptance gates, plan-level verification і privacy checks пройшли.
- `REQ-WBK-01` не позначено Complete до required Google UAT.

---
*Phase: 01-standalone-workbook-and-four-programs*
*Completed: 2026-07-30*
