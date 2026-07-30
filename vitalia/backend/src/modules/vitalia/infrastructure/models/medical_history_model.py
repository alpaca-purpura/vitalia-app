# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""SQLAlchemy 2.0 ORM models — VitaliaPatientMedicalHistoryModel + VitaliaPatientDentalHistoryModel.

Maps to `vitalia_patient_medical_histories` and `vitalia_patient_dental_histories` tables.
LLM-extracted patient histories. Soft-delete. Grouped in one file per § 3.1 layout.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class VitaliaPatientMedicalHistoryModel(Base):
    """LLM-extracted general medical history.

    Stores structured extraction results from patient intake documents or
    copilot conversation. extraction_confidence in [0, 1] range (NUMERIC 3,2).
    extracted_payload is open JSONB — schema governed by extractor version.
    tenant_id is NOT NULL + indexed (R2 tenant-isolation).
    deleted_at enables soft-delete.
    """

    __tablename__ = "vitalia_patient_medical_histories"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    patient_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    extraction_confidence: Mapped[Decimal | None] = mapped_column(Numeric(precision=3, scale=2), nullable=True)
    extracted_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    extractor_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_extracted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # JSONB list of source document IDs used for extraction
    source_document_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VitaliaPatientDentalHistoryModel(Base):
    """LLM-extracted dental history (odontogram-aware).

    Extends the general medical history pattern with dental-specific fields:
    missing_pieces_fdi (FDI tooth numbering system), restorations JSONB map.
    tenant_id is NOT NULL + indexed (R2 tenant-isolation).
    deleted_at enables soft-delete.
    """

    __tablename__ = "vitalia_patient_dental_histories"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    patient_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    # FDI numbering: list of missing tooth numbers e.g. [18, 28, 38]
    missing_pieces_fdi: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # Map of tooth FDI number → restoration details
    restorations: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    extraction_confidence: Mapped[Decimal | None] = mapped_column(Numeric(precision=3, scale=2), nullable=True)
    extracted_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    extractor_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_extracted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # JSONB list of source document IDs used for extraction
    source_document_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
