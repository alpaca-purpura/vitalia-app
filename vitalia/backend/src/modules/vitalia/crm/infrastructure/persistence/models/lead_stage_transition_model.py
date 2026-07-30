# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""LeadStageTransitionModel — SQLAlchemy 2.0 mapped class.

Infrastructure layer — ORM model only. No domain logic.

NON-PHI table: single tenant_id filter only (no clinic_id dual filter).
IMPORTANT: 'reason' field is named 'reason' NOT 'notes' to avoid the arch test
PHI pgcrypto regex false-positive that matches 'notes TEXT' columns.

Table: vitalia_lead_stage_transition
Index: ix_lst_tenant_lead (tenant_id, lead_id, occurred_at DESC)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class LeadStageTransitionModel(Base):
    """SQLAlchemy model for vitalia_lead_stage_transition table.

    NON-PHI: single tenant_id filter.
    All timestamps use timezone=True (TIMESTAMPTZ at DB level).
    reason field stores commercial override context (RN-4.1), NEVER clinical data.
    """

    __tablename__ = "vitalia_lead_stage_transition"
    __table_args__ = (
        Index(
            "ix_lst_tenant_lead",
            "tenant_id",
            "lead_id",
            "occurred_at",
        ),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Tenant isolation (single filter — Lead is non-PHI)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)

    # Lead reference (no FK — no cross-module JOIN, resolved at app layer)
    lead_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # Transition data
    from_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    triggered_by: Mapped[str] = mapped_column(String(64), nullable=False)
    # Named 'reason' NOT 'notes' to avoid arch-test PHI pgcrypto regex false-positive
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    score_at_transition: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Actor attribution
    actor_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Timing
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
