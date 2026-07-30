# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Vitalia AGENTIC tool — `compute_referrals_leaderboard` (Lucas growth setter).

R23: production_code=True AGENTIC tool. Opus 4.7 EXCLUSIVE.
Story: vitalia-copilot-tools-impl T-ag-tools-3.

Spec sources:
  * 02-design-agentic.md § 2.4 (tools sequence Lucas)
  * 03-arch-agentic.md § 4.3 (Lucas tools — pure DB, limit=5)
  * 03-arch-be.md § 8.7 (LucasReferralsService pure DB analytics)

Semantics — pure DB analytics, NO LLM call:
  1. LucasReferralsService.compute_referrals() reads analytics engine
     via AnalyticsEngineQueryAdapter (READ-ONLY).
  2. Build top-N (default 5) referrers list using `referrer_id` UUID only
     — NEVER patient names (HIPAA-lite cardinal).
  3. Persist `referrals_leaderboard_snapshots` row.
  4. Return `LeaderboardDTO` for cron worker to fan-out card refresh.

Cost: $0 (pure DB).
Latency budget: <500ms p95.

Tenant + HIPAA-lite isolation:
  * `tenant_id` + `clinic_id` MANDATORY (dual filter).
  * `referrer_id` is opaque UUID — NEVER patient names in DTO/trace
    (per vitalia/.claude/rules/hipaa-lite.md "PII fields canónicos").

Anti-duplication audit:
  * `sanitize_payload` from `luana_core_observability.recording.sanitization`.
  * `LucasReferralsService` (T-be-services-3) consumed — NEVER raw repo bypass.
  * No referral aggregator mirror in other brands (vitalia-specific medical referrals).
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Any, Protocol
from uuid import UUID

import structlog
from luana_core_observability.recording.sanitization import sanitize_payload
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from src.modules.vitalia.agentic.lucas.application.services.lucas_referrals_service import (
        LucasReferralsService,
        TenantLocaleProtocol,
    )

logger = structlog.get_logger(__name__)


# ─── Pydantic schemas ────────────────────────────────────────────────────


class ComputeReferralsLeaderboardInput(BaseModel):
    """Input schema — Lucas referrals leaderboard for a tenant+clinic+period.

    Default `limit=5` per 03-arch-agentic § 4.3 + 02-design § 2.4.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: UUID = Field(
        ...,
        description="Tenant UUID (MUST match ctx_tenant_id injected by cron worker).",
    )
    clinic_id: UUID = Field(
        ...,
        description="Clinic UUID — HIPAA-lite dual filter.",
    )
    period_start: dt.date = Field(..., description="Period start (inclusive).")
    period_end: dt.date = Field(..., description="Period end (inclusive).")
    limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Top-N referrers to include in leaderboard.",
    )


class LeaderboardDTO(BaseModel):
    """Output DTO — top referrers leaderboard.

    `top_referrers` items contain `referrer_id` (UUID string) ONLY. No PHI.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    period_start: dt.date
    period_end: dt.date
    top_referrers: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Top-N referrers: [{referrer_id, referral_count, converted_count, rank}].",
    )
    total_referrals: int = Field(
        default=0,
        ge=0,
        description="Total referral events in period.",
    )
    total_converted: int = Field(
        default=0,
        ge=0,
        description="Total converted referrals (downstream).",
    )
    snapshot_id: UUID = Field(..., description="Persisted snapshot UUID.")


# ─── Repository protocols ────────────────────────────────────────────────


class _TraceEventRepoLike(Protocol):
    """Mirror of `BaseTraceEventRepoProtocol` from luana_core_observability."""

    def add(
        self,
        *,
        tenant_id: UUID,
        turn_id: UUID,
        span_id: UUID,
        event_type: str,
        name: str | None = ...,
        data: dict[str, Any] | None = ...,
        duration_ms: int | None = ...,
        status: str = ...,
        **agent_specific: Any,
    ) -> Any: ...


# ─── Handler ─────────────────────────────────────────────────────────────


async def compute_referrals_leaderboard(
    input: ComputeReferralsLeaderboardInput,
    *,
    ctx_tenant_id: UUID,
    service: LucasReferralsService,
    locale: TenantLocaleProtocol,
    trace_event_repo: _TraceEventRepoLike | None = None,
    turn_id: UUID | None = None,
    span_id: UUID | None = None,
) -> LeaderboardDTO:
    """Compute top-N referrers leaderboard for a period.

    Parameters
    ----------
    input
        Pydantic-validated input (tenant + clinic + period + limit).
    ctx_tenant_id
        Tenant injected by cron worker. MUST match `input.tenant_id`.
    service
        `LucasReferralsService` (T-be-services-3) — pure DB analytics.
    locale
        `TenantLocale` (passed through to service for future use).
    trace_event_repo, turn_id, span_id
        Best-effort observability.

    Returns
    -------
    LeaderboardDTO — top_referrers (UUIDs only, no names) + totals.

    Raises
    ------
    PermissionError
        If `input.tenant_id != ctx_tenant_id` (defense-in-depth boundary).
    """
    # 1. Defensive tenant boundary check
    if input.tenant_id != ctx_tenant_id:
        raise PermissionError("tenant_id mismatch")

    # 2. Delegate to service (pure DB — NO LLM)
    entity = await service.compute_referrals(
        tenant_id=input.tenant_id,
        clinic_id=input.clinic_id,
        period_start=input.period_start,
        period_end=input.period_end,
        locale=locale,
    )

    # 3. Apply `limit` to top_referrers (service may return more — we clamp here)
    top_referrers = list(entity.top_referrers[: input.limit])

    # 4. Sanitize each referrer row — defense-in-depth against accidental PHI
    sanitized_rows: list[dict[str, Any]] = [sanitize_payload(row) for row in top_referrers]

    dto = LeaderboardDTO(
        period_start=entity.period_start,
        period_end=entity.period_end,
        top_referrers=sanitized_rows,
        total_referrals=entity.total_referrals,
        total_converted=entity.total_converted,
        snapshot_id=entity.id,
    )

    # 5. Best-effort trace event
    await _emit_trace_event(
        trace_event_repo,
        tenant_id=input.tenant_id,
        turn_id=turn_id,
        span_id=span_id,
        input=input,
        dto=dto,
    )

    return dto


# ─── Helpers ─────────────────────────────────────────────────────────────


async def _emit_trace_event(
    trace_event_repo: _TraceEventRepoLike | None,
    *,
    tenant_id: UUID,
    turn_id: UUID | None,
    span_id: UUID | None,
    input: ComputeReferralsLeaderboardInput,
    dto: LeaderboardDTO,
) -> None:
    """Best-effort trace event emission. NEVER breaks tool turn (R23)."""
    if trace_event_repo is None or turn_id is None or span_id is None:
        return

    try:
        payload = sanitize_payload(
            {
                "clinic_id": str(input.clinic_id),
                "period_start": str(input.period_start),
                "period_end": str(input.period_end),
                "limit": input.limit,
                "returned_count": len(dto.top_referrers),
                "total_referrals": dto.total_referrals,
                "total_converted": dto.total_converted,
                "snapshot_id": str(dto.snapshot_id),
                # NOTE: top_referrers list deliberately omitted from trace payload —
                # contains UUIDs only but principle of least exposure applies.
            }
        )
        trace_event_repo.add(
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            event_type="tool.compute_referrals_leaderboard.completed",
            name="compute_referrals_leaderboard",
            data=payload,
            duration_ms=None,
            status="ok",
        )
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "compute_referrals_leaderboard.trace_event_persist_failed",
            exc=str(exc),
            tenant_id=str(tenant_id),
        )


__all__ = [
    "ComputeReferralsLeaderboardInput",
    "LeaderboardDTO",
    "compute_referrals_leaderboard",
]
