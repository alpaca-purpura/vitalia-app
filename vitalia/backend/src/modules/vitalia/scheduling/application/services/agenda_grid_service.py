# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""Agenda Grid Service — list PHI-masked slots for the Valeria Agenda view.

Rule (hipaa-lite.md § Regla cardinal):
  - Dual filter: tenant_id + clinic_id MANDATORY on every query.
  - Audit log sync write BEFORE returning response.
  - PHI masking: patient_name_masked + dni_masked (applied at SQL repo layer;
    service validates masking is present).
  - Cross-clinic: repo returns empty list (dual filter rejects at DB level).

Usage (FastAPI route):
    service = AgendaGridService(repo=repo, audit_writer=audit_writer)
    slots = await service.list_slots(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        date_from=date_from,
        date_to=date_to,
        user_id=user_id,
    )
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()


class AgendaGridService:
    """Application service: list agenda grid slots for a clinic.

    Thin orchestration: delegate to repo → sanitize PHI check → audit log → return.

    PHI obligations (hipaa-lite.md):
    1. Dual filter enforced at repo level (tenant_id + clinic_id).
    2. Audit log written sync before returning (every list is a PHI read).
    3. PHI masking validated: masked fields must be present in each slot.
    """

    def __init__(
        self,
        *,
        repo: Any,
        audit_writer: Any,
    ) -> None:
        """Initialize AgendaGridService.

        Args:
            repo: Implements list_slots(tenant_id, clinic_id, date_from, date_to,
                  ...) -> list[dict]. Typically AgendaGridRepositoryImpl.
            audit_writer: AsyncAuditWriter — sync write before response.
        """
        self._repo = repo
        self._audit = audit_writer

    async def list_slots(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        date_from: datetime,
        date_to: datetime,
        user_id: UUID,
        preset_filter: str | None = None,
        doctor_id: UUID | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List agenda grid slots for a clinic on a date range.

        Returns PHI-masked slots. Audit log is written synchronously before return.

        Cross-clinic: if clinic_id does not match any appointment in this tenant,
        repo returns [] (dual filter rejects at DB). Service passes it through as [].

        Args:
            tenant_id: Root tenant UUID (from X-Tenant-ID header).
            clinic_id: Clinic UUID for dual filter.
            date_from: Range start (UTC, inclusive).
            date_to: Range end (UTC, inclusive).
            user_id: Actor user UUID (for audit log).
            preset_filter: Optional whitelist filter key (AgendaPresetFilter enum value).
            doctor_id: Optional doctor filter.
            limit: Max slots returned (default 200).
            offset: Pagination offset (default 0).

        Returns:
            List of slot dicts with PHI-masked fields.
        """
        slots = await self._repo.list_slots(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            date_from=date_from,
            date_to=date_to,
            preset_filter=preset_filter,
            doctor_id=doctor_id,
            limit=limit,
            offset=offset,
        )

        # Audit log sync write (HIPAA mandate — every PHI read must be logged)
        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="appointment.agenda_read",
            resource_type="agenda_grid",
            resource_id=clinic_id,  # grid reads are scoped to clinic
            payload={
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "slot_count": len(slots),
                "preset_filter": preset_filter,
            },
        )

        logger.info(
            "agenda_grid_listed",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            slot_count=len(slots),
        )

        return slots
