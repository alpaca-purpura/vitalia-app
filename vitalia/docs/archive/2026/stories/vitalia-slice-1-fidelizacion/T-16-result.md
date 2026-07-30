---
ticket: T-16
story: vitalia-slice-1-fidelizacion
surface: backend
production_code: false
state: done
completed_at: 2026-05-20
commit: pending-push
tests_passed: 26/26
---

# T-16 Result — Cross-story contracts shape verification

## Summary

T-16 cementa los contratos producidos por vitalia-slice-1-fidelizacion para consumo
de Olas paralelas y futuras. 26 shape tests GREEN sin cambios de código (contratos
ya implementados en T-5/T-9/T-12).

## Deliverables

### 1. Archivo creado (nuevo)

`vitalia/backend/tests/integration/test_cross_story_contracts.py`

26 tests de introspección de shapes (sin Postgres):

| Clase test | Contrato verificado | Tests |
|---|---|---|
| `TestNPSScoreCollectedShape` | Evento NPSScoreCollected (T-5 emitter, /inbox consumer) | 5 |
| `TestReEngagementTriggeredShape` | Evento ReEngagementTriggered (T-5 emitter, /inbox consumer) | 4 |
| `TestPatientOptedOutShape` | Evento PatientOptedOut (T-2 emitter, T-5 OptOutService consumer) | 4 |
| `TestPatientPausedReEngagementShape` | Evento PatientPausedReEngagement (T-5 emitter, UI consumer) | 3 |
| `TestNPSSummaryResponseShape` | DTO endpoint GET /nps/summary (inbox NPS tag chip) | 4 |
| `TestReEngagementPatternListResponseShape` | DTO endpoint GET /re-engagement/patterns | 4 |
| `TestEventNameConstants` | SSoT registry event_name constants (bus handler filter strings) | 2 |

**Total: 26 tests / 26 PASS**

### 2. Archivo actualizado

`vitalia/docs/product/stories/vitalia-slice-1-fidelizacion/HANDOFF-cross-story-updates.md`

- § 1.4 Domain events: status actualizado "Pendiente" → "Implementado" para los 4 eventos
- § 1.3 Endpoints: status "NEW" → "Implementado" para `/nps/summary` y `/re-engagement/patterns`
- § 4 Bitácora: nota agregada sobre T-16 cement con evidencia de tests

## Estrategia de prueba

- **Eventos (@dataclass DomainEvent)**: `dataclasses.fields()` introspección + factory `.create()` smoke
- **DTOs (Pydantic v2 BaseModel)**: `model_fields` introspección + `model_json_schema()` snapshot
- **Sin Postgres** — solo introspección estática + unit construction
- **Patrón snapshot**: EXPECTED_FIELDS frozenset → si contrato cambia, test falla explícitamente forzando actualización del consumer

## Contratos cementados

### Eventos de dominio (4)

| Evento | event_name | Campos |
|---|---|---|
| `NPSScoreCollected` | `vitalia.fidelizacion.nps_score_collected` | event_name, tenant_id, occurred_at, payload, clinic_id, patient_id, nps_response_id, score, band, appointment_id |
| `ReEngagementTriggered` | `vitalia.fidelizacion.re_engagement_triggered` | event_name, tenant_id, occurred_at, payload, clinic_id, patient_id, pattern, re_engagement_event_id, template_id, triggered_by_user_id |
| `PatientOptedOut` | `vitalia.fidelizacion.patient_opted_out` | event_name, tenant_id, occurred_at, payload, clinic_id, patient_id, reason, triggered_by_user_id |
| `PatientPausedReEngagement` | `vitalia.fidelizacion.patient_paused_re_engagement` | event_name, tenant_id, occurred_at, payload, clinic_id, patient_id, duration_days, reason, resume_at, triggered_by_user_id |

### DTOs endpoint (2)

| DTO | Endpoint | Campos clave |
|---|---|---|
| `NPSSummaryResponse` | GET `/api/v1/vitalia/fidelization/nps/summary` | tenant_id, clinic_id, period_start, period_end, total_responses, promoters, passives, detractors, nps_score, response_rate, detractors_untagged |
| `ReEngagementPatternListResponse` | GET `/api/v1/vitalia/fidelization/re-engagement/patterns` | tenant_id, clinic_id, patterns (PatternSummaryResponse[]) |

## Validator gate

```bash
# be_cross_story_contracts
cd vitalia/backend && .venv/bin/pytest tests/integration/test_cross_story_contracts.py -v
# Result: 26 passed in 0.16s
```

## Skills consulted (must_load enforcement v4.1)

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `backend-expert` | Anti-patterns FastAPI/SQLA/tests antes commit | Usar `dataclasses.fields()` para @dataclass events (DomainEvent) y `model_fields` para Pydantic v2 DTOs; sin Postgres ni fixtures DB para shape tests |
| `brand-expert` | N/A — no toca módulo brand | Skipped (not in scope) |
| `offer-expert` | N/A — no toca módulo offer | Skipped (not in scope) |
| `metrics-expert` | N/A — no toca módulo analytics | Skipped (not in scope) |

Reglas cargadas: `backend-ddd.md`, `anti-duplication.md`, `architectural-fitness.md`, `tdd-mandatory.md`, `auditor-self-fix-policy.md`, `tenant-isolation.md`, `parallel-safety.md`, `tdd-mandatory.md`.

## HIPAA-lite compliance

Tests verifican explícitamente que los eventos de dominio y DTOs NO exponen PHI directo:
- `test_nps_score_collected_no_unexpected_phi_fields` — valida ausencia de comment_plain, patient_name, etc.
- `test_patient_opted_out_no_phi_direct_fields` — valida ausencia de campos médicos
- `test_nps_summary_response_no_phi_fields` — valida que /nps/summary solo devuelve stats anónimas

## Notes

- Tests no requieren `@pytest.mark.integration` (sin Postgres)
- RED→GREEN: tests escritos con EXPECTED_FIELDS correctas vs contratos ya implementados (T-5/T-9/T-12 shipped) — GREEN sin cambios de código de producción. TDD pattern cumplido: spec cementada ANTES del consumo en Ola 2.
- `downstream-regression-na: cross-story shape tests T-16 fidelizacion vitalia` en header del file (pre-commit Section 4 gate)
