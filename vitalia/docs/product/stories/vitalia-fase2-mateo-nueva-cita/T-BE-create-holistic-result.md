# cap: scheduling.mateo-agenda
# T-BE-create-holistic-result.md
# Story: vitalia-fase2-mateo-nueva-cita
# Date: 2026-06-23

## Summary

Fix-loop holístico del create-path (T-BE-2/T-BE-4). Eliminado el último bloqueante del flujo cita-create (bug #8 `NoReferencedTableError`). Test de integración real RED→GREEN. Smoke-insert confirmado.

---

## Bug #8 — Root Cause

**Error:** `sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column 'vitalia_appointment_clinic_map.appointment_id' could not find table 'vitalia_appointments'`

**Trace:** `agenda_router.py:520 → create_appointment_service.py:183 → agenda_grid_repository_impl.py:409 → session.flush()`

**Root cause:**

`AppointmentClinicMapModel` (the ORM model for `vitalia_appointment_clinic_map`) declared:

```python
appointment_id: Mapped[UUID] = mapped_column(
    PgUUID(as_uuid=True),
    ForeignKey("vitalia_appointments.id", ondelete="CASCADE"),  # ← THE BUG
    primary_key=True,
)
```

But `vitalia_appointments` has **no Python SQLAlchemy model class**. It is managed exclusively by raw Alembic migrations. The `AgendaGridRepositoryImpl` explicitly documents this at lines 54-65 with a comment block.

When SQLAlchemy's `configure_mappers()` tries to resolve `ForeignKey("vitalia_appointments.id")`, it calls `_get_table_key()` → fails with `NoReferencedTableError` because the referenced table is not registered in the ORM metadata. This fires at `session.flush()` time.

The DB-level FK constraint (`vitalia_appointment_clinic_map_appointment_id_fkey FOREIGN KEY (appointment_id) REFERENCES vitalia_appointments(id) ON DELETE CASCADE`) was correctly created by migration 050 and **exists in the real database**. The ORM declaration was redundant AND broken.

**Fix applied:** `vitalia/backend/src/modules/vitalia/scheduling/persistence/models/appointment_clinic_map_model.py`

Removed `ForeignKey("vitalia_appointments.id", ondelete="CASCADE")` from the `appointment_id` `mapped_column()` declaration. Also removed the now-unused `ForeignKey` import from sqlalchemy.

After fix:
```python
appointment_id: Mapped[UUID] = mapped_column(
    PgUUID(as_uuid=True),
    primary_key=True,
)
```

The DB-level constraint still enforces referential integrity. The ORM does not need to replicate it.

---

## Full-Flow Audit (holistic column/schema verification)

All columns verified against real `vitalia_dev` DB schema via `docker exec luana-dev-luana_postgres_dev-1 psql`.

### `vitalia_appointments` — repo.create() INSERT audit

| Column | NOT NULL | Supplied by repo.create() | Status |
|---|---|---|---|
| id | YES | YES (uuid4()) | PASS |
| tenant_id | YES | YES | PASS |
| clinic_id | YES | YES (commit 86b90904) | PASS |
| offer_id | YES | YES (commit 86b90904) | PASS |
| patient_id | YES | YES | PASS |
| doctor_id | YES | YES | PASS |
| slot_iso | YES | YES (= start_time param) | PASS |
| duration_minutes | YES | YES (derived from end_time - start_time) | PASS |
| status | YES | YES (hardcoded 'SCHEDULED') | PASS |
| origin | YES | YES | PASS |
| notes_internal | NO | YES (NULL OK, migration 052 fixed) | PASS |
| currency | NO | YES ('USD' default) | PASS |
| created_at | YES | YES (NOW()) | PASS |
| booking_metadata | YES | YES (server default '{}') | PASS |
| balance_status | YES | YES (server default 'no_balance') | PASS |
| payment_status | YES | YES (server default 'unpaid') | PASS |

All NOT NULL columns without server defaults are supplied by the INSERT. PASS.

### `vitalia_appointment_clinic_map` — ORM AppointmentClinicMapModel audit

| Column | NOT NULL | Supplied by create_clinic_map() | Status |
|---|---|---|---|
| appointment_id | YES (PK) | YES | PASS |
| tenant_id | YES | YES | PASS |
| clinic_id | YES | YES | PASS |
| patient_id | YES | YES | PASS |
| doctor_id | YES | YES | PASS |
| service_label | YES | YES | PASS |
| origin | YES | YES | PASS |
| start_time | NO | YES (mirror) | PASS |
| end_time | NO | YES (mirror) | PASS |
| status | NO | YES ('SCHEDULED') | PASS |
| created_at | YES | YES (server_default NOW()) | PASS |
| hold_created_by_agent | YES | YES (server_default false) | PASS |

All fields verified. PASS.

---

## New Integration Test

**File:** `vitalia/backend/tests/modules/vitalia/scheduling/test_create_appointment_e2e_integration.py`

Tests (7 total, all GREEN):

1. `TestClinicMapFlushWorks::test_clinic_map_orm_flush_no_error`
   - **Bug #8 regression gate.** RED before fix (NoReferencedTableError at flush). GREEN after fix.
   - Inserts raw appointment row → creates AppointmentClinicMapModel ORM → session.flush() → verifies row in DB.

2. `TestCreateAppointmentFullPath::test_valid_create_rows_in_both_tables`
   - Full repo layer test: repo.create() + repo.create_clinic_map() → verifies rows in both tables via raw SQL.
   - Asserts all critical field values (clinic_id, offer_id, patient_id, doctor_id, duration, status, start/end mirrors).

3. `TestCreateAppointmentFullPath::test_all_vitalia_appointments_not_null_columns_satisfied`
   - Schema audit gate: queries `information_schema.columns` for NOT NULL columns → verifies repo INSERT covers all with no server defaults.

4. `TestCreateAppointmentFullPath::test_all_clinic_map_not_null_columns_satisfied`
   - Same audit for clinic_map table.

5. `TestOverlapViaExclude::test_overlapping_clinic_map_raises_integrity_error`
   - EXCLUDE anti-overlap gate: same doctor + same slot → IntegrityError with SQLSTATE 23P01. Verifies DB constraint fires end-to-end through the repo.

6. `TestCreateAppointmentServiceE2E::test_service_happy_path_row_in_db`
   - Full service layer (CreateAppointmentService.create_appointment()) against real Postgres. Verifies >= 1 appointment row + >= 1 clinic_map row (status SCHEDULED). Explicitly guards against NoReferencedTableError.

7. `TestCreateAppointmentServiceE2E::test_overlap_via_service_raises_overlap_error`
   - Service maps EXCLUDE violation to AppointmentOverlapError (or IntegrityError 23P01).

**TDD evidence:** Test #1 was confirmed RED before the fix (captures the `NoReferencedTableError` via `PendingRollbackError` from session invalidation). GREEN after removing ForeignKey.

---

## Smoke Insert Proof

Test `test_valid_create_rows_in_both_tables` executed against `vitalia_test` DB (localhost:5435):
- Inserted real row in `vitalia_appointments`: `id`, `tenant_id`, `clinic_id`, `offer_id`, `patient_id`, `doctor_id`, `slot_iso`, `duration_minutes=30`, `status=SCHEDULED`, `origin=walk_in`, `notes_internal=NULL`
- Created `vitalia_appointment_clinic_map` mirror: `status=SCHEDULED`, `start_time` populated, `end_time` populated
- Both rows verified by raw SQL query after flush
- Session rolled back (test cleanup — function-scoped `db_session` fixture)

Result: PASS (0.17s).

---

## Gates Status (G5)

| Gate | Result |
|---|---|
| ruff check scheduling src/ + tests/ | 0 errors (PASS) |
| `test_create_appointment_e2e_integration.py` 7 tests | 7/7 PASS |
| `tests/modules/vitalia/scheduling/` (excl. pre-existing 050 fixture issue) | 249/249 PASS |
| arch fitness `test_ep3_handlers_sync_callable.py` | PRE-EXISTING FAIL (ModuleNotFoundError luana_core_sales_agent.inbound_mode_seam — unrelated to this ticket, present before and after fix) |
| arch fitness test_migration_050_exclude asyncio loop | PRE-EXISTING FAIL (asyncio event-loop isolation in module-scoped fixture — unrelated to this ticket) |

Both pre-existing failures verified: failed identically on stashed (original) code before any changes.

---

## Files Changed

| File | Change |
|---|---|
| `vitalia/backend/src/modules/vitalia/scheduling/persistence/models/appointment_clinic_map_model.py` | Removed `ForeignKey("vitalia_appointments.id", ondelete="CASCADE")` from `appointment_id` `mapped_column()`. Removed `ForeignKey` from sqlalchemy import. Added explanatory docstring block. |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_create_appointment_e2e_integration.py` | NEW — 7 integration tests covering full create path (RED→GREEN), overlap EXCLUDE, schema audit |

---

## Commit SHA

Pending (to be committed in this session).

---

## Pattern: Why These Bugs Ship

All 8 bugs in the create-appointment path shared the same root cause: the unit tests mock `AsyncSession` / the DB entirely. The session mock never exercises:
- ORM mapper configuration (ForeignKey resolution)
- Real column existence
- NOT NULL constraints
- EXCLUDE constraint

The fix is the new integration test — it cannot be green with a mocked session. Any future regression in the ORM schema (wrong ForeignKey, missing column, NOT NULL violation) will be caught at test time, not in live production.
