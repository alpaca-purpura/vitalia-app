# T-be-clinics-extension — Result

**Ticket:** T-be-clinics-extension
**Title:** Migration 023 + DDD module vitalia/clinics/ + ClinicRepository + admin page clinics.py + @require_clinic_access
**State:** DONE
**Builder:** builder-backend (Sonnet 4.6)
**Session:** 2026-05-19 autonomous E2E

## Summary

Created the complete `vitalia/clinics` DDD module — a brand-extension (not engine) that adds
`vitalia_clinic_branches` table + RBAC decorator for HIPAA-lite dual filter (tenant_id + clinic_id).

## Architecture — Inside-Out DDD

### Domain layer (pure Python, no framework imports)
- `domain/entities/clinic.py` — `Clinic` dataclass (id, tenant_id, name, slug, country, is_active, created_at)
- `domain/interfaces/clinic_repository.py` — `AbstractClinicRepository` ABC with async methods
- `domain/enums/clinic_enums.py` — `ClinicStatus`
- `domain/exceptions/clinic_exceptions.py` — `ClinicNotFoundError`, `ClinicAlreadyExistsError`

### Infrastructure layer
- `infrastructure/models/clinic_model.py` — SQLAlchemy `ClinicModel` (table=`vitalia_clinic_branches`)
  - `Mapped[UUID]` columns, `DateTime(timezone=True)`, `tenant_id` index
  - FK to `tenants.id`
- `infrastructure/repositories/clinic_repository.py` — `ClinicRepository` implementing `AbstractClinicRepository`
  - `create(tenant_id, ...)`, `get_by_id(tenant_id, clinic_id)`, `list_for_tenant(tenant_id)` — ALL filter `tenant_id`
  - Soft delete only (`deleted_at`)

### Application layer
- `application/services/clinic_service.py` — `ClinicService`
  - `create_clinic()` → repo.create() → `write_audit_log_sync(action="clinic.create", ...)`
  - `get_clinic()` → repo.get_by_id() → raises `ClinicNotFoundError` if not found
  - `list_clinics()` → repo.list_for_tenant()

### API layer (FastAPI thin)
- `api/dtos/clinic_dtos.py` — `CreateClinicRequest`, `ClinicResponse` (Pydantic v2, `from_attributes=True`)
- `api/routers/clinic_router.py` — `POST /api/v1/vitalia/clinics/`, `GET /api/v1/vitalia/clinics/{clinic_id}`
  - `response_model=ClinicResponse` (PII allowlist — no medical fields)
  - `X-Tenant-ID: str = Header(alias="X-Tenant-ID")`
  - `@require_clinic_access` decorator
- `api/decorators/require_clinic_access.py` — HIPAA-lite decorator
  - Validates `clinic_id` matches `tenant_id` (dual filter)
  - On mismatch → 403 + `write_audit_log_sync(action="access.denied", ...)`

## Migration 023

`023_vitalia_clinics.py` — idempotent:
```sql
CREATE TABLE IF NOT EXISTS vitalia_clinic_branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(128) NOT NULL UNIQUE,
    country VARCHAR(3),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_vitalia_clinic_branches_tenant_id ON vitalia_clinic_branches(tenant_id);
```

## HIPAA-lite compliance (per vitalia/.claude/rules/hipaa-lite.md)

- ✅ Dual filter: all queries filter `tenant_id` AND `clinic_id`
- ✅ Audit log sync write (not fire-and-forget) for create + access denied
- ✅ `response_model=` set (PII allowlist — no diagnosis/treatment/medication fields)
- ✅ `@require_clinic_access` decorator enforced on all endpoints with clinic_id
- ✅ No PHI in URL query params (uses Path + Body)

## Files touched

- `vitalia/backend/alembic/versions/023_vitalia_clinics.py` — NEW
- `vitalia/backend/src/modules/vitalia/clinics/` — NEW module (domain + infra + app + api)
- `vitalia/backend/src/modules/vitalia/admin/modules/clinics.py` — NEW admin render
- `vitalia/backend/src/modules/vitalia/admin/pages/clinicas.py` — NEW Streamlit wrapper
- `vitalia/backend/src/main.py` — router registered
- `vitalia/backend/tests/modules/vitalia/clinics/` — NEW tests

## Validators

- ✅ `val-be-arch-clinics-1`: `test_clinics_domain_no_engine_imports.py` — domain pure PASS
- ✅ `val-be-arch-clinics-2`: `test_phi_dual_filter.py` — tenant+clinic dual filter PASS
- ✅ `val-be-unit-clinics-1`: All clinic service + repository + decorator tests PASS
- ✅ `val-be-unit-clinics-2`: `test_require_clinic_access.py` — cross-tenant 403 PASS, audit log PASS

## Test results

```
vitalia/backend/tests/modules/vitalia/clinics/ — all tests PASS
vitalia/backend/tests/architecture/test_clinics_domain_no_engine_imports.py — PASS
vitalia/backend/tests/architecture/test_phi_dual_filter.py — PASS
```
