# T-infra-9 Result — IAM + CRM modules Slice 1 scaffold

**Ticket:** T-infra-9
**Story:** vitalia-slice-1-infra-cross-cutting
**Branch:** wip/vitalia-slice-1-shipping
**Status:** tests-passing

## Summary

Implemented IAM + CRM modules for Vitalia (Slice 1 scaffold) following TDD Inside-Out pattern. All 64 new tests pass alongside the full suite (1125/1125 pass, 54 skipped — integration markers require live DB).

## Files delivered

### IAM module — 9 source files

| File | Description |
|---|---|
| `iam/__init__.py` | Module init |
| `iam/domain/__init__.py` | Domain layer init |
| `iam/domain/role.py` | `VitaliaRole` enum (7 roles) + `PHI_ALLOWED_ROLES` frozenset (3 roles) + `is_phi_allowed()` |
| `iam/domain/user.py` | `User` frozen dataclass — tenant_id/clinic_id/role/email/name |
| `iam/infrastructure/__init__.py` | Infrastructure layer init |
| `iam/infrastructure/clerk_jwt_decoder.py` | `ClerkJwtDecoder` stub (Slice 1) + `ClerkJwtPayload` + `JwtDecodeError` |
| `iam/application/__init__.py` | Application layer init |
| `iam/application/services/__init__.py` | Services init |
| `iam/application/services/clinic_resolver.py` | `ClinicResolver` + `ClinicContext` + `MissingAuthHeaderError` |
| `iam/api/__init__.py` | API layer init |
| `iam/api/router.py` | `GET /api/v1/iam/me` — `MeResponse` with PII allowlist + stub auth |

### CRM module — 14 source files

| File | Description |
|---|---|
| `crm/__init__.py` | Module init |
| `crm/domain/__init__.py` | Domain layer init |
| `crm/domain/patient.py` | `Patient` dataclass — PHI entity with dual filter fields |
| `crm/domain/lead.py` | `Lead` dataclass — non-PHI marketing prospect |
| `crm/infrastructure/__init__.py` | Infrastructure layer init |
| `crm/infrastructure/persistence/__init__.py` | Persistence layer init |
| `crm/infrastructure/persistence/patient_repository.py` | `PatientRepository` extends `PhiRepositoryBase` — dual filter + audit log on every read/write |
| `crm/infrastructure/persistence/lead_repository.py` | `LeadRepository` (NOT PhiRepositoryBase) — single tenant_id filter |
| `crm/application/__init__.py` | Application layer init |
| `crm/application/services/__init__.py` | Services init |
| `crm/application/services/patient_service.py` | `PatientService` — `get_by_id` + `update` + `opt_out` gated by `@require_phi_access` |
| `crm/application/services/lead_service.py` | `LeadService` — `get_by_id` (no RBAC restriction) |
| `crm/application/dto/__init__.py` | DTO init |
| `crm/application/dto/patient_dto.py` | `PatientResponse` + `PatientPatchRequest` + `OptOutRequest` + `OptOutResponse` |
| `crm/application/dto/lead_dto.py` | `LeadResponse` |
| `crm/api/__init__.py` | API layer init |
| `crm/api/router.py` | 4 endpoints: GET/PATCH patients + POST opt-out + GET leads |

### Test files — 8 files / 64 tests

| File | Tests |
|---|---|
| `tests/modules/vitalia/iam/__init__.py` | — |
| `tests/modules/vitalia/iam/test_role.py` | 24 — VitaliaRole values, PHI_ALLOWED_ROLES cardinality, is_phi_allowed() |
| `tests/modules/vitalia/iam/test_clerk_jwt_decoder.py` | 7 — stub decode, JwtDecodeError paths |
| `tests/modules/vitalia/iam/test_clinic_resolver.py` | 6 — ClinicContext shape, resolve flow, MissingAuthHeaderError, UUID conversion |
| `tests/modules/vitalia/iam/test_iam_api.py` | 5 — GET /iam/me status codes, role/tenant/clinic_id in response, PII allowlist |
| `tests/modules/vitalia/crm/__init__.py` | — |
| `tests/modules/vitalia/crm/test_patient_repository.py` | 7 — PhiRepositoryBase inheritance, dual filter enforcement, audit_repo constructor, opt_out async |
| `tests/modules/vitalia/crm/test_lead_repository.py` | 4 — NOT PhiRepositoryBase, get_by_id async, session constructor, tenant_id required |
| `tests/modules/vitalia/crm/test_patient_service.py` | 6 — RBAC blocks marketing/receptionist/patient, allows doctor/nurse/admin_clinic |
| `tests/modules/vitalia/crm/test_crm_api.py` | 7 — 403 for marketing/receptionist, 422 missing headers, leads accessible without clinic_id |

### Modified

- `vitalia/backend/src/main.py` — mounted `iam_router` at `/api/v1/iam` and `crm_router` at `/api/v1/crm`

## Quality gates (run natively)

| Gate | Result |
|---|---|
| `ruff check` — all new files | PASS (0 errors) |
| `ruff format --check` — all new files | PASS (0 reformats needed after auto-format) |
| Module tests (64 tests) | 64/64 PASS |
| Full suite (vitalia backend) | 1125/1125 PASS, 54 SKIP (integration markers — no live DB) |
| Architecture fitness (216 gates) | 216/216 PASS |

## HIPAA-lite constraints met

- PatientRepository extends PhiRepositoryBase — dual filter enforced on all methods
- AuditLogRepository.write() called sync (awaited) on every PHI read/write
- @require_phi_access decorator enforces 3-role allowlist (doctor/nurse/admin_clinic)
- opt_out restricted to admin_clinic only
- LeadRepository NOT a PhiRepositoryBase subclass (Lead is non-PHI per spec)
- All API routes have `response_model=` (PII gate + arch fitness)
- redirect_slashes=False preserved in main.py
- PHI not in URL params — patient_id in path only

## Skills consulted

| Skill | Invoked | Decision |
|---|---|---|
| `backend-expert` | Yes | Inside-Out DDD, SQLA 2.0, response_model mandatory, structlog, soft-delete |
| `tessl__fastapi` | Yes | Annotated headers, response_model=, redirect_slashes=False on app |
| `tessl__pytest-api-testing` | Yes | httpx AsyncClient + ASGITransport, anyio backend fixture |
| `tessl__graceful-degradation` | N/A | No external HTTP calls in Slice 1 stub |
| `brand-expert` | N/A | No brand studio module touched |
| `offer-expert` | N/A | No offer module touched |
| `metrics-expert` | N/A | No analytics module touched |

## Slice 1 design decisions

1. **ClerkJwtDecoder stub**: parses `stub:{tenant_id}:{clinic_id}:{role}:{user_id}` — real JWKS validation deferred to Slice 2 per spec
2. **No ORM model yet**: PatientRepository and LeadRepository use `text()` raw SQL — the tables don't exist yet (pending T-infra-5 migrations). Slice 2: replace with proper Mapped models
3. **Service uses AsyncMock repos in API layer**: Slice 1 scaffold — no live DB wiring. Slice 2: inject via FastAPI `Depends()`
4. **PatientService delegates to `_guarded` inner methods**: avoids kwargs shadowing issues with the `@require_phi_access` decorator

## Next steps for Slice 2

- Replace `text()` raw SQL with proper SQLAlchemy Mapped models (pending migrations)
- Wire real `AsyncSession` via FastAPI `Depends(get_async_session)` in both routers
- Replace stub `ClerkJwtDecoder` with production JWKS validation
- Add integration tests (marked `@pytest.mark.integration`) using live DB fixtures
