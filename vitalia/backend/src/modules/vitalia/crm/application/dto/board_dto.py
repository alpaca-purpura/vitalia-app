# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""Board DTOs — Kanban board response shapes for Embudo de Adrián.

API layer Pydantic v2 models. All model_config = ConfigDict(from_attributes=True).
Lead PII fields (name/email/phone) excluded from board — cards use masked display.
Currency: never hardcoded; None = tenant locale fallback at FE.

T-FE2bis (2026-06-03): expanded LeadCardDTO to match full FE LeadCardDTO contract.
Fields added: version, tenant_id, is_frozen, frozen_reason, closure_reason,
reactivation_cohort_at, service_interest, assigned_doctor_id, is_blacklisted,
last_activity_description (renamed from last_activity), last_activity_at.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LeadCardDTO(BaseModel):
    """Minimal lead representation for Kanban board card (LeadCard component).

    PII: name is included (masked by PiiMaskedSpan at FE — RN-16).
    email/phone excluded from board card (full detail has them masked too).

    T-FE2bis: expanded to match full FE LeadCardDTO contract so the drag-transition
    mutation (PATCH /stage with optimistic-concurrency version) and all FE card
    renderers receive the fields they declare.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID  # T-FE2bis: required by FE LeadCardDTO
    name: str  # masked at FE via PiiMaskedSpan
    stage: str
    score: int
    temperature: str  # hot | warm | cold
    channel: str | None = None
    estimated_value: Decimal | None = None
    currency: str | None = None  # NEVER hardcoded — tenant locale at FE
    operated_by: str  # agent | human
    buying_signals: list[str]
    stage_entered_at: str | None = None  # ISO8601 string for FE time-in-stage calc
    sla_state: str  # green | amber | red
    deposit_status: str | None = None  # pending | received

    # Freeze / terminal state (T-FE2bis)
    is_frozen: bool  # T-FE2bis: FE uses this to gate Recuperar interactions
    frozen_reason: str | None = None  # T-FE2bis: inactividad_lead | sin_respuesta | ...
    closure_reason: str | None = None  # T-FE2bis: terminal closure text
    reactivation_cohort_at: str | None = None  # T-FE2bis: ISO8601 scheduled reactivation

    # Commercial metadata (T-FE2bis)
    service_interest: str | None = None  # T-FE2bis: service the lead expressed interest in
    assigned_doctor_id: UUID | None = None  # T-FE2bis: doctor assignment
    is_blacklisted: bool = False  # T-FE2bis: blacklist flag

    # Optimistic concurrency (T-FE2bis — CRITICAL for drag-transition PATCH /stage SC-5)
    version: int  # T-FE2bis: must match Lead.version for optimistic lock

    # Activity micro-log (T-FE2bis — renamed from last_activity; added last_activity_at)
    last_activity_description: str | None = None  # replaces last_activity (T-FE2bis)
    last_activity_at: str | None = None  # T-FE2bis: ISO8601 when last activity occurred

    # Internal highlight (post-create ring+pulse 3s)
    is_highlighted: bool = False


class BoardColumn(BaseModel):
    """Single Kanban column — one per HOT_BOARD_STAGES stage."""

    model_config = ConfigDict(from_attributes=True)

    stage: str
    label: str  # Spanish neutro label from STAGE_LABELS_ES
    count: int
    sum_value: Decimal  # sum of estimated_value in this column (bucketed, no PHI)
    currency: str | None = None  # most common currency in column, or None
    over_sla_count: int  # leads with sla_state in {amber, red}
    leads: list[LeadCardDTO]


class BoardKpis(BaseModel):
    """KPI strip displayed above the board columns."""

    model_config = ConfigDict(from_attributes=True)

    active: int  # total non-frozen active leads in HOT_BOARD_STAGES
    agent_count: int  # operated_by=agent
    human_count: int  # operated_by=human
    hot: int  # temperature=hot
    warm: int  # temperature=warm
    cold: int  # temperature=cold
    avg_score: int  # rounded average score across active leads
    deposit_rate: float  # fraction with deposit_status=received
    frozen_count: int  # total frozen leads (separate Recuperar tab)


class BoardResponse(BaseModel):
    """Full board response: columns + KPI strip."""

    model_config = ConfigDict(from_attributes=True)

    columns: list[BoardColumn]
    kpis: BoardKpis
