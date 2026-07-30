# 07-merge — vitalia-fe-tenant-resolution-no-clerk-org

> `/pm-vitalia` · 2026-06-01 · type bugfix · cap_change_type fix · cap_target iam.luana-core-adoption
> Verdict: APPROVED (auditor-frontend T-1 + gate-verified T-2) · state reviewing → **done**

## Resumen

El FE de vitalia resolvía `tenant_id` (header `X-Tenant-ID`) desde `useAuth().orgId` (Clerk Organization id,
formato `org_`, NO-UUID) en 34 archivos → `UUID()` en el backend → **500 en todo endpoint PHI** contra el stack
real. Oculto por e2e mockeado FE-wide (lección verification-real-not-200 a escala de plataforma). Fix:
`useTenantId()` (lee `public_metadata.tenant_id`, nuestra claim) + reemplazo en 33 archivos + sweep de los 2
usos restantes de Clerk Org (AuditedSection audit PHI + useTenantLocale) + tightening arch test + borrado de la
Clerk org drift. Restaura el invariante [[no-clerk-organizations]].

## § 1 — DONE-bar matrix
| Criterio | Verificación | Status |
|---|---|---|
| 0 `tenantId: orgId` | `grep src/` → 0 reales | ✅ |
| arch test caza orgId | no-clerk-organizations 16/16 tightened | ✅ |
| X-Tenant-ID = UUID nuestro | live: e69a691d-… (no org_) | ✅ |
| PHI no 5xx | live: API_5XX=[] · doctors 500→200 | ✅ |
| Clerk org borrada | count=0, no recreación | ✅ |
| HIPAA audit dispara | AuditedSection unit 9/9 (fires/no-fire) | ✅ |

## § 2 — Playwright/Live run
```bash
cd vitalia/frontend && set -a; source ../.env.dev; set +a
E2E_BASE_URL=http://localhost:3002 npx playwright test \
  e2e/regression/vitalia-fe-tenant-resolution-no-clerk-org/systemic-live-check.spec.ts --project=smoke
# → API_5XX=[]; backend GET /clinics/doctors 200 (era 500); X-Tenant-ID=e69a691d-… UUID
```
Gates: tsc 0 · eslint clean · vitest (T-1 2417/2440 + T-2 39/39; 23 fails = nicolify mirror PRE-EXISTENTE).

## § 3 — Capabilities
- `iam.luana-core-adoption` → change_log type=fix (sin scenarios) + last_modified 2026-06-01.

## § 4 — Modules MD
- `modules/iam.md` auto-list regenera post-merge (R3).

## § 5 — How to verify
```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend
grep -rl "tenantId: orgId" src/ | grep -v "test-no-clerk-organizations" | wc -l   # → 0
npx vitest run src/__tests__/architecture/test-no-clerk-organizations.test.ts     # 16/16
# Live (stack up): systemic-live-check.spec.ts → API_5XX=[] + backend doctors 200
```

## Commits
- `79e27a3d` T-1 (useTenantId + 33 files + arch test) · `9148ff6a` live-verify + Clerk org delete
- `e502e4ae`/`8f22d540` T-2 (AuditedSection + useTenantLocale sweep, 39 tests)

## Follow-ups (NO blocker — tracked)
- `features/onboarding/*` wizard aún LEE org state (useOrganization, READ — degrada a null; NO crea orgs).
  Migrar a tenant-resolution nuestra = follow-up menor prioridad. Doc: observed-bugs/2026-06-01-fe-tenant-id-from-clerk-org-systemic.md.
- Learning candidate (cross-brand): "e2e mockeado FE-wide ocultó tenant-from-Clerk-org → 500 en todo PHI real".
