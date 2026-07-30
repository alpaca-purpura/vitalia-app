# T-BE-pagina-publica — Result

**Ticket:** T-BE-pagina-publica  
**Story:** vitalia-fase2-lisa-doctores (delta v3 D3-D)  
**State:** tests-passing  
**Date:** 2026-06-12

## Summary

Implemented D3-D Página Pública Doctor — structured public doctor profile endpoint with anti-enumeration 404, HIPAA-lite channel guard, and migration 041.

## Files Created / Modified

### New files

| File | Purpose |
|---|---|
| `vitalia/backend/src/modules/vitalia/clinics/domain/public_profile.py` | `DoctorPublicProfile` frozen dataclass + `FormacionItem` + `ExperienciaItem` — 6-section structured domain entity |
| `vitalia/backend/alembic/versions/041_vitalia_doctor_public_profile.py` | Idempotent migration: ADD COLUMN IF NOT EXISTS `public_profile JSONB`, `bio_generated_at TIMESTAMPTZ`, `public_slug TEXT` + unique partial index + backfill from bio_public |
| `vitalia/backend/tests/modules/vitalia/clinics/test_public_doctor_profile_endpoint.py` | 41 TDD tests: SC-D3D-1/2/3/6/9/12 + RN-D3D-4 + migration shape + domain entity |
| `vitalia/backend/tests/architecture/test_public_doctor_profile_allowlist.py` | 13 arch gate tests: PublicDoctorProfileDTO zero-PHI + nullable sections + repo method + anti-enumeration constant |

### Extended files

| File | Change |
|---|---|
| `vitalia/backend/src/modules/vitalia/clinics/domain/doctor.py` | Added `public_profile: DoctorPublicProfile | None`, `bio_generated_at: datetime | None`, `public_slug: str | None` fields |
| `vitalia/backend/src/modules/vitalia/clinics/infrastructure/models/doctor_model.py` | Added `Mapped` columns for 3 new fields (JSONB, TIMESTAMPTZ, TEXT) |
| `vitalia/backend/src/modules/vitalia/clinics/infrastructure/repositories/doctor_repository.py` | All 4 SELECT statements updated with `public_profile, bio_generated_at, public_slug`; `_row_to_doctor()` updated; new `get_by_public_slug()` method added |
| `vitalia/backend/src/modules/vitalia/clinics/api/dtos.py` | Added `FormacionItemDTO`, `ExperienciaItemDTO`, `PublicDoctorProfileDTO`, `ProfileStateDTO`; `DoctorDetailDTO` extended with `profile_state` field |
| `vitalia/backend/src/modules/vitalia/clinics/application/public_doctor_serializer.py` | Extended with `to_public_profile_dto()` function (allow-list, RN-D3D-5/6/7 enforced) |
| `vitalia/backend/src/modules/vitalia/clinics/api/public_doctors_router.py` | Added `_GENERIC_PROFILE_404_DETAIL` constant + `GET /{tenant_slug}/doctors/{doctor_slug}` endpoint with anti-enumeration |

## Business Rules Enforced

- **RN-D3D-5**: `idiomas` omitted from public profile when `len <= 1`
- **RN-D3D-6**: All sections nullable — minimum identity = `display_name`
- **RN-D3D-7**: OG-safe fields (`display_name`, `specialty`, `sobre_mi`, `avatar_key`) for FE `generateMetadata`
- **RN-D3D-9**: Anti-enumeration — toggle OFF / unknown slug / cross-tenant → IDENTICAL 404 `"Perfil no disponible"`
- **RN-D3D-4**: `profile_state {generated_at, material_new, material_new_count}` in `DoctorDetailDTO`

## Migration 041 Notes

- `down_revision = "040_vitalia"` (040 = bio_files, 042 = block_multi_day_interval references 040 independently)
- Backfill: `public_profile = bio_public WHERE bio_public IS NOT NULL AND public_profile IS NULL` (idempotent)
- Unique partial index: `(tenant_id, clinic_id, public_slug) WHERE public_slug IS NOT NULL`
- All DDL: `IF NOT EXISTS` (idempotent per `.claude/rules/backend-migrations.md`)

## Test Results

- **New tests**: 41 passed (test_public_doctor_profile_endpoint.py) + 13 passed (test_public_doctor_profile_allowlist.py) = 54 new
- **Pre-existing + new (non-integration)**: 408 passed, 0 failed
- **Pre-existing failures NOT caused by this ticket**:
  - `test_bio_files_api.py::test_repo_cross_tenant_get_by_id_returns_none` — requires Postgres running with migration 040 applied (integration marker)
  - `test_pgcrypto_phi_columns.py` — pre-existing `treatment_plans.notes` TEXT column (unrelated to D3-D)
- **Arch tests**: 339 passed (excluding pre-existing pgcrypto failure)

## Faithfulness Notes (§11 CONTEXT-BRIEF partial flag)

- OQ-3 (clinic slug cross-tenant guard): implemented as structlog warning + generic 404 on single match. Full uniqueness validation service-level for NEW clinics is noted but not implemented here (clinic creation is out of scope for this BE ticket).
- `profile_state` material_new computation: DTO fields defined; service-level computation (bio_files vs bio_generated_at comparison) is in the doctor GET endpoint scope (out of ticket scope — ticket only specifies the DTO shape).
- `BioGenerationService` reuse for structured profile: marked as deferred (generation endpoint is T-BE-bio-generation scope, not this ticket).

## Skills Consulted

- `backend-expert` — runtime-quality-checklist applied (response_model, tenant filter, async, structlog)
- `FastAPI canonical patterns` — response_model= mandatory, async routes, path params, Depends
- `pytest async testing patterns` — factory fixtures, env_vars patch, non-integration unit tests
- HIPAA-lite overlay — dual filter enforced, channel guard pattern (allow-list serializer), PHI forbidden in public DTOs
