# cap: scheduling.mateo-agenda
"""Availability check domain — pure Python, no framework imports.

Defines:
  - TimeRange: half-open [start, end) interval value object with overlap logic (RN-2).
  - AvailabilityStatus: 4-state enum (available | busy | out_of_hours | no_schedule).
  - AvailabilityCheckResult: immutable frozen dataclass returned by check().

Half-open semantics (RN-2):
  Two appointments are overlapping iff: s1 < e2 AND s2 < e1.
  Back-to-back slots (10:00-10:30 and 10:30-11:00) do NOT overlap.
  This mirrors the EXCLUDE USING gist tstzrange(start, end, '[)') constraint in
  vitalia_appointment_clinic_map (migration 050, T-BE-2).

No PHI: AvailabilityCheckResult.conflict_label is a formatted time string only
  (e.g. "se solapa con 10:15") — NEVER contains patient name/ID.

03-arch-be.md § 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AvailabilityStatus(StrEnum):
    """Four possible states for a requested appointment slot (03-arch-be.md § 2)."""

    AVAILABLE = "available"
    BUSY = "busy"
    OUT_OF_HOURS = "out_of_hours"
    NO_SCHEDULE = "no_schedule"


@dataclass(frozen=True)
class TimeRange:
    """Half-open [start, end) interval. Both datetimes are UTC-aware.

    Overlap semantics (RN-2):
        Two ranges overlap iff self.start < other.end AND other.start < self.end.
        Back-to-back (10:00-10:30 and 10:30-11:00) → NOT overlapping.
    """

    start: datetime  # UTC tz-aware
    end: datetime  # UTC tz-aware (exclusive — half-open)

    def overlaps(self, other: "TimeRange") -> bool:
        """Return True if this range overlaps other (half-open [) semantics).

        Implements: start1 < end2 AND start2 < end1 (RN-2).

        Args:
            other: Another TimeRange to test against.

        Returns:
            True if the ranges overlap; False for back-to-back or fully disjoint.
        """
        return self.start < other.end and other.start < self.end

    def contains(self, other: "TimeRange") -> bool:
        """Return True if this range fully contains other (inclusive start, exclusive end).

        Used by AvailabilityCheckService to test whether proposed slot fits within
        a working-hours block.
        """
        return self.start <= other.start and other.end <= self.end


@dataclass(frozen=True)
class AvailabilityCheckResult:
    """Immutable result of an availability check (03-arch-be.md § 2).

    PHI safety: conflict_label and conflict_start carry scheduling time data only —
    NEVER patient name, phone, or any other PHI. The label is formatted as
    "se solapa con HH:MM" (time string only).
    """

    status: AvailabilityStatus
    conflict_label: str | None  # "se solapa con 10:15" — NO PHI
    conflict_start: datetime | None  # UTC datetime of conflicting block start
