# T-be-services-2 — Result

**Ticket:** T-be-services-2 — Adrián sales_agent backend services (3 services + repo + adapters + channel guards)
**Story:** vitalia-copilot-tools-impl
**Branch:** wip/vitalia-slice-1-shipping
**State:** tests-passing
**Completed:** 2026-05-18

## Scope implemented

### Domain layer (new)
- `sales_agent/domain/enums/screening_outcome.py` — `ScreeningOutcome` StrEnum (4 values matching migration 021 CHECK)
- `sales_agent/domain/entities/lead_screening_event.py` — `LeadScreeningEvent` domain dataclass (PHI dual filter fields)

### Infrastructure layer (new)
- `sales_agent/infrastructure/repositories/lead_screening_event_repository.py` — `LeadScreeningEventRepository(PhiRepositoryBase)` with dual filter (tenant_id + clinic_id) on every method including get_by_id
- `sales_agent/infrastructure/adapters/mercadopago_adapter.py` — `MercadoPagoAdapter` (create_preference + HMAC webhook validation, 10s timeout, 1 retry 2s backoff)
- `sales_agent/infrastructure/adapters/whatsapp_business_adapter.py` — `WhatsAppBusinessAdapter` (send_template_message, retract_last_message → NotImplementedError Slice 2)

### Compliance guardrails (new)
- `compliance/guardrails/medical_results_guard.py` — `MedicalResultsChannelGuard` delegating to `VitaliaComplianceAdapter.validate_outbound_message`
- `compliance/guardrails/whatsapp_free_phi_guard.py` — `WhatsAppFreePhiGuard` payload-level PHI key scanner

### YAML SSoT (new)
- `agentic/screening/screening_questions_by_vertical.yaml` — 4 required verticals × 2-4 questions each (dental, estetica, psicologia, fertilidad) + otro fallback

### Application services (new)
- `sales_agent/application/services/screening_questions_service.py` — `ScreeningQuestionsService` (YAML load → LLM nano → PHI sanitize → persist LeadScreeningEvent → audit_log sync write)
- `sales_agent/application/services/payment_link_service.py` — `PaymentLinkService` (channel guard first → MP preference → WA template → payment_events idempotency → audit_log sync write)
- `sales_agent/application/services/reschedule_appointment_service.py` — `RescheduleAppointmentService` (AppointmentService.update_slot + audit_log sync write)

### Architecture test (new)
- `tests/architecture/test_screening_yaml_completeness.py` — 6 tests verifying YAML SSoT structural invariants

### Unit tests (new — TDD RED→GREEN)
- `tests/unit/modules/vitalia/sales_agent/domain/test_screening_outcome.py` (8 tests)
- `tests/unit/modules/vitalia/sales_agent/domain/test_lead_screening_event.py` (9 tests)
- `tests/unit/modules/vitalia/sales_agent/infrastructure/test_lead_screening_event_repository.py` (8 tests)
- `tests/unit/modules/vitalia/sales_agent/test_channel_guards.py` (13 tests)
- `tests/unit/modules/vitalia/sales_agent/application/services/test_screening_questions_service.py` (8 tests)
- `tests/unit/modules/vitalia/sales_agent/application/services/test_payment_link_service.py` (5 tests)
- `tests/unit/modules/vitalia/sales_agent/application/services/test_reschedule_appointment_service.py` (4 tests)

## Test results

| Suite | Tests | Result |
|---|---|---|
| Architecture fitness | 222 | PASS |
| Unit — domain | 17 | PASS |
| Unit — infrastructure | 8 | PASS |
| Unit — channel guards | 13 | PASS |
| Unit — application services | 17 | PASS |
| **Total unit** | **56** | **PASS** |

## HIPAA-lite compliance checks

- PHI dual filter (tenant_id + clinic_id) enforced on ALL repository methods via `PhiRepositoryBase.validate_dual_filter()`
- Audit log written synchronously (await before return) in all 3 services
- `sanitize_phi_payload()` applied before persisting response_text + reasoning in ScreeningQuestionsService
- Channel guard `MedicalResultsChannelGuard.validate()` called FIRST in `PaymentLinkService.send_payment_link()` before any adapter call
- Payment events table uses `ON CONFLICT (appointment_id, deposit_percent) DO NOTHING` for idempotency

## Bugs fixed

- YAML path computation: `parents[6]` → `parents[5]` (from service file to `vitalia/backend/src/`)
- `_YAML_CACHE` module-level singleton correctly initialised after path fix

## Validators GREEN

- `ruff check`: 0 errors in new files
- `ruff format`: all new files formatted
- Architecture fitness: 222 passed
- Unit tests: 56 passed
