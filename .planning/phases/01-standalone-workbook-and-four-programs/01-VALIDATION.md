---
phase: 1
slug: standalone-workbook-and-four-programs
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-25
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pyproject.toml` — Wave 0 installs |
| **Quick run command** | `uv run pytest -q tests/unit tests/contract` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | <60 seconds for quick suite; <180 seconds full suite |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest -q tests/unit tests/contract`
- **After every plan wave:** Run `uv run pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 180 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-W0-01 | TBD | 0 | REQ-WBK-01..05 | T-01-01 | Dependencies pinned; no credential or locator in project config | infrastructure | `uv run pytest -q` | ❌ W0 | ⬜ pending |
| 01-WBK-01 | TBD | TBD | REQ-WBK-01 | T-01-02 | Exact managed topology; unmanaged objects are not deleted | unit + UAT | `uv run pytest -q tests/unit/test_topology.py tests/uat/test_clean_workbook.py` | ❌ W0 | ⬜ pending |
| 01-WBK-02 | TBD | TBD | REQ-WBK-02 | T-01-03 | Strict typed bootstrap preserves exact prescriptions and cohorts | contract | `uv run pytest -q tests/contract/test_program_bootstrap.py` | ❌ W0 | ⬜ pending |
| 01-WBK-03 | TBD | TBD | REQ-WBK-03 | T-01-04 | Only allowlisted validations/protections and formula registry are compiled | contract + UAT | `uv run pytest -q tests/contract/test_input_contract.py` | ❌ W0 | ⬜ pending |
| 01-WBK-04 | TBD | TBD | REQ-WBK-04 | T-01-05 | Missing/incomparable data stays NULL/status; formula text cannot come from user input | unit + UAT | `uv run pytest -q tests/unit/test_metrics_fixtures.py tests/uat/test_formula_results.py` | ❌ W0 | ⬜ pending |
| 01-WBK-05 | TBD | TBD | REQ-WBK-05 | T-01-06 | Second apply is a no-op; stale target fingerprint fails closed | integration + UAT | `uv run pytest -q tests/contract/test_reconcile_idempotency.py tests/uat/test_second_run.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` and `uv.lock` — Python 3.12+, Pydantic, PyYAML,
  Google API/auth clients and pytest.
- [ ] `src/workout_tracker/` package skeleton with pure domain and gateway
  boundaries.
- [ ] `config/workbook-blueprint.yaml` — strict versioned managed-object
  contract.
- [ ] `config/program-bootstrap.yaml` — four exact complexes including
  Dumbbell Romanian deadlift for Lower Hypertrophy C1.
- [ ] `tests/conftest.py` and isolated unit/contract/UAT fixtures.
- [ ] In-memory gateway plus shared gateway contract suite.
- [ ] `google_uat` marker that skips unless explicit safe local opt-in passes.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Narrow-mobile journey from `Старт` to a complex and manual session/set input | REQ-WBK-03 | Google Sheets mobile layout and tap targets cannot be proven by request snapshots alone | Open a disposable test Spreadsheet on a phone/narrow viewport; reach each complex in one tap; enter one session and child set without editing system/formula columns; record only pass/fail and non-sensitive defect notes |
| Formula recalculation and chart rendering in Google Sheets | REQ-WBK-04 | Local evaluator cannot fully reproduce Google recalculation/rendering | Apply blueprint to disposable test Sheet, load non-personal canonical fixtures, wait for recalculation, compare displayed values/status and chart series to expected fixtures |
| Clean apply and second-run no-op on Google infrastructure | REQ-WBK-05 | Requires actual Sheets API semantics | With explicit test-only opt-in, apply once, read managed fingerprint, apply again and confirm empty change plan plus identical logical hash |

---

## Live UAT Safety Gate

Before any Google call require explicit `--apply`, a test-only source alias,
untracked locator resolution, credential resolution without CLI secrets,
identity/title preflight, disposable-target confirmation, minimum Sheets
scope and active redaction. Refuse broad selection, production-like alias,
unsafe credential permissions or missing test marker.

UAT evidence may contain only source alias, contract/version hashes, managed
object counts, change kinds, redacted error code and pass/fail. It must not
contain Spreadsheet ID/URL, token, credential path, workout values or raw
Google error bodies.

---

## Validation Sign-Off

- [ ] All tasks have automated verification or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all missing references
- [ ] No watch-mode flags
- [ ] Feedback latency <180s
- [ ] Full unit/contract suite passes
- [ ] Required live UAT evidence is recorded without sensitive data
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
