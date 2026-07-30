# Observed bug (SISTÉMICO · alta severidad) — el FE resuelve tenant_id desde Clerk Organizations

- **Fecha:** 2026-06-01
- **Detectado por:** live-verify del keystone doctores-500 (al quitar el fallback `useOrganization` de `useClinicId`, el doctores no disparó request → tracking del por qué destapó esto).
- **Severidad:** **ALTA · sistémica.** Contradice el invariante [[no-clerk-organizations]] (ratificado Chris 2026-05-20 y 2026-06-01). Rompe TODOS los endpoints PHI contra el backend real.
- **Por qué nunca se vio:** todos los harness e2e **mockean el backend** → falso verde generalizado (lección lisa-marca / verification-real-not-200, a escala de plataforma).

## El bug

El FE de vitalia resuelve el `tenant_id` (header `X-Tenant-ID`) desde **`useAuth().orgId`** — el ID de la **Clerk Organization**. Patrón `tenantId: orgId` presente en **34 archivos** (`crm-shared`, `fidelizacion`, `marketing`, `inbox`, `lisa/staff`, + `hooks/useCurrentUser.ts`).

**Problemas:**
1. **Viola [[no-clerk-organizations]]:** no usamos Clerk Organizations; los tenants/clinics son NUESTROS (luana-core-iam), no se sincronizan con Clerk. El FE NO debe leer `orgId`.
2. **El org id NO es UUID:** Clerk org ids tienen formato `org_3DzUI3lLjwX83Kth0j5enWrjIDY`. El backend espera `tenant_id` UUID → `UUID("org_3D...")` → `ValueError: badly formed hexadecimal UUID string` → **500** en cada endpoint PHI. (Este era el verdadero culpable del doctores-500, NO el clinic_id — clinic_id sí era UUID válido.)
3. **Drift de datos:** existe una Clerk Organization `org_3DzUI3lLjwX83Kth0j5enWrjIDY` ("Sanaré MX — Vitalia Test Tenant") y dr.demo es miembro. Esa org **no debería existir** per el invariante.

## Evidencia

```
# Clerk instance tiene 1 org (drift):
GET /v1/organizations → org_3DzUI3lLjwX83Kth0j5enWrjIDY "Sanaré MX — Vitalia Test Tenant"
# dr.demo es miembro:
GET /v1/users/{dr.demo}/organization_memberships → 1 (esa org)
# dr.demo public_metadata (LA fuente correcta, ya presente):
{ "role":"owner", "clinicId":"f035be5b-0ac4-5210-8fc3-395650ca2b83", "tenant_id":"e69a691d-070e-5caf-a053-6e74642ec100" }
# 34 archivos FE:
grep -rln "tenantId: orgId" vitalia/frontend/src/ → 34
# backend:
"GET /api/v1/vitalia/clinics/doctors..." 500 · ValueError badly formed hexadecimal UUID string · doctors_router.py:175 tenant_id=UUID(tenant_id)
```

## La fuente correcta YA existe

`dr.demo.public_metadata.tenant_id = e69a691d-...` (UUID válido, = tenant Sanaré en DB) y `clinicId = f035be5b-...` (= `vitalia_clinic_branches.id` real). El FE debe resolver el tenant_id de **esa claim** (o del store de tenant / `GET /iam/users/me`), igual que `useClinicId` ahora resuelve clinicId de la claim. NUNCA de `useAuth().orgId`.

## Fix (cross-cutting — NO scope de una story de feature)

1. Crear `useTenantId()` (espejo de `useClinicId`): lee `user.publicMetadata.tenant_id` (o tenant store / GET /me). NUNCA `orgId`.
2. Reemplazar `tenantId: orgId` → `tenantId: useTenantId()` en los 34 archivos (+ ajustar el guard `if (!orgId) throw`).
3. Tightening arch test `test-no-clerk-organizations.test.ts`: cazar `useAuth().orgId` / destructuring `{ orgId }` de useAuth + dependencia de org membership (hoy NO lo caza — blind spot).
4. **Decisión Chris:** borrar la Clerk Organization `org_3DzUI3...` (drift) — outward-facing, requiere ratificación.
5. Re-live-verify (REAL, no mock) los features afectados (crm/fidelizacion/marketing/inbox/lisa) — varios podrían estar rotos contra el backend real hoy.
6. Considerar guard BE permanente: `X-Tenant-ID` no-UUID → 422 (ya hecho para doctors_router en commit 81a32173; extender al middleware de tenant para TODO endpoint).

## Relación con stories

- **vitalia-fase2-lisa-doctores:** su keystone (staff.ts `tenantId: orgId`) es UNA instancia de este bug. No puede llegar a `done` con live-verify real hasta resolver la resolución de tenant (mínimo staff.ts, idealmente el fix sistémico).
- **Cross-cutting → `/pm-luana` o story dedicada de remediación.** No se debe enterrar el refactor de 34 archivos + el borrado de la Clerk org dentro de la story de doctores.

## Learning candidate

`promotable: candidate` — "Verificación real ≠ HTTP 200, a escala: e2e mockeado FE-wide ocultó que TODO el FE resolvía tenant desde Clerk Orgs (invariante prohibido) → 500 en todo PHI contra backend real. La live-verify de UNA story destapó deuda de plataforma." Aplica cross-brand (toda brand con e2e mockeado puede tener el mismo agujero). Ver `vitalia/docs/learnings/cobertura-tests-vs-realidad-2026-05-29.md`.

---

## Update 2026-06-01 — remediación T-1+T-2 mergeada (story vitalia-fe-tenant-resolution-no-clerk-org)

- **RESUELTO el vector PHI-500:** useTenantId() + 33 archivos + AuditedSection + useTenantLocale. Live-verified
  (X-Tenant-ID=UUID nuestro, API_5XX=[], doctors 500→200). Clerk org `org_3DzUI3...` borrada (count=0).
- **Confirmado:** onboarding NO hace `createOrganization` → la deleción de la org NO se revierte.
- **Follow-up remanente (NO blocker, menor prioridad):** `features/onboarding/*` (wizard, vía
  `use-wizard-onboarding-state.ts`) aún LEE `useOrganization()` (READ, degrada a null — onboarding es flujo
  one-time, no PHI runtime). `useSignOutCleanup.ts` limpia sesión org (inofensivo). Estos quedan en el allowlist
  shrink-only del arch test. Migrarlos a tenant-resolution nuestra cierra el invariante al 100%. Owner sugerido:
  story de onboarding o /pm-luana si se vuelve cross-brand.
