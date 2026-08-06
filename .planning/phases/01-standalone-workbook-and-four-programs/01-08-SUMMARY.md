---
phase: 01-standalone-workbook-and-four-programs
plan: 08
subsystem: google-sheets-transport
tags: [google-sheets, oauth, request-compiler, cli, redaction, tdd]
dependency-graph:
  requires:
    - "01-06 pinned FormulaRegistry and cohort-safe workbook formulas"
    - "01-07 typed ChangePlan, canonical fingerprint and reconciliation"
  provides:
    - "Dependency-ordered allowlisted Sheets v4 request compiler"
    - "Preflighted installed-user Google Sheets gateway with redacted errors"
    - "Credential-free validation and dry-run CLI plus explicit guarded apply"
  affects: [01-09, phase-02]
tech-stack:
  added: []
  patterns:
    - "ChangePlan operations are the only input to the Google request boundary"
    - "OAuth material is resolved outside CLI arguments after exact 0600/0700 checks"
    - "External failures become stable privacy-safe codes before formatting"
key-files:
  created:
    - src/workout_tracker/workbook/requests.py
    - src/workout_tracker/adapters/google_sheets.py
    - src/workout_tracker/cli.py
    - tests/contract/test_google_request_compiler.py
  modified: []
key-decisions:
  - "The transport requests exactly the Sheets write scope and accepts only installed-user authorized tokens; no Drive or service-account fallback exists."
  - "Observed locale/timezone differences are reconciled changes, while exact uk_UA/America/New_York values are mandatory after apply."
  - "Formula source text remains registry-owned; transport substitutions are fixed Git-owned column expressions and never caller formula text."
patterns-established:
  - "Google dry-run compiles the offline desired/reconciliation summary without importing credentials, discovery state or a live locator."
  - "Preflight errors expose only stable codes; paths, locators, tokens and provider bodies never reach CLI output."
requirements-completed: []
coverage:
  - id: D1
    description: "Typed ChangePlan operations compile into bounded dependency-ordered Sheets requests with explicit masks, RAW source strings, registry-only formulas and apply-resolved reserve IDs."
    verification:
      - kind: integration
        ref: "tests/contract/test_google_request_compiler.py"
        status: pass
      - kind: integration
        ref: "complete managed blueprint compiler probe"
        status: pass
    human_judgment: false
  - id: D2
    description: "Installed-user Google transport and CLI enforce disposable identity, exact permission modes, minimum Sheets scope, stale-state fencing, exact post-properties and redacted output."
    verification:
      - kind: integration
        ref: "tests/contract/test_google_request_compiler.py"
        status: pass
    human_judgment: false
duration: 13min
completed: 2026-07-30
status: complete
---

# Phase 01 Plan 08: Guarded Google Sheets Transport Summary

**Typed Sheets request compilation, installed-user OAuth preflight and a redacted setup CLI that keeps every dry-run offline while fail-closing live mutation**

## Performance

- **Duration:** 13 хв
- **Started:** 2026-07-31T00:06:01Z
- **Completed:** 2026-07-31T00:18:39Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Реалізовано pure `ChangePlan` → Sheets v4 compiler із dependency batches, explicit field masks, bounded managed ranges, RAW text cells, registry-only formulas та secure apply-resolved reserve UUID4.
- Додано `GoogleSheetsGateway`, який до auth перевіряє fixed desired properties, disposable test identity, exact `0600` files/`0700` directory, installed-user client type і minimum Sheets scope; stale fingerprint та неточний post-state fail closed.
- CLI `validate`, memory dry-run/apply і Google dry-run не потребують Google credentials або network; live apply вимагає окремий `--apply`, untracked runtime configuration і повертає лише allowlisted hashes/counts/kinds/status або redacted code.

## Task Commits

TDD gates та post-verification fix зафіксовано атомарно:

1. **Task 1 RED: request compiler contract** — `a0134c4` (test)
2. **Task 1 GREEN: allowlisted request compiler** — `322509b` (feat)
3. **Task 2 RED: gateway and CLI safety contract** — `a26db94` (test)
4. **Task 2 GREEN: guarded gateway and CLI** — `2cdb7ff` (feat)
5. **Rule 1 fix: complete managed formula compilation** — `90fe11e` (fix)

## Files Created/Modified

- `src/workout_tracker/workbook/requests.py` — typed operation allowlist, exact masks, RAW/formula separation, bounded ranges and dependency batches.
- `src/workout_tracker/adapters/google_sheets.py` — installed-user token loading, permission/target preflight, narrow observation, bounded batch apply and redacted failures.
- `src/workout_tracker/cli.py` — offline validate/dry-run/apply commands and guarded live apply without secret-bearing arguments.
- `tests/contract/test_google_request_compiler.py` — compiler, permission, fixed-property, post-state, redaction and forbidden-capability contract.

## Decisions Made

- The existing D-20 dependency boundary remains unchanged. The adapter consumes an installed-app authorized token through `google-auth`; it does not add `google-auth-oauthlib`, hand-roll OAuth, or introduce a service-account path.
- Google dry-run is deliberately an offline plan summary. Authentication and discovery occur only for the explicit live apply path.
- A clean target’s provider-default locale/timezone is not rejected during identity preflight; reconciliation must change them and post-apply observation must prove exact `uk_UA` and `America/New_York`.

## TDD Evidence

- **Task 1 RED:** four compiler tests collected and failed only on the behavior-specific assertion that `requests.py` was absent.
- **Task 1 GREEN:** targeted compiler contract passed `4 passed`; existing reconciliation/gateway suite passed `16 passed`.
- **Task 2 RED:** five gateway/CLI tests collected and failed only on the behavior-specific assertion that the gateway/CLI files were absent.
- **Task 2 GREEN:** complete transport contract passed `9 passed`; full offline suite passed `85 passed`.
- **REFACTOR:** no separate refactor commit was needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Completed registry virtual-column resolution and narrowed wildcard detection**
- **Found during:** Overall verification after Task 2
- **Issue:** The complete-blueprint probe exposed unresolved registry virtual columns, and the initial wildcard guard treated legitimate formula multiplication as a wildcard field mask.
- **Fix:** Added fixed Git-owned expressions for the registry’s derived column tokens, fully qualified source-tab references, and a structural check that rejects only an exact `fields: "*"` mask.
- **Files modified:** `src/workout_tracker/workbook/requests.py`
- **Verification:** Complete 2,424-operation blueprint compiled one request per operation; targeted 9 tests and full 85-test suite passed.
- **Committed in:** `90fe11e`

---

**Total deviations:** 1 auto-fixed (1 bug).
**Impact on plan:** The fix was required for complete managed-blueprint correctness and did not add dependencies, live calls or new authority.

## Issues Encountered

- Context7 tooling and its local CLI fallback were unavailable, so current official Google Sheets request/field-mask and Python installed-app guidance was checked directly before implementation.
- Repository-wide relative-link scan reports pre-existing percent-encoded Markdown link false negatives; no documentation links were changed by this plan.

## Authentication Gates

None. No credential, locator, OAuth flow or live Google request was used.

## Known Stubs

None.

## User Setup Required

No setup was performed in this plan. Plan 01-09 retains the explicit owner-controlled disposable target, installed-app authorization and live/manual UAT checkpoint; sensitive runtime values remain outside Git and CLI arguments.

## Verification

- `uv run pytest -q tests/contract/test_google_request_compiler.py` — 9 passed.
- `uv run pytest -q` — 85 passed.
- Complete clean-workbook `ChangePlan` compiled into 2,424 allowlisted requests across dependency batches.
- `uv run python -m compileall -q src`, `uv lock --check`, all 7 repository YAML parses and `git diff --check` passed.
- CLI help, default collection and `google-dry-run` completed without authentication or network.
- Tracked credential/private-key/live-locator scan passed; stub review found only ordinary empty local accumulators and optional type defaults.

## Next Phase Readiness

Plan 01-09 can consume the production gateway/CLI and canonical fixtures for the explicitly authorized disposable Google test target. Live Google mutation and human UAT remain pending and were not started.

## Self-Check: PASSED

- All four created implementation/test files exist.
- Commits `a0134c4`, `322509b`, `a26db94`, `2cdb7ff` and `90fe11e` exist in history.
- Compiler acceptance, permission/identity/redaction contract, full offline suite, YAML parse, CLI offline checks and privacy/stub/threat review passed.
- Plan 01-09 and all live Google/UAT actions remain untouched.

---
*Phase: 01-standalone-workbook-and-four-programs*
*Completed: 2026-07-30*
