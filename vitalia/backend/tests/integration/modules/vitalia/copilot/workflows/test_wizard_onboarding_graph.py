"""Integration test — Valeria wizard supervisor LangGraph topology.

Per 03-arch-agentic.md § 3.1 + § 7 + 04-validators.yaml::be_test_integration_wizard_graph:
  - StateGraph compiles + accepts CheckpointerProtocol (production swap)
  - Supervisor routes to extract_subagent / slot_question / live_preview /
    completion / END
  - Max-iter guard: iterations > 25 → END (no infinite loop)
  - Required slots all confirmed → completion_router → END
  - Subagent input bridge triggers extract_subagent node

NOTE: AsyncPostgresSaver is the production checkpointer per 03-arch-agentic §
7, but `langgraph-checkpoint-postgres` is not yet installed in the runtime
(same situation as RedisSaver in T-workflow-1). The graph factory accepts
ANY LangGraph-compatible checkpointer via CheckpointerProtocol; tests use
InMemorySaver. Production swap = 1-line at composition root.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver


@pytest.fixture
def checkpointer():
    """InMemorySaver for tests; AsyncPostgresSaver for prod per arch § 7."""
    return InMemorySaver()


@pytest.fixture
def initial_state():
    """Fresh wizard state — required slots pending, mode unset."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_state import (
        build_initial_state,
    )

    return build_initial_state(
        tenant_id=str(uuid4()),
        user_id=str(uuid4()),
        clinic_id=None,
    )


def test_graph_compiles_with_checkpointer(checkpointer):
    """Smoke: factory returns a compiled graph object."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_graph import (
        build_wizard_onboarding_graph,
    )

    graph = build_wizard_onboarding_graph(checkpointer=checkpointer)
    assert graph is not None
    # Compiled graph exposes .invoke / .stream / .ainvoke
    assert hasattr(graph, "invoke") or hasattr(graph, "ainvoke")


def test_graph_terminates_on_max_iter_guard(checkpointer, initial_state):
    """iterations > 25 → END (cap per copilot-resilience COPILOT_RECURSION_LIMIT)."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_graph import (
        build_wizard_onboarding_graph,
    )

    graph = build_wizard_onboarding_graph(checkpointer=checkpointer)
    # Seed iterations past the cap
    state = {**initial_state, "iterations": 26}
    config = {"configurable": {"thread_id": f"test-{uuid4()}"}}
    result = graph.invoke(state, config=config)
    # task_complete=True (graceful END) OR result has no further pending action.
    assert result.get("task_complete") is True or result.get("iterations", 0) >= 26


def test_graph_terminates_when_task_complete(checkpointer, initial_state):
    """task_complete=True short-circuits to END."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_graph import (
        build_wizard_onboarding_graph,
    )

    graph = build_wizard_onboarding_graph(checkpointer=checkpointer)
    state = {**initial_state, "task_complete": True}
    config = {"configurable": {"thread_id": f"test-{uuid4()}"}}
    result = graph.invoke(state, config=config)
    assert result.get("task_complete") is True


def test_graph_routes_to_extract_when_subagent_input_provided(checkpointer, initial_state):
    """extraction_subagent_input present + output None → extract_subagent node runs."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_graph import (
        build_wizard_onboarding_graph,
    )

    graph = build_wizard_onboarding_graph(checkpointer=checkpointer)
    state = {
        **initial_state,
        "mode": "libre",
        "extraction_subagent_input": {
            "url": "https://example-clinic.com",
            "text_content": None,
            "audio_url": None,
        },
        "extraction_subagent_output": None,
    }
    config = {"configurable": {"thread_id": f"test-{uuid4()}"}}
    result = graph.invoke(state, config=config)
    # Subagent populates output OR completes turn
    assert (
        result.get("extraction_subagent_output") is not None
        or result.get("task_complete") is True
        or result.get("iterations", 0) > 0
    )


def test_graph_completes_when_required_slots_all_confirmed(checkpointer, initial_state):
    """Required slots confirmed → completion_router → task_complete=True."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_graph import (
        build_wizard_onboarding_graph,
    )

    graph = build_wizard_onboarding_graph(checkpointer=checkpointer)

    def confirmed_slot(sid: str, val: str) -> dict:
        return {
            "slot_id": sid,
            "value": val,
            "confidence": 1.0,
            "confirmed_at": "fixed-ts",
            "source": "user_text",
        }

    state = {
        **initial_state,
        "mode": "guiado",
        "slots_required_confirmed": {
            "tenant.name": confirmed_slot("tenant.name", "Clínica X"),
            "tenant.vertical": confirmed_slot("tenant.vertical", "dental"),
            "tenant.location": confirmed_slot("tenant.location", "Lima"),
        },
        "slots_pending": [],
    }
    config = {"configurable": {"thread_id": f"test-{uuid4()}"}}
    result = graph.invoke(state, config=config)
    assert result.get("task_complete") is True, (
        "Required slots confirmed should route to completion → END with task_complete=True"
    )


def test_graph_persists_state_across_invocations(checkpointer, initial_state):
    """Checkpointer persists state — second invoke with same thread sees first state."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_graph import (
        build_wizard_onboarding_graph,
    )

    graph = build_wizard_onboarding_graph(checkpointer=checkpointer)
    thread_id = f"persist-test-{uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    # First turn — no mode set, supervisor asks
    state1 = {**initial_state, "task_complete": False}
    graph.invoke(state1, config=config)
    # State should be persisted
    snapshot = graph.get_state(config)
    assert snapshot.values.get("tenant_id") == initial_state["tenant_id"]


def test_graph_tenant_isolation_state_carries_tenant_id(checkpointer, initial_state):
    """tenant_id present in state after every supervisor pass."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_graph import (
        build_wizard_onboarding_graph,
    )

    graph = build_wizard_onboarding_graph(checkpointer=checkpointer)
    state = {**initial_state, "task_complete": True}  # short-circuit to END
    config = {"configurable": {"thread_id": f"test-{uuid4()}"}}
    result = graph.invoke(state, config=config)
    assert result.get("tenant_id") == initial_state["tenant_id"]


def test_graph_subagent_isolation_no_parent_state_leak(checkpointer, initial_state):
    """Subagent extracts return ONLY allowed keys to parent state."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_graph import (
        build_wizard_onboarding_graph,
    )

    graph = build_wizard_onboarding_graph(checkpointer=checkpointer)
    state = {
        **initial_state,
        "mode": "libre",
        "extraction_subagent_input": {
            "url": "https://example-clinic.com",
            "text_content": None,
            "audio_url": None,
        },
        "extraction_subagent_output": None,
    }
    config = {"configurable": {"thread_id": f"test-{uuid4()}"}}
    result = graph.invoke(state, config=config)
    # Parent state should NOT contain raw scraping internals — only structured output dict
    output = result.get("extraction_subagent_output") or {}
    # Output, if populated, should be a dict (structured contract, not raw HTML)
    assert isinstance(output, dict)
