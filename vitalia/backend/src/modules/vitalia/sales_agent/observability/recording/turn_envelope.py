# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""Vitalia Adrián sales_agent turn envelope — subclass of engine base.

Story T-ag-tools-2 — R23 production_code=true. Opus 4.7 EXCLUSIVE.

Per .claude/rules/anti-duplication.md § Regla cardinal:
  Observability turn envelope pattern lives in
  ``core/luana-core-observability/src/luana_core_observability/recording/turn_envelope.py``
  (:class:`BaseObservabilityContext`). Vitalia EXTENDS via subclass.
  NEVER mirror plumbing.

What this subclass does (and ONLY this):
  1. Implement abstract ``_add_trace_event`` — writes to vitalia mirror
     of ``sales_agent_trace_event`` (with ``clinic_id`` + ``compliance_level``
     vitalia-specific columns).
  2. Implement abstract ``_aggregate_totals`` — sums vitalia mirror rows of
     ``sales_agent_llm_call`` for the turn.
  3. Implement abstract ``_legacy_compat_keys_or_empty`` — returns ``{}``
     (sales_agent has no JSONB legacy consumer per engine subclass precedent).

What this subclass does NOT do (verified by arch fitness test):
  - Redefine ``observe_turn`` / ``_write_turn_start`` / ``_write_turn_end``
  - Redefine ``set_turn_summary`` / ``set_turn_error`` / ``langchain_config``
  - Redefine ``_commit_session`` / ``_safe_aggregate_totals``
  - Re-implement ``sanitize_payload`` / ``truncate``
  - Mirror ``BaseObservabilityContext`` lifecycle methods

HIPAA-lite (vitalia/.claude/rules/hipaa-lite.md):
  - Trace events include ``clinic_id`` + ``compliance_level`` for audit trail
  - Aggregate totals respects tenant_id + turn_id filters (no cross-tenant leak)

Bug #2 fix lineage (PR-2 PI-1.1 2026-05-01): the lifecycle in engine base now
emits ``turn_start`` + ``turn_end`` rows even when a turn runs without LLM
calls. Vitalia inherits this — no override needed.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import structlog
from luana_core_observability.recording.turn_envelope import (
    BaseObservabilityContext,
    _empty_totals,
)
from sqlalchemy import func, select

from src.modules.vitalia.sales_agent.observability.recording.callback_handler import (
    VitaliaSalesAgentCallbackHandler,
)

if TYPE_CHECKING:
    from luana_core_observability.cost.fx_resolver import FXResolver
    from luana_core_observability.pricing.resolver import PricingResolver
    from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)


@dataclass
class VitaliaSalesAgentObservabilityContext(BaseObservabilityContext):
    """Concrete vitalia sales_agent observability context (turn envelope).

    Inherits the entire lifecycle (``observe_turn``, ``_write_turn_*``,
    ``set_turn_*``, ``langchain_config``, ``_commit_session``) from the
    abstract base.

    Vitalia adds:
      - ``lead_id`` / ``channel_type`` / ``clinic_id`` / ``compliance_level``
        injection onto trace event rows.
      - Aggregation query against vitalia mirror ``sales_agent_llm_call`` table.

    Composition with the callback handler is wired by :meth:`start` —
    one ``VitaliaSalesAgentObservabilityContext`` per turn manages the
    full ``turn_start`` → N×(LLM/tool/chain events) → ``turn_end`` lifecycle.
    """

    lead_id: UUID | None = None
    channel_type: str = ""
    clinic_id: UUID | None = None
    compliance_level: str = "hipaa_lite"  # Vitalia constant

    @classmethod
    def start(
        cls,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        channel_type: str,
        clinic_id: UUID | None,
        llm_call_repo: Any,  # protocol with .add(**kwargs) + .db (Session)
        trace_repo: Any,  # protocol with .add(**kwargs) + .db (Session)
        pricing_resolver: PricingResolver,
        fx_resolver: FXResolver,
        db_session: Session,
        tenant_currency: str = "USD",
        role: str = "sales_agent",
        compliance_level: str = "hipaa_lite",
        turn_id: UUID | None = None,
    ) -> VitaliaSalesAgentObservabilityContext:
        """Build a fresh vitalia sales_agent context for one turn.

        Allocates ``turn_id`` if not provided. Wires the
        :class:`VitaliaSalesAgentCallbackHandler` with the same repos +
        resolvers so ``_commit_session`` covers the same Unit of Work.
        """
        tid = turn_id or uuid4()
        handler = VitaliaSalesAgentCallbackHandler(
            tenant_id=tenant_id,
            turn_id=tid,
            lead_id=lead_id,
            channel_type=channel_type,
            clinic_id=clinic_id,
            compliance_level=compliance_level,
            llm_call_repo=llm_call_repo,
            trace_repo=trace_repo,
            pricing_resolver=pricing_resolver,
            fx_resolver=fx_resolver,
            db_session=db_session,
            tenant_currency=tenant_currency,
            role=role,
        )
        return cls(
            tenant_id=tenant_id,
            turn_id=tid,
            callback_handler=handler,
            trace_repo=trace_repo,
            llm_call_repo=llm_call_repo,
            lead_id=lead_id,
            channel_type=channel_type,
            clinic_id=clinic_id,
            compliance_level=compliance_level,
        )

    # ── Abstract hook implementations ──────────────────────────────────

    def _add_trace_event(
        self,
        *,
        event_type: str,
        name: str,
        data: dict[str, Any],
        duration_ms: int | None = None,
        status: str = "ok",
        span_id: UUID | None = None,
    ) -> None:
        """Persist one row to vitalia ``sales_agent_trace_event`` mirror.

        Includes vitalia-specific columns: ``clinic_id``, ``compliance_level``.

        Best-effort per engine base contract — failures swallowed with
        structlog warning. The outer ``_write_turn_*`` is already wrapped.
        """
        try:
            self.trace_repo.add(
                tenant_id=self.tenant_id,
                lead_id=self.lead_id,
                channel_type=self.channel_type,
                clinic_id=self.clinic_id,
                compliance_level=self.compliance_level,
                turn_id=self.turn_id,
                span_id=span_id or uuid4(),
                event_type=event_type,
                name=name,
                data=data,
                duration_ms=duration_ms,
                status=status,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning(
                "vitalia.sales_agent.obs.add_trace_event_failed",
                event_type=event_type,
                error=str(exc),
            )

    def _aggregate_totals(self) -> dict[str, Any]:
        """Sum vitalia ``sales_agent_llm_call`` rows for this turn.

        Imports the vitalia schema-mirror model lazily to avoid SQLAlchemy
        circular imports at module-load time. Filters by
        (tenant_id, turn_id) — tenant isolation cardinal.

        Best-effort: returns :func:`_empty_totals` on failure.
        """
        try:
            from src.modules.vitalia.sales_agent.persistence.models.sales_agent_llm_call import (  # noqa: PLC0415
                SalesAgentLLMCallVitalia,
            )

            session = self.llm_call_repo.db
            with contextlib.suppress(Exception):
                session.flush()
            stmt = select(
                func.count().label("count"),
                func.coalesce(func.sum(SalesAgentLLMCallVitalia.input_tokens), 0).label(
                    "input_tokens",
                ),
                func.coalesce(func.sum(SalesAgentLLMCallVitalia.output_tokens), 0).label(
                    "output_tokens",
                ),
                func.coalesce(func.sum(SalesAgentLLMCallVitalia.cached_read_tokens), 0).label(
                    "cached_read_tokens",
                ),
                func.coalesce(func.sum(SalesAgentLLMCallVitalia.cost_usd), 0).label("cost_usd"),
            ).where(
                SalesAgentLLMCallVitalia.tenant_id == self.tenant_id,
                SalesAgentLLMCallVitalia.turn_id == self.turn_id,
            )
            row = session.execute(stmt).one()
            return {
                "llm_call_count": int(row.count),
                "total_input_tokens": int(row.input_tokens),
                "total_output_tokens": int(row.output_tokens),
                "total_cached_read_tokens": int(row.cached_read_tokens),
                "total_cost_usd": str(Decimal(row.cost_usd)),
                "model_responded": self._most_used_model(session),
            }
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning("vitalia.sales_agent.obs.aggregate_totals_failed", error=str(exc))
            return _empty_totals()

    def _most_used_model(self, session: Any) -> str:  # noqa: ANN401 — Session
        """Pick the model with the most LLM calls for this turn."""
        try:
            from src.modules.vitalia.sales_agent.persistence.models.sales_agent_llm_call import (  # noqa: PLC0415
                SalesAgentLLMCallVitalia,
            )

            stmt = (
                select(
                    SalesAgentLLMCallVitalia.model_responded,
                    func.count().label("c"),
                )
                .where(
                    SalesAgentLLMCallVitalia.tenant_id == self.tenant_id,
                    SalesAgentLLMCallVitalia.turn_id == self.turn_id,
                )
                .group_by(SalesAgentLLMCallVitalia.model_responded)
                .order_by(func.count().desc())
                .limit(1)
            )
            row = session.execute(stmt).first()
            return str(row.model_responded) if row is not None else ""
        except Exception:  # noqa: BLE001 — best-effort
            return ""

    def _legacy_compat_keys_or_empty(self, totals: dict[str, Any]) -> dict[str, Any]:
        """Vitalia sales_agent has NO legacy JSONB consumer — return ``{}``.

        Per engine base contract + sales_agent precedent (engine subclass
        :class:`SalesAgentObservabilityContext` does the same).
        """
        del totals  # interface contract — unused
        return {}


__all__ = ["VitaliaSalesAgentObservabilityContext"]
