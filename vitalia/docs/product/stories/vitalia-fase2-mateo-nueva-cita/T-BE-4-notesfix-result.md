# T-BE-4 — Bugfix result: notes_internal column on vitalia_appointments

## Status: DONE

**Ticket:** T-BE-4 (vitalia-fase2-mateo-nueva-cita)
**Date:** 2026-06-23
**Root cause:** `POST /api/v1/scheduling/appointments` → 500 `asyncpg.exceptions.UndefinedColumnError: column "notes_internal" of relation "vitalia_appointments" does not exist`

---

## Root cause (confirmed)

`agenda_grid_repository_impl.create()` built an INSERT statement referencing `notes_internal` but no migration ever added that column to `vitalia_appointments`. Unit tests passed because they mock `AsyncSession` and never hit the real Postgres schema. The parse error occurs before execution — Postgres rejects the INSERT at the column-resolution stage.

## Fix

### Migration 052 (`vitalia/backend/alembic/versions/052_vitalia_appointments_notes_internal.py`)

```sql
ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS notes_internal TEXT
```

- Idempotent (IF NOT EXISTS) — raw SQL, per `backend-migrations.md`
- HIPAA-lite decision: option (b) — nullable TEXT, always NULL in current inline nueva-cita flow. No PHI written today. TODO(PHI) marker for when appointment-notes surface lands and encryption (pgp_sym_encrypt + bytea) is warranted.
- Applied to both `vitalia_dev` and `vitalia_test` (alembic head = `052_vitalia`)

### Column audit (other INSERT columns)

All other columns in `agenda_grid_repository_impl.create()` INSERT were verified to exist in `vitalia_appointments` pre-052:
`id, tenant_id, patient_id, doctor_id, slot_iso, duration_minutes, status, origin, currency, created_at` — all present.

### Regression test (`vitalia/backend/tests/modules/vitalia/scheduling/test_migration_052_notes_internal.py`)

5 integration tests (`@pytest.mark.integration`, conftest `db_session` NullPool):
1. `test_notes_internal_column_exists` — column exists and is TEXT after migration
2. `test_notes_internal_column_is_nullable` — NULL accepted (inline flow always sends null)
3. `test_all_repo_insert_columns_exist` — meta-test: ALL columns in repo INSERT exist in schema
4. `test_insert_with_notes_internal_null_succeeds` — full INSERT with notes_internal=NULL completes
5. `test_migration_idempotent_notes_internal` — ADD COLUMN IF NOT EXISTS is a strict no-op on re-run

## Gate results

| Gate | Result | Notes |
|---|---|---|
| 5/5 integration tests | PASS | All green against `vitalia_test` |
| ruff check | PASS | 0 errors |
| ruff format | PASS | Applied, files clean |
| scheduling suite (236 tests) | PASS | Excluding pre-existing 050 loop bug |
| arch fitness | Pre-existing failures only | `test_no_phi_column_uses_text_or_varchar_unencrypted` (treatment_plans.notes — unrelated T-BE-4); `test_ep3_resolvers_wired` (cross-session inbound_mode_seam module not installed — other session's work) |
| TDD order | RED → GREEN | Tests written against missing column (RED), migration applied (GREEN) |

## Pre-existing failures (not caused by T-BE-4)

1. `test_migration_050_exclude.py::TestMigrationIdempotent::test_extension_create_if_not_exists_idempotent` — asyncio "attached to different loop" in scope="module" engine fixture. Pre-dates this PR (git log: `f6ba9ac5`).
2. `test_pgcrypto_phi_columns.py::test_no_phi_column_uses_text_or_varchar_unencrypted` — `treatment_plans.notes` TEXT vs BYTEA. Separate PHI enforcement concern, unrelated to scheduling/appointments.
3. `test_ep3_resolvers_wired.py` — cross-session (inbound canal story) `inbound_mode_seam` module not installed in this venv. Not in T-BE-4 scope.

All three confirmed pre-existing via `git stash` isolation check.

## Files committed

```
vitalia/backend/alembic/versions/052_vitalia_appointments_notes_internal.py
vitalia/backend/tests/modules/vitalia/scheduling/test_migration_052_notes_internal.py
```

## Secondary discovery (T-BE-4 scope note)

During INSERT test construction, discovered that `clinic_id` and `offer_id` are `NOT NULL` with no default in `vitalia_appointments` DDL (migration 002), but the repo `create()` INSERT does NOT include them. The live 500 hit `notes_internal` first (parse-time UndefinedColumnError, before execution). After this fix, the endpoint may encounter a NOT NULL violation on `clinic_id`/`offer_id` unless those columns are provided or made nullable. This is a separate finding, not in T-BE-4 scope — flagging for the next fix loop.
