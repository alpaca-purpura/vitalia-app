# story-origin: vitalia-fase2-adrian-canal-inbound T-AG-GAP23
"""Brand integration — inbound mode-resolver + draft sink + activity subscriber.

Wires vitalia's HonorModeBridge into the engine inbound seam (GAP-2) and a brand
subscriber that writes vitalia_activity_events from AgentTurnCompletedEvent (GAP-3).

These tests drive the brand adapters in isolation with duck-typed ports (no real
DB / engine), proving:
  - resolver maps HonorModeDecision → engine InboundMode (decide/consulta/pausa)
  - draft sink writes a sanitized, dual-filtered activity row (consulta → draft)
  - activity subscriber writes a generic, sanitized, dual-filtered activity row
    from an outbox-reconstructed DomainEvent (IDs + stage only)
  - dual filter (tenant_id + clinic_id) is authoritative from the conversation
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from luana_core_sales_agent.application.orchestrator.inbound_mode_seam import InboundMode

from src.modules.vitalia.sales_agent.application.services.inbound_seam_adapter import (
    VitaliaInboundSeamAdapter,
    build_agent_turn_completed_handler,
)

TENANT_ID = UUID("44444444-4444-4444-4444-444444444444")
CLINIC_ID = UUID("33333333-3333-3333-3333-333333333333")
LEAD_ID = UUID("55555555-5555-5555-5555-555555555555")
CONV_ID = UUID("66666666-6666-6666-6666-666666666666")


def _conv(*, handler_mode: str = "ai", proposal_required: bool = False, pause_until=None):
    return SimpleNamespace(
        id=CONV_ID,
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        lead_id=LEAD_ID,
        handler_mode=handler_mode,
        proposal_required=proposal_required,
        pause_until=pause_until,
    )


# ── mode resolver ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resolve_mode_decide() -> None:
    adapter = VitaliaInboundSeamAdapter(
        conv_loader=AsyncMock(return_value=_conv(handler_mode="ai", proposal_required=False)),
        activity_writer=AsyncMock(),
    )
    mode = await adapter.resolve_mode_async(tenant_id=TENANT_ID, lead_id=LEAD_ID)
    assert mode is InboundMode.DECIDE


@pytest.mark.asyncio
async def test_resolve_mode_consulta() -> None:
    adapter = VitaliaInboundSeamAdapter(
        conv_loader=AsyncMock(return_value=_conv(handler_mode="ai", proposal_required=True)),
        activity_writer=AsyncMock(),
    )
    mode = await adapter.resolve_mode_async(tenant_id=TENANT_ID, lead_id=LEAD_ID)
    assert mode is InboundMode.CONSULTA


@pytest.mark.asyncio
async def test_resolve_mode_pausa_when_human() -> None:
    adapter = VitaliaInboundSeamAdapter(
        conv_loader=AsyncMock(return_value=_conv(handler_mode="human")),
        activity_writer=AsyncMock(),
    )
    mode = await adapter.resolve_mode_async(tenant_id=TENANT_ID, lead_id=LEAD_ID)
    assert mode is InboundMode.PAUSA


@pytest.mark.asyncio
async def test_resolve_mode_pausa_when_future_pause() -> None:
    future = datetime.now(timezone.utc) + timedelta(minutes=30)
    adapter = VitaliaInboundSeamAdapter(
        conv_loader=AsyncMock(return_value=_conv(pause_until=future)),
        activity_writer=AsyncMock(),
    )
    mode = await adapter.resolve_mode_async(tenant_id=TENANT_ID, lead_id=LEAD_ID)
    assert mode is InboundMode.PAUSA


@pytest.mark.asyncio
async def test_resolve_mode_decide_when_no_conversation() -> None:
    """No conversation found → DECIDE (engine default, never blocks)."""
    adapter = VitaliaInboundSeamAdapter(
        conv_loader=AsyncMock(return_value=None),
        activity_writer=AsyncMock(),
    )
    mode = await adapter.resolve_mode_async(tenant_id=TENANT_ID, lead_id=LEAD_ID)
    assert mode is InboundMode.DECIDE


# ── draft sink (consulta → draft activity row, dual filter, sanitized) ───


@pytest.mark.asyncio
async def test_draft_sink_writes_dual_filtered_activity() -> None:
    writes: list = []

    async def _activity_writer(**kwargs: object) -> None:
        writes.append(kwargs)

    adapter = VitaliaInboundSeamAdapter(
        conv_loader=AsyncMock(return_value=_conv(proposal_required=True)),
        activity_writer=_activity_writer,
    )
    await adapter.draft_sink_async(
        tenant_id=TENANT_ID,
        lead_id=LEAD_ID,
        draft_text="Hola, te confirmo el turno el martes.",  # the suppressed reply
        result={"current_state": "closing"},
    )

    assert len(writes) == 1
    row = writes[0]
    assert row["tenant_id"] == TENANT_ID
    assert row["clinic_id"] == CLINIC_ID  # dual filter from the conversation
    assert row["conversation_id"] == CONV_ID
    assert row["event_kind"] == "adrian_draft_pending"
    assert row["agent_id"] == "adrian"
    # description_es is generic — NO raw draft text / PHI leaked
    assert "martes" not in row["description_es"]
    assert "turno" not in row["description_es"].lower()  # no raw body
    # payload is sanitized + carries NO message body
    assert "draft_text" not in row["payload_sanitized"]
    assert "content" not in row["payload_sanitized"]


@pytest.mark.asyncio
async def test_draft_sink_no_conversation_is_noop() -> None:
    writes: list = []

    async def _activity_writer(**kwargs: object) -> None:
        writes.append(kwargs)

    adapter = VitaliaInboundSeamAdapter(
        conv_loader=AsyncMock(return_value=None),
        activity_writer=_activity_writer,
    )
    # No conversation → cannot resolve clinic_id → skip write (never crash).
    await adapter.draft_sink_async(
        tenant_id=TENANT_ID,
        lead_id=LEAD_ID,
        draft_text="x",
        result={},
    )
    assert writes == []


# ── activity subscriber (AgentTurnCompletedEvent → activity row) ─────────


@pytest.mark.asyncio
async def test_subscriber_writes_activity_from_event() -> None:
    writes: list = []

    async def _activity_writer(**kwargs: object) -> None:
        writes.append(kwargs)

    adapter = VitaliaInboundSeamAdapter(
        conv_loader=AsyncMock(return_value=_conv()),
        activity_writer=_activity_writer,
    )

    # Outbox reconstructs a generic DomainEvent (.event_name/.tenant_id/.payload).
    event = SimpleNamespace(
        event_name="agent_turn_completed",
        tenant_id=TENANT_ID,
        payload={
            "lead_id": str(LEAD_ID),
            "conversation_id": str(CONV_ID),
            "role": "assistant",
            "funnel_stage": "discovery",
        },
    )

    await adapter.on_agent_turn_completed_async(event)

    assert len(writes) == 1
    row = writes[0]
    assert row["tenant_id"] == TENANT_ID
    assert row["clinic_id"] == CLINIC_ID
    assert row["conversation_id"] == CONV_ID
    assert row["event_kind"] == "adrian_turn"
    assert row["agent_id"] == "adrian"
    # payload carries IDs + stage ONLY — never a message body / PHI
    assert row["payload_sanitized"].get("funnel_stage") == "discovery"
    assert "content" not in row["payload_sanitized"]
    assert "text" not in row["payload_sanitized"]


@pytest.mark.asyncio
async def test_subscriber_other_event_ignored() -> None:
    writes: list = []

    async def _activity_writer(**kwargs: object) -> None:
        writes.append(kwargs)

    adapter = VitaliaInboundSeamAdapter(
        conv_loader=AsyncMock(return_value=_conv()),
        activity_writer=_activity_writer,
    )
    other = SimpleNamespace(event_name="lead_captured", tenant_id=TENANT_ID, payload={})
    await adapter.on_agent_turn_completed_async(other)
    assert writes == []


def test_build_handler_returns_callable() -> None:
    """The sync handler factory returns a callable (registered via EventBus.subscribe)."""
    adapter = VitaliaInboundSeamAdapter(conv_loader=AsyncMock(), activity_writer=AsyncMock())
    handler = build_agent_turn_completed_handler(adapter)
    assert callable(handler)
