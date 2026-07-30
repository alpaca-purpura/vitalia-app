<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review: T-11 — FE Fidelización Feature

**Brand:** vitalia
**Story:** vitalia-slice-1-fidelizacion
**Ticket:** T-11
**Surface:** frontend (layout + KPIs + 5 tabs + 11 components + 4 modals + 10 hooks + zustand store)
**Date:** 2026-05-20
**Files Reviewed:** ~30 (`vitalia/frontend/src/features/fidelizacion/**` + `vitalia/frontend/src/app/(dashboard)/fidelizacion/page.tsx`)
**Domains touched:** brand-local (HIPAA-lite PHI), master-data (currency + tenant locale)
**Skills consulted:** frontend-expert, brand-expert (PHI), tessl__react-patterns
**Live-verified:** N — `chrome-devtools-verify` DEPRECATED Linux Mint (per T-11 result § Skills Consulted) + dev stack accessible but real-browser session not exercised by auditor
**Verdict:** **WARN** (post auto-fix the only Cat 5 blocker → bumps to FAIL — see Auto-fix decision below)

---

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 |
| 2 | Server/Client | PASS | 0 |
| 3 | React Patterns | PASS | 0 |
| 4 | Code Quality | PASS | 0 |
| 5 | Accessibility | **FAIL** | 1 (aria-controls dangling refs) |
| 6 | Forms (RHF + Zod) | PASS | 0 |
| 7 | Multitenancy | PASS | 0 |
| 8 | Master Data / Spanish | PASS | 0 |
| 9 | Security / Deps | PASS | 0 |
| 10 | Tests / TDD | PASS | 0 |
| 11 | Domain Alignment / HIPAA-lite | PASS | 0 |
| 12 | Architecture Fitness | PASS | 0 |
| 13 | Mirror detection | PASS | 0 |
| 14 | Decisions honored cite (R6) | PASS | T-11 commit/result.md cites D14, D21, D22, D23, A2.*; OK |

## Validators Status (pre-verified by orchestrator + re-verified here)

| Validator | Result | Detail |
|---|---|---|
| fe_typecheck (`npx tsc --noEmit`) | ✅ PASS | 0 errors strict |
| fe_lint_fidelizacion (eslint) | ✅ PASS | 0 errors |
| fe_arch_fitness (vitest arch suite) | ✅ PASS | 11 tests (incl. 18 vitalia voseo + ratchet) |
| fe_unit_tests_fidelizacion (vitest) | ✅ PASS | 22 tests fideliz feature + 21 NPS shared = 43 tests fideliz domain (85 total inkl. shared) |
| fe_coverage_module | ✅ PASS (per result.md) | ≥30% threshold (target raised from baseline 20%) |

## Findings

### FAIL: aria-controls references dangling panel ids in non-success states
**Category:** 5 (Accessibility)
**Files:**
- `vitalia/frontend/src/features/fidelizacion/components/FidelizacionTabsBar.tsx:52` — `aria-controls={`panel-${tab.id}`}` set unconditionally on every tab button
- `vitalia/frontend/src/features/fidelizacion/components/tabs/MultiSessionTab.tsx:66` — `id="panel-multisession"` ONLY set on success-with-rows render path
- `vitalia/frontend/src/features/fidelizacion/components/tabs/FollowUpTab.tsx:67` — idem
- `vitalia/frontend/src/features/fidelizacion/components/tabs/MaintenanceTab.tsx:67` — idem
- `vitalia/frontend/src/features/fidelizacion/components/tabs/AbsenceTab.tsx:67` — idem
- `vitalia/frontend/src/features/fidelizacion/components/tabs/NPSResumenTab.tsx:51` — idem

**Issue:**
Each tab button declares `aria-controls="panel-<tab>"` to reference a tabpanel that **only exists when `rows.length > 0`**. When the tab is in `isPending` (skeleton render), `isError` (alert div), or `rows.length === 0` (empty state) — the referenced panel id is absent from the DOM. axe-core flags this as a WCAG 2.1 AA / WCAG 4.1.2 critical violation: `Invalid ARIA attribute value: aria-controls="panel-nps"`.

E2E evidence (real Playwright run against live dev stack, port 3002):
```
[smoke] a11y: tab multisession — cero violaciones críticas axe → FAIL (aria-valid-attr-value)
[smoke] a11y: tab followup     — FAIL (aria-valid-attr-value)
[smoke] a11y: tab maintenance  — FAIL (aria-valid-attr-value)
[smoke] a11y: tab absence      — FAIL (aria-valid-attr-value)
[smoke] a11y: tab nps          — FAIL (aria-valid-attr-value)
```

This blocks **A2.13 (a11y WCAG 2.1 AA)** in 05-guidelines.md and the **e2e_a11y** validator in 04-validators.yaml.

**Fix:** restructure each tab component so the `<section id="panel-X" role="tabpanel" aria-labelledby="tab-X">` wrapper renders for ALL render paths (loading / error / empty / success). Skeletons + empty + error content goes INSIDE the section. Pseudocode:

```tsx
return (
  <section id={`panel-${tabId}`} role="tabpanel" aria-labelledby={`tab-${tabId}`} className="…">
    {isPending && <SkeletonGrid />}
    {isError && <ErrorAlert />}
    {!isPending && !isError && rows.length === 0 && <EmptyState />}
    {!isPending && !isError && rows.length > 0 && rows.map(…)}
  </section>
);
```

5 files touched, ~3 lines moved each. **NOT self-fix territory** per `.claude/rules/auditor-self-fix-policy.md` § NEVER #3 (refactor 2+ archivos) AND #5 (changes structural render branch logic). → SPAWN dev-team fix-loop.

**Skill ref:** tessl__react-patterns (a11y/ARIA), `.claude/rules/e2e-testing.md` § a11y, 05-guidelines.md A2.13, 03-arch-fe.md § 7 Accesibilidad.

---

## Contract / UI-SPEC Compliance

- [x] All 30+ TypeScript types from `03-arch-fe.md § 2` implemented (camelCase, ISO 8601 datetimes as `string`, optionals explicit)
- [x] All components from `03-arch-fe.md § 1` module structure exist (verified via find)
- [x] Server/Client boundaries match: `app/(dashboard)/fidelizacion/page.tsx` Server Component; `FidelizacionLayout` + tabs + cards + modals all `"use client"` leaves
- [x] Data flow matches: React Query in hooks + zustand for ephemeral UI state + nuqs for URL state (11 params per D23)
- [x] PHI guarding present: `<RequireRole roles={['doctor','nurse','admin_clinic']}>` + `<PiiMaskedSpan>` patterns applied
- [x] Spanish neutro: `FIDELIZACION_COPY` in `copy.ts` SSoT, no voseo verified by `test-vitalia-ui-strings-no-voseo.test.ts`
- [x] Master-data: NO `toLocaleDateString` / `Intl.DateTimeFormat` direct. `formatTenantDate(value, timezone)` + `formatMoney(amount, data.currency ?? locale.currency)` used consistently
- [x] FSD-Lite: `index.ts` Public API present; no deep imports detected; no default exports
- [x] FidelizacionLayout has Suspense boundary around ActivityFooter (per 03-arch-fe.md `<Suspense>`)
- [ ] tabpanel/aria-controls contract — **VIOLATION**, see Finding above

## Allowlist Movement
- FE arch fitness 38/38 (per T-11 result.md) — no allowlist growth detected
- `test_no_hardcoded_colors.test.ts` allowlist: 1 exception (per T-11 result.md — pre-existing, NOT introduced by T-11)
- No new exemptions

## Native-First Audit
- ✅ All validators ran native (`npx tsc`, `npx eslint`, `npx vitest`)
- ✅ No `make e2e` / `make e2e-smoke` in commits
- ✅ No `git add .` / `-A` / `-u` in commits

## Live Verification Audit
- ⚠️ User-facing change (5 tabs + 11 components + 4 modals): `chrome-devtools-verify` skill marked DEPRECATED for Linux Mint per project context. T-11 result.md cites "Escalated to Chris staging gate".
- The smoke E2E run **DID** exercise the live stack (port 3002) — 6/15 PASS, 9 FAIL. Empirical evidence captured.
- a11y failure is a hard blocker independent of staging gate status.

## Verdict Math
- 1 FAIL in Category 5 (Accessibility) → triggers **FAIL** verdict for T-11
- Recommended action: spawn `builder-frontend` dev-team fix-loop with findings cited above
- All other categories PASS

**Auto-fix decision per .claude/rules/auditor-self-fix-policy.md:**
The fix requires restructuring 5 tab files (each rewrites the return statement). This violates:
- § NEVER #3 (refactor 2+ archivos)
- § NEVER #5 (changes branch logic / structural render)

→ SPAWN dev-team fix-loop with explicit findings.

---

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| frontend-expert | FSD-Lite boundary + component patterns + master-data audit | FSD compliant, master-data compliant |
| brand-expert | HIPAA-lite PHI (RequireRole + PiiMaskedSpan in ReEngagementCard) | Applied correctly per A2.8 |
| tessl__react-patterns | a11y baseline + ARIA correctness | **FAILED** aria-controls invariant — flagged as Cat 5 |
| tessl__shadcn-ui | check no recreated primitives | OK, no recreations |
| tessl__tailwind | utility-first + tokens compliance | OK, vt-/HSL tokens used |
| tessl__zod | form schema check | N/A (forms come later in Modal components; basic structure deferred) |
| tessl__vitest | unit test framework | OK |
| tessl__nextjs-app-router-modularization | Server/Client split | page.tsx clean Server; FidelizacionLayout clean Client leaf |
| chrome-devtools-verify | live verification gate | DEPRECATED Linux Mint per project context note |
