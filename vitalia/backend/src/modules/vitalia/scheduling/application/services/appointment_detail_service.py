# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""Appointment Detail Service — PHI-masked drawer detail + audit log.

Rule (hipaa-lite.md § Regla cardinal):
  - Dual filter: tenant_id + clinic_id MANDATORY.
  - Audit log sync write BEFORE returning response (PHI read).
  - Cross-clinic: repo returns None → raise AppointmentNotFoundError (404).
  - Even on 404 (suspicious cross-clinic attempt), audit log MUST be written.
  - PHI masking: validated at service layer (fields must be masked).
  - raw_patient_name / raw_dni / raw_phone NEVER returned in response dict.

Usage:
    service = AppointmentDetailService(repo=repo, audit_writer=audit_writer)
    detail = await service.get_detail(
        appointment_id=appt_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=user_id,
    )
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from src.modules.vitalia.scheduling.domain.exceptions import AppointmentNotFoundError

logger = structlog.get_logger()

# Keys that may contain raw PHI and must never be returned to the caller
_PHI_RAW_KEYS = frozenset(
    {
        "raw_patient_name",
        "raw_dni",
        "raw_phone",
        "raw_email",
        "patient_name",  # unmasked version; masked one is patient_name_masked
        "dni",  # unmasked; masked one is dni_masked
    }
)


class AppointmentDetailService:
    """Application service: get PHI-masked appointment drawer detail.

    Thin orchestration: repo lookup → audit log → PHI raw field strip → return.

    PHI obligations (hipaa-lite.md):
    1. Dual filter enforced at repo (tenant_id + clinic_id WHERE clause).
    2. Audit log written sync before returning (mandatory PHI read log).
    3. Even on cross-clinic 404, audit is written (suspicious access pattern).
    4. Raw PHI keys stripped from response dict before returning to caller.
    """

    def __init__(
        self,
        *,
        repo: Any,
        audit_writer: Any,
    ) -> None:
        """Initialize AppointmentDetailService.

        Args:
            repo: Implements get_by_id(entity_id, tenant_id, clinic_id) -> dict | None.
                Typically AppointmentDetailRepository.
            audit_writer: AsyncAuditWriter — sync write before response.
        """
        self._repo = repo
        self._audit = audit_writer

    async def get_detail(
        self,
        *,
        appointment_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any]:
        """Get PHI-masked appointment detail for the drawer.

        Audit log is always written before returning — including on 404
        (cross-clinic access attempt is a suspicious access event).

        Args:
            appointment_id: Target appointment UUID.
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID for dual filter.
            user_id: Actor user UUID (for audit log).

        Returns:
            Detail dict with PHI-masked fields (no raw PHI keys).

        Raises:
            AppointmentNotFoundError: If appointment not found for this
                tenant+clinic scope (cross-clinic or non-existent).
        """
        detail = await self._repo.get_by_id(
            appointment_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        # Always audit — even on not-found (suspicious access logging per HIPAA-lite)
        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="appointment.detail_read",
            resource_type="appointment",
            resource_id=appointment_id,
            payload={
                "found": detail is not None,
                "cross_clinic_attempt": detail is None,
            },
        )

        if detail is None:
            raise AppointmentNotFoundError(
                appointment_id=appointment_id,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
            )

        # Strip raw PHI keys — never expose unmasked fields
        return {k: v for k, v in detail.items() if k not in _PHI_RAW_KEYS}
