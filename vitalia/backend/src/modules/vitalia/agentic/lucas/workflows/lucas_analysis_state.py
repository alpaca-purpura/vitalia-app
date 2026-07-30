# cap: agentic.lucas-daily-analysis
# story-origin: TBD
"""Lucas daily analysis state schema — LangGraph TypedDict.

Story: vitalia-copilot-tools-impl T-ag-workflows-2 (R23 Opus 4.7 production AGENTIC code).

Per 03-arch-agentic.md § 2.3 + § 3.4 + § 5.3:

  - `tenant_id` + `clinic_id` MANDATORY (HIPAA-lite dual filter — every state carries it).
  - `analysis_date` (YYYY-MM-DD) is TZ-aware (computed from `TenantLocale.timezone` at
    orchestrator entry — NEVER `datetime.utcnow()` for tenant-facing date).
  - `period` (YYYY-MM) is month-granularity, TZ-neutral at storage.
  - `iterations` for max-iter guard (bounded naturally by `stages_to_analyze` list,
    cap 25 defensive per `tessl__langgraph`).
  - Per-stage outputs use `operator.add` reducer so parallel `Send` writes are safe
    (LangGraph 2.0 deterministic merge).
  - `messages` carries optional structured chat-like records (mostly empty for cron-only
    Slice 1; reserved for chat-invokable Slice 3 per design Q2 default).

Cache slot architecture (5.3) reference (NOT stored in state — composed by
`LucasAnalysisPromptCompiler` from prompts/persona files):
  Slot 1 — Lucas persona  (cacheable per-brand, 1h TTL)
  Slot 2 — Stage frame    (cacheable per-stage, 1h TTL)
  Slot 3 — Analysis ctx   (variable: period + tenant aggregates — NEVER cached)

HIPAA-lite invariants (per `vitalia/.claude/rules/hipaa-lite.md`):
  - State holds analytics aggregates only — NO PHI.
  - `top_referrers` rows use `referrer_id` (UUID) only.
  - `clinic_id` in every state dict.

Anti-duplication §0 audit (Step 0 GATE):
  - `TypedDict` from stdlib `typing` (Python 3.12 native).
  - `add_messages` reducer from `langgraph.graph.message` (engine SSoT — NEVER mirror).
  - `operator.add` from stdlib for list accumulators.
  - No equivalent state schema in `core/luana-core-*/` (Lucas vertical-medical
    daily growth analytics is brand-specific — Slice 2+ may lift if cross-brand demand).

downstream-regression-na: brand-local state schema; no cross-brand consumers.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph.message import add_messages

# ──────────────────────────────────────────────────────────────────────────
# Stage literal — matches `ComputeStageRecommendationInput.stage` Literal in
# `tools/compute_stage_recommendation.py` (T-ag-tools-3) to keep contracts
# byte-equal across handoffs.
#
# Note: this Literal uses the DESIGN funnel names (attraction →
# qualification → reservation → adoption → expansion per
# `prompts/lucas_stage_reasoning_frame.md` § "5 etapas canónicas"). The
# `agentic/lucas/domain/enums/stage.py` StageEnum uses different domain
# names (attraction/capture/nurture/opportunity/retention) aligned with
# engine `analytics_engine` ChannelRegistry — those are the "what data we
# pull" labels, while these Literals are the "what the LLM reasons about"
# labels. Both contracts coexist; the orchestrator passes the design
# Literal to the tool and the service maps internally if needed.
# ──────────────────────────────────────────────────────────────────────────

Stage = Literal["attraction", "qualification", "reservation", "adoption", "expansion"]
"""Funnel stages Lucas reasons about. Matches tool Literal contract."""


DEFAULT_STAGES: tuple[Stage, ...] = (
    "attraction",
    "qualification",
    "reservation",
    "adoption",
    "expansion",
)
"""Default ordered stage sequence per design § 1.5 + arch § 3.4."""


class LucasAnalysisState(TypedDict, total=False):
    """Lucas daily analysis state — LangGraph TypedDict.

    `total=False` allows partial updates per LangGraph node return convention
    (nodes return only the keys they modify; missing keys remain as-is).

    Mandatory at graph entry (built by `LucasOrchestratorService.run_daily_analysis`):
        tenant_id, clinic_id, analysis_date, period, stages_to_analyze
    """

    # ── Tenant + clinic isolation (HIPAA-lite dual filter — CARDINAL) ─────
    tenant_id: Any  # uuid.UUID — TypedDict tolerant
    clinic_id: Any
    """Mandatory per `vitalia/.claude/rules/hipaa-lite.md` § Tenant isolation."""

    # ── Run identity ──────────────────────────────────────────────────────
    analysis_date: str  # YYYY-MM-DD, TZ-aware from TenantLocale
    """TZ-aware tenant-local date string. Computed at orchestrator entry via
    `_compute_run_date(locale.timezone)` — NEVER `datetime.utcnow().date()`."""

    period: str  # YYYY-MM, month-granularity
    """Period for which Lucas reasons (month-granular, TZ-neutral at storage)."""

    # ── Stage iteration plan ──────────────────────────────────────────────
    stages_to_analyze: list[Stage]
    """Ordered queue of stages yet to be analyzed. Graph dequeues one per
    `stage_analyze` node invocation; loop exits when empty."""

    current_stage: Stage | None
    """Stage currently under analysis (set when dequeued; cleared after persist)."""

    # ── Per-stage outputs (parallel-safe reducer) ─────────────────────────
    stage_recommendations: Annotated[list[dict[str, Any]], operator.add]
    """Accumulated per-stage `RecommendationDTO.model_dump()` outputs.

    `operator.add` reducer is parallel-safe per LangGraph 2.0 deterministic
    merge — even though Lucas processes stages sequentially (cost discipline,
    Kimi reasoning Slot 1+2 cacheable), the reducer is declared defensively
    in case future Slice 2 fans out via `Send`.
    """

    # ── Attribution + referrals (single-shot, pure DB) ────────────────────
    attribution_matrix: dict[str, Any] | None
    """`MatrixDTO.model_dump()` snapshot; None if not yet computed."""

    referrals_leaderboard: list[dict[str, Any]] | None
    """`LeaderboardDTO.top_referrers` snapshot; None if not yet computed."""

    # ── Control flow ──────────────────────────────────────────────────────
    iterations: int
    """Defensive max-iter guard (cap 25 per `tessl__langgraph`). Naturally bounded
    by `stages_to_analyze` length (5) + attribution + referrals = 7 max iterations
    in happy path."""

    task_complete: bool
    """Sentinel set by final node before END."""

    # ── Conversation (reserved for Slice 3 chat-invokable Lucas) ──────────
    messages: Annotated[list[Any], add_messages]
    """Optional structured chat records. Cron-only Slice 1 leaves this empty
    (per design Q2 default). Reserved for Slice 3 chat-invokable Lucas."""

    # ── Cost + observability ──────────────────────────────────────────────
    cost_accumulated_usd: float
    """Accumulates per-stage LLM cost. Soft cap $0.25/tenant/run per design § 5.5."""

    last_error: dict[str, Any] | None
    """Latest per-stage error captured (status='skipped_timeout' or 'skipped_budget').
    Cleared at successful stage completion. NEVER raised — graph is partial-success
    tolerant per design § 3.4 error recovery matrix."""


# Defensive cap matches `tessl__langgraph` recommendation + `copilot-resilience.md`
MAX_ITERATIONS_HARD_CAP: int = 25


def initial_state(
    *,
    tenant_id: Any,
    clinic_id: Any,
    analysis_date: str,
    period: str,
    stages_to_analyze: tuple[Stage, ...] = DEFAULT_STAGES,
) -> LucasAnalysisState:
    """Build the seed state for a Lucas daily analysis run.

    Args:
        tenant_id: Tenant UUID — MUST be passed by caller (orchestrator).
        clinic_id: Clinic UUID — HIPAA-lite dual filter.
        analysis_date: YYYY-MM-DD tenant-local date (computed by orchestrator
            from `TenantLocale.timezone` — NEVER `datetime.utcnow().date()`).
        period: YYYY-MM month-granular period.
        stages_to_analyze: Ordered stages. Defaults to all 5 canonical stages.

    Returns:
        LucasAnalysisState dict ready for `graph.ainvoke(initial_state)`.
    """
    return LucasAnalysisState(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        analysis_date=analysis_date,
        period=period,
        stages_to_analyze=list(stages_to_analyze),
        current_stage=None,
        stage_recommendations=[],
        attribution_matrix=None,
        referrals_leaderboard=None,
        iterations=0,
        task_complete=False,
        messages=[],
        cost_accumulated_usd=0.0,
        last_error=None,
    )


__all__ = [
    "DEFAULT_STAGES",
    "MAX_ITERATIONS_HARD_CAP",
    "LucasAnalysisState",
    "Stage",
    "initial_state",
]
