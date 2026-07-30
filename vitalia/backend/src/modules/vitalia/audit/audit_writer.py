# cap: audit.audit-writer-ssot
# story-origin: TBD
"""HIPAA-lite audit log writer — SSoT for Vitalia brand.

Rule (hipaa-lite.md § Audit log):
  - Tabla vitalia_audit_log columns: (id, tenant_id, clinic_id, user_id, action,
    resource_type, resource_id, from_ip, user_agent, timestamp, payload_redacted)
  - TODA lectura/modificación de PHI registra row. NO opcional.
  - NO async fire-forget — SYNC write before response.
  - Retention: 10 años (Ley 25.326 AR, Ley 1581 CO, LGPD BR, etc.)
  - PII sanitization: sanitize_phi_payload(payload) via vitalia compliance adapter
    before writing to payload_redacted column.
    (Repointed from engine sanitize_payload — kwarg was removed from engine signature;
    now uses brand-local wrapper per T-1 arreglar-guardado-voz-y-tono.)

Usage (in any admin or API module):
    from src.modules.vitalia.audit.audit_writer import write_audit_log_sync

    with get_sync_session() as db:
        # ... business operation ...
        write_audit_log_sync(
            db,
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            user_id=str(admin_user_id),
            action="tenant.created",
            resource_type="tenant",
            resource_id=str(tenant_id),
            payload={"name": clinic_name, "slug": slug},
        )
        db.commit()
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

logger = structlog.get_logger()


def write_audit_log_sync(
    db: Session,
    *,
    tenant_id: str,
    clinic_id: str,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    payload: dict[str, Any] | None = None,
    from_ip: str | None = None,
    user_agent: str = "VitaliaAdmin/1.0",
) -> None:
    """Write a HIPAA-lite audit log row synchronously.

    MUST be called BEFORE returning from any PHI-adjacent mutation.
    Caller is responsible for db.commit() after this call.

    Invariants:
        - payload is sanitized via sanitize_phi_payload (vitalia brand-local wrapper)
          before writing. Wrapper applies engine generic PII redaction +
          22 vitalia PHI field removal.
        - payload_redacted column stores BYTEA (JSON-encoded bytes).
        - id is gen_random_uuid() in SQL (not Python) for DB-level atomicity.
        - NO PHI fields in payload: only identity data (name, slug, email, role).
          PHI fields (diagnosis, treatment_plan, etc.) must never enter this fn.

    Args:
        db: SQLAlchemy synchronous Session (NOT AsyncSession).
        tenant_id: UUID string of the tenant performing the action.
        clinic_id: UUID string of the clinic context (HIPAA dual-filter).
        user_id: UUID string of the user performing the action.
        action: Dot-notation action identifier (e.g. 'tenant.created', 'user.deactivated').
        resource_type: Resource type string (e.g. 'tenant', 'user_profile', 'clinic').
        resource_id: UUID string of the affected resource.
        payload: Dict of identity-safe fields to log (NO PHI). Default: empty dict.
        from_ip: Client IP address. None if not available (admin Streamlit).
        user_agent: User-agent string. Default: VitaliaAdmin/1.0.

    Raises:
        Exception: Propagates DB errors — caller should handle to avoid silently
                   losing audit trail. Admin modules wrap in try/except + st.error().
    """
    from src.modules.vitalia.compliance.application.compliance_service_adapter import (  # noqa: PLC0415
        sanitize_phi_payload,
    )

    safe_payload = sanitize_phi_payload(payload or {})
    payload_bytes: bytes = json.dumps(safe_payload, default=str, ensure_ascii=False).encode("utf-8")

    db.execute(
        text("""
            INSERT INTO vitalia_audit_log
                (id, tenant_id, clinic_id, user_id, action, resource_type,
                 resource_id, from_ip, user_agent, payload_redacted, occurred_at)
            VALUES
                (gen_random_uuid(),
                 CAST(:tenant_id AS uuid), CAST(:clinic_id AS uuid), CAST(:user_id AS uuid),
                 :action, :resource_type, CAST(:resource_id AS uuid),
                 :from_ip, :user_agent, :payload, NOW())
        """),
        {
            "tenant_id": tenant_id,
            "clinic_id": clinic_id,
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "from_ip": from_ip,
            "user_agent": user_agent,
            "payload": payload_bytes,
        },
    )

    logger.info(
        "audit_log_written",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
    )


class AsyncAuditWriter:
    """Async adapter for the HIPAA-lite audit log writer.

    Bridges the async inbox/crm services (which call `await audit_writer.write(...)`)
    with the sync `write_audit_log_sync` implementation.

    Wraps the sync write in `asyncio.get_event_loop().run_in_executor()` so the
    async service layer can await it without blocking the event loop.

    Medium #6 fix — replaces AsyncMock audit_writer in router DI factories.

    PHI obligations (hipaa-lite.md § Regla cardinal):
    - Audit log written sync pre-response (no fire-and-forget)
    - tenant_id + clinic_id dual filter on every row
    - sanitize_payload applied inside write_audit_log_sync
    """

    def __init__(self, *, session: AsyncSession) -> None:
        """Initialize AsyncAuditWriter.

        Args:
            session: Async SQLAlchemy session (from FastAPI DI).
        """
        self._session = session

    async def write(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: UUID,
        payload: dict[str, Any] | None = None,
        from_ip: str | None = None,
        user_agent: str = "VitaliaAPI/1.0",
    ) -> None:
        """Write a HIPAA-lite audit log row asynchronously.

        Executes the raw SQL INSERT directly on the async session so the audit
        row is written within the same transaction scope as the business operation.

        PHI dual-filter: tenant_id AND clinic_id mandatory.
        PII sanitization applied via sanitize_phi_payload (vitalia brand-local wrapper).

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite second scope filter).
            user_id: User UUID performing the action.
            action: Dot-notation action identifier.
            resource_type: Resource type string.
            resource_id: Affected resource UUID.
            payload: Identity-safe payload dict (NO PHI). Default: empty dict.
            from_ip: Client IP address (optional).
            user_agent: User-agent string. Default: VitaliaAPI/1.0.
        """
        from src.modules.vitalia.compliance.application.compliance_service_adapter import (  # noqa: PLC0415
            sanitize_phi_payload,
        )

        safe_payload = sanitize_phi_payload(payload or {})
        payload_bytes: bytes = json.dumps(safe_payload, default=str, ensure_ascii=False).encode("utf-8")

        await self._session.execute(
            text("""
                INSERT INTO vitalia_audit_log
                    (id, tenant_id, clinic_id, user_id, action, resource_type,
                     resource_id, from_ip, user_agent, payload_redacted, occurred_at)
                VALUES
                    (gen_random_uuid(),
                     CAST(:tenant_id AS uuid), CAST(:clinic_id AS uuid), CAST(:user_id AS uuid),
                     :action, :resource_type, CAST(:resource_id AS uuid),
                     :from_ip, :user_agent, :payload, NOW())
            """),
            {
                "tenant_id": str(tenant_id),
                "clinic_id": str(clinic_id),
                "user_id": str(user_id),
                "action": action,
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "from_ip": from_ip,
                "user_agent": user_agent,
                "payload": payload_bytes,
            },
        )

        logger.info(
            "audit_log_async_written",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
        )
