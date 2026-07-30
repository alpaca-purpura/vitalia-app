# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""Vitalia Adrián sales_agent tool — ``send_proactive_reengagement``.

Story vitalia-slice-1-fidelizacion T-9 — R23 production_code=true. Opus 4.7 EXCLUSIVE.

Per 03-arch-agentic.md § 2.1 + 06-tickets.yaml::T-9.

Semantics:
  Adrián-side wrapper around the existing brand-local ``ProactiveOutboundService``
  (shipped T-5). The tool's responsibility is to:

    1. Accept the LangGraph runtime kwargs from the supervisor / specialist node
       (caller pre-resolves patient context: phone, name, marketing_opt_in, opt_out).
    2. Delegate to ``ProactiveOutboundService.send_proactive_reminder`` with a
       deterministic idempotency key derived from the ``re_engagement_event_id``.
    3. Map the service's ``ProactiveReminderResponse`` to a Spanish-neutro
       summary string suitable for LLM chain-of-thought continuation.
    4. Apply graceful-degradation: every failure path returns a sanitized
       string (never re-raises) so the agent can continue the conversation.

The tool does NOT enforce business rules itself (opt-in, opt-out, throttle,
compliance gate). The service layer is the SSoT for those — the tool faithfully
reports the service's verdict back to the LLM.

Tenant + clinic dual filter cardinal (HIPAA-lite overlay): tenant_id +
clinic_id are MANDATORY in the input schema. Service applies the dual filter
on every repository query.

HIPAA-lite:
  - PHI fields (``patient_name``, ``patient_phone``) are passed to the service
    so it can dispatch the WhatsApp Business API template, but they are
    NEVER echoed back in the tool's return string. Only the structural outcome
    (event_id, status, blocked_reason, template_id, pattern) is surfaced for
    LLM consumption.
  - The service layer writes the ``audit_log`` row SYNCHRONOUSLY before the
    outbound dispatch. The tool does not touch ``audit_log`` directly.
  - The service layer emits ``ReEngagementTriggered`` via the outbox bus
    (``adapter_bus``) — NOT mirrored here.

Cost:
  0 LLM (no model call) — template send is deterministic Meta-approved HSM.

Latency p95:
  ≤3s (ComplianceService check + audit_log sync write + DB persist +
  outbox publish + WhatsApp Business API serial). The service owns these
  budgets; the tool only adds the @tool dispatch overhead (<10ms).

Anti-duplication audit (Step 0 GATE):
  - ``ProactiveOutboundService`` consumed via DI resolver — NEVER instantiated
    inside the tool.
  - ``adapter_bus``, ``audit_log_repository``, ``re_engagement_event_repository``
    are all consumed by the service — NEVER touched here (per
    ``.claude/rules/anti-duplication.md`` § lift shared rule).
  - Engine ``core/luana-core-sales-agent/`` has NO equivalent
    ``send_proactive_reengagement`` tool (re-engagement is vitalia-specific
    fidelization vertical) — this brand-extension is NOT a mirror.
  - The 5 Meta-approved WhatsApp HSM templates are registered via EP-8 at
    ``vitalia/backend/src/modules/vitalia/extensions.py`` (T-8 shipped) and
    consumed by the service via ``WHATSAPP_TEMPLATE_REGISTRY``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal
from uuid import UUID

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field

from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
    ReEngagementPattern,
)

if TYPE_CHECKING:
    from src.modules.vitalia.fidelizacion.application.services.proactive_outbound_service import (
        ProactiveOutboundService,
    )

logger = structlog.get_logger(__name__)


# ── Pydantic schemas (Pydantic v2) ──────────────────────────────────────


class SendProactiveReEngagementInput(BaseModel):
    """Input schema — tenant_id + clinic_id mandatory per HIPAA-lite cardinal.

    All fields are required (no LLM-inferable defaults) because the supervisor
    runtime pre-resolves patient context before invoking the tool.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: UUID = Field(
        ...,
        description="Tenant UUID (root isolation — dual filter).",
    )
    clinic_id: UUID = Field(
        ...,
        description="Clinic UUID (HIPAA-lite dual filter).",
    )
    patient_id: UUID = Field(
        ...,
        description="Patient UUID — addressee of the proactive reminder.",
    )
    patient_phone: str = Field(
        ...,
        description=(
            "Patient phone in E.164 format for WhatsApp send. PHI — never logged or returned in tool surface string."
        ),
    )
    patient_name: str = Field(
        ...,
        description=(
            "Patient display name for template variable substitution. PHI — never "
            "logged or returned in tool surface string."
        ),
    )
    pattern: Literal[
        "multi_session",
        "follow_up",
        "maintenance",
        "absence",
        "nps",
    ] = Field(
        ...,
        description=(
            "Re-engagement pattern triggering this send. Matches ReEngagementPattern "
            "value object: multi_session (active treatment plan), follow_up (post-care), "
            "maintenance (periodic — e.g. dental 6 months), absence (>90d no visit), "
            "nps (post-treatment survey)."
        ),
    )
    template_id: str = Field(
        ...,
        description=(
            "Meta-approved WhatsApp HSM template slug from "
            "WHATSAPP_TEMPLATE_REGISTRY (T-8). One of: "
            "recordatorio_proxima_sesion, recordatorio_control_doctor, "
            "invitacion_mantenimiento, re_engagement_ausencia, nps_post_tratamiento. "
            "MARKETING templates require marketing_opt_in=True (service enforces)."
        ),
    )
    marketing_opt_in: bool = Field(
        ...,
        description=(
            "Whether the patient has consented to MARKETING communications. "
            "Required True for MARKETING templates (invitacion_mantenimiento, "
            "re_engagement_ausencia). Service enforces — blocked_reason="
            "'marketing_opt_in_required' when False + MARKETING template."
        ),
    )
    opt_out: bool = Field(
        ...,
        description=(
            "Whether the patient has globally opted out of re-engagement. When True, "
            "service short-circuits with blocked_reason='patient_opted_out'."
        ),
    )
    re_engagement_event_id: UUID = Field(
        ...,
        description=(
            "Source ReEngagementEvent UUID (from detect_* cron OR manual operator "
            "action). Used as idempotency key suffix to dedupe retries."
        ),
    )
    trigger_source: str = Field(
        ...,
        description=(
            "Origin: cron name (e.g. 'cron multi_session_gap_sweep') or 'manual' "
            "for operator-triggered sends. Persisted on the event row for audit."
        ),
    )
    triggered_by_user_id: UUID = Field(
        ...,
        description=(
            "Operator UUID for audit log attribution. For cron-triggered sends, callers pass the system user UUID."
        ),
    )


# ── Service resolver (DI hook) ──────────────────────────────────────────

_service_resolver: Any = None  # callable returning ProactiveOutboundService


def set_proactive_outbound_service_resolver(resolver: Any) -> None:
    """Wire the service resolver at orchestrator init.

    Resolver signature: ``() -> ProactiveOutboundService``. Called at tool
    invocation time so the service is built within the active request scope
    (FastAPI DI / engine sales_agent middleware).
    """
    global _service_resolver  # noqa: PLW0603 — DI bootstrap hook
    _service_resolver = resolver


def _get_service() -> ProactiveOutboundService:
    if _service_resolver is None:
        raise RuntimeError(
            "send_proactive_reengagement tool: service resolver not configured. "
            "Call set_proactive_outbound_service_resolver(...) during orchestrator init."
        )
    return _service_resolver()


# ── Tool ────────────────────────────────────────────────────────────────


@tool("send_proactive_reengagement", args_schema=SendProactiveReEngagementInput)
async def send_proactive_reengagement(
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
    patient_phone: str,
    patient_name: str,
    pattern: str,
    template_id: str,
    marketing_opt_in: bool,
    opt_out: bool,
    re_engagement_event_id: UUID,
    trigger_source: str,
    triggered_by_user_id: UUID,
) -> str:
    """Send a proactive WhatsApp re-engagement template to a patient.

    Delegates to ``ProactiveOutboundService.send_proactive_reminder`` which
    runs the full 8-step flow: opt_out → marketing_opt_in → throttle →
    compliance gate → audit_log sync → persist event → emit ReEngagementTriggered
    via outbox → return ProactiveReminderResponse.

    Use this tool when a re-engagement event has been detected (by cron or
    operator action) and Adrián is dispatching the corresponding proactive
    template message. The tool is idempotent: passing the same
    ``re_engagement_event_id`` twice short-circuits at the service layer.

    Returns:
        Spanish-neutro summary string suitable for LLM chain-of-thought
        continuation. NEVER includes ``patient_name`` or ``patient_phone``
        (PHI containment). Includes ``event_id``, ``status``, and either
        ``blocked_reason`` or ``template_id`` + ``pattern`` when sent.
    """
    try:
        service = _get_service()
    except RuntimeError:
        logger.warning(
            "vitalia.sales_agent.tools.send_proactive_reengagement.resolver_not_configured",
            patient_id=str(patient_id),
            pattern=pattern,
        )
        return (
            "Hubo un problema interno con el dispatcher de mensajes proactivos. Caso registrado para revisión técnica."
        )

    try:
        pattern_enum = ReEngagementPattern(pattern)
    except ValueError:
        logger.warning(
            "vitalia.sales_agent.tools.send_proactive_reengagement.invalid_pattern",
            pattern=pattern,
        )
        return f"Patrón de re-engagement '{pattern}' no reconocido. Caso registrado para revisión."

    idempotency_key = f"proactive::{tenant_id}::{re_engagement_event_id}"

    try:
        response = await service.send_proactive_reminder(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            patient_phone=patient_phone,
            patient_name=patient_name,
            template_id=template_id,
            pattern=pattern_enum,
            marketing_opt_in=marketing_opt_in,
            opt_out=opt_out,
            user_id=triggered_by_user_id,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:  # noqa: BLE001
        # Graceful-degradation: service-layer failure (compliance raise, DB error,
        # WhatsApp Business API timeout) MUST NOT crash the agent turn. Log
        # warning and return a sanitized Spanish-neutro fallback.
        logger.warning(
            "vitalia.sales_agent.tools.send_proactive_reengagement.failed",
            error=str(exc),
            patient_id=str(patient_id),
            pattern=pattern,
            template_id=template_id,
            re_engagement_event_id=str(re_engagement_event_id),
        )
        return (
            "Hubo un problema técnico al enviar el recordatorio proactivo. "
            "Caso registrado para revisión por el equipo de operaciones."
        )

    # Map structural outcome to Spanish-neutro summary for LLM CoT.
    # Critical: NEVER include patient_name or patient_phone in the return.
    if response.status == "sent":
        sent_at_iso = response.sent_at.isoformat() if response.sent_at else "unknown"
        return (
            f"Recordatorio proactivo enviado (patrón={pattern}, "
            f"template={template_id}, event_id={response.event_id}, "
            f"sent_at={sent_at_iso})."
        )

    if response.status == "throttled":
        return (
            f"Recordatorio no enviado: ventana de throttle activa para el "
            f"patrón '{pattern}' (event_id={response.event_id}). "
            f"Esperá la próxima ventana antes de reintentar."
        )

    if response.status == "blocked":
        blocked_reason = response.blocked_reason or "compliance_blocked"
        # Human-readable hint per known blocked_reason values from the service.
        hint = _BLOCKED_REASON_HINTS.get(blocked_reason, "")
        suffix = f" — {hint}" if hint else ""
        return (
            f"Recordatorio no enviado: bloqueado por '{blocked_reason}'"
            f"{suffix} (event_id={response.event_id}, patrón={pattern})."
        )

    # Defensive fallback — unknown status shape
    return f"Estado del recordatorio: '{response.status}' (event_id={response.event_id}, patrón={pattern})."


# Human-readable Spanish-neutro hints for the service's blocked_reason values.
# Tool surface stays sanitized (no PHI) — the service log already captures detail.
_BLOCKED_REASON_HINTS: dict[str, str] = {
    "marketing_opt_in_required": (
        "el paciente no aceptó comunicaciones de marketing (consentimiento opt-in pendiente)"
    ),
    "patient_opted_out": ("el paciente se dio de baja del sistema de re-engagement"),
    "compliance_blocked": ("el canal no permite envío de PHI (ComplianceService rechazó el envío)"),
}


__all__ = [
    "SendProactiveReEngagementInput",
    "send_proactive_reengagement",
    "set_proactive_outbound_service_resolver",
]
