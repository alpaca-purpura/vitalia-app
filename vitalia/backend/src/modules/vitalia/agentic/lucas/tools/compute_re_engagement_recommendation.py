# cap: agentic.lucas-recommendation-tool
# story-origin: TBD
"""Vitalia AGENTIC tool — `compute_re_engagement_recommendation` (Lucas).

R23: production_code=True AGENTIC tool. Opus 4.7 EXCLUSIVE.
Story: vitalia-slice-1-fidelizacion T-10.

Spec sources:
  * 03-arch-agentic.md § 2.2 (compute_re_engagement_recommendation Lucas tool)
  * 03-arch-agentic.md § 4.2 (Lucas cache slot architecture)
  * 03-arch-agentic.md § 7 (observability writes mandatory)
  * 06-tickets.yaml::T-10 acceptance criteria

Semantics — composite ReAct-like pipeline:
  1. Tenant boundary defensive check (ctx_tenant_id == input.tenant_id)
  2. Delegate to LucasReEngagementService.run(...) which:
     a. aggregate_patterns() — DB query via repo (dual filter tenant+clinic)
     b. detect_clusters() — Python deterministic (no LLM)
     c. generate_recommendations() — single LLM call (Kimi via LiteLLM) +
        sanitize_payload defense-in-depth
  3. Best-effort trace event emission (NEVER breaks tool turn — R23)

Output schema (per caller spec T-10):
  {
    "tenant_id": "<uuid>",
    "clinic_id": "<uuid>",
    "stage": "fidelizacion",
    "recommendations": [
      {
        "pattern": "<multi_session|follow_up|maintenance|absence|nps>",
        "priority": "<high|medium|low>",
        "action": "<accion concreta, espanol neutro>",
        "expected_impact_pct": <int 1-100>,
        "rationale": "<por que esta accion>"
      }
    ]
  }

HIPAA-lite (vitalia/.claude/rules/hipaa-lite.md):
  * tenant_id + clinic_id MANDATORY (dual filter enforced at repo layer)
  * Aggregate-only — NEVER per-patient PHI in output
  * Trace event payload omits recommendation bodies (action/rationale)
    — only counts + period + clinic_id + status logged.

Anti-duplication §0 (.claude/rules/anti-duplication.md):
  * `sanitize_payload` consumed from `luana_core_observability.recording.sanitization`
    — engine SSoT. NEVER mirror.
  * `LucasReEngagementService` consumed — NEVER raw repo bypass.
  * No equivalent tool in `core/luana-core-*/` or other brands
    (vitalia vertical-medical fidelización — Slice 2+ may lift if cross-brand demand).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Protocol
from uuid import UUID

import structlog
from luana_core_observability.recording.sanitization import sanitize_payload
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from src.modules.vitalia.agentic.lucas.application.services.lucas_re_engagement_service import (
        LucasReEngagementService,
    )

logger = structlog.get_logger(__name__)


# ─── Pydantic schemas (input/output contract) ────────────────────────────


class ComputeReEngagementRecommendationInput(BaseModel):
    """Input schema for `compute_re_engagement_recommendation` tool.

    Per 03-arch-agentic.md § 2.2 + caller spec T-10.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: UUID = Field(
        ...,
        description="Tenant UUID (MUST match ctx_tenant_id injected by caller).",
    )
    clinic_id: UUID = Field(
        ...,
        description="Clinic UUID — HIPAA-lite dual filter per vitalia overlay rules.",
    )
    period: Literal["7d", "30d", "90d"] = Field(
        default="30d",
        description="Period over which to aggregate re-engagement signals.",
    )
    top_n: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Max number of recommendations to return.",
    )


# ─── Repository protocols (decouple from concrete classes) ───────────────


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


class _TenantLocaleLike(Protocol):
    """Minimal locale protocol — currency + timezone from TenantLocale.

    Currency NEVER hardcoded — caller passes TenantLocale (per
    .claude/rules/master-data.md + currency-handling.md). For Lucas
    re-engagement aggregates the locale is not used to format monetary
    fields directly (no monetary in recommendations Slice 1), but it is
    passed forward to maintain parity with sibling Lucas tools and to
    support Slice 2+ monetary KPIs in rationale.
    """

    currency: str
    timezone: str


# ─── Period mapping (literal → int days) ─────────────────────────────────


_PERIOD_TO_DAYS: dict[str, int] = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
}


# ─── Handler ─────────────────────────────────────────────────────────────


async def compute_re_engagement_recommendation(
    input: ComputeReEngagementRecommendationInput,
    *,
    ctx_tenant_id: UUID,
    service: LucasReEngagementService,
    locale: _TenantLocaleLike,
    trace_event_repo: _TraceEventRepoLike | None = None,
    turn_id: UUID | None = None,
    span_id: UUID | None = None,
) -> dict[str, Any]:
    """Generate Owner-facing re-engagement recommendations via Lucas analytics.

    See module docstring for full semantics + spec references.

    Parameters
    ----------
    input
        Pydantic-validated input (tenant + clinic + period + top_n).
    ctx_tenant_id
        Tenant injected by caller (cron worker / Owner-triggered API).
        MUST match `input.tenant_id` — defensive check below.
    service
        `LucasReEngagementService` instance. Caller wires repo + LLM service
        via DI (per backend-ddd Inside-Out pattern).
    locale
        Tenant locale (currency + timezone). Passed forward; currency NEVER
        hardcoded in caller code.
    trace_event_repo
        Optional `BaseTraceEventRepoProtocol` impl — when supplied, emits one
        `tool.compute_re_engagement_recommendation.completed` event (best-effort).
    turn_id, span_id
        Required iff `trace_event_repo` supplied — caller correlation IDs.

    Returns
    -------
    dict — `{tenant_id, clinic_id, stage, recommendations}`. NEVER raises
    tool-side errors; downstream errors materialize as empty `recommendations`.

    Raises
    ------
    PermissionError
        If `input.tenant_id != ctx_tenant_id` (cross-tenant leak attempt —
        defense-in-depth even though caller validates upstream).
    """
    # 1. Defensive tenant boundary check (cardinal — per tenant-isolation.md)
    if input.tenant_id != ctx_tenant_id:
        # NEVER leak existence of cross-tenant data — uniform error.
        raise PermissionError("tenant_id mismatch")

    # 2. Map period literal → int days
    period_days = _PERIOD_TO_DAYS[input.period]

    # 3. Delegate to service (aggregate → cluster → LLM → sanitize)
    recommendations = await service.run(
        tenant_id=input.tenant_id,
        clinic_id=input.clinic_id,
        period_days=period_days,
        top_n=input.top_n,
    )

    # 4. Compose response (output schema per caller spec)
    response: dict[str, Any] = {
        "tenant_id": str(input.tenant_id),
        "clinic_id": str(input.clinic_id),
        "stage": "fidelizacion",
        "recommendations": recommendations,
    }

    # 5. Best-effort trace event emission (R23 — never breaks turn)
    await _emit_trace_event(
        trace_event_repo,
        tenant_id=input.tenant_id,
        turn_id=turn_id,
        span_id=span_id,
        input=input,
        recommendations_count=len(recommendations),
    )

    return response


# ─── Helpers ─────────────────────────────────────────────────────────────


async def _emit_trace_event(
    trace_event_repo: _TraceEventRepoLike | None,
    *,
    tenant_id: UUID,
    turn_id: UUID | None,
    span_id: UUID | None,
    input: ComputeReEngagementRecommendationInput,
    recommendations_count: int,
) -> None:
    """Best-effort trace_event emission. NEVER breaks tool turn (R23).

    Skips silently if repo not supplied or correlation IDs missing.
    Logs warning on persistence failure. Audit per caller spec:
    log (tenant_id, clinic_id, recommendations_count) — NEVER bodies.
    """
    if trace_event_repo is None or turn_id is None or span_id is None:
        return

    try:
        # Sanitize payload before persist (engine SSoT — NEVER mirror).
        # NOTE: recommendation_text/action/rationale deliberately omitted —
        # defense-in-depth even though Lucas processes aggregates only and
        # LLM output passes through sanitize_payload upstream in service.
        payload = sanitize_payload(
            {
                "period": input.period,
                "clinic_id": str(input.clinic_id),
                "top_n": input.top_n,
                "recommendations_count": recommendations_count,
            }
        )
        trace_event_repo.add(
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            event_type="tool.compute_re_engagement_recommendation.completed",
            name="compute_re_engagement_recommendation",
            data=payload,
            duration_ms=None,
            status="ok",
        )
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "compute_re_engagement_recommendation.trace_event_persist_failed",
            exc=str(exc),
            tenant_id=str(tenant_id),
        )


__all__ = [
    "ComputeReEngagementRecommendationInput",
    "compute_re_engagement_recommendation",
]
