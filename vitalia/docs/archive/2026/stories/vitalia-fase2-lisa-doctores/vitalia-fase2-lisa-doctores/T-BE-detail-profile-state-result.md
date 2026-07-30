# T-BE-detail-profile-state — Result

**Ticket:** gap final T-BE-pagina-publica — GET detail `/doctors/{id}` profileState null + publicProfile/publicSlug missing
**State:** tests-passing
**Files touched:** 3

## Summary

The GET detail endpoint was returning `profileState: null` always because `_to_detail_dto` never populated `profile_state`, `public_profile`, or `public_slug`. The fix is scoped to the API layer (dtos.py + doctors_router.py) with no DB migrations required.

## Changes

### 1. `vitalia/backend/src/modules/vitalia/clinics/api/dtos.py`

Added to `DoctorDetailDTO` (lines after `bio_files`):
- `public_profile: PublicDoctorProfileDTO | None = None`
- `public_slug: str | None = None`

Existing `profile_state: ProfileStateDTO | None = None` was already present.

Docstring block documents the RN-D3D-4 limitation: material_new tracks bio_files.uploaded_at only; notes/links changes are best-effort (no dedicated timestamp).

`ProfileStateDTO` already had `alias_generator=to_camel` — aliases `generatedAt`, `materialNew`, `materialNewCount` were correct.

### 2. `vitalia/backend/src/modules/vitalia/clinics/api/doctors_router.py`

**New helper `_compute_profile_state(doctor, bio_files)`:**
- Returns `None` when `bio_generated_at` is None (never generated)
- Counts files with `uploaded_at > bio_generated_at` → `material_new_count`
- `material_new = count > 0`

**Updated `_to_detail_dto(doctor, bio_files=None)`:**
- Added `bio_files` parameter (defaults to `[]` for POST create compatibility)
- Now calls `_to_public_profile_dto(doctor)` → `public_profile_dto`
- Now calls `_compute_profile_state(doctor, bio_files)` → `profile_state_dto`
- Maps `public_profile`, `public_slug`, `profile_state` into returned DTO

**Updated `get_doctor` handler:**
- Loads bio_files via `_build_bio_file_service(db).list_files(...)` after doctor is found
- Passes `bio_files` to `_to_detail_dto`

**Imported `ProfileStateDTO`** into router (was missing from import block).

### 3. `vitalia/backend/tests/modules/vitalia/clinics/test_detail_profile_state.py` (NEW)

7 TDD tests (RED first, then GREEN):
1. `test_doctor_detail_dto_has_public_profile_field` — structural gate
2. `test_doctor_detail_dto_has_public_slug_field` — structural gate
3. `test_profile_state_dto_generated_at_alias_is_camel` — camelCase wire contract
4. `test_get_detail_after_generation_profile_state_populated` — core happy path
5. `test_get_detail_after_file_upload_material_new_true` — material_new=True
6. `test_get_detail_no_generation_with_material_profile_state_none` — profileState=None when never generated
7. `test_get_detail_public_profile_camel_case_in_response` — publicProfile + publicSlug camelCase

## Limitation documented (RN-D3D-4 partial)

Notes/links changes do NOT bump `material_new` — there is no `bio_inputs_last_updated` timestamp dedicated to those fields. Only `bio_files.uploaded_at` comparisons are used. This is documented in:
- `DoctorDetailDTO` docstring block in dtos.py
- `_compute_profile_state` docstring in doctors_router.py

## Tests

```
# clinics suite (includes 7 new tests)
vitalia/backend/tests/modules/vitalia/clinics/ → 424 passed (was 417)

# arch (pre-existing test_pgcrypto_phi_columns failure unrelated to this PR)
vitalia/backend/tests/architecture/ → 339 passed (excluding pre-existing failure)

# lint / format
ruff check → All checks passed
ruff format → 8 files already formatted
```

## Pre-existing failure note

`tests/architecture/test_pgcrypto_phi_columns.py::test_no_phi_column_uses_text_or_varchar_unencrypted` — `treatment_plans.notes TEXT` — pre-dates this task (last touched `9a250f1f fix(vitalia/arch): regex false-positive en pgcrypto PHI gate`). NOT introduced by this PR.

## Scope respected

- Did NOT touch `generate-profile` endpoint (working)
- Did NOT touch public router
- Did NOT touch FE
- `patch_doctor` left calling `_to_detail_dto(doctor)` without bio_files — acceptable (PATCH returns a snapshot without material_new computation, consistent with pre-existing behavior)
