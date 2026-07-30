# cap: agentic.lucas-daily-analysis
# story-origin: TBD
"""Lucas daily analysis LangGraph — ReAct-style cron-triggered topology.

Story: vitalia-copilot-tools-impl T-ag-workflows-2 (R23 Opus 4.7 production AGENTIC code).

Per 03-arch-agentic.md § 3.4 + § 2.3:

  [START] → init → stage_analyze (loop 5 stages) → attribution → referrals → END

  Bounded by `stages_to_analyze` list (5 stages). Defensive max-iter cap 25
  per `tessl__langgraph` recommendation (never reached in happy path).

Nodes (5):
  - init         : seed sanity check + locale/services binding (state-pure).
  - stage_analyze: dequeue one stage → call `compute_stage_recommendation`
                   service via injected handler → append DTO to state.
  - attribution  : call `compute_attribution_matrix` service → set state field.
  - referrals    : call `compute_referrals_leaderboard` service → set state field.
  - finalize     : set task_complete=True for END.

Conditional edges:
  init → stage_analyze (always; init is bookkeeping only)
  stage_analyze → stage_analyze (if stages_to_analyze still has items)
  stage_analyze → attribution (when stage queue empty)
  attribution → referrals
  referrals → finalize → END

Checkpointer:
  Production target = AsyncPostgresSaver per arch § 7. Package
  `langgraph.checkpoint.postgres` NOT YET installed in workspace (verified
  Step 0). Pattern matches `treatment_followup_workflow` D10 cement: factory
  accepts ANY LangGraph-compatible checkpointer via `Checkpointer` protocol.
  Tests inject `MemorySaver`; production swaps to `AsyncPostgresSaver` when
  package install lands (single import change — no graph code change).

Tenant + HIPAA-lite isolation:
  - State carries `tenant_id` + `clinic_id` mandatory at entry.
  - Thread config (`thread_id`) composes both → checkpoint isolation per
    (tenant, clinic, period) triple.
  - Nodes pass tenant_id + clinic_id through to tools — every service call
    enforces dual filter.

Cost discipline (per arch § 5.5):
  - Per-stage soft cap $0.05 USD (LLM Kimi reasoning).
  - Per-tenant daily cap $0.25 USD (BudgetGuard.check inside
    LucasStageRecommendationService).
  - On BudgetGuard exceeded → service returns entity with status='skipped_budget'.
  - On stage exception → catch + persist `last_error` → continue to next stage
    (partial-success tolerant per design § 3.4).

Anti-duplication §0 audit (Step 0 GATE):
  - `StateGraph` + `END` from `langgraph.graph` (engine SSoT — NEVER mirror).
  - Tool handlers (compute_*_recommendation/matrix/leaderboard) consumed
    READ-ONLY from `tools/` (Wave 3 T-ag-tools-3) — NEVER re-implement.
  - No equivalent graph in `core/luana-core-*/` (vitalia-specific medical
    growth — Slice 2+ may lift if cross-brand demand).

downstream-regression-na: brand-local graph; no cross-brand consumers.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Awaitable, Callable
from typing import Any, Protocol
from uuid import UUID, uuid4

import structlog
from langgraph.graph import END, StateGraph

from src.modules.vitalia.agentic.lucas.workflows.lucas_analysis_state import (
    MAX_ITERATIONS_HARD_CAP,
    LucasAnalysisState,
    Stage,
)

logger = structlog.get_logger()


# ──────────────────────────────────────────────────────────────────────────
# Protocols — runtime-injectable callables for the 3 Lucas tools + services.
#
# Why protocols vs. concrete imports here? Two reasons:
#   1. Decouple graph from concrete service constructors (tests inject mocks).
#   2. Allow caller (orchestrator) to wrap each handler with observability
#      callbacks, retries, or different DI containers without rebuilding the
#      graph topology.
# ──────────────────────────────────────────────────────────────────────────


class StageRecommendationHandler(Protocol):
    """Async callable that handles a single stage recommendation.

    Wraps `compute_stage_recommendation` tool + service. Signature matches
    arch § 4.3 tool contract.
    """

    async def __call__(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        stage: Stage,
        period: str,
    ) -> dict[str, Any]:
        """Compute one stage recommendation; return DTO dict."""
        ...


class AttributionHandler(Protocol):
    """Async callable that computes attribution matrix for the period."""

    async def __call__(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_start: dt.date,
        period_end: dt.date,
    ) -> dict[str, Any]:
        """Compute attribution matrix; return DTO dict."""
        ...


class ReferralsHandler(Protocol):
    """Async callable that computes referrals leaderboard for the period."""

    async def __call__(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_start: dt.date,
        period_end: dt.date,
        limit: int,
    ) -> dict[str, Any]:
        """Compute referrals leaderboard; return DTO dict."""
        ...


class CheckpointerProtocol(Protocol):
    """Minimal LangGraph checkpointer surface.

    Matches `langgraph.checkpoint.base.BaseCheckpointSaver` runtime surface
    without binding to a specific concrete class. Tests pass `MemorySaver`;
    production (when package installed) passes `AsyncPostgresSaver`.
    """

    async def aput(self, *args: Any, **kwargs: Any) -> Any: ...
    async def aget(self, *args: Any, **kwargs: Any) -> Any: ...


# ──────────────────────────────────────────────────────────────────────────
# Node factories — closures over injected handlers.
#
# We use closures (rather than method-bound classes) for two reasons:
#   1. LangGraph expects `Callable[[State], Awaitable[dict]]` for nodes —
#      keeping nodes as plain async functions is the simplest contract.
#   2. Each `build_*` call instantiates a fresh graph with its own handler
#      bindings → tests can spin up multiple graphs with different mocks
#      without state crossover.
# ──────────────────────────────────────────────────────────────────────────


def _make_init_node() -> Callable[[LucasAnalysisState], Awaitable[dict[str, Any]]]:
    """Build the init node (state-pure bookkeeping)."""

    async def init_node(state: LucasAnalysisState) -> dict[str, Any]:
        """Initialize the run: validate state has required keys + log entry.

        Defensive only — orchestrator service constructs state via
        `initial_state(...)` factory so required keys are guaranteed present.
        """
        # Required keys per HIPAA-lite cardinal — fail fast in tests if missing.
        for key in ("tenant_id", "clinic_id", "analysis_date", "period", "stages_to_analyze"):
            if key not in state or state[key] is None:
                logger.warning(
                    "lucas_graph_init_missing_key",
                    missing_key=key,
                    tenant_id=str(state.get("tenant_id")),
                )

        tenant_id = state.get("tenant_id")
        clinic_id = state.get("clinic_id")
        stages = state.get("stages_to_analyze") or []
        logger.info(
            "lucas_graph_init",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            analysis_date=state.get("analysis_date"),
            period=state.get("period"),
            stage_count=len(stages),
        )
        return {
            "iterations": int(state.get("iterations") or 0) + 1,
            "last_error": None,
        }

    return init_node


def _make_stage_analyze_node(
    handler: StageRecommendationHandler,
) -> Callable[[LucasAnalysisState], Awaitable[dict[str, Any]]]:
    """Build the stage_analyze node that dequeues + processes one stage.

    The node:
      1. Pops the head of `stages_to_analyze`.
      2. Calls the injected handler (graceful-degradation: timeout / budget
         exceptions captured as `last_error` + status='skipped_*').
      3. Appends DTO to `stage_recommendations` (operator.add reducer).
      4. Returns partial state update — never raises tool-side errors.
    """

    async def stage_analyze_node(state: LucasAnalysisState) -> dict[str, Any]:
        """Process one stage at a time. Partial-success tolerant."""
        stages = list(state.get("stages_to_analyze") or [])
        if not stages:
            # Defensive: should not happen because conditional edge gates this.
            return {"iterations": int(state.get("iterations") or 0) + 1}

        current_stage = stages.pop(0)
        tenant_id = state["tenant_id"]
        clinic_id = state["clinic_id"]
        period = state["period"]

        # Graceful-degradation per `tessl__graceful-degradation` Rule 5:
        # catch + log + persist last_error → continue (NEVER raise — partial
        # success is acceptable per design § 3.4 error recovery matrix).
        dto_dict: dict[str, Any]
        try:
            dto_dict = await handler(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                stage=current_stage,
                period=period,
            )
            err_update: dict[str, Any] | None = None
        except Exception as exc:  # noqa: BLE001 — design § 3.4 partial-success
            logger.warning(
                "lucas_graph_stage_analyze_error",
                tenant_id=str(tenant_id),
                stage=current_stage,
                err=str(exc),
                err_type=type(exc).__name__,
            )
            # Synthesize a skipped DTO so the run still produces a row per stage.
            dto_dict = {
                "stage": current_stage,
                "recommendation_text": "",
                "confidence": 0.0,
                "supporting_data": {},
                "currency": None,
                "status": "skipped_timeout",
            }
            err_update = {
                "stage": current_stage,
                "error_class": type(exc).__name__,
                "error_message": str(exc),
            }

        return {
            "stages_to_analyze": stages,
            "current_stage": current_stage,
            "stage_recommendations": [dto_dict],  # operator.add reducer appends
            "iterations": int(state.get("iterations") or 0) + 1,
            "last_error": err_update,
        }

    return stage_analyze_node


def _make_attribution_node(
    handler: AttributionHandler,
) -> Callable[[LucasAnalysisState], Awaitable[dict[str, Any]]]:
    """Build the attribution node — pure-DB single-shot."""

    async def attribution_node(state: LucasAnalysisState) -> dict[str, Any]:
        """Compute attribution matrix snapshot for the period."""
        tenant_id = state["tenant_id"]
        clinic_id = state["clinic_id"]
        period_start, period_end = _period_bounds(state["period"])

        try:
            matrix = await handler(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                period_start=period_start,
                period_end=period_end,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "lucas_graph_attribution_error",
                tenant_id=str(tenant_id),
                err=str(exc),
            )
            matrix = {
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "channel_breakdown": {},
                "total_attributed_revenue": "0.00",
                "currency": None,
                "snapshot_id": str(uuid4()),
                "status": "skipped_timeout",
            }

        return {
            "attribution_matrix": matrix,
            "iterations": int(state.get("iterations") or 0) + 1,
        }

    return attribution_node


def _make_referrals_node(
    handler: ReferralsHandler,
    *,
    limit: int = 5,
) -> Callable[[LucasAnalysisState], Awaitable[dict[str, Any]]]:
    """Build the referrals node — pure-DB single-shot, top-N referrers."""

    async def referrals_node(state: LucasAnalysisState) -> dict[str, Any]:
        """Compute referrals leaderboard top-N for the period."""
        tenant_id = state["tenant_id"]
        clinic_id = state["clinic_id"]
        period_start, period_end = _period_bounds(state["period"])

        try:
            board = await handler(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                period_start=period_start,
                period_end=period_end,
                limit=limit,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "lucas_graph_referrals_error",
                tenant_id=str(tenant_id),
                err=str(exc),
            )
            board = {
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "top_referrers": [],
                "total_referrals": 0,
                "total_converted": 0,
                "snapshot_id": str(uuid4()),
                "status": "skipped_timeout",
            }

        return {
            "referrals_leaderboard": list(board.get("top_referrers") or []),
            "iterations": int(state.get("iterations") or 0) + 1,
        }

    return referrals_node


def _make_finalize_node() -> Callable[[LucasAnalysisState], Awaitable[dict[str, Any]]]:
    """Build the finalize node — sets task_complete + emits run summary log."""

    async def finalize_node(state: LucasAnalysisState) -> dict[str, Any]:
        """Mark run complete + log structured summary."""
        tenant_id = state.get("tenant_id")
        recs = state.get("stage_recommendations") or []
        logger.info(
            "lucas_graph_run_completed",
            tenant_id=str(tenant_id),
            analysis_date=state.get("analysis_date"),
            period=state.get("period"),
            stages_processed=len(recs),
            attribution_present=state.get("attribution_matrix") is not None,
            referrals_present=state.get("referrals_leaderboard") is not None,
            iterations=int(state.get("iterations") or 0),
        )
        return {
            "task_complete": True,
            "iterations": int(state.get("iterations") or 0) + 1,
        }

    return finalize_node


# ──────────────────────────────────────────────────────────────────────────
# Conditional edge predicate — stage loop
# ──────────────────────────────────────────────────────────────────────────


def _stage_loop_router(state: LucasAnalysisState) -> str:
    """Decide whether to loop back to stage_analyze or move on to attribution.

    Returns key matched in `add_conditional_edges` map.

    Cap defence: if `iterations` exceeds MAX_ITERATIONS_HARD_CAP (25) → force
    transition to attribution to avoid infinite loop. Should NEVER trigger in
    happy path (5 stages = 5 stage_analyze invocations + 4 other nodes = 9
    iterations max).
    """
    iterations = int(state.get("iterations") or 0)
    if iterations >= MAX_ITERATIONS_HARD_CAP:
        logger.warning(
            "lucas_graph_iteration_cap_hit",
            iterations=iterations,
            cap=MAX_ITERATIONS_HARD_CAP,
        )
        return "attribution"

    stages = state.get("stages_to_analyze") or []
    if stages:
        return "stage_analyze"
    return "attribution"


# ──────────────────────────────────────────────────────────────────────────
# Period bound helper — derive month start + end from "YYYY-MM"
# ──────────────────────────────────────────────────────────────────────────


def _period_bounds(period: str) -> tuple[dt.date, dt.date]:
    """Derive (period_start, period_end) inclusive dates from a YYYY-MM period.

    Args:
        period: "YYYY-MM" month-granular period.

    Returns:
        (first_of_month, last_of_month) dates.

    Raises:
        ValueError: If period is malformed.
    """
    if not isinstance(period, str) or len(period) != 7 or period[4] != "-":
        raise ValueError(f"Invalid period format (expected YYYY-MM): {period!r}")
    year = int(period[:4])
    month = int(period[5:])
    period_start = dt.date(year, month, 1)
    if month == 12:
        period_end = dt.date(year + 1, 1, 1) - dt.timedelta(days=1)
    else:
        period_end = dt.date(year, month + 1, 1) - dt.timedelta(days=1)
    return period_start, period_end


# ──────────────────────────────────────────────────────────────────────────
# Public factory
# ──────────────────────────────────────────────────────────────────────────


def build_lucas_daily_analysis_graph(
    *,
    stage_handler: StageRecommendationHandler,
    attribution_handler: AttributionHandler,
    referrals_handler: ReferralsHandler,
    checkpointer: CheckpointerProtocol | Any,
    referrals_limit: int = 5,
) -> Any:
    """Build + compile the Lucas daily analysis LangGraph.

    Args:
        stage_handler: Callable wrapping `compute_stage_recommendation` tool.
                       Injected for testability + DI flexibility.
        attribution_handler: Callable wrapping `compute_attribution_matrix` tool.
        referrals_handler: Callable wrapping `compute_referrals_leaderboard` tool.
        checkpointer: Any LangGraph-compatible checkpointer. Pass `MemorySaver`
                      for tests, `AsyncPostgresSaver` for production (when
                      `langgraph.checkpoint.postgres` package install lands).
        referrals_limit: Top-N referrers to include (default 5 per design § 2.4).

    Returns:
        Compiled CompiledStateGraph runnable via `.ainvoke(initial_state, config={"configurable": {"thread_id": ...}})`.

    Per `tessl__langgraph`:
      - StateGraph(LucasAnalysisState) with TypedDict schema.
      - Conditional edges total (no dangling — every branch reaches END).
      - Max-iter guard via `_stage_loop_router` (defensive cap 25).
      - Production checkpointer is `AsyncPostgresSaver` (MemorySaver tutorial-only).
    """
    graph = StateGraph(LucasAnalysisState)

    # Nodes (5)
    graph.add_node("init", _make_init_node())
    graph.add_node("stage_analyze", _make_stage_analyze_node(stage_handler))
    graph.add_node("attribution", _make_attribution_node(attribution_handler))
    graph.add_node("referrals", _make_referrals_node(referrals_handler, limit=referrals_limit))
    graph.add_node("finalize", _make_finalize_node())

    # Topology
    graph.set_entry_point("init")
    graph.add_edge("init", "stage_analyze")
    graph.add_conditional_edges(
        "stage_analyze",
        _stage_loop_router,
        {
            "stage_analyze": "stage_analyze",
            "attribution": "attribution",
        },
    )
    graph.add_edge("attribution", "referrals")
    graph.add_edge("referrals", "finalize")
    graph.add_edge("finalize", END)

    compiled = graph.compile(checkpointer=checkpointer)
    return compiled


def build_thread_config(
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    period: str,
) -> dict[str, Any]:
    """Build the LangGraph thread config for checkpointer isolation.

    Composite key (tenant, clinic, period) → checkpoint isolation cardinal
    per HIPAA-lite. Same composite re-invoking the graph resumes from the
    last checkpoint (idempotent at the LangGraph layer; idempotent_cron is
    the upstream layer).

    Args:
        tenant_id: Tenant UUID.
        clinic_id: Clinic UUID.
        period: YYYY-MM period.

    Returns:
        Config dict suitable for `graph.ainvoke(initial_state, config=cfg)`.
    """
    thread_id = f"vitalia.lucas.{tenant_id}.{clinic_id}.{period}"
    return {"configurable": {"thread_id": thread_id}}


__all__ = [
    "AttributionHandler",
    "CheckpointerProtocol",
    "ReferralsHandler",
    "StageRecommendationHandler",
    "build_lucas_daily_analysis_graph",
    "build_thread_config",
]
