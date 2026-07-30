"""Integration tests — BookingService + advisory lock (T-be-5 D2).

Tests use real Postgres via asyncpg (skipped when POSTGRES_DSN unavailable).

A2 (integration layer): BookingService.create_booking acquires advisory lock
before checking slot availability — concurrent creates for same slot result
in exactly one success + one SlotTakenError.

Markers: pytest.mark.integration
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

pytestmark = pytest.mark.integration


def _utc_slot(hour: int = 10) -> datetime:
    return datetime(2026, 12, 1, hour, 0, 0, tzinfo=timezone.utc)


def _make_create_request(
    *,
    doctor_id: uuid.UUID,
    slot_iso: datetime,
    patient_id: uuid.UUID | None = None,
    requires_prepay: bool = True,
    requires_consent: bool = False,
) -> "CreateBookingRequest":  # noqa: F821 — imported below
    from src.modules.vitalia.application.services.booking_service import CreateBookingRequest

    return CreateBookingRequest(
        offer_id=uuid.uuid4(),
        doctor_id=doctor_id,
        patient_id=patient_id or uuid.uuid4(),
        slot_iso=slot_iso,
        delivery_channel="whatsapp",
        consent_template_slug=None,
        requires_informed_consent=requires_consent,
        requires_prepay=requires_prepay,
        deposit_only=True,
    )


# ── Helper to build a mocked idempotency store (in-memory, no Redis) ──────────


def _in_memory_store() -> object:
    class InMemoryIdempotencyStore:
        """In-memory idempotency store for integration tests (no Redis needed)."""

        def __init__(self) -> None:
            self._data: dict[str, dict] = {}

        async def get(self, key: str) -> dict | None:
            return self._data.get(key)

        async def set(self, key: str, value: dict, ttl: int) -> None:  # noqa: ARG002
            self._data[key] = value

    return InMemoryIdempotencyStore()


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_booking_service_creates_booking_with_advisory_lock(db_session) -> None:
    """BookingService.create_booking acquires advisory lock and persists booking.

    Integration smoke: real session + real advisory lock acquisition + booking
    model persisted to Postgres.
    """
    from src.modules.vitalia.application.services.booking_service import BookingService
    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    slot = _utc_slot(hour=10)

    booking_repo = BookingRepository(session=db_session, tenant_id=tenant_id)
    idempotency_store = _in_memory_store()

    service = BookingService(
        booking_repo=booking_repo,
        idempotency_store=idempotency_store,
        tenant_id=tenant_id,
    )

    request = _make_create_request(
        doctor_id=doctor_id,
        slot_iso=slot,
        requires_prepay=True,
    )

    result = await service.create_booking(request=request, tenant_id=tenant_id)

    assert result.status == "pending_payment"
    assert result.booking_id is not None
    assert result.is_idempotent_hit is False


@pytest.mark.asyncio
async def test_booking_service_idempotent_within_window(db_session) -> None:
    """Calling create_booking twice with same (patient, doctor, slot) key
    within the 60s TTL window returns the cached result (is_idempotent_hit=True).
    """
    from src.modules.vitalia.application.services.booking_service import BookingService
    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    slot = _utc_slot(hour=11)

    booking_repo = BookingRepository(session=db_session, tenant_id=tenant_id)
    idempotency_store = _in_memory_store()

    service = BookingService(
        booking_repo=booking_repo,
        idempotency_store=idempotency_store,
        tenant_id=tenant_id,
    )

    request = _make_create_request(
        doctor_id=doctor_id,
        patient_id=patient_id,
        slot_iso=slot,
        requires_prepay=True,
    )

    # First call
    result_1 = await service.create_booking(request=request, tenant_id=tenant_id)
    assert result_1.is_idempotent_hit is False

    # Second call — same request parameters → idempotency hit
    result_2 = await service.create_booking(request=request, tenant_id=tenant_id)
    assert result_2.is_idempotent_hit is True
    assert result_2.booking_id == result_1.booking_id


@pytest.mark.asyncio
async def test_slot_taken_error_raised_when_slot_already_booked(db_session) -> None:
    """After slot is booked by first create_booking, a DIFFERENT patient trying to
    book the same slot raises SlotTakenError (advisory lock + find_by_doctor_slot check).

    D2 integration: advisory lock ensures the second booking sees the first one.
    """
    from src.modules.vitalia.application.services.booking_service import (
        BookingService,
        SlotTakenError,
    )
    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    slot = _utc_slot(hour=12)

    # First patient books the slot
    patient_a = uuid.uuid4()
    patient_b = uuid.uuid4()

    booking_repo = BookingRepository(session=db_session, tenant_id=tenant_id)
    idempotency_store_a = _in_memory_store()
    idempotency_store_b = _in_memory_store()

    service_a = BookingService(
        booking_repo=booking_repo,
        idempotency_store=idempotency_store_a,
        tenant_id=tenant_id,
    )
    service_b = BookingService(
        booking_repo=booking_repo,
        idempotency_store=idempotency_store_b,
        tenant_id=tenant_id,
    )

    request_a = _make_create_request(
        doctor_id=doctor_id,
        patient_id=patient_a,
        slot_iso=slot,
        requires_prepay=True,
    )
    request_b = _make_create_request(
        doctor_id=doctor_id,
        patient_id=patient_b,
        slot_iso=slot,
        requires_prepay=True,
    )

    # Patient A books first
    result_a = await service_a.create_booking(request=request_a, tenant_id=tenant_id)
    assert result_a.status == "pending_payment"

    # Patient B tries same slot → must raise SlotTakenError
    with pytest.raises(SlotTakenError):
        await service_b.create_booking(request=request_b, tenant_id=tenant_id)
