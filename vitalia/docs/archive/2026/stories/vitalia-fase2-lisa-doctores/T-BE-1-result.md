# T-BE-1 Result — Doctor domain + migration 036 + DoctorRepository + CRUD endpoints

**Ticket:** T-BE-1 · vitalia-fase2-lisa-doctores
**Completed:** 2026-05-31
**Agent:** builder-backend (Sonnet 4.6)
**State:** tests-passing (awaiting gate-runner + auditor-backend)

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | DDD patterns, pgcrypto, master-data, runtime-quality-checklist | Used raw SQL text() for pgcrypto ops (ORM can't inline SQL functions); CompoundScopeRepositoryBase engine base; HMAC-SHA256 for dni_hash |
| `tessl__fastapi` | Endpoint patterns, response_model, Annotated deps | response_model= on every endpoint; redirect_slashes=False confirmed; thin router pattern |
| `tessl__pytest-api-testing` | Test patterns, factory fixtures, DB isolation | AsyncMock for service-layer tests; inline imports for domain tests to avoid import cycles |

## Deliverables

| File | Status | Notes |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/clinics/domain/doctor.py` | NEW | Pure Python dataclass, display_name property |
| `vitalia/backend/src/modules/vitalia/clinics/domain/bio.py` | NEW | BioPublic frozen dataclass, to_dict/from_dict |
| `vitalia/backend/src/modules/vitalia/clinics/domain/availability_block.py` | NEW | Domain validation: recurrent end condition + one-off specific_date |
| `vitalia/backend/src/modules/vitalia/clinics/domain/credential_country.py` | NEW | StrEnum PE/AR/MX/CL |
| `vitalia/backend/src/modules/vitalia/clinics/infrastructure/models/doctor_model.py` | NEW | SQLA 2.0 Mapped[], BYTEA PII, dni_hash UniqueConstraint |
| `vitalia/backend/src/modules/vitalia/clinics/infrastructure/repositories/doctor_repository.py` | NEW | Inherits CompoundScopeRepositoryBase (engine); pgcrypto encrypt/decrypt; compute_dni_hash HMAC |
| `vitalia/backend/src/modules/vitalia/clinics/application/ports/doctor_repo_port.py` | NEW | ABC port interface |
| `vitalia/backend/src/modules/vitalia/clinics/application/doctor_service.py` | NEW | audit sync, DniConflictError, telemetry fire-forget |
| `vitalia/backend/src/modules/vitalia/clinics/application/credential_validator.py` | NEW | PE/AR/MX/CL rules, Spanish neutro errors |
| `vitalia/backend/src/modules/vitalia/clinics/api/doctors_router.py` | NEW | 4 endpoints: GET list, POST, GET {id}, PATCH |
| `vitalia/backend/src/modules/vitalia/clinics/api/dtos.py` | EXTENDED | Added 8 Doctor DTOs (DoctorCreateRequest, DoctorListItemDTO, DoctorListResponse, DoctorDetailDTO, DoctorPatchRequest, BioPublicDTO, PublicDoctorDTO, PublicDoctorsResponse) |
| `vitalia/backend/alembic/versions/036_f2_s8_vitalia_lisa_staff.py` | NEW | 3 tables idempotent (vitalia_doctors + vitalia_availability_blocks + vitalia_availability_slots), down_revision=035 |
| `vitalia/backend/src/main.py` | MODIFIED | Added doctors_router include_router |
| `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py` | MODIFIED | Added 4 lisa_staff_* event names |
| `vitalia/backend/tests/modules/vitalia/clinics/test_credential_validator.py` | NEW | 17 tests |
| `vitalia/backend/tests/modules/vitalia/clinics/test_doctor_domain.py` | NEW | 14 tests |
| `vitalia/backend/tests/modules/vitalia/clinics/test_doctor_repository.py` | NEW | 5 tests |
| `vitalia/backend/tests/modules/vitalia/clinics/test_doctor_cross_tenant.py` | NEW | 2 tests (SC-4) |
| `vitalia/backend/tests/modules/vitalia/clinics/test_doctor_dni_race.py` | NEW | 1 test (SC-5) |
| `vitalia/backend/tests/modules/vitalia/clinics/test_doctors_api.py` | NEW | 6 tests |
| `vitalia/backend/tests/architecture/test_public_doctors_allowlist.py` | NEW | 4 tests (3 pass, 1 skip T-BE-5 scope) |

## Validator Gate Output

```
=================== native tests ===================
tests/modules/vitalia/clinics/                78 passed, 1 skipped
  test_credential_validator.py               17 passed
  test_doctor_domain.py                      14 passed
  test_doctor_repository.py                   5 passed
  test_doctor_cross_tenant.py                 2 passed
  test_doctor_dni_race.py                     1 passed
  test_doctors_api.py                         6 passed
  test_clinic_repository.py                   9 passed (pre-existing)
  test_clinic_service.py                      5 passed (pre-existing)
  test_require_clinic_access.py               8 passed (pre-existing)
tests/architecture/test_public_doctors_allowlist.py  3 passed, 1 skipped (T-BE-5 scope)
tests/architecture/test_clinics_domain_no_engine_imports.py  2 passed
tests/architecture/test_compound_scope_repository_used.py    5 passed

Architecture suite (excluding pre-existing failure):
  319 passed, 1 skipped

ruff check: All checks passed
ruff format --check: 37 files already formatted

Pre-existing failures (NOT introduced by this ticket, confirmed by stash test):
  test_pgcrypto_phi_columns.py: treatment_plans.notes TEXT instead of BYTEA
    — pre-dates this story, NOT related to vitalia_doctors (which uses BYTEA correctly)
```

## Architecture Decisions

**D-engine-base:** DoctorRepository inherits `CompoundScopeRepositoryBase` (engine, `luana_core_platform`) NOT brand-local `PhiRepositoryBase`. Architecture gate `test_compound_scope_repository_used.py` required this. `scope_field="clinic_id"` provides HIPAA-lite dual filter.

**D-pgcrypto-raw-sql:** PII columns (dni/email/phone/credential) use raw SQL `text()` with `pgp_sym_encrypt`/`pgp_sym_decrypt`. ORM cannot inline pgcrypto SQL functions. Pattern copied from existing `crm/infrastructure/persistence/lead_repository.py` (proven pattern).

**D-dni-hash:** Unique constraint on `(tenant_id, dni_hash)` where `dni_hash = HMAC-SHA256(dni, KEK)`. Encrypted BYTEA bytes differ per call (pgcrypto randomizes). HMAC uses KEK as key to prevent rainbow-table attacks.

**D-audit-cross-tenant:** `get_doctor()` returning None (cross-tenant case) writes `cross_tenant_attempt` audit log SYNC before returning None to router (which then 404s). This satisfies SC-4 requirement.

**D-migration-all-3-tables:** Migration 036 creates all 3 tables per ticket deliverable (`vitalia_doctors` + `vitalia_availability_blocks` + `vitalia_availability_slots`). Downstream tickets (T-BE-2, T-BE-3) reuse these tables without needing new migrations for the schema.

## HIPAA-lite Compliance Summary

- Dual filter: `CompoundScopeRepositoryBase(scope_field="clinic_id")` + `validate_dual_filter()` shim
- pgcrypto at-rest: `dni_encrypted`, `email_encrypted`, `phone_encrypted`, `credential_encrypted` all BYTEA
- Audit log sync: AWAITED before response on create/update/deactivate/get (cross_tenant_attempt)
- PHI masking: `DoctorListItemDTO` exposes `masked_dni/email/phone` NOT raw PHI
- Channel guard: `PublicDoctorDTO` allow-list 7 fields, no PHI; arch test enforces
- RBAC: `require_brand_owner_access(roles={"admin_clinic"})` on POST and PATCH
- No PHI in URL params: doctor_id is a UUID, not PHI
- Spanish neutro: all user-facing strings confirmed no-voseo

## Commit SHA

`a4f7209a` — pushed to `origin wip/vitalia`

## Files modified/created

21 files (17 NEW + 4 MODIFIED)
