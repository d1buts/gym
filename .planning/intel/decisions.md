# Синтезовані рішення

## ADR-001: Межі джерел правди

- source: /home/muuser/bushuk-labs/gym/docs/architecture/ADR-001-authority-boundaries.md
- status: locked
- scope: workout facts, program prescriptions, executable rules, local data
- decision: Google Sheets є operational source of truth для виконаних сесій, підходів, зовнішніх рекомендацій і версійованих prescriptions у `Програма`. Git володіє контрактами, нормалізацією, формулами, executable rules, tests і документацією. Raw snapshots, normalized datasets і SQLite є rebuildable analytical projections. Кожна сесія посилається на чинний `program_version_id`; row position ніколи не є identity.

## ADR-002: Python і SQLite для локального аналітичного контуру

- source: /home/muuser/bushuk-labs/gym/docs/architecture/ADR-002-python-sqlite-v1.md
- status: locked
- scope: local validation, synchronization, analytics and restore stack
- decision: Локальний контур використовує Python 3.12+, uv-style dependency management, Pydantic validation boundary, SQLite з foreign keys і transactional staging promotion, pytest-compatible tests та `Decimal` або scaled integers для authoritative numeric calculations. Spreadsheet залишається самодостатнім продуктом, а business logic не залежить від CLI або Google client.

## ADR-003: Spreadsheet-first продукт і контрольований запис через ChatGPT

- source: /home/muuser/bushuk-labs/gym/docs/architecture/ADR-003-spreadsheet-first-product.md
- status: locked
- scope: primary product, ChatGPT write path, authorization and analytical boundary
- decision: Google Spreadsheet є основним UI й operational source of truth. Перший milestone включає workbook із чотирма комплексами, formulas/dashboard, narrow versioned ChatGPT tools, history analytics, evidence-backed recommendations, audit, backup і restore. Кожен write потребує preview, explicit confirmation, stable IDs, contract/version preconditions та idempotency; writer має окремі мінімальні credentials і не може довільно змінювати cells/ranges. Python/Pydantic/SQLite лишаються допоміжним rebuildable analytical layer.

## Підсумок

- Рішень виділено: 3
- Locked-рішень: 3
- Proposed-рішень: 0
