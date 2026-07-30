# Gherkin verification matrix — vitalia/vitalia-fase2-adrian-embudo

> Auditor: /auditor (Phase D · Auditor Responsable v5)
> Date: 2026-06-11
> Verification = REAL (acción ejercida + efecto/logs), no "GET 200" (test-design-doctrine).

## Scenario → test → status

| Scenario (spec § Gherkin / 04-validators) | Test path | Status | Evidence |
|---|---|---|---|
| SC-1 transición agent-driven (RN-3) | `crm/test_funnel_service.py` | ✅ PASS | 28/28 BE suite |
| SC-1b override manual feeds agent (RN-4/4.1) | `sales_agent/test_manual_override_feeds_agent_context.py` | ✅ PASS | 10/10 |
| SC-2 salto inválido → 422 {allowed_next} | `crm/test_funnel_api.py` | ✅ PASS | funnel_api 7/7 |
| SC-4 cross-tenant → 404 genérico (RN-1) | `crm/test_cross_tenant_lead_block.py` | ✅ PASS | 2/2 |
| SC-5 optimistic lock 409 (version) | `crm/test_stage_transition_optimistic_lock.py` | ✅ PASS | 2/2 |
| SC-freeze auto-freeze 14/30/2×SLA + reactivate (RN-13) | `crm/test_auto_freeze_and_reactivate.py` | ✅ PASS | 5/5 |
| SC-board hot-only scope (RN-18) + order (RN-17) | `crm/test_funnel_service.py` board + `board-live.spec.ts` A-1/A-3 | ✅ PASS | live 9/9 |
| SC-5/RN-4 →Reservado gated 403 | `crm/test_funnel_service.py` | ✅ PASS | incl. en 28 |
| F-10 score glass-box determinista | `crm/test_funnel_service.py` (factores=total) | ✅ PASS | B2 fix-loop |
| SC-nuevo alta lead → POST 201 → highlight | `board-live.spec.ts` B-1/B-2 (LIVE) | ✅ PASS LIVE | POST /crm/leads 201 dev-app |
| SC-detalle página lead Resumen/Historial | `resumen-live.spec.ts` D+E (LIVE) | ✅ PASS LIVE | nombre/teléfono/correo/score |
| SC-recuperar congelados + hard-nav | `recuperar-live.spec.ts` R-1 (LIVE) | ✅ PASS LIVE | 5/5, sin hang shell |
| **embudo↔inbox stage sync (sync-fix 2026-06-11)** | `use-lead-stage-mutation.test.ts` cross-invalidation | ✅ PASS | regression guard NEW |

## Live-verify (DoD #37) — REAL writes contra dev-app.vitalialat.com

| Acción (write) | Efecto observado | Backend log |
|---|---|---|
| PATCH /crm/leads/{id}/stage (interesado→calificando, version) | board persiste post-reload, sin burbuja Next | `funnel_transition_complete ... 200 OK` |
| POST /crm/leads (alta dental LatAm) | lead creado, redirect highlight | `lead_created ... 201 Created` |
| Anti-burbuja | board/resumen/recuperar specs importan `fixtures/base.ts` | 0 pageerror/console/4xx |
| Traceback count (3m ventana live-verify) | — | **0** |

## Verdict matrix

**Todos los scenarios del spec con test PASS (BE 28 + agentic 10 + live 9 + sync regression).** Cero NO_COVERAGE, cero FAIL en scope embudo.

`embudo↔inbox sync` (sync-fix) verificado por: (1) regression test unit (invalidation fires sobre `['crm','conversation']` + `['adrian','inbox']`), (2) board-live confirma el PATCH write intacto. La **confirmación visual cross-superficie** (mover etapa en Embudo → thread Inbox refresca) queda para la **demo de Chris** (`demo_required: true` → `chris_verify.signoff`).

## Out-of-scope (pre-existentes, NO regresiones del embudo · ver T-SYNC-review.md § Out-of-scope)

- 3 tests crm slice-1 rotos (test-harness: `asyncio.get_event_loop()`, `MagicMock` no-awaitable) → HB-69.
- `treatment_plans.notes` TEXT-no-BYTEA (módulo **fidelizacion**, PHI real) → HB-70 (HIGH, stake-asimétrico).
