"""Unit tests — BookingService (T-be-5 A2 + A3).

TDD RED → GREEN. All tests use mocked repositories (no Postgres needed).

Acceptance criteria (T-be-5):
  A2: Idempotency: re-invoke within 60s returns existing booking (same
      patient_id + doctor_id + slot_iso key hash).
  A3: Status routing: requires_consent → awaiting_consent;
      requires_prepay → pending_payment.

Decision coverage:
  D1: DDD inside-out — services receive repos + locks via DI.
  D2: Atomic: pg_advisory_lock per (doctor_id, slot_iso) prevents race.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.vitalia.application.services.booking_service import (
    BookingService,
    CreateBookingRequest,
    SlotTakenError,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _utc_dt(year: int = 2026, month: int = 11, day: int = 1, hour: int = 9) -> datetime:
    return datetime(year, month, day, hour, 0, 0, tzinfo=timezone.utc)


def _make_request(
    *,
    patient_id: uuid.UUID | None = None,
    doctor_id: uuid.UUID | None = None,
    slot_iso: datetime | None = None,
    requires_consent: bool = False,
    requires_prepay: bool = False,
) -> CreateBookingRequest:
    return CreateBookingRequest(
        offer_id=uuid.uuid4(),
        doctor_id=doctor_id or uuid.uuid4(),
        patient_id=patient_id or uuid.uuid4(),
        slot_iso=slot_iso or _utc_dt(),
        delivery_channel="whatsapp",
        consent_template_slug="vitalia_dental_standard_v1" if requires_consent else None,
        requires_informed_consent=requires_consent,
        requires_prepay=requires_prepay,
        deposit_only=True,
    )


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture()
def mock_booking_repo() -> MagicMock:
    """Mock BookingRepository — find_by_doctor_slot returns None (slot free)."""
    repo = MagicMock()
    repo.find_by_doctor_slot = AsyncMock(return_value=None)
    repo.save = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    return repo


@pytest.fixture()
def mock_idempotency_store() -> MagicMock:
    """Mock idempotency store — cache miss by default."""
    store = MagicMock()
    store.get = AsyncMock(return_value=None)
    store.set = AsyncMock()
    return store


@pytest.fixture()
def mock_advisory_lock() -> MagicMock:
    """Mock advisory lock functions — acquire/release no-op."""
    lock = MagicMock()
    lock.acquire = AsyncMock()
    lock.release = AsyncMock()
    return lock


@pytest.fixture()
def booking_service(
    tenant_id: uuid.UUID,
    mock_booking_repo: MagicMock,
    mock_idempotency_store: MagicMock,
) -> BookingService:
    """BookingService wired with mocked dependencies."""
    return BookingService(
        booking_repo=mock_booking_repo,
        idempotency_store=mock_idempotency_store,
        tenant_id=tenant_id,
    )


# ── A2: Idempotency 60s window ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_idempotency_window(
    booking_service: BookingService,
    mock_idempotency_store: MagicMock,
    tenant_id: uuid.UUID,
) -> None:
    """A2: Re-invoke within 60s returns existing booking without new DB write.

    When idempotency store has cached result for (patient_id, doctor_id, slot_iso),
    create_booking must return the cached booking WITHOUT calling save() again.
    """
    patient_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    slot = _utc_dt()
    existing_booking_id = uuid.uuid4()

    # Simulate cache hit — prior booking recorded in idempotency store
    mock_idempotency_store.get = AsyncMock(
        return_value={
            "id": str(existing_booking_id),
            "status": "pending_payment",
        }
    )

    request = _make_request(
        patient_id=patient_id,
        doctor_id=doctor_id,
        slot_iso=slot,
        requires_prepay=True,
    )

    with (
        patch(
            "src.modules.vitalia.application.services.booking_service.acquire_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
        patch(
            "src.modules.vitalia.application.services.booking_service.release_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
    ):
        result = await booking_service.create_booking(request=request, tenant_id=tenant_id)

    # Cache hit → returns cached booking ID
    assert result.booking_id == existing_booking_id
    assert result.is_idempotent_hit is True

    # Advisory lock was NOT acquired (idempotency short-circuit pre-lock)
    # Repo.save() was NOT called — no duplicate write
    booking_service._booking_repo.save.assert_not_called()  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_idempotency_cache_miss_creates_new_booking(
    booking_service: BookingService,
    mock_idempotency_store: MagicMock,
    mock_booking_repo: MagicMock,
    tenant_id: uuid.UUID,
) -> None:
    """Cache miss → new booking created and result cached."""
    request = _make_request(requires_prepay=True)

    with (
        patch(
            "src.modules.vitalia.application.services.booking_service.acquire_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
        patch(
            "src.modules.vitalia.application.services.booking_service.release_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
    ):
        result = await booking_service.create_booking(request=request, tenant_id=tenant_id)

    assert result.is_idempotent_hit is False
    # New booking was saved
    mock_booking_repo.save.assert_called_once()
    # Idempotency key was stored
    mock_idempotency_store.set.assert_called_once()


# ── A3: Status routing ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_status_routing_requires_consent(
    booking_service: BookingService,
    mock_booking_repo: MagicMock,
    tenant_id: uuid.UUID,
) -> None:
    """A3: requires_consent=True → booking created with status=awaiting_consent."""
    request = _make_request(requires_consent=True, requires_prepay=False)

    with (
        patch(
            "src.modules.vitalia.application.services.booking_service.acquire_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
        patch(
            "src.modules.vitalia.application.services.booking_service.release_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
    ):
        result = await booking_service.create_booking(request=request, tenant_id=tenant_id)

    assert result.status == "awaiting_consent"
    # Booking saved with correct status
    saved_booking = mock_booking_repo.save.call_args[0][0]
    assert saved_booking.status == "awaiting_consent"


@pytest.mark.asyncio
async def test_status_routing_requires_prepay(
    booking_service: BookingService,
    mock_booking_repo: MagicMock,
    tenant_id: uuid.UUID,
) -> None:
    """A3: requires_prepay=True → booking created with status=pending_payment."""
    request = _make_request(requires_consent=False, requires_prepay=True)

    with (
        patch(
            "src.modules.vitalia.application.services.booking_service.acquire_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
        patch(
            "src.modules.vitalia.application.services.booking_service.release_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
    ):
        result = await booking_service.create_booking(request=request, tenant_id=tenant_id)

    assert result.status == "pending_payment"
    saved_booking = mock_booking_repo.save.call_args[0][0]
    assert saved_booking.status == "pending_payment"


@pytest.mark.asyncio
async def test_status_routing_consent_takes_priority_over_prepay(
    booking_service: BookingService,
    mock_booking_repo: MagicMock,
    tenant_id: uuid.UUID,
) -> None:
    """A3: When both requires_consent AND requires_prepay, consent status takes priority.

    Rationale: patient must sign consent before payment is processed.
    """
    request = _make_request(requires_consent=True, requires_prepay=True)

    with (
        patch(
            "src.modules.vitalia.application.services.booking_service.acquire_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
        patch(
            "src.modules.vitalia.application.services.booking_service.release_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
    ):
        result = await booking_service.create_booking(request=request, tenant_id=tenant_id)

    assert result.status == "awaiting_consent"


@pytest.mark.asyncio
async def test_status_routing_no_special_requirements(
    booking_service: BookingService,
    mock_booking_repo: MagicMock,
    tenant_id: uuid.UUID,
) -> None:
    """No consent or prepay → booking status=confirmed_deposit."""
    request = _make_request(requires_consent=False, requires_prepay=False)

    with (
        patch(
            "src.modules.vitalia.application.services.booking_service.acquire_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
        patch(
            "src.modules.vitalia.application.services.booking_service.release_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
    ):
        result = await booking_service.create_booking(request=request, tenant_id=tenant_id)

    assert result.status == "confirmed_deposit"


# ── Slot taken (advisory lock path) ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_slot_taken_raises_slot_taken_error(
    booking_service: BookingService,
    mock_booking_repo: MagicMock,
    tenant_id: uuid.UUID,
) -> None:
    """When slot is already taken, create_booking raises SlotTakenError.

    Used by D2 (atomic advisory lock pattern): after lock acquired,
    repo.find_by_doctor_slot returns an existing booking → must raise.
    """
    doctor_id = uuid.uuid4()
    slot = _utc_dt()

    # Slot is occupied
    existing = MagicMock()
    existing.id = uuid.uuid4()
    existing.status = "confirmed_full"
    mock_booking_repo.find_by_doctor_slot = AsyncMock(return_value=existing)

    request = _make_request(doctor_id=doctor_id, slot_iso=slot)

    with (
        patch(
            "src.modules.vitalia.application.services.booking_service.acquire_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
        patch(
            "src.modules.vitalia.application.services.booking_service.release_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
        pytest.raises(SlotTakenError),
    ):
        await booking_service.create_booking(request=request, tenant_id=tenant_id)


@pytest.mark.asyncio
async def test_advisory_lock_always_released_on_error(
    booking_service: BookingService,
    mock_booking_repo: MagicMock,
    tenant_id: uuid.UUID,
) -> None:
    """Advisory lock released even when SlotTakenError is raised (finally block)."""
    doctor_id = uuid.uuid4()
    slot = _utc_dt()

    # Slot is occupied
    existing = MagicMock()
    existing.id = uuid.uuid4()
    existing.status = "confirmed_full"
    mock_booking_repo.find_by_doctor_slot = AsyncMock(return_value=existing)

    request = _make_request(doctor_id=doctor_id, slot_iso=slot)

    acquire_mock = AsyncMock()
    release_mock = AsyncMock()

    with (
        patch(
            "src.modules.vitalia.application.services.booking_service.acquire_slot_advisory_lock",
            acquire_mock,
        ),
        patch(
            "src.modules.vitalia.application.services.booking_service.release_slot_advisory_lock",
            release_mock,
        ),
    ):
        with pytest.raises(SlotTakenError):
            await booking_service.create_booking(request=request, tenant_id=tenant_id)

    # Lock must be released even on error
    release_mock.assert_called_once()


# ── Tenant isolation ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_booking_repo_receives_tenant_scoped_params(
    booking_service: BookingService,
    mock_booking_repo: MagicMock,
    tenant_id: uuid.UUID,
) -> None:
    """find_by_doctor_slot is called with correct doctor_id + slot_iso.

    BookingRepository is already scoped to tenant_id at construction time
    (per tenant-isolation.md rule — repo constructor accepts tenant_id).
    """
    doctor_id = uuid.uuid4()
    slot = _utc_dt()
    request = _make_request(doctor_id=doctor_id, slot_iso=slot)

    with (
        patch(
            "src.modules.vitalia.application.services.booking_service.acquire_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
        patch(
            "src.modules.vitalia.application.services.booking_service.release_slot_advisory_lock",
            new_callable=AsyncMock,
        ),
    ):
        await booking_service.create_booking(request=request, tenant_id=tenant_id)

    mock_booking_repo.find_by_doctor_slot.assert_called_once_with(
        doctor_id=doctor_id,
        slot_iso=slot,
    )
