# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""OnboardingProgressModel — SQLA 2.0 ORM for vitalia_onboarding_progress table.

Mirrors the DDL from migration 011_vitalia. No autogenerate — raw SQL migrations.
Not PHI: wizard onboarding config (step, slot state, mode). Single tenant_id filter.

Per .claude/rules/backend-ddd.md — ORM model in persistence layer,
domain entity in domain layer, no cross-import in wrong direction.
"""

# downstream-regression-na: brand-local onboarding persistence model, no cross-brand consumers
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


class OnboardingProgressModel(Base):
    """SQLAlchemy 2.0 ORM model for vitalia_onboarding_progress.

    Table DDL: migration 011_vitalia.
    Unique constraint: (tenant_id, user_id) — one active session per user.
    Soft delete: status='abandoned' (no deleted_at per migration spec).
    """

    __tablename__ = "vitalia_onboarding_progress"

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
    step: Mapped[str] = mapped_column(String(64), nullable=False)
    slots_confirmed: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    slots_pending: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    mode: Mapped[str | None] = mapped_column(String(16), nullable=True)
    draft_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=True,
    )
    attachments: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="in_progress",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
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
