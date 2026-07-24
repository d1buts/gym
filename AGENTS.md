# AGENTS.md

These instructions apply to the entire repository.

## Mission

Build a privacy-preserving, evidence-backed workout tracker whose local state
can always be reconstructed from authoritative source data and versioned
rules. Reliability and traceability take priority over feature count.

## Read before changing anything

1. `.planning/PROJECT.md`
2. `.planning/REQUIREMENTS.md`
3. `.planning/STATE.md`
4. The relevant phase in `.planning/ROADMAP.md`
5. `WORKOUT_TRACKER_ARCHITECTURE.md`
6. The relevant normative files under `docs/architecture/`
7. `config/schema.yaml` and `config/progression-rules.yaml`

Treat `.planning/intel/` as generated ingest evidence. Do not hand-edit it
unless the GSD ingest workflow explicitly requires regeneration.

## Accepted decisions

- Python 3.12+ local CLI.
- uv-style dependency management.
- Pydantic validation boundary.
- SQLite v1 analytical store.
- Google Sheets remains authoritative for operational facts and versioned
  program prescriptions.
- Git owns schemas, normalization, formulas, executable rules, tests and
  documentation.
- V1 is read-only. Workout capture, write-back and generated recommendations
  are v2.

Changing any of these requires an ADR and updates to `PROJECT.md`,
`REQUIREMENTS.md`, roadmap traceability and affected contracts.

## Non-negotiable data rules

- Never use a row number as identity.
- Require source-owned `session_id`, `set_id`, `program_item_id` and
  `recommendation_id`.
- Never invent a missing value. Preserve unknown as `NULL`.
- Keep raw source facts separate from Sheet-calculated and local-derived
  values.
- Preserve source value, unit, basis and provenance before conversion.
- Keep exercise family, exact variant, equipment and comparison cohort
  distinct.
- Link every new session to the program version used.
- A repeated pull of the same logical input must not change the mirror.
- Invalid authoritative session/set bundles must not partially replace the
  active mirror.

## Sync safety

- Use read-only Google authorization in v1.
- Capture all four expected tabs as one version-fenced unit.
- Write immutable snapshots through staging and a completion marker.
- Validate and normalize before opening the SQLite promotion transaction.
- Promote staged state and mirror head atomically.
- A failure must leave the previous complete mirror active.
- Logs contain IDs, hashes, counts and error codes—not tokens, notes, symptoms,
  body mass, Sheet locators or raw row payloads.

## Metric safety

- Follow `docs/architecture/METRICS.md`; do not create ad-hoc formulas.
- Warm-ups and invalid/aborted sets do not count as working volume.
- Missing or incomparable input produces a status and `NULL`, never zero.
- e1RM uses the pinned formula and eligibility window only.
- Do not compare different variants, equipment setups, load bases or
  assistance semantics.
- Recovery analysis in v1 is descriptive and cannot claim causation.
- Deterministic progression is not an AI recommendation.

## Privacy and repository hygiene

- This remote has a known public-history disclosure; do not repeat sensitive
  values in issues, commits, logs or documentation.
- Never commit credentials, populated `.env`, live Sheet locators, raw or
  processed personal data, SQLite files, reports, logs or backups.
- Before committing, inspect `git status`, staged paths and a secret/privacy
  scan.
- Do not change GitHub visibility, rewrite published history, rotate a Sheet
  or alter its sharing without explicit owner authorization.
- Do not send workout or health-context data to an LLM, telemetry system or
  external service as part of v1.

## Medical boundary

Pain, soreness, sleep, stress, nausea, dizziness and performance are
self-reported context, not diagnoses. Do not infer injury, medication
reaction, dehydration, overtraining or treatment. Acute, severe or persistent
symptoms require a qualified medical professional.

## Documentation and naming

- Human-facing documentation is Ukrainian.
- Code identifiers, schema keys, requirement IDs and standard technology
  names remain English.
- Google Sheet titles and source labels are Ukrainian and exact; English names
  are internal aliases only.
- Use stable snake_case identifiers in code and YAML.
- When changing a source column, formula or rule, bump the appropriate
  contract/normalizer/formula/ruleset version and update tests and docs in the
  same change.

## GSD workflow

- Use `.planning/STATE.md` to determine the current phase.
- Discuss/plan a phase before execution unless the requested task is
  explicitly trivial.
- Every v1 requirement must map to exactly one phase.
- Do not mark a requirement complete until implementation, automated
  verification and required UAT/restore evidence all pass.
- Keep phase work scoped; deferred v2 features must not leak into v1.

## Verification

For documentation-only changes:

- parse all YAML files;
- run `git diff --check`;
- verify relative Markdown links;
- scan tracked text for live identifiers, credentials and prohibited personal
  data;
- confirm requirement-to-phase coverage remains complete.

When Python implementation exists, use the project’s documented uv commands
for formatting, static checks and pytest. Do not invent commands before the
corresponding configuration exists.
