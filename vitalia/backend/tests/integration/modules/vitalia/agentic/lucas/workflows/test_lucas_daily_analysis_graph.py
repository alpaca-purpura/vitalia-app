"""Integration test — Lucas daily analysis LangGraph ReAct topology.

Story: vitalia-copilot-tools-impl T-ag-workflows-2 (R23 Opus 4.7 production AGENTIC code).

Per 03-arch-agentic.md § 3.4 + 04-validators.yaml::be_test_integration_lucas_graph:
  - StateGraph compiles + accepts CheckpointerProtocol (production swap pending)
  - init → stage_analyze loop (5 stages) → attribution → referrals → finalize → END
  - Per-stage errors → partial-success tolerant (status='skipped_timeout' in DTO)
  - Max-iter guard cap defensive (never triggers in 5-stage happy path)
  - Thread config composes (tenant, clinic, period) for checkpoint isolation

NOTE on checkpointer: `AsyncPostgresSaver` is the production checkpointer per
arch § 7, but `langgraph.checkpoint.postgres` package is not yet installed in
the runtime (Step 0 verified). Tests use `InMemorySaver`; production swap is
a 1-line change at composition root (per D10 cement pattern from
treatment_followup_workflow Wave 2).

Tool handlers are mocked at the boundary (`StageRecommendationHandler` /
`AttributionHandler` / `ReferralsHandler` protocols). Real handlers consume
T-be-services-3 services which write rows to `lucas_recommendations` /
`attribution_matrix_snapshots` / `referrals_leaderboard_snapshots` — those
DB writes are NOT exercised here (covered by T-be-services-3 unit tests).
"""

from __future__ import annotations

import datetime as dt
import inspect
from typing import Any
from uuid import UUID, uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from src.modules.vitalia.agentic.lucas.workflows.lucas_analysis_state import (
    DEFAULT_STAGES,
    initial_state,
)
from src.modules.vitalia.agentic.lucas.workflows.lucas_daily_analysis_graph import (
    build_lucas_daily_analysis_graph,
    build_thread_config,
)

# ──────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────


@pytest.fixture
def tenant_id() -> UUID:
    """Stable tenant_id."""
    return UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def clinic_id() -> UUID:
    """Stable clinic_id."""
    return UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def checkpointer():
    """InMemorySaver for tests; AsyncPostgresSaver for prod per arch § 7."""
    return InMemorySaver()


@pytest.fixture
def call_log() -> list[dict[str, Any]]:
    """Shared list for handler invocation tracking."""
    return []


@pytest.fixture
def stage_handler_happy(call_log):
    """Stage handler that returns a successful DTO every call."""

    async def handler(*, tenant_id, clinic_id, stage, period):
        call_log.append(
            {
                "tool": "compute_stage_recommendation",
                "stage": stage,
                "tenant_id": tenant_id,
                "clinic_id": clinic_id,
                "period": period,
            },
        )
        return {
            "stage": stage,
            "recommendation_text": f"Test recommendation for {stage}.",
            "confidence": 0.78,
            "supporting_data": {"channel_count": 3, "ctr": 0.032},
            "currency": "PEN",
            "status": "active",
        }

    return handler


@pytest.fixture
def attribution_handler_happy(call_log):
    """Attribution handler that returns a populated matrix."""

    async def handler(*, tenant_id, clinic_id, period_start, period_end):
        call_log.append(
            {
                "tool": "compute_attribution_matrix",
                "tenant_id": tenant_id,
                "clinic_id": clinic_id,
                "period_start": period_start,
                "period_end": period_end,
            },
        )
        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "channel_breakdown": {"meta_ads": "1200.00", "organic": "800.00"},
            "total_attributed_revenue": "2000.00",
            "currency": "PEN",
            "snapshot_id": str(uuid4()),
        }

    return handler


@pytest.fixture
def referrals_handler_happy(call_log):
    """Referrals handler that returns a populated leaderboard."""

    async def handler(*, tenant_id, clinic_id, period_start, period_end, limit):
        call_log.append(
            {
                "tool": "compute_referrals_leaderboard",
                "tenant_id": tenant_id,
                "clinic_id": clinic_id,
                "limit": limit,
            },
        )
        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "top_referrers": [
                {
                    "referrer_id": str(uuid4()),
                    "referral_count": 8,
                    "converted_count": 5,
                    "rank": 1,
                },
                {
                    "referrer_id": str(uuid4()),
                    "referral_count": 4,
                    "converted_count": 2,
                    "rank": 2,
                },
            ],
            "total_referrals": 12,
            "total_converted": 7,
            "snapshot_id": str(uuid4()),
        }

    return handler


@pytest.fixture
def graph_happy(
    stage_handler_happy,
    attribution_handler_happy,
    referrals_handler_happy,
    checkpointer,
):
    """Compiled graph with happy-path handlers."""
    return build_lucas_daily_analysis_graph(
        stage_handler=stage_handler_happy,
        attribution_handler=attribution_handler_happy,
        referrals_handler=referrals_handler_happy,
        checkpointer=checkpointer,
    )


# ──────────────────────────────────────────────────────────────────────────
# Smoke / compile tests
# ──────────────────────────────────────────────────────────────────────────


def test_graph_compiles_with_checkpointer(graph_happy):
    """build_lucas_daily_analysis_graph returns a compiled CompiledStateGraph."""
    assert graph_happy is not None
    # CompiledStateGraph exposes `ainvoke`
    assert callable(graph_happy.ainvoke)


def test_thread_config_composes_tenant_clinic_period(tenant_id, clinic_id):
    """build_thread_config composes deterministic thread_id from (tenant, clinic, period)."""
    cfg = build_thread_config(tenant_id=tenant_id, clinic_id=clinic_id, period="2026-05")
    assert "configurable" in cfg
    thread_id = cfg["configurable"]["thread_id"]
    assert str(tenant_id) in thread_id
    assert str(clinic_id) in thread_id
    assert "2026-05" in thread_id


# ──────────────────────────────────────────────────────────────────────────
# Happy path — graph runs end-to-end through all nodes
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_graph_runs_through_init_to_finalize_happy(
    graph_happy,
    tenant_id,
    clinic_id,
    call_log,
):
    """End-to-end happy path: init → 5 stages → attribution → referrals → finalize."""
    seed = initial_state(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        analysis_date="2026-05-18",
        period="2026-05",
    )
    cfg = build_thread_config(tenant_id=tenant_id, clinic_id=clinic_id, period="2026-05")

    final_state = await graph_happy.ainvoke(seed, config=cfg)

    # Stages: 5 invocations of stage handler
    stage_calls = [c for c in call_log if c["tool"] == "compute_stage_recommendation"]
    assert len(stage_calls) == 5, f"Expected 5 stage invocations, got {len(stage_calls)}"

    # Stage order matches DEFAULT_STAGES
    stage_order = [c["stage"] for c in stage_calls]
    assert tuple(stage_order) == DEFAULT_STAGES

    # Attribution + referrals each fired once
    assert sum(1 for c in call_log if c["tool"] == "compute_attribution_matrix") == 1
    assert sum(1 for c in call_log if c["tool"] == "compute_referrals_leaderboard") == 1

    # Tenant + clinic propagated to every handler
    for call in call_log:
        assert call["tenant_id"] == tenant_id
        assert call["clinic_id"] == clinic_id

    # State outputs
    assert len(final_state["stage_recommendations"]) == 5
    assert final_state["attribution_matrix"] is not None
    assert final_state["referrals_leaderboard"] is not None
    assert final_state["task_complete"] is True
    assert final_state["stages_to_analyze"] == []  # queue drained


@pytest.mark.asyncio
async def test_iterations_bounded_within_cap(graph_happy, tenant_id, clinic_id):
    """Total node invocations stay well below MAX_ITERATIONS_HARD_CAP (25)."""
    from src.modules.vitalia.agentic.lucas.workflows.lucas_analysis_state import (
        MAX_ITERATIONS_HARD_CAP,
    )

    seed = initial_state(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        analysis_date="2026-05-18",
        period="2026-05",
    )
    cfg = build_thread_config(tenant_id=tenant_id, clinic_id=clinic_id, period="2026-05")
    final_state = await graph_happy.ainvoke(seed, config=cfg)

    # init(1) + 5 stage_analyze(5) + attribution(1) + referrals(1) + finalize(1) = 9
    iters = int(final_state["iterations"])
    assert iters < MAX_ITERATIONS_HARD_CAP
    assert iters >= 9, f"Expected ≥9 iterations in happy path, got {iters}"


# ──────────────────────────────────────────────────────────────────────────
# Partial-success tolerance — per-stage handler raises → graph continues
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stage_handler_failure_does_not_break_graph(
    attribution_handler_happy,
    referrals_handler_happy,
    checkpointer,
    tenant_id,
    clinic_id,
):
    """Per-stage exception caught → DTO synthesised → run continues to next stage."""
    call_count = {"n": 0}

    async def flaky_stage_handler(*, tenant_id, clinic_id, stage, period):
        call_count["n"] += 1
        # Fail the 2nd stage (qualification)
        if stage == "qualification":
            raise TimeoutError("Simulated LLM timeout")
        return {
            "stage": stage,
            "recommendation_text": f"OK for {stage}",
            "confidence": 0.8,
            "supporting_data": {},
            "currency": "PEN",
            "status": "active",
        }

    graph = build_lucas_daily_analysis_graph(
        stage_handler=flaky_stage_handler,
        attribution_handler=attribution_handler_happy,
        referrals_handler=referrals_handler_happy,
        checkpointer=checkpointer,
    )
    seed = initial_state(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        analysis_date="2026-05-18",
        period="2026-05",
    )
    cfg = build_thread_config(tenant_id=tenant_id, clinic_id=clinic_id, period="2026-05")

    final_state = await graph.ainvoke(seed, config=cfg)

    # All 5 stages attempted
    assert call_count["n"] == 5
    # All 5 recommendations present (the failed one synthesised as skipped_timeout)
    recs = final_state["stage_recommendations"]
    assert len(recs) == 5
    # Find the failed stage entry
    failed = [r for r in recs if r["stage"] == "qualification"]
    assert len(failed) == 1
    assert failed[0]["status"] == "skipped_timeout"
    # Other stages succeeded
    others = [r for r in recs if r["stage"] != "qualification"]
    assert all(r["status"] == "active" for r in others)
    # Run still completed
    assert final_state["task_complete"] is True


@pytest.mark.asyncio
async def test_attribution_handler_failure_synthesises_skipped(
    stage_handler_happy,
    referrals_handler_happy,
    checkpointer,
    tenant_id,
    clinic_id,
):
    """Attribution exception → DTO synthesised with status='skipped_timeout'; run continues."""

    async def broken_attribution(*, tenant_id, clinic_id, period_start, period_end):
        raise RuntimeError("Engine analytics down")

    graph = build_lucas_daily_analysis_graph(
        stage_handler=stage_handler_happy,
        attribution_handler=broken_attribution,
        referrals_handler=referrals_handler_happy,
        checkpointer=checkpointer,
    )
    seed = initial_state(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        analysis_date="2026-05-18",
        period="2026-05",
    )
    cfg = build_thread_config(tenant_id=tenant_id, clinic_id=clinic_id, period="2026-05")
    final_state = await graph.ainvoke(seed, config=cfg)

    assert final_state["attribution_matrix"] is not None
    assert final_state["attribution_matrix"]["status"] == "skipped_timeout"
    # Referrals still ran (downstream of attribution)
    assert final_state["referrals_leaderboard"] is not None
    assert final_state["task_complete"] is True


# ──────────────────────────────────────────────────────────────────────────
# Period bounds + state schema validation
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_period_bounds_passed_to_attribution(
    graph_happy,
    tenant_id,
    clinic_id,
    call_log,
):
    """Attribution handler receives (period_start, period_end) as inclusive month bounds."""
    seed = initial_state(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        analysis_date="2026-05-18",
        period="2026-05",
    )
    cfg = build_thread_config(tenant_id=tenant_id, clinic_id=clinic_id, period="2026-05")
    await graph_happy.ainvoke(seed, config=cfg)

    attr_call = next(c for c in call_log if c["tool"] == "compute_attribution_matrix")
    assert attr_call["period_start"] == dt.date(2026, 5, 1)
    assert attr_call["period_end"] == dt.date(2026, 5, 31)


def test_state_schema_carries_mandatory_keys(tenant_id, clinic_id):
    """initial_state() seeds the 5 mandatory keys + queue + reducers."""
    seed = initial_state(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        analysis_date="2026-05-18",
        period="2026-05",
    )
    for key in ("tenant_id", "clinic_id", "analysis_date", "period", "stages_to_analyze"):
        assert key in seed
        assert seed[key] is not None

    # Stage queue is full at start
    assert tuple(seed["stages_to_analyze"]) == DEFAULT_STAGES
    # Accumulators initialised empty
    assert seed["stage_recommendations"] == []
    assert seed["iterations"] == 0
    assert seed["task_complete"] is False


# ──────────────────────────────────────────────────────────────────────────
# Defensive: graph signature contract surface
# ──────────────────────────────────────────────────────────────────────────


def test_build_lucas_daily_analysis_graph_signature():
    """Public factory exposes stable kwargs (DI contract)."""
    sig = inspect.signature(build_lucas_daily_analysis_graph)
    params = set(sig.parameters.keys())
    expected = {
        "stage_handler",
        "attribution_handler",
        "referrals_handler",
        "checkpointer",
        "referrals_limit",
    }
    assert expected.issubset(params), f"build_lucas_daily_analysis_graph missing kwargs: {expected - params}"
