# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""SQLAlchemy 2.0 ORM model — VitaliaDoctorExtensionModel.

Maps to `vitalia_doctor_extensions` table.
Medical extensions to doctor profile (extends @luana/core/scheduling doctor entity).
Unique per (tenant_id, doctor_id). Soft-delete.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class VitaliaDoctorExtensionModel(Base):
    """Medical extension to doctor profile.

    Extends the core scheduling doctor entity with medical-vertical data:
    specialty, treatment room, concurrent capacity, offer associations.
    One row per doctor per tenant. Unique constraint (tenant_id, doctor_id).
    tenant_id is NOT NULL + indexed (R2 tenant-isolation).
    deleted_at enables soft-delete.
    """

    __tablename__ = "vitalia_doctor_extensions"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    # References doctor entity in @luana/core/scheduling domain
    doctor_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    specialty: Mapped[str | None] = mapped_column(String(64), nullable=True)
    treatment_room: Mapped[str | None] = mapped_column(String(64), nullable=True)
    max_concurrent_per_slot: Mapped[int] = mapped_column(nullable=False, default=1)
    # JSONB list of appointment type slugs
    appointment_types: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # JSONB list of offer UUIDs this doctor provides
    available_offer_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "doctor_id",
            name="uq_vitalia_doctor_extensions_doctor",
        ),
    )
