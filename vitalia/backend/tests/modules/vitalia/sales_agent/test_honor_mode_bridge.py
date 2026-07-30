# cap: sales_agent.honor-mode-bridge
# story-origin: vitalia-fase2-adrian-canal-inbound T-BE-3
"""RED tests for HonorModeBridge — decide/consulta/pausa modes (SC-2, SC-3, SC-3a).

TDD: these tests MUST go RED before production code is written.

HonorModeBridge resolves the operating mode per-conversation using the three
inbox fields shipped by the adrian-inbox cap:
  - handler_mode:      'ai' | 'human'
  - proposal_required: bool
  - pause_until:       datetime | None

Three modes:
  decide   — handler_mode='ai', proposal_required=False, no active pause
             → outbound ALLOWED (returns HonorModeDecision.DECIDE)
  consulta — handler_mode='ai', proposal_required=True
             → outbound BLOCKED; draft MUST be created (returns CONSULTA)
  pausa    — pause_until is in the future, OR handler_mode='human'
             → AI skips response entirely (returns PAUSA)

Note: the bridge does NOT do any I/O — it is a pure resolver that maps
Conversation domain fields to a HonorModeDecision enum. The call site (in
the brand chat.py extension hook) acts on the decision.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

# ── these imports will FAIL (RED) until production code is written ──
from src.modules.vitalia.sales_agent.application.services.honor_mode_bridge import (
    HonorModeBridge,
    HonorModeDecision,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(timezone.utc)
_FUTURE = _NOW + timedelta(minutes=30)
_PAST = _NOW - timedelta(minutes=30)
_TENANT = uuid4()
_CLINIC = uuid4()
_LEAD = uuid4()


def _conv(
    *,
    handler_mode: str = "ai",
    proposal_required: bool = False,
    pause_until: datetime | None = None,
) -> MagicMock:
    """Build a minimal Conversation-like object with the three mode fields."""
    c = MagicMock()
    c.handler_mode = handler_mode
    c.proposal_required = proposal_required
    c.pause_until = pause_until
    c.tenant_id = _TENANT
    c.clinic_id = _CLINIC
    c.lead_id = _LEAD
    return c


# ---------------------------------------------------------------------------
# SC-decide — happy path: AI active, no proposal required, no pause
# ---------------------------------------------------------------------------


def test_decide_mode_when_ai_no_proposal_no_pause() -> None:
    """SC-decide: handler_mode='ai', proposal_required=False, no pause → DECIDE."""
    bridge = HonorModeBridge()
    decision = bridge.resolve(_conv())
    assert decision == HonorModeDecision.DECIDE


def test_decide_mode_when_pause_expired() -> None:
    """Expired pause_until (past datetime) → treated as no-pause → DECIDE."""
    bridge = HonorModeBridge()
    decision = bridge.resolve(_conv(pause_until=_PAST))
    assert decision == HonorModeDecision.DECIDE


# ---------------------------------------------------------------------------
# SC-2 — consulta: AI active but proposal_required=True → draft, 0 outbound
# ---------------------------------------------------------------------------


def test_consulta_mode_when_proposal_required_true() -> None:
    """SC-2: handler_mode='ai', proposal_required=True → CONSULTA (draft, 0 outbound)."""
    bridge = HonorModeBridge()
    decision = bridge.resolve(_conv(proposal_required=True))
    assert decision == HonorModeDecision.CONSULTA


def test_consulta_mode_not_pausa_even_if_proposal_required() -> None:
    """CONSULTA takes priority over DECIDE when proposal_required=True (not PAUSA)."""
    bridge = HonorModeBridge()
    # No pause → must be CONSULTA (not PAUSA, not DECIDE)
    decision = bridge.resolve(_conv(proposal_required=True, pause_until=None))
    assert decision == HonorModeDecision.CONSULTA


# ---------------------------------------------------------------------------
# SC-3 / SC-3a — pausa: pause_until is future, OR handler_mode='human'
# ---------------------------------------------------------------------------


def test_pausa_mode_when_pause_until_is_future() -> None:
    """SC-3: pause_until is in the future → PAUSA (Adrián skips reply)."""
    bridge = HonorModeBridge()
    decision = bridge.resolve(_conv(pause_until=_FUTURE))
    assert decision == HonorModeDecision.PAUSA


def test_pausa_mode_when_handler_mode_human() -> None:
    """SC-3a: handler_mode='human' → PAUSA regardless of other fields."""
    bridge = HonorModeBridge()
    decision = bridge.resolve(_conv(handler_mode="human"))
    assert decision == HonorModeDecision.PAUSA


def test_pausa_mode_human_overrides_proposal_required() -> None:
    """handler_mode='human' → PAUSA even if proposal_required=True."""
    bridge = HonorModeBridge()
    decision = bridge.resolve(_conv(handler_mode="human", proposal_required=True))
    assert decision == HonorModeDecision.PAUSA


def test_pausa_mode_future_pause_overrides_proposal_required() -> None:
    """Active pause_until overrides proposal_required → PAUSA not CONSULTA."""
    bridge = HonorModeBridge()
    decision = bridge.resolve(_conv(pause_until=_FUTURE, proposal_required=True))
    assert decision == HonorModeDecision.PAUSA


# ---------------------------------------------------------------------------
# Priority ordering: PAUSA > CONSULTA > DECIDE
# ---------------------------------------------------------------------------


def test_mode_priority_order() -> None:
    """PAUSA beats CONSULTA; CONSULTA beats DECIDE. Explicit ordering check."""
    bridge = HonorModeBridge()

    # PAUSA priority
    assert bridge.resolve(_conv(handler_mode="human", proposal_required=True)) == HonorModeDecision.PAUSA
    assert bridge.resolve(_conv(pause_until=_FUTURE, proposal_required=True)) == HonorModeDecision.PAUSA

    # CONSULTA priority
    assert bridge.resolve(_conv(proposal_required=True, pause_until=None)) == HonorModeDecision.CONSULTA

    # DECIDE baseline
    assert bridge.resolve(_conv()) == HonorModeDecision.DECIDE


# ---------------------------------------------------------------------------
# HonorModeDecision enum contract
# ---------------------------------------------------------------------------


def test_decision_enum_has_three_values() -> None:
    """Three and exactly three modes: DECIDE, CONSULTA, PAUSA."""
    values = {d.value for d in HonorModeDecision}
    assert values == {"decide", "consulta", "pausa"}


# ---------------------------------------------------------------------------
# Bridge is pure — no I/O, no DB, no external calls
# ---------------------------------------------------------------------------


def test_bridge_is_pure_no_async() -> None:
    """Bridge.resolve is synchronous — pure function, no await, no side effects."""
    import inspect

    bridge = HonorModeBridge()
    assert not inspect.iscoroutinefunction(bridge.resolve), "resolve must be sync (pure)"
