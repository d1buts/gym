# Requirements: Workout Tracker

**Defined:** 2026-07-24

**Core Value:** Одна повторювана CLI-команда перетворює всі авторитетні факти з Google Sheets на валідовані, ідемпотентні локальні дані та відтворюваний звіт із простежуваними доказами.

## Classification Boundary

Нижче як v1 requirements наведено лише атомарні, перевірні можливості, які може спостерігати користувач. Runtime, library choices, schema details, privacy rules, evidence thresholds і medical boundaries залишаються technical/domain constraints у `PROJECT.md`; вони не підміняють product requirements. Вимоги виведено з source architecture та version-one quality bar, оскільки ingest-корпус містив 0 `PRD`.

## v1 Requirements

### Source Connection and Validation

- [ ] **SRC-01**: Користувач може через локальну конфігурацію під’єднати цільовий Google Sheet і перевірити доступ до нього.
- [ ] **SRC-02**: Користувач може до імпорту перевірити наявність вкладок
  `Програма`, `Сесії`, `Підходи` і `Рекомендації`, їхні headers, field types,
  units, stable IDs та program-version links.
- [ ] **SRC-03**: Користувач отримує validation error, якщо program або session data містять workout type поза `Верх — сила`, `Низ — сила`, `Верх — гіпертрофія` і `Низ — гіпертрофія`.
- [ ] **SRC-04**: Користувач бачить row-level причину для invalid або critical missing data, а невідомі значення залишаються порожніми й не вигадуються.

### Idempotent Synchronization

- [ ] **SYNC-01**: Користувач може виконати pull authoritative tabs `Програма`, `Сесії`, `Підходи` і `Рекомендації` та отримати immutable raw snapshot із timestamp і source fingerprint.
- [ ] **SYNC-02**: Користувач отримує в SQLite normalized current projection
  та immutable revision history для program items, sessions, sets і
  recommendations зі збереженими foreign-key relationships.
- [ ] **SYNC-03**: Користувач може повторити pull незміненого, відсортованого або переміщеного Sheet без дублювання sessions, sets чи інших логічних записів.
- [ ] **SYNC-04**: Після кожного pull користувач отримує audit summary із snapshot ID, accepted/rejected counts, inserts/updates і validation failures.
- [ ] **SYNC-05**: Користувач може виконувати v1 pull і локальну обробку без зміни primary workout facts у Google Sheets.

### History and Metrics

- [ ] **HIST-01**: Користувач може запитати історію sessions за workout type і date range.
- [ ] **HIST-02**: Користувач може запитати історію конкретної exercise з пов’язаними session та set facts.
- [ ] **METR-01**: Користувач може розрахувати training volume за session, exercise, muscle group і time window.
- [ ] **METR-02**: Користувач може переглянути maximum working load та e1RM progression із явно визначеною formula.
- [ ] **METR-03**: Користувач може переглянути RIR і rest summaries та trends для вибраної exercise або workout type.
- [ ] **METR-04**: Користувач може зіставити performance trends із наявними sleep, energy, stress, soreness і subjective performance data та бачить, де цих даних бракує.

### Reproducible Evidence Report

- [ ] **RPRT-01**: Користувач може однією documented top-level CLI-командою виконати validated pull, оновити локальні дані й створити progress report без ручного копіювання.
- [ ] **RPRT-02**: Користувач отримує report із session count, volume, maximum load, e1RM, RIR, rest і recovery trends для вибраного періоду або scope.
- [ ] **RPRT-03**: Повторний запуск із тим самим input snapshot, parameters, config і formula version дає той самий substantive report.
- [ ] **RPRT-04**: Користувач може для кожної report metric або conclusion простежити raw snapshot, source tab, session/set IDs, parameters і calculation evidence.

### Privacy, Backup, and Restore

- [ ] **PRIV-01**: Користувач може запустити repository safety check для index
  і full history, довести відсутність нових secrets/personal artifacts та
  отримати явний failure, доки known public-history disclosure не має
  owner-approved disposition; `.gsheet` не приймається як analytics input
  або durable backup.
- [ ] **BKUP-01**: Користувач може створити timestamped portable backup усіх authoritative tabs із manifest та integrity metadata, окремо від working cache.
- [ ] **BKUP-02**: Користувач може відновити backup в isolated location, перебудувати queryable local data й отримати доказ відповідності очікуваних tabs, stable IDs, row counts та integrity checks.

## v2 Requirements

Deferred capabilities не входять до поточного roadmap.

### Workout Capture and Controlled Write-Back

- **CAPT-01**: Користувач може передати workout через ChatGPT або phone workflow, отримати перевірку одного з чотирьох workout types і уточнення critical missing values.
- **CAPT-02**: Користувач може одним підтвердженим записом створити stable session ID, одну session row і відповідні set rows без вигаданих даних.
- **WBCK-01**: Користувач може явно записати назад лише new recommendation rows, predefined calculated fields і optional last-sync status.

### Recommendation Engine

- **RECO-01**: Користувач може отримати deterministic double-progression step після одного повністю qualifying performance з target RIR, stable technique і без збільшення pain.
- **RECO-02**: Користувач отримує analytical program-change recommendation лише після щонайменше трьох exercise performances, а trend conclusion — приблизно після 6–8 occurrences відповідного workout type.
- **RECO-03**: Користувач бачить для кожної substantive recommendation signal, concrete evidence, confidence, review date і результат наступної перевірки.
- **RECO-04**: Користувач отримує пропозицію додати sets лише за stable recovery і доброї переносимості поточного volume.

### Advanced Coach and Interfaces

- **COACH-01**: Користувач може отримати evidence-backed long-term analysis, next-load forecast, plateau та accumulated-fatigue signals.
- **COACH-02**: Користувач може отримати пояснену пропозицію exercise substitution або next-session plan на основі підтвердженого обладнання й історії.
- **INTF-01**: Користувач може працювати через окремий Telegram bot, mobile app, web interface, voice input або wearable integration.
- **PLAT-01**: Після появи multiple users, authentication або складнішого API система може мігрувати primary store до PostgreSQL чи Supabase, зберігши Google Sheets як administrative або backup access channel.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Silent або bulk automatic mutation primary workout records | Суперечить authoritative-data policy; навіть майбутній write-back потребує дозволеного scope й explicit confirmation. |
| Заміна Google Sheets як authoritative store у v1 | PostgreSQL/Supabase migration відкладена до появи multiple users, authentication або складнішого API. |
| Медичний діагноз, призначення лікування, dosage advice для ліків або nutrition advice при виражених симптомах | Потребує кваліфікованого medical professional, а risk flags не є діагнозом. |
| `.gsheet` як analytics input або durable backup | Це посилання на online document, а не повна diffable data copy. |
| Зберігання API keys, OAuth tokens, populated `.env` чи персональних exports/backups у Git | Порушує secret and privacy boundary навіть у private repository. |
| Автоматичне перетворення paired-set програми на full circuit | Systemic/cardiorespiratory fatigue може стати лімітом для heavy sets; current program rules це виключають. |
| Exercise або program advice, що припускає непідтверджене обладнання | Source catalog навмисно не домислює EZ-bar, landmine, sled, GHD, dedicated leg machines, dip bars, rings, bands або ankle cuff. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SRC-01 | Phase 1 | Pending |
| SRC-02 | Phase 1 | Pending |
| SRC-03 | Phase 1 | Pending |
| SRC-04 | Phase 1 | Pending |
| SYNC-01 | Phase 2 | Pending |
| SYNC-02 | Phase 2 | Pending |
| SYNC-03 | Phase 2 | Pending |
| SYNC-04 | Phase 2 | Pending |
| SYNC-05 | Phase 2 | Pending |
| HIST-01 | Phase 3 | Pending |
| HIST-02 | Phase 3 | Pending |
| METR-01 | Phase 3 | Pending |
| METR-02 | Phase 3 | Pending |
| METR-03 | Phase 3 | Pending |
| METR-04 | Phase 3 | Pending |
| RPRT-01 | Phase 4 | Pending |
| RPRT-02 | Phase 4 | Pending |
| RPRT-03 | Phase 4 | Pending |
| RPRT-04 | Phase 4 | Pending |
| PRIV-01 | Phase 5 | Pending |
| BKUP-01 | Phase 5 | Pending |
| BKUP-02 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0 ✓

---
*Requirements defined: 2026-07-24*
*Last updated: 2026-07-24 after roadmap traceability mapping*
