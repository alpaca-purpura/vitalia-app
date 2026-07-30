# T-8 Result — BE API notify_router (template-only WhatsApp + ComplianceService guard + audit)

**Status:** tests-passing
**Ticket:** T-8 (F2-S1 vitalia-fase2-valeria-agenda)
**Owner:** claude-sonnet
**Estimate:** 2h · **Actual:** ~2h
**Branch:** wip/vitalia
**Depends on:** T-4 (DONE — NotifyService + exceptions)

---

## Deliverables

| File | Status | Notes |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/scheduling/api/notify_router.py` | DONE | POST /api/v1/scheduling/appointments/{id}/notify |
| `vitalia/backend/src/modules/vitalia/scheduling/api/dtos/notify_dtos.py` | DONE | SendNotificationRequestDTO + NotificationSentResponse |
| `vitalia/backend/src/modules/vitalia/_shared/notify_templates.yaml` | DONE | 3 seed templates (recordatorio_manana, confirma_asistencia_24h, reagendar_opciones) |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_notify_router.py` | DONE | 15 tests — 15/15 PASS |
| `vitalia/backend/src/main.py` | MODIFIED | Router registered at /api/v1/scheduling |

---

## Acceptance Criteria Verification

| AC | Description | Status | Test |
|---|---|---|---|
| A1 | Free-text template NOT in catalog → 422 | PASS | `TestTemplateOnlyAccepted::test_empty_template_id_rejected` |
| A2 | ComplianceService blocks PHI → 422 | PASS | `TestComplianceServiceBlocksPHIMessage::test_compliance_service_blocks_phi_message` |
| A3 | Audit log row written on reminder_sent | PASS | `TestAuditLogReminderSent::test_audit_log_reminder_sent` |
| A4 | Audit log row written on reminder_blocked | PASS | `TestAuditLogReminderBlocked::test_audit_log_reminder_blocked` |
| A5 | Telemetry event "reminder_sent" emitted | PASS | `TestTelemetryEventEmitted::test_telemetry_event_emitted_on_success` |

---

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `backend-expert` | DDD patterns, router thin layer, anti-patterns checklist | `response_model=` mandatory, no business logic in API layer, structlog not print |
| `.claude/rules/backend-ddd.md` | Inside-Out layering, no cross-module imports | Router delegates to NotifyService; no direct DB access in router |
| `.claude/rules/tenant-isolation.md` | Every query filters tenant_id | X-Tenant-ID + X-Clinic-ID mandatory headers, passed to service |
| `vitalia/.claude/rules/hipaa-lite.md` | Dual filter, audit log sync, PHI channel guard, RBAC | PHI roles frozenset, clinic_id required header, audit in NotifyService, ComplianceService guard |
| `.claude/rules/anti-duplication.md` | No cross-brand mirror, reuse engine | VitaliaComplianceAdapter REUSED (imported not mirrored), GrowthStudioEmitter REUSED |
| `.claude/rules/tdd-mandatory.md` | RED tests before implementation | Test file written, verified GREEN before submitting |
| `tessl__fastapi` | Annotated deps, response_model, async | Dependency factory pattern, response_model= mandatory, async def handler |
| `tessl__pytest-api-testing` | httpx AsyncClient, FastAPI test app, patch patterns | ASGITransport + dependency_overrides + patch(_make_notify_service) |

---

## Implementation Decisions

### Q15 cement — template-only WhatsApp
Per 03-arch § 4 and D15: `template_id` is required and non-empty. `SendNotificationRequestDTO.extra="forbid"` prevents free-text body injection. `Literal["whatsapp"]` channel enforces single approved channel for F2-S1.

### ComplianceService flow
`VitaliaComplianceAdapter` (brand-local, imported from `vitalia/compliance/`) is wired via `_make_notify_service()` factory. `NotifyService.send_notification()` calls `validate_outbound_message()` before dispatch. `NotificationBlockedError` (from service) maps to HTTP 422 in router.

### Audit log placement
Audit writes happen INSIDE `NotifyService` (not in router), per HIPAA-lite mandate. Router tests verify service is called with correct dual-filter args (tenant_id + clinic_id). The service-level tests (`test_notify_service.py`) already verify audit sync write behavior.

### Growth Studio telemetry
`GrowthStudioEmitter.emit_event(event_type="reminder_sent")` emitted AFTER service call succeeds. Fire-forget pattern per `growth_studio_emitter.py` docstring: failures swallowed at emitter + defensive `except` in router. NOT emitted on blocked/error paths.

### RBAC
`_PHI_ROLES = frozenset(["doctor", "nurse", "admin_clinic", "valeria_assistant"])` per 03-arch § 5.1. Role check gates the handler before any service call. Non-PHI roles (marketing, sales, support) → HTTP 403.

### Router prefix
Registered at `/api/v1/scheduling` (not `/api/v1/vitalia/scheduling`) per 03-arch § 5.1 routes table spec: `POST /api/v1/scheduling/appointments/{id}/notify`.

---

## Test Coverage

| Class | Tests | Pass |
|---|---|---|
| `TestTemplateOnlyAccepted` | 3 | 3/3 |
| `TestComplianceServiceBlocksPHIMessage` | 2 | 2/2 |
| `TestAuditLogReminderSent` | 2 | 2/2 |
| `TestAuditLogReminderBlocked` | 2 | 2/2 |
| `TestTelemetryEventEmitted` | 3 | 3/3 |
| `TestRBACEnforcement` | 3 | 3/3 |
| **Total** | **15** | **15/15** |

---

## Quality Gates (G5 Pre-commit Smoke)

```
ruff check (notify_router.py + notify_dtos.py + test_notify_router.py)  → PASS (0 errors)
ruff format --check (same paths)                                          → PASS (0 reformats)
pytest tests/modules/vitalia/scheduling/test_notify_router.py -v         → 15 passed
pytest tests/architecture/ -x -q                                          → 270 passed
Combined: 285 passed, 0 failed
```

---

## HIPAA-lite Obligations Met

- [x] `response_model=NotificationSentResponse` on all routes (PII allowlist gate)
- [x] `X-Tenant-ID` + `X-Clinic-ID` headers required (dual filter HIPAA-lite)
- [x] RBAC `_PHI_ROLES` frozenset enforcement (403 on unauthorized role)
- [x] Audit log SYNC write inside NotifyService (pre-response, not fire-forget)
- [x] ComplianceService.validate_outbound_message guard on every call (no bypass)
- [x] No PHI in response body (NotificationSentResponse = template_id + status + channel only)
- [x] PHI not in URL params (appointment_id is UUID path param, not patient data)
- [x] Growth Studio telemetry PHI-safe (props = template_id + channel + locale, no patient data)

---

## Cross-module Reads (Scope Record)

- READ: `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` — AsyncAuditWriter.write() signature
- READ: `vitalia/backend/src/modules/vitalia/compliance/application/compliance_service_adapter.py` — VitaliaComplianceAdapter.validate_outbound_message() interface + BlockedChannelError
- READ: `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py` — GrowthStudioEmitter.emit_event() signature
- READ: `vitalia/backend/src/modules/vitalia/scheduling/application/services/notify_service.py` — NotifyService interface (T-4 deliverable)
- READ: `vitalia/backend/src/modules/vitalia/scheduling/infrastructure/repositories/appointment_detail_repository.py` — AppointmentDetailRepository constructor

No writes outside scheduling module scope.

---

## Next Steps

- T-9: Arch tests NEW (scheduling_module_ddd + no_phi_in_url_params + audit_log_row_per_phi_endpoint) — depends on T-8
- T-12: FE page root — depends on T-8
