# SPEC: ChatGPT workout capture, query and recommendations

- **Status:** Normative integration contract
- **Version:** 1.0
- **Date:** 2026-07-24
- **Transport:** pluggable ChatGPT plugin/MCP tool surface

## 1. Boundary

Стабільним контрактом є набір versioned tools і JSON schemas, а не конкретна
назва ChatGPT integration product. Adapter може змінюватися без зміни domain
semantics.

Модель не має:

- arbitrary Spreadsheet range/cell tools;
- доступу до credentials або live Sheet locator;
- права самостійно підтверджувати write;
- права переписувати source IDs, historical facts або program version;
- права застосовувати recommendation як program change.

## 2. Tools

### `preview_workout`

Read-only операція.

Input:

- user-authored workout description;
- optional session date/time and workout type;
- `workbook_contract_version`;
- optional locale/timezone.

Output:

- proposed `session_id`;
- resolved `program_version_id` і workout type;
- normalized session fields;
- ordered logical sets/components;
- missing required fields;
- ambiguities and warnings;
- content hash;
- short-lived `confirmation_token`;
- preview expiry.

Tool не вигадує load, reps, unit, side, RIR, rest, symptoms або program item.
Critical ambiguity блокує commit. Дозволене unknown стає explicit `null`.

### `commit_workout`

Important external write.

Input:

- exact `confirmation_token`;
- matching preview content hash;
- explicit user confirmation;
- caller-generated `idempotency_key`;
- expected workbook/contract/program versions.

Preconditions:

- preview не expired і належить тому самому user/workbook binding;
- payload не змінився після preview;
- IDs унікальні або вже належать тому самому idempotent result;
- parent session і всі child sets проходять validation;
- program version існує.

Outcome:

- весь bundle записано;
- або нічого не записано;
- retry з тим самим key повертає той самий `session_id` і outcome;
- audit event містить IDs, hashes, versions, timestamp і error code без raw
  workout text.

### `query_training_history`

Read-only structured query з обов’язковим bounded date range або explicit
recent limit. Повертає лише requested fields/aggregates, comparison cohort,
status і evidence IDs.

### `analyze_progress`

Read-only deterministic analysis. Приймає exercise/cohort, date window і
metric names з allowlist. Повертає formula/ruleset versions, results,
limitations і evidence IDs.

### `propose_recommendations`

Створює recommendation preview, а після окремого підтвердження — immutable
рядок у `Рекомендації`. Не змінює `Програма`.

Кожна пропозиція містить:

- `recommendation_id`;
- recommendation kind і status;
- evidence window та IDs;
- deterministic rule result, якщо застосовний;
- rationale;
- uncertainty/limitations;
- proposed change;
- generator/model/tool version;
- created/decided timestamps.

## 3. Confirmation protocol

1. Користувач описує тренування або просить рекомендацію.
2. Tool повертає preview та конкретні уточнення.
3. ChatGPT показує compact human-readable summary.
4. Користувач явно підтверджує саме цей preview.
5. Adapter викликає write tool із confirmation token та idempotency key.
6. Результат показує authoritative IDs і статус.

Фраза моделі, inferred intent або попередня згода не замінює крок 4.

## 4. Atomic write strategy

Google Sheets не є транзакційною базою, тому writer використовує
versioned staging/commit protocol:

1. validate bundle поза Sheet;
2. перевірити contract/program preconditions;
3. зарезервувати idempotency record;
4. виконати bounded batch update для session, sets і audit marker;
5. перевірити IDs/content hashes;
6. позначити bundle committed.

Readers і analytical pull ігнорують bundle без valid commit marker. Recovery
може завершити або quarantine incomplete write, але не публікує partial
session.

## 5. Privacy and data minimization

- Capture надсилає моделі лише текст, який користувач свідомо ввів у цей чат,
  і мінімальні довідники для normalization.
- Analysis tools агрегують локально або в trusted adapter та повертають
  мінімально потрібні факти/evidence.
- Bulk raw exports, full notes, Sheet locators, credentials і unrelated health
  context не передаються моделі.
- Logs не містять raw prompts, notes, symptoms, body mass або row payloads.
- Користувач може виконувати manual capture без ChatGPT.

## 6. Recommendation and medical boundary

Deterministic progression є результатом versioned rule. AI recommendation є
окремою інтерпретацією evidence і завжди маркується як така.

Pain, soreness, sleep, stress, nausea, dizziness і performance є
self-reported context. Tool може описати асоціацію або порадити звернутися до
кваліфікованого фахівця, але не ставить діагноз, не призначає лікування й не
стверджує причинність.

## 7. Verification

Contract tests покривають:

- missing and ambiguous input;
- unilateral, duration, assisted і bodyweight sets;
- preview mutation і expired token;
- duplicate retries;
- partial write failure та recovery;
- stale contract/program version;
- unauthorized range/field;
- insufficient/incomparable analysis evidence;
- recommendation creation without program mutation;
- redaction of logs and model context.
