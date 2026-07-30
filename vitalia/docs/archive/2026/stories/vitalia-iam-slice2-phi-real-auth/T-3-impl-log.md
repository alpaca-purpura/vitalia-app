# T-3 Impl Log — FE hook useCurrentUser (rol desde /me)

**Story:** vitalia-iam-slice2-phi-real-auth  
**Ticket:** T-3 — FE hook: useCurrentUser rol desde GET /api/v1/iam/users/me  
**Builder:** builder-frontend (Sonnet)  
**Date:** 2026-05-29  
**cap_target:** iam.iam-scaffold-slice-1

---

## § Primera entrada — RED (TDD obligatorio)

**Test escrito ANTES de la implementación:**
`vitalia/frontend/src/hooks/__tests__/useCurrentUser.test.tsx`

Tests RED iniciales (5 fallidos de 6):
- Test 1: `devuelve rol desde GET /api/v1/iam/users/me (no desde Clerk publicMetadata)`
  — FAIL: `expected 'patient' to be 'doctor'` (Clerk publicMetadata tenía "patient"; /me hubiera devuelto "doctor")
- Test 3: `retorna role null y hasPhiAccess false cuando GET /me falla`
  — FAIL: `expected 'patient' to be null`
- Test 4: `hasPhiAccess es true cuando el rol es doctor`
  — FAIL: `expected 'patient' to be 'doctor'`
- Test 5: `hasPhiAccess es false cuando el rol es marketing`
  — FAIL: `expected 'patient' to be 'marketing'`
- Test 6: shape CurrentUser completo
  — FAIL: `expected 'patient' to be 'doctor'`

Esto confirmó que la implementación anterior leía `publicMetadata.role` de Clerk (role "patient" en el mock)
en vez de la respuesta de `/me` (role "doctor" en el mock).

---

## § OQ-2 — Confirmación shape engine GET /api/v1/iam/users/me

**Archivo leído (solo lectura):** `core/luana-core-iam/src/luana_core_iam/api/routers/auth_router.py`

```python
@router.get("/me")
async def get_current_user_profile(user: Annotated[User, Depends(get_user_from_token)]) -> User:
    return user
```

La dependencia `get_user_from_token` (en `dependencies.py`) resuelve:
- `user.id` (UUID)
- `user.full_name` (str | None)  
- `user.email` (EmailStr)
- `user.role` (str — seteado por `user.role = user_tenant.role` cuando X-Tenant-ID presente)
- `user.tenant_id` (UUID | None)
- `user.is_active` (bool)

**Decisión OQ-2:** El shape del engine `/me` ES SUFICIENTE para el hook. El `role` viene resuelto desde `user_tenants.role` cuando se pasa X-Tenant-ID (que el engine `get_current_user` hace automáticamente). No se necesita endpoint brand-local. Se consume `/api/v1/iam/users/me` directo (AD-3 cumplido).

**Campos mapeados:**
- `user.role` → `CurrentUser.role` (como `VitaliaRole`)
- `user.email` → `CurrentUser.email` (fallback al campo de Clerk)
- `firstName`, `lastName` → desde `useUser()` Clerk (no están en `/me`; `full_name` no se descompone server-side)
- `hasPhiAccess` → calculado FE-side con `PHI_ROLES` set (cero lógica nueva)

---

## § Plan técnico

### Design system first (D1)
- No hay primitivas Shadcn involucradas — es un hook puro sin UI.
- Dependencias: `@tanstack/react-query` + `@clerk/nextjs` + `@/lib/api/fetchClient` (existentes).

### Mockup scope notes
- Este ticket es un hook sin UI → no aplica mockup adherence (D2/D3).
- No se toca `components/ui/`, `layout.tsx`, ni `useClinicId.ts` (scope discipline respetado).

### Batería de tests (test-design-doctrine.md — naturaleza FE hook data)
- Hook test: Vitest — success + loading + error + hasPhiAccess true/false + shape intacto (6 tests)
- E2E/manual: god-matrix JWT real (supervisado por Chris en gate verificación PHI — no es scope T-3)

### Integración CONN
- `useCurrentUser` ya consumido por `RequireRole` + `usePiiRoleGate` — anti-isla cumplido (consumidores previos)
- Shape `CurrentUser` intacto → consumers sin cambios
- El hook se registra en React Query con key `["iam", "me", orgId]` — cache correcta por tenant

---

## § Iteraciones

### Iter 1 — Implementación GREEN

**Cambios en `useCurrentUser.ts`:**
1. Reemplazada dependencia de `useUser` como fuente de rol → ahora `useQuery` a `/api/v1/iam/users/me`
2. Fuente del rol: `meData.role` (DB via engine, 1 fuente de verdad) — NO `user.publicMetadata.role`
3. Shape `CurrentUser` intacto — `id/firstName/lastName` siguen de Clerk user object (no en /me)
4. `hasPhiAccess` calculado FE-side (PHI_ROLES set: doctor/nurse/admin_clinic)
5. Estados: `isLoaded: false` mientras query pending; `isLoaded: true` tras success o error
6. Query key: `["iam", "me", orgId]` — re-fetch automático en cambio de tenant
7. `staleTime: 5min` — rol no cambia frecuentemente en sesión normal
8. ANTI-ISLA: `useCurrentUser` ya wired en `RequireRole` + `usePiiRoleGate` (no isla)

**Fix test iter 1:** mock faltaba `orgId` en `useAuth` → query no se disparaba (enabled: false)
**Fix test iter 2:** error test usaba `waitFor(isLoaded)` pero `retry: 2` en hook retrasaba → cambiado a assert directo en `role/hasPhiAccess`

### Iter 2 — TypeScript fix

Error: `Cannot find namespace 'JSX'` en test (retorno de función wrapper)
Fix: agregar `import React from "react"` + cambiar tipo retorno a `React.ReactElement`

---

## § Gates pre-commit

| Gate | Resultado |
|---|---|
| `npx vitest run src/hooks/__tests__/useCurrentUser.test.tsx` | 6/6 PASS |
| `npx tsc --noEmit` | 0 errores |
| `npx eslint src/hooks/ --cache` | 0 errores |
| Regresión suite completa `npx vitest run` | 2302/2302 PASS |

---

## § CONN anti-isla verificación

- **Consumed:** `useCurrentUser` importado en `usePiiRoleGate.ts` + (implícitamente) `RequireRole` component
- **On-the-map:** cap `iam.iam-scaffold-slice-1` (`cap_change_type: extend`)
- **Navigable:** FE llamada automática al cargar shell-organism autenticado
- **Notarized:** wired en barrel exports (no new file — modificación del hook existente)

Cero isla: el hook estaba ya consumido antes de este cambio; el cambio es interno (fuente del rol).

---

## § Mockup scope notes

No aplica (hook puro sin UI). La story es `adr_004_compliance: n/a-with-rationale` — no es sub-tab UI.

---

## § Notas para auditor-frontend

- `useCurrentUser` mantiene shape `CurrentUser` intacto — `usePiiRoleGate.ts` sin cambios
- `useClinicId.ts` sin tocar (clinic_id sigue por header X-Clinic-ID — fuera de scope T-3)
- `core/luana-core-iam/src/` sin editar (solo leído para conocer shape `/me`)
- Boundary FSD respetado: hook en `src/hooks/` (global hooks layer), no cross-feature imports
- Query key incluye `orgId` para cache isolation por tenant
- No se recrean primitivas Shadcn (no hay UI)
- Spanish neutro: no hay strings user-facing en este hook (solo tipos e interfaces)
