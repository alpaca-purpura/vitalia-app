# cap: lisa.servicios
"""ServiceSpecialistLink — joins an offer to a doctor (vitalia_doctors roster).

Pure domain. Unique (offer_id, doctor_id) WHERE not soft-deleted (enforced at DB).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class ServiceSpecialistLink:
    """Link between an offer and a specialist doctor."""

    tenant_id: UUID
    offer_id: UUID
    doctor_id: UUID  # FK → vitalia_doctors (lisa-doctores roster)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime | None = None
    deleted_at: datetime | None = None
