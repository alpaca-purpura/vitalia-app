<!-- voseo-allowed: internal implementation log -->
# T-4 Implementation Log — F1-S9 vitalia-fase1-routing-shell

**Ticket:** T-4 — FE routing pages (5 NEW + 2 MODIFY + 1 DELETE catchall)
**Brand:** vitalia
**Date:** 2026-05-25
**Builder:** frontend-developer (Claude Sonnet 4.6)
**Branch:** wip/vitalia

---

## § Skills Consulted

| Skill | Razón invocada | Decisión tomada |
|---|---|---|
| `frontend-expert` | Routing pages pattern, Server-First default, FSD-Lite paths | Server Component default. `"use client"` solo en `[agent]/not-found.tsx` (necesita `useParams()`). params Promise pattern Next.js 16. |
| `tessl__react-patterns` | Error boundaries, loading/empty/error states, accessible markup, stable keys | role="main" en outer not-found, role="region" aria-label en inner, aria-hidden="true" en emoji icons, Button asChild + Link para CTA. |
| `tessl__shadcn-ui` | Button component selection | `Button asChild` + `Link` para CTA. No recrear — reuse `components/ui/button.tsx`. |
| `tessl__tailwind` | Semantic tokens, no hardcoded hex | `text-muted-foreground`, `opacity-50`, `min-h-screen`, `flex items-center justify-center`. NO hex hardcoded. |
| `tessl__nextjs-app-router-modularization` | Server vs Client boundaries in new pages | not-found.tsx outer = Server Component (no params arg). not-found.tsx inner = Client Component (useParams). Todos los demás = Server. |

---

## § Scope T-4

### Files NEW (5)

| Path | Type | Status |
|---|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/not-found.tsx` | Server Component (outer 404) | DONE |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/layout.tsx` | Server Component | DONE |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/page.tsx` | Server Component | DONE |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/not-found.tsx` | Client Component (useParams) | DONE |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx` | Server Component | DONE |

### Files MODIFIED (1)

| Path | Change | Status |
|---|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/page.tsx` | redirect `lisa/marca` → `valeria/agenda` per Q1 decision | DONE |

### Files DELETED (1)

| Path | Reason | Status |
|---|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[...slug]/page.tsx` | F1-S7 stub obsolete post-F1-S9 | DONE |

### Arch test NEW (1)

| Path | Scope | Status |
|---|---|---|
| `vitalia/frontend/src/__tests__/architecture/test-no-dashboard-route-group.test.ts` | 2 RED (dashboard/app exist — T-5 deletes) + 1 GREEN (shell-organism exists) | DONE — expected RED per spec |

### Unit tests NEW

| Path | Tests | Status |
|---|---|---|
| `not-found.test.tsx` (outer) | 9 tests | GREEN |
| `[agent]/layout.test.tsx` | 7 tests | GREEN |
| `[agent]/page.test.tsx` | 8 tests | GREEN |
| `[agent]/[subtab]/page.test.tsx` | 11 tests | GREEN |

---

## § Technical Decisions

### 1. 'config' in [agent]/page.tsx

`AGENT_CATALOG` is `Record<AgentSlug, AgentDescriptor>` and `'config'` is not an `AgentSlug`. The spec's example code at § 9.5 shows `AGENT_CATALOG[agent as RibbonTabSlug].defaultSubtab` which would cause a TypeScript error or runtime crash for 'config'.

**Decision:** extracted `getDefaultSubtab(agent: RibbonTabSlug): string` helper that handles `'config'` specially (`return 'cuenta'`). The value 'cuenta' is the first subtab in `RIBBON_SUBTABS['config']` and aligns with spec + CONTEXT-BRIEF.

### 2. [agent]/not-found.tsx as Client Component

Next.js App Router `not-found.tsx` files do NOT receive route params as function arguments. To display the contextual agent label (e.g., "No encontramos esa vista dentro de Camila"), we need to know the agent slug. The only way to access route params in a `not-found.tsx` is via `useParams()` hook, which requires `"use client"`. This is documented in `03-arch-fe.md § 3` as a justified Client Component.

### 3. TDD vi.mock hoisting fix

Initial tests used pattern `const mockFn = vi.fn(); vi.mock("module", () => ({ fn: mockFn }))`. This fails because `vi.mock` is hoisted before `const` declarations — `mockFn` is not initialized. Fixed by:
1. Using `vi.fn()` inline in the mock factory
2. Getting the spy via `import * as navigation from "next/navigation"` + `vi.mocked(navigation.notFound)`

### 4. Arch test path resolution

`resolve(__dirname, "../../..")` from `src/__tests__/architecture/` points to `vitalia/frontend/` (not `src/`). Therefore `APP_DIR = join(ROOT, "src", "app")` — not `join(ROOT, "app")`. Validated by matching pattern used in `test-no-middleware-ts.test.ts` which uses `join(ROOT, "src")`.

### 5. Expected RED tests in arch test

The 2 tests checking `(dashboard)/` and `(app)/` are expected to FAIL in T-4 (those dirs still exist) and become GREEN in T-5 when `rm -rf app/(dashboard)/ app/(app)/` runs. This is explicitly documented in `04-validators.yaml test_construction_plan` and the ticket description.

---

## § Quality Gate Results

| Gate | Result | Notes |
|---|---|---|
| `tsc --noEmit` | PASS — 0 errors | |
| `eslint src/ --cache` | PASS — 0 errors | |
| `vitest run` | 2 expected RED / 1550 GREEN | (dashboard) + (app) arch tests expected RED per T-5 spec |
| Coverage thresholds (20%) | N/A for new files | New pages in `src/app/` — not in coverage include paths |
| Architecture fitness | 2 expected RED (T-5 scope) | All other 20 arch tests GREEN |

---

## § Microcopy Verification (01-spec.md § 10)

| Copy | Expected | Implemented | Spanish neutro |
|---|---|---|---|
| outer title | "No encontramos esta vista" | ✅ | ✅ no voseo |
| outer desc | "Quizás el enlace está roto o el agente que buscas no existe en esta clínica." | ✅ | ✅ |
| outer CTA | "Volver al inicio" | ✅ | ✅ |
| inner title | "No encontramos esa vista dentro de {label}" | ✅ | ✅ |
| inner desc | "Quizás el enlace está roto o esa sub-pestaña no existe." | ✅ | ✅ |
| inner CTA | "Ir a la vista principal de {label}" | ✅ | ✅ |

---

## § Live Verification

`chrome-devtools-verify` skill marked DEPRECATED for Linux (per CONTEXT-BRIEF.md §11 + project context note 2026-05-15). Cannot perform live browser verification in this environment.

Manual verification steps:
1. Start dev stack: `make dev-vitalia`
2. Navigate to `http://localhost:3002/{tenantId}/foo` → should see outer not-found (no chrome)
3. Navigate to `http://localhost:3002/{tenantId}/camila/foo` → should see inner not-found (with chrome)
4. Navigate to `http://localhost:3002/{tenantId}/valeria` → should redirect to `valeria/agenda`
5. Navigate to `http://localhost:3002/{tenantId}` → should redirect to `valeria/agenda`

Escalate to Chris staging gate for live verification before T-4 merge approval.

---

## § §11 Gaps from CONTEXT-BRIEF

None flagged as blocking. All T-4 scope files confirmed existing or noted as new per the brief.
