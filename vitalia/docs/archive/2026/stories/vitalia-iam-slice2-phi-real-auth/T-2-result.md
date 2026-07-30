# T-2-result — BE repos-wire (repos PHI reales DI + rol desde DB)

> **Finalizado por orchestrator** (el builder-backend Sonnet completó el código + tests en el árbol pero se trabó mid-debug de una flakiness que resultó inexistente, sin emitir commit/result). Orchestrator verificó el trabajo ejerciendo los tests (49 passed × 7 seeds + arch 324), confirmó OQ-1, y cerró el commit por pathspec.

## Estado: tests-passing → pushed

## Diff resumen

| Archivo | Acción |
|---|---|
| `vitalia/backend/src/modules/vitalia/crm/api/router.py` | repos reales DI (PatientRepository/LeadRepository) + `await async_resolve(...)`; AsyncMock inline runtime eliminado |
| `vitalia/backend/src/modules/vitalia/crm/api/consent_endpoints.py` | repos reales DI + async_resolve |
| `vitalia/backend/src/modules/vitalia/marketing/api/deps.py` | rol desde DB (async_resolve) |
| `vitalia/backend/src/modules/vitalia/marketing/api/routes.py` | repos reales DI + rol desde DB |
| `vitalia/backend/src/modules/vitalia/inbox/api/router.py` | repos reales DI + rol desde DB |
| `vitalia/backend/tests/integration/test_phi_real_auth.py` | EXTEND: SC-2 (recepcion/marketing 403) + SC-3 (cross-tenant 404 / cross-clinic 403) |
| `vitalia/backend/tests/modules/vitalia/inbox/api/*.py` (9 files) | downstream: actualizados al nuevo wiring async_resolve del inbox router |

## Gate output (literal)

```
pytest tests/integration/test_phi_real_auth.py tests/modules/vitalia/inbox/api/  → 49 passed (determinista)
  random seeds 111/222/333/444/555/777/999 → 49 passed cada uno (NO flakiness)
pytest tests/architecture/  → 324 passed  (incl. test_phi_dual_filter, test_audit_log_sync_write,
  test_audit_log_row_per_phi_endpoint, test_response_model_required, test_no_phi_in_url_params, test_auth_stub_env_gate)
ruff check src/modules/vitalia/{iam,crm,marketing,inbox}/  → All checks passed
ruff format --check  → 8 files already formatted
```

## scenario_coverage (cat-3 + cat-4)

- SC-2 · `test_recepcion_403_on_get_patient` + `test_marketing_403_on_marketing_opt_in` → 403 real + no leak ✅
- SC-3 · `test_cross_tenant_404_no_phi_leak` + `test_cross_clinic_403_no_phi_leak` → 404/403 + assert no-leak ✅

## OQ-1 (sub-scope) — endpoint → repo real

Todos los endpoints PHI de crm/consent/marketing/inbox usan repos reales (PatientRepository, LeadRepository, MessageRepository, ConversationRepository, ActionReceiptRepository, ActivityEventRepository, LucasRecommendationRepository, ChannelMetricRepository, AttributionMatrixSnapshotRepository). Cero repo inventado. Detalle en `T-2-impl-log.md § Sub-scope (OQ-1)`.

**Sub-scope honesto:** `inbox/api/router.py:130-142` conserva un `_AsyncMock()` PRE-EXISTENTE (no tocado por T-2) que es el fallback offline del outbox event bus (import-guarded). No es repo PHI ni path de auth. Limpieza = follow-up fuera del mandato T-2.

## Skills consulted (must_load enforcement v4.1)

| Skill / Rule | Status | When |
|---|---|---|
| backend-expert | ✅ loaded | DDD wiring DI repos |
| tessl__fastapi | ✅ loaded | Depends(get_async_session) pattern |
| tessl__pytest-api-testing | ✅ loaded | integration SC-2/SC-3 |
| .claude/rules/tenant-isolation.md | ✅ loaded | dual filter verify |
| .claude/rules/backend-ddd.md | ✅ loaded | Inside-Out boundaries |
| .claude/rules/tdd-mandatory.md | ✅ loaded | RED-first SC-2/SC-3 |
| .claude/rules/test-design-doctrine.md | ✅ loaded | naturaleza BE endpoint → integration + cross-tenant |
| vitalia/.claude/rules/hipaa-lite.md | ✅ loaded | dual filter + audit + RBAC |

## CONN (anti-isla)

Consumed (async_resolve + repos reales consumidos por endpoints) · On-the-map (cap iam-scaffold-slice-1) · Navigable (FE manda JWT real + headers) · Notarized (routers ya montados en main.py).
