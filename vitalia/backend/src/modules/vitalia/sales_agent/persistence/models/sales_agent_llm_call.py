# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""Vitalia brand schema-mirror for ``sales_agent_llm_call``.

SQLAlchemy 2.0 (mapped_column / Mapped) mirror of the engine model
:class:`luana_core_sales_agent.observability.persistence.models.llm_call_model.SalesAgentLlmCallModel`.

Per .claude/rules/backend-ddd.md schema-mirror exception, builder-backend
MAY create / modify persistence models under
``{brand}/backend/src/modules/{brand}/sales_agent/persistence/models/``
to reflect DDL from engine migrations.

Vitalia-specific additions:
  - ``clinic_id``         — dual filter per HIPAA-lite overlay
  - ``compliance_level``  — always "hipaa_lite" for vitalia

Engine table: ``sales_agent_llm_call``
(owned by luana-core-sales-agent engine migrations).
"""

# downstream-regression-na: schema-mirror only (no engine logic), brand persistence consumer
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import CHAR, Boolean, DateTime, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


class SalesAgentLLMCallVitalia(Base):
    """Vitalia brand schema-mirror of the ``sales_agent_llm_call`` engine table.

    Adds clinic_id (HIPAA-lite dual filter) + compliance_level column.
    Cost columns are denormalized at write time (snapshot pattern).
    """

    __tablename__ = "sales_agent_llm_call"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    clinic_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    lead_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False)
    turn_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    span_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    parent_span_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)

    role: Mapped[str] = mapped_column(String(32), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model_requested: Mapped[str] = mapped_column(String(128), nullable=False)
    model_responded: Mapped[str] = mapped_column(String(128), nullable=False)

    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cached_read_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cached_write_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reasoning_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    pricing_version_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    input_unit_cost_usd: Mapped[Decimal] = mapped_column(Numeric(14, 12), nullable=False)
    output_unit_cost_usd: Mapped[Decimal] = mapped_column(Numeric(14, 12), nullable=False)
    cached_read_unit_cost_usd: Mapped[Decimal] = mapped_column(Numeric(14, 12), nullable=False, default=0)
    # NULL = unknown cost (LiteLLM didn't provide response_cost). Distinct from Decimal("0").
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(16, 10), nullable=True)

    tenant_currency: Mapped[str | None] = mapped_column(CHAR(3), nullable=True)
    fx_rate_to_tenant: Mapped[Decimal | None] = mapped_column(Numeric(16, 8), nullable=True)
    fx_rate_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cost_tenant_currency: Mapped[Decimal | None] = mapped_column(Numeric(16, 8), nullable=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ok")
    error_type: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Vitalia-specific additions
    compliance_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    medical_guardrail_check_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    __table_args__ = (
        Index("ix_sales_agent_llm_call_tenant_time", "tenant_id", "started_at"),
        Index("ix_sales_agent_llm_call_lead", "lead_id"),
    )

    def __repr__(self) -> str:
        """Return debug-friendly representation."""
        return (
            f"<SalesAgentLLMCallVitalia id={self.id} provider={self.provider}"
            f" model={self.model_responded} lead_id={self.lead_id} status={self.status}>"
        )
