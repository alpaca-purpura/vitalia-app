# cap: sales_agent.honor-mode-bridge
# story-origin: vitalia-fase2-adrian-canal-inbound T-AG-1
"""OperatorInstructionBridge — agentic turn-prep wiring for the operator instruction.

This is the agentic completion of the operator-instruction surface (T-BE-3 built
the persistence; T-AG-1 wires it into the turn). It closes the integration gap
documented in the NO-NEW-LAYER cross-module audit (T-AG-1 impl-log):

  - T-BE-3 persists the operator instruction PERSISTENTLY to
    ``agent_state_checkpoints.metadata_info["operator_instructions"]`` (RN-13:
    steers ALL turns until the operator edits / clears it; NOT one-shot).
  - The engine ``conversation_pipeline.prepare_messages_and_intent`` injects
    ``[INSTRUCCION DEL OPERADOR]`` from ``checkpoint.resume_objective`` — a Text
    column it CLEARS after reading (one-shot). It does NOT read the persistent
    ``metadata_info`` key, so the persisted instruction never reaches the turn.

This bridge is the missing link: before each Adrián turn it copies the persistent
instruction into ``resume_objective`` (the engine's existing VOLATILE injection
seam), so the engine injects ``[INSTRUCCION DEL OPERADOR]`` every turn. The
instruction stays persistent because the source key in ``metadata_info`` is never
cleared — only the volatile ``resume_objective`` mirror is refreshed per turn.

Slot integrity (03-arch-agentic § 1.3 + design § 8): ``resume_objective`` is
injected as a SYSTEM MESSAGE in the volatile message tail (POST
``CACHE_BOUNDARY_MARKER``), NEVER in the cacheable prefix — so the instruction
text is never a silent cache invalidator.

ZERO engine edit. The bridge couples to the engine's read surface via an injected
Protocol port (the same decoupling pattern as ``override_context_wire``): it never
imports the engine's sync state repository / checkpoint model concretion (the
``agent_state_checkpoints`` schema is §3-protected per sales-agent-expert; the
concrete adapter touches it via raw SQL under the schema-mirror exception).

Best-effort: a failure here MUST NOT break the conversational turn
(graceful-degradation / copilot-resilience cardinal). On failure the turn simply
proceeds without the instruction applied this turn (it remains persisted and is
retried next turn).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

import structlog

logger = structlog.get_logger()


@runtime_checkable
class CheckpointInstructionBridgePort(Protocol):
    """Copies the persistent operator instruction into the turn's volatile seam.

    The concrete brand adapter reads the active checkpoint for
    ``(tenant_id, lead_id)`` and, if ``metadata_info["operator_instructions"]`` is
    set, writes that value into ``resume_objective`` (the engine's per-turn
    injection point). It NEVER clears the persistent key — the instruction steers
    every subsequent turn until the operator edits / clears it.

    Returns ``True`` if an active checkpoint carried a persistent instruction and
    the volatile seam was refreshed; ``False`` otherwise (no active checkpoint, or
    no persistent instruction set).
    """

    async def apply_persistent_instruction_to_turn(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
    ) -> bool:
        """Mirror metadata_info['operator_instructions'] → resume_objective."""
        ...


class OperatorInstructionBridge:
    """Apply the persistent operator instruction to the next Adrián turn.

    Construct with the injected port; call :meth:`apply_for_turn` at turn-prep
    time (before invoking the engine graph) so the engine injects
    ``[INSTRUCCION DEL OPERADOR]`` from the refreshed ``resume_objective``.
    """

    def __init__(self, *, checkpoint_bridge_port: CheckpointInstructionBridgePort) -> None:
        """Initialize with the injected bridge port (no engine / crm concretion)."""
        self._port = checkpoint_bridge_port

    async def apply_for_turn(self, *, tenant_id: UUID, lead_id: UUID) -> bool:
        """Apply the persistent operator instruction to the upcoming turn.

        Reads the persistent instruction (via the port) and refreshes the engine's
        volatile ``resume_objective`` seam so the next turn injects it. Persistent:
        the source key is never cleared, so the instruction steers all turns until
        edited / cleared (RN-13).

        Best-effort (graceful-degradation): on any failure the turn proceeds
        without the instruction applied this turn — never raises.

        Args:
            tenant_id: Root tenant UUID (dual-filter cardinal — tenant isolation).
            lead_id:   Lead UUID identifying the active checkpoint.

        Returns:
            True if a persistent instruction was applied to the turn's volatile
            seam; False if there was none (or on a swallowed best-effort failure).
        """
        try:
            applied = await self._port.apply_persistent_instruction_to_turn(
                tenant_id=tenant_id,
                lead_id=lead_id,
            )
        except Exception:  # noqa: BLE001 — best-effort; the turn must never break.
            logger.warning(
                "operator_instruction_bridge_apply_failed",
                tenant_id=str(tenant_id),
                lead_id=str(lead_id),
            )
            return False

        logger.debug(
            "operator_instruction_bridge_applied",
            tenant_id=str(tenant_id),
            lead_id=str(lead_id),
            applied=applied,
        )
        return applied
