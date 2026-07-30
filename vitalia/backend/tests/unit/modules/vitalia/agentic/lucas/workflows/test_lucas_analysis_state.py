"""Unit tests — LucasAnalysisState TypedDict + initial_state factory.

Story: vitalia-copilot-tools-impl T-ag-workflows-2.

Per 03-arch-agentic.md § 2.3 + 03-arch-agentic.md § 3.4:
  - State must carry tenant_id + clinic_id (HIPAA-lite dual filter)
  - Stage queue is ordered + dequeues sequentially
  - stage_recommendations uses operator.add reducer (parallel-safe by design)
  - iterations starts at 0 + bounded by MAX_ITERATIONS_HARD_CAP = 25
  - task_complete sentinel False at start
"""

from __future__ import annotations

from uuid import uuid4

from src.modules.vitalia.agentic.lucas.workflows.lucas_analysis_state import (
    DEFAULT_STAGES,
    MAX_ITERATIONS_HARD_CAP,
    LucasAnalysisState,
    initial_state,
)


def test_default_stages_has_five_canonical_funnel_stages():
    """DEFAULT_STAGES enumerates the 5 design funnel stages in canonical order."""
    assert DEFAULT_STAGES == (
        "attraction",
        "qualification",
        "reservation",
        "adoption",
        "expansion",
    )


def test_max_iterations_hard_cap_is_25_per_tessl_langgraph():
    """Cap matches `tessl__langgraph` recommendation + copilot-resilience.md."""
    assert MAX_ITERATIONS_HARD_CAP == 25


def test_initial_state_carries_mandatory_isolation_keys():
    """initial_state() seeds tenant_id + clinic_id + analysis_date + period."""
    tid = uuid4()
    cid = uuid4()
    state = initial_state(
        tenant_id=tid,
        clinic_id=cid,
        analysis_date="2026-05-18",
        period="2026-05",
    )
    assert state["tenant_id"] == tid
    assert state["clinic_id"] == cid
    assert state["analysis_date"] == "2026-05-18"
    assert state["period"] == "2026-05"


def test_initial_state_stage_queue_default_full():
    """When no stages override, queue = all 5 default stages."""
    state = initial_state(
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        analysis_date="2026-05-18",
        period="2026-05",
    )
    assert tuple(state["stages_to_analyze"]) == DEFAULT_STAGES


def test_initial_state_stage_queue_custom_override():
    """Custom stages tuple is honored."""
    state = initial_state(
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        analysis_date="2026-05-18",
        period="2026-05",
        stages_to_analyze=("attraction", "expansion"),
    )
    assert tuple(state["stages_to_analyze"]) == ("attraction", "expansion")


def test_initial_state_accumulators_empty_at_start():
    """stage_recommendations + cost_accumulated_usd + messages start empty."""
    state = initial_state(
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        analysis_date="2026-05-18",
        period="2026-05",
    )
    assert state["stage_recommendations"] == []
    assert state["messages"] == []
    assert state["cost_accumulated_usd"] == 0.0
    assert state["iterations"] == 0
    assert state["task_complete"] is False
    assert state["attribution_matrix"] is None
    assert state["referrals_leaderboard"] is None
    assert state["current_stage"] is None
    assert state["last_error"] is None


def test_initial_state_returns_lucas_analysis_state_typed_dict():
    """Factory returns a TypedDict instance compatible with LucasAnalysisState."""
    state = initial_state(
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        analysis_date="2026-05-18",
        period="2026-05",
    )
    # TypedDict is a dict at runtime — verify dict-like behavior + key shape.
    assert isinstance(state, dict)
    # Verify all canonical keys present
    canonical_keys = {
        "tenant_id",
        "clinic_id",
        "analysis_date",
        "period",
        "stages_to_analyze",
        "current_stage",
        "stage_recommendations",
        "attribution_matrix",
        "referrals_leaderboard",
        "iterations",
        "task_complete",
        "messages",
        "cost_accumulated_usd",
        "last_error",
    }
    assert canonical_keys.issubset(state.keys())


def test_state_supports_partial_updates_per_langgraph_convention():
    """LucasAnalysisState is total=False — nodes can return partial dicts."""
    # Construct a minimal partial state (LangGraph nodes return such dicts)
    partial: LucasAnalysisState = LucasAnalysisState(iterations=1)
    assert partial.get("iterations") == 1
    # Other keys absent — must NOT raise (total=False permits)
    assert "tenant_id" not in partial
