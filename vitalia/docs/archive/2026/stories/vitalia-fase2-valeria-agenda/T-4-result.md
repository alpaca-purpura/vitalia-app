# T-4 Result — BE Scheduling Application Services + Ports

**Story:** vitalia-fase2-valeria-agenda
**Ticket:** T-4
**Branch:** wip/vitalia
**Date:** 2026-05-26
**State:** tests-passing

---

## Files Created / Modified

### New files (16)

| Path | Description |
|---|---|
| `vitalia/backend/src/modules/vitalia/_shared/phi_masking.py` | PHI masking utilities: `mask_name()`, `mask_dni()`, `mask_phone()`, `mask_email()` |
| `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py` | GrowthStudioEmitter — brand-local UX/funnel telemetry (fire-forget, not audit_log) |
| `vitalia/backend/src/modules/vitalia/_shared/telemetry/amount_bucket.py` | `bucket_amount()` — privacy-preserving monetary range bucketing |
| `vitalia/backend/src/modules/vitalia/scheduling/application/services/__init__.py` | Package marker |
| `vitalia/backend/src/modules/vitalia/scheduling/application/services/agenda_grid_service.py` | AgendaGridService — list PHI-masked slots + audit log sync write |
| `vitalia/backend/src/modules/vitalia/scheduling/application/services/appointment_detail_service.py` | AppointmentDetailService — PHI-masked detail + audit log on all calls including 404 |
| `vitalia/backend/src/modules/vitalia/scheduling/application/services/appointment_status_service.py` | AppointmentStatusService — status transition + audit log (from/to) + telemetry |
| `vitalia/backend/src/modules/vitalia/scheduling/application/services/create_appointment_service.py` | CreateAppointmentService — engine create + brand-local clinic_map (A12) + audit + telemetry |
| `vitalia/backend/src/modules/vitalia/scheduling/application/services/notify_service.py` | NotifyService — template-only WhatsApp + ComplianceService guard + audit log |
| `vitalia/backend/src/modules/vitalia/scheduling/application/ports/__init__.py` | Package marker |
| `vitalia/backend/src/modules/vitalia/scheduling/application/ports/payment_charge_port.py` | PaymentChargePort ABC + ExternalPaymentResult + PaymentAdapterUnavailableError |
| `vitalia/backend/src/modules/vitalia/scheduling/application/ports/fiscal_emit_port.py` | FiscalEmitPort ABC + FiscalDocResult + FiscalAdapterUnavailableError + FiscalEmitError |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_agenda_grid_service.py` | 6 unit tests: PHI masking + audit log + cross-clinic empty |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_appointment_detail_service.py` | 6 unit tests: PHI masking + audit log (incl 404) + cross-clinic 404 |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_appointment_status_service.py` | 7 unit tests: audit log from/to + telemetry event + cross-clinic 404 |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_create_appointment_service.py` | 5 unit tests: clinic_map persist (A12) + audit log + telemetry |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_notify_service.py` | 8 unit tests: compliance guard + template-only + audit log (incl blocked) + cross-clinic 404 |

### Modified files (1)

| Path | Change |
|---|---|
| `vitalia/backend/src/modules/vitalia/scheduling/domain/exceptions.py` | Added: `NotificationBlockedError`, `FreeTextNotificationError`, `AppointmentStatusInvalidError` |

---

## Gate Results

### Ruff check
All checks passed (0 errors on `src/` + new test files).

### Ruff format
All 19 new files formatted correctly.

### Architecture tests
270 passed, 0 failed, 0 errors.

### Scheduling module tests
108 passed, 0 failed (includes 30 new service tests + 78 pre-existing tests).

### All service tests (30 new)
```
tests/modules/vitalia/scheduling/test_create_appointment_service.py    5 PASS
tests/modules/vitalia/scheduling/test_notify_service.py                8 PASS
tests/modules/vitalia/scheduling/test_appointment_detail_service.py    6 PASS
tests/modules/vitalia/scheduling/test_appointment_status_service.py    7 PASS
tests/modules/vitalia/scheduling/test_agenda_grid_service.py           6 PASS (includes mask_name/mask_dni functions)
Total: 30/30 PASS
```

---

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Always-on: anti-patterns FastAPI/SQLA/tests/migrations | SQLA 2.0 patterns confirmed; `AsyncAuditWriter.write()` uses `await` (async); PHI masking at repo layer |
| `tessl__fastapi` | Async patterns, response_model, dependency injection | Thin service layer; services receive deps via constructor injection not FastAPI DI (tested with plain mocks) |
| `tessl__pytest-api-testing` | Test fixture patterns, AsyncMock | Lazy import pattern `_import_service()` used to keep RED tests failing only on ImportError, not at collection |
| HIPAA-lite overlay | PHI safety rules for vitalia brand | A1: PHI masking via `_PHI_RAW_KEYS` strip + repo-level masking; A2: sync write before return; A3: cross-clinic 404 + audit on all paths; A4: ComplianceService guard in NotifyService |

---

## HIPAA-lite Compliance Notes

### A1 — PHI masking
- `AppointmentDetailService.get_detail()` strips `_PHI_RAW_KEYS` from repo dict before returning.
- `mask_name()` / `mask_dni()` / `mask_phone()` / `mask_email()` available in `_shared/phi_masking.py`.
- Repo layer already returns masked fields (`patient_name_masked`, `dni_masked`) from SQL-level projections.

### A2 — Audit log sync write
- All 5 services write audit log BEFORE returning response.
- `AppointmentDetailService` and `NotifyService` write audit log EVEN on 404/blocked path.
- Audit action names: `appointment.agenda_read`, `appointment.detail_read`, `appointment.status_change`, `appointment.create`, `appointment.send_notification`.

### A3 — Cross-clinic 404
- `AppointmentDetailService`, `AppointmentStatusService`, `NotifyService`: repo returns `None` → `AppointmentNotFoundError` (audit log written first).
- `AgendaGridService`: repo returns `[]` for cross-clinic (grid = 200 empty, not 404).

### A4 — ComplianceService guard
- `NotifyService.send_notification()` calls `compliance.validate_outbound_message()` before dispatch.
- `BlockedChannelError` from VitaliaComplianceAdapter → re-raised as `NotificationBlockedError`.
- Audit log written even on compliance block (suspicious action logging).

---

## A12 — AppointmentClinicMap

`CreateAppointmentService.create_appointment()` calls:
1. `repo.create()` → engine appointment row (no clinic_id column on engine).
2. `repo.create_clinic_map(tenant_id, clinic_id, appointment_id, ...)` → `vitalia_appointment_clinic_map` row.

Both calls are in same service method. If `create_clinic_map` fails, appointment is considered incomplete.

---

## Port Interfaces (service-blocker pattern)

- `PaymentChargePort` (ABC) + `ExternalPaymentResult` + `PaymentAdapterUnavailableError`
- `FiscalEmitPort` (ABC) + `FiscalDocResult` + `FiscalAdapterUnavailableError` + `FiscalEmitError`

Concrete implementations pending: `vitalia-payment-adapter-mvp` (refined) + `vitalia-fiscal-emission-pe` (refining). F2-S1 ChargeOrchestrator uses stub ports raising `*AdapterUnavailableError` → HTTP 503.

---

## R24 Context-Brief Note

`CONTEXT-BRIEF.md` header had `Validator pass: _pending_` at session start. Caller provided full explicit architect spec + ticket deliverables = context-validator-skipped override. §11 gaps noted: LOW severity (stale cross-brand status). Proceeded per explicit ticket instructions.
