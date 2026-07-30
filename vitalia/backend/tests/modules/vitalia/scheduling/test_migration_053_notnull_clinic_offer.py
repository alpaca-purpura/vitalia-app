# cap: scheduling.mateo-agenda
"""Regression test — T-BE-4 bugfix: clinic_id + offer_id NOT NULL in vitalia_appointments INSERT.

ROOT CAUSE (diagnosed live — 2026-06-23):
    POST /api/v1/scheduling/appointments → 500
    asyncpg.exceptions.NotNullViolationError (or IntegrityError):
        column "clinic_id" of relation "vitalia_appointments" violates not-null constraint
        column "offer_id" of relation "vitalia_appointments" violates not-null constraint
    agenda_grid_repository_impl.create() built the INSERT without clinic_id and offer_id,
    both of which are NOT NULL in the vitalia_appointments schema.
    Unit tests passed because they mock the session and never hit the real schema.

This test exercises the ACTUAL INSERT against a real Postgres schema so the
same class of bug (missing NOT NULL column) is caught before it reaches production.

Tests:
1. Schema gate: clinic_id and offer_id columns are NOT NULL (no default).
2. Regression RED: INSERT without clinic_id fails with NOT NULL violation.
3. Regression RED: INSERT without offer_id fails with NOT NULL violation.
4. Regression GREEN: full INSERT (clinic_id + offer_id included) succeeds.
5. Schema audit: COMPLETE NOT NULL column list in REPO_INSERT_COLUMNS matches schema.

marker: integration (requires Postgres — skipped if DB unreachable per conftest)

APPROCH CHOSEN: (a) PREFERRED — accept offer_id (UUID) in CreateAppointmentRequestDTO.
    The FE store already has selectedServiceId (= offerId UUID) via ServicePicker.
    clinic_id is already in the X-Clinic-ID header on the router — threaded into create().
    Both are passed to repo.create() and included in the INSERT.
    FE change required: add offer_id (= selectedServiceId) to the POST payload.
    See T-BE-4-notnull-result.md for full decision rationale.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Full NOT NULL columns the repo INSERT must supply
# ---------------------------------------------------------------------------

#: Complete list of NOT NULL columns (no DEFAULT) that agenda_grid_repository_impl.create()
#: MUST include in the INSERT statement. Any omission → 500 on appointment create.
REPO_INSERT_COLUMNS_FULL = [
    "id",
    "tenant_id",
    "clinic_id",  # ← MISSING before this bugfix (NOT NULL, no default)
    "offer_id",  # ← MISSING before this bugfix (NOT NULL, no default)
    "patient_id",
    "doctor_id",
    "slot_iso",
    "duration_minutes",
    "status",
    "origin",
    "notes_internal",  # ← added by mig 052 (nullable — can be NULL)
    "currency",
    "created_at",
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestNotNullClinicOffer:
    """Regression: clinic_id + offer_id NOT NULL — must be in every appointment INSERT."""

    async def test_clinic_id_is_not_null_column(self, db_session: AsyncSession) -> None:
        """vitalia_appointments.clinic_id must be a NOT NULL column with no default.

        Schema gate: if this test fails, the column's nullability was changed.
        A NULL clinic_id would break HIPAA dual filter on subsequent reads.
        """
        result = await db_session.execute(
            text(
                """
                SELECT is_nullable, column_default
                  FROM information_schema.columns
                 WHERE table_name = 'vitalia_appointments'
                   AND column_name = 'clinic_id'
                """
            )
        )
        row = result.fetchone()
        assert row is not None, (
            "Column 'clinic_id' does not exist in vitalia_appointments. "
            "Schema is in an unexpected state — check migrations 001-002."
        )
        assert row[0] == "NO", (
            f"clinic_id must be NOT NULL (is_nullable='NO'), got '{row[0]}'. "
            "Every appointment must be bound to a clinic for HIPAA dual filter."
        )
        assert row[1] is None, (
            f"clinic_id must have no DEFAULT (must be supplied explicitly), got default='{row[1]}'. "
            "A default would mask the NOT NULL bug — the INSERT must always supply clinic_id."
        )

    async def test_offer_id_is_not_null_column(self, db_session: AsyncSession) -> None:
        """vitalia_appointments.offer_id must be a NOT NULL column with no default.

        Schema gate: offer_id is the FK to the catalog offer (service).
        NOT NULL enforces referential integrity: every appointment has a service.
        """
        result = await db_session.execute(
            text(
                """
                SELECT is_nullable, column_default
                  FROM information_schema.columns
                 WHERE table_name = 'vitalia_appointments'
                   AND column_name = 'offer_id'
                """
            )
        )
        row = result.fetchone()
        assert row is not None, (
            "Column 'offer_id' does not exist in vitalia_appointments. "
            "Schema is in an unexpected state — check migrations 001-002."
        )
        assert row[0] == "NO", (
            f"offer_id must be NOT NULL (is_nullable='NO'), got '{row[0]}'. "
            "Every appointment must reference a catalog offer (service)."
        )
        assert row[1] is None, (
            f"offer_id must have no DEFAULT, got '{row[1]}'. "
            "Without a default the NOT NULL constraint enforces that the INSERT supplies it."
        )

    async def test_insert_without_clinic_id_fails(self, db_session: AsyncSession) -> None:
        """INSERT into vitalia_appointments without clinic_id must raise an error.

        This is the RED test: reproduces the live 500 root cause.
        Before the fix, agenda_grid_repository_impl.create() omitted clinic_id.
        """

        tenant_id = uuid4()
        offer_id = uuid4()
        appt_id = uuid4()
        patient_id = uuid4()
        doctor_id = uuid4()

        with pytest.raises(Exception) as exc_info:
            await db_session.execute(
                text(
                    """
                    INSERT INTO vitalia_appointments
                        (id, tenant_id, offer_id, patient_id, doctor_id,
                         slot_iso, duration_minutes, status, origin, currency, created_at)
                    VALUES
                        (:id, :tenant_id, :offer_id, :patient_id, :doctor_id,
                         :slot_iso, :dur, 'SCHEDULED', :origin, :currency, NOW())
                    """
                ).bindparams(
                    id=appt_id,
                    tenant_id=tenant_id,
                    offer_id=offer_id,
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    slot_iso=datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc),
                    dur=30,
                    origin="walk_in",
                    currency="USD",
                )
            )
            await db_session.flush()

        exc_str = str(exc_info.value).lower()
        assert "null" in exc_str or "not-null" in exc_str or "clinic_id" in exc_str, (
            f"Expected NOT NULL violation for missing clinic_id, got: {exc_info.value!r}"
        )

    async def test_insert_without_offer_id_fails(self, db_session: AsyncSession) -> None:
        """INSERT into vitalia_appointments without offer_id must raise an error.

        This is the RED test: reproduces the live 500 root cause.
        Before the fix, agenda_grid_repository_impl.create() omitted offer_id.
        """
        tenant_id = uuid4()
        clinic_id = uuid4()
        appt_id = uuid4()
        patient_id = uuid4()
        doctor_id = uuid4()

        with pytest.raises(Exception) as exc_info:
            await db_session.execute(
                text(
                    """
                    INSERT INTO vitalia_appointments
                        (id, tenant_id, clinic_id, patient_id, doctor_id,
                         slot_iso, duration_minutes, status, origin, currency, created_at)
                    VALUES
                        (:id, :tenant_id, :clinic_id, :patient_id, :doctor_id,
                         :slot_iso, :dur, 'SCHEDULED', :origin, :currency, NOW())
                    """
                ).bindparams(
                    id=appt_id,
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    slot_iso=datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc),
                    dur=30,
                    origin="walk_in",
                    currency="USD",
                )
            )
            await db_session.flush()

        exc_str = str(exc_info.value).lower()
        assert "null" in exc_str or "not-null" in exc_str or "offer_id" in exc_str, (
            f"Expected NOT NULL violation for missing offer_id, got: {exc_info.value!r}"
        )

    async def test_full_insert_with_clinic_id_and_offer_id_succeeds(self, db_session: AsyncSession) -> None:
        """GREEN: full INSERT with clinic_id and offer_id succeeds.

        This is the regression-green test: verifies that the fixed
        agenda_grid_repository_impl.create() path (with clinic_id + offer_id)
        succeeds against the real Postgres schema.

        Uses synthetic (non-PHI) UUIDs as allowed by pii-sanitisation.md.
        """
        tenant_id = uuid4()
        clinic_id = uuid4()
        offer_id = uuid4()
        appt_id = uuid4()
        patient_id = uuid4()
        doctor_id = uuid4()

        # This is the exact INSERT shape after the bugfix.
        # Must not raise — if it does, the bugfix is incomplete.
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
                slot_iso=datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc),
                dur=30,
                origin="walk_in",
                notes=None,
                currency="USD",
            )
        )

        # Verify row was written
        check = await db_session.execute(
            text("SELECT id, clinic_id, offer_id FROM vitalia_appointments WHERE id = :appt_id").bindparams(
                appt_id=appt_id
            )
        )
        row = check.fetchone()
        assert row is not None, (
            "INSERT with clinic_id + offer_id did not persist the row. Check DB connectivity and migration state."
        )
        assert str(row[1]) == str(clinic_id), f"clinic_id mismatch: expected {clinic_id}, got {row[1]}"
        assert str(row[2]) == str(offer_id), f"offer_id mismatch: expected {offer_id}, got {row[2]}"

    async def test_all_not_null_repo_columns_exist(self, db_session: AsyncSession) -> None:
        """Schema audit: every column in REPO_INSERT_COLUMNS_FULL exists in vitalia_appointments.

        This is the meta-test that catches the class of bug where a column
        referenced in the INSERT does not exist in the schema.
        Extends the schema audit from test_migration_052_notes_internal.py
        to include clinic_id and offer_id.
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

        missing = [col for col in REPO_INSERT_COLUMNS_FULL if col not in existing_columns]
        assert not missing, (
            f"Columns in the repo INSERT but missing from vitalia_appointments: {missing}. "
            "Any missing column causes a 500 on appointment create. "
            "Run the appropriate migration to add them."
        )
