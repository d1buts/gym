# Architecture Review

> **Historical review.** Цей документ описує попередній read-only milestone і
> не є поточним product verdict. Spreadsheet-first scope прийнято в ADR-003;
> актуальні requirement counts і phases визначаються новим GSD ingest.

**Reviewed:** 2026-07-24

**Method:** Open GSD document ingest, conflict synthesis, roadmapping and
three focused audits

**Corpus:** 11 documents — 2 SPEC, 9 DOC

## Verdict

Початкова архітектура мала правильну форму, але була design narrative, а не
implementation contract. Після допрацювання вона придатна для phase
planning: ownership boundaries, source schema, stable identities, sync
semantics, metric formulas, privacy controls і restore acceptance винесені в
нормативні документи.

Код v1 ще не реалізований. Позначка `0 conflicts` у GSD означає, що ingest
джерела не суперечать одне одному; вона не означає, що продукт уже готовий.

## GSD results

- Initial reference graph: 10 navigation cycles.
- Final reference graph: acyclic.
- Initial semantic variants:
  - one-session deterministic progression проти three-session analytical
    recommendation;
  - inconsistent quadriceps/core weekly volume;
  - 7–9 minute warm-up проти 0–8 minute session budget.
- Final conflict report: 0 blockers, 0 warnings, 0 info.
- Derived v1 requirements: 22.
- Roadmap: 5 sequential phases with 22/22 unique mappings.

Попередні blocked/warning attempts збережені локально під
`.planning/attempts/` і виключені з Git, оскільки можуть містити verbatim
source snapshots.

## Findings and disposition

### Resolved in the source documents

1. Navigation uses `4-day upper lower program/README.md` as a one-way hub.
2. One qualifying performance can trigger only the deterministic standard
   progression step; program-changing analysis requires at least three
   comparable session occurrences.
3. Weekly volume is reconciled at 13 mandatory quadriceps sets, up to 15
   optional, and 12 core sets.
4. Lower-strength warm-up is 7–8 minutes.
5. Personalized medication wording and the live Sheet locator were removed
   from current files.

### Resolved by normative contracts

1. Source-owned `set_id`, `program_item_id` and `recommendation_id` are
   mandatory; `session_id` alone is insufficient.
2. Program prescriptions are versioned and linked to sessions.
3. One logical set can have bilateral, each-side or separate left/right
   components and can be repetition- or duration-based.
4. Load value, unit, basis, implement count, variant, equipment and setup
   cohort are explicit.
5. Pull is a coherent four-tab snapshot with immutable manifest, validation,
   quarantine and atomic SQLite promotion.
6. Corrections create revisions under the same identity; disappearance from
   a complete snapshot creates a tombstone.
7. Volume is a typed family of metrics rather than one scalar.
8. e1RM, RIR, rest and recovery semantics are pinned and versioned.
9. Backup has concrete RPO, retention, encryption and restore-proof
   acceptance.

### External privacy blocker

The remote repository was verified as public, and already-pushed history
contains a Sheet locator and personalized health context. Current-file
sanitization and `.gitignore` prevent new exposure but do not erase history.

Repository visibility, Sheet sharing/rotation and history rewrite affect
external state and require an explicit owner decision. Until remediated,
`PRIV-01` cannot be considered complete.

## Architecture score after refinement

- Component boundaries: strong
- Authority model: explicit
- Data model: implementation-ready contract
- Sync reliability: implementation-ready protocol
- Metrics: deterministic v1 definitions
- Privacy: local controls defined; remote-history action outstanding
- Delivery readiness: ready for `$gsd-plan-phase 1`, not for execution without
  a phase plan

## Normative documents

- [Architecture overview](../../WORKOUT_TRACKER_ARCHITECTURE.md)
- [Authority boundaries](ADR-001-authority-boundaries.md)
- [Python and SQLite decision](ADR-002-python-sqlite-v1.md)
- [Data model](DATA_MODEL.md)
- [Synchronization protocol](SYNC_PROTOCOL.md)
- [Metric contract](METRICS.md)
- [Security and backup](SECURITY_AND_BACKUP.md)
- [Source schema](../../config/schema.yaml)
- [Progression rules](../../config/progression-rules.yaml)
