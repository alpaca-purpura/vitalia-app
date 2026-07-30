# cap: inbox.adrian-inbox
# story-origin: vitalia-fase2-adrian-inbox T-2
"""NudgeService — vitalia inbox application layer.

Empujón 1:1 a UNA conversación viva estancada (RN-13).

Scope (hard boundaries per 03-arch-be.md § 6.2):
- Applies ONLY to an existing OPEN conversation.
- Conversation must be stalled (last_message_at > STALE_THRESHOLD_HOURS ago).
- Does NOT create a new conversation (RN-13 invariant).
- Does NOT re-activate cold leads (that is Camila's domain).
- Consumes send_proactive_reengagement (brand tool, shipped) via proactive_resolver DI
  — NEVER imports directly from sales_agent/.

Idempotency dedup:
- Natural key: (tenant_id, conv_id, 'nudge_sent', UTC-date).
- Checks ActivityEventRepository.find_nudge_today() before sending.
- Repeated call on same day → nudge_sent=False, no double outbound.

PHI obligations (hipaa-lite.md § Regla cardinal):
1. tenant_id + clinic_id dual filter on all repo calls.
2. Audit log row written sync pre-response.
3. Activity event description_es: no raw PHI (uses conversation_id reference only).
4. proactive_resolver result is structural only (no PHI echoed to logs).

Anti-coupling guard:
  ❌ NEVER import sales_agent tools directly — coupling breaks DDD boundaries.
  ✅ Always: proactive_resolver callable injected via DI (service resolver pattern).

downstream-regression-na: brand-local vitalia inbox service
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

if TYPE_CHECKING:
    from src.modules.vitalia.crm.infrastructure.persistence.activity_event_repository import (
        ActivityEventRepository,
    )
    from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
        ConversationRepository,
    )

logger = structlog.get_logger()

# Staleness threshold: conv with last message older than this is considered stalled.
# RN-13: nudge applies to "stalled" live conversations.
_STALE_THRESHOLD_HOURS: int = 24

# Agent identifier written to activity events (Adrian owns the inbox).
_AGENT_ID: str = "adrian"


# ---------------------------------------------------------------------------
# Domain exceptions
# ---------------------------------------------------------------------------


class ConvNotFoundError(Exception):
    """Raised when the conversation is not found (or access denied by dual filter)."""

    def __init__(self, conv_id: UUID) -> None:
        """Initialize."""
        super().__init__(f"Conversación {conv_id} no encontrada o acceso denegado.")
        self.conv_id = conv_id


class NudgeNotApplicableError(Exception):
    """Raised when nudge cannot be applied to the conversation.

    Possible causes:
    - Conv status is not 'open' (RN-13: must be a live conversation).
    - Conv is not stalled (last message < STALE_THRESHOLD_HOURS ago).
    """

    def __init__(self, *, conv_id: UUID, reason: str) -> None:
        """Initialize."""
        super().__init__(f"Conversación {conv_id}: {reason}")
        self.conv_id = conv_id
        self.reason = reason


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class NudgeResult:
    """Result from NudgeService.nudge()."""

    conversation_id: UUID
    message_id: UUID | None
    nudge_sent: bool
    activity_event_id: UUID | None
    sent_at: datetime


# ---------------------------------------------------------------------------
# NudgeService
# ---------------------------------------------------------------------------


class NudgeService:
    """Re-engagement empujón 1:1 on a live stalled conversation.

    Consumes send_proactive_reengagement (brand tool) via a resolver callable
    injected at construction. NEVER imports from sales_agent/ directly
    (anti-coupling per anti-duplication.md + 03-arch-be.md § 6.2).

    The resolver signature is:
        async def proactive_resolver(*, tenant_id, clinic_id, conversation_id,
                                     sent_by_user_id, reason) -> ProactiveResult
    where ProactiveResult has: .message_id: UUID, .conversation_id: UUID, .sent_at: datetime.
    """

    def __init__(
        self,
        *,
        conv_repo: ConversationRepository,
        activity_repo: ActivityEventRepository,
        audit_writer: object,
        event_bus: object,
        proactive_resolver: Callable[..., Awaitable[object]],
    ) -> None:
        """Initialize NudgeService.

        Args:
            conv_repo: ConversationRepository (dual-filter enforced).
            activity_repo: ActivityEventRepository (dual-filter enforced).
            audit_writer: AsyncAuditWriter (sync write pre-response).
            event_bus: Outbox event bus for domain event emission.
            proactive_resolver: Async callable resolving the proactive re-engagement
                send. Injected by DI (never instantiated from sales_agent/).
        """
        self._conv_repo = conv_repo
        self._activity_repo = activity_repo
        self._audit_writer = audit_writer
        self._event_bus = event_bus
        self._proactive_resolver = proactive_resolver

    async def nudge(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        conversation_id: UUID,
        sent_by_user_id: UUID,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> NudgeResult:
        """Send a 1:1 re-engagement nudge to a live stalled conversation.

        PHI dual-filter: all repo calls include tenant_id AND clinic_id.
        Idempotency: checks for an existing nudge_sent event today before sending.
        Audit log written sync pre-response (hipaa-lite.md § Audit log).

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite second scope filter).
            conversation_id: Target conversation UUID (must be open + stalled).
            sent_by_user_id: User triggering the nudge.
            reason: Optional reason (forwarded to activity event description_es).
            idempotency_key: Optional client key (natural key used if omitted).

        Returns:
            NudgeResult(nudge_sent=True) on new send.
            NudgeResult(nudge_sent=False) on same-day dedup.

        Raises:
            ConvNotFoundError: Conversation not found or access denied.
            NudgeNotApplicableError: Conv not open or not stalled.
        """
        now = datetime.now(UTC)

        # 1. Fetch conversation (dual filter: tenant_id + clinic_id)
        conv = await self._conv_repo.get_by_id(
            id=conversation_id,
            tenant_id=tenant_id,
            scope_id=clinic_id,
        )
        if conv is None:
            raise ConvNotFoundError(conversation_id)

        # 2. Validate conv is live (open)
        if conv.status != "open":
            raise NudgeNotApplicableError(
                conv_id=conversation_id,
                reason="La conversación no está activa (status != open).",
            )

        # 3. Validate conv is stalled (last message older than threshold)
        last_msg_at = getattr(conv, "last_message_at", None)
        if last_msg_at is not None:
            if (now - last_msg_at) < timedelta(hours=_STALE_THRESHOLD_HOURS):
                raise NudgeNotApplicableError(
                    conv_id=conversation_id,
                    reason=(
                        f"La conversación no está estancada: último mensaje hace "
                        f"{(now - last_msg_at).total_seconds() / 3600:.1f}h "
                        f"(umbral: {_STALE_THRESHOLD_HOURS}h)."
                    ),
                )

        # 4. Idempotency dedup: check for existing nudge_sent today
        existing_event = await self._activity_repo.find_nudge_today(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            conversation_id=conversation_id,
        )
        if existing_event is not None:
            logger.info(
                "nudge_service.dedup_skipped",
                tenant_id=str(tenant_id),
                conversation_id=str(conversation_id),
                existing_event_id=str(existing_event.id),
            )
            return NudgeResult(
                conversation_id=conversation_id,
                message_id=None,
                nudge_sent=False,
                activity_event_id=existing_event.id,
                sent_at=existing_event.occurred_at,
            )

        # 5. Invoke proactive re-engagement via resolver (service resolver pattern)
        #    NEVER import from sales_agent/ directly.
        proactive_result = await self._proactive_resolver(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            conversation_id=conversation_id,
            sent_by_user_id=sent_by_user_id,
            reason=reason,
        )

        # 6. Write activity event (description_es — no raw PHI, conv_id reference only)
        description_es = f"Empujón de reactivación enviado. Conversación: {conversation_id}."
        if reason:
            description_es = f"{description_es} Motivo: {reason}"

        activity_event = await self._activity_repo.create(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            conversation_id=conversation_id,
            event_kind="nudge_sent",
            description_es=description_es,
            agent_id=_AGENT_ID,
            occurred_at=now,
            payload_sanitized={
                "nudge_sent": True,
                "conversation_id": str(conversation_id),
                "idempotency_key": idempotency_key,
                # message_id and sent_by_user_id are structural, not PHI
                "sent_by_user_id": str(sent_by_user_id),
            },
        )

        # 7. Audit log sync write — MANDATORY pre-response (hipaa-lite.md § Audit log)
        await self._audit_writer.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=sent_by_user_id,
            action="inbox.nudge.sent",
            resource_type="inbox.nudge",
            resource_id=activity_event.id,
            payload={
                "conversation_id": str(conversation_id),
                "idempotency_key": idempotency_key,
            },
        )

        logger.info(
            "nudge_service.sent",
            tenant_id=str(tenant_id),
            conversation_id=str(conversation_id),
            activity_event_id=str(activity_event.id),
        )

        return NudgeResult(
            conversation_id=conversation_id,
            message_id=getattr(proactive_result, "message_id", None),
            nudge_sent=True,
            activity_event_id=activity_event.id,
            sent_at=now,
        )
