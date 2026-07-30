# T-3 Result — FE hook useCurrentUser (rol desde /me)

**Story:** vitalia-iam-slice2-phi-real-auth  
**Ticket:** T-3 — FE hook: useCurrentUser rol desde GET /api/v1/iam/users/me  
**Commit:** af3c6fda  
**Branch:** wip/vitalia  
**Date:** 2026-05-29  

---

## Diff resumen

### Archivos modificados

| Archivo | Tipo | Cambio |
|---|---|---|
| `vitalia/frontend/src/hooks/useCurrentUser.ts` | MODIFIED | Fuente del rol: Clerk publicMetadata → React Query /me |
| `vitalia/frontend/src/hooks/__tests__/useCurrentUser.test.tsx` | NEW | Vitest 6 tests (TDD RED→GREEN) |
| `vitalia/docs/product/stories/vitalia-iam-slice2-phi-real-auth/T-3-impl-log.md` | NEW | Iteration log + OQ-2 confirmación |

### Archivos NO tocados (forbidden list respetado)

- `core/luana-core-*/src/` — solo leído auth_router.py para conocer shape /me
- `vitalia/frontend/src/components/ui/` — sin cambios
- `vitalia/frontend/src/app/**/layout.tsx` — sin cambios
- `vitalia/frontend/src/hooks/useClinicId.ts` — sin cambios
- `nicolify/`, `comunify/`, `lupulo/` — sin cambios

---

## Gate output literal

### tsc --noEmit
```
(sin output — 0 errores)
```

### eslint src/hooks/ --cache
```
(sin output — 0 errores)
```

### vitest run (T-3 target)
```
 ✓ useCurrentUser > devuelve rol desde GET /api/v1/iam/users/me (no desde Clerk publicMetadata)
 ✓ useCurrentUser > retorna isLoaded false mientras la query de /me está pendiente
 ✓ useCurrentUser > nunca devuelve un rol cuando GET /me falla (no hay data leak)
 ✓ useCurrentUser > hasPhiAccess es true cuando el rol es doctor (rol PHI)
 ✓ useCurrentUser > hasPhiAccess es false cuando el rol es marketing (no PHI)
 ✓ useCurrentUser > retorna shape CurrentUser completo (id, firstName, lastName, email, role, hasPhiAccess, isLoaded)

 Test Files  1 passed (1)
      Tests  6 passed (6)
   Duration  851ms
```

### vitest run (suite completa — regresión)
```
 Test Files  211 passed (211)
      Tests  2302 passed (2302)
   Duration  14.60s
```

---

## OQ-2 confirmado

Engine `GET /api/v1/iam/users/me` shape (auth_router.py → User domain):
- `id: UUID` — disponible
- `full_name: str | None` — disponible (no se descompone firstName/lastName)
- `email: str` — disponible
- `role: str` — **clave**: seteado por `user.role = user_tenant.role` vía X-Tenant-ID en `get_current_user`
- `tenant_id: UUID | None` — disponible

Conclusión: el shape engine basta. `firstName`/`lastName` siguen de Clerk `useUser()` (no están en /me; `full_name` no se descompone server-side). No se necesita endpoint brand-local. AD-3 cumplido.

---

## cat-5-fe-role-source (04-validators.yaml) — checks cumplidos

- [x] `useCurrentUser` lee role desde `GET /api/v1/iam/users/me` (React Query), no de Clerk publicMetadata.role
- [x] shape `CurrentUser` intacto (consumers `RequireRole`/`usePiiRoleGate` sin cambios)
- [x] NO toca `components/ui/` ni layout
- [x] estados loading/error/success cubiertos (6 tests)

---

## Skills consulted

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `frontend-expert` | Cargada per assignment must_load_skills. SOP data fetching hooks. | Seguir patrón `useAuth().orgId` como tenantId (igual que `useConversations`, `useTenants`) |
| `vitalia-design-system` | Cargada per assignment (canal único FE). | No aplica a hook puro sin UI. Confirmado no tocar shell components. |
| `tessl__react-patterns` | Baseline siempre. Error boundaries, loading/error/empty states. | Hook expone `isLoaded: false` durante pending; `role: null` en error. Shape intacto previene breaking changes consumers. |
| `tessl__vitest` | Tests nuevos. | `renderHook` + `QueryClientProvider` wrapper. `waitFor` para async resolution. `vi.mock` para Clerk + fetchClient. |
| `.claude/rules/frontend-fsd.md` | Boundary matrix. | Hook en `src/hooks/` (global layer) — correcto. No cross-feature imports. |
| `.claude/rules/spanish-text.md` | Spanish neutro. | No hay strings user-facing en este hook. N/A para comentarios técnicos. |
| `.claude/rules/tdd-mandatory.md` | RED-first obligatorio. | Tests escritos PRIMERO (RED 5/6), luego implementación (GREEN 6/6). |

---

## Commit SHA

`af3c6fda`

---

## Notas para auditor-frontend

1. `useCurrentUser.ts` ahora depende de React Query + Clerk auth (ambos `"use client"` correcto).
2. La función retorna `CurrentUser` síncrono pero internamente usa `useQuery` async — el shape `isLoaded: false` es el señal de carga para consumers.
3. `usePiiRoleGate.ts` NO necesitó cambios — consumo de `{ role, hasPhiAccess, isLoaded }` es idéntico.
4. `ME_QUERY_KEY` exportado para facilitar cache invalidation futura si es necesario.
5. El `retry: 2` en el hook se justifica: el endpoint /me es crítico (sin él el usuario no puede acceder a PHI). Un fallo temporal de red no debe bloquear inmediatamente.
6. Chrome DevTools verify: este ticket es hook puro sin UI visual nueva. La verificación funcional del rol real se hace en el gate god-matrix (supervisado por Chris — T-1/T-2 gate, no T-3).
