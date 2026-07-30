# cap: sales_agent.state-overlay-langgraph
# story-origin: vitalia-fase2-adrian-canal-inbound T-AG-1
"""Tests for the booking keys EXTENDED onto VitaliaSalesAgentStateExtension (T-AG-1).

Per 03-arch-agentic.md § 1.1 + 02-design-agentic.md § 6: extend the brand state
overlay with 4 MINIMAL booking keys (total=False), referencing — not duplicating —
the engine ``scheduled_meetings``. Keys carry no PHI; ``candidate_slots`` is a
VOLATILE per-turn signal (slot 8) that MUST NEVER enter a cacheable prompt prefix.

The engine AgentState TypedDict + MeetingEntry are NOT touched (engine read-only).
"""

from __future__ import annotations

from typing import get_type_hints

from src.modules.vitalia.sales_agent.domain.state_overlay import (
    VitaliaSalesAgentStateExtension,
)

# Existing keys (must remain — no regression on the shipped overlay).
_EXISTING_KEYS = {
    "clinic_id",
    "vertical",
    "screening_outcome",
    "medical_disclaimer_shown",
    "phi_blocked_messages",
    "compliance_level",
}

# NEW booking keys added by T-AG-1.
_NEW_BOOKING_KEYS = {
    "recommended_doctor_id",
    "recommended_service_offer_id",
    "candidate_slots",
    "doctor_profile_shared_at",
}


def test_overlay_keeps_existing_keys() -> None:
    """Regression: the shipped overlay keys are preserved (no destructive edit)."""
    hints = get_type_hints(VitaliaSalesAgentStateExtension, include_extras=True)
    missing = _EXISTING_KEYS - set(hints.keys())
    assert not missing, f"overlay lost existing keys: {missing}"


def test_overlay_adds_booking_keys() -> None:
    """T-AG-1: the 4 minimal booking keys are present on the overlay."""
    hints = get_type_hints(VitaliaSalesAgentStateExtension, include_extras=True)
    missing = _NEW_BOOKING_KEYS - set(hints.keys())
    assert not missing, f"overlay missing new booking keys: {missing}"


def test_overlay_is_total_false() -> None:
    """All overlay keys are optional (total=False) — gradual lifecycle population."""
    # TypedDict total=False → __total__ is False; all keys live in __optional_keys__.
    assert VitaliaSalesAgentStateExtension.__total__ is False
    optional = VitaliaSalesAgentStateExtension.__optional_keys__
    for key in _NEW_BOOKING_KEYS:
        assert key in optional, f"{key} must be optional (total=False)"


def test_candidate_slots_documented_volatile() -> None:
    """``candidate_slots`` MUST be documented as volatile-only (never cacheable prefix).

    Cache integrity (03-arch-agentic § 1.1 + § 2.3): candidate_slots is a per-turn
    signal for reasoning-based slot mapping and is a forbidden cacheable-prefix
    element. The source module must say so explicitly so future edits don't
    promote it into the cacheable prefix (silent invalidator).
    """
    import src.modules.vitalia.sales_agent.domain.state_overlay as overlay_mod

    src = overlay_mod.__doc__ or ""
    # The module docstring documents the volatile/cacheable boundary for candidate_slots.
    assert "candidate_slots" in src
    assert "volatile" in src.lower() or "volátil" in src.lower()


def test_engine_state_not_touched() -> None:
    """The overlay declares ONLY brand keys — it never redeclares engine base keys.

    ``messages`` / ``tenant_id`` / ``scheduled_meetings`` are engine-owned; the
    brand overlay must not shadow them (composition, not duplication).
    """
    hints = get_type_hints(VitaliaSalesAgentStateExtension, include_extras=True)
    engine_owned = {"messages", "tenant_id", "scheduled_meetings", "resume_objective"}
    leaked = engine_owned & set(hints.keys())
    assert not leaked, f"overlay must not redeclare engine-owned keys: {leaked}"
