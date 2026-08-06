---
phase: 1
slug: standalone-workbook-and-four-programs
status: planned
nyquist_compliant: true
wave_0_complete: false
plan_map_complete: true
execution_complete: false
created: 2026-07-25
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pyproject.toml` — Plan 01-01, Wave 1 |
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

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | Planned Test/File Owner | Execution Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------------------|------------------|
| 01-01-T1 | 01-01 | 1 | Support | T-01-01 | Official uv bootstrap is preflighted before project commands | infrastructure | `command -v uv && uv --version && uv python find '>=3.12'` | `pyproject.toml` — 01-01 T1 | ⬜ planned, not executed |
| 01-01-T2 | 01-01 | 1 | Support | T-01-SC, T-01-02 | Exact approved dependency/source set; default collection performs no auth | contract | `uv lock --check && uv sync --locked && uv run pytest -q tests/contract/test_dependency_policy.py` | `tests/contract/test_dependency_policy.py` — 01-01 T2 | ⬜ planned, not created |
| 01-02-T1 | 01-02 | 2 | Support | T-01-03..05 | Strict safe YAML/Pydantic boundary and privacy-safe failures | contract | `uv run pytest -q tests/contract/test_contract_loading.py` | `tests/contract/test_contract_loading.py` — 01-02 T1 | ⬜ planned, not created |
| 01-03-T1 | 01-03 | 3 | REQ-WBK-01 | T-01-06..08 | Exact managed topology and fixed desired workbook properties | unit + contract | `uv run pytest -q tests/unit/test_topology.py tests/contract/test_contract_loading.py` | `tests/unit/test_topology.py` — 01-03 T1 | ⬜ planned, not created |
| 01-03-T2 | 01-03 | 3 | REQ-WBK-01 | T-01-06..08 | Unowned objects are preserved; mutable positions/provider IDs are not identity | contract | `uv run pytest -q tests/unit/test_topology.py tests/contract/test_gateway_contract.py` | `tests/contract/test_gateway_contract.py` — 01-03 T2 | ⬜ planned, not created |
| 01-04-T1 | 01-04 | 4 | REQ-WBK-02 | T-01-04..07 | Exact 31-row typed bootstrap, stable IDs and immutable version semantics | contract | `uv run pytest -q tests/contract/test_program_bootstrap.py` | `tests/contract/test_program_bootstrap.py` — 01-04 T1 | ⬜ planned, not created |
| 01-05-T1 | 01-05 | 5 | REQ-WBK-03 | T-01-08..12 | Allowlisted validations/protections, visible NULL/status behavior and mobile contract | contract | `uv run pytest -q tests/contract/test_input_contract.py` | `tests/contract/test_input_contract.py` — 01-05 T1 | ⬜ planned, not created |
| 01-05-T2 | 01-05 | 5 | REQ-WBK-03 | T-01-09 | Pure desired model carries logical reserve slots without random IDs | unit + contract | `uv run pytest -q tests/unit/test_workbook_model.py tests/contract/test_input_contract.py` | `tests/unit/test_workbook_model.py` — 01-05 T2 | ⬜ planned, not created |
| 01-06-T1 | 01-06 | 6 | REQ-WBK-04 | T-01-13..17 | Missing/incomparable data stays NULL/status; formula text is registry-owned | unit | `uv run pytest -q tests/unit/test_metrics_fixtures.py` | `tests/unit/test_metrics_fixtures.py` — 01-06 T1 | ⬜ planned, not created |
| 01-06-T2 | 01-06 | 6 | REQ-WBK-04 | T-01-13..17 | Dashboard filters/charts preserve cohort and NULL-gap semantics | contract + unit | `uv run pytest -q tests/unit/test_metrics_fixtures.py tests/contract/test_dashboard_contract.py` | `tests/contract/test_dashboard_contract.py` — 01-06 T2 | ⬜ planned, not created |
| 01-07-T1 | 01-07 | 7 | REQ-WBK-05 | T-01-18..20 | Apply allocates UUID4 only for missing logical slots; the second full cycle preserves all IDs and has zero operations | integration + contract | `uv run pytest -q tests/contract/test_reconcile_idempotency.py tests/contract/test_gateway_contract.py` | `tests/contract/test_reconcile_idempotency.py` — 01-07 T1 | ⬜ planned, not created |
| 01-08-T1 | 01-08 | 8 | Support | T-01-23 | Typed request allowlist, explicit masks, RAW text and apply-resolved reserve writes | contract | `uv run pytest -q tests/contract/test_google_request_compiler.py -k 'compiler or request'` | `tests/contract/test_google_request_compiler.py` — 01-08 T1 | ⬜ planned, not created |
| 01-08-T2 | 01-08 | 8 | Support | T-01-21..24 | 0600 file/0700 directory gate precedes auth; locale/timezone drift is managed and exact post-state is required | contract | `uv run pytest -q tests/contract/test_google_request_compiler.py` | `tests/contract/test_google_request_compiler.py` — 01-08 T2 | ⬜ planned, not created |
| 01-09-T1 | 01-09 | 9 | UAT support | T-01-25..29 | Safe runner rejects zero executed tests and preserves redacted evidence | contract | `uv run pytest -q tests/contract/test_google_uat_runner.py` | `tests/contract/test_google_uat_runner.py` — 01-09 T1 | ⬜ planned, not created |
| 01-09-T2 | 01-09 | 9 | UAT support | T-01-25..29 | Live tests cover clean property initialization, formulas/dashboard and stable reserve IDs on an empty second plan | collection contract | `uv run pytest -q tests/contract/test_google_uat_runner.py && uv run pytest -q --collect-only tests/uat/test_clean_workbook.py tests/uat/test_formula_results.py tests/uat/test_second_run.py` | three `tests/uat/` modules — 01-09 T2 | ⬜ planned, not created |
| 01-09-T3 | 01-09 | 9 | UAT gate | T-01-25..29 | Live apply and manual mobile/rendering proof run only on a permission-safe disposable target | live automated + human | `uv run python scripts/run_google_uat.py` | `scripts/run_google_uat.py` and UAT modules — 01-09 T3 | ⬜ planned checkpoint, not executed |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Planned Infrastructure Ownership

- [ ] Plan 01-01, Wave 1 owns `pyproject.toml`, `uv.lock`, package skeleton,
  pytest configuration, `tests/conftest.py`, and the default-safe `google_uat`
  marker behavior.
- [ ] Plan 01-03, Wave 3 owns `config/workbook-blueprint.yaml`, the in-memory
  gateway seam, and its shared gateway contract tests.
- [ ] Plan 01-04, Wave 4 owns `config/program-bootstrap.yaml` and its exact
  four-complex contract suite.
- [ ] Plan 01-06, Wave 6 owns `tests/fixtures/metrics-v1.yaml`.
- [ ] Plan 01-09, Wave 9 owns the live-only UAT modules and fail-closed runner.

`wave_0_complete: false` records that no implementation/scaffold wave has run;
there is no unresolved ownership/TBD in the finalized plan map. The
`nyquist_compliant: true` and `plan_map_complete: true` fields describe plan
coverage only. They do not claim that files exist, tests pass, or UAT is
complete; those remain pending until execution.

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

- [x] Every finalized plan task has an automated verification command
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Every planned test/infrastructure artifact has explicit plan/task/wave ownership
- [ ] No watch-mode flags
- [ ] Feedback latency <180s
- [ ] Full unit/contract suite passes
- [ ] Required live UAT evidence is recorded without sensitive data
- [x] `nyquist_compliant: true` records complete plan-level verification mapping

**Approval:** pending
