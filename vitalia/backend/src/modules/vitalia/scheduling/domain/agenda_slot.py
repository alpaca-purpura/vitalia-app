# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""AgendaSlot — frozen domain projection for the calendar cell.

NOT a SQLA table — this is a projection DTO derived from:
  - Appointment engine entity (via AppointmentDetailRepository)
  - AppointmentPayment brand-local records (balance computed)
  - PHI masking applied server-side (HIPAA-lite mandate)

PHI masking contract (HIPAA-lite dual-filter § 2.3):
  patient_name_masked — "P. Hernández" format (first initial + surname)
  dni_masked          — "12.***.***" format (first 2 digits visible)

The FE NEVER receives raw patient.name or patient.dni.
Masking is applied in AgendaSlotService before this object is created.

Per 03-arch § 2.2 + vitalia/.claude/rules/hipaa-lite.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AgendaSlot:
    """Domain projection representing a single calendar cell.

    Frozen: immutable once created (projection from query, never mutated).
    Not persisted — reconstructed per request from AppointmentRepository
    + AppointmentPaymentRepository join.

    Attributes:
        slot_id:             Synthetic display ID (appointment_id aliased for FE).
        appointment_id:      FK to engine appointments.id.
        tenant_id:           Tenant identifier (HIPAA dual filter 1st key).
        clinic_id:           Clinic identifier (HIPAA dual filter 2nd key).
        patient_name_masked: PHI-masked patient name (e.g. "P. Hernández").
        dni_masked:          PHI-masked DNI (e.g. "12.***.***").
        service:             Service label (e.g. "Limpieza dental"). Not PHI.
        doctor:              Doctor display name (e.g. "Dra. García"). Not PHI.
        start_at:            UTC tz-aware start datetime.
        end_at:              UTC tz-aware end datetime.
        payment_status:      SlotPaymentStatus value (color coding).
        origin:              AppointmentOrigin value (badge on cell).
        balance_amount_cents: Remaining balance in cents. None = unknown.
        currency:            ISO 4217 currency code (PEN/ARS/MXN/USD/...).
    """

    slot_id: UUID
    appointment_id: UUID
    tenant_id: UUID
    clinic_id: UUID
    patient_name_masked: str
    dni_masked: str
    service: str
    doctor: str
    start_at: datetime
    end_at: datetime
    payment_status: str
    origin: str
    balance_amount_cents: int | None
    currency: str
