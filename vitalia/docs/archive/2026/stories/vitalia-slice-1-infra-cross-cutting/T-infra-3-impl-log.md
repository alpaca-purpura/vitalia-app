# T-infra-3 Implementation Log — PHI Compliance Infrastructure

**Ticket:** T-infra-3
**Story:** vitalia-slice-1-infra-cross-cutting (vitalia-ux-discovery)
**Branch:** wip/vitalia-slice-1-shipping
**Model:** Sonnet (production_code: false)
**Date:** 2026-05-18

## § Skills Consulted

| Skill | Invoked | Reason | Decision Taken |
|---|---|---|---|
| `backend-expert` | Yes — mandatory | TDD, DDD layers, SQLA 2.0, tenant isolation patterns | Used `runtime-quality-checklist.md`: async def, ConfigDict extra=forbid, no datetime.utcnow(), SQLA 2.0 select(), structlog only |
| `tessl__fastapi` | Yes — mandatory | Annotated deps, response_model, async lifespan | Confirmed decorator pattern for RBAC is correct; no FastAPI imports in domain layer |
| `tessl__pytest-api-testing` | Yes — mandatory | httpx AsyncClient, fixture scoping, factory fixtures | Used AsyncMock + MagicMock pattern for session mocking; @pytest.mark.asyncio for async tests |
| `tessl__graceful-degradation` | Not invoked | No external HTTP calls in this ticket (pure domain + shared layer) | N/A |
| `brand-expert` / `offer-expert` / `metrics-expert` | Not invoked | T-infra-3 touches _shared/ + compliance/ only (no brand/offer/analytics modules) | N/A |

## § Implementation Summary

### Files Created

**Production (13 files):**

1. `vitalia/backend/src/modules/vitalia/_shared/__init__.py` — marker
2. `vitalia/backend/src/modules/vitalia/_shared/repositories/__init__.py` — marker
3. `vitalia/backend/src/modules/vitalia/_shared/repositories/phi_repository.py` — `PhiRepositoryBase` ABC with `validate_dual_filter()`, `MissingClinicFilterError`
4. `vitalia/backend/src/modules/vitalia/_shared/repositories/audit_log_repository.py` — `AuditLogRepository.write()` async + `AuditLogEntry` dataclass
5. `vitalia/backend/src/modules/vitalia/_shared/encryption/__init__.py` — marker
6. `vitalia/backend/src/modules/vitalia/_shared/encryption/kek_client.py` — `KEKClient` env-var based for Slice 1
7. `vitalia/backend/src/modules/vitalia/_shared/auth/__init__.py` — marker
8. `vitalia/backend/src/modules/vitalia/_shared/auth/rbac.py` — `@require_phi_access` decorator + `PHIAccessDeniedError`
9. `vitalia/backend/src/modules/vitalia/compliance/__init__.py` — marker
10. `vitalia/backend/src/modules/vitalia/compliance/domain/__init__.py` — marker
11. `vitalia/backend/src/modules/vitalia/compliance/domain/phi_fields.py` — 22 PHI fields SSoT
12. `vitalia/backend/src/modules/vitalia/compliance/application/__init__.py` — marker
13. `vitalia/backend/src/modules/vitalia/compliance/application/compliance_service_adapter.py` — `VitaliaComplianceAdapter` + `BlockedChannelError` + `sanitize_phi_payload()`

**Tests (7 files):**

14. `vitalia/backend/tests/modules/__init__.py` — marker (already existed from prior T)
15. `vitalia/backend/tests/modules/vitalia/__init__.py` — marker (already existed)
16. `vitalia/backend/tests/modules/vitalia/compliance/__init__.py` — marker
17. `vitalia/backend/tests/modules/vitalia/compliance/test_phi_repository.py` — 6 tests
18. `vitalia/backend/tests/modules/vitalia/compliance/test_audit_log_repository.py` — 5 tests
19. `vitalia/backend/tests/modules/vitalia/compliance/test_rbac.py` — 6 tests
20. `vitalia/backend/tests/modules/vitalia/compliance/test_compliance_service_adapter.py` — 11 tests

**Architecture fitness tests (3 new):**

21. `vitalia/backend/tests/architecture/test_phi_dual_filter.py` — 4 tests (AST scan PHI repos)
22. `vitalia/backend/tests/architecture/test_audit_log_sync_write.py` — 6 tests (sync write enforcement)
23. `vitalia/backend/tests/architecture/test_pgcrypto_phi_columns.py` — 7 tests (BYTEA column enforcement)

## § Architecture Decisions

### PhiRepositoryBase design
- Pure ABC with `validate_dual_filter()` non-abstract method — enforces dual filter at call site
- `MissingClinicFilterError` raised (not ValueError) for clinic_id — enables precise exception handling
- `object | None` return type on abstract methods — concrete subclasses narrow to domain type
- NO SQLA imports in base — stays domain-pure per DDD Inside-Out

### AuditLogRepository write() design
- Raw SQL `text()` insert (not ORM model) — avoids infrastructure import in _shared/ layer
- `await session.execute()` + `await session.flush()` — sync, never fire-forget
- `AuditLogEntry` as `@dataclass` (not Pydantic) — pure value object, no framework deps
- `occurred_at` defaults to `datetime.now(tz=timezone.utc)` — satisfies DateTime(timezone=True) rule

### @require_phi_access decorator
- Accepts `audit_repo: Any | None` — enables DI without importing concrete repo (test-friendly)
- Writes audit events on BOTH grant AND denial (per hipaa-lite.md test requirement #2)
- Swallows audit write exceptions with structlog warning — audit failure MUST NOT block PHI response
- `PHIAccessDeniedError` contains user_role + required_roles for precise error messages

### sanitize_phi_payload
- Delegates to engine `luana_core_observability.recording.sanitization.sanitize_payload` first
- Then applies vitalia-specific 22-field redaction (top-level + nested patient.*)
- Engine import wrapped in try/except ImportError — graceful fallback for isolated test environments
- Returns new dict (does NOT mutate input) — safety for call sites

### VitaliaComplianceAdapter channel guard
- Conservative: any channel in `BLOCKED_PHI_CHANNELS` raises `BlockedChannelError` regardless of content
- Channel comparison is `.lower()` normalized for case-insensitive matching
- `BlockedChannelError` includes channel name + tenant_id (for audit trail)

### KEKClient
- Slice 1: env-var `VITALIA_PHI_KEK` (32+ byte hex = 256-bit AES)
- Cached after first read (rotation via `invalidate_cache()`)
- `from_env()` factory classmethod for DI injection in main.py
- Minimum key length validation (32 bytes) raises `KEKConfigurationError` with helpful message

## § Anti-duplication Grep Evidence

```bash
# grep luana_core_observability/sanitization — IMPORTED not mirrored
grep -rn "sanitize_payload" vitalia/backend/src/modules/vitalia/compliance/application/compliance_service_adapter.py
# → imports from luana_core_observability.recording.sanitization

# grep luana_core_compliance — NOT imported (engine ComplianceService API doesn't fit vitalia use case)
# VitaliaComplianceAdapter owns channel guard logic directly per 03-arch-be.md
```

## § Cross-module Reads

None. T-infra-3 is a cross-cutting infrastructure module only. No reads from `copilot/` or `sales_agent/`.

## § Default Flip Pre-Audit

Not applicable — T-infra-3 does not flip any feature flags.

## § Test Results

```
vitalia/backend/tests/modules/vitalia/compliance/  — 28 tests PASS
vitalia/backend/tests/architecture/ (3 new tests)  — 17 tests PASS
vitalia/backend/tests/architecture/ (full suite)   — 184 tests PASS
vitalia/backend/tests/ (full suite)                — 1012 passed, 46 skipped
```

All skips are integration tests (`@pytest.mark.integration`) requiring live Postgres — not a T-infra-3 concern.

## § Quality Gate Results

- `ruff check` — PASS (0 errors)
- `ruff format --check` — PASS (0 files to reformat)
- `pytest vitalia/backend/tests/modules/vitalia/compliance/` — 28/28 PASS
- `pytest vitalia/backend/tests/architecture/` — 184/184 PASS
