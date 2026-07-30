"""Workflow tests — TreatmentFollowupWorkflow paused_awaiting_clinic + dropped branches.

TDD: RED first per `.claude/rules/tdd-mandatory.md`.

Covers (02-design § 4.2 + § 4.3):
  - D5_check (no patient response, timeout) → paused_awaiting_clinic (per § 4.3 48h)
  - D14_check (no response, timeout) → paused_awaiting_clinic
  - paused_awaiting_clinic (clinic resumes patient) → D{N}_check
  - paused_awaiting_clinic (>14d cumulative no engagement) → dropped (terminal)

Timeouts in unit tests are simulated by passing explicit `timeout_exceeded`
flag in cron tick input — no live wall-clock waiting. Real timeout
enforcement happens in cron worker scheduling layer (out of scope T-workflow-1
unit tests).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import pytest


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.UUID("99999999-9999-9999-9999-999999999999")


@pytest.fixture
def treatment_id() -> uuid.UUID:
    return uuid.UUID("88888888-8888-8888-8888-888888888888")


@pytest.fixture
def initial_state(tenant_id: uuid.UUID, treatment_id: uuid.UUID) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "treatment_id": treatment_id,
        "patient_id": uuid.UUID("77777777-7777-7777-7777-777777777777"),
        "doctor_id": uuid.UUID("66666666-6666-6666-6666-666666666666"),
        "booking_id": uuid.UUID("55555555-aaaa-bbbb-cccc-dddddddddddd"),
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
# Timeout at D5_check → paused_awaiting_clinic
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_d5_check_no_response_timeout_routes_to_awaiting_clinic(
    initial_state: dict[str, Any],
    thread_config: dict[str, Any],
    memory_checkpointer: Any,
) -> None:
    """D5_check with explicit timeout (no last_patient_response) → paused_awaiting_clinic."""
    from src.modules.vitalia.copilot.workflows.treatment_followup_workflow import (
        build_treatment_followup_workflow,
    )

    workflow = build_treatment_followup_workflow(checkpointer=memory_checkpointer)

    await workflow.ainvoke(initial_state, config=thread_config)

    # D5_check tick fires but patient never responded — timeout exceeded
    timeout_input = {
        "current_step": "D5_check",
        "last_patient_response": None,  # No response ever received
        "paused_reason": "timeout_no_response_48h",
    }
    state_after = await workflow.ainvoke(timeout_input, config=thread_config)

    assert state_after["current_step"] == "paused_awaiting_clinic", (
        f"Expected paused_awaiting_clinic on timeout, got {state_after['current_step']}"
    )
    assert state_after["paused_reason"] is not None


@pytest.mark.asyncio
async def test_d14_check_no_response_routes_to_awaiting_clinic(
    initial_state: dict[str, Any],
    thread_config: dict[str, Any],
    memory_checkpointer: Any,
) -> None:
    """D14_check timeout same as D5_check — routes to paused_awaiting_clinic."""
    from src.modules.vitalia.copilot.workflows.treatment_followup_workflow import (
        build_treatment_followup_workflow,
    )

    workflow = build_treatment_followup_workflow(checkpointer=memory_checkpointer)

    await workflow.ainvoke(initial_state, config=thread_config)

    timeout_input = {
        "current_step": "D14_check",
        "last_patient_response": None,
        "paused_reason": "timeout_no_response_48h",
    }
    state_after = await workflow.ainvoke(timeout_input, config=thread_config)

    assert state_after["current_step"] == "paused_awaiting_clinic"


# ---------------------------------------------------------------------------
# Resume from awaiting_clinic
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_paused_awaiting_clinic_resume_returns_to_check(
    initial_state: dict[str, Any],
    thread_config: dict[str, Any],
    memory_checkpointer: Any,
) -> None:
    """Patient finally responds OR clinic manual handoff → workflow resumes to D{N}_check."""
    from src.modules.vitalia.copilot.workflows.treatment_followup_workflow import (
        build_treatment_followup_workflow,
    )

    workflow = build_treatment_followup_workflow(checkpointer=memory_checkpointer)

    await workflow.ainvoke(initial_state, config=thread_config)

    # Trigger awaiting_clinic
    await workflow.ainvoke(
        {
            "current_step": "D5_check",
            "last_patient_response": None,
            "paused_reason": "timeout_no_response_48h",
        },
        config=thread_config,
    )

    # Resume signal: patient responded (or clinic manual outreach succeeded)
    resume_input = {
        "current_step": "paused_awaiting_clinic",
        "last_patient_response": "Perdón, recién veo el mensaje, todo bien.",
        "paused_reason": "patient_responded_late",
    }
    state_after = await workflow.ainvoke(resume_input, config=thread_config)

    assert state_after["current_step"] in {"D5_check", "D5_complete", "D14_check"}, (
        f"Expected resume to D5_check or onward, got {state_after['current_step']}"
    )


# ---------------------------------------------------------------------------
# Dropped terminal
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_paused_awaiting_clinic_14d_no_engagement_drops(
    initial_state: dict[str, Any],
    thread_config: dict[str, Any],
    memory_checkpointer: Any,
) -> None:
    """>14d cumulative no engagement → dropped terminal."""
    from src.modules.vitalia.copilot.workflows.treatment_followup_workflow import (
        build_treatment_followup_workflow,
    )

    workflow = build_treatment_followup_workflow(checkpointer=memory_checkpointer)

    await workflow.ainvoke(initial_state, config=thread_config)
    await workflow.ainvoke(
        {
            "current_step": "D5_check",
            "last_patient_response": None,
            "paused_reason": "timeout_no_response_48h",
        },
        config=thread_config,
    )

    # 14d cumulative no engagement — drop signal
    drop_input = {
        "current_step": "paused_awaiting_clinic",
        "paused_reason": "cumulative_14d_no_engagement_dropped",
    }
    state_after = await workflow.ainvoke(drop_input, config=thread_config)

    assert state_after["current_step"] == "dropped", f"Expected dropped terminal, got {state_after['current_step']}"
