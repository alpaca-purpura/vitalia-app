# cap: agentic.lucas-daily-analysis
# story-origin: TBD
"""Lucas daily analysis cron job — LangGraph orchestrator integration entrypoint.

Story: vitalia-copilot-tools-impl T-ag-workflows-2 (R23 Opus 4.7 production AGENTIC code).

This is the graph-layer cron entry point. It:
  1. Iterates the active tenants supplied by the caller (cron worker passes them).
  2. For each tenant, invokes `LucasOrchestratorService.run_daily_analysis(...)`.
  3. Returns a per-tenant report (success / skipped reason).

Idempotency:
  - The production ARQ wrapper at `_shared/workers/jobs/lucas_weekly_recommendations.py`
    is decorated with `@idempotent_cron` (Redis-backed, TTL=1h). That decorator
    enforces dedup at the cron-execution level (preventing double-fire on retry
    bursts within the TTL window).
  - At THIS layer we additionally enforce per-tenant + per-date idempotency by
    composing a deterministic key `lucas_daily:{tenant_id}:{date}` and consulting
    the engine `IdempotencyStore` BEFORE invoking the graph. If the key was
    already claimed within `idem_ttl_seconds` (default 1h), the run is skipped
    (returns a `status='skipped_already_run'` row) and NO graph invocation
    occurs (NO LLM cost, NO duplicate persistence).
  - Soft-fail: if the IdempotencyStore is unavailable (Redis down), we log a
    warning and proceed (graceful-degradation per `tessl__graceful-degradation`
    Rule 5 — a missed dedup is acceptable; failing the whole cron is not).

Anti-duplication §0 audit (Step 0 GATE):
  - `IdempotencyKey` + `RedisIdempotencyStore` imported from engine
    `luana_core_idempotency.{domain,infrastructure}` — NEVER re-implemented
    locally (the existing `@idempotent_cron` decorator in `_shared/workers/base.py`
    already follows this pattern; we follow the SAME convention here).
  - `LucasOrchestratorService` consumed from sibling application services.
  - No equivalent cron entrypoint in `core/luana-core-*/` (vitalia-specific).
  - The vitalia learning `2026-05-18-idempotent-cron-pattern.md` documents the
    lift-shared candidate for the `@idempotent_cron` decorator (engine
    `luana_core_platform.workers`). When that lift lands, this module imports
    the engine decorator instead of composing the key inline — the public
    contract here (`run_lucas_daily_analysis_job`) does NOT change.

downstream-regression-na: brand-local cron entrypoint; no cross-brand consumers.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol
from uuid import UUID

import structlog

from src.modules.vitalia.agentic.lucas.application.services.lucas_orchestrator_service import (
    AnalysisReport,
    LucasOrchestratorService,
    TenantLocaleProtocol,
    compute_run_date,
)

logger = structlog.get_logger()


# ──────────────────────────────────────────────────────────────────────────
# Idempotency primitives (soft-fail per graceful-degradation).
#
# We use `luana_core_idempotency` directly (NOT the existing
# `@idempotent_cron` decorator at `_shared/workers/base.py`) because we need
# the key composition to be DETERMINISTIC from (tenant_id, date) rather than
# from the ARQ job_id. The cron wrapper in `_shared/workers/` adds an outer
# layer of dedup keyed on job_id; this layer adds per-tenant per-date dedup.
# ──────────────────────────────────────────────────────────────────────────


class _IdempotencyStoreLike(Protocol):
    """Minimal protocol matching `luana_core_idempotency` RedisIdempotencyStore."""

    async def claim(self, key: Any) -> bool: ...  # pragma: no cover
    async def cached_result(self, key: Any) -> Any: ...  # pragma: no cover
    async def store_result(self, key: Any, result: Any) -> None: ...  # pragma: no cover


def _build_idempotency_key(
    *,
    tenant_id: UUID,
    analysis_date: str,
    ttl_seconds: int,
) -> Any:
    """Compose engine IdempotencyKey for (tenant, date) tuple. Soft-fail import.

    Returns None if engine package unavailable (test environment without engine
    install). Caller treats None as "idempotency unavailable, proceed".
    """
    try:
        from luana_core_idempotency.domain.key import IdempotencyKey  # noqa: PLC0415
    except ImportError:
        logger.warning("lucas_idempotency_engine_unavailable_softfail")
        return None
    return IdempotencyKey(
        namespace="vitalia.lucas.daily_analysis",
        key=f"{tenant_id}:{analysis_date}",
        ttl_seconds=ttl_seconds,
    )


# ──────────────────────────────────────────────────────────────────────────
# Input + result DTOs
# ──────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class TenantRunInput:
    """Single tenant entry for the daily analysis run.

    Attributes:
        tenant_id: Tenant UUID.
        clinic_id: Clinic UUID (HIPAA-lite dual filter).
        locale: TenantLocale (provides timezone for TZ-aware date).
    """

    tenant_id: UUID
    clinic_id: UUID
    locale: TenantLocaleProtocol


@dataclass(frozen=True, slots=True)
class LucasDailyAnalysisJobInput:
    """Input envelope for a daily Lucas analysis job invocation.

    Attributes:
        tenants: Iterable of TenantRunInput. Caller (cron worker) MUST filter
                 to active tenants (`is_active=true`) — this entry point
                 trusts the caller.
        idem_ttl_seconds: TTL for per-tenant idempotency key (default 3600 = 1h
                          — aligns with `lucas_weekly_recommendations.py`
                          cron `idem_ttl_seconds=3600` baseline).
    """

    tenants: tuple[TenantRunInput, ...]
    idem_ttl_seconds: int = 3600


@dataclass(frozen=True, slots=True)
class TenantRunResult:
    """Per-tenant outcome of a daily analysis run.

    Status values:
        completed                — graph ran end-to-end; report has data.
        skipped_already_run      — idempotency dedup (same tenant+date in TTL window).
        failed                   — uncaught exception bubbled from graph.

    Attributes:
        tenant_id: Tenant UUID.
        clinic_id: Clinic UUID.
        analysis_date: TZ-aware date string used for this run.
        status: Outcome literal.
        report: AnalysisReport if status='completed', else None.
        error: Exception class name + message if status='failed', else None.
    """

    tenant_id: UUID
    clinic_id: UUID
    analysis_date: str
    status: Literal["completed", "skipped_already_run", "failed"]
    report: AnalysisReport | None = None
    error: dict[str, str] | None = None


@dataclass(frozen=True, slots=True)
class LucasDailyAnalysisJobResult:
    """Aggregate result of a daily analysis job invocation.

    Attributes:
        tenant_results: Per-tenant outcomes in input order.
        completed_count: Count of successful runs.
        skipped_count: Count of dedup-skipped runs.
        failed_count: Count of failed runs.
        idempotency_available: Whether the engine idempotency store was usable
                               during this invocation (False = soft-fail mode).
    """

    tenant_results: list[TenantRunResult] = field(default_factory=list)
    completed_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    idempotency_available: bool = True


# ──────────────────────────────────────────────────────────────────────────
# Public entrypoint
# ──────────────────────────────────────────────────────────────────────────


async def run_lucas_daily_analysis_job(
    *,
    orchestrator: LucasOrchestratorService,
    job_input: LucasDailyAnalysisJobInput,
    idempotency_store: _IdempotencyStoreLike | None = None,
    now_utc: dt.datetime | None = None,
) -> LucasDailyAnalysisJobResult:
    """Run the daily Lucas analysis for each tenant supplied.

    Args:
        orchestrator: `LucasOrchestratorService` (already constructed with
                       handlers + checkpointer by caller).
        job_input: Tenant list + idempotency TTL.
        idempotency_store: Optional engine `RedisIdempotencyStore` for
                            per-tenant per-date dedup. None → soft-fail mode
                            (all runs proceed, no dedup). Tests inject a mock.
        now_utc: Optional UTC datetime override (test injection). None → utcnow.

    Returns:
        LucasDailyAnalysisJobResult with per-tenant outcomes.

    Per `tessl__graceful-degradation`:
        - Idempotency unavailable → log + proceed (Rule 5).
        - Per-tenant graph crash → captured as `status='failed'`, OTHER tenants
          continue (Rule 6 — degradation per tenant, not whole batch).
    """
    results: list[TenantRunResult] = []
    completed = skipped = failed = 0
    idem_available = idempotency_store is not None

    for tenant_input in job_input.tenants:
        analysis_date = compute_run_date(tenant_input.locale.timezone, now_utc=now_utc).isoformat()

        # ── Idempotency claim (soft-fail) ─────────────────────────────────
        claimed = True  # If no store, treat as always-claimed (proceed).
        if idempotency_store is not None:
            idem_key = _build_idempotency_key(
                tenant_id=tenant_input.tenant_id,
                analysis_date=analysis_date,
                ttl_seconds=job_input.idem_ttl_seconds,
            )
            if idem_key is not None:
                try:
                    claimed = await idempotency_store.claim(idem_key)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "lucas_cron_idempotency_claim_softfail",
                        tenant_id=str(tenant_input.tenant_id),
                        analysis_date=analysis_date,
                        err=str(exc),
                    )
                    claimed = True  # soft-fail → proceed
                    idem_available = False

        if not claimed:
            logger.info(
                "lucas_cron_skipped_already_run",
                tenant_id=str(tenant_input.tenant_id),
                clinic_id=str(tenant_input.clinic_id),
                analysis_date=analysis_date,
            )
            results.append(
                TenantRunResult(
                    tenant_id=tenant_input.tenant_id,
                    clinic_id=tenant_input.clinic_id,
                    analysis_date=analysis_date,
                    status="skipped_already_run",
                ),
            )
            skipped += 1
            continue

        # ── Graph invocation (per-tenant graceful-degradation) ────────────
        try:
            report = await orchestrator.run_daily_analysis(
                tenant_id=tenant_input.tenant_id,
                clinic_id=tenant_input.clinic_id,
                locale=tenant_input.locale,
                run_date_override=dt.date.fromisoformat(analysis_date),
            )
        except Exception as exc:  # noqa: BLE001 — per-tenant degradation Rule 6
            logger.exception(
                "lucas_cron_tenant_run_failed",
                tenant_id=str(tenant_input.tenant_id),
                clinic_id=str(tenant_input.clinic_id),
                analysis_date=analysis_date,
            )
            results.append(
                TenantRunResult(
                    tenant_id=tenant_input.tenant_id,
                    clinic_id=tenant_input.clinic_id,
                    analysis_date=analysis_date,
                    status="failed",
                    error={
                        "error_class": type(exc).__name__,
                        "error_message": str(exc),
                    },
                ),
            )
            failed += 1
            continue

        results.append(
            TenantRunResult(
                tenant_id=tenant_input.tenant_id,
                clinic_id=tenant_input.clinic_id,
                analysis_date=analysis_date,
                status="completed",
                report=report,
            ),
        )
        completed += 1

    logger.info(
        "lucas_cron_daily_analysis_batch_complete",
        completed=completed,
        skipped=skipped,
        failed=failed,
        idempotency_available=idem_available,
    )

    return LucasDailyAnalysisJobResult(
        tenant_results=results,
        completed_count=completed,
        skipped_count=skipped,
        failed_count=failed,
        idempotency_available=idem_available,
    )


__all__ = [
    "LucasDailyAnalysisJobInput",
    "LucasDailyAnalysisJobResult",
    "TenantRunInput",
    "TenantRunResult",
    "run_lucas_daily_analysis_job",
]
