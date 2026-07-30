# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""SQLAlchemy 2.0 ORM model — VitaliaPlanTierConfigModel.

Maps to `vitalia_plan_tier_configs` table.
CROSS-TENANT global catalog — NO tenant_id, NO deleted_at.
Managed by platform ops; read-only for tenant services.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class VitaliaPlanTierConfigModel(Base):
    """Global plan tier catalog.

    Cross-tenant — one row per pricing tier (solo_doctor / clinic / multi_site).
    No tenant_id (global platform data). No deleted_at (is_active flag instead).
    Seed data inserted in 001_vitalia_initial_snapshot.py.
    """

    __tablename__ = "vitalia_plan_tier_configs"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    # No tenant_id — CROSS-TENANT global catalog
    plan_tier_slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    price_usd_monthly: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    included_user_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_doctors: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # JSONB map of feature flag → bool
    features_enabled: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    # No deleted_at — use is_active=False to deactivate
