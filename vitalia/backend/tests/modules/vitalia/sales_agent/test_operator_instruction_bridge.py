# cap: sales_agent.honor-mode-bridge
# story-origin: vitalia-fase2-adrian-canal-inbound T-AG-1
"""Tests for OperatorInstructionBridge — agentic turn-prep wiring (T-AG-1, SC-8).

TDD order: RED first, then GREEN in
``sales_agent/application/services/operator_instruction_bridge.py``.

The integration gap this closes (NO-NEW-LAYER audit, T-AG-1 impl-log):
  - T-BE-3 persists the operator instruction PERSISTENTLY to
    ``agent_state_checkpoints.metadata_info["operator_instructions"]`` (RN-13:
    steers ALL turns until edited/cleared).
  - The engine ``conversation_pipeline.prepare_messages_and_intent`` injects
    ``[INSTRUCCION DEL OPERADOR]`` from ``checkpoint.resume_objective`` (a
    one-shot Text column it clears after reading) — it does NOT read the
    persistent ``metadata_info`` key.
  - This brand-side bridge is the missing link: before each turn it copies the
    persistent instruction into ``resume_objective`` (the engine's volatile
    injection seam), so the engine injects ``[INSTRUCCION DEL OPERADOR]`` every
    turn. Persistent because the source key in ``metadata_info`` is never
    cleared. ZERO engine edit; the bridge consumes the engine's existing read
    surface via an injected Protocol port (like ``override_context_wire``).

Covers (SC-8 / RN-13 / AC-13):
  - happy: persistent instruction present → applied to the turn's volatile seam.
  - no-op: no persistent instruction → nothing applied (no crash).
  - persistence semantics: applying does NOT clear the persistent key (steers
    every subsequent turn — RN-13 "no one-shot").
  - tenant-isolation: tenant_id is propagated to the port (dual-filter guard).
  - graceful-degradation: a port failure is best-effort (turn never breaks).
  - DDD / anti-dup: module source imports no engine/crm concretions.
"""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.vitalia.sales_agent.application.services.operator_instruction_bridge import (
    OperatorInstructionBridge,
)

TENANT_ID = uuid4()
LEAD_ID = uuid4()


def _make_bridge(*, applied: bool = True) -> tuple[OperatorInstructionBridge, AsyncMock]:
    """Construct a bridge with an AsyncMock port. Returns (bridge, port)."""
    port = AsyncMock()
    port.apply_persistent_instruction_to_turn = AsyncMock(return_value=applied)
    bridge = OperatorInstructionBridge(checkpoint_bridge_port=port)
    return bridge, port


# ---------------------------------------------------------------------------
# SC-8 happy — persistent instruction is applied to the turn's volatile seam
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_for_turn_copies_persistent_instruction_to_resume_objective() -> None:
    """SC-8/RN-13: a present persistent instruction is applied before the turn.

    The bridge delegates to the port, which copies
    metadata_info['operator_instructions'] → resume_objective (engine seam).
    Returns True when an active checkpoint carried an instruction.
    """
    bridge, port = _make_bridge(applied=True)

    applied = await bridge.apply_for_turn(tenant_id=TENANT_ID, lead_id=LEAD_ID)

    assert applied is True
    port.apply_persistent_instruction_to_turn.assert_awaited_once()
    kwargs = port.apply_persistent_instruction_to_turn.await_args.kwargs
    assert kwargs["tenant_id"] == TENANT_ID
    assert kwargs["lead_id"] == LEAD_ID


# ---------------------------------------------------------------------------
# no-op — no persistent instruction → nothing to apply
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_for_turn_no_instruction_is_noop() -> None:
    """No active instruction (port returns False) → bridge returns False, no crash."""
    bridge, port = _make_bridge(applied=False)

    applied = await bridge.apply_for_turn(tenant_id=TENANT_ID, lead_id=LEAD_ID)

    assert applied is False
    port.apply_persistent_instruction_to_turn.assert_awaited_once()


# ---------------------------------------------------------------------------
# RN-13 persistence — applying must NOT clear the persistent source key
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_for_turn_does_not_clear_persistent_key() -> None:
    """RN-13: the instruction steers EVERY subsequent turn (not one-shot).

    The bridge's port surface is intentionally narrow — a single
    ``apply_persistent_instruction_to_turn``. There is no clear/delete/reset call
    on the persistent ``metadata_info`` key, so the instruction persists across
    turns until the operator edits/clears it via the set-instruction endpoint.
    """
    bridge, port = _make_bridge(applied=True)

    await bridge.apply_for_turn(tenant_id=TENANT_ID, lead_id=LEAD_ID)
    await bridge.apply_for_turn(tenant_id=TENANT_ID, lead_id=LEAD_ID)

    # Re-application on the next turn is allowed (persistent) — the bridge never
    # exposes a clear/delete operation on the persistent key.
    called = {call[0].split(".")[-1] for call in port.mock_calls if call[0]}
    forbidden = {"clear_operator_instruction", "delete", "reset", "deactivate"}
    assert not (called & forbidden), f"bridge must not clear the persistent key: {called & forbidden}"
    assert port.apply_persistent_instruction_to_turn.await_count == 2


# ---------------------------------------------------------------------------
# tenant-isolation — tenant_id always propagated to the port
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_for_turn_propagates_tenant_id() -> None:
    """tenant-isolation: the port receives tenant_id for the dual-filter query."""
    bridge, port = _make_bridge(applied=True)
    other_tenant = uuid4()

    await bridge.apply_for_turn(tenant_id=other_tenant, lead_id=LEAD_ID)

    kwargs = port.apply_persistent_instruction_to_turn.await_args.kwargs
    assert kwargs["tenant_id"] == other_tenant


# ---------------------------------------------------------------------------
# graceful-degradation — a port failure is best-effort (turn never breaks)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_port_failure_is_best_effort() -> None:
    """A bridge failure MUST NOT propagate — the turn proceeds without the instruction.

    Observability degradation never breaks the conversational turn
    (copilot-resilience / graceful-degradation cardinal).
    """
    bridge, port = _make_bridge(applied=True)
    port.apply_persistent_instruction_to_turn.side_effect = RuntimeError("db down")

    # Must not raise; returns False (instruction not applied this turn).
    applied = await bridge.apply_for_turn(tenant_id=TENANT_ID, lead_id=LEAD_ID)

    assert applied is False


# ---------------------------------------------------------------------------
# anti-duplication / DDD — no engine/crm concretion imports
# ---------------------------------------------------------------------------


def test_bridge_does_not_import_engine_or_crm_concretions() -> None:
    """DDD boundary + anti-dup: the bridge couples via injected ports only."""
    from src.modules.vitalia.sales_agent.application.services import operator_instruction_bridge

    source = inspect.getsource(operator_instruction_bridge)
    # No engine sync state repository / checkpoint model concretion.
    assert "AgentStateCheckpointModel" not in source, "bridge must not import the engine checkpoint model"
    assert "StateRepository" not in source, "bridge must not import the engine state repository"
    # No crm cross-module import.
    assert "from src.modules.vitalia.crm" not in source, "bridge must not import crm (cross-module ban)"
    # No engine package import (consume via the injected Protocol port only).
    assert "import luana_core_sales_agent" not in source
    assert "from luana_core_sales_agent" not in source
