# T-1 result — vitalia-bugfix-agenda-actor-headers-422

**Brand:** vitalia · **Carril:** R (fix-and-own) · **Type:** bugfix lite
**Builder:** builder-frontend · **Date:** 2026-06-15

---

## Bug (confirmado por PM)

`GET /api/v1/scheduling/agenda/grid` (y los otros 4 endpoints de `agenda_router.py`)
exigen 3 headers REQUERIDOS sin default — `X-Tenant-ID` + `X-Clinic-ID` + `X-User-ID` —
y leen `X-User-Role` (default `""` → RBAC 403 si está vacío). El FE de agenda mandaba
SOLO `X-Tenant-ID` (`vitaliaFetch(url, { token, tenantId })`) → **422 repetido + grilla
vacía** en `/{tenant}/mateo/agenda`.

BE confirmado correcto (contrato HIPAA-lite dual-filter + audit). Bug 100% FE.

### Header requirements verificados (los 5 endpoints de agenda_router.py)

| Endpoint | X-Tenant-ID | X-Clinic-ID | X-User-ID | X-User-Role |
|---|---|---|---|---|
| GET `/agenda/grid` (l.195-198) | req | req | req | leído (RBAC) |
| GET `/agenda/aggregates` (l.325-328) | req | req | req | leído (RBAC) |
| GET `/appointments/{id}` (l.395-398) | req | req | req | leído (RBAC) |
| POST `/appointments` (l.461-464) | req | req | req | leído (RBAC) |
| PATCH `/appointments/{id}` (l.567-570) | req | req | req | leído (RBAC) |

`ALLOWED_PHI_ROLES = {valeria_assistant, doctor, nurse, admin_clinic}` (l.101). El rol
DEBE ser el **per-tenant real** (no un literal `"owner"` — agenda 403ea con owner).

---

## Opción elegida: (b) hook compartido de actor-headers — NO (a) auto-inyección

**Por qué NO (a):** `vitaliaFetch` (`src/lib/fetch-client.ts`, cliente legacy de agenda) es
**una función async pura, NO un hook** (decisión de diseño documentada en su cabecera).
X-Clinic-ID viene de `useUser()` (Clerk), X-User-ID del cache de `GET /iam/users/me`, y
X-User-Role del tenant store — TODOS requieren React hooks que no pueden vivir dentro de
una función pura sin convertirla en hook (rompería su contrato + a TODOS sus consumers).
Auto-inyectar X-User-ID/Role además los mandaría a consumers que no los necesitan.
`vitaliaFetch` ni siquiera acepta `clinicId` (a diferencia de `fetchClient`).

**Por qué SÍ (b):** El patrón YA shippeado y verde para esto es lisa/staff:
`useClinicId()` (X-Clinic-ID, hook compartido) + `useStaffActorHeaders()` (X-User-ID DB-UUID
+ X-User-Role per-tenant). Pero `useStaffActorHeaders` vive en `features/lisa/api/staff.ts`
→ cross-import desde `features/mateo` está **prohibido por FSD-Lite**. Solución: **LIFT** la
lógica a un hook compartido `src/hooks/useActorHeaders.ts` (no duplicar, no cross-import).
`features/lisa` también pasa a consumir el hook compartido (mantiene `useStaffActorHeaders`
como wrapper delgado para no romper sus consumers internos).

### De dónde salen los valores

**Client:**
- `X-Tenant-ID` → `vitaliaFetch` lo inyecta hoy desde el `tenantId` que pasa cada hook.
- `X-Clinic-ID` → `useClinicId()` (`@/hooks/useClinicId`, shared) → `user.publicMetadata.clinicId`.
- `X-User-ID` → `useActorHeaders()` → cache de `GET /api/v1/iam/users/me` (DB UUID `meData.id`,
  mismo `ME_QUERY_KEY` → react-query dedupe, sin call extra). NUNCA el Clerk id (`user_…` → 422 UUID).
- `X-User-Role` → `useActorHeaders()` → rol **per-tenant** del tenant store
  (`availableTenants.find(t=>t.id===tenantId)?.role ?? activeTenant?.role`). NO el rol global de `/me`.

**SSR (`agenda-server.ts`):**
- `X-Clinic-ID` → `session.sessionClaims["clinic_id"]` (igual que `lisa/staff/page.tsx`),
  resuelto en `page.tsx` Server Component y pasado a `getInitialAgendaState`.
- `X-User-ID` + `X-User-Role` → fetch server-side a `GET /api/v1/iam/users/me` con
  `Authorization` + `X-Tenant-ID` (el handler resuelve `id` DB-UUID + `role` per-tenant via
  X-Tenant-ID, `dependencies.py:340-341`). Helper `resolveActorContext()` nuevo en agenda-server,
  graceful (devuelve `{}` si falla → cae a `emptyGrid`, sin romper el render).

---

## Archivos tocados

**Nuevos:**
- `vitalia/frontend/src/hooks/useActorHeaders.ts` — hook compartido LIFTeado (X-User-ID DB-UUID + X-User-Role per-tenant). Header `// cap: compliance.hipaa-lite-defensive-stack`.
- `vitalia/frontend/src/hooks/__tests__/useActorHeaders.test.tsx` — 3 tests (UUID de /me, rol per-tenant del store, gate empty antes de /me).
- `vitalia/frontend/e2e/regression/vitalia-bugfix-agenda-actor-headers-422/agenda-actor-headers-live.spec.ts` — regression live real-backend (sin mock del grid).

**Modificados:**
- `vitalia/frontend/src/features/lisa/api/staff.ts` — `useStaffActorHeaders` → wrapper delgado sobre `useActorHeaders` (lift, sin cambio de comportamiento; quita la lógica duplicada + imports `useTenantStore`/`ME_QUERY_KEY`).
- `vitalia/frontend/src/features/mateo/api/agenda.ts` — helper `useAgendaActorHeaders()` (clinic+actor) + los 5 hooks (grid/aggregates/detail/create/patch) mandan los 3 headers; las 3 queries PHI gatean `enabled` en `ready` (X-User-ID resuelto).
- `vitalia/frontend/src/features/mateo/api/payments.ts` — `useChargeMutation` merge actor headers + idempotency key.
- `vitalia/frontend/src/features/mateo/api/fiscal.ts` — `useFiscalEmitMutation` actor headers.
- `vitalia/frontend/src/features/mateo/api/notify.ts` — `useSendNotificationMutation` (live-wired en AccionesAvanzadas) actor headers.
- `vitalia/frontend/src/features/mateo/api/agenda-server.ts` — SSR: `resolveActorHeaders()` (X-User-ID/Role via /me server-side) + `resolveClinicId()` (X-Clinic-ID via Clerk backend `clerkClient().users.getUser().publicMetadata.clinicId` — el JWT dev NO trae clinic claim, era el agujero del SSR).
- `vitalia/frontend/src/app/[tenantId]/(shell-organism)/mateo/agenda/page.tsx` — delega la resolución del actor context al SSR helper (ya no depende de sessionClaims, que estaban vacíos).
- `vitalia/frontend/src/features/mateo/api/agenda.test.ts` — mocks de useClinicId/useActorHeaders + 2 regression tests (manda los 3 headers · disabled hasta X-User-ID).
- `vitalia/frontend/src/features/mateo/components/agenda/ValeriaAgendaView.test.tsx` — mock de useActorHeaders (la query transitiva pulleaba useUser).

---

## Verificación

### Repro confirmado (live, BE real)
```
curl ... /scheduling/agenda/grid?view=semana -H 'X-Tenant-ID: e69a691d-...'
→ HTTP 422 · X-Clinic-ID "Field required", X-User-ID "Field required"
```

### Playwright real-backend guard — PASSED (4/4) · NO mocks del grid
`e2e/regression/vitalia-bugfix-agenda-actor-headers-422/agenda-actor-headers-live.spec.ts`
contra `localhost:3002` (Clerk testing token, user `dr.demo@vitalialat.com`, tenant
`e69a691d-...`). El poll client-side de React Query capturó la request real:
```
AGENDA_GRID_CALLS=[{ status: 403,
  tenantHeader: "e69a691d-...", clinicHeader: "f035be5b-...",
  userIdHeader: "527050c3-...", userRoleHeader: "owner", ... }]
```
Los 3 headers actor VIAJAN. **422 ELIMINADO** (assert `had422 === false` verde). Esto
ejerce la acción real contra el BE real (live-verify #37 satisfecho para el contrato FE).

### Gates FE (native host) — TODOS VERDE
- `npx tsc --noEmit` → **0 errores**.
- `npx eslint src/ --cache` → **0 errores, 0 warnings** (baselines no crecieron).
- `npx vitest run src/features/mateo src/hooks src/features/lisa` → **881 passed**.
- `npx vitest run src/__tests__/architecture/` → **187 passed** (FSD no-cross-imports verde — el lift evitó la violación).

### ⚠️ Upstream BE deficiencies (fuera del carril FE — el 422 las enmascaraba)
Con los 3 headers ahora presentes, el grid endpoint expone DOS bugs BE pre-existentes
que el 422 ocultaba (el request nunca llegaba al servicio/repo):

1. **403 RBAC** — `dr.demo` tiene `user_tenants.role = owner` (global `doctor`), pero
   `agenda_router.py::ALLOWED_PHI_ROLES = {valeria_assistant, doctor, nurse, admin_clinic}`
   NO incluye `owner`. Un dueño de clínica no puede ver su propia agenda. Decisión de
   policy RBAC del BE (¿agregar `owner`?). El cliente manda el rol per-tenant correcto.
2. **500 repo crash** — SSR (rol `doctor`) pasa RBAC y crashea en
   `agenda_grid_repository_impl.py:287`: `AttributeError: 'TextClause' object has no
   attribute 'selectable'` (raw-SQL mal usado en SQLAlchemy 2.0). Crash de data-layer.

Ambos son deuda BE (`/scheduling`), no FE. La grilla no rendea data REAL hasta que el BE
los resuelva. El bug REPORTADO (422 por headers FE faltantes) está **resuelto y verificado
live**. Recomendación PM: abrir bugfix BE para (1) política RBAC `owner` en agenda y
(2) el `TextClause.selectable` del repo.

### Nota client/SSR rol
SSR resuelve rol via `/me` (per-tenant), client via tenant-store (per-tenant, fallback
`owner`). Ambos mandan el rol real per-tenant del usuario. El gap es de POLICY BE (qué
roles permite agenda), no de plumbing FE.

