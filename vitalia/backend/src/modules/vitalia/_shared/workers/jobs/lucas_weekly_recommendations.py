# cap: agentic.lucas-recommendation-tool
# story-origin: TBD
"""ARQ cron job: lucas_weekly_recommendations — Lucas growth setter weekly sweep.

Schedule: weekly Monday 04:00 UTC (configured in WorkerSettings.cron_jobs)
Span: vitalia.cron.lucas_weekly_recommendations
Owner module: copilot (Lucas agent cron-only — T-be-services-3)

Runs all 3 Lucas services per active tenant+clinic:
  1. LucasStageRecommendationService — AI recommendations for each stage
  2. LucasAttributionService — attribution matrix snapshot (current month)
  3. LucasReferralsService — referrals leaderboard snapshot (current month)

Wrapped with idempotent_cron for Redis idempotency + cron_span OTel tracing.
BudgetGuard pre-flight inside LucasStageRecommendationService (skips LLM if exceeded).

downstream-regression-na: brand-local cron; no cross-brand consumers
"""

from __future__ import annotations

import datetime as dt
from uuid import UUID

import structlog

from src.modules.vitalia._shared.workers.base import idempotent_cron

logger = structlog.get_logger()


@idempotent_cron("vitalia.cron.lucas_weekly_recommendations", idem_ttl_seconds=3600)
async def lucas_weekly_recommendations(ctx: dict) -> None:
    """Run Lucas growth setter weekly sweep per active tenant+clinic.

    Generates weekly recommendations across all 5 funnel stages:
    attraction, capture, nurture, opportunity, retention.

    Uses idempotent_cron wrapper:
      - Redis idempotency key (TTL=1h) prevents double-run.
      - cron_span OTel context for distributed tracing.
      - structlog audit on success, Sentry capture on exception.

    DI wiring:
      - DB session from ARQ ctx['db_session'] (injected by WorkerSettings startup).
      - BudgetGuard from luana_core_billing (per-job instantiation).
      - LiteLLM service from luana_core_llm.
      - Analytics adapter — READ-ONLY engine consumption.

    Args:
        ctx: ARQ worker context dict (job_id, redis, db_session, settings, etc.)
    """
    from src.modules.vitalia.agentic.lucas.application.services.lucas_attribution_service import (
        LucasAttributionService,
    )
    from src.modules.vitalia.agentic.lucas.application.services.lucas_referrals_service import (
        LucasReferralsService,
    )
    from src.modules.vitalia.agentic.lucas.application.services.lucas_stage_recommendation_service import (
        LucasStageRecommendationService,
    )
    from src.modules.vitalia.agentic.lucas.infrastructure.adapters.analytics_engine_query_adapter import (
        AnalyticsEngineQueryAdapter,
    )
    from src.modules.vitalia.agentic.lucas.infrastructure.repositories.attribution_matrix_snapshot_repository import (
        AttributionMatrixSnapshotRepository,
    )
    from src.modules.vitalia.agentic.lucas.infrastructure.repositories.referrals_leaderboard_snapshot_repository import (  # noqa: E501
        ReferralsLeaderboardSnapshotRepository,
    )
    from src.modules.vitalia.agentic.lucas.infrastructure.repositories.stage_recommendation_repository import (
        StageRecommendationRepository,
    )

    # Funnel stages to generate recommendations for
    stages = ["attraction", "capture", "nurture", "opportunity", "retention"]

    # Current period (YYYY-MM) and date range
    now = dt.datetime.now(tz=dt.timezone.utc)
    period = now.strftime("%Y-%m")
    period_start = now.replace(day=1).date()
    # period_end: last day of current month
    if now.month == 12:
        period_end = now.replace(year=now.year + 1, month=1, day=1).date() - dt.timedelta(days=1)
    else:
        period_end = now.replace(month=now.month + 1, day=1).date() - dt.timedelta(days=1)

    # Get active tenants from ctx (injected by WorkerSettings startup)
    active_tenants: list[dict] = ctx.get("active_tenants", [])
    if not active_tenants:
        logger.warning("lucas_weekly_no_active_tenants", period=period)
        return

    # Build shared adapter once
    analytics_adapter = AnalyticsEngineQueryAdapter()

    for tenant_data in active_tenants:
        tenant_id: UUID = tenant_data["tenant_id"]
        clinic_id: UUID = tenant_data["clinic_id"]
        locale = tenant_data.get("locale")  # TenantLocale with .currency

        if not locale:
            logger.warning(
                "lucas_weekly_skip_no_locale",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
            )
            continue

        db_session = ctx.get("db_session")
        if db_session is None:
            logger.error("lucas_weekly_no_db_session", tenant_id=str(tenant_id))
            continue

        try:
            # Service 1: Stage recommendations (LLM-backed, BudgetGuard inside)
            _budget_guard = _get_budget_guard(ctx)
            _llm_service = _get_llm_service(ctx)
            stage_repo = StageRecommendationRepository(session=db_session)
            stage_service = LucasStageRecommendationService(
                repo=stage_repo,
                budget_guard=_budget_guard,
                llm_service=_llm_service,
                analytics_adapter=analytics_adapter,
            )
            for stage in stages:
                try:
                    await stage_service.compute(
                        tenant_id=tenant_id,
                        clinic_id=clinic_id,
                        stage=stage,
                        period=period,
                        locale=locale,
                    )
                except Exception:
                    logger.exception(
                        "lucas_weekly_stage_error",
                        tenant_id=str(tenant_id),
                        stage=stage,
                    )

            # Service 2: Attribution matrix (pure DB)
            attribution_repo = AttributionMatrixSnapshotRepository(session=db_session)
            attribution_service = LucasAttributionService(
                repo=attribution_repo,
                analytics_adapter=analytics_adapter,
            )
            try:
                await attribution_service.compute_attribution(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    period_start=period_start,
                    period_end=period_end,
                    locale=locale,
                )
            except Exception:
                logger.exception(
                    "lucas_weekly_attribution_error",
                    tenant_id=str(tenant_id),
                )

            # Service 3: Referrals leaderboard (pure DB)
            referrals_repo = ReferralsLeaderboardSnapshotRepository(session=db_session)
            referrals_service = LucasReferralsService(
                repo=referrals_repo,
                analytics_adapter=analytics_adapter,
            )
            try:
                await referrals_service.compute_referrals(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    period_start=period_start,
                    period_end=period_end,
                    locale=locale,
                )
            except Exception:
                logger.exception(
                    "lucas_weekly_referrals_error",
                    tenant_id=str(tenant_id),
                )

        except Exception:
            logger.exception(
                "lucas_weekly_tenant_error",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
            )

    logger.info(
        "lucas_weekly_recommendations_complete",
        period=period,
        tenant_count=len(active_tenants),
    )


def _get_budget_guard(ctx: dict) -> object:
    """Get BudgetGuard instance from worker context or create new one.

    Graceful fallback: if luana_core_billing is unavailable, returns a
    pass-through guard that always allows (logs warning).
    """
    if "budget_guard" in ctx:
        return ctx["budget_guard"]
    try:
        from luana_core_billing import BudgetGuard

        return BudgetGuard()
    except ImportError:
        logger.warning("lucas_budget_guard_unavailable_using_passthrough")
        return _PassthroughBudgetGuard()


def _get_llm_service(ctx: dict) -> object:
    """Get LiteLLM service from worker context or create new one."""
    if "llm_service" in ctx:
        return ctx["llm_service"]
    try:
        from luana_core_llm.providers.litellm import LiteLLMService

        return LiteLLMService()
    except ImportError:
        logger.warning("lucas_llm_service_unavailable")
        return _NopLLMService()


class _PassthroughBudgetGuard:
    """Passthrough BudgetGuard used when luana_core_billing is unavailable."""

    def check(self, *, agent_kind: str) -> bool:
        """Always approve — used as fallback when billing package missing."""
        logger.warning("lucas_passthrough_budget_guard_check", agent_kind=agent_kind)
        return True


class _NopLLMService:
    """No-op LLM service used when luana_core_llm is unavailable."""

    async def complete(self, prompt: str, **kwargs: object) -> object:
        """Return empty content when LLM unavailable."""

        class _NopResponse:
            content = "Servicio de IA no disponible temporalmente."

        return _NopResponse()
