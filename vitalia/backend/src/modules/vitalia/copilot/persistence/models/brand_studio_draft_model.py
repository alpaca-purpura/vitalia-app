# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""BrandStudioDraftModel — SQLA 2.0 ORM for vitalia_brand_studio_drafts table.

Mirrors the DDL from migration 012_vitalia. No autogenerate — raw SQL migrations.
Not PHI: brand identity extraction staging (clinic name, vertical, voice samples).
Single tenant_id filter — brand studio is tenant-level config, no clinic_id required.

Per .claude/rules/backend-ddd.md — ORM model in persistence layer,
domain entity in domain layer, no cross-import in wrong direction.
"""

# downstream-regression-na: brand-local brand studio draft model, no cross-brand consumers
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


class BrandStudioDraftModel(Base):
    """SQLAlchemy 2.0 ORM model for vitalia_brand_studio_drafts.

    Table DDL: migration 012_vitalia.
    Uncommitted drafts have committed_at=NULL and a TTL via expires_at.
    Committed drafts have committed_at set; expires_at is informational.
    """

    __tablename__ = "vitalia_brand_studio_drafts"

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=False,
    )
    draft_kind: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="onboarding_extraction",
    )
    draft_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    voice_profile_partial_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    committed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
