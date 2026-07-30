# cap: lisa.servicios
"""OfferServiceCaseModel — maps to offer_service_cases (045). PHI (patient photos).

Holds before/after patient images → PHI under HIPAA-lite. clinic_id present for the
dual filter. consent_signed is the persist gate (RN-33) enforced at the repo layer.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class OfferServiceCaseModel(Base):
    """Before/after patient case (PHI)."""

    __tablename__ = "offer_service_cases"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    offer_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    clinic_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)

    before_asset_url: Mapped[str] = mapped_column(String, nullable=False)
    after_asset_url: Mapped[str] = mapped_column(String, nullable=False)
    consent_signed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    consent_ref: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_offer_service_cases_tenant", "tenant_id"),
        Index("ix_offer_service_cases_offer", "offer_id"),
    )
