# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""Vitalia Adrián sales_agent callback handler — subclass of engine base.

Story T-ag-tools-2 — R23 production_code=true. Opus 4.7 EXCLUSIVE.

Per .claude/rules/anti-duplication.md § Regla cardinal:
  Observability/cost/pricing/turn_envelope/callback-handler patterns live in
  ``core/luana-core-observability/``. Vitalia EXTENDS via subclass.
  NEVER mirror plumbing.

What this subclass does (and ONLY this):
  1. Implement abstract ``_persist_llm_call_row`` — writes to vitalia mirror
     of ``sales_agent_llm_call`` (with ``clinic_id`` + ``compliance_level``
     vitalia-specific columns).
  2. Implement abstract ``_persist_trace_event_row`` — writes to vitalia mirror
     of ``sales_agent_trace_event`` (with same vitalia-specific columns).
  3. Apply ``sanitize_payload`` with ``compliance_level="hipaa_lite"`` on the
     vitalia-specific path (engine base already calls ``sanitize_payload`` —
     this is extra defense-in-depth for PHI fields).

What this subclass does NOT do (verified by arch fitness test):
  - Redefine ``on_chat_model_start`` / ``on_llm_end`` / ``on_llm_error``
  - Redefine ``on_tool_start`` / ``on_tool_end`` / ``on_tool_error``
  - Redefine ``on_chain_start`` / ``on_chain_end``
  - Redefine ``_persist_llm_call`` Template Method skeleton
  - Re-implement ``sanitize_payload`` / ``truncate`` / ``redact_value``
  - Re-implement ``PricingResolver`` / ``FXResolver`` / ``pop_cost``
  - Mirror ``calculate_cost`` reconciliation utility

Cost canonicalization (PI-12 S1 T-1 cement 2026-05-02):
  - ``cost_usd`` consumed via ``pop_cost(litellm_call_id)`` (engine base path)
  - Test fixtures inject ``litellm_call_id`` in ``response_metadata``
  - This subclass NEVER recomputes cost — relies on engine base

HIPAA-lite (vitalia/.claude/rules/hipaa-lite.md):
  - ``sanitize_payload(compliance_level="hipaa_lite")`` applied at persist hook
    (defense-in-depth — base already sanitizes, vitalia re-sanitizes the row
    payload before write to filter against the 22 canonical PHI fields).
  - ``try/except + structlog.warning + _safe_rollback`` per best-effort rule
    (inherited from engine base via ``_safe_rollback``; this subclass adds
    its own try/except around the repo write).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog
from luana_core_observability.recording.base_callback_handler import (
    BaseAgentCallbackHandler,
)

from src.modules.vitalia.compliance.application.compliance_service_adapter import (
    sanitize_phi_payload,
)

logger = structlog.get_logger(__name__)


@dataclass
class VitaliaSalesAgentCallbackHandler(BaseAgentCallbackHandler):
    """Subclass of engine ``BaseAgentCallbackHandler`` with vitalia injection.

    Inherits the entire 8-callback LangChain plumbing from the abstract base
    (``on_chat_model_start`` / ``on_llm_end`` / ``on_llm_error`` /
    ``on_tool_start`` / ``on_tool_end`` / ``on_tool_error`` /
    ``on_chain_start`` / ``on_chain_end``) plus the ``_persist_llm_call``
    Template Method skeleton (sanitize → resolve pricing → calculate cost →
    persist).

    This subclass adds:
      - ``lead_id`` / ``channel_type`` / ``clinic_id`` / ``compliance_level``
        injection onto every persisted row (vitalia schema-mirror addition).
      - ``llm_call_repo`` / ``trace_repo`` repository deps (sync interface
        with ``.add(**kwargs)`` shape).
      - Best-effort wrapping around the actual repo writes (engine base
        already wraps but defense-in-depth in case repo internals fail).

    Repos accept any concrete that exposes ``.add(**kwargs)`` — wired by the
    factory at orchestrator init.
    """

    lead_id: Any = None  # UUID — defaulted to None for dataclass inheritance ordering
    channel_type: str = ""
    clinic_id: Any = None  # UUID | None — populated per turn
    compliance_level: str = "hipaa_lite"  # Vitalia constant
    llm_call_repo: Any = None  # protocol with .add(**kwargs)
    trace_repo: Any = None  # protocol with .add(**kwargs)
    db_session: Any = None  # SQLAlchemy Session — for _safe_rollback hook

    # ── Abstract method implementations (Template Method) ────────────────

    def _persist_llm_call_row(self, **kwargs: Any) -> None:  # noqa: ANN401 — Template Method passthrough
        """Persist one row to vitalia ``sales_agent_llm_call`` mirror.

        Vitalia-specific kwargs added on top of base contract:
          - ``lead_id``: required
          - ``channel_type``: required
          - ``clinic_id``: optional but populated for HIPAA-lite turns
          - ``compliance_level``: "hipaa_lite" constant

        Best-effort: failures swallowed with structlog warning + rollback.
        """
        if self.llm_call_repo is None:
            logger.warning("vitalia.sales_agent.observability.llm_call_repo_unset")
            return
        try:
            # Defense-in-depth sanitization (engine base also sanitizes; this
            # re-runs the 22 PHI-field pass to catch any agent-specific kwargs
            # that may have slipped through).
            safe_kwargs = sanitize_phi_payload(dict(kwargs))
            self.llm_call_repo.add(
                parent_span_id=None,
                lead_id=self.lead_id,
                channel_type=self.channel_type,
                clinic_id=self.clinic_id,
                compliance_level=self.compliance_level,
                **safe_kwargs,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning(
                "vitalia.sales_agent.observability.llm_call_persist_failed",
                error=str(exc),
            )
            self._safe_rollback()

    def _persist_trace_event_row(self, **kwargs: Any) -> None:  # noqa: ANN401 — Template Method passthrough
        """Persist one row to vitalia ``sales_agent_trace_event`` mirror.

        Same vitalia-specific kwargs injection pattern as
        :meth:`_persist_llm_call_row`. Best-effort.
        """
        if self.trace_repo is None:
            logger.warning("vitalia.sales_agent.observability.trace_event_repo_unset")
            return
        try:
            safe_kwargs = sanitize_phi_payload(dict(kwargs))
            self.trace_repo.add(
                lead_id=self.lead_id,
                channel_type=self.channel_type,
                clinic_id=self.clinic_id,
                compliance_level=self.compliance_level,
                **safe_kwargs,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning(
                "vitalia.sales_agent.observability.trace_event_persist_failed",
                error=str(exc),
            )
            self._safe_rollback()


__all__ = ["VitaliaSalesAgentCallbackHandler"]
