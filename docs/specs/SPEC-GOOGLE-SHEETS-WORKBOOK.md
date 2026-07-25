# SPEC: Google Sheets workbook

- **Status:** Normative product contract
- **Version:** 1.0
- **Date:** 2026-07-24
- **Source labels:** Ukrainian and exact

## 1. Workbook topology

Workbook має рівно сім керованих вкладок.

| Вкладка | Роль | Авторитетність |
|---|---|---|
| `Старт` | навігація, коротка інструкція, поточний комплекс | user interface |
| `Програма` | versioned program prescriptions | authoritative |
| `Сесії` | один рядок на виконану сесію | authoritative |
| `Підходи` | logical sets і components | authoritative |
| `Рекомендації` | immutable recommendation history | authoritative |
| `Довідники` | validation lists, aliases, contract metadata | configuration projection |
| `Дашборд` | формули, pivots/charts і statuses | derived |

Чотири authoritative operational tabs зберігають чинні назви й domain
contracts. Три support tabs не стають джерелом виконаних фактів.

## 2. Mobile workflow

### `Старт`

Верхня частина екрана без горизонтального scroll показує:

1. дату й останню завершену сесію;
2. наступний рекомендований workout type за розкладом, без примусового
   автоматичного вибору;
3. посилання на чотири комплекси;
4. коротку інструкцію ручного capture і capture через ChatGPT;
5. статус останнього sync/backup без sensitive locators.

### Manual capture

Ручний режим використовує append-only рядки в `Сесії` та `Підходи`.
Користувацькі колонки стоять перед system/formula columns. Freeze, filter,
width, formats і validation мають дозволяти введення з телефона.

ChatGPT capture пише до тих самих authoritative columns і не створює
паралельний hidden source.

## 3. Program bootstrap

`Програма` завантажує чотири workout types:

| Порядок | Source label | Internal alias | Specification |
|---:|---|---|---|
| 1 | `Верх — сила` | `upper_strength` | `01 upper strength.md` |
| 2 | `Низ — сила` | `lower_strength` | `02 lower strength.md` |
| 3 | `Верх — гіпертрофія` | `upper_hypertrophy` | `03 upper hypertrophy.md` |
| 4 | `Низ — гіпертрофія` | `lower_hypertrophy` | `04 lower hypertrophy.md` |

Кожна prescription row має source-owned `program_item_id`,
`program_version_id`, workout type, order/pair code, exact exercise variant,
equipment/setup, sets, repetition або duration target, target RIR, rest і
optional flag.

Setup:

- детерміновано створює IDs із versioned bootstrap namespace лише під час
  первинного імпорту;
- не змінює вже використану program version;
- створює нову version при зміні prescription;
- не дублює items під час повторного запуску.

## 4. Validation and protection

`Довідники` містить versioned lists для workout types, exercise families,
variants, equipment, units, load basis, loading kind, set status, side mode,
RIR і recommendation status.

Обов’язково:

- dropdown validation для finite enums;
- date/time, integer і decimal constraints;
- formula columns захищені від звичайного ручного редагування;
- system ID columns приховані або візуально відокремлені, але доступні для
  audit;
- alternate colors, frozen header і filter views;
- conditional formatting для missing required field, invalid bundle,
  duplicate ID і pending recommendation;
- validation не перетворює порожнє значення на `0` або порожній рядок у
  domain projection.

Protection не є security boundary: writer і local validator усе одно
перевіряють contract.

## 5. Formula contract

Формули мають `formula_version`. Вони не змінюють source facts.

### Working set

Підхід враховується лише якщо він не warm-up, має valid completed status і
відповідає eligibility rules у `METRICS.md`.

### Working volume

Для repetition/load set:

```text
volume = comparable_load × completed_repetitions × eligible_component_factor
```

Якщо load відсутній або semantics непорівнювані, результат — blank/`NULL` і
status, не zero.

### e1RM

Workbook використовує pinned e1RM formula та eligibility window з
`METRICS.md`. Інші формули не додаються без version bump і tests.

### Session summaries

`Сесії` може містити protected derived columns:

- working sets count;
- completed repetitions;
- comparable working volume;
- maximum comparable load;
- best eligible e1RM;
- average reported RIR;
- average completed rest;
- data-quality status.

### Dashboard

`Дашборд` показує:

- сесії за тиждень і workout type;
- comparable working volume trend;
- best eligible e1RM trend для вибраної exercise variant/cohort;
- target-versus-actual RIR;
- completion і data-quality statuses;
- recent deterministic progression outcomes;
- pending/accepted/rejected recommendations.

Chart/filter ніколи не об’єднує різні variants, equipment, load bases,
assistance semantics або comparison cohorts.

## 6. Named ranges and generated objects

Усі generated named ranges, tables, pivots, charts і protections мають
stable internal names та owner marker. Setup змінює лише власні об’єкти.
Користувацькі довільні вкладки або notes поза managed range не видаляються.

Machine-readable workbook blueprint має містити:

- `workbook_contract_version`;
- exact tabs і columns;
- validation sources;
- formulas з version IDs;
- protections;
- conditional formats;
- chart definitions;
- program bootstrap version.

## 7. Quality gates

До production setup:

- contract і program YAML/Markdown fixtures проходять validation;
- formulas тестуються на normal, missing, invalid та incomparable fixtures;
- setup двічі на clean test workbook дає той самий logical state;
- mobile UAT проходить на вузькому viewport;
- жоден committed fixture не містить live Sheet ID або персональних даних.
