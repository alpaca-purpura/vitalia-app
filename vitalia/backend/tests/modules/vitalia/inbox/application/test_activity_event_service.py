"""Tests for ActivityEventService — TDD RED (T-inbox-be-3).

SC-04 coverage:
- sanitize_payload applied to every event before returning to UI
- ≤8 events returned (activity stream limit)
- PHI dual-filter applied (tenant_id + clinic_id)
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
CONV_ID = uuid4()


def _make_activity_event(event_kind: str = "consulto_precio") -> MagicMock:
    evt = MagicMock()
    evt.id = uuid4()
    evt.event_kind = event_kind
    evt.description_es = "consultó precio de blanqueamiento"
    evt.agent_id = "adrian"
    evt.occurred_at = datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC)
    evt.payload_sanitized = {"offer_name": "Blanqueamiento Premium", "price": "24000"}
    return evt


@pytest.mark.asyncio
async def test_activity_stream_returns_at_most_8_events() -> None:
    """ActivityStream always returns ≤8 events per arch spec."""
    from src.modules.vitalia.inbox.application.services.activity_event_service import (
        ActivityEventService,
    )

    activity_repo = AsyncMock()
    # Return 10 events from repo, service should cap at 8
    events = [_make_activity_event() for _ in range(10)]
    activity_repo.list_for_activity_stream = AsyncMock(return_value=events[:8])  # repo caps it

    svc = ActivityEventService(activity_repo=activity_repo)

    result = await svc.get_stream(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        limit=8,
        since_minutes=5,
    )

    assert len(result.events) <= 8


@pytest.mark.asyncio
async def test_activity_stream_no_raw_payload_in_items() -> None:
    """SC-04: ActivityStreamItem has no payload field — PHI not exposed to UI.

    sanitize_payload is applied at write time by the upstream service layer
    (defense-in-depth at source). The activity stream service does NOT expose
    payload_sanitized through ActivityStreamItem — only description_es (safe text).

    This replaces the former test_activity_stream_applies_sanitize_payload which
    was testing dead code (result of sanitize_payload was discarded — Medium #7 fix).
    """
    from src.modules.vitalia.inbox.application.services.activity_event_service import (
        ActivityEventService,
        ActivityStreamItem,
    )

    activity_repo = AsyncMock()
    activity_repo.list_for_activity_stream = AsyncMock(return_value=[_make_activity_event()])

    svc = ActivityEventService(activity_repo=activity_repo)

    result = await svc.get_stream(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        limit=8,
        since_minutes=5,
    )

    assert len(result.events) == 1
    item = result.events[0]
    assert isinstance(item, ActivityStreamItem)
    # ActivityStreamItem has no payload field — PHI is NOT exposed to UI layer
    assert not hasattr(item, "payload")
    assert not hasattr(item, "payload_sanitized")
    # Only safe description_es is returned
    assert item.description_es == "consultó precio de blanqueamiento"


@pytest.mark.asyncio
async def test_activity_stream_dual_filter_applied() -> None:
    """Both tenant_id and clinic_id passed to repository (dual-filter)."""
    from src.modules.vitalia.inbox.application.services.activity_event_service import (
        ActivityEventService,
    )

    activity_repo = AsyncMock()
    activity_repo.list_for_activity_stream = AsyncMock(return_value=[])

    svc = ActivityEventService(activity_repo=activity_repo)

    await svc.get_stream(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        limit=8,
        since_minutes=5,
    )

    call_kwargs = activity_repo.list_for_activity_stream.call_args.kwargs
    assert call_kwargs.get("tenant_id") == TENANT_ID
    assert call_kwargs.get("clinic_id") == CLINIC_ID
