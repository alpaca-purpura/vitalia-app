# cap: scheduling.mateo-agenda
"""Availability API DTOs — T-BE-3 endpoints (03-arch-be.md § 7).

PHI contract: NO patient PHI in any DTO here. Availability = scheduling metadata only.
  - conflict_label: time string only ("se solapa con 10:15")
  - doctor_label: professional display name ("Dr. García"), not patient data
  - DayBlockItem: start/end times + block type only (no names, no IDs that link to patients)

All response DTOs use ConfigDict(from_attributes=True) per Pydantic v2.
response_model= enforced on every route (arch test enforces, pii-sanitisation.md).

03-arch-be.md § 7.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# POST /availability/check
# ---------------------------------------------------------------------------


class AvailabilityCheckRequest(BaseModel):
    """Request body for POST /availability/check."""

    doctor_id: UUID
    start: datetime = Field(..., description="Proposed appointment start (UTC ISO-8601)")
    duration_minutes: int = Field(..., gt=0, le=480, description="Appointment duration (1–480 min)")


class AvailabilityCheckResponse(BaseModel):
    """Availability check result — NO PHI.

    status: available | busy | out_of_hours | no_schedule
    conflict_label: human-readable time label when busy ("se solapa con 10:15")
    conflict_start: UTC datetime of conflicting block start (null unless busy)
    """

    model_config = ConfigDict(from_attributes=True)

    status: str  # AvailabilityStatus string value
    conflict_label: str | None = None
    conflict_start: datetime | None = None


# ---------------------------------------------------------------------------
# POST /availability/free-doctors
# ---------------------------------------------------------------------------


class FreeDoctorsRequest(BaseModel):
    """Request body for POST /availability/free-doctors."""

    start: datetime = Field(..., description="Proposed appointment start (UTC ISO-8601)")
    duration_minutes: int = Field(..., gt=0, le=480)


class FreeDoctorItem(BaseModel):
    """A doctor available for the requested slot. No PHI.

    doctor_label is professional display name ("Dr. García"), never patient data.
    """

    model_config = ConfigDict(from_attributes=True)

    doctor_id: UUID
    doctor_label: str


class FreeDoctorsResponse(BaseModel):
    """Response for POST /availability/free-doctors."""

    model_config = ConfigDict(from_attributes=True)

    doctors: list[FreeDoctorItem]
    count: int


# ---------------------------------------------------------------------------
# GET /availability/day-strip
# ---------------------------------------------------------------------------


class DayBlockItem(BaseModel):
    """A time block in the day-strip view — NO PHI.

    kind: working_hours | busy | unavailable
    Busy blocks contain only time data (no patient name/ID).
    """

    model_config = ConfigDict(from_attributes=True)

    kind: str  # "working_hours" | "busy" | "unavailable"
    start: datetime  # UTC
    end: datetime  # UTC


class DayStripResponse(BaseModel):
    """Response for GET /availability/day-strip — paints working + busy blocks.

    No PHI: busy blocks carry only start/end times (no patient references).
    FE uses this to render the visual time-strip in the nueva-cita picker.
    """

    model_config = ConfigDict(from_attributes=True)

    doctor_id: UUID
    date: date
    blocks: list[DayBlockItem]


# ---------------------------------------------------------------------------
# GET /availability/service-day (T-D1)
# ---------------------------------------------------------------------------


class ServiceDayDoctor(BaseModel):
    """One doctor's full-day strips for a service — NO PHI.

    doctor_label is professional display name ("Dr. García"), never patient data.
    Reuses DayBlockItem (working_hours | busy blocks, time-only).
    """

    model_config = ConfigDict(from_attributes=True)

    doctor_id: UUID
    doctor_label: str
    blocks: list[DayBlockItem]


class ServiceDayResponse(BaseModel):
    """Response for GET /availability/service-day — every doctor of a service on a day.

    No PHI: blocks carry only kind + start/end times. service_id is the offer
    (catalog) UUID, not a patient reference.
    """

    model_config = ConfigDict(from_attributes=True)

    service_id: UUID
    date: date
    doctors: list[ServiceDayDoctor]
