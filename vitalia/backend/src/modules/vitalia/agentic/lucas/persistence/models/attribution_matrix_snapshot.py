# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""SQLAlchemy 2.0 ORM model — AttributionMatrixSnapshotModel.

Maps to ``attribution_matrix_snapshots`` table (created in
018_vitalia_attribution_matrix_snapshots.py). Provides the SA 2.0 ORM
surface for the LucasAttributionRepository.

Dual filter ``tenant_id`` + ``clinic_id`` mandatory on all queries.
Soft-delete only (set deleted_at, never hard-delete).

Currency stored as ISO-4217 from tenant locale — NEVER hardcoded.
One snapshot per (tenant_id, clinic_id, period_start) enforced by
migration 018 unique partial index (WHERE deleted_at IS NULL).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import CHAR, Date, DateTime, Index, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


class AttributionMatrixSnapshotModel(Base):
    """ORM mapping for ``attribution_matrix_snapshots``.

    Queries MUST filter both tenant_id AND clinic_id.
    """

    __tablename__ = "attribution_matrix_snapshots"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    period_start: Mapped[dt.date] = mapped_column(Date, nullable=False)
    period_end: Mapped[dt.date] = mapped_column(Date, nullable=False)
    channel_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    total_attributed_revenue: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    # ISO-4217 from tenant locale. Never hardcoded. See .claude/rules/currency-handling.md
    currency: Mapped[str | None] = mapped_column(CHAR(3), nullable=True)
    computed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "ix_attribution_matrix_snapshots_tenant_clinic_period",
            "tenant_id",
            "clinic_id",
            "period_start",
            "period_end",
        ),
    )

    def __repr__(self) -> str:
        """Return debug-friendly representation."""
        return (
            f"<AttributionMatrixSnapshotModel id={self.id} period_start={self.period_start} tenant_id={self.tenant_id}>"
        )
