# cap: lisa.servicios
"""DoctorRosterAdapter — read-only projection of the clinics roster.

Cross-module access to ``clinics`` happens ONLY through this port (no direct
import of the clinics domain into offer services). It wraps the clinics
``DoctorRepository`` read path and projects each ``Doctor`` into the slim
``RosterDoctor`` (id, full_name, specialty, active) — NO PHI fields leak out.
The roster is dual-scoped (tenant_id + clinic_id) like every clinics read.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.clinics.infrastructure.repositories.doctor_repository import DoctorRepository
from src.modules.vitalia.offer.application.ports.doctor_roster_port import DoctorRosterPort, RosterDoctor


class DoctorRosterAdapter(DoctorRosterPort):
    """Projects the clinics ``DoctorRepository`` read path into ``RosterDoctor``."""

    def __init__(self, session: AsyncSession) -> None:
        # KEKClient defaults to from_env() inside DoctorRepository — PHI columns
        # are decrypted there but we never surface them in the projection.
        self._repo = DoctorRepository(session)

    async def get_doctor(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
    ) -> RosterDoctor | None:
        doctor = await self._repo.get_by_id(doctor_id, tenant_id=tenant_id, clinic_id=clinic_id)
        return _project(doctor) if doctor is not None else None

    async def list_doctors(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> list[RosterDoctor]:
        doctors = await self._repo.list_by_filter(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            active=True,
        )
        return [_project(d) for d in doctors]


def _project(doctor: object) -> RosterDoctor:
    """Map a clinics ``Doctor`` to the slim roster projection (no PHI)."""
    return RosterDoctor(
        id=doctor.id,  # type: ignore[attr-defined]
        full_name=f"{doctor.first_name} {doctor.last_name}".strip(),  # type: ignore[attr-defined]
        specialty=doctor.specialty,  # type: ignore[attr-defined]
        active=doctor.active,  # type: ignore[attr-defined]
    )
