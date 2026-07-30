<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review — T-4 Routing pages (5 NEW + 2 MODIFY + 1 DELETE)

**Date:** 2026-05-26
**Brand:** vitalia
**Story:** vitalia-fase1-routing-shell (F1-S9)
**Ticket:** T-4 — `[agent]/{layout,page,not-found}.tsx` + `[agent]/[subtab]/page.tsx` + outer `not-found.tsx` + MODIFY root page + DELETE `[...slug]`
**Commit:** 99bd19e9
**Files Reviewed:** 7 source pages + 4 test files + 1 arch test
**Domains touched:** Routing pages + a11y (Next.js 16 file convention) — no agentic skill required
**Skills consulted:** frontend-expert · tessl__react-patterns · tessl__nextjs-app-router-modularization · spanish-text.md · frontend-fsd.md · tdd-mandatory.md
**Live-verified:** NO (covered by T-6 E2E + manual staging per CONTEXT-BRIEF § 11)
**Verdict:** **APPROVED**

---

## /test-vitalia Gate Status (from gate-output.json iter 1)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | Next.js 16 `params: Promise<>` strict OK |
| ESLint | PASS | 0 errors |
| Vitest | PASS | 1549/1549 (includes 9+7+8+11 = 35 page unit tests for T-4) |
| Arch fitness | PASS | includes NEW `test-no-dashboard-route-group.test.ts` (GREEN post T-5) |

---

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | pages in `app/`, validators imported from `@/lib/agent-catalog` (lib slot) — boundary OK |
| 2 | Server/Client correctness | PASS | All Server Components except `[agent]/not-found.tsx` (Client — justified by `useParams()` since not-found.tsx convention doesn't receive params arg). `params: Promise<{tenantId, agent, subtab?}>` + await in every page (Next.js 16 ✅) |
| 3 | React patterns baseline | PASS · 1 MINOR | error boundary route-level via `notFound()` → `not-found.tsx`; loading via Next streaming; aria-label dead code on aria-hidden span (see WARN) |
| 4 | Code quality | PASS | tsc/eslint clean; unused `RibbonTabSlug` import in `[agent]/not-found.tsx` line 38 (TS doesn't flag because it's a type import — eslint also OK; cosmetic) |
| 5 | Accessibility | PASS · 1 MINOR WARN | `role="main"` + `data-testid`; aria-label dead code (below). axe-core scans 4 pages in `a11y-keyboard-nav.spec.ts @axe` will catch any real violation post-merge. |
| 6 | Forms | N/A | No forms |
| 7 | Multitenancy | PASS | `tenantId` from `params` (server-side, validated upstream by parent layout T-3); no client-side injection |
| 8 | Master Data / Spanish neutro | PASS | Microcopy spec § 10 verbatim — see findings below |
| 9 | Security / Deps | PASS | XSS: validators use enum membership check (`slug in AGENT_CATALOG`); no dynamic html injection; Link from next/link for internal nav |
| 10 | Tests / TDD | PASS | RED-first per T-4-impl-log; 35 unit tests covering all branches (valid agent, invalid agent, valid subtab, invalid subtab, redirect, notFound) |
| 11 | Domain Alignment | N/A | Shell routing — no agentic surface |
| 12 | Arch Fitness | PASS | NEW `test-no-dashboard-route-group.test.ts` ratchet enforces (dashboard)/(app) removed (GREEN post T-5) |
| 13 | Mirror detection | PASS | not-found.tsx + [agent]/[subtab] pages absent in nicolify/comunify/lupulo (CONTEXT-BRIEF § 7 grep scan) |
| 14 | Decisions honored (R6) | N/A | Ticket has no `decisions_applicable` field |

---

## Findings

### PASS · Default landing change verbatim Q1 (Chris 2026-05-25)
`(shell-organism)/page.tsx:30-31`:
```ts
const { tenantId } = await params;
redirect(`/${tenantId}/valeria/agenda`);
```
Confirmed: F1-S4 default `lisa/marca` → F1-S9 default `valeria/agenda` (Chris dictum cementado).

### PASS · Next.js 16 `params: Promise<>` discipline
All routing files use:
```ts
interface PageProps { params: Promise<{tenantId, agent, ...}>; }
const { tenantId, agent } = await params;
```
Verified in:
- `(shell-organism)/page.tsx:25-31`
- `[agent]/layout.tsx:26-34`
- `[agent]/page.tsx:40-48`
- `[agent]/[subtab]/page.tsx:24-39`

### PASS · `notFound()` correctly imported from `next/navigation`
Confirmed in `[agent]/layout.tsx:22` + `[agent]/page.tsx:22` + `[agent]/[subtab]/page.tsx:20`. Spec § 9.5 + 9.6 satisfied.

### PASS · Outer not-found chrome-less, inner with chrome contextual
- `(shell-organism)/not-found.tsx` — `<main>` filling viewport, NO TopBar/Ribbon/SubTabsBar (the file lives at route-group root, parent of `[agent]/` layout where chrome lives). Verbatim spec § 6.1.
- `[agent]/not-found.tsx` — `<section>` only (chrome inherited from parent layouts), contextual `{label}` from `AGENT_CATALOG` via `useParams()` Client hook. Verbatim spec § 6.2.

### PASS · `[agent]/not-found.tsx` Client justification documented
Lines 1-15 explain why Client: "Not-found.tsx files in Next.js App Router do NOT receive params as function arguments, so `useParams()` (Client-only hook) is required to access the agent slug for contextual label." Spec § 3.3 justification respected.

### PASS · `[agent]/page.tsx` defaultSubtab redirect (handles `config`)
Lines 35-38:
```ts
function getDefaultSubtab(agent: RibbonTabSlug): string {
  if (agent === "config") return "cuenta";
  return AGENT_CATALOG[agent as AgentSlug].defaultSubtab;
}
```
Config handled as special case (not in AGENT_CATALOG, defaultSubtab `cuenta`). Spec § 9.5 satisfied.

### PASS · `[subtab]/page.tsx` defense-in-depth
Lines 28-32: both `isValidAgent(agent)` + `isValidSubtab(agent as RibbonTabSlug, subtab)` checked, `notFound()` fires either way. Spec § 9.6 satisfied. Placeholder text "Contenido próximamente — F1-S10 empty-states" awaits F1-S10.

### PASS · Microcopy spec § 10 verbatim
- not-found outer: "No encontramos esta vista" ✅ · "Quizás el enlace está roto o el agente que buscas no existe en esta clínica." ✅ · "Volver al inicio" ✅
- not-found inner: "No encontramos esa vista dentro de {label}" ✅ · "Quizás el enlace está roto o esa sub-pestaña no existe." ✅ · "Ir a la vista principal de {label}" ✅

### PASS · Spanish neutro
Grep for voseo tokens in routing-shell user-facing strings → 0 matches.

### WARN (minor a11y, non-blocking) · Dead `aria-label` on `aria-hidden` span
Both not-found pages (T-4) and NetworkErrorFallback (T-3) use:
```jsx
<span aria-hidden="true" role="img" aria-label="Advertencia">🔍</span>
```
`aria-hidden="true"` removes the element from AT tree → `aria-label="Advertencia"` is dead code (won't be read).

**Resolution paths:**
- (A) Keep `aria-hidden="true"`, drop `role="img"` + `aria-label` (purely decorative — descriptive heading text replaces icon meaning) — spec § 12 suggests this.
- (B) Drop `aria-hidden`, keep `role="img" aria-label="Advertencia"` — make icon visible to AT with semantic label.

axe-core configured at 4 pages in `a11y-keyboard-nav.spec.ts @axe`. Live run (post-merge) will flag WCAG 2.1 AA violation if rule `aria-hidden-focus` or `presentation-role-conflict` fires. **Builder-frontend self-fix scope** if axe fires — whitelist category 17 (variable renamed/dead attribute cleanup, ≤2 files, ≤10 lines per `.claude/rules/auditor-self-fix-policy.md`). Not blocking T-4 review.

### WARN (cosmetic) · Unused type import
`[agent]/not-found.tsx:38`:
```ts
import { AGENT_CATALOG, isValidAgent, type AgentSlug, type RibbonTabSlug } from "@/lib/agent-catalog";
```
`RibbonTabSlug` is imported but not used in the file. tsc + eslint don't flag (type imports are tree-shaken). Cosmetic only, can be cleaned in next iteration.

---

## Contract / UI-SPEC Compliance

- [x] All Next.js 16 conventions respected (`params: Promise<>`, `notFound()` from `next/navigation`)
- [x] Server Component default except `[agent]/not-found.tsx` (Client justified inline)
- [x] Wireframes § 6.1 + 6.2 implemented faithfully
- [x] Microcopy spec § 10 verbatim
- [x] AC-1 `/{tenant}` redirect → `/{tenant}/valeria/agenda` ✅
- [x] AC-2 `/{tenant}/{agent}` redirect → defaultSubtab ✅
- [x] AC-3 invalid agent → outer not-found 404 ✅
- [x] AC-4 invalid subtab → inner not-found 404 with chrome ✅
- [x] AC-16 `agent-catalog.ts` EXTEND validators exported (T-2) ✅

---

## Allowlist Movement
- [x] No allowlist growth.
- [x] No warning baseline growth.
- [x] NEW arch test `test-no-dashboard-route-group.test.ts` is shrink-only ratchet (forbids re-creation of legacy route groups).

## Native-First Audit
- [x] No `docker exec`, no `make e2e`, no `git add .`/-A/-u.

## Live Verification Audit
- ⚠️ NOT executed — covered by T-6 E2E specs (compile OK, live run deferred to staging) + CONTEXT-BRIEF § 11 LOW caveat.

## Skills Consulted (must_load enforcement v4.1)
- ✅ `frontend-expert` — Server Components default + Client leaf justification
- ✅ `tessl__react-patterns` — error boundary at route level via not-found.tsx convention; stable Link/Button patterns
- ✅ `tessl__nextjs-app-router-modularization` — Server pages + Client leaf split where needed
- ✅ `spanish-text.md` — neutro user-facing strings (no voseo)
- ✅ `frontend-fsd.md` — lib import boundary respected
- ✅ `tdd-mandatory.md` — RED-first per T-4-impl-log

## Verdict Math
- ✅ No FAIL in cat 1/2/3/7/11/12/14
- ⚠️ 1 minor WARN (dead aria-label) — non-blocking, axe scan covers post-merge
- ⚠️ 1 cosmetic WARN (unused type import) — cleanup in future iter
- ✅ Live verification deferred per CONTEXT-BRIEF § 11 LOW caveat
- → **APPROVED**

---

<!-- @pm: REVIEW.md ready (verdict=APPROVED). Brand: vitalia. Cross-brand flags: 0. Engine-edit flags: 0. Live-verified: deferred to T-6 E2E + staging. -->
