# Протокол синхронізації Google Sheets → SQLite

- **Статус:** нормативний контракт v1
- **Версія протоколу:** `sync-protocol-v1`
- **Дата:** 2026-07-24
- **Покриває:** `SRC-01..04`, `SYNC-01..05`
- **Напрямок v1:** лише читання Google Sheets; локальні записи дозволені

## 1. Призначення і межі

Цей документ визначає, як один локальний процес перетворює чотири
authoritative вкладки Google Sheets на:

1. узгоджений immutable raw snapshot;
2. перевірені або quarantined entity bundles;
3. детермінований normalized staging dataset;
4. атомарне SQLite-дзеркало з current state, history та tombstones;
5. audit summary, достатній для повторення й розслідування запуску.

Google Sheets володіє operational facts. Raw snapshot, staging та SQLite є
відтворюваними локальними проєкціями й не створюють альтернативного джерела
правди. Межі ownership зафіксовано в
[ADR-001](./ADR-001-authority-boundaries.md), runtime і SQLite — в
[ADR-002](./ADR-002-python-sqlite-v1.md).

V1 не записує жодної клітинки, властивості, permission або metadata назад у
Google Workspace. Workout capture, recommendation write-back і будь-який
двосторонній sync є v2 scope.

## 2. Нормативна мова та залежні контракти

`MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT` і `MAY` мають значення вимоги,
заборони, сильної рекомендації та дозволеної опції. Реалізація відповідає v1
лише тоді, коли виконує всі `MUST` і всі інваріанти розділу 18.

Цей протокол навмисно не дублює field-level правила:

- canonical entities, поля, ключі та SQLite constraints:
  [DATA_MODEL.md](./DATA_MODEL.md);
- source labels, типи, nullable rules, aliases і діапазони:
  [schema.yaml](../../config/schema.yaml);
- формули та semantic metric versions:
  [METRICS.md](./METRICS.md);
- секрети, permissions, retention, encryption і restore:
  [SECURITY_AND_BACKUP.md](./SECURITY_AND_BACKUP.md).

Пріоритет у разі розходження: accepted ADR → цей протокол для sync behavior →
`DATA_MODEL.md` для entity semantics → `schema.yaml` для конкретного source
contract. Формула метрики ніколи не визначається sync-кодом.

## 3. Терміни

| Термін | Нормативне значення |
|---|---|
| `source` | Один Google Spreadsheet, явно дозволений локальною конфігурацією. |
| `source_alias` | Нечутливий локальний псевдонім source; не Spreadsheet ID. |
| `source version` | Opaque Drive metadata version у profile A або logical raw fingerprint у profile B. |
| `capture attempt` | Один profile-specific fence: version-wrapped capture (A) або два complete Sheets captures (B). |
| `snapshot` | Immutable каталог raw API responses, manifest і marker `COMPLETE`. |
| `snapshot_id` | `snp_<64 lowercase hex>` від canonical capture descriptor. |
| `entity` | `program_version`, `program_item`, `session`, `set` або `recommendation`. |
| `bundle` | Мінімальна група source rows, яку можна прийняти або відхилити лише цілком. |
| `quarantine` | Immutable diagnostics, що посилаються на відхилені rows у raw snapshot. |
| `staging` | Детермінований normalized dataset перед SQLite transaction. |
| `logical payload` | Canonical business fields entity без row position і run metadata. |
| `mirror head` | Єдиний committed tuple snapshot/schema/normalizer/config, який бачить analytics. |
| `tombstone` | History event про зникнення stable ID із повного валідного source snapshot. |
| `no-op` | Успішний run, який не змінює logical current state або history. |

Усі timestamps, створені локальним процесом, MUST бути UTC RFC 3339 із
суфіксом `Z`. Source dates зберігаються за правилами data model; runtime
locale або timezone операційної системи не можуть неявно змінювати результат.

## 4. Станова модель одного запуску

Durable `sync_run` має один із п’яти станів:

`started → captured → validated → committed`

Будь-який незавершений перехід може завершитися `failed`. Детальні phase
events (`lock`, `preflight`, `fence`, `publish`, `normalize`, `reconcile`,
`commit`) записуються окремо й не розширюють durable enum.

Успішний шлях:

1. створити `run_id` і взяти локальний lock;
2. виконати local та remote preflight;
3. отримати fenced multi-range capture;
4. опублікувати або повторно використати immutable raw snapshot;
5. перевірити source rows і побудувати quarantine closure;
6. чисто нормалізувати accepted bundles та опублікувати staging;
7. звірити staging з SQLite current state;
8. одним transaction записати current/history/observations/run audit і
   `mirror_head`;
9. надрукувати final summary та звільнити lock.

Raw snapshot може існувати без нового mirror head. Mirror head не може
посилатися на snapshot без валідного `COMPLETE`.

## 5. Read-only security boundary v1

### 5.1 Auth/coherence profiles та OAuth scopes

Core v1 MUST працювати без Drive scope. Реалізація підтримує два explicit
profiles; обраний profile записується в run і snapshot manifest.

| Profile | Identity | Дозволені scopes | Coherence fence |
|---|---|---|---|
| **A — service-account metadata fence (recommended)** | Dedicated service account, shared як Viewer лише з target Sheet | `spreadsheets.readonly` + `drive.metadata.readonly` | `File.version`/`modifiedTime` до і після capture |
| **B — desktop OAuth double capture (baseline)** | Installed desktop OAuth | лише `spreadsheets.readonly` | Два повні consecutive captures з однаковим logical raw fingerprint |

Повні scope URIs:

- `https://www.googleapis.com/auth/spreadsheets.readonly`;
- лише для profile A:
  `https://www.googleapis.com/auth/drive.metadata.readonly`.

Profile A не отримує Drive content, export або write scope. Metadata scope
використовується лише для exact-ID `files.get`; service account не має
доступу до інших Drive files завдяки окремій identity і target-only share.
Profile B не викликає Drive API взагалі.

Credential cache для sync MUST бути окремим від майбутніх write-capable
credentials. Якщо реалізація не може довести відповідність credential
обраному read-only profile, preflight MUST завершитися помилкою. Наявність
ширшого grant не дозволяє викликати додаткові methods. Детальні identity та
storage controls визначає
[SECURITY_AND_BACKUP.md](./SECURITY_AND_BACKUP.md).

### 5.2 API method allowlist

Єдині дозволені remote methods:

| Method | Дозволене використання |
|---|---|
| `Drive files.get` | Лише profile A: `id`, `mimeType`, `trashed`, `version`, `modifiedTime` для точно відомого file ID |
| `Sheets spreadsheets.get` | spreadsheet properties та required sheet properties/headers |
| `Sheets spreadsheets.values.batchGet` | ordered read чотирьох authoritative ranges; один раз у profile A, двічі у profile B |

У profile B allowlist містить лише два Sheets methods. `files.list`, Drive
content/download/export, Sheets export, append, update, batchUpdate, clear,
create, copy, delete, permission changes і Apps Script calls заборонені.
Remote client adapter MUST відхиляти method поза profile-specific allowlist
до мережевого запиту, навіть якщо token технічно має ширші права.

### 5.3 Source allowlist

Локальний secret/config store містить точний Spreadsheet ID, але runtime
працює з його `source_alias`. V1:

- MUST мати рівно один active allowlisted Spreadsheet ID на run;
- MUST NOT знаходити source через search/list;
- MUST відхиляти CLI override, URL або redirect на інший ID;
- MUST перевіряти response Spreadsheet/File ID проти allowlist;
- MUST NOT писати live ID у console, structured logs, reports, manifest,
  snapshot, staging або quarantine;
- MUST відкинути transport identity field після allowlist check і до
  persistence, залишивши `source_alias`.

## 6. Локальний lock і crash recovery

До першого remote request процес MUST отримати exclusive non-blocking OS file
lock для `source_alias` і SQLite mirror. Lock охоплює preflight, capture,
snapshot publication, validation, normalization, transaction та final durable
audit.

Lock file MAY містити лише diagnostic `run_id`, PID і UTC start time, має mode
`0600`, але наявність файла не визначає ownership: істинним lock є kernel
lock. Реалізація MUST NOT видаляти чужий lock через `--force`.

Якщо lock зайнятий, run завершується `LOCK_BUSY` без remote calls і без
SQLite writes. Якщо файл залишився після crash, але kernel lock вільний, новий
run може його безпечно перевикористати.

Після отримання lock процес MUST:

1. знайти incomplete каталоги `.inflight`;
2. не трактувати їх як snapshots або staging;
3. перевірити, чи попередній `committing` run має target tuple у
   `mirror_head`;
4. класифікувати його як committed-after-crash або failed-before-commit;
5. лише після цього починати новий pull.

Cleanup stale `.inflight` artifacts відбувається за retention policy з
`SECURITY_AND_BACKUP.md`, а не за PID у назві.

## 7. Preflight

Preflight не приймає facts у mirror. Він MUST завершити всі перевірки нижче
до створення publishable snapshot.

### 7.1 Local preflight

- configuration parse і version compatibility;
- exact read-only scopes та source allowlist;
- наявність `schema.yaml` і підтримуваний `schema_version`;
- наявність підтримуваного `normalizer_version`;
- writable private directories для raw, staging, quarantine, logs і SQLite;
- filesystem permissions відповідно до security contract;
- SQLite application/schema version compatibility;
- `PRAGMA foreign_keys=ON` і успішний SQLite integrity precheck;
- достатній вільний простір за configured safety floor;
- відсутність нерозв’язаного ambiguous prior commit.

Semantic config fingerprint MUST охоплювати schema, explicit aliases,
normalization options і unit policy. Він MUST NOT охоплювати credential,
absolute paths, log verbosity або поточний час.

### 7.2 Remote preflight

Для allowlisted ID процес MUST перевірити:

- source існує й доступний як Google Spreadsheet;
- у profile A File не в trash, має Google Spreadsheet MIME type, а `version`
  доступний як source fence;
- у profile B два Sheets reads повертають exact allowlisted Spreadsheet ID;
- доступні рівно required titles `Програма`, `Сесії`, `Підходи`,
  `Рекомендації`;
- кожен title однозначно відповідає одному numeric sheet ID;
- captured header row відповідає `schema.yaml`: немає missing, duplicate або
  невідомих columns поза explicit versioned alias/extension policy;
- spreadsheet locale і timezone доступні та записані для deterministic
  parsing;
- усі configured A1 ranges є whole-tab ranges без штучної верхньої межі
  рядків.

Preflight header read є ранньою діагностикою. Лише headers із fenced raw
snapshot використовуються для подальшого рішення, бо source може змінитися
після preflight.

Field-level types перевіряються після raw preservation, але до staging і
SQLite import. Таким чином raw evidence не втрачається, а invalid values не
стають accepted facts.

## 8. Coherent multi-range capture

### 8.1 Complete Sheets capture

Один **complete Sheets capture** складається з:

1. `Sheets spreadsheets.get` → locale, timezone, allowlisted Spreadsheet ID,
   sheet IDs, titles та grid metadata;
2. одного `spreadsheets.values.batchGet` з чотирма ranges у canonical order
   з `schema.yaml`.

`batchGet` MUST використовувати:

- `majorDimension=ROWS`;
- explicit `valueRenderOption` і `dateTimeRenderOption`, pinned у
  `capture_contract_version`;
- quoted sheet titles і exact whole-tab ranges;
- ordered ranges: `Програма`, `Сесії`, `Підходи`, `Рекомендації`.

Кожен response MUST містити allowlisted Spreadsheet ID, рівно чотири
`valueRanges`, кожен у requested order і для expected sheet. Missing response,
duplicate response, truncated transport body або unexpected range робить
attempt недійсним.

Для порівняння complete captures обчислюється `logical_raw_fingerprint`:
SHA-256 canonical JSON від request parameters, relevant spreadsheet/sheet
metadata та ordered raw JSON scalar arrays. Він не залежить від JSON key
order, whitespace або HTTP headers, але розрізняє JSON types, row order,
blank-vs-present values, locale, timezone, sheet IDs/titles і cell values.
Жодна domain normalization у fingerprint не виконується.

### 8.2 Profile A: Drive metadata version fence

Один profile A attempt MUST виконати:

1. `Drive files.get` → `source_version_before`;
2. один complete Sheets capture;
3. `Drive files.get` → `source_version_after`.

Capture є придатним лише якщо:

- `version_before == version_after`;
- `modifiedTime_before == modifiedTime_after`;
- File ID і MIME type однакові;
- обидві version responses успішні й повні.

Profile A source version у manifest є exact `version` та `modifiedTime`; live
File ID проходить allowlist check, але не копіюється в manifest/log.

### 8.3 Profile B: double-capture fingerprint fence

Один profile B attempt MUST виконати два complete Sheets captures поспіль:
`capture_a`, потім `capture_b`. Обидва raw responses зберігаються як fence
evidence. Capture придатний лише якщо:

- `logical_raw_fingerprint_a == logical_raw_fingerprint_b`;
- обидва metadata responses містять той самий allowlisted Spreadsheet ID;
- sheet IDs/titles, locale, timezone, request parameters та response shapes
  однакові.

Для normalization використовується `capture_b`; рівність fingerprints
доводить, що його logical raw content збігається з `capture_a`. Profile B
source version у manifest є пара цих fingerprints.

Будь-який profile-specific mismatch означає, що source міг змінитися під час
читання. Усі bytes attempt залишаються лише в `.inflight`, не отримують
`COMPLETE`, не проходять validation і не можуть створити tombstones. Retry
повторює весь profile attempt: від version-before у A або від нового
`capture_a` у B.

Profile A виявляє будь-яку server-recorded File version change. Profile B
виявляє зміну logical captured content між двома observations, але не може
довести, що content не змінився й не повернувся до того самого стану між
ними. Обидва profiles є detection-and-retry fences, а не server-side lock
або provider-guaranteed snapshot transaction; межу v2 описано в розділі 19.

## 9. Immutable content-addressed raw snapshot

### 9.1 Layout

Private raw store має таку логічну структуру:

```text
data/raw/
├── .inflight/<run_id>/
└── snapshots/sha256/<first-two-hex>/<full-64-hex>/
    ├── payload/
    │   ├── profile-a/
    │   │   ├── drive-version-before.json
    │   │   ├── spreadsheet-metadata.json
    │   │   ├── values-batch-get.json
    │   │   └── drive-version-after.json
    │   └── profile-b/
    │       ├── capture-a-metadata.json
    │       ├── capture-a-values.json
    │       ├── capture-b-metadata.json
    │       └── capture-b-values.json
    ├── manifest.json
    └── COMPLETE
```

Snapshot містить **один** profile-specific payload subtree, не обидва.
Payload files є versioned `raw-capture-v1` envelopes, а не HTTP archives.
Після allowlist check adapter MUST видалити тільки transport identity
(live Spreadsheet/File ID) і transport/security metadata. Усі
contract-relevant sheet properties, headers, JSON scalar cell values, array
boundaries і source versions/fingerprints зберігаються без domain
normalization, inference, renamed headers або padded cells. Trailing empty
cells omitted by Google remain omitted в raw. HTTP headers, URLs,
authorization data, cookies і tokens MUST NOT зберігатися.

Обов’язкова locator redaction є transport sanitation, а не data
normalization: вона не має права змінювати жодну cell value. Envelope version
і список omitted transport fields записуються в manifest.

### 9.2 Hashes та IDs

Для кожного payload file manifest записує relative path, byte length і
SHA-256. Canonical capture descriptor містить:

- `capture_contract_version`;
- `auth_coherence_profile`;
- `source_alias`;
- ordered requested ranges та render options;
- profile A source-version response hashes або profile B обидва
  `logical_raw_fingerprint`;
- ordered payload path/hash/length entries.

`snapshot_id` має форму `snp_<sha256>`, де suffix є SHA-256 від UTF-8
canonical JSON capture descriptor. Timestamp не входить до цього hash.
Повторно отриманий byte-identical sanitized descriptor має той самий
`snapshot_id`; semantic idempotency не залежить від того, чи Google
серіалізував еквівалентну transport response іншими bytes.

`manifest.json` MUST містити щонайменше:

- protocol і capture contract versions;
- `snapshot_id`, `source_alias`;
- `auth_coherence_profile` і його source versions/fingerprints before/after;
- first `captured_at`;
- spreadsheet locale/timezone і sheet ID/title map;
- ordered request parameters;
- payload hashes/lengths;
- per-tab raw row counts;
- creator software version;
- hash algorithm і canonicalization identifier.

Actual Spreadsheet ID не дублюється в manifest. Повний SHA-256 bytes
`manifest.json` записується в `COMPLETE`.

### 9.3 Publication

Процес MUST:

1. створювати payload у `.inflight/<run_id>` на тому самому filesystem, що й
   final raw store;
2. записати й перевірити всі payload hashes;
3. обчислити `snapshot_id`;
4. записати manifest;
5. записати `COMPLETE` останнім;
6. flush/fsync files і directory згідно storage contract;
7. атомарно rename temporary directory у content-addressed final path.

Consumer MUST приймати snapshot лише коли final path, `manifest.json` і
`COMPLETE` існують, manifest hash збігається, усі payload hashes збігаються,
а path відповідає `snapshot_id`.

Якщо final path уже існує, publisher MUST повністю перевірити existing
snapshot. За збігу він повторно використовує його й видаляє свій temporary
candidate. Будь-яка розбіжність під тим самим ID є integrity failure, а не
приводом перезаписати каталог.

Після publication жоден файл snapshot не змінюється. Нове спостереження того
самого content записується в `sync_runs`, а не в existing manifest.

## 10. Validation і entity-bundle quarantine

### 10.1 Два validation boundaries

1. **External model validation:** raw header/value → typed source row за
   `schema.yaml`.
2. **Canonical model validation:** normalized entity → constraints із
   `DATA_MODEL.md`.

Unknown value залишається `null`. Порожній source факт не можна замінювати
default, середнім, попереднім значенням або LLM inference. Defaults дозволені
лише для технічних полів, явно позначених як generated і versioned.

Diagnostics мають одну з чотирьох severity з `schema.yaml`, стабільний
`reason_code`, entity/bundle type, field path і raw source reference
(`snapshot_id`, tab, 1-based row number):

| Severity | Sync behavior v1 |
|---|---|
| `fatal` | Відхиляє весь snapshot для staging/promotion; head не змінюється. |
| `error` | Quarantines цілий dependency-closed bundle; fail-closed policy не просуває head. |
| `warning` | Entity може бути accepted; warning входить в audit. |
| `info` | Entity може бути accepted; downstream eligibility MAY виключати її за окремим контрактом. |

User-entered value не потрапляє в звичайний log.

### 10.2 Stable IDs

Source-owned IDs є обов’язковими:

- `program_version_id`;
- `program_item_id`;
- `session_id`;
- `set_id`;
- `recommendation_id`.

Вони валідовуються за `schema.yaml` і `DATA_MODEL.md`. Row number, sheet sort
order, timestamp імпорту або hash усього mutable payload не можуть бути
entity identity.

Generated, content-derived, normalizer-derived та row-position fallback IDs
заборонені. Legacy data проходить explicit source migration і отримує ID у
Google Sheets до імпорту. Відсутній/invalid required ID є `error`. Один ID
і revision із різними payloads є snapshot-level `fatal`. Навіть
byte-identical duplicate source rows не collapse мовчки — вони відхиляються
за explicit duplicate rule з `schema.yaml`.

Кожна source entity також має integer `source_revision`. Пара
`(stable_id, source_revision)` є immutable:

- той самий revision з іншим `source_payload_sha256` є fatal identity
  conflict і quarantines bundle;
- revision, нижчий за вже committed revision цього ID, є error;
- source correction MUST зберігати stable ID і збільшувати revision;
- normalizer не генерує, не збільшує й не «виправляє» source revision.

### 10.3 Bundle boundaries

| Bundle | Склад |
|---|---|
| Program version | один `program_version_id` та всі його `program_item` rows |
| Session | одна `session` та всі `set` rows з її `session_id` |
| Recommendation | одна `recommendation` та її evidence references |
| Orphan/identity conflict | rows, які неможливо безпечно приєднати до domain bundle |

Якщо одна row у bundle має `error`, quarantined є весь bundle. `fatal`
відхиляє snapshot незалежно від bundle closure. Invalid parent
каскадно quarantines dependent bundles: invalid program version → sessions,
що на неї посилаються → recommendations, що посилаються на ці facts.
Closure обчислюється детерміновано до fixed point.

Set без валідної session, session без валідної program version або
recommendation з required evidence reference на відсутній/quarantined fact
не може бути accepted.

### 10.4 Quarantine artifact

Quarantine не копіює й не редагує raw snapshot. Він створює private immutable
reference artifact:

```text
data/quarantine/<snapshot-id>/<normalizer-version>/
├── manifest.json
├── bundles.jsonl
└── COMPLETE
```

Кожен record містить deterministic `quarantine_bundle_id`, source row
references, stable ID якщо його вдалося прочитати, reason codes і dependency
closure. Повні raw values SHOULD залишатися лише в snapshot; diagnostics
посилаються на них. Quarantine files є personal data, мають mode `0600`,
виключаються з Git та керуються security retention policy.

### 10.5 Fail-closed promotion policy

V1 не підтримує `--allow-partial`. Якщо snapshot має `fatal` або хоча б один
bundle має `error`:

- raw snapshot і quarantine зберігаються;
- accepted/rejected counts входять в audit;
- normalized accepted bundles MAY бути збережені для diagnosis;
- SQLite current/history/source observations не змінюються;
- `mirror_head` не просувається;
- run завершується `VALIDATION_QUARANTINED`.

При `fatal` accepted staging не публікується; quarantine/diagnostic artifact
MAY містити snapshot-level synthetic bundle для traceability. Це правило не
дозволяє помилково створити tombstones через rejected або непрочитані rows.
`warning`/`info` без `fatal`/`error` не блокують promotion.

## 11. Pure versioned normalization і staging

Normalization визначається як чиста функція:

`snapshot payload + schema_version + normalizer_version + semantic_config`
→ `canonical entities + diagnostics`.

Вона MUST:

- не робити network, clock або SQLite-current reads;
- не залежати від process locale, hash seed або input row order;
- використовувати explicit spreadsheet locale/timezone;
- нормалізувати Unicode, dates, decimals, units, enums і exercise aliases
  лише за versioned rules;
- зберігати `null` як unknown;
- сортувати output за entity type і stable ID;
- відокремлювати logical payload від source location;
- перевіряти canonical models через Pydantic boundary;
- давати byte-identical canonical staging для однакових inputs і versions.

Зміна normalization semantics вимагає нового `normalizer_version`. Зміна
лише implementation без зміни output MAY зберегти version, але regression
fixtures мають довести тотожність.

Staging layout:

```text
data/processed/staging/<snapshot-id>/<normalizer-version>/<config-fingerprint>/
├── entities/
│   ├── program-versions.jsonl
│   ├── program-items.jsonl
│   ├── sessions.jsonl
│   ├── sets.jsonl
│   └── recommendations.jsonl
├── diagnostics.jsonl
├── staging-manifest.json
└── COMPLETE
```

`normalization_fingerprint` є SHA-256 canonical ordered entity files,
diagnostics і semantic versions. Manifest містить raw/accepted/rejected/
ignored counts та file hashes. Entirely blank source rows є `ignored`, не
entities. Staging publication використовує той самий temp → hash → COMPLETE
→ atomic rename pattern, що й raw snapshot.

Якщо `mirror_head` уже має той самий `snapshot_id`, `schema_version`,
`normalizer_version`, `semantic_config_fingerprint` і
`normalization_fingerprint`, run MAY застосувати verified no-op fast path.

## 12. Reconciliation та SQLite mirror

### 12.1 Logical comparison

Для кожної entity обчислюється `logical_payload_sha256` лише з canonical
business fields. Окремий `source_payload_sha256` доводить exact source
revision за `DATA_MODEL.md`. Із logical hash виключаються:

- source row number і A1 location;
- `run_id`, timestamps pull/commit;
- snapshot path;
- log/audit metadata.

Тому sort або move row створює нове source observation, але не logical
`UPDATE`.

Staging порівнюється з current state за `(entity_type, stable_id)`, а source
revision rules перевіряються до logical diff:

| Стан | Logical operation |
|---|---|
| ID відсутній у current, присутній у staging | `INSERT` або `RESTORE` після tombstone |
| ID є в обох, logical payload hash однаковий | `UNCHANGED` |
| ID є в обох, revision більший і logical payload hash різний | `UPDATE` |
| ID є в current, відсутній у повному staging | `DELETE` + tombstone |

Source observations зберігають `snapshot_id`, entity ID, tab/sheet ID і row
reference окремо від logical history.

### 12.2 Current і history

SQLite MUST мати:

- current tables з максимум однією live row на stable ID;
- append-only history events або equivalently immutable revisions;
- tombstone history event для delete;
- source observations;
- `sync_runs`;
- singleton `mirror_head`.

Deterministic history event ID MUST включати entity type, stable ID,
source revision або tombstone marker, snapshot ID, operation/change kind і
source і logical payload hashes. Unique constraint робить повтор того самого
promotion безпечним.

History change kind має відрізняти source correction від local
reinterpretation після зміни schema/normalizer/config. Old history payload
не переписується. Current tables містять лише live entities; tombstone
залишається в history. Reappearance того самого stable ID створює `RESTORE`
і нову current row.

### 12.3 Atomic transaction

Після повної staging validation процес:

1. відкриває SQLite з foreign keys та очікуваним application/schema version;
2. починає write transaction, який не дозволяє другому writer;
3. повторно читає current `mirror_head` і звіряє його з head, від якого
   обчислено diff;
4. завантажує/перевіряє staging constraints;
5. додає history events і source observations;
6. застосовує current inserts/updates/deletes;
7. записує reconciled counts та durable run audit;
8. оновлює `mirror_head` **останньою логічною операцією того самого
   transaction**;
9. виконує commit.

`mirror_head` tuple містить щонайменше snapshot, schema, normalization і
semantic config fingerprints, mirror sequence та committed run ID.

Current, history, observations, run audit і head або стають видимими разом,
або не змінюються взагалі. Analytics і reports MUST читати лише tuple,
досяжний через committed `mirror_head`; staging чи failed run не є
queryable truth.

SQLite WAL дозволяє readers бачити попередній committed head під час
promotion. Reader, що потребує consistency між кількома queries, MUST
використовувати один read transaction.

## 13. Corrections, deletions і reorder

### Correction

Source row зі stable ID, що вже існує, більшим `source_revision` та зміненим
logical payload є correction. Зміна payload без increment revision є
quarantined identity conflict. Наступний successful pull:

- додає рівно одну immutable `UPDATE` revision/event;
- замінює current payload у transaction;
- зберігає lineage на old і new snapshots;
- не змінює old history.

Зміна stable ID не є correction: old ID tombstoned, new ID inserted. Для
виправлення помилково зміненого ID користувач має відновити original ID у
Google Sheets.

### Deletion

Відсутність stable ID створює tombstone лише якщо:

- capture coherent і має valid `COMPLETE`;
- усі чотири whole-tab ranges присутні;
- validation `fatal`/`error` count дорівнює zero;
- normalization і referential checks успішні;
- staging позначено complete.

Deletion у Google Sheets не видаляє raw snapshot або history. Повторний pull
того самого snapshot не створює другий tombstone.

### Reorder

Row reorder або sort змінює source observations і може створити новий raw
snapshot, але не змінює stable ID чи `logical_payload_sha256`. Audit має
показувати `logical_updates=0` і `logical_deletes=0`, якщо business values не
змінилися.

## 14. Partial failures та відновлення

| Failure point | Durable result | `mirror_head` |
|---|---|---|
| До lock/preflight | Санітизований failure audit, якщо storage доступний | Без змін |
| Під час capture або fence mismatch | Лише incomplete `.inflight`; не snapshot | Без змін |
| Після snapshot publication, до validation | Valid raw snapshot можна перевикористати | Без змін |
| Validation/quarantine error | Raw snapshot + quarantine + failed run audit | Без змін |
| Normalization/staging error | Raw snapshot; complete diagnostics якщо можливо | Без змін |
| До SQLite commit | Transaction rollback; staging залишається rebuildable | Без змін |
| Crash під час SQLite transaction | SQLite rollback/recovery | Старий або новий atomic head, ніколи проміжний |
| Commit result невідомий процесу | Новий run перевіряє target tuple та run ID у head | Визначається з DB, не з log |
| Після commit, до console summary | Durable run і head доводять success | Новий head |

Raw snapshot публікується до validation навмисно: invalid source також
потребує незмінного доказу. Але жодна failure path після publication не має
права частково просунути entities.

Якщо SQLite commit повернув ambiguous I/O outcome, процес MUST закрити й
відкрити DB, виконати integrity check і прочитати `mirror_head`:

- target tuple + committed run ID присутні → вважати commit успішним;
- старий head і clean DB → наступний run може повторити promotion;
- інший або inconsistent state → `SQLITE_TRANSACTION`, без автоматичного
  «ремонту».

## 15. Retry і backoff

Retry дозволений лише для:

- transport timeout/reset;
- HTTP `408`, `429`, `500`, `502`, `503`, `504`;
- одного credential refresh після initial `401`;
- profile-specific source fence mismatch.

HTTP `400`, повторний `401`, `403`, `404`, allowlist mismatch, schema/data
validation, identity conflict, snapshot hash mismatch і SQLite integrity
failure не retry-яться як transient.

Remote transient policy v1:

- максимум 5 complete capture attempts;
- exponential backoff з full jitter;
- base `1 s`, cap `30 s`;
- valid `Retry-After` поважається до cap `120 s`;
- кожен retry починається з нового profile fence (version-before в A або
  `capture_a` в B);
- максимум 3 із 5 attempts можуть завершитися саме fence mismatch.

Після вичерпання fence attempts повертається `SOURCE_CHANGED`; після інших
retryable remote failures — `REMOTE_RETRY_EXHAUSTED`. Retry count і sanitized
status class входять в audit, response body — ні.

SQLite `busy/locked` після local lock означає external writer або
довготривалий reader/checkpoint conflict. Реалізація MAY чекати configured
busy timeout до 5 секунд, але MUST завершитися `SQLITE_BUSY`, а не retry
loop без межі.

## 16. Audit, logs і redaction

### 16.1 Durable audit summary

Кожен run отримує random `run_id`, не похідний від personal data. Final
summary MUST містити:

- protocol/software/schema/normalization versions;
- `run_id`, `source_alias`, start/end UTC;
- result: `committed`, `noop` або `failed`;
- stable exit code і phase/reason code;
- snapshot ID, auth/coherence profile та його fence evidence, якщо capture
  відбувся;
- mirror head before/after;
- raw rows per tab;
- accepted, quarantined, ignored rows і bundles;
- logical inserts, updates, deletes, restores, unchanged;
- fatal/error/warning/info counts;
- retry counts і durations;
- normalization fingerprint, якщо staging завершено.

Counts мають арифметично узгоджуватися. Окремо рахуються source rows, bundles
та logical entities — їх не можна змішувати в одному полі.

### 16.2 Structured logs

Logs — UTF-8 JSON Lines з UTC timestamp, level, event code, phase, run ID,
source alias, safe object IDs, counts і duration. Exception text проходить
redaction до запису.

Logs MUST NOT містити:

- OAuth access/refresh token, authorization header, cookies або credential
  path;
- live Spreadsheet ID, URL, email чи user display name;
- cell values, notes, pain/recovery/health values або normalized payload;
- full request/response body;
- environment dump або SQLite row dump.

Допустимі canonical tab names, row references без values, stable reason codes,
counts, snapshot hash і domain stable IDs лише якщо security policy дозволяє
їх для local logs. За замовчуванням domain IDs у console хешуються або
пропускаються; повна діагностика доступна через protected quarantine
references.

Якщо required durable audit не можна записати до commit, promotion MUST
зупинитися. Failure зовнішнього console sink після успішного DB commit не
може перетворити committed transaction на нібито failed; істина визначається
`mirror_head` і `sync_runs`.

## 17. Stable CLI exit codes

Ці numbers заморожені для `sync-protocol-v1`; нові коди додаються без
перенумерації.

| Code | Symbol | Значення |
|---:|---|---|
| 0 | `OK` | Committed або verified no-op |
| 2 | `USAGE` | Некоректні CLI arguments |
| 10 | `CONFIG_OR_SECURITY` | Local config, scope, permission або version preflight |
| 11 | `LOCK_BUSY` | Інший sync writer тримає lock |
| 12 | `AUTH` | Credential/refresh failure |
| 13 | `SOURCE_ACCESS` | Allowlist, not found, trashed, MIME або permission |
| 14 | `SOURCE_CONTRACT` | Missing/duplicate tab/header/range або unsupported source schema |
| 15 | `SOURCE_CHANGED` | Source-version fence не стабілізувався |
| 16 | `REMOTE_RETRY_EXHAUSTED` | Retryable remote/transport failures вичерпано |
| 20 | `SNAPSHOT_INTEGRITY` | Hash, manifest, COMPLETE або atomic publication failure |
| 21 | `VALIDATION_QUARANTINED` | Snapshot має fatal або один чи більше bundles мають error |
| 22 | `NORMALIZATION_OR_STAGING` | Pure transform, canonical validation або staging publication failure |
| 30 | `SQLITE_COMPAT_OR_INTEGRITY` | DB version, migration, FK або integrity precheck |
| 31 | `SQLITE_BUSY` | Bounded DB busy timeout |
| 32 | `SQLITE_TRANSACTION` | Reconciliation, commit або ambiguous recovery failure |
| 40 | `LOCAL_IO_OR_AUDIT` | Private local storage/audit failure поза попередніми класами |
| 70 | `INTERNAL_INVARIANT` | Непередбачена bug/invariant violation |
| 130 | `INTERRUPTED` | Operator interrupt до підтвердженого commit |

Machine-readable final summary і process exit code MUST збігатися. Для
post-commit interrupt/process loss наступний run визначає результат з
durable head, а не припускає rollback.

## 18. Conformance invariants

Кожен пункт нижче MUST мати automated test. Посилання на invariant ID
використовується в test name або marker.

| ID | Перевірний інваріант |
|---|---|
| `SYNC-INV-001` | V1 client не може викликати remote method поза allowlist обраного profile; profile B не може викликати Drive. |
| `SYNC-INV-002` | Configured/requested OAuth scopes не містять write scope. |
| `SYNC-INV-003` | Неallowlisted Spreadsheet ID відхиляється до values read. |
| `SYNC-INV-004` | Два паралельні sync writers для одного mirror не проходять lock одночасно. |
| `SYNC-INV-005` | `LOCK_BUSY` run не робить remote calls і SQLite writes. |
| `SYNC-INV-006` | Missing, duplicate або renamed required tab завершує preflight з code 14. |
| `SYNC-INV-007` | Кожен complete Sheets capture використовує один values `batchGet` із рівно чотирма ordered ranges; profile A робить один, profile B — рівно два. |
| `SYNC-INV-008` | Різні A source versions або різні B logical raw fingerprints не створюють final snapshot. |
| `SYNC-INV-009` | Fence retry починає новий повний profile attempt, а не продовжує старий. |
| `SYNC-INV-010` | Final snapshot без valid `COMPLETE` ніколи не читається downstream. |
| `SYNC-INV-011` | Зміна одного byte payload робить snapshot integrity check failed. |
| `SYNC-INV-012` | Однаковий canonical capture descriptor дає однаковий `snapshot_id`. |
| `SYNC-INV-013` | Existing valid content-addressed snapshot повторно використовується без modification. |
| `SYNC-INV-014` | Raw payload зберігає unknown/blank значення без inference. |
| `SYNC-INV-015` | Однакові snapshot, schema, normalizer і semantic config дають byte-identical staging. |
| `SYNC-INV-016` | Clock, host locale і input row order не змінюють logical normalized payload. |
| `SYNC-INV-017` | Required missing stable ID створює error, а не row-position ID. |
| `SYNC-INV-018` | Duplicate stable ID, навіть з однаковими values, не collapse мовчки. |
| `SYNC-INV-019` | Invalid set quarantines parent session bundle і всі sibling sets. |
| `SYNC-INV-020` | Invalid program version каскадно quarantines dependent sessions. |
| `SYNC-INV-021` | Set без accepted session не може потрапити в staging accepted set. |
| `SYNC-INV-022` | Будь-який fatal/error залишає current/history/observations/head byte-for-byte логічно незміненими. |
| `SYNC-INV-023` | Warning/info-only snapshot може пройти promotion, а diagnostics зберігаються в audit. |
| `SYNC-INV-024` | Reorder rows без business changes дає zero logical inserts/updates/deletes. |
| `SYNC-INV-025` | Повторний promotion того самого head tuple не додає history events. |
| `SYNC-INV-026` | Correction під тим самим stable ID додає рівно один UPDATE event і зберігає old revision. |
| `SYNC-INV-027` | Зникнення ID з complete fatal/error-free snapshot додає рівно один tombstone. |
| `SYNC-INV-028` | Зникнення ID з incomplete або fatal/error snapshot не створює tombstone. |
| `SYNC-INV-029` | Reappearance tombstoned ID створює RESTORE і одну live current row. |
| `SYNC-INV-030` | Зміна stable ID моделюється як DELETE old + INSERT new, не UPDATE. |
| `SYNC-INV-031` | Current/history/observations/run audit/head змінюються одним SQLite transaction. |
| `SYNC-INV-032` | Injected failure перед commit залишає попередній head і current state. |
| `SYNC-INV-033` | Reader бачить або весь old head, або весь new head, ніколи суміш. |
| `SYNC-INV-034` | `mirror_head` ніколи не посилається на snapshot без valid COMPLETE/hash chain. |
| `SYNC-INV-035` | History event deterministic unique key запобігає duplicate event після retry. |
| `SYNC-INV-036` | Raw rows = accepted rows + quarantined rows + ignored blank rows для кожної вкладки. |
| `SYNC-INV-037` | Structured logs проходять fixture scan без tokens, live source ID і cell values. |
| `SYNC-INV-038` | HTTP 400/403/404 і validation errors не запускають transient retry. |
| `SYNC-INV-039` | HTTP 429/5xx retry не перевищує attempt/backoff limits. |
| `SYNC-INV-040` | Після ambiguous commit recovery результат визначається target tuple у DB, не останнім log event. |
| `SYNC-INV-041` | Machine summary `exit_code` дорівнює process exit code для всіх normal failure paths. |
| `SYNC-INV-042` | Failed validation зберігає valid raw snapshot і quarantine, але не staging як queryable truth. |

Мінімальний acceptance suite додатково має включати fixtures для: empty
required tab, Unicode header drift, locale decimal/date parsing, orphan set,
duplicate IDs, source correction, source deletion, full row reorder, fence
mismatch, crash у кожній publication/transaction boundary та log-redaction
canary values.

## 19. V2: справді атомарний source capture — не частина v1

Google Sheets v1 flow не блокує user edits і не має provider-guaranteed
snapshot transaction, що pin-ить кілька API reads до однієї immutable
revision. Version fence лише **виявляє** server-recorded concurrent changes і
повторює capture.

V2 MAY замінити fence на revision-addressable atomic source, але лише якщо
обраний механізм доводить усі властивості:

1. усі чотири tabs читаються з одного immutable revision ID;
2. revision ID входить у snapshot manifest і перевіряється при повторному
   download;
3. capture не залежить від row order або live mutable head;
4. scope expansion і будь-який server-side copy/export проходять окремий
   security review та ADR;
5. v1 read-only client не отримує write methods «про запас».

Можливі design investigations: provider-supported pinned revision export або
producer-created immutable export artifact. Жоден із них не вважається
прийнятим рішенням цим документом. До окремого ADR реалізація MUST
використовувати v1 multi-range read + source-version fence.

## 20. API assumptions

API assumptions перевірені за official Google documentation:

- [`spreadsheets.values.batchGet`](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/batchGet)
  повертає кілька ranges у requested order;
- [Sheets OAuth scopes](https://developers.google.com/workspace/sheets/api/scopes)
  містять `spreadsheets.readonly`;
- лише для optional profile A:
  [`Drive files.get`](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/get)
  підтримує `drive.metadata.readonly`, а
  [Drive File resource](https://developers.google.com/workspace/drive/api/reference/rest/v3/files)
  визначає output-only monotonically increasing `version` і `modifiedTime`.

Profile B не припускає undocumented Sheets revision token: він порівнює два
повні logical raw captures і тому є обов’язковим Drive-free baseline.

Зміна цих provider assumptions потребує protocol compatibility review,
оновлення conformance fixtures і, якщо змінюється гарантія coherence, нового
ADR.
