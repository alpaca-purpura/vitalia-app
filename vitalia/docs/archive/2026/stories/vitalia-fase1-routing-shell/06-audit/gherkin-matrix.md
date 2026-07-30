<!-- voseo-allowed: audit phase D matrix may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Phase D — Gherkin Matrix · F1-S9 vitalia-fase1-routing-shell

**Story:** `vitalia-fase1-routing-shell`
**Date:** 2026-05-26
**Auditor:** auditor-frontend (Opus 4.7)
**Spec source:** `01-spec.md § 5` (8 scenarios SC-1..SC-8)
**Coverage source:** `04-validators.yaml::scenario_to_test` + actual test files in `vitalia/frontend/e2e/regression/vitalia-fase1-routing-shell/`

## Coverage table

| # | Scenario (01-spec.md § 5) | Test file | Status | Notes |
|---|---|---|---|---|
| SC-1 | happy · login + default landing + navegación completa | `happy-navigation.spec.ts` | COMPILE_PASS · deferred runtime | Drives login → `/[tenantId]/valeria/agenda` default landing → ribbon nav + sub-tab nav assertions; live run deferred staging gate |
| SC-2 | negative · agent slug inválido → outer not-found | `not-found-outer.spec.ts` | COMPILE_PASS · deferred runtime | Navigates `/[tenantId]/inexistente` → expects shell-organism outer `(shell-organism)/not-found.tsx` HTTP 404 |
| SC-3 | edge · subtab inválido dentro de agent válido → inner not-found | `not-found-inner.spec.ts` | COMPILE_PASS · deferred runtime | `/[tenantId]/valeria/inexistente` → `[agent]/not-found.tsx` inner; ribbon visible, sub-tab error placeholder rendered |
| SC-4 | adversarial · cross-tenant access blocked | `cross-tenant-blocked.spec.ts` | COMPILE_PASS · deferred runtime | Mocks `/api/v1/iam/users/me/tenants` with `mockCrossTenantList`; user attempts `/[tenantId-not-mine]/valeria/agenda` → expects 403/redirect per proxy.ts |
| SC-5 | network_failure · BE tenant fetch timeout | `network-failure-tenant-fetch.spec.ts` | COMPILE_PASS · deferred runtime | `mockNetworkFailure()` → tenant fetch errors; expects fallback UI with manual "Reintentar" button per Q7 batch_2 decision (no auto-retry) |
| SC-6 | accessibility · keyboard nav + screen reader anuncia cambio de página | `a11y-keyboard-nav.spec.ts` | COMPILE_PASS · deferred runtime | Tab + Enter through ribbon + sub-tabs + axe-core WCAG 2.1 AA scans @axe tag on 4 pages: valid shell · outer 404 · inner 404 · network error fallback |
| SC-7 | i18n · microcopy Spanish neutro LatAm | `i18n-spanish-neutro.spec.ts` | COMPILE_PASS · deferred runtime | Rendered page regex scan for voseo forbidden tokens (vos/sos/tenés/podés/mirá/dejá) on shell + not-found + network error pages |
| SC-8 | edge · user autenticado sin tenants asignados (Q6 batch_2 edge case) | `no-tenants-edge.spec.ts` | COMPILE_PASS · deferred runtime | `mockEmptyTenants()` → user logged in with empty tenants list → expects sign_out_plus_admin_message UI per Q6 decision (NOT `/onboarding/wizard`) |

## Summary

| Metric | Value |
|---|---|
| Total scenarios specified | 8 (SC-1..SC-8) |
| Scenarios with test file present | 8/8 (100%) |
| Coverage: compile + lint | ALL PASS (tsc --noEmit exit 0, ESLint 0 errors, 0 warnings on e2e/regression/vitalia-fase1-routing-shell/) |
| Live run | deferred staging gate (chrome-devtools-verify deprecated Linux per T-6 escalation note + CONTEXT-BRIEF § 11 LOW caveat) |
| Visual goldens iter 1 | generated in `vitalia/frontend/e2e/visual/` · Chris ratify pending pre-merge |
| Sub-categorías mandatory v4.1 marked `not_applicable` | 4 (race_condition · concurrent_users · empty_state · large_dataset — justificadas spec § 5 batch_1 Q5 decision) |
| Coverage gap | 0 — all scenarios have test file present mapped 1:1 per `04-validators.yaml § scenario_to_test` |

## Deferral rationale (live runtime)

Per `01-spec.md § 7` + T-6 review caveat + CONTEXT-BRIEF § 11: live Playwright execution deferred to `/pm-vitalia` merge phase (live app required at `localhost:3002` or staging deploy). Specs validated at:

1. **Compile-time:** `tsc --noEmit` exit 0 strict mode on all 8 specs + POM + fixture (gate-output.json iter 1 PASS).
2. **Lint:** ESLint 0 errors, 0 warnings on `e2e/regression/vitalia-fase1-routing-shell/` (gate iter 1 PASS).
3. **Scenario mapping:** 1:1 per `04-validators.yaml § scenario_to_test`, verified manually + via T-6 review.
4. **Architectural authorization:** auditor-frontend acepta deferral porque (a) `gate-output.json command: test-frontend` cubre tsc + ESLint + Vitest unit + arch fitness — 5 gates GREEN; (b) chrome-devtools-verify skill deprecated Linux Mint (was WSL2-specific); (c) `/pm-vitalia` merge phase responsibility is live runtime via staging deploy + Chris manual gate.

This mirrors F1-S8 deferral pattern (auditor-authorized, no escalate needed).

## Verdict

Phase D **COVERED** — 8/8 scenarios have test file present. Compile + lint PASS for all. Live runtime deferred to `/pm-vitalia` merge phase (staging deploy gate). Visual goldens iter 1 pending Chris pre-merge ratification.
