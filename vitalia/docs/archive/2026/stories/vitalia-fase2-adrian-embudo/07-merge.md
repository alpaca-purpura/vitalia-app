# Merge artifact — vitalia/vitalia-fase2-adrian-embudo

> Brand: vitalia
> Merged: 2026-06-11
> Commit (squash-merge): wip/vitalia rolling (hub único ADR-009 — commits clave: `59894c99` root-fix funnel + `8ce72b0e` dev-infra + `732794a0` tests 326/326 + `a07fd880` learnings/cap + este commit 07-merge+archive)
> Signoff: `chris_verify.signoff: SATISFIED` (Chris, 2026-06-11 — demo live: spinner crear-lead · canal en detalle · /recuperar empty-state)

## § 1 — Gherkin verification matrix

> Copia de `06-audit/gherkin-matrix.md` (auditor Phase D, 2026-06-11). Verificación REAL (acción + efecto/logs).

| Scenario (Gherkin) | Test path | Status |
|---|---|---|
| SC-1 transición agent-driven (RN-3) | `vitalia/backend/tests/modules/vitalia/crm/test_funnel_service.py` | ✅ PASS (28/28) |
| SC-1b override manual feeds agent (RN-4/4.1) | `vitalia/backend/tests/modules/vitalia/sales_agent/test_manual_override_feeds_agent_context.py` | ✅ PASS (10/10) |
| SC-2 salto inválido → 422 {allowed_next} | `vitalia/backend/tests/modules/vitalia/crm/test_funnel_api.py` | ✅ PASS (7/7) |
| SC-4 cross-tenant → 404 genérico (RN-1) | `vitalia/backend/tests/modules/vitalia/crm/test_cross_tenant_lead_block.py` | ✅ PASS (2/2) |
| SC-5 optimistic lock 409 (version) | `vitalia/backend/tests/modules/vitalia/crm/test_stage_transition_optimistic_lock.py` | ✅ PASS (2/2) |
| SC-freeze auto-freeze + reactivate (RN-13) | `vitalia/backend/tests/modules/vitalia/crm/test_auto_freeze_and_reactivate.py` | ✅ PASS (5/5) |
| SC-board hot-only (RN-18) + orden (RN-17) | `board-live.spec.ts` A-1/A-3 (LIVE) | ✅ PASS LIVE |
| SC-nuevo alta lead → POST 201 → highlight | `board-live.spec.ts` B-1/B-2 (LIVE) | ✅ PASS LIVE |
| SC-detalle página lead Resumen/Historial | `resumen-live.spec.ts` D+E (LIVE) | ✅ PASS LIVE |
| SC-recuperar congelados + hard-nav | `recuperar-live.spec.ts` R-1 (LIVE) | ✅ PASS LIVE |
| embudo↔inbox stage sync (sync-fix 2026-06-11) | `use-lead-stage-mutation.test.ts` cross-invalidation | ✅ PASS (regression guard) |
| **Funnel fields persisten en POST (fix demo bug 2)** | `vitalia/backend/tests/modules/vitalia/crm/test_lead_repo_funnel_fields.py` | ✅ PASS (2/2, RED→GREEN) + fila DB `channel=whatsapp` |
| SC-3/6/7/8/9/10/11 (tenant-switch, paralelo, network, empty, 1200, a11y, i18n) | — | ⏳ WIP (T-E2E-1 deferred, ratificado Chris 2026-06-04 — scenarios `wip` en el cap) |

## § 2 — Playwright E2E run

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase2-adrian-embudo/
```

- Specs run: **13** (board-live 8 + recuperar-live 2 + resumen-live 2 + setup auth)
- Passed: **13** · Failed: **0** (corrida 2026-06-11, repetida sobre container FE recreado desde imagen nueva — mismo verde)
- Trace: `vitalia/frontend/playwright-report/`
- Backend durante la corrida: 0 tracebacks · POST /crm/leads 201 · PATCH /stage 200

## § 3 — Capabilities updated/created

- `vitalia/docs/product/capabilities/crm/adrian-embudo.yaml` — UPDATE (status: planned → **live**) + 15 scenarios poblados verbatim del spec (8 `live` con test PASS, 7 `wip` e2e-deferred) + change_log ×2 (new shipped + fix shipped `59894c99`)

## § 4 — Modules MD refreshed

- `vitalia/docs/product/modules/crm.md` — auto-list incluye `adrian-embudo` (status live) post-`make portfolio`

## § 5 — How to verify (reproducible commands)

```bash
WS=$(git rev-parse --show-toplevel)

# 1. BE suite crm (326/326 — incluye regresión funnel fields)
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/crm/ -q

# 2. Arch fitness
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ -x -q

# 3. E2E live (stack arriba: make dev-vitalia)
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test e2e/regression/vitalia-fase2-adrian-embudo/

# 4. Verificación manual (dr.demo@vitalialat.com en localhost:3002):
#    /adrian/embudo → + Nuevo lead (spinner visible al crear) → detalle muestra canal
#    → mover etapa (drag) → /adrian/recuperar (empty-state si no hay congelados)

# 5. Efecto en DB (canal persistido):
docker exec luana-dev-luana_postgres_dev-1 psql -U postgres -d vitalia_dev \
  -c "SELECT stage, channel, service_interest FROM vitalia_leads ORDER BY created_at DESC LIMIT 3;"
```

## Notas de cierre

- **Demo-fix loop 2026-06-11:** demo Chris encontró 3 bugs → root-fix (spinner FE · funnel fields en `LeadRepository.create` — el service Y el `funnel_service` original los dropeaban · /recuperar = no-bug). Re-verificado live 13/13 + fila DB.
- **Incidente colateral resuelto:** stack caído por store pnpm congelado en imagen FE (post-lift ui-kit 0.4.0) + KEK pisado por compose → 3 learnings capturados (`docs/learnings/2026-06-11-*`) + fix portado a nicolify/comunify.
- **Out-of-scope flaggeado:** HB-70 (HIGH — `treatment_plans.notes` PHI sin cifrar, módulo fidelizacion → story dedicada) · HB-69 CERRADO (suite crm 326/326, commit `732794a0`) · TD-1 (cadena alembic no self-contained desde DB cero).
- **Follow-up:** T-E2E-1 (7 scenarios `wip`: SC-3/6/7/8/9/10/11 + visual goldens) — deferred ratificado 2026-06-04.
