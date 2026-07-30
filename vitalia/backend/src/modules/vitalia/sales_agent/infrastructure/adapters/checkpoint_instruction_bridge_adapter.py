# cap: sales_agent.honor-mode-bridge
# story-origin: vitalia-fase2-adrian-canal-inbound T-AG-1
"""CheckpointInstructionBridgeAdapter — concrete bridge that refreshes the turn seam.

Implements the ``CheckpointInstructionBridgePort`` Protocol from
``OperatorInstructionBridge`` by mirroring the persistent operator instruction
(``metadata_info["operator_instructions"]``, written by T-BE-3) into the engine's
per-turn volatile injection seam (``resume_objective``).

The engine ``conversation_pipeline.prepare_messages_and_intent`` reads
``resume_objective`` → injects ``[INSTRUCCION DEL OPERADOR]`` as a system message
in the VOLATILE message tail (post CACHE_BOUNDARY) → then clears it (one-shot).
This adapter re-populates ``resume_objective`` from the PERSISTENT key on every
turn, so the instruction steers all subsequent turns (RN-13) without ever clearing
the persistent source key.

Same raw-SQL schema-mirror pattern as ``checkpoint_instruction_adapter.py`` (the
``agent_state_checkpoints`` table is §3-protected per sales-agent-expert — no
schema change, no column, no engine state-repository import; the brand touches the
table directly via raw SQL under `.claude/rules/backend-ddd.md § Schema-mirror
exception`).

Idempotent: re-running the same UPDATE for the same turn yields the same state
(``resume_objective`` ends equal to the persistent instruction). The
``metadata_info ? 'operator_instructions'`` guard skips the write when no
instruction is set (so a normal turn's ``resume_objective`` is untouched).

Tenant isolation: ``tenant_id`` + ``lead_id`` + ``is_active`` filter (the active
checkpoint for this lead in this tenant).
"""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CheckpointInstructionBridgeAdapter:
    """Concrete implementation of CheckpointInstructionBridgePort.

    Mirrors metadata_info['operator_instructions'] → resume_objective on the active
    checkpoint via the brand's AsyncSession. No schema change — both columns already
    exist on agent_state_checkpoints (metadata_info JSONB nullable + resume_objective
    Text nullable).

    Args:
        session: Async SQLAlchemy session (from FastAPI DI).
    """

    def __init__(self, *, session: AsyncSession) -> None:
        """Initialize adapter with the brand async session."""
        self._session = session

    async def apply_persistent_instruction_to_turn(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
    ) -> bool:
        """Copy the persistent operator instruction into resume_objective.

        Only refreshes ``resume_objective`` when ``metadata_info`` actually carries
        an ``operator_instructions`` key (the ``? 'operator_instructions'`` guard) —
        a normal turn without an instruction is untouched. The persistent key is
        NEVER cleared (RN-13: steers every subsequent turn).

        Args:
            tenant_id: Root tenant UUID.
            lead_id:   Lead UUID (active checkpoint = tenant + lead + is_active).

        Returns:
            True if an active checkpoint carried an instruction and the volatile
            seam was refreshed; False otherwise.
        """
        result = await self._session.execute(
            text("""
                UPDATE agent_state_checkpoints
                SET resume_objective = metadata_info ->> 'operator_instructions'
                WHERE tenant_id = CAST(:tenant_id AS uuid)
                  AND lead_id   = CAST(:lead_id AS uuid)
                  AND is_active = TRUE
                  AND metadata_info ? 'operator_instructions'
                  AND COALESCE(metadata_info ->> 'operator_instructions', '') <> ''
            """),
            {
                "tenant_id": str(tenant_id),
                "lead_id": str(lead_id),
            },
        )
        rows_updated: int = result.rowcount  # type: ignore[assignment]
        applied = rows_updated > 0

        logger.debug(
            "checkpoint_instruction_bridge_adapter.apply",
            tenant_id=str(tenant_id),
            lead_id=str(lead_id),
            rows_updated=rows_updated,
        )
        return applied
