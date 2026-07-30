# T-5 Result — BE fidelización application services

**Ticket:** T-5
**Story:** vitalia-slice-1-fidelizacion
**Brand:** vitalia
**State:** done (tests passing)
**Date:** 2026-05-20

## Summary

Implemented 6 application services (application layer — DDD Inside-Out) + 3 DTO files + 29 unit tests for the vitalia fidelización module. All tests GREEN, lint clean, arch fitness 265/265 passing.

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `tessl__fastapi` | Application services consume repos + emit DTOs | Thin services: validate → repo → DTO; no route logic in application layer |
| `tessl__pytest-api-testing` | 29 unit tests across 6 services | AsyncMock pattern, `MagicMock(spec=Model)` with explicit field values for Pydantic v2 compat |
| `backend-expert` (runtime-quality-checklist) | Anti-patterns FastAPI/SQLA/tests/migrations | Verified: no `session.query()`, no `datetime.utcnow()`, all repos async, structlog only |

## Files Created

### DTOs (3 files)

- `vitalia/backend/src/modules/vitalia/fidelizacion/application/dtos/re_engagement_dtos.py` — ReEngagementEventResponse, TriggerReEngagementRequest, ListPatternsRequest, PatternSummaryResponse, ProactiveReminderRequest, ProactiveReminderResponse, PausePatientRequest, PausePatientResponse, ManualCallRequest, ManualCallResponse
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/dtos/nps_dtos.py` — NPSSubmitRequest, NPSResponseResponse, NPSSummaryResponse
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/dtos/fidelizacion_summary_dtos.py` — TreatmentPlanSummaryResponse, FidelizacionDashboardResponse, OptOutPatientResponse

### Application Services (6 files)

- `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/re_engagement_service.py` — detect_multi_session_gaps, detect_follow_up_due, detect_maintenance_due, detect_absence, trigger_nps_post_treatment, mark_response_timeout, list_patterns, check_throttle
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/proactive_outbound_service.py` — 8-step SC-01 flow (opt_out → marketing_opt_in → throttle → compliance → audit → persist → event → return) + SC-02 blocking
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/pause_patient_service.py` — pause_patient (creates ABSENCE event with trigger_at=pause_until, emits PatientPausedReEngagement)
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/manual_call_service.py` — record_call (dual filter, PHI bytes for notes, HIPAA-lite audit log)
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/nps_service.py` — submit (NPS band detection, encrypted comment, audit, NPSScoreCollected event) + summary (aggregate stats, no per-patient PHI)
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/opt_out_service.py` — opt_out_patient (cascade cancel pending events → OPTED_OUT, audit log, PatientOptedOut event)

### Infrastructure Modified (1 file)

- `vitalia/backend/src/modules/vitalia/fidelizacion/infrastructure/repositories/re_engagement_event_repository.py` — added `list_pending_for_patient(*, tenant_id, clinic_id, patient_id)` (required by OptOutService cascade cancel; dual filter + `sent_at IS NULL + deleted_at IS NULL`)

### Test Files (6 files, 29 tests total)

- `test_re_engagement_service.py` — 8 tests (CheckThrottle×2, ListPatterns×2, DetectMultiSessionGaps×2, MarkResponseTimeout×1, TriggerNpsPostTreatment×1)
- `test_proactive_outbound_service.py` — 5 tests (SC-01 full flow×2, SC-02 blocking×3)
- `test_nps_service.py` — 6 tests (Submit×3, Summary×3)
- `test_opt_out_service.py` — 4 tests (cascade cancel, no pending, audit log, domain event)
- `test_pause_patient_service.py` — 3 tests (creates event, dual filter, emits domain event)
- `test_manual_call_service.py` — 3 tests (creates event + audit, with conversion, dual filter)

## HIPAA-lite Compliance

All services enforce:
- **Dual filter:** every repo call passes both `tenant_id` + `clinic_id`
- **Audit log:** sync write via `AuditLogRepository.write()` mandatory before response
- **PHI sanitization:** no patient name/diagnosis in logs; `payload_redacted=b""` in audit entries
- **Soft delete:** opt_out cascade marks events `OPTED_OUT` (not hard delete)

## Outbox Pattern

All 4 services that emit domain events (proactive_outbound, pause_patient, opt_out, nps) use module-level `adapter_bus` with try/except fallback for test environments — matching `patient_consent_service.py` precedent.

## Quality Gates

| Gate | Result |
|---|---|
| ruff check | 0 errors |
| ruff format | 0 files to reformat |
| pytest fidelizacion/application/ | 29/29 PASS |
| pytest tests/architecture/ | 265/265 PASS |
| No `session.query()` / `Column()` / `from_orm()` | Verified |
| No `datetime.utcnow()` | Verified |
| No `print()` / stdlib logging | Verified (structlog only) |
| Soft deletes only | Verified |
| tenant_id + clinic_id dual filter | Verified |

## Next Ticket

T-7: API layer (FastAPI routers + `response_model=` + `X-Tenant-ID` Header) — depends on T-5 DONE.
