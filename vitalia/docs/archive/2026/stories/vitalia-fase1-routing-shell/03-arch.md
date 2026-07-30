<!-- voseo-allowed: internal architect documentation, not user-facing -->
---
story_id: vitalia-fase1-routing-shell
brand: vitalia
type: ui-story
phase: fase-1
last_modified: 2026-05-26
architect_iter: 1
architect_run_on: 2026-05-26
surfaces: FE + BE (NO agentic)
---

# F1-S9 · `vitalia-fase1-routing-shell` — 03-arch.md (consolidado)

> Single source of truth for parallel implementation across FE + BE. NO agentic surface. Sub-archivos `03-arch-be.md` y `03-arch-fe.md` también emitidos per-surface (idénticos por dimensión).

---

## § 0 — Context Summary

- **Story:** vitalia-fase1-routing-shell — outcome `vitalia-mvp-ui-foundation` fase-1. Closes shell-organism routing (último gap antes de F1-S10 empty-states).
- **PR folder:** `vitalia/docs/product/stories/vitalia-fase1-routing-shell/`
- **Architect run on:** 2026-05-26 (Step 0 captured: `date -u +%Y-%m-%d` → 2026-05-26, `date -u +%Y-%m` → 2026-05). Opus 4.7 knowledge cutoff Jan 2026; library currency verified live via WebSearch + canonical WebFetch on 2026-05-26.
- **Modules touched:**
  - `shell-organism` (brand-local Vitalia frontend chrome — routing tree + proxy + helpers + cleanup legacy).
  - `vitalia/backend/src/main.py` (1-line mount of core `auth_router`).
  - `vitalia/docs/product/capabilities/**` (1 DELETE + 6 MODIFY + 1 KEEP per spec § 3.4).

- **Surface → builder → auditor mapping** (PM uses to spawn correct agents):

  | Surface | Builder | Auditor |
  |---|---|---|
  | `vitalia/frontend/src/proxy.ts` (modify) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
  | `vitalia/frontend/src/app/[tenantId]/(shell-organism)/**` (new pages + modify layout/page + delete catchall) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
  | `vitalia/frontend/src/lib/agent-catalog.ts` (extend validators) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
  | `vitalia/frontend/src/lib/iam/api.ts` (new fetchUserTenants) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
  | `vitalia/frontend/src/app/(dashboard)/**` + `vitalia/frontend/src/app/(app)/**` (delete) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
  | `vitalia/frontend/e2e/**` (modify legacy specs + new regression suite) | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
  | `vitalia/backend/src/main.py` (mount core auth_router + remove vitalia local /me stub) | `builder-backend` (Sonnet/opencode) | `auditor-backend` (Opus) |
  | `vitalia/backend/src/modules/vitalia/iam/api/router.py` (delete `/me` stub) | `builder-backend` (Sonnet/opencode) | `auditor-backend` (Opus) |
  | `vitalia/docs/product/capabilities/**` (delete + modify YAMLs) | `builder-frontend` o `builder-backend` (cualquier sonnet — doc-only) | included in story-level review (no per-surface auditor needed for YAMLs) |

  **NO AGENTIC surface.** R23 NO aplica (zero agentic; ZERO Opus en build per scope).

- **Skills consulted (decisions ratified verbatim):**
  - `frontend-expert` — Server-First Components default; `params: Promise<>` async Next.js 16 pattern; FSD-Lite boundaries (lib/iam/api.ts vive en `lib/` cross-feature, OK); test colocation `__tests__/` sibling; cleanup legacy `(dashboard)/` = simple `rm -rf` (no migration data layer).
  - `playwright-expert` — POM pattern (`RoutingShellPage`), Clerk auth fixture reuse F1-S3, freshness gate pre-run, port 3002 vitalia, axe-core scan per scenario, `page.route()` interception para SC-5 network failure + SC-8 empty tenants response mocking.
  - `backend-expert` — minimal change BE: 1-line `app.include_router()` matching nicolify:543 pattern verbatim (`prefix="/api/v1/iam/users"`); delete vitalia local `/me` stub (anti-duplication — no consumers post-cleanup); `response_model=` ya garantizado por core router definition.
  - `tessl__nextjs-app-router-modularization` — `proxy.ts` Next.js 16 file convention (replaces `middleware.ts`); function exported as `proxy` (NOT `middleware`); Node.js runtime default (config `runtime` PROHIBITED in proxy file); negative matcher pattern excludes `_next` + static assets; `auth.protect()` from Clerk SDK redirects to `/sign-in` automatically.
  - `tessl__react-patterns` — Server Components default; no `'use client'` en routing pages (todos son async server components que invocan `redirect()`/`notFound()` server-side); inline `<NetworkErrorFallback>` JSX en server layout es OK porque es presentation puro sin hooks.

- **CONTEXT-BRIEF source:** self-ran greps Path B + Read on 01-spec.md + checkpoint.md + predecessor F1-S4 03-arch.md + agent-catalog.ts SSoT + vitalia/backend/main.py + nicolify/backend/main.py:543 + core/luana-core-iam/src/.../auth_router.py + existing proxy.ts (already created by F1-S0). CONTEXT-BRIEF.md absent (story-by-story, no Haiku context-builder for this run).

- **Cross-module anti-duplication audit (NO-NEW-LAYER):** see § 0.1 below. **Verdict: REUSE core `GET /me/tenants` (luana-core-iam) via mount + DELETE vitalia local `/me` stub.** Zero new BE endpoints. Zero parallel layer.

- **capability YAML files affected (post-merge updates required, paradigma post 2026-05):**
  - DELETE: `vitalia/docs/product/capabilities/dashboard/welcome-state.yaml` (FE-only legacy; no re-implementation in Fase 2 — landing va direct a `valeria/agenda`).
  - MODIFY (6 archivos): `booking/booking-widget-embed.yaml`, `compliance/compliance-hipaa-lite-audit.yaml`, `brand_studio/brand-studio-medical-sections.yaml`, `offer_studio/medical-services-offer-preset.yaml`, `patients/patient-records-medical-history.yaml`, `treatments/treatment-followup-workflow.yaml` — strip `+ vitalia/frontend/src/app/(dashboard)/...` del `package_path`, add `fe_planned_phase2: vitalia-fase2-{story}` field. NO cambiar `status: live`.
  - KEEP: `platform/shell-foundation-shadcn-tailwind-v4.yaml` (intacto — FE foundation activa).
  - Auto-list refresh post-merge via `reconcile_capabilities.py --brand vitalia`.

- **Architecture gates that must keep passing:**
  - `vitalia/frontend/src/__tests__/architecture/*.test.ts` (18 tests today — FSD boundaries, no-cross-brand, semantic tokens, voseo, etc.). Allowlists shrink only.
  - `vitalia/backend/tests/architecture/test_vitalia_response_models_required.py` (PII gate `response_model=`) — sin cambios (core router ya cumple).
  - `vitalia/backend/tests/architecture/test_phi_dual_filter.py` (HIPAA-lite dual filter) — N/A para `/me/tenants` (no PHI; user identity + tenant list).
  - NEW arch test sugerido (T-3): `test-no-middleware-ts.test.ts` (grep guard) + NEW (T-4): `test-no-dashboard-route-group.test.ts` (grep guard).

## § 0.1 — Existing Systems Audit (NO NEW LAYER rule)

### Source of evidence

- [ ] CONTEXT-BRIEF.md § 7 + § 8 (no context-brief para esta story)
- [x] Self-run greps (Path B — fallback)

### Audit cross-module ejecutado

```bash
# 1. ¿Existe endpoint /me/tenants en core engine?
grep -rln "me/tenants" $WS/core/luana-core-iam/src/
# Result: core/luana-core-iam/src/luana_core_iam/api/routers/auth_router.py:23 ✅ EXISTE

# 2. ¿Nicolify ya monta el router? (referencia pattern)
grep -n "auth_router\|iam_users" $WS/nicolify/backend/src/main.py
# Result: line 92 import + line 543 include_router(prefix="/api/v1/iam/users") ✅

# 3. ¿Vitalia ya tiene helper FE fetchUserTenants?
grep -rln "fetchUserTenants\|getUserTenants\|/me/tenants" $WS/vitalia/frontend/src/
# Result: 0 matches ✅ → NEW file lib/iam/api.ts

# 4. ¿Vitalia local /me stub tiene consumers además de DashboardWelcome (que se borra)?
grep -rln "/api/v1/iam/me" $WS/vitalia/frontend/src/ $WS/vitalia/backend/tests/
# Result:
#   - vitalia/frontend/src/features/dashboard/components/DashboardWelcome.tsx (DELETED en T-5 legacy cleanup)
#   - vitalia/frontend/src/features/dashboard/__tests__/DashboardWelcome.test.tsx (DELETED idem)
#   - vitalia/frontend/src/features/dashboard/types/DashboardData.ts (DELETED idem)
#   - vitalia/backend/tests/modules/vitalia/iam/test_router.py (TEST — covered by /me stub; debe eliminarse junto con stub)
# Conclusión: zero consumers post-cleanup. SAFE to delete vitalia local /me stub.

# 5. ¿proxy.ts ya existe o middleware.ts?
ls $WS/vitalia/frontend/src/proxy.ts $WS/vitalia/frontend/src/middleware.ts
# Result: proxy.ts existe (creado en F1-S0 auth-base), middleware.ts NO. ✅
# → MODIFY proxy.ts existente para añadir matcher coverage shell-organism (auth.protect already in place).

# 6. Cross-brand mirror scan (anti-duplication.md § lift shared rule)
for b in nicolify comunify lupulo; do
  grep -rln "proxy.ts\|fetchUserTenants" $b/frontend/src/ 2>/dev/null
done
# Result: 0 matches. Pattern brand-local Vitalia (Next.js 16 first-mover). LIFT-candidate cuando otras brands upgrade.

# 7. Engine core consultation (READ-ONLY)
find $WS/core -name "fetch*" -type f 2>/dev/null
# Result: zero TS helpers (engine es Python). FE helpers viven per-brand hoy. OK.
```

### Sistemas existentes encontrados

| Sistema | Path | Tipo | Estado | Decisión |
|---|---|---|---|---|
| Endpoint listado tenants user | `core/luana-core-iam/src/luana_core_iam/api/routers/auth_router.py::get_my_tenants` | core engine endpoint | active | **REUSE** via mount en `vitalia/backend/main.py` (paridad nicolify) |
| Pattern montaje nicolify | `nicolify/backend/src/main.py:543` `prefix="/api/v1/iam/users"` | reference pattern | active | **MIRROR pattern verbatim** (mismo prefix → `/api/v1/iam/users/me/tenants`) |
| `proxy.ts` Clerk wrapper | `vitalia/frontend/src/proxy.ts` | brand-local | active (F1-S0) | **MODIFY mínimo** — añadir comment/docs anclando shell-organism scope; matcher actual ya cubre shell-organism vía `auth.protect()` default branch |
| `agent-catalog.ts` SSoT 6 agentes | `vitalia/frontend/src/lib/agent-catalog.ts` | brand-local | active | **EXTEND** — añadir `isValidAgent` + `isValidSubtab` validators (zero break) |
| `fetchClient` tenant+clinic | `vitalia/frontend/src/lib/api/fetchClient.ts` | brand-local | active | **REUSE** — `fetchUserTenants` lo invoca con token+tenantId desde Clerk |
| `(shell-organism)/layout.tsx` server | `vitalia/frontend/src/app/[tenantId]/(shell-organism)/layout.tsx` | brand-local | active (F1-S4) | **MODIFY** — añadir tenant validation server-side + network error fallback + no-tenants sign-out |
| `(shell-organism)/page.tsx` redirect | `vitalia/frontend/src/app/[tenantId]/(shell-organism)/page.tsx` | brand-local | active (F1-S4) | **MODIFY** — cambiar default `lisa/marca` → `valeria/agenda` (Q1 Chris ratified) |
| `[...slug]` catchall stub | `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[...slug]/page.tsx` | brand-local | active (F1-S7 stub) | **DELETE** — obsoleto post F1-S9 (las rutas reales vienen ahora de `[agent]/[subtab]/page.tsx`) |
| Vitalia local `/me` stub | `vitalia/backend/src/modules/vitalia/iam/api/router.py::get_me` | brand-local (Slice 1) | active (sin consumers post-cleanup) | **DELETE** — anti-duplication + Chris dictum "no legacy"; FE consumer `DashboardWelcome` también delete en T-5 |
| `(dashboard)/`, `(app)/inbox/` legacy | `vitalia/frontend/src/app/(dashboard)/**` + `(app)/**` | brand-local legacy | live but no shell consumer | **DELETE entirely** (Chris dictum 2026-05-25 — no legacy en pre-prod) |
| Legacy E2E specs | `e2e/specs/regression/fidelizacion-*.spec.ts`, `e2e/specs/smoke/fidelizacion.smoke.spec.ts`, `e2e/pages/fidelizacion.page.ts` | brand-local | active | **DELETE** (fidelizacion route group eliminated) |
| Legacy visual/a11y/mobile smoke specs apuntando a `(dashboard)` | `e2e/visual/visual-smoke.spec.ts`, `e2e/visual/stack-stability/dev-stack-baseline.spec.ts`, `e2e/mobile/mobile-smoke.spec.ts`, `e2e/a11y/a11y-smoke.spec.ts` | brand-local | active | **MODIFY** (refactor: drop dashboard assertions; replace with `(shell-organism)` or `test-stack` targets) |

### Decisión por sistema

- **Sistema: core `/me/tenants`** → **REUSE via mount**. Justificación: endpoint canónico vive en `luana-core-iam`; vitalia consume via 1-line `app.include_router(...)` con prefix paridad nicolify. Cero duplication. Engine read-only — no edit.
- **Sistema: vitalia local `/me` stub** → **DELETE**. Justificación: (1) sin consumers post legacy cleanup, (2) anti-duplication (core `/me` también devuelve user — semantic overlap), (3) Chris dictum "no legacy", (4) reduce surface area HIPAA-lite audit.
- **Sistema: proxy.ts existente** → **MODIFY mínimo**. Justificación: ya creado F1-S0 auth-base; `auth.protect()` default branch ya cubre `[tenantId]/**`. Cambio = solo añadir comment-docs anclando shell-organism scope + verificar matcher excluye `_next` + `api/` correctamente. Cero rewrite.
- **Cross-brand mirror**: Pattern Vitalia Next.js 16 first-mover → anotar en learnings como `promotable: candidate` para lift a `core/luana-core-frontend-shared/` cuando nicolify/comunify/lupulo migran a Next.js 16. NO mirror prematuro.

---

## § 1 — High-level Architecture

### § 1.1 — Routing tree post-merge

```
vitalia/frontend/src/
├── proxy.ts                                         # MODIFY (docs + verify matcher coverage)
└── app/
    ├── (auth)/
    │   ├── sign-in/[[...rest]]/page.tsx             # KEEP (Clerk hosted page)
    │   └── sign-up/[[...rest]]/page.tsx             # KEEP
    ├── (dashboard)/                                  # DELETE entire dir
    ├── (app)/                                        # DELETE entire dir
    ├── marketing/page.tsx                            # KEEP (public landing)
    ├── onboarding/wizard/page.tsx                    # KEEP (post-sign-up flow)
    ├── public/[clinic-slug]/                         # KEEP (public agendamiento per clínica)
    ├── test-stack/                                   # KEEP (Playwright visual baseline)
    └── [tenantId]/
        └── (shell-organism)/
            ├── layout.tsx                            # MODIFY (tenant validation + network fallback + no-tenants edge)
            ├── page.tsx                              # MODIFY (redirect → valeria/agenda)
            ├── not-found.tsx                        # NEW (outer 404, sin chrome)
            ├── [...slug]/page.tsx                   # DELETE (F1-S7 stub obsoleto)
            └── [agent]/
                ├── layout.tsx                        # NEW (isValidAgent gate)
                ├── page.tsx                          # NEW (redirect → defaultSubtab)
                ├── not-found.tsx                    # NEW (inner 404, con chrome contextual)
                └── [subtab]/
                    └── page.tsx                      # NEW (isValidSubtab + placeholder F1-S10)
```

### § 1.2 — Request flow (happy path) — login → shell

```
1. User hits dev-app.vitalialat.com/
   ↓
2. proxy.ts intercepta — auth.protect() check
   - No session → redirect /sign-in (Clerk hosted)
   - Session → continue
   ↓
3. Clerk post-login redirect → /{tenantId}/(shell-organism)/
   (Clerk SSR config: afterSignInUrl = /[active-org-id]; Next.js maps to (shell-organism)/page.tsx)
   ↓
4. (shell-organism)/layout.tsx (Server Component) executes:
   - await params → { tenantId }
   - await auth() → { userId }
   - try: tenants = await fetchUserTenants(userId)
     - On AbortError/network → <NetworkErrorFallback /> (inline)
   - If tenants.length === 0 → audit log + redirect /sign-out?next=...
   - If !tenants.some(t => t.id === tenantId) → audit log + redirect first valid tenant
   - Else → wrap children in <ShellOrganismLayout tenantId>
   ↓
5. (shell-organism)/page.tsx → redirect /{tenantId}/valeria/agenda
   ↓
6. [agent]/layout.tsx (Server Component) → isValidAgent("valeria") → true → render children
   ↓
7. [agent]/page.tsx → redirect /{tenantId}/valeria/agenda
   (Note: ya estamos ahí; este redirect aplica si user hace /{tenantId}/valeria sin subtab)
   ↓
8. [agent]/[subtab]/page.tsx → isValidSubtab("valeria","agenda") → true → render placeholder F1-S10
   ↓
9. Final UI: TopBar · ValeriaSidebar · Ribbon (Valeria active) · SubTabsBar (Agenda active) · placeholder
```

### § 1.3 — Request flow (edge case Q6) — user sin tenants

```
1-3. idem happy.
4. fetchUserTenants(userId) → [] (BE devuelve lista vacía)
5. layout.tsx:
   - logNoTenantsAssigned({ userId }) → audit_log row
   - redirect("/sign-out?next=/sign-in?error=no_tenants_assigned")
6. Clerk sign-out endpoint clears session
7. Browser final URL: /sign-in?error=no_tenants_assigned
8. /sign-in page reads ?error=... query param → renders message "Tu cuenta no tiene clínicas asignadas. Contactá al administrador..."
```

### § 1.4 — Request flow (SC-4) — cross-tenant attempt

```
1-3. user JWT.tenant_id = clinic-A, but URL = /clinic-B/(shell-organism)/valeria/agenda
4. fetchUserTenants(userId) → [{ id: "clinic-A", name: "Clinic A" }]
5. layout.tsx detects: params.tenantId="clinic-B" ∉ tenants
   - logCrossTenantAttempt({ userId, attemptedTenant: "clinic-B" }) → audit_log row
   - redirect("/clinic-A/valeria/agenda")
6. Browser final URL: /clinic-A/valeria/agenda (NO leak de chrome clinic-B)
```

---

## § 2 — Backend (BE wiring — minimal)

### § 2.1 — Domain entities

**N/A** — no entities new. Reusing core `User` + `TenantSchema` from `luana_core_iam`.

### § 2.2 — SQLAlchemy 2.0 models

**N/A** — no models new.

### § 2.3 — Pydantic v2 DTOs

**N/A** — DTOs heredados de core engine (`TenantSchema` en `luana_core_iam.api.dto.users`).

### § 2.4 — API Routes

| Method | Path | Auth | Request | Response | Description |
|---|---|---|---|---|---|
| GET | `/api/v1/iam/users/me` | Bearer (Clerk JWT) | n/a | `User` (core schema) | Current user profile — **REUSE core endpoint** |
| GET | `/api/v1/iam/users/me/tenants` | Bearer (Clerk JWT) | n/a | `list[TenantSchema]` | List user's tenants — **REUSE core endpoint** (F1-S9 primary consumer) |
| GET | `/api/v1/iam/me` | Bearer + `X-Tenant-ID` | n/a | `MeResponse` (brand stub) | **DELETE** (vitalia legacy slice 1 stub — no consumers post-cleanup) |

**FastAPI app**: `redirect_slashes=False` already in `vitalia/backend/src/main.py:39` (arch test enforces — no change).

### § 2.5 — TypeScript types (frontend mirror)

```ts
// vitalia/frontend/src/lib/iam/types.ts (NEW)
export interface UserTenant {
  id: string;          // UUID (string per JSON serialization)
  name: string;
  slug: string;
  // Note: TenantSchema en core puede tener más fields; FE consume sólo id + name.
}
```

(Exact shape verified at build time against core `TenantSchema`.)

### § 2.6 — Repository interfaces

**N/A** — no new repos. Core's `UserService.get_user_tenants(user_id)` already implements the read with tenant_id-aware filtering (inherits core IAM tenant isolation).

### § 2.7 — Application services

**N/A** — no new services.

### § 2.8 — Migration notes

**N/A** — no DDL changes. Mounting a router doesn't touch schema.

### § 2.9 — Wiring change (verbatim diff)

```python
# vitalia/backend/src/main.py — DIFF

# ADD import after line 27 (idem nicolify:92):
from luana_core_iam.api.routers import auth_router as iam_users

# REMOVE import (line 26):
- from src.modules.vitalia.iam.api.router import router as iam_router

# REMOVE include_router (line 47):
- app.include_router(iam_router, prefix="/api/v1/iam")

# ADD include_router (paridad nicolify:543, after vitalia_router mount):
+ app.include_router(
+     iam_users.router,
+     prefix="/api/v1/iam/users",
+     tags=["IAM - Users"],
+ )

# DELETE entire file (no consumers post legacy cleanup):
- vitalia/backend/src/modules/vitalia/iam/api/router.py
- vitalia/backend/tests/modules/vitalia/iam/test_router.py (associated test file)
```

**Net result**: `GET /api/v1/iam/users/me/tenants` accessible · `GET /api/v1/iam/me` returns 404 (Chris dictum no legacy).

---

## § 3 — Frontend

### § 3.1 — `proxy.ts` (MODIFY — minimal)

The existing `proxy.ts` (F1-S0) already implements the canonical Next.js 16 + Clerk pattern. F1-S9 only adds documentation anchors. **Net diff is comments + 1 line clarifying shell-organism scope is covered by `auth.protect()` default branch.**

```ts
// vitalia/frontend/src/proxy.ts (post F1-S9)
/**
 * Clerk Proxy — Vitalia (F1-S0 created · F1-S9 anchored shell-organism scope)
 *
 * Next.js 16 file convention: `proxy.ts` (replaces `middleware.ts`).
 * Function exported as `proxy` (NOT `middleware`). Runtime: Node.js default.
 *
 * Public routes (whitelist): sign-in, sign-up, marketing landing, public clínica
 *   agendamiento, webhooks BE (HMAC validated), health check, test-stack
 *   (Playwright visual baseline, no PHI).
 *
 * All other routes (incl. `/[tenantId]/(shell-organism)/**`) → auth.protect()
 * redirects to /sign-in if no Clerk session. Tenant ownership validation
 * happens in (shell-organism)/layout.tsx server-side (defense-in-depth).
 *
 * Canonical reference: https://nextjs.org/docs/app/api-reference/file-conventions/proxy (accessed 2026-05-26)
 */

import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isPublicRoute = createRouteMatcher([
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/public(.*)",
  "/marketing(.*)",          // F1-S9 explicit (marketing landing — was implicit pre)
  "/api/v1/vitalia/webhooks(.*)",
  "/api/health",
  "/test-stack(.*)",
]);

export const proxy = clerkMiddleware(async (auth, request) => {
  if (!isPublicRoute(request)) {
    await auth.protect();
  }
});

export default proxy;

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
```

### § 3.2 — `lib/agent-catalog.ts` (EXTEND — add 2 validators)

```ts
// vitalia/frontend/src/lib/agent-catalog.ts — EXTEND F1-S9
// (Append after existing extractSubtabFromPath function — line ~275)

/**
 * Type guard: validates `slug` is a known RibbonTabSlug (5 agents + 'config').
 * Mateo NOT included (transversal, not in Ribbon — paridad F1-S7 / AGENT_RIBBON_ORDER).
 *
 * Used by:
 * - [agent]/layout.tsx server-side gate (F1-S9)
 * - [agent]/page.tsx default redirect (F1-S9)
 * - [agent]/[subtab]/page.tsx validation (F1-S9)
 *
 * spec_anchor: F1-S9 01-spec.md § 9.4 + AC-16
 */
export function isValidAgent(slug: string): slug is RibbonTabSlug {
  if (slug === "config") return true;
  return (AGENT_RIBBON_ORDER as readonly string[]).includes(slug);
}

/**
 * Validates `subtab` is a known sub-tab id within the agent's RIBBON_SUBTABS list.
 *
 * Pre-condition: caller MUST have already verified `agent` via isValidAgent.
 * Returns false defensively if agent is unknown (defense-in-depth).
 *
 * spec_anchor: F1-S9 01-spec.md § 9.4 + AC-16
 */
export function isValidSubtab(agent: RibbonTabSlug, subtab: string): boolean {
  const subtabs = RIBBON_SUBTABS[agent];
  if (!subtabs || subtabs.length === 0) return false;
  return subtabs.some((st) => st.id === subtab);
}
```

**Test surface** (TDD RED first in T-2):
- `lib/__tests__/agent-catalog.test.ts` — extend with ~14 new test cases (5 agents × valid/invalid + config + edge mateo + 22 subtab combos).

### § 3.3 — `lib/iam/api.ts` (NEW — `fetchUserTenants`)

```ts
// vitalia/frontend/src/lib/iam/api.ts (NEW)
/**
 * IAM API helpers — Vitalia FE.
 * F1-S9 vitalia-fase1-routing-shell — server-side tenant fetch.
 *
 * Anti-duplication: consumes core endpoint `/api/v1/iam/users/me/tenants`
 * (mounted in vitalia/backend/main.py from luana_core_iam.api.routers.auth_router).
 * DO NOT duplicate the listing logic locally.
 *
 * spec_anchor: F1-S9 01-spec.md § 3.4 + § 9.3 + Q8 ratified
 */

import type { UserTenant } from "./types";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8002";

export interface FetchUserTenantsError {
  code: "network_failure" | "unauthorized" | "unknown";
  status?: number;
  message: string;
}

/**
 * Fetch user's tenant list from BE (core /me/tenants).
 *
 * Server-side only — uses Clerk auth() bearer token from caller layout.
 * Timeout: 5s (AbortController). On timeout/network failure → throws.
 *
 * @throws FetchUserTenantsError on network failure or 401/5xx response.
 */
export async function fetchUserTenants(args: {
  token: string;
  signal?: AbortSignal;
}): Promise<UserTenant[]> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);

  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/iam/users/me/tenants`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${args.token}`,
        // X-Tenant-ID NOT required for /me/tenants — endpoint is user-scoped, not tenant-scoped
      },
      signal: args.signal ?? controller.signal,
      cache: "no-store",   // tenant list can change (e.g., admin assigns new tenant)
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw {
        code: response.status === 401 ? "unauthorized" : "unknown",
        status: response.status,
        message: `BE /me/tenants returned ${response.status}`,
      } as FetchUserTenantsError;
    }

    return (await response.json()) as UserTenant[];
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof Error && err.name === "AbortError") {
      throw { code: "network_failure", message: "Tenant fetch timeout" } as FetchUserTenantsError;
    }
    if (typeof err === "object" && err !== null && "code" in err) throw err;
    throw { code: "network_failure", message: String(err) } as FetchUserTenantsError;
  }
}
```

**Test surface** (TDD RED first in T-2):
- `lib/iam/__tests__/api.test.ts` — vitest with mocked `global.fetch`:
  - happy path (200 → array)
  - 401 → throws `{ code: "unauthorized", status: 401 }`
  - 500 → throws `{ code: "unknown", status: 500 }`
  - timeout → throws `{ code: "network_failure" }`
  - empty array → returns `[]` (valid response, NOT error — Q6 edge)

### § 3.4 — `(shell-organism)/layout.tsx` (MODIFY)

```tsx
// vitalia/frontend/src/app/[tenantId]/(shell-organism)/layout.tsx — MODIFY F1-S9
/**
 * Shell Organism Route Group Layout — Server Component.
 * F1-S4 created · F1-S9 added tenant validation + network fallback + no-tenants edge.
 *
 * Sequence (server-side, before any chrome renders):
 * 1. Await params + auth().
 * 2. Fetch user tenants via core endpoint (catches network failure).
 * 3. If tenants.length === 0 → audit + sign-out (Q6 edge SC-8).
 * 4. If params.tenantId ∉ tenants → audit + redirect first valid (SC-4).
 * 5. Else → wrap children in ShellOrganismLayout (chrome).
 *
 * spec_anchor: F1-S9 01-spec.md § 9.3 + § 15 (HIPAA-lite audit log)
 */

import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { ShellOrganismLayout } from "@/components/shared/shell-organism/ShellOrganismLayout";
import { fetchUserTenants, type FetchUserTenantsError } from "@/lib/iam/api";
import { NetworkErrorFallback } from "./_components/NetworkErrorFallback";  // see § 3.4.1
import { logCrossTenantAttempt, logNoTenantsAssigned } from "@/lib/iam/audit";  // see § 3.4.2

interface LayoutProps {
  children: React.ReactNode;
  params: Promise<{ tenantId: string }>;
}

export default async function Layout({ children, params }: LayoutProps) {
  const { tenantId } = await params;
  const { userId, getToken } = await auth();
  if (!userId) redirect("/sign-in");   // defense-in-depth (proxy ya lo hace)

  const token = await getToken();
  if (!token) redirect("/sign-in");

  let tenants;
  try {
    tenants = await fetchUserTenants({ token });
  } catch (err) {
    const e = err as FetchUserTenantsError;
    if (e.code === "unauthorized") redirect("/sign-in");
    // Network failure (timeout, 5xx) → render fallback (Q7: manual retry only)
    return <NetworkErrorFallback />;
  }

  // Q6 edge SC-8: user authenticated but no tenants assigned.
  if (tenants.length === 0) {
    await logNoTenantsAssigned({ userId });
    redirect("/sign-out?next=/sign-in?error=no_tenants_assigned");
  }

  const isValidTenant = tenants.some((t) => t.id === tenantId);
  if (!isValidTenant) {
    // SC-4 cross-tenant attempt: audit log + redirect first valid tenant.
    await logCrossTenantAttempt({ userId, attemptedTenant: tenantId });
    redirect(`/${tenants[0].id}/valeria/agenda`);
  }

  return <ShellOrganismLayout tenantId={tenantId}>{children}</ShellOrganismLayout>;
}
```

#### § 3.4.1 — `_components/NetworkErrorFallback.tsx` (NEW — inline)

```tsx
// vitalia/frontend/src/app/[tenantId]/(shell-organism)/_components/NetworkErrorFallback.tsx (NEW)
/**
 * Network error fallback — rendered when fetchUserTenants throws on network failure.
 *
 * Server Component (no hooks). Client-side "Reintentar" button uses router.refresh()
 * via a thin Client Component leaf — see RefreshButton below.
 *
 * spec_anchor: F1-S9 01-spec.md § 6.3 + SC-5
 */

import { RefreshButton } from "./RefreshButton";

export function NetworkErrorFallback() {
  return (
    <div
      role="alert"
      aria-live="polite"
      data-testid="network-error-fallback"
      className="flex flex-col items-center justify-center min-h-screen p-10 text-center"
    >
      <span aria-hidden="true" className="text-6xl mb-4 opacity-50">⚠️</span>
      <h2 className="text-xl font-semibold mb-2">
        Estamos teniendo problemas conectando con el servidor
      </h2>
      <p className="text-muted-foreground mb-6 max-w-md">
        Intenta de nuevo en unos segundos.
      </p>
      <RefreshButton />
    </div>
  );
}
```

```tsx
// vitalia/frontend/src/app/[tenantId]/(shell-organism)/_components/RefreshButton.tsx (NEW — Client leaf)
"use client";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

export function RefreshButton() {
  const router = useRouter();
  return (
    <Button onClick={() => router.refresh()} data-testid="network-error-retry">
      Reintentar
    </Button>
  );
}
```

#### § 3.4.2 — `lib/iam/audit.ts` (NEW — audit helpers)

```ts
// vitalia/frontend/src/lib/iam/audit.ts (NEW)
/**
 * Audit log helpers — vitalia HIPAA-lite.
 *
 * Server-side only. POST to BE audit_log endpoint (best-effort: try/catch,
 * structlog warn on failure — never block routing on audit log failure).
 *
 * Scope: SC-4 cross-tenant attempts + SC-8 no-tenants-assigned events.
 * PII rule: payload includes ONLY user_id + attempted_tenant_id + timestamp.
 *           NO PHI (per .claude/rules/hipaa-lite.md sanitization rule).
 *
 * spec_anchor: F1-S9 01-spec.md § 15 + vitalia/.claude/rules/hipaa-lite.md § Audit log
 */

interface AuditPayload {
  userId: string;
  action: "cross_tenant_attempt" | "no_tenants_assigned";
  attemptedTenant?: string;
  timestamp: string;  // ISO 8601 UTC
}

async function postAudit(payload: AuditPayload): Promise<void> {
  // BE endpoint TBD: F1-S9 uses console.warn fallback if BE audit endpoint not yet wired.
  // F2+ wires real `/api/v1/vitalia/audit/cross-tenant-attempt` etc.
  try {
    if (process.env.NEXT_PUBLIC_AUDIT_ENABLED === "true") {
      // BE endpoint to be wired in F2 (out of F1-S9 scope per spec § 13 telemetry).
      // For now: structured console log captured by Next.js runtime logs.
    }
    console.warn("[audit]", JSON.stringify(payload));
  } catch {
    /* best-effort — never throw from audit helper */
  }
}

export async function logCrossTenantAttempt(args: { userId: string; attemptedTenant: string }) {
  await postAudit({
    userId: args.userId,
    action: "cross_tenant_attempt",
    attemptedTenant: args.attemptedTenant,
    timestamp: new Date().toISOString(),
  });
}

export async function logNoTenantsAssigned(args: { userId: string }) {
  await postAudit({
    userId: args.userId,
    action: "no_tenants_assigned",
    timestamp: new Date().toISOString(),
  });
}
```

**Note:** F1-S9 uses `console.warn` as transport (captured by Next.js runtime logs). A BE audit endpoint is **F2 scope** (per spec § 13 telemetry deferred). This keeps F1-S9 small + unblocks Fase 2 cabling.

### § 3.5 — `(shell-organism)/page.tsx` (MODIFY — change default)

```tsx
// vitalia/frontend/src/app/[tenantId]/(shell-organism)/page.tsx — MODIFY F1-S9
import { redirect } from "next/navigation";

interface PageProps {
  params: Promise<{ tenantId: string }>;
}

export default async function ShellRootPage({ params }: PageProps) {
  const { tenantId } = await params;
  redirect(`/${tenantId}/valeria/agenda`);   // F1-S9 Q1: changed from F1-S4 'lisa/marca'
}
```

### § 3.6 — `(shell-organism)/[agent]/layout.tsx` (NEW)

```tsx
// vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/layout.tsx (NEW)
import { notFound } from "next/navigation";
import { isValidAgent } from "@/lib/agent-catalog";

interface AgentLayoutProps {
  children: React.ReactNode;
  params: Promise<{ tenantId: string; agent: string }>;
}

export default async function AgentLayout({ children, params }: AgentLayoutProps) {
  const { agent } = await params;
  if (!isValidAgent(agent)) notFound();   // triggers [agent]/not-found.tsx? No — closest not-found is outer (shell-organism)/not-found.tsx since agent slug invalid means no chrome context.
  return <>{children}</>;
}
```

**Note on not-found resolution:** Next.js 16 resolves `notFound()` to the closest `not-found.tsx` upward in the segment tree. When `[agent]/layout.tsx` calls `notFound()`, Next.js renders `(shell-organism)/not-found.tsx` (outer) because the layout itself failed — no `[agent]` segment fully resolved. The inner `[agent]/not-found.tsx` is reached when `[agent]/[subtab]/page.tsx` calls `notFound()` (subtab invalid, agent valid).

### § 3.7 — `(shell-organism)/[agent]/page.tsx` (NEW — default subtab redirect)

```tsx
// vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/page.tsx (NEW)
import { redirect, notFound } from "next/navigation";
import { AGENT_CATALOG, isValidAgent, type AgentSlug } from "@/lib/agent-catalog";

interface PageProps {
  params: Promise<{ tenantId: string; agent: string }>;
}

export default async function AgentRootPage({ params }: PageProps) {
  const { tenantId, agent } = await params;
  if (!isValidAgent(agent)) notFound();

  // config is a RibbonTabSlug but NOT in AGENT_CATALOG (no AgentDescriptor for 'config').
  // Default subtab for config: first sub-tab (cuenta).
  if (agent === "config") redirect(`/${tenantId}/config/cuenta`);

  const defaultSubtab = AGENT_CATALOG[agent as AgentSlug].defaultSubtab;
  redirect(`/${tenantId}/${agent}/${defaultSubtab}`);
}
```

### § 3.8 — `(shell-organism)/[agent]/[subtab]/page.tsx` (NEW)

```tsx
// vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx (NEW)
import { notFound } from "next/navigation";
import { isValidAgent, isValidSubtab, type RibbonTabSlug } from "@/lib/agent-catalog";

interface PageProps {
  params: Promise<{ tenantId: string; agent: string; subtab: string }>;
}

export default async function SubtabPage({ params }: PageProps) {
  const { agent, subtab } = await params;
  if (!isValidAgent(agent)) notFound();
  if (!isValidSubtab(agent as RibbonTabSlug, subtab)) notFound();

  // F1-S10 will replace this placeholder with <SubTabContent agent subtab />
  return (
    <div className="flex items-center justify-center h-full text-muted-foreground" data-testid="subtab-placeholder">
      <p>Contenido próximamente — F1-S10 empty-states</p>
    </div>
  );
}
```

### § 3.9 — `(shell-organism)/not-found.tsx` (NEW — outer)

```tsx
// vitalia/frontend/src/app/[tenantId]/(shell-organism)/not-found.tsx (NEW)
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFoundShell() {
  return (
    <div
      role="main"
      data-testid="not-found-shell"
      className="flex flex-col items-center justify-center min-h-screen p-10 text-center"
    >
      <span aria-hidden="true" className="text-6xl mb-4 opacity-50">🔍</span>
      <h2 className="text-xl font-semibold mb-2">No encontramos esta vista</h2>
      <p className="text-muted-foreground mb-6 max-w-md">
        Quizás el enlace está roto o el agente que buscas no existe en esta clínica.
      </p>
      <Button asChild>
        <Link href="/">Volver al inicio</Link>
      </Button>
    </div>
  );
}

export const metadata = {
  title: "Vitalia · Página no encontrada",
};
```

### § 3.10 — `(shell-organism)/[agent]/not-found.tsx` (NEW — inner)

```tsx
// vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/not-found.tsx (NEW)
"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { AGENT_CATALOG, type AgentSlug } from "@/lib/agent-catalog";

export default function NotFoundAgent() {
  const params = useParams<{ tenantId: string; agent: string }>();
  const agent = params.agent;
  // At this point agent is guaranteed valid (outer layout passed isValidAgent).
  // config special case (no AgentDescriptor for 'config'):
  const isConfig = agent === "config";
  const agentLabel = isConfig ? "Configurar" : AGENT_CATALOG[agent as AgentSlug].name;
  const defaultSubtab = isConfig ? "cuenta" : AGENT_CATALOG[agent as AgentSlug].defaultSubtab;

  return (
    <div
      role="region"
      aria-label="Vista no encontrada"
      data-testid="not-found-agent"
      className="flex flex-col items-center justify-center h-full p-10 text-center"
    >
      <span aria-hidden="true" className="text-6xl mb-4 opacity-50">🔍</span>
      <h2 className="text-xl font-semibold mb-2">
        No encontramos esa vista dentro de {agentLabel}
      </h2>
      <p className="text-muted-foreground mb-6 max-w-md">
        Quizás el enlace está roto o esa sub-pestaña no existe.
      </p>
      <Button asChild>
        <Link href={`/${params.tenantId}/${agent}/${defaultSubtab}`}>
          Ir a la vista principal de {agentLabel}
        </Link>
      </Button>
    </div>
  );
}
```

**Note**: This must be `"use client"` because `useParams()` is a Client hook. Inner not-found is the only Client Component in the routing tree (because we need the contextual `agent` slug to dynamically render the right label/CTA). All others are pure Server Components.

### § 3.11 — DELETE — `(shell-organism)/[...slug]/page.tsx`

```bash
rm vitalia/frontend/src/app/\[tenantId\]/\(shell-organism\)/\[...slug\]/page.tsx
rmdir vitalia/frontend/src/app/\[tenantId\]/\(shell-organism\)/\[...slug\]
```

Justificación: F1-S7 stub que servía para tests Ribbon active state. Post F1-S9 las rutas reales vienen de `[agent]/[subtab]/page.tsx`. Stub catchall colisiona con la tree dinámica si queda.

### § 3.12 — DELETE — legacy app dirs

```bash
rm -rf vitalia/frontend/src/app/\(dashboard\)/
rm -rf vitalia/frontend/src/app/\(app\)/
```

Sub-directorios afectados: `offers`, `bookings`, `appointments`, `brand-studio`, `fidelizacion`, `medical-compliance`, `patients`, `treatments`, `inbox`. **Total: 9 sub-routes + layouts/pages eliminated.**

**Pre-merge gate**: ensure no `vitalia/frontend/src/features/{dashboard,...}/` imports from these route groups. If features reference them, those features are unconsumed (no public landing). Decision per spec § 16: features stay (BE-only consumers remain via tests/admin), routes go.

### § 3.13 — E2E specs refactor

Per spec § 3.4 / § 16:

- **DELETE**:
  - `vitalia/frontend/e2e/pages/fidelizacion.page.ts` (POM legacy)
  - `vitalia/frontend/e2e/specs/regression/fidelizacion-*.spec.ts` (4 specs)
  - `vitalia/frontend/e2e/specs/smoke/fidelizacion.smoke.spec.ts`
- **MODIFY** (drop `(dashboard)` assertions, redirect targets to `test-stack` or `(shell-organism)`):
  - `vitalia/frontend/e2e/visual/visual-smoke.spec.ts`
  - `vitalia/frontend/e2e/visual/stack-stability/dev-stack-baseline.spec.ts`
  - `vitalia/frontend/e2e/mobile/mobile-smoke.spec.ts`
  - `vitalia/frontend/e2e/a11y/a11y-smoke.spec.ts`

### § 3.14 — NEW Playwright E2E suite

```
vitalia/frontend/e2e/regression/vitalia-fase1-routing-shell/
├── happy-navigation.spec.ts            # SC-1
├── not-found-outer.spec.ts             # SC-2
├── not-found-inner.spec.ts             # SC-3
├── cross-tenant-blocked.spec.ts        # SC-4
├── network-failure-tenant-fetch.spec.ts # SC-5
├── a11y-keyboard-nav.spec.ts           # SC-6 (axe-core integration)
├── i18n-spanish-neutro.spec.ts         # SC-7 (regex scan)
├── no-tenants-edge.spec.ts             # SC-8
└── (visual goldens for not-found outer/inner + network fallback, light/dark)
```

**POM**: `vitalia/frontend/e2e/pages/RoutingShellPage.ts` with methods:
- `gotoTenantRoot(tenantId)`
- `gotoInvalidAgent(tenantId, slug)`
- `gotoInvalidSubtab(tenantId, agent, slug)`
- `mockNetworkFailure(delay)` (uses Playwright `page.route()`)
- `mockEmptyTenants()` (returns `[]`)
- `waitForRibbonActive(agent)`
- `waitForSubTabActive(subtab)`
- `assertHttp404()`

**Fixtures**:
- REUSE `vitalia/frontend/e2e/auth.fixture.ts` (Clerk session)
- NEW `vitalia/frontend/e2e/fixtures/routing-shell.fixture.ts` (per-test BE mocks)

---

## § 4 — Architecture fitness gates (validators category 5)

### § 4.1 — Existing gates (must keep passing)

| Gate | File | Why F1-S9 impacts |
|---|---|---|
| FSD-Lite boundaries | `vitalia/frontend/src/__tests__/architecture/test_fsd_boundaries.test.ts` | New `lib/iam/` cross-feature OK (no `features/` import) |
| Agent catalog SSoT | `vitalia/frontend/src/__tests__/architecture/test-agent-catalog-ssot.test.ts` | EXTEND validators must satisfy ratchet (count growth allowed for net-new exports per spec § 16) |
| Shell store schema | `vitalia/frontend/src/__tests__/architecture/test-shell-store-schema.test.ts` | Sin cambios (F1-S9 no toca store) |
| No-cross-brand mirror | `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` | proxy.ts / lib/iam pattern brand-local — verify no nicolify-mirror reference |
| No-voseo | `vitalia/frontend/src/__tests__/architecture/test_no_voseo_in_copy.test.ts` + `test-vitalia-ui-strings-no-voseo.test.ts` | not-found copy + network error copy + audit log strings |
| Hardcoded colors | `vitalia/frontend/src/__tests__/architecture/test_no_hardcoded_colors.test.ts` | not-found uses semantic `text-muted-foreground`, `opacity-50` — verify pass |
| Server-first | `vitalia/frontend/src/__tests__/architecture/test_server_first.test.ts` | Only inner `not-found.tsx` + `RefreshButton.tsx` are Client — both justified (useParams, useRouter) |
| BE response_model PII | `vitalia/backend/tests/architecture/test_vitalia_response_models_required.py` | Core router already compliant |
| BE redirect_slashes | (implicit in app instantiation) | Unchanged |
| BE PHI dual filter | `vitalia/backend/tests/architecture/test_phi_dual_filter.py` | `/me/tenants` exempt (no PHI; user identity + tenant list) |

### § 4.2 — NEW arch tests (T-3 + T-4)

| Test ID | File | Purpose | Command |
|---|---|---|---|
| `arch-no-middleware-ts` | `vitalia/frontend/src/__tests__/architecture/test-no-middleware-ts.test.ts` (NEW) | Guard: middleware.ts MUST NOT exist (Next.js 16 file convention) | `npx vitest run src/__tests__/architecture/test-no-middleware-ts.test.ts` |
| `arch-no-dashboard-route-group` | `vitalia/frontend/src/__tests__/architecture/test-no-dashboard-route-group.test.ts` (NEW) | Guard: no `app/(dashboard)/` or `app/(app)/` directories | `npx vitest run src/__tests__/architecture/test-no-dashboard-route-group.test.ts` |
| `arch-proxy-ts-exists` | (covered by existing tsc-build — proxy.ts is a build-time required file once auth is enabled) | n/a | n/a |

Allowlist principle: both new tests start at `KNOWN_VIOLATIONS = []` (zero baseline). Future violations require justification.

---

## § 5 — Cross-cutting concerns

- **Tenant isolation** — layout server-side validates `params.tenantId ∈ user.tenants`. Audit log captures cross-tenant attempts. Defense-in-depth: BE `/me/tenants` enforces tenant_id at core IAM level.
- **Currency / master data** — N/A (no monetary fields; no date formatting in routing).
- **Spanish neutro LatAm** — all user-facing strings checked (not-found copy, network fallback, sign-in error). Glosario verbatim per `.claude/rules/spanish-text.md`. Audit log strings (internal) NOT user-facing — no voseo check needed.
- **PII / HIPAA-lite** — `/me/tenants` returns User identity + tenant list (NOT PHI per `vitalia/.claude/rules/hipaa-lite.md` PHI canonical list). audit_log payload: `userId + attemptedTenant + timestamp` only. NO PHI in routing.
- **Native-first dev** — all lint/tests/typecheck native Linux per `.claude/rules/backend-quality.md` + `frontend-quality.md`. No `docker exec`.

---

## § 6 — Test surfaces (TDD-mandatory)

| Layer | RED first | GREEN file(s) |
|---|---|---|
| BE app mount | `vitalia/backend/tests/test_main_iam_routes_mounted.py` (NEW — asserts GET `/api/v1/iam/users/me/tenants` is registered + GET `/api/v1/iam/me` is 404) | `vitalia/backend/src/main.py` (modified) |
| BE legacy stub deletion | (delete test file alongside stub) | `vitalia/backend/src/modules/vitalia/iam/api/router.py` (delete) |
| FE lib agent-catalog | `vitalia/frontend/src/lib/__tests__/agent-catalog.test.ts` (EXTEND — ~14 new cases) | `vitalia/frontend/src/lib/agent-catalog.ts` (extend) |
| FE lib iam api | `vitalia/frontend/src/lib/iam/__tests__/api.test.ts` (NEW — 5 cases) | `vitalia/frontend/src/lib/iam/api.ts` (new) |
| FE lib iam audit | `vitalia/frontend/src/lib/iam/__tests__/audit.test.ts` (NEW — 2 cases, console.warn capture) | `vitalia/frontend/src/lib/iam/audit.ts` (new) |
| FE proxy.ts (docs change only) | N/A (covered by existing build) | `vitalia/frontend/src/proxy.ts` (modified) |
| FE routing pages | (covered by Playwright E2E + tsc strict) | NEW pages |
| FE arch tests | `vitalia/frontend/src/__tests__/architecture/test-no-middleware-ts.test.ts` (NEW) + `test-no-dashboard-route-group.test.ts` (NEW) | run via vitest |
| FE E2E Playwright | 8 spec files RED (each scenario) | NEW pages must satisfy each spec |
| FE visual goldens | Playwright `@project=visual` generate iter 1 | not-found outer + inner (light/dark) + network fallback (light/dark) |

---

## § 7 — Research notes (date-aware — accessed 2026-05-26)

| Source | Accessed | Key takeaway |
|---|---|---|
| https://nextjs.org/docs/app/api-reference/file-conventions/proxy | 2026-05-26 | `middleware.ts` DEPRECATED as of Next.js 16. Replaced by `proxy.ts` (src/ or root). Function exported as `proxy` (default or named). Node.js runtime default; `runtime` config option PROHIBITED in proxy files. Negative matcher pattern excludes `_next` + static assets. Codemod: `npx @next/codemod@canary middleware-to-proxy .` |
| https://clerk.com/docs/reference/nextjs/clerk-middleware | 2026-05-26 | `clerkMiddleware()` SDK helper unchanged across Next.js 15 → 16 migration. Still imported from `@clerk/nextjs/server`. The helper name "middleware" is historical (function returned wraps a request handler that Next.js invokes via the `proxy` file convention in v16+). `auth.protect()` redirects to `/sign-in` if no session. `createRouteMatcher` accepts array of glob/regex patterns. |
| Existing predecessor F1-S0 (vitalia-auth-base-functional) | 2026-05-19 | `proxy.ts` already created with canonical pattern. F1-S9 only adds docs anchor; no functional change. |
| Existing predecessor F1-S4 (vitalia-fase1-shell-layout-5050) | 2026-05-23 | `(shell-organism)/layout.tsx` + `page.tsx` exist; F1-S9 modifies them additively (tenant validation + change default). |
| Existing predecessor F1-S7 (vitalia-fase1-ribbon-6-tabs) | 2026-05-25 | `agent-catalog.ts` SSoT extended with `RibbonTabSlug`, `AGENT_RIBBON_ORDER`, `RIBBON_SUBTABS`. F1-S9 adds validators atop. |
| nicolify backend pattern | (existing code, no fetch needed) | `main.py:543` `app.include_router(iam_users.router, prefix="/api/v1/iam/users")` — F1-S9 BE mirrors verbatim. |

**Knowledge cutoff disclosure**: Opus 4.7 cutoff Jan 2026. Next.js 16 `proxy.ts` convention was introduced in v16.0.0 (post-cutoff). Researched live on 2026-05-26 via WebFetch → confirmed canonical pattern + behavior.

---

## § 8 — Open questions for PM

**None.** Spec batch 1 + batch 2 cementadas verbatim Chris 2026-05-25T16:30:00Z. All architectural decisions follow from spec ratification + skill consultation + WebFetch canonical docs. No ambiguity surfaced.

---

## § 9 — Drift / capability YAML deltas (post-merge)

| File | Action | Field change |
|---|---|---|
| `vitalia/docs/product/capabilities/dashboard/welcome-state.yaml` | DELETE | (entire file) |
| `vitalia/docs/product/capabilities/booking/booking-widget-embed.yaml` | MODIFY | `package_path: vitalia/backend/src/modules/vitalia/booking/` (strip `+ vitalia/frontend/src/app/(dashboard)/bookings/`); add `fe_planned_phase2: vitalia-fase2-valeria-agenda` |
| `vitalia/docs/product/capabilities/booking/prepaid-booking-advisory-locks.yaml` | MODIFY (same pattern) | idem |
| `vitalia/docs/product/capabilities/compliance/compliance-hipaa-lite-audit.yaml` | MODIFY | `fe_planned_phase2: vitalia-fase2-lisa-compliance` |
| `vitalia/docs/product/capabilities/compliance/hipaa-lite-defensive-stack.yaml` | KEEP (no FE path in current package_path) | n/a |
| `vitalia/docs/product/capabilities/compliance/whatsapp-template-registry.yaml` | KEEP (BE-only) | n/a |
| `vitalia/docs/product/capabilities/brand_studio/brand-studio-medical-sections.yaml` | MODIFY | `fe_planned_phase2: vitalia-fase2-lisa-marca` |
| `vitalia/docs/product/capabilities/offer_studio/medical-services-offer-preset.yaml` | MODIFY | `fe_planned_phase2: vitalia-fase2-lisa-servicios` |
| `vitalia/docs/product/capabilities/patients/patient-records-medical-history.yaml` | MODIFY | `fe_planned_phase2: vitalia-fase2-valeria-pacientes` |
| `vitalia/docs/product/capabilities/patients/nps-tracking.yaml` | KEEP/INSPECT (BE-only likely — verify in T-5) | n/a |
| `vitalia/docs/product/capabilities/treatments/treatment-followup-workflow.yaml` | MODIFY | `fe_planned_phase2: vitalia-fase2-valeria-pacientes` (sub-vista) |
| `vitalia/docs/product/capabilities/platform/shell-foundation-shadcn-tailwind-v4.yaml` | KEEP (intact) | n/a |
| `vitalia/docs/product/modules/{m}.md` auto-list | post-merge regen | `reconcile_capabilities.py --brand vitalia` |

(T-5 verifies each YAML in detail. If `nps-tracking.yaml` or `compliance-hipaa-lite-audit.yaml` references `(dashboard)/`, also MODIFY them. Default assumption per spec: 6 MODIFY exactly as Chris ratified.)
