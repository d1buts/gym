# Нормативний контракт метрик

**Version:** `metrics-v1`

**Status:** Accepted design contract

**Applies to:** normalized data, Sheet dashboard, SQLite analytics,
deterministic progression and substantive reports

## 1. Мета і нормативна мова

Цей документ визначає однакову семантику метрик для Sheet formulas/dashboard,
CLI, SQLite, тестів і звітів. `MUST`, `MUST NOT`, `SHOULD` і `MAY` мають
нормативне значення.
Формули, eligibility та правила порівняння не можна змінювати без нового
`formula_version` і regression fixtures.

Google Sheets зберігає факти, а цей контракт визначає лише їхню
детерміновану проєкцію. Розрахована метрика ніколи не виправляє і не
дописує source fact.

## 2. Спільна модель результату

Кожен результат метрики MUST містити:

| Поле | Значення |
|---|---|
| `formula_id` | Стабільний ідентифікатор формули з цього документа |
| `formula_version` | `metrics-v1` |
| `snapshot_id` | Immutable source snapshot |
| `schema_version` | Source/canonical schema, використана для validation |
| `normalizer_version` | Versioned normalization semantics |
| `status` | Один зі статусів §11 |
| `value` | Canonical Decimal string, integer або `null` |
| `unit` | Явна одиниця або `count` |
| `parameters_json` | Canonical filters, inclusive date/time window, timezone та formula parameters |
| `comparison_cohort_id` | Стабільний cohort ID або `null`, якщо метрика не потребує cohort |
| `included_count` | Кількість contributing logical observations |
| `excluded_count` | Кількість in-scope observations, що не ввійшли |
| `coverage` | `included_count / applicable_count` або `null`, якщо denominator не визначений |
| `reason_codes` | Відсортований унікальний список кодів §12 |
| `evidence` | Lineage за §14 |

`null`, `0` і порожній набір мають різну семантику. Відсутню метрику MUST
NOT серіалізувати як нуль. Row position може бути trace locator, але MUST
NOT бути identity.

## 3. Спільна eligibility робочого підходу

Базово eligible logical working set:

1. належить accepted current revision нетомбстонованої завершеної сесії;
2. має source-owned `set_id` і валідний зв’язок із `session_id`;
3. має `status = completed`;
4. має роль `working` або `backoff`;
5. не є `warmup`, planned-but-skipped чи quarantined record;
6. для `laterality = unilateral_both` містить обидві виконані сторони.

Виконаний optional set є звичайним working set. Optional — поле
`prescribed_optional`, а не окрема фізіологічна роль. Source `set_id` уже
ідентифікує один logical set. Праву і ліву сторони система зберігає як
components `(set_id, component_side)` і MUST рахувати одним set; два
component rows не збільшують working-set count.

Окрема метрика MAY мати додаткові eligibility rules. Відхилене
спостереження залишається в lineage з reason code.

## 4. Сімейство volume

Слово `volume` без qualifier заборонене в API, SQLite views і report
evidence. V1 має чотири різні метрики.

### 4.1 Working-set count

`working_set_count_v1`:

```text
count(distinct eligible set_id)
```

- один bilateral set = `1`;
- один завершений `unilateral_both` set = `1`, а не `2`;
- repetition- і duration-based working sets однаково можуть дати `1`;
- warm-up і невиконаний optional set дають `0` contribution.

Це єдина volume-метрика, яку можна без конверсії агрегувати за вправами.
Вона описує виконану кількість підходів, а не однаковий фізіологічний
стимул.

### 4.2 Rep volume

`rep_volume_v1`:

```text
sum(movement_repetitions)
```

`movement_repetitions` — загальна кількість фактично виконаних dynamic
repetitions:

- для `bilateral` і `alternating_total` використовується `reps_total`;
- `10` повторень на кожен бік дають `20` movement repetitions;
- для `unilateral_both` використовується `reps_left + reps_right`;
- для `left_only`/`right_only` використовується відповідний component;
- duration-only set не дає rep contribution.

Rep volume можна показувати за session/exercise/window, але порівнювати як
performance trend SHOULD лише в однаковому exercise/program cohort. Він не
є мірою механічної роботи і не замінює load volume.

### 4.3 Load volume

`load_volume_v1` обчислюється лише всередині одного load-comparison cohort:

```text
set_load_volume = comparable_load_quantity * movement_repetitions
load_volume     = sum(set_load_volume)
```

`comparable_load_quantity` нормалізується з canonical source tuple
`load_value`, `load_unit`, `load_basis`, `implement_count`.
Для mass-based load результат має одиницю `kg·rep`. Canonical load:

- `total_external` уже означає повне зовнішнє навантаження;
- `per_implement` множиться на explicit `implement_count`;
- маса штанги MUST включати гриф;
- pounds конвертуються за exact factor `1 lb = 0.45359237 kg`;
- `machine_stack` у `kg`/`lb` дозволений лише для того самого
  `comparison_cohort_id` і не трактується як фактична сила на руків’ї;
- `machine_level` не конвертується в kg: усередині одного
  `comparison_cohort_id` він дає окрему метрику `machine_level·rep`;
- bodyweight-only, assisted, banded, невідомий load basis або load, де
  більше число не означає більший опір, не входять до цієї формули.

Load volume з різних cohort або unit families MUST NOT додаватися в один
scalar. Session із кількома cohort повертає map/list cohort results. Для
загального session summary використовуються working-set count і rep
volume, а не фальшива сума несумісних `kg·rep`/`machine_level·rep`.

### 4.4 Muscle-group volume

`muscle_group_set_volume_v1` має одиницю `set-equivalent`:

```text
sum(working_set_contribution * muscle_allocation_weight)
```

Для кожного eligible logical set `working_set_contribution = 1`. Вага
allocation:

- MUST походити з versioned program/taxonomy mapping;
- MUST бути Decimal у діапазоні `[0, 1]`;
- за відсутності explicit mapping дозволений лише deterministic fallback
  `primary_muscle_group_id = 1`, secondary muscles не домислюються;
- MUST зберігати `allocation_version` в evidence.

Один set може мати credit у кількох групах, тому сума всіх muscle-group
values може перевищувати загальний working-set count. Muscle-group
set-equivalents не можна перетворювати на load volume або порівнювати між
різними allocation versions без окремого перерахунку всього window.

## 5. Maximum comparable load

`maximum_comparable_load_v1` — максимальна canonical load quantity серед
eligible working sets **усередині одного comparison cohort та unit
family**:

```text
max(comparable_load_quantity)
```

Higher numeric load MUST означати higher external resistance. Відповідь за
вправою з кількома cohort є набором максимумів, не одним переможцем. Усі
`set_id`, що поділяють максимальне значення, входять до evidence.
`kg`/`lb` mass нормалізується до `kg`; `machine_level` залишається окремою
unit family й порівнюється лише в тому самому source cohort.

Навантаження не є comparable, якщо відрізняються
`exercise_family_id`, `exercise_variant_id`, source-owned
`comparison_cohort_id`, `equipment_id`, `setup_id`, load basis, implement
count, laterality semantics чи resistance direction. Source-owned cohort
ID MUST змінюватися при material зміні machine/equipment/setup. Зміна
тільки display unit після exact mass conversion не створює нового cohort.

Assistance values, bodyweight-only movements і невідомий machine/setup
можна показати як source facts, але вони отримують `not_applicable` або
`incomparable` для цієї метрики.

## 6. Epley e1RM v1

### 6.1 Формула

`epley_e1rm_v1`:

```text
e1RM_kg = load_kg * (1 + repetitions_for_effort / 30)
```

Canonical порядок Decimal-операцій:

```text
(load_kg * (30 + repetitions_for_effort)) / 30
```

Формула застосовується і при одному повторенні без special case.

### 6.2 Eligibility

Set eligible для e1RM лише якщо:

- пройшов спільну working-set eligibility;
- є dynamic repetition effort;
- `repetitions_for_effort` — integer від `1` до `12` включно;
- `load_kg > 0`, load basis однозначний і higher load means harder;
- `exercise_family_id`, `exercise_variant_id`, `equipment_id`, `setup_id`
  і `comparison_cohort_id` утворюють повний comparison cohort;
- `load_unit` є `kg` або `lb`; `machine_level` не є mass для Epley;
- load basis не є `added_to_bodyweight`, `assistance` або
  `bodyweight_only`.

Для `bilateral`/`alternating_total` set
`repetitions_for_effort = reps_total`. Для unilateral set використовуються
повторення **одного effort/side**, а не rep volume обох сторін. Якщо
сторони мають різні reps, estimates зберігаються окремо із side у
cohort/evidence. Duration-only, assisted, bodyweight-only, ambiguous-side
і `13+` repetition sets не отримують e1RM.

RIR не входить до Epley v1. Система MUST NOT додавати RIR до repetitions,
оцінювати «reps to failure» або коригувати формулу через target RIR.
Відсутній RIR сам по собі не робить otherwise-valid e1RM неeligible.
`pain_score` і `technique_score` залишаються context/evidence й не
змінюють Epley formula. Invalid/quarantined source record уже виключений
спільною eligibility; metric layer не вигадує technique threshold.
Пороги, що використовуються саме для progression qualification, належать
версійованому
[progression ruleset](../../config/progression-rules.yaml), а не формулі
e1RM.

Session/window e1RM progression — ordered series максимумів
`epley_e1rm_v1` у межах того самого cohort. e1RM між різними cohort,
формулами чи contract versions MUST NOT подаватися як одна progression
line.

## 7. RIR

Actual `RIR` — введена користувачем Decimal-оцінка кількості додаткових
технічно чистих повторень, можливих одразу після set. V1 приймає значення
`0..10` включно; `0` означає, що ще одного технічно чистого повторення не
залишалося. Unknown залишається `null`.

Target RIR є prescription range і зберігається окремо від actual RIR.
Actual value:

- не виводиться з reps, load, velocity чи текстової нотатки;
- не замінюється target midpoint;
- не переноситься з іншого set.

`rir_summary_v1` для eligible working sets повертає:

- `reported_count`, `applicable_count` і coverage;
- arithmetic mean, minimum, maximum і median reported values;
- кількість `below_target`, `within_target`, `above_target`, якщо для set
  відома versioned prescription range.

Mean і median не отримують `0` за missing values. Target-adherence дані з
різних prescription versions MUST зберігати окремі cohort або явно
перераховуватися за pinned version.

## 8. Rest

Canonical source field `rest_seconds` MUST мати basis
`same_exercise_elapsed`: кількість секунд від завершення попереднього
`set_id` тієї самої вправи до початку поточного. Для paired sets цей
інтервал включає paired exercise і всі паузи. Саме він відповідає
фактичному відновленню перед наступним effort.

Нееквівалентні rest concepts MUST мати різну семантику; лише перший рядок
має canonical source field у V1:

| `rest_basis` | Семантика |
|---|---|
| `same_exercise_elapsed` | Comparable v1 performance-rest interval |
| `post_set_pause` | Лише нерухома пауза після set; не еквівалентна рядку вище |
| `between_sides` | Пауза всередині одного unilateral logical set |
| `prescribed` | Target, а не observed rest |
| `unknown` | Невизначена семантика |

Перший set вправи має `rest_seconds = null`, бо не має
`same_exercise_elapsed` у межах session. Якщо source capture означає лише
нерухому паузу після попереднього set, її не можна записувати в
`rest_seconds`: до розширення schema вона залишається окремим unsupported
fact із `REST_BASIS_UNSUPPORTED`.
`rest_summary_v1` обчислює count, mean, median, minimum і maximum observed
seconds лише для однакового `rest_basis`, exercise/block format і
comparison cohort. Prescribed rest MUST NOT підміняти observed rest.
Майбутнє schema field для `post_set_pause` можна звітувати окремо, але не
змішувати з `same_exercise_elapsed`.

## 9. Recovery context

V1 recovery context є session-level facts:

- `sleep_hours`;
- `energy_score`;
- `stress_score`;
- `soreness_score`;
- `performance_score`.

Кожне поле зберігає source scale/version. Current 1–5 subjective scales не
нормалізуються до відсотків і не змішуються між собою. Recovery value
приєднується до session metric один раз; його MUST NOT вагувати кількістю
sets. Missing context не виключає performance metric, але робить відповідну
recovery comparison `partial` або `missing`.

`recovery_context_v1` повертає chronological aligned rows
`session metric ↔ available recovery facts`, coverage для кожного поля і
descriptive summaries в межах однакової scale version. V1 не заявляє
причинності й не генерує медичних висновків. Correlation, якщо буде додана,
потребує окремого versioned metric; вільний текст на кшталт «сон спричинив
падіння результату» не є результатом V1.

## 10. Comparison cohorts і descriptive trend

### 10.1 Cohort identity

Source-owned `comparison_cohort_id` є stable canonical slug, семантика
якого MUST змінюватися разом із material equipment/setup cohort. Локальний
`comparison_cohort_fingerprint` — SHA-256 canonical JSON tuple з:

- cohort schema version;
- `exercise_family_id`, `exercise_variant_id` і source-owned
  `comparison_cohort_id`;
- `equipment_id` і `setup_id`;
- load basis, implement count і resistance direction;
- laterality/side semantics;
- performance modality (`repetition` або `duration`);
- для rest — rest basis і block format;
- для target-relative metrics — `program_item_id` та prescription version;
- для muscle volume — allocation version;
- для recovery — field scale version.

Значення `unknown`, яке впливає на comparable load або effort, не дозволяє
«припустити» cohort. Такий результат має `incomparable`. Зміна
`program_version_id` сама по собі не розриває raw load/e1RM cohort, якщо
material dimensions незмінні; вона розриває target-adherence cohort.

### 10.2 Trend window

Ordered series можна показувати з одного observation. Deterministic
`descriptive_trend_v1` потребує від `6` до `8` останніх comparable
session observations. Спочатку requested metric агрегується рівно один раз
для кожного distinct completed `session_id` у cohort; окремі sets або side
components не є самостійними trend occurrences.

1. взяти останні `min(total, 8)` session observations за `session_date`,
   `session_id`;
2. якщо їх менше `6`, повернути `insufficient_data`;
3. поділити chronologically: earlier half отримує `floor(n/2)`, recent half
   — решту;
4. повернути `median_recent - median_earlier`;
5. relative delta дозволена лише для ratio-meaningful metric і ненульової
   earlier median.

Це descriptive change, не прогноз і не рекомендація. Будь-яке об’єднання
cohort або зміна window MUST бути явним report parameter.

## 11. Статуси

| Status | Нормативне значення |
|---|---|
| `ok` | Метрика обчислена з усіх applicable in-scope observations |
| `partial` | Метрика обчислена, але частина applicable observations виключена або має missing inputs |
| `missing` | Метрика застосовна, але немає жодного потрібного source value |
| `incomparable` | Валідні values існують, але cohort/unit/basis не дозволяє requested aggregation або delta |
| `insufficient_data` | Comparable values є, але їх менше deterministic threshold |
| `not_applicable` | Метрика семантично не стосується modality, наприклад e1RM для side plank |
| `invalid` | Required source record не пройшов schema/quality validation і перебуває в quarantine |

Для одного requested scalar:

1. `not_applicable` використовується, якщо метрика не має сенсу для всього
   scope;
2. fatal snapshot/schema failure дає `invalid`;
3. спроба злити кілька cohort/unit bases дає `incomparable`;
4. відсутність будь-якого applicable source value дає `missing`;
5. валідні comparable values нижче threshold дають `insufficient_data`;
6. хоча б один обчислений contribution разом із відхиленими applicable
   rows дає `partial`;
7. повне покриття дає `ok`.

Warm-up/skipped records, для яких requested metric за визначенням не
застосовна, не знижують coverage. Детальні per-observation statuses і
reason codes MUST зберігатися, навіть якщо summary має один статус.

## 12. Exclusion reason codes

Коди є стабільним API. Текстове пояснення можна локалізувати, код — ні.

| Code | Причина |
|---|---|
| `SESSION_NOT_COMPLETE` | Сесія не завершена |
| `SESSION_TOMBSTONED` | Current source revision видалена |
| `SOURCE_RECORD_QUARANTINED` | Record не пройшов validation |
| `SUPERSEDED_REVISION` | Існує новіша revision того самого stable ID |
| `SET_NOT_COMPLETED` | Planned/skipped set |
| `SET_ROLE_WARMUP` | Warm-up не є working set |
| `SET_ROLE_UNSUPPORTED` | Role не належить до working/backoff |
| `UNILATERAL_COMPONENT_INCOMPLETE` | Немає однієї потрібної сторони |
| `SIDE_BASIS_AMBIGUOUS` | Total/per-side semantics невідомі |
| `REPS_MISSING` | Немає reps |
| `REPS_INVALID` | Reps не пройшли validation |
| `DURATION_ONLY` | Set не має repetitions |
| `LOAD_MISSING` | Немає load |
| `LOAD_UNIT_UNKNOWN` | Unit не конвертується |
| `LOAD_UNIT_NOT_MASS` | Unit не є mass і не придатний для Epley |
| `LOAD_BASIS_UNKNOWN` | Total/per-implement semantics невідомі |
| `LOAD_BASIS_UNSUPPORTED_FOR_E1RM` | Load basis не є Epley-compatible external mass |
| `IMPLEMENT_COUNT_MISSING` | Не можна отримати total load |
| `RESISTANCE_DIRECTION_UNSUPPORTED` | Більше число не означає більше навантаження |
| `BODYWEIGHT_ONLY` | Немає comparable external load |
| `ASSISTED_LOAD` | Assistance не є maximum external load/e1RM basis |
| `COHORT_DIMENSION_MISSING` | Немає material variant/equipment/setup dimension |
| `COHORT_MISMATCH` | Requested scalar змішує різні cohort |
| `E1RM_REPS_OUT_OF_RANGE` | Reps поза inclusive range `1..12` |
| `RIR_MISSING` | Actual RIR не записаний |
| `RIR_OUT_OF_RANGE` | RIR поза `0..10` |
| `TARGET_RIR_MISSING` | Немає prescription для adherence |
| `REST_NOT_OBSERVED` | Немає measured interval |
| `REST_FIRST_SET` | Немає попереднього same-exercise set |
| `REST_BASIS_UNSUPPORTED` | Rest facts мають іншу семантику |
| `MUSCLE_MAPPING_MISSING` | Немає allocation і primary fallback |
| `ALLOCATION_VERSION_MISMATCH` | Змішані mapping versions |
| `RECOVERY_VALUE_MISSING` | Немає конкретного recovery field |
| `RECOVERY_SCALE_MISMATCH` | Змішані scale versions |
| `OBSERVATION_COUNT_BELOW_THRESHOLD` | Недостатньо comparable observations |

Нове значення додається backward-compatibly; зміна семантики наявного коду
вимагає нового contract version.

## 13. Decimal, одиниці й округлення

- Numeric source strings MUST парситися напряму в `Decimal`; binary float
  заборонений на validation/calculation/evidence boundary.
- Arithmetic context: precision `28`, rounding `ROUND_HALF_EVEN`.
- Canonical mass-load unit — `kg`; `machine_level` лишається окремою unit
  family. Original value/unit зберігаються в lineage.
- Integer counts, reps і observed whole seconds залишаються integers.
- Intermediate results не округлюються, крім дії Decimal context.
- Median: після ascending sort odd count бере central value, even count —
  arithmetic mean двох central values у тому самому Decimal context.
- Canonical JSON Decimal — plain base-10 string без exponent і зайвих
  trailing zeros; `-0` серіалізується як `0`.
- Display rounding не змінює evidence value:
  - load, e1RM і `kg·rep`: `0.1`;
  - means, medians, set-equivalents і RIR: `0.1`;
  - percentages: `0.1%`;
  - counts, reps і seconds: whole number.

Tests MUST містити unit conversion, repeating Epley division, `.05` ties,
unilateral sets і mixed-cohort rejection.

## 14. Evidence lineage

Кожна metric/conclusion MUST бути відтворювана без live Sheet. Evidence
містить щонайменше:

- `snapshot_id` і snapshot content SHA-256;
- schema, normalization і metric contract versions;
- code revision і canonical hashes relevant config/rules;
- source tab, stable entity ID, source revision і source-row fingerprint
  кожного included та excluded observation;
- exact `source_payload_sha256` кожної source entity revision;
- normalized input values, original units і conversion factor;
- scope/window/timezone, cohort tuple та cohort ID;
- exact formula ID, parameters, canonical unrounded result;
- exclusion status/reason code для кожного rejected observation;
- deterministic evidence-record SHA-256.

Source row number MAY бути diagnostic locator, але не доказом identity.
Evidence не містить OAuth material, raw authorization locator чи
непотрібний free text.

## 15. Substantive report hash

RPRT-03 перевіряється полем `substantive_report_sha256`. До substantive
payload MUST входити:

- report schema/version;
- snapshot content fingerprint;
- normalized dataset fingerprint;
- metric/config/rules/code versions;
- canonical report parameters;
- усі metric values, statuses, cohort IDs, coverage і evidence hashes;
- deterministic conclusions та exclusion summaries.

Не входять: `generated_at`, duration, host/user name, absolute paths,
SQLite byte layout, log ordering, terminal color, pagination і cosmetic
Markdown/HTML formatting.

Canonicalization algorithm:

1. Unicode strings привести до NFC; timestamps/dates — ISO 8601;
2. Decimal серіалізувати за §13, missing — explicit JSON `null`;
3. object keys сортувати lexicographically;
4. unordered ID/reason/evidence collections сортувати за stable ID/hash;
5. серіалізувати UTF-8 JSON без insignificant whitespace;
6. обчислити SHA-256 bytes і записати lowercase hexadecimal digest.

Ті самі snapshot, normalized facts, parameters, config і versions MUST
дати той самий substantive hash. Зміна лише часу генерації або renderer
MUST NOT його змінювати.

## 16. Межа deterministic analytics та AI

Metric engine і substantive report є повністю deterministic та не
викликають LLM. Missing values не заповнюються AI.

Стандартна double progression — versioned deterministic program rule:
одне виконання може кваліфікувати стандартний крок лише коли всі prescribed
working sets досягли верхньої межі reps при target RIR, stable technique і
без зростання pain. Сам факт qualification не дозволяє змінювати source
records. Перший milestone показує deterministic outcome окремо від AI
recommendation.

У ruleset `1.1.0` stable technique означає `technique_score >= 4`.
Pain gate проходить, коли максимальний `pain_score` поточної session дорівнює
нулю або не перевищує попередню comparable session; без попереднього
comparator ненульовий pain не є pass. Відсутнє значення technique або pain
завжди disqualifies. Нормативним машинозчитуваним джерелом цих умов є
[progression-rules.yaml](../../config/progression-rules.yaml).

Зміна progression rule, sets, exercise або програми є analytical/AI
recommendation і потребує щонайменше трьох comparable exercise
performances; trend claim використовує поріг §10. Така рекомендація:

- не може змінити формулу або об’єднати incomparable cohort;
- не може приховати missing/partial evidence;
- має окремий recommendation ID, evidence, confidence і review date;
- не є медичним діагнозом;
- зберігається окремо від deterministic substantive payload.

Будь-який non-deterministic AI narrative є clearly labelled recommendation
або non-substantive appendix. Він не може змінювати metric values/statuses,
автоматично змінювати program prescription або використовуватися для
перевірки reproducibility hash.
