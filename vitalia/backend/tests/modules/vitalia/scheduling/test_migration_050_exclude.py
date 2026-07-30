# cap: scheduling.mateo-agenda
"""TDD RED tests — Migration 050 EXCLUDE constraint anti-solape (T-BE-2).

Tests verify:
1. EXCLUDE blocks overlapping inserts (SC-race, SC-half-open-block) → psycopg2 23P01
2. Back-to-back half-open ranges coexist (SC-half-open-ok, RN-2)
3. CANCELLED appointment allows rebooking same range (SC-cancelled-reuse, RN-6)
4. Migration is idempotent (re-run produces no error, no new constraint duplication)
5. Prod-clone flow (schema clone + upgrade = no-op)

Per 03-arch-be.md § 7, 04-validators.yaml SC-race/SC-half-open-ok/SC-half-open-block/
SC-cancelled-reuse/SC-bypass-availability, and .claude/rules/backend-migrations.md.

Architecture:
- EXCLUDE constraint lives in vitalia_appointment_clinic_map (D-A/D-E.1)
- NOT in core engine appointments table (engine boundary respected)
- Uses btree_gist + tstzrange half-open '[)' (back-to-back OK, overlaps blocked)
- Partial WHERE status <> 'CANCELLED' (CANCELLED frees the slot)

marker: integration (requires Postgres — skipped if DB unreachable per conftest)
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Constants (synthetic PHI-free test data)
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
DOCTOR_ID = uuid4()
DOCTOR_ID_2 = uuid4()

BASE_TIME = datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc)


def _start(hour: int, minute: int = 0) -> datetime:
    """Return a UTC datetime on 2026-07-01 at h:mm."""
    return BASE_TIME.replace(hour=hour, minute=minute)


def _appt_row(
    *,
    tenant_id: object = TENANT_ID,
    clinic_id: object = CLINIC_ID,
    doctor_id: object = DOCTOR_ID,
    start_time: datetime,
    end_time: datetime,
    status: str = "SCHEDULED",
) -> dict:
    """Build a minimal vitalia_appointment_clinic_map row."""
    return {
        "appointment_id": uuid4(),
        "tenant_id": tenant_id,
        "clinic_id": clinic_id,
        "patient_id": uuid4(),
        "doctor_id": doctor_id,
        "service_label": "Consulta prueba",
        "origin": "walk_in",
        "start_time": start_time,
        "end_time": end_time,
        "status": status,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

INSERT_SQL = text(
    """
    INSERT INTO vitalia_appointment_clinic_map
        (appointment_id, tenant_id, clinic_id, patient_id,
         doctor_id, service_label, origin,
         start_time, end_time, status)
    VALUES
        (:appointment_id, :tenant_id, :clinic_id, :patient_id,
         :doctor_id, :service_label, :origin,
         :start_time, :end_time, :status)
    """
)

UPDATE_STATUS_SQL = text(
    """
    UPDATE vitalia_appointment_clinic_map
       SET status = :status
     WHERE appointment_id = :appointment_id
    """
)

# Parent row in vitalia_appointments — the mirror has a DB-level FK
# vitalia_appointment_clinic_map.appointment_id → vitalia_appointments(id), so a
# parent MUST exist before the mirror insert (matches the repo create-path:
# parent first, then mirror). vitalia_appointments itself has NO overlap
# constraint (the EXCLUDE under test lives on the mirror), so overlapping parents
# coexist and only the mirror insert raises 23P01.
_INSERT_PARENT = text(
    """
    INSERT INTO vitalia_appointments
        (id, tenant_id, clinic_id, offer_id, patient_id, doctor_id,
         slot_iso, duration_minutes, status, origin, notes_internal,
         currency, created_at)
    VALUES
        (:id, :tenant_id, :clinic_id, :offer_id, :patient_id, :doctor_id,
         :slot_iso, :dur, :status, :origin, NULL, 'USD', NOW())
    """
)


async def _insert_map(db_session, row: dict) -> None:  # type: ignore[no-untyped-def]
    """Insert the FK parent (vitalia_appointments) + flush, then the clinic_map
    mirror + flush. The mirror flush is what raises 23P01 on EXCLUDE overlap.
    """
    dur = int((row["end_time"] - row["start_time"]).total_seconds() // 60) or 30
    await db_session.execute(
        _INSERT_PARENT,
        {
            "id": row["appointment_id"],
            "tenant_id": row["tenant_id"],
            "clinic_id": row["clinic_id"],
            "offer_id": uuid4(),
            "patient_id": row["patient_id"],
            "doctor_id": row["doctor_id"],
            "slot_iso": row["start_time"],
            "dur": dur,
            "status": row["status"],
            "origin": row["origin"],
        },
    )
    await db_session.flush()
    await db_session.execute(INSERT_SQL, row)
    await db_session.flush()


# ---------------------------------------------------------------------------
# Fixtures: uses the shared conftest `db_session` (function-scoped, loop-safe).
#
# A home-rolled module-scoped `async_engine` bound its asyncpg connection pool
# to the FIRST test's event loop; pytest-asyncio (asyncio_mode=auto) gives each
# test a function-scoped loop → "got Future attached to a different loop". The
# conftest `db_session`/`engine` pair is the canonical pattern (same one the
# green test_create_appointment_e2e_integration.py uses).
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Gate: verify 050 migration is applied (columns + constraint exist)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestMigration050Applied:
    """Verify migration 050 DDL artifacts exist in the database."""

    async def test_start_time_column_exists(self, db_session: AsyncSession) -> None:
        """vitalia_appointment_clinic_map.start_time column must exist."""
        result = await db_session.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                 WHERE table_name = 'vitalia_appointment_clinic_map'
                   AND column_name = 'start_time'
                """
            )
        )
        assert result.fetchone() is not None, (
            "Column start_time not found in vitalia_appointment_clinic_map. Run migration 050 first."
        )

    async def test_end_time_column_exists(self, db_session: AsyncSession) -> None:
        """vitalia_appointment_clinic_map.end_time column must exist."""
        result = await db_session.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                 WHERE table_name = 'vitalia_appointment_clinic_map'
                   AND column_name = 'end_time'
                """
            )
        )
        assert result.fetchone() is not None, "Column end_time not found."

    async def test_status_column_exists(self, db_session: AsyncSession) -> None:
        """vitalia_appointment_clinic_map.status column must exist."""
        result = await db_session.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                 WHERE table_name = 'vitalia_appointment_clinic_map'
                   AND column_name = 'status'
                """
            )
        )
        assert result.fetchone() is not None, "Column status not found."

    async def test_exclude_constraint_exists(self, db_session: AsyncSession) -> None:
        """EXCLUDE constraint 'no_overlap_per_doctor' must exist in pg_constraint."""
        result = await db_session.execute(
            text(
                """
                SELECT conname FROM pg_constraint
                 WHERE conname = 'no_overlap_per_doctor'
                   AND contype = 'x'
                """
            )
        )
        assert result.fetchone() is not None, (
            "EXCLUDE constraint 'no_overlap_per_doctor' not found. Run migration 050 to create it."
        )

    async def test_btree_gist_extension_exists(self, db_session: AsyncSession) -> None:
        """btree_gist extension must be installed."""
        result = await db_session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'btree_gist'"))
        assert result.fetchone() is not None, "btree_gist extension not installed."


# ---------------------------------------------------------------------------
# Core: EXCLUDE constraint semantic tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestExcludeOverlapBlocks:
    """SC-race + SC-half-open-block: overlapping inserts must be rejected."""

    async def test_exact_overlap_blocked(self, db_session: AsyncSession) -> None:
        """Two inserts for the exact same range [09:00, 09:30) → second raises 23P01."""
        from sqlalchemy.exc import IntegrityError

        row1 = _appt_row(
            start_time=_start(9, 0),
            end_time=_start(9, 30),
            status="SCHEDULED",
        )
        await _insert_map(db_session, row1)

        row2 = _appt_row(
            start_time=_start(9, 0),
            end_time=_start(9, 30),
            status="SCHEDULED",
        )
        with pytest.raises(IntegrityError) as exc_info:
            await _insert_map(db_session, row2)

        # SQLSTATE 23P01 = exclusion_violation
        err_str = str(exc_info.value).lower()
        assert "23p01" in err_str or "exclusion" in err_str or "no_overlap_per_doctor" in err_str, (
            f"Expected SQLSTATE 23P01 exclusion violation, got: {exc_info.value}"
        )

    async def test_partial_overlap_blocked(self, db_session: AsyncSession) -> None:
        """10:00-10:30 + 10:15-10:45 → second blocked (overlaps by 15 min)."""
        from sqlalchemy.exc import IntegrityError

        row1 = _appt_row(
            start_time=_start(10, 0),
            end_time=_start(10, 30),
            status="SCHEDULED",
        )
        await _insert_map(db_session, row1)

        row2 = _appt_row(
            start_time=_start(10, 15),
            end_time=_start(10, 45),
            status="SCHEDULED",
        )
        with pytest.raises(IntegrityError) as exc_info:
            await _insert_map(db_session, row2)

        err_str = str(exc_info.value).lower()
        assert "23p01" in err_str or "exclusion" in err_str or "no_overlap_per_doctor" in err_str

    async def test_superset_overlap_blocked(self, db_session: AsyncSession) -> None:
        """09:30-10:30 blocked by existing 10:00-10:30 (superset from left)."""
        from sqlalchemy.exc import IntegrityError

        row1 = _appt_row(
            start_time=_start(10, 0),
            end_time=_start(10, 30),
            status="SCHEDULED",
        )
        await _insert_map(db_session, row1)

        row2 = _appt_row(
            start_time=_start(9, 30),
            end_time=_start(10, 30),
            status="SCHEDULED",
        )
        with pytest.raises(IntegrityError) as exc_info:
            await _insert_map(db_session, row2)

        err_str = str(exc_info.value).lower()
        assert "23p01" in err_str or "exclusion" in err_str or "no_overlap_per_doctor" in err_str


@pytest.mark.integration
class TestHalfOpenRangesCoexist:
    """SC-half-open-ok (RN-2): back-to-back appointments must coexist."""

    async def test_back_to_back_10_and_1030(self, db_session: AsyncSession) -> None:
        """10:00-10:30 and 10:30-11:00 coexist (half-open '[)' semantics)."""
        row1 = _appt_row(
            start_time=_start(10, 0),
            end_time=_start(10, 30),
            status="SCHEDULED",
        )
        row2 = _appt_row(
            start_time=_start(10, 30),
            end_time=_start(11, 0),
            status="SCHEDULED",
        )
        # Both must insert without exception
        await _insert_map(db_session, row1)
        await _insert_map(db_session, row2)

        # Verify both rows exist
        result = await db_session.execute(
            text(
                """
                SELECT COUNT(*) FROM vitalia_appointment_clinic_map
                 WHERE doctor_id = :doctor_id
                   AND tenant_id = :tenant_id
                   AND status = 'SCHEDULED'
                   AND start_time IN (:s1, :s2)
                """
            ),
            {
                "doctor_id": DOCTOR_ID,
                "tenant_id": TENANT_ID,
                "s1": _start(10, 0),
                "s2": _start(10, 30),
            },
        )
        count = result.scalar()
        assert count == 2, f"Expected 2 back-to-back rows, got {count}"

    async def test_back_to_back_three_consecutive(self, db_session: AsyncSession) -> None:
        """Three consecutive 30-min slots for same doctor coexist."""
        rows = [
            _appt_row(start_time=_start(14, 0), end_time=_start(14, 30), status="SCHEDULED"),
            _appt_row(start_time=_start(14, 30), end_time=_start(15, 0), status="SCHEDULED"),
            _appt_row(start_time=_start(15, 0), end_time=_start(15, 30), status="SCHEDULED"),
        ]
        for row in rows:
            await _insert_map(db_session, row)

        result = await db_session.execute(
            text(
                "SELECT COUNT(*) FROM vitalia_appointment_clinic_map "
                "WHERE doctor_id = :did AND tenant_id = :tid AND status = 'SCHEDULED' "
                "AND start_time >= :s1 AND end_time <= :s2"
            ),
            {"did": DOCTOR_ID, "tid": TENANT_ID, "s1": _start(14, 0), "s2": _start(15, 30)},
        )
        count = result.scalar()
        assert count == 3, f"Expected 3 consecutive rows, got {count}"

    async def test_different_doctors_same_time_allowed(self, db_session: AsyncSession) -> None:
        """Different doctors can have overlapping appointment times (constraint is per-doctor)."""
        row1 = _appt_row(
            doctor_id=DOCTOR_ID,
            start_time=_start(11, 0),
            end_time=_start(11, 30),
            status="SCHEDULED",
        )
        row2 = _appt_row(
            doctor_id=DOCTOR_ID_2,
            start_time=_start(11, 0),
            end_time=_start(11, 30),
            status="SCHEDULED",
        )
        # Must NOT raise — different doctors
        await _insert_map(db_session, row1)
        await _insert_map(db_session, row2)


@pytest.mark.integration
class TestCancelledSlotReuse:
    """SC-cancelled-reuse (RN-6): CANCELLED appointment frees the slot for rebooking."""

    async def test_cancelled_does_not_count_as_conflict(self, db_session: AsyncSession) -> None:
        """Insert CANCELLED, then insert SCHEDULED on same range → no conflict."""
        # Step 1: Insert an appointment that will be cancelled
        appt_id = uuid4()
        row1 = {
            "appointment_id": appt_id,
            "tenant_id": TENANT_ID,
            "clinic_id": CLINIC_ID,
            "patient_id": uuid4(),
            "doctor_id": DOCTOR_ID,
            "service_label": "Consulta",
            "origin": "walk_in",
            "start_time": _start(13, 0),
            "end_time": _start(13, 30),
            "status": "CANCELLED",  # Already cancelled from the start
        }
        await _insert_map(db_session, row1)

        # Step 2: Insert SCHEDULED on same range → must succeed (CANCELLED excluded from constraint)
        row2 = _appt_row(
            start_time=_start(13, 0),
            end_time=_start(13, 30),
            status="SCHEDULED",
        )
        # Should NOT raise
        await _insert_map(db_session, row2)

    async def test_active_becomes_cancelled_allows_rebook(self, db_session: AsyncSession) -> None:
        """SCHEDULED→CANCELLED frees the slot; new SCHEDULED in same range is allowed.

        This is the real SC-cancelled-reuse scenario: an existing appointment is
        cancelled, then a new one is booked in the freed slot.
        """
        from sqlalchemy.exc import IntegrityError

        appt_id = uuid4()
        row1 = {
            "appointment_id": appt_id,
            "tenant_id": TENANT_ID,
            "clinic_id": CLINIC_ID,
            "patient_id": uuid4(),
            "doctor_id": DOCTOR_ID,
            "service_label": "Consulta",
            "origin": "walk_in",
            "start_time": _start(16, 0),
            "end_time": _start(16, 30),
            "status": "SCHEDULED",
        }
        await _insert_map(db_session, row1)

        # Verify duplicate would fail before cancel
        row2 = _appt_row(
            start_time=_start(16, 0),
            end_time=_start(16, 30),
            status="SCHEDULED",
        )
        with pytest.raises(IntegrityError):
            await _insert_map(db_session, row2)

        # Rollback to try again after cancel
        await db_session.rollback()

        # Now re-insert row1 and cancel it
        await _insert_map(db_session, row1)
        await db_session.execute(
            UPDATE_STATUS_SQL,
            {"status": "CANCELLED", "appointment_id": appt_id},
        )
        await db_session.flush()

        # New SCHEDULED booking on freed slot should succeed
        row3 = _appt_row(
            start_time=_start(16, 0),
            end_time=_start(16, 30),
            status="SCHEDULED",
        )
        await _insert_map(db_session, row3)

    async def test_two_cancelled_same_range_allowed(self, db_session: AsyncSession) -> None:
        """Two CANCELLED rows for the same range are allowed (both excluded from constraint)."""
        row1 = _appt_row(
            start_time=_start(8, 0),
            end_time=_start(8, 30),
            status="CANCELLED",
        )
        row2 = _appt_row(
            start_time=_start(8, 0),
            end_time=_start(8, 30),
            status="CANCELLED",
        )
        await _insert_map(db_session, row1)
        await _insert_map(db_session, row2)


# ---------------------------------------------------------------------------
# Idempotency: migration re-run must be a no-op
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestMigrationIdempotent:
    """Verify the 050 migration SQL can be re-run without error.

    Per .claude/rules/backend-migrations.md: IF NOT EXISTS guards make re-run safe.
    This mirrors gate 10 of /test-backend (migration idempotency clone).
    """

    async def test_extension_create_if_not_exists_idempotent(self, db_session: AsyncSession) -> None:
        """CREATE EXTENSION IF NOT EXISTS btree_gist is safe to run again."""
        # Must not raise
        await db_session.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))

    async def test_column_add_if_not_exists_idempotent(self, db_session: AsyncSession) -> None:
        """ALTER TABLE ADD COLUMN IF NOT EXISTS is safe to run again (columns exist)."""
        await db_session.execute(
            text("ALTER TABLE vitalia_appointment_clinic_map ADD COLUMN IF NOT EXISTS start_time timestamptz")
        )
        await db_session.execute(
            text("ALTER TABLE vitalia_appointment_clinic_map ADD COLUMN IF NOT EXISTS end_time timestamptz")
        )
        await db_session.execute(
            text("ALTER TABLE vitalia_appointment_clinic_map ADD COLUMN IF NOT EXISTS status varchar(32)")
        )

    async def test_constraint_add_do_block_idempotent(self, db_session: AsyncSession) -> None:
        """DO $$ IF NOT EXISTS pg_constraint check is safe to run again (constraint exists)."""
        # The DO block checks pg_constraint before adding — safe to re-run
        await db_session.execute(
            text(
                """
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
                """
            )
        )

    async def test_index_create_if_not_exists_idempotent(self, db_session: AsyncSession) -> None:
        """CREATE INDEX IF NOT EXISTS is safe to run again."""
        await db_session.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_acm_doctor_range "
                "ON vitalia_appointment_clinic_map (doctor_id, start_time)"
            )
        )
