# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""LeadScreeningEvent domain entity.

Pure Python dataclass — NO SQLAlchemy, NO Pydantic, NO framework imports.
Maps to the ``lead_screening_events`` table (migration 017).

PHI table per vitalia/.claude/rules/hipaa-lite.md:
  - tenant_id + clinic_id BOTH mandatory (dual filter)
  - response_text and reasoning MUST be sanitized via sanitize_phi_payload
    BEFORE writing to any trace/observability/audit surface
  - soft delete only (deleted_at — never hard-delete PHI)

Outcome values reference ScreeningOutcome enum (str values match DB CHECK).

downstream-regression-na: brand-local domain entity for vitalia sales_agent
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID


def _utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


@dataclass
class LeadScreeningEvent:
    """Domain entity representing one screening assessment for a lead.

    Created by ScreeningQuestionsService after evaluating the lead's answers
    against the vertical-specific YAML question bank via LLM nano classifier.

    Fields:
        id: Primary key UUID.
        tenant_id: Root tenant isolation (mandatory — all queries must filter).
        clinic_id: Second mandatory filter — HIPAA-lite dual filter.
        lead_id: CRM lead being screened.
        vertical: Clinical vertical (dental | estetica | psicologia | fertilidad | otro).
        questions_asked: List of question strings presented to the lead.
        response_text: Lead's raw response (sanitized before persist — may be None
            if evaluation ran before patient replied).
        outcome: Result of screening — one of ScreeningOutcome enum values.
        reasoning: LLM explanation for the outcome (sanitized before persist).
        evaluated_at: When the LLM evaluation ran (None if awaiting_response).
        created_at: Row creation timestamp (UTC).
        deleted_at: Soft-delete timestamp (None = active).
    """

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    lead_id: UUID
    vertical: str
    questions_asked: list[str]
    outcome: str
    created_at: datetime
    response_text: Optional[str] = None
    reasoning: Optional[str] = None
    evaluated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
