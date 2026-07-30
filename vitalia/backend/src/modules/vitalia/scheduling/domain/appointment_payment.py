# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""AppointmentPayment — brand-local persisted payment record.

Tracks each payment transaction against a clinic appointment.
Supports optimistic locking (balance_version) per 03-arch A7 (SC-5 race condition).
Supports idempotency (idempotency_key = client-generated UUID) per 03-arch A8.

PHI context: appointment_id + clinic_id + tenant_id are the dual-filter anchors.
No patient PHI stored here (patient_name, DNI, etc. live in engine patient model).

Currency stored as cents (integer) per .claude/rules/currency-handling.md:
  amount_cents = 15000 → S/ 150.00 PEN
  Currency ISO code stored separately in `currency` field (NEVER defaults to 'USD').

Per 03-arch § 2.3 + vitalia/.claude/rules/hipaa-lite.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID


@dataclass(frozen=True)
class AppointmentPayment:
    """Brand-local payment record for appointment-level billing.

    Frozen: represents a committed payment state snapshot.
    Infrastructure layer creates mutable model; domain receives frozen projection.

    Optimistic lock: balance_version incremented on each charge attempt.
    Idempotency: idempotency_key (client UUID) prevents duplicate charges on retry.

    Attributes:
        id:                Unique payment record identifier.
        appointment_id:    FK to engine appointments.id.
        tenant_id:         Tenant identifier (dual filter key 1).
        clinic_id:         Clinic identifier (dual filter key 2 — HIPAA-lite).
        amount_cents:      Payment amount in smallest currency unit (cents).
        currency:          ISO 4217 currency code (PEN/ARS/MXN/USD/...).
        method:            PaymentMethod value (efectivo/tarjeta/transferencia/...).
        balance_version:   Optimistic lock version. Starts at 1.
        idempotency_key:   Client-generated UUID to prevent duplicate charges.
        status:            Payment status string (pending/completed/failed/refunded).
        created_at:        UTC creation timestamp (tz-aware).
    """

    id: UUID
    appointment_id: UUID
    tenant_id: UUID
    clinic_id: UUID
    amount_cents: int
    currency: str
    method: str
    balance_version: int
    idempotency_key: str | None
    status: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
