"""RED→GREEN — AgentTurnCompletedEvent emit seam (GAP-3).

Lightweight per-turn domain event emitted via the EXISTING outbox EventBus
(``luana_core_events.outbox.adapter_bus``, already used in ``audit_emitter.py``).
Payload = IDs + funnel_stage ONLY. ZERO PHI, ZERO message bodies (HIPAA-lite).

# [SALES-AGENT-AGENT-TURN-COMPLETED-GAP3] -> docs/promotion-protocol/proposals/
# 2026-06-23-sales-agent-inbound-mode-activity-seams.md
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from luana_core_platform.domain.events import AgentTurnCompletedEvent

from luana_core_sales_agent.application.orchestrator.audit_emitter import AuditEmitter

TENANT_ID = UUID("44444444-4444-4444-4444-444444444444")
LEAD_ID = UUID("55555555-5555-5555-5555-555555555555")
CONV_ID = UUID("66666666-6666-6666-6666-666666666666")

# Fields that would constitute PHI / message bodies — must NEVER appear in the
# event payload (HIPAA-lite: the inbox is nourished by IDs + stage, not content).
_FORBIDDEN_PAYLOAD_KEYS = frozenset(
    {
        "content",
        "text",
        "message",
        "bot_text",
        "body",
        "patient_name",
        "name",
        "email",
        "phone",
        "diagnosis",
        "messages",
    }
)


def test_event_payload_is_ids_and_stage_only() -> None:
    """Payload keys = tenant/lead/conversation/role/funnel_stage ONLY. No PHI/bodies."""
    event = AgentTurnCompletedEvent.create(
        tenant_id=TENANT_ID,
        lead_id=LEAD_ID,
        conversation_id=CONV_ID,
        role="assistant",
        funnel_stage="closing",
    )
    assert event.event_name == "agent_turn_completed"
    assert event.tenant_id == TENANT_ID

    payload = event.payload
    assert payload["lead_id"] == str(LEAD_ID)
    assert payload["conversation_id"] == str(CONV_ID)
    assert payload["role"] == "assistant"
    assert payload["funnel_stage"] == "closing"

    # ZERO PHI / message bodies in the payload (the contract bar).
    assert _FORBIDDEN_PAYLOAD_KEYS.isdisjoint(payload.keys()), (
        f"AgentTurnCompletedEvent payload leaked a forbidden key: "
        f"{set(payload.keys()) & _FORBIDDEN_PAYLOAD_KEYS}"
    )
    # And no value looks like a free-text body (all values are IDs/short tokens).
    for key, val in payload.items():
        assert isinstance(val, (str, type(None))), (
            f"{key} must be str|None, got {type(val)}"
        )


def test_event_conversation_id_optional() -> None:
    """conversation_id is optional (engine may not always resolve it) → None payload."""
    event = AgentTurnCompletedEvent.create(
        tenant_id=TENANT_ID,
        lead_id=LEAD_ID,
        conversation_id=None,
        role="assistant",
        funnel_stage="rapport",
    )
    assert event.payload["conversation_id"] is None


@pytest.mark.asyncio
async def test_emit_turn_completed_publishes_via_outbox(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AuditEmitter.emit_turn_completed publishes AgentTurnCompletedEvent via adapter_bus."""
    published: list = []

    def _capture_publish(event: object, session: object = None, **_: object) -> None:
        published.append((event, session))

    monkeypatch.setattr(
        "luana_core_sales_agent.application.orchestrator.audit_emitter.EventBus.publish",
        _capture_publish,
    )

    db = MagicMock()
    user = SimpleNamespace(id=LEAD_ID)
    result = {"current_state": "discovery", "lead_score": 30}

    await AuditEmitter.emit_turn_completed(
        TENANT_ID,
        user,
        result,
        conversation_id=CONV_ID,
        db=db,
    )

    assert len(published) == 1
    event, session = published[0]
    assert isinstance(event, AgentTurnCompletedEvent)
    assert event.payload["funnel_stage"] == "discovery"
    assert event.payload["lead_id"] == str(LEAD_ID)
    assert session is db  # deferred dispatch after the caller's commit


@pytest.mark.asyncio
async def test_emit_turn_completed_best_effort_swallows_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A publish failure must NOT propagate (observability never breaks the turn)."""

    def _boom(*_a: object, **_k: object) -> None:
        raise RuntimeError("outbox down")

    monkeypatch.setattr(
        "luana_core_sales_agent.application.orchestrator.audit_emitter.EventBus.publish",
        _boom,
    )
    # Must not raise.
    await AuditEmitter.emit_turn_completed(
        TENANT_ID,
        SimpleNamespace(id=LEAD_ID),
        {"current_state": "rapport"},
        conversation_id=None,
        db=MagicMock(),
    )
