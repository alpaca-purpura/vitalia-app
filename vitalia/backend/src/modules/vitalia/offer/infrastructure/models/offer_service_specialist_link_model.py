# cap: lisa.servicios
"""OfferServiceSpecialistLinkModel — maps to offer_service_specialist_links (045)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, Index
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class OfferServiceSpecialistLinkModel(Base):
    """Links an offer to a specialist doctor (vitalia_doctors roster)."""

    __tablename__ = "offer_service_specialist_links"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    offer_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    doctor_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_offer_service_links_tenant", "tenant_id"),
        Index("ix_offer_service_links_offer", "offer_id"),
    )
