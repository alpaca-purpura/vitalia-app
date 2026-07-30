# T-BE-2 Result — AvailabilityBlock domain + models + AvailabilityProjectionService + AvailabilityBlockRepository

**Ticket:** T-BE-2  
**Story:** vitalia-fase2-lisa-doctores  
**State:** pushed  
**Commit SHA:** 2f88b316  
**Branch:** wip/vitalia  
**Date:** 2026-05-31

---

## Deliverables produced

| File | Status | Notes |
|---|---|---|
| `clinics/domain/availability_block.py` | ALREADY EXISTED (T-BE-1) | Full domain validation already implemented |
| `clinics/infrastructure/models/availability_block_model.py` | NEW | SQLA 2.0 model mapping to `vitalia_availability_blocks` (migration 036) |
| `clinics/infrastructure/models/availability_slot_model.py` | NEW | SQLA 2.0 model mapping to `vitalia_availability_slots` (migration 036) |
| `clinics/infrastructure/repositories/availability_block_repository.py` | NEW | Inherits `CompoundScopeRepositoryBase`, scope_field=clinic_id, soft deletes, SC-1d/SC-3b preserved |
| `clinics/application/ports/availability_repo_port.py` | NEW | ABC port with 6 abstract methods |
| `clinics/application/availability_projection_service.py` | NEW | dateutil.rrule expansion (weekly/biweekly/end_date/occurrences/open_ended-90d/one_off) |
| `tests/modules/vitalia/clinics/test_availability_projection.py` | NEW | 12 tests — rrule expansion + slot structure (TDD RED-first) |
| `tests/modules/vitalia/clinics/test_availability_block_mutable.py` | NEW | 17 tests — domain validation + repository contracts + service invariants (TDD RED-first) |

**No new migration** — all 3 tables already created in migration 036 (T-BE-1).

---

## Test results

```
vitalia/backend/tests/modules/vitalia/clinics/
  96 passed (full suite — 29 new T-BE-2 + 67 from T-BE-1)

vitalia/backend/tests/architecture/
  319 passed, 1 skipped, 2 warnings
  (excluding pre-existing: test_pgcrypto_phi_columns.py::treatment_plans.notes — TEXT vs BYTEA, introduced in T-BE-1 context, not T-BE-2 scope)
```

---

## Validators covered

| Validator | Test | Status |
|---|---|---|
| V-FN-1 weekly + end_date | `test_project_weekly_end_date_returns_correct_count` + `test_project_weekly_slots_have_correct_duration` | GREEN |
| V-FN-2 biweekly + occurrences | `test_project_biweekly_occurrences_6` + `test_project_biweekly_occurrences_correct_slot_count` | GREEN |
| V-FN-4 one_off | `test_project_one_off_single_date` + `test_project_one_off_slots_utc_aware` | GREEN |
| V-FN-7 open_ended 90d | `test_project_open_ended_uses_90d_horizon` + `test_project_open_ended_has_slots_within_90d` | GREEN |
| V-ARCH-1 CompoundScopeRepositoryBase | `test_availability_block_repository_inherits_compound_scope_repository_base` | GREEN |
| V-ARCH-4 ABC port | `test_availability_repo_port_is_abc` + `test_availability_repo_port_has_required_methods` | GREEN |

---

## Architecture decisions applied

- **D-2 (anti-duplication confirmed):** `dateutil.rrule` brand-local. `core/luana-core-commercial-calendar` has zero RRULE support — NOT consumed. No engine lift (single consumer → over-engineering).
- **HIPAA dual-filter:** `AvailabilityBlockRepository` inherits `CompoundScopeRepositoryBase` (scope_field=`clinic_id`). Same contract as `DoctorRepository` for cross-clinic isolation consistency even though availability blocks are not PHI.
- **Reproject-future-only:** `project_block(block, reference_date)` accepts a `reference_date` parameter filtering out past dates. `classify_future_slots_for_deletion` splits future slots into deletable (free) vs preserved (confirmed appointments). Repository `delete_block` / `update_block` use this logic.
- **SC-1d / SC-3b (delete preserves confirmed):** `classify_future_slots_for_deletion` returns `(to_delete, preserved_count)`. Repository `delete_block` returns the preserved count as the API return value `{deleted: bool, preserved_appointments: N}`.
- **open_ended 90d:** `_OPEN_ENDED_HORIZON_DAYS = 90` constant, rolling from `reference_date`.

---

## Pre-existing failure (not T-BE-2 scope)

`test_pgcrypto_phi_columns.py::test_no_phi_column_uses_text_or_varchar_unencrypted` — `treatment_plans.notes` defined as TEXT instead of BYTEA. Confirmed pre-existing from T-BE-1 context (stash test confirms it failed before T-BE-2 files). This must be fixed in a separate ticket targeting `treatment_plans` migration.

---

## Skills consulted

| Skill | Invoked | Decision |
|---|---|---|
| `backend-expert` | Yes (SOP, runtime-quality-checklist) | SQLA 2.0 `select()`, Pydantic v2 ConfigDict, SA 2.0 async patterns, CompoundScopeRepositoryBase for dual-filter |
| `tessl__pytest-api-testing` | Yes | TDD RED-first order: tests written before implementation; factory fixtures; parametrize for edge cases |

---

## Code quality gates

| Gate | Result |
|---|---|
| ruff check | 0 errors (after auto-fix of 4 import-related issues) |
| ruff format --check | 0 files to reformat |
| pytest clinics/ | 96/96 PASS |
| arch fitness (excl. pre-existing) | 319/319 PASS |
| No engine imports in domain | clinics/domain/*.py — pure Python, zero luana_core_* imports |
| No new migration needed | migration 036 already creates all 3 tables |

---

## Next ticket

**T-BE-3** — Availability blocks endpoints (GET/POST/PATCH/DELETE) + scheduling slot materialization + audit. Depends on T-BE-2 (DONE).
