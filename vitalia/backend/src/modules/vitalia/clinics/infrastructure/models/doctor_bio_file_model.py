# cap: clinics.lisa.doctores
"""VitaliaDoctorBioFileModel — SQLAlchemy 2.0 model for vitalia_doctor_bio_files.

Maps to the table created in migration 040_vitalia_doctor_bio_files.py.
The binary lives in the assets storage backend (R2/local) under storage_key —
this row is the tenant-scoped registry (listing / soft delete / download audit /
RN-D3D-4 material-new detection via uploaded_at).

No PHI columns — bio material metadata (filename/size/type), not patient data;
dual filter (tenant_id + clinic_id) applied anyway per hipaa-lite consistency.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import BigInteger, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class VitaliaDoctorBioFileModel(Base):
    """A private bio material file registered for a doctor (delta v3 D3-B)."""

    __tablename__ = "vitalia_doctor_bio_files"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    doctor_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)

    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_doctor_bio_files_scope", "tenant_id", "clinic_id", "doctor_id"),
        Index("ix_doctor_bio_files_tenant", "tenant_id"),
    )
