"""Integration tests — BookingRepository.

TDD: Written RED before implementation exists.
Requires live Postgres + alembic upgrade head.

Acceptance criteria (T-be-3):
  A1: Cross-tenant query returns empty (tenant_A repo cannot read tenant_B rows)

Covers:
  - get_by_id filters tenant_id + deleted_at
  - list_by_patient filters tenant_id + deleted_at
  - list_by_doctor_slot returns active bookings for a specific (doctor, slot)
  - save persists a new booking
  - soft_delete sets deleted_at without destroying the row
  - cross_tenant_isolation: tenant_A BookingRepository cannot see tenant_B rows
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_booking_row(tenant_id: uuid.UUID, **overrides) -> dict:
    """Returns a dict of valid column values for INSERT INTO vitalia_bookings."""
    now = datetime.now(timezone.utc)
    defaults = {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "offer_id": uuid.uuid4(),
        "doctor_id": uuid.uuid4(),
        "patient_id": uuid.uuid4(),
        "consent_id": None,
        "slot_iso": now,
        "duration_minutes": 60,
        "status": "pending_payment",
        "payment_status": "not_initiated",
        "amount_paid": None,
        "amount_pending": None,
        "currency": "ARS",
        "deposit_percent": 30,
        "booking_metadata": {},
        "idempotency_key": str(uuid.uuid4()),
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }
    defaults.update(overrides)
    return defaults


async def _insert_booking(session, row: dict) -> None:
    """Raw INSERT — bypasses repository to set up test fixtures."""
    from sqlalchemy import text

    await session.execute(
        text("""
            INSERT INTO vitalia_bookings
            (id, tenant_id, offer_id, doctor_id, patient_id, consent_id,
             slot_iso, duration_minutes, status, payment_status,
             amount_paid, amount_pending, currency, deposit_percent,
             booking_metadata, idempotency_key, created_at, updated_at, deleted_at)
            VALUES
            (:id, :tenant_id, :offer_id, :doctor_id, :patient_id, :consent_id,
             :slot_iso, :duration_minutes, :status, :payment_status,
             :amount_paid, :amount_pending, :currency, :deposit_percent,
             :booking_metadata::jsonb, :idempotency_key, :created_at, :updated_at, :deleted_at)
        """),
        {**row, "booking_metadata": "{}"},
    )
    await session.flush()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_id_returns_booking(db_session) -> None:
    """get_by_id returns a booking row for the correct tenant."""
    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

    tenant_id = uuid.uuid4()
    row = _make_booking_row(tenant_id)
    await _insert_booking(db_session, row)

    repo = BookingRepository(session=db_session, tenant_id=tenant_id)
    result = await repo.get_by_id(row["id"])

    assert result is not None
    assert result.id == row["id"]
    assert result.tenant_id == tenant_id


@pytest.mark.asyncio
async def test_get_by_id_respects_deleted_at(db_session) -> None:
    """get_by_id returns None for soft-deleted rows."""
    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

    tenant_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    row = _make_booking_row(tenant_id, deleted_at=now)
    await _insert_booking(db_session, row)

    repo = BookingRepository(session=db_session, tenant_id=tenant_id)
    result = await repo.get_by_id(row["id"])

    assert result is None, "Soft-deleted booking must not be returned by get_by_id"


@pytest.mark.asyncio
async def test_cross_tenant_isolation(db_session) -> None:
    """A1 acceptance: tenant_A repo cannot see tenant_B rows."""
    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()

    row_b = _make_booking_row(tenant_b)
    await _insert_booking(db_session, row_b)

    # Repo scoped to tenant_A must NOT return tenant_B's booking
    repo_a = BookingRepository(session=db_session, tenant_id=tenant_a)
    result = await repo_a.get_by_id(row_b["id"])

    assert result is None, "Cross-tenant isolation violated: tenant_A repo returned tenant_B booking"


@pytest.mark.asyncio
async def test_list_by_patient_filters_tenant(db_session) -> None:
    """list_by_patient only returns rows belonging to the repo's tenant."""
    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    patient_id = uuid.uuid4()

    row_a = _make_booking_row(tenant_a, patient_id=patient_id)
    row_b = _make_booking_row(tenant_b, patient_id=patient_id)
    await _insert_booking(db_session, row_a)
    await _insert_booking(db_session, row_b)

    repo_a = BookingRepository(session=db_session, tenant_id=tenant_a)
    results = await repo_a.list_by_patient(patient_id)

    ids = [r.id for r in results]
    assert row_a["id"] in ids, "tenant_A booking must appear"
    assert row_b["id"] not in ids, "tenant_B booking must not appear for tenant_A repo"


@pytest.mark.asyncio
async def test_list_by_patient_excludes_deleted(db_session) -> None:
    """list_by_patient excludes soft-deleted rows."""
    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

    tenant_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    active_row = _make_booking_row(tenant_id, patient_id=patient_id)
    deleted_row = _make_booking_row(tenant_id, patient_id=patient_id, deleted_at=now)
    await _insert_booking(db_session, active_row)
    await _insert_booking(db_session, deleted_row)

    repo = BookingRepository(session=db_session, tenant_id=tenant_id)
    results = await repo.list_by_patient(patient_id)

    ids = [r.id for r in results]
    assert active_row["id"] in ids
    assert deleted_row["id"] not in ids


@pytest.mark.asyncio
async def test_save_persists_booking(db_session) -> None:
    """save() persists a new booking row via the model."""
    from src.modules.vitalia.infrastructure.models.booking_model import VitaliaBookingModel
    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

    tenant_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    model = VitaliaBookingModel(
        id=booking_id,
        tenant_id=tenant_id,
        offer_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        slot_iso=now,
        duration_minutes=45,
        status="confirmed_full",
        payment_status="not_initiated",
        booking_metadata={},
        created_at=now,
        updated_at=now,
    )

    repo = BookingRepository(session=db_session, tenant_id=tenant_id)
    await repo.save(model)

    fetched = await repo.get_by_id(booking_id)
    assert fetched is not None
    assert fetched.id == booking_id
    assert fetched.status == "confirmed_full"


@pytest.mark.asyncio
async def test_soft_delete_sets_deleted_at(db_session) -> None:
    """soft_delete sets deleted_at without hard-deleting the row."""
    from sqlalchemy import text

    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

    tenant_id = uuid.uuid4()
    row = _make_booking_row(tenant_id)
    await _insert_booking(db_session, row)

    repo = BookingRepository(session=db_session, tenant_id=tenant_id)
    await repo.soft_delete(row["id"])

    # get_by_id filters out deleted rows, so use raw SQL to verify row still exists
    result = await db_session.execute(
        text("SELECT deleted_at FROM vitalia_bookings WHERE id = :id"),
        {"id": row["id"]},
    )
    db_row = result.fetchone()
    assert db_row is not None, "Row must not be hard-deleted"
    assert db_row.deleted_at is not None, "deleted_at must be set after soft_delete"


@pytest.mark.asyncio
async def test_find_by_doctor_slot_returns_active_booking(db_session) -> None:
    """find_by_doctor_slot returns active booking for (doctor_id, slot_iso)."""
    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    slot = datetime(2026, 12, 1, 10, 0, 0, tzinfo=timezone.utc)

    row = _make_booking_row(
        tenant_id,
        doctor_id=doctor_id,
        slot_iso=slot,
        status="confirmed_deposit",
    )
    await _insert_booking(db_session, row)

    repo = BookingRepository(session=db_session, tenant_id=tenant_id)
    result = await repo.find_by_doctor_slot(doctor_id=doctor_id, slot_iso=slot)

    assert result is not None
    assert result.doctor_id == doctor_id


@pytest.mark.asyncio
async def test_find_by_doctor_slot_ignores_cancelled(db_session) -> None:
    """find_by_doctor_slot returns None for cancelled bookings (slot is free)."""
    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    slot = datetime(2026, 12, 1, 11, 0, 0, tzinfo=timezone.utc)

    row = _make_booking_row(
        tenant_id,
        doctor_id=doctor_id,
        slot_iso=slot,
        status="cancelled",
    )
    await _insert_booking(db_session, row)

    repo = BookingRepository(session=db_session, tenant_id=tenant_id)
    result = await repo.find_by_doctor_slot(doctor_id=doctor_id, slot_iso=slot)

    assert result is None, "Cancelled booking should not block the slot"
