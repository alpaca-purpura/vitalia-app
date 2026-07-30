"""Workflow tests — TreatmentFollowupWorkflow D0→D90 happy path.

TDD: RED first per `.claude/rules/tdd-mandatory.md`.

Acceptance per 06-tickets.yaml::T-workflow-1:
  A1: D0→D90 happy path completes via cron ticks
  A4: Total D0→D90 cost ≤$0.25 USD per workflow run

Covers (02-design § 4.1 ASCII diagram + § 4.2 transitions table):
  - D0_init → D5_check via cron tick D+5d
  - D5_check (patient response OK + no safety) → D5_complete
  - D5_complete → D14_check via cron tick D+14d
  - D14_check (response OK + no safety) → D14_complete
  - D14_complete → D90_check via cron tick D+90d
  - D90_check (response OK) → completed terminal

These are UNIT tests — uses MemorySaver checkpointer (RedisSaver swap deferred
per D10 + langgraph-checkpoint-redis package install). LLM tool calls (ping
composers + adherence/sentiment classifiers) are mocked at workflow node
boundary; T-tools-4 implements the real tool. Cost accumulator increments
deterministically per node invocation (mock cost contributions).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tenant_id() -> uuid.UUID:
    """Stable tenant_id for happy-path runs."""
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def treatment_id() -> uuid.UUID:
    """Stable treatment_id for happy-path runs."""
    return uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def initial_state(tenant_id: uuid.UUID, treatment_id: uuid.UUID) -> dict[str, Any]:
    """Initial workflow state at D0_init entry per 02-design § 4 + § 6.1."""
    return {
        "tenant_id": tenant_id,
        "treatment_id": treatment_id,
        "patient_id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
        "doctor_id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
        "booking_id": uuid.UUID("55555555-5555-5555-5555-555555555555"),
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
    """Per-thread config — composite (tenant_id, treatment_id) per 02-design § 4.4."""
    return {"configurable": {"thread_id": f"{tenant_id}:{treatment_id}"}}


@pytest.fixture
def memory_checkpointer():
    """In-process checkpointer — RedisSaver swap deferred per D10 staging."""
    from langgraph.checkpoint.memory import MemorySaver

    return MemorySaver()


# ---------------------------------------------------------------------------
# A1 — D0 → D90 happy path (cron-driven)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_d0_to_d90_happy_path_completes(
    initial_state: dict[str, Any],
    thread_config: dict[str, Any],
    memory_checkpointer: Any,
) -> None:
    """A1 acceptance: D0 → D5 → D14 → D90 → completed via cron-driven ticks.

    Each cron tick advances the workflow one milestone. Patient responds OK
    with no safety keywords. Workflow reaches `completed` terminal.
    """
    from src.modules.vitalia.copilot.workflows.treatment_followup_workflow import (
        build_treatment_followup_workflow,
    )

    workflow = build_treatment_followup_workflow(checkpointer=memory_checkpointer)

    # D0_init runs (procedure_completed event simulated by entry node)
    state_after_d0 = await workflow.ainvoke(initial_state, config=thread_config)
    assert state_after_d0["current_step"] in {"D0_init", "D5_check"}, (
        f"After D0_init, expected to be at D0_init or D5_check (cron tick deferred), "
        f"got {state_after_d0['current_step']}"
    )

    # Simulate cron tick D5: invoke workflow with milestone update + patient response
    d5_response_input = {
        "current_step": "D5_check",
        "last_patient_response": "Todo bien, sin dolor ni sangrado.",
    }
    state_after_d5 = await workflow.ainvoke(d5_response_input, config=thread_config)
    assert state_after_d5["current_step"] in {"D5_complete", "D14_check"}, (
        f"After D5_check with OK response, expected D5_complete or D14_check, got {state_after_d5['current_step']}"
    )
    assert state_after_d5["safety_triggered"] is False
    assert state_after_d5["adherence_score"] is not None and state_after_d5["adherence_score"] >= 1

    # Simulate cron tick D14
    d14_response_input = {
        "current_step": "D14_check",
        "last_patient_response": "Sutura cicatrizando bien, sin molestias.",
    }
    state_after_d14 = await workflow.ainvoke(d14_response_input, config=thread_config)
    assert state_after_d14["current_step"] in {"D14_complete", "D90_check"}
    assert state_after_d14["safety_triggered"] is False

    # Simulate cron tick D90
    d90_response_input = {
        "current_step": "D90_check",
        "last_patient_response": "Corona colocada hace dos semanas, todo perfecto.",
    }
    state_after_d90 = await workflow.ainvoke(d90_response_input, config=thread_config)
    assert state_after_d90["current_step"] == "completed", (
        f"After D90_check with OK response, expected completed, got {state_after_d90['current_step']}"
    )


# ---------------------------------------------------------------------------
# A4 — Total cost across D0 → D90 ≤ $0.25 USD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_total_cost_budget(
    initial_state: dict[str, Any],
    thread_config: dict[str, Any],
    memory_checkpointer: Any,
) -> None:
    """A4 acceptance: total D0→D90 cost ≤$0.25 USD per workflow run.

    cost_budget_per_workflow_run from module_registry_entry. Cost accumulates
    in state.cost_accumulated_usd at each node invocation.
    """
    from src.modules.vitalia.copilot.workflows.module_registry_entry_helpers import (
        get_workflow_cost_budget_usd,
    )
    from src.modules.vitalia.copilot.workflows.treatment_followup_workflow import (
        build_treatment_followup_workflow,
    )

    budget = get_workflow_cost_budget_usd()
    assert budget == 0.25, f"Expected cost_budget_per_workflow_run=0.25 USD, got {budget}"

    workflow = build_treatment_followup_workflow(checkpointer=memory_checkpointer)

    # Run full happy path
    await workflow.ainvoke(initial_state, config=thread_config)
    await workflow.ainvoke(
        {"current_step": "D5_check", "last_patient_response": "Todo bien."},
        config=thread_config,
    )
    await workflow.ainvoke(
        {"current_step": "D14_check", "last_patient_response": "Sin molestias."},
        config=thread_config,
    )
    final_state = await workflow.ainvoke(
        {"current_step": "D90_check", "last_patient_response": "Todo perfecto."},
        config=thread_config,
    )

    accumulated = final_state["cost_accumulated_usd"]
    assert accumulated <= budget, f"Total cost {accumulated:.4f} USD exceeded budget {budget:.4f} USD"
    # Cost must be positive (nodes did execute)
    assert accumulated > 0, "Expected non-zero accumulated cost (nodes invoked LLM stubs)"
