# Синтезовані constraints

## Progression and Session Rules

### Межа між deterministic progression і recommendation

- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/05 progression and session rules.md
- type: protocol
- content: Стандартний крок double progression є детермінованим правилом поточної програми, а не аналітичною або AI-рекомендацією. Одного виконання вправи достатньо лише тоді, коли всі заплановані working sets досягли верхньої межі repetitions із заданим RIR, стабільною технікою та без зростання болю. Зміна progression rule, кількості sets, вправи чи іншої частини програми потребує щонайменше трьох виконань вправи. Випадковий результат із `RIR 0`, погіршенням техніки або болем не запускає стандартний крок.

### Double progression для основних силових вправ

- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/05 progression and session rules.md
- type: protocol
- content: Bench press, squat, RDL, lat pulldown, shoulder press і seated row використовують double progression. Для prescription `4 × 4–6` load збільшується після виконання всіх чотирьох sets по шість repetitions із заданим RIR; типовий крок для barbell становить 2.5–5 lb на бік, а після збільшення load допустиме повернення до 4–5 repetitions.

### Прогресія hypertrophy-вправ

- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/05 progression and session rules.md
- type: protocol
- content: Для prescription `3 × 8–12` load збільшується лише після 12 repetitions у всіх трьох sets із правильною технікою та щонайменше `RIR 1`. Якщо мінімальний load increment завеликий, спочатку збільшуються repetitions або сповільнюється контрольована eccentric phase.

### Прогресія isolation-вправ

- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/05 progression and session rules.md
- type: protocol
- content: Для вправ у діапазоні `12–20` усі sets спочатку доводяться до верхньої межі, після чого додається мінімальна доступна вага. Повернення до 12–14 repetitions після load increase є допустимим.

### Умови виходу з paired sets

- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/05 progression and session rules.md
- type: protocol
- content: Вправи виконуються окремо, якщо heavy exercise втрачає два або більше repetitions між першим і другим set, техніка погіршується, cardiorespiratory strain стає головним limiter, друга вправа втомлює потрібні першій stabilizers, виникають нудота, запаморочення чи слабкість або спека й недостатня гідратація роблять pairing небезпечним.

### Symptom і clinician boundary

- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/05 progression and session rules.md
- type: nfr
- content: Тренування не перетворюється на metabolic stress test; мета — зберігати performance. За вираженої нудоти, запаморочення, слабкості чи інших стійких симптомів тренування припиняється, а питання ліків, небажаних реакцій і харчування належать кваліфікованому медичному фахівцю. Документ не задає персоналізованого medication advice.

### Бюджет 60-хвилинної session

- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/05 progression and session rules.md
- type: nfr
- content: Час розподіляється так: хвилини 0–8 — warm-up, 8–25 — block A, 25–40 — block B, 40–52 — block C, 52–60 — block D.

### Порядок скорочення при time overrun

- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/05 progression and session rules.md
- type: protocol
- content: Коли час закінчується, rest у головних вправах не скорочується. Зберігаються головний strength movement, основний pull або leg movement і більшість working volume; спочатку прибирається останній isolation set, а потім увесь останній block.

### Виключення full-circuit формату

- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/05 progression and session rules.md
- type: protocol
- content: Full circuit не використовується для цієї програми, оскільки breathing і systemic fatigue обмежуватимуть heavy sets. Paired sets є кращим time-saving форматом, бо зберігають strength, technique і loading.

## Workout Tracker Architecture

### Read-only topology і межа v1

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: schema
- content: V1 має односторонній потік `Google Sheets → read-only pull → immutable raw snapshot → validation/quarantine → versioned normalization → SQLite staging → atomic mirror promotion → metrics → evidence-backed report`; backup проходить окрему encrypted й isolated restore-перевірку. У v1 немає стрілки назад до Google Sheets, workout capture, write-back, generated progression або AI recommendations.

### One-command processing contract

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: api-contract
- content: Одна повторювана CLI-команда має безпечно прочитати authoritative Google Sheets data, перевірити contract і row quality, створити immutable raw snapshot, побудувати idempotent SQLite mirror, обчислити versioned metrics, створити reproducible evidence-lineage report і надати перевірний шлях до backup restore evidence.

### Розподіл authority

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: protocol
- content: Google Sheets володіє виконаними sessions/sets, operational program versions і зовнішніми recommendations. Git володіє Sheet schema, normalization, formulas, progression rules, tests і документацією. Raw snapshots, normalized data, derived metrics і SQLite є rebuildable local projections та не стають окремими owners source facts.

### Operational tabs, labels і stable IDs

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: schema
- content: Очікуються рівно чотири authoritative tabs — `Програма`, `Сесії`, `Підходи`, `Рекомендації` — і рівно чотири source workout labels: `Верх — сила`, `Низ — сила`, `Верх — гіпертрофія`, `Низ — гіпертрофія`. English codes є internal aliases. Обов’язкові source-owned identities: `program_item_id`, `session_id`, `set_id`, `recommendation_id`; row number, date, exercise name, set ordinal і content hash identity не утворюють.

### Revisions, occurrences і program history

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: schema
- content: Factual correction зберігає source-owned identity й створює нову immutable content revision. Snapshot occurrence зберігає `snapshot_id`, source tab, numeric sheet ID, diagnostic row locator, raw row hash, schema/normalizer versions і validation outcome. Кожна нова session посилається на `program_version_id`, а вже використана program version не редагується заднім числом.

### Logical set components

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: schema
- content: Set моделюється як logical header з одним або кількома components і може бути bilateral, `each_side`, окремим `left`/`right`, repetition-based або duration-based. Bulgarian split squat для двох ніг залишається одним prescribed set, а side plank зберігає seconds, а не вигадані repetitions.

### Load semantics і comparison cohort

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: schema
- content: Unitless load заборонено. Зберігаються `load_value`, `load_unit`, `load_basis`, `loading_kind`, `implement_count`, exact exercise variant, equipment і setup/comparison cohort. Machine display, free-weight total, per-dumbbell load і assistance не змішуються.

### Version-fenced four-tab capture

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: protocol
- content: Один pull працює під exclusive lock, виконує preflight, перевіряє source version до й після coherent capture всіх чотирьох tabs і скасовує attempt, якщо source змінився. Immutable snapshot публікується через staging, content hashes, manifest і `COMPLETE` marker; partial capture не вважається complete.

### Validation, quarantine й atomic promotion

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: protocol
- content: Validation і deterministic normalization завершуються до SQLite promotion transaction. Invalid authoritative session або child set quarantine-ить увесь session bundle, rejected entity за замовчуванням не замінює active mirror, а mirror tables і `current_snapshot_id` просуваються однією transaction. Failure залишає попередній complete mirror активним.

### Local storage і SQLite boundary

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: schema
- content: Local layout розділяє immutable raw snapshots, rebuildable processed exports, quarantine diagnostics, encrypted backups і rebuildable SQLite. SQLite окремо зберігає current source projections, immutable revision history, snapshot occurrences, quarantine, metric evidence, sync ledger і active mirror head; source facts та derived metrics перебувають у різних tables.

### Нормативна metric semantics

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: protocol
- content: Volume є сімейством working-set, repetition, eligible-load і primary-muscle-set metrics, а не одним scalar. Maximum load і e1RM порівнюються лише в одному comparison cohort; `epley-v1` застосовується до eligible working sets із 1–12 reps. Missing, ambiguous, timed, bodyweight, assistance й incomparable inputs повертають status/reason і `NULL`, а recovery comparisons лишаються descriptive, не causal.

### Evidence report contract

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: api-contract
- content: Report identity включає snapshot і per-tab hashes, code commit, schema/normalizer/taxonomy/program/formula versions, canonical CLI parameters, timezone й deterministic ordering. Generated timestamp і output path не входять до substantive hash. Кожна metric зберігає formula version, canonical parameters, included/excluded evidence та source IDs.

### Future progression і recommendations

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: protocol
- content: V1 не генерує progression output. У майбутньому deterministic standard step є pure versioned rule й потребує повної перевірки prescribed sets, reps, RIR, technique, pain, program version, comparison cohort та configured increment. Analytical program change потребує щонайменше трьох comparable session occurrences; trend evidence має thresholds `<6` insufficient, `6–7` provisional, `8+` normal; missing context не означає pass.

### Security, privacy й egress

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: nfr
- content: Tracked config і docs не містять live Sheet locator. Tokens зберігаються поза repository в secure storage, core v1 запитує лише read-only Sheets access, local data має private permissions, а workout/health data не надсилаються до LLM або telemetry. Logs містять IDs, hashes, counts і error codes, але не tokens, notes, symptoms, body mass, Sheet locators чи raw rows. Current-file cleanup не усуває вже опубліковану історію; remote remediation потребує explicit owner authorization.

### Backup і isolated restore

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: nfr
- content: RPO становить не більше 24 hours; backup створюється після successful validated pull і щонайменше daily, зберігаються 35 daily та 12 month-end verified copies у двох encrypted fault domains. Full isolated offline restore виконується щонайменше weekly, перевіряє manifest/checksums, rebuilds fresh SQLite, запускає integrity/foreign-key checks і canary hash, а неповний чи змінений archive завершується nonzero без publication.

### Runtime і local analytical stack

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: nfr
- content: Runtime v1 — Python 3.12+ local CLI. SQLite є rebuildable analytical store із staging та atomic promotion; server database, multi-user, authentication і web/mobile interfaces відкладені. Детальний stack decision належить нормативному ADR-002, на який посилається architecture SPEC.

### Repository layout

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: schema
- content: Repository розділяє versioned contracts у `config/`, normative docs у `docs/architecture/`, модулі `source`, `sync`, `storage`, `analytics`, `reporting` у `src/`, generated private data в `data/`, generated reports і tests. `src/`, `data/`, `reports/` і `tests/` створюються під час execution phases, а не як порожній scaffold.

### Run audit і exit contract

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: api-contract
- content: Кожен run має `run_id`, `snapshot_id`, stage durations, retry counts, per-tab fetched/accepted/rejected/inserted/updated/unchanged/tombstoned counts, stable error codes, machine-readable manifest і redacted human summary. Manifest outcome є authoritative, а documented exit categories забезпечують automation для success, auth/remote/source, schema/quarantine, storage/SQLite і invariant failures.

### Idempotence і deterministic reproducibility

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: nfr
- content: Repeated identical snapshot не створює domain/history versions; correction під тим самим ID створює одну revision; coherent disappearance створює tombstone без видалення history. Однакові inputs і versions дають однаковий substantive report hash, а зміна одного set впливає лише на metrics, які посилаються на нього в dependency evidence.

### Safety і definition-of-done quality bar

- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: nfr
- content: Missing values не вигадуються, incomparable exercise variants/equipment/load bases не змішуються, а система не подає medical diagnosis як analytics. V1 не є готовим, доки всі 22 requirements, stable-ID migration, idempotence/reorder/correction/tombstone/quarantine/failure tests, metric exclusions, substantive-hash reproducibility, repository safety й clean offline restore не мають verification evidence та owner disposition для відомого public-history disclosure.
