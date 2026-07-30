# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""SQLAlchemy 2.0 model — ReferralModel.

Maps to ``vitalia_referrals`` table (base columns from 007_vitalia_initial_tables.py,
additions from 029_slice1_marketing_referrals.py,
value columns from 031_slice1_marketing_referrals_value_columns.py).

HIPAA-lite:
  - patient_id: UUID reference only — no name, DNI, or contact data stored here.
  - referred_patient_id: UUID reference to newly registered patient (no PHI).
  - clinic_id: second scope filter (dual filter per hipaa-lite.md § Tenant isolation refuerzo).
  - code: referral tracking code, contains NO PHI.

This table is deliberately PHI-free: it stores only UUID references and
aggregate referral tracking data. The patient record itself lives in the
crm/patients module with full HIPAA-lite protections.

downstream-regression-na: brand-local marketing infrastructure model
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import BigInteger, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class ReferralModel(Base):
    """Patient referral tracking record.

    PHI-free: patient_id and referred_patient_id are UUID references only.
    Full patient data lives in the crm module with PHI protections.

    Status lifecycle per spec § 2.4:
      open → shared → signed_up → converted → expired
    """

    __tablename__ = "vitalia_referrals"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)

    # UUID reference to the referring patient (no name/DNI stored)
    patient_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)

    # Referral code (e.g. "REF-A3B4C5") — no PHI embedded
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    # Lifecycle: "open" | "shared" | "signed_up" | "converted" | "expired"
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")

    # UUID reference to the patient who was referred (set on conversion)
    referred_patient_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)

    # Conversion value in the smallest currency unit (e.g. cents)
    # Set by referrals_value_sync cron from vitalia_appointments.conversion_value_cents
    conversion_value_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # ISO-4217 currency code — NEVER hardcoded, from tenant locale
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    # When the referral code was shared with a prospect
    shared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # When the referred prospect signed up (booked first appointment)
    signed_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Conversion timestamp (appointment completed with non-zero value)
    converted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # When the referral expires (cron job sweeps expired open referrals)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "ix_vitalia_referrals_clinic_status",
            "tenant_id",
            "clinic_id",
            "status",
        ),
        Index(
            "ix_vitalia_referrals_patient",
            "tenant_id",
            "clinic_id",
            "patient_id",
        ),
    )
