# Phase 1: Standalone Workbook and Four Programs - Context

**Gathered:** 2026-07-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 створює самодостатній mobile-friendly Google Spreadsheet product:
сім точних вкладок, чотири versioned workout complexes, ручний capture,
contract-defined formulas/dashboard та ідемпотентний setup. ChatGPT tool
capture, локальний mirror і recommendations належать наступним фазам.

</domain>

<decisions>
## Implementation Decisions

### Mobile UX і навігація
- `Старт` показує наступний комплекс, останню завершену сесію, чотири швидкі
  посилання та redacted status sync/backup.
- Один tap із `Старт` відкриває `Програма` з відповідним filter view.
- Основні дії не потребують горизонтального scroll на вузькому mobile viewport.
- Ручний режим залишається повністю придатним без ChatGPT integration.

### Visual system і dashboard
- Використовується світла high-contrast тема з послідовним accent color для
  кожного workout type.
- Значення не кодуються лише кольором: status завжди має текст або symbol.
- `Дашборд` починається з компактних summary cards, нижче містить filters,
  contract-defined trends і data-quality statuses.
- Headers frozen, input/system zones візуально розділені; декоративні merged
  cells та надмірне форматування не використовуються.

### Manual input і validation
- `Сесії` та `Підходи` мають append-only managed input zones; user-editable
  columns ідуть першими, system/formula columns захищені.
- Сесія створюється перед дочірніми sets; зв’язок завжди використовує
  `session_id`, а не row number.
- Stable IDs генеруються один раз керованою операцією й не змінюються після
  сортування або factual correction.
- Missing дозволене значення лишається blank/`NULL`; critical omission отримує
  visible validation status і не перетворюється на zero.
- Dates/times використовують timezone і locale, явно задані workbook
  properties.

### Setup, formulas і portability
- Workbook описується version-controlled machine-readable blueprint і
  застосовується повторюваним Python setup command із dry-run/test backend.
- Setup створює або reconciles лише managed tabs, ranges, formulas, validation,
  protections і charts; він не видаляє довільні user objects.
- Формули мають pinned `formula_version`, реалізують лише `METRICS.md` і
  перевіряються тими самими canonical fixtures, що й локальна metric semantics.
- Program bootstrap бере чотири комплекси з repository specifications,
  детерміновано створює початкові IDs і не змінює вже використану version.
- Clean-workbook та second-run idempotency UAT виконуються на test Spreadsheet;
  production locator і credentials лишаються поза Git.

### the agent's Discretion
- Конкретні Python libraries, module boundaries і workbook blueprint format
  обираються за project constraints та uv-style tooling.
- Точні accent colors, column widths і chart geometry можуть бути підібрані під
  accessibility та mobile UAT без зміни domain semantics.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `config/schema.yaml` уже визначає exact columns, labels, enums, units,
  nullable rules і data classes чотирьох authoritative domain tabs.
- `config/progression-rules.yaml` і `docs/architecture/METRICS.md` визначають
  pinned progression/metric semantics.
- `4-day upper lower program/` містить усі чотири комплекси та session rules.
- `gym equipment/` містить підтверджені equipment і exercise references.

### Established Patterns
- Python 3.12+, uv-style dependency management, Pydantic validation boundary,
  Decimal/scaled numeric semantics і pytest-compatible verification є LOCKED.
- Google Sheets володіє operational facts; Git володіє contracts, formulas,
  executable rules, tests і documentation.
- Source facts, Sheet-calculated values і local-derived values не змішуються.

### Integration Points
- Machine-readable workbook blueprint доповнює `config/schema.yaml`, не
  замінюючи authoritative domain contract.
- Google adapter має окрему boundary від pure blueprint/reconciliation logic.
- Phase 2 використовуватиме ті самі domain columns, stable IDs і manual
  append semantics через controlled ChatGPT writer.
- Phase 3 порівнюватиме dashboard formulas із локальним metric engine на
  canonical fixtures.

</code_context>

<specifics>
## Specific Ideas

Користувач прийняв усі рекомендовані рішення одним явним вибором. Пріоритет:
практична, компактна й зрозуміла таблиця для щоденного використання з телефона,
а не демонстраційний dashboard.

</specifics>

<deferred>
## Deferred Ideas

- ChatGPT preview/confirm/write tools — Phase 2.
- Coherent snapshots, SQLite mirror і query tools — Phase 3.
- Evidence-backed recommendations і program decision workflow — Phase 4.

</deferred>
