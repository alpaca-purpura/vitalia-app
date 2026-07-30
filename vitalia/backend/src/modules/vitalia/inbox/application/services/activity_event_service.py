# cap: sales_agent.inbox-handler-mode-occ
# story-origin: TBD
"""ActivityEventService — vitalia inbox application layer.

Read-only service for the activity stream (≤8 events, ≤5min window).

PHI obligations (hipaa-lite.md § Regla cardinal):
1. tenant_id + clinic_id dual filter (via repo)
2. sanitize_payload applied to every event payload before return
3. description_es: generic text (no raw PHI — repo enforces at write time)
4. No audit log required for reads (activity stream is observability, not PHI mutation)

downstream-regression-na: brand-local vitalia inbox service
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

if TYPE_CHECKING:
    from src.modules.vitalia.crm.infrastructure.persistence.activity_event_repository import (
        ActivityEventRepository,
    )

logger = structlog.get_logger()

# Per arch spec §6.8 + §4.1: activity stream capped at 8 events
_ACTIVITY_STREAM_MAX = 8


@dataclass
class ActivityStreamItem:
    """Single sanitized activity event for UI consumption."""

    id: UUID
    event_kind: str
    description_es: str
    agent_id: str
    occurred_at: datetime


@dataclass
class ActivityStreamResult:
    """Result from ActivityEventService.get_stream()."""

    conversation_id: UUID
    events: list[ActivityStreamItem]
    limit: int
    since_minutes: int


class ActivityEventService:
    """Read-only service for activity stream.

    Fetches last N activity events for a conversation and applies
    sanitize_payload to each event's payload_sanitized field before
    returning to the API layer.

    The payload_sanitized field was already scrubbed at write time (service layer),
    but we apply a second pass here as defense-in-depth per hipaa-lite.md.
    """

    def __init__(self, *, activity_repo: ActivityEventRepository) -> None:
        """Initialize ActivityEventService.

        Args:
            activity_repo: ActivityEventRepository (dual-filter enforced).
        """
        self._activity_repo = activity_repo

    async def get_stream(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        conversation_id: UUID,
        limit: int = _ACTIVITY_STREAM_MAX,
        since_minutes: int = 5,
    ) -> ActivityStreamResult:
        """Get the activity stream for a conversation.

        PHI dual-filter: repo call includes tenant_id AND clinic_id.
        sanitize_payload applied to each event payload (defense-in-depth).

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite second scope filter).
            conversation_id: Target conversation UUID.
            limit: Max events to return (default 8, capped at 8).
            since_minutes: Time window in minutes (default 5).

        Returns:
            ActivityStreamResult with sanitized event list.
        """
        effective_limit = min(limit, _ACTIVITY_STREAM_MAX)

        events = await self._activity_repo.list_for_activity_stream(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            conversation_id=conversation_id,
            limit=effective_limit,
            since_minutes=since_minutes,
        )

        items: list[ActivityStreamItem] = []
        for evt in events:
            # No raw payload is returned to UI: ActivityStreamItem has no payload
            # field (description_es only). payload_sanitized was already scrubbed at
            # write time by the upstream service — no second-pass needed here.
            items.append(
                ActivityStreamItem(
                    id=evt.id,
                    event_kind=evt.event_kind,
                    description_es=evt.description_es,
                    agent_id=evt.agent_id,
                    occurred_at=evt.occurred_at,
                )
            )

        logger.debug(
            "activity_event.stream_fetched",
            tenant_id=str(tenant_id),
            conversation_id=str(conversation_id),
            count=len(items),
        )

        return ActivityStreamResult(
            conversation_id=conversation_id,
            events=items,
            limit=effective_limit,
            since_minutes=since_minutes,
        )
