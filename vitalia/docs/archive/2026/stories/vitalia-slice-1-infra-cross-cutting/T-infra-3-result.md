# T-infra-3 Result — PHI Compliance Infrastructure

**State:** tests-passing
**Ticket:** T-infra-3
**Story:** vitalia-slice-1-infra-cross-cutting
**Branch:** wip/vitalia-slice-1-shipping
**Date:** 2026-05-18

## Deliverables

| Component | Path | Status |
|---|---|---|
| `PhiRepositoryBase` ABC | `_shared/repositories/phi_repository.py` | DONE |
| `MissingClinicFilterError` | `_shared/repositories/phi_repository.py` | DONE |
| `AuditLogRepository.write()` | `_shared/repositories/audit_log_repository.py` | DONE |
| `AuditLogEntry` dataclass | `_shared/repositories/audit_log_repository.py` | DONE |
| `KEKClient` (env-var Slice 1) | `_shared/encryption/kek_client.py` | DONE |
| `@require_phi_access` decorator | `_shared/auth/rbac.py` | DONE |
| `PHIAccessDeniedError` | `_shared/auth/rbac.py` | DONE |
| `phi_fields.py` SSoT (22 fields) | `compliance/domain/phi_fields.py` | DONE |
| `VitaliaComplianceAdapter` | `compliance/application/compliance_service_adapter.py` | DONE |
| `BlockedChannelError` | `compliance/application/compliance_service_adapter.py` | DONE |
| `sanitize_phi_payload()` | `compliance/application/compliance_service_adapter.py` | DONE |

## Arch Fitness Gates Added

| Test | Gate | Result |
|---|---|---|
| `test_phi_dual_filter.py` | PHI repos must filter by tenant_id + clinic_id | PASS |
| `test_audit_log_sync_write.py` | AuditLogRepository.write() is async, no fire-forget | PASS |
| `test_pgcrypto_phi_columns.py` | BYTEA columns confirmed + KEKClient exists | PASS |

## Test Coverage

- 28 compliance unit tests (phi_repository, audit_log_repository, rbac, compliance_service_adapter)
- 17 architecture fitness tests (3 new files + existing 167 passing)
- Full suite: 1012 passed, 46 skipped (integration — needs Postgres)

## HIPAA-lite Invariants Implemented

- [x] Dual filter `tenant_id + clinic_id` enforced in PhiRepositoryBase
- [x] Audit log sync write (awaited, never fire-forget)
- [x] Audit events on both PHI access GRANT and DENIAL
- [x] RBAC: `doctor`, `nurse`, `admin_clinic` allowed; all others blocked
- [x] Channel guard: `whatsapp_free`, `sms` blocked for PHI
- [x] 22 PHI fields redacted by `sanitize_phi_payload()`
- [x] KEK from env var only (never hardcoded)
- [x] BYTEA columns confirmed in migrations (from T-infra-1/2)

## Notes for PM

- `compliance/application/compliance_service_adapter.py` owns channel guard logic directly (engine `ComplianceService.check()` is lead-centric API, not message-centric — adapter bridges the gap without requiring engine modification)
- `sanitize_phi_payload()` gracefully falls back if `luana_core_observability` not available in test isolation
- KEKClient `from_env()` factory ready for DI injection in future API routes (T-api-* tickets)
- `AuditLogRepository.write()` uses raw SQL text() insert to avoid circular imports between `_shared/` layer and ORM model layer
