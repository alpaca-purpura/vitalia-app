# cap: lisa.servicios
"""DoctorRosterPort — cross-module read of the clinics doctor roster.

Cross-module access to ``clinics`` MUST go through this port (backend-ddd: no raw
cross-module imports). Used by SpecialistLinkService to verify a doctor exists
before linking (vincular ≠ crear doctor).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RosterDoctor:
    """Minimal doctor projection needed by the offer module (no PHI)."""

    id: UUID
    full_name: str
    specialty: str | None
    active: bool


class DoctorRosterPort(ABC):
    """Read-only roster lookups scoped to tenant + clinic."""

    @abstractmethod
    async def get_doctor(self, *, tenant_id: UUID, clinic_id: UUID, doctor_id: UUID) -> RosterDoctor | None:
        """Fetch one doctor. None if not found in the tenant/clinic scope."""

    @abstractmethod
    async def list_doctors(self, *, tenant_id: UUID, clinic_id: UUID) -> list[RosterDoctor]:
        """List active doctors for the clinic."""
