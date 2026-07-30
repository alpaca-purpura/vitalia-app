# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""LeadActivityModel — SQLAlchemy 2.0 mapped class.

Infrastructure layer — ORM model only. No domain logic.

NON-PHI table: single tenant_id filter only (no clinic_id dual filter).
Distinct from ActivityEventModel (vitalia_activity_events) which is PHI dual-filter.
LeadActivity = commercial/funnel micro-log, NEVER clinical data.

Table: vitalia_lead_activity
Index: ix_la_tenant_lead (tenant_id, lead_id, occurred_at DESC)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class LeadActivityModel(Base):
    """SQLAlchemy model for vitalia_lead_activity table.

    NON-PHI: single tenant_id filter.
    description_es: commercial/funnel timeline text, Spanish neutro LatAm.
    All timestamps use timezone=True (TIMESTAMPTZ at DB level).
    """

    __tablename__ = "vitalia_lead_activity"
    __table_args__ = (
        Index(
            "ix_la_tenant_lead",
            "tenant_id",
            "lead_id",
            "occurred_at",
        ),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Tenant isolation (single filter — Lead is non-PHI)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)

    # Lead reference (no FK — no cross-module JOIN)
    lead_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # Actor attribution
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    # agent | human | lead | system

    # Activity classification
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    # message | stage_move | info_sent | deposit | note

    # Spanish neutro LatAm timeline text — NEVER PHI/clinical
    description_es: Mapped[str] = mapped_column(Text, nullable=False)

    # Timing
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
