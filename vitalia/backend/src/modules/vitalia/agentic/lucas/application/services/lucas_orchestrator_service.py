# cap: agentic.lucas-daily-analysis
# story-origin: TBD
"""Lucas orchestrator service — high-level entry for daily analysis runs.

Story: vitalia-copilot-tools-impl T-ag-workflows-2 (R23 Opus 4.7 production AGENTIC code).

Per 03-arch-agentic.md § 3.4:

  Orchestrator entry-point service that:
    1. Computes TZ-aware `analysis_date` (YYYY-MM-DD) from `TenantLocale.timezone`.
    2. Computes month-granular `period` (YYYY-MM) — also TZ-aware.
    3. Builds the LangGraph (`build_lucas_daily_analysis_graph`) with injected
       tool handlers + checkpointer.
    4. Invokes the graph via `ainvoke(initial_state, config=thread_config)`.
    5. Returns the final state for caller (cron job) inspection / logging.

TZ-aware date computation (CARDINAL — per `.claude/rules/master-data.md`):
  - `analysis_date` MUST come from `TenantLocale.timezone` — NEVER
    `datetime.utcnow().date()` (would label runs with wrong calendar date
    for tenants in non-UTC timezones — Lima operator at 23:00 local UTC-5
    would see "today's run" labelled as tomorrow if we used UTC).
  - `period` derived from `analysis_date.strftime("%Y-%m")` (same TZ).
  - Internal timestamps still UTC (DateTime with timezone=True per master-data
    rule).

HIPAA-lite invariants:
  - Tenant + clinic_id flow through every layer.
  - No PHI processed in graph state.
  - Audit log written by individual services (T-be-services-3) — orchestrator
    does NOT duplicate audit writes.

Idempotency:
  - Orchestrator service itself is NOT idempotent — repeated calls produce
    independent runs (graph thread_config differs per checkpoint).
  - Idempotency is enforced ONE LEVEL UP at the cron job via `@idempotent_cron`
    decorator (`_shared/workers/base.py`). The cron's Redis key (composed
    from `job_id` per current `_shared/workers/base.py` impl) prevents
    double-fire on retry bursts within `idem_ttl_seconds` window.
  - The smoke test for this story validates that re-invoking the orchestrator
    with the same (tenant_id, period) DOES produce a fresh run (NOT idempotent
    at this layer) — idempotency belongs to the cron wrapper, not here. This
    is intentional separation per SRP.

Anti-duplication §0 audit (Step 0 GATE):
  - LangGraph factory `build_lucas_daily_analysis_graph` consumed from sibling
    workflows module (this brand) — not mirrored.
  - `TenantLocaleProtocol` consumed from sibling services — not mirrored.
  - No existing orchestrator pattern in `core/luana-core-*/` for this use case
    (Lucas-specific cron analysis flow — Slice 2+ candidate for lift to
    `core/luana-core-platform/workers/` once 2nd brand pattern emerges).
  - The existing cron job `_shared/workers/jobs/lucas_weekly_recommendations.py`
    calls services DIRECTLY (no graph layer). This orchestrator adds the
    LangGraph layer per Slice 1 design § 3.4 — the cron job can later switch
    to invoke this orchestrator to get the graph observability + checkpoint
    benefits without changing the public service contract.

downstream-regression-na: brand-local orchestrator; no cross-brand consumers.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID
from zoneinfo import ZoneInfo

import structlog

from src.modules.vitalia.agentic.lucas.workflows.lucas_analysis_state import (
    DEFAULT_STAGES,
    LucasAnalysisState,
    Stage,
    initial_state,
)
from src.modules.vitalia.agentic.lucas.workflows.lucas_daily_analysis_graph import (
    AttributionHandler,
    CheckpointerProtocol,
    ReferralsHandler,
    StageRecommendationHandler,
    build_lucas_daily_analysis_graph,
    build_thread_config,
)

logger = structlog.get_logger()


class TenantLocaleProtocol(Protocol):
    """Minimal locale protocol — currency + timezone for TZ-aware computations."""

    @property
    def currency(self) -> str: ...  # pragma: no cover

    @property
    def timezone(self) -> str: ...  # pragma: no cover


@dataclass(frozen=True, slots=True)
class AnalysisReport:
    """Summary returned by `run_daily_analysis` — used by cron + tests.

    Attributes:
        tenant_id: Tenant UUID.
        clinic_id: Clinic UUID.
        analysis_date: TZ-aware tenant-local date (YYYY-MM-DD).
        period: YYYY-MM period.
        stages_processed: Count of stage_recommendations appended to state.
        attribution_present: True if attribution_matrix populated.
        referrals_present: True if referrals_leaderboard populated.
        iterations: Total graph node invocations.
        task_complete: Sentinel (True when finalize ran).
        final_state: Full final state (for tests + debug — production cron logs
                     summary only).
    """

    tenant_id: UUID
    clinic_id: UUID
    analysis_date: str
    period: str
    stages_processed: int
    attribution_present: bool
    referrals_present: bool
    iterations: int
    task_complete: bool
    final_state: LucasAnalysisState


def compute_run_date(tz_name: str | None, *, now_utc: dt.datetime | None = None) -> dt.date:
    """Compute TZ-aware tenant-local date for a Lucas run.

    Args:
        tz_name: IANA timezone string (e.g. "America/Lima"). None → UTC fallback.
        now_utc: Optional UTC datetime override (test injection). None → utcnow.

    Returns:
        Date instance in the tenant's local timezone.

    Raises:
        ZoneInfoNotFoundError: If tz_name is non-empty but invalid.
    """
    now_utc = now_utc or dt.datetime.now(tz=dt.timezone.utc)
    if not tz_name:
        return now_utc.date()
    tz = ZoneInfo(tz_name)
    return now_utc.astimezone(tz).date()


def compute_run_period(run_date: dt.date) -> str:
    """Compute YYYY-MM period string from a run date."""
    return run_date.strftime("%Y-%m")


class LucasOrchestratorService:
    """High-level orchestrator for Lucas daily analysis runs.

    Encapsulates TZ-aware date computation + graph construction + invocation.

    Caller (typically the cron job in `_shared/workers/jobs/`) constructs
    this service ONCE per cron run with the tool handlers + checkpointer,
    then invokes `run_daily_analysis(tenant_id, clinic_id, locale)` once per
    active tenant.

    Usage:
        orchestrator = LucasOrchestratorService(
            stage_handler=stage_handler,
            attribution_handler=attribution_handler,
            referrals_handler=referrals_handler,
            checkpointer=MemorySaver(),  # or AsyncPostgresSaver in prod
        )
        for tenant in active_tenants:
            report = await orchestrator.run_daily_analysis(
                tenant_id=tenant.id,
                clinic_id=tenant.clinic_id,
                locale=tenant.locale,
            )
            logger.info("lucas_run_complete", report=asdict(report))
    """

    def __init__(
        self,
        *,
        stage_handler: StageRecommendationHandler,
        attribution_handler: AttributionHandler,
        referrals_handler: ReferralsHandler,
        checkpointer: CheckpointerProtocol | Any,
        referrals_limit: int = 5,
        stages: tuple[Stage, ...] = DEFAULT_STAGES,
    ) -> None:
        """Initialise the orchestrator with injected dependencies.

        The graph is built once at construction time and reused across runs
        (LangGraph compiled graphs are reusable; thread_config provides the
        per-run isolation).
        """
        self._stages = stages
        self._graph = build_lucas_daily_analysis_graph(
            stage_handler=stage_handler,
            attribution_handler=attribution_handler,
            referrals_handler=referrals_handler,
            checkpointer=checkpointer,
            referrals_limit=referrals_limit,
        )

    async def run_daily_analysis(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        locale: TenantLocaleProtocol,
        run_date_override: dt.date | None = None,
    ) -> AnalysisReport:
        """Run the daily Lucas analysis for one tenant.

        Args:
            tenant_id: Tenant UUID (HIPAA-lite dual filter).
            clinic_id: Clinic UUID.
            locale: TenantLocale providing `timezone` for TZ-aware date.
            run_date_override: Optional date override (test injection).
                               Production passes None — date computed from locale.

        Returns:
            AnalysisReport summary.

        Per `tessl__graceful-degradation` Rule 5:
            Per-stage / attribution / referrals errors are caught INSIDE the
            graph nodes (see `lucas_daily_analysis_graph.py`). Graph-level
            failures (state corruption, checkpointer crash) bubble up — caller
            (cron job) is responsible for try/except + Sentry capture.
        """
        run_date = run_date_override or compute_run_date(locale.timezone)
        period = compute_run_period(run_date)
        analysis_date = run_date.isoformat()

        seed = initial_state(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            analysis_date=analysis_date,
            period=period,
            stages_to_analyze=self._stages,
        )
        thread_config = build_thread_config(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            period=period,
        )

        logger.info(
            "lucas_orchestrator_run_started",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            analysis_date=analysis_date,
            period=period,
            tz=locale.timezone,
        )

        final_state: LucasAnalysisState = await self._graph.ainvoke(
            seed,
            config=thread_config,
        )

        report = AnalysisReport(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            analysis_date=analysis_date,
            period=period,
            stages_processed=len(final_state.get("stage_recommendations") or []),
            attribution_present=final_state.get("attribution_matrix") is not None,
            referrals_present=final_state.get("referrals_leaderboard") is not None,
            iterations=int(final_state.get("iterations") or 0),
            task_complete=bool(final_state.get("task_complete")),
            final_state=final_state,
        )

        logger.info(
            "lucas_orchestrator_run_completed",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            period=period,
            stages_processed=report.stages_processed,
            attribution_present=report.attribution_present,
            referrals_present=report.referrals_present,
            iterations=report.iterations,
        )

        return report


__all__ = [
    "AnalysisReport",
    "LucasOrchestratorService",
    "TenantLocaleProtocol",
    "compute_run_date",
    "compute_run_period",
]
