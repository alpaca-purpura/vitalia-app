# cap: crm.crm-consent-optout
# story-origin: TBD
"""Patient domain entity — PHI (Protected Health Information).

Domain layer — pure Python dataclass, no ORM imports.

Per hipaa-lite.md: Patient fields are PHI. Dual filter (tenant_id + clinic_id)
required on all queries. Audit log mandatory on all reads/writes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class Patient:
    """Patient domain entity.

    All fields marked [PHI] are Protected Health Information per hipaa-lite.md.
    These fields must be sanitized before logging and never returned to
    unauthorized roles.

    tenant_id + clinic_id dual filter enforced at repository layer.
    """

    id: UUID
    tenant_id: UUID
    clinic_id: UUID  # Required — dual filter mandatory for PHI

    # [PHI] Identity fields
    name: str
    date_of_birth: datetime | None = None
    dni: str | None = None  # National ID
    phone: str | None = None
    email: str | None = None
    address: str | None = None

    # Opt-out tracking (LGPD/HIPAA right to erasure)
    marketing_opt_out_at: datetime | None = None

    # Consent flags — added in migration 023 (T-1 Slice 1 fidelizacion)
    marketing_opt_in: bool = False
    opt_out: bool = False
    opt_out_reason: str | None = None
    opt_out_at: datetime | None = None

    # Soft delete
    deleted_at: datetime | None = None

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now())
    updated_at: datetime = field(default_factory=lambda: datetime.now())
