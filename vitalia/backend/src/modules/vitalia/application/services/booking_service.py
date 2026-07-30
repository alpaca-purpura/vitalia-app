# cap: booking.booking-widget-embed
# story-origin: TBD
"""BookingService — atomic slot reservation with pg_advisory_lock + idempotency.

Per 03-arch-be.md § 9.2:
  1. Idempotency check via (patient_id, doctor_id, target_slot) hash — 60s window.
  2. Acquire pg_advisory_lock(hash(doctor_id, slot_iso)) — blocks concurrent creates.
  3. find_by_doctor_slot → if exists → raise SlotTakenError.
  4. Status routing:
     a. requires_informed_consent → status=awaiting_consent + ConsentRequestedV1 (TODO T-be-6).
     b. requires_prepay → status=pending_payment + PaymentIntent created (TODO T-be-6).
     c. Neither → status=confirmed_deposit.
  5. Release advisory lock (always — finally block).
  6. Return BookingResult.

D1: Receives repos via DI — no direct session construction.
D2: pg_advisory_lock per (doctor_id, slot_iso) prevents race conditions.

Idempotency protocol:
  - Key: SHA-256(patient_id:doctor_id:slot_iso_utc_epoch) hex digest, 60s TTL.
  - Store interface: IdempotencyStoreProtocol (async get/set).
  - In tests: in-memory or MagicMock.
  - In production: Redis-backed store (luana-core-idempotency pattern).

Advisory lock protocol:
  - acquire_slot_advisory_lock from infrastructure.advisory_locks.
  - Always released in finally block (session-scoped Postgres lock).
  - Lock key is deterministic on (doctor_id, slot_iso) — cross-patient race safe.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Protocol

import structlog
from pydantic import BaseModel, ConfigDict

from src.modules.vitalia.infrastructure.advisory_locks import (
    acquire_slot_advisory_lock,
    release_slot_advisory_lock,
)
from src.modules.vitalia.infrastructure.models.booking_model import VitaliaBookingModel

if TYPE_CHECKING:
    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

logger = structlog.get_logger()

_IDEMPOTENCY_TTL_SECONDS = 60  # 60s window per T-be-5 spec A2
_KEY_PREFIX = "vitalia:booking"


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _booking_idempotency_key(
    *,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    slot_iso: datetime,
) -> str:
    """Derive a deterministic idempotency key for a booking attempt.

    Key format: ``vitalia:booking:<sha256_hex>``
    Combines patient_id, doctor_id, slot_iso UTC epoch seconds for uniqueness.
    """
    slot_ts = int(slot_iso.timestamp())
    raw = f"{patient_id!s}:{doctor_id!s}:{slot_ts}"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"{_KEY_PREFIX}:{digest}"


# ── Exceptions ────────────────────────────────────────────────────────────────


class SlotTakenError(Exception):
    """Raised when the requested (doctor_id, slot_iso) slot is already booked.

    Triggered inside advisory lock after find_by_doctor_slot returns a booking.
    Callers (API layer) translate this to HTTP 409 Conflict.
    """

    def __init__(self, doctor_id: uuid.UUID, slot_iso: datetime) -> None:
        self.doctor_id = doctor_id
        self.slot_iso = slot_iso
        super().__init__(f"Slot {slot_iso.isoformat()} for doctor {doctor_id} is already taken")


# ── Idempotency store protocol ────────────────────────────────────────────────


class IdempotencyStoreProtocol(Protocol):
    """Minimal interface for an idempotency backing store.

    Production: Redis-backed (luana-core-idempotency pattern).
    Tests: in-memory dict or MagicMock with AsyncMock get/set.
    """

    async def get(self, key: str) -> dict[str, Any] | None:
        """Return cached result dict or None if key absent / expired."""
        ...

    async def set(self, key: str, value: dict[str, Any], ttl: int) -> None:
        """Store value under key with TTL in seconds."""
        ...


# ── DTOs ──────────────────────────────────────────────────────────────────────


class CreateBookingRequest(BaseModel):
    """Input DTO for booking creation.

    Pydantic v2 — ConfigDict(from_attributes=True) for ORM-compat.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    offer_id: uuid.UUID
    doctor_id: uuid.UUID
    patient_id: uuid.UUID
    slot_iso: datetime
    delivery_channel: str  # "whatsapp" | "email" | "both"
    consent_template_slug: str | None = None
    requires_informed_consent: bool = False
    requires_prepay: bool = False
    deposit_only: bool = True


class BookingResult(BaseModel):
    """Output DTO for create_booking.

    Pydantic v2.
    """

    model_config = ConfigDict(from_attributes=True)

    booking_id: uuid.UUID
    status: str  # "awaiting_consent" | "pending_payment" | "confirmed_deposit"
    is_idempotent_hit: bool  # True when returned from idempotency cache
    payment_url: str | None = None
    consent_url: str | None = None


# ── Service ───────────────────────────────────────────────────────────────────


class BookingService:
    """Atomic slot reservation with advisory lock + 60s idempotency window.

    Usage (D1 — receive deps via DI, FastAPI Depends):
        svc = BookingService(
            booking_repo=BookingRepository(session=db, tenant_id=tid),
            idempotency_store=store,
            tenant_id=tid,
        )
        result = await svc.create_booking(request=req, tenant_id=tid)
    """

    def __init__(
        self,
        booking_repo: "BookingRepository",
        idempotency_store: IdempotencyStoreProtocol,
        tenant_id: uuid.UUID,
    ) -> None:
        self._booking_repo = booking_repo
        self._idempotency_store = idempotency_store
        self._tenant_id = tenant_id

    async def create_booking(
        self,
        request: CreateBookingRequest,
        tenant_id: uuid.UUID,
    ) -> BookingResult:
        """Atomic booking creation with advisory lock per (doctor_id, slot_iso).

        Algorithm (per 03-arch-be.md § 9.2):
        1. Idempotency check — return cached result if within 60s TTL.
        2. Acquire pg_advisory_lock(hash(doctor_id, slot_iso)).
        3. find_by_doctor_slot → if taken → raise SlotTakenError.
        4. Determine status from consent/prepay flags.
        5. Create VitaliaBookingModel + save via repo.
        6. Cache idempotency key (60s TTL).
        7. Release advisory lock (always, in finally).

        Args:
            request: CreateBookingRequest validated DTO.
            tenant_id: Authoritative tenant ID from request context (X-Tenant-ID header).

        Returns:
            BookingResult with booking_id, status, is_idempotent_hit.

        Raises:
            SlotTakenError: If (doctor_id, slot_iso) is already booked by another patient.
        """
        # ── Step 1: Idempotency short-circuit ────────────────────────────────
        idem_key = _booking_idempotency_key(
            patient_id=request.patient_id,
            doctor_id=request.doctor_id,
            slot_iso=request.slot_iso,
        )
        cached = await self._idempotency_store.get(idem_key)
        if cached is not None:
            logger.info(
                "booking_idempotent_hit",
                tenant_id=str(tenant_id),
                booking_id=cached.get("id"),
                status=cached.get("status"),
            )
            return BookingResult(
                booking_id=uuid.UUID(str(cached["id"])),
                status=str(cached["status"]),
                is_idempotent_hit=True,
            )

        # ── Steps 2–6: Advisory lock + creation (always release in finally) ──
        session = self._booking_repo._session  # noqa: SLF001 — service layer accesses repo internals
        acquired = False
        try:
            # Step 2: Acquire advisory lock
            await acquire_slot_advisory_lock(
                session,
                doctor_id=request.doctor_id,
                slot_iso=request.slot_iso,
            )
            acquired = True

            # Step 3: Slot availability check under lock
            existing = await self._booking_repo.find_by_doctor_slot(
                doctor_id=request.doctor_id,
                slot_iso=request.slot_iso,
            )
            if existing is not None:
                logger.warning(
                    "booking_slot_taken",
                    tenant_id=str(tenant_id),
                    doctor_id=str(request.doctor_id),
                    slot_iso=request.slot_iso.isoformat(),
                    existing_booking_id=str(existing.id),
                )
                raise SlotTakenError(
                    doctor_id=request.doctor_id,
                    slot_iso=request.slot_iso,
                )

            # Step 4: Determine status
            status = _determine_booking_status(
                requires_consent=request.requires_informed_consent,
                requires_prepay=request.requires_prepay,
            )

            # Step 5: Build and persist booking model
            now = _utc_now()
            booking_id = uuid.uuid4()
            model = VitaliaBookingModel(
                id=booking_id,
                tenant_id=tenant_id,
                offer_id=request.offer_id,
                doctor_id=request.doctor_id,
                patient_id=request.patient_id,
                slot_iso=request.slot_iso,
                duration_minutes=60,  # Default; overridden by offer config in T-be-7
                status=status,
                payment_status="not_initiated",
                idempotency_key=idem_key,
                created_at=now,
                updated_at=now,
            )
            await self._booking_repo.save(model)

            # Step 6: Cache idempotency result (60s TTL)
            cached_payload: dict[str, Any] = {
                "id": str(booking_id),
                "status": status,
            }
            await self._idempotency_store.set(idem_key, cached_payload, ttl=_IDEMPOTENCY_TTL_SECONDS)

            logger.info(
                "booking_created",
                tenant_id=str(tenant_id),
                booking_id=str(booking_id),
                doctor_id=str(request.doctor_id),
                status=status,
            )

            return BookingResult(
                booking_id=booking_id,
                status=status,
                is_idempotent_hit=False,
            )

        finally:
            # Step 7: Always release advisory lock
            if acquired:
                await release_slot_advisory_lock(
                    session,
                    doctor_id=request.doctor_id,
                    slot_iso=request.slot_iso,
                )


# ── Internal helpers ──────────────────────────────────────────────────────────


def _determine_booking_status(
    *,
    requires_consent: bool,
    requires_prepay: bool,
) -> str:
    """Determine initial booking status from consent + prepay flags.

    Priority order (per spec § 3.4 + 03-arch-be.md § 9.2):
    1. requires_consent → awaiting_consent (consent must precede payment).
    2. requires_prepay → pending_payment.
    3. Neither → confirmed_deposit (booking confirmed; payment collected on arrival).

    Returns:
        Status string: "awaiting_consent" | "pending_payment" | "confirmed_deposit"
    """
    if requires_consent:
        return "awaiting_consent"
    if requires_prepay:
        return "pending_payment"
    return "confirmed_deposit"
