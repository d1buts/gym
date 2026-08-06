# Document-Ingest Synthesis

## Corpus

- Documents synthesized: 21
- ADR: 3
- SPEC: 8
- PRD: 1
- DOC: 9
- UNKNOWN: 0
- Classification confidence: 21 high, 0 medium, 0 low
- Per-document precedence overrides: 0
- Cross-reference cycle detection: passed, 0 synthesis-dependency cycles
- Maximum traversal depth: below cap 50

Source-relative paths and percent-encoded references were normalized before
three-color DFS. Shorthand ADR mentions and external normative links were
retained as provenance references; they do not require recursive content
expansion and therefore do not create synthesis-dependency edges.

## Decisions

- Decisions extracted: 3
- Locked decisions: 3
- Locked-decision sources:
  - /home/muuser/bushuk-labs/gym/docs/architecture/ADR-001-authority-boundaries.md
  - /home/muuser/bushuk-labs/gym/docs/architecture/ADR-002-python-sqlite-v1.md
  - /home/muuser/bushuk-labs/gym/docs/architecture/ADR-003-spreadsheet-first-product.md
- Detail: /home/muuser/bushuk-labs/gym/.planning/intel/decisions.md

ADR-003 explicitly supersedes only ADR-001's earlier read-only v1 consequence
and refines ADR-002 by retaining Python/SQLite as an auxiliary layer. The
accepted authority boundaries, runtime stack and Spreadsheet-first write path
are complementary rather than contradictory.

## Requirements

- Requirements extracted: 26
- Workbook: 5 (`REQ-WBK-01`–`REQ-WBK-05`)
- ChatGPT capture: 6 (`REQ-CAP-01`–`REQ-CAP-06`)
- Reading and analytics: 5 (`REQ-ANL-01`–`REQ-ANL-05`)
- Recommendations: 5 (`REQ-REC-01`–`REQ-REC-05`)
- Privacy, audit and recovery: 5 (`REQ-SAFE-01`–`REQ-SAFE-05`)
- Competing acceptance variants: 0
- Detail: /home/muuser/bushuk-labs/gym/.planning/intel/requirements.md

## Constraints

- Constraints extracted: 41
- api-contract: 3
- schema: 10
- nfr: 10
- protocol: 18
- Detail: /home/muuser/bushuk-labs/gym/.planning/intel/constraints.md

The constraints preserve the exact authority split, stable identity,
version-fenced pull, atomic promotion, metric eligibility, workbook topology,
controlled ChatGPT confirmation/write protocol, privacy boundary and isolated
restore contract.

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

Each topic retains attributed source notes fenced with a unique randomized
untrusted-data marker; the complete authoritative document remains at its
listed `source` path.

## Conflict Review

- Unresolved blockers: 0
- Competing acceptance variants: 0
- Auto-resolved precedence conflicts: 0
- Routing status: ready
- Report: /home/muuser/bushuk-labs/gym/.planning/INGEST-CONFLICTS.md

The PRD, SPECs and DOC context are aligned with all three locked ADRs. No
lower-precedence statement required rewriting, and the single PRD cannot
produce cross-PRD acceptance variants.

## Intel Files

- Decisions: /home/muuser/bushuk-labs/gym/.planning/intel/decisions.md
- Requirements: /home/muuser/bushuk-labs/gym/.planning/intel/requirements.md
- Constraints: /home/muuser/bushuk-labs/gym/.planning/intel/constraints.md
- Context: /home/muuser/bushuk-labs/gym/.planning/intel/context.md
- Conflict report: /home/muuser/bushuk-labs/gym/.planning/INGEST-CONFLICTS.md
