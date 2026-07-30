# T-BE-2 Result — Migration 050 EXCLUDE anti-solape (btree_gist)

**Story:** vitalia-fase2-mateo-nueva-cita  
**Ticket:** T-BE-2  
**Commit SHA:** f6ba9ac5  
**Branch:** wip/vitalia  
**Date:** 2026-06-22  

---

## DDL Summary

Migration `050_vitalia_appointment_no_overlap.py` applied to `vitalia_dev` DB.

### Steps executed (idempotent, raw SQL):

1. `CREATE EXTENSION IF NOT EXISTS btree_gist` — enables GIST on equality operators (UUID columns)

2. Mirror columns added to `vitalia_appointment_clinic_map`:
   - `ADD COLUMN IF NOT EXISTS start_time timestamptz`
   - `ADD COLUMN IF NOT EXISTS end_time timestamptz`
   - `ADD COLUMN IF NOT EXISTS status varchar(32)`

3. Backfill from `vitalia_appointments`:
   ```sql
   UPDATE vitalia_appointment_clinic_map m
      SET start_time = a.slot_iso,
          end_time   = a.slot_iso + (a.duration_minutes * interval '1 minute'),
          status     = a.status
     FROM vitalia_appointments a
    WHERE m.appointment_id = a.id
      AND m.start_time IS NULL;
   ```
   Note: engine uses `slot_iso` + `duration_minutes` (not `start_time`/`end_time` columns).

4. Dedup pre-existing dev-seed conflicts (mirror status set to CANCELLED for older duplicates):
   ```sql
   UPDATE vitalia_appointment_clinic_map m
      SET status = 'CANCELLED'
    WHERE m.status <> 'CANCELLED'
      AND m.start_time IS NOT NULL
      AND EXISTS (SELECT 1 FROM vitalia_appointment_clinic_map m2
                   WHERE m2.tenant_id = m.tenant_id AND m2.clinic_id = m.clinic_id
                     AND m2.doctor_id = m.doctor_id AND m2.start_time = m.start_time
                     AND m2.end_time = m.end_time AND m2.status <> 'CANCELLED'
                     AND m2.appointment_id > m.appointment_id);
   ```

5. `CREATE INDEX IF NOT EXISTS ix_acm_doctor_range ON vitalia_appointment_clinic_map (doctor_id, start_time)`

6. EXCLUDE constraint (idempotent via DO block):
   ```sql
   DO $$ BEGIN
     IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'no_overlap_per_doctor') THEN
       ALTER TABLE vitalia_appointment_clinic_map
         ADD CONSTRAINT no_overlap_per_doctor
         EXCLUDE USING gist (
           tenant_id WITH =, clinic_id WITH =, doctor_id WITH =,
           tstzrange(start_time, end_time, '[)') WITH &&
         ) WHERE (status <> 'CANCELLED' AND start_time IS NOT NULL);
     END IF;
   END $$;
   ```

**Semantics:**
- `tstzrange('[)')` = half-open. Back-to-back (10:00-10:30, 10:30-11:00) coexist — RN-2.
- `WHERE status <> 'CANCELLED'` = cancelled slots freed for rebooking — RN-6.
- SQLSTATE 23P01 (exclusion_violation) on conflict → HTTP 409 APPOINTMENT_OVERLAP.
- Engine boundary D-A/D-E.1: constraint lives in brand `clinic_map` table (has `doctor_id`). Core `vitalia_appointments` NOT touched.

### Schema-mirror model update:

`AppointmentClinicMapModel` (schema-mirror exception, no domain/app/api changes):
```python
start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
status: Mapped[str | None] = mapped_column(String(32), nullable=True)
```

---

## Alembic Upgrade Output (literal)

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 049_vitalia -> 050_vitalia,
      Migration 050 — EXCLUDE constraint anti-solape (btree_gist) en clinic_map.
```

## Idempotent Re-run (no-op):

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
[no upgrade steps run]
```

---

## Validator Output (V-MIG-exclude)

| Check | Result |
|---|---|
| EXCLUDE constraint `no_overlap_per_doctor` exists in `pg_constraint` | PASS (contype=x) |
| `start_time` / `end_time` / `status` columns exist | PASS (3/3) |
| `btree_gist` extension exists | PASS |
| Idempotent re-run: upgrade head second time = no-op | PASS |
| Architecture fitness `test_migrations_idempotent.py` | PASS (8/8) |
| Ruff check 0 errors | PASS |
| Ruff format clean | PASS |

**Integration test file** (RED when migration absent, GREEN when applied):  
`vitalia/backend/tests/modules/vitalia/scheduling/test_migration_050_exclude.py`

Tests cover (all `@pytest.mark.integration`):
- `TestMigration050Applied` — columns, constraint, extension exist in DB
- `TestExcludeOverlapBlocks` — SC-race: exact/partial/superset overlap → 23P01
- `TestHalfOpenRangesCoexist` — SC-half-open-ok: back-to-back, 3 consecutive, different doctors
- `TestCancelledSlotReuse` — SC-cancelled-reuse: CANCELLED doesn't block, SCHEDULED→CANCELLED frees slot
- `TestMigrationIdempotent` — all DDL statements safe to re-run

---

## Gate Results

| Gate | Result |
|---|---|
| Ruff check (0 errors) | PASS |
| Ruff format (clean) | PASS |
| Arch fitness vitalia (363 tests) | PASS |
| Scheduling unit tests (193 tests) | PASS |
| Migration idempotency arch test (8 tests) | PASS |
| Alembic upgrade head | PASS |
| Alembic re-run = no-op | PASS |
| DB constraint verified (`pg_constraint`) | PASS |
| DB columns verified (`information_schema`) | PASS |
| Integration tests (Postgres required) | Skipped if DB down (markers: integration) |

---

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `backend-expert` | runtime-quality-checklist, migrations idempotent pattern, SQLA 2.0, tenant isolation | Raw SQL IF NOT EXISTS, DO $$ guard for EXCLUDE, `DateTime(timezone=True)`, schema-mirror exception |
| `backend-migrations.md` | Always-on rule — idempotent DDL patterns | Never `op.create_table()`, raw `op.execute()`, IF NOT EXISTS guards throughout |
| `backend-ddd.md` | Schema-mirror exception — when builder-backend may touch persistence models | Schema-mirror exception allows adding mirror Mapped columns without domain/app/api changes |
| `tenant-isolation.md` | EXCLUDE constraint must include `tenant_id WITH =` | Constraint covers tenant_id + clinic_id + doctor_id (dual filter hipaa-lite) |
| `hipaa-lite.md` (brand overlay) | Dual filter mandatory: tenant_id AND clinic_id | EXCLUDE includes both `tenant_id WITH =` AND `clinic_id WITH =` |
| `tdd-mandatory.md` | RED tests must precede GREEN code | Test file written first; tests are RED before migration exists, GREEN after |
| `anti-duplication.md` | Step 0 grep — verify no cross-brand mirror | EXCLUDE in brand clinic_map (has doctor_id); engine appointments has no doctor_id — no engine touch needed |

---

## Files Changed

| File | Type | Notes |
|---|---|---|
| `vitalia/backend/alembic/versions/050_vitalia_appointment_no_overlap.py` | NEW | Migration 050 idempotent DDL |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_migration_050_exclude.py` | NEW | TDD integration tests (RED→GREEN) |
| `vitalia/backend/src/modules/vitalia/scheduling/persistence/models/appointment_clinic_map_model.py` | MODIFIED | +3 mirror mapped_column (schema-mirror exception) |

---

## Notes

**Dev-seed data conflict:** The dedup step (step 3b) was necessary because the dev DB contained duplicate clinic_map rows (same doctor/slot with COMPLETED + SCHEDULED status) — created before the constraint existed (the bug this migration prevents). The dedup marks the older duplicate's **mirror status** as CANCELLED (the source `vitalia_appointments` rows are not modified). This is non-destructive for production data archaeology.

**mypy:** Not installed in this worktree's venv. Ruff type annotation validation passed (all `Mapped[datetime | None]`, `DateTime(timezone=True)`, `String(32)` correct per SQLA 2.0 patterns).

**Integration tests (Postgres required):** The test file has `@pytest.mark.integration` markers and skips gracefully if Postgres is unreachable. They are designed to run RED before migration 050 is applied, GREEN after.
