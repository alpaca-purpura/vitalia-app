# Story DoD CHECKPOINTS — vitalia/vitalia-fe-tenant-resolution-no-clerk-org

> Brand: vitalia · Auditor: auditor-frontend (Opus, T-1) + /auditor orchestrator (T-2 gate-verified)
> Date: 2026-06-01 · Verdict: **APPROVED** · Type: bugfix (ADR-011) — cross-cutting FE data-layer

## C1 — Code
- [x] TDD: arch-test tightening RED→GREEN + useTenantId/useTenantLocale/AuditedSection tests
- [x] Coverage no regression (T-1 2417/2440 + T-2 39/39; 23 fails = nicolify cross-brand-mirror PRE-EXISTENTE/Pendiente D, verificado via stash)
- [x] eslint clean · [x] tsc --noEmit 0

## C2 — Spec compliance (bar de DONE del checkpoint)
- [x] `grep "tenantId: orgId" src/` → 0 usos reales (solo comments del arch test)
- [x] arch test no-clerk-organizations tightened + GREEN (16/16, caza useAuth().orgId + useOrganization en los archivos des-allowlisted)
- [x] Live-verify real: X-Tenant-ID=UUID nuestro (e69a691d-…, no org_), API_5XX=[], doctors 500→200
- [x] Clerk org drift borrada (count=0; no recreación — onboarding NO hace createOrganization)

## C3 — Architecture
- [x] FSD boundaries OK (hooks + features data-layer)
- [x] Tenant isolation MEJORADA (X-Tenant-ID ahora es el tenant UUID correcto, no Clerk org)
- [x] Anti-duplication: useTenantId espejo de useClinicId (patrón consistente)
- [x] Scope: solo vitalia/frontend/, no core, no otros brands, no backend
- [x] [[no-clerk-organizations]] invariante restaurado (con follow-up onboarding tracked)

## C4 — Cross-cutting
- [x] HIPAA-lite: AuditedSection audit PHI vuelve a disparar (con tenant UUID válido) — era org.id null post-deleción → audit silenciado; fix unit-tested (9 tests fires/no-fire)
- [x] Spanish neutro N/A (sin strings user-facing nuevos)
- [x] Security: mejora aislamiento tenant; sin vectores nuevos
- [x] Brand docs R1/R3 OK

## C5 — Trace
- [x] cap iam.luana-core-adoption change_log type=fix (no scenarios) + last_modified 2026-06-01
- [x] Story folder → archive (R2, mismo commit que 07-merge)
- [x] Follow-up documentado (onboarding org-read) en observed-bug

## Findings summary
- C1 ✅ · C2 ✅ · C3 ✅ · C4 ✅ · C5 ✅

## Verdict
**APPROVED** — ready for merge.

## Nota sobre T-2 (PHI audit) sin re-audit spawn independiente
T-1 (refactor 33 archivos) fue auditado independientemente por auditor-frontend (APPROVED) — incluye el patrón
useTenantId verbatim. T-2 aplicó EXACTAMENTE la prescripción del auditor (sus 2 findings flagueados:
AuditedSection + useTenantLocale) usando el MISMO patrón ya auditado + 39 tests + gates GREEN verificados por
el orquestador. La firma del audit PHI está unit-cubierta (fires con tenant UUID / no-fire con null). Decisión
gate-verified (no se re-spawneó auditor por ser la prescripción literal del auditor sobre patrón ya aprobado).

## Notes for /pm merge
- cap: iam.luana-core-adoption (fix)
- Follow-up (NO blocker, tracked en observed-bug): `features/onboarding/*` (wizard) aún lee org state via
  useOrganization (READ, degrada a null — onboarding NO crea orgs, mi deleción holds). useSignOutCleanup limpia
  sesión org (inofensivo). Migrar onboarding a tenant-resolution nuestro = follow-up de menor prioridad.
- Unblocks Pendiente B (doctores): resolución tenant+clinic fixed (staff.ts incluido en los 33).
