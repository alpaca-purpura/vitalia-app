# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""LeadActivityRepository — commercial micro-log for funnel timeline.

Infrastructure layer — SA 2.0 async raw SQL.

NON-PHI table: single tenant_id filter only.
Distinct from ActivityEventRepository (vitalia_activity_events) which is PHI dual-filter.
LeadActivity = commercial/funnel timeline, NEVER clinical data.

Primary use cases:
  - record(): append a new activity when funnel event occurs
  - last_for_lead(): get the most recent activity for board card micro-log
  - list_for_lead(): full timeline for Historial tab
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.crm.domain.lead_activity import LeadActivity

logger = structlog.get_logger()


def _utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


class LeadActivityRepository:
    """Repository for LeadActivity commercial micro-log.

    NON-PHI — single tenant_id filter only.
    Append-only: activities are never updated (corrections = new activity).
    description_es must be Spanish neutro, 3rd person, NEVER PHI/clinical.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with async DB session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def record(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
        actor: str,
        kind: str,
        description_es: str,
        occurred_at: datetime | None = None,
    ) -> LeadActivity:
        """Append a new activity to the lead commercial timeline.

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID — isolation (required).
            actor: Who generated this (agent|human|lead|system).
            kind: Activity type (message|stage_move|info_sent|deposit|note).
            description_es: Spanish neutro, 3rd person, NON-PHI text.
            occurred_at: Timestamp (defaults to now UTC).

        Returns:
            LeadActivity domain entity.

        Raises:
            ValueError: If tenant_id is None.
        """
        if tenant_id is None:
            raise ValueError("LeadActivityRepository.record requires tenant_id — tenant isolation mandatory")

        activity_id = uuid4()
        timestamp = occurred_at or _utc_now()

        stmt = text(
            """
            INSERT INTO vitalia_lead_activity
                (id, tenant_id, lead_id, actor, kind, description_es, occurred_at, deleted_at)
            VALUES
                (:id, :tenant_id, :lead_id, :actor, :kind, :description_es, :occurred_at, NULL)
            """
        )
        await self._session.execute(
            stmt,
            {
                "id": str(activity_id),
                "tenant_id": str(tenant_id),
                "lead_id": str(lead_id),
                "actor": actor,
                "kind": kind,
                "description_es": description_es,
                "occurred_at": timestamp,
            },
        )

        logger.info(
            "lead_activity_recorded",
            activity_id=str(activity_id),
            lead_id=str(lead_id),
            tenant_id=str(tenant_id),
            actor=actor,
            kind=kind,
        )

        return LeadActivity(
            id=activity_id,
            tenant_id=tenant_id,
            lead_id=lead_id,
            actor=actor,
            kind=kind,
            description_es=description_es,
            occurred_at=timestamp,
            deleted_at=None,
        )

    async def last_for_lead(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
    ) -> LeadActivity | None:
        """Retrieve the most recent activity for a lead (board card micro-log).

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID — isolation (required).

        Returns:
            Most recent LeadActivity or None if no activities.

        Raises:
            ValueError: If tenant_id is None.
        """
        if tenant_id is None:
            raise ValueError("LeadActivityRepository.last_for_lead requires tenant_id")

        stmt = text(
            """
            SELECT
                id, tenant_id, lead_id, actor, kind, description_es,
                occurred_at, deleted_at
            FROM vitalia_lead_activity
            WHERE tenant_id = :tenant_id
              AND lead_id = :lead_id
              AND deleted_at IS NULL
            ORDER BY occurred_at DESC
            LIMIT 1
            """
        )
        result = await self._session.execute(
            stmt,
            {
                "tenant_id": str(tenant_id),
                "lead_id": str(lead_id),
            },
        )
        row = result.fetchone()

        if row is None:
            return None

        return LeadActivity(
            id=UUID(str(row.id)),
            tenant_id=UUID(str(row.tenant_id)),
            lead_id=UUID(str(row.lead_id)),
            actor=row.actor,
            kind=row.kind,
            description_es=row.description_es,
            occurred_at=row.occurred_at,
            deleted_at=row.deleted_at,
        )

    async def list_for_lead(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
        limit: int = 50,
    ) -> list[LeadActivity]:
        """List activities for a lead, ordered newest-first.

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID — isolation (required).
            limit: Maximum number of activities to return (default 50).

        Returns:
            List of LeadActivity sorted by occurred_at DESC.

        Raises:
            ValueError: If tenant_id is None.
        """
        if tenant_id is None:
            raise ValueError("LeadActivityRepository.list_for_lead requires tenant_id")

        stmt = text(
            """
            SELECT
                id, tenant_id, lead_id, actor, kind, description_es,
                occurred_at, deleted_at
            FROM vitalia_lead_activity
            WHERE tenant_id = :tenant_id
              AND lead_id = :lead_id
              AND deleted_at IS NULL
            ORDER BY occurred_at DESC
            LIMIT :limit
            """
        )
        result = await self._session.execute(
            stmt,
            {
                "tenant_id": str(tenant_id),
                "lead_id": str(lead_id),
                "limit": limit,
            },
        )
        rows = result.fetchall()

        return [
            LeadActivity(
                id=UUID(str(row.id)),
                tenant_id=UUID(str(row.tenant_id)),
                lead_id=UUID(str(row.lead_id)),
                actor=row.actor,
                kind=row.kind,
                description_es=row.description_es,
                occurred_at=row.occurred_at,
                deleted_at=row.deleted_at,
            )
            for row in rows
        ]
