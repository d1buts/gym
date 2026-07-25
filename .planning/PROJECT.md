# Workout Tracker

## Що це

Workout Tracker — приватний Spreadsheet-first трекер тренувань для одного власника. Google Spreadsheet є повноцінним щоденним продуктом для програми, ручного введення, перегляду прогресу й рішень, а вузькі версійовані ChatGPT plugin/MCP tools додають контрольоване capture/write-back; локальний Python 3.12+ контур перевіряє, дзеркалить та аналізує авторитетні дані у rebuildable SQLite.

## Core Value

Повний цикл «план → тренування → capture → verification → analysis → recommendation → explicit user decision» працює без прихованої ручної обробки, а кожен результат можна простежити до авторитетних фактів і версійованих правил.

## Вимоги

### Validated

(Ще немає — цінність підтверджується після реалізації, automated verification та обов’язкового UAT/restore evidence.)

### Active

- [ ] Самодостатній Google Spreadsheet із точними сімома вкладками, чотирма версійованими комплексами, безпечним mobile input, визначеними formulas/dashboard та ідемпотентним setup.
- [ ] Natural-language capture через вузькі ChatGPT tools із preview, explicit confirmation, stable IDs, idempotency, atomic allowlisted write та мінімальним model egress.
- [ ] Read-only coherent pull у rebuildable SQLite mirror і фільтрована аналітика зі спільними versioned metric semantics, comparable cohorts та evidence lineage.
- [ ] Чітко відокремлені deterministic progression results і evidence-backed recommendations, які не змінюють програму без explicit owner approval.
- [ ] Privacy, redacted audit, portable backup та verified isolated restore як release gates.

### Out of Scope

| Функція | Причина |
|---------|---------|
| Multi-user, ролі та shared tenancy | Перший milestone є приватним single-owner продуктом. |
| Wearables та автоматичний імпорт із fitness platforms | Не потрібні для основного циклу й розширюють privacy boundary. |
| Arbitrary Sheet cell/range editing через ChatGPT | Суперечить allowlisted writer boundary та принципу least privilege. |
| Automatic program changes | Prescription змінюється лише після explicit owner approval і створення нової `program_version_id`. |
| Server database або обов’язковий hosted backend | SQLite є локальним rebuildable analytical store; Spreadsheet має працювати самостійно. |
| Medical diagnosis, treatment або causal health claims | Recovery context у v1 є лише self-reported descriptive context. |

## Контекст

- Авторитетний корпус уже визначає чотириденну upper/lower програму: `upper_strength`, `lower_strength`, `upper_hypertrophy`, `lower_hypertrophy`, включно з paired-set, reps, RIR, rest, equipment та progression semantics.
- Exact source labels у Google Sheets є українськими; English aliases використовуються лише всередині коду й контрактів.
- Google Sheets володіє operational facts, recommendation journal і versioned program prescriptions. Git володіє schemas, normalization, formulas, executable rules, tests і documentation.
- Raw snapshots, normalized datasets і SQLite — похідні projections, які мають повністю відбудовуватися з авторитетного джерела та версійованих правил.
- Відомий public-history disclosure підвищує вимоги до repository hygiene: planning, logs і commits не повинні повторювати sensitive values або live identifiers.
- Product success означає 26/26 вимог, кожна з яких відображена рівно в одну phase і закрита implementation, automated verification та потрібним UAT/restore evidence.

## Constraints

- **Primary product**: Google Spreadsheet має залишатися високоякісним standalone daily product навіть без ChatGPT або локального CLI.
- **Runtime**: Python 3.12+, uv-style dependency management, Pydantic validation boundary, SQLite з foreign keys і transactional staging promotion; authoritative numeric calculations використовують `Decimal` або scaled integers.
- **Identity**: `program_item_id`, `session_id`, `set_id` і `recommendation_id` є source-owned immutable IDs; row number або content-derived fallback ніколи не є identity.
- **Authority**: Unknown зберігається як `NULL`; raw source facts, Sheet-calculated values і local-derived values не змішуються; кожна session посилається на `program_version_id`.
- **Write safety**: Кожен external write потребує preview, explicit confirmation, stable IDs, contract/version preconditions та idempotency; writer має окремі мінімальні credentials і лише allowlisted bundle operations.
- **Sync safety**: Analytical pull є read-only, захоплює чотири authoritative tabs як version-fenced unit, публікує immutable complete snapshot і атомарно promotes mirror; failure залишає попередній complete mirror active.
- **Metric safety**: Застосовуються лише `docs/architecture/METRICS.md` і pinned versions; missing/incomparable input дає status та `NULL`, а warm-up/invalid/aborted sets не входять до working volume.
- **Privacy**: Credentials, live Sheet locators, personal exports, SQLite, reports, logs і backups не потрапляють у Git; model egress обмежений minimum user-authorized context.
- **Language**: Human-facing documentation і точні Sheet labels — українською; identifiers, schema keys, requirement IDs і technology names — англійською.
- **Change control**: Зміна accepted authority/runtime/product boundary потребує ADR та синхронного оновлення PROJECT, REQUIREMENTS, roadmap traceability, contracts і tests.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| **ADR-001 LOCKED:** Google Sheets володіє operational facts і versioned prescriptions; Git — contracts/rules/tests/docs; local stores є rebuildable projections. | Запобігає розходженню джерел правди та втраті provenance. | LOCKED |
| **ADR-002 LOCKED:** Локальний контур — Python 3.12+, uv-style dependencies, Pydantic і SQLite з transactional staging promotion. | Дає перевірюваний, portable та rebuildable analytical runtime без server database. | LOCKED |
| **ADR-003 LOCKED:** Spreadsheet-first product із контрольованим ChatGPT write path, окремими credentials, preview/confirmation та idempotency. | Зберігає standalone UX Spreadsheet і мінімізує blast radius зовнішнього запису. | LOCKED |

## Evolution

Після кожної phase цей документ переглядається: verified requirements переходять у Validated лише після automated verification і потрібного UAT; нові scope/authority рішення потребують traceability update, а зміни locked boundaries — нового ADR.

---
*Останнє оновлення: 2026-07-25 після document-ingest rebaseline*
