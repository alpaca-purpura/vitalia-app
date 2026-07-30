# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""Postgres advisory locks for vitalia slot reservation.

Used by BookingService to prevent double-booking the same (doctor_id, slot_iso)
slot within the same tenant. Advisory locks are session-scoped (released on
session close or explicit release call).

Pattern: pg_advisory_lock (blocking) for create_booking flow;
         pg_try_advisory_lock (non-blocking) for race detection tests.

Lock key derivation: deterministic integer hash of (doctor_id, slot_iso)
via hashlib.sha256 → truncated to signed 64-bit int (Postgres bigint range).
"""

from __future__ import annotations

import hashlib
import struct
import uuid
from datetime import datetime

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


def _slot_lock_key(*, doctor_id: uuid.UUID, slot_iso: datetime) -> int:
    """Derive a deterministic Postgres advisory lock key for (doctor_id, slot_iso).

    Returns a signed 64-bit integer within Postgres bigint range [-2^63, 2^63-1].
    Combines doctor_id bytes + UTC slot timestamp bytes for collision resistance.
    """
    # Normalize slot to UTC epoch seconds (ignores microseconds for practical lock granularity)
    slot_ts = int(slot_iso.timestamp())

    raw = doctor_id.bytes + struct.pack(">q", slot_ts)
    digest = hashlib.sha256(raw).digest()

    # Take first 8 bytes → unsigned 64-bit int → convert to signed int
    unsigned = int.from_bytes(digest[:8], byteorder="big")
    # Convert to signed int64 (Postgres bigint)
    signed = unsigned if unsigned < 2**63 else unsigned - 2**64
    return signed


async def acquire_slot_advisory_lock(
    session: AsyncSession,
    *,
    doctor_id: uuid.UUID,
    slot_iso: datetime,
) -> None:
    """Acquire a blocking Postgres advisory lock for (doctor_id, slot_iso).

    Blocks until the lock is available. Lock is session-scoped — released when
    the session closes OR when release_slot_advisory_lock is called.

    Use this in BookingService.create_booking() before the slot availability check.
    Always call release_slot_advisory_lock() in a finally block.
    """
    key = _slot_lock_key(doctor_id=doctor_id, slot_iso=slot_iso)
    await session.execute(text("SELECT pg_advisory_lock(:key)"), {"key": key})
    logger.debug(
        "advisory_lock_acquired",
        doctor_id=str(doctor_id),
        slot_iso=slot_iso.isoformat(),
        lock_key=key,
    )


async def try_acquire_slot_advisory_lock(
    session: AsyncSession,
    *,
    doctor_id: uuid.UUID,
    slot_iso: datetime,
) -> bool:
    """Non-blocking attempt to acquire advisory lock for (doctor_id, slot_iso).

    Returns True if lock was acquired, False if lock is already held.
    Used in race-condition tests and as a fast-fail guard.
    """
    key = _slot_lock_key(doctor_id=doctor_id, slot_iso=slot_iso)
    result = await session.execute(text("SELECT pg_try_advisory_lock(:key)"), {"key": key})
    acquired: bool = result.scalar_one()
    logger.debug(
        "advisory_lock_try_acquire",
        doctor_id=str(doctor_id),
        slot_iso=slot_iso.isoformat(),
        lock_key=key,
        acquired=acquired,
    )
    return acquired


async def release_slot_advisory_lock(
    session: AsyncSession,
    *,
    doctor_id: uuid.UUID,
    slot_iso: datetime,
) -> None:
    """Release a previously acquired advisory lock for (doctor_id, slot_iso).

    Call this in a finally block after BookingService.create_booking() resolves.
    If the lock was never acquired, this is a no-op (pg_advisory_unlock returns false
    but does not raise an error).
    """
    key = _slot_lock_key(doctor_id=doctor_id, slot_iso=slot_iso)
    await session.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
    logger.debug(
        "advisory_lock_released",
        doctor_id=str(doctor_id),
        slot_iso=slot_iso.isoformat(),
        lock_key=key,
    )
