# Phase 1: Довірений контракт даних - Context

**Gathered:** 2026-07-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Реалізувати безпечне read-only підключення до одного явно налаштованого
Google Sheet та preflight, який до будь-якого імпорту перевіряє доступ,
структуру чотирьох authoritative вкладок і придатність source facts. Фаза
повертає redacted actionable diagnostics, але не зберігає source rows, не
створює stable IDs і нічого не записує назад у Google Sheets.

</domain>

<decisions>
## Implementation Decisions

### Підключення та авторизація
- Основний auth mode — viewer-only service account, якому надано доступ лише
  до цільової таблиці; desktop OAuth залишається documented fallback.
- Таблиця вибирається тільки через точний `WORKOUT_SHEET_ID` з локального
  environment; пошук за назвою або приймання live URL не підтримуються.
- Preflight до читання facts перевіряє exact spreadsheet ID, доступ,
  contract-relevant metadata та наявність усіх чотирьох вкладок.
- Помилка підключення працює fail closed, має стабільний error code і не
  підміняється cached snapshot.

### Виконання schema contract
- Headers мають точні українські назви й нормативний порядок; fuzzy matching,
  case folding або неявне перейменування заборонені.
- Невідома колонка є `fatal`, якщо її немає в explicit versioned
  alias/extension policy.
- Порожнє optional значення зберігається як `NULL` із відповідним diagnostic;
  defaults або inference не застосовуються.
- Відсутні source-owned stable IDs дають звіт про explicit one-time migration;
  v1 не генерує локальні тимчасові IDs і не змінює Sheet.

### CLI та diagnostics
- Canonical preflight command — `workout-tracker source check`; майбутня
  команда `pull` завжди запускає ту саму перевірку автоматично.
- За замовчуванням команда показує стислий human-readable результат і має
  стабільний machine-readable режим `--json`.
- Diagnostic містить tab, field, stable ID або безпечний row locator та
  стабільний code, але не містить raw personal value.
- CLI використовує стабільні exit-code categories для auth, remote, schema,
  validation та internal failures замість одного загального `1`.

### Конфігурація та перевірка
- Configuration precedence: CLI для non-secret overrides, потім environment,
  ignored `settings.yaml`, потім versioned defaults.
- Credentials читаються через ADC або `GOOGLE_APPLICATION_CREDENTIALS`;
  передавання secret JSON через CLI заборонене.
- Automated verification за замовчуванням використовує повністю offline
  fixtures; live smoke test є opt-in і не запускається у звичайному test suite.
- Phase 1 не зберігає source rows: дозволений лише redacted validation summary
  без credentials, Sheet locator або personal values.

### the agent's Discretion
- Вибір Python CLI framework, HTTP/client abstraction, internal module
  boundaries і presentation formatting, якщо вони зберігають наведені
  contracts та прийнятий Python/Pydantic stack.
- Точна кількість displayed diagnostics у human-readable режимі, якщо JSON
  output залишається повним, детермінованим і redacted.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `config/schema.yaml` уже є нормативним машинозчитуваним контрактом чотирьох
  вкладок і 152 source columns.
- `config/settings.example.yaml` та `.env.example` задають read-only auth і
  local configuration boundary.
- `docs/architecture/DATA_MODEL.md` і
  `docs/architecture/SYNC_PROTOCOL.md` визначають validation severity,
  error-code categories, stable IDs та preflight invariants.

### Established Patterns
- Runtime implementation ще відсутня; phase має створити Python package,
  dependency metadata, CLI boundary і перші automated tests.
- Google Sheets володіє operational facts, Git — schema/rules, а unknown
  завжди залишається `NULL`.
- Human-facing prose українська; code identifiers, CLI names і stable codes
  англійські.

### Integration Points
- CLI entry point `workout-tracker` і майбутній `src/.../source` boundary.
- Google Sheets API adapter із viewer-only service-account та desktop OAuth
  implementations.
- Pydantic models, що компілюються з або перевіряються проти
  `config/schema.yaml`.
- Phase 2 повторно використовуватиме preflight як обов’язкову першу стадію
  `pull`.

</code_context>

<specifics>
## Specific Ideas

CLI повинен одразу пояснювати, чи проблема в auth, remote availability,
структурі Sheet або конкретному source record, не розкриваючи значення самого
record. Offline fixtures мають охопити Unicode header drift, відсутню вкладку,
unknown column, missing stable ID, unsupported workout type та program-version
link failure.

</specifics>

<deferred>
## Deferred Ideas

- Immutable raw snapshots, SQLite promotion та cached mirror належать Phase 2.
- Analytics, reports, backup restore і history remediation виконуються у
  відповідних наступних фазах.
- Capture, write-back та generated recommendations залишаються v2.

</deferred>
