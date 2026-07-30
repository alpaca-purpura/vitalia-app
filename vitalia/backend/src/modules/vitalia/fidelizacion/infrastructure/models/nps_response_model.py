# cap: patients.nps-tracking
# story-origin: TBD
"""SQLAlchemy 2.0 model — vitalia_nps_responses.

Mapea la tabla creada en migration 022.
PHI: comment BYTEA (pgcrypto — comentario libre del paciente).
Dual filter: tenant_id + clinic_id (HIPAA-lite vitalia).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Boolean, DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class NPSResponseModel(Base):
    """ORM model para vitalia_nps_responses.

    PHI: comment (BYTEA pgcrypto — comentario libre del paciente).
    Score CHECK 0-10 (enforced en DB migration 022 + dominio entity).
    Soft delete: deleted_at.
    """

    __tablename__ = "vitalia_nps_responses"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    patient_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)

    appointment_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    band: Mapped[str] = mapped_column(String(16), nullable=False)

    # PHI — cifrado pgcrypto (symmetric encryption at rest, hipaa-lite.md)
    comment: Mapped[bytes | None] = mapped_column(BYTEA, nullable=True)

    source: Mapped[str] = mapped_column(String(32), nullable=False, server_default="whatsapp_template")
    trigger_re_engagement_event_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    responded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    tagged_in_inbox: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    audit_log_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "ix_vitalia_nps_responses_tenant_clinic_band",
            "tenant_id",
            "clinic_id",
            "band",
            "responded_at",
        ),
        Index(
            "ix_vitalia_nps_responses_patient",
            "tenant_id",
            "clinic_id",
            "patient_id",
            "responded_at",
        ),
    )
