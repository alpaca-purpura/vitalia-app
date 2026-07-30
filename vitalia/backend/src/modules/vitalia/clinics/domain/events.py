# cap: configuracion.cuenta
"""Vitalia Clinic domain events — pure Python, no framework imports.

Domain events are emitted by services when significant state changes occur.
They are dispatched best-effort (try/except on emit — never block the main flow).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID


@dataclass(frozen=True)
class ClinicSpecialtiesChanged:
    """Emitted when a clinic's primary specialties list changes.

    Used to trigger downstream side-effects (e.g., re-index RAG catalog,
    update recommendation engine). Dispatched best-effort.

    Attributes:
        tenant_id: Tenant owning the clinic.
        clinic_id: Clinic whose specialties changed.
        previous_specialties: Specialty IDs before the change.
        new_specialties: Specialty IDs after the change.
        changed_by: User ID who triggered the change.
        occurred_at: UTC timestamp of the change.
    """

    tenant_id: UUID
    clinic_id: UUID
    previous_specialties: tuple[str, ...]
    new_specialties: tuple[str, ...]
    changed_by: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
