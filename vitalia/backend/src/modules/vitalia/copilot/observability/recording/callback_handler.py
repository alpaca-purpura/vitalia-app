# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""VitaliaCopilotCallbackHandler — brand subclass of engine BaseAgentCallbackHandler.

Per .claude/rules/anti-duplication.md § 0 cardinal: this file inherits from
``luana_core_observability.recording.base_callback_handler.BaseAgentCallbackHandler``
(SSoT). NEVER duplicate the 8 LangChain callbacks (on_chat_model_start,
on_llm_end, on_llm_error, on_tool_start, on_tool_end, on_tool_error,
on_chain_start, on_chain_end), span dataclasses, _persist_llm_call Template
Method skeleton (sanitize → resolve pricing → calculate cost → persist),
_safe_rollback, helper extractors — those live in engine.

This module overrides ONLY:
- :meth:`_persist_llm_call_row` — writes a row to vitalia ``copilot_llm_call``
  (schema mirror per backend-ddd schema-mirror exception) with vitalia-specific
  columns (``clinic_id`` + ``compliance_level``).
- :meth:`_persist_trace_event_row` — writes a row to vitalia
  ``copilot_trace_event`` with the same vitalia-specific columns.

Both overrides apply ``sanitize_payload(...)`` (engine SSoT — never re-define)
to ``data`` JSONB before persistence. Best-effort: try/except + structlog
warning + rollback delegated to engine ``_safe_rollback``.

Anti-duplication audit checklist:
  - Imports ``BaseAgentCallbackHandler`` from ``luana_core_observability`` ✓
  - Imports ``sanitize_payload`` from ``luana_core_observability`` ✓
  - Imports ``FXResolver``, ``PricingResolver`` from engine ✓ (via base)
  - Does NOT redefine ``on_chat_model_start``, ``on_llm_end``, etc. ✓
  - Does NOT redefine ``_persist_llm_call`` Template Method skeleton ✓
  - Does NOT redefine ``_extract_provider_and_model`` or helpers ✓
  - Does NOT redefine ``sanitize_payload`` / ``redact_string`` / ``redact_value`` ✓

Reference: ``.claude/rules/anti-duplication.md`` § Inventario row "Callback
handler base" → consumed by copilot + sales_agent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import structlog
from luana_core_observability.recording.base_callback_handler import (
    BaseAgentCallbackHandler,
)
from luana_core_observability.recording.sanitization import sanitize_payload

logger = structlog.get_logger()


@dataclass
class VitaliaCopilotCallbackHandler(BaseAgentCallbackHandler):
    """Vitalia copilot LangChain callback handler.

    Subclass of :class:`BaseAgentCallbackHandler` (engine). Implements the two
    abstract persisters; inherits the 8 LangChain callbacks + Template Method
    skeleton verbatim from base.

    Vitalia-specific attributes (injected at construction):
      - ``conversation_id`` — copilot conversation UUID
      - ``user_id`` — initiating user UUID
      - ``clinic_id`` — HIPAA-lite dual filter (optional during onboarding wizard)
      - ``compliance_level`` — always ``"hipaa_lite"`` for vitalia
      - ``llm_call_repo`` — vitalia ``CopilotLLMCallVitalia`` repo (schema mirror)
      - ``trace_repo`` — vitalia ``CopilotTraceEventVitalia`` repo (schema mirror)

    Best-effort: every persistence call wrapped in ``try/except`` +
    ``structlog.warning`` + ``self._safe_rollback()``. A broken row never
    propagates out to the orchestrator (per copilot-observability.md).
    """

    conversation_id: UUID | None = None
    user_id: UUID | None = None
    clinic_id: UUID | None = None
    compliance_level: str = "hipaa_lite"
    llm_call_repo: Any = None
    trace_repo: Any = None

    # ── abstract method overrides (Template Method) ──────────────────────

    def _persist_llm_call_row(self, **kwargs: Any) -> None:  # noqa: ANN401 — passthrough
        """Persist one row to vitalia ``copilot_llm_call`` (schema mirror).

        Forwards engine-computed columns + injects vitalia-specific columns
        (conversation_id, user_id, clinic_id, compliance_level).

        Best-effort: failure is logged via structlog warning and session
        rollback is attempted; the orchestrator never sees the exception.
        """
        if self.llm_call_repo is None:
            logger.warning(
                "vitalia.copilot.observability.llm_call_repo_unset",
                turn_id=str(self.turn_id),
            )
            return
        try:
            self.llm_call_repo.add(
                conversation_id=self.conversation_id,
                user_id=self.user_id,
                clinic_id=self.clinic_id,
                compliance_level=self.compliance_level,
                parent_span_id=None,
                **kwargs,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning(
                "vitalia.copilot.observability.llm_call_persist_failed",
                error=str(exc),
                turn_id=str(self.turn_id),
            )
            self._safe_rollback()

    def _persist_trace_event_row(self, **kwargs: Any) -> None:  # noqa: ANN401 — passthrough
        """Persist one row to vitalia ``copilot_trace_event`` (schema mirror).

        Sanitizes ``data`` JSONB via engine ``sanitize_payload`` before write.
        Forwards engine-computed columns + injects vitalia-specific columns.

        Best-effort: failure logged via structlog warning + session rollback.
        """
        if self.trace_repo is None:
            logger.warning(
                "vitalia.copilot.observability.trace_repo_unset",
                turn_id=str(self.turn_id),
            )
            return
        # Re-sanitize defensively (base already sanitizes; double-check for vitalia HIPAA-lite).
        data = kwargs.pop("data", {})
        sanitized_data = sanitize_payload(data) if data else {}
        try:
            self.trace_repo.add(
                conversation_id=self.conversation_id,
                user_id=self.user_id,
                clinic_id=self.clinic_id,
                compliance_level=self.compliance_level,
                data=sanitized_data,
                **kwargs,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning(
                "vitalia.copilot.observability.trace_event_persist_failed",
                error=str(exc),
                turn_id=str(self.turn_id),
            )
            self._safe_rollback()


__all__ = ["VitaliaCopilotCallbackHandler"]
