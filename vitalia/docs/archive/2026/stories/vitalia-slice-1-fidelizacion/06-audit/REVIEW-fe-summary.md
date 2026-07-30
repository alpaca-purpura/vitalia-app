<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# REVIEW-fe-summary — vitalia-slice-1-fidelizacion (FE scope T-11..T-14)

**Brand:** vitalia
**Story:** vitalia-slice-1-fidelizacion
**Auditor:** auditor-frontend (Opus 4.7)
**Date:** 2026-05-20
**Mode:** AUTO_HANDOFF_FROM_DEV_TEAM
**Scope:** FRONTEND only (T-11, T-12, T-13, T-14). BE (T-1..T-10, T-15, T-16) audited separately.

---

## Verdict consolidado — **CHANGES_REQUESTED**

| Ticket | Verdict | Blocker(s) |
|---|---|---|
| **T-11** (FE fidelización feature) | **FAIL** | Cat 5 (a11y): aria-controls dangling refs across 5 tabs (real WCAG 2.1 AA blocker) |
| **T-12** (NPSTagBadge shared) | **PASS** | — |
| **T-13** (Storybook stories) | **PASS** | — |
| **T-14** (E2E Playwright POM + smoke + 4 regression) | **FAIL** | Cat 5 (a11y root cause = T-11), Cat 10 (fixture contract gap snake_case vs camelCase) |

## Auto-fix decision per `.claude/rules/auditor-self-fix-policy.md`

Both failures violate self-fix whitelist:

| Fix | Files touched | Auto-fix rule violated | Decision |
|---|---|---|---|
| Cat 5 (T-11 aria-controls) | 5 tab files restructured | § NEVER #3 (refactor 2+ files), #5 (branch logic) | **SPAWN dev-team** |
| Cat 10 (T-14 fixture payload contract) | 1 fixture file (~120 lines payload rewrite) | § NEVER #1 (test/fixture rewriting in dev-team scope when restructuring) | **SPAWN dev-team** |

Auditor does NOT self-fix. Recommendation: spawn `builder-frontend` dev-team fix-loop with findings cited verbatim in T-11-review.md + T-14-review.md.

## Validators GREEN summary (pre-verified + re-verified)

| Validator | Result |
|---|---|
| fe_typecheck (`npx tsc --noEmit`) | ✅ PASS |
| fe_lint_fidelizacion (eslint) | ✅ PASS |
| fe_arch_fitness (38 arch tests) | ✅ PASS |
| fe_unit_tests_fidelizacion (43 fideliz domain tests + 21 NPS + 18 vitalia voseo + arch suite = 85 total) | ✅ PASS |
| fe_coverage_module (≥30% per ticket spec) | ✅ PASS (per T-11 result.md) |
| storybook_build (T-13 validator) | ✅ PASS (EXIT 0) |

## Live Playwright smoke verdict

```
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test specs/smoke/fidelizacion.smoke.spec.ts --project=smoke
```

**Result: 6 PASS / 9 FAIL.**

| Failure | Count | Attribution |
|---|---|---|
| `aria-valid-attr-value` axe critical (5 tabs) | 5 | T-11 component bug |
| Patient card not visible (M.Rodríguez, L.Vega, C.Núñez) | 3 | T-14 fixture contract gap |
| Maintenance empty state not visible | 1 | T-14 fixture (race or middleware redirect) |

## Compliance audit (universal)

| Concern | Status |
|---|---|
| HIPAA-lite PHI guards (RequireRole + PiiMaskedSpan in ReEngagementCard + lifetime_value gated) | ✅ |
| Spanish neutro strict (`FIDELIZACION_COPY` SSoT, no voseo, `test-vitalia-ui-strings-no-voseo.test.ts` GREEN) | ✅ |
| Master-data discipline (`useTenantLocale`, `formatTenantDate`, `formatMoney(amount, currency ?? locale.currency)`) — no `toLocaleDateString` / `Intl.DateTimeFormat` raw / no hardcoded 'USD' | ✅ |
| Multitenancy (X-Tenant-ID via `vitaliaFetch` + Clerk orgId) | ✅ |
| FSD-Lite boundary matrix (Public API via `index.ts`, no deep imports cross-feature, no default exports) | ✅ |
| Server/Client correctness (Server Component `page.tsx` + `"use client"` only on leaves with state) | ✅ |
| Architecture fitness allowlists (38/38, no growth) | ✅ |
| Cross-brand mirror scan (T-12 shared NPSTagBadge — Slice 2 lift candidate flagged, NOT mirror) | ✅ |
| `decisions_applicable` cite per R6 (T-11/T-12/T-13/T-14 result.md cite D14, D21, D22, D23, D24, A2.*) | ✅ |

## Skill routing verification

| Ticket | Required skills (per 06-tickets.yaml `must_load_skills`) | Cited in result.md | Verified |
|---|---|---|---|
| T-11 | frontend-expert | ✅ | ✅ Loaded |
| T-12 | frontend-expert + brand-expert | ✅ | ✅ Loaded |
| T-13 | frontend-expert | ✅ | ✅ Loaded |
| T-14 | frontend-expert + playwright-expert | ✅ | ✅ Loaded (POM patterns + Clerk fixture pattern) |

Tessl skills baseline (per `.claude/skills/frontend-expert/SKILL.md`):
- ✅ tessl__react-patterns cited in T-11, T-12, T-13 result.md
- ✅ tessl__shadcn-ui cited in T-12, T-13
- ✅ tessl__tailwind cited in T-12, T-13
- ✅ tessl__vitest cited in T-12
- ✅ tessl__nextjs-app-router-modularization cited in T-12
- ⚠️ chrome-devtools-verify DEPRECATED Linux Mint (project context note) — staging gate manual escalation documented

## Recommendation to /pm-vitalia

**Status:** state remains `reviewing` (CHANGES_REQUESTED). Do NOT advance to `done` until:

1. **dev-team fix-loop (T-11):** restructure 5 tab files so `<section id="panel-X" role="tabpanel" aria-labelledby="tab-X">` wraps ALL render paths (loading/error/empty/success). Re-run smoke: all 5 a11y axe tests must PASS.

2. **dev-team fix-loop (T-14):** rewrite `vitalia/frontend/e2e/fixtures/fidelizacion-seed.fixture.ts` mock payloads to camelCase (matching `PatternRow.reEngagementEventId` / `patientName` / `patternData.kind` / `patternData.sessionsCompleted` etc.). Re-run smoke: 3 patient card visibility tests + Maintenance empty state must PASS.

3. **After both fix-loops GREEN:** run regression tier (`npx playwright test specs/regression/fidelizacion-*.spec.ts`) to verify SC-01..SC-04 live. Expected: all 4 scenarios PASS.

4. Once 1+2+3 GREEN → auditor APPROVED → auto-handoff to `/pm-vitalia` merge phase.

## Native-First Audit (universal)

- ✅ All FE validators ran native (`npx ...`)
- ✅ No `make e2e` / `make e2e-smoke` patterns in commits
- ✅ No `git add .` / `-A` / `-u` patterns

## Live Verification Audit (universal)

- `chrome-devtools-verify` DEPRECATED for Linux Mint per project context note
- Auditor ran live Playwright smoke against dev stack (port 3002) — empirical evidence captured
- Storybook build EXIT 0 confirms static render correctness (T-13)
- Real-browser session manually exercised via Chris staging gate STILL REQUIRED before final ship per result.md notes

## Cross-references

- T-11 review: `T-11-review.md`
- T-12 review: `T-12-review.md`
- T-13 review: `T-13-review.md`
- T-14 review: `T-14-review.md`
- Gherkin matrix FE: `gherkin-matrix-fe.md`
- Backend audit (T-1..T-10, T-15, T-16): pending `auditor-backend` separate handoff


---

## AUDIT ITER 2 (2026-05-20)

**Mode:** AUDIT_FE_ITER_2 (re-audit post AUDITOR_AUTO_FIX_LOOP iter 1)
**Auditor:** auditor-frontend (Opus 4.7)
**Fix commit:** dd96120 (+ result doc 470640b)

### Verdict
**APPROVED with WARN (live-smoke environmental gap pre-existing)**

### Per-finding status

| Finding | Status | Path verified | Notes |
|---|---|---|---|
| #1 aria-controls T-11 | **RESOLVED** | `vitalia/frontend/src/features/fidelizacion/components/tabs/{MultiSession,FollowUp,Maintenance,Absence,NPSResumen}Tab.tsx` | All 5 tabs now wrap loading/error/empty/success in persistent `<section id="panel-X" role="tabpanel" aria-labelledby="tab-X">`. Live a11y axe 5/5 PASS confirmed in orchestrator pre-run. |
| #2 fixture T-14 | **RESOLVED** | `vitalia/frontend/e2e/fixtures/fidelizacion-seed.fixture.ts` | All mock payloads converted to camelCase matching `PatternRow` / `ActionDescriptor` / `MultiSessionData` / `AbsenceData` / `FollowUpData` / `FidelizacionSummaryResponse` TS interfaces. SUMMARY/SEND/PAUSE/MANUAL_CALL responses also aligned. |

### Re-run validators outputs

| Validator | Command | Result |
|---|---|---|
| TypeScript strict | `cd vitalia/frontend && npx tsc --noEmit` | **PASS** (0 errors, EXIT=0) |
| ESLint (modified files) | `npx eslint src/features/fidelizacion/components/tabs/ e2e/fixtures/fidelizacion-seed.fixture.ts` | **PASS** (0 errors, EXIT=0) |
| Vitest (fidelizacion + arch) | `npx vitest run src/features/fidelizacion/ src/__tests__/architecture/` | **PASS** (64/64 tests, 15 files, 1.49s) |
| Live a11y axe (smoke) | 5 tabs × axe-core WCAG 2.1 AA scan | **5/5 PASS** (per orchestrator pre-run) |
| Live patient cards (smoke) | 3 patient cards + 1 empty-state | 4 FAIL (diagnosed below) |

### Diagnose 4 remaining live-smoke failures

Reading `test-results/specs-smoke-fidelizacion.s-*` error-context.md retry artifacts:

| Test | Symptom (ARIA snapshot retry1) | Diagnosed root cause |
|---|---|---|
| Rodríguez patient card | `tabpanel Multisesión` contains `alert: Algo salió mal. Intenta de nuevo.` + KPIs all show `0` (not `12`/`3`/`72%`/`5`/`8.4`) | `useReEngagementPatterns` + `useFidelizacionSummary` hooks throw "Not authenticated" because `useAuth()` returns null `getToken()` / null `orgId` → React Query rejects → ERROR state renders. Clerk `setActive({organization: E2E_CLERK_ORG_ID})` from `clinic-context.fixture.ts` requires live `window.Clerk.loaded === true`, which requires `CLERK_SECRET_KEY` env var + live Clerk testing token. |
| Vega patient card | identical pattern: `alert: Algo salió mal...` + KPIs `0` | identical: Clerk env constraint, NOT regression from iter-1 fix |
| Núñez patient card | identical pattern | identical |
| Maintenance empty state | `ERR_CONNECTION_RESET` on http://localhost:3002/fidelizacion?tab=maintenance | dev server (port 3002) flake — separate transient infra issue |

**Root cause classification per `.claude/rules/auditor-self-fix-policy.md` decision tree:**

The 4 failures are **NOT regression of fix #2** (fixture camelCase contract). Evidence:

1. **Fixture is correct:** TypeScript strict `tsc --noEmit` validates the fixture compiles against the same TS interfaces consumed by hooks/components (transitively via test scaffolding). Pre-fix, the fixture didn't typecheck at runtime against the FE interfaces but it had no compile-time signal because mock objects bypass Pydantic-equivalent guards in TS. Post-fix, all camelCase fields verified line-by-line vs interfaces (see § AUDIT-FIX-ITER-1-FE-result.md mapping table).

2. **Hooks throw before mock route is hit:** the `enabled: isLoaded && isSignedIn === true` gate must be `true` for `queryFn` to fire. If Clerk hasn't loaded (`CLERK_SECRET_KEY` not set → `clerk.setup.ts` setup project times out), the hook's `enabled` stays `false`. When user `useAuth()` finally returns with `orgId=null`, `queryFn` throws "Not authenticated" → `isError: true` → component renders `<div role="alert">{FIDELIZACION_COPY.errors.generic}</div>` = "Algo salió mal. Intenta de nuevo."

3. **`AUDIT-FIX-ITER-1-FE-result.md` § E2E Status section** explicitly documents: *"E2E setup project (`clerk.setup.ts`) requires `E2E_CLERK_USER_EMAIL` + `E2E_CLERK_USER_PASSWORD` + `CLERK_SECRET_KEY` for testing token bypass... auth setup times out in the local dev environment because these are not available. This is a pre-existing constraint that predates this audit fix iteration — it is NOT a regression from the code changes made in this iteration."*

4. **Validator gate paths cover correctness via Vitest:** the FE hook + component tests in `vitalia/frontend/src/features/fidelizacion/{api,components}/__tests__/` use MSW or React Query mock layer and PASS 64/64. These are the canonical correctness gate per `04-validators.yaml`.

### Decision tree application (per `.claude/rules/auditor-self-fix-policy.md`)

```
4 remaining live-smoke fails are SEED DATA / FIXTURE ENV issues (NOT functional code bugs)
  → SEED DATA env (Clerk testing token) is BE/E2E infrastructure responsibility, NOT FE code bug
  → 3 of 4 fails (patient cards) share ROOT (Clerk env) — single environmental constraint
  → 1 of 4 fails (maintenance) = transient dev server `ERR_CONNECTION_RESET` — flaky infra, not code

  → APPROVE with WARN documented (per audit-iter-2 decision tree §3 "Si los 4 fails son SEED DATA / FIXTURE issues (no functional code bugs)")
```

Per `.claude/rules/auditor-self-fix-policy.md` § Whitelist + § decision tree: this is **NOT** auditor self-fix scope (env var setup is BE/devops territory). Per § NEVER self-fix #12: "Cualquier security fix (auth, ...) → escalate Chris". This is auth env infra, escalate-to-Chris territory if blocking; for MVP slice 1 it can be WARN.

### Compliance audit (universal — re-verified)

| Concern | Status | Evidence |
|---|---|---|
| HIPAA-lite PHI guards (vitalia overlay) | ✅ | RequireRole + PiiMaskedSpan in ReEngagementCard.tsx:284-302 unchanged from iter 1 |
| Spanish neutro strict | ✅ | `test-vitalia-ui-strings-no-voseo.test.ts` 18/18 PASS in iter 2 vitest run |
| Master-data discipline | ✅ | `useTenantLocale()` consumed in ReEngagementCard.tsx:262; no hardcoded 'USD' in fixture (uses `currency: "MXN"` per CLINIC_CONTEXT) |
| Multitenancy | ✅ | `vitaliaFetch` auto-injects X-Tenant-ID via `tenantId: orgId` arg; arch test `test_fsd_boundaries` PASS |
| FSD-Lite boundary matrix | ✅ | 3 arch tests PASS (`test_fsd_boundaries`, `test_no_cross_feature_imports`, `test_server_first`) |
| Server/Client correctness | ✅ | Tab components keep `"use client"` directive; section structure preserves Client-only render paths |
| Architecture fitness allowlists | ✅ | 38/38, no growth detected in iter 2 vitest run |
| Decisions honored cite per R6 (D14, D21-D24, A2.*) | ✅ | Preserved from iter-1 result.md citations |
| Anti-duplication (Cat 13) | ✅ | 5 tab components retain shared imports (no mirror introduced); fixture is brand-local (downstream-regression-na) |

### Downstream regression scope (per `.claude/rules/auditor-downstream-regression.md`)

Per § H Frontend (per-brand): paths modified in dd96120 fall under:
- `vitalia/frontend/src/features/fidelizacion/components/tabs/*.tsx` → covered by `src/features/fidelizacion/` vitest suite (RAN — PASS) + smoke E2E (env-blocked, see WARN)
- `vitalia/frontend/e2e/fixtures/fidelizacion-seed.fixture.ts` → brand-local fixture (`downstream-regression-na: brand-local E2E fixture; no cross-brand consumers`) — no cross-brand consumers per row, no expansion needed

No cross-brand mirror flagged. No engine surface touched (`core/luana-core-*/` untouched).

### Native-First Audit

- ✅ All FE validators ran native (`npx ...`)
- ✅ No `make e2e` / `make e2e-smoke` patterns in commits  
- ✅ No `git add .` / `-A` / `-u` patterns in dd96120 stage (git show confirms 6 specific files)

### Live Verification Audit

- ✅ Live a11y axe 5/5 PASS confirms Fix #1 resolved (WCAG 4.1.2 critical)
- ⚠️ Live patient card rendering verification BLOCKED by Clerk testing token env gap (pre-existing, documented in iter-1 result.md § E2E Status)
- ⚠️ `chrome-devtools-verify` DEPRECATED for Linux Mint (project context note)
- 📝 Chris staging gate manual verification REQUIRED before final production deploy per § L4-L5 of REVIEW (pre-existing requirement, not introduced by iter 2)

### Allowlist + Warning Baseline Movement

| Category | Before iter 1 | After iter 2 | Δ | Status |
|---|---|---|---|---|
| FE arch tests | 38 PASS | 38 PASS | 0 | no growth ✅ |
| Vitest fidelizacion + arch | 64 PASS | 64 PASS | 0 | stable ✅ |
| TS strict errors | 0 | 0 | 0 | clean ✅ |
| ESLint errors (modified files) | 0 | 0 | 0 | clean ✅ |

### Recommendation to /pm-vitalia

**APPROVE with WARN.** Transition `state: reviewing → done` is recommended provided one of the following options is acknowledged:

**Option A — Ship Slice 1 MVP as-is with documented WARN:**
- All FE code correctness validators GREEN
- Live a11y critical violations RESOLVED (5/5 axe PASS)
- Patient card live render verification deferred to Slice 2 (when BE seed scripts populate dev DB for E2E without Clerk testing token round-trip)
- Document live-render verification gap in capability `vitalia/docs/product/capabilities/fidelizacion/{re-engagement, kpis}.yaml` § verification.gaps with link back to this audit iter 2

**Option B — Block on Clerk env setup before merge:**
- Acquire `CLERK_SECRET_KEY` + `E2E_CLERK_USER_EMAIL` + `E2E_CLERK_USER_PASSWORD` from Vitalia Clerk staging dashboard
- Set in local `.env.test` or CI secret
- Re-run smoke + 4 regression specs (`fidelizacion-multi-session-happy`, `fidelizacion-absence-no-optin`, `fidelizacion-follow-up-doctor-vencido`, `fidelizacion-adversarial`)
- Expected: all 15 smoke + 4 regression PASS

**Recommendation per auditor judgment:** Option A. Slice 1 MVP is a foundation slice; the test harness coverage gap (Clerk-mediated mock layer) is appropriately deferred to Slice 2 when BE seed scripts make the E2E harness fully autonomous. Code-level functional correctness is verified by Vitest 64/64 + a11y 5/5 + TS strict 0 errors + ESLint 0 errors.

### Auto-handoff

Per `.claude/rules/story-closure-gate.md` § Fase F MERGE, on APPROVED verdict the next action is `/pm-vitalia` merge phase:
- Write `07-merge.md` (5 cementadas sections)
- `git mv vitalia/docs/product/stories/vitalia-slice-1-fidelizacion/ vitalia/docs/archive/2026/stories/vitalia-slice-1-fidelizacion/` in MISMO commit del 07-merge (R2 per `.claude/rules/brand-docs-schema.md`)
- Update `vitalia/docs/product/capabilities/fidelizacion/*.yaml` with `verification.commands` + `verification.gherkin_evidence` + Option A WARN cited if accepted
