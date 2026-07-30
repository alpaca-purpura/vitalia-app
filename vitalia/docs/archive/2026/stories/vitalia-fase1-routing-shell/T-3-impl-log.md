# T-3 Implementation Log — proxy polish + tenant validation layout + network fallback

**Story:** vitalia-fase1-routing-shell (F1-S9)
**Ticket:** T-3 — FE proxy.ts polish + tenant validation server-side en layout + edge sin tenants + network fallback
**Brand:** vitalia
**Branch:** wip/vitalia
**Commit:** 0fdac50e
**Date:** 2026-05-25
**Status:** DONE — 1514/1514 tests GREEN, tsc clean, ESLint clean

---

## § Skills Consulted

| Skill | Invocada | Decisión tomada |
|---|---|---|
| `frontend-expert` | Sí — rule loading inicial | Confirma boundary matrix FSD-Lite, Server-First default para layout.tsx, _components/ collocated (no components/shared/). runtime-quality-checklist.md revisado pre-commit. |
| `tessl__react-patterns` | Sí — baseline siempre | Error boundary via NetworkErrorFallback (SC-7). Loading/error/empty states en layout. Accessible markup: `role="img" aria-label` en ⚠️, `role="alert"` en no-tenants panel. Stable keys N/A (sin listas dinámicas en estos componentes). |
| `tessl__shadcn-ui` | Sí — RefreshButton usa Button | `Button` variant="default" de `@/components/ui/button` (existente). No recrear. |
| `tessl__tailwind` | Sí — NetworkErrorFallback + sign-in | `cn()` N/A en estos componentes (clases fijas). Tokens semánticos: `text-foreground`, `text-muted-foreground`, `min-h-screen`. NO inline `style={{}}`. |
| `tessl__nextjs-app-router-modularization` | Sí — layout + NetworkErrorFallback | layout.tsx puro Server Component (auth() + redirect() requieren server). NetworkErrorFallback = Server Component síncrono. RefreshButton = único Client leaf (justified: useRouter()). No "use client" en layout. |
| `tessl__vitest` | Sí — NetworkErrorFallback.test.tsx | vi.mock("next/navigation") para useRouter. render + screen + fireEvent. 10 assertions GREEN. |

---

## § Scope implementado

### 1. MODIFY `src/proxy.ts`

**Antes:** 6 rutas públicas. Faltaban `/marketing(.*)` y `/__clerk/(.*)`.

**Después:** 8 rutas públicas.

Cambios:
- `// F1-S9 routing-shell: matcher polish + /marketing(.*) explicit` — comment anchor verbatim spec § 9.2
- `/marketing(.*)` — rutas de landing pública por tenant
- `/__clerk/(.*)` — rutas internas Clerk (OAuth callbacks, account portal)

### 2. MODIFY `src/app/[tenantId]/(shell-organism)/layout.tsx`

Reescrito de minimal F1-S4 wrapper a Server Component con tenant validation completa:

| Scenario | Condición | Acción |
|---|---|---|
| SC-01 | Sin sesión Clerk | `redirect("/sign-in")` |
| SC-7 | fetchUserTenants lanza excepción | `<NetworkErrorFallback />` |
| SC-8 | tenants.length === 0 | `logNoTenantsAssigned()` + `redirect("/sign-out?next=/sign-in?error=no_tenants_assigned")` |
| SC-4/5 | tenantId ∉ user.tenants | `logCrossTenantAttempt()` + `redirect(/{tenants[0].id}/valeria/agenda)` |
| Happy path | tenantId válido | `<ShellOrganismLayout tenantId={tenantId}>` |

HIPAA-lite: audit log `console.warn("[audit]", { action, userId, ..., timestamp })` — SOLO userId opaque (Clerk ID, no PII), no PHI.

### 3. NEW `_components/NetworkErrorFallback.tsx` (Server Component)

- Síncrono (no async data — solo JSX composition)
- `data-testid="network-error-fallback"` presente
- Microcopy verbatim spec § 10:
  - Título: "Estamos teniendo problemas conectando con el servidor"
  - Descripción: "Intenta de nuevo en unos segundos."
  - Ícono: ⚠️ con `role="img" aria-label="Advertencia"`
- Incluye `<RefreshButton />` como Client leaf

### 4. NEW `_components/RefreshButton.tsx` (Client Component)

- `"use client"` justificado: `useRouter().refresh()`
- `data-testid="network-error-retry"` presente
- Shadcn `Button` variant="default"
- Texto: "Reintentar"

### 5. EXTEND `app/(auth)/sign-in/[[...rest]]/page.tsx`

- `searchParams: Promise<Record<string, string | string[] | undefined>>` (Next.js 16 pattern)
- Detecta `?error=no_tenants_assigned` → panel amber con `role="alert"` + `data-testid="no-tenants-error"`
- Microcopy verbatim spec § 10:
  - "Tu cuenta no tiene clínicas asignadas"
  - "Contacta al administrador de tu clínica para activar tu acceso."
- Sin voseo. Tildes correctas.

### 6. NEW arch test `src/__tests__/architecture/test-no-middleware-ts.test.ts`

TDD RED-first. Dos assertions:
1. `middleware.ts MUST NOT exist anywhere in src/` — escanea recursivamente
2. `proxy.ts MUST exist in src/` — verifica path canónico

### 7. NEW `_components/NetworkErrorFallback.test.tsx`

10 assertions RED → GREEN:
- NetworkErrorFallback: mensaje, descripción, data-testid, botón Reintentar, ícono aria
- RefreshButton: texto, data-testid, router.refresh() al click

---

## § Quality Gates

| Gate | Resultado | Detalle |
|---|---|---|
| `tsc --noEmit` | ✅ PASS | 0 errores. strict mode. |
| `eslint src/` | ✅ PASS | 0 errores, 0 warnings nuevos en archivos T-3. |
| `vitest run` | ✅ PASS | 1514/1514 tests GREEN (incluye 10 nuevos + 2 arch). |
| Coverage | ✅ PASS | 82.56% statements (threshold 20%). |
| Arch test middleware | ✅ PASS | proxy.ts existe, middleware.ts ausente. |

---

## § Anti-patterns evitados

- ❌ `"use client"` en layout.tsx — puro Server Component
- ❌ `useEffect` para data fetching — N/A (Server Component)
- ❌ URL hardcodeada `http://localhost:8002` — fetchUserTenants usa env var (T-2)
- ❌ PHI en audit log — solo userId opaque + attemptedTenant + timestamp
- ❌ Voseo — "Contacta", "Intenta", "Reintentar" (tuteo neutro)
- ❌ middleware.ts — solo proxy.ts (arch test enforcement)
- ❌ X-Tenant-ID manual — fetchClient lo inyecta automáticamente (T-2)

---

## § HIPAA-lite compliance

- Transport F1-S9: `console.warn("[audit]", {...})` — Fase 2 scope reemplaza con POST `/api/v1/audit/iam-events`
- Payload audit: `action + userId + attemptedTenant? + timestamp` — CERO PHI
- userId = Clerk opaque ID (no es PII en aislamiento per HIPAA-lite overlay)
- `tenant_fetch_failure` audit: `error: String(err)` — solo tipo de error, no datos de paciente

---

## § Decisiones de diseño

**NetworkErrorFallback ubicación:** `app/[tenantId]/(shell-organism)/_components/` (route-collocated), no `components/shared/shell-organism/`. 03-arch-fe.md § 2.1 es SSoT — toma precedencia sobre la mención en el prompt de `/dev-team`.

**RefreshButton como hoja Client:** única alternativa a `useRouter().refresh()` es un `<form action={...}>` Server Action para reload, pero `router.refresh()` es más preciso (re-fetches Server Components sin full page reload). Justificación documentada en JSDoc.

**sign-in searchParams async:** Next.js 16 App Router requiere `searchParams: Promise<...>` y `await searchParams` en Server Components. Implementado correctamente.
