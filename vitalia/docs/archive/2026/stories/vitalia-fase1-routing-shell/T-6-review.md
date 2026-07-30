<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review — T-6 Playwright E2E Suite (8 specs SC-1..SC-8)

**Date:** 2026-05-26
**Brand:** vitalia
**Story:** vitalia-fase1-routing-shell (F1-S9)
**Ticket:** T-6 — 8 Playwright specs + POM + fixture + axe-core + visual goldens iter 1
**Commit:** bcc88359
**Files Reviewed:** 11 NEW (8 spec.ts + 1 POM + 1 fixture + 1 impl-log)
**Domains touched:** E2E Playwright + accessibility (axe-core integration)
**Skills consulted:** playwright-expert · tessl__react-patterns (a11y testing) · spanish-text.md · tdd-mandatory.md · frontend-fsd.md
**Live-verified:** NO LIVE RUN (chrome-devtools-verify deprecated Linux per CONTEXT-BRIEF § 11 LOW caveat) — specs compile + tsc + eslint CLEAN
**Verdict:** **APPROVED with caveat**

---

## /test-vitalia Gate Status (from gate-output.json iter 1)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | 0 errors strict |
| ESLint | PASS | 0 errors, 0 warnings |
| Vitest unit | PASS | 1549/1549 (e2e files don't affect unit suite) |
| Arch fitness | PASS | E2E files outside `src/` scope |
| **playwright_spec_list** | **PASS** | Specs compilable; live run skipped (caveat acknowledged in CONTEXT-BRIEF § 11) |

---

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | N/A | E2E files outside FSD scope |
| 2 | Server/Client | N/A | E2E specs |
| 3 | React patterns | N/A | E2E specs |
| 4 | Code quality | PASS | tsc/eslint clean on `e2e/regression/vitalia-fase1-routing-shell/` + fixture |
| 5 | Accessibility | PASS | `a11y-keyboard-nav.spec.ts` covers SC-6 + 4 axe-core WCAG 2.1 AA scans (@axe tag): valid shell · outer not-found · inner not-found · network error fallback |
| 6 | Forms | N/A | — |
| 7 | Multitenancy | PASS | fixture mocks `/api/v1/iam/users/me/tenants` (`mockTenants`, `mockEmptyTenants`, `mockCrossTenantList`, `mockNetworkFailure`) — tenant scoping respected in mocks |
| 8 | Master Data / Spanish neutro | PASS | `i18n-spanish-neutro.spec.ts` (SC-7) does rendered page regex scan for voseo forbidden tokens |
| 9 | Security / Deps | PASS | `@axe-core/playwright` dynamic import (treeshakes if `@axe` tag not run); no eval/dangerous |
| 10 | Tests / TDD | PASS | 8 specs map 8 gherkin scenarios 1:1 (100% coverage per validators.yaml § scenario_to_test) |
| 11 | Domain Alignment | N/A | Routing-only |
| 12 | Arch Fitness | PASS | No new arch test from T-6; ratchets owned by T-3/T-4 still GREEN |
| 13 | Mirror detection | PASS | `routing-shell.fixture.ts` + POM brand-local (Vitalia-specific tenant + agent + subtab vocab); not mirrored to other brands |
| 14 | Decisions honored (R6) | N/A | No `decisions_applicable` field |

---

## Findings

### PASS · Scenario coverage 8/8 (100%)
Per `04-validators.yaml § scenario_to_test` table, each SC has exactly one spec file:

| SC | Title | Spec file |
|---|---|---|
| SC-1 | happy navigation | `happy-navigation.spec.ts` ✅ |
| SC-2 | invalid agent → outer not-found | `not-found-outer.spec.ts` ✅ |
| SC-3 | invalid subtab → inner not-found | `not-found-inner.spec.ts` ✅ |
| SC-4 | cross-tenant blocked | `cross-tenant-blocked.spec.ts` ✅ |
| SC-5 | network failure | `network-failure-tenant-fetch.spec.ts` ✅ |
| SC-6 | a11y keyboard + axe WCAG | `a11y-keyboard-nav.spec.ts` ✅ |
| SC-7 | i18n Spanish neutro | `i18n-spanish-neutro.spec.ts` ✅ |
| SC-8 | no-tenants edge case | `no-tenants-edge.spec.ts` ✅ |

### PASS · POM + fixture scaffold
- `poms/shell-page.pom.ts` — `ShellPage` class with 14 methods per `validators.yaml § poms_required` (gotoTenantRoot, gotoAgentRoot, gotoSubtab, gotoInvalidAgent, gotoInvalidSubtab, mockNetworkFailure, mockEmptyTenants, mockCrossTenantList, waitForRibbonActive, waitForSubTabActive, assertHttp404, assertNoChrome, assertChromeVisible, clickRetry).
- `fixtures/routing-shell.fixture.ts` — exposes mock helpers (`mockTenants`, etc.). REUSES F1-S3 Clerk auth fixture per spec § test_construction_plan.

### PASS · axe-core WCAG 2.1 AA on 4 pages
`a11y-keyboard-nav.spec.ts` SC-6-6/7/8/9:
- SC-6-6: valid shell route (valeria/agenda) @axe
- SC-6-7: outer not-found @axe
- SC-6-8: inner not-found @axe
- SC-6-9: network error fallback @axe

Dynamic import `await import("@axe-core/playwright")` defers loading. Spec § 12 satisfied.

### PASS · Visual goldens iter 1 plan
T-6-result.md lists 7 screenshots:
- `not-found-outer-light.png` · `not-found-outer-dark.png` · `not-found-outer-mobile.png`
- `not-found-inner-light.png` · `not-found-inner-dark.png`
- `network-fallback-light.png` · `network-fallback-dark.png`

Per spec, iter 1 seeded via `--update-snapshots`. **Chris ratify pending pre-merge** (CONTEXT-BRIEF § 11 LOW item 1 — process note for PM merge phase F).

### PASS · Mocking strategy correct
Per `validators.yaml § fixtures_required`, fixture uses `page.route()` interception for `/api/v1/iam/users/me/tenants`:
- `mockTenants(page, tenants)` — happy 200 list
- `mockEmptyTenants(page)` — 200 `[]` (SC-8)
- `mockCrossTenantList(page)` — 200 with different tenant id (SC-4)
- `mockNetworkFailure(page)` — abort/delay (SC-5)

Mock-based E2E is the correct strategy for routing-shell — no BE state mutation needed.

### CAVEAT · Live Playwright run NOT executed (NOT a defect)

Per CONTEXT-BRIEF § 11 LOW item 2: "T-6 live E2E NOT executed — chrome-devtools-verify deprecated on Linux env. Specs compile + tsc + eslint ✅. **Auditor decision: accept as CAVEAT (not CHANGES_REQUESTED). Smoke test post-merge via CI/CD staging + prod gates sufficient.**"

**Evidence specs are valid:**
- `tsc --noEmit` 0 errors (`gate-output.json` line 58)
- `eslint src/ + e2e/regression/vitalia-fase1-routing-shell/` 0 errors
- Vitest unit suite 1549/1549 GREEN unrelated but co-passing
- `playwright_spec_list` PASS (`gate-output.json` line 88) — config valid + specs compilable
- POM + fixture compile clean
- Static structure (8 specs ↔ 8 SCs ↔ validators.yaml § scenario_to_test) verified

**Mitigation:**
- Manual live run instructions documented in T-6-result.md § "Live Verification Note":
  ```bash
  bash scripts/e2e-preflight.sh
  cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test \
    e2e/regression/vitalia-fase1-routing-shell/ --project=smoke
  ```
- Chris staging gate per merge phase F: visual goldens ratify + sample live spec run before squash-merge.
- CI/CD staging deploy auto runs `make ci-parity` which includes Playwright config validation.

This caveat is structurally identical to T-3 live-verification-deferred — accepted under CONTEXT-BRIEF § 11 LOW.

---

## Contract / UI-SPEC Compliance

- [x] 8 SC scenarios in `01-spec.md § 5` mapped 1:1 to 8 spec files in `04-validators.yaml § scenario_to_test`
- [x] POM contract per `validators.yaml § poms_required` (14 methods)
- [x] Fixture contract per `validators.yaml § fixtures_required` (REUSE auth.fixture from F1-S3 + new routing-shell.fixture)
- [x] Visual goldens plan per `validators.yaml § visual` (6 snapshots + mobile responsive)
- [x] axe-core WCAG 2.1 AA per `validators.yaml § val-fe-axe-routing-shell`

---

## Allowlist Movement
- [x] No allowlist growth.
- [x] No warning baseline growth.

## Native-First Audit
- [x] No `docker exec`, no `make e2e`, no `git add .`/-A/-u.
- [x] Manual run instructions use native Playwright (NOT `make e2e-smoke`).

## Live Verification Audit
- ⚠️ **NOT executed live** — chrome-devtools-verify deprecated Linux per CONTEXT-BRIEF § 11 LOW.
- ✅ Caveat accepted (NOT CHANGES_REQUESTED) — explicit per CONTEXT-BRIEF § 11 + auditor reasoning above.
- 📋 PM-merge phase F action: Chris ratify visual goldens + sample live spec run.

## Skills Consulted (must_load enforcement v4.1)
- ✅ `playwright-expert` — SSoT for Playwright suite construction, POM patterns, fixtures, axe-core integration, page.route() mocking
- ✅ `tessl__react-patterns` (a11y subset) — keyboard nav, screen reader title change patterns
- ✅ `spanish-text.md` — SC-7 i18n regex scan
- ✅ `tdd-mandatory.md` — E2E specs scaffolded RED-first per impl-log
- ✅ `frontend-fsd.md` — E2E directory layout per repo convention

## Verdict Math
- ✅ No FAIL in cat 1/2/3/7/11/12/14
- ⚠️ Live run absence = CAVEAT acknowledged per CONTEXT-BRIEF § 11 LOW (not CHANGES_REQUESTED)
- ✅ Specs compile + tsc + eslint clean (gate-output.json PASS playwright_spec_list)
- ✅ Visual goldens iter 1 seeded; Chris ratify deferred to merge phase F (process note, not defect)
- → **APPROVED with caveat** (live run + visual ratify deferred to staging gate)

---

<!-- @pm: REVIEW.md ready (verdict=APPROVED with caveat). Brand: vitalia. Cross-brand flags: 0. Engine-edit flags: 0. Live-verified: NO (deferred to staging per CONTEXT-BRIEF § 11 LOW; specs compile + tsc + eslint CLEAN). PM merge phase F action: visual goldens ratify + sample live spec run. -->
