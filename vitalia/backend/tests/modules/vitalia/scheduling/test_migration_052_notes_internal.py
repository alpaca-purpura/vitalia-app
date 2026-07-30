# cap: scheduling.mateo-agenda
"""Regression test — Migration 052: notes_internal column on vitalia_appointments (T-BE-4).

ROOT CAUSE (live 500 on 2026-06-22/23):
    POST /api/v1/scheduling/appointments → 500
    asyncpg.exceptions.UndefinedColumnError:
        column "notes_internal" of relation "vitalia_appointments" does not exist.
    agenda_grid_repository_impl.create() built the INSERT with notes_internal
    but no migration ever added the column to vitalia_appointments.
    Unit tests passed because they mock the session and never hit the real schema.

This test exercises the ACTUAL INSERT against a real Postgres schema so the
same class of bug (missing column) is caught before it reaches production.

Uses the conftest `db_session` fixture (NullPool, per-function, rollback isolation)
matching the established pattern in this test suite.

Tests:
1. Schema gate: notes_internal column exists after migration 052.
2. Regression: INSERT with notes_internal=NULL succeeds (inline nueva-cita flow).
3. Nullable: column is nullable.
4. Schema audit: all other columns in the repo INSERT exist.
5. Idempotency: DDL re-run (ADD COLUMN IF NOT EXISTS) is a no-op.

marker: integration (requires Postgres — skipped if DB unreachable per conftest)
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Columns that the repo INSERT references — audit all of them
# ---------------------------------------------------------------------------

REPO_INSERT_COLUMNS = [
    "id",
    "tenant_id",
    "patient_id",
    "doctor_id",
    "slot_iso",
    "duration_minutes",
    "status",
    "origin",
    "notes_internal",  # ← the missing column that caused the live 500
    "currency",
    "created_at",
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestMigration052NotesInternal:
    """Verify migration 052 DDL artifacts and INSERT compatibility."""

    async def test_notes_internal_column_exists(self, db_session: AsyncSession) -> None:
        """vitalia_appointments.notes_internal column must exist after migration 052.

        RED before migration: column is absent → this assertion fails.
        GREEN after migration: column is present with type TEXT.
        """
        result = await db_session.execute(
            text(
                """
                SELECT column_name, data_type
                  FROM information_schema.columns
                 WHERE table_name = 'vitalia_appointments'
                   AND column_name = 'notes_internal'
                """
            )
        )
        row = result.fetchone()
        assert row is not None, (
            "Column 'notes_internal' does not exist in vitalia_appointments. "
            "Migration 052 not applied. This is the root cause of the live 500 "
            "on POST /api/v1/scheduling/appointments."
        )
        assert row[1] == "text", f"Expected data_type='text' for notes_internal, got '{row[1]}'"

    async def test_notes_internal_column_is_nullable(self, db_session: AsyncSession) -> None:
        """notes_internal must be nullable (inline nueva-cita flow always sends null)."""
        result = await db_session.execute(
            text(
                """
                SELECT is_nullable
                  FROM information_schema.columns
                 WHERE table_name = 'vitalia_appointments'
                   AND column_name = 'notes_internal'
                """
            )
        )
        row = result.fetchone()
        assert row is not None, "Column 'notes_internal' not found in vitalia_appointments."
        assert row[0] == "YES", (
            f"notes_internal must be nullable — inline create flow sends NULL. Got is_nullable='{row[0]}'"
        )

    async def test_all_repo_insert_columns_exist(self, db_session: AsyncSession) -> None:
        """Schema audit: every column in agenda_grid_repository_impl.create() INSERT exists.

        This is the meta-test that would have caught the bug before it shipped.
        If any column is missing, the INSERT will 500 in production even if
        unit tests pass (because unit tests mock the session and skip real DDL).
        """
        result = await db_session.execute(
            text(
                """
                SELECT column_name
                  FROM information_schema.columns
                 WHERE table_name = 'vitalia_appointments'
                """
            )
        )
        existing_columns = {row[0] for row in result.fetchall()}

        missing = [col for col in REPO_INSERT_COLUMNS if col not in existing_columns]
        assert not missing, (
            f"Columns in the repo INSERT but missing from vitalia_appointments: {missing}. "
            "Any missing column causes a 500 on appointment create. "
            "Run the appropriate migration to add them."
        )

    async def test_insert_with_notes_internal_null_succeeds(self, db_session: AsyncSession) -> None:
        """Regression: INSERT into vitalia_appointments with notes_internal=NULL succeeds.

        This is the exact failure path from the live 500. Before migration 052,
        Postgres raised UndefinedColumnError because the column did not exist.
        After migration 052, the column exists and NULL is accepted.

        The test uses a complete INSERT that satisfies all NOT NULL constraints
        (clinic_id, offer_id are required by schema). Uses synthetic PHI-free data.
        """
        tenant_id = uuid4()
        clinic_id = uuid4()
        offer_id = uuid4()
        appt_id = uuid4()
        patient_id = uuid4()
        doctor_id = uuid4()

        # Full INSERT that satisfies all NOT NULL constraints.
        # The key regression being tested: notes_internal is now recognized.
        # Before migration 052: UndefinedColumnError on 'notes_internal'.
        # After migration 052: INSERT succeeds.
        await db_session.execute(
            text(
                """
                INSERT INTO vitalia_appointments
                    (id, tenant_id, clinic_id, offer_id, patient_id, doctor_id,
                     slot_iso, duration_minutes, status, origin,
                     notes_internal, currency, created_at)
                VALUES
                    (:id, :tenant_id, :clinic_id, :offer_id, :patient_id, :doctor_id,
                     :slot_iso, :dur, 'SCHEDULED', :origin,
                     :notes, :currency, NOW())
                """
            ).bindparams(
                id=appt_id,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                offer_id=offer_id,
                patient_id=patient_id,
                doctor_id=doctor_id,
                slot_iso=datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc),
                dur=30,
                origin="walk_in",
                notes=None,  # inline nueva-cita flow always sends null
                currency="USD",
            )
        )
        # Verify the row was actually written (not silently skipped)
        check = await db_session.execute(
            text("SELECT id, notes_internal FROM vitalia_appointments WHERE id = :appt_id").bindparams(appt_id=appt_id)
        )
        row = check.fetchone()
        assert row is not None, "INSERT did not persist the appointment row — check DB connectivity."
        assert row[1] is None, f"Expected notes_internal=NULL for inline create, got: {row[1]!r}"

    async def test_migration_idempotent_notes_internal(self, db_session: AsyncSession) -> None:
        """Idempotency: ALTER TABLE ... ADD COLUMN IF NOT EXISTS is a strict no-op on re-run.

        Migration 052 uses IF NOT EXISTS. Running it twice must not raise.
        After re-run, column must still exist with correct type.
        """
        # Should not raise: IF NOT EXISTS prevents duplicate-column error
        await db_session.execute(text("ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS notes_internal TEXT"))
        # Column must still exist and have correct type
        result = await db_session.execute(
            text(
                """
                SELECT data_type FROM information_schema.columns
                 WHERE table_name = 'vitalia_appointments'
                   AND column_name = 'notes_internal'
                """
            )
        )
        row = result.fetchone()
        assert row is not None, "Column notes_internal disappeared after idempotent re-run."
        assert row[0] == "text", f"Column type changed after re-run: expected 'text', got '{row[0]}'"
