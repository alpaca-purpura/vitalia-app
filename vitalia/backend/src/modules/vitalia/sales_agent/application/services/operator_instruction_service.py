# cap: sales_agent.honor-mode-bridge
# story-origin: vitalia-fase2-adrian-canal-inbound T-BE-3
"""OperatorInstructionService — persists per-conversation operator instruction.

The operator (front-desk / receptionist) can instruct Adrián on how to behave
in subsequent turns of a specific conversation. The instruction is persisted
PERSISTENTLY to agent_state_checkpoints.metadata_info["operator_instructions"]
via the CheckpointInstructionPort (same JSONB-merge pattern as override_context_wire
— no schema change, no column, no checkpoint reset). It steers ALL subsequent
turns until edited or cleared.

RN-13: persistente en metadata_info, steerea hasta editar/limpiar.
RN-14: composer en 'decide' mode = instrucción a Adrián (Opción A ratificada Chris).
RN-15: audit row + NON-PHI activity event; el lead NUNCA la ve.
AC-13: instrucción rechazada si la conversación NO está en modo 'decide'.
V-NF-3: audit sync write pre-response (HIPAA-lite).

The engine's supervisor_routing.j2 already reads
  [INSTRUCCION DEL OPERADOR]
with max priority — brand code only persists + injects via the port.

ZERO engine edits. §3-protected: OutputManager and agent_state_checkpoints
schema are NOT touched.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol, runtime_checkable
from uuid import UUID

import structlog

from src.modules.vitalia.sales_agent.application.services.honor_mode_bridge import (
    HonorModeBridge,
    HonorModeDecision,
)
from src.modules.vitalia.sales_agent.application.services.operator_instruction_bridge import (
    OperatorInstructionBridge,
)

logger = structlog.get_logger()

#: JSONB key under agent_state_checkpoints.metadata_info where the operator's
#: instruction is stored. Distinct from "override_context" (funnel stage wire).
OPERATOR_INSTRUCTION_KEY = "operator_instructions"


class ConversationNotInDecideModeError(Exception):
    """Raised when a set-instruction call targets a conversation not in DECIDE mode.

    AC-13: the endpoint only accepts instructions when Adrián is in 'decide'
    mode (handler_mode='ai', proposal_required=False, no active pause). Caller
    must resolve the mode (set handler_mode='ai', clear pause, etc.) first.
    """


# ---------------------------------------------------------------------------
# Ports (DI — no direct import of engine or crm concretions)
# ---------------------------------------------------------------------------


@runtime_checkable
class CheckpointInstructionPort(Protocol):
    """Writes operator instruction to the active checkpoint's metadata_info.

    Returns True if a checkpoint was found and updated, False if there is no
    active checkpoint yet (instruction is still recorded in audit + activity).
    """

    async def set_operator_instruction(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        instruction: str,
    ) -> bool:
        """Merge {"operator_instructions": instruction} into metadata_info JSONB."""
        ...


@runtime_checkable
class ConversationRepoPort(Protocol):
    """Minimal conversation lookup port (avoids direct CRM repo import)."""

    async def get_by_id(self, entity_id: UUID, *, tenant_id: UUID) -> object | None:
        """Return Conversation domain object or None if not found / unauthorized."""
        ...


@runtime_checkable
class AuditWriterPort(Protocol):
    """HIPAA-lite audit writer port (V-NF-3)."""

    async def write(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: UUID,
        payload: dict | None,
    ) -> None:
        """Write audit row synchronously within the current async session scope."""
        ...


@runtime_checkable
class ActivityRepoPort(Protocol):
    """NON-PHI activity event creation port (RN-15)."""

    async def create(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        conversation_id: UUID,
        event_kind: str,
        description_es: str,
        agent_id: str,
        payload_sanitized: dict | None,
    ) -> object:
        """Append a non-PHI activity event to the lead commercial timeline."""
        ...


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class OperatorInstructionService:
    """Persist an operator instruction and record audit + activity.

    Collaborators are injected (Protocol-typed) to keep this module decoupled
    from CRM and engine concretions (DDD cross-module ban + anti-duplication).
    """

    def __init__(
        self,
        *,
        conv_repo: ConversationRepoPort,
        checkpoint_port: CheckpointInstructionPort,
        audit_writer: AuditWriterPort,
        activity_repo: ActivityRepoPort,
        bridge_to_turn: OperatorInstructionBridge | None = None,
    ) -> None:
        """Initialize with all collaborator ports injected.

        Args:
            conv_repo: Conversation lookup (to read mode fields).
            checkpoint_port: Writes to agent_state_checkpoints.metadata_info.
            audit_writer: HIPAA-lite sync audit writer (V-NF-3).
            activity_repo: NON-PHI activity event repository (RN-15).
            bridge_to_turn: OPTIONAL agentic bridge (T-AG-1). When present, after
                persisting the instruction the service mirrors it into the engine's
                volatile ``resume_objective`` seam so the very next Adrián turn
                injects ``[INSTRUCCION DEL OPERADOR]`` (closes the integration gap:
                the engine reads ``resume_objective``, not the persistent JSONB key).
                Optional for back-compat with T-BE-3's 4-arg construction.
        """
        self._conv_repo = conv_repo
        self._checkpoint_port = checkpoint_port
        self._audit_writer = audit_writer
        self._activity_repo = activity_repo
        self._bridge = HonorModeBridge()
        self._bridge_to_turn = bridge_to_turn

    async def set_instruction(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        conversation_id: UUID,
        instruction: str,
        actor_user_id: UUID,
    ) -> bool:
        """Persist an operator instruction for a conversation.

        Guards:
          - AC-13: conversation must be in DECIDE mode; raises
            ConversationNotInDecideModeError otherwise.

        Side effects (in order):
          1. Merges instruction into metadata_info JSONB (CheckpointInstructionPort).
          2. Writes sync audit row (AuditWriterPort — V-NF-3).
          3. Appends NON-PHI activity event (ActivityRepoPort — RN-15).

        Args:
            tenant_id:       Root tenant UUID (from X-Tenant-ID header).
            clinic_id:       Clinic UUID (HIPAA-lite dual-filter).
            conversation_id: Target conversation UUID.
            instruction:     Operator-authored commercial steering text.
            actor_user_id:   User who issued the instruction (for audit).

        Returns:
            True if an active checkpoint was found and updated.
            False if no active checkpoint exists (instruction recorded in
            audit + activity for glass-box visibility).

        Raises:
            ConversationNotInDecideModeError: conversation is in consulta or pausa mode.
        """
        # 1. Load conversation (dual-filter: tenant_id at repo level)
        conv = await self._conv_repo.get_by_id(conversation_id, tenant_id=tenant_id)
        if conv is None:
            # Treat missing conversation as a mode-guard failure (not a 404 — the
            # endpoint layer translates it, but the service stays clean).
            raise ConversationNotInDecideModeError(f"Conversation {conversation_id} not found for tenant {tenant_id}.")

        # 2. AC-13: guard — only accept instructions in DECIDE mode
        decision = self._bridge.resolve(conv)  # type: ignore[arg-type]
        if decision != HonorModeDecision.DECIDE:
            raise ConversationNotInDecideModeError(
                f"Conversation {conversation_id} is in mode '{decision.value}', "
                "not 'decide'. Resolve the mode first before setting an instruction."
            )

        lead_id: UUID = conv.lead_id  # type: ignore[attr-defined]
        now_iso = datetime.now(timezone.utc).isoformat()

        # 3. Persist to agent_state_checkpoints.metadata_info (JSONB merge, no schema change)
        persisted = await self._checkpoint_port.set_operator_instruction(
            tenant_id=tenant_id,
            lead_id=lead_id,
            instruction=instruction,
        )
        if not persisted:
            logger.info(
                "operator_instruction_no_active_checkpoint",
                tenant_id=str(tenant_id),
                conversation_id=str(conversation_id),
                lead_id=str(lead_id),
            )

        # 4. Audit row — SYNC (V-NF-3 / HIPAA-lite: audit BEFORE response)
        await self._audit_writer.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=actor_user_id,
            action="operator_instruction.set",
            resource_type="conversation",
            resource_id=conversation_id,
            payload={
                "lead_id": str(lead_id),
                "has_checkpoint": persisted,
                # RN-15: instruction text NOT stored in audit payload
                # (operator content stays internal; audit logs the action, not the content)
            },
        )

        # 5. NON-PHI activity event — visible in Historial (commercial text, no PHI, no raw instruction)
        # RN-15: "La recepción instruyó a Adrián" — lead never sees the instruction text itself.
        description_es = "La recepción instruyó a Adrián para las siguientes respuestas."
        await self._activity_repo.create(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            conversation_id=conversation_id,
            event_kind="operator_instruction_set",
            description_es=description_es,
            agent_id="system",
            payload_sanitized={
                "actor_user_id": str(actor_user_id),
                "checkpoint_updated": persisted,
                "occurred_at": now_iso,
                # instruction text deliberately omitted (RN-15)
            },
        )

        # 6. Agentic bridge (T-AG-1, optional): mirror the persistent instruction into
        # the engine's volatile resume_objective seam so the NEXT Adrián turn injects
        # [INSTRUCCION DEL OPERADOR] (slot 7 volatile, post CACHE_BOUNDARY). Best-effort
        # — the bridge never raises (graceful-degradation); the instruction is already
        # persisted in metadata_info regardless.
        if self._bridge_to_turn is not None:
            await self._bridge_to_turn.apply_for_turn(tenant_id=tenant_id, lead_id=lead_id)

        logger.info(
            "operator_instruction_set",
            tenant_id=str(tenant_id),
            conversation_id=str(conversation_id),
            lead_id=str(lead_id),
            checkpoint_updated=persisted,
        )

        return persisted
