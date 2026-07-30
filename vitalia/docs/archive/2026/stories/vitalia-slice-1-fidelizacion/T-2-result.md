# T-2 Result — CRM extension: patient consent (opt-in/opt-out) service + endpoints

> Brand: vitalia
> Ticket: T-2
> Builder: builder-backend (Sonnet 4.6)
> Completed: 2026-05-20
> Status: tests-passing

## Summary

Implemented the patient consent lifecycle for Slice 1 fidelizacion:
- `PatientConsentService` — opt-out (admin_clinic only) + marketing-opt-in (doctor/nurse/admin_clinic)
- `consent_endpoints.py` — POST `/api/v1/crm/patients/{id}/opt-out` + PATCH `/api/v1/crm/patients/{id}/marketing-opt-in`
- `consent_dtos.py` — `OptOutRequest`, `OptOutResponse`, `MarketingOptInRequest`, `MarketingOptInResponse`
- `PatientOptedOut` domain event (in `crm/domain/events.py`) emitted via outbox adapter_bus
- Extended `Patient` domain entity with migration-023 columns
- Extended `PatientRepository` with new column reads + `marketing_opt_in()` method + updated `opt_out()` to use new columns

## Files modified/created

### NEW files
- `vitalia/backend/src/modules/vitalia/crm/application/services/patient_consent_service.py` — PatientConsentService
- `vitalia/backend/src/modules/vitalia/crm/application/dto/consent_dtos.py` — 4 Pydantic v2 DTOs
- `vitalia/backend/src/modules/vitalia/crm/api/consent_endpoints.py` — 2 FastAPI endpoints
- `vitalia/backend/tests/modules/vitalia/crm/test_patient_consent_service.py` — 14 service tests
- `vitalia/backend/tests/modules/vitalia/crm/api/__init__.py` — package marker
- `vitalia/backend/tests/modules/vitalia/crm/api/test_consent_endpoints.py` — 14 API tests

### EXTENDED files
- `vitalia/backend/src/modules/vitalia/crm/domain/patient.py` — +4 consent fields (marketing_opt_in, opt_out, opt_out_reason, opt_out_at)
- `vitalia/backend/src/modules/vitalia/crm/domain/events.py` — +PatientOptedOut event dataclass
- `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/patient_repository.py` — updated SELECT queries for new columns + new marketing_opt_in() method + fixed opt_out() to use migration-023 columns
- `vitalia/backend/src/modules/vitalia/crm/api/router.py` — include_router(consent_router) + removed duplicate old opt-out endpoint

## Quality gates

| Gate | Result |
|---|---|
| `ruff check src/modules/vitalia/crm/ tests/modules/vitalia/crm/` | PASS — 0 errors |
| `ruff format --check ...` | PASS — 0 files to reformat |
| `pytest tests/modules/vitalia/crm/ -v` | PASS — 204 tests |
| `pytest tests/architecture/ -v` | PASS — 265 tests |
| `pytest tests/modules/vitalia/crm/test_patient_consent_service.py` | PASS — 14 tests |
| `pytest tests/modules/vitalia/crm/api/test_consent_endpoints.py` | PASS — 14 tests |

## gherkin_coverage verification (from 06-tickets.yaml)

| Scenario | Test | Status |
|---|---|---|
| SC-02 marketing_opt_in_false_blocks_marketing_template | `test_patient_consent_service.py::TestPatientConsentServiceMarketingOptIn::test_marketing_opt_in_false_blocks_marketing_template` | PASS |
| SC-04 opt_out_cascades_cancel_pending_events | `test_patient_consent_service.py::TestPatientConsentServiceOptOut::test_opt_out_cascades_cancel_pending_events` | PASS |

## HIPAA-lite compliance

Per `vitalia/.claude/rules/hipaa-lite.md`:

1. **Dual filter**: All service methods pass `tenant_id + clinic_id` to repository. Repository validates both via `PhiRepositoryBase.validate_dual_filter()`.
2. **Audit log sync**: `audit_repo.write()` awaited before service method returns. Verified in `test_opt_out_writes_audit_log_sync` + `test_marketing_opt_in_writes_audit_log`.
3. **RBAC**: `@require_phi_access(roles=["admin_clinic"])` on opt_out; `@require_phi_access(roles=["doctor","nurse","admin_clinic"])` on marketing_opt_in.
4. **No PHI in responses**: `OptOutResponse` and `MarketingOptInResponse` expose only UUIDs + consent booleans + Spanish messages.
5. **Domain event**: `PatientOptedOut` carries only UUIDs (patient_id, tenant_id, clinic_id, triggered_by_user_id) — no PHI fields.

## Architecture decisions

- `PatientOptedOut` event defined in `crm/domain/events.py` (T-4's `fidelizacion/domain/events.py` can re-import or alias it when ready)
- Outbox `adapter_bus` import wrapped in `try/except ImportError` for dev environments without full core package
- Old `opt_out_patient` endpoint in `router.py` removed (superseded by `consent_endpoints.py`)
- Consent router included via `router.include_router(consent_router)` in the existing CRM router

## Skills Consulted (must_load enforcement v4.1)

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Anti-pattern checklist: SQLA 2.0, Pydantic v2, tenant isolation, audit log | Used raw SQL text() matching existing repo pattern; ConfigDict(from_attributes=True); validated dual filter in all repo methods |
| `backend-ddd.md` | DDD Inside-Out layering enforcement | Domain (pure Python) → Infrastructure (raw SQL) → Application (service) → API (thin); no business logic in routes |
| `tenant-isolation.md` | Every query filters tenant_id | validate_dual_filter() called in all repo methods; X-Tenant-ID + X-Clinic-ID both required on endpoints |
| `hipaa-lite.md` (vitalia overlay) | PHI dual filter + audit log + RBAC mandatory | Added clinic_id dual filter; sync audit write before response; @require_phi_access decorator on all service methods |
| `spanish-text.md` | Spanish neutro LatAm on user-facing strings | "El paciente ha sido registrado como excluido del marketing." — no voseo; uses tú-form |
| `anti-duplication.md` | Pre-write grep for existing patterns | Confirmed no mirror: PatientConsentService is new (not mirroring other brands); adapter_bus used from luana_core_events (not re-implemented) |
| `tdd-mandatory.md` | RED tests before GREEN implementation | Wrote 28 test cases across 2 files before any implementation; confirmed RED (ModuleNotFoundError) before GREEN |
| `auditor-self-fix-policy.md` | Understanding self-fix vs dev-team scope | N/A — no auditor findings yet |
| `tessl__fastapi` | Annotated deps, response_model, async patterns | response_model= on every route; Annotated[str, Header(alias="...")] for headers; async def throughout |
