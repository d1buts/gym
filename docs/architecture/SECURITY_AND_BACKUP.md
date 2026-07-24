# Безпека, приватність і резервне відновлення

**Version:** `security-backup-v1`

**Status:** Accepted design contract

**Applies to:** local CLI, Google Sheets read path, Git, snapshots, reports and backups

## 1. Межі й модель загроз

V1 читає персональні тренувальні факти з одного allowlisted Google Sheet,
обробляє їх локально і не змінює source. Захищаються:

- OAuth tokens, service-account keys та recovery keys;
- Sheet locator і sharing metadata;
- raw/normalized workout facts, health context, notes і reports;
- SQLite, logs, quarantine та backup artifacts;
- цілісність snapshot, manifest і restore evidence.

Основні ризики: надмірні Google permissions, випадковий pull чужої таблиці,
секрети або персональні exports у Git/logs, LLM/telemetry egress, CSV
formula injection, втрата локального диска, пошкоджений чи невідновлюваний
backup і вже опублікована Git history.

## 2. Підтверджене finding публічної історії

Станом на 2026-07-24 read-only audit підтвердив:

- GitHub origin є **public**;
- already-pushed history містить прямий locator живої Google Sheet;
- already-pushed history містить персоналізований health/medication context;
- scoped text scan не виявив OAuth/API secrets, але це не замінює
  повноісторичний secret scan.

Значення locator, назва medication і персональний текст навмисно тут не
повторюються. Видалення їх із current files, новий `.gitignore` або
звичайний commit **не стирають Git history**, forks, clones чи caches.
Публічно доступне значення треба вважати disclosed.

Це зовнішня remediation, яка потребує **явної дії власника**:

1. перевірити sharing живої Sheet і, якщо disclosure був ненавмисний,
   обмежити доступ або замінити її locator;
2. окремо вирішити, чи змінювати GitHub visibility;
3. окремо схвалити destructive coordinated history rewrite/force-push,
   якщо він потрібний;
4. після remediation просканувати всі refs і перевірити remote повторно.

Зміна GitHub visibility, Sheet sharing/locator або already-pushed history
не виконується локальним workflow без explicit owner approval. Навіть після
rewrite система MUST виходити з того, що попередні public copies могли
зберегтися. До зовнішнього рішення `PRIV-01` не може мати статус complete.

## 3. Read-only Google authorization

V1 MUST NOT запитувати write, Drive content/export або domain-wide
delegation permissions. Core capture MUST працювати без Drive scope.
Допустимі два least-privilege profiles.

### 3.1 OAuth installed application

- користувач авторизує локальний CLI під своїм Google account;
- scope обмежений `spreadsheets.readonly`;
- coherent-capture fence виконується подвійним повним читанням і
  порівнянням content fingerprints;
- desktop OAuth MUST NOT запитувати Drive metadata/content/export scope;
- refresh/access tokens зберігаються за §5;
- CLI показує requested scope і source alias до consent;
- revoke/logout видаляє локальний token reference і пояснює, як відкликати
  grant у Google account.

OAuth grant може технічно бачити більше таблиць, доступних account, тому
application-enforced allowlist §4 залишається обов’язковим.

### 3.2 Isolated dedicated service account

- цільову Sheet ділять із dedicated principal лише як `Viewer`;
- service account не отримує editor, folder-wide або domain-wide access;
- обов’язковий scope — `spreadsheets.readonly`;
- `drive.metadata.readonly` MAY додаватися лише для exact-ID
  `files.get(version, modifiedTime)` version fence;
- з optional Drive metadata scope застосунок MUST NOT викликати
  list/search/export, приймати довільний file ID або читати Drive content;
- одна identity SHOULD обслуговувати лише цей tracker/environment;
- long-lived JSON key SHOULD уникатися. Якщо він необхідний, файл
  зберігається поза workspace, має mode `0600`, encryption at rest і
  rotation/revocation procedure.

Repository містить лише templates та secret aliases. Client secret,
private key, token, raw Sheet locator або populated `.env` у Git
заборонені.

Оскільки `drive.metadata.readonly` ширший на рівні grant, його дозволено
тільки isolated service account, якому надано доступ виключно до target
Sheet. Якщо ця ізоляція не доведена, використовується Sheets-only
double-capture profile.

## 4. Sheet allowlist і source binding

V1 за замовчуванням має рівно один `source_alias`. Його raw spreadsheet
locator живе в untracked secure local settings, не в versioned config.

До читання rows preflight MUST:

1. отримати metadata через read-only API;
2. exact-match returned spreadsheet identity з локальним allowlist;
3. перевірити expected title лише як secondary diagnostic, не identity;
4. перевірити allowlisted tabs `Програма`, `Сесії`, `Підходи`,
   `Рекомендації`;
5. відхилити redirect, copied/foreign Sheet, unexpected source або
   multi-source selection.

Logs/manifests використовують `source_alias` і non-reversible operational
fingerprint, а не raw locator. Додавання іншої Sheet є explicit local
configuration change з новим preflight; wildcard allowlist заборонений.

## 5. Secret storage і local permissions

Пріоритет зберігання:

1. OS keyring/credential manager або dedicated secret manager;
2. encrypted credential file поза repository/workspace;
3. plaintext local file лише як documented development fallback, mode
   `0600`, у директорії mode `0700`, з fail-fast permission check.

Secrets MUST NOT передаватися в command-line arguments, traceback,
shell history, environment dump, snapshot, manifest, test fixture або
support bundle. Environment variables MAY переносити ephemeral reference,
але populated `.env` не є рекомендованим сховищем.

Raw, processed, SQLite, reports, quarantine і restore staging directories
MUST бути owner-only (`0700`); files MUST бути owner-readable/writable only
(`0600`) за винятком платформи, де еквівалент забезпечує ACL. CLI MUST
відмовитися від роботи при world/group-readable credential або personal
artifact, якщо не може безпечно виправити permission.

## 6. Logging, redaction і egress

Structured logs дозволяють: run/snapshot/backup ID, source alias,
fingerprints, row counts, stable error codes, durations і version metadata.
Заборонено логувати:

- authorization headers, tokens, keys, cookies або credential paths із
  secret-bearing names;
- raw Sheet locator;
- workout rows, names, notes, health fields або cell contents;
- full exception objects від Google client, доки їх не пройдено redaction;
- backup recovery key чи plaintext data path у shared telemetry.

Redaction MUST виконуватися до formatting, persistence і exception
reporting. Unknown external error payload вважається sensitive by default.
Debug mode не скасовує redaction.

V1 analytics є local deterministic workflow. Raw/normalized rows, reports,
notes та health context MUST NOT надсилатися до LLM, ChatGPT, hosted error
tracking, product analytics або unrelated API. Network allowlist під час
pull обмежується Google authentication/Sheets endpoints; remote backup
отримує лише client-side encrypted bundle. Майбутній LLM workflow потребує
окремого opt-in threat review і data-minimization contract.

## 7. Git safety і full-history scan

`.gitignore` MUST охоплювати щонайменше:

- populated `.env` і credential/token files;
- `data/raw/`, `data/processed/`, `data/backups/`, SQLite і journals;
- generated personal reports, quarantine, restore staging і caches;
- native `.gsheet` pointers;
- local GSD attempts/intel, якщо вони містять verbatim personal sources.

До кожного release/ship repository safety check MUST перевірити:

1. tracked files (`git ls-files`);
2. index/staged diff;
3. working tree та ignored-boundary regressions;
4. **усі commits, branches, tags і refs**, а не лише `HEAD`;
5. high-entropy/API/private-key patterns і known local locator/health
   fingerprints без друку matching value;
6. oversized exports, images/metadata та archive contents;
7. remote visibility і branch, що буде pushed.

Scanner output MUST містити тільки finding category, path, commit/ref і
redacted fingerprint. Scan report без findings не доводить, що disclosure
ніколи не було; finding у public history залишається відкритим до owner-led
remediation й повторної remote verification.

Secrets, якщо будь-коли знайдені, MUST бути revoked/rotated до history
cleanup. History rewrite сам по собі не є secret rotation.

## 8. CSV formula injection

Будь-яке Sheet text поле є untrusted. Quoting CSV cell не заважає
spreadsheet application виконати formula.

V1 розділяє два artifacts:

- canonical restore data — JSON із typed strings/values усередині
  encrypted backup; його не відкривають у spreadsheet application;
- human-view CSV — похідний файл, безпечний для відкриття, але не
  authoritative restore source.

Для human-view CSV exporter MUST:

1. видалити leading BOM лише для detection, не для source preservation;
2. для text field вважати небезпечним raw prefix tab/CR/LF або перший
   non-space code point `=`, `+`, `-`, `@`;
3. prefix небезпечну cell апострофом;
4. RFC-compatible quote/escape separators, quotes і newlines;
5. записати count трансформацій без cell contents.

Canonical JSON зберігає точне source value і захищений encryption/access
controls. Restore MUST NOT використовувати sanitized CSV як доказ exact
round-trip. Імпорт ніколи не eval-ить formulas, hyperlinks, macros або
text як code. `.xlsx` backup розглядається як potentially active content і
відкривається лише в protected mode; canonical restore не залежить від
нього.

## 9. Backup objective, schedule і retention

- **RPO:** не більше `24 hours`.
- Успішний encrypted canonical backup створюється щонайменше раз на добу
  після coherent pull або з останнього verified snapshot.
- Monitor MUST fail/alert, коли age останнього verified backup перевищує
  24 години.
- Retention: `35` rolling daily backups і `12` monthly backups.
- Monthly copy — останній успішно verified daily backup календарного
  місяця, promoted до окремого retention class.
- Retention deletion виконується лише після успішної перевірки новішої
  копії та з урахуванням active investigation hold.

Google Sheet, `.gsheet` pointer, working cache і SQLite mirror не
вважаються backup. XLSX MAY бути додатковою usability copy, але не замінює
canonical typed export і restore proof.

## 10. Копії, fault domains і encryption

Кожен retained backup MUST мати щонайменше **дві encrypted backup copies**
поза working cache у різних fault domains, наприклад:

- offline/removable local storage, від’єднане після запису;
- окремий remote object store/account.

Дві директорії, partitions або sync-folders одного пристрою/акаунта не є
різними fault domains. Primary Google Sheet не рахується однією з двох
backup copies.

Bundle шифрується client-side authenticated encryption до remote transfer;
transport також використовує TLS. Manifest усередині bundle зашифрований.
Зовнішній envelope містить лише format version, opaque backup ID, ciphertext
size/hash і encryption key ID — ніколи сам key чи personal metadata.

Encryption/recovery keys зберігаються окремо від обох copies. Має існувати
offline owner recovery material; його доступність перевіряється restore
procedure. Втрата ключа прирівнюється до втрати backup.

## 11. Exact backup manifest

Decrypted canonical bundle MUST містити `manifest.json` із:

- `manifest_version`, opaque `backup_id`, UTC `created_at`;
- `source_alias` і redacted source fingerprint;
- `snapshot_id`, snapshot content SHA-256 і pull timestamp;
- source schema, normalizer/exporter versions і code revision;
- expected authoritative tab list;
- для кожного tab: exact tab label, artifact relative path, media type,
  encoding, ordered headers/schema hash, row count, stable-ID count,
  sorted stable-ID-set SHA-256;
- для кожного artifact: byte length і SHA-256;
- relationships/count expectations: sessions, sets, program items,
  recommendations та expected zero-orphan constraints;
- canonical normalized-dataset SHA-256;
- encryption format/algorithm і non-secret key ID;
- `manifest_payload_sha256`, обчислений над canonical manifest з цим полем
  omitted.

Manifest MUST NOT містити raw Sheet locator, token, key, source cell values
або free-text notes. Paths є relative й MUST бути path-traversal safe.
Manifest canonicalization використовує UTF-8 JSON, lexicographically sorted
object keys, stable list ordering і no insignificant whitespace.

Для ciphertext bundle зовнішній envelope MUST зафіксувати exact byte length
і SHA-256, щоб corruption виявлявся до decrypt. Authenticity failure,
missing artifact, extra undeclared restore input, hash/count/ID mismatch
або unsupported version є hard failure.

## 12. Weekly offline isolated restore

Restore verification MUST успішно виконуватися щонайменше раз на `7 days`
для latest daily backup, а monthly class перевіряється при promotion.
Перевірка відбувається у fresh isolated location, не поверх working data.

Перед запуском staging отримує encrypted bundle і offline recovery
material. Потім restore process:

1. не має Google credentials і network access;
2. перевіряє ciphertext envelope, decrypt/authentication і manifest hash;
3. відхиляє absolute paths, `..`, symlinks та undeclared artifacts;
4. перевіряє exact artifact size/hash, expected tabs, headers, row counts,
   stable-ID counts і ID-set digests;
5. валідовує schema та rebuilding rules із pinned versions;
6. створює новий SQLite з empty state;
7. перевіряє uniqueness, foreign keys, zero orphan sets, current revisions
   і tombstone semantics;
8. обчислює normalized logical dataset fingerprint і порівнює з manifest;
9. виконує smoke queries history-by-workout і history-by-exercise;
10. створює redacted restore-evidence record і видаляє plaintext staging
    після завершення.

### Acceptance

Restore accepted лише якщо одночасно:

- процес доведено працював offline та без live Sheet;
- усі cryptographic/integrity checks збіглися;
- усі чотири authoritative tabs відновлені;
- stable IDs, exact row counts і relationship constraints збіглися;
- rebuilt SQLite queryable, foreign-key check чистий;
- normalized logical fingerprint дорівнює manifest;
- evidence містить backup ID, tested copy/fault domain, tool versions,
  start/end UTC, checks і `PASS`, але не персональні rows.

Будь-який mismatch дає non-zero exit, `FAIL`, зберігає лише encrypted
quarantine та redacted diagnostics і **не** оновлює дату останнього
успішного restore. Перевірка факту створення archive без цього acceptance
не є restore test.

## 13. Operational evidence й інциденти

Backup/restore ledger зберігає:

- opaque backup ID і retention class;
- creation/verification timestamps;
- ciphertext hashes та copy fault-domain aliases;
- restore status/evidence hash;
- expiration date й deletion result.

Ledger не містить source rows або keys і сам резервується. Якщо RPO,
copy count, encryption, hash або weekly restore порушено, CLI/monitor
показує actionable non-zero status. Corrupt copy не видаляється до
створення/перевірки replacement і завершення incident review.

Security incident procedure: припинити affected automation, revoke/rotate
реальні credentials, зберегти redacted evidence, оцінити disclosure scope,
відновити least privilege, виконати full-history scan та isolated restore.
Дії над public remote, sharing або Git history завжди залишаються явними
owner-controlled external actions.
