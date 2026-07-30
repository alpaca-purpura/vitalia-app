# cap: sales_agent.honor-mode-bridge
# story-origin: vitalia-fase2-adrian-canal-inbound T-BE-3
"""HonorModeBridge — resolve operating mode per-conversation (decide/consulta/pausa).

Pure resolver: reads the three inbox fields from a Conversation domain object
(or any object with the matching attributes) and returns a HonorModeDecision.
Zero I/O — the call site acts on the decision.

Three modes (01-spec.md § 5 + RN-1/2/10):

  PAUSA    — handler_mode='human' OR pause_until is in the future.
             Adrián does NOT respond. Inbound persisted + feeds inbox.
             Priority: highest (overrides CONSULTA).

  CONSULTA — handler_mode='ai' + proposal_required=True.
             Graph RUNS (tokens consumed). Outbound INTERCEPTED before Telegram send.
             A DRAFT / borrador is created in the activity stream.
             0 outbound to lead (RN-10, SC-2, AC-2).
             Priority: medium.

  DECIDE   — handler_mode='ai' + proposal_required=False + no active pause.
             Normal operation: graph runs + outbound SENT.
             Priority: baseline.

Caller (brand chat extension hook — NOT OutputManager, §3-protected):
  decision = HonorModeBridge().resolve(conversation)
  if decision == HonorModeDecision.PAUSA:
      # skip AI entirely; persist inbound + feed inbox
  elif decision == HonorModeDecision.CONSULTA:
      # run graph; intercept before send; create draft
  else:  # DECIDE
      # run graph; send normally
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Protocol, runtime_checkable


class HonorModeDecision(str, Enum):
    """Operating mode resolved from conversation state."""

    DECIDE = "decide"  # AI active, proposal not required, no pause → send
    CONSULTA = "consulta"  # AI active, proposal required → draft, 0 outbound
    PAUSA = "pausa"  # handler=human OR future pause → skip AI entirely


@runtime_checkable
class ConversationModeFields(Protocol):
    """Minimal structural protocol — any object with these attributes is accepted."""

    handler_mode: str  # 'ai' | 'human'
    proposal_required: bool  # True = consulta HITL mode
    pause_until: datetime | None  # None or a timezone-aware datetime


class HonorModeBridge:
    """Pure resolver for per-conversation operating mode.

    Stateless — construct once, call resolve() many times.
    Thread-safe (no mutable state).
    """

    def resolve(self, conversation: ConversationModeFields) -> HonorModeDecision:
        """Return the current operating mode for this conversation.

        Priority order: PAUSA > CONSULTA > DECIDE.

        Args:
            conversation: Any object exposing handler_mode, proposal_required,
                          and pause_until attributes (duck-typed).

        Returns:
            HonorModeDecision enum value.
        """
        now = datetime.now(timezone.utc)

        # PAUSA: human control active OR pause window not yet expired
        if conversation.handler_mode == "human":
            return HonorModeDecision.PAUSA
        if conversation.pause_until is not None and conversation.pause_until > now:
            return HonorModeDecision.PAUSA

        # CONSULTA: AI active but operator wants to review before sending
        if conversation.proposal_required:
            return HonorModeDecision.CONSULTA

        # DECIDE: normal AI operation
        return HonorModeDecision.DECIDE
