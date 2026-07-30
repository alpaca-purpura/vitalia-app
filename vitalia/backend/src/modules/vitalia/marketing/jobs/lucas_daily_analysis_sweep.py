# cap: marketing.lucas-stage-recommendations
# story-origin: TBD
"""lucas_daily_analysis_sweep — ARQ cron job, daily 06:00 UTC.

Regenerates Lucas AI marketing recommendations for every active tenant+clinic.

Steps per clinic:
  1. Expire stale OPEN recommendations (expires_at < now → status=expired).
  2. Build 30-day rejection cooldown set: recommendation_kinds rejected in last 30d.
  3. Invoke `LucasOrchestratorService.run_daily_analysis(tenant_id, clinic_id, locale)`.
     - The orchestrator runs the full LangGraph analysis internally.
     - Cooldown filtering applied POST-call on stage_recommendations from AnalysisReport.
  4. Publish LucasRecommendationGenerated for each recommendation NOT in cooldown.

HIPAA-lite:
  - Dual filter tenant_id + clinic_id on all queries.
  - No PHI in recommendation rows (marketing metrics only).
  - _get_active_clinics() uses a raw cross-tenant SQL for the cron sweep
    (system-level admin query, not user-facing — justification below).

Soft-fail: one clinic failure never aborts the sweep for other clinics.

downstream-regression-na: brand-local marketing cron — no cross-brand consumers
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from luana_core_platform.workers.cron_envelope import cron_envelope

from src.modules.vitalia.marketing.domain.enums import BowtieStage
from src.modules.vitalia.marketing.domain.events import LucasRecommendationGenerated
from src.modules.vitalia.marketing.infrastructure.repositories.lucas_recommendation_repository import (
    LucasRecommendationRepository,
)

try:
    from luana_core_events.outbox import adapter_bus  # type: ignore[import]
except ImportError:  # pragma: no cover
    import structlog as _structlog

    _fb_logger = _structlog.get_logger()

    class _FallbackBus:  # type: ignore[no-redef]
        """No-op fallback bus for dev environments without luana_core_events installed."""

        async def publish(self, event: object) -> None:  # noqa: D102
            _fb_logger.warning("adapter_bus.fallback_publish", event=repr(event))

    adapter_bus = _FallbackBus()

logger = structlog.get_logger()

# 30-day cooldown window for rejected recommendation_kinds
_REJECTION_COOLDOWN_DAYS: int = 30


# ---------------------------------------------------------------------------
# Minimal locale fallback — UTC/USD defaults for system-level cron sweep.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _FallbackLocale:
    """Minimal TenantLocaleProtocol implementation for the cron sweep.

    The daily sweep is a system-level operation that doesn't have access to
    per-tenant locale preferences from the request context.  UTC/USD is safe
    as a fallback because:
    - `analysis_date` is used only for period labelling (YYYY-MM) in Slice 1.
    - Off-by-<TZ> errors affect only the period boundary for tenants near
      midnight when the cron runs (06:00 UTC); acceptable for a daily sweep.
    - A proper locale lookup can be wired in Slice 2 when per-tenant locale
      service is available to the cron layer.
    """

    currency: str = "USD"
    timezone: str = "UTC"


# ---------------------------------------------------------------------------
# Injectable factory helpers (patchable for tests)
# ---------------------------------------------------------------------------


async def _get_active_clinics() -> list[dict[str, UUID]]:
    """Return list of {tenant_id, clinic_id} dicts for all active clinics.

    Queries channel_sync_state for clinics with at least one active marketing
    channel connection (status=ok, enabled=true).

    Note: This is a system-level admin cross-tenant sweep. The cron job runs as
    a privileged background process (not user-facing), so it intentionally queries
    across all tenants. All subsequent operations within the loop apply strict
    dual filter (tenant_id + clinic_id) per HIPAA-lite mandate.
    """
    from src.core.db import get_db_session  # type: ignore[import]  # noqa: PLC0415

    async with get_db_session() as session:
        from sqlalchemy import text  # noqa: PLC0415

        # Query distinct tenant+clinic pairs from channel_sync_state (active channels only)
        sql = text(
            "SELECT DISTINCT tenant_id, clinic_id "
            "FROM vitalia_channel_sync_state "
            "WHERE status = 'ok' AND enabled = TRUE AND deleted_at IS NULL"
        )
        result = await session.execute(sql)
        rows = result.fetchall()
        return [{"tenant_id": row.tenant_id, "clinic_id": row.clinic_id} for row in rows]


def _get_rec_repo() -> LucasRecommendationRepository:
    """Return LucasRecommendationRepository instance (patchable in tests)."""
    from src.core.db import get_sync_session  # type: ignore[import]  # noqa: PLC0415

    return LucasRecommendationRepository(session=get_sync_session())


async def _get_orchestrator() -> Any:
    """Return LucasOrchestratorService instance (patchable in tests).

    Uses the `make_orchestrator()` factory from the agentic services module,
    which wires no-op handlers + the brand-wide DURABLE checkpointer
    (``AsyncPostgresSaver`` via ``luana_core_flows.make_durable_checkpointer``)
    so the daily-analysis graph persists its LangGraph state to Postgres.

    Async because the durable checkpointer is constructed asynchronously
    (connection pool + ``.setup()``).

    In Slice 2, this factory will be upgraded to inject real
    LucasStageRecommendationService / AttributionService / ReferralsService
    instances with proper DB session DI.
    """
    from src.modules.vitalia.agentic.lucas.application.services import (  # noqa: PLC0415
        make_orchestrator,
    )

    return await make_orchestrator()


# ---------------------------------------------------------------------------
# Cron job
# ---------------------------------------------------------------------------


@cron_envelope("vitalia.cron.lucas_daily_analysis_sweep", ttl=86400)  # 24h TTL
async def lucas_daily_analysis_sweep(ctx: dict[str, Any]) -> None:
    """Daily 06:00 UTC — regenerate Lucas recommendations per stage per tenant+clinic.

    Runs LangGraph daily analysis via LucasOrchestratorService.run_daily_analysis,
    then applies 30d rejection cooldown filter post-call on stage_recommendations.
    Soft-fail per clinic — one LLM/BudgetGuard failure does not stop other clinics.
    """
    now = datetime.now(UTC)
    cooldown_since = now - timedelta(days=_REJECTION_COOLDOWN_DAYS)

    active_clinics = await _get_active_clinics()
    rec_repo = _get_rec_repo()
    orchestrator = await _get_orchestrator()
    locale = _FallbackLocale()

    swept = 0
    failed = 0

    for clinic in active_clinics:
        tenant_id: UUID = clinic["tenant_id"]
        clinic_id: UUID = clinic["clinic_id"]

        try:
            # Step 1: expire stale OPEN recommendations
            expired_count = await rec_repo.expire_stale_open(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                now=now,
            )
            if expired_count > 0:
                logger.info(
                    "lucas_daily_analysis_sweep.expired_stale",
                    tenant_id=str(tenant_id),
                    clinic_id=str(clinic_id),
                    expired=expired_count,
                )

            # Step 2: build 30d rejection cooldown set
            recent_rejections = await rec_repo.list_recent_rejections_by_kind(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                since=cooldown_since,
            )
            cooldown_kinds: set[str] = {r.recommendation_kind for r in recent_rejections}

            if cooldown_kinds:
                logger.info(
                    "lucas_daily_analysis_sweep.cooldown_kinds",
                    tenant_id=str(tenant_id),
                    clinic_id=str(clinic_id),
                    kinds=list(cooldown_kinds),
                )

            # Step 3: invoke orchestrator via real run_daily_analysis interface
            from src.modules.vitalia.agentic.lucas.application.services.lucas_orchestrator_service import (  # noqa: PLC0415
                AnalysisReport,
            )

            report: AnalysisReport = await orchestrator.run_daily_analysis(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                locale=locale,
            )

            # Step 4: extract stage recommendations from AnalysisReport and apply
            # cooldown filter post-call (cooldown_kinds are excluded from events)
            all_recs: list[dict[str, Any]] = list(report.final_state.get("stage_recommendations") or [])
            filtered_recs = [r for r in all_recs if r.get("recommendation_kind") not in cooldown_kinds]

            # Step 5: publish LucasRecommendationGenerated for each non-cooled rec
            for rec in filtered_recs:
                try:
                    rec_stage_raw = rec.get("stage")
                    # F-iter2-3 fix: pass BowtieStage ENUM (not .value string)
                    # LucasRecommendationGenerated expects stage: BowtieStage
                    # and calls stage.value internally — passing a string causes
                    # AttributeError: 'str' object has no attribute 'value'
                    if isinstance(rec_stage_raw, BowtieStage):
                        rec_stage = rec_stage_raw
                    else:
                        try:
                            rec_stage = BowtieStage(rec_stage_raw) if rec_stage_raw else BowtieStage.ATTRACTION
                        except ValueError:
                            rec_stage = BowtieStage.ATTRACTION

                    rec_id_raw = rec.get("id") or rec.get("recommendation_id")
                    try:
                        from uuid import UUID as _UUID  # noqa: PLC0415

                        rec_id = _UUID(str(rec_id_raw)) if rec_id_raw else UUID(int=0)
                    except (ValueError, AttributeError):
                        rec_id = UUID(int=0)

                    await adapter_bus.publish(
                        LucasRecommendationGenerated(
                            tenant_id=tenant_id,
                            recommendation_id=rec_id,
                            stage=rec_stage,
                            recommendation_kind=str(rec.get("recommendation_kind") or ""),
                            priority=int(rec.get("priority") or 1),
                        )
                    )
                except Exception as event_exc:
                    logger.warning(
                        "lucas_daily_analysis_sweep.event_publish_failed",
                        error=str(event_exc),
                    )

            swept += 1
            logger.info(
                "lucas_daily_analysis_sweep.clinic_ok",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
                all_recs=len(all_recs),
                published_recs=len(filtered_recs),
                cooled_down=len(all_recs) - len(filtered_recs),
            )

        except Exception as exc:
            # Soft-fail per clinic — log + continue
            failed += 1
            logger.warning(
                "lucas_daily_analysis_sweep.clinic_error",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
                error=str(exc),
            )

    logger.info(
        "lucas_daily_analysis_sweep.completed",
        total=len(active_clinics),
        swept=swept,
        failed=failed,
    )
