# Синтезовані constraints

## Progression and Session Rules

### Межа deterministic progression
- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/05 progression and session rules.md
- type: protocol
- content: Один fully qualifying performance може запустити лише стандартний double-progression step; зміна rule, exercise або set count потребує щонайменше трьох виконань. `RIR 0`, degraded technique або increased pain не проходять eligibility.

### Основна, hypertrophy та isolation progression
- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/05 progression and session rules.md
- type: protocol
- content: Main lifts збільшують load після досягнення верхньої rep boundary в усіх sets із заданим RIR; `3 × 8–12` потребує 12 reps у трьох sets із `RIR >= 1`; isolation `12–20` спершу доводиться до верхньої межі, потім отримує minimum increment.

### Paired-set safety і 60-minute budget
- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/05 progression and session rules.md
- type: nfr
- content: Pairing припиняється за втрати performance/technique або symptom context. Rest головних рухів не скорочується; при time overrun першими прибираються останній isolation set і останній block. Acute or persistent symptoms належать qualified medical professional, не analytics.

## Workout Tracker Architecture

### Spreadsheet-first system boundary
- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: protocol
- content: Google Spreadsheet є standalone daily product і operational authority; narrow ChatGPT tools додають controlled write-back, а Python/SQLite забезпечують rebuildable validation, analytics, evidence і restore.

### Seven-tab workbook і four program complexes
- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: schema
- content: Workbook має exact Ukrainian source labels для семи tabs та versioned bootstrap чотирьох complexes. English aliases є internal only.

### Controlled ChatGPT write path
- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: api-contract
- content: `preview_workout` не мутує source; `commit_workout` потребує confirmed preview, stable IDs, idempotency key і contract/version preconditions та атомарно додає allowlisted session/set bundle.

### Authority, identity і revisions
- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: schema
- content: Sheets володіє operational facts/program prescriptions; Git — schemas/rules/tests/docs; local state є projection. `session_id`, `set_id`, `program_item_id`, `recommendation_id` source-owned; row number не identity; correction створює revision під тим самим ID.

### Coherent capture та atomic promotion
- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: protocol
- content: Analytical pull захоплює всі чотири authoritative tabs як version-fenced unit, публікує immutable complete snapshot, validates до transaction і атомарно promotes staged mirror head. Failure залишає попередній complete mirror active.

### Comparable evidence metrics
- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: protocol
- content: Metrics використовують pinned formulas, explicit eligibility, cohort identity і evidence lineage. Missing/incomparable input повертає status та `NULL`; recovery analysis descriptive only.

### Privacy, audit і backup
- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: nfr
- content: Read і writer credentials розділені; logs містять IDs/hashes/counts/error codes, не raw facts або locators. Backups portable, encrypted і перевіряються isolated restore з manifest/count/hash evidence.

### Runtime boundary
- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md
- type: nfr
- content: Python 3.12+, uv-style management, Pydantic і SQLite є local analytical stack. Server database, multi-user, wearables, arbitrary Sheet editing та automatic program changes не входять у milestone.

## DATA_MODEL

### Три класи полів
- source: /home/muuser/bushuk-labs/gym/docs/architecture/DATA_MODEL.md
- type: schema
- content: Source facts, Sheet-calculated values і local-derived values зберігаються окремо з provenance; derived output не переписує authoritative facts.

### Source-owned identity та version linkage
- source: /home/muuser/bushuk-labs/gym/docs/architecture/DATA_MODEL.md
- type: schema
- content: Stable IDs обов’язкові для program items, sessions, sets і recommendations. Кожна session посилається на `program_version_id`; identity не виводиться з row/date/name/ordinal/hash.

### Canonical tabs і field contracts
- source: /home/muuser/bushuk-labs/gym/docs/architecture/DATA_MODEL.md
- type: schema
- content: `Програма`, `Сесії`, `Підходи`, `Рекомендації` мають exact versioned columns, nullable semantics, ranges, referential invariants і cross-field validation.

### Exercise and load comparability
- source: /home/muuser/bushuk-labs/gym/docs/architecture/DATA_MODEL.md
- type: schema
- content: Exercise family, exact variant, equipment, setup/cohort, `load_value`, `load_unit`, `load_basis`, `loading_kind`, implement count і assistance semantics є distinct fields; source value/unit/basis зберігаються до conversion.

### Bundle validation і evolution
- source: /home/muuser/bushuk-labs/gym/docs/architecture/DATA_MODEL.md
- type: protocol
- content: Invalid authoritative session/set bundle quarantine-иться цілком. Schema/normalizer changes versioned; compatibility та source migration мають explicit gates і tests.

## METRICS

### Shared metric-result contract
- source: /home/muuser/bushuk-labs/gym/docs/architecture/METRICS.md
- type: schema
- content: Кожен metric result має value або `NULL`, unit, status/reason, formula version, parameters, cohort identity та included/excluded source evidence.

### Working-set eligibility і volume family
- source: /home/muuser/bushuk-labs/gym/docs/architecture/METRICS.md
- type: protocol
- content: Warm-ups та invalid/aborted sets виключаються. Working-set count, rep volume, load volume і muscle-group volume є окремими metrics, а не одним scalar.

### Maximum load і e1RM
- source: /home/muuser/bushuk-labs/gym/docs/architecture/METRICS.md
- type: protocol
- content: Maximum load та Epley `e1RM` обчислюються лише в identical comparison cohort; e1RM використовує pinned formula та eligible 1–12 rep window. Ineligible input дає status і `NULL`.

### RIR, rest і recovery
- source: /home/muuser/bushuk-labs/gym/docs/architecture/METRICS.md
- type: protocol
- content: Missing RIR/rest/recovery не дорівнює zero або pass. Recovery summaries описують association/context і не стверджують causation, diagnosis або treatment.

### Deterministic analytics vs AI
- source: /home/muuser/bushuk-labs/gym/docs/architecture/METRICS.md
- type: nfr
- content: Formula/ruleset output маркується deterministic; AI recommendation є окремим object із evidence, uncertainty і limitations та не може автоматично змінити program.

## SYNC_PROTOCOL

### Read-only source boundary
- source: /home/muuser/bushuk-labs/gym/docs/architecture/SYNC_PROTOCOL.md
- type: api-contract
- content: Analytical sync використовує read-only Google authorization, API method allowlist і explicit source binding. Writer credentials та operations не входять у pull.

### Lock, preflight і coherent capture
- source: /home/muuser/bushuk-labs/gym/docs/architecture/SYNC_PROTOCOL.md
- type: protocol
- content: Run бере local exclusive lock, виконує local/remote preflight і захоплює всі source ranges під Drive version fence або double-capture fingerprint fence.

### Immutable snapshot publication
- source: /home/muuser/bushuk-labs/gym/docs/architecture/SYNC_PROTOCOL.md
- type: protocol
- content: Raw capture пишеться в staging, отримує content-addressed hashes/manifest та стає valid snapshot лише після atomic publication і completion marker.

### Normalize, reconcile, promote
- source: /home/muuser/bushuk-labs/gym/docs/architecture/SYNC_PROTOCOL.md
- type: protocol
- content: Versioned pure normalization завершується до SQLite transaction; reconciliation розрізняє unchanged, corrected, missing/tombstoned і new identities; staged tables та mirror head promote атомарно.

### Retry, audit і failure semantics
- source: /home/muuser/bushuk-labs/gym/docs/architecture/SYNC_PROTOCOL.md
- type: nfr
- content: Retry/backoff дозволено лише для documented transient cases. Stable exit codes, durable redacted audit summary і invariant checks роблять failure diagnosable, не exposing raw payload.

## SECURITY_AND_BACKUP

### Authorization profiles
- source: /home/muuser/bushuk-labs/gym/docs/architecture/SECURITY_AND_BACKUP.md
- type: protocol
- content: Read-only OAuth/service-account profile і controlled writer profile із minimal scopes/allowlist фізично та логічно розділені; source binding перевіряється до access.

### Secret and repository safety
- source: /home/muuser/bushuk-labs/gym/docs/architecture/SECURITY_AND_BACKUP.md
- type: nfr
- content: Credentials, live locators, personal exports, databases, reports, logs і backups не tracked. Known public-history disclosure не повторюється; history rewrite, sharing або rotation потребують owner authorization.

### Logging, egress і CSV safety
- source: /home/muuser/bushuk-labs/gym/docs/architecture/SECURITY_AND_BACKUP.md
- type: nfr
- content: Logs/audits redact notes, symptoms, body mass, locators, tokens і raw rows; model egress мінімізовано до user-authorized need. Exported text нейтралізує spreadsheet formula injection.

### Backup manifest and retention
- source: /home/muuser/bushuk-labs/gym/docs/architecture/SECURITY_AND_BACKUP.md
- type: schema
- content: Backup має exact manifest, hashes, contract/version metadata, snapshot/program coverage і encryption/fault-domain evidence; retention та RPO є explicit operational properties.

### Isolated restore acceptance
- source: /home/muuser/bushuk-labs/gym/docs/architecture/SECURITY_AND_BACKUP.md
- type: protocol
- content: Offline isolated restore перевіряє archive checksums, rebuilds fresh SQLite, запускає integrity/foreign-key checks і порівнює counts/hashes; неповний restore не публікується.

## SPEC: ChatGPT workout capture, query and recommendations

### Narrow versioned tools
- source: /home/muuser/bushuk-labs/gym/docs/specs/SPEC-CHATGPT-WORKOUT-CAPTURE.md
- type: api-contract
- content: Integration exposes `preview_workout`, `commit_workout`, filtered history/analysis і recommendation tools із versioned input/output schemas; arbitrary range mutation відсутня.

### Preview/confirmation protocol
- source: /home/muuser/bushuk-labs/gym/docs/specs/SPEC-CHATGPT-WORKOUT-CAPTURE.md
- type: protocol
- content: Preview normalizes only user-provided facts, surfaces missing/ambiguous fields and warnings, and produces confirmation-bound payload/hash. Commit rejects absent, stale або mismatched confirmation.

### Atomic idempotent write
- source: /home/muuser/bushuk-labs/gym/docs/specs/SPEC-CHATGPT-WORKOUT-CAPTURE.md
- type: protocol
- content: Commit validates contract/version preconditions, stable IDs та idempotency key й додає session plus child sets як one logical bundle; replay returns original result.

### Query and recommendation evidence
- source: /home/muuser/bushuk-labs/gym/docs/specs/SPEC-CHATGPT-WORKOUT-CAPTURE.md
- type: schema
- content: Read tools minimize returned facts; analytics/recommendations include versions, status, cohort/evidence and limitations. Recommendation never masquerades as deterministic rule or accepted program change.

### Privacy and medical boundary
- source: /home/muuser/bushuk-labs/gym/docs/specs/SPEC-CHATGPT-WORKOUT-CAPTURE.md
- type: nfr
- content: Only user-authored workout content and minimum authorized context enter model processing. Bulk history and unrelated health context are excluded; symptom context is self-report, not diagnosis.

## SPEC: Google Sheets workbook

### Exact workbook topology
- source: /home/muuser/bushuk-labs/gym/docs/specs/SPEC-GOOGLE-SHEETS-WORKBOOK.md
- type: schema
- content: Workbook contains exact tabs `Старт`, `Програма`, `Сесії`, `Підходи`, `Рекомендації`, `Довідники`, `Дашборд`, with exact Ukrainian source labels and versioned machine bindings.

### Mobile workflow and manual fallback
- source: /home/muuser/bushuk-labs/gym/docs/specs/SPEC-GOOGLE-SHEETS-WORKBOOK.md
- type: nfr
- content: `Старт` prioritizes today’s complex and safe entry flow on phone. Manual capture remains usable when ChatGPT integration або local analytics unavailable.

### Program bootstrap and idempotence
- source: /home/muuser/bushuk-labs/gym/docs/specs/SPEC-GOOGLE-SHEETS-WORKBOOK.md
- type: protocol
- content: Setup loads four repository-defined complexes with versioned stable items and is repeatable without duplicating tabs, named ranges, formulas or prescriptions.

### Validation, protection and formulas
- source: /home/muuser/bushuk-labs/gym/docs/specs/SPEC-GOOGLE-SHEETS-WORKBOOK.md
- type: protocol
- content: Input cells use validation/hints/formats; formula/system columns are protected. Working-set, volume, e1RM and session summaries follow METRICS and display missing/incomparable states.

### Dashboard quality gate
- source: /home/muuser/bushuk-labs/gym/docs/specs/SPEC-GOOGLE-SHEETS-WORKBOOK.md
- type: nfr
- content: Dashboard exposes only traceable defined metrics, avoids causal health claims, and remains consistent with ChatGPT/local analytics semantics under automated setup and UAT.
