# cap: scheduling.mateo-agenda
"""Integration test — list_active_doctors returns real doctor name (L3 fix).

Bug: AvailabilityQueryRepository.list_active_doctors returned placeholder
     "Dr. {uuid8}" instead of the doctor's actual name.
Root cause: plain DISTINCT select on vitalia_availability_slots with no JOIN
            to vitalia_doctors.
Fix: raw SQL JOIN on vitalia_doctors resolves first_name + last_name.

HB-108 compliance: tests use a REAL DB session (db_session fixture from conftest).
Mocking the repository would not catch an SQL JOIN bug — real Postgres required.

marker: integration (skipped if Postgres unavailable, per conftest auto-skip).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Seed helpers (synthetic data — no real PHI)
# ---------------------------------------------------------------------------


async def _insert_doctor(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    first_name: str,
    last_name: str,
) -> UUID:
    """Insert a minimal vitalia_doctors row and return its id."""
    doctor_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO vitalia_doctors
                (id, tenant_id, clinic_id, first_name, last_name,
                 credential_country, languages, active, visible_en_landing,
                 created_at)
            VALUES
                (:id, :tenant_id, :clinic_id, :first_name, :last_name,
                 'MX', '[]'::jsonb, true, false, NOW())
            """
        ),
        {
            "id": doctor_id,
            "tenant_id": tenant_id,
            "clinic_id": clinic_id,
            "first_name": first_name,
            "last_name": last_name,
        },
    )
    await session.flush()
    return doctor_id


async def _insert_slot(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    doctor_id: UUID,
    slot_date: date,
) -> None:
    """Insert a minimal vitalia_availability_slots row."""
    start_ts = datetime(slot_date.year, slot_date.month, slot_date.day, 9, 0, tzinfo=timezone.utc)
    end_ts = start_ts.replace(hour=17)
    await session.execute(
        text(
            """
            INSERT INTO vitalia_availability_slots
                (id, tenant_id, clinic_id, doctor_id, slot_date,
                 start_ts, end_ts, has_confirmed_appointment, created_at)
            VALUES
                (:id, :tenant_id, :clinic_id, :doctor_id, :slot_date,
                 :start_ts, :end_ts, false, NOW())
            """
        ),
        {
            "id": uuid4(),
            "tenant_id": tenant_id,
            "clinic_id": clinic_id,
            "doctor_id": doctor_id,
            "slot_date": slot_date,
            "start_ts": start_ts,
            "end_ts": end_ts,
        },
    )
    await session.flush()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_A = uuid4()
TENANT_B = uuid4()
CLINIC_A = uuid4()
CLINIC_B = uuid4()
_SLOT_DATE = date(2026, 8, 1)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestListActiveDoctorsRealName:
    """list_active_doctors joins vitalia_doctors and returns real names (L3 fix)."""

    async def test_returns_real_first_and_last_name(self, db_session: AsyncSession) -> None:
        """Happy path: doctor with first_name + last_name → label = 'Nombre Apellido'."""
        # SEED
        doctor_id = await _insert_doctor(
            db_session,
            tenant_id=TENANT_A,
            clinic_id=CLINIC_A,
            first_name="María",
            last_name="González",
        )
        await _insert_slot(
            db_session,
            tenant_id=TENANT_A,
            clinic_id=CLINIC_A,
            doctor_id=doctor_id,
            slot_date=_SLOT_DATE,
        )

        # CALL REAL REPO (bug lives in SQL JOIN — mock would hide it)
        from src.modules.vitalia.scheduling.infrastructure.repositories.availability_query_repository import (  # noqa: PLC0415
            AvailabilityQueryRepository,
        )

        repo = AvailabilityQueryRepository(session=db_session)
        results = await repo.list_active_doctors(tenant_id=TENANT_A, clinic_id=CLINIC_A)

        # ASSERT: real name, NOT "Dr. {8hex}"
        assert len(results) == 1
        result_id, result_label = results[0]
        assert result_id == doctor_id
        assert result_label == "María González", (
            f"Expected 'María González', got {result_label!r} — placeholder bug still present"
        )
        # Regression guard: must NOT look like the old placeholder pattern
        assert not result_label.startswith("Dr. "), f"Label {result_label!r} looks like the old UUID-based placeholder"

    async def test_doctor_without_name_returns_sin_asignar(self, db_session: AsyncSession) -> None:
        """Edge case: no vitalia_doctors row (slot with orphan doctor_id) → 'Sin asignar'."""
        orphan_doctor_id = uuid4()  # no row in vitalia_doctors
        await _insert_slot(
            db_session,
            tenant_id=TENANT_A,
            clinic_id=CLINIC_A,
            doctor_id=orphan_doctor_id,
            slot_date=_SLOT_DATE,
        )

        from src.modules.vitalia.scheduling.infrastructure.repositories.availability_query_repository import (  # noqa: PLC0415
            AvailabilityQueryRepository,
        )

        repo = AvailabilityQueryRepository(session=db_session)
        results = await repo.list_active_doctors(tenant_id=TENANT_A, clinic_id=CLINIC_A)

        # Find our orphan slot result
        matched = [(rid, lbl) for rid, lbl in results if rid == orphan_doctor_id]
        assert len(matched) == 1
        _id, label = matched[0]
        assert label == "Sin asignar", f"Expected 'Sin asignar' for orphan doctor, got {label!r}"

    async def test_cross_tenant_isolation_not_visible(self, db_session: AsyncSession) -> None:
        """Dual filter L1: doctors of TENANT_B not visible when queried for TENANT_A."""
        doctor_b_id = await _insert_doctor(
            db_session,
            tenant_id=TENANT_B,
            clinic_id=CLINIC_B,
            first_name="Juan",
            last_name="Pérez",
        )
        await _insert_slot(
            db_session,
            tenant_id=TENANT_B,
            clinic_id=CLINIC_B,
            doctor_id=doctor_b_id,
            slot_date=_SLOT_DATE,
        )

        from src.modules.vitalia.scheduling.infrastructure.repositories.availability_query_repository import (  # noqa: PLC0415
            AvailabilityQueryRepository,
        )

        repo = AvailabilityQueryRepository(session=db_session)
        # Query with TENANT_A — must not see TENANT_B doctors
        results_a = await repo.list_active_doctors(tenant_id=TENANT_A, clinic_id=CLINIC_A)
        ids = [r[0] for r in results_a]
        assert doctor_b_id not in ids, "Cross-tenant leak: TENANT_B doctor visible to TENANT_A"

    async def test_cross_clinic_isolation_not_visible(self, db_session: AsyncSession) -> None:
        """Dual filter L2: doctor slot in CLINIC_B not visible when querying CLINIC_A (same tenant)."""
        doctor_c_id = await _insert_doctor(
            db_session,
            tenant_id=TENANT_A,
            clinic_id=CLINIC_B,  # different clinic, same tenant
            first_name="Ana",
            last_name="Martínez",
        )
        await _insert_slot(
            db_session,
            tenant_id=TENANT_A,
            clinic_id=CLINIC_B,
            doctor_id=doctor_c_id,
            slot_date=_SLOT_DATE,
        )

        from src.modules.vitalia.scheduling.infrastructure.repositories.availability_query_repository import (  # noqa: PLC0415
            AvailabilityQueryRepository,
        )

        repo = AvailabilityQueryRepository(session=db_session)
        # Query CLINIC_A — must not see CLINIC_B doctor
        results_clinic_a = await repo.list_active_doctors(tenant_id=TENANT_A, clinic_id=CLINIC_A)
        ids = [r[0] for r in results_clinic_a]
        assert doctor_c_id not in ids, "Cross-clinic leak: CLINIC_B doctor visible to CLINIC_A"

    async def test_deleted_slot_excluded(self, db_session: AsyncSession) -> None:
        """Soft-delete: slot with deleted_at set must not appear in results."""
        doctor_del_id = await _insert_doctor(
            db_session,
            tenant_id=TENANT_A,
            clinic_id=CLINIC_A,
            first_name="Carlos",
            last_name="Ruiz",
        )
        # Insert slot then soft-delete it
        slot_id = uuid4()
        start_ts = datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc)
        await db_session.execute(
            text(
                """
                INSERT INTO vitalia_availability_slots
                    (id, tenant_id, clinic_id, doctor_id, slot_date,
                     start_ts, end_ts, has_confirmed_appointment, created_at, deleted_at)
                VALUES
                    (:id, :tenant_id, :clinic_id, :doctor_id, :slot_date,
                     :start_ts, :end_ts, false, NOW(), NOW())
                """
            ),
            {
                "id": slot_id,
                "tenant_id": TENANT_A,
                "clinic_id": CLINIC_A,
                "doctor_id": doctor_del_id,
                "slot_date": date(2026, 8, 2),
                "start_ts": start_ts,
                "end_ts": start_ts.replace(hour=17),
            },
        )
        await db_session.flush()

        from src.modules.vitalia.scheduling.infrastructure.repositories.availability_query_repository import (  # noqa: PLC0415
            AvailabilityQueryRepository,
        )

        repo = AvailabilityQueryRepository(session=db_session)
        results = await repo.list_active_doctors(tenant_id=TENANT_A, clinic_id=CLINIC_A)
        ids = [r[0] for r in results]
        assert doctor_del_id not in ids, "Soft-deleted slot's doctor leaked into results"
