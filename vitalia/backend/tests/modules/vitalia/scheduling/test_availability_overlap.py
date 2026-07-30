# cap: scheduling.mateo-agenda
"""TDD RED tests — AvailabilityCheck domain: half-open overlap logic (T-BE-3).

Tests verify TimeRange.overlaps() truth table per RN-2 (half-open [start, end)):
  - Back-to-back (10:00-10:30 vs 10:30-11:00) → NO overlap (RN-2 invariant)
  - Actual overlap (10:00-10:30 vs 10:15-10:45) → overlap
  - Same range → overlap
  - No-touch (10:00-10:30 vs 11:00-11:30) → NO overlap
  - Overlap at end (10:00-10:30 vs 10:25-11:00) → overlap
  - Superset (09:00-11:00 vs 10:00-10:30) → overlap
  - AvailabilityStatus enum values present
  - AvailabilityCheckResult is immutable (frozen dataclass)

Per 03-arch-be.md § 2 + RN-2 half-open semantics.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest


def _dt(h: int, m: int = 0) -> datetime:
    """UTC datetime at given hour:minute on 2026-07-01."""
    return datetime(2026, 7, 1, h, m, tzinfo=timezone.utc)


class TestTimeRangeOverlaps:
    """Truth table for half-open [start, end) overlap semantics (RN-2)."""

    def _make_range(self, h_start: int, h_end: int, m_start: int = 0, m_end: int = 0):
        from src.modules.vitalia.scheduling.domain.availability_check import TimeRange  # noqa: PLC0415

        return TimeRange(start=_dt(h_start, m_start), end=_dt(h_end, m_end))

    def test_back_to_back_does_not_overlap(self):
        """10:00-10:30 vs 10:30-11:00 → NOT overlapping (half-open — RN-2)."""
        r1 = self._make_range(10, 10, 0, 30)
        r2 = self._make_range(10, 11, 30, 0)
        assert not r1.overlaps(r2)
        assert not r2.overlaps(r1)

    def test_actual_overlap(self):
        """10:00-10:30 vs 10:15-10:45 → overlapping."""
        r1 = self._make_range(10, 10, 0, 30)
        r2 = self._make_range(10, 10, 15, 45)
        assert r1.overlaps(r2)
        assert r2.overlaps(r1)

    def test_same_range_overlaps(self):
        """Same range → overlapping."""
        r = self._make_range(10, 11, 0, 0)
        assert r.overlaps(r)

    def test_no_touch_no_overlap(self):
        """10:00-10:30 vs 11:00-11:30 → NOT overlapping."""
        r1 = self._make_range(10, 10, 0, 30)
        r2 = self._make_range(11, 11, 0, 30)
        assert not r1.overlaps(r2)
        assert not r2.overlaps(r1)

    def test_overlap_at_end(self):
        """10:00-10:30 vs 10:25-11:00 → overlapping (25 < 30 and 0 < 30)."""
        r1 = self._make_range(10, 10, 0, 30)
        r2 = self._make_range(10, 11, 25, 0)
        assert r1.overlaps(r2)

    def test_superset_overlaps(self):
        """09:00-11:00 vs 10:00-10:30 → overlapping."""
        r1 = self._make_range(9, 11)
        r2 = self._make_range(10, 10, 0, 30)
        assert r1.overlaps(r2)
        assert r2.overlaps(r1)

    def test_starts_exactly_at_end_no_overlap(self):
        """08:00-09:00 vs 09:00-10:00 — touches at end → NOT overlapping (half-open)."""
        r1 = self._make_range(8, 9)
        r2 = self._make_range(9, 10)
        assert not r1.overlaps(r2)

    def test_ends_exactly_at_start_no_overlap(self):
        """10:00-11:00 vs 09:00-10:00 — touches at start → NOT overlapping (half-open)."""
        r1 = self._make_range(10, 11)
        r2 = self._make_range(9, 10)
        assert not r1.overlaps(r2)


class TestAvailabilityStatus:
    """AvailabilityStatus enum sanity."""

    def test_status_values_present(self):
        from src.modules.vitalia.scheduling.domain.availability_check import AvailabilityStatus  # noqa: PLC0415

        assert AvailabilityStatus.AVAILABLE == "available"
        assert AvailabilityStatus.BUSY == "busy"
        assert AvailabilityStatus.OUT_OF_HOURS == "out_of_hours"
        assert AvailabilityStatus.NO_SCHEDULE == "no_schedule"


class TestAvailabilityCheckResult:
    """AvailabilityCheckResult domain value object."""

    def test_result_is_immutable(self):
        """AvailabilityCheckResult must be frozen (dataclass invariant)."""
        from src.modules.vitalia.scheduling.domain.availability_check import (  # noqa: PLC0415
            AvailabilityCheckResult,
            AvailabilityStatus,
        )

        result = AvailabilityCheckResult(
            status=AvailabilityStatus.AVAILABLE,
            conflict_label=None,
            conflict_start=None,
        )
        with pytest.raises((AttributeError, TypeError)):
            result.status = AvailabilityStatus.BUSY  # type: ignore[misc]

    def test_result_conflict_fields(self):
        from src.modules.vitalia.scheduling.domain.availability_check import (  # noqa: PLC0415
            AvailabilityCheckResult,
            AvailabilityStatus,
        )

        conflict_time = _dt(10, 15)
        result = AvailabilityCheckResult(
            status=AvailabilityStatus.BUSY,
            conflict_label="se solapa con 10:15",
            conflict_start=conflict_time,
        )
        assert result.status == AvailabilityStatus.BUSY
        assert result.conflict_label == "se solapa con 10:15"
        assert result.conflict_start == conflict_time
