# cap: lisa.servicios
"""OfferServiceSalesBriefModel — maps to offer_service_sales_brief (045). NOT PHI.

1:1 per offer. faq/objections/keywords persist as JSONB. Write-through to the engine
Offer happens at the application layer (T-2/T-4).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Boolean, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class OfferServiceSalesBriefModel(Base):
    """Adrián-facing sales brief for an offer (1:1)."""

    __tablename__ = "offer_service_sales_brief"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    offer_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)

    candidate_ideal: Mapped[str | None] = mapped_column(Text, nullable=True)
    contraindications: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualification_questions: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalation_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_evaluation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    emotional_benefits: Mapped[str | None] = mapped_column(Text, nullable=True)
    pain_of_not_treating: Mapped[str | None] = mapped_column(Text, nullable=True)
    differentiators: Mapped[str | None] = mapped_column(Text, nullable=True)
    promos: Mapped[str | None] = mapped_column(Text, nullable=True)
    faq: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    objections: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    keywords: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    problems_solved: Mapped[str | None] = mapped_column(Text, nullable=True)
    language_to_avoid: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_offer_service_sales_brief_tenant", "tenant_id"),)
