# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""Vitalia Adrián sales_agent tool — ``retract_last_message``.

Story vitalia-slice-1-inbox T-inbox-agentic-1 — R23 production_code=true. Opus 4.7 EXCLUSIVE.

Per 03-arch-agentic.md § 2 + 05-guidelines.md § 3 + 06-tickets.yaml::T-inbox-agentic-1.

Semantics:
  Allows Adrián (modo 'ai') to revert its OWN last sent message within the
  5-minute action-receipt window. Invoked autonomously when:

    1. Adrián detects a self-inconsistency in its prior message
       (e.g., overpromise, medical claim outside scope flagged by
       compliance/safety guardrails post-send).
    2. ComplianceService raises an after-the-fact violation that demands
       retraction (HIPAA-lite voice patterns).
    3. The patient explicitly contradicts what Adrián said and Adrián
       chooses to acknowledge with humility (warm_close persona behavior).

  Tool delegates to :class:`RetractMessageService` (shipped T-inbox-be-3) which:
    1. Validates 5-min window via ``action_receipts.expires_at``
    2. Checks no patient reply after this message (409 Conflict if replied)
    3. Calls ``connections.{channel}.adapter.retract_message_id`` with timeout
    4. On adapter failure or unsupported channel → ``fallback_applied=True``
       ("marcar como erróneo" UI treatment)
    5. Updates ``vitalia_messages.retracted_at`` + ``handler_mode='human'``
    6. Emits ``MessageRetracted`` domain event via outbox bus
    7. Sync writes ``audit_log`` row pre-response (HIPAA-lite mandate)

Tenant + clinic dual filter cardinal (hipaa-lite.md § Regla cardinal):
  ``tenant_id`` + ``clinic_id`` MANDATORY in input schema. Service-level
  dual filter enforced via ``CompoundScopeRepositoryBase`` (engine shipped).

Cost: $0 LLM (deterministic — calls service, returns Spanish summary).
Latency p95: ≤2s (service includes adapter timeout 5s + audit log write).

Anti-duplication §0 audit (.claude/rules/anti-duplication.md):
  - :class:`RetractMessageService` consumed via DI — NEVER instantiated here
  - Engine observability (``SalesAgentObservabilityContext``) NEVER mirrored —
    callback handler shipped engine records tool call automatically
  - Connection adapters (``WhatsAppAdapter.retract_message_id``,
    ``InstagramAdapter.retract_message_id``, ``EmailAdapter.retract_message_id``)
    consumed transitively via service — NEVER called from this tool surface
  - Audit log writer consumed via service — NEVER instantiated here
  - PII sanitization happens in service layer (sanitize_payload(compliance_level='hipaa_lite'))
    before audit log write; this tool surface NEVER logs ``reason`` verbatim

PHI obligations honored (hipaa-lite.md):
  - Dual filter (tenant_id + clinic_id) — input schema mandate
  - Audit log sync write — delegated to service
  - PII sanitize in traces — delegated to service + tool surface scrubs error
  - Encryption — transport handled by engine; ``reason`` never traverses
    unencrypted channels (in-memory dispatch only)

Voice neutrality:
  Tool returns Spanish neutral natural-language summaries (Mexico/Colombia/Chile
  registry-safe — sales_agent voice exemption from ``.claude/rules/spanish-text.md``
  applies to AGENT'S OWN response to the patient, not to this internal tool's
  return string which is consumed by the LLM as a system observation).

downstream-regression-na: brand-local vitalia sales_agent tool (consumes
``vitalia/.../inbox/.../retract_message_service.py``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        RetractMessageService,
    )

logger = structlog.get_logger(__name__)


# ── Pydantic schemas (Pydantic v2) ──────────────────────────────────────


class RetractLastMessageInput(BaseModel):
    """Input schema — tenant_id + clinic_id mandatory per HIPAA-lite cardinal.

    ``reason`` field captures Adrián's self-explanation for the audit log
    (min_length=10 enforces non-trivial justification; max_length=500 contains
    PII surface). Service layer sanitizes the reason before persisting.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: UUID = Field(
        ...,
        description="Tenant UUID (root isolation — dual filter mandatory).",
    )
    clinic_id: UUID = Field(
        ...,
        description="Clinic UUID (HIPAA-lite dual filter mandatory).",
    )
    conversation_id: UUID = Field(
        ...,
        description="Conversation UUID containing the message to retract.",
    )
    message_id: UUID = Field(
        ...,
        description="Message UUID Adrián wants to retract (its own last sent message).",
    )
    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description=(
            "Adrián's justification for the retraction (audit log mandate). "
            "Examples: 'Promesa clínica fuera de scope detectada por ComplianceService', "
            "'Información de precio incorrecta', 'Cliente reaccionó negativamente'. "
            "Service sanitizes PHI before persisting."
        ),
    )


# ── Service resolver (DI hook) ──────────────────────────────────────────

_service_resolver: Any = None  # callable returning RetractMessageService


def set_retract_message_service_resolver(resolver: Any) -> None:
    """Wire the service resolver at orchestrator init.

    Resolver signature: ``() -> RetractMessageService``. Called at tool
    invocation time so the service is built within the active request scope
    (FastAPI DI / engine sales_agent middleware).

    Pattern parallels ``set_payment_link_service_resolver`` /
    ``set_screening_service_resolver`` (Story T-ag-tools-2 cement).
    """
    global _service_resolver  # noqa: PLW0603 — DI bootstrap hook
    _service_resolver = resolver


def _get_service() -> RetractMessageService:
    if _service_resolver is None:
        raise RuntimeError(
            "retract_last_message tool: service resolver not configured. "
            "Call set_retract_message_service_resolver(...) during orchestrator init."
        )
    return _service_resolver()


# ── Tool ────────────────────────────────────────────────────────────────


@tool("retract_last_message", args_schema=RetractLastMessageInput)
async def retract_last_message(
    tenant_id: UUID,
    clinic_id: UUID,
    conversation_id: UUID,
    message_id: UUID,
    reason: str,
) -> str:
    """Retract a message Adrián sent within the 5-minute undo window.

    Returns:
        Spanish neutral natural-language summary for Adrián consumption.
        The LLM uses this string as a system observation to decide its next turn
        (e.g., emit an apology, switch tone, escalate to human, etc.).

        Possible returns (deterministic given service outcome):
          * "Mensaje revertido. La conversación quedó en modo manual."
          * "No pude revertir el mensaje (excedió 5 minutos). Lo marqué como erróneo
             en el historial."
          * "No pude revertir: el paciente ya respondió."
          * "Este canal no permite revertir mensajes. Lo marqué como erróneo."
          * "No pude revertir el mensaje. Quedó marcado como erróneo."  (generic fallback)
          * "No pude revertir el mensaje. Quedó registrado para revisión."  (catastrophic)

    Never raises (graceful-degradation per ``tessl__graceful-degradation`` rule):
      - Service exceptions are categorized into known states and reduced to the
        appropriate Spanish summary string.
      - Unexpected exceptions yield the catastrophic-but-recoverable summary
        and a structlog warning. PII in ``reason`` is NEVER logged at tool
        surface (service handles redacted audit log via sanitize_payload).

    Implementation contract (validated by tests):
      1. Input schema (Pydantic v2) enforces tenant_id + clinic_id + UUIDs +
         reason length bounds (HIPAA-lite + injection containment).
      2. Service resolution is lazy (per-request DI scope).
      3. Service ``retract(...)`` is awaited with kwargs matching the engine
         shipped ``RetractMessageService.retract`` signature (T-inbox-be-3).
      4. ``retracted_by_user_id`` is set to ``tenant_id`` since the agent
         (not a human operator) initiated the retraction — audit log
         distinguishes via ``action='inbox.message.retracted'`` +
         ``payload.initiated_by='agent_adrian'``.
      5. Tool surface NEVER calls adapters/repos directly — service owns
         channel dispatch + fallback semantics.
    """
    # Lazy imports for the exception classes — service module is heavy
    # (imports repositories, event bus, etc.). Tool keeps cold-start light.
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        ActionReceiptExpiredError,
        MessageNotRetractableError,
        PatientRepliedConflictError,
    )

    try:
        service = _get_service()
    except RuntimeError as exc:  # resolver not wired
        logger.warning(
            "vitalia.sales_agent.tools.retract_last_message.resolver_missing",
            error=str(exc),
            conversation_id=str(conversation_id),
        )
        return "No pude revertir el mensaje. Quedó registrado para revisión."

    try:
        result = await service.retract(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            conversation_id=conversation_id,
            message_id=message_id,
            # Agent self-correction: attribute audit log to tenant (system actor)
            # since no human operator triggered this. Service captures the
            # initiator-kind in the payload via the reason prefix.
            retracted_by_user_id=tenant_id,
            reason=reason,
        )
    except ActionReceiptExpiredError:
        logger.info(
            "vitalia.sales_agent.tools.retract_last_message.expired",
            conversation_id=str(conversation_id),
            message_id=str(message_id),
        )
        return "No pude revertir el mensaje (excedió 5 minutos). Lo marqué como erróneo en el historial."
    except PatientRepliedConflictError:
        logger.info(
            "vitalia.sales_agent.tools.retract_last_message.patient_replied",
            conversation_id=str(conversation_id),
            message_id=str(message_id),
        )
        return "No pude revertir: el paciente ya respondió."
    except MessageNotRetractableError:
        logger.info(
            "vitalia.sales_agent.tools.retract_last_message.not_retractable",
            conversation_id=str(conversation_id),
            message_id=str(message_id),
        )
        return "No pude revertir el mensaje. Quedó marcado como erróneo."
    except Exception as exc:  # noqa: BLE001 — graceful-degradation envelope
        # PII containment: NEVER log `reason` verbatim. Service handles the
        # audit log with PII sanitize. Tool surface logs only opaque identifiers.
        logger.warning(
            "vitalia.sales_agent.tools.retract_last_message.unexpected_error",
            error_type=type(exc).__name__,
            conversation_id=str(conversation_id),
            message_id=str(message_id),
        )
        return "No pude revertir el mensaje. Quedó registrado para revisión."

    # Service returned a structured result (not an exception path)
    if result.retract_succeeded:
        return "Mensaje revertido. La conversación quedó en modo manual."

    # retract_succeeded=False — distinguish channel-unsupported (fallback_applied)
    # vs adapter-failure (also fallback_applied=True after T-inbox-be-3 service logic)
    if result.fallback_applied:
        return "Este canal no permite revertir mensajes. Lo marqué como erróneo."

    return "No pude revertir el mensaje. Quedó marcado como erróneo."


__all__ = [
    "RetractLastMessageInput",
    "retract_last_message",
    "set_retract_message_service_resolver",
]
