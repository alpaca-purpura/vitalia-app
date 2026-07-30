# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Vitalia AGENTIC tool — `compute_attribution_matrix` (Lucas growth setter).

R23: production_code=True AGENTIC tool. Opus 4.7 EXCLUSIVE.
Story: vitalia-copilot-tools-impl T-ag-tools-3.

Spec sources:
  * 02-design-agentic.md § 2.4 (tools sequence Lucas)
  * 03-arch-agentic.md § 4.3 (Lucas tools — pure DB)
  * 03-arch-be.md § 8.7 (LucasAttributionService pure DB analytics)

Semantics — pure DB analytics, NO LLM call:
  1. LucasAttributionService.compute_attribution() reads engine ChannelRegistry
     + STAGE_CHANNEL_MAP via AnalyticsEngineQueryAdapter (READ-ONLY).
  2. Compute channel_breakdown total_attributed_revenue from engine data.
  3. Persist `attribution_matrix_snapshots` row (tenant_id + clinic_id).
  4. Return `MatrixDTO` for cron worker to fan-out card refresh.

Cost: $0 (pure DB).
Latency budget: <500ms p95 (indexed query on tenant_id + clinic_id + period_start).
NO BudgetGuard call needed (no LLM cost).

Tenant + HIPAA-lite isolation:
  * `tenant_id` + `clinic_id` MANDATORY (dual filter per vitalia overlay).
  * No PHI processed — channel attribution aggregates only.

Anti-duplication audit (per .claude/rules/anti-duplication.md):
  * `sanitize_payload` consumed from `luana_core_observability.recording.sanitization`.
  * `LucasAttributionService` (T-be-services-3) consumed — NEVER raw repo bypass.
  * `_GROUP_MAP` / `STAGE_CHANNEL_MAP` NEVER mirrored here
    (per .claude/rules/analytics-metrics.md cardinal — engine SSoT).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol
from uuid import UUID

import structlog
from luana_core_observability.recording.sanitization import sanitize_payload
from pydantic import BaseModel, ConfigDict, Field, field_serializer

if TYPE_CHECKING:
    from src.modules.vitalia.agentic.lucas.application.services.lucas_attribution_service import (
        LucasAttributionService,
        TenantLocaleProtocol,
    )

logger = structlog.get_logger(__name__)


# ─── Pydantic schemas ────────────────────────────────────────────────────


class ComputeAttributionMatrixInput(BaseModel):
    """Input schema — Lucas attribution matrix for a tenant+clinic+period."""

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


class MatrixDTO(BaseModel):
    """Output DTO — attribution matrix breakdown by origin channel.

    Per 02-design-agentic § 2.4 4 origins per channel breakdown.
    `total_attributed_revenue` uses Decimal (financial precision)
    serialised as string for JSON cross-language safety.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    period_start: dt.date
    period_end: dt.date
    channel_breakdown: dict[str, Any] = Field(
        default_factory=dict,
        description="Channel slug → attributed revenue. Engine ChannelRegistry SSoT.",
    )
    total_attributed_revenue: Decimal = Field(
        default=Decimal("0.00"),
        description="Sum of channel_breakdown values (Decimal precision).",
    )
    currency: str | None = Field(
        default=None,
        description="ISO-4217 currency from tenant locale (NEVER hardcoded).",
    )
    snapshot_id: UUID = Field(..., description="Persisted snapshot UUID.")

    @field_serializer("total_attributed_revenue")
    def _serialize_decimal(self, value: Decimal) -> str:
        """Serialise Decimal as string for JSON safety."""
        return str(value)


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


async def compute_attribution_matrix(
    input: ComputeAttributionMatrixInput,
    *,
    ctx_tenant_id: UUID,
    service: LucasAttributionService,
    locale: TenantLocaleProtocol,
    trace_event_repo: _TraceEventRepoLike | None = None,
    turn_id: UUID | None = None,
    span_id: UUID | None = None,
) -> MatrixDTO:
    """Compute attribution matrix breakdown for a period.

    Parameters
    ----------
    input
        Pydantic-validated input (tenant + clinic + period range).
    ctx_tenant_id
        Tenant injected by cron worker. MUST match `input.tenant_id`.
    service
        `LucasAttributionService` (T-be-services-3) — pure DB analytics.
    locale
        `TenantLocale` providing currency + timezone (currency NEVER hardcoded).
    trace_event_repo, turn_id, span_id
        Best-effort observability — same contract as other Lucas tools.

    Returns
    -------
    MatrixDTO — channel_breakdown + total_attributed_revenue + currency.

    Raises
    ------
    PermissionError
        If `input.tenant_id != ctx_tenant_id` (defense-in-depth boundary).
    """
    # 1. Defensive tenant boundary check
    if input.tenant_id != ctx_tenant_id:
        raise PermissionError("tenant_id mismatch")

    # 2. Delegate to service (pure DB — NO LLM)
    entity = await service.compute_attribution(
        tenant_id=input.tenant_id,
        clinic_id=input.clinic_id,
        period_start=input.period_start,
        period_end=input.period_end,
        locale=locale,
    )

    # 3. Map entity → DTO (currency from tenant locale)
    dto = MatrixDTO(
        period_start=entity.period_start,
        period_end=entity.period_end,
        channel_breakdown=entity.channel_breakdown,
        total_attributed_revenue=entity.total_attributed_revenue,
        currency=entity.currency or locale.currency,
        snapshot_id=entity.id,
    )

    # 4. Best-effort trace event
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
    input: ComputeAttributionMatrixInput,
    dto: MatrixDTO,
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
                "channel_count": len(dto.channel_breakdown),
                "total_attributed_revenue": str(dto.total_attributed_revenue),
                "currency": dto.currency,
                "snapshot_id": str(dto.snapshot_id),
            }
        )
        trace_event_repo.add(
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            event_type="tool.compute_attribution_matrix.completed",
            name="compute_attribution_matrix",
            data=payload,
            duration_ms=None,
            status="ok",
        )
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "compute_attribution_matrix.trace_event_persist_failed",
            exc=str(exc),
            tenant_id=str(tenant_id),
        )


__all__ = [
    "ComputeAttributionMatrixInput",
    "MatrixDTO",
    "compute_attribution_matrix",
]
