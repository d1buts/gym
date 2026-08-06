# PRD: Google Sheets Workout Coach

- **Status:** Source of product requirements
- **Version:** 1.0
- **Date:** 2026-07-24
- **Primary user:** власник персональної тренувальної таблиці

## 1. Product outcome

Користувач отримує одну продуману Google Spreadsheet, у якій можна:

1. побачити актуальний чотириденний план тренувань;
2. швидко занести факти завершеного тренування вручну або повідомленням у
   ChatGPT;
3. перевірити історію, прогрес і контекст відновлення;
4. отримати пояснену рекомендацію з посиланням на використані факти;
5. відновити дані та зрозуміти, хто, коли і чому їх змінив.

Успіх вимірюється не кількістю компонентів, а тим, що повний цикл
`план → тренування → capture → перевірка → аналіз → рішення` працює без
прихованої ручної обробки.

## 2. Jobs to be done

### Перед тренуванням

Коли я відкриваю таблицю з телефона, я хочу одразу бачити сьогоднішній
комплекс, порядок paired sets, цільові повторення, RIR і відпочинок.

### Після тренування

Коли я надсилаю в ChatGPT нотатку про виконане тренування, я хочу отримати
структурований preview, виправити неоднозначності й підтвердити один запис без
дублів.

### Під час огляду

Коли я питаю про прогрес вправи або періоду, я хочу бачити порівнювані дані,
статуси відсутності даних і evidence, а не вигадані нулі.

### Під час планування

Коли система пропонує зміну навантаження або програми, я хочу розрізняти
детерміноване правило та AI recommendation і самостійно приймати зміну.

## 3. Functional requirements

### WBK — Workbook

- **WBK-01:** Workbook має сім точних вкладок: `Старт`, `Програма`, `Сесії`,
  `Підходи`, `Рекомендації`, `Довідники`, `Дашборд`.
- **WBK-02:** `Програма` містить чотири версійовані комплекси з repository
  program specifications без втрати paired-set, reps, RIR, rest і equipment
  semantics.
- **WBK-03:** Поля вводу мають validation, підказки, формати й mobile-friendly
  порядок; formula/system columns захищені.
- **WBK-04:** Формули й дашборд показують лише визначені метрики та явно
  відображають missing/incomparable status.
- **WBK-05:** Workbook setup є повторюваним: повторний запуск не дублює
  вкладки, формули, named ranges або program items.

### CAP — ChatGPT capture

- **CAP-01:** Користувач може описати виконане тренування природною мовою.
- **CAP-02:** Система не вигадує пропущені факти: вона запитує критичні
  уточнення або залишає дозволене значення невідомим.
- **CAP-03:** До запису користувач бачить normalized preview сесії й підходів,
  а також warnings.
- **CAP-04:** `commit_workout` працює лише після explicit confirmation і
  додає session/set bundle атомарно.
- **CAP-05:** Stable IDs та idempotency key запобігають дублюванню під час
  повтору, timeout або retry.
- **CAP-06:** Writer не має arbitrary cell/range mutation і працює лише з
  allowlisted fields.

### ANL — Reading and analytics

- **ANL-01:** Користувач може запитати історію за workout type, exercise,
  program version і date range.
- **ANL-02:** Working volume, load, e1RM, RIR, rest і recovery summaries
  відповідають версійованим metric contracts.
- **ANL-03:** Variant, equipment, load basis, assistance semantics і comparison
  cohort перевіряються до порівняння.
- **ANL-04:** Кожен аналітичний результат містить formula/ruleset version,
  status і достатній evidence locator.
- **ANL-05:** Dashboard і ChatGPT query tools використовують однакові
  семантики метрик.

### REC — Recommendations

- **REC-01:** Deterministic progression rule повертає результат окремо від
  AI-generated recommendation.
- **REC-02:** Recommendation містить `recommendation_id`, created time,
  evidence window, rationale, confidence/limitations і status.
- **REC-03:** Недостатні або непорівнювані дані створюють рекомендацію
  `insufficient_evidence` або відмову, а не вигадану пораду.
- **REC-04:** Рекомендація не змінює program prescription без explicit owner
  approval та нової `program_version_id`.
- **REC-05:** Recovery context є описовим; система не ставить діагноз і не
  робить причинного медичного висновку.

### SAFE — Privacy, audit and recovery

- **SAFE-01:** Secrets, live Sheet locator і персональні exports не потрапляють
  у Git, logs або generated documentation.
- **SAFE-02:** Write audit містить IDs, actor/tool version, timestamps, hashes
  і outcome, але не raw notes чи зайві health fields.
- **SAFE-03:** Аналітичний pull створює coherent immutable snapshots, а
  promotion mirror є атомарним.
- **SAFE-04:** Є portable backup і перевірений isolated restore для workbook
  data, program versions та локального аналітичного стану.
- **SAFE-05:** До моделі передається мінімальний user-authorized контекст,
  потрібний для конкретного capture або analysis request.

## 4. User acceptance journeys

### UAT-01 — Новий workbook

На чистому тестовому Spreadsheet setup створює сім вкладок, чотири комплекси,
validation, formulas і dashboard. Другий запуск не змінює logical content.

### UAT-02 — Додавання тренування

Користувач описує сесію з кількома підходами, бачить preview, уточнює одне
поле й підтверджує. У `Сесії` з’являється одна сесія, у `Підходи` — правильні
дочірні записи; повторний commit повертає той самий результат без дубля.

### UAT-03 — Відмова без підтвердження

Невалідний, неповний або непідтверджений payload не змінює Spreadsheet.

### UAT-04 — Аналіз прогресу

Запит конкретної вправи повертає лише порівнюваний cohort, метрики з evidence
і чіткий статус там, де даних недостатньо.

### UAT-05 — Рекомендація

Система показує deterministic rule result і окрему recommendation. Програма
не змінюється, доки користувач явно не прийме пропозицію.

### UAT-06 — Restore

Із backup у відокремленому середовищі відновлюються operational records і
аналітичний mirror; counts та hashes збігаються з manifest.

## 5. Non-goals for the first milestone

- multi-user coaching platform;
- wearable ingestion і background health monitoring;
- автоматичні медичні висновки;
- автоматичне застосування program changes;
- довільний Sheet editor у ChatGPT;
- server database як нове primary source of truth.

## 6. Product constraints

- Google Spreadsheet лишається придатною для ручного використання, навіть
  коли ChatGPT integration недоступна.
- Local state завжди можна перебудувати з authoritative Sheet data і
  versioned Git rules.
- Python/SQLite є допоміжним validation/analytics layer, а не вимогою для
  відкриття плану чи ручного capture.
- Усі production writes перевіряються проти machine-readable contract version.
