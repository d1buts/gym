# ADR-001: Межі джерел правди

- **Status:** Accepted
- **Date:** 2026-07-24
- **Scope:** workout facts, program prescriptions, executable rules, local data
- **Superseded in part by:** ADR-003 for controlled v1 write-back

## Context

Початковий документ одночасно описував вкладку `Програма` в Google Sheets і
майбутній `config/program.yaml`, не визначаючи, яка копія перемагає при
розходженні. Аналогічно, локальні CSV/JSON/SQLite могли бути помилково
сприйняті як незалежні версії тренувальних фактів.

Система потребує одного власника для кожного класу інформації. Інакше
ідемпотентний pull, історична програма та відтворюваний звіт не мають
однозначної семантики.

## Decision

### Google Sheets

Google Sheets є operational source of truth для:

- виконаних сесій;
- виконаних підходів;
- наявних зовнішніх рекомендацій;
- версійованих operational prescriptions у вкладці `Програма`.

Кожна нова сесія посилається на `program_version_id`, що був чинним під час
виконання. Уже використану версію програми не редагують заднім числом:
створюють нову версію.

### Git

Git є source of truth для:

- контракту вкладок і нормалізації;
- алгоритмів синхронізації;
- формул метрик;
- executable progression rules;
- тестів, документації та прикладів без персональних даних.

Markdown-файли чотириденної програми є bootstrap specification і
людиночитаним поясненням. Вони не повинні непомітно перезаписувати історичні
prescriptions у Google Sheets.

`config/program.yaml`, якщо з’явиться, може бути лише згенерованим
mirror/validator artifact. Його не можна редагувати як друге незалежне
джерело програми.

### Локальне сховище

Raw snapshots, normalized datasets і SQLite є rebuildable analytical
projections. Вони не стають власниками тренувальних фактів.

Локальні розрахунки зберігаються окремо від source facts і завжди мають
`snapshot_id`, formula/ruleset version та evidence links.

## Consequences

- Ручне виправлення тренувального факту виконується в Google Sheets і
  надходить локально наступним pull під тим самим stable ID.
- Позиція рядка не є identity.
- Для `Сесії`, `Підходи`, `Програма` і `Рекомендації` потрібні source-owned
  stable IDs.
- Аналітичний pull використовує read-only authorization.
- Контрольований v1 write-back має окрему мінімальну credential boundary,
  allowlist, stable-ID preconditions, idempotency та explicit confirmation
  згідно з ADR-003.
- Зміна ownership boundary потребує нового ADR і migration plan.

## Rejected alternatives

### Git як власник усієї програми

Дає зручний diff, але створює write-path у Sheets уже для v1 і ускладнює
поточний mobile-first operational workflow.

### Двостороння синхронізація

Не прийнята через конфлікти, відсутність row-level uniqueness у Sheets і
непропорційну складність для персонального v1.

### SQLite як primary store

Відкладено до появи окремого інтерфейсу, кількох користувачів або складнішого
API.
