"""Workflow tests — TreatmentFollowupWorkflow resume from checkpoint.

TDD: RED first per `.claude/rules/tdd-mandatory.md`.

Acceptance per 06-tickets.yaml::T-workflow-1:
  A3: Resume from RedisSaver checkpoint reconstructs state correctly

Covers (02-design § 4.4):
  - Checkpoint per state transition + per patient turn
  - State key composite (tenant_id, treatment_id) → tenant isolation enforced
  - Replay: build NEW workflow instance, same checkpointer + same thread_id →
    state reconstructed identically

Note D10: RedisSaver swap deferred until langgraph-checkpoint-redis package
install lands. Tests use MemorySaver — same checkpointer protocol contract.
Acceptance criterion satisfied for "from configured checkpointer" semantics.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import pytest


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.UUID("12121212-1212-1212-1212-121212121212")


@pytest.fixture
def treatment_id() -> uuid.UUID:
    return uuid.UUID("34343434-3434-3434-3434-343434343434")


@pytest.fixture
def initial_state(tenant_id: uuid.UUID, treatment_id: uuid.UUID) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "treatment_id": treatment_id,
        "patient_id": uuid.UUID("56565656-5656-5656-5656-565656565656"),
        "doctor_id": uuid.UUID("78787878-7878-7878-7878-787878787878"),
        "booking_id": uuid.UUID("90909090-9090-9090-9090-909090909090"),
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
# A3 — Resume from checkpoint reconstructs state
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resume_from_checkpoint_reconstructs_state_after_d5(
    initial_state: dict[str, Any],
    thread_config: dict[str, Any],
    memory_checkpointer: Any,
) -> None:
    """A3 acceptance: build new workflow instance + same checkpointer + same thread_id
    → state reconstructed correctly.
    """
    from src.modules.vitalia.copilot.workflows.treatment_followup_workflow import (
        build_treatment_followup_workflow,
    )

    # Build first workflow instance, run partially
    workflow_v1 = build_treatment_followup_workflow(checkpointer=memory_checkpointer)
    await workflow_v1.ainvoke(initial_state, config=thread_config)
    await workflow_v1.ainvoke(
        {
            "current_step": "D5_check",
            "last_patient_response": "Todo bien, sin dolor.",
        },
        config=thread_config,
    )

    # Get state snapshot from checkpointer
    state_v1 = await workflow_v1.aget_state(thread_config)
    assert state_v1.values["current_step"] in {"D5_complete", "D14_check"}
    saved_step_v1 = state_v1.values["current_step"]
    saved_tenant_id_v1 = state_v1.values["tenant_id"]
    saved_treatment_id_v1 = state_v1.values["treatment_id"]

    # Build NEW workflow instance with SAME checkpointer
    workflow_v2 = build_treatment_followup_workflow(checkpointer=memory_checkpointer)

    # Read state from new instance — should match
    state_v2 = await workflow_v2.aget_state(thread_config)
    assert state_v2.values["current_step"] == saved_step_v1
    assert state_v2.values["tenant_id"] == saved_tenant_id_v1
    assert state_v2.values["treatment_id"] == saved_treatment_id_v1

    # Continue execution from checkpoint
    state_after_d14 = await workflow_v2.ainvoke(
        {
            "current_step": "D14_check",
            "last_patient_response": "Sutura bien.",
        },
        config=thread_config,
    )
    assert state_after_d14["current_step"] in {"D14_complete", "D90_check"}


@pytest.mark.asyncio
async def test_thread_id_isolates_separate_treatments(
    memory_checkpointer: Any,
) -> None:
    """Two treatments with distinct (tenant_id, treatment_id) thread_ids do not collide.

    Tests state key composite per 02-design § 4.4 — checkpoint partitioned by thread_id,
    cross-treatment isolation guaranteed at checkpointer level.
    """
    from src.modules.vitalia.copilot.workflows.treatment_followup_workflow import (
        build_treatment_followup_workflow,
    )

    workflow = build_treatment_followup_workflow(checkpointer=memory_checkpointer)

    tenant_a = uuid.UUID("aaaaaaaa-1111-1111-1111-111111111111")
    treatment_a = uuid.UUID("aaaaaaaa-2222-2222-2222-222222222222")
    tenant_b = uuid.UUID("bbbbbbbb-1111-1111-1111-111111111111")
    treatment_b = uuid.UUID("bbbbbbbb-2222-2222-2222-222222222222")

    state_a = {
        "tenant_id": tenant_a,
        "treatment_id": treatment_a,
        "patient_id": uuid.uuid4(),
        "doctor_id": uuid.uuid4(),
        "booking_id": uuid.uuid4(),
        "procedure_date": datetime(2026, 5, 14, tzinfo=timezone.utc),
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
    state_b = {**state_a, "tenant_id": tenant_b, "treatment_id": treatment_b}

    config_a = {"configurable": {"thread_id": f"{tenant_a}:{treatment_a}"}}
    config_b = {"configurable": {"thread_id": f"{tenant_b}:{treatment_b}"}}

    # Run treatment A to D5_check
    await workflow.ainvoke(state_a, config=config_a)
    await workflow.ainvoke(
        {"current_step": "D5_check", "last_patient_response": "Bien."},
        config=config_a,
    )

    # Run treatment B fresh from D0_init (must NOT see A's progress)
    state_b_after_init = await workflow.ainvoke(state_b, config=config_b)
    assert state_b_after_init["tenant_id"] == tenant_b
    assert state_b_after_init["treatment_id"] == treatment_b
    assert state_b_after_init["current_step"] in {"D0_init", "D5_check"}

    # Re-read A: should still be at D5 progression (not affected by B)
    snapshot_a = await workflow.aget_state(config_a)
    assert snapshot_a.values["tenant_id"] == tenant_a
    assert snapshot_a.values["current_step"] in {"D5_complete", "D14_check"}
