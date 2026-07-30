# cap: agentic.lucas-recommendation-tool
# story-origin: TBD
"""Vitalia AGENTIC tool — `compute_stage_recommendation` (Lucas growth setter).

R23: production_code=True AGENTIC tool. Opus 4.7 EXCLUSIVE.
Story: vitalia-copilot-tools-impl T-ag-tools-3.

Spec sources:
  * 02-design-agentic.md § 2.4 (tools sequence Lucas) + § 3.5 (voice constraints)
  * 03-arch-agentic.md § 4.3 (Lucas tools table) + § 5.3 (cache slots)
  * 03-arch-be.md § 4.3 (Lucas tools DTOs) + § 8.6 (service contract)
  * 06-tickets.yaml::T-ag-tools-3 acceptance criteria

Semantics — single-shot LLM call (Kimi reasoning) per funnel stage:
  1. BudgetGuard.check(agent_kind="copilot") via LucasStageRecommendationService
  2. Fetch stage metrics from analytics engine (READ-ONLY ChannelRegistry)
  3. LLM completion (Kimi-k2.6, slot 1 + slot 2 cacheable per 03-arch-agentic § 5.3)
  4. Persist `lucas_recommendations` row (status='open' | 'skipped_budget')
  5. Return `RecommendationDTO` for cron worker to fan-out card refresh

Cost: $0.02-0.05 USD per stage (Kimi reasoning, 1h cache TTL batch nature).
BudgetGuard cap: $0.25 USD per tenant daily (Others pool — Lucas not sales_agent).

Tenant + HIPAA-lite isolation:
  * `tenant_id` + `clinic_id` MANDATORY (dual filter per vitalia/.claude/rules/hipaa-lite.md)
  * No PHI processed — analytics aggregates only.
  * Pre-flight: input.tenant_id MUST match `ctx_tenant_id` injected by caller
    (cron worker resolves tenant from `LUCAS_CRON_SECRET` Bearer + X-Tenant-ID).

Observability (best-effort per R23):
  * `trace_event_repo` optional — when supplied, tool records one event
    with `sanitize_payload` applied (engine sanitization SSoT — NEVER mirror).
  * Repository failure during trace MUST NOT break tool turn
    (try/except + structlog warning).

Anti-duplication audit (Step 0 GATE pre-write — per .claude/rules/anti-duplication.md):
  * `sanitize_payload` consumed from `luana_core_observability.recording.sanitization`
    — engine SSoT. NEVER re-implemented.
  * `LucasStageRecommendationService` (T-be-services-3) consumed — NEVER raw repo bypass.
  * No equivalent tool in `core/luana-core-*/` or other brands
    (vitalia vertical-medical growth analytics — Slice 2+ may lift if cross-brand demand).
  * Spanish neutro tuteo (Lucas UI chrome per § 1.20 guidelines — no voseo).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Protocol
from uuid import UUID

import structlog
from luana_core_observability.recording.sanitization import sanitize_payload
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from src.modules.vitalia.agentic.lucas.application.services.lucas_stage_recommendation_service import (
        LucasStageRecommendationService,
        TenantLocaleProtocol,
    )

logger = structlog.get_logger(__name__)


# ─── Pydantic schemas (input/output contract) ────────────────────────────


class ComputeStageRecommendationInput(BaseModel):
    """Input schema for `compute_stage_recommendation` tool.

    Per 03-arch-agentic.md § 4.3 + 03-arch-be.md § 4.3.

    Note: `tenant_id` is included here (NOT omitted like sales_agent tools)
    because Lucas is cron-triggered — the cron worker passes the explicit
    tenant context. Still enforced via ctx match check at handler.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    stage: Literal["attraction", "qualification", "reservation", "adoption", "expansion"] = Field(
        ...,
        description="Funnel stage for which to generate a growth recommendation.",
    )
    tenant_id: UUID = Field(
        ...,
        description="Tenant UUID (MUST match ctx_tenant_id injected by cron worker).",
    )
    clinic_id: UUID = Field(
        ...,
        description="Clinic UUID — HIPAA-lite dual filter per vitalia overlay rules.",
    )
    period: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="Period 'YYYY-MM' for which to compute the recommendation.",
    )


class RecommendationDTO(BaseModel):
    """Output DTO for `compute_stage_recommendation` tool.

    Per 03-arch-be.md § 4.3. Mapped from `StageRecommendation` domain entity.
    Schema cementado: includes `confidence` (mandatory) + `supporting_data`
    per design § Forbidden ("Lucas recommendations without confidence score").
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    stage: str = Field(..., description="Funnel stage analysed.")
    recommendation_text: str = Field(
        ...,
        description="Concrete actionable recommendation (Spanish neutro tuteo).",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score in [0.0, 1.0]. Required (per design § 3.5).",
    )
    supporting_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Stage metrics + LLM rationale used to derive the recommendation.",
    )
    currency: str | None = Field(
        default=None,
        description="ISO-4217 currency from tenant locale (NEVER hardcoded).",
    )
    status: Literal["active", "skipped_timeout", "skipped_budget", "applied", "rejected"] = Field(
        ...,
        description="Recommendation lifecycle status.",
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


# ─── Status mapping helper (entity → DTO) ────────────────────────────────


_ENTITY_STATUS_TO_DTO: dict[str, Literal["active", "skipped_timeout", "skipped_budget", "applied", "rejected"]] = {
    "open": "active",
    "approved": "applied",
    "rejected": "rejected",
    "skipped_budget": "skipped_budget",
    "skipped_timeout": "skipped_timeout",
    "expired": "rejected",
    "undone": "rejected",
}


def _confidence_from_status(status: str) -> float:
    """Derive a confidence score for the DTO from entity status.

    Per design § 3.5 Lucas recommendations require confidence score.
    Until Slice 2 introduces LLM self-rated confidence, derive a stable
    floor per status:
      - active recommendation → 0.75 (LLM-grounded analytics)
      - applied (operator approved) → 0.85
      - skipped_* → 0.0 (no recommendation generated)
    """
    if status == "open":
        return 0.75
    if status == "approved":
        return 0.85
    return 0.0


# ─── Handler ─────────────────────────────────────────────────────────────


async def compute_stage_recommendation(
    input: ComputeStageRecommendationInput,
    *,
    ctx_tenant_id: UUID,
    service: LucasStageRecommendationService,
    locale: TenantLocaleProtocol,
    trace_event_repo: _TraceEventRepoLike | None = None,
    turn_id: UUID | None = None,
    span_id: UUID | None = None,
) -> RecommendationDTO:
    """Generate a growth-stage recommendation via Lucas analytics agent.

    See module docstring for full semantics + spec references.

    Parameters
    ----------
    input
        Pydantic-validated input (stage + tenant_id + clinic_id + period).
    ctx_tenant_id
        Tenant injected by cron worker (from validated `LUCAS_CRON_SECRET` Bearer
        + X-Tenant-ID). MUST match `input.tenant_id` — defensive check below.
    service
        `LucasStageRecommendationService` instance (T-be-services-3). Caller
        wires repo + budget_guard + LLM service + analytics adapter via DI.
    locale
        `TenantLocale` providing currency + timezone. Currency NEVER hardcoded
        (per `.claude/rules/currency-handling.md` + `.claude/rules/master-data.md`).
    trace_event_repo
        Optional `BaseTraceEventRepoProtocol` impl — when supplied, emits one
        `tool.compute_stage_recommendation.completed` event (best-effort).
    turn_id, span_id
        Required iff `trace_event_repo` supplied — caller correlation IDs.

    Returns
    -------
    RecommendationDTO — never raises tool-side errors; downstream errors
    (LLM timeout, BudgetGuard) materialize as `status` field values.

    Raises
    ------
    PermissionError
        If `input.tenant_id != ctx_tenant_id` (cross-tenant leak attempt —
        defense-in-depth even though cron worker validates upstream).
    """
    # 1. Defensive tenant boundary check (cardinal — per tenant-isolation.md)
    if input.tenant_id != ctx_tenant_id:
        # NEVER leak existence of cross-tenant data — uniform error.
        raise PermissionError("tenant_id mismatch")

    # 2. Delegate to service (T-be-services-3) which handles:
    #    - BudgetGuard.check(agent_kind="copilot")
    #    - analytics engine fetch (READ-ONLY ChannelRegistry)
    #    - LLM completion (Kimi-k2.6 via LiteLLM canonical)
    #    - persist `lucas_recommendations` row via repo (tenant_id + clinic_id)
    entity = await service.compute(
        tenant_id=input.tenant_id,
        clinic_id=input.clinic_id,
        stage=input.stage,
        period=input.period,
        locale=locale,
    )

    # 3. Map entity → DTO (currency from tenant locale, NEVER hardcoded)
    dto_status = _ENTITY_STATUS_TO_DTO.get(entity.status, "rejected")
    confidence = _confidence_from_status(entity.status)

    # 4. Extract supporting data from entity rationale (sanitized — no PHI)
    raw_supporting = entity.rationale_json if isinstance(entity.rationale_json, dict) else {}
    supporting_data = sanitize_payload(raw_supporting)

    dto = RecommendationDTO(
        stage=entity.stage,
        recommendation_text=entity.body,
        confidence=confidence,
        supporting_data=supporting_data,
        currency=locale.currency,
        status=dto_status,
    )

    # 5. Best-effort trace event emission
    await _emit_trace_event(
        trace_event_repo,
        tenant_id=input.tenant_id,
        turn_id=turn_id,
        span_id=span_id,
        input=input,
        dto=dto,
        recommendation_id=entity.id,
    )

    return dto


# ─── Helpers ─────────────────────────────────────────────────────────────


async def _emit_trace_event(
    trace_event_repo: _TraceEventRepoLike | None,
    *,
    tenant_id: UUID,
    turn_id: UUID | None,
    span_id: UUID | None,
    input: ComputeStageRecommendationInput,
    dto: RecommendationDTO,
    recommendation_id: UUID,
) -> None:
    """Best-effort trace_event emission. NEVER breaks tool turn (R23).

    Skips silently if repo not supplied or correlation IDs missing.
    Logs warning on persistence failure. Sanitizes payload (no PHI possible
    here — analytics only — but defense-in-depth per hipaa-lite.md).
    """
    if trace_event_repo is None or turn_id is None or span_id is None:
        return

    try:
        # Sanitize payload before persist (engine SSoT — NEVER mirror)
        payload = sanitize_payload(
            {
                "stage": dto.stage,
                "period": input.period,
                "clinic_id": str(input.clinic_id),
                "status": dto.status,
                "confidence": dto.confidence,
                "currency": dto.currency,
                "recommendation_id": str(recommendation_id),
                # NOTE: recommendation_text deliberately omitted — LLM outputs
                # could theoretically reflect PHI from upstream prompt (defense
                # in depth even though we don't pass PHI to LLM).
            }
        )
        trace_event_repo.add(
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            event_type="tool.compute_stage_recommendation.completed",
            name="compute_stage_recommendation",
            data=payload,
            duration_ms=None,
            status="ok",
        )
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "compute_stage_recommendation.trace_event_persist_failed",
            exc=str(exc),
            stage=dto.stage,
            tenant_id=str(tenant_id),
        )


__all__ = [
    "ComputeStageRecommendationInput",
    "RecommendationDTO",
    "compute_stage_recommendation",
]
