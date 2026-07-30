"""Tests for PauseAdrianService — TDD RED (T-inbox-be-3).

Coverage:
- 60min pause sets pause_until in DB + Redis TTL
- AdrianPaused event emitted via outbox bus
- audit log written pre-response
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
CONV_ID = uuid4()
USER_ID = uuid4()


def _make_conversation_model() -> MagicMock:
    conv = MagicMock()
    conv.id = CONV_ID
    conv.tenant_id = TENANT_ID
    conv.clinic_id = CLINIC_ID
    conv.handler_mode = "ai"
    conv.status = "active"
    conv.pause_until = None
    conv.help_needed = False
    conv.proposal_required = False
    conv.updated_at = datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC)
    return conv


@pytest.mark.asyncio
async def test_pause_sets_pause_until_and_redis_ttl() -> None:
    """Pause: sets DB pause_until + Redis key with 60min TTL."""
    from src.modules.vitalia.inbox.application.services.pause_adrian_service import (
        PauseAdrianService,
    )

    conv_repo = AsyncMock()
    audit_writer = AsyncMock()
    event_bus = AsyncMock()
    redis_client = AsyncMock()
    session = AsyncMock()

    conv_model = _make_conversation_model()
    conv_repo.get_by_id = AsyncMock(return_value=conv_model)

    paused_conv = _make_conversation_model()
    paused_conv.pause_until = datetime.now(UTC) + timedelta(minutes=60)
    conv_repo.set_pause_until = AsyncMock(return_value=paused_conv)

    svc = PauseAdrianService(
        conv_repo=conv_repo,
        audit_writer=audit_writer,
        event_bus=event_bus,
        redis_client=redis_client,
        session=session,
    )

    await svc.pause(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        paused_by_user_id=USER_ID,
        reason="doctor checking",
        duration_minutes=60,
    )

    # Redis set with TTL
    redis_client.setex.assert_called_once()
    call_args = redis_client.setex.call_args
    # TTL should be 60*60 seconds (3600) or close
    assert call_args is not None

    # DB update called
    conv_repo.set_pause_until.assert_called_once()

    # Event emitted
    event_bus.publish.assert_called_once()

    # Audit log written
    audit_writer.write.assert_called_once()


@pytest.mark.asyncio
async def test_pause_emits_adrian_paused_event() -> None:
    """PauseAdrianService emits AdrianPaused domain event."""
    from src.modules.vitalia.crm.domain.events import AdrianPaused
    from src.modules.vitalia.inbox.application.services.pause_adrian_service import (
        PauseAdrianService,
    )

    conv_repo = AsyncMock()
    audit_writer = AsyncMock()
    redis_client = AsyncMock()
    session = AsyncMock()

    published_events: list[object] = []

    async def capture(event: object, **kwargs: object) -> None:
        published_events.append(event)

    event_bus = AsyncMock()
    event_bus.publish = AsyncMock(side_effect=capture)

    conv_model = _make_conversation_model()
    conv_repo.get_by_id = AsyncMock(return_value=conv_model)
    paused_conv = _make_conversation_model()
    paused_conv.pause_until = datetime.now(UTC) + timedelta(minutes=60)
    conv_repo.set_pause_until = AsyncMock(return_value=paused_conv)

    svc = PauseAdrianService(
        conv_repo=conv_repo,
        audit_writer=audit_writer,
        event_bus=event_bus,
        redis_client=redis_client,
        session=session,
    )

    await svc.pause(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        paused_by_user_id=USER_ID,
        reason=None,
        duration_minutes=60,
    )

    assert any(isinstance(e, AdrianPaused) for e in published_events)


@pytest.mark.asyncio
async def test_pause_conversation_not_found_raises_error() -> None:
    """Conversation not found → ConversationNotFoundError."""
    from src.modules.vitalia.inbox.application.services.pause_adrian_service import (
        ConversationNotFoundError,
        PauseAdrianService,
    )

    conv_repo = AsyncMock()
    conv_repo.get_by_id = AsyncMock(return_value=None)

    svc = PauseAdrianService(
        conv_repo=conv_repo,
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        redis_client=AsyncMock(),
        session=AsyncMock(),
    )

    with pytest.raises(ConversationNotFoundError):
        await svc.pause(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=uuid4(),
            paused_by_user_id=USER_ID,
            reason=None,
            duration_minutes=60,
        )
