# cap: inbox.adrian-inbox
"""Tests for NudgeService — TDD RED-first (T-2 vitalia-fase2-adrian-inbox).

SC-6 coverage (RN-13 — nudge = empujón 1:1 a UNA conv viva estancada):
- nudge on live stalled conversation → outbound + activity event 'nudge_sent' + audit row
- conv not found → ConvNotFoundError raised
- conv not open (status != 'open') → NudgeNotApplicableError raised
- conv not stalled (recent message within threshold) → NudgeNotApplicableError raised
- idempotency: same (tenant, conv, day) key → nudge_sent=False, no double-send
- cross-tenant: conv_id from different tenant → ConvNotFoundError (dual filter)
- reason forwarded to activity event description_es
- audit row written sync pre-response
- no new conversation created (RN-13 invariant)
- activity event repository called exactly once

PHI dual-filter: NudgeService accepts BOTH tenant_id AND clinic_id on every call.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
CONV_ID = uuid4()
USER_ID = uuid4()
MSG_ID = uuid4()
ACTIVITY_ID = uuid4()
TODAY = datetime.now(UTC).date()
_STALE_THRESHOLD_HOURS = 24


def _make_conversation(
    *,
    tenant_id=None,
    clinic_id=None,
    status: str = "open",
    last_message_at: datetime | None = None,
) -> MagicMock:
    """Create a minimal ConversationModel mock."""
    conv = MagicMock()
    conv.id = CONV_ID
    conv.tenant_id = tenant_id or TENANT_ID
    conv.clinic_id = clinic_id or CLINIC_ID
    conv.status = status
    # Default: stalled (last message was 2 days ago)
    conv.last_message_at = last_message_at or datetime.now(UTC) - timedelta(days=2)
    conv.channel = "whatsapp"
    conv.handler_mode = "ai"
    conv.deleted_at = None
    return conv


def _make_activity_event() -> MagicMock:
    evt = MagicMock()
    evt.id = ACTIVITY_ID
    evt.event_kind = "nudge_sent"
    evt.occurred_at = datetime.now(UTC)
    return evt


# ---------------------------------------------------------------------------
# Test: happy path — nudge on live stalled conversation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_happy_path_sends_outbound_and_writes_audit() -> None:
    """SC-6: nudge on live stalled conv → outbound sent, audit row + activity event written."""
    from src.modules.vitalia.inbox.application.services.nudge_service import NudgeService

    conv_repo = AsyncMock()
    conv_repo.get_by_id.return_value = _make_conversation()

    activity_repo = AsyncMock()
    activity_repo.find_nudge_today.return_value = None
    activity_repo.create.return_value = _make_activity_event()

    audit_writer = AsyncMock()
    event_bus = AsyncMock()

    proactive_result = MagicMock()
    proactive_result.message_id = MSG_ID
    proactive_result.conversation_id = CONV_ID
    proactive_result.sent_at = datetime.now(UTC)

    proactive_resolver = AsyncMock(return_value=proactive_result)

    svc = NudgeService(
        conv_repo=conv_repo,
        activity_repo=activity_repo,
        audit_writer=audit_writer,
        event_bus=event_bus,
        proactive_resolver=proactive_resolver,
    )

    result = await svc.nudge(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        sent_by_user_id=USER_ID,
        reason="paciente no responde desde hace 2 días",
    )

    # Outbound called exactly once
    proactive_resolver.assert_awaited_once()

    # Result fields
    assert result.nudge_sent is True
    assert result.conversation_id == CONV_ID
    assert result.message_id == MSG_ID
    assert result.sent_at is not None

    # Audit written sync
    audit_writer.write.assert_awaited_once()
    call_kwargs = audit_writer.write.call_args.kwargs
    assert call_kwargs["action"] == "inbox.nudge.sent"
    assert call_kwargs["tenant_id"] == TENANT_ID
    assert call_kwargs["clinic_id"] == CLINIC_ID

    # Activity event created
    activity_repo.create.assert_awaited_once()
    activity_call_kwargs = activity_repo.create.call_args.kwargs
    assert activity_call_kwargs["event_kind"] == "nudge_sent"


# ---------------------------------------------------------------------------
# Test: conversation not found → ConvNotFoundError
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_conv_not_found_raises() -> None:
    """get_by_id returns None (dual filter: wrong tenant/conv) → ConvNotFoundError."""
    from src.modules.vitalia.inbox.application.services.nudge_service import (
        ConvNotFoundError,
        NudgeService,
    )

    conv_repo = AsyncMock()
    conv_repo.get_by_id.return_value = None  # not found or wrong tenant

    svc = NudgeService(
        conv_repo=conv_repo,
        activity_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        proactive_resolver=AsyncMock(),
    )

    with pytest.raises(ConvNotFoundError):
        await svc.nudge(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=uuid4(),
            sent_by_user_id=USER_ID,
        )


# ---------------------------------------------------------------------------
# Test: conversation not open → NudgeNotApplicableError
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_conv_not_open_raises() -> None:
    """SC-6: conv with status 'closed' is not a live conversation → NudgeNotApplicableError."""
    from src.modules.vitalia.inbox.application.services.nudge_service import (
        NudgeNotApplicableError,
        NudgeService,
    )

    conv_repo = AsyncMock()
    conv_repo.get_by_id.return_value = _make_conversation(status="closed")

    svc = NudgeService(
        conv_repo=conv_repo,
        activity_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        proactive_resolver=AsyncMock(),
    )

    with pytest.raises(NudgeNotApplicableError, match="no está activa"):
        await svc.nudge(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=CONV_ID,
            sent_by_user_id=USER_ID,
        )


# ---------------------------------------------------------------------------
# Test: conversation not stalled (recent message) → NudgeNotApplicableError
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_conv_not_stalled_raises() -> None:
    """SC-6: conv with recent message (< 24h) is not stalled → NudgeNotApplicableError."""
    from src.modules.vitalia.inbox.application.services.nudge_service import (
        NudgeNotApplicableError,
        NudgeService,
    )

    conv_repo = AsyncMock()
    # Recent message 30 minutes ago — NOT stalled
    recent_msg_at = datetime.now(UTC) - timedelta(minutes=30)
    conv_repo.get_by_id.return_value = _make_conversation(last_message_at=recent_msg_at)

    svc = NudgeService(
        conv_repo=conv_repo,
        activity_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        proactive_resolver=AsyncMock(),
    )

    with pytest.raises(NudgeNotApplicableError, match="no está estancada"):
        await svc.nudge(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=CONV_ID,
            sent_by_user_id=USER_ID,
        )


# ---------------------------------------------------------------------------
# Test: idempotency — same natural key on same day → nudge_sent=False
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_idempotency_same_day_returns_no_double_send() -> None:
    """SC-6: Repeated nudge on same (tenant, conv, day) → nudge_sent=False, no outbound."""
    from src.modules.vitalia.inbox.application.services.nudge_service import NudgeService

    conv_repo = AsyncMock()
    conv_repo.get_by_id.return_value = _make_conversation()

    activity_repo = AsyncMock()
    # Simulate: activity repo detects duplicate (returns existing event)
    existing_event = _make_activity_event()
    activity_repo.find_nudge_today.return_value = existing_event  # dedup check

    audit_writer = AsyncMock()
    event_bus = AsyncMock()
    proactive_resolver = AsyncMock()

    svc = NudgeService(
        conv_repo=conv_repo,
        activity_repo=activity_repo,
        audit_writer=audit_writer,
        event_bus=event_bus,
        proactive_resolver=proactive_resolver,
    )

    result = await svc.nudge(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        sent_by_user_id=USER_ID,
        idempotency_key=f"nudge-{TENANT_ID}-{CONV_ID}-{TODAY}",
    )

    # No outbound sent on duplicate
    proactive_resolver.assert_not_awaited()
    assert result.nudge_sent is False
    assert result.conversation_id == CONV_ID
    assert result.activity_event_id == ACTIVITY_ID


# ---------------------------------------------------------------------------
# Test: explicit idempotency_key provided and dedup does not apply (first call)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_with_idempotency_key_first_call_sends() -> None:
    """Explicit idempotency_key on first call → sends normally."""
    from src.modules.vitalia.inbox.application.services.nudge_service import NudgeService

    conv_repo = AsyncMock()
    conv_repo.get_by_id.return_value = _make_conversation()

    activity_repo = AsyncMock()
    activity_repo.find_nudge_today.return_value = None  # no prior nudge today
    activity_repo.create.return_value = _make_activity_event()

    proactive_result = MagicMock()
    proactive_result.message_id = MSG_ID
    proactive_result.conversation_id = CONV_ID
    proactive_result.sent_at = datetime.now(UTC)
    proactive_resolver = AsyncMock(return_value=proactive_result)

    svc = NudgeService(
        conv_repo=conv_repo,
        activity_repo=activity_repo,
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        proactive_resolver=proactive_resolver,
    )

    result = await svc.nudge(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        sent_by_user_id=USER_ID,
        idempotency_key="custom-key-abc123",
    )

    proactive_resolver.assert_awaited_once()
    assert result.nudge_sent is True


# ---------------------------------------------------------------------------
# Test: cross-tenant isolation — conv from tenant B returns None for tenant A
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_cross_tenant_raises_not_found() -> None:
    """RN-9 / SC-10: Cross-tenant query → dual filter returns None → ConvNotFoundError."""
    from src.modules.vitalia.inbox.application.services.nudge_service import (
        ConvNotFoundError,
        NudgeService,
    )

    conv_repo = AsyncMock()
    # Dual filter: tenant_a querying tenant_b's conv → None
    conv_repo.get_by_id.return_value = None

    svc = NudgeService(
        conv_repo=conv_repo,
        activity_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        proactive_resolver=AsyncMock(),
    )

    with pytest.raises(ConvNotFoundError):
        await svc.nudge(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=CONV_ID,
            sent_by_user_id=USER_ID,
        )

    # Verify dual filter: get_by_id called with both tenant_id AND scope_id
    conv_repo.get_by_id.assert_awaited_once()
    call_kwargs = conv_repo.get_by_id.call_args.kwargs
    assert call_kwargs.get("tenant_id") == TENANT_ID
    assert call_kwargs.get("scope_id") == CLINIC_ID


# ---------------------------------------------------------------------------
# Test: reason forwarded to activity event description_es
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_reason_forwarded_to_activity_description() -> None:
    """reason param forwarded to activity event description_es."""
    from src.modules.vitalia.inbox.application.services.nudge_service import NudgeService

    conv_repo = AsyncMock()
    conv_repo.get_by_id.return_value = _make_conversation()

    activity_repo = AsyncMock()
    activity_repo.find_nudge_today.return_value = None
    activity_repo.create.return_value = _make_activity_event()

    proactive_result = MagicMock()
    proactive_result.message_id = MSG_ID
    proactive_result.conversation_id = CONV_ID
    proactive_result.sent_at = datetime.now(UTC)

    svc = NudgeService(
        conv_repo=conv_repo,
        activity_repo=activity_repo,
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        proactive_resolver=AsyncMock(return_value=proactive_result),
    )

    test_reason = "paciente inactivo 3 días — reactivación manual"
    await svc.nudge(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        sent_by_user_id=USER_ID,
        reason=test_reason,
    )

    # Activity event create called with description_es containing the reason
    activity_repo.create.assert_awaited_once()
    create_kwargs = activity_repo.create.call_args.kwargs
    assert test_reason in create_kwargs.get("description_es", "")


# ---------------------------------------------------------------------------
# Test: no new conversation created (RN-13 invariant)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_does_not_create_new_conversation() -> None:
    """RN-13: nudge ONLY works on existing live conv — never creates a new one."""
    from src.modules.vitalia.inbox.application.services.nudge_service import NudgeService

    conv_repo = AsyncMock()
    conv_repo.get_by_id.return_value = _make_conversation()

    activity_repo = AsyncMock()
    activity_repo.find_nudge_today.return_value = None
    activity_repo.create.return_value = _make_activity_event()

    proactive_result = MagicMock()
    proactive_result.message_id = MSG_ID
    proactive_result.conversation_id = CONV_ID
    proactive_result.sent_at = datetime.now(UTC)

    svc = NudgeService(
        conv_repo=conv_repo,
        activity_repo=activity_repo,
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        proactive_resolver=AsyncMock(return_value=proactive_result),
    )

    await svc.nudge(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        sent_by_user_id=USER_ID,
    )

    # get_or_create NOT called — only get_by_id
    assert not hasattr(conv_repo, "get_or_create") or conv_repo.get_or_create.call_count == 0
    assert not hasattr(conv_repo, "create") or conv_repo.create.call_count == 0
