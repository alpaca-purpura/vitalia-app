# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""VitaliaCopilotObservabilityContext — brand subclass of engine BaseObservabilityContext.

Per .claude/rules/anti-duplication.md § 0 cardinal: this file inherits from
``luana_core_observability.recording.turn_envelope.BaseObservabilityContext``
(SSoT). NEVER duplicate ``observe_turn``, ``_write_turn_start``,
``_write_turn_end``, ``set_turn_summary``, ``set_turn_error``,
``langchain_config``, ``_commit_session``, ``_safe_aggregate_totals``,
``_safe_legacy_compat_keys`` — those live in engine.

This module overrides ONLY:
- :meth:`_add_trace_event` — passes vitalia-specific kwargs (conversation_id,
  user_id, clinic_id, compliance_level) to the trace repo.
- :meth:`_aggregate_totals` — sums vitalia ``copilot_llm_call`` rows for the
  current turn (uses ``CopilotLLMCallVitalia`` schema mirror).
- :meth:`_legacy_compat_keys_or_empty` — returns ``{}`` (Streamlit ``/trazas``
  is owned by engine copilot; vitalia brand panels read schema mirror directly).

Best-effort: persistence wrapping via try/except + structlog warning lives in
base; the abstract hooks themselves use a defensive try/except so a single
broken row never leaks out of ``observe_turn``.

Reference: ``.claude/rules/anti-duplication.md`` § Inventario row
"Observability turn envelope" → consumed by copilot + sales_agent.
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

from src.modules.vitalia.copilot.observability.recording.callback_handler import (
    VitaliaCopilotCallbackHandler,
)
from src.modules.vitalia.copilot.persistence.models.copilot_llm_call import (
    CopilotLLMCallVitalia,
)

if TYPE_CHECKING:
    from luana_core_observability.cost.fx_resolver import FXResolver
    from luana_core_observability.pricing.resolver import PricingResolver

logger = structlog.get_logger()


@dataclass
class VitaliaCopilotObservabilityContext(BaseObservabilityContext):
    """Vitalia copilot per-turn observability envelope.

    Inherits the full lifecycle (``observe_turn`` + ``_write_turn_*`` +
    ``set_turn_*`` + ``langchain_config`` + ``_commit_session``) from engine
    :class:`BaseObservabilityContext`. Implements the three abstract hooks.

    Vitalia-specific attributes (set on construction via :meth:`start`):
      - ``conversation_id`` — copilot conversation UUID
      - ``user_id`` — initiating user UUID
      - ``clinic_id`` — HIPAA-lite dual filter (optional during wizard)
      - ``compliance_level`` — always ``"hipaa_lite"``
    """

    conversation_id: UUID | None = None
    user_id: UUID | None = None
    clinic_id: UUID | None = None
    compliance_level: str = "hipaa_lite"

    @classmethod
    def start(
        cls,
        *,
        tenant_id: UUID,
        conversation_id: UUID | None,
        user_id: UUID | None,
        llm_call_repo: Any,
        trace_repo: Any,
        pricing_resolver: PricingResolver,
        fx_resolver: FXResolver,
        clinic_id: UUID | None = None,
        compliance_level: str = "hipaa_lite",
        tenant_currency: str = "USD",
        role: str = "agent",
        turn_id: UUID | None = None,
    ) -> VitaliaCopilotObservabilityContext:
        """Build a fresh vitalia copilot context. Turn id allocated if absent."""
        tid = turn_id or uuid4()
        handler = VitaliaCopilotCallbackHandler(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            user_id=user_id,
            clinic_id=clinic_id,
            compliance_level=compliance_level,
            turn_id=tid,
            llm_call_repo=llm_call_repo,
            trace_repo=trace_repo,
            pricing_resolver=pricing_resolver,
            fx_resolver=fx_resolver,
            tenant_currency=tenant_currency,
            role=role,
        )
        return cls(
            tenant_id=tenant_id,
            turn_id=tid,
            callback_handler=handler,
            trace_repo=trace_repo,
            llm_call_repo=llm_call_repo,
            conversation_id=conversation_id,
            user_id=user_id,
            clinic_id=clinic_id,
            compliance_level=compliance_level,
        )

    # ── Abstract hook impls ────────────────────────────────────────────

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
        """Persist one row to vitalia ``copilot_trace_event`` (schema mirror).

        Best-effort: failure is logged via structlog warning and swallowed
        (base ``_write_turn_*`` already wraps the outer call).
        """
        try:
            self.trace_repo.add(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                conversation_id=self.conversation_id,
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
                "vitalia.copilot.observability.add_trace_event_failed",
                event_type=event_type,
                error=str(exc),
            )

    def _aggregate_totals(self) -> dict[str, Any]:
        """Sum vitalia ``copilot_llm_call`` rows for this turn.

        Flushes the session first so rows added by the callback handler
        during the turn (which only ``session.add`` without committing) are
        visible to the aggregate SELECT.

        Best-effort: returns :func:`_empty_totals` on failure.
        """
        try:
            session = self.llm_call_repo.db
            with contextlib.suppress(Exception):
                session.flush()
            stmt = select(
                func.count().label("count"),
                func.coalesce(func.sum(CopilotLLMCallVitalia.input_tokens), 0).label(
                    "input_tokens",
                ),
                func.coalesce(func.sum(CopilotLLMCallVitalia.output_tokens), 0).label(
                    "output_tokens",
                ),
                func.coalesce(func.sum(CopilotLLMCallVitalia.cached_read_tokens), 0).label("cached_read_tokens"),
                func.coalesce(func.sum(CopilotLLMCallVitalia.cost_usd), 0).label("cost_usd"),
            ).where(
                CopilotLLMCallVitalia.tenant_id == self.tenant_id,
                CopilotLLMCallVitalia.turn_id == self.turn_id,
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
            logger.warning(
                "vitalia.copilot.observability.aggregate_totals_failed",
                error=str(exc),
            )
            return _empty_totals()

    def _most_used_model(self, session: Any) -> str:  # noqa: ANN401 — Session
        """Pick the model with the most LLM calls for this turn."""
        try:
            stmt = (
                select(
                    CopilotLLMCallVitalia.model_responded,
                    func.count().label("c"),
                )
                .where(
                    CopilotLLMCallVitalia.tenant_id == self.tenant_id,
                    CopilotLLMCallVitalia.turn_id == self.turn_id,
                )
                .group_by(CopilotLLMCallVitalia.model_responded)
                .order_by(func.count().desc())
                .limit(1)
            )
            row = session.execute(stmt).first()
            return str(row.model_responded) if row is not None else ""
        except Exception:  # noqa: BLE001 — best-effort
            return ""

    def _legacy_compat_keys_or_empty(self, totals: dict[str, Any]) -> dict[str, Any]:
        """Vitalia returns ``{}`` — brand panels read the schema mirror directly.

        Engine copilot subclass populates the JSONB legacy shape for Streamlit
        ``/trazas`` + ``/copilot-routing`` consumers. Vitalia is a separate
        brand with its own admin surfaces; those consume the typed columns
        (``cost_usd``, ``input_tokens``, etc.) directly.
        """
        return {}


__all__ = ["VitaliaCopilotObservabilityContext"]
