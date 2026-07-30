# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""Vitalia brand schema-mirror for ``sales_agent_trace_event``.

SQLAlchemy 2.0 (mapped_column / Mapped) mirror of the engine model
:class:`luana_core_sales_agent.observability.persistence.models.trace_event_model.SalesAgentTraceEventModel`.

Per .claude/rules/backend-ddd.md schema-mirror exception, builder-backend
MAY create / modify persistence models under
``{brand}/backend/src/modules/{brand}/sales_agent/persistence/models/``
to reflect DDL from engine migrations.

Vitalia-specific additions:
  - ``clinic_id``                      — dual filter per HIPAA-lite overlay
  - ``compliance_level``               — always "hipaa_lite" for vitalia
  - ``medical_guardrail_check_passed`` — did medical safety guardrail pass?

Engine table: ``sales_agent_trace_event``
(owned by luana-core-sales-agent engine migrations).
"""

# downstream-regression-na: schema-mirror only (no engine logic), brand persistence consumer
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Boolean, DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class SalesAgentTraceEventVitalia(Base):
    """Vitalia brand schema-mirror of the ``sales_agent_trace_event`` engine table.

    Adds clinic_id (HIPAA-lite dual filter) + vitalia-specific compliance columns.
    """

    __tablename__ = "sales_agent_trace_event"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    clinic_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    lead_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False)
    turn_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    span_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    parent_span_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)

    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ok")

    # Vitalia-specific additions
    compliance_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    medical_guardrail_check_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_sales_agent_trace_event_tenant_lead", "tenant_id", "lead_id"),
        Index("ix_sales_agent_trace_event_turn", "turn_id", "created_at"),
    )

    def __repr__(self) -> str:
        """Return debug-friendly representation."""
        return (
            f"<SalesAgentTraceEventVitalia id={self.id} event_type={self.event_type}"
            f" lead_id={self.lead_id} status={self.status}>"
        )
