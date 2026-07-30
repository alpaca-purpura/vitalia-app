# cap: sales_agent.honor-mode-bridge
# story-origin: vitalia-fase2-adrian-canal-inbound T-BE-3
"""CheckpointInstructionAdapter — concrete brand port that writes operator instructions.

Implements the CheckpointInstructionPort Protocol from OperatorInstructionService
by merging the operator instruction into the active agent_state_checkpoints row's
metadata_info JSONB.

Same JSONB-merge pattern as override_context_wire (raw SQL, no column change, no
checkpoint reset — §3-protected schema). Uses the key "operator_instructions"
(distinct from "override_context" used by the funnel wire).

Per anti-duplication.md: this file does NOT import the engine's state repository
concretion. It queries the agent_state_checkpoints table DIRECTLY via raw SQL
on the brand's async session — the same table is §3-protected (schema-mirror rule
per `.claude/rules/backend-ddd.md § Schema-mirror exception`).

SQL pattern (idempotent merge via JSONB ||):
  UPDATE agent_state_checkpoints
  SET metadata_info = COALESCE(metadata_info, '{}') ||
      jsonb_build_object('operator_instructions', :instruction)
  WHERE tenant_id = :tenant_id
    AND lead_id = :lead_id
    AND is_active = TRUE
"""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CheckpointInstructionAdapter:
    """Concrete implementation of CheckpointInstructionPort.

    Reads/writes agent_state_checkpoints.metadata_info via the brand's AsyncSession.
    The schema (metadata_info JSONB nullable column) already exists — NO migration.

    Args:
        session: Async SQLAlchemy session from FastAPI DI.
    """

    def __init__(self, *, session: AsyncSession) -> None:
        """Initialize adapter.

        Args:
            session: Async SQLAlchemy session (from FastAPI DI).
        """
        self._session = session

    async def set_operator_instruction(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        instruction: str,
    ) -> bool:
        """Merge operator_instructions into metadata_info JSONB.

        Uses JSONB || (merge operator) to add/overwrite the key without
        resetting other metadata_info entries. No schema change.

        Args:
            tenant_id:  Root tenant UUID.
            lead_id:    Lead UUID (active checkpoint identified by tenant+lead+is_active).
            instruction: Operator-authored steering text.

        Returns:
            True if a checkpoint row was found and updated.
            False if no active checkpoint exists for (tenant_id, lead_id).
        """
        result = await self._session.execute(
            text("""
                UPDATE agent_state_checkpoints
                SET metadata_info = COALESCE(metadata_info, '{}') ||
                    jsonb_build_object('operator_instructions', :instruction)
                WHERE tenant_id = CAST(:tenant_id AS uuid)
                  AND lead_id   = CAST(:lead_id AS uuid)
                  AND is_active = TRUE
            """),
            {
                "tenant_id": str(tenant_id),
                "lead_id": str(lead_id),
                "instruction": instruction,
            },
        )
        rows_updated: int = result.rowcount  # type: ignore[assignment]
        found = rows_updated > 0

        logger.info(
            "checkpoint_instruction_adapter.set",
            tenant_id=str(tenant_id),
            lead_id=str(lead_id),
            rows_updated=rows_updated,
        )
        return found
