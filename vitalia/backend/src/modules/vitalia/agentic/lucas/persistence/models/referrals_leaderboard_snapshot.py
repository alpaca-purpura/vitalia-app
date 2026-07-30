# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""SQLAlchemy 2.0 ORM model — ReferralsLeaderboardSnapshotModel.

Maps to ``referrals_leaderboard_snapshots`` table (created in
019_vitalia_referrals_leaderboard_snapshots.py). Provides the SA 2.0 ORM
surface for the LucasReferralsRepository.

Dual filter ``tenant_id`` + ``clinic_id`` mandatory on all queries.
Soft-delete only (set deleted_at, never hard-delete).

One snapshot per (tenant_id, clinic_id, period_start) enforced
by migration 019 unique partial index (WHERE deleted_at IS NULL).
"""

from __future__ import annotations

import datetime as dt
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Date, DateTime, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


class ReferralsLeaderboardSnapshotModel(Base):
    """ORM mapping for ``referrals_leaderboard_snapshots``.

    Queries MUST filter both tenant_id AND clinic_id.
    top_referrers: list of dicts {referrer_id, name, referral_count, converted_count, rank}.
    """

    __tablename__ = "referrals_leaderboard_snapshots"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    period_start: Mapped[dt.date] = mapped_column(Date, nullable=False)
    period_end: Mapped[dt.date] = mapped_column(Date, nullable=False)
    top_referrers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    total_referrals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_converted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    computed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "ix_referrals_leaderboard_snapshots_tenant_clinic_period",
            "tenant_id",
            "clinic_id",
            "period_start",
            "period_end",
        ),
    )

    def __repr__(self) -> str:
        """Return debug-friendly representation."""
        return f"<ReferralsLeaderboardSnapshotModel id={self.id} period_start={self.period_start}>"
