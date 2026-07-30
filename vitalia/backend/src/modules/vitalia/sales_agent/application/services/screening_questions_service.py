# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""ScreeningQuestionsService — Adrián medical screening for leads.

Loads questions from YAML SSoT, calls LLM nano classifier (kimi or deepseek),
sanitizes response via sanitize_phi_payload, persists LeadScreeningEvent, and
writes audit log synchronously.

Per 03-arch-be.md § 1 + 06-tickets.yaml T-be-services-2:
  "screening_questions_service.py — LLM call (single nano) per vertical YAML
   + persist event"

HIPAA-lite requirements (vitalia/.claude/rules/hipaa-lite.md):
  1. PHI dual filter: tenant_id + clinic_id mandatory on persist
  2. sanitize_phi_payload() applied before persist of response_text/reasoning
  3. audit_log row written synchronously (never async fire-forget)

downstream-regression-na: brand-local service for vitalia Adrián sales_agent
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import structlog
import yaml

from src.modules.vitalia.compliance.application.compliance_service_adapter import (
    sanitize_phi_payload,
)
from src.modules.vitalia.sales_agent.domain.entities.lead_screening_event import (
    LeadScreeningEvent,
)
from src.modules.vitalia.sales_agent.domain.enums.screening_outcome import (
    ScreeningOutcome,
)

if TYPE_CHECKING:
    from src.modules.vitalia._shared.repositories.audit_log_repository import (
        AuditLogRepository,
    )
    from src.modules.vitalia.sales_agent.infrastructure.repositories.lead_screening_event_repository import (
        LeadScreeningEventRepository,
    )

logger = structlog.get_logger()

_YAML_PATH = (
    Path(__file__).resolve().parents[5]  # back to vitalia/backend/src/
    / "modules"
    / "vitalia"
    / "agentic"
    / "screening"
    / "screening_questions_by_vertical.yaml"
)

_YAML_CACHE: dict[str, Any] | None = None


def _load_yaml() -> dict[str, Any]:
    """Load screening questions YAML (cached after first load)."""
    global _YAML_CACHE  # noqa: PLW0603
    if _YAML_CACHE is None:
        if not _YAML_PATH.exists():
            logger.error(
                "screening_yaml_not_found",
                path=str(_YAML_PATH),
            )
            _YAML_CACHE = {}
        else:
            with _YAML_PATH.open(encoding="utf-8") as f:
                _YAML_CACHE = yaml.safe_load(f) or {}
    return _YAML_CACHE


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


class ScreeningResult:
    """Value object holding the result of a screening assessment."""

    __slots__ = ("event_id", "outcome", "reasoning", "questions_asked")

    def __init__(
        self,
        event_id: UUID,
        outcome: str,
        reasoning: str | None,
        questions_asked: list[str],
    ) -> None:
        self.event_id = event_id
        self.outcome = outcome
        self.reasoning = reasoning
        self.questions_asked = questions_asked


class ScreeningQuestionsService:
    """Service for medical screening of leads before booking.

    Responsibilities:
      1. Load vertical-specific questions from YAML SSoT.
      2. Call LLM nano classifier to assess lead responses.
      3. Sanitize PHI from response_text + reasoning.
      4. Persist LeadScreeningEvent via repository (dual filter enforced).
      5. Write audit log synchronously.

    LLM model: kimi-k2.6 (nano) — single non-streaming call.
    """

    def __init__(
        self,
        screening_repo: "LeadScreeningEventRepository",
        audit_log_repo: "AuditLogRepository",
        llm_service: Any,
    ) -> None:
        """Initialize service with required dependencies.

        Args:
            screening_repo: Repository for persisting screening events.
            audit_log_repo: Repository for HIPAA-lite audit log writes.
            llm_service: LLM service implementing .generate(prompt) coroutine.
        """
        self._repo = screening_repo
        self._audit = audit_log_repo
        self._llm = llm_service

    def load_questions_for_vertical(self, vertical: str) -> list[str]:
        """Return list of question text strings for the given vertical.

        Args:
            vertical: Clinical vertical slug (dental | estetica | psicologia | fertilidad | otro).

        Returns:
            List of question text strings. Empty list if vertical unknown.
        """
        data = _load_yaml()
        entry = data.get(vertical)
        if not entry or not isinstance(entry, dict):
            logger.warning("screening.unknown_vertical", vertical=vertical)
            return []
        questions = entry.get("questions", [])
        return [q.get("text", q) if isinstance(q, dict) else str(q) for q in questions]

    async def screen(
        self,
        lead_id: UUID,
        vertical: str,
        response_text: str,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
    ) -> ScreeningResult:
        """Perform medical screening assessment for a lead.

        Loads vertical questions, calls LLM classifier to determine
        ScreeningOutcome, sanitizes PHI, persists event, writes audit log.

        Args:
            lead_id: CRM lead UUID being screened.
            vertical: Clinical vertical (dental | estetica | psicologia | fertilidad | otro).
            response_text: Lead's answers to screening questions.
            tenant_id: Tenant UUID (root isolation — dual filter).
            clinic_id: Clinic UUID (HIPAA-lite dual filter).
            user_id: Operator UUID for audit log attribution.

        Returns:
            ScreeningResult with event_id, outcome, reasoning, questions_asked.
        """
        questions = self.load_questions_for_vertical(vertical)

        # Build LLM prompt
        questions_text = "\n".join(f"- {q}" for q in questions) if questions else "(ninguna)"
        prompt = (
            f"Eres un evaluador médico de pre-screening para una clínica de salud y bienestar. "
            f"Evalúa las respuestas del paciente a las siguientes preguntas de screening.\n\n"
            f"PREGUNTAS FORMULADAS:\n{questions_text}\n\n"
            f"RESPUESTAS DEL PACIENTE:\n{response_text}\n\n"
            f"Responde con un JSON con dos campos:\n"
            f"  outcome: uno de [ok_proceed, derivar_doctor, derivar_emergencia, awaiting_response]\n"
            f"  reasoning: breve explicación (máximo 2 oraciones, sin datos de identificación)\n\n"
            f"JSON:"
        )

        llm_response = await self._llm.generate(prompt)
        raw_content: str = getattr(llm_response, "content", str(llm_response))

        # Parse JSON — fallback to awaiting_response on parse error
        outcome = ScreeningOutcome.AWAITING_RESPONSE.value
        reasoning: str | None = None
        try:
            parsed = json.loads(raw_content.strip())
            raw_outcome = parsed.get("outcome", "awaiting_response")
            # Validate outcome value
            valid_outcomes = {e.value for e in ScreeningOutcome}
            outcome = raw_outcome if raw_outcome in valid_outcomes else ScreeningOutcome.AWAITING_RESPONSE.value
            reasoning = parsed.get("reasoning")
        except (json.JSONDecodeError, AttributeError, TypeError) as exc:
            logger.warning(
                "screening.llm_parse_error",
                error=str(exc),
                content_preview=raw_content[:100] if raw_content else "",
            )

        # Sanitize PHI from text fields before persist
        sanitized_payload = sanitize_phi_payload({"response_text": response_text, "reasoning": reasoning or ""})
        safe_response_text = sanitized_payload.get("response_text")
        safe_reasoning = sanitized_payload.get("reasoning") or None

        event_id = uuid4()
        now = _utc_now()

        entity = LeadScreeningEvent(
            id=event_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            lead_id=lead_id,
            vertical=vertical,
            questions_asked=questions,
            response_text=str(safe_response_text) if safe_response_text else None,
            outcome=outcome,
            reasoning=str(safe_reasoning) if safe_reasoning else None,
            evaluated_at=now,
            created_at=now,
            deleted_at=None,
        )

        await self._repo.create(entity, tenant_id=tenant_id, clinic_id=clinic_id)

        # Audit log — synchronous write (HIPAA-lite mandate)
        from src.modules.vitalia._shared.repositories.audit_log_repository import (  # noqa: PLC0415
            AuditLogEntry,
        )

        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="screening_assessment",
            resource_type="lead_screening_event",
            resource_id=event_id,
            payload_redacted=b"",
        )
        await self._audit.write(audit_entry)

        logger.info(
            "screening.assessment_complete",
            event_id=str(event_id),
            lead_id=str(lead_id),
            vertical=vertical,
            outcome=outcome,
            tenant_id=str(tenant_id),
        )

        return ScreeningResult(
            event_id=event_id,
            outcome=outcome,
            reasoning=safe_reasoning,
            questions_asked=questions,
        )
