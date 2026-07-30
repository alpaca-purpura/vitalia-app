# cap: sales_agent.adrian-override-context
# story-origin: vitalia-fase2-adrian-embudo
"""Tests for OverrideContextWire — RN-4.1 override-context wire (T-AG-1, SC-1b).

TDD order: RED first, then GREEN in
`sales_agent/application/services/override_context_wire.py`.

The wire is a brand-local thin subscriber of the `lead_stage_overridden` domain
event (emitted by crm FunnelService.transition_stage on a manual override with
reason). It does TWO things, both via injected ports (no direct import of crm or
the engine sync repo):

  1. Persists `override_context` into the EXISTING nullable `metadata_info` JSONB
     of the active `agent_state_checkpoints` row — so the agent's NEXT turn reads
     it (no schema change, no column, no checkpoint reset).
  2. Settles the handover (🙋 humano → 🤖 Adrián) as a NON-PHI activity in the
     lead commercial timeline (LeadActivity), so the Historial shows the takeover.

Covers:
  AE-1 / SC-1b: override → override_context persisted to next-turn read surface
                + handover activity recorded; agent NOT reinitialized.
  RN-4.1 negative: payload without reason → skipped (no crash).
  tenant-isolation: payload without tenant_id → ValueError.
  graceful-degradation: a port failure is best-effort (origin turn never breaks).
  anti-duplication / DDD: module source imports no crm/engine concretions.
"""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.vitalia.sales_agent.application.services.override_context_wire import (
    LeadStageOverriddenEvent,
    OverrideContextWire,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
LEAD_ID = uuid4()
USER_ID = uuid4()


def _payload(
    *,
    reason: str | None = "El paciente confirmó presupuesto por teléfono.",
    tenant_id: str | None = None,
    lead_id: str | None = None,
    from_stage: str = "interesado",
    to_stage: str = "calificando",
) -> dict:
    """Build a lead_stage_overridden outbox payload (shape from T-BE-2)."""
    return {
        "event_type": "lead_stage_overridden",
        "tenant_id": tenant_id if tenant_id is not None else str(TENANT_ID),
        "lead_id": lead_id if lead_id is not None else str(LEAD_ID),
        "from_stage": from_stage,
        "to_stage": to_stage,
        "reason": reason,
        "actor_user_id": str(USER_ID),
        "version_after": 2,
    }


def _make_wire() -> tuple[OverrideContextWire, AsyncMock, AsyncMock]:
    """Construct a wire with AsyncMock ports. Returns (wire, metadata_port, activity_port)."""
    metadata_port = AsyncMock()
    metadata_port.set_override_context = AsyncMock(return_value=True)
    activity_port = AsyncMock()
    activity_port.record_handover = AsyncMock(return_value=None)
    wire = OverrideContextWire(metadata_port=metadata_port, activity_port=activity_port)
    return wire, metadata_port, activity_port


# ---------------------------------------------------------------------------
# AE-1 / SC-1b — happy path: context persisted to next-turn read surface
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_override_persists_context_to_next_turn_read_surface() -> None:
    """AE-1/SC-1b: valid manual override → override_context written once.

    The override_context carries the human's reason + stage delta so the agent's
    next turn can read it from `metadata_info` (no re-prompt of answered questions).
    """
    wire, metadata_port, _ = _make_wire()

    await wire.handle_lead_stage_overridden(_payload())

    metadata_port.set_override_context.assert_awaited_once()
    kwargs = metadata_port.set_override_context.await_args.kwargs
    assert kwargs["tenant_id"] == TENANT_ID
    assert kwargs["lead_id"] == LEAD_ID
    ctx = kwargs["override_context"]
    # reason is the load-bearing field — it's what the next turn reads.
    assert ctx["reason"] == "El paciente confirmó presupuesto por teléfono."
    assert ctx["from_stage"] == "interesado"
    assert ctx["to_stage"] == "calificando"
    assert ctx["source"] == "manual_override"
    assert "occurred_at" in ctx  # ISO timestamp for the next turn to dedupe/expire


# ---------------------------------------------------------------------------
# SC-1b — handover activity 🙋 humano → 🤖 Adrián
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_override_records_handover_activity_human_to_agent() -> None:
    """SC-1b: the takeover is settled in the lead commercial timeline (NON-PHI)."""
    wire, _, activity_port = _make_wire()

    await wire.handle_lead_stage_overridden(_payload())

    activity_port.record_handover.assert_awaited_once()
    kwargs = activity_port.record_handover.await_args.kwargs
    assert kwargs["tenant_id"] == TENANT_ID
    assert kwargs["lead_id"] == LEAD_ID
    desc = kwargs["description_es"]
    # 🙋 → 🤖 handover, Spanish neutro, references Adrián, includes reason snippet.
    assert "🙋" in desc and "🤖" in desc
    assert "Adrián" in desc
    assert "presupuesto" in desc  # reason snippet surfaced for the Historial


# ---------------------------------------------------------------------------
# SC-1b — "NO re-inicia el agente"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_override_context_does_not_reinitialize_agent() -> None:
    """SC-1b: the wire only WRITES context; it never resets the checkpoint.

    The metadata port surface is intentionally narrow: a single
    `set_override_context`. There is no deactivate / recreate / reset-stage call,
    so Adrián resumes from his accumulated state, not from scratch.
    """
    wire, metadata_port, _ = _make_wire()

    await wire.handle_lead_stage_overridden(_payload())

    # Only the override-context setter may be touched on the metadata port.
    # mock_calls entries are (name, args, kwargs); collect the leaf attr names.
    called = {call[0].split(".")[-1] for call in metadata_port.mock_calls if call[0]}
    forbidden = {"deactivate", "save_checkpoint", "reset", "create", "set_current_stage"}
    assert not (called & forbidden), f"wire must not reset the agent: {called & forbidden}"


# ---------------------------------------------------------------------------
# RN-4.1 negative — payload without reason is skipped
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_payload_missing_reason_is_skipped() -> None:
    """RN-4.1 negative: no reason → nothing to inject; skip both ports, no crash."""
    wire, metadata_port, activity_port = _make_wire()

    await wire.handle_lead_stage_overridden(_payload(reason=None))

    metadata_port.set_override_context.assert_not_awaited()
    activity_port.record_handover.assert_not_awaited()


@pytest.mark.asyncio
async def test_payload_blank_reason_is_skipped() -> None:
    """RN-4.1 negative: whitespace-only reason is treated as no reason."""
    wire, metadata_port, activity_port = _make_wire()

    await wire.handle_lead_stage_overridden(_payload(reason="   "))

    metadata_port.set_override_context.assert_not_awaited()
    activity_port.record_handover.assert_not_awaited()


# ---------------------------------------------------------------------------
# tenant-isolation — missing tenant_id raises
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_payload_missing_tenant_id_raises() -> None:
    """tenant-isolation: a payload without tenant_id is rejected (no cross-tenant write)."""
    wire, _, _ = _make_wire()
    bad = _payload()
    del bad["tenant_id"]

    with pytest.raises((ValueError, KeyError)):
        await wire.handle_lead_stage_overridden(bad)


# ---------------------------------------------------------------------------
# graceful-degradation — a port failure is best-effort
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_metadata_port_failure_is_best_effort() -> None:
    """The origin override turn already committed — a wire failure must NOT propagate.

    If the metadata write raises (e.g. no active checkpoint yet because the agent
    has never run on this lead), the wire still records the handover and returns
    cleanly.
    """
    wire, metadata_port, activity_port = _make_wire()
    metadata_port.set_override_context.side_effect = RuntimeError("no active checkpoint")

    # Must not raise.
    await wire.handle_lead_stage_overridden(_payload())

    # Handover still recorded despite the metadata write failing.
    activity_port.record_handover.assert_awaited_once()


@pytest.mark.asyncio
async def test_activity_port_failure_is_best_effort() -> None:
    """A failure recording the handover must not propagate either."""
    wire, metadata_port, activity_port = _make_wire()
    activity_port.record_handover.side_effect = RuntimeError("db down")

    await wire.handle_lead_stage_overridden(_payload())

    # Context still attempted on the metadata port.
    metadata_port.set_override_context.assert_awaited_once()


# ---------------------------------------------------------------------------
# event DTO parsing
# ---------------------------------------------------------------------------


def test_event_dto_parses_outbox_payload() -> None:
    """LeadStageOverriddenEvent maps the outbox payload (UUIDs from str)."""
    evt = LeadStageOverriddenEvent.model_validate(_payload())
    assert evt.tenant_id == TENANT_ID
    assert evt.lead_id == LEAD_ID
    assert evt.reason == "El paciente confirmó presupuesto por teléfono."
    assert evt.event_type == "lead_stage_overridden"


# ---------------------------------------------------------------------------
# anti-duplication / DDD — no crm/engine concretion imports
# ---------------------------------------------------------------------------


def test_wire_does_not_import_crm_or_engine_concretions() -> None:
    """DDD boundary + anti-dup: sales_agent wire must not import crm or engine repos.

    Cross-module coupling is via the domain event payload + injected ports only.
    """
    from src.modules.vitalia.sales_agent.application.services import override_context_wire

    source = inspect.getsource(override_context_wire)
    assert "from src.modules.vitalia.crm" not in source, "wire must not import crm (cross-module ban)"
    assert "import src.modules.vitalia.crm" not in source
    # No direct dependency on the engine sync state repository / checkpoint model.
    assert "AgentStateCheckpointModel" not in source
    assert "StateRepository" not in source
