<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review: T-14 — E2E Playwright POM + Smoke + 4 Regression Specs

**Brand:** vitalia
**Story:** vitalia-slice-1-fidelizacion
**Ticket:** T-14
**Surface:** frontend tests (POM + smoke + 4 regression + 2 fixtures)
**Date:** 2026-05-20
**Files Reviewed:** 8 (T-14 scope per 06-tickets.yaml + commit 119d4fc — strict scope)
**Domains touched:** E2E test infrastructure
**Skills consulted:** frontend-expert, playwright-expert
**Live-verified:** Yes (real Playwright run against dev stack port 3002 by auditor — 6 PASS / 9 FAIL)
**Verdict:** **FAIL** (root cause: 5× axe critical violations are T-11 component bug + 4× cards-not-found indicate seed fixture / contract gap)

---

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | E2E lives under `vitalia/frontend/e2e/`, POM/fixtures separated correctly |
| 2 | Server/Client | N/A | E2E |
| 3 | React Patterns | N/A | E2E |
| 4 | Code Quality | PASS | tsc EXIT 0 + eslint T-14 files EXIT 0 (per T-14 result § Static validation) |
| 5 | Accessibility | **FAIL** | 5/5 a11y tab smoke FAILs (real WCAG 2.1 AA blocker — see T-11 review) |
| 6 | Forms | N/A | |
| 7 | Multitenancy | PASS | clinic-context.fixture.ts injects X-Tenant-ID + X-Clinic-ID |
| 8 | Master Data / Spanish | PASS | locator labels in neutro |
| 9 | Security / Deps | PASS | Adversarial spec covers SC-04 |
| 10 | Tests / TDD | **WARN** | Smoke spec compiles + static OK, but live: 6 PASS / 9 FAIL — gap between static and runtime |
| 11 | Domain Alignment / HIPAA-lite | PASS | Adversarial spec covers PHI-role + cross-tenant + XSS |
| 12 | Architecture Fitness | PASS | 38/38 maintained |
| 13 | Mirror detection | PASS | No cross-brand mirror; inbox.smoke uses parallel pattern (consistent, not duplicate) |
| 14 | Decisions honored (R6) | PASS | T-14 result.md cites A2.13 |

## /test-frontend Gate Status (live smoke run by auditor)

```
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test specs/smoke/fidelizacion.smoke.spec.ts --project=smoke
```

| Test | Result |
|---|---|
| monta página con título y descripción | ✅ PASS |
| muestra 5 tabs navegables | ✅ PASS (post POM eaefd41 fix) |
| KPI hero muestra stat cards con aria-label | ✅ PASS |
| selector de período (7d/30d/90d) es funcional | ✅ PASS |
| tab Multisesión carga tarjeta (M. Rodríguez) | ❌ FAIL — `getByTestId('re-engagement-card-multi_session-evt-fidel-multisess-001')` not visible (timeout 10s) |
| tab Ausencia carga tarjeta (L. Vega) | ❌ FAIL — idem |
| tab Seguimiento médico carga tarjeta (C. Núñez) | ❌ FAIL — idem |
| tabs vacíos muestran empty state (Mantenimiento) | ❌ FAIL — `/no hay pacientes que requieran mantenimiento/i` not visible |
| a11y: tab multisession | ❌ FAIL — `aria-valid-attr-value` critical: `aria-controls="panel-multisession"` invalid (panel id absent from DOM when no rows) |
| a11y: tab followup | ❌ FAIL — idem (panel-followup) |
| a11y: tab maintenance | ❌ FAIL — idem (panel-maintenance) |
| a11y: tab absence | ❌ FAIL — idem (panel-absence) |
| a11y: tab nps | ❌ FAIL — `aria-valid-attr-value` critical: `aria-controls="panel-nps"` invalid |

Total: 6 PASS / 9 FAIL.

## Findings

### FAIL: a11y tabs (5/5) — aria-controls dangling refs
**Category:** 5 (Accessibility)
**Root cause:** T-11 component bug (`FidelizacionTabsBar` button `aria-controls="panel-X"` ↔ tab panels only rendered in success-with-rows path).
**Detail:** see `T-11-review.md` FAIL finding. T-14 spec is correct; failures expose a real T-11 bug.

**Resolution path:** dev-team fix-loop targeted at T-11 components (FidelizacionTabsBar + 5 tabs) — NOT T-14 spec changes.

### FAIL: patient card visibility (3/3) + empty state Maintenance (1) — runtime seed/network contract gap
**Category:** 10 (Tests / TDD)
**Files:** `vitalia/frontend/e2e/fixtures/fidelizacion-seed.fixture.ts`
**Issue:** seed fixture mocks return snake_case (`re_engagement_event_id`, `patient_name`, `pattern_data`), but FE TS types + React Query consumer (`PatternRow.reEngagementEventId`) expect camelCase. No automatic key-translator in `vitaliaFetch` or hook. Mock fulfill arrives but parses into a row where `row.reEngagementEventId` is `undefined`, breaking `data-testid` derivation.

Additionally, "Mantenimiento empty state" timeout may be a related issue (mock fallback returns `{rows: []}` but page redirect-trapped by Clerk middleware OR React Query stays in `isPending` after navigation race).

**Evidence (real Playwright run):**
- Spec failed: `Locator: getByTestId('re-engagement-card-multi_session-evt-fidel-multisess-001')` not found
- Spec failed: `Locator: getByRole('main').getByText(/no hay pacientes que requieran mantenimiento/i)` not found
- snapshot showed only `<nav>` header — main content never hydrated

**Fix:**
Option A (preferred): Adjust fixture payloads to camelCase to match FE contract:
```ts
const MULTI_SESSION_ROWS = [{
  reEngagementEventId: SEED_IDS.eventIdMultiSession,
  patientId: SEED_IDS.patientIdMultiSession,
  patientName: "M. Rodríguez",
  pattern: "multi_session",
  urgency: "critical",
  patternData: { … kind: "multi_session", offerLabel: …, sessionsCompleted: 4, … },
  acciones: [...]
}];
```

Option B: Add a snake_case-to-camelCase keys transformer at `vitaliaFetch` boundary (cross-cutting concern, much larger scope — defer to design review).

Recommended: **Option A** — single-file fixture edit (~120 lines refactored to camelCase keys), zero production code touched. **NOT self-fix territory** per `.claude/rules/auditor-self-fix-policy.md` § NEVER #1 (writing/rewriting tests is dev-team scope when restructuring fixtures). → SPAWN dev-team fix-loop.

**Skill ref:** playwright-expert (mock fixtures), 03-arch-fe.md § 2 TS types (camelCase mirror).

---

## Compliance Audit

- ✅ POM lives in `e2e/pages/fidelizacion.page.ts` — ARIA-first locators, no CSS/XPath, action methods represent user flows
- ✅ Fixtures separated: `clinic-context.fixture.ts` (multi-tenant injection) + `fidelizacion-seed.fixture.ts` (data mocks)
- ✅ Smoke + 4 regression specs (SC-01..SC-04) compile cleanly
- ✅ POM ARIA role correctness fix applied in commit eaefd41 (tablist not navigation)
- ❌ a11y axe-core scan (5 tabs) — see Cat 5 FAIL
- ❌ Patient card fixture contract mismatch — see Cat 10 FAIL

## Gherkin Coverage Matrix

| Scenario | Test path | Static compile | Live status |
|---|---|---|---|
| SC-01 Happy multi-session | `e2e/specs/regression/fidelizacion-multi-session-happy.spec.ts::scenario-01` | ✅ COMPILES | ⏸ DEFERRED — not run by auditor (regression tier; smoke ran first per `--project=smoke`) |
| SC-02 Absence no opt-in | `e2e/specs/regression/fidelizacion-absence-no-optin.spec.ts::scenario-02` | ✅ COMPILES | ⏸ DEFERRED |
| SC-03 Follow-up doctor vencido | `e2e/specs/regression/fidelizacion-follow-up-doctor-vencido.spec.ts::scenario-03` | ✅ COMPILES | ⏸ DEFERRED |
| SC-04 Adversarial | `e2e/specs/regression/fidelizacion-adversarial.spec.ts::scenario-04` | ✅ COMPILES | ⏸ DEFERRED |

Regression specs will fail with same root causes (Cat 5 a11y + Cat 10 fixture) — recommendation: run regression tier ONLY after T-11 + T-14 dev-team fix-loop closes.

## Allowlist Movement

None.

## Native-First Audit

- ✅ Smoke run native (`npx playwright test ...`)
- ✅ No `make e2e` / `make e2e-smoke` patterns
- ✅ Dev stack reached via `localhost:3002` (vitalia FE port per `docs/process/docker-dev-multibrand.md`)

## Live Verification Audit

- ✅ Auditor ran live Playwright suite against real dev stack
- Empirical evidence captured at `test-results/specs-smoke-fidelizacion.s-*/{test-failed-1.png, error-context.md, trace.zip}`

## Verdict Math

- 1 FAIL Cat 5 (a11y — T-11 root cause) + 1 FAIL Cat 10 (TDD — fixture contract gap)
- → **overall FAIL**

**Auto-fix decision per .claude/rules/auditor-self-fix-policy.md:**
- Cat 5 fix: 5-file restructure → NEVER self-fix #3 (>2 files) → SPAWN dev-team
- Cat 10 fix: rewriting fixture payloads → NEVER self-fix #1 (no test-writing by auditor — but here it's fixture-payload data, not test logic; could be borderline. Per cautious read: still hands-off to maintain TDD discipline) → SPAWN dev-team

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| frontend-expert | E2E surface lives in `vitalia/frontend/e2e/` per FSD outside `src/` | Correct placement |
| playwright-expert | POM patterns, Clerk auth fixture, smoke spec architecture | POM correct, fixture contract gap flagged |

