# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""LeadStageTransitionRepository — audit log for funnel transitions.

Infrastructure layer — SA 2.0 async raw SQL.

NON-PHI table: single tenant_id filter only (no clinic_id dual filter).
Tenant isolation: every method requires tenant_id (raises ValueError if None).

Primary use cases:
  - record(): persist a transition audit row when stage changes (sync write pre-response)
  - list_for_lead(): timeline history for lead detail view (Historial tab)
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.crm.domain.lead_stage_transition import LeadStageTransition

logger = structlog.get_logger()


def _utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


class LeadStageTransitionRepository:
    """Repository for LeadStageTransition audit records.

    NON-PHI — single tenant_id filter only.
    Append-only: no update/delete (soft_delete via deleted_at if needed).
    Audit retention: 10y per LatAm health regulations (hipaa-lite.md).
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with async DB session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def record(
        self,
        *,
        lead_id: UUID,
        tenant_id: UUID,
        from_stage: str | None,
        to_stage: str,
        triggered_by: str,
        reason: str | None,
        score_at_transition: int | None,
        actor_user_id: UUID | None,
    ) -> LeadStageTransition:
        """Persist a funnel transition audit row.

        Called sync (pre-response) by FunnelService.transition_stage().
        reason = commercial override context, NEVER clinical data.

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID — isolation (required).
            from_stage: Previous stage slug (None for initial set).
            to_stage: New stage slug.
            triggered_by: Actor slug (agent|manual_override|webhook|reactivation|auto_freeze).
            reason: Commercial override context for RN-4.1 (NON-PHI).
            score_at_transition: Glass-box score at time of transition.
            actor_user_id: User ID for manual overrides.

        Returns:
            LeadStageTransition domain entity.

        Raises:
            ValueError: If tenant_id is None.
        """
        if tenant_id is None:
            raise ValueError("LeadStageTransitionRepository.record requires tenant_id — tenant isolation mandatory")

        transition_id = uuid4()
        now = _utc_now()

        stmt = text(
            """
            INSERT INTO vitalia_lead_stage_transition
                (id, tenant_id, lead_id, from_stage, to_stage,
                 triggered_by, reason, score_at_transition, actor_user_id,
                 occurred_at, deleted_at)
            VALUES
                (:id, :tenant_id, :lead_id, :from_stage, :to_stage,
                 :triggered_by, :reason, :score_at_transition, :actor_user_id,
                 :occurred_at, NULL)
            """
        )
        await self._session.execute(
            stmt,
            {
                "id": str(transition_id),
                "tenant_id": str(tenant_id),
                "lead_id": str(lead_id),
                "from_stage": from_stage,
                "to_stage": to_stage,
                "triggered_by": triggered_by,
                "reason": reason,
                "score_at_transition": score_at_transition,
                "actor_user_id": str(actor_user_id) if actor_user_id else None,
                "occurred_at": now,
            },
        )

        logger.info(
            "lead_transition_recorded",
            transition_id=str(transition_id),
            lead_id=str(lead_id),
            tenant_id=str(tenant_id),
            from_stage=from_stage,
            to_stage=to_stage,
            triggered_by=triggered_by,
        )

        return LeadStageTransition(
            id=transition_id,
            tenant_id=tenant_id,
            lead_id=lead_id,
            from_stage=from_stage,
            to_stage=to_stage,
            triggered_by=triggered_by,
            reason=reason,
            score_at_transition=score_at_transition,
            actor_user_id=actor_user_id,
            occurred_at=now,
            deleted_at=None,
        )

    async def list_for_lead(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
    ) -> list[LeadStageTransition]:
        """Retrieve all transitions for a lead, ordered newest-first.

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID — isolation (required).

        Returns:
            List of LeadStageTransition sorted by occurred_at DESC.

        Raises:
            ValueError: If tenant_id is None.
        """
        if tenant_id is None:
            raise ValueError("LeadStageTransitionRepository.list_for_lead requires tenant_id")

        stmt = text(
            """
            SELECT
                id, tenant_id, lead_id, from_stage, to_stage,
                triggered_by, reason, score_at_transition, actor_user_id,
                occurred_at, deleted_at
            FROM vitalia_lead_stage_transition
            WHERE tenant_id = :tenant_id
              AND lead_id = :lead_id
              AND deleted_at IS NULL
            ORDER BY occurred_at DESC
            """
        )
        result = await self._session.execute(
            stmt,
            {
                "tenant_id": str(tenant_id),
                "lead_id": str(lead_id),
            },
        )
        rows = result.fetchall()

        return [
            LeadStageTransition(
                id=UUID(str(row.id)),
                tenant_id=UUID(str(row.tenant_id)),
                lead_id=UUID(str(row.lead_id)),
                from_stage=row.from_stage,
                to_stage=row.to_stage,
                triggered_by=row.triggered_by,
                reason=row.reason,
                score_at_transition=row.score_at_transition,
                actor_user_id=UUID(str(row.actor_user_id)) if row.actor_user_id else None,
                occurred_at=row.occurred_at,
                deleted_at=row.deleted_at,
            )
            for row in rows
        ]
