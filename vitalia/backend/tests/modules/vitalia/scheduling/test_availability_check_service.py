# cap: scheduling.mateo-agenda
"""TDD RED tests — AvailabilityCheckService: status matrix (T-BE-3).

Tests verify the 4-state matrix (AVAILABLE/BUSY/OUT_OF_HOURS/NO_SCHEDULE)
per 03-arch-be.md § 6 and gherkin scenarios:
  - SC-sin-horario: no working hours blocks → NO_SCHEDULE
  - SC-fuera-horario: proposed slot outside working hours → OUT_OF_HOURS
  - SC-solape: proposed slot overlaps busy range → BUSY (with conflict_label)
  - Happy path: proposed slot inside working hours, no conflicts → AVAILABLE
  - free_doctors: returns only doctors in AVAILABLE state
  - free_doctors empty: no doctors → empty list

Uses mocked AvailabilitySourcePort (D-B pattern — no cross-module import).
All tests are pure unit tests (no Postgres required).

Per 03-arch-be.md § 6, gherkin SC-sin-horario/SC-fuera-horario/SC-solape/SC-reasignar/
SC-reasignar-vacio, vitalia/.claude/rules/hipaa-lite.md (dual filter).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dt(h: int, m: int = 0) -> datetime:
    """UTC datetime at given hour:minute on 2026-07-01."""
    return datetime(2026, 7, 1, h, m, tzinfo=timezone.utc)


def _range(h_start: int, h_end: int, m_start: int = 0, m_end: int = 0):
    """Shorthand TimeRange factory."""
    from src.modules.vitalia.scheduling.domain.availability_check import TimeRange  # noqa: PLC0415

    return TimeRange(start=_dt(h_start, m_start), end=_dt(h_end, m_end))


TENANT_ID = uuid4()
CLINIC_ID = uuid4()
DOCTOR_ID = uuid4()
REQ_DAY = date(2026, 7, 1)


def _make_port(*, working_hours=None, busy_ranges=None, active_doctors=None) -> AsyncMock:
    """Build a mock AvailabilitySourcePort."""
    port = AsyncMock()
    port.get_working_hours.return_value = working_hours or []
    port.get_busy_ranges.return_value = busy_ranges or []
    port.list_active_doctors.return_value = active_doctors or []
    return port


def _make_service(port):
    """Instantiate AvailabilityCheckService with a mock port."""
    from src.modules.vitalia.scheduling.application.services.availability_check_service import (  # noqa: PLC0415
        AvailabilityCheckService,
    )

    return AvailabilityCheckService(port=port)


# ---------------------------------------------------------------------------
# check() matrix tests
# ---------------------------------------------------------------------------


class TestAvailabilityCheckService:
    """Status matrix per 03-arch-be.md § 6."""

    @pytest.mark.asyncio
    async def test_no_schedule_when_no_working_hours(self):
        """SC-sin-horario: no availability blocks → NO_SCHEDULE."""
        port = _make_port(working_hours=[])
        svc = _make_service(port)

        result = await svc.check(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            doctor_id=DOCTOR_ID,
            start=_dt(10),
            duration_minutes=30,
        )

        from src.modules.vitalia.scheduling.domain.availability_check import AvailabilityStatus  # noqa: PLC0415

        assert result.status == AvailabilityStatus.NO_SCHEDULE
        assert result.conflict_label is None
        assert result.conflict_start is None

    @pytest.mark.asyncio
    async def test_out_of_hours_when_proposed_outside_working_block(self):
        """SC-fuera-horario: proposed slot 15:00-15:30 outside 09:00-13:00 → OUT_OF_HOURS."""
        port = _make_port(working_hours=[_range(9, 13)])
        svc = _make_service(port)

        result = await svc.check(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            doctor_id=DOCTOR_ID,
            start=_dt(15),
            duration_minutes=30,
        )

        from src.modules.vitalia.scheduling.domain.availability_check import AvailabilityStatus  # noqa: PLC0415

        assert result.status == AvailabilityStatus.OUT_OF_HOURS

    @pytest.mark.asyncio
    async def test_busy_when_proposed_overlaps_busy_range(self):
        """SC-solape: proposed slot 10:00-10:30 overlaps busy 10:15-10:45 → BUSY."""
        port = _make_port(
            working_hours=[_range(9, 13)],
            busy_ranges=[_range(10, 10, 15, 45)],
        )
        svc = _make_service(port)

        result = await svc.check(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            doctor_id=DOCTOR_ID,
            start=_dt(10),
            duration_minutes=30,
        )

        from src.modules.vitalia.scheduling.domain.availability_check import AvailabilityStatus  # noqa: PLC0415

        assert result.status == AvailabilityStatus.BUSY
        # conflict_label must NOT contain PHI — only time info
        assert result.conflict_label is not None
        assert "10:15" in result.conflict_label
        assert result.conflict_start == _dt(10, 15)

    @pytest.mark.asyncio
    async def test_available_when_inside_working_hours_no_conflicts(self):
        """Happy path: 10:00-10:30 within 09:00-13:00, no busy → AVAILABLE."""
        port = _make_port(working_hours=[_range(9, 13)], busy_ranges=[])
        svc = _make_service(port)

        result = await svc.check(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            doctor_id=DOCTOR_ID,
            start=_dt(10),
            duration_minutes=30,
        )

        from src.modules.vitalia.scheduling.domain.availability_check import AvailabilityStatus  # noqa: PLC0415

        assert result.status == AvailabilityStatus.AVAILABLE
        assert result.conflict_label is None

    @pytest.mark.asyncio
    async def test_available_back_to_back_does_not_conflict(self):
        """RN-2: busy 10:00-10:30, proposed 10:30-11:00 → AVAILABLE (half-open)."""
        port = _make_port(
            working_hours=[_range(9, 13)],
            busy_ranges=[_range(10, 10, 0, 30)],
        )
        svc = _make_service(port)

        result = await svc.check(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            doctor_id=DOCTOR_ID,
            start=_dt(10, 30),
            duration_minutes=30,
        )

        from src.modules.vitalia.scheduling.domain.availability_check import AvailabilityStatus  # noqa: PLC0415

        assert result.status == AvailabilityStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_port_called_with_dual_filter(self):
        """Dual filter: port.get_working_hours and get_busy_ranges receive tenant_id + clinic_id."""
        port = _make_port(working_hours=[_range(9, 13)])
        svc = _make_service(port)

        await svc.check(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            doctor_id=DOCTOR_ID,
            start=_dt(10),
            duration_minutes=30,
        )

        port.get_working_hours.assert_called_once_with(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            doctor_id=DOCTOR_ID,
            day=REQ_DAY,
        )
        port.get_busy_ranges.assert_called_once_with(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            doctor_id=DOCTOR_ID,
            day=REQ_DAY,
        )


# ---------------------------------------------------------------------------
# free_doctors() tests
# ---------------------------------------------------------------------------


class TestFreeDoctors:
    """free_doctors() returns AVAILABLE doctors for a slot."""

    @pytest.mark.asyncio
    async def test_returns_only_available_doctors(self):
        """SC-reasignar: two doctors, one busy → only available one returned."""
        doctor_a = uuid4()
        doctor_b = uuid4()
        port = AsyncMock()
        port.list_active_doctors.return_value = [(doctor_a, "Dr. García"), (doctor_b, "Dra. López")]
        # doctor_a: free, doctor_b: busy at proposed slot
        port.get_working_hours.return_value = [_range(9, 13)]
        port.get_busy_ranges.side_effect = [
            [],  # doctor_a: no conflicts
            [_range(10, 10, 0, 30)],  # doctor_b: busy at 10:00-10:30
        ]

        svc = _make_service(port)

        result = await svc.free_doctors(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            start=_dt(10),
            duration_minutes=30,
        )

        assert len(result) == 1
        assert result[0].doctor_id == doctor_a
        assert result[0].doctor_label == "Dr. García"

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_doctors(self):
        """SC-reasignar-vacio: no active doctors → empty list."""
        port = AsyncMock()
        port.list_active_doctors.return_value = []
        svc = _make_service(port)

        result = await svc.free_doctors(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            start=_dt(10),
            duration_minutes=30,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_all_busy(self):
        """SC-reasignar-vacio: all doctors busy → empty list."""
        doctor_a = uuid4()
        port = AsyncMock()
        port.list_active_doctors.return_value = [(doctor_a, "Dr. García")]
        port.get_working_hours.return_value = [_range(9, 13)]
        port.get_busy_ranges.return_value = [_range(10, 10, 0, 30)]

        svc = _make_service(port)

        result = await svc.free_doctors(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            start=_dt(10),
            duration_minutes=30,
        )

        assert result == []
