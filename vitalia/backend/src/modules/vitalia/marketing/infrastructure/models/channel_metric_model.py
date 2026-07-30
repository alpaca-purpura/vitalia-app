# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""SQLAlchemy 2.0 model — ChannelMetricModel.

Maps to ``vitalia_channel_metrics`` table (base columns from 007_vitalia_initial_tables.py,
additions from 027_slice1_marketing_channel_metrics.py).

HIPAA-lite:
  - NO PHI: metrics table contains campaign performance data only (impressions, clicks, spend).
  - clinic_id: second scope filter (dual filter per hipaa-lite.md § Tenant isolation refuerzo).
  - spend_cents: integer cents to avoid float precision issues (no currency conversion on write).

Natural key for upsert (ON CONFLICT DO UPDATE):
  (tenant_id, clinic_id, provider, channel_slug, campaign_id, metric_date)

downstream-regression-na: brand-local marketing infrastructure model
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import BigInteger, Date, DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class ChannelMetricModel(Base):
    """Daily performance metrics snapshot for a clinic's ad channel.

    Uniquely identified by the natural key:
      (tenant_id, clinic_id, provider, channel_slug, campaign_id, metric_date)

    spend_cents stores spend as integer cents (no float precision issues).
    currency is stored alongside for display purposes (no conversion on write).
    """

    __tablename__ = "vitalia_channel_metrics"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)

    # Provider and channel identification
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    channel_slug: Mapped[str] = mapped_column(String(128), nullable=False)

    # Campaign grouping (None = provider-level aggregate)
    campaign_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    campaign_name: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # The date this snapshot covers
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Performance metrics
    impressions: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    clicks: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    conversions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Spend in integer cents (avoids float precision issues)
    spend_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # ISO 4217 currency code (e.g. "USD", "MXN", "COP")
    # NOT defaulted to "USD" per currency-handling.md — set from provider response
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    # Raw provider API response for audit/debug (no PHI)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # Unique natural key for ON CONFLICT DO UPDATE upsert
        UniqueConstraint(
            "tenant_id",
            "clinic_id",
            "provider",
            "channel_slug",
            "campaign_id",
            "metric_date",
            name="uq_vitalia_channel_metrics_natural_key",
        ),
        Index(
            "ix_vitalia_channel_metrics_clinic_date",
            "tenant_id",
            "clinic_id",
            "metric_date",
        ),
    )
