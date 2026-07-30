# Story DoD CHECKPOINTS — vitalia/vitalia-fase2-adrian-embudo

> Brand: vitalia
> Auditor: /auditor (Auditor Responsable v5) + auditor-frontend/backend surfaces
> Date: 2026-06-11
> Verdict: **APPROVED** — ready for merge by /pm-vitalia (pending `chris_verify.signoff` demo gate, DoD #37)

## C1 — Code
- [x] Tests RED → GREEN (sync-fix: stale retract test corregido + regression test nuevo, ambos GREEN)
- [x] Coverage no regression (vitest adrian+crm-shared 351/351; +1 test neto)
- [x] Lint + format clean (eslint exit 0 adrian + crm-shared)
- [x] Type-check clean (tsc --noEmit exit 0, whole project)

## C2 — Spec compliance
- [x] Cada Gherkin scenario con test GREEN (06-audit/gherkin-matrix.md — BE 28 + agentic 10 + live 9 + sync regression)
- [x] Playwright live-verify (board-live 9/9, resumen-live, recuperar-live contra dev-app real)
- [x] Agentic SC-1b override-feeds-agent 10/10 (sin grafo/prompt nuevo — wire only)
- [x] Visual goldens / mockup ratificado embudo-v3.html (ratified_visual_by_chris: true)
- [ ] **Demo Chris (`demo_required: true`) → `chris_verify.signoff`** — PENDIENTE (gate humano, /pm-vitalia REFUSE merge sin él)

## C3 — Architecture
- [x] Arch fitness FE 0 violations (187/187 — boundary inbox→adrian RESUELTO)
- [x] DDD boundaries (crm EXTEND; override-context vía evento a sales_agent, no cross-module import directo)
- [x] Tenant isolation (NF-1 test_cross_tenant_lead_block 2/2; lead non-PHI single-tenant filter)
- [x] Anti-duplication (sync-fix consume key factory centralizada `_keys.ts`; no mirror)
- [x] Cross-namespace key contract (`['crm','conversation',id]` = key renderizada de crm-shared, alineada)
- [x] 05-guidelines scope respetado (sync-fix FE-only, sin scope creep)

## C4 — Cross-cutting
- [x] Spanish neutro (sin strings user-facing nuevos; comentarios internos OK)
- [x] PII: lead non_PHI (phi_classification ratificado); cero PHI en cache keys/payload
- [x] Currency/master-data: N/A en el delta sync-fix
- [x] Migrations: N/A (sync-fix sin DDL; migración 038 ya aplicada + idempotente)
- [x] Security: cache invalidation no expone datos cross-tenant (keys namespaced, fetch sigue tenant-scoped)
- [x] Brand docs schema R1/R3 (docs en sub-dirs; cap editada en source, no auto-gen)
- [~] **Pre-existing out-of-scope:** treatment_plans.notes TEXT→BYTEA (fidelizacion PHI, HB-70 HIGH) — NO embudo, flag a Chris

## C5 — Trace
- [ ] checkpoint.md final state=done (lo setea /pm-vitalia al merge)
- [ ] BACKLOG regen post-merge (auto)
- [x] Capability ready: cap_change_type=fix → change_log entry + planned→live con scenarios + e2e_test al merge F.3
- [x] Story folder listo para archive a vitalia/docs/archive/2026/stories/ (R2, mismo commit que 07-merge)
- [x] Learnings: out-of-scope findings → HB-69 (test-harness) + HB-70 (pgcrypto PHI) en harness-backlog

## Findings summary
- C1: 4/4 ✅
- C2: 4/5 ✅ (1 pendiente = demo Chris, gate humano)
- C3: 6/6 ✅
- C4: 6/6 ✅ (+1 pre-existing out-of-scope flag)
- C5: 3/6 (resto lo cierra /pm-vitalia al merge)

## Verdict
**APPROVED** — story técnicamente lista para merge por /pm-vitalia.
Único gate restante = **demo de Chris** (`chris_verify.signoff`, DoD #37 — negocio, separado del técnico).

## Notes for /pm-vitalia merge
- Capability a actualizar: `vitalia/docs/product/capabilities/crm/adrian-embudo.yaml` → `planned`→`live` + change_log entry type=fix (sync-fix) + scenarios SC-1..SC-11 verbatim del spec + `e2e_test` anchors (board-live/resumen-live/recuperar-live) + `dev_app_verified`.
- Módulo MD: `vitalia/docs/product/modules/crm.md` auto-list refresh.
- Learnings: ninguno cardinal nuevo del embudo (sync-fix es mecánico). Out-of-scope → HB-69/70.
- Promotion candidate (cross-brand): cross-namespace RQ invalidation entre features = patrón potencialmente útil en nicolify/comunify (CRM similar) → `candidate` (mencionar a /pm-luana, no bloqueante).
- **REFUSE merge** hasta `chris_verify.signoff.result ∈ {SATISFIED, SATISFIED_WITH_FOLLOWUPS(sev≤medium)}`.
