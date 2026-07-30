# story-origin: vitalia-fase2-adrian-canal-inbound T-AG-GAP23
"""Anti-orphan wiring test — wire_inbound_mode_seam registers into the engine seam.

Proves the brand composition root actually CONSUMES the engine inbound seam:
after wire_inbound_mode_seam(), the engine resolves CONSULTA/DECIDE via vitalia's
HonorModeBridge and exposes the brand draft sink + activity subscriber. Without
this, the resolver/sink/subscriber would be islands (CONN — anti-orphan-integration).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from luana_core_platform.domain.events import EventBus as LegacyEventBus
from luana_core_sales_agent.application.orchestrator.inbound_mode_seam import (
    InboundMode,
    get_draft_sink,
    reset_inbound_seam,
    resolve_inbound_mode,
)

from src.modules.vitalia.sales_agent import composition

TENANT_ID = UUID("44444444-4444-4444-4444-444444444444")
CLINIC_ID = UUID("33333333-3333-3333-3333-333333333333")
LEAD_ID = UUID("55555555-5555-5555-5555-555555555555")
CONV_ID = UUID("66666666-6666-6666-6666-666666666666")


@pytest.fixture(autouse=True)
def _isolate() -> None:
    reset_inbound_seam()
    LegacyEventBus.clear()
    yield
    reset_inbound_seam()
    LegacyEventBus.clear()


@pytest.mark.asyncio
async def test_wire_registers_resolver_into_engine_seam(monkeypatch: pytest.MonkeyPatch) -> None:
    """After wiring, the engine resolves CONSULTA from a proposal_required conversation."""
    conv = SimpleNamespace(
        id=CONV_ID,
        clinic_id=CLINIC_ID,
        lead_id=LEAD_ID,
        handler_mode="ai",
        proposal_required=True,
        pause_until=None,
    )
    monkeypatch.setattr(
        composition,
        "_load_open_conversation",
        AsyncMock(return_value=conv),
    )

    composition.wire_inbound_mode_seam()

    # Engine resolves through the brand-registered resolver (not the default DECIDE).
    mode = await resolve_inbound_mode(tenant_id=TENANT_ID, lead_id=LEAD_ID, checkpoint=None)
    assert mode is InboundMode.CONSULTA

    # The draft sink is registered (CONSULTA path has a sink to call).
    assert get_draft_sink() is not None

    # The activity subscriber is registered on the legacy bus (outbox re-dispatches here).
    assert "agent_turn_completed" in LegacyEventBus._handlers
    assert len(LegacyEventBus._handlers["agent_turn_completed"]) == 1


@pytest.mark.asyncio
async def test_wire_resolver_decide_when_no_conversation(monkeypatch: pytest.MonkeyPatch) -> None:
    """No open conversation → engine resolves DECIDE (never blocks the turn)."""
    monkeypatch.setattr(
        composition,
        "_load_open_conversation",
        AsyncMock(return_value=None),
    )
    composition.wire_inbound_mode_seam()
    mode = await resolve_inbound_mode(tenant_id=TENANT_ID, lead_id=LEAD_ID, checkpoint=None)
    assert mode is InboundMode.DECIDE
