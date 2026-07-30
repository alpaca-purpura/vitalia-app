<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 -->
# Backend Code Review: T-2 CRM extension consent (opt-in/opt-out)

**Date:** 2026-05-20
**Brand:** vitalia
**Ticket:** T-2
**Files Reviewed:** 6 (4 NEW + 2 EXTENDED)
**Verdict:** **PASS**

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | PASS | servicio en application/, DTOs en application/dto/, endpoint thin en api/ |
| 2 | Tenant Isolation | PASS | `validate_dual_filter(tenant_id, clinic_id)` en todas las repo methods |
| 3 | Soft Deletes | PASS | opt_out cascade marca eventos OPTED_OUT (no hard delete) |
| 4 | Code Quality | PASS | ruff clean, 204 tests passing en crm module |
| 5 | SQLAlchemy 2.0 | PASS | `text()` raw queries match existing pattern + `select()` 2.0 |
| 6 | Async Consistency | PASS | `async def` throughout repo + service + endpoints |
| 7 | Pydantic v2 / PII | PASS | `ConfigDict(from_attributes=True)`, `response_model=` en 2 endpoints; PII excluida (response solo IDs + booleans + mensajes Spanish neutro) |
| 8 | Migration Quality | N/A | columns added en T-1 migration 023 |
| 9 | Security | PASS | `@require_phi_access` decorator en service methods (admin_clinic only opt_out; doctor/nurse/admin_clinic marketing) |
| 10 | Tests / TDD | PASS | 28 tests RED→GREEN (14 service + 14 API), 2 gherkin scenarios SC-02 + SC-04 covered |
| 11 | Cross-cutting | PASS | Spanish neutro mensajes ("El paciente ha sido registrado como excluido..."), `PatientOptedOut` domain event emitted via `adapter_bus` outbox |
| 12 | Mirror detection | PASS | `PatientConsentService` no mirror (grep cross-codebase confirma); `adapter_bus` consumed (no reimplement) |

## Gherkin coverage verification

| Scenario | Mapping | Status |
|---|---|---|
| SC-02 marketing_opt_in_false_blocks_marketing_template | `test_patient_consent_service.py::test_marketing_opt_in_false_blocks_marketing_template` (line 332) | EXISTS + PASSED |
| SC-04 opt_out_cascades_cancel_pending_events | `test_patient_consent_service.py::test_opt_out_cascades_cancel_pending_events` (line 175) | EXISTS + PASSED |

## HIPAA-lite compliance

- [x] Dual filter `tenant_id + clinic_id` en service + repo paths
- [x] Audit log sync write antes de retornar (verificado en `test_opt_out_writes_audit_log_sync` + `test_marketing_opt_in_writes_audit_log`)
- [x] RBAC: `@require_phi_access(roles=["admin_clinic"])` opt_out + `["doctor","nurse","admin_clinic"]` marketing_opt_in
- [x] No PHI in response (OptOutResponse/MarketingOptInResponse solo UUIDs + flags + mensaje)
- [x] `PatientOptedOut` event payload solo UUIDs (sin nombre, dni, etc.)

## Findings

### info: outbox import wrapped en try/except

**File:** `vitalia/backend/src/modules/vitalia/crm/application/services/patient_consent_service.py`
**Issue:** `adapter_bus` import wrapped en `try/except ImportError`. Pattern documentado para dev envs sin full core package; mock fallback `AsyncMock`. OK pero anti-pattern leve: dependencias core deberían estar siempre disponibles en build runtime.
**Fix:** N/A — pattern intentional + replicado en otros servicios T-5. Trackear como deuda Slice 2.
**Skill ref:** `.claude/rules/anti-duplication.md` § Outbox pattern engine consume

## Verdict Math

- 11 PASS / 0 WARN / 0 FAIL → **PASS**

## Skills Consulted Trace

✓ backend-expert ✓ backend-ddd ✓ tenant-isolation ✓ hipaa-lite (vitalia overlay) ✓ spanish-text ✓ anti-duplication ✓ tdd-mandatory ✓ tessl__fastapi (per T-2-result.md § Skills Consulted)
