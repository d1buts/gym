# Roadmap: Workout Tracker

## Overview

Roadmap послідовно створює довіру до даних: спочатку користувач перевіряє Google Sheets contract, потім отримує ідемпотентне SQLite-дзеркало, використовує його для історії та метрик, формує відтворюваний evidence-backed report і завершує v1 перевіркою privacy та реального backup restore. Кожна фаза дає завершену, спостережувану можливість і розширює попередню без зміни authoritative facts.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): запланована milestone-робота
- Decimal phases (2.1, 2.2): термінові вставки, позначені `INSERTED`

- [ ] **Phase 1: Довірений контракт даних** - Користувач може безпечно під’єднати й перевірити authoritative Google Sheet до імпорту.
- [ ] **Phase 2: Ідемпотентне локальне дзеркало** - Користувач отримує повний, нормалізований та audit-ready SQLite mirror без дублікатів.
- [ ] **Phase 3: Історія та базова аналітика** - Користувач може запитувати тренувальну історію й отримувати перевірні progress metrics.
- [ ] **Phase 4: Відтворюваний звіт із доказами** - Одна команда створює однаковий substantive report із повною evidence lineage.
- [ ] **Phase 5: Приватність і перевірене відновлення** - Користувач доводить Git safety та здатність backup відновити повний локальний стан.

## Phase Details

### Phase 1: Довірений контракт даних
**Goal**: Користувач може безпечно під’єднати authoritative Google Sheet і до імпорту зрозуміти, чи придатні його структура та факти.
**Mode:** standard
**Depends on**: Nothing (first phase)
**Requirements**: SRC-01, SRC-02, SRC-03, SRC-04
**Success Criteria** (what must be TRUE):
  1. Користувач налаштовує локальне підключення й отримує однозначний результат перевірки доступу до потрібного Google Sheet.
  2. Preflight перевіряє вкладки `Програма`, `Сесії`, `Підходи`,
     `Рекомендації`, їхні headers, field types, units, source-owned stable IDs,
     program-version links і чотири canonical workout types до прийняття
     даних.
  3. Користувач отримує actionable row-level diagnostics для invalid або critical missing values; система не домислює відсутні факти.
**Plans**: TBD

### Phase 2: Ідемпотентне локальне дзеркало
**Goal**: Користувач може повторювано отримати в SQLite точне локальне дзеркало всіх authoritative training facts.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: SYNC-01, SYNC-02, SYNC-03, SYNC-04, SYNC-05
**Success Criteria** (what must be TRUE):
  1. Один pull читає `Програма`, `Сесії`, `Підходи` і `Рекомендації` та зберігає immutable raw snapshot із timestamp і fingerprint.
  2. SQLite містить normalized current projection та immutable revision
     history, а кожен set пов’язаний зі своєю session і program version.
  3. Повторний pull незмінених, відсортованих або переміщених rows дає той
     самий logical fingerprint; corrections створюють одну revision, а
     coherent disappearances — один tombstone.
  4. Користувач бачить audit summary прийнятих, відхилених, inserted та updated records, а primary Google Sheets facts залишаються незміненими.
**Plans**: TBD

### Phase 3: Історія та базова аналітика
**Goal**: Користувач може відповідати на питання про історію та прогрес без ручного перегляду чи копіювання Google Sheets.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: HIST-01, HIST-02, METR-01, METR-02, METR-03, METR-04
**Success Criteria** (what must be TRUE):
  1. Користувач запитує sessions за workout type/date range та повну історію exercise з пов’язаними set facts.
  2. Користувач окремо отримує working-set, rep і eligible load volume,
     maximum comparable load та `epley-v1` e1RM progression; incomparable або
     missing inputs мають explicit status/exclusion reason.
  3. Користувач бачить RIR і rest trends разом із наявним sleep, energy, stress, soreness та subjective performance context.
  4. Порівняння performance і recovery trends явно показує відсутні sleep, energy, stress, soreness або subjective-performance inputs, щоб неповний context не подавався як достовірний зв’язок.
**Plans**: TBD

### Phase 4: Відтворюваний звіт із доказами
**Goal**: Користувач може однією повторюваною командою перейти від validated Google Sheets facts до доказового progress report.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: RPRT-01, RPRT-02, RPRT-03, RPRT-04
**Success Criteria** (what must be TRUE):
  1. Одна documented top-level CLI-команда виконує validated pull, оновлює local store і створює report без manual copying.
  2. Report охоплює session count, volume, maximum load, e1RM, RIR, rest і recovery trends для обраного period або scope.
  3. Незмінні snapshot, parameters, config і formula version створюють той самий substantive report при повторному запуску.
  4. Для кожної metric або conclusion користувач може простежити raw snapshot, source tab, session/set IDs, parameters і calculation evidence.
**Plans**: TBD

### Phase 5: Приватність і перевірене відновлення
**Goal**: Користувач може довести, що локальний workflow не витікає в Git і що backup справді відновлює queryable data.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: PRIV-01, BKUP-01, BKUP-02
**Success Criteria** (what must be TRUE):
  1. Repository safety check охоплює index і full history, не допускає нових
     secrets/personal artifacts та не проходить, доки known public-history
     disclosure не отримав owner-approved disposition; `.gsheet`
     відхиляється як input або durable backup.
  2. Користувач створює encrypted timestamped portable backup із manifest та
     integrity metadata в межах RPO ≤24 hours і retention 35 daily + 12
     month-end copies.
  3. Backup відновлюється в isolated location у queryable local data з очікуваними tabs, stable IDs і row counts.
  4. Щонайменше weekly restore verification видає повторюваний доказ
     integrity checks і чітко завершується помилкою при неповній або зміненій
     backup-копії.
**Plans**: TBD

## Progress

**Execution Order:** Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Довірений контракт даних | 0/TBD | Not started | - |
| 2. Ідемпотентне локальне дзеркало | 0/TBD | Not started | - |
| 3. Історія та базова аналітика | 0/TBD | Not started | - |
| 4. Відтворюваний звіт із доказами | 0/TBD | Not started | - |
| 5. Приватність і перевірене відновлення | 0/TBD | Not started | - |
