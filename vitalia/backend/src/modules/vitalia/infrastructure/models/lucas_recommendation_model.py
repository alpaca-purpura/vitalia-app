# cap: __shared__
# story-origin: TBD
"""SQLAlchemy 2.0 model — LucasRecommendationModel (canonical · shared).

Maps to ``vitalia_lucas_recommendations`` (created 009, extended 028). Shared by
TWO features that both persist to this single physical table:
  - agentic lucas daily-analysis (stage recommendations) — repo
    `agentic/lucas/infrastructure/repositories/stage_recommendation_repository.py`
  - marketing lucas recommendations — repo + service in `marketing/...`

HB-84 (2026-06-16): this consolidates a previous DUPLICATE — there were two ORM
classes (`LucasStageRecommendationModel` 18-col + `LucasRecommendationModel`
24-col) declaring the SAME `__tablename__` on the shared `Base`, which raised
`InvalidRequestError: Table already defined` and broke the arch suite. One model
in shared infrastructure (the established home for cross-module tables — see
booking/payment/consent models here) is the fix. Both feature repos import THIS.

Schema is the 24-col superset, corrected to MATCH the real DDL (migrations 009+028):
  - status VARCHAR(16) (NOT 32 — the old marketing model over-spec'd; longest
    persisted status is agentic `skipped_budget`=14 ≤ 16)
  - title / projected_impact_text TEXT (NOT String(256) — DDL is TEXT)
  - priority DEFAULT 50 (matches DDL)
  - indexes named + scoped exactly as the migrations created them

HIPAA-lite: NO PHI (marketing metrics + budget advice; *_by_user_id are IAM UUIDs).
Lifecycle (status): open → approved (5-min undo) | rejected | expired | undone | skipped_budget.

downstream-regression-na: brand-local shared infrastructure model
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, Index, Integer, SmallInteger, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class LucasRecommendationModel(Base):
    """Lucas recommendation for a clinic (agentic stage analysis + marketing).

    Lifecycle states (status column): open | approved | rejected | expired |
    undone | skipped_budget. undo_until: 5-minute window after approval.
    """

    __tablename__ = "vitalia_lucas_recommendations"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)

    # Bowtie funnel stage: "attraction" | "qualification" | "reservation" | "adoption" | "expansion"
    stage: Mapped[str] = mapped_column(String(32), nullable=False)

    # Recommendation classification (e.g. "increase_budget", "adjust_targeting")
    recommendation_kind: Mapped[str] = mapped_column(String(64), nullable=False)

    # User-facing content (no PHI). DDL: TEXT.
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # AI-generated rationale (metrics evidence, no patient data)
    rationale_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Sort order (higher = more urgent). DDL DEFAULT 50.
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)

    # Lifecycle. DDL: VARCHAR(16).
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")

    # Expiry — cron marks OPEN recs as expired after this datetime
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Optional structured action (e.g. {"action": "increase_budget", "amount_cents": 5000})
    action_payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # AI confidence percentage (0-100)
    confidence_pct: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # Human-readable projected impact (e.g. "+15% CTR estimated"). DDL: TEXT.
    projected_impact_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Approval tracking
    approved_by_user_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 5-minute undo window after approval
    undo_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Rejection tracking
    rejected_by_user_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Index names + columns + partial predicates mirror the real DDL (009 + 028).
    __table_args__ = (
        Index(
            "ix_vitalia_lucas_recommendations_stage_status",
            "tenant_id",
            "clinic_id",
            "stage",
            "status",
            "priority",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "ix_vitalia_lucas_recommendations_expires",
            "tenant_id",
            "clinic_id",
            "expires_at",
            postgresql_where=text("status = 'open'"),
        ),
        Index(
            "ix_vitalia_lucas_recommendations_undo_window",
            "undo_until",
            postgresql_where=text("undo_until IS NOT NULL"),
        ),
    )
