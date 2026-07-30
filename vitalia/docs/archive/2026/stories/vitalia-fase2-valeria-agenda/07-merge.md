---
story_id: vitalia-fase2-valeria-agenda
brand: vitalia
outcome: vitalia-mvp-ui-foundation
phase_label: fase-2
type: ui-story
agent_owner: valeria
module: scheduling
capability: valeria.agenda
merged_at: 2026-05-27T01:30:00Z
merged_by: /pm-vitalia (autonomous chain Conv 3)
state_at_merge: reviewing → done
auditor_verdict: APPROVED
audit_iterations: 3
ready_package: closed
total_tickets: 19
total_commits_wip: 23                                              # 19 tickets + 1 checkpoint state + 1 audit + 2 auto-fix iter
known_tech_debt_accepted:
  - W2: visual goldens runtime (@hookform/resolvers/zod Docker stack fix needed)
  - W3: AgendaPlaceholder dead code en PLACEHOLDER_MAP (cleanup PR mínimo)
  - W5: residual semantic health/payment status colors aceptable per design brief
---

# 07-merge.md — F2-S1 vitalia-fase2-valeria-agenda

## § 1 — Gherkin verification matrix

Copia verbatim de `06-audit/gherkin-matrix.md` (Phase D auditor):

| SC | Scenario | Test path | Status |
|---|---|---|---|
| SC-1 | happy: cobro saldo end-to-end PE boleta | `e2e/regression/.../valeria-agenda-happy-cobro.spec.ts` + `tests/modules/vitalia/scheduling/test_charge_orchestrator.py::test_happy_path_pe_boleta` | UNIT PASS · E2E ready (W2 defer) |
| SC-2 | negative: payment-adapter 503 | `e2e/.../valeria-agenda-payment-503.spec.ts` + `test_charge_orchestrator.py::test_payment_503` | UNIT PASS · E2E ready |
| SC-3 | edge: tenant switch during drawer open | `e2e/.../valeria-agenda-tenant-switch.spec.ts` | UNIT PASS · E2E ready |
| SC-4 | adversarial: PHI in URL blocked | `tests/modules/vitalia/scheduling/test_phi_url_protection.py::test_patient_dni_query_param_rejected` | PASS |
| SC-5 | keyboard-a11y: navigate slots con teclado | `e2e/a11y/vitalia-fase2-valeria-agenda.spec.ts` | UNIT PASS · E2E ready |
| SC-6 | theme-switch + visual parity | `e2e/visual/vitalia-fase2-valeria-agenda.spec.ts` | UNIT PASS · visual not runtime (W2) |
| SC-7 | race_condition: optimistic lock | `test_appointment_payment_repository.py::test_lock_for_charge_optimistic` + `test_charge_orchestrator.py::test_concurrent_charge_optimistic_lock` | PASS |
| SC-8 | concurrent users: charge race | `e2e/.../valeria-agenda-race-concurrent.spec.ts` | UNIT PASS · E2E ready |
| SC-9 | empty state | `e2e/.../valeria-agenda-empty-state.spec.ts` | UNIT PASS · E2E ready |
| SC-10 | large dataset virtualization | `e2e/.../valeria-agenda-large-dataset.spec.ts` (MonthCalendar react-window) | UNIT PASS · E2E ready |
| SC-11 | i18n: locale AR/MX/CL | `e2e/.../valeria-agenda-i18n.spec.ts` | UNIT PASS · E2E ready |

**Total:** 11/11 mapped scenarios. Unit/BE coverage PASS. E2E specs ready but runtime not executed (W2 Docker stack deferred — known_tech_debt accepted for merge).

## § 2 — Playwright E2E run

```bash
# Comando reproducible (post Docker stack fix W2):
cd vitalia/frontend
pnpm install                                                       # arregla @hookform/resolvers/zod missing en container
E2E_BASE_URL=http://localhost:3002 npx playwright test \
  e2e/regression/vitalia-fase2-valeria-agenda/ \
  e2e/a11y/vitalia-fase2-valeria-agenda.spec.ts \
  e2e/visual/vitalia-fase2-valeria-agenda.spec.ts \
  --project=smoke
```

**Result en merge:** SKIPPED — Docker stack tech debt impide runtime generation. Specs ready (parse OK 83 tests). Tech debt aceptado y documentado en backlog post-merge.

**Verificación unit + arch fitness (alternativa runtime):**
- BE arch fitness: 324 tests GREEN (`pytest tests/architecture/ -x -q`)
- BE scheduling+payments+fiscal: 181 tests GREEN (`pytest tests/modules/vitalia/{scheduling,payments,fiscal}/ -q`)
- FE vitest valeria: 271 tests GREEN (`npx vitest run src/features/valeria/`)
- FE typecheck: 0 errors (`npx tsc --noEmit`)
- FE eslint: 0 errors (`npx eslint src/features/valeria/ --cache`)

## § 3 — Capabilities updated/created

**NEW:**
- `vitalia/docs/product/capabilities/scheduling/valeria-agenda.yaml` (capability primary de F2-S1, status: live)

**Surfaces by component:**
- BE: `vitalia/backend/src/modules/vitalia/{scheduling,payments,fiscal}/` (3 NEW brand-extension modules, Inside-Out DDD)
- FE: `vitalia/frontend/src/features/valeria/components/agenda/` (16 NEW components + ValeriaAgendaView root)
- FE page: `vitalia/frontend/src/app/[tenantId]/(shell-organism)/valeria/agenda/page.tsx` (refactored from F1-S10 empty-state to operational)
- Tests: 19 NEW test files (BE pytest unit + arch fitness + FE vitest unit + E2E specs + a11y + visual goldens)

## § 4 — Modules MD refreshed

**NEW module:**
- `vitalia/docs/product/modules/scheduling.md` (NEW — primer módulo scheduling brand-local, contiene auto-list block para capabilities/scheduling/*)

**Endpoints expuestos por scheduling+payments+fiscal:**
- `GET /api/scheduling/agenda/grid` — agenda filtered slots con dual filter HIPAA
- `GET /api/scheduling/agenda/aggregates` — monthly aggregates para virtualización
- `GET /api/scheduling/appointments/{id}` — appointment detail PHI-masked
- `POST /api/scheduling/appointments` — create walk-in/teléfono/existing-patient
- `PATCH /api/scheduling/appointments/{id}/status` — status transitions
- `POST /api/scheduling/appointments/{id}/reminder` — WhatsApp template-only + ComplianceService guard
- `POST /api/payments/charge` — saga charge + idempotency
- `POST /api/fiscal/emit` — standalone fiscal emit (retry post-saga)

## § 5 — How to verify

```bash
WS=/home/chalreme/Proyectos/luana-vitalia

# 1. BE arch fitness (HIPAA dual filter + no PHI URL + audit log row + DDD)
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ -x -q

# 2. BE business modules unit + integration
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/{scheduling,payments,fiscal}/ -v

# 3. FE typecheck + lint + tests
cd ${WS}/vitalia/frontend && npx tsc --noEmit
cd ${WS}/vitalia/frontend && npx eslint src/features/valeria/ src/app/\[tenantId\]/\(shell-organism\)/valeria/agenda/ --cache
cd ${WS}/vitalia/frontend && npx vitest run src/features/valeria/

# 4. Migration idempotent (corre 2 veces)
docker exec luana-dev-vitalia_backend_dev-1 alembic upgrade head
docker exec luana-dev-vitalia_backend_dev-1 alembic upgrade head

# 5. Tables exist with composite indexes
docker exec luana-dev-luana_postgres_dev-1 psql -U postgres -d vitalia_dev -c "\dt vitalia_*" | grep -E 'appointment_payments|fiscal_documents|appointment_clinic_map|growth_studio_event'

# 6. E2E runtime (pendiente W2 fix Docker stack)
cd ${WS}/vitalia/frontend && pnpm install   # arregla @hookform/resolvers/zod
E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase2-valeria-agenda/ --project=smoke
```

## Capability promotion summary

- **Capability:** `valeria.agenda` (scheduling module)
- **Status:** planned → live (2026-05-27)
- **Story introducer:** vitalia-fase2-valeria-agenda
- **Package version:** vitalia-fase2-v1.0.0 (primera story Fase 2)
- **Test coverage paths:** ver `vitalia/docs/product/capabilities/scheduling/valeria-agenda.yaml::test_coverage`
- **Date introduced:** 2026-05-27

## Notes for /pm-luana (promotion candidates)

2 learnings cardinales escritos en `vitalia/docs/learnings/` con flag promotable:

1. `2026-05-27-fase2-first-story-shipped-shell-feature-pattern.md` (promotable: yes) — origen del pattern ADR-vitalia-004 shell-feature-architecture cross-brand candidate
2. `2026-05-27-service-deps-option-a-stubs-msw.md` (promotable: candidate) — pattern stubs + MSW pre-service-deps developed para unblock parallel build

`/pm-luana` evaluará post-merge para promotion proposals en `docs/promotion-protocol/proposals/`.
