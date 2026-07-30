---
ticket: T-1
story: vitalia-fe-tenant-resolution-no-clerk-org
type: bugfix
agent: builder-frontend
state: developed
commit: 3ded799f
files_touched: 93
tests_native: 2417/2440 PASS (23 pre-existing cross-brand-mirror failures — not introduced by T-1)
arch_tests: 16/16 PASS (test-no-clerk-organizations.test.ts)
tsc: 0 errors
eslint: 0 errors
vitalia_bar_of_done: partial (tsc+eslint+vitest GREEN; live-verify pending dev-app spin-up)
---

# T-1 Result — FE Tenant Resolution Refactor

## Summary

Refactor sistémico: reemplaza `useAuth().orgId` (Clerk org id, formato `org_xxx`, NO-UUID) → `useTenantId()` que lee `user.publicMetadata.tenant_id` (UUID válido de luana-core-iam).

**Root cause**: el FE enviaba `X-Tenant-ID: org_3DzUI3...` → backend `UUID()` parse → 500 en TODOS los endpoints PHI. Enmascarado por e2e mockeado.

**Fix**: `useTenantId()` nuevo hook + refactor de 34 archivos + tightening del arch test.

## Skills Consulted

| Skill | Por qué | Decisión tomada |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary, naming, testing patterns | Hook en `src/hooks/`, test en `src/hooks/__tests__/`, patrón espejo de `useClinicId.ts` |
| `tessl__react-patterns` | Client hook patterns, no useEffect | Hook `"use client"` + `useUser()` directo, sin efectos secundarios |
| `tessl__vitest` | Test setup para hooks Clerk | `vi.mock("@clerk/nextjs", () => ({ useUser: () => mockUseUser() }))` — mock solo lo que el hook usa |
| `.claude/rules/tdd-mandatory.md` | RED→GREEN → arch test primero | Arch test tightening primero (RED 35 violaciones), luego hook + refactor (GREEN) |
| `.claude/rules/tenant-isolation.md` | Invariante X-Tenant-ID | Confirmado: `useTenantId()` devuelve UUID de luana-core-iam, no Clerk org id |

## Arch Test Tightening (RED→GREEN)

**Antes**: `test-no-clerk-organizations.test.ts` tenía 14 tests pero NO catchaba `orgId` en código de producción — blind spot.

**Nuevo describe block**: `"Architecture: T-1 — production source files must NOT use orgId from useAuth()"` escanea todos los archivos `.ts`/`.tsx` bajo `src/` (excluyendo `__tests__/`) buscando `orgId` en líneas no-comentario.

- **RED**: 35 violaciones detectadas (35 archivos con `orgId`)
- **GREEN post-refactor**: 0 violaciones

Total arch test: 16/16 PASS.

## Archivos Tocados (producción)

**NEW** (2 archivos):
- `src/hooks/useTenantId.ts` — hook espejo de `useClinicId.ts`
- `src/hooks/__tests__/useTenantId.test.tsx` — 8 tests

**MODIFIED — hooks** (2 archivos):
- `src/hooks/useCurrentUser.ts` — migrado: `{ getToken, orgId }` → `{ getToken }` + `useTenantId()`
- `src/__tests__/architecture/test-no-clerk-organizations.test.ts` — tightened (nuevo describe block)

**MODIFIED — crm-shared** (3 archivos):
- `src/features/crm-shared/api/use-leads.ts`
- `src/features/crm-shared/api/use-conversations.ts`
- `src/features/crm-shared/api/use-conversation-detail.ts`

**MODIFIED — fidelizacion** (9 archivos):
- `src/features/fidelizacion/api/use-activity-stream.ts`
- `src/features/fidelizacion/api/use-availability-slots.ts`
- `src/features/fidelizacion/api/use-fidelizacion-summary.ts`
- `src/features/fidelizacion/api/use-log-manual-call.ts`
- `src/features/fidelizacion/api/use-mark-external.ts`
- `src/features/fidelizacion/api/use-mark-no-continue.ts`
- `src/features/fidelizacion/api/use-nps-responses.ts`
- `src/features/fidelizacion/api/use-pause-patient.ts`
- `src/features/fidelizacion/api/use-re-engagement-patterns.ts`
- `src/features/fidelizacion/api/use-send-proactive-template.ts`

**MODIFIED — inbox** (8 archivos):
- `src/features/inbox/api/use-activity-stream.ts`
- `src/features/inbox/api/use-attach-media.ts`
- `src/features/inbox/api/use-pause-adrian.ts`
- `src/features/inbox/api/use-proactive-outbound.ts`
- `src/features/inbox/api/use-retract-message.ts`
- `src/features/inbox/api/use-send-message.ts`
- `src/features/inbox/api/use-set-mode.ts`
- `src/features/inbox/api/use-tools-state.ts`
- `src/features/inbox/api/use-transcribe-audio.ts`

**MODIFIED — marketing** (10 archivos):
- `src/features/marketing/api/use-approve-recommendation.ts`
- `src/features/marketing/api/use-attribution-matrix.ts`
- `src/features/marketing/api/use-bowtie-summary.ts`
- `src/features/marketing/api/use-channel-detail.ts`
- `src/features/marketing/api/use-lucas-recommendations.ts`
- `src/features/marketing/api/use-referrals.ts`
- `src/features/marketing/api/use-reject-recommendation.ts`
- `src/features/marketing/api/use-stage-detail.ts`
- `src/features/marketing/api/use-sync-channel.ts`
- `src/features/marketing/api/use-undo-recommendation.ts`

**MODIFIED — lisa** (3 archivos):
- `src/features/lisa/api/staff.ts`
- `src/features/lisa/components/staff/workspace/StaffWorkspaceShell.tsx`

**MODIFIED — test files** (55+ archivos):
- Todos los test files que mock `@clerk/nextjs` con `useAuth` ahora también tienen:
  `vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }))`
- PHI safety header assertions actualizadas a `"mock-tenant-id"` (valor del mock)

## Bar de DONE — Verificación

- [x] `grep -rl "tenantId: orgId" src/` → **0 archivos** (solo el arch test en string literal)
- [x] `npx tsc --noEmit` → **0 errores**
- [x] `npx eslint src/ --cache` → **0 errores**
- [x] `npx vitest run` → **2417/2440 PASS** (23 pre-existing cross-brand-mirror failures no introducidas por T-1; verificado con git stash)
- [x] arch test `test-no-clerk-organizations.test.ts` → **16/16 PASS** (incluye 2 nuevos tests)
- [ ] Live-verify real (dev-app.vitalialat.com) → PENDING (requiere `make dev-app-vitalia` + stack dev corriendo)

## Live-Verify Status

La verificación live contra el stack real requiere que el dev-app esté corriendo (`make dev-app-vitalia`). Esta sesión corrió en modo headless sin acceso al stack docker. El fix es correcto a nivel de código — el `X-Tenant-ID` header ahora enviará `e69a691d-070e-5caf-a053-6e74642ec100` (UUID de publicMetadata) en vez de `org_3DzUI3...` (Clerk org id).

**Evidencia de correctitud**:
1. `useTenantId()` lee `user.publicMetadata.tenant_id` (igual que `useClinicId()` lee `clinicId`)
2. `dr.demo.publicMetadata.tenant_id = "e69a691d-070e-5caf-a053-6e74642ec100"` (UUID válido)
3. Backend doctors_router espera UUID → ahora recibe UUID → no más 500

**Escalar para live-verify**: Chris debe ejecutar `make dev-app-vitalia` y navegar a `/{tenant}/lisa/staff` autenticado como `dr.demo@vitalialat.com` → verificar que el GET /clinics/doctors responde 200 (o empty list) en vez de 500.

## Pre-existing Failures (no introducidas por T-1)

`test-no-cross-brand-shell-mirror.test.ts` — 23 tests FAILing. Verificado con `git stash` que fallaban ANTES del refactor. Estos tests buscan nombres de componentes vitalia en otros brands (`nicolify`, `comunify`, `lupulo`) y fallan porque esas brands están en estado bootstrap (no tienen los directorios del shell-organism). No es regresión de T-1.

## Commit SHA

`3ded799f` — `git push origin wip/vitalia` ejecutado exitosamente.

## Pattern del fix (para referencia futura)

```typescript
// ANTES (BUG): orgId es formato org_xxx, NO UUID
const { getToken, orgId, isLoaded, isSignedIn } = useAuth();
// tenantId: orgId → X-Tenant-ID: org_3DzUI3... → backend UUID() parse → 500

// DESPUÉS (FIX): tenant_id desde publicMetadata, UUID real
import { useTenantId } from "@/hooks/useTenantId";
const { getToken, isLoaded, isSignedIn } = useAuth();
const tenantId = useTenantId(); // user.publicMetadata.tenant_id (UUID)
// tenantId → X-Tenant-ID: e69a691d-... → backend UUID() parse → OK
```
