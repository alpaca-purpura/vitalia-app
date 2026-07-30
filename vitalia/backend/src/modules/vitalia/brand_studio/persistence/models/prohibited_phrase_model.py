# cap: brand_studio.brand-studio-medical-sections
# story-origin: vitalia-fase2-s7-TBD
"""VitaliaProhibitedPhraseModel — SA 2.0 model for vitalia_prohibited_phrases table.

Brand-local prohibited phrases for soft warning UI.
tenant_id NULL → seed default (cross-tenant baseline). UUID → tenant override.
NO PHI; safe for full text indexing.

Migration: shipped T-1 (033_f2_s7_vitalia_lisa_marca.py).
downstream-regression-na: brand-local SQLA model vitalia
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


class VitaliaProhibitedPhraseModel(Base):
    """SA 2.0 model — vitalia brand-local prohibited phrases table.

    tenant_id NULL → seed default (cross-tenant baseline). UUID → tenant override.
    NO PHI; safe for full text indexing.

    Composite indexes (created by migration T-1):
      - idx_vit_phrase_tenant_severity (tenant_id, severity) WHERE deleted_at IS NULL
      - idx_vit_phrase_country_severity (country_scope, severity) WHERE deleted_at IS NULL AND tenant_id IS NULL
      - idx_vit_phrase_lookup (phrase) WHERE deleted_at IS NULL
    """

    __tablename__ = "vitalia_prohibited_phrases"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True, index=True)
    phrase: Mapped[str] = mapped_column(String(200), nullable=False)
    suggested_alternative: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    country_scope: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
