# T-SYNC review — EMBUDO-INBOX-SYNC-FIX + story close audit

> Auditor: /auditor (Auditor Responsable v5)
> Date: 2026-06-11
> Brand: vitalia · Story: vitalia-fase2-adrian-embudo
> Verdict: **APPROVED** (técnico) — merge bloqueado solo por `chris_verify.signoff` (demo Chris, `demo_required: true`)

## Scope auditado

1. **EMBUDO-INBOX-SYNC-FIX** (7 archivos FE, cambio de programación ratificado por Chris en `chris_verify.rounds`): cross-namespace RQ invalidation embudo↔inbox.
2. Cierre del story (todos sus tickets ya construidos + fix-loop B1/B2/U1/U2 live-verified 2026-06-04) — primera CHECKPOINTS formal (antes bloqueada por gate inbox, ahora resuelto).

## Carril R aplicado (Auditor Responsable v5)

El sync-fix llegó con 3 gaps (todos determinísticos / gate-captured, ninguno stake-asimétrico). El auditor los cerró él mismo:

1. **1 test RED (fixture stale)** — `use-retract-message.test.ts` sembraba la key LEGACY `['adrian','inbox','conversation',id]` mientras el hook (correctamente) optimistic-updatea la key RENDERIZADA `['crm','conversation',id]`. **El hook quedó correcto** (alineado con send/set-mode + `crm-shared/useConversationDetail`); el test estaba stale. Fix: el test ahora importa `conversationDetailKeyForInvalidation` de `../_keys` (misma factory que el hook → no puede driftar). Test 2 (rollback) que pasaba por la razón equivocada (false green) ahora ejerce de verdad la key correcta.
2. **Regression test faltante** — agregado `use-lead-stage-mutation.test.ts` "onSuccess cross-invalidates Inbox + Embudo namespaces": spy sobre `invalidateQueries` → assert `['crm','conversation']` + `['adrian','inbox']` se invalidan al mover etapa. Guard del contrato embudo↔inbox.
3. **Live-verify faltante** — board-live.spec contra dev-app real (PATCH /stage + POST /leads) con el código del sync-fix hot-loaded → 9/9, 0 traceback.

## Gates (post Carril R)

| Gate | Resultado |
|---|---|
| tsc --noEmit (strict) | ✅ exit 0 |
| eslint (adrian + crm-shared) | ✅ exit 0 |
| FE arch-fitness | ✅ 187/187 |
| vitest (adrian + crm-shared) | ✅ 351/351 (incl. regression test nuevo) |
| BE embudo scenarios (funnel/score/freeze/lock/cross-tenant/api) | ✅ 28/28 |
| BE agentic SC-1b override-feeds-agent | ✅ 10/10 |
| Live-verify dev-app (board-live, real backend) | ✅ 9/9 · POST 201 · PATCH 200 · persist · 0 traceback |
| Anti-burbuja (specs importan fixtures/base.ts) | ✅ board/resumen/recuperar |
| demo-script.md (demo_required) | ✅ presente |

## Verdict sync-fix: APPROVED

El cambio es correcto y de bajo riesgo (client-cache-only, sin cambio BE), consistente con el patrón ya establecido (send/set-mode ya usaban la key renderizada), y ahora guardado por un regression test + live-verify del write path. La confirmación visual cross-superficie es la demo de Chris.

## Out-of-scope findings (pre-existentes · NO regresiones del embudo · el sync-fix es FE-only)

Detectados al correr la suite BE completa. NINGUNO causado por el embudo ni el sync-fix:

1. **3 tests crm slice-1 rotos (test-harness)** — `test_lead_repository.py::test_get_by_id_raises_without_tenant_id` (`asyncio.get_event_loop().run_until_complete()` → `RuntimeError: no current event loop` en Python 3.12) + `test_router_conversation_detail.py::test_get_conversation_detail_404_slice1` (`MagicMock can't be used in 'await'` — debió ser AsyncMock) + (probable) otros `_slice1`. Origen: `50143d57` (slice-1, pre-embudo). Producto correcto; el **test** es el roto. → **HB-69** (test-harness debt, MED). NO los arreglo aquí (scope discipline: no son del embudo).
2. **`treatment_plans.notes` definido TEXT en vez de BYTEA** — columna PHI real en el módulo **fidelizacion** (`treatment_plan_model.py`, origen fidelizacion T-4 `df92ede3`), NO lead/embudo. Arch test `test_pgcrypto_phi_columns` FAIL. Es deuda PHI/compliance genuina (HIPAA-lite: PHI columns deben usar pgcrypto BYTEA). **Stake-asimétrico** (PHI + migración) → Carril C: **NO auditor self-fix**. → **HB-70 (HIGH)** + flag a Chris para story dedicada fidelizacion. NO bloquea el embudo (módulo distinto).

> Por qué no bloquean el embudo `done`: el embudo es FE-only en este delta + su BE propio (28 scenarios) verde; estos fallos viven en slice-1/fidelizacion y son anteriores a este story. Se rutean al CIL (harness-backlog) para cierre dedicado.

## Upstream deficiency

- Artefacto: `04-validators.yaml` — el `scenario_coverage` no incluía un scenario para el contrato **embudo↔inbox sync** (el bug que el sync-fix arregla existía latente porque ninguna verificación cruzaba las dos superficies). Acción: cuando una mutation de un módulo afecta la cache de OTRA feature, el architect debe declarar un scenario cross-surface + el dev un test de invalidation. Ancla: HB-42/44 (contrato imaginado / per-surface live-verify) — misma familia.
- Reflex auto-hardening: HB-69 + HB-70 registrados en `docs/process/harness-backlog.md`.

## Próximo

`/auditor` APPROVED (técnico) → **demo Chris** (`demo-script.md` contra dev-app, hard-reload primero) → `chris_verify.signoff` → `/pm-vitalia merge` (cap planned→live + 07-merge + archive). REFUSE merge sin signoff (DoD #37).
