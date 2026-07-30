"""Workflow tests — TreatmentFollowupWorkflow safety escalation branch.

TDD: RED first per `.claude/rules/tdd-mandatory.md`.

Acceptance per 06-tickets.yaml::T-workflow-1:
  A2: Safety keyword triggers paused_safety_escalation

Covers (02-design § 4.2 transitions table):
  - D5_check (safety keywords detected) → paused_safety_escalation
  - paused_safety_escalation (clinic resolves "Resolved, re-engage patient") → resume D5_check
  - paused_safety_escalation (clinic resolves "Treatment closed / referred elsewhere") → completed

Safety keywords per 02-design § 2.2:
  ["dolor", "hinchazón", "sangrado", "fiebre", "dolor pecho", "no puedo respirar",
   "alergia", "reacción"]
Plus diagnosis-request regex: r"(tengo|tendré|sufro|padezco|me dio).*(cáncer|...)"
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import pytest


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def treatment_id() -> uuid.UUID:
    return uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture
def initial_state(tenant_id: uuid.UUID, treatment_id: uuid.UUID) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "treatment_id": treatment_id,
        "patient_id": uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        "doctor_id": uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
        "booking_id": uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
        "procedure_date": datetime(2026, 5, 14, 10, 0, 0, tzinfo=timezone.utc),
        "current_step": "D0_init",
        "last_patient_response": None,
        "adherence_score": None,
        "sentiment": None,
        "safety_triggered": False,
        "next_milestone_at": None,
        "paused_reason": None,
        "cost_accumulated_usd": 0.0,
        "iterations": 0,
    }


@pytest.fixture
def thread_config(tenant_id: uuid.UUID, treatment_id: uuid.UUID) -> dict[str, Any]:
    return {"configurable": {"thread_id": f"{tenant_id}:{treatment_id}"}}


@pytest.fixture
def memory_checkpointer():
    from langgraph.checkpoint.memory import MemorySaver

    return MemorySaver()


# ---------------------------------------------------------------------------
# A2 — Safety keyword routes to paused_safety_escalation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_safety_keyword_pain_chest_triggers_escalation(
    initial_state: dict[str, Any],
    thread_config: dict[str, Any],
    memory_checkpointer: Any,
) -> None:
    """A2 acceptance: 'dolor pecho' keyword in patient response → paused_safety_escalation.

    Workflow MUST:
      1. Set state.safety_triggered = True
      2. Populate state.paused_reason with safety descriptor
      3. Route to paused_safety_escalation node (not D5_complete)
    """
    from src.modules.vitalia.copilot.workflows.treatment_followup_workflow import (
        build_treatment_followup_workflow,
    )

    workflow = build_treatment_followup_workflow(checkpointer=memory_checkpointer)

    # D0_init
    await workflow.ainvoke(initial_state, config=thread_config)

    # D5_check with safety keyword
    safety_response_input = {
        "current_step": "D5_check",
        "last_patient_response": "Tengo mucho dolor pecho desde anoche, no puedo respirar bien.",
    }
    state_after = await workflow.ainvoke(safety_response_input, config=thread_config)

    assert state_after["safety_triggered"] is True, "Expected safety_triggered=True after dolor pecho keyword detection"
    assert state_after["current_step"] == "paused_safety_escalation", (
        f"Expected route to paused_safety_escalation, got {state_after['current_step']}"
    )
    assert state_after["paused_reason"] is not None, "Expected paused_reason populated with safety descriptor"
    assert "safety" in state_after["paused_reason"].lower() or "dolor" in state_after["paused_reason"].lower(), (
        f"Expected paused_reason to mention safety/dolor, got {state_after['paused_reason']!r}"
    )


@pytest.mark.asyncio
async def test_safety_keyword_allergy_triggers_escalation(
    initial_state: dict[str, Any],
    thread_config: dict[str, Any],
    memory_checkpointer: Any,
) -> None:
    """Edge case: 'alergia' / 'reacción' keywords also trigger safety escalation."""
    from src.modules.vitalia.copilot.workflows.treatment_followup_workflow import (
        build_treatment_followup_workflow,
    )

    workflow = build_treatment_followup_workflow(checkpointer=memory_checkpointer)

    await workflow.ainvoke(initial_state, config=thread_config)

    safety_response_input = {
        "current_step": "D14_check",
        "last_patient_response": "Tengo una reacción alérgica fuerte al medicamento que me dieron.",
    }
    state_after = await workflow.ainvoke(safety_response_input, config=thread_config)

    assert state_after["safety_triggered"] is True
    assert state_after["current_step"] == "paused_safety_escalation"


@pytest.mark.asyncio
async def test_safety_resume_clinic_resolves_re_engage(
    initial_state: dict[str, Any],
    thread_config: dict[str, Any],
    memory_checkpointer: Any,
) -> None:
    """Clinic resolves safety escalation with 'resume' action → workflow returns to milestone check."""
    from src.modules.vitalia.copilot.workflows.treatment_followup_workflow import (
        build_treatment_followup_workflow,
    )

    workflow = build_treatment_followup_workflow(checkpointer=memory_checkpointer)

    await workflow.ainvoke(initial_state, config=thread_config)

    # Trigger safety
    await workflow.ainvoke(
        {
            "current_step": "D5_check",
            "last_patient_response": "Mucho dolor pecho, ayuda.",
        },
        config=thread_config,
    )

    # Clinic resolves, re-engage patient at D5
    resume_input = {
        "current_step": "paused_safety_escalation",
        "paused_reason": "clinic_resolved_re_engage",
    }
    state_after_resume = await workflow.ainvoke(resume_input, config=thread_config)

    assert state_after_resume["current_step"] in {"D5_check", "D5_complete", "D14_check"}, (
        f"Expected resume to D5_check (or onward), got {state_after_resume['current_step']}"
    )
    assert (
        state_after_resume["safety_triggered"] is False
        or state_after_resume["current_step"] != "paused_safety_escalation"
    )


@pytest.mark.asyncio
async def test_safety_resume_clinic_closes_treatment(
    initial_state: dict[str, Any],
    thread_config: dict[str, Any],
    memory_checkpointer: Any,
) -> None:
    """Clinic resolves with 'completed' → workflow terminates."""
    from src.modules.vitalia.copilot.workflows.treatment_followup_workflow import (
        build_treatment_followup_workflow,
    )

    workflow = build_treatment_followup_workflow(checkpointer=memory_checkpointer)

    await workflow.ainvoke(initial_state, config=thread_config)
    await workflow.ainvoke(
        {
            "current_step": "D5_check",
            "last_patient_response": "Sangrado fuerte, fiebre alta.",
        },
        config=thread_config,
    )

    close_input = {
        "current_step": "paused_safety_escalation",
        "paused_reason": "clinic_closed_referred_elsewhere",
    }
    state_after_close = await workflow.ainvoke(close_input, config=thread_config)

    assert state_after_close["current_step"] == "completed"
