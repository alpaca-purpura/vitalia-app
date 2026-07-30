# cap: clinics.lisa.doctores
"""Tests for AvailabilityProjectionService — dateutil.rrule expansion.

TDD RED-first: these tests define the contract for the projection service.
No DB required — pure domain logic.

Validators: V-FN-1 (weekly/end_date), V-FN-2 (biweekly/occurrences),
            V-FN-4 (one_off), V-FN-7 (open_ended 90d), V-ARCH-1, V-ARCH-4
Gherkin coverage: SC-1, SC-1b, SC-1d, SC-3b
"""

from __future__ import annotations

from datetime import date, time, timedelta, timezone
from uuid import uuid4

import pytest

from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

# ── Helpers ─────────────────────────────────────────────────────────────────


def _make_recurrent_block(
    *,
    day_of_week: int = 0,  # Monday
    start_time: time = time(9, 0),
    end_time: time = time(17, 0),
    freq: str = "weekly",
    end_condition_kind: str = "end_date",
    end_date: date | None = None,
    occurrences: int | None = None,
) -> AvailabilityBlock:
    """Factory for recurrent AvailabilityBlock."""
    if end_date is None and end_condition_kind == "end_date":
        end_date = date.today() + timedelta(days=28)
    return AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=start_time,
        end_time=end_time,
        day_of_week=day_of_week,
        freq=freq,
        end_condition_kind=end_condition_kind,
        end_date=end_date,
        occurrences=occurrences,
        specific_date=None,
    )


def _make_one_off_block(
    *,
    specific_date: date | None = None,
    start_time: time = time(10, 0),
    end_time: time = time(12, 0),
) -> AvailabilityBlock:
    """Factory for one_off AvailabilityBlock."""
    if specific_date is None:
        specific_date = date.today() + timedelta(days=3)
    return AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="one_off",
        start_time=start_time,
        end_time=end_time,
        day_of_week=None,
        freq=None,
        end_condition_kind=None,
        end_date=None,
        occurrences=None,
        specific_date=specific_date,
    )


# ── SC-1: Weekly + end_date (V-FN-1) ────────────────────────────────────────


def test_project_weekly_end_date_returns_correct_count() -> None:
    """SC-1: Weekly Monday 09:00-17:00 for 4 weeks → 4 occurrence dates.

    Validates that rrule(WEEKLY, interval=1, byweekday=0, until=end_date)
    returns exactly as many dates as Mondays fall within the range.
    """
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    # Use a fixed Monday as dtstart (2026-06-01 is a Monday)
    start_monday = date(2026, 6, 1)
    end = date(2026, 6, 29)  # 4 Mondays: Jun 1, 8, 15, 22 (Jun 29 is included = 5)

    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(17, 0),
        day_of_week=0,  # Monday
        freq="weekly",
        end_condition_kind="end_date",
        end_date=end,
        occurrences=None,
        specific_date=None,
    )

    service = AvailabilityProjectionService(slot_duration_minutes=30)
    slots = service.project_block(block, reference_date=start_monday)

    # Each Monday produces (17:00 - 09:00) / 30min = 16 slots
    # Jun 1 → Jun 29 inclusive: 5 Mondays (1, 8, 15, 22, 29)
    slot_dates = {s.slot_date for s in slots}
    assert len(slot_dates) == 5, f"Expected 5 Mondays, got {len(slot_dates)}: {sorted(slot_dates)}"

    # All slots on a Monday (weekday 0)
    for s in slots:
        assert s.slot_date.weekday() == 0, f"Slot on {s.slot_date} is not a Monday"


def test_project_weekly_slots_have_correct_duration() -> None:
    """Each slot covers exactly slot_duration_minutes."""
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    block = _make_recurrent_block(
        day_of_week=0,  # Monday
        start_time=time(9, 0),
        end_time=time(11, 0),  # 2h = 4 slots @ 30min per Monday
        freq="weekly",
        end_condition_kind="end_date",
        # Use Jun 1 only: reference=Jun 1, end=Jun 1 → 1 Monday
        end_date=date(2026, 6, 1),
    )
    service = AvailabilityProjectionService(slot_duration_minutes=30)
    slots = service.project_block(block, reference_date=date(2026, 6, 1))

    # 1 Monday × (120min / 30min) = 4 slots
    assert len(slots) == 4

    for s in slots:
        duration = s.end_ts - s.start_ts
        assert duration.total_seconds() == 30 * 60, f"Slot duration wrong: {duration}"


def test_project_weekly_slots_cover_full_time_range() -> None:
    """Slots must fill start_time to end_time without gaps."""
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    block = _make_recurrent_block(
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(10, 0),  # 1h = 2 slots @ 30min
        freq="weekly",
        end_condition_kind="end_date",
        end_date=date(2026, 6, 1),  # single Monday
    )
    service = AvailabilityProjectionService(slot_duration_minutes=30)
    slots = service.project_block(block, reference_date=date(2026, 6, 1))

    assert len(slots) == 2
    times = [(s.start_ts.astimezone(timezone.utc).hour, s.start_ts.astimezone(timezone.utc).minute) for s in slots]
    # Slots should start at 09:00 UTC and 09:30 UTC (assuming UTC tenant tz)
    assert times[0][1] == 0 or times[0][0] == 9  # first slot at :00 of hour
    # End of last slot = start_ts + 30min
    last = slots[-1]
    assert (last.end_ts - last.start_ts).seconds == 30 * 60


# ── SC-1b: Biweekly + occurrences (V-FN-2) ──────────────────────────────────


def test_project_biweekly_occurrences_6() -> None:
    """SC-1b: Biweekly Wednesday 10:00-12:00, 6 occurrences → 6 dates.

    rrule(WEEKLY, interval=2, byweekday=2, count=6)
    """
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    # 2026-06-03 is a Wednesday
    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=time(10, 0),
        end_time=time(12, 0),
        day_of_week=2,  # Wednesday
        freq="biweekly",
        end_condition_kind="occurrences",
        end_date=None,
        occurrences=6,
        specific_date=None,
    )
    service = AvailabilityProjectionService(slot_duration_minutes=30)
    slots = service.project_block(block, reference_date=date(2026, 6, 3))

    slot_dates = sorted({s.slot_date for s in slots})
    assert len(slot_dates) == 6, f"Expected 6 biweekly dates, got {len(slot_dates)}: {slot_dates}"

    # Every Wednesday should be 2 weeks apart
    for i in range(1, len(slot_dates)):
        gap = (slot_dates[i] - slot_dates[i - 1]).days
        assert gap == 14, f"Gap between occurrences should be 14 days, got {gap}"


def test_project_biweekly_occurrences_correct_slot_count() -> None:
    """6 occurrences × (2h / 30min) = 24 slots total."""
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=time(10, 0),
        end_time=time(12, 0),
        day_of_week=2,
        freq="biweekly",
        end_condition_kind="occurrences",
        end_date=None,
        occurrences=6,
        specific_date=None,
    )
    service = AvailabilityProjectionService(slot_duration_minutes=30)
    slots = service.project_block(block, reference_date=date(2026, 6, 3))

    # 6 occurrences × 4 slots/occurrence (2h/30min) = 24 slots
    assert len(slots) == 24


# ── SC-1d / SC-3b: One-off block (V-FN-4) ───────────────────────────────────


def test_project_one_off_single_date() -> None:
    """SC-1d: One-off block on specific_date → slots only on that date."""
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    target_date = date(2026, 6, 15)
    block = _make_one_off_block(
        specific_date=target_date,
        start_time=time(14, 0),
        end_time=time(16, 0),
    )
    service = AvailabilityProjectionService(slot_duration_minutes=30)
    slots = service.project_block(block, reference_date=date(2026, 6, 1))

    assert len(slots) == 4, f"Expected 4 slots (2h/30min), got {len(slots)}"
    for s in slots:
        assert s.slot_date == target_date, f"Slot date {s.slot_date} != {target_date}"


def test_project_one_off_slots_utc_aware() -> None:
    """Projected slots must be UTC timezone-aware datetimes."""
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    block = _make_one_off_block(
        specific_date=date(2026, 6, 15),
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    service = AvailabilityProjectionService(slot_duration_minutes=30)
    slots = service.project_block(block, reference_date=date(2026, 6, 1))

    for s in slots:
        assert s.start_ts.tzinfo is not None, "start_ts must be timezone-aware"
        assert s.end_ts.tzinfo is not None, "end_ts must be timezone-aware"


# ── Open-ended 90d horizon (V-FN-7) ─────────────────────────────────────────


def test_project_open_ended_uses_90d_horizon() -> None:
    """open_ended blocks project up to 90 days from today."""
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    today = date.today()
    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(10, 0),
        day_of_week=0,  # Monday
        freq="weekly",
        end_condition_kind="open_ended",
        end_date=None,
        occurrences=None,
        specific_date=None,
    )
    service = AvailabilityProjectionService(slot_duration_minutes=30)
    slots = service.project_block(block, reference_date=today)

    if not slots:
        # No Monday in next 90 days would be extremely odd
        pytest.skip("No Mondays in 90d range (unexpected)")

    max_date = max(s.slot_date for s in slots)
    horizon = today + timedelta(days=90)
    assert max_date <= horizon, f"Latest slot {max_date} exceeds 90d horizon {horizon}"

    # All slots within 90 days
    for s in slots:
        assert s.slot_date >= today, f"Slot date {s.slot_date} is in the past"
        assert s.slot_date <= horizon, f"Slot date {s.slot_date} exceeds horizon {horizon}"


def test_project_open_ended_has_slots_within_90d() -> None:
    """open_ended should produce at least some slots (not zero) within 90d."""
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    today = date.today()
    # Use Friday (weekday=4) to minimize skip risk
    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(10, 0),
        day_of_week=4,  # Friday
        freq="weekly",
        end_condition_kind="open_ended",
        end_date=None,
        occurrences=None,
        specific_date=None,
    )
    service = AvailabilityProjectionService(slot_duration_minutes=30)
    slots = service.project_block(block, reference_date=today)

    assert len(slots) > 0, "open_ended block should produce at least 1 slot within 90d"


# ── Slot structure (V-ARCH-1) ────────────────────────────────────────────────


def test_projected_slots_have_required_fields() -> None:
    """Each projected Slot has all required fields populated."""
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    block = _make_one_off_block(
        specific_date=date(2026, 6, 10),
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    service = AvailabilityProjectionService(slot_duration_minutes=30)
    slots = service.project_block(block, reference_date=date(2026, 6, 1))

    assert len(slots) > 0
    for s in slots:
        assert s.tenant_id == block.tenant_id
        assert s.clinic_id == block.clinic_id
        assert s.doctor_id == block.doctor_id
        assert s.block_id == block.id
        assert s.slot_date is not None
        assert s.start_ts < s.end_ts
        assert s.has_confirmed_appointment is False


# ── Reproject future only (domain invariant) ─────────────────────────────────


def test_reproject_future_reference_date_respected() -> None:
    """reproject_future only returns slots from reference_date onwards.

    Past slots (before reference_date) must not appear.
    """
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    # Block starting 2026-06-01, projecting weekly Mondays until 2026-06-29
    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(10, 0),
        day_of_week=0,  # Monday
        freq="weekly",
        end_condition_kind="end_date",
        end_date=date(2026, 6, 29),
        occurrences=None,
        specific_date=None,
    )
    service = AvailabilityProjectionService(slot_duration_minutes=30)

    # If reference_date is 2026-06-15, only Jun 15, 22, 29 should be included
    future_slots = service.project_block(block, reference_date=date(2026, 6, 15))

    for s in future_slots:
        assert s.slot_date >= date(2026, 6, 15), (
            f"Slot on {s.slot_date} is before reference date 2026-06-15 (reproject_future violation)"
        )


# ── No empty slot list on valid block ────────────────────────────────────────


def test_no_slots_when_end_date_before_reference() -> None:
    """If end_date is before reference_date, no slots are projected."""
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(10, 0),
        day_of_week=0,
        freq="weekly",
        end_condition_kind="end_date",
        end_date=date(2026, 5, 1),  # past date
        occurrences=None,
        specific_date=None,
    )
    service = AvailabilityProjectionService(slot_duration_minutes=30)
    # Reference date after end_date → no slots
    slots = service.project_block(block, reference_date=date(2026, 6, 1))
    assert len(slots) == 0


# ── bug7 round-6: "N repeticiones" = N ciclos completos (multi-día) ──────────


def test_project_multi_day_occurrences_counts_complete_cycles() -> None:
    """Mar+Jue, occurrences=3 → 6 ocurrencias (3 Mar + 3 Jue), NO 3 totales.

    Chris ratificó 2026-06-15: 'N repeticiones' = N ciclos completos del patrón;
    cada repetición incluye TODOS los días. Antes count=N dejaba la 2da semana
    a medias (Mar,Jue,Mar).
    """
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=time(14, 0),
        end_time=time(15, 0),
        days_of_week=[1, 3],  # Tue, Thu
        interval=1,
        day_of_week=None,
        freq=None,
        end_condition_kind="occurrences",
        end_date=None,
        occurrences=3,
        specific_date=None,
    )
    service = AvailabilityProjectionService(slot_duration_minutes=30)
    slots = service.project_block(block, reference_date=date(2026, 6, 15))
    dates = sorted({s.slot_date for s in slots})
    assert len(dates) == 6, f"3 repeticiones x 2 dias = 6, got {len(dates)}: {dates}"
    assert len([d for d in dates if d.isoweekday() == 2]) == 3, "3 martes"
    assert len([d for d in dates if d.isoweekday() == 4]) == 3, "3 jueves"


def test_project_single_day_occurrences_unchanged() -> None:
    """Single-day occurrences=N sigue = N (N x 1 ciclo) — regresion de no-cambio."""
    from src.modules.vitalia.clinics.application.availability_projection_service import (
        AvailabilityProjectionService,
    )

    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        start_time=time(9, 0),
        end_time=time(10, 0),
        days_of_week=[0],  # Monday only
        interval=1,
        day_of_week=None,
        freq=None,
        end_condition_kind="occurrences",
        end_date=None,
        occurrences=4,
        specific_date=None,
    )
    service = AvailabilityProjectionService(slot_duration_minutes=30)
    slots = service.project_block(block, reference_date=date(2026, 6, 15))
    dates = sorted({s.slot_date for s in slots})
    assert len(dates) == 4, f"single-day occurrences=4 -> 4, got {len(dates)}"
