# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""Lead domain entity — NOT PHI.

Domain layer — pure Python dataclass, no ORM imports.

Per arch spec § T-infra-9: Lead is NOT PHI. Single tenant_id filter only.
No dual filter required. Marketing role can access leads.

Extended in T-BE-1 (vitalia-fase2-adrian-embudo):
  + 6-stage dental funnel fields (stage, stage_entered_at, score, ...)
  + optimistic lock (version)
  + freeze state (is_frozen, frozen_reason, frozen_at)
  + commercial metadata (channel, service_interest, estimated_value, currency)
  + buying_signals JSONB list
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass
class Lead:
    """Lead domain entity — marketing prospect, non-PHI.

    Only tenant_id isolation required (no clinic_id dual filter).
    Marketing, receptionist, and admin roles can access lead data.

    Funnel fields added in vitalia-fase2-adrian-embudo (T-BE-1):
    - stage: 6-stage dental funnel (interesado|calificando|consulta_agendada|
             plan_presentado|reservado|decidio_no)
    - version: optimistic lock counter (WHERE version=expected → rowcount 0 = 409)
    - is_frozen / frozen_reason / frozen_at: RN-13 freeze state
    - currency: NEVER hardcoded — from tenant locale (RN-15)

    NEVER store clinical data (diagnosis, treatment notes, etc.) on Lead.
    RN-2 firewall: Lead is commercial / marketing, not PHI.
    """

    id: UUID
    tenant_id: UUID

    # Contact info (PII, pgcrypto-encrypted at DB level — name/email/phone/notes)
    name: str
    email: str | None = None
    phone: str | None = None
    source: str | None = None  # e.g., "website", "referral", "instagram"

    # Legacy flat status (keep for back-compat; stage is the SSoT for funnel)
    status: str = "new"  # new | contacted | qualified | lost | converted
    notes: str | None = None

    # ── Funnel fields (vitalia-fase2-adrian-embudo T-BE-1) ──────────────────
    stage: str = "interesado"
    # interesado | calificando | consulta_agendada | plan_presentado | reservado | decidio_no
    stage_entered_at: datetime | None = None  # time-in-stage SLA calc (RN-11)

    # Glass-box scoring (0-100, deterministic — no ML)
    score: int = 0
    temperature: str = "cold"  # hot | warm | cold

    # Operator attribution
    operated_by: str = "agent"  # agent | human (mirrors handler_mode checkpoint RN-12)

    # Origin channel (feeds ChannelBadge)
    channel: str | None = None  # wa | ig | meta | web | referido | tiktok

    # Commercial metadata (NON-PHI — no clinical context)
    service_interest: str | None = None
    assigned_doctor_id: UUID | None = None
    estimated_value: Decimal | None = None
    currency: str | None = None  # PEN/MXN/etc — tenant locale, never hardcoded (RN-15)

    # Buying signals — JSONB list of signal slugs (plaintext, non-PHI)
    buying_signals: list[str] = field(default_factory=list)

    # Freeze state (RN-13: 14d no response | 2×SLA | 30d hard)
    is_frozen: bool = False
    frozen_reason: str | None = None  # inactividad_lead | sin_respuesta | agente_trabado
    frozen_at: datetime | None = None

    # Terminal metadata
    closure_reason: str | None = None
    reactivation_cohort_at: datetime | None = None

    # Payment state stub (MSW for this story — real integration later)
    deposit_status: str | None = None  # pending | received

    # Blacklist flag (RN-13 variant)
    is_blacklisted: bool = False

    # Optimistic lock counter (SC-5 / RN-4)
    # Update WHERE version = expected_version; rowcount 0 → caller raises 409
    version: int = 1

    # Soft delete
    deleted_at: datetime | None = None

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now())
    updated_at: datetime = field(default_factory=lambda: datetime.now())
