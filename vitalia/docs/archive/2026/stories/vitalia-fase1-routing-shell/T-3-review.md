<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review — T-3 Proxy polish + tenant validation layout + network fallback

**Date:** 2026-05-26
**Brand:** vitalia
**Story:** vitalia-fase1-routing-shell (F1-S9)
**Ticket:** T-3 — `proxy.ts` MODIFY anchor + `(shell-organism)/layout.tsx` server-side tenant validation + NetworkErrorFallback + RefreshButton + sign-in error panel
**Commit:** 0fdac50e
**Files Reviewed:** 7 (`proxy.ts`, `layout.tsx`, `sign-in/[[...rest]]/page.tsx`, `NetworkErrorFallback.tsx`, `RefreshButton.tsx`, `NetworkErrorFallback.test.tsx`, `test-no-middleware-ts.test.ts`)
**Domains touched:** Routing/auth (Next.js 16 + Clerk) — no agentic skill required
**Skills consulted:** frontend-expert · tessl__react-patterns · tessl__nextjs-app-router-modularization · tessl__graceful-degradation · tenant-isolation.md · hipaa-lite.md (vitalia overlay) · frontend-fsd.md · spanish-text.md
**Live-verified:** NO (chrome-devtools-verify deprecated Linux per CONTEXT-BRIEF § 11) — manual staging gate via Chris merge phase
**Verdict:** **APPROVED**

---

## /test-vitalia Gate Status (from gate-output.json iter 1)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | 0 errors |
| ESLint | PASS | 0 errors |
| Vitest + coverage | PASS | 1549/1549 · 82.56% statements |
| Arch fitness | PASS | includes NEW `test-no-middleware-ts.test.ts` GREEN |
| playwright_spec_list | PASS | E2E specs compilable; live run deferred (caveat) |

---

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | layout consumes `@/lib/iam`, `@/components/shared/shell-organism` — boundary matrix OK |
| 2 | Server/Client correctness | PASS | layout/NetworkErrorFallback Server; RefreshButton Client leaf (justified `useRouter().refresh()`) |
| 3 | React patterns baseline | PASS · 1 MINOR | error boundary route-level via layout fallback; loading via Next 16 streaming; aria-label dead code on aria-hidden span (see WARN below — also present in T-4) |
| 4 | Code quality | PASS | tsc/eslint clean |
| 5 | Accessibility | PASS | `role="img"` + descriptive label structure on icon; RefreshButton focus visible via Shadcn variant default |
| 6 | Forms | N/A | No forms |
| 7 | Multitenancy | PASS | Server-side tenant validation: `auth()` + `fetchUserTenants(userId)` + check `tenants.some(t => t.id === tenantId)`; cross-tenant redirects to `tenants[0].id/valeria/agenda` with audit log. No client-side tenant injection (fetchClient mode); no hardcoded tenantId. |
| 8 | Master Data / Spanish neutro | PASS | Microcopy verbatim spec § 10 — "Estamos teniendo problemas conectando con el servidor" · "Intenta de nuevo en unos segundos." · "Reintentar" · "Tu cuenta no tiene clínicas asignadas" · "Contacta al administrador..." (NEUTRO — spec said voseo "Contactá" but neutro is correct per spanish-text.md R2; spec § 1 has voseo-allowed magic comment as internal doc) |
| 9 | Security / Deps | PASS | No `dangerouslySetInnerHTML`; no eval; tenant validation server-side defense-in-depth (proxy already auth-checks); Clerk JWT not echoed |
| 10 | Tests / TDD | PASS | `NetworkErrorFallback.test.tsx` 10 cases · `test-no-middleware-ts.test.ts` arch ratchet |
| 11 | Domain Alignment | N/A | No agentic surface |
| 12 | Arch Fitness | PASS | NEW `test-no-middleware-ts.test.ts` blocks accidental middleware.ts revival |
| 13 | Mirror detection | PASS | nicolify has `proxy.ts` but with different logic (legacy-redirects); brand-local pattern (CONTEXT-BRIEF § 7 cross-brand grep zero on routing-shell artifacts). Lift candidate noted for F2. |
| 14 | Decisions honored (R6) | N/A | Ticket has no `decisions_applicable` field |

---

## Findings

### PASS · layout.tsx — verbatim spec § 9.3 flow
Server Component implementing exactly:
1. `await params` → `tenantId` (Next.js 16 Promise pattern ✅)
2. `auth()` → `userId`; falsy → `redirect("/sign-in")` (defense-in-depth, proxy already protects)
3. `try { fetchUserTenants(userId) } catch (err) { return <NetworkErrorFallback /> }` (SC-7 mapping)
4. `tenants.length === 0` → `logNoTenantsAssigned({userId})` + `redirect("/sign-out?next=/sign-in?error=no_tenants_assigned")` (SC-8 audit + sign-out)
5. `!isValidTenant` → `logCrossTenantAttempt({userId, attemptedTenant: tenantId})` + `redirect(/${tenants[0].id}/valeria/agenda)` (SC-4)
6. Happy path → `<ShellOrganismLayout tenantId={tenantId}>{children}</ShellOrganismLayout>`

**HIPAA-lite verification:** audit payload contains ONLY `userId` (opaque Clerk ID) + `attemptedTenant` + `timestamp`. NO PHI fields ever logged. Also the error catch path logs `[audit] tenant_fetch_failure` with stringified error — verified `String(err)` does not include PHI by construction (network errors emit only `Error.name/message`, not patient data).

### PASS · proxy.ts — Next.js 16 canonical
- Named export `proxy` (NOT legacy `middleware`).
- `default export proxy` for compatibility.
- `isPublicRoute` includes `/sign-in`, `/sign-up`, `/public`, `/marketing`, `/__clerk/`, `/api/v1/vitalia/webhooks`, `/api/health`, `/test-stack`.
- `auth.protect()` covers all private routes (no manual RBAC).
- Negative matcher excludes `_next` + static assets per Next 16 docs cite.

### PASS · NetworkErrorFallback (Server) + RefreshButton (Client leaf split)
Textbook `tessl__nextjs-app-router-modularization` pattern:
- NetworkErrorFallback = Server Component (no hooks)
- RefreshButton = Client leaf (just `useRouter().refresh()` — minimal surface)
- Split prevents tagging entire fallback as Client.

Microcopy verbatim spec § 6.3 + § 10.

### PASS · sign-in/[[...rest]]/page.tsx — error panel + Clerk integration
- `searchParams: Promise<...>` Next.js 16 pattern ✅
- `?error=no_tenants_assigned` → conditional render of error panel with `role="alert"` (a11y compliant)
- Microcopy spec § 10:
  - "Tu cuenta no tiene clínicas asignadas" ✅
  - "Contacta al administrador de tu clínica para activar tu acceso." — **NEUTRO ratified** (spec had "Contactá" but `.claude/rules/spanish-text.md` R2 mandates "Contacta" for user-facing → CORRECT)
- `appearance.variables` uses CSS vars (`var(--vitalia-cian-color)`) → no hex hardcoded.

### PASS · arch test-no-middleware-ts.test.ts
Recursive scan src/ → asserts no file named `middleware.ts` exists. Ratchet-style. AC-15 enforced.

### WARN (minor a11y) · Dead `aria-label` on `aria-hidden` span
In `NetworkErrorFallback.tsx:32-34`:
```jsx
<span className="text-4xl" role="img" aria-label="Advertencia">⚠️</span>
```
This has `role="img"` + `aria-label="Advertencia"` (visible to AT) — correct.

But T-4's `not-found.tsx` (outer + inner) uses:
```jsx
<span aria-hidden="true" role="img" aria-label="Advertencia">🔍</span>
```
The `aria-hidden="true"` removes the element from the AT tree, so `aria-label="Advertencia"` is dead code. Pick one mode:
- (A) `aria-hidden="true"` (purely decorative — and the descriptive heading text below replaces the icon's meaning) — spec § 12 suggests this; OR
- (B) `role="img" aria-label="..."` (icon-as-content with semantic label) — what T-3 NetworkErrorFallback uses.

**Action:** Documented but not blocking. axe-core scan in `a11y-keyboard-nav.spec.ts @axe` will catch any real WCAG 2.1 AA violation when live run executes (post-merge staging). If axe flags, dev-team fixes T-4 file. Cataloged here for trace.

---

## Contract / UI-SPEC Compliance

- [x] Spec § 9.3 server-side tenant validation flow implemented verbatim (auth → fetch → empty → invalid → render)
- [x] Spec § 6.3 NetworkErrorFallback wireframe respected (icon + title + description + CTA)
- [x] Spec § 9.2 proxy.ts matcher pattern verbatim
- [x] Spec § 10 microcopy implemented (Spanish neutro applied where spec used voseo per rule)
- [x] HIPAA-lite audit log payload verified non-PHI

---

## Allowlist Movement
- [x] No allowlist growth.
- [x] No warning baseline growth.

## Native-First Audit
- [x] No `docker exec`, no `make e2e`, no `git add .`/-A/-u.

## Live Verification Audit
- ⚠️ NOT executed live — chrome-devtools-verify deprecated Linux per CONTEXT-BRIEF § 11 (LOW caveat, not defect).
- E2E specs (T-6) cover SC-1/4/5/7/8 which exercise this layout — staging gate will catch any regression.
- Manual verify steps documented in T-3-result.md § "Live verification" for Chris staging gate.
- **Caveat accepted (per CONTEXT-BRIEF § 11 LOW)** — not CHANGES_REQUESTED.

## Skills Consulted (must_load enforcement v4.1)
- ✅ `frontend-expert` — Server Component default + Client leaf split
- ✅ `tessl__react-patterns` — error boundary at route-level via try/catch + fallback
- ✅ `tessl__nextjs-app-router-modularization` — Server + Client leaf pattern (NetworkErrorFallback + RefreshButton)
- ✅ `tessl__graceful-degradation` — try/catch network failure + fallback UI + retry button
- ✅ `tenant-isolation.md` — dual-side validation (proxy + server layout)
- ✅ `hipaa-lite.md` (vitalia overlay) — audit log payload non-PHI
- ✅ `frontend-fsd.md` — layout in app/ + _components/ subfolder convention
- ✅ `spanish-text.md` — neutro user-facing strings

## Verdict Math
- ✅ No FAIL in cat 1/2/3/7/11/12/14
- ⚠️ 1 minor a11y WARN (dead aria-label) — non-blocking, axe scan covers
- ✅ Live verification absence covered by CONTEXT-BRIEF § 11 LOW + manual staging gate plan
- → **APPROVED**

---

<!-- @pm: REVIEW.md ready (verdict=APPROVED). Brand: vitalia. Cross-brand flags: 0. Engine-edit flags: 0. Live-verified: deferred to staging (CONTEXT-BRIEF § 11 LOW caveat). -->
