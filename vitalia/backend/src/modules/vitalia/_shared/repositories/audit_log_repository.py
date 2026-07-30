# cap: audit.audit-writer-ssot
# story-origin: TBD
"""AuditLog Repository — HIPAA-lite sync write enforcement.

CRITICAL: Audit log writes MUST be synchronous (await before response).
NO fire-and-forget. NO background task scheduling of any kind.

Per vitalia/.claude/rules/hipaa-lite.md § Audit log:
  "TODA lectura/modificación de PHI registra row. NO opcional.
   NO async fire-forget (sync write antes response)."

Table: vitalia_audit_log
  id                UUID PK
  tenant_id         TEXT NOT NULL (indexed)
  clinic_id         UUID NOT NULL (dual filter)
  user_id           UUID NOT NULL
  action            TEXT NOT NULL
  resource_type     TEXT NOT NULL
  resource_id       UUID
  from_ip           TEXT
  user_agent        TEXT
  payload_redacted  BYTEA (sanitized via sanitize_phi_payload)
  occurred_at       TIMESTAMPTZ NOT NULL DEFAULT now()

Retention: 10 years minimum (Ley 25.326 AR, LGPD BR, Ley 1581 CO,
           Ley 19.628 CL, Ley 29733 PE, HIPAA §164.312 US reference).

downstream-regression-na: brand-local audit log for vitalia HIPAA-lite
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


def _utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


@dataclass
class AuditLogEntry:
    """Immutable audit log entry for a PHI access or modification event.

    All fields except optional ones MUST be populated before writing.
    occurred_at defaults to current UTC time if not provided.
    """

    tenant_id: UUID
    clinic_id: UUID
    user_id: UUID
    action: str
    resource_type: str
    resource_id: UUID | None = None
    from_ip: str | None = None
    user_agent: str | None = None
    payload_redacted: bytes = b""
    occurred_at: datetime = field(default_factory=_utc_now)
    id: UUID = field(default_factory=uuid4)


class AuditLogRepository:
    """Repository for writing PHI audit log entries synchronously.

    HIPAA-lite requires that audit log writes complete BEFORE the response
    is returned to the client. This repository MUST be awaited explicitly.

    Usage:
        audit_repo = AuditLogRepository(session=db_session)
        entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=current_user.id,
            action="view_treatment_plan",
            resource_type="treatment_plan",
            resource_id=plan_id,
            from_ip=request.client.host,
        )
        await audit_repo.write(entry)  # MUST be awaited, never fire-forget
    """

    def __init__(self, session: "AsyncSession") -> None:
        """Initialize with an active async DB session.

        Args:
            session: SQLAlchemy async session. Must be the same session
                     used for the PHI operation to ensure atomicity.
        """
        self._session = session

    async def write(self, entry: AuditLogEntry) -> None:
        """Write an audit log entry synchronously.

        This method MUST be awaited. NEVER schedule as background task.

        Uses raw SQL execute for direct TIMESTAMPTZ insert without ORM model
        dependency — keeps the _shared layer free of infrastructure imports.

        Args:
            entry: The audit log entry to persist.

        Raises:
            Exception: Propagates DB errors — caller must handle
                       (do NOT swallow audit write failures silently).
        """
        from sqlalchemy import text  # noqa: PLC0415

        stmt = text(
            """
            INSERT INTO vitalia_audit_log
              (id, tenant_id, clinic_id, user_id, action, resource_type,
               resource_id, from_ip, user_agent, payload_redacted, occurred_at)
            VALUES
              (:id, :tenant_id, :clinic_id, :user_id, :action, :resource_type,
               :resource_id, :from_ip, :user_agent, :payload_redacted, :occurred_at)
            """
        )
        await self._session.execute(
            stmt,
            {
                "id": str(entry.id),
                "tenant_id": str(entry.tenant_id),
                "clinic_id": str(entry.clinic_id),
                "user_id": str(entry.user_id),
                "action": entry.action,
                "resource_type": entry.resource_type,
                "resource_id": str(entry.resource_id) if entry.resource_id else None,
                "from_ip": entry.from_ip,
                "user_agent": entry.user_agent,
                "payload_redacted": entry.payload_redacted,
                "occurred_at": entry.occurred_at,
            },
        )
        await self._session.flush()

        logger.info(
            "phi_audit_log_written",
            audit_id=str(entry.id),
            tenant_id=str(entry.tenant_id),
            clinic_id=str(entry.clinic_id),
            action=entry.action,
            resource_type=entry.resource_type,
        )
