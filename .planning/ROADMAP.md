# Roadmap: Workout Tracker

## Overview

Milestone спочатку робить Google Spreadsheet корисним самостійним продуктом із чотирма програмами, потім додає контрольований ChatGPT capture/write-back, coherent local mirror і спільну evidence-backed аналітику, рекомендації з explicit owner decision, а завершується privacy та verified restore gates. Кожна phase дає завершену observable capability; внутрішні layers не винесені в окремі горизонтальні phases.

## Phases

- [ ] **Phase 1: Standalone Workbook and Four Programs** - Користувач отримує ідемпотентно створений mobile-friendly workbook із чотирма комплексами, formulas і dashboard.
- [ ] **Phase 2: Controlled ChatGPT Workout Capture** - Користувач перетворює natural-language workout note на preview і лише після confirmation атомарно записує allowlisted bundle.
- [ ] **Phase 3: Coherent Mirror and Evidence-Backed Analytics** - Користувач читає фільтровану історію та однакові traceable metrics із dashboard і ChatGPT без ризику partial mirror.
- [ ] **Phase 4: Recommendations and Explicit Program Decisions** - Користувач бачить deterministic progression окремо від evidence-backed recommendation і сам вирішує, чи змінювати програму.
- [ ] **Phase 5: Privacy and Verified Recovery Gates** - Продукт проходить repository privacy checks і доводить portable isolated restore перед release.

## Phase Details

### Phase 1: Standalone Workbook and Four Programs
**Goal**: Користувач може планувати, вводити й переглядати тренування у самодостатньому Google Spreadsheet із чотирма точними versioned complexes.
**Depends on**: Nothing (first phase)
**Requirements**: REQ-WBK-01, REQ-WBK-02, REQ-WBK-03, REQ-WBK-04, REQ-WBK-05
**Success Criteria** (what must be TRUE):
  1. На чистому Spreadsheet setup створює рівно сім вкладок із точними українськими labels і завантажує всі чотири versioned complexes зі збереженими paired-set, reps, RIR, rest та equipment semantics.
  2. Користувач може з телефона знайти сьогоднішній комплекс і внести workout facts через validated, hinted і formatted input fields, не редагуючи protected formula/system columns.
  3. Formulas і dashboard показують лише contract-defined metrics; missing або incomparable input видно як explicit status і `NULL`, а не zero.
  4. Повторний setup не створює duplicate tabs, named ranges, formulas чи program items і не змінює logical workbook content.
**Plans**: TBD
**UI hint**: yes

### Phase 2: Controlled ChatGPT Workout Capture
**Goal**: Користувач може безпечно додати описане природною мовою тренування через preview, explicit confirmation та atomic idempotent write.
**Depends on**: Phase 1
**Requirements**: REQ-CAP-01, REQ-CAP-02, REQ-CAP-03, REQ-CAP-04, REQ-CAP-05, REQ-CAP-06, REQ-SAFE-02, REQ-SAFE-05
**Success Criteria** (what must be TRUE):
  1. User-authored workout note перетворюється на normalized session/set preview із warnings; неоднозначні критичні поля запитуються, а дозволені unknown залишаються `NULL`.
  2. Користувач може виправити preview до confirmation, і unconfirmed, stale, incomplete або invalid payload не змінює Spreadsheet.
  3. Після explicit confirmation valid session і child sets додаються як один logical bundle зі stable IDs, `program_version_id` та contract/version preconditions.
  4. Replay, timeout або retry з тим самим idempotency key повертає original result без duplicate rows; arbitrary або non-allowlisted mutation відхиляється до запису.
  5. Successful і failed attempts залишають traceable redacted audit, а model payload містить лише minimum context поточного запиту без credentials, live locators, bulk history чи unrelated health context.
**Plans**: TBD

### Phase 3: Coherent Mirror and Evidence-Backed Analytics
**Goal**: Користувач може надійно запитувати history та metrics, відтворені з coherent authoritative snapshot і однакових versioned semantics.
**Depends on**: Phase 2
**Requirements**: REQ-ANL-01, REQ-ANL-02, REQ-ANL-03, REQ-ANL-04, REQ-ANL-05, REQ-SAFE-03
**Success Criteria** (what must be TRUE):
  1. Read-only pull захоплює `Програма`, `Сесії`, `Підходи` і `Рекомендації` як один version-fenced immutable snapshot; partial або failed capture залишає попередній complete mirror active.
  2. Користувач може одночасно фільтрувати history за workout type, exercise, program version і date range та отримує лише matching records.
  3. Working volume, load, e1RM, RIR, rest і recovery summaries відтворюються з pinned formula/ruleset versions; warm-ups та invalid/aborted sets не потрапляють у working metrics.
  4. Incomparable variant, equipment, load basis, assistance semantics або cohort виключається з explicit status, а кожен result має version і evidence locator до source-owned IDs.
  5. Для однакових eligible inputs і versions dashboard та ChatGPT query повертають семантично однакові values/status.
**Plans**: TBD
**UI hint**: yes

### Phase 4: Recommendations and Explicit Program Decisions
**Goal**: Користувач може оцінити evidence-backed progression/recommendation output і явно прийняти або відхилити program change без автоматичної mutation.
**Depends on**: Phase 3
**Requirements**: REQ-REC-01, REQ-REC-02, REQ-REC-03, REQ-REC-04, REQ-REC-05
**Success Criteria** (what must be TRUE):
  1. Користувач чітко бачить, де deterministic progression rule result, а де AI-generated recommendation; одне не маскується під інше.
  2. Кожна recommendation має stable `recommendation_id`, created time, evidence window, rationale, confidence/limitations і lifecycle status.
  3. Недостатній або incomparable evidence повертає explicit `insufficient_evidence`/refusal без fabricated change.
  4. Перегляд recommendation не змінює active prescription; program change можливий лише після explicit owner approval із новою `program_version_id`.
  5. Recovery output описує self-reported context без diagnosis чи causal medical conclusion та направляє acute, severe або persistent symptoms до qualified professional.
**Plans**: TBD

### Phase 5: Privacy and Verified Recovery Gates
**Goal**: Власник може випустити й відновити продукт, маючи перевірене підтвердження, що sensitive data не потрапили в repository, а authoritative і local state є portable.
**Depends on**: Phase 4
**Requirements**: REQ-SAFE-01, REQ-SAFE-04
**Success Criteria** (what must be TRUE):
  1. Tracked artifacts і generated documentation проходять privacy/secret scan без credentials, live Sheet locators, personal exports, SQLite, reports, logs або backups.
  2. Portable backup містить workbook data, program versions, required contract/version metadata та local analytical reconstruction evidence з перевірюваними manifest hashes/counts.
  3. Offline isolated restore відбудовує operational records і fresh SQLite mirror; integrity/foreign-key checks та manifest counts/hashes збігаються.
  4. Неповний або невірний restore не публікується як active state, а попередня працездатна система лишається доступною.
**Plans**: TBD

## Coverage

| Phase | Requirements | Count |
|-------|--------------|------:|
| 1. Standalone Workbook and Four Programs | REQ-WBK-01–05 | 5 |
| 2. Controlled ChatGPT Workout Capture | REQ-CAP-01–06, REQ-SAFE-02, REQ-SAFE-05 | 8 |
| 3. Coherent Mirror and Evidence-Backed Analytics | REQ-ANL-01–05, REQ-SAFE-03 | 6 |
| 4. Recommendations and Explicit Program Decisions | REQ-REC-01–05 | 5 |
| 5. Privacy and Verified Recovery Gates | REQ-SAFE-01, REQ-SAFE-04 | 2 |
| **Total** | **Every v1 requirement exactly once** | **26** |

## Progress

**Execution Order:** Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Standalone Workbook and Four Programs | 0/TBD | Not started | - |
| 2. Controlled ChatGPT Workout Capture | 0/TBD | Not started | - |
| 3. Coherent Mirror and Evidence-Backed Analytics | 0/TBD | Not started | - |
| 4. Recommendations and Explicit Program Decisions | 0/TBD | Not started | - |
| 5. Privacy and Verified Recovery Gates | 0/TBD | Not started | - |
