# T-FIX-bug7-round5-BE — Result

**Story:** vitalia-fase2-lisa-doctores  
**Ticket:** T-FIX-bug7-round5  
**Surface:** Backend — module clinics  
**Date:** 2026-06-14  

## Verdict

`tests-passing` — 455/455 clinics tests PASS · ruff clean · migration 044 applied + idempotent no-op confirmed.

## Features Implemented

### Feature #1 — Scoped DELETE for recurrent availability blocks

**Migration 044** (`vitalia/backend/alembic/versions/044_vitalia_availability_excluded_dates.py`):
- `ALTER TABLE vitalia_availability_blocks ADD COLUMN IF NOT EXISTS excluded_dates JSONB;`
- Idempotent up + down. Applied at `044_vitalia (head)`. Re-upgrade = no-op.

**Model** (`infrastructure/models/availability_block_model.py`):
- Added `excluded_dates: Mapped[list[str] | None]` with `PgJSON` type.

**Domain** (`domain/availability_block.py`):
- Added `excluded_dates: list[str] = field(default_factory=list)`.

**Projection** (`application/availability_projection_service.py`):
- Single helper `_is_excluded(occurrence_date, block)` — single source of truth.
- `_project_one_off()`: returns `[]` when specific_date is in excluded_dates.
- `_project_recurrent()`: filters occurrence dates removing those in excluded_dates.
- `occurrence_dates_in_range()`: both one_off and recurrent branches respect excluded_dates.

**Port** (`application/ports/availability_repo_port.py`):
- Added 4 abstract methods: `persist_excluded_dates()`, `retire_free_slots_on_date()`, `truncate_block()`, `retire_free_slots_from_date()`.

**Repository** (`infrastructure/repositories/availability_block_repository.py`):
- Implemented all 4 new port methods (dual filter tenant_id+clinic_id on all).
- `_model_to_block` + `_block_to_model` updated for `excluded_dates`.

**Service** (`application/availability_block_service.py`):
- `count_future_confirmed()` — DDD-clean delegation from service (router never accesses `svc._repo` directly).
- `exclude_occurrence()` — dedup-append excluded_dates → retire free slots on date → persist_excluded_dates → audit SYNC "doctor.availability_block_occurrence_excluded".
- `truncate_from()` — retire free slots from date → truncate_block (end_date = occ_date - 1) → audit SYNC "doctor.availability_block_truncated".
- Confirmed-slot invariant preserved in all paths: slots with `has_confirmed_appointment=True` NEVER retired.

**DTO** (`api/dtos.py`):
- `DeleteBlockResponse` gains `scope: str = "series"` field.

**Router** (`api/doctors_router.py`):
- DELETE endpoint adds `scope: str = Query(default="series")` + `occurrence_date: date | None = Query(default=None)`.
- `scope=series` → existing `delete_block()` (backward compat).
- `scope=occurrence` → `exclude_occurrence()` + `count_future_confirmed()` + commit.
- `scope=this_and_future` → `truncate_from()` + `count_future_confirmed()` + commit.
- 422 (Spanish neutro) when scope requires occurrence_date and it's missing.
- Router accesses `svc.count_future_confirmed()` (no private `_repo` access from API layer).

### Feature #2 — Cannot create blocks in the past

**Service** (`application/availability_block_service.py` — `create_block()`):
- `one_off` + `specific_date < today` → `ValueError("No puedes crear bloques en fechas pasadas.")` → 422.
- `recurrent` + `end_condition_kind='end_date'` + `end_date < today` → `ValueError("La fecha de fin no puede estar en el pasado.")` → 422.

## Tests

**New test file:** `vitalia/backend/tests/modules/vitalia/clinics/test_availability_block_scoped_delete.py`

15 tests (TDD RED-first):
- `test_projection_skips_excluded_occurrence` ✅
- `test_occurrence_dates_in_range_skips_excluded` ✅
- `test_one_off_skips_excluded_specific_date` ✅
- `test_service_exclude_occurrence_persists_excluded_date` ✅
- `test_service_exclude_occurrence_retires_free_slots_not_confirmed` ✅
- `test_service_truncate_from_sets_end_date` ✅
- `test_service_truncate_from_retires_future_free_slots` ✅
- `test_delete_route_has_response_model` ✅
- `test_delete_scope_response_includes_scope_field` ✅
- `test_delete_scope_occurrence_returns_scope_in_response` ✅
- `test_delete_scope_occurrence_without_occurrence_date_returns_422` ✅
- `test_delete_scope_this_and_future_without_occurrence_date_returns_422` ✅
- `test_create_one_off_past_date_raises_value_error` ✅
- `test_create_recurrent_past_end_date_raises_value_error` ✅
- `test_post_one_off_past_date_returns_422` ✅

Full suite: **455/455 PASS**.

## Quality Gates

- `ruff check` → All checks passed
- `ruff format --check` → All files formatted
- Migration 044 applied: `044_vitalia (head)`. Re-upgrade = no-op (idempotent).
- Pre-existing arch failure (`test_pgcrypto_phi_columns` — `treatment_plans.notes TEXT` vs BYTEA) is NOT introduced by this PR; baseline unrelated.

## Files Changed

| File | Change |
|---|---|
| `vitalia/backend/alembic/versions/044_vitalia_availability_excluded_dates.py` | NEW — migration |
| `vitalia/backend/src/modules/vitalia/clinics/infrastructure/models/availability_block_model.py` | MODIFY — `excluded_dates` column |
| `vitalia/backend/src/modules/vitalia/clinics/domain/availability_block.py` | MODIFY — `excluded_dates` field |
| `vitalia/backend/src/modules/vitalia/clinics/application/availability_projection_service.py` | MODIFY — `_is_excluded` helper + branch updates |
| `vitalia/backend/src/modules/vitalia/clinics/application/ports/availability_repo_port.py` | MODIFY — 4 new abstract methods |
| `vitalia/backend/src/modules/vitalia/clinics/infrastructure/repositories/availability_block_repository.py` | MODIFY — 4 new impl methods + model↔entity mapping |
| `vitalia/backend/src/modules/vitalia/clinics/application/availability_block_service.py` | MODIFY — `count_future_confirmed` + `exclude_occurrence` + `truncate_from` + past-date guards |
| `vitalia/backend/src/modules/vitalia/clinics/api/dtos.py` | MODIFY — `DeleteBlockResponse.scope` |
| `vitalia/backend/src/modules/vitalia/clinics/api/doctors_router.py` | MODIFY — scoped DELETE endpoint |
| `vitalia/backend/tests/modules/vitalia/clinics/test_availability_block_scoped_delete.py` | NEW — 15 tests |
