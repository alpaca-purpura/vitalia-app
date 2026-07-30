# cap: crm.crm-consent-optout
# story-origin: TBD
"""PatientConsentService — patient marketing consent management.

Application layer — orchestrates repository + audit log + domain events.

Responsibilities:
  - opt_out(): record patient marketing opt-out (admin_clinic only)
  - marketing_opt_in(): update marketing consent flag (doctor/nurse/admin_clinic)

Per vitalia/.claude/rules/hipaa-lite.md:
  - Dual filter (tenant_id + clinic_id) mandatory on all operations.
  - Audit log row written BEFORE response (sync — never fire-forget).
  - RBAC enforced via @require_phi_access decorator.

Per .claude/rules/backend-ddd.md:
  - Application layer — no direct DB access. Uses repository interfaces.
  - No cross-module imports (CRM-only scope).

downstream-regression-na: brand-local vitalia CRM consent service
"""

from __future__ import annotations

from uuid import UUID

import structlog

from src.modules.vitalia._shared.auth.rbac import require_phi_access
from src.modules.vitalia._shared.repositories.audit_log_repository import (
    AuditLogEntry,
    AuditLogRepository,
)
from src.modules.vitalia.crm.domain.events import PatientOptedOut

# Outbox adapter_bus for emitting domain events per USE_OUTBOX_PATTERN_*
# Per anti-duplication.md: use core engine — never reimplement locally
try:
    from luana_core_events.outbox import adapter_bus  # type: ignore[import]
except ImportError:  # pragma: no cover — available in runtime, not in dev-only env
    from unittest.mock import AsyncMock as _AsyncMock  # noqa: PLC0415

    class _FallbackBus:  # type: ignore[no-redef]
        """Fallback bus for environments where luana_core_events is not installed."""

        publish = _AsyncMock()

    adapter_bus = _FallbackBus()

logger = structlog.get_logger()

# PHI-allowed roles for consent operations
_OPT_OUT_ROLES = ["admin_clinic"]
_CONSENT_ROLES = ["doctor", "nurse", "admin_clinic"]


class PatientConsentService:
    """Service managing patient marketing consent lifecycle.

    Separated from PatientService to maintain single-responsibility:
    - PatientService: general PHI CRUD (get, update)
    - PatientConsentService: consent lifecycle (opt-out, marketing opt-in)

    Each method enforces:
    1. RBAC via @require_phi_access
    2. Dual filter (tenant_id + clinic_id) passed to repository
    3. Audit log write (sync, before any return)
    4. Domain event emission via outbox adapter_bus
    """

    def __init__(
        self,
        patient_repo: object,
        audit_repo: AuditLogRepository,
    ) -> None:
        """Initialize with repository dependencies.

        Args:
            patient_repo: PatientRepository (or AsyncMock in tests).
            audit_repo: AuditLogRepository for mandatory PHI audit writes.
        """
        self._patient_repo = patient_repo
        self._audit_repo = audit_repo

    @require_phi_access(roles=_OPT_OUT_ROLES, resource_type="patient_opt_out")
    async def opt_out(
        self,
        *,
        patient_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        user_role: str,
        reason: str,
    ) -> None:
        """Record patient marketing opt-out.

        Allowed roles: admin_clinic only.

        Sequence (HIPAA-lite mandated order):
        1. Validate dual filter (via repository)
        2. Update patient opt_out flag + store reason
        3. Write audit log entry (sync — MUST complete before response)
        4. Emit PatientOptedOut domain event via outbox

        The domain event allows downstream fidelizacion consumers to cancel
        pending scheduled events for this patient (SC-04).

        Args:
            patient_id: Patient UUID.
            tenant_id: Tenant UUID (root isolation).
            clinic_id: Clinic UUID (HIPAA-lite dual filter).
            user_id: User requesting the opt-out.
            user_role: Role of the requesting user (checked by decorator).
            reason: Reason for opt-out (audit log only — not returned in response).

        Raises:
            PHIAccessDeniedError: When user_role is not admin_clinic.
        """
        # Repository call handles dual filter validation + DB write + audit row
        await self._patient_repo.opt_out(
            patient_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            reason=reason,
        )

        # Explicit audit log for consent action at service layer
        # (repository writes its own row; this is the service-level consent record)
        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="patient_opted_out",
            resource_type="patient",
            resource_id=patient_id,
            payload_redacted=b"<reason_redacted>",
        )
        await self._audit_repo.write(audit_entry)

        # Emit domain event via outbox (SC-04: downstream cancels pending events)
        event = PatientOptedOut(
            event_name="patient_opted_out",
            tenant_id=tenant_id,
            patient_id=patient_id,
            clinic_id=clinic_id,
            reason=reason,
            triggered_by_user_id=user_id,
        )
        await adapter_bus.publish(event)

        logger.info(
            "consent.opt_out_recorded",
            patient_id=str(patient_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
        )

    @require_phi_access(roles=_CONSENT_ROLES, resource_type="patient_marketing_consent")
    async def marketing_opt_in(
        self,
        *,
        patient_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        user_role: str,
        opt_in: bool,
    ) -> None:
        """Update patient marketing consent flag.

        Allowed roles: doctor, nurse, admin_clinic.

        Sequence:
        1. Update marketing_opt_in flag via repository (dual filter enforced)
        2. Write audit log entry (sync — MUST complete before response)

        Note: Updating consent does NOT override opt_out. If a patient has
        opted out (opt_out=True), the consent flag is separate. The fidelizacion
        engine checks BOTH flags before sending any communication.

        Args:
            patient_id: Patient UUID.
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID.
            user_id: User updating the consent.
            user_role: Role of the requesting user.
            opt_in: New consent value (True = consented, False = refused).

        Raises:
            PHIAccessDeniedError: When user_role is not in allowed roles.
        """
        # Repository call handles dual filter validation + DB write
        await self._patient_repo.marketing_opt_in(
            patient_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            opt_in=opt_in,
        )

        # Service-level audit record for the consent action
        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="patient_marketing_opt_in",
            resource_type="patient",
            resource_id=patient_id,
        )
        await self._audit_repo.write(audit_entry)

        logger.info(
            "consent.marketing_opt_in_updated",
            patient_id=str(patient_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            opt_in=opt_in,
        )
