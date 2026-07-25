# Синтезовані вимоги

Усі вимоги походять із одного PRD, тому competing acceptance variants не
виявлено. IDs збережено як стабільні `REQ-{source-id}`.

## Workbook

### REQ-WBK-01 — Точна topology workbook
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: workbook topology
- description: Workbook має сім точних вкладок: `Старт`, `Програма`, `Сесії`, `Підходи`, `Рекомендації`, `Довідники`, `Дашборд`.
- acceptance criteria: UAT-01 на чистому Spreadsheet підтверджує наявність рівно цих семи вкладок.

### REQ-WBK-02 — Чотири версійовані комплекси
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: program bootstrap
- description: `Програма` містить чотири версійовані комплекси з repository specifications без втрати paired-set, reps, RIR, rest і equipment semantics.
- acceptance criteria: UAT-01 підтверджує завантаження чотирьох комплексів та збереження всіх prescription semantics.

### REQ-WBK-03 — Безпечний mobile input
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: workbook UX
- description: Input fields мають validation, hints, formats і mobile-friendly порядок; formula/system columns захищені.
- acceptance criteria: UAT-01 перевіряє validation і protection, а mobile flow дозволяє внести facts без редагування system columns.

### REQ-WBK-04 — Визначені formula metrics
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: formulas and dashboard
- description: Формули й dashboard показують лише визначені metric contracts та явно відображають missing/incomparable status.
- acceptance criteria: UAT-04 повертає визначені metrics і status замість вигаданого zero.

### REQ-WBK-05 — Ідемпотентний setup
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: workbook setup
- description: Повторний setup не дублює tabs, formulas, named ranges або program items.
- acceptance criteria: UAT-01 запускає setup двічі; другий запуск не змінює logical content.

## ChatGPT capture

### REQ-CAP-01 — Natural-language capture
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: workout capture
- description: Користувач може описати виконане тренування природною мовою.
- acceptance criteria: UAT-02 перетворює user-authored note на session/set preview.

### REQ-CAP-02 — Unknown не вигадується
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: capture normalization
- description: Система запитує критичні уточнення або залишає дозволене значення unknown/`NULL`.
- acceptance criteria: Missing input не перетворюється на fabricated fact; invalid critical omissions fail closed.

### REQ-CAP-03 — Preview до запису
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: capture confirmation
- description: До запису користувач бачить normalized preview сесії, підходів і warnings.
- acceptance criteria: UAT-02 дозволяє виправити щонайменше одне неоднозначне поле до confirmation.

### REQ-CAP-04 — Confirmed atomic commit
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: controlled writer
- description: `commit_workout` працює лише після explicit confirmation і додає session/set bundle атомарно.
- acceptance criteria: UAT-03 доводить, що invalid, incomplete або unconfirmed payload не змінює Spreadsheet.

### REQ-CAP-05 — Stable IDs та idempotency
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: write identity
- description: Stable IDs та idempotency key запобігають дублюванню під час repeat, timeout або retry.
- acceptance criteria: UAT-02 повторює commit і отримує той самий result без duplicate rows.

### REQ-CAP-06 — Allowlisted writer
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: writer authorization
- description: Writer не має arbitrary cell/range mutation і працює лише з allowlisted fields.
- acceptance criteria: Неallowlisted operation відхиляється до mutation; audit фіксує outcome без sensitive payload.

## Reading and analytics

### REQ-ANL-01 — Filtered history query
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: history query
- description: Історію можна запитати за workout type, exercise, program version і date range.
- acceptance criteria: Query повертає лише записи, що відповідають усім заданим filters.

### REQ-ANL-02 — Versioned metric semantics
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: analytics
- description: Working volume, load, e1RM, RIR, rest і recovery summaries відповідають versioned metric contracts.
- acceptance criteria: UAT-04 відтворює results із pinned formula/ruleset versions.

### REQ-ANL-03 — Comparable cohorts only
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: comparison safety
- description: Variant, equipment, load basis, assistance semantics і comparison cohort перевіряються до порівняння.
- acceptance criteria: UAT-04 виключає incomparable observations і пояснює exclusion status.

### REQ-ANL-04 — Evidence-bearing results
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: analytics provenance
- description: Кожен результат містить formula/ruleset version, status і достатній evidence locator.
- acceptance criteria: UAT-04 дозволяє простежити result до source-owned IDs без raw sensitive payload.

### REQ-ANL-05 — Shared Sheet/ChatGPT semantics
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: cross-surface metrics
- description: Dashboard і ChatGPT query tools використовують однакові metric semantics.
- acceptance criteria: Однакові eligible inputs і versions дають семантично однакові values/status на обох surfaces.

## Recommendations

### REQ-REC-01 — Deterministic result окремо від AI
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: recommendation classification
- description: Deterministic progression rule повертається окремо від AI-generated recommendation.
- acceptance criteria: UAT-05 візуально та структурно розрізняє rule result і recommendation.

### REQ-REC-02 — Provenance recommendation
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: recommendation schema
- description: Recommendation містить `recommendation_id`, created time, evidence window, rationale, confidence/limitations і status.
- acceptance criteria: UAT-05 відхиляє або позначає incomplete recommendation без required provenance fields.

### REQ-REC-03 — Insufficient evidence fail-safe
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: recommendation eligibility
- description: Недостатні або непорівнювані дані створюють `insufficient_evidence` або відмову, а не вигадану пораду.
- acceptance criteria: Ineligible cohort повертає explicit status і не пропонує fabricated change.

### REQ-REC-04 — Owner approval для program change
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: program authority
- description: Recommendation не змінює prescription без explicit owner approval та нової `program_version_id`.
- acceptance criteria: UAT-05 доводить, що показ recommendation не змінює active program.

### REQ-REC-05 — Medical boundary
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: recovery interpretation
- description: Recovery context є descriptive; система не ставить diagnosis і не робить causal medical conclusion.
- acceptance criteria: Recovery output використовує descriptive language та routes acute/severe/persistent symptoms до qualified professional.

## Privacy, audit and recovery

### REQ-SAFE-01 — Sensitive data поза Git/logs/docs
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: privacy
- description: Secrets, live Sheet locator і personal exports не потрапляють у Git, logs або generated documentation.
- acceptance criteria: Repository/privacy scan не знаходить prohibited values у tracked artifacts.

### REQ-SAFE-02 — Redacted write audit
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: write audit
- description: Audit містить IDs, actor/tool version, timestamps, hashes і outcome, але не raw notes чи зайві health fields.
- acceptance criteria: Successful і failed writes створюють traceable redacted audit records.

### REQ-SAFE-03 — Coherent snapshot та atomic mirror
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: analytical pull
- description: Pull створює coherent immutable snapshots, а mirror promotion є atomic.
- acceptance criteria: Failure або partial capture залишає попередній complete mirror active.

### REQ-SAFE-04 — Portable verified restore
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: backup and restore
- description: Є portable backup і verified isolated restore для workbook data, program versions та local analytical state.
- acceptance criteria: UAT-06 відновлює operational records і mirror; counts та hashes збігаються з manifest.

### REQ-SAFE-05 — Minimal model egress
- source: /home/muuser/bushuk-labs/gym/docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md
- scope: LLM data minimization
- description: До моделі передається мінімальний user-authorized context для конкретного capture або analysis request.
- acceptance criteria: Bulk history, credentials, locators і unrelated health context відсутні в model payload.

## Підсумок

- Вимог виділено: 26
- Requirement IDs: `REQ-WBK-01`–`REQ-WBK-05`, `REQ-CAP-01`–`REQ-CAP-06`, `REQ-ANL-01`–`REQ-ANL-05`, `REQ-REC-01`–`REQ-REC-05`, `REQ-SAFE-01`–`REQ-SAFE-05`
- Competing acceptance variants: 0
