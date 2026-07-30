<!-- voseo-allowed: doc interno de proceso -->
# Story DoD CHECKPOINTS — vitalia/vitalia-fase2-lisa-doctores · bug7 rounds 4-6

> Brand: vitalia
> Auditor: /auditor (opus) + auditor-backend (opus) + auditor-frontend (opus)
> Date: 2026-06-15
> Scope: deltas bug7 rounds 4-6 (día-de-semana TZ · borrado recurrente con scope + migración 044 · no-crear-pasado · occurrences = N ciclos). La story delta-v3 base fue auditada/verificada antes.
> Verdict: **APPROVED**

## C1 — Code
- [x] Tests RED → GREEN (round-4 RED capturado "lunes→col6"; round-6 semantics; TDD en T-FIX-bug7-round{4,5,6}-result.md)
- [x] Coverage no regresión (clinics 457 · vitest 525 · +tests nuevos BE/FE)
- [x] Lint + format clean (ruff · eslint 0)
- [x] Type-check clean (tsc 0)

## C2 — Spec compliance
- [x] Cada regla/scenario bug7 tiene test GREEN (06-audit/gherkin-matrix.md — sin MISSING)
- [x] Playwright E2E real-backend GREEN (bug7-r5 8/8 · bug7-r4 22 · r3 16 · ground truth DB + geometría)
- [x] Specs FE importan de fixtures/base.ts / authed-runtime (anti-burbuja) — NO @playwright/test directo
- [x] Spec RECONCILIADO (Fase R) — RN-D3F-2 invertida a N-ciclos · § "Reconcile bug7 (rounds 4-6)" en 01-spec
- [x] chris_verify.signoff = SATISFIED (Chris, rounds 1-6) — scope ratificado NO revertido

## C3 — Architecture
- [x] Arch fitness 0 violations introducidas (full arch 353 pass; única falla = pre-existente CRM pgcrypto treatment_plans.notes, fuera de scope)
- [x] DDD boundaries (router no toca _repo; count_future_confirmed delegado; projection SSoT)
- [x] Tenant isolation — dual filter tenant_id+clinic_id en los 4 métodos repo nuevos + exclude/truncate
- [x] Migración 044 idempotente (ADD COLUMN IF NOT EXISTS · down_revision 043 · DROP IF EXISTS · raw SQL)
- [x] Anti-dup — calendarDates SSoT único (MonthCalendar deduped, jscpd clean); sin mirror cross-brand
- [x] Scope discipline — solo vitalia/ (cero core/, cero otra brand)

## C4 — Cross-cutting
- [x] Spanish neutro (diálogo "Solo este turno"/"Este y los siguientes"/"Cancelar"; 422 messages; sin voseo)
- [x] PII/audit — audit SYNC pre-response (occurrence_excluded/truncated); availability no-PHI; confirmados nunca borrados
- [x] Master-data/TZ — root fix calendarDates componentes locales (nunca toISOString para Y-M-D)
- [x] Migraciones idempotentes (044 · sin sa.Enum/op.add_column)
- [x] Security — sin SQL injection / leak; RBAC require_brand_owner_access en mutations; 422 paths
- [x] Brand docs schema R1/R3 — sin .md sueltos en vitalia/docs raíz; sin edición manual de auto-gen

## C5 — Trace
- [x] checkpoint state → done lo pone /pm-vitalia en merge
- [ ] BACKLOG regen post-merge (R33 hook · /pm-vitalia)
- [ ] Capability lisa.doctores ledger update Fase F.3 (/pm-vitalia: cap_change_type=fix/extend para los deltas bug7 + scenarios nuevos delete-scope/past/cycles)
- [ ] modules/clinics.md auto-list refresh (/pm-vitalia)
- [x] Learnings sugeridos (ver Notes) — promotable candidates
- [ ] Archive story a archive/2026/stories/ (R2 · /pm-vitalia en 07-merge, MISMO commit)

## Findings summary
- C1: 4/4 ✅ · C2: 5/5 ✅ · C3: 6/6 ✅ · C4: 6/6 ✅ · C5: code-side ✅ (merge-side pendiente /pm-vitalia)
- Sub-reviews: T-bug7-be-review.md APPROVED · T-bug7-fe-review.md APPROVED (PASS)
- Findings bloqueantes: **0**. CHANGES_REQUESTED: 0. ESCALATED: 0.

### WARN no-bloqueantes (→ CIL, no bloquean merge)
1. BE: 2 service-tests de scope mockean el repo (predicado SQL confirmed-preservation idéntico al path `series` cubierto por integración) → CIL L3 follow-up (test repo-real).
2. FE: ramas fallback vacuas en availability-calendar-past-cell.test.tsx (guard-strength) → CIL L3.
3. FE: mención stale `orgId` en docstring de staff.ts (código correcto, solo doc) → quick-win.
4. Pre-existente NO de esta story: arch test pgcrypto `treatment_plans.notes TEXT` (módulo CRM, deuda PHI de otra story) → flag a /pm-vitalia / CIL L4.

## Live verification (Critical Rule #37)
- chris_verify.signoff = **SATISFIED** (Chris ejerció live en dev-app rounds 1-6).
- Verificación técnica live: real-backend e2e (cero mocks del surface · POST 201 / PATCH 200 / DELETE · efecto en DB + BE logs) + screenshots de render real Chromium (día-de-semana claro+oscuro · diálogo scope · semana pasada grisada · Mar+Jue×3 semanas completas), vistos por el orquestador.
- ⚠️ La herramienta **Chrome DevTools MCP estuvo locked** por la sesión paralela de Chris (HB-73, que Chris trabajaba en simultáneo). La obligación de "ejercer acción real + observar efecto, no GET 200, no e2e mockeado" se cumplió vía el e2e real-backend + screenshots de render real. Stack dev UP (BE:8002, FE:3002).

## Notes for /pm-vitalia merge
- cap_change_type: los deltas bug7 son **fix** (día-de-semana, occurrences-cycles) + **extend** (delete-scope, past-disable = comportamiento nuevo) sobre `clinics/lisa.doctores`. Agregar scenarios: delete-occurrence, delete-this-and-future, no-create-past, occurrences-cycles.
- Learnings sugeridos (promotable candidate cross-brand): (a) `toISOString()` para Y-M-D de calendario = bug TZ bajo offset negativo → SSoT date-local (aplica a cualquier calendario multi-brand); (b) test ground-truth no debe espejar el cálculo de producción (el escape de round-3).
- Open_item NO bloqueante: bloques multi-día creados pre-round6 no auto-corrigen (editar/recrear).

## Verdict
**APPROVED** — story (deltas bug7 rounds 4-6) ready for merge by /pm-vitalia.
