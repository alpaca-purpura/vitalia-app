# cap: sales_agent.honor-mode-bridge
# story-origin: vitalia-fase2-adrian-canal-inbound T-AG-GAP23
"""VitaliaInboundSeamAdapter — brand adapter for the engine inbound seam (GAP-2/3).

Wires vitalia's existing :class:`HonorModeBridge` into the engine
``inbound_mode_seam`` (mode resolver + draft sink) and writes
``vitalia_activity_events`` rows from the engine ``AgentTurnCompletedEvent``
(activity subscriber). The engine knows NOTHING vitalia — it only sees an
``InboundMode`` enum + best-effort hooks; this adapter is the brand side.

Three responsibilities (all dual-filtered tenant_id + clinic_id, all sanitized,
all best-effort — a brand failure NEVER breaks the inbound turn):

1. **resolve_mode** — load the open Conversation for a lead (tenant-scoped), run
   :class:`HonorModeBridge` (PAUSA > CONSULTA > DECIDE), map its
   :class:`HonorModeDecision` → engine :class:`InboundMode`. No conversation →
   DECIDE (engine default — never blocks).

2. **draft_sink** — on CONSULTA the engine suppressed outbound; we persist an
   ``adrian_draft_pending`` activity row so the operator sees Adrián drafted a
   reply pending review. Generic ``description_es`` (no raw body), payload
   sanitized (IDs + stage only — the draft text NEVER lands in the activity row;
   HIPAA-lite + the inbox is a glass-box of *that something happened*, not of PHI).

3. **on_agent_turn_completed** — subscriber for ``AgentTurnCompletedEvent``
   (delivered as a reconstructed ``DomainEvent`` with ``.event_name``/``.payload``
   by the outbox dispatcher, OR the in-memory bus). Writes a generic
   ``adrian_turn`` activity row from the event's IDs + funnel_stage.

The clinic_id is ALWAYS resolved from the conversation (authoritative dual
filter) — never trusted from the event payload (the engine event carries no
clinic_id by design: IDs the brand can re-resolve, never PHI).

Anti-duplication: REUSES ``HonorModeBridge`` (resolver) + ``ActivityEventRepository``
(writer) + ``sanitize_payload`` (shared engine). NO new abstraction.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable
from uuid import UUID

import structlog
from luana_core_observability.recording.sanitization import sanitize_payload
from luana_core_sales_agent.application.orchestrator.inbound_mode_seam import InboundMode

from src.modules.vitalia.sales_agent.application.services.honor_mode_bridge import (
    HonorModeBridge,
    HonorModeDecision,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = structlog.get_logger()

#: HonorModeDecision → engine InboundMode (1:1 by value).
_DECISION_TO_MODE: dict[HonorModeDecision, InboundMode] = {
    HonorModeDecision.DECIDE: InboundMode.DECIDE,
    HonorModeDecision.CONSULTA: InboundMode.CONSULTA,
    HonorModeDecision.PAUSA: InboundMode.PAUSA,
}

#: Generic, PHI-free activity descriptions (Spanish neutro — operator-facing).
_DRAFT_DESCRIPTION_ES = "Adrián preparó un borrador de respuesta pendiente de tu revisión."
_TURN_DESCRIPTION_ES = "Adrián respondió en la conversación."

_AGENT_TURN_EVENT_NAME = "agent_turn_completed"


@runtime_checkable
class ConversationModeFields(Protocol):
    """The Conversation fields this adapter reads (duck-typed)."""

    id: UUID
    clinic_id: UUID
    handler_mode: str
    proposal_required: bool
    pause_until: object | None


class _ConvLoader(Protocol):
    """Loads the open Conversation for a lead (tenant-scoped). None if absent."""

    def __call__(self, *, tenant_id: UUID, lead_id: UUID | None) -> "Awaitable[Any]":
        """Return the Conversation or None."""
        ...


class _ActivityWriter(Protocol):
    """Writes one vitalia_activity_events row (dual filter enforced by the repo)."""

    def __call__(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        conversation_id: UUID,
        event_kind: str,
        description_es: str,
        agent_id: str,
        payload_sanitized: dict,
    ) -> "Awaitable[Any]":
        """Append a non-PHI activity event."""
        ...


class VitaliaInboundSeamAdapter:
    """Brand adapter bridging vitalia mode + activity into the engine seam.

    Collaborators are injected (Protocol-typed) so unit tests drive each
    responsibility without a real DB / engine. The composition root
    (``composition.py``) opens an AsyncSession per call (main-loop bound) and
    builds the loader + writer from the brand repos.
    """

    def __init__(self, *, conv_loader: _ConvLoader, activity_writer: _ActivityWriter) -> None:
        """Initialize with a conversation loader + an activity writer port."""
        self._conv_loader = conv_loader
        self._activity_writer = activity_writer
        self._bridge = HonorModeBridge()

    # ── 1. mode resolver ──────────────────────────────────────────────

    async def resolve_mode_async(self, *, tenant_id: UUID, lead_id: UUID | None) -> InboundMode:
        """Resolve the inbound mode for this lead's open conversation.

        No conversation → DECIDE (never blocks). Maps HonorModeDecision → InboundMode.
        """
        conv = await self._conv_loader(tenant_id=tenant_id, lead_id=lead_id)
        if conv is None:
            return InboundMode.DECIDE
        decision = self._bridge.resolve(conv)  # type: ignore[arg-type]
        return _DECISION_TO_MODE.get(decision, InboundMode.DECIDE)

    # ── 2. draft sink (CONSULTA) ──────────────────────────────────────

    async def draft_sink_async(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID | None,
        draft_text: str,  # noqa: ARG002 — deliberately NOT persisted (PHI containment)
        result: dict,
    ) -> None:
        """Persist an ``adrian_draft_pending`` activity row for a suppressed (CONSULTA) reply.

        The draft text itself is NEVER stored in the activity row — the inbox
        shows that Adrián drafted *something* pending review (glass-box), not the
        content. The full draft lives in the conversation message log (audit), not
        the activity timeline.
        """
        conv = await self._conv_loader(tenant_id=tenant_id, lead_id=lead_id)
        if conv is None:
            logger.info(
                "inbound_draft_sink_no_conversation",
                tenant_id=str(tenant_id),
            )
            return
        payload = sanitize_payload(
            {
                "lead_id": str(lead_id) if lead_id else None,
                "funnel_stage": result.get("current_state", "rapport"),
                # NO draft_text / content — PHI containment.
            }
        )
        await self._activity_writer(
            tenant_id=tenant_id,
            clinic_id=conv.clinic_id,
            conversation_id=conv.id,
            event_kind="adrian_draft_pending",
            description_es=_DRAFT_DESCRIPTION_ES,
            agent_id="adrian",
            payload_sanitized=payload,
        )

    # ── 3. activity subscriber ────────────────────────────────────────

    async def on_agent_turn_completed_async(self, event: Any) -> None:  # noqa: ANN401 — duck-typed DomainEvent
        """Write an ``adrian_turn`` activity row from an AgentTurnCompletedEvent.

        Accepts the outbox-reconstructed ``DomainEvent`` (``.event_name`` +
        ``.payload`` dict) OR the in-memory event. Ignores other events. clinic_id
        is re-resolved from the conversation (authoritative — the event carries
        IDs + stage only, never clinic_id / PHI).
        """
        if getattr(event, "event_name", None) != _AGENT_TURN_EVENT_NAME:
            return
        payload = dict(getattr(event, "payload", {}) or {})
        tenant_id = getattr(event, "tenant_id", None)
        lead_raw = payload.get("lead_id")
        lead_id = UUID(lead_raw) if lead_raw else None
        if tenant_id is None:
            return

        conv = await self._conv_loader(tenant_id=tenant_id, lead_id=lead_id)
        if conv is None:
            logger.info("agent_turn_activity_no_conversation", tenant_id=str(tenant_id))
            return

        conv_raw = payload.get("conversation_id")
        conversation_id = UUID(conv_raw) if conv_raw else conv.id
        sanitized = sanitize_payload(
            {
                "lead_id": payload.get("lead_id"),
                "role": payload.get("role"),
                "funnel_stage": payload.get("funnel_stage"),
                # IDs + stage ONLY — no message body ever reaches here.
            }
        )
        await self._activity_writer(
            tenant_id=tenant_id,
            clinic_id=conv.clinic_id,
            conversation_id=conversation_id,
            event_kind="adrian_turn",
            description_es=_TURN_DESCRIPTION_ES,
            agent_id="adrian",
            payload_sanitized=sanitized,
        )


def build_agent_turn_completed_handler(adapter: VitaliaInboundSeamAdapter) -> "Callable[[Any], None]":
    """Build the SYNC subscriber registered via ``EventBus.subscribe``.

    The in-memory bus + outbox dispatcher call handlers SYNCHRONOUSLY. This
    wrapper schedules the adapter's async write on the running loop when one is
    available (the outbox worker runs inside an event loop); otherwise it runs
    the coroutine to completion. Best-effort — never raises into the dispatcher.
    """

    def _handler(event: Any) -> None:  # noqa: ANN401 — duck-typed DomainEvent
        try:
            coro = adapter.on_agent_turn_completed_async(event)
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop is not None and loop.is_running():
                # fire-and-forget on the dispatcher's loop (best-effort).
                loop.create_task(coro)  # noqa: RUF006 — intentional fire-and-forget
            else:
                asyncio.run(coro)
        except Exception:  # noqa: BLE001 — subscriber is best-effort, never breaks dispatch
            logger.warning("agent_turn_activity_handler_failed", exc_info=True)

    return _handler


__all__ = [
    "VitaliaInboundSeamAdapter",
    "build_agent_turn_completed_handler",
]
