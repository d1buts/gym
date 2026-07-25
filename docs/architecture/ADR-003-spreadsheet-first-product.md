# ADR-003: Spreadsheet-first продукт і контрольований запис через ChatGPT

- **Status:** Accepted
- **Date:** 2026-07-24
- **Decision owner:** repository owner
- **Supersedes in part:** ADR-001 consequence that v1 is read-only
- **Refines:** ADR-002 by making Python/SQLite an auxiliary analytical layer

## Context

Попередній milestone оптимізував архітектуру навколо локального read-only CLI.
Це добре визначило schema validation, snapshots, provenance, метрики й restore,
але не відповідало основній користувацькій цілі:

1. мати якісно спроєктовану Google Spreadsheet із чотирма тренувальними
   комплексами, формулами та зрозумілим mobile workflow;
2. додавати нове тренування природною мовою через ChatGPT;
3. читати й аналізувати історію без ручного зведення даних;
4. отримувати обґрунтовані рекомендації, не втрачаючи контроль над фактами.

Якщо workbook, capture і write-back відкласти, система може мати надійне
дзеркало, але не мати корисного щоденного продукту.

## Decision

### Основний продукт

Google Spreadsheet є основним користувацьким інтерфейсом і operational source
of truth. Вона містить версійовану програму, виконані сесії та підходи,
рекомендації, довідники й похідний дашборд.

Перший milestone включає:

- створення або налаштування workbook;
- завантаження чотирьох комплексів із repository specifications;
- data validation, захищені formula columns, умовне форматування й дашборд;
- контрольований capture/write-back через ChatGPT tools;
- читання історії, відтворювану аналітику й evidence-backed recommendations;
- audit, backup і restore перевірку.

### Контрольований write path

ChatGPT не отримує довільного доступу до комірок. Інтеграція публікує вузькі
versioned tools, незалежно від конкретної поверхні ChatGPT plugin/MCP:

- `preview_workout` нормалізує повідомлення, повертає пропущені або неоднозначні
  поля й формує preview без запису;
- `commit_workout` приймає лише підтверджений preview, stable IDs та
  `idempotency_key`, після чого атомарно додає session/set bundle;
- read tools повертають мінімальний набір фактів або агрегатів для конкретного
  запиту;
- recommendation tools створюють окрему пропозицію з evidence, але не
  переписують виконані факти або програму.

Кожен зовнішній запис потребує явного підтвердження користувача. Повторний
виклик із тим самим `idempotency_key` повертає попередній результат і не
створює дубль. Невалідний session/set bundle не записується частково.

### Авторизація

Аналітичний pull використовує read-only authorization. Writer має окрему
мінімальну credential boundary і може:

- додавати лише до allowlisted operational tables;
- читати потрібні contract/version preconditions;
- записувати audit metadata;
- відмовлятися від arbitrary range/cell operations.

Зміна програми або прийняття рекомендації є окремою важливою дією та потребує
явного owner approval.

### Аналітичний контур

Python 3.12+, Pydantic і SQLite залишаються прийнятим стеком для validation,
immutable snapshots, rebuildable mirror, metrics, evidence reports і restore.
Цей контур підтримує Spreadsheet-продукт, але не є його основним UI.

## Consequences

- V1 більше не є read-only: capture, allowlisted write-back і recommendations
  входять до scope.
- Spreadsheet UX і формули мають власний нормативний контракт.
- Інтеграція ChatGPT не прив’язується до однієї назви продуктового механізму;
  стабільною межею є versioned tool schema.
- Невідомі значення не вигадуються. Capture ставить уточнення або зберігає
  дозволене `NULL`.
- Raw facts, Sheet-calculated values, local-derived metrics і recommendations
  залишаються різними класами даних.
- AI-generated recommendation не може видаватися за deterministic progression
  rule, медичний висновок або автоматично прийняту зміну програми.
- Bulk workout history, довільні нотатки та health context не надсилаються до
  моделі без конкретної потреби й явного користувацького запиту.

## Rejected alternatives

### Лише локальний CLI

Надійний як аналітичний backend, але не вирішує щоденний capture і роботу з
таблицею.

### Довільне редагування Sheet моделлю

Не дає стабільних preconditions, ідемпотентності, атомарності або
відтворюваного audit trail.

### Автоматичне застосування рекомендацій

Змішує пораду, deterministic rule і авторитетну програму та прибирає
користувацький контроль.
