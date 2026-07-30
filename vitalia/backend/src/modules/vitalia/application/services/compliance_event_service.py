# cap: compliance.compliance-hipaa-lite-audit
# story-origin: TBD
"""ComplianceEventService — best-effort medical audit log writes.

HIPAA-lite pattern: writes are best-effort — persist failures NEVER raise
and NEVER interrupt user flow. All exceptions are caught and logged via
structlog.warning (same pattern as copilot observability).

Per 03-arch-be.md § 9.6 + 05-guidelines.md § 1.6:
  - sanitize_payload() invoked BEFORE persist (D7 HIPAA-lite).
  - try/except + structlog.warning wraps every write.
  - Caller flow is NEVER interrupted by audit log failures.

D1: Receives audit_repo via DI — no direct DB session access.
D7: contains_phi=false metadata on every audit event.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from luana_core_observability.recording.sanitization import sanitize_payload

from src.modules.vitalia.infrastructure.models.medical_audit_log_model import (
    VitaliaMedicalAuditLogModel,
)
from src.modules.vitalia.infrastructure.repositories.medical_audit_log_repository import (
    MedicalAuditLogRepository,
)

logger = structlog.get_logger()


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


class ComplianceEventService:
    """Best-effort HIPAA-lite compliance event logger.

    All writes are best-effort: any exception is caught and logged
    via structlog.warning — the caller flow is NEVER interrupted.

    Usage (D1 — receive repo via DI):
        svc = ComplianceEventService(audit_repo=repo)
        await svc.log_event("pii_detected", "high", payload={...}, tenant_id=tid)

    The service is intentionally thin — just sanitize + model creation + save.
    """

    def __init__(self, audit_repo: MedicalAuditLogRepository) -> None:
        self._audit_repo = audit_repo

    async def log_event(
        self,
        event_type: str,
        severity: str,
        payload: dict[str, Any],
        tenant_id: uuid.UUID,
        patient_id: uuid.UUID | None = None,
        booking_id: uuid.UUID | None = None,
        actor_id: uuid.UUID | None = None,
        actor_type: str | None = None,
    ) -> None:
        """Best-effort write to vitalia_medical_audit_log. NEVER raises.

        Args:
            event_type: Event type slug (e.g. "pii_detected", "consent_signed").
            severity: "info" | "medium" | "high".
            payload: Raw event payload — will be PII-sanitized before persist.
            tenant_id: Required tenant identifier (R2 isolation).
            patient_id: Optional patient UUID for patient-linked events.
            booking_id: Optional booking UUID for booking-linked events.
            actor_id: Optional actor UUID (clinic_owner / agent / system).
            actor_type: Optional actor role string.
        """
        try:
            # D7: sanitize_payload BEFORE persist (HIPAA-lite redaction)
            sanitized = sanitize_payload(payload)

            audit = VitaliaMedicalAuditLogModel(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                event_type=event_type,
                severity=severity,
                payload_redacted=sanitized,
                patient_id=patient_id,
                booking_id=booking_id,
                actor_id=actor_id,
                actor_type=actor_type,
                created_at=_utc_now(),
            )
            await self._audit_repo.save(audit)

        except Exception as exc:  # noqa: BLE001 — best-effort: catch ALL exceptions
            logger.warning(
                "compliance_event_persist_failed",
                exc=str(exc),
                event_type=event_type,
                severity=severity,
                tenant_id=str(tenant_id),
            )
            # NEVER re-raise — user flow must not be interrupted by audit failures
