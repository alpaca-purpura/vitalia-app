"""Unit tests — WizardOnboardingState TypedDict + helper guards.

Per 03-arch-agentic.md § 2.1 + 05-guidelines.md § 1.11 LangGraph patterns:
  - TypedDict state schemas with tenant_id MANDATORY in every state
  - iterations: int key + max-iter guard
  - Sub-keys cover slot machinery, deepagents sandbox bridge, compliance

This module guards the SHAPE (annotations) and the helper invariants used by
the supervisor router (decide_next_node). The state is intentionally
brand-extension (not engine) because the wizard supervisor is brand-specific
per § 3.1.
"""

from __future__ import annotations

from typing import get_type_hints
from uuid import uuid4


def test_state_has_tenant_isolation_keys():
    """Tenant isolation cardinal — tenant_id + user_id present in annotations."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_state import (
        WizardOnboardingState,
    )

    hints = get_type_hints(WizardOnboardingState, include_extras=True)
    assert "tenant_id" in hints, "tenant_id MUST be present (tenant-isolation cardinal)"
    assert "user_id" in hints, "user_id MUST be present"
    assert "clinic_id" in hints, "clinic_id optional but declared (HIPAA-lite dual filter slot)"


def test_state_has_iterations_guard_field():
    """Max-iter guard requires `iterations: int` per copilot-resilience.md."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_state import (
        WizardOnboardingState,
    )

    hints = get_type_hints(WizardOnboardingState, include_extras=True)
    assert "iterations" in hints, "iterations field required for max-iter guard (cap 25)"


def test_state_has_slot_machinery_keys():
    """Wizard core: required + optional + pending + bonus slot maps."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_state import (
        WizardOnboardingState,
    )

    hints = get_type_hints(WizardOnboardingState, include_extras=True)
    for key in (
        "slots_required_confirmed",
        "slots_optional_confirmed",
        "slots_pending",
        "bonus_extracted",
    ):
        assert key in hints, f"slot machinery key missing: {key}"


def test_state_has_subagent_bridge_keys():
    """Deepagents sandbox bridge — input + output keys (state isolation surface)."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_state import (
        WizardOnboardingState,
    )

    hints = get_type_hints(WizardOnboardingState, include_extras=True)
    assert "extraction_subagent_input" in hints, "subagent input bridge required"
    assert "extraction_subagent_output" in hints, "subagent output bridge required"


def test_state_has_completion_and_error_keys():
    """Termination + error bridge for honest trace recorder."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_state import (
        WizardOnboardingState,
    )

    hints = get_type_hints(WizardOnboardingState, include_extras=True)
    assert "task_complete" in hints, "task_complete bool flag for END branch"
    assert "last_error" in hints, "last_error dict for set_turn_error trace honesty"


def test_required_all_confirmed_guard_helper_true_when_all_present():
    """Helper: required slots all marked confirmed → True."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_state import (
        WizardOnboardingState,
        required_all_confirmed,
    )

    state: WizardOnboardingState = {
        "tenant_id": str(uuid4()),
        "user_id": str(uuid4()),
        "clinic_id": None,
        "messages": [],
        "iterations": 0,
        "slots_required_confirmed": {
            "tenant.name": {
                "slot_id": "tenant.name",
                "value": "Clínica X",
                "confidence": 1.0,
                "confirmed_at": "2026-05-18T00:00:00Z",
                "source": "user_text",
            },
            "tenant.vertical": {
                "slot_id": "tenant.vertical",
                "value": "dental",
                "confidence": 1.0,
                "confirmed_at": "2026-05-18T00:00:00Z",
                "source": "user_text",
            },
            "tenant.location": {
                "slot_id": "tenant.location",
                "value": "Lima",
                "confidence": 1.0,
                "confirmed_at": "2026-05-18T00:00:00Z",
                "source": "user_text",
            },
        },
        "slots_optional_confirmed": {},
        "slots_pending": [],
        "bonus_extracted": {},
        "mode": "guiado",
        "voice_profile_partial": None,
        "voice_samples": [],
        "landing_preview_url": None,
        "extraction_subagent_input": None,
        "extraction_subagent_output": None,
        "pii_detected_in_doc": False,
        "consent_voice_activation": False,
        "last_error": None,
        "task_complete": False,
    }
    assert required_all_confirmed(state) is True


def test_required_all_confirmed_guard_helper_false_when_one_missing():
    """Helper: required slot missing → False."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_state import (
        required_all_confirmed,
    )

    state = {
        "slots_required_confirmed": {
            "tenant.name": {
                "slot_id": "tenant.name",
                "value": "X",
                "confidence": 1.0,
                "confirmed_at": "2026-05-18T00:00:00Z",
                "source": "user_text",
            }
            # tenant.vertical + tenant.location missing
        }
    }
    assert required_all_confirmed(state) is False


def test_initial_state_factory_provides_defaults():
    """Factory: build_initial_state() returns dict with all required keys + safe defaults."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_state import (
        build_initial_state,
    )

    tenant_id = str(uuid4())
    user_id = str(uuid4())
    state = build_initial_state(tenant_id=tenant_id, user_id=user_id, clinic_id=None)
    assert state["tenant_id"] == tenant_id
    assert state["user_id"] == user_id
    assert state["clinic_id"] is None
    assert state["iterations"] == 0
    assert state["task_complete"] is False
    assert state["slots_required_confirmed"] == {}
    assert state["messages"] == []
    assert state["pii_detected_in_doc"] is False


def test_initial_state_required_slots_pending_list():
    """slots_pending seeded with required slot ids."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_state import (
        REQUIRED_SLOT_IDS,
        build_initial_state,
    )

    state = build_initial_state(tenant_id=str(uuid4()), user_id=str(uuid4()), clinic_id=None)
    assert sorted(state["slots_pending"]) == sorted(REQUIRED_SLOT_IDS)
