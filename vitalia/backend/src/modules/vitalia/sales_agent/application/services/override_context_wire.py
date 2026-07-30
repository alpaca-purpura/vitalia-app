# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""OverrideContextWire — RN-4.1 override-context wire (brand-extension, thin).

When a human manually overrides a lead's funnel stage WITH a reason, the crm
``FunnelService.transition_stage`` emits the ``lead_stage_overridden`` domain
event (outbox). This wire is the brand-local subscriber of that event. It does
two things — both via INJECTED PORTS, so it never imports ``crm`` (cross-module
ban, backend-ddd) nor the engine's sync state repository / checkpoint model
(anti-duplication; the ``agent_state_checkpoints`` schema is §3-protected):

  1. Persists ``override_context`` into the EXISTING nullable ``metadata_info``
     JSONB of the active ``agent_state_checkpoints`` row — so the sales agent's
     NEXT turn reads the human's reason and does NOT re-prompt questions already
     answered (RN-4.1: "feeds the agent, does not reinitialize it"). No schema
     change, no new column, no checkpoint reset.
  2. Settles the handover (🙋 humano → 🤖 Adrián) as a NON-PHI activity in the
     lead commercial timeline, so the Historial shows the takeover.

Scope is intentionally minimal (03-arch.md § 8): NO new LangGraph state, NO new
topology, NO new tool, NO new prompt/specialist, NO eval goldens. The
override-context is a volatile per-turn signal (§ 8.5) — it never enters a
cacheable prompt prefix.

Best-effort: the origin override turn (the PATCH /stage) has already committed
by the time this runs. A failure here MUST NOT propagate — it is logged and
swallowed (graceful-degradation).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol, runtime_checkable
from uuid import UUID

import structlog
from pydantic import BaseModel, ConfigDict

logger = structlog.get_logger()

#: JSONB key under ``agent_state_checkpoints.metadata_info`` where the agent's
#: next turn reads the override-context. Brand-local convention (NOT a column).
OVERRIDE_CONTEXT_KEY = "override_context"

#: Max chars of the human reason surfaced in the Historial micro-log (NON-PHI,
#: commercial text only — the reason is operator-authored funnel context).
_REASON_SNIPPET_LEN = 120


def _utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


class LeadStageOverriddenEvent(BaseModel):
    """Typed view of the ``lead_stage_overridden`` outbox payload (from T-BE-2).

    UUID fields are coerced from their stringified outbox form. Extra keys are
    ignored so the wire is resilient to additive payload evolution.
    """

    model_config = ConfigDict(extra="ignore")

    event_type: str = "lead_stage_overridden"
    tenant_id: UUID
    lead_id: UUID
    from_stage: str | None = None
    to_stage: str
    reason: str | None = None
    actor_user_id: UUID | None = None
    version_after: int | None = None


@runtime_checkable
class CheckpointMetadataPort(Protocol):
    """Writes override-context to the agent's next-turn read surface.

    Concrete brand adapter (deferred — wired when Inbox/sales_agent is live)
    reads the active checkpoint for ``(tenant_id, lead_id)`` and merges
    ``override_context`` into its ``metadata_info`` JSONB. The wire stays
    decoupled from the engine's SYNC state repository and checkpoint model
    concretions (only this Protocol is known here).

    Returns ``True`` if a checkpoint was found and updated, ``False`` if there
    is no active checkpoint yet (agent has never run on this lead — the context
    is simply not persisted; the override still stands in the funnel).
    """

    async def set_override_context(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        override_context: dict,
    ) -> bool:
        """Merge ``override_context`` into the active checkpoint's metadata_info."""
        ...


@runtime_checkable
class HandoverActivityPort(Protocol):
    """Records the 🙋→🤖 handover in the lead commercial timeline (NON-PHI).

    Concrete brand adapter delegates to the crm ``LeadActivityRepository.record``
    — but the wire only knows this Protocol, never the crm concretion (DDD
    cross-module ban). ``description_es`` must be Spanish neutro, 3rd person,
    NEVER clinical/PHI (RN-2 firewall).
    """

    async def record_handover(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        description_es: str,
    ) -> None:
        """Append a handover activity to the lead timeline."""
        ...


class OverrideContextWire:
    """Brand-local subscriber that feeds a manual override into the agent.

    Construct with the two ports; call :meth:`handle_lead_stage_overridden` with
    the raw outbox payload (the subscriber registration point passes it through).
    """

    def __init__(
        self,
        *,
        metadata_port: CheckpointMetadataPort,
        activity_port: HandoverActivityPort,
    ) -> None:
        """Initialize with injected ports (no crm / engine concretions)."""
        self._metadata_port = metadata_port
        self._activity_port = activity_port

    async def handle_lead_stage_overridden(self, payload: dict) -> None:
        """Handle one ``lead_stage_overridden`` event (best-effort, never raises).

        Args:
            payload: Raw outbox payload (shape from T-BE-2 FunnelService step 10).

        Raises:
            ValueError | KeyError: ONLY for a malformed payload missing the
                tenant_id (tenant-isolation guard — a cross-tenant write must
                never proceed on incomplete data). All downstream port failures
                are swallowed.
        """
        event = LeadStageOverriddenEvent.model_validate(payload)

        # RN-4.1: nothing to inject without a human reason → skip silently.
        if not event.reason or not event.reason.strip():
            logger.debug(
                "override_context_wire_skip_no_reason",
                tenant_id=str(event.tenant_id),
                lead_id=str(event.lead_id),
            )
            return

        reason = event.reason.strip()
        override_context = {
            "reason": reason,
            "from_stage": event.from_stage,
            "to_stage": event.to_stage,
            "actor_user_id": str(event.actor_user_id) if event.actor_user_id else None,
            "source": "manual_override",
            "occurred_at": _utc_now().isoformat(),
        }

        # 1. Persist to the agent's next-turn read surface (best-effort).
        try:
            updated = await self._metadata_port.set_override_context(
                tenant_id=event.tenant_id,
                lead_id=event.lead_id,
                override_context=override_context,
            )
            if not updated:
                logger.info(
                    "override_context_wire_no_active_checkpoint",
                    tenant_id=str(event.tenant_id),
                    lead_id=str(event.lead_id),
                )
        except Exception:  # noqa: BLE001 — best-effort; origin turn already committed.
            logger.warning(
                "override_context_wire_metadata_write_failed",
                tenant_id=str(event.tenant_id),
                lead_id=str(event.lead_id),
            )

        # 2. Settle the 🙋 humano → 🤖 Adrián handover in the timeline (best-effort).
        description_es = self._build_handover_description(reason)
        try:
            await self._activity_port.record_handover(
                tenant_id=event.tenant_id,
                lead_id=event.lead_id,
                description_es=description_es,
            )
        except Exception:  # noqa: BLE001 — best-effort observability.
            logger.warning(
                "override_context_wire_handover_record_failed",
                tenant_id=str(event.tenant_id),
                lead_id=str(event.lead_id),
            )

        logger.info(
            "override_context_wire_complete",
            tenant_id=str(event.tenant_id),
            lead_id=str(event.lead_id),
            to_stage=event.to_stage,
        )

    @staticmethod
    def _build_handover_description(reason: str) -> str:
        """Spanish neutro, 3rd person, NON-PHI handover micro-log.

        The reason is operator-authored commercial funnel context (RN-2 firewall
        guarantees no clinical data enters the funnel layer), so it is safe to
        surface a snippet in the Historial.
        """
        snippet = reason[:_REASON_SNIPPET_LEN]
        return f"🙋 Un humano tomó el control y devolvió la atención a 🤖 Adrián. Motivo: {snippet}"
