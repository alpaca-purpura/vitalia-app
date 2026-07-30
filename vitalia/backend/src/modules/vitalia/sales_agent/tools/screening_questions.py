# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""Vitalia Adrián sales_agent tool — ``screening_questions``.

Story T-ag-tools-2 — R23 production_code=true. Opus 4.7 EXCLUSIVE.

Per 03-arch-agentic.md § 4.2 + 02-design-agentic.md § 2.3 + § 2.7.

Semantics:
  Fires the ``ScreeningQuestionsService.screen`` async pipeline:
    1. Load vertical-specific questions from YAML SSoT
    2. Call LLM nano classifier (deepseek-v4-flash or kimi-k2.6 nano)
    3. Sanitize PHI from response_text + reasoning (compliance_level=hipaa_lite)
    4. Persist LeadScreeningEvent (tenant + clinic dual filter)
    5. Sync audit log row

Outcome ∈ {ok_proceed, derivar_doctor, derivar_emergencia, awaiting_response}.

Tenant isolation cardinal: tenant_id + clinic_id are MANDATORY in input schema.
Tool dispatcher injects them from per-turn state (sales_agent runtime
``VitaliaSalesAgentStateExtension``). Service queries enforce dual filter.

HIPAA-lite:
  - PHI sanitized BEFORE persist (sanitize_phi_payload, 22-field redaction)
  - Audit log SYNC write (never fire-forget)
  - response_text NEVER returned raw to LLM caller — only the outcome enum

Cost: $0.005-0.01 USD (single LLM nano call). Latency p95 ≤2s.

Anti-duplication audit (Step 0 GATE):
  - ``ScreeningQuestionsService`` consumed via DI — NEVER instantiated in tool
  - ``sanitize_phi_payload`` NOT called here (service already applies it)
  - No mirror of LLM dispatch logic — service owns it
  - Engine has NO equivalent (vertical-medical specific)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from src.modules.vitalia.sales_agent.application.services.screening_questions_service import (
        ScreeningQuestionsService,
    )

logger = structlog.get_logger(__name__)


# ── Pydantic schemas (Pydantic v2) ──────────────────────────────────────


class ScreeningQuestionsInput(BaseModel):
    """Input schema — tenant_id + clinic_id mandatory per HIPAA-lite cardinal."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lead_id: UUID = Field(
        ...,
        description="CRM lead UUID being screened.",
    )
    vertical: str = Field(
        ...,
        description="Clinical vertical: dental | estetica | psicologia | fertilidad | otro.",
    )
    tenant_id: UUID = Field(
        ...,
        description="Tenant UUID (root isolation — dual filter).",
    )
    clinic_id: UUID = Field(
        ...,
        description="Clinic UUID (HIPAA-lite dual filter).",
    )
    lead_response: str | None = Field(
        None,
        description=(
            "Optional patient answer text to evaluate against vertical questions. "
            "If None, tool returns the question list for first-turn dispatch."
        ),
    )
    user_id: UUID | None = Field(
        None,
        description="Operator UUID for audit log attribution. Defaults to lead_id when None.",
    )


# ── Service resolver (DI hook) ──────────────────────────────────────────

_service_resolver: Any = None  # callable returning ScreeningQuestionsService


def set_screening_service_resolver(resolver: Any) -> None:
    """Wire the service resolver at orchestrator init.

    Resolver signature: ``() -> ScreeningQuestionsService``. Called at tool
    invocation time so the service is built within the active request scope
    (FastAPI DI / engine sales_agent middleware).
    """
    global _service_resolver  # noqa: PLW0603 — DI bootstrap hook
    _service_resolver = resolver


def _get_service() -> ScreeningQuestionsService:
    if _service_resolver is None:
        raise RuntimeError(
            "screening_questions tool: service resolver not configured. "
            "Call set_screening_service_resolver(...) during orchestrator init."
        )
    return _service_resolver()


# ── Tool ────────────────────────────────────────────────────────────────


@tool("screening_questions", args_schema=ScreeningQuestionsInput)
async def screening_questions(
    lead_id: UUID,
    vertical: str,
    tenant_id: UUID,
    clinic_id: UUID,
    lead_response: str | None = None,
    user_id: UUID | None = None,
) -> str:
    """Apply medical screening to a lead before booking.

    Returns a short Spanish summary suitable for LLM consumption. The actual
    structured ``ScreeningOutcome`` is persisted via the service; the tool's
    return string is for chain-of-thought continuation.

    Outcomes:
    - ``ok_proceed`` → Adrián continues quote/booking flow
    - ``derivar_doctor`` → derive to professional (no payment link)
    - ``derivar_emergencia`` → STOP + emergency derive + escalate operator
    - ``awaiting_response`` → first turn, questions emitted; await lead

    Returns:
        Spanish summary string with outcome + brief reasoning (PHI-sanitized).
    """
    service = _get_service()
    effective_user_id = user_id or lead_id

    if lead_response is None:
        # First turn — emit questions, no LLM evaluation yet
        questions = service.load_questions_for_vertical(vertical)
        if not questions:
            return f"No hay screening configurado para la vertical '{vertical}'. Continuar con el flujo estándar."
        joined = "; ".join(questions)
        return (
            f"Screening pendiente — preguntas a formular al lead "
            f"(vertical={vertical}): {joined}. Outcome: awaiting_response."
        )

    try:
        result = await service.screen(
            lead_id=lead_id,
            vertical=vertical,
            response_text=lead_response,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=effective_user_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "vitalia.sales_agent.tools.screening_questions.failed",
            error=str(exc),
            lead_id=str(lead_id),
            vertical=vertical,
        )
        return "Error técnico aplicando screening. Continuá con el flujo estándar y anotá el caso para revisión manual."

    reasoning_suffix = f" Reasoning: {result.reasoning}" if result.reasoning else ""
    return (
        f"Screening completado para lead {lead_id} (vertical={vertical}). Outcome: {result.outcome}.{reasoning_suffix}"
    )


__all__ = [
    "ScreeningQuestionsInput",
    "screening_questions",
    "set_screening_service_resolver",
]
