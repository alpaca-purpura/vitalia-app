"""Integration tests — advisory_locks (A2 acceptance criterion).

TDD: Written RED before implementation exists.

A2: Advisory lock prevents slot race — concurrent bookings for the same
(doctor_id, slot_iso) within the same tenant must result in exactly one
success and one failure (SlotTakenError or equivalent).

Tests are skipped automatically when Postgres is unavailable.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_advisory_lock_acquire_and_release(db_session) -> None:
    """Acquire then release advisory lock — no error on sequential access."""
    from src.modules.vitalia.infrastructure.advisory_locks import (
        acquire_slot_advisory_lock,
        release_slot_advisory_lock,
    )

    doctor_id = uuid.uuid4()
    slot = datetime(2026, 11, 1, 9, 0, 0, tzinfo=timezone.utc)

    # Should not raise
    await acquire_slot_advisory_lock(db_session, doctor_id=doctor_id, slot_iso=slot)
    await release_slot_advisory_lock(db_session, doctor_id=doctor_id, slot_iso=slot)


@pytest.mark.asyncio
async def test_slot_race_prevented(db_session) -> None:
    """A2 acceptance: second lock acquire for same slot fails while first is held.

    Uses pg_try_advisory_lock (non-blocking) to simulate concurrent requests.
    When tenant A holds the lock on (doctor, slot), a second attempt returns False.
    """
    from src.modules.vitalia.infrastructure.advisory_locks import (
        acquire_slot_advisory_lock,
        release_slot_advisory_lock,
        try_acquire_slot_advisory_lock,
    )

    doctor_id = uuid.uuid4()
    slot = datetime(2026, 11, 2, 14, 0, 0, tzinfo=timezone.utc)

    # First acquire (blocking) — succeeds
    await acquire_slot_advisory_lock(db_session, doctor_id=doctor_id, slot_iso=slot)

    # Second attempt (non-blocking) — must return False while first lock is held
    acquired = await try_acquire_slot_advisory_lock(db_session, doctor_id=doctor_id, slot_iso=slot)
    assert acquired is False, "A2 slot_race_prevented: second advisory lock acquire on same slot must fail"

    # Cleanup
    await release_slot_advisory_lock(db_session, doctor_id=doctor_id, slot_iso=slot)


@pytest.mark.asyncio
async def test_slot_lock_key_is_deterministic(db_session) -> None:
    """Same (doctor_id, slot_iso) always produces the same lock key."""
    from src.modules.vitalia.infrastructure.advisory_locks import _slot_lock_key

    doctor_id = uuid.uuid4()
    slot = datetime(2026, 11, 3, 10, 30, 0, tzinfo=timezone.utc)

    key1 = _slot_lock_key(doctor_id=doctor_id, slot_iso=slot)
    key2 = _slot_lock_key(doctor_id=doctor_id, slot_iso=slot)

    assert key1 == key2, "Lock key must be deterministic"


@pytest.mark.asyncio
async def test_different_slots_get_different_lock_keys() -> None:
    """Different (doctor_id, slot_iso) pairs produce different lock keys."""
    from src.modules.vitalia.infrastructure.advisory_locks import _slot_lock_key

    doctor_id = uuid.uuid4()
    slot_1 = datetime(2026, 11, 4, 10, 0, 0, tzinfo=timezone.utc)
    slot_2 = datetime(2026, 11, 4, 11, 0, 0, tzinfo=timezone.utc)

    key1 = _slot_lock_key(doctor_id=doctor_id, slot_iso=slot_1)
    key2 = _slot_lock_key(doctor_id=doctor_id, slot_iso=slot_2)

    assert key1 != key2, "Different slots must produce different lock keys"
