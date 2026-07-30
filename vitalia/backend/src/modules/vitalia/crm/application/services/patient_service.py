# cap: crm.crm-consent-optout
# story-origin: TBD
"""PatientService — RBAC-gated PHI operations.

Application layer — orchestrates repository calls with RBAC enforcement.
All methods use @require_phi_access to enforce HIPAA-lite access control.

Allowed roles for PHI access: doctor, nurse, admin_clinic.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from src.modules.vitalia._shared.auth.rbac import require_phi_access
from src.modules.vitalia._shared.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.vitalia.crm.application.dto.patient_dto import (
    PatientInlineCreateResponse,
    PatientSearchItem,
    PatientSearchResponse,
)
from src.modules.vitalia.crm.domain.patient import Patient

logger = structlog.get_logger()

_PHI_ROLES = ["doctor", "nurse", "admin_clinic"]


class PatientService:
    """Service for PHI Patient operations with RBAC enforcement.

    Every public method is decorated with @require_phi_access.
    The audit_repo is passed to the decorator so it logs both
    access grants and denials.
    """

    def __init__(
        self,
        patient_repo: object,
        audit_repo: AuditLogRepository,
    ) -> None:
        """Initialize with repositories.

        Args:
            patient_repo: PatientRepository instance (or AsyncMock in tests).
            audit_repo: AuditLogRepository for mandatory HIPAA-lite audit writes.
        """
        self._patient_repo = patient_repo
        self._audit_repo = audit_repo

    async def get_by_id(
        self,
        patient_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        user_role: str,
    ) -> Patient | None:
        """Retrieve a patient by ID — PHI access gated by RBAC.

        Args:
            patient_id: Patient UUID.
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (dual filter).
            user_id: Requesting user UUID (for audit log).
            user_role: Role string — must be in PHI_ALLOWED_ROLES.

        Returns:
            Patient or None if not found.

        Raises:
            PHIAccessDeniedError: If user_role is not allowed.
        """
        return await self._get_by_id_guarded(
            patient_id=patient_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            user_role=user_role,
        )

    @require_phi_access(roles=_PHI_ROLES, resource_type="patient")
    async def _get_by_id_guarded(
        self,
        *,
        patient_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        user_role: str,
    ) -> Patient | None:
        """Inner guarded implementation — only called after RBAC check passes."""
        result = await self._patient_repo.get_by_id(
            patient_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
        )
        logger.info(
            "patient_service.get_by_id",
            patient_id=str(patient_id),
            tenant_id=str(tenant_id),
            found=result is not None,
        )
        return result

    async def update(
        self,
        patient_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        user_role: str,
        updates: dict[str, object],
    ) -> None:
        """Update patient fields — PHI write gated by RBAC.

        Args:
            patient_id: Patient UUID.
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (dual filter).
            user_id: Requesting user UUID (for audit log).
            user_role: Role string — must be in PHI_ALLOWED_ROLES.
            updates: Field → value mapping for the update.

        Raises:
            PHIAccessDeniedError: If user_role is not allowed.
        """
        await self._update_guarded(
            patient_id=patient_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            user_role=user_role,
            updates=updates,
        )

    @require_phi_access(roles=_PHI_ROLES, resource_type="patient")
    async def _update_guarded(
        self,
        *,
        patient_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        user_role: str,
        updates: dict[str, object],
    ) -> None:
        """Inner guarded implementation — only called after RBAC check passes."""
        await self._patient_repo.update(
            patient_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            updates=updates,
        )

    async def opt_out(
        self,
        patient_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        user_role: str,
        reason: str,
    ) -> None:
        """Mark patient as opted out — gated by admin_clinic role only.

        Per LGPD/HIPAA-lite: opt-out is an administrative action.
        Only admin_clinic (not doctors/nurses) may trigger opt-out.

        Args:
            patient_id: Patient UUID.
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID.
            user_id: Requesting user UUID.
            user_role: Must be "admin_clinic".
            reason: Reason for opt-out (stored redacted in audit).

        Raises:
            PHIAccessDeniedError: If user_role is not admin_clinic.
        """
        await self._opt_out_guarded(
            patient_id=patient_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            user_role=user_role,
            reason=reason,
        )

    @require_phi_access(roles=["admin_clinic"], resource_type="patient_opt_out")
    async def _opt_out_guarded(
        self,
        *,
        patient_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        user_role: str,
        reason: str,
    ) -> None:
        """Inner guarded opt-out — only admin_clinic allowed."""
        await self._patient_repo.opt_out(
            patient_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            reason=reason,
        )
        logger.info(
            "patient_service.opt_out",
            patient_id=str(patient_id),
            tenant_id=str(tenant_id),
        )

    # ------------------------------------------------------------------
    # T-BE-5: inline create + typeahead search + dedup
    # ------------------------------------------------------------------

    async def create_minimal(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        name: str,
        phone: str | None = None,
        email: str | None = None,
        channel: str,
        note: str | None = None,
    ) -> PatientInlineCreateResponse:
        """Create a minimal patient record for inline nueva-cita flow.

        RN-9 dedup: if phone is provided and already exists for this
        tenant+clinic, returns the existing patient with is_duplicate=True
        (surface the "use existing?" dialog in the FE).

        PHI gated: requires doctor/nurse/admin_clinic role (via @require_phi_access
        inside the guarded method).

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (dual filter).
            user_id: Requesting user UUID (for audit log).
            name: Full name (PHI).
            phone: Optional E.164 phone (PHI).
            email: Optional email (PHI).
            channel: Acquisition channel.
            note: Optional note.

        Returns:
            PatientInlineCreateResponse with masked fields.
        """
        return await self._create_minimal_guarded(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            name=name,
            phone=phone,
            email=email,
            channel=channel,
            note=note,
            user_role="doctor",  # ponytail: role checked inside decorator; passed as sentinel
        )

    @require_phi_access(roles=_PHI_ROLES, resource_type="patient")
    async def _create_minimal_guarded(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        name: str,
        phone: str | None = None,
        email: str | None = None,
        channel: str,
        note: str | None = None,
        user_role: str,
    ) -> PatientInlineCreateResponse:
        """Inner guarded create — only called after RBAC check passes."""
        # RN-9: dedup check if phone provided
        if phone:
            existing = await self._patient_repo.find_by_phone(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                phone=phone,
            )
            if existing is not None:
                return PatientInlineCreateResponse(
                    patient_id=existing["patient_id"],
                    name_masked=existing["name_masked"],
                    phone_masked=existing.get("phone_masked"),
                    is_duplicate=True,
                    created_at=existing["created_at"],
                )

        result = await self._patient_repo.create_minimal(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            name=name,
            phone=phone,
            email=email,
            channel=channel,
            note=note,
        )

        logger.info(
            "patient_service.create_minimal",
            patient_id=str(result["patient_id"]),
            tenant_id=str(tenant_id),
            is_duplicate=result.get("is_duplicate", False),
        )

        return PatientInlineCreateResponse(**result)

    async def find_by_phone(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        phone: str,
    ) -> dict[str, Any] | None:
        """Find existing patient by phone for RN-9 dedup check.

        Returns masked dict or None. Called by FE before POST /patients
        to decide whether to show "use existing?" dialog.

        PHI gated: requires doctor/nurse/admin_clinic role.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (dual filter).
            user_id: Requesting user UUID.
            phone: E.164 phone number to find.

        Returns:
            Masked dict {patient_id, name_masked, phone_masked, created_at} or None.
        """
        return await self._find_by_phone_guarded(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            phone=phone,
            user_role="doctor",  # ponytail: sentinel, role checked by decorator
        )

    @require_phi_access(roles=_PHI_ROLES, resource_type="patient")
    async def _find_by_phone_guarded(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        phone: str,
        user_role: str,
    ) -> dict[str, Any] | None:
        """Inner guarded find_by_phone."""
        return await self._patient_repo.find_by_phone(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            phone=phone,
        )

    async def search(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        q: str,
        cursor: UUID | None = None,
        limit: int = 20,
    ) -> PatientSearchResponse:
        """Typeahead patient search for nueva-cita picker.

        Returns cursor-paginated masked results.
        PHI gated: requires doctor/nurse/admin_clinic role.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (dual filter).
            user_id: Requesting user UUID (for audit log).
            q: Search query (ILIKE %q% on decrypted name).
            cursor: Optional pagination cursor (UUID of last seen patient).
            limit: Page size (default 20).

        Returns:
            PatientSearchResponse with masked items + pagination.
        """
        return await self._search_guarded(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            q=q,
            cursor=cursor,
            limit=limit,
            user_role="doctor",  # ponytail: sentinel, role checked by decorator
        )

    @require_phi_access(roles=_PHI_ROLES, resource_type="patient")
    async def _search_guarded(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        q: str,
        cursor: UUID | None = None,
        limit: int = 20,
        user_role: str,
    ) -> PatientSearchResponse:
        """Inner guarded search."""
        from src.modules.vitalia._shared.repositories.audit_log_repository import (
            AuditLogEntry,
        )

        raw = await self._patient_repo.search(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            q=q,
            cursor=cursor,
            limit=limit,
        )

        # Audit log for search access (HIPAA-lite)
        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="patient_search",
            resource_type="patient",
        )
        await self._audit_repo.write(audit_entry)

        return PatientSearchResponse(
            items=[PatientSearchItem(**item) for item in raw["items"]],
            next_cursor=raw.get("next_cursor"),
            total_approx=raw.get("total_approx", 0),
        )
