<!-- voseo-allowed: internal architect documentation -->
---
story_id: vitalia-fase1-routing-shell
brand: vitalia
type: ui-story
phase: fase-1
last_modified: 2026-05-26
architect_iter: 1
---

# F1-S9 · `05-guidelines.md` — patterns required / forbidden / files in scope / must_load_skills

## § 0 — Must-load skills (enforceable — builder MUST load before coding)

| Skill | Trigger | Why |
|---|---|---|
| `frontend-expert` | any FE file touch | FSD-Lite boundaries + Server-First + tests colocation |
| `backend-expert` | T-1 BE wiring | minimal change pattern, response_model gate |
| `playwright-expert` | T-6 E2E suite | POM + fixtures + Clerk auth + freshness gate native run |
| `tessl__shadcn-ui` | not-found.tsx Button usage | Shadcn Button asChild + Link composition pattern |
| `tessl__tailwind` | not-found + network-fallback styling | semantic tokens consumption (text-muted-foreground, opacity-50, min-h-screen) |
| `tessl__nextjs-app-router-modularization` | proxy.ts + routing tree changes | Next.js 16 `params: Promise<>` async + `proxy` file convention + `notFound()` resolution |
| `tessl__react-patterns` | Server vs Client boundary decisions | only [agent]/not-found.tsx + RefreshButton.tsx are Client |
| `tessl__vitest` | T-2 unit tests + T-3/T-4 arch tests | RED-first, mock global.fetch, vi.mock patterns |

### Skills MUST NOT load (out of scope)

- ❌ `copilot-expert` — no copilot surface touched in F1-S9
- ❌ `sales-agent-expert` — idem
- ❌ `brand-expert`, `offer-expert`, `metrics-expert` — no business domain edits
- ❌ `chrome-devtools-verify` — defer to F1-S10 (when content actually visible)

## § 1 — Rules required (verbatim — builder MUST follow)

### § 1.1 — Universal (`.claude/rules/` raíz)

| Rule | Why |
|---|---|
| `tenant-isolation.md` | layout server-side validates tenantId ∈ user.tenants |
| `anti-duplication.md` | reuse core `/me/tenants` (no parallel endpoint) + delete vitalia local `/me` stub |
| `backend-ddd.md` | core engine read-only; BE change is 1-line mount + 1 file delete |
| `frontend-fsd.md` | lib/iam/ is new lib sub-folder; no cross-feature import |
| `spanish-text.md` | all user-facing strings checked against glosario voseo→neutro |
| `tdd-mandatory.md` | RED tests precede GREEN code per layer |
| `story-closure-gate.md` | story=developed → AUTO-HANDOFF /auditor → APPROVED AUTO-HANDOFF /pm-vitalia merge |
| `brand-docs-schema.md` | story archived to `vitalia/docs/archive/2026/stories/{story-id}/` post merge (R2) |
| `auditor-self-fix-policy.md` | whitelist categories only; tests written by dev-team, NOT auditor |
| `git-safety.md` | triple-branch policy; commits in wip/vitalia-fase1-routing-shell worktree |
| `parallel-safety.md` | M14 bucket lock per skill (code bucket for /dev-team) |
| `step-0-worktree.md` | /pm-vitalia + /architect + /dev-team + /auditor enforce step 0 |

### § 1.2 — Vitalia overlay

| Rule | Why |
|---|---|
| `vitalia/.claude/rules/hipaa-lite.md` | audit log row obligatorio para cross-tenant attempt + no-tenants-assigned events; audit payload no contiene PHI |
| `vitalia/.claude/rules/shell-mockup-per-component.md` | N/A esta story (routing puro sin componente visual nuevo, justificado en spec frontmatter `ratified_visual_by_chris: not_applicable`) |

## § 2 — Patterns required (verbatim do)

### § 2.1 — `proxy.ts` (Next.js 16)

```ts
// Pattern: function exported as `proxy` (default OR named)
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isPublicRoute = createRouteMatcher([/* whitelist */]);

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

- File location: `vitalia/frontend/src/proxy.ts` (NOT `app/proxy.ts`, NOT root).
- Runtime: Node.js default — DO NOT set `runtime` config (PROHIBITED in proxy files per Next.js 16 docs).
- Function name: `proxy` (legacy `middleware` deprecated — codemod available `npx @next/codemod@canary middleware-to-proxy .`).
- Reference URL (accessed 2026-05-26): https://nextjs.org/docs/app/api-reference/file-conventions/proxy

### § 2.2 — Server Component routing pages (Next.js 16 `params: Promise<>`)

```tsx
// Pattern: async function + await params + redirect()/notFound() server-side
import { redirect, notFound } from "next/navigation";

interface PageProps {
  params: Promise<{ tenantId: string; agent: string; subtab: string }>;
}

export default async function SubtabPage({ params }: PageProps) {
  const { agent, subtab } = await params;          // ← MUST await params (Next.js 16 breaking change)
  if (!isValidAgent(agent)) notFound();
  if (!isValidSubtab(agent, subtab)) notFound();
  return <div data-testid="subtab-placeholder">…</div>;
}
```

- All routing pages MUST be `async` functions.
- `params` MUST be `Promise<...>` and `await`ed.
- `redirect()` + `notFound()` from `next/navigation` are server actions — call only from Server Components (or via `useRouter()` for redirect in Client Components).

### § 2.3 — Client Component leaf (justified)

```tsx
// Pattern: minimal Client leaf — only when hook is required
"use client";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

export function RefreshButton() {
  const router = useRouter();
  return <Button onClick={() => router.refresh()}>Reintentar</Button>;
}
```

- Mark with `"use client"` at top.
- Justify presence with comment (`// Client: useRouter required`).
- Re-export from server parent — Client leaf is small, single-purpose.

### § 2.4 — Anti-duplication mount pattern (BE)

```python
# vitalia/backend/src/main.py — MIRROR nicolify:543 verbatim
from luana_core_iam.api.routers import auth_router as iam_users

# (... existing app setup ...)

# REUSE core IAM auth router (anti-duplication — delete vitalia local /me stub).
app.include_router(
    iam_users.router,
    prefix="/api/v1/iam/users",
    tags=["IAM - Users"],
)
```

- Prefix `/api/v1/iam/users` matches nicolify pattern verbatim.
- Endpoint becomes `GET /api/v1/iam/users/me/tenants`.
- Delete `vitalia/backend/src/modules/vitalia/iam/api/router.py` + associated test file in same commit.

### § 2.5 — FE consumer (server-side fetch)

```ts
// Pattern: server-safe helper, no React hooks, AbortController timeout
export async function fetchUserTenants(args: { token: string; signal?: AbortSignal }): Promise<UserTenant[]> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/iam/users/me/tenants`, {
      method: "GET",
      headers: { Authorization: `Bearer ${args.token}` },
      signal: args.signal ?? controller.signal,
      cache: "no-store",
    });
    clearTimeout(timeoutId);
    if (!response.ok) throw { code: response.status === 401 ? "unauthorized" : "unknown", status: response.status };
    return (await response.json()) as UserTenant[];
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof Error && err.name === "AbortError") throw { code: "network_failure" };
    throw err;
  }
}
```

- Server-safe (no React hooks). Called from `(shell-organism)/layout.tsx` Server Component.
- Authorization header from Clerk `getToken()` in caller layout.
- `cache: "no-store"` — tenant list can change (admin assigns new tenant).
- 5s AbortController timeout.

### § 2.6 — Spanish neutro (verbatim copy)

| Lugar | Copy verbatim |
|---|---|
| not-found outer título | `"No encontramos esta vista"` |
| not-found outer desc | `"Quizás el enlace está roto o el agente que buscas no existe en esta clínica."` |
| not-found outer CTA | `"Volver al inicio"` |
| not-found inner título | `"No encontramos esa vista dentro de {AGENT_LABEL}"` |
| not-found inner desc | `"Quizás el enlace está roto o esa sub-pestaña no existe."` |
| not-found inner CTA | `"Ir a la vista principal de {AGENT_LABEL}"` |
| network error título | `"Estamos teniendo problemas conectando con el servidor"` |
| network error desc | `"Intenta de nuevo en unos segundos."` |
| network error CTA | `"Reintentar"` |
| sign-in error no-tenants título | `"Tu cuenta no tiene clínicas asignadas"` |
| sign-in error no-tenants desc | `"Contactá al administrador de tu clínica para activar tu acceso."` |
| sign-in error no-tenants CTA | `"Volver a iniciar sesión"` |
| document.title shell | `"Vitalia · {AgentLabel} · {SubtabLabel}"` |
| document.title not-found | `"Vitalia · Página no encontrada"` |
| document.title network error | `"Vitalia · Sin conexión"` |

### § 2.7 — Audit log payload (HIPAA-lite — NO PHI)

```ts
{
  userId: "user_xxx",                       // Clerk user_id — NOT name/email
  action: "cross_tenant_attempt" | "no_tenants_assigned",
  attemptedTenant?: "tenant-uuid",           // tenant id only, NOT name
  timestamp: "2026-05-26T15:30:00.000Z",     // ISO 8601 UTC
}
```

- Audit transport for F1-S9: `console.warn("[audit]", JSON.stringify(payload))` (captured by Next.js runtime logs). BE audit endpoint is F2 scope.

## § 3 — Patterns forbidden (verbatim do NOT)

| ❌ | Why |
|---|---|
| Crear archivo `vitalia/frontend/src/middleware.ts` | Next.js 16 deprecated — must use `proxy.ts` |
| Setear `export const config = { runtime: "..." }` en proxy.ts | PROHIBITED per Next.js 16 docs (throws) |
| Llamar `redirect()` / `notFound()` desde Client Component | Client uses `useRouter().push()`; server actions only from Server Components |
| Hardcodear hex en not-found / network fallback (ej. `#fff`, `text-[#666]`) | Arch test bloquea — use semantic tokens (`text-muted-foreground`, `opacity-50`) |
| Voseo en strings user-facing (`tenés`, `volvé`, `dale`, `laburo`) | Spanish neutro mandatory; arch test `no_voseo` bloquea |
| Cross-brand import (`import ... from "../../../nicolify/..."`) | Hard ban per `.claude/rules/anti-duplication.md` + arch test `no-cross-brand-shell-mirror` |
| Mirror endpoint user-tenants en vitalia backend | REUSE core `auth_router` via mount — zero duplication |
| Mantener vitalia local `/me` stub después del cleanup | Anti-duplication + Chris dictum no legacy |
| Crear `app/(dashboard)/` o `app/(app)/` | Delete pre-existing; arch test `no-dashboard-route-group` bloquea futuro |
| Tocar `core/luana-core-iam/src/` (cualquier file) | Engine boundary — read-only; promotion gate `/pm-luana` required (out of scope F1-S9) |
| Olvidar `await params` en Server Component | Next.js 16 breaking change — typescript runtime error |
| Skip Clerk public matcher for `/api/health` | Used by post-deploy smoke + Docker HEALTHCHECK — must remain public |
| `git add .` / `-A` / `-u` | Forbidden per `.claude/rules/git-safety.md` (parallel sessions) |
| `git pull` / `--force` / `--no-verify` | Forbidden per `.claude/rules/git-safety.md` |
| Inventar `useAuth()` patterns sin verificar Clerk SDK actual | Use canonical `import { auth } from "@clerk/nextjs/server"` |
| Hard delete data layer (DB tables, fixtures) | F1-S9 scope is FE chrome + 1-line BE wiring; BE data layer untouched per spec § 16 |
| Crear redirect 308 desde URLs legacy (`/(dashboard)/offers` → shell) | Spec § 16 Q3 ratified: delete + no redirect (URLs legacy quedan 404 — dev-only) |
| Auto-retry en network error fallback | Spec § Q7 ratified: manual only via "Reintentar" button (router.refresh()) |
| Wirear BE audit endpoint en F1-S9 | F2 scope — F1-S9 usa `console.warn` transport |

## § 4 — Files in scope (allowlist)

### § 4.1 — Allowed to NEW

```
vitalia/frontend/src/lib/iam/api.ts
vitalia/frontend/src/lib/iam/audit.ts
vitalia/frontend/src/lib/iam/types.ts
vitalia/frontend/src/lib/iam/__tests__/api.test.ts
vitalia/frontend/src/lib/iam/__tests__/audit.test.ts
vitalia/frontend/src/app/[tenantId]/(shell-organism)/not-found.tsx
vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/layout.tsx
vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/page.tsx
vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/not-found.tsx
vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx
vitalia/frontend/src/app/[tenantId]/(shell-organism)/_components/NetworkErrorFallback.tsx
vitalia/frontend/src/app/[tenantId]/(shell-organism)/_components/RefreshButton.tsx
vitalia/frontend/src/__tests__/architecture/test-no-middleware-ts.test.ts
vitalia/frontend/src/__tests__/architecture/test-no-dashboard-route-group.test.ts
vitalia/frontend/e2e/pages/RoutingShellPage.ts
vitalia/frontend/e2e/fixtures/routing-shell.fixture.ts
vitalia/frontend/e2e/regression/vitalia-fase1-routing-shell/*.spec.ts  (8 spec files)
vitalia/frontend/e2e/__screenshots__/visual/routing-shell/*.png  (visual goldens iter 1)
vitalia/backend/tests/test_main_iam_routes_mounted.py
vitalia/docs/learnings/2026-05-26-nextjs16-proxy-pattern.md   (lift candidate annotation)
```

### § 4.2 — Allowed to MODIFY

```
vitalia/frontend/src/proxy.ts                                     (docs anchor + verify matcher)
vitalia/frontend/src/lib/agent-catalog.ts                          (append validators)
vitalia/frontend/src/lib/__tests__/agent-catalog.test.ts          (extend ~14 cases)
vitalia/frontend/src/app/[tenantId]/(shell-organism)/layout.tsx   (add tenant validation block)
vitalia/frontend/src/app/[tenantId]/(shell-organism)/page.tsx     (change redirect default)
vitalia/frontend/e2e/visual/visual-smoke.spec.ts                   (drop dashboard assertions)
vitalia/frontend/e2e/visual/stack-stability/dev-stack-baseline.spec.ts  (idem)
vitalia/frontend/e2e/mobile/mobile-smoke.spec.ts                   (idem)
vitalia/frontend/e2e/a11y/a11y-smoke.spec.ts                       (idem)
vitalia/backend/src/main.py                                         (import + include_router; remove vitalia local iam_router mount)
vitalia/docs/product/capabilities/booking/booking-widget-embed.yaml
vitalia/docs/product/capabilities/booking/prepaid-booking-advisory-locks.yaml
vitalia/docs/product/capabilities/compliance/compliance-hipaa-lite-audit.yaml
vitalia/docs/product/capabilities/brand_studio/brand-studio-medical-sections.yaml
vitalia/docs/product/capabilities/offer_studio/medical-services-offer-preset.yaml
vitalia/docs/product/capabilities/patients/patient-records-medical-history.yaml
vitalia/docs/product/capabilities/treatments/treatment-followup-workflow.yaml
vitalia/docs/product/stories/vitalia-fase1-routing-shell/checkpoint.md  (state refined → developing → developed)
```

### § 4.3 — Allowed to DELETE

```
vitalia/frontend/src/app/[tenantId]/(shell-organism)/[...slug]/page.tsx
vitalia/frontend/src/app/[tenantId]/(shell-organism)/[...slug]/      (empty dir)
vitalia/frontend/src/app/(dashboard)/                                  (entire dir, 9+ sub-routes)
vitalia/frontend/src/app/(app)/                                        (entire dir, inbox)
vitalia/frontend/src/features/dashboard/                               (IF zero remaining consumer post (dashboard)/ delete — verify in T-5)
vitalia/frontend/e2e/pages/fidelizacion.page.ts
vitalia/frontend/e2e/specs/regression/fidelizacion-follow-up-doctor-vencido.spec.ts
vitalia/frontend/e2e/specs/regression/fidelizacion-adversarial.spec.ts
vitalia/frontend/e2e/specs/regression/fidelizacion-multi-session-happy.spec.ts
vitalia/frontend/e2e/specs/regression/fidelizacion-absence-no-optin.spec.ts
vitalia/frontend/e2e/specs/smoke/fidelizacion.smoke.spec.ts
vitalia/backend/src/modules/vitalia/iam/api/router.py
vitalia/backend/tests/modules/vitalia/iam/test_router.py                (if exists)
vitalia/docs/product/capabilities/dashboard/welcome-state.yaml
vitalia/docs/product/capabilities/dashboard/                              (empty dir post welcome-state delete)
```

### § 4.4 — NEVER touch (hard ban)

```
core/luana-core-iam/src/**                       — engine read-only; promotion gate required
core/luana-core-platform/src/**                  — idem
nicolify/**, comunify/**, lupulo/**              — cross-brand; F1-S9 brand-local Vitalia only
vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/**  — agentic scope (R23 N/A but defense)
vitalia/frontend/src/components/shared/shell-organism/{Ribbon,SubTabsBar,ValeriaSidebar,TopBarGlobal,ShellOrganismLayout}.tsx  — F1-S4..F1-S8 done, F1-S9 sólo CONSUMES (no edits)
vitalia/frontend/src/stores/shell-store.ts        — F1-S4 done; F1-S9 sólo CONSUMES via existing layout
.claude/skills/**, .claude/rules/**, docs/process/**, docs/architecture/** — meta-paradigm, out of scope
```

## § 5 — TDD discipline (RED-first per layer)

Per `.claude/rules/tdd-mandatory.md`:

1. **T-1 BE**: write `tests/test_main_iam_routes_mounted.py` (RED — 3 cases) BEFORE modifying main.py.
2. **T-2 FE lib**: extend `lib/__tests__/agent-catalog.test.ts` (RED ~14 cases) BEFORE adding validators; write `lib/iam/__tests__/api.test.ts` + `audit.test.ts` (RED 7 cases total) BEFORE creating helpers.
3. **T-3 proxy + auth**: NEW arch test `test-no-middleware-ts.test.ts` (RED — passes trivially today; ratchet locks future violations). Layout server-side validation is covered by Playwright SC-5 + SC-8 RED (no unit test needed for layout — server component test infra costly; E2E covers it well).
4. **T-4 routing pages**: NEW arch test `test-no-dashboard-route-group.test.ts` (RED — initially failing because (dashboard) exists; GREEN after T-5). Page-level behavior covered by Playwright SC-1/SC-2/SC-3 specs (RED first).
5. **T-5 cleanup**: no code TDD — verification is grep-based + arch test green.
6. **T-6 Playwright**: 8 spec files RED first (write spec → fail → confirm — then routing pages from T-4 satisfy). POM + fixtures NEW first to enable specs.

## § 6 — Auditor handoff

`/dev-team` closes state `developed` → AUTO-HANDOFF `/auditor` (per `.claude/rules/story-closure-gate.md`).

Auditor will:
- Verify all 30 validators GREEN.
- Phase D gherkin matrix: 8 SC mapped 1:1 to spec files.
- Self-fix policy: whitelist categories only (ruff/eslint/prettier/typo/import ordering). Substantive fixes → spawn dev-team Caso B.
- Cap 3 audit iterations.
- APPROVED → AUTO-HANDOFF `/pm-vitalia` merge (Fase F): squash + R2 archive + capability reconcile.

## § 7 — Story state machine

```
refined  ── /architect cierra ───────→  ready                    (after this artifact + 04 + 06)
ready    ── /dev-team picks up ──────→  developing
developing ── ticket sequence T-1..T-6 done ──→ developed
developed ── AUTO /auditor ──────────→  reviewing
reviewing ── APPROVED + AUTO /pm-vitalia ─→ done (squash-merge + archive R2)
```
