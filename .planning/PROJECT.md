# Workout Tracker

## What This Is

Workout Tracker — персональний локальний CLI для власника чотириденної програми `Upper/Lower`, який забирає авторитетні тренувальні факти з Google Sheets, перевіряє їх, будує ідемпотентне аналітичне дзеркало в SQLite та створює відтворюваний звіт прогресу. Система зберігає Google Sheets єдиним джерелом правди, а локальні дані використовує для запитів, розрахунків, доказів і перевіреного резервного відновлення.

## Core Value

Одна повторювана CLI-команда перетворює всі авторитетні факти з Google Sheets на валідовані, ідемпотентні локальні дані та відтворюваний звіт із простежуваними доказами.

## Requirements

### Validated

(Поки немає — цінність буде підтверджена після реалізації та перевірки)

### Active

- [ ] Користувач може безпечно під’єднати Google Sheet і до імпорту перевірити його структуру та якість даних.
- [ ] Користувач може отримати повне, нормалізоване й ідемпотентне SQLite-дзеркало вкладок `Програма`, `Сесії`, `Підходи` і `Рекомендації`.
- [ ] Користувач може запитувати історію тренувань і вправ та обчислювати volume, working load, e1RM, RIR, rest і recovery trends.
- [ ] Користувач може однією командою створити відтворюваний звіт, у якому кожен висновок має зв’язок із вихідними сесіями, підходами та snapshot.
- [ ] Користувач може довести, що секрети й персональні експорти не відстежуються Git, а резервна копія справді відновлюється.

### Out of Scope

- Автоматичне масове або непомітне перезаписування первинних тренувальних записів — суперечить політиці єдиного джерела правди.
- Заміна Google Sheets як authoritative store у v1 — міграція primary store можлива лише в post-v1 після появи multi-user, authentication або складнішого API.
- Медичні діагнози, дозування ліків або поради щодо лікування й харчування при виражених побічних реакціях — це зона відповідальності кваліфікованого медичного фахівця.
- Використання `.gsheet` як аналітичного input чи надійної резервної копії — файл є посиланням, а не довговічною копією даних.
- Автоматичне перетворення поточної програми на full circuit або зміна програми без достатніх доказів — це не входить до доказового v1 workflow.
- Припущення про непідтверджене обладнання чи підтримку вправ, для яких потрібні відсутні засоби — джерельний каталог навмисно обмежений підтвердженим інвентарем.

## Context

- Проєкт створюється з ingest-корпусу з 11 документів: 2 `SPEC`, 9 `DOC`, 0 `PRD` і 0 `ADR`. У джерелах виділено 29 constraints; conflict review має 0 blockers, 0 warnings і 0 info.
- Через відсутність `PRD` атомарні v1-вимоги виведено з architecture goals, version-one quality bar, user-supplied developer-facing success metric від 2026-07-24, workout/program context і прийнятих узгоджень.
- Поточна програма має рівно чотири authoritative source labels:
  `Верх — сила`, `Низ — сила`, `Верх — гіпертрофія`,
  `Низ — гіпертрофія`. English codes є лише internal aliases.
- Програма використовує paired sets, зберігає головні силові рухи та відпочинок у межах 60-хвилинного бюджету й не повинна перетворюватися на метаболічний circuit.
- Узгоджений тижневий обсяг становить 13 обов’язкових quadriceps sets, до 15 з optional lower-strength block, і 12 core sets. Розминка `Lower Strength` триває 7–8 хвилин у межах бюджету 0–8 хвилин.
- Стандартна double progression є детермінованим правилом: одного повністю кваліфікованого виконання достатньо для стандартного кроку. Зміна правила, кількості підходів, вправи чи іншої частини програми потребує щонайменше трьох виконань вправи; trend analysis орієнтується приблизно на 6–8 повторень типу тренування.
- Джерельна архітектура: [WORKOUT_TRACKER_ARCHITECTURE.md](../WORKOUT_TRACKER_ARCHITECTURE.md). Узгоджені правила: [05 progression and session rules.md](<../4-day upper lower program/05 progression and session rules.md>).

## Constraints

- **Runtime**: Python 3.12+ local CLI з uv-style dependency management — прийняте рішення користувача.
- **Validation**: Pydantic має бути межею валідації зовнішніх і нормалізованих даних; невідомі значення залишаються порожніми, а не вигадуються.
- **Analytical store**: SQLite є локальним queryable store для v1; Google Sheets залишається єдиним джерелом тренувальних фактів.
- **Testability**: Компоненти й CLI мають бути придатними для pytest-compatible automated verification.
- **Source schema**: Pull читає фактичні вкладки `Програма`, `Сесії`,
  `Підходи` і `Рекомендації`; приймаються лише чотири визначені workout types
  та source-owned `program_item_id`, `session_id`, `set_id` і
  `recommendation_id`. Internal English identifiers можуть бути aliases, але
  не замінюють перевірку реальних Sheet labels.
- **Sheet contracts**: `Програма` зберігає prescription fields; `Сесії` — session identity, context, recovery й summaries; `Підходи` — set facts, load/reps/RIR/rest, volume/e1RM, pain/technique; `Рекомендації` — signal, evidence, confidence і review metadata. Повні field lists залишаються в source architecture.
- **Identity and history**: Ідентичність визначається stable IDs, а не
  позицією рядка; factual correction створює revision під тим самим ID,
  coherent disappearance — tombstone, а кожна нова session посилається на
  immutable `program_version_id`.
- **Sync safety**: Raw snapshot незмінний; повторний pull ідемпотентний; primary facts не перезаписуються непомітно.
- **Storage boundary**: CSV — tabular interchange, JSON — structured exchange, XLSX — повна ручна backup-копія, SQLite — analytics; `.gsheet` не є input або backup.
- **Privacy**: API keys, OAuth tokens, populated `.env`, персональні raw/processed exports, caches і backups не потрапляють у Git.
- **Evidence**: Формули, input fingerprint, session/set IDs і джерельний snapshot мають дозволяти відтворити кожен звітний висновок.
- **Backup**: RPO ≤24 hours; 35 daily + 12 month-end verified backups; дві
  encrypted copies у різних fault domains; full isolated restore verification
  щонайменше weekly.
- **Repository boundaries**: Source-derived layout розділяє `config/`, `src/sync/`, `src/analytics/`, `data/raw/`, `data/processed/`, `data/backups/`, `reports/`, `tests/` і `scripts/`; recommendation code додається лише в post-v1 scope.
- **Recommendation safety**: v1 не генерує AI program-change recommendations; майбутня логіка мусить відрізняти deterministic progression від аналітичних рекомендацій і дотримуватися evidence thresholds.
- **Medical safety**: Pain/risk flags не є діагнозом; гострий, сильний або стійкий біль вимагає професійної оцінки.

## Key Decisions

Ingest не містив ADR. Наведені нижче записи є project decisions із provenance, а не `LOCKED` рішеннями; source-derived baseline може переглядатися через звичайний decision workflow. Позначка `Pending` означає, що рішення прийняте для планування, але його результат ще має бути перевірений виконанням.

| Decision | Rationale and provenance | Outcome |
|----------|--------------------------|---------|
| Використовувати Python 3.12+ local CLI, uv-style dependencies, Pydantic і pytest-compatible design | Пряме рішення користувача від 2026-07-24 | ✓ Accepted |
| Використовувати SQLite як v1 analytical store | Пряме рішення користувача; уточнює відкритий вибір local store у `WORKOUT_TRACKER_ARCHITECTURE.md` §9 | ✓ Accepted |
| Google Sheets володіє operational facts і versioned program prescriptions; Git володіє schemas, formulas і executable rules | [ADR-001](../docs/architecture/ADR-001-authority-boundaries.md) усуває dual-source ambiguity | ✓ Accepted |
| Залишити Google Sheets єдиним джерелом тренувальних фактів | Source-derived architecture baseline, `WORKOUT_TRACKER_ARCHITECTURE.md` §§2–3 | — Pending validation in Phase 2 |
| Обмежити v1 напрямком pull → validate → analyze → report, без автоматичної mutation primary facts | Source-derived sync contract і delivery sequence, `WORKOUT_TRACKER_ARCHITECTURE.md` §§8, 13–15 | — Pending validation in Phases 2–4 |
| Зберігати чіткі module/data boundaries між sync, analytics, raw, processed, backups, reports і tests | Source-derived repository layout, `WORKOUT_TRACKER_ARCHITECTURE.md` §6; конкретні Python package names залишаються implementation choice | — Pending validation during phase planning |
| Відкласти workout capture/write-back і recommendation engine до v2 | Basic metrics мають бути перевірені раніше за automated recommendations, `WORKOUT_TRACKER_ARCHITECTURE.md` §§10–13 | ✓ Accepted for v1 scope |
| Вимагати evidence lineage для кожного висновку | User-supplied developer-facing success metric від 2026-07-24 і `WORKOUT_TRACKER_ARCHITECTURE.md` §§11, 15 | — Pending validation in Phase 4 |
| Вважати backup готовим лише після isolated restore verification | Source-derived backup policy, `WORKOUT_TRACKER_ARCHITECTURE.md` §12 | — Pending validation in Phase 5 |
| Не вважати privacy requirement виконаною до disposition already-published public history | Security audit 2026-07-24; current-file cleanup не видаляє remote history | — External owner action required |

## Evolution

Цей документ змінюється на межах фаз і milestones.

**Після переходу між фазами**:
1. Невалідні вимоги переносяться до Out of Scope з причиною.
2. Перевірені вимоги переходять до Validated із посиланням на фазу.
3. Нові вимоги додаються до Active.
4. Нові рішення фіксуються в Key Decisions.
5. Опис продукту оновлюється, якщо фактичний продукт змінився.

**Після кожного milestone**:
1. Перевіряються всі розділи.
2. Повторно оцінюється Core Value.
3. Переглядаються межі Out of Scope.
4. Context оновлюється фактичними результатами.

---
*Last updated: 2026-07-24 after ingest-based initialization*
