"""RED→GREEN — inbound mode-resolver + draft_only seam (GAP-2).

Engine seam (additive, backward-compatible). Default (no resolver registered) =
EXACT current behavior. A brand registers a mode-resolver (DECIDE|CONSULTA|PAUSA)
+ a draft sink; on CONSULTA the engine suppresses outbound and hands the draft
to the brand sink.

Hexagonal: the engine imports NOTHING brand. The resolver/sink are module-level
injectable hooks (default None).

# [SALES-AGENT-INBOUND-MODE-SEAM-GAP2] -> docs/promotion-protocol/proposals/
# 2026-06-23-sales-agent-inbound-mode-activity-seams.md
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from luana_core_platform.domain.messages import IncomingMessage

from luana_core_sales_agent.application.orchestrator.conversation_pipeline import (
    ConversationPipeline,
)
from luana_core_sales_agent.application.orchestrator.inbound_mode_seam import (
    InboundMode,
    get_draft_sink,
    reset_inbound_seam,
    resolve_inbound_mode,
    set_draft_sink,
    set_mode_resolver,
)

TENANT_ID = UUID("44444444-4444-4444-4444-444444444444")
LEAD_ID = UUID("55555555-5555-5555-5555-555555555555")


@pytest.fixture(autouse=True)
def _isolate_seam() -> None:
    """Each test starts + ends with a clean (default-off) seam registry."""
    reset_inbound_seam()
    yield
    reset_inbound_seam()


# ── resolve_inbound_mode (registry, async) ──────────────────────────────


def _async_returns(value: InboundMode):
    async def _resolver(**_: object) -> InboundMode:
        return value

    return _resolver


@pytest.mark.asyncio
async def test_default_resolver_returns_decide() -> None:
    """No resolver registered → DECIDE (engine default = current behavior)."""
    mode = await resolve_inbound_mode(
        tenant_id=TENANT_ID, lead_id=LEAD_ID, checkpoint=None
    )
    assert mode is InboundMode.DECIDE


@pytest.mark.asyncio
async def test_registered_resolver_consulta() -> None:
    set_mode_resolver(_async_returns(InboundMode.CONSULTA))
    mode = await resolve_inbound_mode(
        tenant_id=TENANT_ID, lead_id=LEAD_ID, checkpoint=None
    )
    assert mode is InboundMode.CONSULTA


@pytest.mark.asyncio
async def test_registered_resolver_pausa() -> None:
    set_mode_resolver(_async_returns(InboundMode.PAUSA))
    mode = await resolve_inbound_mode(
        tenant_id=TENANT_ID, lead_id=LEAD_ID, checkpoint=None
    )
    assert mode is InboundMode.PAUSA


@pytest.mark.asyncio
async def test_resolver_exception_degrades_to_decide() -> None:
    """A raising resolver must degrade to DECIDE — never break the turn."""

    async def _boom(**_: object) -> InboundMode:
        raise RuntimeError("resolver down")

    set_mode_resolver(_boom)
    mode = await resolve_inbound_mode(
        tenant_id=TENANT_ID, lead_id=LEAD_ID, checkpoint=None
    )
    assert mode is InboundMode.DECIDE


def test_draft_sink_default_none() -> None:
    assert get_draft_sink() is None


def test_draft_sink_registration() -> None:
    sink = AsyncMock()
    set_draft_sink(sink)
    assert get_draft_sink() is sink


# ── deliver_response — DECIDE path = EXACT current behavior ──────────────


@pytest.mark.asyncio
async def test_deliver_response_decide_sends_normally(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No resolver (default DECIDE) → OutputManager.process_response IS called."""
    monkeypatch.setattr(
        "luana_core_sales_agent.application.orchestrator.conversation_pipeline.ConversationPipeline.sanitize_text",
        AsyncMock(return_value="respuesta"),
    )
    output_calls: list = []

    async def _capture_output(
        uid: str, text: str, _adapter: object, channel_type: str
    ) -> None:
        output_calls.append((uid, text, channel_type))

    monkeypatch.setattr(
        "luana_core_sales_agent.infrastructure.external.output_manager.OutputManager.process_response",
        _capture_output,
    )
    monkeypatch.setattr(
        "luana_core_sales_agent.application.orchestrator.audit_emitter.AuditEmitter.emit_assistant_message",
        staticmethod(AsyncMock()),
    )

    audit_repo = SimpleNamespace(log_message=lambda **_: None)
    incoming = IncomingMessage(
        user_id="tg_u", text="hola", channel_type="telegram", metadata={}
    )
    result = {
        "messages": [{"role": "assistant", "content": "respuesta"}],
        "current_state": "discovery",
    }

    await ConversationPipeline.deliver_response(
        SimpleNamespace(),
        incoming,
        result,
        audit_repo,
        SimpleNamespace(id=LEAD_ID),
        "telegram",
        TENANT_ID,
        lead_id=LEAD_ID,
    )

    assert output_calls == [("tg_u", "respuesta", "telegram")]


# ── deliver_response — CONSULTA path = draft, ZERO outbound ──────────────


@pytest.mark.asyncio
async def test_deliver_response_consulta_suppresses_outbound_and_drafts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Resolver=CONSULTA → 0 OutputManager calls + draft sink called + WS fired."""
    monkeypatch.setattr(
        "luana_core_sales_agent.application.orchestrator.conversation_pipeline.ConversationPipeline.sanitize_text",
        AsyncMock(return_value="borrador adrián"),
    )
    output_calls: list = []

    async def _capture_output(*a: object, **k: object) -> None:
        output_calls.append((a, k))

    monkeypatch.setattr(
        "luana_core_sales_agent.infrastructure.external.output_manager.OutputManager.process_response",
        _capture_output,
    )
    ws_calls: list = []

    async def _capture_ws(
        _tid: object, _user: object, _text: str, _result: dict
    ) -> None:
        ws_calls.append(True)

    monkeypatch.setattr(
        "luana_core_sales_agent.application.orchestrator.audit_emitter.AuditEmitter.emit_assistant_message",
        staticmethod(_capture_ws),
    )

    draft_calls: list = []

    async def _draft_sink(
        *, tenant_id: object, lead_id: object, draft_text: str, result: dict
    ) -> None:
        draft_calls.append((tenant_id, lead_id, draft_text))

    set_mode_resolver(_async_returns(InboundMode.CONSULTA))
    set_draft_sink(_draft_sink)

    audit_repo = SimpleNamespace(log_message=lambda **_: None)
    incoming = IncomingMessage(
        user_id="tg_u", text="hola", channel_type="telegram", metadata={}
    )
    result = {
        "messages": [{"role": "assistant", "content": "borrador adrián"}],
        "current_state": "closing",
    }

    await ConversationPipeline.deliver_response(
        SimpleNamespace(),
        incoming,
        result,
        audit_repo,
        SimpleNamespace(id=LEAD_ID),
        "telegram",
        TENANT_ID,
        lead_id=LEAD_ID,
    )

    # CONSULTA → graph already ran (text exists) but NOTHING sent to the channel
    assert output_calls == []
    # draft handed to the brand sink with the bot text
    assert draft_calls == [(TENANT_ID, LEAD_ID, "borrador adrián")]
    # inbox still notified (glass-box)
    assert ws_calls == [True]


@pytest.mark.asyncio
async def test_deliver_response_consulta_without_sink_still_suppresses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CONSULTA but no draft sink registered → still 0 outbound (no crash)."""
    monkeypatch.setattr(
        "luana_core_sales_agent.application.orchestrator.conversation_pipeline.ConversationPipeline.sanitize_text",
        AsyncMock(return_value="texto"),
    )
    output_calls: list = []
    monkeypatch.setattr(
        "luana_core_sales_agent.infrastructure.external.output_manager.OutputManager.process_response",
        AsyncMock(side_effect=lambda *a, **k: output_calls.append(1)),
    )
    monkeypatch.setattr(
        "luana_core_sales_agent.application.orchestrator.audit_emitter.AuditEmitter.emit_assistant_message",
        staticmethod(AsyncMock()),
    )
    set_mode_resolver(_async_returns(InboundMode.CONSULTA))

    audit_repo = SimpleNamespace(log_message=lambda **_: None)
    incoming = IncomingMessage(
        user_id="tg_u", text="hola", channel_type="telegram", metadata={}
    )
    result = {"messages": [{"role": "assistant", "content": "texto"}]}

    await ConversationPipeline.deliver_response(
        SimpleNamespace(),
        incoming,
        result,
        audit_repo,
        SimpleNamespace(id=LEAD_ID),
        "telegram",
        TENANT_ID,
        lead_id=LEAD_ID,
    )
    assert output_calls == []
