---
brand: vitalia
date: 2026-06-01
slug: fe-tenant-from-clerk-org-systemic
promotable: candidate
applies_to_other_brands_potentially: [nicolify, comunify, lupulo]
target_core_package: n/a (es disciplina de verificación + invariante de identidad)
---

# E2E mockeado FE-wide oculta deuda de plataforma: tenant_id desde Clerk Org → 500 en todo PHI

**Qué aprendimos:** El live-verify REAL de UNA story (doctores) destapó que **TODO el FE de vitalia (35 archivos)**
resolvía `tenant_id` desde `useAuth().orgId` (Clerk Organization id, formato `org_…`, NO-UUID) → `UUID()` en el
backend → **500 en cada endpoint PHI** contra el stack real. Nadie lo vio nunca porque **todos los harness e2e
mockean el backend** → falso verde a escala de plataforma. Además había una Clerk Organization "drift" creada
(contradiciendo el invariante [[no-clerk-organizations]]).

**Origen:** sesión 2026-06-01 — Pendiente A (dual-mount) → su live-verify destapó el doctores-500 → el tracking
del 500 destapó el patrón sistémico. Fix: story `vitalia-fe-tenant-resolution-no-clerk-org` (useTenantId() + 33
archivos + AuditedSection/useTenantLocale + arch-test endurecido + borrado de la Clerk org). Live-verified.

**Why:** Dos lecciones convergen:
1. **Verificación real ≠ 200** ([[verification-real-not-200]] / [[dod-live-verify]]) a escala: si TODA la suite
   mockea el backend del surface bajo prueba, el verde no dice NADA sobre producción. La live-verify contra el
   stack real (Chrome MCP / Playwright autenticado + leer logs del backend) es la única que destapa esto.
2. **Invariante de identidad** [[no-clerk-organizations]]: Clerk = solo usuarios; tenants/clinics son NUESTROS
   (luana-core-iam). Un arch test que NO caza `useAuth().orgId` (solo `useOrganization` imports) tiene blind spot.

**How to apply:**
- Toda brand con e2e mockeado puede tener el mismo agujero: auditar `grep "tenantId: orgId" / useAuth().orgId /
  useOrganization` y correr live-verify REAL de ≥1 endpoint PHI por feature contra el backend real.
- Un arch test de invariante debe cazar TODAS las superficies del anti-patrón (no solo el import obvio): para
  no-clerk-orgs, cazar `useOrganization*`, `OrganizationSwitcher/CreateOrganization`, Y `useAuth().orgId` /
  destructuring `{ orgId }`.
- Cuando una story scopeada destapa deuda de plataforma, NO enterrar el fix en la story: abrir remediación
  dedicada (lo hicimos: story E) y reportar a Chris/pm-luana.

> Doc técnico completo: `vitalia/docs/observed-bugs/2026-06-01-fe-tenant-id-from-clerk-org-systemic.md`
