# Document-Ingest Synthesis

## Corpus

- Documents synthesized: 11
- ADR: 0
- SPEC: 2
- PRD: 0
- DOC: 9
- UNKNOWN: 0
- Classification confidence: 11 high, 0 medium, 0 low
- Per-document precedence overrides: 0
- Cross-reference cycle detection: passed, 0 cycles
- Maximum graph depth: 3 classified nodes of 50; 4 nodes including an external leaf

Percent-encoded references were decoded, source-relative paths were normalized,
and duplicate edges were collapsed before three-color DFS. The 27 raw
references produced 26 unique targets, 10 unique in-classification edges and
16 external leaves.

Non-conflict metadata notes:

- `/home/muuser/bushuk-labs/gym/.planning/intel/classifications/all-gym-exercises-77306ec0.json`
  names the equipment list twice after normalization; the duplicate edge was
  collapsed.
- `/home/muuser/bushuk-labs/gym/.planning/intel/classifications/WORKOUT-TRACKER-ARCHITECTURE-dec08252.json`
  resolves `settings.example.yaml` at repository root, while the current file
  is `/home/muuser/bushuk-labs/gym/config/settings.example.yaml`; this external
  reference-hygiene issue does not create a cycle or semantic conflict.

## Decisions

- Decisions extracted: 0
- Locked decisions: 0
- Locked-decision source paths: none
- Detail: /home/muuser/bushuk-labs/gym/.planning/intel/decisions.md

## Requirements

- Requirements extracted: 0
- Requirement IDs: none
- Competing acceptance variants: 0
- Detail: /home/muuser/bushuk-labs/gym/.planning/intel/requirements.md

## Constraints

- Constraints extracted: 29
- api-contract: 3
- schema: 7
- nfr: 7
- protocol: 12
- Detail: /home/muuser/bushuk-labs/gym/.planning/intel/constraints.md

## Context

- Context topics: 9
- Four-day upper/lower program
- Upper-strength session
- Lower-strength session
- Upper-hypertrophy session
- Lower-hypertrophy session
- Confirmed gym-equipment inventory
- Equipment-derived master exercise catalog
- Exercise taxonomy
- Curated exercise-selection reference
- Detail: /home/muuser/bushuk-labs/gym/.planning/intel/context.md

## Conflict Review

- Unresolved blockers: 0
- Competing variants: 0
- Auto-resolved precedence conflicts: 0
- Routing status: ready
- Report: /home/muuser/bushuk-labs/gym/.planning/INGEST-CONFLICTS.md

The current sources are semantically aligned:

- One fully qualifying exercise performance may trigger only the deterministic
  standard progression step; analytical program changes require at least
  three comparable performances, while v1 emits no progression output.
- All session warm-ups fit the progression SPEC's `0–8` minute budget;
  Lower Strength uses 7–8 minutes.
- Session prescriptions total 13 mandatory quadriceps sets, up to 15 with the
  optional lower-strength block, and 12 core sets, matching the program
  overview.
- Current architecture and progression prose use a generic medical/clinician
  boundary and contain neither a live Sheet locator nor personalized
  medication wording.

Alignment sources:

- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/README.md
- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/01 upper strength.md
- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/02 lower strength.md
- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/03 upper hypertrophy.md
- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/04 lower hypertrophy.md
- source: /home/muuser/bushuk-labs/gym/4-day upper lower program/05 progression and session rules.md
- source: /home/muuser/bushuk-labs/gym/WORKOUT_TRACKER_ARCHITECTURE.md

## Intel Files

- Decisions: /home/muuser/bushuk-labs/gym/.planning/intel/decisions.md
- Requirements: /home/muuser/bushuk-labs/gym/.planning/intel/requirements.md
- Constraints: /home/muuser/bushuk-labs/gym/.planning/intel/constraints.md
- Context: /home/muuser/bushuk-labs/gym/.planning/intel/context.md
- Conflict report: /home/muuser/bushuk-labs/gym/.planning/INGEST-CONFLICTS.md
