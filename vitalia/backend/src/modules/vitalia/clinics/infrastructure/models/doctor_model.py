# cap: clinics.lisa.doctores
"""VitaliaDoctorModel — SQLAlchemy 2.0 model for vitalia_doctors table.

PII columns (dni/email/phone/credential) are stored as BYTEA ciphertext.
Encryption/decryption via pgcrypto pgp_sym_encrypt / pgp_sym_decrypt in repository.
dni_hash (HMAC-SHA256 + KEK) enables unique constraint on DNI without plaintext.

Migration: 036_f2_s8_vitalia_lisa_staff.py
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class VitaliaDoctorModel(Base):
    """Doctor profile entity for a Vitalia clinic staff member.

    PII columns stored as BYTEA ciphertext (pgcrypto symmetric encryption):
      - dni_encrypted: patient DNI/document number
      - email_encrypted: professional contact email
      - phone_encrypted: mobile phone (nullable)
      - credential_encrypted: credential number (CMP/matrícula/cédula/registro)

    dni_hash: HMAC-SHA256 of raw DNI + KEK — used for unique constraint
    because encrypted BYTEA bytes differ per call and can't be compared directly.

    Unique constraint: (tenant_id, dni_hash) — prevents duplicate DNI per tenant.
    """

    __tablename__ = "vitalia_doctors"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)

    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)

    # PII — stored as BYTEA ciphertext (pgcrypto)
    dni_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    email_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    phone_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    credential_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    # dni_hash: HMAC-SHA256(dni, KEK) — for unique constraint (not reversible)
    dni_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Non-PII metadata
    specialty: Mapped[str | None] = mapped_column(String(128), nullable=True)
    credential_country: Mapped[str] = mapped_column(String(2), nullable=False)
    years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    languages: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    # Bio inputs for generation
    bio_inputs_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    bio_links: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    bio_public: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Structured public profile (D3-D) — supersedes bio_public (kept for compat)
    public_profile: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    """Structured 6-section public profile: sobre_mi, formacion[], experiencia[],
    tratamientos[], certificaciones[], idiomas[]. Migration 041."""

    bio_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    """Timestamp of last profile/bio generation (RN-D3D-4 material_new detection). Migration 041."""

    public_slug: Mapped[str | None] = mapped_column(String(256), nullable=True)
    """URL-safe slug for public doctor profile page. Unique per tenant+clinic. Migration 041."""

    # Landing visibility
    avatar_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    visible_en_landing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # Unique DNI per tenant (via deterministic hash — not plaintext)
        UniqueConstraint("tenant_id", "dni_hash", name="uq_vitalia_doctors_tenant_dni"),
        # Composite indexes for common queries
        Index("ix_vitalia_doctors_tenant_clinic", "tenant_id", "clinic_id"),
        Index("ix_vitalia_doctors_tenant_specialty", "tenant_id", "specialty"),
        Index("ix_vitalia_doctors_tenant_active", "tenant_id", "active"),
        Index(
            "ix_vitalia_doctors_tenant_visible_active",
            "tenant_id",
            "visible_en_landing",
            "active",
        ),
    )
