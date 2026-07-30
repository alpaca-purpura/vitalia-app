# cap: compliance.compliance-hipaa-lite-audit
# story-origin: TBD
"""Vitalia admin audit log helper — HIPAA-lite PHI-safe action logging.

Provides log_admin_action() for writing sanitized admin events to
vitalia_audit_log (partitioned table, created in migration 013_vitalia).

HIPAA-lite invariants enforced:
- payload_redacted NEVER contains PHI fields (sanitize_phi_payload applied)
- Write is SYNC before returning (HIPAA: audit write must complete before response)
- BYTEA storage: JSON-encoded bytes (not encrypted in dev; pgcrypto in prod)

References:
- hipaa-lite.md § Audit log
- vitalia/backend/alembic/versions/013_vitalia_audit_log.py (table DDL)
"""

from __future__ import annotations

import json
from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.compliance.application.compliance_service_adapter import sanitize_phi_payload

logger = structlog.get_logger()


async def log_admin_action(
    *,
    session: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    user_id: UUID,
    action: str,
    resource_type: str,
    resource_id: UUID | None = None,
    from_ip: str = "",
    user_agent: str = "",
    payload_redacted: dict | None = None,
) -> None:
    """Write a HIPAA-lite compliant admin action row to vitalia_audit_log.

    Applies sanitize_phi_payload() to payload_redacted before storage
    to ensure no PHI fields are persisted in the audit log.

    SYNC WRITE: This function must be awaited and completed BEFORE the
    calling admin action returns (HIPAA mandate: audit row must exist
    before response is sent).

    Args:
        session: AsyncSession (must be flushed/committed by caller)
        tenant_id: Tenant UUID
        clinic_id: Clinic UUID (HIPAA dual filter — mandatory)
        user_id: Admin user UUID performing the action
        action: Action name, e.g. 'tenant.created', 'user.created', 'clinic.viewed'
        resource_type: Resource type, e.g. 'tenant', 'user_profile', 'clinic'
        resource_id: Resource UUID (optional)
        from_ip: Source IP address string (optional)
        user_agent: User agent string (optional)
        payload_redacted: Identity-only payload dict (clinic_name, email, country OK;
                          PHI fields will be stripped by sanitize_phi_payload)
    """
    # Apply PHI sanitization — strip diagnosis, treatment_plan, medication,
    # patient.name, patient.dni, etc. before storing
    raw_payload = payload_redacted or {}
    safe_payload = sanitize_phi_payload(raw_payload)

    # Encode as BYTEA (JSON bytes)
    payload_bytes: bytes = json.dumps(safe_payload, default=str, ensure_ascii=False).encode("utf-8")

    # Log the action for observability (structlog — no PHI, only identifiers)
    logger.info(
        "admin_action_logged",
        tenant_id=str(tenant_id),
        clinic_id=str(clinic_id),
        user_id=str(user_id),
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
    )

    # Insert into vitalia_audit_log (raw SQL — partitioned table, SA ORM has
    # issues with partitioned tables and bulk inserts)
    await session.execute(
        text("""
            INSERT INTO vitalia_audit_log
                (id, tenant_id, clinic_id, user_id, action, resource_type,
                 resource_id, from_ip, user_agent, payload_redacted, occurred_at)
            VALUES
                (gen_random_uuid(), :tenant_id, :clinic_id, :user_id, :action,
                 :resource_type, :resource_id, :from_ip::inet, :user_agent,
                 :payload_redacted, NOW())
        """),
        {
            "tenant_id": str(tenant_id),
            "clinic_id": str(clinic_id),
            "user_id": str(user_id),
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "from_ip": from_ip or None,
            "user_agent": user_agent or "",
            "payload_redacted": payload_bytes,
        },
    )
