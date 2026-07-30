# cap: lisa.servicios
"""OfferServiceExtModel — maps to offer_service_ext (migration 045_vitalia).

Brand projection over the engine Offer (offer_id → products.id, no hard FK at T-1).
VO bundles (variants, pricing, intervals) persist as JSONB. NOT PHI (RN-13).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class OfferServiceExtModel(Base):
    """Brand-level extension of a medical service offer."""

    __tablename__ = "offer_service_ext"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    offer_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    modality: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    canonical_service_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    clinic_scope: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)

    description_long: Mapped[str | None] = mapped_column(Text, nullable=True)
    includes: Mapped[str | None] = mapped_column(Text, nullable=True)
    excludes: Mapped[str | None] = mapped_column(Text, nullable=True)
    warranty: Mapped[str | None] = mapped_column(Text, nullable=True)
    variants: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")

    procedure_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    anesthesia_pain: Mapped[str | None] = mapped_column(Text, nullable=True)
    prep: Mapped[str | None] = mapped_column(Text, nullable=True)
    aftercare: Mapped[str | None] = mapped_column(Text, nullable=True)
    downtime: Mapped[str | None] = mapped_column(Text, nullable=True)

    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_timing: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_lifespan: Mapped[str | None] = mapped_column(Text, nullable=True)
    realistic_expectations: Mapped[str | None] = mapped_column(Text, nullable=True)

    risks: Mapped[str | None] = mapped_column(Text, nullable=True)
    red_flags: Mapped[str | None] = mapped_column(Text, nullable=True)

    session_interval: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    recurrence_interval: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    initial_appt_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    initial_appt_type: Mapped[str | None] = mapped_column(String, nullable=True)
    pricing: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    candidate_for_library: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_offer_service_ext_tenant", "tenant_id"),)
