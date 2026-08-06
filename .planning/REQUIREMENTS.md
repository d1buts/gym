# Requirements: Workout Tracker

**Defined:** 2026-07-25
**Core Value:** Повний цикл «план → тренування → capture → verification → analysis → recommendation → explicit user decision» працює без прихованої ручної обробки, а кожен результат можна простежити до авторитетних фактів і версійованих правил.

## v1 Requirements

### Workbook

- [ ] **REQ-WBK-01**: Workbook має рівно сім вкладок: `Старт`, `Програма`, `Сесії`, `Підходи`, `Рекомендації`, `Довідники`, `Дашборд`.
- [ ] **REQ-WBK-02**: `Програма` містить чотири версійовані комплекси з repository specifications без втрати paired-set, reps, RIR, rest і equipment semantics.
- [ ] **REQ-WBK-03**: Input fields мають validation, hints, formats і mobile-friendly порядок, а formula/system columns захищені.
- [ ] **REQ-WBK-04**: Formulas і dashboard показують лише визначені metric contracts та явно відображають missing/incomparable status замість вигаданого zero.
- [ ] **REQ-WBK-05**: Повторний setup не дублює tabs, formulas, named ranges або program items і не змінює logical content.

### ChatGPT Capture

- [ ] **REQ-CAP-01**: Користувач може описати виконане тренування природною мовою та отримати session/set preview.
- [ ] **REQ-CAP-02**: Система запитує критичні уточнення або зберігає дозволене unknown як `NULL`; invalid critical omissions fail closed.
- [ ] **REQ-CAP-03**: До запису користувач бачить normalized preview сесії, підходів і warnings та може виправити неоднозначні поля.
- [ ] **REQ-CAP-04**: `commit_workout` працює лише після explicit confirmation і додає valid session/set bundle атомарно.
- [ ] **REQ-CAP-05**: Stable IDs та idempotency key повертають той самий result без duplicate rows під час repeat, timeout або retry.
- [ ] **REQ-CAP-06**: Writer не має arbitrary cell/range mutation, приймає лише allowlisted fields і відхиляє неallowlisted operation до mutation.

### Reading and Analytics

- [ ] **REQ-ANL-01**: Користувач може фільтрувати історію одночасно за workout type, exercise, program version і date range.
- [ ] **REQ-ANL-02**: Working volume, load, e1RM, RIR, rest і recovery summaries відтворюються з pinned formula/ruleset versions.
- [ ] **REQ-ANL-03**: Variant, equipment, load basis, assistance semantics і comparison cohort перевіряються до порівняння, а exclusions пояснюються status.
- [ ] **REQ-ANL-04**: Кожен analytical result містить formula/ruleset version, status і evidence locator до source-owned IDs без raw sensitive payload.
- [ ] **REQ-ANL-05**: Dashboard і ChatGPT query tools повертають семантично однакові values/status для однакових eligible inputs і versions.

### Recommendations

- [ ] **REQ-REC-01**: Deterministic progression result візуально й структурно відокремлений від AI-generated recommendation.
- [ ] **REQ-REC-02**: Recommendation містить `recommendation_id`, created time, evidence window, rationale, confidence/limitations і status.
- [ ] **REQ-REC-03**: Недостатні або непорівнювані дані повертають `insufficient_evidence` або відмову, а не вигадану пораду.
- [ ] **REQ-REC-04**: Recommendation не змінює prescription без explicit owner approval та нової `program_version_id`.
- [ ] **REQ-REC-05**: Recovery output є descriptive, не ставить diagnosis, не робить causal medical conclusion і routes acute/severe/persistent symptoms до qualified professional.

### Privacy, Audit and Recovery

- [ ] **REQ-SAFE-01**: Secrets, live Sheet locator, personal exports, SQLite, reports, logs і backups не потрапляють у Git або generated documentation.
- [ ] **REQ-SAFE-02**: Successful і failed writes створюють redacted audit з IDs, actor/tool version, timestamps, hashes і outcome без raw notes або зайвих health fields.
- [ ] **REQ-SAFE-03**: Pull створює coherent immutable snapshots, а atomic mirror promotion залишає попередній complete mirror active після failure або partial capture.
- [ ] **REQ-SAFE-04**: Portable backup і verified isolated restore відновлюють workbook data, program versions та local analytical state з matching manifest counts/hashes.
- [ ] **REQ-SAFE-05**: До моделі передається лише minimum user-authorized context для конкретного capture або analysis request без bulk history, credentials, locators чи unrelated health context.

## v2 Requirements

Немає затверджених v2 вимог. Новий scope додається лише через окреме рішення та roadmap update.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-user та role management | Milestone призначений для одного власника. |
| Wearables та сторонні fitness imports | Не потрібні для core cycle і збільшують privacy scope. |
| Arbitrary Sheet editing | Writer обмежений versioned allowlisted bundle tools. |
| Automatic program changes | Google Sheets program owner має explicitly approve нову version. |
| Server database | Локальний SQLite достатній як rebuildable projection. |
| Medical diagnosis або treatment advice | Recovery analysis у v1 лише descriptive. |

## Acceptance and Completion

Requirement стає Complete лише коли implementation, automated verification та відповідний UAT/restore evidence пройшли. Основні end-to-end gates: UAT-01 workbook/setup; UAT-02 preview/idempotency; UAT-03 confirmed atomic write; UAT-04 metrics/cohorts/provenance; UAT-05 recommendations/owner decision; UAT-06 backup/isolated restore.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-WBK-01 | Phase 1 | Pending |
| REQ-WBK-02 | Phase 1 | Pending |
| REQ-WBK-03 | Phase 1 | Pending |
| REQ-WBK-04 | Phase 1 | Pending |
| REQ-WBK-05 | Phase 1 | Pending |
| REQ-CAP-01 | Phase 2 | Pending |
| REQ-CAP-02 | Phase 2 | Pending |
| REQ-CAP-03 | Phase 2 | Pending |
| REQ-CAP-04 | Phase 2 | Pending |
| REQ-CAP-05 | Phase 2 | Pending |
| REQ-CAP-06 | Phase 2 | Pending |
| REQ-SAFE-02 | Phase 2 | Pending |
| REQ-SAFE-05 | Phase 2 | Pending |
| REQ-ANL-01 | Phase 3 | Pending |
| REQ-ANL-02 | Phase 3 | Pending |
| REQ-ANL-03 | Phase 3 | Pending |
| REQ-ANL-04 | Phase 3 | Pending |
| REQ-ANL-05 | Phase 3 | Pending |
| REQ-SAFE-03 | Phase 3 | Pending |
| REQ-REC-01 | Phase 4 | Pending |
| REQ-REC-02 | Phase 4 | Pending |
| REQ-REC-03 | Phase 4 | Pending |
| REQ-REC-04 | Phase 4 | Pending |
| REQ-REC-05 | Phase 4 | Pending |
| REQ-SAFE-01 | Phase 5 | Pending |
| REQ-SAFE-04 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 26 total
- Mapped to phases: 26
- Unmapped: 0 ✓
- Duplicate mappings: 0 ✓

---
*Requirements defined: 2026-07-25*
*Last updated: 2026-07-25 after document-ingest rebaseline*
