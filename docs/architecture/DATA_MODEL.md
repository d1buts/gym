# Нормативний контракт даних

**Version:** `1.0.0`

**Status:** Accepted design contract

**Applies to:** Google Sheets source, raw snapshots, normalization, SQLite mirror,
metric evidence and future controlled write-back

Машинозчитуваним джерелом цього контракту є
[`config/schema.yaml`](../../config/schema.yaml). Цей документ пояснює його
семантику. Реалізація не повинна витягувати схему з Markdown-таблиць.

Пов’язані контракти:

- [ADR-001: межі джерел правди](ADR-001-authority-boundaries.md);
- [ADR-002: Python і SQLite](ADR-002-python-sqlite-v1.md);
- [протокол синхронізації](SYNC_PROTOCOL.md);
- [контракт метрик](METRICS.md);
- [безпека і резервне відновлення](SECURITY_AND_BACKUP.md);
- [виконувані правила прогресії](../../config/progression-rules.yaml);
- [вимоги v1](../../.planning/REQUIREMENTS.md).

## 1. Нормативна мова і пріоритет

Слова **МАЄ**, **ПОВИНЕН**, **НЕ МОЖНА**, **СЛІД** і **МОЖЕ** мають
нормативне значення.

У разі розбіжності діє такий пріоритет:

1. accepted ADR;
2. `config/schema.yaml` для назв, типів, nullable-правил і діапазонів;
3. цей документ для семантики сутностей і полів;
4. `SYNC_PROTOCOL.md` для capture, reconciliation і promotion;
5. `METRICS.md` для eligibility та формул;
6. overview і початкові Markdown-описи програми.

Зміна поля, enum, одиниці, identity або умовної валідації потребує нової
`schema_version`. Виправлення лише пояснювального тексту без зміни поведінки
може залишити поточну версію.

## 2. Межі авторитетності

| Клас даних | Власник | Роль локальної системи |
|---|---|---|
| Виконані сесії | Google Sheets, `Сесії` | Незмінно захопити, перевірити, версіонувати і дзеркалити |
| Виконані підходи | Google Sheets, `Підходи` | Незмінно захопити, перевірити, версіонувати і дзеркалити |
| Operational prescriptions | Google Sheets, `Програма` | Перевірити версію та зберегти історичний зв’язок |
| Журнал рекомендацій | Google Sheets, `Рекомендації` | У v1 лише читати; у майбутньому додавати через окремий allowlist |
| Схема, нормалізація, формули, executable rules | Git | Версіонувати код і декларативні контракти |
| Raw snapshot, normalized data, SQLite, reports | Локальна система | Rebuildable projection, не незалежне джерело фактів |

Markdown-файли програми є bootstrap specification і поясненням. Майбутній
`config/program.yaml`, якщо його буде створено, є лише mirror/validator
artifact. Він **НЕ МОЖЕ** непомітно перезаписувати історичну вкладку
`Програма`.

### 2.1 Три класи полів

Кожна колонка в `schema.yaml` має рівно один `data_class`.

- `source_fact` — значення, яким володіє source writer. Raw snapshot зберігає
  точний source value; нормалізатор не «покращує» його заднім числом.
- `sheet_calculated` — кеш для зручного показу в таблиці. Він може бути
  перевірений, але **НЕ Є** доказом для локальної метрики і не перемагає
  source facts.
- `local_derived` — нормалізований компонент, метрика, cohort result чи інший
  локальний результат. Він існує лише з повним lineage і версіями алгоритмів.

У `Сесіях` і `Підходах` колонки з суфіксом `_sheet` належать до
`sheet_calculated`. Локальна аналітика завжди рахує значення повторно за
`METRICS.md`.

## 3. Версії

Контракт використовує чотири незалежні осі версій.

| Поле/metadata | Поточне значення | Що воно версіонує |
|---|---|---|
| `schema_version` | `1.0.0` | Заголовки, типи, nullable та cross-field правила |
| `program_version_id` | source-owned `pver_<uuid4>` | Конкретну operational version програми |
| `normalizer_version` | `normalizer-v1` | Перетворення source row у normalized model |
| `formula_version` | `metrics-v1` | Eligibility, формули й одиниці локальних метрик |

Вкладка `Програма` додатково має людиночитаний label `program_version` у
форматі `program-vMAJOR.MINOR.PATCH`. Foreign key завжди є
`program_version_id`, а не label.

`sheet_formula_version` версіонує лише формули Google Sheets. Збіг його
назви з локальним `metrics-v1` не перетворює Sheet cache на authoritative
metric.

Кожен snapshot також має opaque source version/ETag, якщо connector його
надає, і обов’язковий content SHA-256. Якщо API не надає надійної revision,
content hash є остаточним fingerprint capture.

## 4. Identity: лише source-owned IDs

Чотири row identity створює writer до першого запису і зберігає у source:

| Сутність | Поле | Формат |
|---|---|---|
| Елемент програми | `program_item_id` | `prg_<uuid4>` |
| Сесія | `session_id` | `ses_<uuid4>` |
| Логічний підхід | `set_id` | `set_<uuid4>` |
| Рекомендація | `recommendation_id` | `rec_<uuid4>` |

`program_version_id` також є source-owned `pver_<uuid4>`. Це identity
group entity `program_version`; кожен `program_item` row належить рівно
одній такій групі.

Правила identity:

1. ID незмінний протягом життя логічної сутності.
2. Номер рядка, дата, назва вправи, порядковий номер підходу або hash payload
   **НЕ МОЖУТЬ** бути primary ID.
3. Нормалізатор **НЕ МОЖЕ** генерувати fallback ID з row position або
   content.
4. Рядок без валідного ID потрапляє в quarantine з
   `STABLE_ID_MISSING_OR_INVALID`.
5. Legacy backfill є окремою source migration: ID генерують один раз,
   записують назад у Sheet з явним дозволом і тільки після цього імпортують.
6. Однаковий ID у двох рядках не означає «можливо той самий запис». Якщо
   payload одного `source_revision` різний, весь snapshot неоднозначний.

`set_id` уже є identity **логічного підходу**. Окремий `logical_set_id` не
потрібний: left/right components не є окремими source rows.

## 5. Ревізії, виправлення і provenance

Кожна source entity має:

- `source_revision`, починаючи з `1`;
- `created_at` і `updated_at` там, де source writer змінює row;
- entity-specific status замість фізичного видалення;
- stable ID, який не змінюється під час виправлення.

При зміні source fact writer збільшує `source_revision`. Локальна система
зберігає версію незмінно під ключем:

```text
(entity_id, source_revision, source_payload_sha256)
```

Однаковий `(entity_id, source_revision)` з іншим payload є `fatal`, бо
історію неможливо однозначно відтворити. Revision нижча за вже committed
revision є `error` і потребує явної процедури rollback/recovery.

Для кожної локальної версії обов’язкові:

- `snapshot_id`;
- `source_tab`;
- `source_row_number` лише як locator для діагностики;
- `source_payload_sha256`;
- `schema_version`;
- `observed_at`.

Якщо сутність зникає з **повного coherent snapshot**, sync створює локальну
tombstone revision. Відсутність не перетворюється на вигаданий source fact.
Partial capture ніколи не створює tombstones. Деталі визначає
`SYNC_PROTOCOL.md`.

### 5.1 Виправлення програми

Після того як `program_version_id` використано сесією, prescription не
редагують заднім числом:

- typo або metadata correction, що не змінює prescription semantics, може
  збільшити `source_revision`;
- зміна вправи, кількості підходів, rep/duration range, RIR, rest,
  optionality або progression semantics створює новий
  `program_version_id`, новий `program_version` і нові `program_item_id`;
- попередня version отримує `program_version_status=retired`, але її item
  rows залишаються доступними для історії;
- у workbook рівно одна version має `program_version_status=active`;
- session може посилатися лише на `active` або історичну `retired` version.

## 6. Чотири canonical workout types

Source Sheet приймає лише точні українські labels:

| Source label | Внутрішній English alias |
|---|---|
| `Верх — сила` | `upper_strength` |
| `Низ — сила` | `lower_strength` |
| `Верх — гіпертрофія` | `upper_hypertrophy` |
| `Низ — гіпертрофія` | `lower_hypertrophy` |

У label використовується em dash `—` з пробілами. English aliases існують
лише після нормалізації. Sheet row з alias, коротким hyphen або іншим
перекладом отримує `WORKOUT_TYPE_INVALID`; система не виправляє його
мовчки.

## 7. Source tabs і колонки

Source workbook має рівно чотири обов’язкові вкладки:

```text
Програма
Сесії
Підходи
Рекомендації
```

Exact український header, internal field, type, nullable, enum, range і
`data_class` кожної колонки визначені у
`sheet_tabs` файла [`schema.yaml`](../../config/schema.yaml). Header row —
перший. Переміщення або сортування data rows не змінює identity.

Нижче наведено вичерпні internal fields. Цей список потрібний для людського
review; runtime використовує YAML.

### 7.1 `Програма`

`Програма` містить operational prescriptions. Primary key —
`program_item_id`.

Source facts:

```text
program_item_id, schema_version, program_version_id, program_version,
program_version_status, source_revision, published_at, status, workout_type, block_code,
exercise_order, exercise_family_id, exercise_variant_id,
comparison_cohort_id, equipment_id, setup_id, exercise_name,
primary_muscle_group_id, set_role, target_sets, prescribed_optional,
measurement_kind, laterality, target_reps_min, target_reps_max,
target_duration_seconds_min, target_duration_seconds_max, target_rir_min,
target_rir_max, rest_seconds_min, rest_seconds_max, load_increment_value,
load_increment_unit, load_increment_basis, expected_implement_count,
priority, technical_notes, definition_sha256
```

`definition_sha256` є hash canonical prescription payload, а не primary ID.
Він виявляє drift, але не замінює `program_item_id` або
`program_version_id`.

Rows групуються за `program_version_id` у canonical entity
`program_version`. Для всіх rows групи мають збігатися `schema_version`,
`program_version`, `program_version_status` і `published_at`. Розбіжність
карантинує всю version bundle.

`program_version_status` має лише `active` або `retired`. Поле `status`
на тому самому row окремо описує item як `active` або `inactive`.

### 7.2 `Сесії`

Один row — одна workout session. Primary key — `session_id`.

Source facts:

```text
session_id, schema_version, source_revision, created_at, updated_at, status,
program_version_id, session_date, workout_type, started_at, completed_at,
duration_minutes, expected_set_count, body_mass_value, body_mass_unit,
sleep_hours, energy_score, stress_score, soreness_score, performance_score,
notes, void_reason
```

Sheet-calculated display caches:

```text
observed_set_count_sheet, working_set_count_sheet, volume_sheet,
average_rir_sheet, average_rest_seconds_sheet, risk_flags_sheet,
sheet_formula_version
```

`status`:

- `writing` — capture ще не завершено; raw row зберігається, analytics його
  не використовує;
- `complete` — `completed_at` заповнено, а `expected_set_count` дорівнює
  кількості non-void set rows;
- `void` — row анульовано, `void_reason` обов’язковий.

Під час майбутнього atomic capture session спочатку є `writing`, а
`complete` стає лише після перевірки всіх `set_id`.

### 7.3 `Підходи`

Один row — один логічний set, навіть для руху «на бік». Primary key —
`set_id`; foreign keys — `session_id`, `program_version_id` і, зазвичай,
`program_item_id`.

Source facts:

```text
set_id, session_id, program_item_id, schema_version, program_version_id,
source_revision, created_at, updated_at, status, set_number,
performed_order, set_role, prescribed_optional, unplanned_reason,
exercise_family_id, exercise_variant_id, comparison_cohort_id, equipment_id, setup_id,
exercise_name, primary_muscle_group_id, measurement_kind, laterality,
load_value, load_unit, load_basis, implement_count, reps_total, reps_left,
reps_right, duration_seconds_total, duration_seconds_left,
duration_seconds_right, rir, rest_seconds, pain_score, pain_location,
technique_score, skip_reason, void_reason, notes
```

Sheet-calculated display caches:

```text
session_date_sheet, workout_type_sheet, volume_sheet, volume_unit_sheet,
e1rm_sheet, e1rm_unit_sheet, sheet_formula_version
```

Дата і workout type в set row є формулами lookup. Authoritative значення
беруться через `session_id`, тому виправлення сесії не створює суперечливу
другу копію факту.

`set_role` має `warmup`, `working` або `backoff`.
`prescribed_optional` — окрема ознака prescription; optional set не є новою
фізіологічною роллю. Виконаний optional working set залишається `working`.

`status`:

- `completed` — усі обов’язкові компоненти виконано;
- `partial` — виконано лише частину, фактичні компоненти збережено;
- `skipped` — performance components порожні, `skip_reason` обов’язковий;
- `void` — row анульовано, `void_reason` обов’язковий.

Для working/backoff set має бути заповнено рівно одне:
`program_item_id` для prescribed set або `unplanned_reason` для справді
позапланового. Нормалізатор не підбирає program item лише за назвою вправи.

### 7.4 `Рекомендації`

Один row — одна версійована пропозиція або decision record. Primary key —
`recommendation_id`.

Source facts:

```text
recommendation_id, schema_version, program_version_id, source_revision,
created_at, updated_at, analysis_date, scope, workout_type,
exercise_family_id, exercise_variant_id, comparison_cohort_id,
recommendation_type, signal_code, signal_summary, evidence_summary,
evidence_refs_json, evidence_sha256, recommendation_text, confidence,
generated_by, generator_id, generator_version, rule_id, rule_version,
snapshot_id, normalizer_version, formula_version, status, decision_at,
decision_notes, review_due_date, reviewed_at, outcome, outcome_notes,
supersedes_recommendation_id, void_reason
```

`evidence_refs_json` є JSON array структурованих посилань
`{snapshot_id, entity_type, entity_id}`. Вільний текст
`evidence_summary` не замінює machine references.

Для `rules_engine` або `llm` обов’язкові `snapshot_id`,
`normalizer_version` і `formula_version`; для rules engine також
`rule_id` і `rule_version`. `generated_by=human` усе одно потребує
`generator_id` і `generator_version`, наприклад version інструкції ручного
review.

`status` описує lifecycle:
`proposed → accepted|rejected|expired|superseded`; `void` потребує причини.
`outcome` не заповнюють до реальної перевірки й не підмінюють status.

## 8. Сімейство вправи, варіант і comparison cohort

Система не використовує неоднозначне поле `exercise_id`.

- `exercise_family_id` групує споріднену механіку для навігації, наприклад
  сімейство Romanian deadlift.
- `exercise_variant_id` визначає конкретну execution variant: barbell і
  dumbbell RDL є різними variants.
- `equipment_id` визначає конкретний тип/екземпляр обладнання, важливий для
  опору.
- `setup_id` фіксує material setup: attachment, grip/stance class,
  seat/lever configuration або іншу versioned конфігурацію.
- `comparison_cohort_id` означає, що values справді можна порівнювати за
  визначеною метрикою.

Comparison cohort щонайменше враховує:

```text
exercise_variant_id
equipment_id
setup_id
load_basis
implement_count
laterality
measurement_kind
resistance semantics
```

Однакове `exercise_family_id` не дозволяє порівнювати e1RM чи load.
Наприклад, barbell RDL, dumbbell RDL і machine hinge можуть бути одним
family, але різними variants/cohorts.

Set row зберігає фактично виконані variant/equipment/setup/cohort, а не
сліпо копіює current program. Якщо вони відрізняються від linked
`program_item_id`, це має бути явне відхилення, а не silent normalization.

## 9. Навантаження

Навантаження є чотирикомпонентним значенням:

```text
load_value + load_unit + load_basis + implement_count
```

### 9.1 Одиниці

`load_unit`:

- `kg`;
- `lb`;
- `machine_level` — номер/рівень без твердження, що це маса.

Canonical локальна маса використовує Decimal і exact conversion
`1 lb = 0.45359237 kg`. `machine_level` не конвертується у kg.

### 9.2 База

| `load_basis` | Семантика |
|---|---|
| `total_external` | `load_value` уже є повним зовнішнім навантаженням, для штанги разом із грифом |
| `per_implement` | Значення для одного снаряда; `implement_count` обов’язковий |
| `machine_stack` | Показ шкали/стека конкретної машини; порівняння лише в одному equipment/setup cohort |
| `added_to_bodyweight` | Лише зовнішня вага, додана до маси тіла |
| `assistance` | Величина допомоги; більше число не означає важчий результат |
| `bodyweight_only` | Зовнішнього load немає; value, unit і implement count мають бути `null` |

Нуль і `null` не взаємозамінні. Невідоме навантаження є `null`; значення
`0` дозволене лише коли воно справді виміряне і семантично допустиме.

Для `per_implement` два dumbbells по 30 lb записуються як:

```yaml
load_value: 30
load_unit: lb
load_basis: per_implement
implement_count: 2
```

Запис `30×10` без unit і basis є недостатнім для load metric.

## 10. Повторення, час і сторонність

`measurement_kind`:

- `repetitions`;
- `duration`;
- `repetitions_and_duration`.

`laterality` визначає дозволені components.

| `laterality` | Source components | Logical set credit |
|---|---|---:|
| `bilateral` | `*_total` | 1 |
| `alternating_total` | `*_total`, значення вже сумарне для чергування | 1 |
| `unilateral_both` | окремі `*_left` і `*_right` | 1 |
| `left_only` | лише `*_left` | 1 |
| `right_only` | лише `*_right` | 1 |

`*` означає `reps` або `duration_seconds`. Для `unilateral_both` completed
set потребує обидві сторони; нерівні значення зберігаються окремо.

Приклади з чинної програми:

- Bulgarian split squat `10 на ногу`:
  `laterality=unilateral_both`, `reps_left=10`, `reps_right=10`;
- side plank `35 с на бік`:
  `laterality=unilateral_both`, `duration_seconds_left=35`,
  `duration_seconds_right=35`;
- bilateral bench press `6`:
  `laterality=bilateral`, `reps_total=6`.

Праву і ліву сторони Bulgarian split squat програма рахує одним set. Тому
обидві сторони мають один `set_id`, а нормалізована child model
`set_component` має composite key `(set_id, component_side)`.

`alternating_total=10` означає десять рухів **разом**, а не десять на кожен
бік. Якщо source каже «10 на бік», потрібно використати
`unilateral_both`, а не вгадувати basis.

## 11. Nullable і діапазони

Порожня Sheet cell нормалізується в `null` до type coercion. Whitespace
навколо значення обрізається. `0`, `false` і текст `"0"` не стають `null`.
Placeholder values `N/A`, `unknown`, `невідомо` у typed field не є null і
не проходять валідацію; пояснення можна залишити в `notes`.

Система **НЕ МОЖЕ**:

- підставляти `0` для невідомого RIR, rest, pain або load;
- копіювати target reps як фактичні reps;
- обчислювати відсутню сторону з наявної;
- домислювати kg або lb;
- виводити workout type чи program item з вільного тексту;
- трактувати Sheet formula cache як source fact.

Ключові межі:

| Поле | Діапазон |
|---|---|
| RIR | Decimal `[0, 10]` |
| Pain | Integer `[0, 10]`; при `>0` потрібна location |
| Technique | Integer `[1, 5]` |
| Energy/stress/soreness/performance | Integer `[1, 5]` |
| Sleep | Decimal `[0, 24]` hours |
| Session duration | Decimal `(0, 360]` minutes |
| Rest | Integer `[0, 3600]` seconds |
| Repetitions | Integer `[1, 1000]` на component |
| Timed component | Decimal `(0, 86400]` seconds |
| Confidence | Decimal `[0, 1]` |
| `source_revision` | Integer `>=1` |

Усі поля мають explicit `nullable` у YAML. Відсутність ключа `nullable`
не дозволяється при розширенні контракту.

## 12. Referential і cross-field invariants

Перед acceptance нормалізатор перевіряє щонайменше:

1. кожен `set.session_id` посилається на session;
2. `set.program_version_id == session.program_version_id`;
3. `program_item_id`, якщо він є, належить тому самому
   `program_version_id`;
4. `complete` session має `completed_at` і рівно `expected_set_count`
   non-void sets;
5. program min не перевищує max для reps, duration, RIR і rest;
6. load fields утворюють дозволену комбінацію;
7. set components відповідають `measurement_kind`, `laterality` і `status`;
8. skipped/void rows мають причину;
9. рекомендація має references і generator provenance відповідно до author;
10. усі source timestamps мають RFC 3339 offset, а source dates —
    `YYYY-MM-DD`.

Complete session з orphan/missing set не може частково потрапити в
аналітику. Session group карантинується як цілісна referential unit.

## 13. Local-derived models

### 13.1 `source_record_version`

Зберігає exact provenance source revision. `source_row_number` є лише
locator; primary identity ним ніколи не будується.

### 13.2 `set_component`

Нормалізує wide Sheet columns до:

```text
(set_id, component_side, reps, duration_seconds)
```

`component_side` має `total`, `left` або `right`. Усі components одного
`set_id` разом дають рівно один logical-set credit.

### 13.3 `normalized_record`

Кожен normalized record містить:

```text
snapshot_id
source_payload_sha256
schema_version
normalizer_version
```

### 13.4 `metric_result`

Кожна метрика додатково містить:

```text
formula_version
formula_id
parameters_json
contributing_entity_ids
excluded_entity_ids_with_reason
```

Результат без цієї provenance envelope не можна показувати як
відтворюваний висновок.

## 14. Severity і наслідки валідації

| Severity | Що означає | Наслідок |
|---|---|---|
| `fatal` | Snapshot структурно або ідентифікаційно неоднозначний | Raw capture зберігається; mirror head не рухається; весь snapshot відхиляється |
| `error` | Row або referential entity group не відповідає контракту | Запис/група йде в quarantine; інші дані можна promote лише за збереженої referential completeness |
| `warning` | Значення прийнятне, але потребує уваги | Запис приймається з diagnostic |
| `info` | Очікувана неповнота або run metadata | Запис приймається; analytics може виключити його за eligibility |

Основні stable codes:

- `TAB_MISSING`;
- `REQUIRED_HEADER_MISSING`;
- `UNKNOWN_HEADER`;
- `SCHEMA_VERSION_UNSUPPORTED`;
- `STABLE_ID_MISSING_OR_INVALID`;
- `DUPLICATE_ID_CONFLICT`;
- `DUPLICATE_ID_REDUNDANT`;
- `REVISION_REGRESSION`;
- `WORKOUT_TYPE_INVALID`;
- `PROGRAM_VERSION_UNKNOWN`;
- `FOREIGN_KEY_MISSING`;
- `SESSION_NOT_COMPLETE`;
- `SESSION_SET_COUNT_MISMATCH`;
- `CONDITIONAL_FIELD_INVALID`;
- `VALUE_OUT_OF_RANGE`;
- `SHEET_FORMULA_VALUE_INVALID`;
- `OPTIONAL_VALUE_MISSING`;
- `ROW_POSITION_USED_AS_IDENTITY`.

Diagnostic має містити code, severity, tab, source row locator, internal
field і redacted explanation. Він не повинен друкувати notes, health
context або raw row у звичайний log.

## 15. Schema evolution

### 15.1 Сумісність

- Patch: пояснення або validator bug fix без зміни accepted data.
- Minor: additive nullable field або enum extension, яку старий reader може
  безпечно ігнорувати лише за документованим правилом.
- Major: rename/removal, зміна identity, unit, nullable, range, enum
  semantics або formula eligibility.

Importer має explicit allowlist `versions.schema.accepted`; «прочитаємо
будь-яку майбутню версію» заборонено.

### 15.2 Міграція поточної Sheet

До першого production pull потрібно:

1. створити exact headers із `schema.yaml`;
2. source-side згенерувати stable IDs для всіх чотирьох tabs;
3. створити `program_version_id` і versioned program rows;
4. прив’язати sessions і sets до фактичної version;
5. розділити ambiguous `weight` на value/unit/basis/count;
6. розкласти unilateral/timed values у правильні components;
7. позначити formula columns і `sheet_formula_version`;
8. виставити `source_revision=1` після ручного review;
9. виконати preflight, не імпортуючи invalid rows;
10. зберегти migration snapshot і audit evidence поза Git.

Немає дозволу автоматично змінювати live Sheet у v1. Migration є окремою
явно підтвердженою операцією власника.

## 16. Acceptance checklist

Контракт реалізовано коректно лише якщо automated tests доводять:

- exact чотири labels і відхилення aliases у source;
- source-owned IDs не залежать від sorting/row movement;
- same revision/different payload є fatal;
- set/session/program foreign keys і versions узгоджені;
- completed bilateral, unilateral, timed, partial, skipped і void cases
  проходять або відхиляються очікувано;
- дві гантелі, barbell total, machine stack, assistance і bodyweight мають
  різну load semantics;
- `sheet_calculated` ніколи не є входом local metric;
- `null`, zero і missing component не змішуються;
- local result має snapshot/schema/normalizer/formula lineage;
- quarantine diagnostics мають stable code та не витікають персональні
  значення;
- повторний імпорт того самого snapshot дає той самий logical state.
