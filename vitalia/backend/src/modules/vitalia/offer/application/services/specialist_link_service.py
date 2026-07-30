# cap: lisa.servicios
"""SpecialistLinkService — link/unlink doctors to a service (T-2 § 6).

Linking verifies the doctor exists in the roster through :class:`DoctorRosterPort`
(cross-module access to ``clinics`` ONLY via the port). It NEVER creates a doctor.
The roster read is dual-scoped (tenant_id + clinic_id); the link itself is
tenant-scoped (the catalog is NOT PHI). Unlink is idempotent.

G2-F13-BE: ``list_for_offer`` accepts an optional ``clinic_id``. When provided,
the service enriches each link with ``display_name`` + ``specialty`` from the
doctor roster (one ``list_doctors`` bulk call + fallback ``get_doctor`` for
missing entries). When ``clinic_id`` is absent or a doctor is not found, those
fields are ``None`` — the detail endpoint never breaks due to enrichment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from src.modules.vitalia.offer.application.ports.doctor_roster_port import DoctorRosterPort, RosterDoctor
from src.modules.vitalia.offer.domain.specialist_link import ServiceSpecialistLink


class DoctorNotInRosterError(Exception):
    """Raised when linking a doctor that is not in the clinic roster."""

    def __init__(self, doctor_id: UUID) -> None:
        super().__init__(f"Doctor {doctor_id} is not in the clinic roster.")
        self.doctor_id = doctor_id


@dataclass(frozen=True)
class EnrichedSpecialistLink:
    """A specialist link enriched with read-model data from the doctor roster.

    ``display_name`` and ``specialty`` are ``None`` when ``clinic_id`` was not
    supplied or when the doctor is no longer present in the roster.
    """

    id: UUID
    offer_id: UUID
    doctor_id: UUID
    display_name: str | None
    specialty: str | None


class _LinkRepo(Protocol):
    """Minimal repository contract used by this service."""

    async def link(self, link: ServiceSpecialistLink) -> ServiceSpecialistLink: ...
    async def list_by_offer(self, offer_id: UUID, *, tenant_id: UUID) -> list[ServiceSpecialistLink]: ...
    async def unlink(self, offer_id: UUID, doctor_id: UUID, *, tenant_id: UUID) -> None: ...


class SpecialistLinkService:
    """Manages the (offer ↔ doctor) links, gated by roster membership."""

    def __init__(self, *, roster: DoctorRosterPort, link_repo: _LinkRepo) -> None:
        self._roster = roster
        self._links = link_repo

    async def link(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        offer_id: UUID,
        doctor_id: UUID,
    ) -> ServiceSpecialistLink:
        """Link a doctor to an offer after verifying roster membership."""
        doctor = await self._roster.get_doctor(tenant_id=tenant_id, clinic_id=clinic_id, doctor_id=doctor_id)
        if doctor is None:
            raise DoctorNotInRosterError(doctor_id)
        link = ServiceSpecialistLink(tenant_id=tenant_id, offer_id=offer_id, doctor_id=doctor_id)
        return await self._links.link(link)

    async def list_for_offer(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        clinic_id: UUID | None = None,
    ) -> list[EnrichedSpecialistLink]:
        """Return enriched specialist links for an offer.

        When *clinic_id* is provided the service performs one ``list_doctors``
        call to build a lookup map, then falls back to ``get_doctor`` for any
        doctor_id not present in that bulk result (e.g. inactive doctors
        filtered by the roster implementation). Both ``display_name`` and
        ``specialty`` are ``None`` when the doctor cannot be resolved — the
        caller never breaks due to enrichment.
        """
        raw_links = await self._links.list_by_offer(offer_id, tenant_id=tenant_id)

        roster_map: dict[UUID, RosterDoctor] = {}
        if clinic_id is not None:
            doctors = await self._roster.list_doctors(tenant_id=tenant_id, clinic_id=clinic_id)
            roster_map = {d.id: d for d in doctors}

        enriched: list[EnrichedSpecialistLink] = []
        for link in raw_links:
            display_name: str | None = None
            specialty: str | None = None

            if clinic_id is not None:
                roster_doctor = roster_map.get(link.doctor_id)
                if roster_doctor is None:
                    # Fallback for doctors absent from bulk list (e.g. inactive).
                    roster_doctor = await self._roster.get_doctor(
                        tenant_id=tenant_id,
                        clinic_id=clinic_id,
                        doctor_id=link.doctor_id,
                    )
                if roster_doctor is not None:
                    display_name = roster_doctor.full_name
                    specialty = roster_doctor.specialty

            enriched.append(
                EnrichedSpecialistLink(
                    id=link.id,
                    offer_id=link.offer_id,
                    doctor_id=link.doctor_id,
                    display_name=display_name,
                    specialty=specialty,
                )
            )

        return enriched

    async def unlink(self, *, tenant_id: UUID, offer_id: UUID, doctor_id: UUID) -> None:
        """Remove a specialist link (idempotent)."""
        await self._links.unlink(offer_id, doctor_id, tenant_id=tenant_id)
